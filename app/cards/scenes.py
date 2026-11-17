"""Финальные сцены (SVG 360×280). Анимации — классы, которые включает CSS по триггеру #t-fin.

couple — двое тянутся к сердцу (только пара); hug — обнимашки (семья);
highfive — «дай пять» (друзья); trophy — кубок и аплодисменты (коллеги);
cake — торт со свечами (день рождения); gift — подарок (универсально).
"""
from app.cards.themes import Palette

SKIN = ('<linearGradient id="sk" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f1c7a4"/>'
        '<stop offset="1" stop-color="#c98e6b"/></linearGradient>')


def _defs(p: Palette) -> str:
    return (
        "<defs>" + SKIN
        + f'<linearGradient id="outA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{p.accent2}"/>'
        f'<stop offset=".45" stop-color="{p.accent}"/><stop offset="1" stop-color="{p.accent_deep}"/></linearGradient>'
        '<linearGradient id="outB" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5a5a64"/>'
        '<stop offset="1" stop-color="#202026"/></linearGradient>'
        '<linearGradient id="pants" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#2a3550"/>'
        '<stop offset=".5" stop-color="#3d4a6b"/><stop offset="1" stop-color="#1e2740"/></linearGradient>'
        '<radialGradient id="glow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#fff" stop-opacity=".9"/>'
        f'<stop offset=".4" stop-color="{p.accent2}" stop-opacity=".5"/><stop offset="1" stop-color="{p.accent}" stop-opacity="0"/></radialGradient>'
        "</defs>"
    )


def _hair(cx: float, style: str) -> tuple[str, str]:
    """(волосы сзади головы, волосы/убор спереди)"""
    if style == "long":
        back = f'<path d="M{cx-22} 60 Q{cx-26} 34 {cx} 34 Q{cx+26} 34 {cx+22} 60 L{cx+26} 110 Q{cx+12} 116 {cx} 106 Q{cx-12} 116 {cx-26} 110Z" fill="#3a2418"/>'
        front = f'<path d="M{cx-20} 56 Q{cx-16} 38 {cx+2} 39 Q{cx+18} 40 {cx+20} 56 Q{cx+10} 46 {cx-4} 48 Q{cx-14} 50 {cx-20} 56Z" fill="#4a2e1f"/>'
        return back, front
    if style == "bun":
        front = (f'<circle cx="{cx}" cy="34" r="10" fill="#6b4a2e"/>'
                 f'<path d="M{cx-20} 58 Q{cx-20} 38 {cx} 38 Q{cx+20} 38 {cx+20} 58 Q{cx+8} 46 {cx} 48 Q{cx-10} 46 {cx-20} 58Z" fill="#6b4a2e"/>')
        return "", front
    if style == "cap":
        front = (f'<path d="M{cx-21} 58 Q{cx-20} 36 {cx+1} 36 Q{cx+22} 37 {cx+21} 58Z" fill="#26262c"/>'
                 f'<path d="M{cx-21} 58 Q{cx-32} 56 {cx-40} 60 Q{cx-28} 62 {cx-18} 61Z" fill="#1a1a1f"/>'
                 f'<path d="M{cx-14} 44 Q{cx} 36 {cx+16} 46" fill="none" stroke="#fff" stroke-opacity=".15" stroke-width="2"/>')
        return "", front
    if style == "gray":
        front = f'<path d="M{cx-21} 60 Q{cx-22} 36 {cx} 37 Q{cx+22} 36 {cx+21} 60 Q{cx+16} 44 {cx} 46 Q{cx-16} 44 {cx-21} 60Z" fill="#c9c6c2"/>'
        return "", front
    front = f'<path d="M{cx-20} 58 Q{cx-21} 37 {cx} 37 Q{cx+21} 37 {cx+20} 58 Q{cx+12} 45 {cx} 47 Q{cx-12} 45 {cx-20} 58Z" fill="#2f2118"/>'
    return "", front


