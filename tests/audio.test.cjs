const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

// Run the browser's sound controls without downloading media or a browser.
const source = fs.readFileSync('site/site.js', 'utf8');
const controls = source.slice(source.indexOf('const soundtrack ='), source.indexOf('const readingProgress ='));

function eventTarget(properties = {}) {
  const events = new Map();
  return Object.assign({
    addEventListener(name, callback, { once } = {}) { events.set(name, { callback, once }); },
    emit(name, event = {}) {
      const listener = events.get(name);
      if (!listener) return;
      if (listener.once) events.delete(name);
      return listener.callback(event);
    },
  }, properties);
}

function sound(optIn) {
  const audio = eventTarget({
    paused: true, duration: 120, playCalls: 0,
    hasAttribute(name) { return Object.hasOwn(this, name); },
    async play() { this.playCalls++; this.paused = false; this.emit('play'); },
    pause() { this.paused = true; this.emit('pause'); },
  });
  const toggle = eventTarget({ setAttribute(name, value) { this[name] = value; } });
  const panel = { hasAttribute: name => optIn && name === 'data-opt-in', classList: { toggle() {} } };
  const nodes = { '#soundtrack': audio, '.sound-toggle': toggle, '.sound-panel': panel, '#sound-status': {} };
  const document = eventTarget({ querySelector: selector => nodes[selector] ?? null });
  vm.runInNewContext(controls, { document, friContent: { music: { src: '/static/music.mp3', startSeconds: 35 } } });
  return { audio, toggle, document };
}

test('opt-in soundtrack loads only on its button; starting offset, pause/resume, mute and repeat are preserved', async () => {
  const { audio, toggle, document } = sound(true);
  const elsewhere = { closest: () => null };
  document.emit('click', { target: elsewhere });
  assert.equal(audio.hasAttribute('src'), false);
  assert.equal(audio.playCalls, 0);

  await toggle.emit('click');
  assert.equal(audio.src, '/static/music.mp3');
  audio.emit('loadedmetadata');
  assert.equal(audio.currentTime, 35);
  assert.equal(audio.playCalls, 1);
  assert.equal(toggle['aria-pressed'], 'true');

  audio.currentTime = 50;
  document.emit('keydown', { code: 'KeyM', target: elsewhere });
  assert.equal(audio.paused, true);
  assert.equal(toggle['aria-pressed'], 'false');
  await toggle.emit('click');
  assert.equal(audio.currentTime, 50);
  assert.equal(audio.playCalls, 2);
  await audio.emit('ended');
  assert.equal(audio.currentTime, 35);
  assert.equal(audio.playCalls, 3);
  await toggle.emit('click');
  assert.equal(audio.paused, true);
});

test('legacy static panel still initializes and starts the track at the configured offset', () => {
  const { audio } = sound(false);
  assert.equal(audio.src, '/static/music.mp3');
  audio.emit('loadedmetadata');
  assert.equal(audio.currentTime, 35);
  assert.equal(audio.playCalls, 1);
});
