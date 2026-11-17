"""Анкеты тарифов.

«Записка»  — ~10 вопросов кнопками + 2 текстом, 1–4 фото.
«Свидание» — ~20 кнопками + 5 текстом, 1–7 фото (нейросеть смотрит фото).
«Принц»    — ~30 кнопками + до 10 текстом, 1–15 фото, до 5 картинок-референсов, своя музыка.
Вопросы фильтруются по получателю: коллеге — «на вы», без романтики и т.п.
"""
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

TRAITS = {"care": "Заботливый(ая)", "funny": "Смешной(ая)", "smart": "Умный(ая)", "strong": "Сильный(ая)",
          "tender": "Нежный(ая)", "stubborn": "Упрямый(ая)", "creative": "Творческий(ая)", "sport": "Спортивный(ая)",
          "calm": "Спокойный(ая)", "leader": "Лидер", "late": "Вечно опаздывает", "foodie": "Гурман"}

PLACES = {"sea": "Море", "mountains": "Горы", "city": "Город, прогулки", "dacha": "Дача", "cafe": "Кафе",
          "cinema": "Кино", "home": "Дома на диване", "trips": "Поездки", "office": "Работа, офис", "school": "Школа, учёба"}

BLOCKS = {"envelope": "Конверт с печатью", "phone": "Телефон с нашими фото", "polaroids": "Стопка полароидов",
          "cards": "Предметы-карточки", "letter": "Письмо от руки", "quiz": "Викторина «а помнишь?»",
          "timeline": "Наша история по годам", "reasons": "«N причин, почему ты…»"}

SCENES = {"couple": "Двое тянутся к сердцу", "hug": "Обнимашки", "highfive": "Дай пять",
          "trophy": "Кубок и аплодисменты", "cake": "Торт со свечами", "gift": "Подарок открывается"}

TIER_LIMITS = {
    "zapiska": {"photos": (1, 4), "refs": 0, "music": False},
    "svidanie": {"photos": (1, 7), "refs": 0, "music": False},
    "prince": {"photos": (1, 15), "refs": 5, "music": True},
}


def _ch(id_, title, options, default=None, **kw):
    return {"id": id_, "kind": "choice", "title": title, "options": list(options), "default": default, **kw}


def _multi(id_, title, options, mx, default=None):
    return {"id": id_, "kind": "multi", "title": title, "options": list(options), "max": mx, "default": default or []}


def _short(id_, title, placeholder, mx=26):
    return {"id": id_, "kind": "short", "title": title, "placeholder": placeholder, "max": mx}


def _text(id_, title, placeholder, mx=300, required=False):
    return {"id": id_, "kind": "text", "title": title, "placeholder": placeholder, "max": mx, "required": required}


def _common(recipient: str) -> list[dict[str, Any]]:
    formal = recipient in ("colleague", "teacher")
    romantic = recipient == "partner"
    return [
        _short("recipient_name", "Как вы называете получателя?", "Мама, Ирина Петровна, кис…"),
        _short("sender_name", "Как подписать открытку?", "Аня, твой сын, команда…"),
        _ch("address", "Обращение", [("ty", "На «ты»"), ("vy", "На «вы»")], "vy" if formal else "ty"),
        _ch("mood", "Настроение цветов", [(k, v[0]) for k, v in THEME_BY_MOOD.items()
                                          if k != "dark" or recipient in ("partner", "friend", "sibling")]),
        _ch("symbol", "Главный символ", [(k, v) for k, v in SYMBOLS.items() if k != "heart" or not formal]),
        _multi("loves", "Что любит получатель?", LOVES.items(), 4),
        _ch("known", "Сколько вы знакомы?", [("lt1", "Меньше года"), ("1to5", "1–5 лет"), ("gt5", "Больше 5 лет"), ("life", "Всю жизнь")]),
        _ch("humor", "Шутки", [("none", "Без шуток"), ("light", "Чуть-чуть"), ("more", "Побольше")], "none" if formal else "light"),
        _ch("length", "Длина текстов", [("short", "Коротко"), ("mid", "Средне"), ("long", "Подробнее")], "mid"),
        _ch("finale", "Финал", [("question", "Вопрос с кнопками и убегающим «нет»"), ("words", "Просто тёплые слова")],
            "question" if romantic else "words"),
    ]


def _scenes(recipient: str) -> list[tuple[str, str]]:
    return [(k, v) for k, v in SCENES.items() if k != "couple" or recipient == "partner"]


def zapiska_questions(recipient: str, occasion: str) -> list[dict[str, Any]]:
    templates = presets_for(recipient, occasion) or presets_for(recipient)
    return (
        [_ch("template", "Шаблон открытки", [(t, all_presets()[t]["meta"]["title"]) for t in templates],
             templates[0] if templates else None)]
        + _common(recipient)
        + [_text("message", "Главное, что хотите сказать", "Своими словами, можно с ошибками — нейросеть аккуратно перепишет", 400, True),
           _text("secret", "Что-то только ваше", "Шутка, прозвище, общее воспоминание, любимое место…")]
    )


