// "יומן חזותי של האנושות" — נתונים חיים מהעולם, שמפעילים מודולציה עדינה
// ומוגבלת על היצירה.
//
// עיקרון-על שלא נשבר: הנתונים האלה *לעולם* לא נוגעים במבנה הפרקטלי, במסלול
// ה-seed או בזמני-הלידה של הפרטים. כל אלה נשארים דטרמיניסטיים לחלוטין
// וניתנים לשחזור זהה בכל מחשב ובכל זמן. הנתונים משפיעים אך ורק על שכבת
// הגימור — גוון, זוהר, קצב, מרקם ועדשה — כלומר על "מזג האוויר" הרגעי של
// היצירה, לא על הגאולוגיה שלה.
//
// כל מקור עצמאי לחלוטין: כישלון של אחד (רשת, CORS, שינוי API, חסימה
// ארגונית) לעולם לא משפיע על האחרים ולא על היצירה — הוא פשוט משאיר את
// הממד שלו בערך הניטרלי, והיצירה ממשיכה לעבוד בדיוק כרגיל.
//
// ⚠️ הערה על אימות: כל המקורות כאן נבחרו כ-API-ים פתוחים ללא מפתח, אך
// סביבת הפיתוח שבה נכתב הקוד חוסמת גישה לרשת חיצונית, ולכן מבנה התגובות
// מבוסס על התיעוד הרשמי של כל שירות ונבדק מול mock-ים — לא מול השרתים
// החיים. ראו INFINITE_ART_README.md.

const FETCH_TIMEOUT_MS = 8000;
const POLL_INTERVAL_MS = 5 * 60 * 1000;

// ערכים ניטרליים = "אין נתונים". היצירה נראית בדיוק כך כשאין רשת בכלל.
const NEUTRAL = Object.freeze({
  hue: 0, // הטיית גוון עדינה (רדיאנים) — רוח גלובלית
  glow: 1, // מכפיל בהירות — פעילות גיאומגנטית/סולארית
  flow: 1, // מכפיל קצב אנימציה — פעילות סייסמית
  warmth: 0, // הטיית חום הפלטה — תנודת מחיר הזהב
  haze: 0, // ערפל אטמוספרי — כיסוי עננים
  turbulence: 0, // חוסר שקט במרקם העדין — קצב זרימת המידע בעולם
  focus: 0, // התכנסות המבט למרכז — ריכוזיות תשומת הלב הציבורית
  tension: 0, // ניגודיות/קרירות — נפח השיח הפוליטי
  fracture: 0, // סדקים דקיקים — תשומת לב לתיאוריות קונספירציה
  accentHue: 0, // גוון הדגשה (רדיאנים) — צבע יצירת האמנות של היום
  accentAmount: 0, // עוצמת ההדגשה
});

const current = { ...NEUTRAL };
const target = { ...NEUTRAL };

function clamp(x, a, b) {
  return Math.min(b, Math.max(a, x));
}

