// Enhancements only: every page works without this file.
(function () {
  const nav = document.getElementById('nav');
  const menu = document.getElementById('menu');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = window.matchMedia('(pointer: fine)').matches;

  // ----- nav: current page, mobile menu, background once scrolled
  const page = document.body.className.replace(/^page-/, '');
  document.querySelectorAll('.navlinks [data-page]').forEach(a => {
    if (a.dataset.page === page) { a.classList.add('active'); a.setAttribute('aria-current', 'page'); }
  });
  const closeMenu = () => { nav.classList.remove('open'); menu.setAttribute('aria-expanded', 'false'); };
  menu.addEventListener('click', () => menu.setAttribute('aria-expanded', String(nav.classList.toggle('open'))));
  document.querySelectorAll('#navlinks a').forEach(a => a.addEventListener('click', closeMenu));
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMenu(); });

  // ----- reveal on scroll, staggered among siblings that arrive together
  const reveal = new IntersectionObserver(entries => {
    entries.filter(e => e.isIntersecting).forEach((e, i) => {
      e.target.style.setProperty('--stagger', i);
      e.target.classList.add('in');
      reveal.unobserve(e.target);
    });
  }, { rootMargin: '0px 0px -6% 0px' });
  document.querySelectorAll('.reveal').forEach(el => reveal.observe(el));

  // ----- numbers count up when they come into view
  const counters = new IntersectionObserver(entries => {
    entries.filter(e => e.isIntersecting).forEach(e => {
      const el = e.target, end = +el.dataset.count, suffix = el.dataset.suffix || '';
      counters.unobserve(el);
      if (reduced) return;
      const start = performance.now(), dur = 1100;
      const tick = now => {
        const t = Math.min(1, (now - start) / dur), eased = 1 - Math.pow(1 - t, 3);
        el.textContent = Math.round(end * eased) + suffix;
        if (t < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }, { threshold: .6 });
  document.querySelectorAll('[data-count]').forEach(el => counters.observe(el));

  // ----- spotlight that follows the cursor on cards
  if (finePointer) {
    document.addEventListener('pointermove', e => {
      const card = e.target.closest && e.target.closest('.spot');
      if (!card) return;
      const r = card.getBoundingClientRect();
      card.style.setProperty('--mx', `${e.clientX - r.left}px`);
      card.style.setProperty('--my', `${e.clientY - r.top}px`);
    }, { passive: true });
  }

  // ----- /work/ filters; animated with a view transition where the browser has it
  const grid = document.getElementById('work-grid');
  if (grid) {
    const buttons = [...document.querySelectorAll('.filter')];
    const cards = [...grid.querySelectorAll('.case-card')];
    const apply = area => {
      let shown = 0;
      cards.forEach(c => {
        const hit = area === 'all' || c.dataset.areas.split(' ').includes(area);
        c.classList.toggle('hide', !hit);
        c.classList.add('in');
        if (hit) shown++;
      });
      buttons.forEach(b => b.classList.toggle('on', b.dataset.area === area));
      document.getElementById('empty').hidden = shown > 0;
    };
    buttons.forEach(b => b.addEventListener('click', () => {
      const area = b.dataset.area;
      history.replaceState(null, '', area === 'all' ? location.pathname : `#${area}`);
      if (document.startViewTransition && !reduced) document.startViewTransition(() => apply(area));
      else apply(area);
    }));
    const fromHash = location.hash.slice(1);
    if (fromHash && buttons.some(b => b.dataset.area === fromHash)) apply(fromHash);
  }

  // ----- hero parallax, at most one update per frame
  const portrait = document.querySelector('.hero-portrait');
  let ticking = false;
  const onScroll = () => {
    const y = window.scrollY;
    nav.classList.toggle('scrolled', y > 24);
    if (portrait && !reduced && y < window.innerHeight * 1.2) {
      portrait.style.transform = `translate3d(0, ${y * 0.12}px, 0) scale(${1 - Math.min(y, 600) / 6000})`;
    }
    ticking = false;
  };
  window.addEventListener('scroll', () => {
    if (!ticking) { ticking = true; requestAnimationFrame(onScroll); }
  }, { passive: true });
  onScroll();
})();
