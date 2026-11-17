"""Анкеты тарифов. Сейчас — «Записка»: ~10 вопросов кнопками + 2 текстовых + 1–4 фото."""
from typing import Any

from app.cards.presets import all_presets, presets_for

THEME_BY_MOOD = {
    "warm": ("Тёплое", "cream_rose"),
    "dark": ("Тёмное, стильное", "noir_pink"),
    "bright": ("Яркое", "kraft_sun"),
    "tender": ("Нежное", "candy_sky"),
    "festive": ("Праздничное", "navy_gold"),
    "calm": ("Спокойное", "mint_fresh"),
    "lilac": ("Лавандовое", "lilac_dream"),
}

SYMBOLS = {"heart": "Сердце", "star": "Звезда", "flower": "Цветок", "sun": "Солнце",
           "snowflake": "Снежинка", "balloon": "Шарик", "gift": "Подарок"}

LOVES = {"cup": "Кофе и чай", "pizza": "Вкусно поесть", "gamepad": "Игры", "ball": "Футбол, спорт",
         "music": "Музыка", "plane": "Путешествия", "book": "Книги", "cat": "Котики", "paw": "Собаки",
         "flower": "Цветы, сад", "camera": "Фото", "guitar": "Гитара", "cake": "Сладкое", "house": "Дом, уют",
         "chess": "Настолки, шахматы", "medal": "Достижения, работа"}

TIER_LIMITS = {"zapiska": {"photos": (1, 4), "text": 2}}


def zapiska_questions(recipient: str, occasion: str) -> list[dict[str, Any]]:
    templates = presets_for(recipient, occasion) or presets_for(recipient)
    formal = recipient in ("colleague", "teacher")
    romantic = recipient == "partner"
    q: list[dict[str, Any]] = [
        {"id": "template", "kind": "choice", "title": "Шаблон открытки",
         "options": [(t, all_presets()[t]["meta"]["title"]) for t in templates], "default": templates[0] if templates else None},
        {"id": "recipient_name", "kind": "short", "title": "Как вы называете получателя?", "placeholder": "Мама, Ирина Петровна, кис…", "max": 26},
        {"id": "sender_name", "kind": "short", "title": "Как подписать открытку?", "placeholder": "Аня, твой сын, команда…", "max": 26},
        {"id": "address", "kind": "choice", "title": "Обращение", "options": [("ty", "На «ты»"), ("vy", "На «вы»")],
         "default": "vy" if formal else "ty"},
        {"id": "mood", "kind": "choice", "title": "Настроение цветов",
         "options": [(k, v[0]) for k, v in THEME_BY_MOOD.items() if romantic or k != "dark" or recipient == "friend"],
         "default": None},
        {"id": "symbol", "kind": "choice", "title": "Главный символ",
         "options": [(k, v) for k, v in SYMBOLS.items() if k != "heart" or not formal], "default": None},
        {"id": "loves", "kind": "multi", "title": "Что любит получатель? (до 4)", "options": list(LOVES.items()), "max": 4},
        {"id": "known", "kind": "choice", "title": "Сколько вы знакомы?",
         "options": [("lt1", "Меньше года"), ("1to5", "1–5 лет"), ("gt5", "Больше 5 лет"), ("life", "Всю жизнь")]},
        {"id": "humor", "kind": "choice", "title": "Шутки", "options": [("none", "Без шуток"), ("light", "Чуть-чуть"), ("more", "Побольше")],
         "default": "none" if formal else "light"},
        {"id": "length", "kind": "choice", "title": "Длина текстов", "options": [("short", "Коротко"), ("mid", "Средне"), ("long", "Подробнее")],
         "default": "mid"},
        {"id": "finale", "kind": "choice", "title": "Финал",
         "options": [("question", "Вопрос с кнопками «да/нет»"), ("words", "Просто тёплые слова")], "default": "words"},
        {"id": "message", "kind": "text", "title": "Главное, что хотите сказать", "placeholder": "Своими словами, можно с ошибками — нейросеть аккуратно перепишет", "max": 400},
        {"id": "secret", "kind": "text", "title": "Что-то только ваше", "placeholder": "Шутка, прозвище, общее воспоминание, любимое место…", "max": 300},
    ]
    return q


def validate_answers(questions: list[dict[str, Any]], answers: dict[str, Any], complete: bool) -> tuple[dict[str, Any], list[str]]:
    """Чистит ответы: только известные поля, только допустимые варианты, обрезка длины."""
    clean: dict[str, Any] = {}
    errors: list[str] = []
    for q in questions:
        v = answers.get(q["id"], q.get("default"))
        allowed = {o[0] for o in q.get("options", [])}
        if q["kind"] == "choice":
            if v in allowed:
                clean[q["id"]] = v
            elif complete:
                errors.append(f"Ответьте на вопрос «{q['title']}»")
        elif q["kind"] == "multi":
            vals = [x for x in (v or []) if x in allowed][: q.get("max", 4)]
            clean[q["id"]] = vals
        else:
            text = str(v or "").strip()[: q.get("max", 300)]
            clean[q["id"]] = text
            if complete and q["kind"] == "short" and not text:
                errors.append(f"Заполните «{q['title']}»")
    if complete and not clean.get("message"):
        errors.append("Напишите, что хотите сказать")
    return clean, errors
