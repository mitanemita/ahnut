from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from app.db import SessionLocal
from app.cards.routes import router as cards_router
from app.orders import router as orders_router

BASE = Path(__file__).parent

app = FastAPI(title="Ахнуть", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
app.include_router(orders_router)
app.include_router(cards_router)


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
