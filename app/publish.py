"""Публикация и выдача: правки, публичная ссылка /c/<id>, пароль, файл, сроки хостинга, фоновые задачи.

Две разные ссылки:
- /order/<public_id> — у отправителя: предпросмотр, правки, публикация, продление (НЕ пересылать получателю);
- /c/<card_id>       — у получателя: только открытка.
"""
import asyncio
import hashlib
import hmac
import logging
import secrets
import shutil
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import edits as ed
from app import mailer
from app import photos as ph
from app.catalog import HOSTING_DAYS
from app.cards.spec import CardSpec
from app.config import settings
from app.generation import notify_pipeline
from app.models import Card, Order, OrderStatus
from app.orders import _aware, _order, get_session
from app.web import CARD_CSP, latest_card, render_order_card

log = logging.getLogger(__name__)
router = APIRouter()


def _tpl():
    from app.main import templates
    return templates


# ---------- правки ----------

class EditIn(BaseModel):
    text: str = Field(min_length=2, max_length=300)


@router.post("/api/orders/{public_id}/edits")
async def request_edit(public_id: str, body: EditIn, bg: BackgroundTasks, s: AsyncSession = Depends(get_session)):
    o = await _order(s, public_id)
    if o.status not in (OrderStatus.READY, OrderStatus.PUBLISHED):
        raise HTTPException(409, "Сейчас править нельзя — дождитесь, пока открытка будет готова")
    if ed.edits_left(o) <= 0:
        raise HTTPException(402, "Правки закончились — докупите ещё")
    o.status, o.edit_error = OrderStatus.EDITING, None
    await s.commit()
    bg.add_task(ed.run_edit_in_background, public_id, body.text.strip())
    return {"status": o.status}


class RevertIn(BaseModel):
    version: int


@router.post("/api/orders/{public_id}/revert")
async def revert(public_id: str, body: RevertIn, s: AsyncSession = Depends(get_session)):
    o = await _order(s, public_id)
    if o.status not in (OrderStatus.READY, OrderStatus.PUBLISHED):
        raise HTTPException(409, "Сейчас нельзя")
    await ed.revert(s, o, body.version)
    return {"ok": True}


@router.post("/api/orders/{public_id}/retry")
async def retry(public_id: str, s: AsyncSession = Depends(get_session)):
    """Генерация не удалась — повтор бесплатно (деньги не возвращаем, но открытку обязаны сделать)."""
    o = await _order(s, public_id)
    if o.status != OrderStatus.FAILED or not o.paid:
        raise HTTPException(409, "Повтор не нужен")
    o.status = OrderStatus.QUEUED
    await s.commit()
    await notify_pipeline(o)
    return {"status": o.status}


# ---------- публикация ----------

def _hash_password(pw: str) -> str:
    salt = secrets.token_hex(8)
    return salt + "$" + hashlib.scrypt(pw.encode(), salt=salt.encode(), n=2**14, r=8, p=1).hex()


def _check_password(pw: str, stored: str) -> bool:
    salt, h = stored.split("$", 1)
    return hmac.compare_digest(hashlib.scrypt(pw.encode(), salt=salt.encode(), n=2**14, r=8, p=1).hex(), h)


class PublishIn(BaseModel):
    password: str = Field("", max_length=40)


@router.post("/api/orders/{public_id}/publish")
async def publish(public_id: str, body: PublishIn, s: AsyncSession = Depends(get_session)):
    o = await _order(s, public_id)
    if o.status == OrderStatus.PUBLISHED:
        return {"card_url": mailer.card_url(o)}
    if o.status != OrderStatus.READY:
        raise HTTPException(409, "Опубликовать можно готовую открытку")
    now = datetime.now(timezone.utc)
    o.card_id = secrets.token_urlsafe(16)
    o.card_password = _hash_password(body.password) if body.password.strip() else None
    o.published_at, o.status = now, OrderStatus.PUBLISHED
    if not o.forever and not o.expires_at:
        o.expires_at = now + timedelta(days=HOSTING_DAYS)
    await s.commit()
    await mailer.send_published(o)
    return {"card_url": mailer.card_url(o), "expires_at": o.expires_at}


def is_expired(o: Order) -> bool:
    if o.purged_at:
        return True
    return not o.forever and o.expires_at is not None and _aware(o.expires_at) < datetime.now(timezone.utc)


def _cookie_name(card_id: str) -> str:
    return "c_" + card_id[:12]


def _cookie_value(o: Order) -> str:
    return hmac.new(settings.secret_key.encode(), (o.card_id + (o.card_password or "")).encode(), "sha256").hexdigest()


