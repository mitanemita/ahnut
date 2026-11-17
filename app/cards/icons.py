"""Библиотека значков-«предметов». Объём — градиенты, блики, тени; без чужих логотипов.

Каждый значок — <symbol id="i-<name>" viewBox="0 0 100 100">. Цвета берутся из палитры открытки,
поэтому один и тот же значок подходит маме, другу и коллеге.
"""
from typing import Callable

from app.cards.themes import Palette

# Значки, допустимые только для пары
ROMANTIC_ICONS = {"ring"}


def _lg(gid: str, stops: list[tuple[float, str]], x1=0, y1=0, x2=0, y2=1) -> str:
    s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{s}</linearGradient>'


def _rg(gid: str, stops: list[tuple[float, str]], cx=".38", cy=".32", r=".75") -> str:
    s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}">{s}</radialGradient>'


GOLD = [(0, "#fff6c9"), (.3, "#f3c64b"), (.55, "#b8860b"), (.75, "#f6d36b"), (1, "#8a5a00")]
SILVER = [(0, "#ffffff"), (.35, "#c9c9d1"), (.5, "#f4f4f7"), (.55, "#6d6d76"), (1, "#a9a9b2")]
SHADOW = '<ellipse cx="50" cy="95" rx="30" ry="3.5" fill="#000" opacity=".28"/>'


def heart(p: Palette) -> str:
    return (
        _rg("ih-g", [(0, "#ffffff"), (.2, p.accent2), (.55, p.accent), (1, p.accent_deep)], ".35", ".28", ".8")
        + SHADOW
        + '<path d="M50 88 C20 66 6 50 6 31 C6 17 17 7 30 7 C39 7 46 12 50 20 C54 12 61 7 70 7 C83 7 94 17 94 31 C94 50 80 66 50 88Z" fill="url(#ih-g)"/>'
        + '<path d="M22 15 C14 18 10 25 11 33 C15 25 21 21 31 19Z" fill="#fff" opacity=".7"/>'
        + '<ellipse cx="71" cy="18" rx="7" ry="3.5" fill="#fff" opacity=".35" transform="rotate(22 71 18)"/>'
        + '<path d="M50 88 C70 72 88 58 94 38 C90 58 72 72 50 88Z" fill="#000" opacity=".22"/>'
    )


def star(p: Palette) -> str:
    pts = "50,6 61,37 94,38 68,58 77,90 50,71 23,90 32,58 6,38 39,37"
    return (
        _lg("is-g", GOLD, 0, 0, 1, 1) + SHADOW
        + f'<polygon points="{pts}" fill="url(#is-g)" stroke="#7a4c00" stroke-width="1.2" stroke-linejoin="round"/>'
        + '<polygon points="50,6 50,71 23,90 32,58 6,38 39,37" fill="#fff" opacity=".18"/>'
        + '<path d="M44 26 L50 10 L54 22" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" opacity=".8"/>'
    )


def flower(p: Palette) -> str:
    return (
        _lg("if-st", [(0, "#6fbf73"), (1, "#2e6b33")], 0, 0, 1, 0)
        + _rg("if-p", [(0, "#fff"), (.25, p.accent2), (.7, p.accent), (1, p.accent_deep)], ".4", ".25", ".9")
        + SHADOW
        + '<path d="M50 92 C49 75 50 62 51 48" stroke="url(#if-st)" stroke-width="5" fill="none" stroke-linecap="round"/>'
        + '<path d="M50 78 C38 70 28 72 22 66 C34 62 44 66 50 74Z" fill="#3f8a45"/>'
        + '<path d="M51 70 C62 60 72 62 80 56 C70 52 58 56 52 66Z" fill="#4f9d55"/>'
        + '<path d="M50 50 C34 48 26 34 30 14 C38 22 44 24 50 16 C56 24 62 22 70 14 C74 34 66 48 50 50Z" fill="url(#if-p)"/>'
        + '<path d="M50 50 C42 44 40 30 50 16 C60 30 58 44 50 50Z" fill="#000" opacity=".12"/>'
        + '<path d="M34 22 C33 30 36 38 42 43" stroke="#fff" stroke-width="2" fill="none" opacity=".6" stroke-linecap="round"/>'
    )


