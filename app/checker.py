"""Самопроверка открытки в настоящем браузере (Playwright) на ширине телефона 375px.

Открывает HTML, нажимает конверт и интерактивные элементы, собирает ошибки JS, горизонтальную
прокрутку и скриншоты секций — их потом смотрит нейросеть («Принц»).
В Docker браузер живёт в отдельном сервисе (PLAYWRIGHT_WS), локально — запускается сам.
"""
import asyncio
import logging
import re
from dataclasses import dataclass, field

from app.config import settings

log = logging.getLogger(__name__)

# Что нельзя в своих блоках: сеть, хранилища, внешние ресурсы, выход за рамки блока
FORBIDDEN = [
    (r"\bfetch\s*\(", "fetch"), (r"XMLHttpRequest", "XMLHttpRequest"), (r"WebSocket", "WebSocket"),
    (r"EventSource", "EventSource"), (r"sendBeacon", "sendBeacon"), (r"\bimport\s*\(", "import()"),
    (r"\beval\s*\(", "eval"), (r"new\s+Function", "new Function"), (r"document\.cookie", "cookie"),
    (r"localStorage|sessionStorage|indexedDB", "хранилища браузера"), (r"window\.open", "window.open"),
    (r"\blocation\s*(\.|=)", "location"), (r"document\.write", "document.write"),
    (r"https?://", "внешние ссылки"), (r"<\s*/?\s*(script|style|iframe|object|embed|link|meta|base|form)\b", "запрещённый тег"),
    (r"javascript:", "javascript:"), (r"@import", "@import"), (r"feTurbulence", "feTurbulence (тормозит iPhone)"),
    (r"url\(\s*['\"]?(?!data:|#)", "внешние url() в стилях"), (r"\bon[a-z]+\s*=", "inline-обработчики (on...=) в HTML"),
    (r"\b(parent|top|opener|frameElement)\s*[.\[]", "js: доступ к окну снаружи открытки"),
]


def code_problems(spec) -> list[str]:
    out = []
    for b in spec.blocks:
        if b.type != "custom":
            continue
        for part, code in (("html", b.html), ("css", b.css), ("js", b.js)):
            for pat, what in FORBIDDEN:
                if part != "html" and what.startswith("inline"):
                    continue
                if part != "js" and what.startswith("js:"):
                    continue
                if re.search(pat, code, flags=re.I):
                    out.append(f"свой блок «{b.step or 'custom'}», {part}: нельзя {what}")
        if b.css and not re.search(r"#cx\b", b.css):
            out.append(f"свой блок «{b.step or 'custom'}»: стили должны начинаться с #cx (иначе ломают остальную открытку)")
    return out


@dataclass
class CheckReport:
    errors: list[str] = field(default_factory=list)
    overflow: int = 0                     # на сколько px шире экрана
    clipped: list[str] = field(default_factory=list)  # элементы своих блоков, вылезающие за экран (обрезаны)
    shots: list[tuple[str, bytes]] = field(default_factory=list)  # (подпись, jpeg)

    @property
    def hard_problems(self) -> list[str]:
        out = [f"ошибка JS: {e}" for e in self.errors[:8]]
        if self.overflow > 2:
            out.append(f"горизонтальная прокрутка: страница шире экрана на {self.overflow}px")
        for c in self.clipped[:5]:
            out.append(f"в своём блоке элемент не помещается в экран 375px и обрезан: {c}")
        return out


# Одна проверка за раз: Chromium ест 300–500 МБ, на маленьком сервере параллельные проверки упрутся в память
_one_at_a_time = asyncio.Semaphore(1)


async def check_card(html: str, max_shots: int = 8) -> CheckReport:
    async with _one_at_a_time:
        return await _check_card(html, max_shots)


async def _check_card(html: str, max_shots: int) -> CheckReport:
    from playwright.async_api import async_playwright

    rep = CheckReport()
    async with async_playwright() as pw:
        browser = await (pw.chromium.connect(settings.playwright_ws, timeout=30000) if settings.playwright_ws
                         else pw.chromium.launch())
        try:
            ctx = await browser.new_context(viewport={"width": 375, "height": 740}, device_scale_factor=1,
                                            is_mobile=True, has_touch=True)
            page = await ctx.new_page()
            page.on("pageerror", lambda e: rep.errors.append(str(e)[:300]))
            page.on("console", lambda m: m.type == "error" and rep.errors.append(m.text[:300]))
            await page.set_content(html, wait_until="load", timeout=30000)
            await page.wait_for_timeout(1200)
            if await page.locator("#intro [data-act=env]").count():
                rep.shots.append(("конверт", await page.screenshot(type="jpeg", quality=60)))
                await page.locator("#intro .envelope").click(force=True)
                await page.wait_for_timeout(3600)
            n = await page.locator("main > section").count()
            for i in range(n):
                sec = page.locator("main > section").nth(i)
                await sec.evaluate("e => e.scrollIntoView({block:'start'})")
                await page.wait_for_timeout(500)
                cls = await sec.get_attribute("class") or ""
                if "custom" in cls:  # свои блоки — нажимаем всё нажимаемое
                    btns = sec.locator("button, [role=button]")
                    for k in range(min(await btns.count(), 12)):
                        try:
                            await btns.nth(k).click(timeout=1500, force=True)
                            await page.wait_for_timeout(250)
                        except Exception:  # noqa: BLE001
                            pass
                    await page.wait_for_timeout(800)
                if len(rep.shots) < max_shots and ("custom" in cls or "final" in cls or i < 3):
                    label = f"секция {i + 1}" + (" (свой блок, после нажатий)" if "custom" in cls else "")
                    rep.shots.append((label, await page.screenshot(type="jpeg", quality=60)))
            rep.errors += await page.evaluate("window.__cardErrors || []")
            rep.clipped = await page.evaluate("""() => [...document.querySelectorAll('.custom *')].filter(e => {
                const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
                return r.width > 0 && cs.visibility !== 'hidden' && cs.opacity !== '0' && (r.right > innerWidth + 2 || r.left < -2);
              }).slice(0, 5).map(e => `${e.tagName.toLowerCase()}.${[...e.classList].join('.')} (${Math.round(e.getBoundingClientRect().width)}px)`)""")
            sw = await page.evaluate("document.documentElement.scrollWidth")
            rep.overflow = max(0, sw - 375)
        finally:
            await browser.close()
    return rep