def person(cx: float, hair: str, outfit: str, cls: str = "", arms: str = "") -> str:
    """Человечек ростом ~230px, ноги стоят на y=258. arms — SVG рук (рисуются поверх тела)."""
    back, front = _hair(cx, hair)
    leg = lambda x1, x2: f'<line x1="{x1}" y1="176" x2="{x2}" y2="256" stroke="url(#pants)" stroke-width="13" stroke-linecap="round"/>'  # noqa: E731
    return (
        f'<g class="person {cls}">'
        + back
        + leg(cx - 10, cx - 13) + leg(cx + 10, cx + 13)
        + f'<path d="M{cx-22} 256 h16 l2 7 h-20z M{cx+6} 256 h16 l4 7 h-20z" fill="#f2efea"/>'
        + f'<path d="M{cx-24} 106 Q{cx} 94 {cx+24} 106 L{cx+22} 182 H{cx-22} Z" fill="url(#{outfit})"/>'
        + f'<path d="M{cx-12} 101 Q{cx} 109 {cx+12} 101" fill="none" stroke="#000" stroke-opacity=".25" stroke-width="3"/>'
        + f'<path d="M{cx-18} 112 L{cx-16} 176" stroke="#fff" stroke-opacity=".18" stroke-width="3"/>'
        + f'<rect x="{cx-6}" y="82" width="12" height="16" rx="5" fill="url(#sk)"/>'
        + f'<ellipse cx="{cx}" cy="62" rx="20" ry="23" fill="url(#sk)"/>'
        + f'<ellipse cx="{cx-7}" cy="54" rx="5" ry="3" fill="#fff" opacity=".25"/>'
        + front + arms + "</g>"
    )


def arm(x1, y1, x2, y2, outfit: str, cls: str = "", origin: tuple[float, float] | None = None) -> str:
    o = f' style="transform-origin:{origin[0]}px {origin[1]}px"' if origin else ""
    return (f'<g class="{cls}"{o}><line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="url(#{outfit})" stroke-width="11" stroke-linecap="round"/>'
            f'<circle cx="{x2}" cy="{y2}" r="6" fill="url(#sk)"/></g>')


GROUND = '<ellipse cx="180" cy="264" rx="160" ry="8" fill="#000" opacity=".35"/>'


def _heart(cx, cy, s, cls="", fill="url(#hrt)") -> str:
    return (f'<g class="{cls}" style="transform-origin:{cx}px {cy}px"><g transform="translate({cx-50*s} {cy-48*s}) scale({s})">'
            '<path d="M50 88 C20 66 6 50 6 31 C6 17 17 7 30 7 C39 7 46 12 50 20 C54 12 61 7 70 7 C83 7 94 17 94 31 C94 50 80 66 50 88Z" fill="' + fill + '"/>'
            '<path d="M22 15 C14 18 10 25 11 33 C15 25 21 21 31 19Z" fill="#fff" opacity=".7"/></g></g>')


def _heart_grad(p: Palette) -> str:
    return (f'<defs><radialGradient id="hrt" cx=".35" cy=".28" r=".8"><stop offset="0" stop-color="#fff"/>'
            f'<stop offset=".22" stop-color="{p.accent2}"/><stop offset=".6" stop-color="{p.accent}"/>'
            f'<stop offset="1" stop-color="{p.accent_deep}"/></radialGradient></defs>')


def couple(p: Palette) -> str:
    a = person(70, "long", "outA", "pl", arm(92, 110, 142, 114, "outA", "reach rl", (92, 110)) + arm(48, 110, 40, 162, "outA"))
    b = person(290, "short", "outB", "pr", arm(268, 110, 218, 114, "outB", "reach rr", (268, 110)) + arm(312, 110, 322, 164, "outB"))
    return (_defs(p) + _heart_grad(p) + GROUND + a + b
            + '<circle class="halo" cx="180" cy="112" r="46" fill="url(#glow)"/>'
            + _heart(180, 112, .5, "beat"))


def hug(p: Palette) -> str:
    a = person(110, "bun", "outA", "hl", arm(132, 110, 160, 140, "outA", "hug-arm hal", (132, 110)) + arm(88, 110, 80, 164, "outA"))
    b = person(250, "gray", "outB", "hr", arm(228, 110, 200, 140, "outB", "hug-arm har", (228, 110)) + arm(272, 110, 280, 164, "outB"))
    return (_defs(p) + _heart_grad(p) + GROUND + a + b
            + '<circle class="halo" cx="180" cy="40" r="40" fill="url(#glow)"/>'
            + _heart(180, 40, .34, "pop-heart"))


