"""Страницы для пользователя: выбор, анкета, загрузки, предпросмотр."""
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import photos as ph
from app.catalog import RECIPIENTS, TIERS, occasions_for, tones_for
from app.cards.render import render
from app.cards.spec import CardSpec
from app.forms import TIER_LIMITS, questions_for
from app.models import Card, Order, OrderStatus
from app.orders import _order, get_session

router = APIRouter()

# Политика безопасности страницы открытки: свои блоки «Принца» не могут ничего загрузить или отправить наружу
CARD_CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; media-src 'self'; font-src 'self' data:; connect-src 'none'; "
            "frame-src 'none'; object-src 'none'; form-action 'none'; base-uri 'none'")


def _tpl():
    from app.main import templates
    return templates


@router.get("/api/catalog")
async def catalog(recipient: str):
    if recipient not in RECIPIENTS:
        raise HTTPException(404)
    return {"occasions": occasions_for(recipient), "tones": tones_for(recipient),
            "tiers": {k: {"title": t.title, "price": t.price_rub, "photos": t.max_photos, "music": t.music, "available": True}
                      for k, t in TIERS.items()}}


@router.get("/new", response_class=HTMLResponse)
async def new_page(request: Request):
    return _tpl().TemplateResponse(request, "new.html", {"recipients": RECIPIENTS})


def _questions(o: Order):
    return questions_for(o.tier, o.recipient, o.occasion)


@router.get("/order/{public_id}/form", response_class=HTMLResponse)
async def form_page(public_id: str, request: Request, s: AsyncSession = Depends(get_session)):
    o = await _order(s, public_id)
    if o.generation_requested_at:
        return RedirectResponse(f"/order/{public_id}", status_code=303)
    lim = TIER_LIMITS[o.tier]
    return _tpl().TemplateResponse(request, "form.html", {
        "o": o, "tier": TIERS[o.tier], "questions": _questions(o), "answers": o.answers or {},
        "photos": o.photos or [], "refs": o.refs or [], "music": o.music,
        "min_photos": lim["photos"][0], "max_photos": lim["photos"][1], "max_refs": lim["refs"], "allow_music": lim["music"]})


def _check_editable(o: Order):
    if o.generation_requested_at:
        raise HTTPException(409, "Открытка уже в работе")


def _files_view(o: Order) -> dict:
    return {"photos": o.photos or [], "refs": o.refs or [], "music": o.music}


@router.post("/api/orders/{public_id}/photos")
async def upload_photo(public_id: str, file: UploadFile = File(...), s: AsyncSession = Depends(get_session)):
    return await upload(public_id, "photos", file, s)


@router.post("/api/orders/{public_id}/files/{kind}")
async def upload(public_id: str, kind: str, file: UploadFile = File(...), s: AsyncSession = Depends(get_session)):
    o = await _order(s, public_id)
    _check_editable(o)
    lim = TIER_LIMITS[o.tier]
    data = await file.read(max(ph.MAX_UPLOAD, ph.MAX_MUSIC) + 1)
    try:
        if kind == "photos":
            if len(o.photos or []) >= lim["photos"][1]:
                raise HTTPException(422, "Достигнут лимит фото для тарифа")
            o.photos = list(o.photos or []) + [ph.save_photo(public_id, data)]
        elif kind == "refs":
            if len(o.refs or []) >= lim["refs"]:
                raise HTTPException(422, "Референсы доступны на «Принце», до 5 штук")
            o.refs = list(o.refs or []) + [ph.save_ref(public_id, data)]
        elif kind == "music":
            if not lim["music"]:
                raise HTTPException(422, "Музыка доступна на «Принце»")
            if o.music:
                ph.file_path(public_id, o.music).unlink(missing_ok=True)
            o.music = ph.save_music(public_id, data)
        else:
            raise HTTPException(404)
    except ph.PhotoError as e:
        raise HTTPException(422, str(e)) from e
    await s.commit()
    return _files_view(o)


@router.delete("/api/orders/{public_id}/photos/{name}")
@router.delete("/api/orders/{public_id}/files/{name}")
async def delete_file(public_id: str, name: str, s: AsyncSession = Depends(get_session)):
    o = await _order(s, public_id)
    _check_editable(o)
    if name in (o.photos or []) or name in (o.refs or []) or name == o.music:
        ph.file_path(public_id, name).unlink(missing_ok=True)
        o.photos = [p for p in (o.photos or []) if p != name]
        o.refs = [p for p in (o.refs or []) if p != name]
        if o.music == name:
            o.music = None
        await s.commit()
    return _files_view(o)


@router.get("/f/{public_id}/{name}")
async def order_file(public_id: str, name: str):
    try:
        p = ph.file_path(public_id, name)
    except ph.PhotoError:
        raise HTTPException(404)
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, media_type=ph.mime_for(name), headers={"Cache-Control": "private, max-age=604800"})


async def latest_card(s: AsyncSession, o: Order) -> Card | None:
    return (await s.execute(select(Card).where(Card.order_id == o.id).order_by(Card.version.desc()).limit(1))).scalar_one_or_none()


def photo_urls(o: Order) -> list[str]:
    return [f"/f/{o.public_id}/{n}" for n in (o.photos or [])]


def render_order_card(o: Order, spec: CardSpec, **kw) -> str:
    music = f"/f/{o.public_id}/{o.music}" if o.music else None
    return render(spec, kw.pop("photos", None) or photo_urls(o), recipient=o.recipient, music_src=music, **kw)


@router.get("/order/{public_id}/card", response_class=HTMLResponse)
async def preview_card(public_id: str, s: AsyncSession = Depends(get_session)):
    o = await _order(s, public_id)
    c = await latest_card(s, o)
    if not c or o.status not in (OrderStatus.READY, OrderStatus.PUBLISHED):
        raise HTTPException(404, "Открытка ещё не готова")
    return HTMLResponse(render_order_card(o, CardSpec.model_validate(c.spec)),
                        headers={"X-Robots-Tag": "noindex", "Content-Security-Policy": CARD_CSP})
