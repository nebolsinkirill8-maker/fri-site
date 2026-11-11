const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('site/sponsor-orbit.js', 'utf8');

function node(extra = {}) {
  const handlers = {};
  return Object.assign({
    handlers, attrs: {}, style: { removeProperty(key) { delete this[key]; } },
    addEventListener(name, handler) { handlers[name] = handler; },
    setAttribute(name, value) { this.attrs[name] = value; },
    contains(target) { return this === target; },
  }, extra);
}

function orbit(count = 4, reduced = false) {
  const cards = Array.from({ length: count }, () => node());
  const toggle = node();
  const space = node({ getBoundingClientRect: () => ({ width: 360 }), contains: target => cards.includes(target) });
  const classes = new Set();
  const scene = node({
    classList: { toggle(name, on) { on ? classes.add(name) : classes.delete(name); } },
    querySelector: selector => selector === '.sponsor-space' ? space : toggle,
    querySelectorAll: () => cards,
  });
  const document = node({ hidden: false, querySelectorAll: () => [scene] });
  const motion = node({ matches: reduced });
  let frameId = 0;
  const pending = new Map();
  let observer;
  vm.runInNewContext(source, {
    document, window: node(), matchMedia: () => motion,
    requestAnimationFrame(callback) { pending.set(++frameId, callback); return frameId; },
    cancelAnimationFrame(id) { pending.delete(id); },
    IntersectionObserver: class { constructor(callback) { observer = callback; } observe() {} },
  });
  return {
    cards, toggle, space, document, motion, classes, pending,
    visibility(visible) { observer([{ isIntersecting: visible }]); },
    tick(time) { const current = [...pending.values()]; pending.clear(); current.forEach(callback => callback(time)); },
  };
}

test('stickers orbit with depth, auto-advance, and a single sponsor is not cloned', () => {
  const instance = orbit();
  assert.match(instance.cards[0].style.transform, /58\.000px, 130\.000px/);
  assert.match(instance.cards[2].style.transform, /-58\.000px, -130\.000px/);
  const initial = instance.cards[0].style.transform;
  instance.tick(0);
  instance.tick(50);
  assert.notEqual(instance.cards[0].style.transform, initial);
  assert.equal(orbit(1).cards.length, 1);
  assert.equal(orbit(0).toggle.hidden, true);
});

test('pointer hover does not stop orbit; explicit pause is retained across visibility changes', () => {
  const instance = orbit();
  assert.equal(instance.space.handlers.pointerenter, undefined);
  assert.equal(instance.space.handlers.pointerleave, undefined);
  instance.toggle.handlers.click();
  assert.equal(instance.toggle.attrs['aria-pressed'], 'true');
  assert.equal(instance.pending.size, 0);
  instance.visibility(false);
  instance.visibility(true);
  assert.equal(instance.pending.size, 0);
  instance.toggle.handlers.click();
  assert.equal(instance.pending.size, 1);
  instance.document.hidden = true;
  instance.document.handlers.visibilitychange();
  assert.equal(instance.pending.size, 0);
});

test('focus moves rear sticker to the front and pauses motion', () => {
  const instance = orbit();
  instance.space.handlers.focusin({ target: instance.cards[2] });
  assert.match(instance.cards[2].style.transform, /0\.000px, 58\.000px, 130\.000px/);
  assert.equal(instance.pending.size, 0);
  instance.space.handlers.focusout({ relatedTarget: null });
  assert.equal(instance.pending.size, 1);
});

test('reduced motion stays static and changes without a page reload', () => {
  const instance = orbit(4, true);
  assert.equal(instance.pending.size, 0);
  assert.equal(instance.toggle.disabled, true);
  assert.equal(instance.classes.has('is-orbit'), false);
  instance.motion.matches = false;
  instance.motion.handlers.change();
  assert.equal(instance.classes.has('is-orbit'), true);
  assert.equal(instance.pending.size, 1);
  instance.motion.matches = true;
  instance.motion.handlers.change();
  assert.equal(instance.cards[0].style.transform, undefined);
  assert.equal(instance.pending.size, 0);
});
