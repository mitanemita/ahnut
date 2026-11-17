"""Поддельная «нейросеть» для разработки (LLM_FAKE=true): без сети, подставляет ответы анкеты в шаблон.
Проверку оплаты не обходит — вызывается из llm.generate уже после неё."""
import json
import re

from pydantic import BaseModel

from app.models import Order


def generate(order: Order, content: list[dict], model_cls: type[BaseModel]) -> BaseModel:
    text = content[0]["text"]
    tpl = json.loads(re.search(r"<template>\n(.*)\n</template>", text, re.S).group(1))
    a = order.answers or {}
    to, frm, msg = a.get("recipient_name", ""), a.get("sender_name", ""), a.get("message", "")
    for b in tpl["blocks"]:
        if b["type"] == "hero":
            b["from_label"], b["to_label"] = (f"от: {frm}")[:26], (f"для: {to}")[:26]
        if b["type"] == "envelope":
            b["to_tag"] = f"для: {to}"[:26]
        if b["type"] == "letter" and msg:
            b["text"] = msg[:700]
            b["signature"] = frm[:40]
        if b["type"] == "final" and msg and not b.get("finale"):
            b["finale"] = msg[:80]
        if b["type"] == "phone":
            b["slides"] = [{"photo": i, "caption": ""} for i in range(max(1, len(order.photos or [])))]
    return model_cls.model_validate(tpl)
