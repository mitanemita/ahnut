/* Ахнуть: интерактив открытки. Без внешних зависимостей. API для своих блоков «Принца» — window.Ahnut. */
(() => {
  const B = document.body, H = document.documentElement;
  const SYM = B.dataset.sym || 'heart';
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const rnd = (a, b) => a + Math.random() * (b - a);
  const vibrate = (ms = 12) => { try { navigator.vibrate && navigator.vibrate(ms); } catch (e) {} };
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------- частицы ----------
  function particle(x, y, s) {
    const i = document.createElement('i');
    i.className = 'fx'; i.style.setProperty('--s', s + 'px');
    i.innerHTML = `<svg viewBox="0 0 100 100"><use href="#i-${SYM}"/></svg>`;
    i.style.transform = `translate(${x}px,${y}px)`;
    document.body.appendChild(i);
    return i;
  }
  function burst(x, y, n = 10, spread = 120) {
    if (reduce) return;
    for (let k = 0; k < n; k++) {
      const s = rnd(16, 32), a = rnd(0, Math.PI * 2), d = rnd(spread * .4, spread);
      const el = particle(x, y, s);
      el.animate([{ transform: `translate(${x}px,${y}px) scale(.4)`, opacity: 1 },
                  { transform: `translate(${x + Math.cos(a) * d}px,${y + Math.sin(a) * d - 40}px) rotate(${rnd(-90, 90)}deg) scale(1.2)`, opacity: 0 }],
                 { duration: rnd(700, 1200), easing: 'cubic-bezier(.2,.8,.3,1)' }).onfinish = () => el.remove();
    }
  }
  function rain(n = 18) {
    if (reduce) return;
    const W = innerWidth, Hh = innerHeight;
    for (let k = 0; k < n; k++) {
      const x = rnd(0, W), s = rnd(18, 40), el = particle(x, -50, s);
      el.animate([{ transform: `translate(${x}px,-50px) rotate(0)` },
                  { transform: `translate(${x + rnd(-60, 60)}px,${Hh + 60}px) rotate(${rnd(-300, 300)}deg)` }],
                 { duration: rnd(2200, 4200), delay: rnd(0, 1400), easing: 'linear', fill: 'backwards' }).onfinish = () => el.remove();
    }
  }
  const at = (ev, el) => {
    if (ev && ev.clientX) return [ev.clientX, ev.clientY];
    const r = el.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2];
  };

  // ---------- бутоны: каждое действие — бутон появляется, следующее — раскрывается ----------
  const buds = $$('.decor .bl');
  function grow() {
    const half = buds.find(b => b.classList.contains('show') && !b.classList.contains('open'));
    if (half) { half.classList.add('open'); return; }
    const next = buds.find(b => !b.classList.contains('show'));
    if (next) next.classList.add('show');
  }
  function bloomAll() { buds.forEach((b, i) => setTimeout(() => b.classList.add('show', 'open'), i * 150)); }

  const done = new Set();
  function act(name, ev, el) {
    vibrate();
    if (name) B.classList.add('a-' + name);
    if (!name || !done.has(name)) grow();
    if (name) done.add(name);
    if (ev || el) { const [x, y] = at(ev, el || document.body); burst(x, y); }
  }

  // ---------- конверт ----------
  const intro = document.getElementById('intro');
  if (intro) {
    H.classList.add('lock');
    const t = intro.querySelector('.teaser'), txt = t.dataset.text || '';
    let k = 0; const type = () => { if (k <= txt.length) { t.firstChild.textContent = txt.slice(0, k++); setTimeout(type, 70); } };
    setTimeout(type, 300);
    const open = ev => {
      if (B.classList.contains('a-env')) return;
      act('env', ev, intro.querySelector('.envelope')); rain(14); startMusic();
      setTimeout(() => H.classList.remove('lock'), 2600);
      setTimeout(() => intro.remove(), 3300);
    };
    $$('[data-act=env]', intro).forEach(e => e.addEventListener('click', open));
  } else B.classList.add('no-env');

  // ---------- телефон: ползунок тянется пальцем ----------
  $$('.iphone').forEach(ph => {
    const knob = ph.querySelector('.knob'), slider = ph.querySelector('.slider');
    if (!knob) return;
    const max = () => slider.clientWidth - knob.offsetWidth - 6;
    const unlock = ev => { B.classList.add('a-unlock'); act('unlock', ev, knob); };
    let x0 = null;
    knob.addEventListener('pointerdown', e => { x0 = e.clientX; knob.classList.add('drag'); knob.setPointerCapture(e.pointerId); });
    knob.addEventListener('pointermove', e => { if (x0 === null) return; const dx = Math.max(0, Math.min(max(), e.clientX - x0)); knob.style.transform = `translateX(${dx}px)`; });
    const up = e => { if (x0 === null) return; const dx = e.clientX - x0; x0 = null; knob.classList.remove('drag');
      if (dx > max() * .6 || Math.abs(dx) < 6) unlock(e); else knob.style.transform = ''; };
    knob.addEventListener('pointerup', up); knob.addEventListener('pointercancel', up);
    slider.addEventListener('click', e => { if (e.target === slider || e.target.closest('.slider-text')) unlock(e); });
    // галерея: точки и счётчик по прокрутке
    const g = ph.querySelector('.gallery'), slides = $$('.slide', g), seen = new Set([0]);
    g && g.addEventListener('scroll', () => {
      const i = Math.round(g.scrollLeft / g.clientWidth);
      $$('.dots', ph).forEach(d => [...d.children].forEach((c, j) => c.classList.toggle('on', j === i)));
      if (!seen.has(i)) { seen.add(i); grow(); }
    }, { passive: true });
    slides.forEach(s => s.addEventListener('click', () => g.scrollTo({ left: (slides.indexOf(s) + 1) % slides.length * g.clientWidth, behavior: 'smooth' })));
  });

  // ---------- карточки ----------
  $$('.board .card').forEach(c => c.addEventListener('click', ev => {
    const first = !c.classList.contains('on');
    if (c.classList.contains('flip')) c.classList.toggle('on'); else c.classList.add('on');
    c.classList.remove('hit'); void c.offsetWidth; c.classList.add('hit');
    const pops = c.classList.contains('e-burst') || c.classList.contains('e-shake');
    if (first) act(null, pops ? ev : null); else if (pops) burst(...at(ev, c));
    if (first && (c.classList.contains('word') || c.classList.contains('ticket'))) burst(...at(ev, c), 14);
  }));

  // ---------- письмо ----------
  $$('.note').forEach(n => n.addEventListener('click', () => { if (!n.classList.contains('on')) { n.classList.add('on'); act('letter'); } }));

  // ---------- полароиды: тап — верхняя улетает ----------
  $$('.stack').forEach(st => {
    const ps = $$('.pola', st).reverse(); let top = 0;
    ps.forEach((p, i) => p.style.transform = `rotate(${(i % 2 ? 1 : -1) * rnd(2, 6)}deg)`);
    st.addEventListener('click', ev => {
      const p = ps[top]; if (!p) { ps.forEach(q => { q.classList.remove('gone'); }); top = 0; ps.forEach((q, i) => q.style.transform = `rotate(${(i % 2 ? 1 : -1) * rnd(2, 6)}deg)`); return; }
      p.style.transform = `translate(${rnd(-1, 1) > 0 ? 420 : -420}px,${rnd(-120, 60)}px) rotate(${rnd(-40, 40)}deg)`; p.classList.add('gone'); top++;
      act(null, ev);
    });
  });

  // ---------- викторина ----------
  $$('.quiz').forEach(q => {
    const reply = q.querySelector('.reply');
    $$('.ans', q).forEach(a => a.addEventListener('click', ev => {
      reply.textContent = a.dataset.reply || '';
      if (a.dataset.ok === '1') { a.classList.add('good'); act(null, ev); rain(10); }
      else { a.classList.remove('bad'); void a.offsetWidth; a.classList.add('bad'); vibrate(30); }
    }));
  });

  // ---------- причины ----------
  $$('.reasons').forEach(r => {
    const items = $$('.rs', r), num = r.querySelector('.num'), btn = r.querySelector('.more'); let i = 0;
    const show = () => { items.forEach((x, j) => x.classList.toggle('cur', j === i)); num.textContent = `${i + 1} из ${items.length}`; };
    show();
    btn.addEventListener('click', ev => { i = (i + 1) % items.length; show(); act(null, ev); if (i === items.length - 1) btn.textContent = btn.dataset.last || btn.textContent; });
  });

  // ---------- хронология: появляется при прокрутке ----------
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: .3 });
    $$('.tl .pt').forEach(p => io.observe(p));
  } else $$('.tl .pt').forEach(p => p.classList.add('in'));

  // ---------- финал ----------
  $$('.scene-hit').forEach(h => h.addEventListener('click', ev => { if (!B.classList.contains('a-fin')) { act('fin', ev); rain(16); } }));
  $$('.btn.yes').forEach(y => y.addEventListener('click', ev => { act('yes', ev); rain(36); bloomAll(); vibrate(40); }));
  $$('.btn.no').forEach(no => {
    const box = no.closest('.btns'); const words = JSON.parse(no.dataset.words || '[]'); let n = 0;
    const flee = ev => {
      ev.preventDefault(); vibrate(8);
      const bw = box.clientWidth, bh = box.clientHeight, w = no.offsetWidth, h = no.offsetHeight;
      const yes = box.querySelector('.btn.yes').getBoundingClientRect(), br = box.getBoundingClientRect();
      let x, y, tries = 0;
      do { x = rnd(0, bw - w); y = rnd(0, bh - h); tries++; }
      while (tries < 20 && x + br.left < yes.right + 8 && x + w + br.left > yes.left - 8 && y + br.top < yes.bottom + 8 && y + h + br.top > yes.top - 8);
      no.style.left = x + 'px'; no.style.top = y + 'px'; no.style.transform = `rotate(${rnd(-12, 12)}deg)`;
      n++; if (words[n]) no.textContent = words[n];
      if (n >= words.length + 2) { no.style.display = 'none'; }
    };
    no.addEventListener('pointerdown', flee);
    no.addEventListener('mouseenter', flee);
    no.addEventListener('click', e => e.preventDefault());
  });

  // ---------- музыка («Принц») ----------
  const audio = document.getElementById('bgm'), mb = document.querySelector('.music');
  function startMusic() { if (!audio) return; audio.play().then(() => mb && mb.classList.add('play')).catch(() => {}); }
  mb && mb.addEventListener('click', () => { if (audio.paused) startMusic(); else { audio.pause(); mb.classList.remove('play'); } });
  if (!intro && audio) document.addEventListener('pointerdown', startMusic, { once: true });

  // ---------- API для своих блоков ----------
  window.Ahnut = { act: (name, ev, el) => act(name, ev, el), burst, rain, grow, bloomAll, vibrate,
                   icon: n => `<svg viewBox="0 0 100 100"><use href="#i-${n || SYM}"/></svg>` };
})();
