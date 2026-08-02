// יקום אמנותי אינסופי — מנוע התצוגה, הקלט וממשק המשתמש
import { VERTEX_SRC, FRAGMENT_SRC } from './shaders.js';
import { FractalCamera } from './camera.js';
import { startWorldPulse, tickWorldPulse, getWorldPulseSources } from './worldpulse.js';

const canvas = document.getElementById('gl');
const hud = {
  depth: document.getElementById('hudDepth'),
  scale: document.getElementById('hudScale'),
  time: document.getElementById('hudTime'),
  era: document.getElementById('hudEra'),
  fps: document.getElementById('hudFps'),
  pulse: document.getElementById('hudPulse'),
};
const timeline = document.getElementById('timeline');
const playBtn = document.getElementById('playBtn');
const speedSel = document.getElementById('speedSel');
const resetBtn = document.getElementById('resetBtn');
const randomBtn = document.getElementById('randomBtn');
const helpToggle = document.getElementById('helpToggle');
const helpPanel = document.getElementById('helpPanel');

const gl = canvas.getContext('webgl2', { antialias: false, alpha: false });
if (!gl) {
  document.getElementById('unsupported').classList.add('visible');
  throw new Error('WebGL2 not supported');
}

function compileShader(type, src) {
  const sh = gl.createShader(type);
  gl.shaderSource(sh, src);
  gl.compileShader(sh);
  if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(sh);
    gl.deleteShader(sh);
    throw new Error('Shader compile error: ' + log);
  }
  return sh;
}

const program = gl.createProgram();
gl.attachShader(program, compileShader(gl.VERTEX_SHADER, VERTEX_SRC));
gl.attachShader(program, compileShader(gl.FRAGMENT_SHADER, FRAGMENT_SRC));
gl.linkProgram(program);
if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
  throw new Error('Program link error: ' + gl.getProgramInfoLog(program));
}
gl.useProgram(program);

const vao = gl.createVertexArray();
gl.bindVertexArray(vao);

const uniforms = {};
for (const name of [
  'uResolution', 'uAspect', 'uSeed', 'uLocalUV', 'uZoomFrac', 'uDepth', 'uTime',
  'uWorldHue', 'uWorldGlow', 'uWorldFlow', 'uWorldWarmth', 'uWorldHaze',
]) {
  uniforms[name] = gl.getUniformLocation(program, name);
}

const camera = new FractalCamera();

const state = {
  // מתחילים כמה "שנים" אחרי בראשית כדי שתהיה יצירה גלויה מיד עם הטעינה;
  // רגע ה-0 המוחלט (קנבס ריק לחלוטין) עדיין נגיש בגרירת הציר לתחילתו.
  time: 60,
  playing: false,
  speed: Number(speedSel.value), // שנים לשנייה
  dragging: false,
  lastPointer: null,
  dpr: Math.min(window.devicePixelRatio || 1, 2),
};

function resize() {
  const w = Math.floor(canvas.clientWidth * state.dpr);
  const h = Math.floor(canvas.clientHeight * state.dpr);
  if (canvas.width !== w || canvas.height !== h) {
    canvas.width = w;
    canvas.height = h;
    gl.viewport(0, 0, w, h);
  }
}
window.addEventListener('resize', resize);

// --- קלט: זום (גלגלת/פינץ'), גרירה (יד) ---
canvas.addEventListener(
  'wheel',
  (e) => {
    e.preventDefault();
    const amount = -e.deltaY * 0.0016;
    camera.zoomBy(amount);
  },
  { passive: false }
);

canvas.addEventListener('pointerdown', (e) => {
  state.dragging = true;
  state.lastPointer = { x: e.clientX, y: e.clientY };
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove', (e) => {
  if (!state.dragging) return;
  const dx = (e.clientX - state.lastPointer.x) / canvas.clientHeight;
  const dy = (e.clientY - state.lastPointer.y) / canvas.clientHeight;
  camera.pan(dx, dy);
  state.lastPointer = { x: e.clientX, y: e.clientY };
});
window.addEventListener('pointerup', () => {
  state.dragging = false;
});

// פינץ' למגע (שני אצבעות)
let pinchDist = null;
canvas.addEventListener(
  'touchmove',
  (e) => {
    if (e.touches.length === 2) {
      e.preventDefault();
      const [a, b] = e.touches;
      const d = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
      if (pinchDist != null) {
        camera.zoomBy((d - pinchDist) * 0.004);
      }
      pinchDist = d;
    }
  },
  { passive: false }
);
canvas.addEventListener('touchend', () => {
  pinchDist = null;
});

