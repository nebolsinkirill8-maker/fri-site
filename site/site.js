const dialog = document.querySelector("#access-dialog");

document.querySelectorAll("[data-action]").forEach((button) => {
  button.addEventListener("click", () => {
    const registering = button.dataset.action === "register";
    dialog.querySelector("h2").textContent = registering ? "Регистрация" : "Вход";
    dialog.querySelector("p").textContent = registering
      ? "Это локальное превью. Регистрация пока недоступна."
      : "Это локальное превью. Вход пока недоступен.";
    dialog.showModal();
  });
});

if (friContent.prize) document.querySelector("#prize-value").textContent = friContent.prize;

function makeLink(label, url) {
  const element = document.createElement(url ? "a" : "span");
  element.textContent = label;
  if (url) element.href = url;
  return element;
}

const contactList = document.querySelector("#contact-list");
contactList.replaceChildren(...friContent.contacts.map(({ name, url }) => {
  const item = document.createElement("li");
  item.append(makeLink(name, url));
  return item;
}));
document.querySelector("#contact-note").hidden = friContent.contacts.every(({ url }) => url);

if (friContent.sponsors.length) {
  const sponsorList = document.querySelector("#sponsor-list");
  for (const { name, logo, url } of friContent.sponsors) {
    const item = document.createElement("li");
    const card = makeLink(name, url);
    if (logo) {
      const image = document.createElement("img");
      image.src = logo;
      image.alt = "";
      image.loading = "lazy";
      card.prepend(image);
    }
    item.append(card);
    sponsorList.append(item);
  }
  sponsorList.hidden = false;
  document.querySelector("#sponsors-empty").hidden = true;
}

const milestones = friContent.stages
  .map(({ name, startsAt }) => ({ name, timestamp: Date.parse(startsAt) }))
  .filter(({ timestamp }) => Number.isFinite(timestamp))
  .sort((a, b) => a.timestamp - b.timestamp);
const milestoneName = document.querySelector("#milestone-name");
const milestoneTime = document.querySelector("#milestone-time");

function updateMilestone() {
  const now = Date.now();
  const next = milestones.find(({ timestamp }) => timestamp > now);
  if (!next) {
    milestoneName.textContent = friContent.stages.find(({ startsAt }) => !startsAt)?.name ?? "Расписание";
    milestoneTime.textContent = "Дата будет объявлена";
    return;
  }

  milestoneName.textContent = next.name;
  const minutes = Math.ceil((next.timestamp - now) / 60000);
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  milestoneTime.textContent = `${days} д · ${hours} ч · ${minutes % 60} мин`;
}

updateMilestone();
if (milestones.length) setInterval(updateMilestone, 1000);

const organizerCarousel = document.querySelector("#organizer-carousel");
const organizerControls = document.querySelector("#organizer-controls");
const organizerCount = document.querySelector("#organizer-count");
const organizerName = document.querySelector("#organizer-name");
const organizerCards = [...organizerCarousel.querySelectorAll("figure")];
const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
const positions = ["center", "right", "left"];

let activeOrganizer = 0;
let moving = false;
let pendingDirection = 0;
let animations = [];

function setPositions() {
  organizerCards.forEach((card, index) => {
    const distance = (index - activeOrganizer + positions.length) % positions.length;
    card.dataset.position = positions[distance];
  });
}

function announceOrganizer() {
  organizerCards.forEach((card, index) => {
    card.setAttribute("aria-hidden", String(index !== activeOrganizer));
  });
  const caption = organizerCards[activeOrganizer].querySelector("figcaption");
  organizerCount.textContent = `${activeOrganizer + 1} / ${organizerCards.length}`;
  organizerName.textContent = ` · ${caption.querySelector("strong").textContent}, ${caption.querySelector("span").textContent}`;
}

function appearance(card) {
  const { transform, filter, opacity } = getComputedStyle(card);
  return { transform, filter, opacity };
}

