"""Этап 4: анкета «Записки», фото, генерация JSON → сборка → предпросмотр."""
import io
import json

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import generation, llm
from app import yookassa as yk
from app.cards.presets import preset_spec
from app.cards.spec import CardSpec
from app.config import settings
from app.main import app
from tests.test_payments import VALID, FakeYooKassa, jpeg_bytes, new_order

client = TestClient(app)
TOKEN = {"X-Internal-Token": "test-internal"}


@pytest.fixture(autouse=True)
def no_pipeline(monkeypatch):
    calls = []

    async def fake_notify(order):
        calls.append(order.public_id)

    monkeypatch.setattr(generation, "notify_pipeline", fake_notify)
    return calls


@pytest.fixture
def paid_order(monkeypatch):
    """Оплаченный заказ с анкетой и двумя фото (оплата подтверждена «через API ЮKassa»)."""
    f = FakeYooKassa()
    monkeypatch.setattr(yk, "yookassa", yk.YooKassa(transport=httpx.MockTransport(f.handler)))
    o = new_order("zapiska", recipient="parent", occasion="birthday", tone="family")
    oid = o["order_id"]
    for c in ((200, 80, 90), (90, 120, 200)):
        client.post(f"/api/orders/{oid}/photos", files={"file": ("a.jpg", jpeg_bytes(c), "image/jpeg")})
    r = client.put(f"/api/orders/{oid}/answers", json={"answers": {**VALID, "template": "mom_birthday"},
                                                        "complete": True, "pd_consent": True})
    assert r.status_code == 200, r.text
    client.post(f"/api/orders/{oid}/pay", json={"email": "a@example.com"})
    pid = list(f.payments)[0]
    f.succeed(pid)
    client.post("/yookassa/webhook", json={"event": "payment.succeeded", "object": {"id": pid}})
    assert client.get(f"/api/orders/{oid}").json()["status"] == "queued"
    return oid


# ---------- фото ----------

def test_photo_is_resized_and_exif_removed():
    o = new_order()
    im = Image.new("RGB", (4000, 3000), (10, 20, 30))
    exif = Image.Exif()
    exif[0x010F] = "SecretPhone"  # производитель; GPS удаляется тем же способом
    exif[0x0131] = "geo:55.75,37.61"
    buf = io.BytesIO()
    im.save(buf, "JPEG", exif=exif)
    r = client.post(f"/api/orders/{o['order_id']}/photos", files={"file": ("big.jpg", buf.getvalue(), "image/jpeg")})
    name = r.json()["photos"][0]
    got = Image.open(io.BytesIO(client.get(f"/f/{o['order_id']}/{name}").content))
    assert max(got.size) <= 1280
    assert not got.getexif()


def test_not_an_image_rejected():
    o = new_order()
    r = client.post(f"/api/orders/{o['order_id']}/photos", files={"file": ("x.jpg", b"not an image", "image/jpeg")})
    assert r.status_code == 422


def test_photo_limit_for_zapiska():
    o = new_order()
    for _ in range(4):
        assert client.post(f"/api/orders/{o['order_id']}/photos", files={"file": ("a.jpg", jpeg_bytes(), "image/jpeg")}).status_code == 200
    assert client.post(f"/api/orders/{o['order_id']}/photos", files={"file": ("a.jpg", jpeg_bytes(), "image/jpeg")}).status_code == 422


def test_photo_path_traversal_blocked():
    o = new_order()
    assert client.get(f"/f/{o['order_id']}/..%2F..%2Fetc%2Fpasswd").status_code == 404


# ---------- анкета ----------

def test_answers_need_photo_and_message():
    o = new_order()
    r = client.put(f"/api/orders/{o['order_id']}/answers", json={"answers": VALID, "complete": True, "pd_consent": True})
    assert r.status_code == 422 and "фото" in r.json()["detail"]
    client.post(f"/api/orders/{o['order_id']}/photos", files={"file": ("a.jpg", jpeg_bytes(), "image/jpeg")})
    r = client.put(f"/api/orders/{o['order_id']}/answers",
                   json={"answers": {**VALID, "message": ""}, "complete": True, "pd_consent": True})
    assert r.status_code == 422


def test_answers_cleaned_to_known_options():
    o = new_order(recipient="colleague", occasion="thanks", tone="business")
    r = client.put(f"/api/orders/{o['order_id']}/answers",
                   json={"answers": {**VALID, "mood": "evil", "loves": ["cup", "ring", "x"], "junk": "y" * 9999}}).json()
    assert r["answers_complete"] is False
    page = client.get(f"/order/{o['order_id']}/form").text
    assert 'value="Мама"' in page and "y" * 500 not in page
    assert "Коллеге: спасибо" in page
    assert "На «вы»" in page


