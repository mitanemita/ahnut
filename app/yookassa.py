"""Минимальный клиент API ЮKassa (v3). Статус платежа берём только отсюда, не из редиректа и не из тела уведомления."""
import ipaddress
import uuid
from typing import Any

import httpx

from app.config import settings

# Адреса, с которых ЮKassa шлёт уведомления (https://yookassa.ru/developers/using-api/webhooks)
YOOKASSA_NETS = [
    ipaddress.ip_network(n)
    for n in (
        "185.71.76.0/27",
        "185.71.77.0/27",
        "77.75.153.0/25",
        "77.75.156.11/32",
        "77.75.156.35/32",
        "77.75.154.128/25",
        "2a02:5180::/32",
    )
]


def is_yookassa_ip(ip: str | None) -> bool:
    if not ip:
        return False
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr in net for net in YOOKASSA_NETS)


class YooKassaError(RuntimeError):
    pass


class YooKassa:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None):
        self._transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=settings.yookassa_api_url,
            auth=(settings.yookassa_shop_id, settings.yookassa_secret_key),
            timeout=20,
            transport=self._transport,
        )

    async def create_payment(
        self, *, amount_rub: int, description: str, return_url: str, metadata: dict[str, str], idempotence_key: str
    ) -> dict[str, Any]:
        body = {
            "amount": {"value": f"{amount_rub}.00", "currency": "RUB"},
            "capture": True,
            "confirmation": {"type": "redirect", "return_url": return_url},
            # Для самозанятого ЮKassa сама регистрирует доход в «Мой налог»;
            # description попадает в чек как название услуги (≤128 символов).
            "description": description[:128],
            "metadata": metadata,
        }
        async with self._client() as c:
            r = await c.post("/payments", json=body, headers={"Idempotence-Key": idempotence_key})
        if r.status_code >= 400:
            raise YooKassaError(f"create_payment {r.status_code}: {r.text[:300]}")
        return r.json()

    async def get_payment(self, payment_id: str) -> dict[str, Any] | None:
        async with self._client() as c:
            r = await c.get(f"/payments/{payment_id}")
        if r.status_code == 404:
            return None
        if r.status_code >= 400:
            raise YooKassaError(f"get_payment {r.status_code}: {r.text[:300]}")
        return r.json()


def new_idempotence_key() -> str:
    return str(uuid.uuid4())


yookassa = YooKassa()
