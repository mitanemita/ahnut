"""Готовые темы оформления. Нейросеть выбирает тему и может поправить акцентные цвета."""
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Palette:
    bg: str          # фон страницы
    bg2: str         # второй цвет фона (градиент)
    ink: str         # основной текст
    muted: str       # второстепенный текст
    accent: str      # главный акцент
    accent2: str     # светлый акцент (блики, мягкие элементы)
    accent_deep: str  # тёмный акцент (тени, обводки)
    accent_ink: str  # текст на кнопке-акценте
    surface: str     # карточки
    surface2: str    # второй цвет карточек
    surface_ink: str  # текст на карточках
    stitch: str      # строчка-пунктир по краю карточек
    dark: bool       # тёмная тема (влияет на текстуры)
    material: str    # fabric | paper


THEMES: dict[str, Palette] = {
    # тёмная ткань и розовый — как в первой открытке
    "noir_pink": Palette("#09090b", "#1b161a", "#f4f0f2", "#8d8d96", "#ff4fa3", "#ffb3d6", "#9d0f47", "#1a0b12",
                         "#48484f", "#2c2c31", "#eeeeee", "rgba(215,215,225,.42)", True, "fabric"),
    # тёплая бумага, пыльная роза и золото — маме, бабушке
    "cream_rose": Palette("#f6ece2", "#fffaf4", "#3b2620", "#8a6f66", "#c4566f", "#f2b8c3", "#7d2a3c", "#fff",
                          "#fffaf3", "#f1e4d6", "#3b2620", "rgba(150,110,95,.45)", False, "paper"),
    # крафт и солнечно-оранжевый — другу, смешное
    "kraft_sun": Palette("#e9d8b8", "#f6ead2", "#2b2118", "#7a6650", "#ff7a1a", "#ffd166", "#b34700", "#2b1300",
                         "#2b2b31", "#1d1d21", "#f4efe6", "rgba(255,209,102,.55)", False, "paper"),
    # тёмно-синий и золото — Новый год, юбилей, торжественно
    "navy_gold": Palette("#0b1330", "#16224d", "#f5f1e6", "#9aa3c0", "#e2b34a", "#ffe7a3", "#8a5a00", "#1b1300",
                         "#1d2a5a", "#121c40", "#f5f1e6", "rgba(226,179,74,.5)", True, "fabric"),
    # мятный и бирюзовый — коллеге, деловой-душевный
    "mint_fresh": Palette("#eef6f3", "#ffffff", "#1c2b2a", "#5f7471", "#14967f", "#9fe3d2", "#0b5c4e", "#fff",
                          "#ffffff", "#e3f1ec", "#1c2b2a", "rgba(20,150,127,.35)", False, "paper"),
    # пастель — ребёнку
    "candy_sky": Palette("#dff1ff", "#fff6fb", "#26324a", "#6b7896", "#ff5c8a", "#ffd1e0", "#c2185b", "#fff",
                         "#ffffff", "#fff3c4", "#26324a", "rgba(255,92,138,.4)", False, "paper"),
    # лаванда — день рождения, нейтрально
    "lilac_dream": Palette("#1d1530", "#2d2150", "#f3eefe", "#a99cc9", "#b388ff", "#e4d4ff", "#5e35b1", "#140a2b",
                           "#3a2d5c", "#261c40", "#f3eefe", "rgba(228,212,255,.4)", True, "fabric"),
}

THEME_NAMES = sorted(THEMES)


def palette(theme: str, accent: str | None = None, accent2: str | None = None, accent_deep: str | None = None) -> Palette:
    p = THEMES.get(theme, THEMES["cream_rose"])
    kw = {k: v for k, v in {"accent": accent, "accent2": accent2, "accent_deep": accent_deep}.items() if v}
    return replace(p, **kw) if kw else p