def svidanie_questions(recipient: str, occasion: str) -> list[dict[str, Any]]:
    return (
        [q for q in _common(recipient) if q["id"] != "loves"]
        + [
            _multi("loves", "Что любит получатель? (до 6)", LOVES.items(), 6),
            _multi("traits", "Какой(ая) он(а)? (до 4)", TRAITS.items(), 4),
            _multi("places", "Ваши места (до 4)", PLACES.items(), 4),
            _multi("blocks", "Что хотите в открытке? (до 5)", BLOCKS.items(), 5, ["envelope", "phone", "cards"]),
            _ch("scene", "Финальная сцена", _scenes(recipient)),
            _ch("intro", "Как начать", [("intrigue", "Интрига: «открой, там кое-что»"), ("warm", "Сразу тепло"),
                                        ("joke", "С шутки")]),
            _ch("captions", "Подписи к фото", [("ai", "Придумает нейросеть по фото"), ("short", "Коротко, 2–3 слова"),
                                               ("story", "Мини-история к каждому")], "ai"),
            _ch("emotion", "Какую реакцию хотите?", [("tears", "Растрогать"), ("laugh", "Рассмешить"),
                                                     ("both", "И то и другое"), ("proud", "Чтобы гордился(ась)")]),
            _ch("emoji", "Смайлики в тексте", [("no", "Без смайликов"), ("few", "Немного")], "no"),
            _ch("decor", "Что «растёт» на фоне от нажатий", [("flowers", "Цветы"), ("stars", "Звёзды"), ("snow", "Снежинки"),
                                                           ("balloons", "Шарики"), ("none", "Ничего")], "flowers"),
            _ch("nickname", "Обращаться по прозвищу?", [("yes", "Да, по прозвищу"), ("no", "По имени")], "yes"),
            _ch("easter", "Спрятать пасхалку-шутку", [("yes", "Да"), ("no", "Не нужно")], "yes"),
            _short("special_time", "Время, которое что-то значит (для экрана телефона)", "напр. 18:50", 5),
            _text("message", "Главное, что хотите сказать", "Своими словами — нейросеть перепишет красиво", 500, True),
            _text("secret", "Ваши шутки и прозвища", "«дос/кис», «надень шапку», как вы друг друга называете…"),
            _text("memory", "Общее воспоминание", "Где, когда, что было — можно несколько"),
            _text("wish", "Пожелание или обещание", "Чего желаете, что обещаете"),
            _text("avoid", "Чего точно НЕ писать", "Темы, слова, имена, которые лучше не упоминать", 200),
        ]
    )


def prince_questions(recipient: str, occasion: str) -> list[dict[str, Any]]:
    base = [q for q in svidanie_questions(recipient, occasion) if q["id"] not in ("blocks",)]
    return base + [
        _multi("blocks", "Готовые блоки, которые хотите (до 6)", BLOCKS.items(), 6, ["envelope", "phone"]),
        _ch("realism", "Стиль", [("real", "Максимальный реализм"), ("semi", "Полуреализм"), ("illu", "Иллюстрация")], "real"),
        _ch("motion", "Анимации", [("calm", "Спокойные"), ("rich", "Много движения"), ("wow", "Вау-эффекты")], "rich"),
        _ch("interactive", "Сколько нажимать", [("few", "Немного"), ("many", "Много сюрпризов"), ("game", "Как мини-игра")], "many"),
        _ch("custom_count", "Своих сцен, нарисованных с нуля", [("1", "Одна"), ("2", "Две"), ("3", "Три")], "2"),
        _ch("secret_end", "Тайный финал", [("yes", "Да, спрятать сюрприз"), ("no", "Не нужно")], "yes"),
        _ch("music", "Музыка", [("own", "Своя (загружу файл)"), ("none", "Без музыки")], "none"),
        _ch("pace", "Темп", [("slow", "Неспешно"), ("mid", "Средне"), ("fast", "Динамично")], "mid"),
        _ch("palette_own", "Цвета", [("theme", "Как в выбранном настроении"), ("own", "Свои цвета (ниже)")], "theme"),
        {"id": "color1", "kind": "color", "title": "Свой главный цвет", "default": "#e2b34a"},
        {"id": "color2", "kind": "color", "title": "Свой второй цвет", "default": "#ffe7a3"},
        _text("story", "Ваша история подробно", "Как познакомились, что прошли вместе, чем живёте", 1200),
        _text("scene_idea", "Идея своей сцены", "Например: «звёздное небо, где звёзды складываются в наши инициалы»", 500),
        _text("unique", "Что делает вас особенными", "То, чего нет ни у кого другого"),
        _text("details", "Мелкие детали", "Любимый цвет, запах, песня, фраза, привычка", 400),
        _text("refs_note", "Что взять из картинок-референсов", "Цвета, настроение, конкретный предмет…", 200),
    ]


QUESTIONS = {"zapiska": zapiska_questions, "svidanie": svidanie_questions, "prince": prince_questions}


def questions_for(tier: str, recipient: str, occasion: str) -> list[dict[str, Any]]:
    return QUESTIONS[tier](recipient, occasion)


def count_kinds(questions: list[dict[str, Any]]) -> tuple[int, int]:
    buttons = sum(q["kind"] in ("choice", "multi", "color") for q in questions)
    texts = sum(q["kind"] == "text" for q in questions)
    return buttons, texts


def validate_answers(questions: list[dict[str, Any]], answers: dict[str, Any], complete: bool) -> tuple[dict[str, Any], list[str]]:
    """Чистит ответы: только известные поля, только допустимые варианты, обрезка длины."""
    import re
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
            clean[q["id"]] = [x for x in (v or []) if x in allowed][: q.get("max", 4)]
        elif q["kind"] == "color":
            clean[q["id"]] = v if isinstance(v, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", v) else q.get("default")
        else:
            text = str(v or "").strip()[: q.get("max", 300)]
            clean[q["id"]] = text
            if complete and (q["kind"] == "short" and q["id"] != "special_time" or q.get("required")) and not text:
                errors.append(f"Заполните «{q['title']}»")
    return clean, errors