def highfive(p: Palette) -> str:
    a = person(100, "short", "outA", "fl", arm(122, 106, 150, 56, "outA", "five fal", (122, 106)) + arm(78, 110, 70, 164, "outA"))
    b = person(260, "cap", "outB", "fr", arm(238, 106, 210, 56, "outB", "five far", (238, 106)) + arm(282, 110, 290, 164, "outB"))
    rays = "".join(f'<path d="M180 48 L{180+6} {48-40} L{180-6} {48-40}Z" transform="rotate({a} 180 48)"/>' for a in range(0, 360, 30))
    return (_defs(p) + GROUND + a + b
            + f'<g class="flash" style="transform-origin:180px 48px"><g fill="{p.accent2}" opacity=".9">{rays}</g>'
            + '<circle cx="180" cy="48" r="16" fill="url(#glow)"/></g>')


def trophy(p: Palette) -> str:
    gold = ('<linearGradient id="tg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8a5a00"/><stop offset=".3" stop-color="#f6d36b"/>'
            '<stop offset=".5" stop-color="#fff6c9"/><stop offset=".7" stop-color="#d9a520"/><stop offset="1" stop-color="#7a4c00"/></linearGradient>')
    cup = ('<g class="cup" style="transform-origin:180px 150px">'
           '<path d="M146 62 H214 V92 C214 118 198 132 180 132 C162 132 146 118 146 92Z" fill="url(#tg)" stroke="#7a4c00"/>'
           '<path d="M146 70 C124 70 124 104 152 108 M214 70 C236 70 236 104 208 108" fill="none" stroke="url(#tg)" stroke-width="7"/>'
           '<rect x="173" y="130" width="14" height="22" fill="url(#tg)"/><rect x="154" y="152" width="52" height="10" rx="2" fill="url(#tg)"/>'
           '<path d="M156 70 V94 C156 108 163 118 172 122" stroke="#fff" stroke-width="4" fill="none" opacity=".6" stroke-linecap="round"/>'
           '<polygon points="180,78 186,92 200,92 189,100 193,114 180,106 167,114 171,100 160,92 174,92" fill="#fff" opacity=".6"/></g>')
    podium = (f'<rect x="118" y="162" width="124" height="96" rx="4" fill="{p.surface}"/>'
              f'<rect x="118" y="162" width="124" height="12" fill="{p.accent}"/>'
              f'<text x="180" y="226" text-anchor="middle" font-family="Oswald,Arial Narrow,sans-serif" font-size="44" font-weight="600" fill="{p.accent}">1</text>'
              '<rect x="122" y="176" width="6" height="78" fill="#fff" opacity=".18"/>')
    hand = lambda x, flip: (f'<g class="clap" style="transform-origin:{x}px 200px"><g transform="translate({x} 186) scale({flip} 1)">'  # noqa: E731
                            '<path d="M0 40 C-10 26 -6 10 4 6 L8 -10 C9 -16 16 -15 16 -9 L16 4 L20 -14 C21 -20 28 -19 28 -13 L26 6 L32 -8 C34 -13 40 -11 39 -5 L34 14 C40 6 46 10 43 16 C38 30 30 42 16 46Z" fill="url(#sk)" stroke="#b07a58" stroke-width="1"/></g></g>')
    return ('<defs>' + SKIN + gold + f'<radialGradient id="spot" cx=".5" cy=".2" r=".8"><stop offset="0" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="{p.accent2}" stop-opacity="0"/></radialGradient></defs>'
            + '<path class="spot" d="M150 0 H210 L270 260 H90Z" fill="url(#spot)"/>' + GROUND + podium + cup
            + hand(60, 1) + hand(300, -1))


