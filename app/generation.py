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
        log.warning("N8N_GENERATE_URL не задан — заказ %s ждёт в очереди", order.public_id)
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