def gift(p: Palette) -> str:
    return (
        _lg("ig-b", [(0, p.accent2), (.5, p.accent), (1, p.accent_deep)], 0, 0, 1, 1)
        + _lg("ig-r", GOLD, 0, 0, 1, 0) + SHADOW
        + '<rect x="14" y="44" width="72" height="48" rx="3" fill="url(#ig-b)"/>'
        + '<rect x="10" y="32" width="80" height="16" rx="3" fill="url(#ig-b)"/>'
        + '<rect x="10" y="44" width="80" height="4" fill="#000" opacity=".2"/>'
        + '<rect x="44" y="32" width="12" height="60" fill="url(#ig-r)"/>'
        + '<path d="M50 32 C38 14 22 16 26 26 C29 33 42 32 50 32Z M50 32 C62 14 78 16 74 26 C71 33 58 32 50 32Z" fill="url(#ig-r)" stroke="#8a5a00" stroke-width="1"/>'
        + '<rect x="16" y="50" width="4" height="38" fill="#fff" opacity=".25"/>'
    )


def cake(p: Palette) -> str:
    return (
        _lg("ic-c", [(0, "#fffaf2"), (1, "#e9d9c3")], 0, 0, 0, 1)
        + _lg("ic-a", [(0, p.accent2), (1, p.accent)], 0, 0, 0, 1)
        + _rg("ic-f", [(0, "#fffbe0"), (.5, "#ffd34d"), (1, "#ff7a00")], ".5", ".6", ".6") + SHADOW
        + '<ellipse cx="50" cy="90" rx="40" ry="6" fill="#d9d4cf"/>'
        + '<path d="M16 58 H84 V86 Q50 94 16 86Z" fill="url(#ic-c)"/>'
        + '<path d="M16 58 Q24 68 30 60 Q38 70 44 60 Q50 70 56 60 Q62 70 70 60 Q76 68 84 58 V54 H16Z" fill="url(#ic-a)"/>'
        + '<path d="M24 40 H76 V58 H24Z" fill="url(#ic-c)"/>'
        + '<path d="M24 40 Q32 50 38 42 Q44 50 50 42 Q56 50 62 42 Q68 50 76 40 V36 H24Z" fill="url(#ic-a)"/>'
        + '<rect x="47" y="18" width="6" height="20" rx="2" fill="#fff" stroke="#ccc"/>'
        + '<path d="M47 22 l6 -3 M47 28 l6 -3 M47 34 l6 -3" stroke="' + p.accent + '" stroke-width="2"/>'
        + '<path class="flame" d="M50 4 C56 12 55 17 50 18 C45 17 44 12 50 4Z" fill="url(#ic-f)"/>'
        + '<rect x="18" y="62" width="3" height="20" fill="#fff" opacity=".5"/>'
    )


def cup(p: Palette) -> str:
    return (
        _lg("iu-b", [(0, "#ffffff"), (.6, "#e8e4ea"), (1, "#bdb7c2")], 0, 0, 1, 0) + SHADOW
        + '<path d="M22 34 H72 L68 86 Q47 94 26 86Z" fill="url(#iu-b)" stroke="#9a94a0" stroke-width="1"/>'
        + '<path d="M72 44 C90 42 90 70 70 70" fill="none" stroke="#d6d1da" stroke-width="7"/>'
        + '<ellipse cx="47" cy="34" rx="25" ry="6" fill="#4a2a17"/>'
        + '<ellipse cx="47" cy="34" rx="20" ry="4" fill="#6b3b1f"/>'
        + f'<path d="M30 60 C36 50 46 52 47 58 C48 52 58 50 64 60 C60 70 47 76 47 76 C47 76 34 70 30 60Z" fill="{p.accent}" opacity=".9"/>'
        + '<path class="steam" d="M38 26 C34 18 42 14 38 6 M50 26 C46 18 54 14 50 6 M60 26 C56 18 64 14 60 6" stroke="#fff" stroke-width="2.5" fill="none" stroke-linecap="round" opacity=".55"/>'
    )


