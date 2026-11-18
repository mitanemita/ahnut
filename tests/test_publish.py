"""Этап 5: правки (2 включены + докупка), публикация, ссылка, пароль, файл, сроки, продление, письма, удаление ПДн."""
import asyncio
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app import mailer
from app import yookassa as yk
from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.models import Order
from app.publish import housekeeping
from tests.test_generation import TOKEN, paid_order  # noqa: F401  (фикстура)
from tests.test_payments import FakeYooKassa

client = TestClient(app)


@pytest.fixture
def ready(paid_order, monkeypatch):  # noqa: F811
    monkeypatch.setattr(settings, "llm_fake", True)
    mailer.SENT.clear()
    assert client.post(f"/internal/orders/{paid_order}/generate", headers=TOKEN).json()["status"] == "ready"
    return paid_order


@pytest.fixture
def yk_fake(monkeypatch):
    f = FakeYooKassa()
    monkeypatch.setattr(yk, "yookassa", yk.YooKassa(transport=httpx.MockTransport(f.handler)))
    return f


def _set(oid, **kw):
    async def go():
        async with SessionLocal() as s:
            o = (await s.execute(select(Order).where(Order.public_id == oid))).scalar_one()
            for k, v in kw.items():
                setattr(o, k, v)
            await s.commit()
    asyncio.run(go())


def _get(oid) -> Order:
    async def go():
        async with SessionLocal() as s:
            return (await s.execute(select(Order).where(Order.public_id == oid))).scalar_one()
    return asyncio.run(go())


def pay_last(f, kind_url, body, oid):
    r = client.post(f"/api/orders/{oid}/{kind_url}", json=body)
    assert r.status_code == 200, r.text
    pid = list(f.payments)[-1]
    f.succeed(pid)
    client.post("/yookassa/webhook", json={"event": "payment.succeeded", "object": {"id": pid}})
    client.post("/yookassa/webhook", json={"event": "payment.succeeded", "object": {"id": pid}})  # повтор
    return f.payments[pid]


def test_ready_email_sent(ready):
    assert any("Открытка готова" in m["subject"] for m in mailer.SENT)


def test_two_edits_included_then_buy_more(ready, yk_fake):
    for t in ("Мамуля, ты лучшая", "С праздником, мам"):
        assert client.post(f"/api/orders/{ready}/edits", json={"text": t}).status_code == 200
    assert t in client.get(f"/order/{ready}/card").text           # правка применилась
    assert client.post(f"/api/orders/{ready}/edits", json={"text": "ещё"}).status_code == 402
    page = client.get(f"/order/{ready}").text
    assert "осталось 0" in page and "+3 правки · 119 ₽" in page
    p = pay_last(yk_fake, "buy-edits", {"qty": 3}, ready)
    assert p["amount"]["value"] == "119.00"
    o = _get(ready)
    assert o.edits_bought == 3                                    # повторное уведомление не удвоило
    assert client.post(f"/api/orders/{ready}/edits", json={"text": "Третья правка"}).status_code == 200


def test_failed_edit_is_not_charged(ready, monkeypatch):
    from tests.test_generation import _mock_model
    monkeypatch.setattr(settings, "llm_fake", False)
    _mock_model(monkeypatch, ['{"broken": true}'])
    client.post(f"/api/orders/{ready}/edits", json={"text": "сломай всё"})
    o = _get(ready)
    assert o.edits_used == 0 and o.status == "ready" and "не списана" in (o.edit_error or "")


def test_revert_to_previous_version(ready):
    before = client.get(f"/order/{ready}/card").text
    client.post(f"/api/orders/{ready}/edits", json={"text": "Новый заголовок"})
    assert "Новый заголовок" in client.get(f"/order/{ready}/card").text
    client.post(f"/api/orders/{ready}/revert", json={"version": 1})
    assert client.get(f"/order/{ready}/card").text == before
    assert _get(ready).edits_used == 1                            # откат — бесплатно


def test_buy_edits_requires_known_pack(ready, yk_fake):
    assert client.post(f"/api/orders/{ready}/buy-edits", json={"qty": 100}).status_code == 422


