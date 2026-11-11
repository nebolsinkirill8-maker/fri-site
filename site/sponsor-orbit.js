(() => {
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  document.querySelectorAll('[data-sponsor-orbit]').forEach((scene) => {
    const space = scene.querySelector('.sponsor-space');
    const cards = [...scene.querySelectorAll('.sponsor-sticker')];
    const toggle = scene.querySelector('[data-orbit-toggle]');
    if (!space || !cards.length) {
      if (toggle) toggle.hidden = true;
      return;
    }
    if (toggle) toggle.hidden = false;

    const step = Math.PI * 2 / cards.length;
    let phase = 0;
    let frame = null;
    let previousTime = null;
    let paused = false;
    let focused = false;
    let visible = true;
    let width = 0;
    let maxCardWidth = 0;

    function position() {
      if (reducedMotion.matches) {
        cards.forEach(card => card.style.removeProperty('transform'));
        return;
      }
      const radiusX = Math.max(0, Math.min(width * .32, width / 2 - maxCardWidth * .65 - 12));
      const radiusZ = width < 600 ? 130 : 180;
      cards.forEach((card, index) => {
        const angle = phase + index * step;
        const x = Math.sin(angle) * radiusX;
        const z = Math.cos(angle) * radiusZ;
        const y = width < 600 ? Math.cos(angle) * 58 : 0;
        card.style.transform = `translate(-50%, -50%) translate3d(${x.toFixed(3)}px, ${y.toFixed(3)}px, ${z.toFixed(3)}px)`;
      });
    }

    function canRun() {
      return !reducedMotion.matches && !paused && !focused && visible && !document.hidden;
    }

    function tick(time) {
      frame = null;
      if (!canRun()) { previousTime = null; return; }
      if (previousTime !== null) phase = (phase + Math.min(time - previousTime, 80) * Math.PI * 2 / 32000) % (Math.PI * 2);
      previousTime = time;
      position();
      frame = requestAnimationFrame(tick);
    }

    function sync() {
      scene.classList.toggle('is-orbit', !reducedMotion.matches);
      if (toggle) {
        toggle.disabled = reducedMotion.matches;
        toggle.setAttribute('aria-pressed', String(paused || reducedMotion.matches));
        toggle.textContent = reducedMotion.matches ? 'Вращение отключено' : paused ? 'Продолжить вращение' : 'Пауза';
      }
      if (!canRun()) {
        if (frame !== null) cancelAnimationFrame(frame);
        frame = null;
        previousTime = null;
      } else if (frame === null) frame = requestAnimationFrame(tick);
    }

    function resize() {
      width = space.getBoundingClientRect().width;
      maxCardWidth = Math.max(...cards.map(card => card.offsetWidth || (width < 600 ? 124 : 220)));
      position();
    }

    toggle?.addEventListener('click', () => { paused = !paused; sync(); });
    space.addEventListener('focusin', event => {
      focused = true;
      const index = cards.findIndex(card => card.contains(event.target));
      if (index !== -1) { phase = -index * step; position(); }
      sync();
    });
    space.addEventListener('focusout', event => {
      focused = space.contains(event.relatedTarget);
      sync();
    });
    document.addEventListener('visibilitychange', sync);
    reducedMotion.addEventListener('change', () => { position(); sync(); });
    if (typeof ResizeObserver === 'function') new ResizeObserver(resize).observe(space);
    else window.addEventListener('resize', resize);
    if (typeof IntersectionObserver === 'function') {
      new IntersectionObserver(entries => {
        visible = entries.some(entry => entry.isIntersecting);
        sync();
      }).observe(scene);
    }
    resize();
    sync();
  });
})();