def trophy(p: Palette) -> str:
    return (
        _lg("it-g", GOLD, 0, 0, 1, 0) + SHADOW
        + '<path d="M26 10 H74 V30 C74 48 62 58 50 58 C38 58 26 48 26 30Z" fill="url(#it-g)" stroke="#7a4c00"/>'
        + '<path d="M26 16 C10 16 10 40 30 44 M74 16 C90 16 90 40 70 44" fill="none" stroke="url(#it-g)" stroke-width="5"/>'
        + '<rect x="45" y="56" width="10" height="16" fill="url(#it-g)"/>'
        + '<rect x="30" y="72" width="40" height="8" rx="2" fill="url(#it-g)" stroke="#7a4c00"/>'
        + '<rect x="24" y="80" width="52" height="12" rx="2" fill="#2b2b30"/>'
        + f'<rect x="36" y="84" width="28" height="4" rx="1" fill="{p.accent}"/>'
        + '<path d="M33 16 V32 C33 42 38 48 44 51" stroke="#fff" stroke-width="3" fill="none" opacity=".6" stroke-linecap="round"/>'
        + '<polygon points="50,20 54,30 64,30 56,36 59,46 50,40 41,46 44,36 36,30 46,30" fill="#fff" opacity=".55"/>'
    )


def medal(p: Palette) -> str:
    return (
        _lg("im-g", GOLD, 0, 0, 1, 1) + SHADOW
        + f'<path d="M30 4 H46 L56 44 H40Z" fill="{p.accent}"/><path d="M70 4 H54 L44 44 H60Z" fill="{p.accent_deep}"/>'
        + '<circle cx="50" cy="66" r="26" fill="url(#im-g)" stroke="#7a4c00" stroke-width="1.5"/>'
        + '<circle cx="50" cy="66" r="19" fill="none" stroke="#7a4c00" stroke-width="1.2" opacity=".6"/>'
        + '<polygon points="50,52 54,62 65,62 56,68 60,79 50,72 40,79 44,68 35,62 46,62" fill="#fff" opacity=".6"/>'
        + '<path d="M32 58 C34 50 40 45 46 44" stroke="#fff" stroke-width="3" fill="none" opacity=".7" stroke-linecap="round"/>'
    )


def balloon(p: Palette) -> str:
    return (
        _rg("ib-g", [(0, "#fff"), (.2, p.accent2), (.7, p.accent), (1, p.accent_deep)], ".35", ".3", ".8")
        + '<path d="M50 70 C48 78 54 84 50 98" stroke="#999" stroke-width="1.2" fill="none"/>'
        + '<path d="M50 70 C28 66 18 48 20 32 C22 14 36 4 50 4 C64 4 78 14 80 32 C82 48 72 66 50 70Z" fill="url(#ib-g)"/>'
        + f'<path d="M46 70 L54 70 L52 75 L48 75Z" fill="{p.accent_deep}"/>'
        + '<ellipse cx="36" cy="22" rx="6" ry="10" fill="#fff" opacity=".55" transform="rotate(25 36 22)"/>'
    )


def ball(p: Palette) -> str:
    return (
        _rg("ifb-g", [(0, "#ffffff"), (.6, "#e9e9ee"), (1, "#a6a6b0")]) + SHADOW
        + '<circle cx="50" cy="48" r="40" fill="url(#ifb-g)" stroke="#555" stroke-width="1"/>'
        + '<polygon points="50,32 64,42 59,58 41,58 36,42" fill="#1e1e22"/>'
        + '<path d="M50 32 V12 M64 42 L82 34 M59 58 L70 76 M41 58 L30 76 M36 42 L18 34" stroke="#555" stroke-width="1.5"/>'
        + '<path d="M44 10 L56 10 L60 14 L50 18 L40 14Z M86 40 L84 52 L78 46 Z M14 40 L16 52 L22 46Z" fill="#1e1e22"/>'
        + '<ellipse cx="34" cy="28" rx="10" ry="6" fill="#fff" opacity=".7" transform="rotate(-35 34 28)"/>'
    )