def test_publish_with_password(ready):
    r = client.post(f"/api/orders/{ready}/publish", json={"password": "кис"}).json()
    card_id = r["card_url"].rsplit("/", 1)[-1]
    assert card_id != ready                                        # ссылка получателя ≠ ссылка управления
    assert client.get(f"/order/{card_id}").status_code == 404
    c = TestClient(app)
    assert "Нужен пароль" in c.get(f"/c/{card_id}").text
    assert c.post(f"/c/{card_id}", data={"password": "нет"}).status_code == 403
    r = c.post(f"/c/{card_id}", data={"password": "кис"})
    assert r.status_code == 200 and "Мама" in r.text and "connect-src 'none'" in r.headers["content-security-policy"]
    assert any("опубликована" in m["subject"] and card_id in m["text"] for m in mailer.SENT)
    exp = _get(ready).expires_at
    days = ((exp if exp.tzinfo else exp.replace(tzinfo=timezone.utc)) - datetime.now(timezone.utc)).days
    assert 6 <= days <= 7                                          # 1 неделя хостинга


def test_publish_without_password_and_download(ready):
    card_id = client.post(f"/api/orders/{ready}/publish", json={}).json()["card_url"].rsplit("/", 1)[-1]
    r = client.get(f"/c/{card_id}")
    assert r.status_code == 200 and "noindex" in r.headers["x-robots-tag"]
    assert f"/f/{ready}/p_" in r.text                               # по ссылке — фото файлами
    d = client.get(f"/order/{ready}/download")
    assert "attachment" in d.headers["content-disposition"]
    assert "data:image/jpeg;base64," in d.text and f"/f/{ready}/" not in d.text and "url(/static" not in d.text


def test_expiry_and_extensions(ready, yk_fake):
    card_id = client.post(f"/api/orders/{ready}/publish", json={}).json()["card_url"].rsplit("/", 1)[-1]
    _set(ready, expires_at=datetime.now(timezone.utc) - timedelta(hours=1))
    r = client.get(f"/c/{card_id}")
    assert r.status_code == 410 and "истёк" in r.text and ready not in r.text   # получатель не видит ссылку управления
    assert "Срок ссылки истёк" in client.get(f"/order/{ready}").text
    p = pay_last(yk_fake, "extend", {"period": "month"}, ready)
    assert p["amount"]["value"] == "149.00"
    exp = _get(ready).expires_at
    assert (exp if exp.tzinfo else exp.replace(tzinfo=timezone.utc)) > datetime.now(timezone.utc) + timedelta(days=29)
    assert client.get(f"/c/{card_id}").status_code == 200
    pay_last(yk_fake, "extend", {"period": "forever"}, ready)
    o = _get(ready)
    assert o.forever and o.expires_at is None
    assert client.post(f"/api/orders/{ready}/extend", json={"period": "year"}).status_code == 409


def test_reminder_and_purge(ready):
    card_id = client.post(f"/api/orders/{ready}/publish", json={}).json()["card_url"].rsplit("/", 1)[-1]
    _set(ready, expires_at=datetime.now(timezone.utc) + timedelta(hours=20))
    mailer.SENT.clear()

    async def hk():
        async with SessionLocal() as s:
            return await housekeeping(s)
    assert asyncio.run(hk())["reminders"] == 1
    assert asyncio.run(hk())["reminders"] == 0                     # одно напоминание
    assert any("Завтра" in m["subject"] for m in mailer.SENT)
    _set(ready, expires_at=datetime.now(timezone.utc) - timedelta(days=settings.purge_after_days + 1))
    assert asyncio.run(hk())["purged"] == 1
    o = _get(ready)
    assert o.purged_at and not o.photos and o.answers is None
    assert client.get(f"/c/{card_id}").status_code == 410


def test_retry_after_failed_generation(paid_order, monkeypatch):  # noqa: F811
    from tests.test_generation import _mock_model
    _mock_model(monkeypatch, ["не json"] * 3)
    assert client.post(f"/internal/orders/{paid_order}/generate", headers=TOKEN).json()["status"] == "failed"
    assert "Попробовать ещё раз" in client.get(f"/order/{paid_order}").text
    assert client.post(f"/api/orders/{paid_order}/retry").json()["status"] == "queued"


def test_legal_pages():
    offer = client.get("/offer").text
    assert "результатом труда" in offer and "не несёт ответственности за их незаконное" in offer
    assert "не возвращаются" in offer and "докупить" in offer
    assert "Трансграничная" in client.get("/privacy").text or "трансграничная" in client.get("/privacy").text


def test_admin_purge_by_email(ready):
    from app.admin import main
    asyncio.run(main(["purge", "a@example.com"]))
    assert _get(ready).purged_at is not None
