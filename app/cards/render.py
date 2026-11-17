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

# Куда «убегает» кнопка «нет» после каждого нажатия
RUNAWAY = ["translate(-40%,72px) rotate(10deg)", "translate(25%,-64px) rotate(-14deg)",
           "translate(-150%,60px) rotate(8deg)", "translate(30%,84px) rotate(-8deg)", "translate(-120%,-50px) rotate(6deg)"]


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
            it["icon"] = swap(it["icon"])
        if b["type"] == "final" and b["scene"] in ROMANTIC_SCENES:
            b["scene"] = "hug"
    return CardSpec.model_validate(data)


def render(spec: CardSpec, photos: list[str] | None = None, *, recipient: str | None = None,
           asset_base: str = "/static", inline: bool = False) -> str:
    spec = sanitize(spec, recipient)
    photos = photos or []
    p = palette(spec.theme, spec.accent, spec.accent2, spec.accent_deep)
    seed = int(hashlib.sha1(spec.model_dump_json().encode()).hexdigest()[:8], 16)
    rnd = random.Random(seed)

    triggers: list[str] = []
    dyn: list[str] = []
    used_icons = {spec.symbol}
    blocks = []
    envelope: Envelope | None = None
    scene_svg = ""
    card_n = 0

    for b in spec.blocks:
        d = b.model_dump()
        if b.type == "envelope":
            envelope = b
            triggers.insert(0, "t-env")
            used_icons.add(b.seal_icon)
            continue
        if b.type == "hero":
            used_icons.add(b.icon)
        elif b.type == "phone":
            used_icons.add(b.wallpaper_icon)
            triggers.append("t-unlock")
            n = len(b.slides)
            for i, s in enumerate(d["slides"], 1):
                s["src"] = photos[s["photo"]] if s["photo"] < len(photos) else None
                s["dots"] = [j == i for j in range(1, n + 1)]
                triggers.append(f"t-p{i}")
        elif b.type == "cards":
            for it in d["items"]:
                card_n += 1
                tid, cid = f"t-c{card_n}", f"c{card_n}"
                it.update(tid=tid, cid=cid, rot=rnd.choice((-2, -1, 1, 2)))
                triggers.append(tid)
                used_icons.add(it["icon"])
                sel = f"#{tid}:checked ~ main #{cid}"
                dyn.append(f"{sel} .hint{{opacity:0}}")
                if it["kind"] == "word":
                    dyn.append(f"{sel} .w1::after{{transform:rotate(-8deg) scaleX(1)}}{sel} .w2{{transform:scale(1)}}")
                elif it["kind"] == "ticket":
                    dyn.append(f"{sel} .r{{transform:translateX(16px) rotate(8deg);opacity:0}}"
                               f"{sel} .stamp{{opacity:.9;transform:translateY(-50%) rotate(-74deg) scale(1)}}")
                elif it["effect"] == "flip":
                    dyn.append(f"{sel} .fl{{transform:rotateY(180deg)}}")
                else:
                    it["pop_icon"] = spec.symbol
                    it["pops"] = [{"dx": rnd.randint(-100, 100), "dy": rnd.randint(-100, 60), "dl": rnd.choice((0, .1, .2))}
                                  for _ in range(7)] if it["effect"] in ("burst", "shake") else []
                    dyn.append(f"{sel} .pop i{{display:block;animation:shot 1s ease-out forwards}}")
                    if it["effect"] == "spin":
                        dyn.append(f"{sel} .ic{{animation-play-state:running}}")
                    if it["effect"] == "shake":
                        dyn.append(f"{sel} .ic{{animation:shake .9s ease}}")
                    if it["effect"] == "burst":
                        dyn.append(f"{sel} .ic{{animation:beat .8s ease}}")
        elif b.type == "letter":
            if "t-letter" not in triggers:
                triggers.append("t-letter")
        elif b.type == "final":
            if not b.yes:
                b = b.model_copy(update={"no": []})
                d["no"] = []
            triggers += ["t-fin"] + (["t-yes"] if b.yes else []) + [f"t-no{i}" for i in range(1, len(b.no) + 1)]
            scene_svg = SCENES[b.scene](p)
            for i in range(1, len(b.no) + 1):
                dyn.append(f"#t-no{i}:checked ~ main .btn.no.n{i}{{display:none}}")
                if i < len(b.no):
                    dyn.append(f"#t-no{i}:checked ~ main .btn.no.n{i+1}{{display:block;transform:{RUNAWAY[(i-1) % len(RUNAWAY)]}}}")
            if not b.yes:
                dyn.append("#t-fin:checked ~ main .finale{opacity:1;transition-delay:1.2s}")
        blocks.append(d)

    # Декор: каждый бутон привязан к двум действиям — появляется после первого, раскрывается после обоих
    decor = []
    acts = [t for t in triggers if not t.startswith("t-no")]
    if spec.decor != "none" and acts:
        kind = {"stars": "star", "snow": "snowflake", "balloons": "balloon"}.get(spec.decor)
        if kind:
            used_icons.add(kind)
        order = {t: i for i, t in enumerate(triggers)}
        for k, (x, y, sz, r) in enumerate(DECOR_SLOTS, 1):
            pair = sorted({acts[(2 * k - 2) % len(acts)], acts[(2 * k - 1) % len(acts)]}, key=order.get)
            svg = bloom_svg(p, k) if spec.decor == "flowers" else _icon_decor(kind)
            decor.append({"x": x, "y": y, "sz": sz, "r": r, "svg": svg})
            shown = f"transform:scale(1) rotate({r}deg)"
            dyn.append(",".join(f"#{t}:checked ~ .decor .b{k}" for t in pair) + f"{{{shown}}}")
            both = " ~ ".join(f"#{t}:checked" for t in pair) + f" ~ .decor .b{k}"
            dyn.append(f"{both} .pt{{transform:rotate(var(--a))}}{both} .core{{opacity:1}}")
            fin = "#t-yes" if "t-yes" in triggers else ("#t-fin" if "t-fin" in triggers else None)
            if fin:
                dyn.append(f"{fin}:checked ~ .decor .b{k}{{{shown};transition-delay:{.15*k:.2f}s}}"
                           f"{fin}:checked ~ .decor .b{k} .pt{{transform:rotate(var(--a))}}{fin}:checked ~ .decor .b{k} .core{{opacity:1}}")
        dyn.append(".bl .pt{transform:rotate(calc(var(--a)*.08)) scale(.5,.62)}" if spec.decor == "flowers"
                   else ".bl svg{transform:scale(.7)}")

    # Дождь значков и вспышки на ключевые действия
    rain = [{"x": rnd.randint(0, 95), "s": rnd.randint(16, 28), "o": round(rnd.uniform(.25, .5), 2),
             "d": rnd.randint(9, 16), "dl": -rnd.randint(0, 14), "rot": rnd.randint(-200, 200)} for _ in range(7)]
    bursts = []
    for key, t in (("env", "t-env"), ("fin", "t-fin"), ("yes", "t-yes")):
        if t in triggers:
            items = [{"x": rnd.randint(0, 95), "s": rnd.randint(18, 40), "d": round(rnd.uniform(2.2, 4.2), 1),
                      "dl": round(rnd.uniform(0, 1.6), 2), "rot": rnd.randint(-300, 300)} for _ in range(16)]
            bursts.append({"key": key, "list": items})
            dyn.append(f"#{t}:checked ~ .b-{key} i{{display:block;animation:fall var(--d) linear var(--dl) forwards}}")

    used_icons |= {it for b in blocks for it in [b.get("icon")] if it}
    symbols = "".join(ic.symbol(n, p) for n in sorted(used_icons) if n in ic.ICONS)

    tpl = _env.get_template("card.html.j2")
    return tpl.render(
        title=spec.title or "Открытка",
        fonts_css=_fonts_css(asset_base, inline),
        vars=_vars(p, asset_base, inline),
        base_css=_base_css(),
        dyn_css="\n".join(dyn),
        symbols=symbols,
        triggers=triggers,
        decor=decor, rain=rain, bursts=bursts,
        symbol=spec.symbol,
        icon=lambda n: ic.use(n),
        envelope=envelope, has_env=envelope is not None,
        blocks=blocks, scene_svg=scene_svg,
    )