def eightball(p: Palette) -> str:
    return (
        _rg("ie-g", [(0, "#6a6a72"), (.3, "#1b1b1f"), (1, "#000")]) + SHADOW
        + '<circle cx="50" cy="48" r="40" fill="url(#ie-g)"/>'
        + '<circle cx="54" cy="44" r="17" fill="#f6f6f6"/>'
        + '<text x="54" y="51" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-weight="700" font-size="21" fill="#111">8</text>'
        + '<ellipse cx="34" cy="26" rx="10" ry="5" fill="#fff" opacity=".45" transform="rotate(-35 34 26)"/>'
    )


def chess(p: Palette) -> str:
    return (
        _lg("ich-g", [(0, "#050506"), (.3, "#3c3c44"), (.42, "#9a9aa4"), (.5, "#2a2a30"), (1, "#050506")], 0, 0, 1, 0)
        + SHADOW
        + '<path d="M30 92 H70 V84 Q70 78 64 78 H36 Q30 78 30 84Z" fill="url(#ich-g)"/>'
        + '<path d="M38 78 L42 46 H58 L62 78Z" fill="url(#ich-g)"/>'
        + '<rect x="36" y="40" width="28" height="7" rx="2" fill="url(#ich-g)"/>'
        + '<path d="M38 40 L34 20 L42 26 L46 14 L50 22 L54 14 L58 26 L66 20 L62 40Z" fill="url(#ich-g)"/>'
        + f'<circle cx="46" cy="14" r="3" fill="{p.accent}"/><circle cx="54" cy="14" r="3" fill="{p.accent}"/>'
        + f'<circle cx="34" cy="20" r="3" fill="{p.accent}"/><circle cx="66" cy="20" r="3" fill="{p.accent}"/>'
    )


def camera(p: Palette) -> str:
    return (
        _lg("ica-b", [(0, "#4a4a52"), (1, "#1a1a1e")], 0, 0, 0, 1)
        + _rg("ica-l", [(0, "#8fb3ff"), (.3, "#24304f"), (1, "#050507")], ".4", ".35", ".7") + SHADOW
        + '<rect x="8" y="28" width="84" height="58" rx="8" fill="url(#ica-b)"/>'
        + '<path d="M34 28 L40 16 H60 L66 28Z" fill="#2a2a30"/>'
        + f'<rect x="8" y="40" width="84" height="8" fill="{p.accent}" opacity=".85"/>'
        + '<circle cx="50" cy="58" r="22" fill="#111" stroke="#8a8a92" stroke-width="3"/>'
        + '<circle cx="50" cy="58" r="15" fill="url(#ica-l)"/>'
        + '<circle cx="45" cy="53" r="4" fill="#fff" opacity=".6"/>'
        + '<rect x="72" y="32" width="12" height="6" rx="2" fill="#ddd"/>'
    )


def plane(p: Palette) -> str:
    return (
        _lg("ipl-g", SILVER, 0, 0, 0, 1)
        + '<ellipse cx="50" cy="94" rx="26" ry="3" fill="#000" opacity=".2"/>'
        + '<path d="M8 52 C8 46 18 44 30 44 H78 C88 44 94 48 94 52 C94 56 88 60 78 60 H30 C18 60 8 58 8 52Z" fill="url(#ipl-g)" stroke="#6d6d76"/>'
        + f'<path d="M46 46 L32 12 H42 L64 46Z" fill="{p.accent}"/><path d="M46 58 L36 84 H46 L64 58Z" fill="{p.accent_deep}"/>'
        + f'<path d="M14 46 L8 28 H16 L26 46Z" fill="{p.accent}"/>'
        + '<path d="M80 47 C86 47 90 49 91 52 H80Z" fill="#24304f"/>'
        + '<g fill="#24304f">' + "".join(f'<rect x="{x}" y="49" width="4" height="4" rx="1"/>' for x in range(34, 76, 7)) + '</g>'
    )


def book(p: Palette) -> str:
    return (
        _lg("ibk-c", [(0, p.accent2), (1, p.accent_deep)], 0, 0, 1, 1) + SHADOW
        + '<path d="M14 18 H76 Q84 18 84 26 V90 H22 Q14 90 14 82Z" fill="url(#ibk-c)"/>'
        + '<path d="M22 82 H84 V90 H22 Q16 90 16 86 Q16 82 22 82Z" fill="#f4efe6"/>'
        + '<path d="M22 84 H82 M22 87 H82" stroke="#cfc6b8" stroke-width=".8"/>'
        + '<rect x="30" y="30" width="44" height="22" rx="2" fill="none" stroke="#f3c64b" stroke-width="2"/>'
        + '<path d="M38 41 H66" stroke="#f3c64b" stroke-width="2"/>'
        + '<rect x="18" y="20" width="4" height="60" fill="#fff" opacity=".25"/>'
    )


