"""Справочники: тарифы, получатели, тоны, поводы. Единственный источник цен для оплаты."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Tier:
    slug: str
    title: str
    price_rub: int
    max_photos: int
    music: bool


TIERS: dict[str, Tier] = {
    "zapiska": Tier("zapiska", "Записка", 390, 4, False),
    "svidanie": Tier("svidanie", "Свидание", 990, 7, False),
    "prince": Tier("prince", "Принц", 2490, 15, True),
}

# Хостинг ссылки, входящий в любой тариф
HOSTING_DAYS = 7
# Продление хостинга: период → (цена, дней; None — навсегда)
EXTENSIONS: dict[str, tuple[int, int | None]] = {"month": (149, 30), "year": (490, 365), "forever": (990, None)}
EXTENSION_TITLES = {"month": "месяц", "year": "год", "forever": "навсегда"}

# Правки: 2 входят в тариф, дальше — докупаются. Цена зависит от тарифа (у «Принца» правка дороже:
# каждая проходит самопроверку в браузере). Пакеты: количество → цена, ₽.
EDITS_INCLUDED = 2
EDIT_PACKS: dict[str, dict[int, int]] = {
    "zapiska": {1: 49, 3: 119},
    "svidanie": {1: 99, 3: 249},
    "prince": {1: 199, 3: 499},
}

RECIPIENTS = {
    "partner": "Вторая половинка",
    "parent": "Мама / папа",
    "grandparent": "Бабушка / дедушка",
    "friend": "Друг / подруга",
    "sibling": "Брат / сестра",
    "child": "Ребёнок",
    "colleague": "Коллега / начальник",
    "teacher": "Учитель / наставник",
    "other": "Другое",
}
ROMANTIC_RECIPIENTS = {"partner"}

TONES = {
    "romantic": "Романтичный",
    "family": "Тёплый семейный",
    "friendly": "Дружеский с подколами",
    "funny": "Смешной / абсурдный",
    "solemn": "Торжественный",
    "business": "Деловой, но душевный",
}

# Повод → для кого допустим (None = для всех)
_ALL = None
OCCASIONS: dict[str, tuple[str, set[str] | None]] = {
    "birthday": ("День рождения", _ALL),
    "new_year": ("Новый год", _ALL),
    "sorry": ("Извинение", _ALL),
    "thanks": ("Спасибо", _ALL),
    "just_because": ("Просто так", _ALL),
    "miss_you": ("Скучаю", _ALL),
    "get_well": ("Выздоравливай", _ALL),
    "support": ("Поддержка в трудный момент", _ALL),
    "success": ("Поздравление с успехом", _ALL),
    "graduation": ("Выпускной", _ALL),
    "housewarming": ("Новоселье", _ALL),
    "newborn": ("Рождение ребёнка", _ALL),
    "wedding_guest": ("Свадьба", _ALL),
    "jubilee": ("Юбилей", _ALL),
    "retirement": ("Проводы на пенсию", _ALL),
    "anniversary": ("Годовщина / месяц вместе", {"partner"}),
    "valentine": ("14 февраля", {"partner"}),
    "proposal": ("Предложение руки и сердца", {"partner"}),
    "date_invite": ("Приглашение на свидание", {"partner"}),
    "wedding_anniversary": ("Годовщина свадьбы", {"partner", "parent", "grandparent"}),
    "march8": ("8 марта", _ALL),
    "feb23": ("23 февраля", _ALL),
    "mothers_day": ("День матери", {"parent", "grandparent", "other"}),
    "fathers_day": ("День отца", {"parent", "grandparent", "other"}),
    "teachers_day": ("День учителя", {"teacher"}),
    "corporate": ("Корпоративное поздравление", {"colleague"}),
}

# Какие тоны уместны для получателя (романтика — только паре)
FORBIDDEN_TONES = {r: {"romantic"} for r in RECIPIENTS if r not in ROMANTIC_RECIPIENTS}


def occasions_for(recipient: str) -> dict[str, str]:
    return {k: title for k, (title, allowed) in OCCASIONS.items() if allowed is None or recipient in allowed}


def tones_for(recipient: str) -> dict[str, str]:
    banned = FORBIDDEN_TONES.get(recipient, set())
    return {k: v for k, v in TONES.items() if k not in banned}


def validate_choice(tier: str, recipient: str, occasion: str, tone: str) -> str | None:
    """Возвращает текст ошибки или None."""
    if tier not in TIERS:
        return "Неизвестный тариф"
    if recipient not in RECIPIENTS:
        return "Неизвестный получатель"
    if occasion not in occasions_for(recipient):
        return "Этот повод не подходит для выбранного получателя"
    if tone not in tones_for(recipient):
        return "Этот тон не подходит для выбранного получателя"
    return None