async function turnOrganizer(direction) {
  if (moving) {
    pendingDirection = direction;
    return;
  }

  const previous = activeOrganizer;
  const count = organizerCards.length;
  const animate = !reducedMotion.matches && typeof organizerCards[0].animate === "function";
  const before = animate ? organizerCards.map(appearance) : [];
  activeOrganizer = (activeOrganizer + direction + count) % count;
  setPositions();

  if (animate) {
    moving = true;
    const after = organizerCards.map(appearance);
    animations = organizerCards.map((card, index) => {
      const wraps = index !== previous && index !== activeOrganizer;
      card.style.zIndex = index === activeOrganizer ? "3" : index === previous ? "2" : "0";
      // The far card changes sides while invisible. Only adjacent slots travel on screen.
      const exitX = -direction * (organizerCarousel.clientWidth / 2 + card.clientWidth);
      const enterX = -exitX;
      const frames = wraps
        ? [
            { ...before[index], offset: 0 },
            { transform: `translateX(${exitX}px) translateY(-55px) rotate(${-direction * 18}deg) scale(.65)`, opacity: 0, offset: .42 },
            { transform: `translateX(${enterX}px) translateY(30px) rotate(${direction * 14}deg) scale(.65)`, opacity: 0, offset: .43 },
            { ...after[index], offset: 1 },
          ]
        : [before[index], after[index]];
      return card.animate(frames, { duration: 650, easing: "cubic-bezier(.22,.68,.18,1)" });
    });
    await Promise.allSettled(animations.map(({ finished }) => finished));
    animations = [];
    organizerCards.forEach((card) => card.style.removeProperty("z-index"));
    moving = false;
  }

  announceOrganizer();
  if (pendingDirection) {
    const next = pendingDirection;
    pendingDirection = 0;
    turnOrganizer(next);
  }
}

reducedMotion.addEventListener("change", ({ matches }) => {
  if (matches) animations.forEach((animation) => animation.finish());
});

setPositions();
announceOrganizer();
organizerCarousel.classList.add("is-carousel");
organizerControls.hidden = false;

organizerControls.addEventListener("click", (event) => {
  const button = event.target.closest("[data-turn]");
  if (button) turnOrganizer(Number(button.dataset.turn));
});
organizerControls.addEventListener("keydown", (event) => {
  const direction = { ArrowLeft: -1, ArrowRight: 1 }[event.key];
  if (!direction) return;
  event.preventDefault();
  turnOrganizer(direction);
});

let touchStart = null;
organizerCarousel.addEventListener("pointerdown", (event) => {
  if (event.pointerType === "touch") touchStart = { x: event.clientX, y: event.clientY };
});
organizerCarousel.addEventListener("pointerup", (event) => {
  if (!touchStart) return;
  const dx = event.clientX - touchStart.x;
  const dy = event.clientY - touchStart.y;
  touchStart = null;
  if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) turnOrganizer(dx < 0 ? 1 : -1);
});
organizerCarousel.addEventListener("pointercancel", () => { touchStart = null; });

