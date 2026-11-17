"""Сборка открытки: CardSpec (JSON) + фото → один HTML.

Ссылка (основной путь): шрифты/текстуры/фото — отдельные файлы с нашего сервера.
Файл для скачивания (inline=True): шрифты и текстуры встраиваются внутрь, чтобы файл открывался сам.
"""
import base64
import hashlib
import random
import re
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.cards import icons as ic
from app.cards.scenes import ROMANTIC_SCENES, SCENES
from app.cards.spec import CardSpec, Envelope
from app.cards.themes import Palette, palette

ASSETS = Path(__file__).parent / "assets"
STATIC = Path(__file__).parent.parent / "static"

_env = Environment(loader=FileSystemLoader(ASSETS), autoescape=select_autoescape(["j2", "html"]))

FONTS = [
    # (семейство, файл-префикс, вес, стиль)
    ("Cormorant Garamond", "cormorant-garamond", 500, "italic"),
    ("Cormorant Garamond", "cormorant-garamond", 700, "italic"),
    ("Cormorant Garamond", "cormorant-garamond", 600, "normal"),
    ("Oswald", "oswald", 400, "normal"),
    ("Oswald", "oswald", 600, "normal"),
    ("Inter", "inter", 400, "normal"),
    ("Inter", "inter", 600, "normal"),
    ("Caveat", "caveat", 600, "normal"),
]
RANGES = {
    "cyrillic": "U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116",
    "latin": "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD",
}

# Места для бутонов по краям экрана (x%, y%, размер, поворот)
DECOR_SLOTS = [(4, 18, 96, -18), (95, 30, 84, 16), (2, 52, 80, 10), (97, 64, 100, -12),
               (6, 86, 92, 20), (93, 90, 80, -22), (50, 101, 110, 0), (96, 6, 70, 30)]



def _data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def _asset(name: str, base: str, inline: bool, mime: str) -> str:
    return _data_uri(STATIC / name, mime) if inline else f"{base}/{name}"


@lru_cache(maxsize=4)
def _fonts_css(base: str, inline: bool) -> str:
    out = []
    for fam, pref, w, st in FONTS:
        for sub, rng in RANGES.items():
            name = f"fonts/{pref}-{sub}-{w}-{st}.woff2"
            src = _asset(name, base, inline, "font/woff2")
            out.append(f"@font-face{{font-family:'{fam}';font-style:{st};font-weight:{w};font-display:swap;"
                       f"src:url({src}) format('woff2');unicode-range:{rng}}}")
    return "\n".join(out)


def _alpha(hex_color: str, a: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{a})"


def _vars(p: Palette, base: str, inline: bool) -> dict[str, str]:
    tex = _asset(f"tex/{'fabric' if p.material == 'fabric' else 'paper'}.png", base, inline, "image/png")
    paper = _asset("tex/paper.png", base, inline, "image/png")
    grain = _asset("tex/grain.png", base, inline, "image/png")
    return {
        "bg": p.bg, "bg2": p.bg2, "ink": p.ink, "muted": p.muted,
        "accent": p.accent, "accent2": p.accent2, "accent-deep": p.accent_deep, "accent-ink": p.accent_ink,
        "surface": p.surface, "surface2": p.surface2, "surface-ink": p.surface_ink, "stitch": p.stitch,
        "env1": p.surface, "env2": p.surface2, "env-ink": p.muted,
        "title": p.accent2 if p.dark else p.accent_deep,
        "title-hi": "rgba(255,255,255,.35)" if p.dark else "rgba(255,255,255,.9)",
        "title-glow": _alpha(p.accent, .45 if p.dark else .25),
        "shadow": "rgba(0,0,0,.55)" if p.dark else "rgba(70,45,30,.22)",
        "vig": "rgba(0,0,0,.6)" if p.dark else "rgba(90,60,40,.16)",
        "tex": f"url({tex})", "tex-size": "80px" if p.material == "fabric" else "128px",
        "tex-paper": f"url({paper})", "grain": f"url({grain})", "grain-o": ".07" if p.dark else ".05",
        "serif": "'Cormorant Garamond',Georgia,serif", "label": "'Oswald','Arial Narrow',sans-serif",
        "sans": "'Inter',system-ui,sans-serif", "hand": "'Caveat','Comic Sans MS',cursive",
    }


@lru_cache
def _base_css() -> str:
    css = re.sub(r"/\*.*?\*/", "", (ASSETS / "card.css").read_text(), flags=re.S)
    return re.sub(r"\n\s*\n", "\n", css).strip()


@lru_cache
def _runtime_js() -> str:
    return (ASSETS / "card.js").read_text()


