// Small enhancements only: the page works without this file.
(function () {
  document.documentElement.classList.add('js');

  const nav = document.getElementById('nav');
  const menu = document.getElementById('menu');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // mobile menu
  const closeMenu = () => {
    nav.classList.remove('open');
    menu.setAttribute('aria-expanded', 'false');
  };
  menu.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    menu.setAttribute('aria-expanded', String(open));
  });
  document.querySelectorAll('#navlinks a').forEach(a => a.addEventListener('click', closeMenu));
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMenu(); });

  // fade sections in as they arrive
  const reveal = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('in');
        reveal.unobserve(e.target);
      }
    });
  }, { rootMargin: '0px 0px -8% 0px' });
  document.querySelectorAll('.reveal').forEach(el => reveal.observe(el));

  // highlight the section in view
  const links = new Map([...document.querySelectorAll('.navlinks > a[href^="#"]')].map(a => [a.hash.slice(1), a]));
  const spy = new IntersectionObserver(entries => {
    entries.forEach(e => {
      const link = links.get(e.target.id);
      if (link) link.classList.toggle('active', e.isIntersecting);
    });
  }, { rootMargin: '-45% 0px -50% 0px' });
  links.forEach((_, id) => { const s = document.getElementById(id); if (s) spy.observe(s); });

  // nav background and a gentle hero parallax, one rAF per frame at most
  const portrait = document.querySelector('.hero-portrait');
  const name = document.querySelector('.hero-name');
  let ticking = false;
  const onScroll = () => {
    const y = window.scrollY;
    nav.classList.toggle('scrolled', y > 24);
    if (!reduced && y < window.innerHeight * 1.2) {
      portrait.style.transform = `translate3d(0, ${y * 0.12}px, 0) scale(${1 - Math.min(y, 600) / 6000})`;
      name.style.transform = `translate3d(0, ${y * 0.3}px, 0)`;
    }
    ticking = false;
  };
  window.addEventListener('scroll', () => {
    if (!ticking) { ticking = true; requestAnimationFrame(onScroll); }
  }, { passive: true });
  onScroll();
})();