def test_form_hides_romantic_templates_for_mom():
    o = new_order()
    page = client.get(f"/order/{o['order_id']}/form").text
    assert "Паре: извинение" not in page and "Маме: день рождения" in page


# ---------- генерация ----------

def test_generation_with_fake_llm_builds_preview(paid_order, monkeypatch):
    monkeypatch.setattr(settings, "llm_fake", True)
    assert client.get(f"/order/{paid_order}/card").status_code == 404  # ещё не готово
    r = client.post(f"/internal/orders/{paid_order}/generate", headers=TOKEN)
    assert r.status_code == 200 and r.json()["status"] == "ready", r.text
    html = client.get(f"/order/{paid_order}/card").text
    assert "Мама" in html and "Аня" in html
    assert html.count('class="slide"') == 2  # слайдов столько, сколько фото
    assert f"/f/{paid_order}/p_" in html     # фото — файлами по ссылке
    assert "Готово" in client.get(f"/order/{paid_order}").text


def _mock_model(monkeypatch, replies: list[str]):
    sent = []

    class Block:
        def __init__(self, t):
            self.type, self.text = "text", t

    class Usage:
        input_tokens, output_tokens = 3000, 1500

        def model_dump(self):
            return {}

    class Resp:
        def __init__(self, t):
            self.content, self.stop_reason, self.usage = [Block(t)], "end_turn", Usage()

    class Stream:
        def __init__(self, kw):
            sent.append(kw)
            self.r = Resp(replies[min(len(sent) - 1, len(replies) - 1)])

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get_final_message(self):
            return self.r

    class C:
        class messages:  # noqa: N801
            pass
    C.messages.stream = staticmethod(lambda **kw: Stream(kw))
    monkeypatch.setattr(llm, "_client", lambda: C())
    return sent


def test_real_llm_path_valid_json(paid_order, monkeypatch):
    spec = preset_spec("mom_birthday").model_dump()
    spec["blocks"][1]["title"] = "Мамуля, с праздником!"
    sent = _mock_model(monkeypatch, [json.dumps(spec, ensure_ascii=False)])
    r = client.post(f"/internal/orders/{paid_order}/generate", headers=TOKEN).json()
    assert r["status"] == "ready" and r["usage"]["output_tokens"] == 1500
    kw = sent[0]
    # в нейросеть ушёл только текст анкеты, без фото
    assert all(c["type"] == "text" for c in kw["messages"][0]["content"])
    assert "пироги по воскресеньям" in kw["messages"][0]["content"][0]["text"]
    assert "maxLength" not in json.dumps(kw["output_config"]["format"]["schema"])
    assert "Мамуля, с праздником!" in client.get(f"/order/{paid_order}/card").text


def test_real_llm_retries_then_fails_on_broken_structure(paid_order, monkeypatch):
    bad = preset_spec("partner_sorry").model_dump()  # другая структура блоков
    sent = _mock_model(monkeypatch, [json.dumps(bad), "не json", json.dumps(bad)])
    r = client.post(f"/internal/orders/{paid_order}/generate", headers=TOKEN).json()
    assert r["status"] == "failed"
    assert len(sent) == 1  # структура проверяется после валидации — повтор не помогает, сразу failed


def test_real_llm_fixes_invalid_json_on_retry(paid_order, monkeypatch):
    good = preset_spec("mom_birthday").model_dump()
    broken = {**good, "theme": "no_such_theme"}
    sent = _mock_model(monkeypatch, [json.dumps(broken), json.dumps(good)])
    r = client.post(f"/internal/orders/{paid_order}/generate", headers=TOKEN).json()
    assert r["status"] == "ready" and len(sent) == 2
    assert "не прошёл проверку" in sent[1]["messages"][-1]["content"]


def test_romance_stripped_even_if_model_adds_it(paid_order, monkeypatch):
    spec = preset_spec("mom_birthday").model_dump()
    spec["blocks"][-2]["scene"] = "couple"
    spec["symbol"] = "ring"
    _mock_model(monkeypatch, [json.dumps(spec)])
    client.post(f"/internal/orders/{paid_order}/generate", headers=TOKEN)
    html = client.get(f"/order/{paid_order}/card").text
    assert 'class="person pl"' not in html and "#i-ring" not in html


def test_strict_schema_is_supported_subset():
    sch = json.dumps(llm.strict_schema(CardSpec))
    for k in ("maxLength", "minItems", "maxItems", "discriminator", '"default"'):
        assert k not in sch

    def walk(n):
        if isinstance(n, dict):
            if n.get("type") == "object" and "properties" in n:
                assert n.get("additionalProperties") is False
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    walk(llm.strict_schema(CardSpec))


def test_wizard_pages_render():
    assert "Кому дарим?" in client.get("/new").text
    assert client.get("/api/catalog?recipient=colleague").json()["occasions"].get("proposal") is None
