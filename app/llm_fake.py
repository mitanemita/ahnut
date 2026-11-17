"""Поддельная «нейросеть» для разработки (LLM_FAKE=true): без сети, подставляет ответы анкеты в шаблон/пример.
Проверку оплаты не обходит — вызывается из llm.generate уже после неё."""
import copy
import json
import re

from pydantic import BaseModel

from app.models import Order


def _names(tpl: dict, order: Order) -> dict:
    a = order.answers or {}
    to, frm, msg = a.get("recipient_name", ""), a.get("sender_name", ""), a.get("message", "")
    n = max(1, len(order.photos or []))
    for b in tpl["blocks"]:
        if b["type"] == "hero":
            b["from_label"], b["to_label"] = f"от: {frm}"[:26], f"для: {to}"[:26]
        if b["type"] == "envelope":
            b["to_tag"] = f"для: {to}"[:26]
        if b["type"] == "letter" and msg:
            b["text"], b["signature"] = msg[:700], frm[:40]
        if b["type"] == "final" and msg and not b.get("finale"):
            b["finale"] = msg[:80]
        if b["type"] == "phone":
            b["slides"] = [{"photo": i, "caption": ""} for i in range(n)]
        if b["type"] == "polaroids":
            b["items"] = [{"photo": i, "caption": ""} for i in range(n)]
    return tpl


def generate(order: Order, content: list[dict], model_cls: type[BaseModel]) -> dict:
    text = content[0]["text"]
    m = re.search(r"<template>\n(.*)\n</template>", text, re.S)
    if m:
        return _names(json.loads(m.group(1)), order)
    if model_cls.__name__ == "Review":
        return {"verdict": "ok", "problems": [], "spec": None}
    from app.cards.presets import all_examples
    name = "prince_anniversary" if order.tier == "prince" else "svidanie_friend"
    tpl = copy.deepcopy(all_examples()[name]["spec"])
    if order.recipient != "partner":
        for b in tpl["blocks"]:
            if b["type"] == "final" and b["scene"] == "couple":
                b["scene"] = "hug"
    if order.tier == "prince":  # фото в примере на «телефоне» — гарантируем, что все фото показаны
        tpl["blocks"].insert(3, {"type": "polaroids", "step": "архив", "items": []})
        want = int((order.answers or {}).get("custom_count") or 1)
        custom = next(b for b in tpl["blocks"] if b["type"] == "custom")
        for _ in range(want - 1):
            tpl["blocks"].insert(4, copy.deepcopy(custom))
    return _names(tpl, order)
