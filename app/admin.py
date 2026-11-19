"""Служебные команды на сервере.

Удалить персональные данные по запросу (152-ФЗ), по номеру заказа или email:
    docker compose exec web python -m app.admin purge <id-заказа | email>
Проверить ключи и доступность сервисов (ЮKassa, OpenRouter, UniOne) — секреты не печатаются:
    docker compose exec web python -m app.admin check
Запустить фоновые задачи вручную (напоминания, удаление по сроку):
    docker compose exec web python -m app.admin housekeeping
"""
import asyncio
import sys

import httpx

from sqlalchemy import or_, select

from app.config import settings
from app.db import SessionLocal
from app.models import Order
from app.publish import housekeeping, purge


async def check() -> None:
    """Каждая проверка — один безопасный запрос только на чтение; ничего не оплачивается и не отправляется."""
    async def probe(name, fn):
        try:
            print(f"{name}: {await fn()}")
        except Exception as e:  # noqa: BLE001
            print(f"{name}: ОШИБКА — {type(e).__name__}: {str(e)[:200]}")

    async def yookassa():
        if not settings.yookassa_shop_id or not settings.yookassa_secret_key:
            return "нет YOOKASSA_SHOP_ID / YOOKASSA_SECRET_KEY в .env"
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{settings.yookassa_api_url}/me", auth=(settings.yookassa_shop_id, settings.yookassa_secret_key))
        if r.status_code == 200:
            j = r.json()
            return f"ok, магазин {j.get('account_id')}, тестовый: {j.get('test')}, статус: {j.get('status')}"
        return f"HTTP {r.status_code} — проверьте shopId и секретный ключ"

    async def openrouter():
        if not settings.llm_api_key:
            return "нет LLM_API_KEY в .env"
        base = settings.llm_base_url.rstrip("/")
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(f"{base}/v1/models")
            models = {m["id"] for m in r.json().get("data", [])} if r.status_code == 200 else set()
        want = {settings.llm_model_zapiska, settings.llm_model_svidanie, settings.llm_model_prince}
        missing = sorted(want - models) if models else []
        return (f"ok, сервер доступен с этого сервера (HTTP {r.status_code})"
                + (f"; НЕТ таких моделей: {missing} — поправьте LLM_MODEL_* в .env" if missing else "; модели найдены"))

    async def unione():
        if not settings.unione_api_key:
            return "нет UNIONE_API_KEY в .env (письма пишутся только в лог)"
        url = settings.unione_api_url.replace("email/send.json", "system/info.json")
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(url, json={}, headers={"X-API-KEY": settings.unione_api_key})
        return "ok" if r.status_code == 200 else f"HTTP {r.status_code}: {r.text[:150]}"

    await probe("ЮKassa", yookassa)
    await probe("OpenRouter", openrouter)
    await probe("UniOne", unione)
    print(f"Адрес сайта: {settings.public_base_url}; письма от: {settings.email_from}; поддержка: {settings.support_email}")


async def main(argv: list[str]) -> None:
    if argv[:1] == ["check"]:
        await check()
        return
    async with SessionLocal() as s:
        if argv[:1] == ["purge"] and len(argv) == 2:
            orders = (await s.execute(select(Order).where(or_(Order.public_id == argv[1], Order.email == argv[1])))).scalars().all()
            for o in orders:
                await purge(s, o)
            await s.commit()
            print(f"удалено заказов: {len(orders)}")
        elif argv[:1] == ["housekeeping"]:
            print(await housekeeping(s))
        else:
            print(__doc__)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
