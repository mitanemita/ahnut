"""Шаблоны «Записки»: готовая структура блоков, нейросеть переписывает тексты и подбирает цвета."""
import json
from functools import lru_cache
from pathlib import Path

from app.cards.spec import CardSpec

DIR = Path(__file__).parent / "presets"


@lru_cache
def all_presets() -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text()) for p in sorted(DIR.glob("*.json"))}


def preset_spec(name: str) -> CardSpec:
    return CardSpec.model_validate(all_presets()[name]["spec"])


def presets_for(recipient: str, occasion: str | None = None) -> list[str]:
    out = []
    for name, p in all_presets().items():
        m = p["meta"]
        if recipient in m["recipients"] and (occasion is None or occasion in m["occasions"]):
            out.append(name)
    return out