def guitar(p: Palette) -> str:
    return (
        _lg("igu-b", [(0, "#f2b56b"), (.5, "#c26a1f"), (1, "#6b3108")], 0, 0, 1, 1) + SHADOW
        + '<g transform="rotate(-30 50 50)">'
        + '<rect x="46" y="2" width="8" height="46" fill="#3a2414"/><rect x="43" y="0" width="14" height="10" rx="2" fill="#1e1e22"/>'
        + '<path d="M50 44 C34 44 30 54 34 62 C26 66 24 80 32 88 C40 96 60 96 68 88 C76 80 74 66 66 62 C70 54 66 44 50 44Z" fill="url(#igu-b)"/>'
        + '<circle cx="50" cy="66" r="7" fill="#1e1206"/>'
        + f'<rect x="42" y="78" width="16" height="4" rx="1" fill="{p.accent_deep}"/>'
        + '<path d="M48 4 V80 M50 4 V80 M52 4 V80" stroke="#e8e0d0" stroke-width=".5"/>'
        + '<path d="M36 58 C34 66 34 76 40 84" stroke="#fff" stroke-width="2" fill="none" opacity=".35"/></g>'
    )


def gamepad(p: Palette) -> str:
    return (
        _lg("igp-b", [(0, "#4a4a52"), (1, "#141417")], 0, 0, 0, 1) + SHADOW
        + '<path d="M28 30 H72 C86 30 94 50 94 66 C94 80 84 86 76 78 L66 66 H34 L24 78 C16 86 6 80 6 66 C6 50 14 30 28 30Z" fill="url(#igp-b)"/>'
        + '<path d="M22 46 H30 V40 H36 V46 H44 V52 H36 V58 H30 V52 H22Z" fill="#0b0b0d"/>'
        + f'<circle cx="68" cy="44" r="4.5" fill="{p.accent}"/><circle cx="76" cy="52" r="4.5" fill="{p.accent2}"/>'
        + '<circle cx="60" cy="52" r="4.5" fill="#f3c64b"/><circle cx="68" cy="60" r="4.5" fill="#6fbf73"/>'
        + '<path d="M28 34 H70" stroke="#fff" stroke-width="2" opacity=".2"/>'
    )


def paw(p: Palette) -> str:
    return (
        _rg("ipw-g", [(0, p.accent2), (1, p.accent_deep)]) + SHADOW
        + '<path d="M50 50 C66 50 78 66 74 78 C70 88 58 82 50 82 C42 82 30 88 26 78 C22 66 34 50 50 50Z" fill="url(#ipw-g)"/>'
        + '<ellipse cx="24" cy="44" rx="9" ry="12" fill="url(#ipw-g)"/><ellipse cx="40" cy="26" rx="9" ry="13" fill="url(#ipw-g)"/>'
        + '<ellipse cx="60" cy="26" rx="9" ry="13" fill="url(#ipw-g)"/><ellipse cx="76" cy="44" rx="9" ry="12" fill="url(#ipw-g)"/>'
        + '<ellipse cx="38" cy="20" rx="3" ry="5" fill="#fff" opacity=".5"/>'
    )


def sun(p: Palette) -> str:
    rays = "".join(
        f'<path d="M50 4 L55 16 L45 16Z" fill="#f6b21a" transform="rotate({a} 50 50)"/>' for a in range(0, 360, 30)
    )
    return (
        _rg("isu-g", [(0, "#fff7c2"), (.5, "#ffd33d"), (1, "#f08c00")]) + rays
        + '<circle cx="50" cy="50" r="28" fill="url(#isu-g)"/>'
        + '<ellipse cx="40" cy="38" rx="8" ry="5" fill="#fff" opacity=".55" transform="rotate(-30 40 38)"/>'
    )