// Animate only when an element enters view. Content stays visible without JS.
const pageAnimations = new Set();
function animateDetail(element, frames, options = {}) {
  if (reducedMotion.matches || !element.animate) return;
  const animation = element.animate(frames, {
    duration: 700, easing: "cubic-bezier(.16,.8,.23,1)", ...options,
  });
  pageAnimations.add(animation);
  // A background tab or interrupted animation must never hide real content.
  const cleanup = setTimeout(() => animation.cancel(), Number(options.duration || 700) + Number(options.delay || 0) + 600);
  animation.finished.catch(() => {}).finally(() => clearTimeout(cleanup));
  animation.finished.catch(() => {}).finally(() => pageAnimations.delete(animation));
}
const revealTargets = document.querySelectorAll(
  '.section-head, .stages li, .milestone, .prize h2, .carousel, .sponsors-empty, .question-list details, .closing-inner > *, .footer-inner > *'
);
document.querySelectorAll('.stages li, .question-list details, .closing-inner > *').forEach((element) => {
  element.dataset.revealDelay = Math.min([...element.parentElement.children].indexOf(element) * 85, 255);
});
if ('IntersectionObserver' in window) {
  const revealObserver = new IntersectionObserver((entries) => {
    for (const { target, isIntersecting } of entries) {
      if (!isIntersecting) continue;
      animateDetail(target, [{ opacity: .85, translate: '0 20px' }, { opacity: 1, translate: '0 0' }], {
        delay: Number(target.dataset.revealDelay || 0), fill: 'backwards',
      });
      revealObserver.unobserve(target);
    }
  }, { threshold: .12 });
  revealTargets.forEach((element) => revealObserver.observe(element));
  const sceneObserver = new IntersectionObserver((entries) => {
    entries.forEach(({ target, isIntersecting }) => {
      if (!isIntersecting) return;
      target.classList.add('is-in-view');
      sceneObserver.unobserve(target);
    });
  }, { threshold: .15 });
  document.querySelectorAll('#tournament, .prize, .closing').forEach((element) => sceneObserver.observe(element));
}
document.querySelectorAll('.question-list details').forEach((detail) => {
  detail.addEventListener('toggle', () => {
    if (detail.open) animateDetail(detail.querySelector('p'), [
      { opacity: 0, translate: '0 -8px' }, { opacity: 1, translate: '0 0' },
    ], { duration: 260 });
  });
});
reducedMotion.addEventListener('change', ({ matches }) => {
  if (matches) pageAnimations.forEach((animation) => animation.cancel());
});

// The prize is a single, first-view sequence, independent of generic reveals.
const prizeScene = document.querySelector('.prize');
const prizeValue = document.querySelector('#prize-value');
const prizeLabel = prizeValue.textContent;
prizeValue.setAttribute('aria-label', prizeLabel);
prizeValue.replaceChildren(...Array.from(prizeLabel, (character, index) => {
  const span = document.createElement('span');
  span.className = character === ' ' ? 'prize-glyph prize-space' : 'prize-glyph';
  span.textContent = character === ' ' ? '\u00a0' : character;
  span.setAttribute('aria-hidden', 'true');
  span.dataset.order = index;
  return span;
}));
const rays = document.createElement('div');
rays.className = 'prize-burst-rays';
rays.setAttribute('aria-hidden', 'true');
prizeScene.prepend(rays);
function firePrize() {
  if (prizeScene.classList.contains('prize-fired')) return;
  prizeScene.classList.add('prize-fired');
  prizeValue.querySelectorAll('.prize-glyph').forEach((glyph, index) => {
    const lean = (index % 2 ? 1 : -1) * 18;
    animateDetail(glyph, [
      { opacity: .75, transform: `translateY(45px) scale(.8) rotate(${lean}deg)`, offset: 0 },
      { opacity: 1, transform: `translateY(-20px) scale(1.28) rotate(${-lean / 4}deg)`, offset: .58 },
      { opacity: 1, transform: 'translateY(5px) scale(.96) rotate(1deg)', offset: .8 },
      { opacity: 1, transform: 'translateY(0) scale(1) rotate(0deg)', offset: 1 },
    ], { duration: 1050, delay: 130 + index * 65, fill: 'backwards' });
  });
  [...rays.children].forEach((ray, index) => {
    const angle = index * 360 / rays.children.length + (index % 3) * 7;
    animateDetail(ray, [
      { opacity: 0, transform: `rotate(${angle}deg) translateX(2vw) scale(.2)` },
      { opacity: .7, transform: `rotate(${angle}deg) translateX(16vw) scale(1)`, offset: .4 },
      { opacity: 0, transform: `rotate(${angle}deg) translateX(43vw) scale(.25)` },
    ], { duration: 650 + index % 3 * 90, delay: 60, fill: 'backwards' });
  });
}
if ('IntersectionObserver' in window) {
  prizeScene.classList.add('prize-ready');
  const prizeObserver = new IntersectionObserver((entries) => {
    if (entries.some(entry => entry.isIntersecting)) {
      firePrize();
      prizeObserver.disconnect();
    }
  }, { threshold: .4 });
  prizeObserver.observe(prizeScene);
} else firePrize();