async function safeFetchJson(url) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, { signal: controller.signal });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return await res.json();
  } catch (e) {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

function utcDaysAgo(n) {
  const d = new Date(Date.now() - n * 86400000);
  const p = (x) => String(x).padStart(2, '0');
  return { y: d.getUTCFullYear(), m: p(d.getUTCMonth() + 1), d: p(d.getUTCDate()) };
}

// --- מקורות גאופיזיים ---------------------------------------------------

async function readEarthquakes(s) {
  const data = await safeFetchJson(
    'https://earthquake.usgs.gov/earthquake/feed/v1.0/summary/2.5_day.geojson'
  );
  const feats = data && Array.isArray(data.features) ? data.features : null;
  if (!feats) throw new Error('no features');
  const mags = feats
    .map((f) => f.properties && f.properties.mag)
    .filter((m) => typeof m === 'number');
  if (mags.length === 0) throw new Error('no magnitudes');
  const maxMag = Math.max(...mags);
  target.flow = clamp(1 + mags.length / 60 + Math.max(0, maxMag - 4) * 0.03, 0.85, 1.4);
  s.detail = `${mags.length} רעידות ב-24 שעות, החזקה M${maxMag.toFixed(1)}`;
}

async function readSolar(s) {
  const data = await safeFetchJson(
    'https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'
  );
  if (!Array.isArray(data) || data.length < 2) throw new Error('bad shape');
  const kp = Number(data[data.length - 1][1]);
  if (!Number.isFinite(kp)) throw new Error('bad Kp');
  target.glow = clamp(1 + (kp / 9) * 0.2, 1, 1.22);
  s.detail = `מדד Kp נוכחי: ${kp}`;
}

const SAMPLE_CITIES = [
  { lat: 31.77, lon: 35.21 },
  { lat: 40.71, lon: -74.0 },
  { lat: 35.68, lon: 139.69 },
  { lat: -33.92, lon: 18.42 },
];
async function readWeather(s) {
  const results = await Promise.all(
    SAMPLE_CITIES.map((c) =>
      safeFetchJson(
        `https://api.open-meteo.com/v1/forecast?latitude=${c.lat}&longitude=${c.lon}` +
          '&current=cloud_cover,wind_speed_10m'
      )
    )
  );
  const valid = results.filter((r) => r && r.current);
  if (valid.length === 0) throw new Error('no cities responded');
  const avgCloud = valid.reduce((a, r) => a + r.current.cloud_cover, 0) / valid.length;
  const avgWind = valid.reduce((a, r) => a + r.current.wind_speed_10m, 0) / valid.length;
  target.haze = clamp(avgCloud / 100, 0, 1) * 0.07;
  target.hue = clamp((avgWind - 10) / 40, -0.06, 0.06);
  s.detail = `עננות ${Math.round(avgCloud)}%, רוח ${avgWind.toFixed(1)} קמ"ש`;
}

async function readGold(s) {
  const data = await safeFetchJson('https://data-asg.goldprice.org/dbXRates/USD');
  const item = data && Array.isArray(data.items) ? data.items[0] : null;
  if (!item || typeof item.pcXau !== 'number') throw new Error('bad shape');
  target.warmth = clamp(item.pcXau / 2, -1, 1) * 0.1;
  s.detail = `זהב ${item.pcXau >= 0 ? '+' : ''}${item.pcXau.toFixed(2)}% היום`;
}

// --- זרימת המידע העולמית ------------------------------------------------

// EventStreams של ויקימדיה: זרם חי של *כל* עריכה בכל ויקי בעולם, ברגע
// שהיא קורית. אנחנו לא קוראים את התוכן — רק סופרים את הקצב. זהו אולי
// המדד הישיר ביותר ל"כמה האנושות כותבת על עצמה כרגע".
const editWindow = [];
let editStream = null;
let hnRate = null;
let streamNote = '';

function startEditStream(s) {
  if (editStream || typeof EventSource === 'undefined') return;
  try {
    editStream = new EventSource('https://stream.wikimedia.org/v2/stream/recentchange');
  } catch (e) {
    s.error = 'EventSource נכשל';
    return;
  }
  editStream.onmessage = () => {
    editWindow.push(Date.now());
  };
  // ניתוקים זמניים הם חלק נורמלי מ-SSE ו-EventSource מתחבר מחדש לבד.
  // לכן לא מסמנים כאן כישלון: הסמכות היחידה לשאלה "יש נתונים?" היא
  // sampleEditRate, שבודק אם באמת הגיעו אירועים בדקה האחרונה.
  editStream.onerror = () => {
    streamNote = 'החיבור נותק זמנית — מתחבר מחדש';
  };
}

// נקרא בכל סבב: מחשב עריכות לשנייה בחלון של 60 שניות אחרונות.
function sampleEditRate(s) {
  const cutoff = Date.now() - 60000;
  while (editWindow.length && editWindow[0] < cutoff) editWindow.shift();
  if (editWindow.length === 0) throw new Error(streamNote || 'טרם התקבלו אירועים');
  const perSec = editWindow.length / 60;
  // ~30-100 עריכות/שנייה זה טווח נורמלי בוויקימדיה
  const wikiPart = clamp((perSec - 25) / 90, 0, 1);
  const hnPart = hnRate == null ? wikiPart : clamp(hnRate / 40, 0, 1);
  target.turbulence = clamp((wikiPart * 0.7 + hnPart * 0.3), 0, 1);
  s.detail = `${perSec.toFixed(1)} עריכות ויקי לשנייה`;
}

async function readHackerNews(s) {
  const data = await safeFetchJson(
    'https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=100'
  );
  const hits = data && Array.isArray(data.hits) ? data.hits : null;
  if (!hits || hits.length < 2) throw new Error('bad shape');
  const times = hits.map((h) => h.created_at_i).filter((t) => typeof t === 'number');
  if (times.length < 2) throw new Error('no timestamps');
  const spanHours = (Math.max(...times) - Math.min(...times)) / 3600;
  hnRate = spanHours > 0 ? times.length / spanHours : null;
  s.detail = hnRate ? `${hnRate.toFixed(1)} סיפורים חדשים לשעה` : 'זמין';
}

// --- תשומת הלב הציבורית: מיינסטרים, פוליטיקה, קונספירציה ----------------

// היוריסטיקה גסה ומוצהרת: התאמת מילות מפתח לכותרות הערכים הנצפים ביותר
// בוויקיפדיה. זהו אות אמנותי על *תשומת לב*, לא מדידה סוציולוגית ולא
// אמירה על נכונות של שום נושא. שום תוכן לא מוצג ושום טענה לא מועברת —
// המספר היחיד שיוצא מכאן הופך לגוון ולמרקם.
// גבולות מילה חיוניים כאן: התאמת תת-מחרוזת תמימה הייתה מזהה את "war"
// בתוך Software / Award / Warren ומנפחת את האות הפוליטי לחלוטין.
const POLITICS_RE =
  /\b(election\w*|president\w*|prime[ ]minister|parliament\w*|senate|congress\w*|government\w*|minister\w*|politic\w*|vote|votes|voting|sanction\w*|treaty|treaties|coup|protest\w*|war|wars|wartime|military|referendum\w*|campaign\w*|diplomat\w*|geopolitic\w*)\b/i;
const CONSPIRACY_RE =
  /\b(conspirac\w*|hoax\w*|deep[ ]state|illuminati|chemtrail\w*|flat[ ]earth|qanon|false[ ]flag|cover[- ]?up|ufo\w*|area[ ]51|roswell|pseudoscien\w*|paranormal|cryptid\w*|occult(?:ism|ists?)?)\b/i;

// כותרות ויקיפדיה משתמשות בקו תחתון, ו-JS מחשיב "_" כתו-מילה — ולכן
// \b לא היה נתפס כלל בלי הנרמול הזה.
function titleText(article) {
  return String(article || '').replace(/_/g, ' ');
}

function shareMatching(articles, total, re) {
  let sum = 0;
  for (const a of articles) {
    if (re.test(titleText(a.article))) sum += a.views || 0;
  }
  return total > 0 ? sum / total : 0;
}

async function readPublicAttention(s) {
  // נתוני pageviews מתפרסמים בפיגור של יום, ולעיתים יותר — מנסים אחורה.
  let payload = null;
  for (let back = 1; back <= 3 && !payload; back++) {
    const { y, m, d } = utcDaysAgo(back);
    payload = await safeFetchJson(
      `https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/${y}/${m}/${d}`
    );
  }
  const items = payload && Array.isArray(payload.items) ? payload.items[0] : null;
  const raw = items && Array.isArray(items.articles) ? items.articles : null;
  if (!raw) throw new Error('no articles');

  // מסננים ערכים טכניים ששולטים ברשימה ואינם "נושא" (עמוד ראשי, חיפוש וכו')
  const articles = raw.filter((a) => {
    const t = String(a.article || '');
    return t !== 'Main_Page' && !t.startsWith('Special:') && !t.startsWith('Wikipedia:');
  });
  if (articles.length === 0) throw new Error('all filtered');

  const total = articles.reduce((sum, a) => sum + (a.views || 0), 0);
  if (total <= 0) throw new Error('no views');

  const topShare = (articles[0].views || 0) / total;
  target.focus = clamp((topShare - 0.02) / 0.12, 0, 1) * 0.8;

  const polShare = shareMatching(articles, total, POLITICS_RE);
  target.tension = clamp(polShare / 0.18, 0, 1);

  const conShare = shareMatching(articles, total, CONSPIRACY_RE);
  target.fracture = clamp(conShare / 0.05, 0, 1);

  s.detail =
    `הנצפה ביותר: ${titleText(articles[0].article)} · ` +
    `פוליטי ${(polShare * 100).toFixed(1)}% · שולי ${(conShare * 100).toFixed(1)}%`;
}

// --- תרבות ואמנות -------------------------------------------------------

// "יצירת היום" מאוסף מוזיאון האמנות של שיקגו: הצבע הדומיננטי של יצירה
// אנושית אמיתית צובע בעדינות את היצירה הגנרטיבית. הבחירה דטרמיניסטית
// לפי התאריך, כך שכל הצופים בעולם רואים את אותה יצירה באותו יום.
async function readArtOfTheDay(s) {
  const { y, m, d } = utcDaysAgo(0);
  const dayIndex = Math.floor(Date.UTC(y, Number(m) - 1, Number(d)) / 86400000);
  const page = (dayIndex % 50) + 1;
  const data = await safeFetchJson(
    `https://api.artic.edu/api/v1/artworks?limit=100&page=${page}&fields=id,title,color,artist_title`
  );
  const list = data && Array.isArray(data.data) ? data.data : null;
  if (!list) throw new Error('bad shape');
  const withColor = list.filter((a) => a.color && typeof a.color.h === 'number');
  if (withColor.length === 0) throw new Error('no color data');

  const pick = withColor[dayIndex % withColor.length];
  const { h, s: sat } = pick.color;
  target.accentHue = (h / 360) * Math.PI * 2;
  target.accentAmount = clamp((sat || 0) / 100, 0, 1) * 0.5;
  s.detail = `${pick.title || 'ללא שם'}${pick.artist_title ? ' · ' + pick.artist_title : ''}`;
}

// --- רישום המקורות ------------------------------------------------------

const registry = [
  { key: 'quake', label: 'רעידות אדמה', group: 'כדור הארץ', run: readEarthquakes },
  { key: 'solar', label: 'פעילות סולארית', group: 'כדור הארץ', run: readSolar },
  { key: 'weather', label: 'מזג אוויר גלובלי', group: 'כדור הארץ', run: readWeather },
  { key: 'gold', label: 'שוק הזהב', group: 'כלכלה', run: readGold },
  { key: 'wikiStream', label: 'זרם עריכות ויקימדיה', group: 'זרימת מידע', run: sampleEditRate },
  { key: 'hn', label: 'Hacker News', group: 'זרימת מידע', run: readHackerNews },
  { key: 'attention', label: 'תשומת לב ציבורית', group: 'חברה', run: readPublicAttention },
  { key: 'art', label: 'יצירת היום', group: 'תרבות', run: readArtOfTheDay },
];

const sources = {};
for (const src of registry) {
  sources[src.key] = { label: src.label, group: src.group, ok: false, detail: '', error: '' };
}

async function runSource(src) {
  const s = sources[src.key];
  try {
    await src.run(s);
    s.ok = true;
    s.error = '';
  } catch (e) {
    s.ok = false;
    s.error = (e && e.message) || 'נכשל';
  }
}

async function pollAll() {
  await Promise.allSettled(registry.map(runSource));
}

let started = false;
export function startWorldPulse() {
  if (started) return;
  started = true;
  startEditStream(sources.wikiStream);
  pollAll();
  setInterval(pollAll, POLL_INTERVAL_MS);
  // קצב העריכות משתנה משנייה לשנייה — דוגמים אותו תכופות יותר מהשאר.
  setInterval(() => runSource(registry.find((r) => r.key === 'wikiStream')), 10000);
}

// התכנסות רכה בכל פריים כך שערכים חדשים אף פעם לא "קופצים" — מזג האוויר
// של היצירה משתנה בהדרגה, כמו מזג אוויר אמיתי.
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