def bloom_svg(p: Palette, k: int) -> str:
    """Цветок «бутон → цветок»: лепестки поворачиваются из бутона (CSS .bl.open)."""
    petals = "".join(
        f'<path class="pt" style="--a:{a}deg" d="M50 50 C40 38 40 16 50 4 C60 16 60 38 50 50Z" fill="url(#bp{k})"/>'
        f'<path class="pt" style="--a:{a}deg" d="M50 46 L50 12" stroke="{p.accent_deep}" stroke-width=".8" opacity=".35"/>'
        for a in range(0, 360, 60)
    )
    return (
        f'<svg viewBox="0 0 100 100"><defs><linearGradient id="bp{k}" x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0" stop-color="{p.accent_deep}"/><stop offset=".45" stop-color="{p.accent}"/>'
        f'<stop offset="1" stop-color="{p.accent2}"/></linearGradient></defs>'
        '<path d="M50 52 C50 70 48 84 52 100" stroke="#3f7a3c" stroke-width="3.5" fill="none"/>'
        '<path d="M51 78 C62 70 72 72 78 66 C68 62 56 66 51 74Z" fill="#4f9d55"/>'
        + petals
        + '<g class="core"><circle cx="50" cy="50" r="7" fill="#f6d36b"/>'
        + "".join(f'<circle cx="{50+11*dx}" cy="{50+11*dy}" r="1.8" fill="#8a5a00"/>' for dx, dy in
                  ((0, -1), (.87, -.5), (.87, .5), (0, 1), (-.87, .5), (-.87, -.5)))
        + "</g></svg>"
    )


def _icon_decor(name: str) -> str:
    return ic.use(name)


def sanitize(spec: CardSpec, recipient: str | None) -> CardSpec:
    """Никакой романтики не-паре: сцена «пара» → обнимашки, кольцо → подарок."""
    if recipient == "partner" or recipient is None:
        return spec
    data = spec.model_dump()
    swap = lambda n: "gift" if n in ic.ROMANTIC_ICONS else n  # noqa: E731
    data["symbol"] = swap(data["symbol"])
    for b in data["blocks"]:
        for key in ("icon", "seal_icon", "wallpaper_icon"):
            if key in b:
                b[key] = swap(b[key])
        for it in b.get("items", []):
            if isinstance(it, dict) and "icon" in it:
                it["icon"] = swap(it["icon"])
        if b["type"] == "final" and b["scene"] in ROMANTIC_SCENES:
            b["scene"] = "hug"
    return CardSpec.model_validate(data)


def render(spec: CardSpec, photos: list[str] | None = None, *, recipient: str | None = None,
           asset_base: str = "/static", inline: bool = False, music_src: str | None = None) -> str:
    """photos — адреса фото по порядку (или data: URI для самопроверки/файла)."""
    spec = sanitize(spec, recipient)
    photos = photos or []
    p = palette(spec.theme, spec.accent, spec.accent2, spec.accent_deep)
    seed = int(hashlib.sha1(spec.model_dump_json().encode()).hexdigest()[:8], 16)
    rnd = random.Random(seed)
    src = lambda i: photos[i] if 0 <= i < len(photos) else None  # noqa: E731

    used_icons = {spec.symbol}
    blocks, customs = [], []
    envelope: Envelope | None = None
    scene_svg = ""
    for n, b in enumerate(spec.blocks):
        d = b.model_dump()
        if b.type == "envelope":
            envelope = b
            used_icons.add(b.seal_icon)
            continue
        if b.type == "hero":
            used_icons.add(b.icon)
        elif b.type == "phone":
            used_icons.add(b.wallpaper_icon)
            for s_ in d["slides"]:
                s_["src"] = src(s_["photo"])
        elif b.type == "polaroids":
            for it in d["items"]:
                it["src"] = src(it["photo"])
        elif b.type == "cards":
            for it in d["items"]:
                it["rot"] = rnd.choice((-2, -1, 1, 2))
                used_icons.add(it["icon"])
        elif b.type == "timeline":
            used_icons |= {m["icon"] for m in d["items"]}
        elif b.type == "custom":
            d["cid"] = f"cx{n}"
            d["css"] = re.sub(r"#cx\b", f"#cx{n}", d["css"])  # стили своего блока — только внутри него
            customs.append(d)
        elif b.type == "final":
            if not b.yes:
                d["no"] = []
            scene_svg = SCENES[b.scene](p)
        blocks.append(d)

    decor = []
    if spec.decor != "none":
        kind = {"stars": "star", "snow": "snowflake", "balloons": "balloon"}.get(spec.decor)
        if kind:
            used_icons.add(kind)
        for k, (x, y, sz, r) in enumerate(DECOR_SLOTS, 1):
            svg = bloom_svg(p, k) if spec.decor == "flowers" else _icon_decor(kind)
            decor.append({"x": x, "y": y, "sz": sz, "r": r, "svg": svg, "ico": spec.decor != "flowers"})

    rain = [{"x": rnd.randint(0, 95), "s": rnd.randint(16, 28), "o": round(rnd.uniform(.25, .5), 2),
             "d": rnd.randint(9, 16), "dl": -rnd.randint(0, 14), "rot": rnd.randint(-200, 200)} for _ in range(7)]
    # значки, которые могут понадобиться своим блокам «Принца»
    if customs:
        used_icons |= set(ic.ICONS) - ic.ROMANTIC_ICONS if recipient != "partner" else set(ic.ICONS)
    symbols = "".join(ic.symbol(n, p) for n in sorted(used_icons) if n in ic.ICONS)

    tpl = _env.get_template("card.html.j2")
    return tpl.render(
        title=spec.title or "Открытка",
        fonts_css=_fonts_css(asset_base, inline),
        vars=_vars(p, asset_base, inline),
        base_css=_base_css(),
        runtime_js=_runtime_js(),
        symbols=symbols,
        decor=decor, rain=rain,
        symbol=spec.symbol,
        icon=lambda n: ic.use(n),
        envelope=envelope, has_env=envelope is not None,
        blocks=blocks, scene_svg=scene_svg, customs=customs,
        music_src=music_src if spec.music else None,
    )