// --- ציר זמן ---
const MAX_YEARS = 200000;
function timelineToTime(norm) {
  return Math.pow(norm, 3) * MAX_YEARS;
}
function timeToTimeline(t) {
  return Math.pow(Math.max(t, 0) / MAX_YEARS, 1 / 3);
}
timeline.addEventListener('input', () => {
  state.time = timelineToTime(Number(timeline.value) / 1000);
  state.playing = false;
  playBtn.textContent = '▶';
});

playBtn.addEventListener('click', () => {
  state.playing = !state.playing;
  playBtn.textContent = state.playing ? '⏸' : '▶';
});
speedSel.addEventListener('change', () => {
  state.speed = Number(speedSel.value);
});
resetBtn.addEventListener('click', () => {
  camera.reset();
  state.time = 0;
  state.playing = false;
  playBtn.textContent = '▶';
  timeline.value = 0;
});
randomBtn.addEventListener('click', () => {
  camera.teleportRandom(4 + Math.floor(Math.random() * 4));
});
helpToggle.addEventListener('click', () => {
  helpPanel.classList.toggle('visible');
});

function eraName(t) {
  if (t < 40) return 'בראשית';
  if (t < 400) return 'התהוות';
  if (t < 4000) return 'בגרות';
  if (t < 40000) return 'עידן עתיק';
  return 'נצח';
}
function scaleName(depth) {
  const names = ['תת-אטומי', 'מיקרוסקופי', 'תאי', 'מרקם', 'דיוקן', 'נופי', 'יבשתי', 'כוכבי', 'קוסמי'];
  // depth 0 => 'דיוקן' (אמצע הרשימה); זום פנימה מוריד לעבר תת-אטומי, זום החוצה מעלה לעבר קוסמי
  const centered = 4 - depth;
  const clamped = Math.max(0, Math.min(names.length - 1, centered));
  return names[clamped];
}
function formatYears(t) {
  return Math.floor(t).toLocaleString('he-IL');
}

let lastFrame = performance.now();
let fpsSmooth = 60;

function updatePulseHud() {
  const sources = getWorldPulseSources();
  const active = Object.values(sources).filter((s) => s.ok);
  if (active.length === 0) {
    hud.pulse.textContent = 'ממתין…';
    hud.pulse.title = 'עדיין לא התקבלו נתונים חיים מהעולם (או שאין גישת רשת)';
    return;
  }
  hud.pulse.textContent = `${active.length}/4 מקורות`;
  hud.pulse.title = active.map((s) => `${s.label}: ${s.detail}`).join('\n');
}

function frame(now) {
  const dt = Math.min((now - lastFrame) / 1000, 0.1);
  lastFrame = now;
  fpsSmooth = fpsSmooth * 0.9 + (1 / Math.max(dt, 1e-6)) * 0.1;

  if (state.playing) {
    state.time += dt * state.speed;
    if (state.time > MAX_YEARS) state.time = MAX_YEARS;
    timeline.value = Math.round(timeToTimeline(state.time) * 1000);
  }

  resize();

  const pulse = tickWorldPulse(dt);

  const u = camera.uniforms();
  gl.uniform2f(uniforms.uResolution, canvas.width, canvas.height);
  gl.uniform1f(uniforms.uAspect, canvas.width / canvas.height);
  gl.uniform1ui(uniforms.uSeed, u.seed);
  gl.uniform2f(uniforms.uLocalUV, u.localUV.x, u.localUV.y);
  gl.uniform1f(uniforms.uZoomFrac, u.zoomFrac);
  gl.uniform1i(uniforms.uDepth, u.depth);
  gl.uniform1f(uniforms.uTime, state.time);
  gl.uniform1f(uniforms.uWorldHue, pulse.hue);
  gl.uniform1f(uniforms.uWorldGlow, pulse.glow);
  gl.uniform1f(uniforms.uWorldFlow, pulse.flow);
  gl.uniform1f(uniforms.uWorldWarmth, pulse.warmth);
  gl.uniform1f(uniforms.uWorldHaze, pulse.haze);

  gl.drawArrays(gl.TRIANGLES, 0, 3);

  hud.depth.textContent = camera.continuousDepth.toFixed(2);
  hud.scale.textContent = scaleName(Math.round(camera.continuousDepth));
  hud.time.textContent = formatYears(state.time);
  hud.era.textContent = eraName(state.time);
  hud.fps.textContent = Math.round(fpsSmooth);

  requestAnimationFrame(frame);
}

timeline.value = Math.round(timeToTimeline(state.time) * 1000);
resize();
startWorldPulse();
setInterval(updatePulseHud, 2000);
requestAnimationFrame(frame);
