"""Письма через UniOne (Unisender Go) по HTTPS — как во втором проекте.

Без UNIONE_API_KEY письма не отправляются, а пишутся в лог (разработка).
Нужно в UniOne: подтверждённый домен отправки ahnut.ru (DKIM/SPF) и домен для трекинга.
"""
import logging
from datetime import datetime, timezone

import httpx

from app.config import settings
from app.models import Order

log = logging.getLogger(__name__)
SENT: list[dict] = []  # последние письма (для тестов и отладки)


def _date(d: datetime | None) -> str:
    if not d:
        return "навсегда"
    months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    d = d.astimezone(timezone.utc)
    return f"{d.day} {months[d.month - 1]} {d.year}"


def order_url(o: Order) -> str:
    return f"{settings.public_base_url}/order/{o.public_id}"


def card_url(o: Order) -> str:
    return f"{settings.public_base_url}/c/{o.card_id}"


async def send(to: str | None, subject: str, text: str) -> bool:
    if not to:
        return False
    msg = {"to": to, "subject": subject, "text": text}
    SENT.append(msg)
    del SENT[:-50]
    if not settings.unione_api_key:
        log.warning("UNIONE_API_KEY не задан — письмо не отправлено: %s → %s", subject, to)
        return False
    body = {"message": {
        "recipients": [{"email": to}],
        "subject": subject,
        "from_email": settings.email_from,
        "from_name": settings.email_from_name,
        "body": {"plaintext": text},
        "track_links": 0, "track_read": 0, "skip_unsubscribe": 1,
    }}
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(settings.unione_api_url, json=body, headers={"X-API-KEY": settings.unione_api_key})
        if r.status_code >= 400:
            log.error("UniOne %s: %s", r.status_code, r.text[:300])
            return False
        return True
    except httpx.HTTPError as e:
        log.error("UniOne недоступен: %s", e)
        return False


SIGN = "\n\n—\n«Ахнуть» · открытка, от которой ахнут\nЭто письмо отправлено, потому что вы заказали открытку на ahnut.ru."


async def send_ready(o: Order) -> bool:
    return await send(o.email, "Открытка готова — посмотрите", (
        "Здравствуйте!\n\nВаша открытка собрана. Посмотрите её, при необходимости попросите правки "
        f"(2 входят в тариф) и нажмите «Опубликовать»:\n{order_url(o)}\n\n"
        "Эта ссылка — только для вас, не пересылайте её получателю: по ней можно править и продлевать открытку." + SIGN))


async def send_published(o: Order) -> bool:
    return await send(o.email, "Открытка опубликована — вот ссылка для получателя", (
        f"Готово! Ссылка для получателя:\n{card_url(o)}\n\n"
        f"Ссылка работает до: {_date(o.expires_at)}. Продлить (месяц, год или навсегда) и скачать файл можно здесь:\n{order_url(o)}\n\n"
        "Совет: отправляйте получателю именно ссылку. HTML-файл, открытый из WhatsApp или «Файлов» на iPhone, "
        "покажется во встроенном просмотрщике без анимаций и нажатий." + SIGN))


async def send_expiring(o: Order) -> bool:
    return await send(o.email, "Завтра ссылка на открытку перестанет работать", (
        f"Ссылка на вашу открытку работает до {_date(o.expires_at)}.\n"
        f"Чтобы она не пропала, продлите её на месяц, год или навсегда:\n{order_url(o)}" + SIGN))


async def send_extended(o: Order) -> bool:
    return await send(o.email, "Открытка продлена", (
        f"Спасибо! Ссылка {card_url(o)} теперь работает до: {_date(o.expires_at)}." + SIGN))


async def send_failed_admin(o: Order, error: str) -> bool:
    return await send(settings.admin_email or None, f"[ахнуть] генерация не удалась {o.public_id[:8]}",
                      f"Заказ {order_url(o)}\nТариф: {o.tier}\nОшибка: {error}\nВремя: {datetime.now(timezone.utc).isoformat()}")
