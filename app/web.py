"""Страницы для пользователя: выбор, анкета, фото, предпросмотр."""
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import photos as ph
from app.catalog import RECIPIENTS, TIERS, occasions_for, tones_for
from app.cards.render import render
from app.cards.spec import CardSpec
from app.forms import TIER_LIMITS, zapiska_questions
from app.models import Card, Order, OrderStatus
from app.orders import _order, get_session

router = APIRouter()


def _tpl():
    from app.main import templates
    return templates


@router.get("/api/catalog")
async def catalog(recipient: str):
    if recipient not in RECIPIENTS:
        raise HTTPException(404)
    return {"occasions": occasions_for(recipient), "tones": tones_for(recipient),
            "tiers": {k: {"title": t.title, "price": t.price_rub, "photos": t.max_photos, "available": k == "zapiska"}
                      for k, t in TIERS.items()}}


@router.get("/new", response_class=HTMLResponse)
async def new_page(request: Request):
    return _tpl().TemplateResponse(request, "new.html", {"recipients": RECIPIENTS})


def _questions(o: Order):
    if o.tier != "zapiska":
        raise HTTPException(501, "Анкеты «Свидания» и «Принца» появятся на этапе 6")
    return zapiska_questions(o.recipient, o.occasion)


@router.get("/order/{public_id}/form", response_class=HTMLResponse)
async def form_page(public_id: str, request: Request, s: AsyncSession = Depends(get_session)):
    o = await _order(s, public_id)
    if o.generation_requested_at:
        return HTMLResponse(status_code=303, headers={"Location": f"/order/{public_id}"})
    lim = TIER_LIMITS[o.tier]["photos"]
    return _tpl().TemplateResponse(request, "form.html", {
        "o": o, "tier": TIERS[o.tier], "questions": _questions(o), "answers": o.answers or {},
        "photos": o.photos or [], "min_photos": lim[0], "max_photos": lim[1]})


@router.post("/api/orders/{public_id}/photos")
async def upload_photo(public_id: str, file: UploadFile = File(...), s: AsyncSession = Depends(get_session)):
    o = await _order(s, public_id)
    if o.generation_requested_at:
        raise HTTPException(409, "Открытка уже в работе")
    have = list(o.photos or [])
    if len(have) >= TIER_LIMITS[o.tier]["photos"][1]:
        raise HTTPException(422, "Достигнут лимит фото для тарифа")
    try:
        name = ph.save_photo(public_id, await file.read(ph.MAX_UPLOAD + 1))
    except ph.PhotoError as e:
        raise HTTPException(422, str(e)) from e
    o.photos = have + [name]
    await s.commit()
    return {"photos": o.photos}


@router.delete("/api/orders/{public_id}/photos/{name}")
async def delete_photo(public_id: str, name: str, s: AsyncSession = Depends(get_session)):
    o = await _order(s, public_id)
    if o.generation_requested_at:
        raise HTTPException(409, "Открытка уже в работе")
    if name in (o.photos or []):
        ph.delete_photo(public_id, name)
        o.photos = [p for p in o.photos if p != name]
        await s.commit()
    return {"photos": o.photos or []}


@router.get("/f/{public_id}/{name}")
async def photo_file(public_id: str, name: str):
    try:
        p = ph.photo_path(public_id, name)
    except ph.PhotoError:
        raise HTTPException(404)
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=604800"})


async def latest_card(s: AsyncSession, o: Order) -> Card | None:
    return (await s.execute(select(Card).where(Card.order_id == o.id).order_by(Card.version.desc()).limit(1))).scalar_one_or_none()


def photo_urls(o: Order) -> list[str]:
    return [f"/f/{o.public_id}/{n}" for n in (o.photos or [])]


@router.get("/order/{public_id}/card", response_class=HTMLResponse)
async def preview_card(public_id: str, s: AsyncSession = Depends(get_session)):
    o = await _order(s, public_id)
    c = await latest_card(s, o)
    if not c or o.status not in (OrderStatus.READY, OrderStatus.PUBLISHED):
        raise HTTPException(404, "Открытка ещё не готова")
    return HTMLResponse(render(CardSpec.model_validate(c.spec), photo_urls(o), recipient=o.recipient),
                        headers={"X-Robots-Tag": "noindex"})
