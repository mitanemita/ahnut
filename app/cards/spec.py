"""Структура открытки (JSON). Её отдаёт нейросеть, правки меняют её же, сервер по ней собирает HTML."""
import re
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, field_validator

from app.cards.icons import ICON_NAMES
from app.cards.themes import THEME_NAMES

IconName = Literal[tuple(ICON_NAMES)]  # type: ignore[valid-type]
ThemeName = Literal[tuple(THEME_NAMES)]  # type: ignore[valid-type]
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def S(n: int):  # noqa: N802 — короткая строка с лимитом длины
    return Annotated[str, Field(max_length=n)]


class Envelope(BaseModel):
    type: Literal["envelope"] = "envelope"
    teaser: S(40) = Field(description="Строка, которая «печатается» над конвертом")
    letter_title: S(22)
    letter_sub: S(22) = ""
    to_tag: S(26) = Field(description="Надпись на конверте, напр. «ДЛЯ МАМЫ»")
    seal_icon: IconName = "heart"


class Hero(BaseModel):
    type: Literal["hero"] = "hero"
    title: S(48)
    from_label: S(26) = ""
    to_label: S(26) = ""
    icon: IconName = "heart"


class PhotoSlide(BaseModel):
    photo: int = Field(ge=0, description="Номер фото из загруженных (с нуля)")
    caption: S(48) = ""


class Phone(BaseModel):
    type: Literal["phone"] = "phone"
    step: S(30) = ""
    lock_time: S(5) = "18:50"
    lock_date: S(30) = ""
    notif_from: S(26) = ""
    notif_text: S(60) = ""
    unlock_hint: S(20) = "сдвинь вправо"
    unlock_sub: S(24) = ""
    wallpaper_icon: IconName = "heart"
    slides: list[PhotoSlide] = Field(min_length=1, max_length=15)


class CardItem(BaseModel):
    kind: Literal["icon", "word", "ticket"] = "icon"
    icon: IconName = "star"
    effect: Literal["burst", "spin", "shake", "flip"] = "burst"
    line: S(30) = Field("", description="Крупная подпись (курсив)")
    label: S(24) = Field("", description="Мелкая подпись капслоком")
    back: S(90) = Field("", description="Текст на обороте (для effect=flip)")
    word_from: S(14) = Field("", description="kind=word: слово, которое зачёркивается")
    word_to: S(14) = Field("", description="kind=word: слово, которое появляется")
    t_kicker: S(36) = ""
    t_title: S(26) = ""
    t_sub: S(26) = ""
    t_stub: S(12) = "оторви"
    t_stamp: S(16) = ""
    wide: bool = False


class Cards(BaseModel):
    type: Literal["cards"] = "cards"
    step: S(30) = ""
    items: list[CardItem] = Field(min_length=1, max_length=8)


class Letter(BaseModel):
    type: Literal["letter"] = "letter"
    step: S(30) = ""
    text: S(700)
    signature: S(40) = ""


class Final(BaseModel):
    type: Literal["final"] = "final"
    step: S(30) = ""
    scene: Literal["couple", "hug", "highfive", "trophy", "cake", "gift"]
    tap_hint: S(30) = "нажми"
    question: S(30) = ""
    yes: S(16) = "да"
    no: list[S(16)] = Field(default_factory=list, max_length=5, description="Убегающие варианты «нет»")
    finale: S(80) = ""


class Polaroid(BaseModel):
    photo: int = Field(ge=0)
    caption: S(30) = ""


class Polaroids(BaseModel):
    type: Literal["polaroids"] = "polaroids"
    step: S(30) = ""
    hint: S(30) = "нажми на фото"
    items: list[Polaroid] = Field(min_length=1, max_length=15)


class QuizAnswer(BaseModel):
    text: S(40)
    correct: bool = False
    reply: S(80) = Field("", description="Реакция на этот ответ")


class Quiz(BaseModel):
    type: Literal["quiz"] = "quiz"
    step: S(30) = ""
    question: S(80)
    answers: list[QuizAnswer] = Field(min_length=2, max_length=4)


