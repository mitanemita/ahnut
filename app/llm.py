"""Единственная точка доступа к нейросети.

Провайдер задаётся в .env (LLM_BASE_URL / LLM_API_KEY / LLM_MODEL_*): OpenRouter,
прямой API Anthropic или свой прокси — код не меняется.

ВАЖНО: функции принимают только оплаченный заказ. Это вторая линия защиты
после проверки в orders.py: анкета и фото неоплаченного заказа сюда не попадают.
"""
import json
import logging
import re
from typing import Any, Callable

import anthropic
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.models import Order

log = logging.getLogger(__name__)


class UnpaidOrderError(PermissionError):
    pass


class LLMError(RuntimeError):
    pass


def model_for_tier(tier: str) -> str:
    return {
        "zapiska": settings.llm_model_zapiska,
        "svidanie": settings.llm_model_svidanie,
        "prince": settings.llm_model_prince,
    }[tier]


def _client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(base_url=settings.llm_base_url, api_key=settings.llm_api_key, timeout=300)


_UNSUPPORTED = {"minLength", "maxLength", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
                "multipleOf", "minItems", "maxItems", "discriminator", "default", "title", "pattern"}


def strict_schema(model: type[BaseModel]) -> dict[str, Any]:
    """JSON Schema из pydantic → подмножество, которое принимает structured outputs.
    Снятые ограничения (длины и т.п.) проверяются потом pydantic-валидацией."""
    def clean(node):
        if isinstance(node, dict):
            out = {k: clean(v) for k, v in node.items() if k not in _UNSUPPORTED}
            if out.get("type") == "object" and "properties" in out:
                out["additionalProperties"] = False
            return out
        if isinstance(node, list):
            return [clean(x) for x in node]
        return node
    return clean(model.model_json_schema())


def _extract_json(text: str) -> Any:
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        raise LLMError("в ответе нет JSON")
    return json.loads(m.group(0))


async def generate(order: Order, *, system: str, content: list[dict[str, Any]], model_cls: type[BaseModel],
                   post: Callable[[dict], dict] | None = None, effort: str = "medium",
                   max_tokens: int = 16000) -> tuple[BaseModel, dict[str, Any]]:
    """Запрос к модели → проверенный pydantic-объект и суммарный usage (для подсчёта себестоимости)."""
    if not order.paid:
        raise UnpaidOrderError(f"order {order.public_id} is not paid")
    if settings.llm_fake:
        from app import llm_fake
        return llm_fake.generate(order, content, model_cls), {"fake": True}

    usage_total: dict[str, Any] = {"input_tokens": 0, "output_tokens": 0, "calls": 0}
    messages: list[dict[str, Any]] = [{"role": "user", "content": content}]
    structured = settings.llm_structured
    last_err = ""
    for _attempt in range(3):
        kw: dict[str, Any] = {"effort": effort}
        if structured:
            kw["format"] = {"type": "json_schema", "schema": strict_schema(model_cls)}
        try:
            resp = await _client().messages.create(
                model=model_for_tier(order.tier), max_tokens=max_tokens, system=system,
                messages=messages, output_config=kw,
            )
        except anthropic.BadRequestError as e:
            if structured:  # провайдер не умеет structured outputs — переходим на обычный JSON
                log.warning("structured outputs отклонены провайдером: %s", e)
                structured = False
                continue
            raise
        usage_total["calls"] += 1
        if resp.usage:
            usage_total["input_tokens"] += resp.usage.input_tokens or 0
            usage_total["output_tokens"] += resp.usage.output_tokens or 0
        if resp.stop_reason == "refusal":
            raise LLMError("модель отказалась выполнять запрос")
        text = next((b.text for b in resp.content if b.type == "text"), "")
        try:
            data = _extract_json(text)
            if post:
                data = post(data)
            return model_cls.model_validate(data), usage_total
        except (ValueError, ValidationError, LLMError) as e:
            last_err = str(e)[:1500]
            messages += [{"role": "assistant", "content": text},
                         {"role": "user", "content": f"JSON не прошёл проверку: {last_err}\nИсправь и верни только JSON."}]
    raise LLMError(f"не удалось получить корректный JSON: {last_err}")
