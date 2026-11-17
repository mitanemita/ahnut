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


class Footer(BaseModel):
    type: Literal["footer"] = "footer"
    text: S(60) = ""


Block = Annotated[Union[Envelope, Hero, Phone, Cards, Letter, Final, Footer], Field(discriminator="type")]


class CardSpec(BaseModel):
    version: Literal[1] = 1
    theme: ThemeName = "cream_rose"
    accent: str | None = Field(None, description="Свой акцентный цвет #rrggbb (необязательно)")
    accent2: str | None = None
    accent_deep: str | None = None
    symbol: IconName = Field("heart", description="Значок для дождя и вспышек")
    decor: Literal["flowers", "stars", "snow", "balloons", "none"] = "flowers"
    title: S(60) = Field("", description="Заголовок вкладки браузера")
    blocks: list[Block] = Field(min_length=2, max_length=12)

    @field_validator("accent", "accent2", "accent_deep")
    @classmethod
    def _hex(cls, v):
        if v is not None and not HEX.match(v):
            raise ValueError("цвет должен быть в формате #rrggbb")
        return v