async def _by_card(s: AsyncSession, card_id: str) -> Order:
    o = (await s.execute(select(Order).where(Order.card_id == card_id))).scalar_one_or_none()
    if not o:
        raise HTTPException(404)
    return o


@router.get("/c/{card_id}", response_class=HTMLResponse)
async def public_card(card_id: str, request: Request, s: AsyncSession = Depends(get_session)):
    o = await _by_card(s, card_id)
    if is_expired(o):
        return _tpl().TemplateResponse(request, "card_expired.html", {}, status_code=410)
    if o.card_password and request.cookies.get(_cookie_name(card_id)) != _cookie_value(o):
        return _tpl().TemplateResponse(request, "card_password.html", {"card_id": card_id, "error": False})
    c = await latest_card(s, o)
    return HTMLResponse(render_order_card(o, CardSpec.model_validate(c.spec)),
                        headers={"X-Robots-Tag": "noindex", "Content-Security-Policy": CARD_CSP,
                                 "Referrer-Policy": "no-referrer", "Cache-Control": "private, no-store"})


@router.post("/c/{card_id}", response_class=HTMLResponse)
async def card_password(card_id: str, request: Request, password: str = Form(""), s: AsyncSession = Depends(get_session)):
    o = await _by_card(s, card_id)
    if not o.card_password or not _check_password(password, o.card_password):
        await asyncio.sleep(1)  # притормозить перебор
        return _tpl().TemplateResponse(request, "card_password.html", {"card_id": card_id, "error": True}, status_code=403)
    r = RedirectResponse(f"/c/{card_id}", status_code=303)
    r.set_cookie(_cookie_name(card_id), _cookie_value(o), max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax",
                 secure=settings.public_base_url.startswith("https"))
    return r


@router.get("/order/{public_id}/download")
async def download(public_id: str, s: AsyncSession = Depends(get_session)):
    """Файл-бонус: всё внутри одного HTML (фото, шрифты). Музыка в файл не кладётся — только по ссылке."""
    o = await _order(s, public_id)
    if o.status != OrderStatus.PUBLISHED or is_expired(o):
        raise HTTPException(409, "Файл доступен для опубликованной открытки")
    c = await latest_card(s, o)
    from app.pipeline import data_uri_photos
    spec = CardSpec.model_validate(c.spec).model_copy(update={"music": False})
    html = render_order_card(o, spec, photos=data_uri_photos(o), inline=True)
    return Response(html, media_type="text/html; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="otkrytka.html"'})


# ---------- фоновые задачи: напоминания и удаление ПДн по сроку ----------

def purge_files(o: Order) -> None:
    d = ph.order_dir(o.public_id)
    shutil.rmtree(d, ignore_errors=True)


async def purge(s: AsyncSession, o: Order) -> None:
    """Удалить персональные данные заказа: фото, музыку, анкету, тексты открытки. Платёжные записи остаются (учёт)."""
    purge_files(o)
    for c in (await s.execute(select(Card).where(Card.order_id == o.id))).scalars():
        await s.delete(c)
    o.answers, o.photos, o.refs, o.music, o.card_password = None, [], [], None, None
    o.purged_at = datetime.now(timezone.utc)


async def housekeeping(s: AsyncSession) -> dict:
    now = datetime.now(timezone.utc)
    sent = purged = 0
    published = (await s.execute(select(Order).where(Order.status == OrderStatus.PUBLISHED, Order.forever.is_(False),
                                                     Order.purged_at.is_(None)))).scalars().all()
    for o in published:
        exp = _aware(o.expires_at) if o.expires_at else None
        if exp and o.reminder_sent_at is None and now < exp <= now + timedelta(hours=26):
            if await mailer.send_expiring(o) or not settings.unione_api_key:  # без ключа — только в лог, один раз
                o.reminder_sent_at = now
                sent += 1
        if exp and exp + timedelta(days=settings.purge_after_days) < now:
            await purge(s, o)
            purged += 1
    stale = (await s.execute(select(Order).where(Order.purged_at.is_(None), Order.published_at.is_(None)))).scalars().all()
    for o in stale:
        created = _aware(o.created_at) if o.created_at else now
        if (not o.paid and created + timedelta(days=30) < now) or (o.paid and created + timedelta(days=180) < now):
            await purge(s, o)
            purged += 1
    await s.commit()
    return {"reminders": sent, "purged": purged}


async def scheduler_loop() -> None:
    from app.db import SessionLocal
    while True:
        try:
            async with SessionLocal() as s:
                res = await housekeeping(s)
                if any(res.values()):
                    log.info("фоновые задачи: %s", res)
        except Exception:  # noqa: BLE001
            log.exception("фоновые задачи упали")
        await asyncio.sleep(settings.scheduler_minutes * 60)
