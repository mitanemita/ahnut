"""Этап 3: библиотека блоков и шаблоны «Записки»."""
import re

import pytest
from fastapi.testclient import TestClient

from app.cards.presets import all_presets, preset_spec, presets_for
from app.cards.render import render
from app.cards.spec import CardSpec
from app.main import app

PHOTOS = ["/static/demo/photo0.jpg", "/static/demo/photo1.jpg"]


@pytest.mark.parametrize("name", sorted(all_presets()))
def test_every_preset_renders(name):
    meta = all_presets()[name]["meta"]
    html = render(preset_spec(name), PHOTOS, recipient=meta["recipients"][0])
    assert html.startswith("<!doctype html>")
    # уроки первой открытки
    assert "feTurbulence" not in html, "тяжёлые SVG-фильтры подвешивают iPhone"
    assert "background-clip:text" not in html.replace(" ", "")
    assert "skew" not in html, "skew на широких элементах даёт горизонтальную прокрутку"
    # никаких внешних ресурсов (Google Fonts и т.п.) — только наш сервер
    assert not re.search(r"(src|href)=\"https?://", html)
    assert "fonts.googleapis" not in html
    # фото — файлами, а не base64 внутри HTML ссылки
    assert "data:image/jpeg" not in html


def test_preset_metadata_matches_catalog():
    from app.catalog import OCCASIONS, RECIPIENTS, TONES
    for name, p in all_presets().items():
        m = p["meta"]
        assert set(m["recipients"]) <= set(RECIPIENTS), name
        assert set(m["occasions"]) <= set(OCCASIONS), name
        assert set(m["tones"]) <= set(TONES), name


def test_each_recipient_has_a_template():
    for r in ("partner", "parent", "grandparent", "friend", "sibling", "child", "colleague", "teacher"):
        assert presets_for(r), r


def test_romance_never_reaches_non_partner():
    spec = preset_spec("partner_sorry")
    data = spec.model_dump()
    data["blocks"][2]["wallpaper_icon"] = "ring"
    spec = CardSpec.model_validate(data)
    for who in ("parent", "colleague", "child", "friend"):
        html = render(spec, PHOTOS, recipient=who)
        assert 'class="person pl"' not in html  # сцена «пара» заменена
        assert 'class="person hl"' in html      # на «обнимашки»
        assert "#i-ring" not in html
    assert 'class="person pl"' in render(spec, PHOTOS, recipient="partner")


def test_user_text_is_escaped():
    data = preset_spec("mom_birthday").model_dump()
    data["blocks"][1]["title"] = "<script>alert(1)</script>"
    html = render(CardSpec.model_validate(data), PHOTOS, recipient="parent")
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html


def test_download_version_is_self_contained():
    html = render(preset_spec("mom_birthday"), PHOTOS, recipient="parent", inline=True)
    assert "url(/static/fonts" not in html and "data:font/woff2;base64," in html


def test_spec_limits_rejected():
    data = preset_spec("mom_birthday").model_dump()
    data["blocks"][1]["title"] = "x" * 500
    with pytest.raises(Exception):
        CardSpec.model_validate(data)
    data = preset_spec("mom_birthday").model_dump()
    data["accent"] = "red; background:url(//evil)"
    with pytest.raises(Exception):
        CardSpec.model_validate(data)


def test_missing_photo_gets_placeholder():
    html = render(preset_spec("partner_sorry"), [], recipient="partner")
    assert 'class="ph"' in html


def test_demo_route():
    c = TestClient(app)
    assert c.get("/demo/new_year").status_code == 200
    assert c.get("/demo/nope").status_code == 404
