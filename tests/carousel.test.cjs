const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

// Exercise the actual carousel block without adding exports to the browser script.
const source = fs.readFileSync('site/site.js', 'utf8');
const carouselSource = source.slice(source.indexOf('const organizerCarousel ='), source.indexOf('// Animate only when'));

function carousel(count, animated = false) {
  const pending = [];
  const cards = Array.from({ length: count }, (_, index) => ({
    dataset: {}, attrs: {}, clientWidth: 300, frames: [],
    style: { removeProperty() {} },
    setAttribute(name, value) { this.attrs[name] = value; },
    querySelector() { return { querySelector: (selector) => ({ textContent: selector === 'strong' ? `Person ${index}` : 'Organizer' }) }; },
    animate(frames) {
      this.frames.push(frames);
      let finish;
      const finished = new Promise(resolve => { finish = resolve; });
      pending.push(finish);
      return { finished, finish };
    },
  }));
  const events = {};
  const carouselNode = { querySelectorAll: () => cards, classList: { add() {} }, clientWidth: 1200, addEventListener(name, callback) { events[name] = callback; } };
  const controls = { addEventListener() {} };
  const counter = {};
  const nodes = { '#organizer-carousel': carouselNode, '#organizer-controls': controls, '#organizer-count': counter, '#organizer-name': {} };
  const context = vm.createContext({
    document: { querySelector: selector => nodes[selector] },
    matchMedia: () => ({ matches: !animated, addEventListener() {} }),
    getComputedStyle: card => ({ transform: card.dataset.position, filter: 'none', opacity: card.dataset.position === 'hidden' ? '0' : '1', visibility: card.dataset.position === 'hidden' ? 'hidden' : 'visible' }),
  });
  vm.runInContext(carouselSource, context);
  return {
    cards, counter, events,
    turn: direction => vm.runInContext(`turnOrganizer(${direction})`, context),
    async finish() { pending.splice(0).forEach(resolve => resolve()); await new Promise(resolve => setImmediate(resolve)); },
  };
}

function assertSlots(instance, active, count) {
  assert.equal(instance.cards[active].dataset.position, 'center');
  assert.equal(instance.cards[(active + 1) % count].dataset.position, 'right');
  assert.equal(instance.cards[(active + count - 1) % count].dataset.position, 'left');
  assert.equal(instance.cards.filter(card => card.dataset.position === 'hidden').length, count - 3);
  assert.equal(instance.cards.filter(card => card.attrs['aria-hidden'] === 'false').length, 1);
  assert.equal(instance.counter.textContent, `${active + 1} / ${count}`);
}

for (const count of [3, 4]) {
  test(`${count} organizers cycle forward/backward without duplicate slots`, async () => {
    const instance = carousel(count);
    assertSlots(instance, 0, count);
    for (let i = 1; i <= count * 2; i++) {
      await instance.turn(1);
      assertSlots(instance, i % count, count);
    }
    for (let i = 1; i <= count * 2; i++) {
      await instance.turn(-1);
      assertSlots(instance, (count - i % count) % count, count);
    }
  });
}

test('four organizers animate hidden cards with invisible wrapping frames', async () => {
  const instance = carousel(4, true);
  const turn = instance.turn(1);
  assert.equal(instance.cards[2].frames[0][0].opacity, '0');
  assert.equal(instance.cards[2].frames[0][0].visibility, 'hidden');
  assert.equal(instance.cards[3].frames[0].at(-1).opacity, '0');
  assert.equal(instance.cards[3].frames[0].at(-1).visibility, 'hidden');
  for (const index of [2, 3]) {
    assert.equal(instance.cards[index].frames[0][1].opacity, 0);
    assert.equal(instance.cards[index].frames[0][2].opacity, 0);
  }
  await instance.finish();
  await turn;
  assertSlots(instance, 1, 4);
});

test('rapid input keeps the latest requested direction', async () => {
  const instance = carousel(4, true);
  instance.turn(1);
  instance.turn(1);
  instance.turn(-1);
  await instance.finish();
  await instance.finish();
  assertSlots(instance, 0, 4);
});