def cake(p: Palette) -> str:
    cream = '<linearGradient id="cr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fffaf2"/><stop offset="1" stop-color="#e9d9c3"/></linearGradient>'
    glaze = f'<linearGradient id="gl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p.accent2}"/><stop offset="1" stop-color="{p.accent}"/></linearGradient>'
    flame = '<radialGradient id="fl" cx=".5" cy=".65" r=".6"><stop offset="0" stop-color="#fffbe0"/><stop offset=".5" stop-color="#ffd34d"/><stop offset="1" stop-color="#ff7a00"/></radialGradient>'
    candles = ""
    for i, x in enumerate((140, 180, 220)):
        candles += (f'<rect x="{x-5}" y="70" width="10" height="38" rx="3" fill="#fff" stroke="#ddd"/>'
                    f'<path d="M{x-5} 78 l10 -5 M{x-5} 88 l10 -5 M{x-5} 98 l10 -5" stroke="{p.accent}" stroke-width="2.5"/>'
                    f'<g class="flame" style="transform-origin:{x}px 68px;animation-delay:-{i*.13}s">'
                    f'<path d="M{x} 44 C{x+9} 56 {x+8} 66 {x} 68 C{x-8} 66 {x-9} 56 {x} 44Z" fill="url(#fl)"/>'
                    f'<circle cx="{x}" cy="58" r="16" fill="#ffd34d" opacity=".18"/></g>'
                    f'<path class="smoke" style="animation-delay:{i*.2}s" d="M{x} 66 C{x-6} 56 {x+6} 48 {x} 38 C{x-6} 30 {x+4} 22 {x} 14" stroke="#ccc" stroke-width="2.5" fill="none" stroke-linecap="round"/>')
    return ('<defs>' + cream + glaze + flame + '</defs>' + GROUND
            + '<ellipse cx="180" cy="254" rx="118" ry="14" fill="#e6e1dc"/><ellipse cx="180" cy="250" rx="118" ry="12" fill="#f6f3ef"/>'
            + '<path d="M84 170 H276 V240 Q180 258 84 240Z" fill="url(#cr)"/>'
            + '<path d="M84 170 Q96 190 108 174 Q120 192 132 174 Q144 192 156 174 Q168 192 180 174 Q192 192 204 174 Q216 192 228 174 Q240 192 252 174 Q264 190 276 170 V162 H84Z" fill="url(#gl)"/>'
            + '<path d="M112 108 H248 V170 H112Z" fill="url(#cr)"/>'
            + '<path d="M112 108 Q124 126 136 112 Q148 128 160 112 Q172 128 184 112 Q196 128 208 112 Q220 128 232 112 Q240 124 248 108 V102 H112Z" fill="url(#gl)"/>'
            + '<rect x="90" y="186" width="5" height="48" fill="#fff" opacity=".5"/>'
            + "".join(f'<circle cx="{x}" cy="{y}" r="3" fill="{c}"/>' for x, y, c in
                      ((110, 210, p.accent), (150, 222, "#f3c64b"), (200, 216, p.accent_deep), (244, 206, "#6fbf73"), (130, 150, "#f3c64b"), (226, 146, p.accent)))
            + candles)


def gift(p: Palette) -> str:
    box = f'<linearGradient id="bx" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{p.accent2}"/><stop offset=".5" stop-color="{p.accent}"/><stop offset="1" stop-color="{p.accent_deep}"/></linearGradient>'
    rib = '<linearGradient id="rb" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8a5a00"/><stop offset=".5" stop-color="#fff6c9"/><stop offset="1" stop-color="#b8860b"/></linearGradient>'
    rays = "".join(f'<path d="M180 150 L{180+5} 30 L{180-5} 30Z" transform="rotate({a} 180 150)"/>' for a in range(-75, 76, 15))
    return ('<defs>' + box + rib + '</defs>' + GROUND
            + '<radialGradient id="ry" cx=".5" cy="1" r="1"><stop offset="0" stop-color="#fff" stop-opacity=".9"/>'
            + f'<stop offset=".6" stop-color="{p.accent2}" stop-opacity=".5"/><stop offset="1" stop-color="{p.accent2}" stop-opacity="0"/></radialGradient>'
            + f'<g class="rays" style="transform-origin:180px 150px" fill="url(#ry)">{rays}</g>'
            + '<rect x="110" y="150" width="140" height="106" rx="4" fill="url(#bx)"/>'
            + '<rect x="110" y="150" width="140" height="8" fill="#000" opacity=".2"/>'
            + '<rect x="170" y="150" width="20" height="106" fill="url(#rb)"/>'
            + '<rect x="116" y="160" width="6" height="90" fill="#fff" opacity=".25"/>'
            + '<g class="lid" style="transform-origin:250px 150px">'
            + '<rect x="100" y="122" width="160" height="30" rx="4" fill="url(#bx)"/><rect x="170" y="122" width="20" height="30" fill="url(#rb)"/>'
            + '<path d="M180 122 C160 90 130 94 136 110 C140 120 166 120 180 122Z M180 122 C200 90 230 94 224 110 C220 120 194 120 180 122Z" fill="url(#rb)" stroke="#7a4c00"/>'
            + '</g>')


SCENES = {"couple": couple, "hug": hug, "highfive": highfive, "trophy": trophy, "cake": cake, "gift": gift}
ROMANTIC_SCENES = {"couple"}