class Moment(BaseModel):
    when: S(30) = Field(description="Подпись времени: «лето 2021», «первое свидание»")
    what: S(120)
    icon: IconName = "star"


class Timeline(BaseModel):
    type: Literal["timeline"] = "timeline"
    step: S(30) = ""
    items: list[Moment] = Field(min_length=2, max_length=8)


class Reasons(BaseModel):
    type: Literal["reasons"] = "reasons"
    step: S(30) = ""
    title: S(50) = Field(description="Напр. «5 причин, почему ты лучшая»")
    items: list[S(120)] = Field(min_length=2, max_length=12)
    button: S(20) = "ещё"
    last_button: S(20) = "по кругу"


class Custom(BaseModel):
    """Свой блок «Принца»: HTML+CSS+JS, написанные нейросетью. Корень — <section class="custom cx">.
    JS получает root (элемент блока) и A (window.Ahnut: act, burst, rain, grow, icon, vibrate)."""
    type: Literal["custom"] = "custom"
    step: S(30) = ""
    html: S(9000)
    css: S(9000) = ""
    js: S(9000) = ""


class Footer(BaseModel):
    type: Literal["footer"] = "footer"
    text: S(60) = ""


Block = Annotated[Union[Envelope, Hero, Phone, Polaroids, Cards, Letter, Quiz, Timeline, Reasons, Custom, Final, Footer],
                  Field(discriminator="type")]


class CardSpec(BaseModel):
    version: Literal[1] = 1
    theme: ThemeName = "cream_rose"
    accent: str | None = Field(None, description="Свой акцентный цвет #rrggbb (необязательно)")
    accent2: str | None = None
    accent_deep: str | None = None
    symbol: IconName = Field("heart", description="Значок для дождя и вспышек")
    decor: Literal["flowers", "stars", "snow", "balloons", "none"] = "flowers"
    title: S(60) = Field("", description="Заголовок вкладки браузера")
    music: bool = Field(False, description="Включить фоновую музыку (только «Принц», если загружена)")
    blocks: list[Block] = Field(min_length=2, max_length=16)

    @field_validator("accent", "accent2", "accent_deep")
    @classmethod
    def _hex(cls, v):
        if v is not None and not HEX.match(v):
            raise ValueError("цвет должен быть в формате #rrggbb")
        return v


# Какие блоки доступны тарифам
TIER_BLOCKS = {
    "zapiska": {"envelope", "hero", "phone", "cards", "letter", "final", "footer"},
    "svidanie": {"envelope", "hero", "phone", "polaroids", "cards", "letter", "quiz", "timeline", "reasons", "final", "footer"},
    "prince": {"envelope", "hero", "phone", "polaroids", "cards", "letter", "quiz", "timeline", "reasons", "custom", "final", "footer"},
}
MAX_CUSTOM = 3


def tier_problems(spec: CardSpec, tier: str, n_photos: int) -> list[str]:
    """Что в открытке не подходит тарифу. Пустой список — всё в порядке."""
    out = []
    allowed = TIER_BLOCKS[tier]
    for b in spec.blocks:
        if b.type not in allowed:
            out.append(f"блок {b.type} недоступен на этом тарифе")
        for idx in [s.photo for s in getattr(b, "slides", [])] + [p.photo for p in (b.items if b.type == "polaroids" else [])]:
            if idx >= max(n_photos, 1):
                out.append(f"фото №{idx} не загружено (всего {n_photos})")
    if sum(b.type == "custom" for b in spec.blocks) > MAX_CUSTOM:
        out.append(f"своих блоков больше {MAX_CUSTOM}")
    if sum(b.type == "final" for b in spec.blocks) > 1 or sum(b.type == "envelope" for b in spec.blocks) > 1:
        out.append("конверт и финал — не больше одного")
    if spec.music and tier != "prince":
        out.append("музыка только на «Принце»")
    return out