const soundtrack = document.querySelector('#soundtrack');
const soundPanel = document.querySelector('.sound-panel');
const soundToggle = document.querySelector('.sound-toggle');
const soundStatus = document.querySelector('#sound-status');
const runawayMute = document.querySelector('.runaway-mute');
let dodges = 0;
let autoStartCancelled = false;
const muteHome = runawayMute.parentElement;
function resetRunaway() {
  muteHome.append(runawayMute);
  runawayMute.classList.remove('is-running');
  runawayMute.style.cssText = '';
}
let youtubePlayer = null;
let youtubeReady = false;
let youtubePlaying = false;
let youtubeWanted = false;
let youtubeLoading = false;
let youtubeFailed = false;
const youtubeShell = document.querySelector('.youtube-player-shell');
function updateSound() {
  const playing = friContent.music?.youtubeId ? youtubePlaying : !soundtrack.paused && !soundtrack.muted;
  soundPanel.classList.toggle('is-playing', playing);
  soundToggle.setAttribute('aria-pressed', String(playing));
  soundToggle.setAttribute('aria-label', playing ? 'Выключить музыку' : 'Включить музыку');
  soundStatus.textContent = playing ? 'TRAVIS SCOTT · M — выкл.' : 'Нажми ▶ для музыки';
  runawayMute.disabled = !playing;
  if (!playing) { resetRunaway(); dodges = 0; }
}
function muteTrack() {
  autoStartCancelled = true;
  youtubeWanted = false;
  if (youtubeReady) youtubePlayer.pauseVideo();
  youtubePlaying = false;
  soundtrack.pause(); updateSound();
}
if (friContent.music?.youtubeId) {
  soundToggle.disabled = false;
  updateSound();
  soundStatus.textContent = 'Включить · с 0:35';
  const failYoutube = () => {
    youtubeFailed = true;
    youtubeLoading = false;
    youtubeWanted = false;
    youtubePlaying = false;
    updateSound();
    soundStatus.textContent = 'Видео недоступно · открой YouTube';
  };
  const createYoutubePlayer = () => {
    if (youtubePlayer || !window.YT?.Player) return;
    youtubePlayer = new YT.Player('youtube-player', {
      width: '320', height: '200', videoId: friContent.music.youtubeId,
      playerVars: { playsinline: 1, start: friContent.music.startSeconds, origin: location.origin, controls: 1 },
      events: {
        onReady: ({ target }) => {
          youtubeReady = true; youtubeLoading = false;
          target.setVolume(35);
          if (youtubeWanted) target.loadVideoById({ videoId: friContent.music.youtubeId, startSeconds: friContent.music.startSeconds });
          else target.cueVideoById({ videoId: friContent.music.youtubeId, startSeconds: friContent.music.startSeconds });
        },
        onStateChange: ({ data, target }) => {
          if (youtubeFailed && data !== 1) return;
          youtubeFailed = false;
          youtubePlaying = data === 1;
          if (data === 1) youtubeWanted = true;
          if (data === 2) youtubeWanted = false;
          updateSound();
          if (data === 0 && youtubeWanted) target.loadVideoById({ videoId: friContent.music.youtubeId, startSeconds: friContent.music.startSeconds });
        },
        onError: failYoutube,
        onAutoplayBlocked: () => { soundStatus.textContent = 'Нажми ▶ в плеере'; },
      },
    });
  };
  soundToggle.addEventListener('click', () => {
    if (youtubePlaying || youtubeWanted) { muteTrack(); return; }
    youtubeWanted = true;
    youtubeShell.hidden = false;
    if (youtubeReady) { youtubePlayer.playVideo(); return; }
    soundStatus.textContent = 'Загрузка YouTube…';
    if (window.YT?.Player) { createYoutubePlayer(); return; }
    if (youtubeLoading) return;
    youtubeLoading = true;
    window.onYouTubeIframeAPIReady = createYoutubePlayer;
    const script = document.createElement('script');
    script.src = 'https://www.youtube.com/iframe_api';
    script.onerror = () => { script.remove(); failYoutube(); };
    document.head.append(script);
    setTimeout(() => { if (!youtubeReady && youtubeWanted) failYoutube(); }, 15000);
  });
} else if (friContent.music?.src) {
  const startSeconds = Math.max(0, Number(friContent.music.startSeconds) || 0);
  soundtrack.preload = 'metadata';
  soundtrack.loop = false;
  soundtrack.addEventListener('loadedmetadata', () => {
    soundtrack.currentTime = startSeconds < soundtrack.duration ? startSeconds : 0;
    if (!autoStartCancelled) soundtrack.play().catch(() => { soundStatus.textContent = 'Звук после первого клика'; });
  }, { once: true });
  soundtrack.src = friContent.music.src;
  soundtrack.volume = .35;
  soundToggle.disabled = false;
  updateSound();
  soundStatus.textContent = 'Включить · с 0:35';
  document.addEventListener('click', (event) => {
    if (autoStartCancelled || !soundtrack.paused || event.target.closest('.sound-panel, .runaway-mute')) return;
    soundtrack.play().catch(() => {});
  }, { once: true });
  soundToggle.addEventListener('click', async () => {
    if (!soundtrack.paused) { muteTrack(); return; }
    try { await soundtrack.play(); updateSound(); }
    catch { soundStatus.textContent = 'Не удалось включить трек'; }
  });
  soundtrack.addEventListener('error', () => {
    muteTrack(); soundStatus.textContent = 'Трек недоступен';
  });
  soundtrack.addEventListener('pause', updateSound);
  soundtrack.addEventListener('play', updateSound);
  soundtrack.addEventListener('ended', async () => {
    soundtrack.currentTime = startSeconds < soundtrack.duration ? startSeconds : 0;
    try { await soundtrack.play(); }
    catch { updateSound(); }
  });
}
runawayMute.addEventListener('pointerenter', (event) => {
  if (event.pointerType !== 'mouse' || reducedMotion.matches || runawayMute.disabled || document.activeElement === runawayMute) return;
  document.body.append(runawayMute);
  runawayMute.classList.add('is-running');
  const width = runawayMute.offsetWidth, height = runawayMute.offsetHeight;
  const maxX = Math.max(12, innerWidth - width - 12), maxY = Math.max(12, innerHeight - height - 12);
  let x, y;
  for (let i = 0; i < 10; i++) {
    x = 12 + Math.random() * (maxX - 12); y = 12 + Math.random() * (maxY - 12);
    if (Math.hypot(x - event.clientX, y - event.clientY) > Math.min(innerWidth, innerHeight) * .4) break;
  }
  runawayMute.style.left = `${x}px`; runawayMute.style.top = `${y}px`;
});
runawayMute.addEventListener('click', muteTrack);
runawayMute.addEventListener('focus', resetRunaway);
window.addEventListener('resize', resetRunaway);
document.addEventListener('keydown', (event) => {
  if (event.code !== 'KeyM' || event.ctrlKey || event.metaKey || event.altKey || event.target.closest('input, textarea, select, [contenteditable]')) return;
  muteTrack();
});

const readingProgress = document.createElement('div');
readingProgress.className = 'reading-progress';
readingProgress.setAttribute('aria-hidden', 'true');
document.body.append(readingProgress);
let progressQueued = false;
function updateReadingProgress() {
  progressQueued = false;
  const max = document.documentElement.scrollHeight - innerHeight;
  readingProgress.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, Math.max(0, scrollY / max)) : 0) + ')';
}
addEventListener('scroll', () => { if (!progressQueued) { progressQueued = true; requestAnimationFrame(updateReadingProgress); } }, { passive: true });
addEventListener('resize', updateReadingProgress);
updateReadingProgress();

