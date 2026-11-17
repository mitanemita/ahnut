"""Запуск генерации. Правило: в конвейер уходит только оплаченный заказ с заполненной анкетой."""
import logging
from datetime import datetime, timezone

import httpx

from app.config import settings
from app.models import Order, OrderStatus

log = logging.getLogger(__name__)


def ready_for_generation(order: Order) -> bool:
    return order.paid and order.answers_complete and order.generation_requested_at is None


async def notify_pipeline(order: Order) -> None:
    """Сообщить n8n, что заказ можно генерировать. Передаём только id — данные n8n заберёт сам у web."""
    if not settings.n8n_generate_url:
        # Без n8n (разработка, простая установка) — генерируем прямо в web, в фоне
        log.warning("N8N_GENERATE_URL не задан — генерирую %s локально", order.public_id)
        import asyncio
        asyncio.get_running_loop().create_task(run_locally(order.public_id))
        return
    async with httpx.AsyncClient(timeout=10) as c:
        await c.post(
            settings.n8n_generate_url,
            json={"order_id": order.public_id},
            headers={"X-Internal-Token": settings.internal_token},
        )


async def maybe_start_generation(order: Order) -> bool:
    """Вызывается после подтверждения оплаты и после сохранения анкеты (порядок любой)."""
    if not ready_for_generation(order):
        return False
    order.generation_requested_at = datetime.now(timezone.utc)
    order.status = OrderStatus.QUEUED
    try:
        await notify_pipeline(order)
    except httpx.HTTPError as e:  # заказ остаётся в очереди, n8n подберёт по расписанию
        log.error("n8n недоступен для %s: %s", order.public_id, e)
    return True


async def run_locally(public_id: str) -> None:
    import asyncio
    from sqlalchemy import select

    from app import pipeline
    from app.db import SessionLocal
    for _ in range(40):  # ждём, пока вызывающий запрос закоммитит постановку в очередь
        await asyncio.sleep(0.25)
        async with SessionLocal() as s:
            o = (await s.execute(select(Order).where(Order.public_id == public_id))).scalar_one()
            if o.generation_requested_at:
                break
    async with SessionLocal() as s:
        o = (await s.execute(select(Order).where(Order.public_id == public_id))).scalar_one()
        if o.paid and o.answers_complete and o.generation_requested_at:
            try:
                await pipeline.run(s, o)
            except Exception:  # noqa: BLE001
                log.exception("локальная генерация %s упала", public_id)
