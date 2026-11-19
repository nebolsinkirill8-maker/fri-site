(() => {
  const sidebar = document.querySelector('.home-sidebar');
  const toggle = document.querySelector('.fri-menu-toggle');
  if (!sidebar || !toggle) return;

  const close = sidebar.querySelector('.fri-menu-close');
  const backdrop = document.querySelector('.fri-menu-backdrop');
  const desktop = matchMedia('(min-width:761px)');
  const background = new Map();
  document.body.classList.add('drawer-ready');

  function setOpen(open, restoreFocus = false) {
    // Restore the previous inert state before applying the next modal state.
    for (const [element, wasInert] of background) element.inert = wasInert;
    background.clear();
    const modal = open && !desktop.matches;
    if (modal) {
      for (const element of document.body.children) {
        if (element === sidebar || element === backdrop) continue;
        background.set(element, element.inert);
        element.inert = true;
      }
      sidebar.setAttribute('role', 'dialog');
      sidebar.setAttribute('aria-modal', 'true');
    } else {
      sidebar.removeAttribute('role');
      sidebar.removeAttribute('aria-modal');
    }
    document.body.classList.toggle('fri-drawer-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    sidebar.inert = !open;
    if (restoreFocus) toggle.focus();
  }

  function sync() {
    const hadFocus = sidebar.contains(document.activeElement);
    sidebar.querySelector('details').open = true;
    setOpen(false, hadFocus);
  }

  toggle.addEventListener('click', () => {
    setOpen(true);
    close.focus();
  });
  close.addEventListener('click', () => setOpen(false, true));
  backdrop.addEventListener('click', () => setOpen(false, true));
  sidebar.addEventListener('click', event => {
    const link = event.target.closest('a');
    if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const destination = new URL(link.href);
    const samePage = destination.origin === location.origin
      && destination.pathname === location.pathname
      && destination.search === location.search;
    const target = samePage && destination.hash
      ? document.getElementById(decodeURIComponent(destination.hash.slice(1)))
      : null;
    setOpen(false, !target);
    if (target) {
      const hadTabIndex = target.hasAttribute('tabindex');
      if (!hadTabIndex) {
        target.setAttribute('tabindex', '-1');
        target.addEventListener('blur', () => target.removeAttribute('tabindex'), { once: true });
      }
      target.focus({ preventScroll: true });
    }
  });
  document.addEventListener('keydown', event => {
    if (!document.body.classList.contains('fri-drawer-open')) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      setOpen(false, true);
      return;
    }
    if (event.key !== 'Tab' || desktop.matches) return;
    const items = [...sidebar.querySelectorAll('a[href], button, input, select, textarea, [tabindex]')]
      .filter(element => !element.disabled && element.tabIndex >= 0 && element.getClientRects().length);
    const first = items[0];
    const last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });
  desktop.addEventListener('change', sync);
  sync();
})();