def snowflake(p: Palette) -> str:
    arm = ('<g stroke="url(#isn-g)" stroke-width="5" stroke-linecap="round"><path d="M50 50 V8"/>'
           '<path d="M50 22 L40 12 M50 22 L60 12 M50 34 L42 26 M50 34 L58 26"/></g>')
    return (
        _lg("isn-g", [(0, "#ffffff"), (1, "#9ccfff")], 0, 0, 1, 1)
        + "".join(f'<g transform="rotate({a} 50 50)">{arm}</g>' for a in range(0, 360, 60))
        + '<circle cx="50" cy="50" r="6" fill="#fff"/>'
    )


def tree(p: Palette) -> str:
    return (
        _lg("itr-g", [(0, "#4caf50"), (1, "#1b5e20")], 0, 0, 1, 1) + SHADOW
        + '<rect x="44" y="80" width="12" height="12" fill="#6b3b1f"/>'
        + '<path d="M50 8 L80 50 H64 L86 82 H14 L36 50 H20Z" fill="url(#itr-g)"/>'
        + '<path d="M50 8 L36 50 H20Z M36 50 L14 82 H30Z" fill="#fff" opacity=".12"/>'
        + f'<circle cx="40" cy="58" r="4" fill="{p.accent}"/><circle cx="60" cy="44" r="4" fill="#f3c64b"/>'
        + f'<circle cx="62" cy="70" r="4" fill="{p.accent2}"/><circle cx="34" cy="74" r="4" fill="#f3c64b"/>'
        + '<polygon points="50,0 53,7 60,7 54,11 56,18 50,14 44,18 46,11 40,7 47,7" fill="#ffd33d"/>'
    )


def house(p: Palette) -> str:
    return (
        _lg("iho-w", [(0, "#fffaf2"), (1, "#e2d6c4")], 0, 0, 0, 1)
        + _lg("iho-r", [(0, p.accent2), (1, p.accent_deep)], 0, 0, 0, 1) + SHADOW
        + '<rect x="20" y="44" width="60" height="48" fill="url(#iho-w)"/>'
        + '<path d="M10 48 L50 12 L90 48 L84 54 L50 24 L16 54Z" fill="url(#iho-r)"/>'
        + '<rect x="42" y="62" width="16" height="30" rx="2" fill="#6b3b1f"/><circle cx="54" cy="78" r="1.6" fill="#f3c64b"/>'
        + '<rect x="26" y="56" width="12" height="12" fill="#9ccfff" stroke="#fff" stroke-width="2"/>'
        + '<rect x="62" y="56" width="12" height="12" fill="#ffe08a" stroke="#fff" stroke-width="2"/>'
        + '<rect x="66" y="20" width="8" height="18" fill="#8a7f72"/>'
    )


def music(p: Palette) -> str:
    return (
        _lg("imu-g", [(0, p.accent2), (1, p.accent_deep)], 0, 0, 1, 1)
        + '<path d="M36 74 V22 L82 12 V64" stroke="url(#imu-g)" stroke-width="6" fill="none"/>'
        + '<path d="M36 22 L82 12 V24 L36 34Z" fill="url(#imu-g)"/>'
        + '<ellipse cx="26" cy="76" rx="13" ry="10" fill="url(#imu-g)" transform="rotate(-20 26 76)"/>'
        + '<ellipse cx="72" cy="66" rx="13" ry="10" fill="url(#imu-g)" transform="rotate(-20 72 66)"/>'
        + '<ellipse cx="22" cy="72" rx="4" ry="2.5" fill="#fff" opacity=".6" transform="rotate(-20 22 72)"/>'
    )


