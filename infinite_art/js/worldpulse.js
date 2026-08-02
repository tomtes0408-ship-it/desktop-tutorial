// "יומן חזותי של האנושות" — נתונים חיים מהעולם, שמפעילים מודולציה עדינה
// ומוגבלת על היצירה. זה *לא* משנה אף פעם את המבנה, המסלול הפרקטלי או
// זמני-הלידה של הפרטים (אלה תמיד דטרמיניסטיים ונשארים ניתנים לשחזור) —
// זה רק "מזג האוויר" הרגעי שעל פני היצירה: גוון, זוהר, קצב תנועה, וערפל
// אטמוספרי קליל.
//
// כל מקור נתונים עצמאי לחלוטין. כישלון של אחד (רשת, CORS, שינוי API
// חיצוני) לעולם לא משפיע על האחרים ולא על היצירה עצמה — הוא פשוט משאיר
// את הממד הזה בערכו הניטרלי (או האחרון שהתקבל בהצלחה).

const FETCH_TIMEOUT_MS = 7000;
const POLL_INTERVAL_MS = 5 * 60 * 1000;

const NEUTRAL = Object.freeze({
  hue: 0, // הטיית גוון עדינה (רדיאנים) — נגזרת מרוח גלובלית
  glow: 1, // מכפיל בהירות/אנרגיה — פעילות גיאומגנטית/סולארית
  flow: 1, // מכפיל קצב אנימציה — פעילות סייסמית
  warmth: 0, // הטיית "חום" הפלטה — תנודת מחיר הזהב
  haze: 0, // ערפל אטמוספרי עדין — כיסוי עננים ממוצע
});

const current = { ...NEUTRAL };
const target = { ...NEUTRAL };
const sources = {
  quake: { ok: false, label: 'רעידות אדמה', detail: '' },
  solar: { ok: false, label: 'פעילות סולארית', detail: '' },
  weather: { ok: false, label: 'מזג אוויר גלובלי', detail: '' },
  gold: { ok: false, label: 'שוק הזהב', detail: '' },
};

function clamp(x, a, b) {
  return Math.min(b, Math.max(a, x));
}

async function safeFetchJson(url) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, { signal: controller.signal });
    if (!res.ok) throw new Error('status ' + res.status);
    return await res.json();
  } catch (e) {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

async function fetchEarthquakes() {
  const data = await safeFetchJson(
    'https://earthquake.usgs.gov/earthquake/feed/v1.0/summary/2.5_day.geojson'
  );
  const feats = data && Array.isArray(data.features) ? data.features : null;
  if (!feats) return;
  const mags = feats.map((f) => f.properties && f.properties.mag).filter((m) => typeof m === 'number');
  if (mags.length === 0) return;
  const maxMag = Math.max(...mags);
  target.flow = clamp(1 + mags.length / 60 + Math.max(0, maxMag - 4) * 0.03, 0.85, 1.4);
  sources.quake.ok = true;
  sources.quake.detail = `${mags.length} רעידות ב-24 שעות, החזקה ביותר M${maxMag.toFixed(1)}`;
}

async function fetchSolarActivity() {
  const data = await safeFetchJson('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json');
  if (!Array.isArray(data) || data.length < 2) return;
  const last = data[data.length - 1];
  const kp = Number(last && last[1]);
  if (!Number.isFinite(kp)) return;
  target.glow = clamp(1 + (kp / 9) * 0.2, 1, 1.22);
  sources.solar.ok = true;
  sources.solar.detail = `מדד Kp נוכחי: ${kp}`;
}

const SAMPLE_CITIES = [
  { lat: 31.77, lon: 35.21 },
  { lat: 40.71, lon: -74.0 },
  { lat: 35.68, lon: 139.69 },
  { lat: -33.92, lon: 18.42 },
];
async function fetchWeather() {
  const results = await Promise.all(
    SAMPLE_CITIES.map((c) =>
      safeFetchJson(
        `https://api.open-meteo.com/v1/forecast?latitude=${c.lat}&longitude=${c.lon}&current=cloud_cover,wind_speed_10m`
      )
    )
  );
  const valid = results.filter((r) => r && r.current);
  if (valid.length === 0) return;
  const avgCloud = valid.reduce((s, r) => s + r.current.cloud_cover, 0) / valid.length;
  const avgWind = valid.reduce((s, r) => s + r.current.wind_speed_10m, 0) / valid.length;
  target.haze = clamp(avgCloud / 100, 0, 1) * 0.07;
  target.hue = clamp((avgWind - 10) / 40, -0.06, 0.06);
  sources.weather.ok = true;
  sources.weather.detail = `כיסוי עננים ${Math.round(avgCloud)}%, רוח ${avgWind.toFixed(1)} קמ"ש (ממוצע גלובלי)`;
}

async function fetchGold() {
  const data = await safeFetchJson('https://data-asg.goldprice.org/dbXRates/USD');
  const item = data && Array.isArray(data.items) ? data.items[0] : null;
  if (!item || typeof item.pcXau !== 'number') return;
  target.warmth = clamp(item.pcXau / 2, -1, 1) * 0.1;
  sources.gold.ok = true;
  sources.gold.detail = `זהב ${item.pcXau >= 0 ? '+' : ''}${item.pcXau.toFixed(2)}% היום`;
}

async function pollAll() {
  await Promise.allSettled([fetchEarthquakes(), fetchSolarActivity(), fetchWeather(), fetchGold()]);
}

let started = false;
export function startWorldPulse() {
  if (started) return;
  started = true;
  pollAll();
  setInterval(pollAll, POLL_INTERVAL_MS);
}

// התכנסות רכה בכל פריים כך שערכים חדשים אף פעם לא "קופצים" פתאום —
// המזג-אוויר של היצירה משתנה בהדרגה, כמו מזג אוויר אמיתי.
export function tickWorldPulse(dt) {
  const rate = 1 - Math.pow(0.0005, Math.max(dt, 0));
  for (const k of Object.keys(NEUTRAL)) {
    current[k] += (target[k] - current[k]) * rate;
  }
  return current;
}

export function getWorldPulseSources() {
  return sources;
}
