"""Единственная точка доступа к нейросети.

Провайдер задаётся в .env (LLM_BASE_URL / LLM_API_KEY / LLM_MODEL_*): OpenRouter,
прямой API Anthropic или свой прокси — код не меняется.

ВАЖНО: функции принимают только оплаченный заказ. Это вторая линия защиты
после проверки в generation.py: анкета и фото неоплаченного заказа сюда не попадают.
"""
import json
from typing import Any

import anthropic

from app.config import settings
from app.models import Order


class UnpaidOrderError(PermissionError):
    pass


def model_for_tier(tier: str) -> str:
    return {
        "zapiska": settings.llm_model_zapiska,
        "svidanie": settings.llm_model_svidanie,
        "prince": settings.llm_model_prince,
    }[tier]


def _client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(base_url=settings.llm_base_url, api_key=settings.llm_api_key)


async def generate_json(order: Order, *, system: str, content: list[dict[str, Any]], schema: dict[str, Any],
                        effort: str = "medium", max_tokens: int = 16000) -> tuple[dict[str, Any], dict[str, Any]]:
    """Запрос к модели со структурированным ответом. Возвращает (json, usage)."""
    if not order.paid:
        raise UnpaidOrderError(f"order {order.public_id} is not paid")
    resp = await _client().messages.create(
        model=model_for_tier(order.tier),
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": content}],
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("model refused")
    text = next(b.text for b in resp.content if b.type == "text")
    usage = resp.usage.model_dump() if resp.usage else {}
    return json.loads(text), usage
