"""Этап 2: оплата через ЮKassa. Главное правило — без подтверждённой оплаты генерация невозможна."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app import generation, llm
from app import yookassa as yk
from app.main import app

client = TestClient(app)


class FakeYooKassa:
    """Имитация API ЮKassa: хранит платежи, статус меняется только «на стороне ЮKassa»."""

    def __init__(self):
        self.payments: dict[str, dict] = {}
        self.created = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith("/payments"):
            body = json.loads(request.content)
            assert request.headers.get("Idempotence-Key")
            pid = f"pay-{len(self.payments) + 1}"
            p = {"id": pid, "status": "pending", "paid": False, "amount": body["amount"],
                 "metadata": body["metadata"], "description": body["description"],
                 "confirmation": {"type": "redirect", "confirmation_url": f"https://yoomoney.example/{pid}"}}
            self.payments[pid] = p
            self.created.append(body)
            return httpx.Response(200, json=p)
        if request.method == "GET":
            pid = request.url.path.rsplit("/", 1)[-1]
            p = self.payments.get(pid)
            return httpx.Response(200, json=p) if p else httpx.Response(404, json={})
        return httpx.Response(400)

    def succeed(self, pid, value=None):
        p = self.payments[pid]
        p.update(status="succeeded", paid=True)
        if value:
            p["amount"] = {"value": value, "currency": "RUB"}


@pytest.fixture
def fake(monkeypatch):
    f = FakeYooKassa()
    monkeypatch.setattr(yk, "yookassa", yk.YooKassa(transport=httpx.MockTransport(f.handler)))
    return f


@pytest.fixture
def pipeline_calls(monkeypatch):
    calls = []

    async def fake_notify(order):
        calls.append(order.public_id)

    monkeypatch.setattr(generation, "notify_pipeline", fake_notify)
    return calls


@pytest.fixture
def llm_calls(monkeypatch):
    calls = []

    async def fake_create(*a, **kw):
        calls.append(kw)
        raise AssertionError("нейросеть не должна вызываться")

    class FakeClient:
        class messages:  # noqa: N801
            create = staticmethod(fake_create)

    monkeypatch.setattr(llm, "_client", lambda: FakeClient())
    return calls


def new_order(tier="zapiska", recipient="parent", occasion="birthday", tone="family"):
    r = client.post("/api/orders", json={"tier": tier, "recipient": recipient, "occasion": occasion, "tone": tone})
    assert r.status_code == 200, r.text
    return r.json()


def fill_answers(oid, complete=True):
    return client.put(f"/api/orders/{oid}/answers",
                      json={"answers": {"name": "мама"}, "complete": complete, "pd_consent": True})


def webhook(pid, event="payment.succeeded", body_status="succeeded"):
    return client.post("/yookassa/webhook", json={"type": "notification", "event": event,
                                                   "object": {"id": pid, "status": body_status}})


def pay(oid):
    r = client.post(f"/api/orders/{oid}/pay", json={"email": "test@example.com"})
    assert r.status_code == 200, r.text
    return r.json()


# ---------- выбор ----------

def test_price_comes_from_catalog():
    assert new_order("zapiska")["amount_rub"] == 390
    assert new_order("svidanie")["amount_rub"] == 990
    assert new_order("prince")["amount_rub"] == 2490


def test_romantic_occasion_rejected_for_colleague():
    r = client.post("/api/orders", json={"tier": "zapiska", "recipient": "colleague",
                                         "occasion": "proposal", "tone": "business"})
    assert r.status_code == 422


def test_romantic_tone_rejected_for_mom():
    r = client.post("/api/orders", json={"tier": "zapiska", "recipient": "parent",
                                         "occasion": "birthday", "tone": "romantic"})
    assert r.status_code == 422


# ---------- оплата ----------

def test_create_payment_sends_correct_amount(fake):
    o = new_order("svidanie", recipient="friend", tone="friendly")
    res = pay(o["order_id"])
    assert res["confirmation_url"].startswith("https://")
    sent = fake.created[0]
    assert sent["amount"] == {"value": "990.00", "currency": "RUB"}
    assert sent["metadata"]["order_id"] == o["order_id"]
    assert sent["confirmation"]["return_url"].endswith(f"/order/{o['order_id']}")
    assert res["status"] == "awaiting_payment" and res["paid"] is False


def test_forged_webhook_does_not_mark_paid(fake, pipeline_calls):
    """Тело уведомления говорит «succeeded», но API ЮKassa — «pending»: не верим телу."""
    o = new_order()
    fill_answers(o["order_id"])
    p = pay(o["order_id"])
    pid = list(fake.payments)[0]
    webhook(pid)
    st = client.get(f"/api/orders/{o['order_id']}").json()
    assert st["paid"] is False and pipeline_calls == []
    assert p["paid"] is False


def test_unknown_payment_webhook_ignored(fake, pipeline_calls):
    assert webhook("pay-does-not-exist").status_code == 200
    assert pipeline_calls == []


def test_amount_mismatch_not_paid(fake, pipeline_calls):
    o = new_order()
    fill_answers(o["order_id"])
    pay(o["order_id"])
    pid = list(fake.payments)[0]
    fake.succeed(pid, value="1.00")
    webhook(pid)
    assert client.get(f"/api/orders/{o['order_id']}").json()["paid"] is False
    assert pipeline_calls == []


def test_answers_then_payment_starts_generation_once(fake, pipeline_calls):
    o = new_order()
    fill_answers(o["order_id"])
    assert pipeline_calls == []  # анкета есть, оплаты нет — ничего не запускаем
    pay(o["order_id"])
    pid = list(fake.payments)[0]
    fake.succeed(pid)
    webhook(pid)
    webhook(pid)  # ЮKassa может прислать повторно
    st = client.get(f"/api/orders/{o['order_id']}").json()
    assert st["paid"] is True and st["status"] == "queued"
    assert pipeline_calls == [o["order_id"]]


def test_payment_then_answers_starts_generation(fake, pipeline_calls):
    o = new_order()
    pay(o["order_id"])
    pid = list(fake.payments)[0]
    fake.succeed(pid)
    webhook(pid)
    st = client.get(f"/api/orders/{o['order_id']}").json()
    assert st["paid"] is True and st["status"] == "paid" and pipeline_calls == []
    fill_answers(o["order_id"])
    assert pipeline_calls == [o["order_id"]]


def test_return_from_payment_checks_api_not_redirect(fake, pipeline_calls):
    """Вебхук не дошёл, пользователь вернулся на страницу заказа — статус берём из API."""
    o = new_order()
    pay(o["order_id"])
    r = client.get(f"/order/{o['order_id']}")
    assert "Ждём подтверждение оплаты" in r.text
    fake.succeed(list(fake.payments)[0])
    r = client.get(f"/order/{o['order_id']}")
    assert "Оплата прошла" in r.text


def test_answers_require_pd_consent():
    o = new_order()
    r = client.put(f"/api/orders/{o['order_id']}/answers",
                   json={"answers": {"x": 1}, "complete": True, "pd_consent": False})
    assert r.status_code == 422


def test_webhook_from_foreign_ip_rejected(monkeypatch, fake):
    from app.config import settings
    monkeypatch.setattr(settings, "yookassa_check_ip", True)
    assert webhook("pay-1").status_code == 403  # testclient = не IP ЮKassa
    assert yk.is_yookassa_ip("185.71.76.5") and not yk.is_yookassa_ip("8.8.8.8")


# ---------- генерация без оплаты невозможна ----------

def test_internal_generate_refuses_unpaid(llm_calls):
    o = new_order()
    fill_answers(o["order_id"])
    r = client.post(f"/internal/orders/{o['order_id']}/generate", headers={"X-Internal-Token": "test-internal"})
    assert r.status_code == 402
    assert llm_calls == []


def test_internal_generate_requires_token():
    o = new_order()
    assert client.post(f"/internal/orders/{o['order_id']}/generate").status_code == 403
    assert client.post(f"/internal/orders/{o['order_id']}/generate",
                       headers={"X-Internal-Token": "wrong"}).status_code == 403


@pytest.mark.asyncio
async def test_llm_module_refuses_unpaid_order(llm_calls):
    from app.models import Order
    with pytest.raises(llm.UnpaidOrderError):
        await llm.generate_json(Order(tier="zapiska", paid=False, public_id="x"),
                                system="s", content=[{"type": "text", "text": "секрет"}], schema={})
    assert llm_calls == []
