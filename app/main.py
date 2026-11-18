import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from app.db import SessionLocal
from app.cards.routes import router as cards_router
from app.orders import router as orders_router
from app.publish import router as publish_router
from app.publish import scheduler_loop
from app.web import router as web_router

BASE = Path(__file__).parent

@asynccontextmanager
async def lifespan(_app):
    task = asyncio.create_task(scheduler_loop())  # напоминания о сроке и удаление данных по сроку
    yield
    task.cancel()


app = FastAPI(title="Ахнуть", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
app.include_router(orders_router)
app.include_router(cards_router)
app.include_router(web_router)
app.include_router(publish_router)


@app.get("/offer", response_class=HTMLResponse)
async def offer(request: Request):
    return templates.TemplateResponse(request, "legal/offer.html", _legal_ctx())


@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse(request, "legal/privacy.html", _legal_ctx())


def _legal_ctx() -> dict:
    from app.catalog import EDIT_PACKS, EDITS_INCLUDED, EXTENSIONS, HOSTING_DAYS, TIERS
    from app.config import settings
    return {"tiers": TIERS, "packs": EDIT_PACKS, "edits_included": EDITS_INCLUDED, "ext": EXTENSIONS,
            "hosting_days": HOSTING_DAYS, "support": settings.support_email, "purge_days": settings.purge_after_days}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/healthz")
async def healthz():
    try:
        async with SessionLocal() as s:
            await s.execute(text("SELECT 1"))
        return {"ok": True, "db": "ok"}
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"ok": False, "db": type(e).__name__}, status_code=503)
