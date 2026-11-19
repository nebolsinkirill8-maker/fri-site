(() => {
  const gallery = document.querySelector('#sponsors');
  const pause = gallery.querySelector('#fri-gallery-pause');
  const dialog = gallery.querySelector('dialog');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');

  gallery.querySelectorAll('.fri-frame-row').forEach((row, index) => {
    const track = row.firstElementChild;
    const duration = [58000, 77000, 65000][index];
    const motion = track.animate(
      [{ transform: 'translateX(0)' }, { transform: 'translateX(-50%)' }],
      { duration, iterations: Infinity }
    );
    motion.currentTime = reducedMotion.matches ? 0 : duration * [0.04, 0.38, 0.23][index];
    let drag;
    let suppressClick = false;
    let visible = false;
    function sync() {
      if (pause.checked || dialog.open || reducedMotion.matches || drag || !visible || row.contains(document.activeElement) && document.activeElement.matches(':focus-visible')) motion.pause();
      else motion.play();
    }
    new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; sync(); }).observe(row);
    pause.addEventListener('change', sync);
    reducedMotion.addEventListener('change', sync);
    dialog.addEventListener('close', sync);
    row.addEventListener('focusin', sync);
    row.addEventListener('focusout', () => queueMicrotask(sync));
    row.addEventListener('pointerdown', event => {
      if (!event.isPrimary || event.button !== 0) return;
      suppressClick = false;
      drag = { id: event.pointerId, x: event.clientX, time: motion.currentTime, moved: false };
      sync();
    });
    row.addEventListener('pointermove', event => {
      if (drag?.id !== event.pointerId) return;
      const delta = event.clientX - drag.x;
      if (!drag.moved && Math.abs(delta) < 6) return;
      if (!drag.moved) row.setPointerCapture(event.pointerId);
      drag.moved = true;
      row.dataset.dragging = '';
      const time = drag.time - delta * duration / (track.offsetWidth / 2);
      motion.currentTime = ((time % duration) + duration) % duration;
    });
    function release(event) {
      if (drag?.id !== event.pointerId) return;
      suppressClick = drag.moved;
      drag = null;
      delete row.dataset.dragging;
      sync();
    }
    window.addEventListener('pointerup', release);
    window.addEventListener('pointercancel', release);
    row.addEventListener('keydown', event => {
      if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
      event.preventDefault();
      const time = motion.currentTime + (event.key === 'ArrowRight' ? 4000 : -4000);
      motion.currentTime = ((time % duration) + duration) % duration;
    });
    row.addEventListener('click', event => {
      const frame = event.target.closest('[data-slot]');
      if (!frame || suppressClick && event.detail) return;
      const content = document.getElementById('fri-sponsor-' + frame.dataset.slot);
      dialog.querySelector('[data-sponsor-content]').replaceChildren(content.content.cloneNode(true));
      dialog.showModal();
    });
    dialog.addEventListener('toggle', sync);
    sync();
  });
})();
