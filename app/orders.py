"""Заказы, оплата, уведомления ЮKassa. Порядок «анкета → оплата» и «оплата → анкета» оба работают."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import yookassa as yk
from app.catalog import EDIT_PACKS, EXTENSION_TITLES, EXTENSIONS, TIERS, validate_choice
from app.config import settings
from app.db import SessionLocal
from app.generation import maybe_start_generation
from app.models import Order, OrderStatus, Payment

log = logging.getLogger(__name__)
router = APIRouter()


async def get_session():
    async with SessionLocal() as s:
        yield s


async def _order(s: AsyncSession, public_id: str) -> Order:
    o = (await s.execute(select(Order).where(Order.public_id == public_id))).scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Заказ не найден")
    return o


def _order_view(o: Order) -> dict[str, Any]:
    return {
        "order_id": o.public_id, "tier": o.tier, "status": o.status, "paid": o.paid,
        "amount_rub": o.amount_rub, "answers_complete": o.answers_complete,
    }


# ---------- создание заказа ----------

class OrderIn(BaseModel):
    tier: str
    recipient: str
    occasion: str
    tone: str


@router.post("/api/orders")
async def create_order(body: OrderIn, s: AsyncSession = Depends(get_session)):
    err = validate_choice(body.tier, body.recipient, body.occasion, body.tone)
    if err:
        raise HTTPException(422, err)
    o = Order(tier=body.tier, recipient=body.recipient, occasion=body.occasion, tone=body.tone,
              amount_rub=TIERS[body.tier].price_rub)
    s.add(o)
    await s.commit()
    return _order_view(o)


@router.get("/api/orders/{public_id}")
async def order_status(public_id: str, s: AsyncSession = Depends(get_session)):
    o = await _order(s, public_id)
    await _refresh_pending_payments(s, o)
    return _order_view(o)


# ---------- анкета ----------

class AnswersIn(BaseModel):
    answers: dict[str, Any]
    complete: bool = False
    pd_consent: bool = False  # согласие на обработку ПДн (152-ФЗ)


@router.put("/api/orders/{public_id}/answers")
async def save_answers(public_id: str, body: AnswersIn, s: AsyncSession = Depends(get_session)):
    from app.forms import TIER_LIMITS, validate_answers
    from app.web import _questions
    o = await _order(s, public_id)
    if o.generation_requested_at:
        raise HTTPException(409, "Анкета уже передана в работу")
    if body.complete and not body.pd_consent:
        raise HTTPException(422, "Нужно согласие на обработку персональных данных")
    clean, errors = validate_answers(_questions(o), body.answers, body.complete)
    if body.complete and len(o.photos or []) < TIER_LIMITS[o.tier]["photos"][0]:
        errors.append("Добавьте хотя бы одно фото")
    if body.complete and clean.get("music") == "own" and not o.music:
        errors.append("Загрузите музыку или выберите «Без музыки»")
    if errors:
        raise HTTPException(422, "; ".join(errors))
    o.answers = clean
    if body.complete:
        o.answers_complete = True
        o.pd_consent_at = datetime.now(timezone.utc)
    await maybe_start_generation(o)
    await s.commit()
    return _order_view(o)


# ---------- оплата: заказ, докупка правок, продление ----------

class PayIn(BaseModel):
    email: EmailStr


async def create_payment(s: AsyncSession, o: Order, kind: str, amount: int, description: str,
                         meta: dict[str, Any] | None = None) -> str:
    """Создать платёж в ЮKassa и запись о нём. Возвращает адрес страницы оплаты."""
    p = await yk.yookassa.create_payment(
        amount_rub=amount, description=description,
        return_url=f"{settings.public_base_url}/order/{o.public_id}",
        metadata={"order_id": o.public_id, "kind": kind},
        idempotence_key=yk.new_idempotence_key(),
    )
    s.add(Payment(order_id=o.id, yookassa_id=p["id"], kind=kind, amount_rub=amount, status=p["status"], meta=meta))
    return p["confirmation"]["confirmation_url"]


@router.post("/api/orders/{public_id}/pay")
async def pay(public_id: str, body: PayIn, s: AsyncSession = Depends(get_session)):
    o = await _order(s, public_id)
    if o.paid:
        raise HTTPException(409, "Заказ уже оплачен")
    o.email = str(body.email)
    url = await create_payment(s, o, "order", o.amount_rub, f"Открытка «{TIERS[o.tier].title}», заказ {o.public_id[:8]}")
    o.status = OrderStatus.AWAITING_PAYMENT if o.status == OrderStatus.DRAFT else o.status
    await s.commit()
    return {"confirmation_url": url, **_order_view(o)}


class EditsIn(BaseModel):
    qty: int


@router.post("/api/orders/{public_id}/buy-edits")
async def buy_edits(public_id: str, body: EditsIn, s: AsyncSession = Depends(get_session)):
    o = await _order(s, public_id)
    price = EDIT_PACKS[o.tier].get(body.qty)
    if not o.paid or price is None:
        raise HTTPException(422, "Такого пакета правок нет")
    url = await create_payment(s, o, "edits", price, f"Дополнительные правки открытки: {body.qty} шт., заказ {o.public_id[:8]}",
                               {"qty": body.qty})
    await s.commit()
    return {"confirmation_url": url}


class ExtendIn(BaseModel):
    period: str


@router.post("/api/orders/{public_id}/extend")
async def extend(public_id: str, body: ExtendIn, s: AsyncSession = Depends(get_session)):
    o = await _order(s, public_id)
    if body.period not in EXTENSIONS or not o.published_at:
        raise HTTPException(422, "Продлить можно опубликованную открытку")
    if o.forever:
        raise HTTPException(409, "Открытка уже доступна навсегда")
    price = EXTENSIONS[body.period][0]
    url = await create_payment(s, o, "extension", price, f"Продление ссылки на открытку: {EXTENSION_TITLES[body.period]}",
                               {"period": body.period})
    await s.commit()
    return {"confirmation_url": url}


def _payment_is_valid_success(obj: dict[str, Any], pay: Payment, order: Order) -> bool:
    amount = obj.get("amount") or {}
    meta = obj.get("metadata") or {}
    return (
        obj.get("status") == "succeeded"
        and obj.get("paid") is True
        and amount.get("currency") == "RUB"
        and amount.get("value") == f"{pay.amount_rub}.00"
        and meta.get("order_id") == order.public_id
        and meta.get("kind", "order") == pay.kind
    )


def apply_extension(order: Order, period: str) -> None:
    days = EXTENSIONS[period][1]
    if days is None:
        order.forever, order.expires_at = True, None
        return
    now = datetime.now(timezone.utc)
    base = order.expires_at if order.expires_at and _aware(order.expires_at) > now else now
    order.expires_at = _aware(base) + timedelta(days=days)
    order.reminder_sent_at = None


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


async def apply_payment_state(s: AsyncSession, yookassa_id: str) -> None:
    """Сверить платёж с API ЮKassa и зачесть его. Источник правды — только ответ API; зачёт — ровно один раз."""
    pay = (await s.execute(select(Payment).where(Payment.yookassa_id == yookassa_id))).scalar_one_or_none()
    if not pay:
        log.warning("Неизвестный платёж %s", yookassa_id)
        return
    obj = await yk.yookassa.get_payment(yookassa_id)
    if not obj:
        return
    order = await s.get(Order, pay.order_id)
    pay.status = obj.get("status", pay.status)
    if pay.applied or pay.status != "succeeded":
        await s.commit()
        return
    if not _payment_is_valid_success(obj, pay, order):
        log.error("Платёж %s успешен, но не прошёл сверку (сумма/заказ/вид)", yookassa_id)
        await s.commit()
        return
    pay.applied = True
    if pay.kind == "order":
        order.paid = True
        order.paid_at = datetime.now(timezone.utc)
        if order.status in (OrderStatus.DRAFT, OrderStatus.AWAITING_PAYMENT):
            order.status = OrderStatus.PAID
        await maybe_start_generation(order)
    elif pay.kind == "edits":
        order.edits_bought += int((pay.meta or {}).get("qty", 0))
    elif pay.kind == "extension":
        apply_extension(order, (pay.meta or {}).get("period", "month"))
        if order.status == OrderStatus.PUBLISHED and order.email:
            from app import mailer
            await mailer.send_extended(order)
    await s.commit()


async def _refresh_pending_payments(s: AsyncSession, o: Order) -> None:
    """Пользователь вернулся с оплаты — не верим редиректу, спрашиваем API."""
    pending = (await s.execute(
        select(Payment).where(Payment.order_id == o.id, Payment.status.in_(("pending", "waiting_for_capture")))
    )).scalars().all()
    for p in pending:
        try:
            await apply_payment_state(s, p.yookassa_id)
        except yk.YooKassaError as e:
            log.error("Проверка платежа %s: %s", p.yookassa_id, e)


@router.post("/yookassa/webhook")
async def yookassa_webhook(request: Request, s: AsyncSession = Depends(get_session)):
    ip = request.client.host if request.client else None
    if settings.yookassa_check_ip and not yk.is_yookassa_ip(ip):
        log.warning("Уведомление ЮKassa с чужого IP %s", ip)
        raise HTTPException(403)
    data = await request.json()
    event = data.get("event", "")
    obj = data.get("object") or {}
    payment_id = obj.get("payment_id") if event.startswith("refund.") else obj.get("id")
    if payment_id:
        await apply_payment_state(s, payment_id)
    return {"ok": True}  # 200, иначе ЮKassa будет повторять


# ---------- страница заказа ----------

@router.get("/order/{public_id}", response_class=HTMLResponse)
async def order_page(public_id: str, request: Request, s: AsyncSession = Depends(get_session)):
    from app import edits as ed
    from app import mailer
    from app.catalog import EDIT_PACKS, EDITS_INCLUDED, EXTENSION_TITLES, EXTENSIONS, HOSTING_DAYS
    from app.main import templates
    from app.publish import is_expired
    o = await _order(s, public_id)
    await _refresh_pending_payments(s, o)
    versions = ed.summary(await ed.card_versions(s, o))
    return templates.TemplateResponse(request, "order.html", {
        "o": o, "tier": TIERS[o.tier], "edits_left": ed.edits_left(o), "edits_included": EDITS_INCLUDED,
        "packs": EDIT_PACKS[o.tier], "ext": {k: (v[0], EXTENSION_TITLES[k]) for k, v in EXTENSIONS.items()},
        "versions": versions, "card_url": mailer.card_url(o) if o.card_id else None,
        "expires": mailer._date(o.expires_at) if o.published_at else None, "expired": o.published_at and is_expired(o),
        "hosting_days": HOSTING_DAYS})


# ---------- внутренний API для n8n ----------

def _check_internal(token: str | None) -> None:
    if not settings.internal_token or token != settings.internal_token:
        raise HTTPException(403)


@router.post("/internal/orders/{public_id}/generate")
async def internal_generate(public_id: str, s: AsyncSession = Depends(get_session),
                            x_internal_token: str | None = Header(default=None)):
    _check_internal(x_internal_token)
    o = await _order(s, public_id)
    if not o.paid:
        raise HTTPException(402, "Заказ не оплачен — генерация запрещена")
    if not o.answers_complete:
        raise HTTPException(409, "Анкета не заполнена")
    from app import pipeline
    result = await pipeline.run(s, o)
    await s.commit()
    return result