def vinyl(p: Palette) -> str:
    return (
        '<circle cx="50" cy="50" r="44" fill="#111"/>'
        + "".join(f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="#2a2a2e" stroke-width=".8"/>' for r in range(18, 44, 3))
        + f'<circle cx="50" cy="50" r="15" fill="{p.accent}"/><circle cx="50" cy="50" r="2.5" fill="#000"/>'
        + '<path d="M50 6 A44 44 0 0 1 88 28 L50 50Z" fill="#fff" opacity=".08"/>'
    )


def ring(p: Palette) -> str:
    return (
        _lg("irn-g", GOLD, 0, 0, 1, 1)
        + _lg("irn-d", [(0, "#ffffff"), (.5, "#bfe8ff"), (1, "#6aa9d8")], 0, 0, 1, 1) + SHADOW
        + '<ellipse cx="50" cy="62" rx="30" ry="26" fill="none" stroke="url(#irn-g)" stroke-width="8"/>'
        + '<path d="M38 34 L50 18 L62 34 L50 44Z" fill="url(#irn-d)" stroke="#5b8fb8"/>'
        + '<path d="M38 34 H62 M50 18 L46 34 L50 44 M50 18 L54 34" stroke="#fff" stroke-width=".8" opacity=".8"/>'
        + '<path d="M26 54 C28 46 34 40 42 38" stroke="#fff" stroke-width="2.5" fill="none" opacity=".7"/>'
    )


def cat(p: Palette) -> str:
    return (
        _rg("ica2-g", [(0, "#ffd9a8"), (.6, "#f2994a"), (1, "#a35412")]) + SHADOW
        + '<path d="M18 40 L22 10 L40 28 H60 L78 10 L82 40 C88 66 72 88 50 88 C28 88 12 66 18 40Z" fill="url(#ica2-g)"/>'
        + f'<path d="M24 22 L26 36 L34 30Z M76 22 L74 36 L66 30Z" fill="{p.accent2}" opacity=".8"/>'
        + '<ellipse cx="38" cy="54" rx="6" ry="8" fill="#2a1a0a"/><ellipse cx="62" cy="54" rx="6" ry="8" fill="#2a1a0a"/>'
        + '<circle cx="40" cy="51" r="2" fill="#fff"/><circle cx="64" cy="51" r="2" fill="#fff"/>'
        + f'<path d="M46 64 H54 L50 69Z" fill="{p.accent_deep}"/>'
        + '<path d="M50 69 Q46 75 41 73 M50 69 Q54 75 59 73" stroke="#2a1a0a" stroke-width="1.6" fill="none"/>'
        + '<path d="M30 66 H12 M30 70 L14 76 M70 66 H88 M70 70 L86 76" stroke="#fff" stroke-width="1.2" opacity=".8"/>'
    )


def pizza(p: Palette) -> str:
    return (
        _lg("ipz-c", [(0, "#ffe08a"), (1, "#f2b33d")], 0, 0, 0, 1) + SHADOW
        + '<path d="M12 18 Q50 4 88 18 L50 92Z" fill="url(#ipz-c)"/>'
        + '<path d="M12 18 Q50 4 88 18 L84 26 Q50 12 16 26Z" fill="#c9792b"/>'
        + '<circle cx="40" cy="34" r="7" fill="#c0392b"/><circle cx="60" cy="40" r="7" fill="#c0392b"/><circle cx="50" cy="60" r="6" fill="#c0392b"/>'
        + '<path d="M36 50 q4 2 6 0 M58 26 q4 2 6 0" stroke="#3f8a45" stroke-width="2.5" fill="none"/>'
        + '<path d="M50 78 Q48 86 50 92 Q52 86 50 78Z" fill="#ffd34d"/>'
    )


ICONS: dict[str, Callable[[Palette], str]] = {
    "heart": heart, "star": star, "flower": flower, "gift": gift, "cake": cake, "cup": cup,
    "trophy": trophy, "medal": medal, "balloon": balloon, "ball": ball, "eightball": eightball,
    "chess": chess, "camera": camera, "plane": plane, "book": book, "guitar": guitar,
    "gamepad": gamepad, "paw": paw, "sun": sun, "snowflake": snowflake, "tree": tree,
    "house": house, "music": music, "vinyl": vinyl, "ring": ring, "cat": cat, "pizza": pizza,
}

ICON_NAMES = sorted(ICONS)


def symbol(name: str, p: Palette) -> str:
    return f'<symbol id="i-{name}" viewBox="0 0 100 100">{ICONS[name](p)}</symbol>'


def use(name: str, cls: str = "", size: int | None = None) -> str:
    wh = f' width="{size}" height="{size}"' if size else ""
    return f'<svg class="ico {cls}"{wh} viewBox="0 0 100 100" aria-hidden="true"><use href="#i-{name}"/></svg>'
