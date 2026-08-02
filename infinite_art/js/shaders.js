// יקום אמנותי אינסופי — שיידרים (GLSL ES 3.00 / WebGL2)
//
// כל הפרטים החזותיים נוצרים כאן, בזמן אמת, ממערכת חוקים דטרמיניסטית.
// שום פיקסל לא נשמר: הצבע של כל נקודה נגזר מהמיקום המרחבי שלה (uLocalUV + עומק
// הזום, uDepth/uZoomFrac) ומהזמן האמנותי (uTime). זו הסיבה שהיצירה יכולה
// "להתקיים" אלפי שנים בלי שהמידע המאוחסן יגדל.

export const VERTEX_SRC = `#version 300 es
precision highp float;
const vec2 POS[3] = vec2[3](vec2(-1.0,-1.0), vec2(3.0,-1.0), vec2(-1.0,3.0));
void main() {
  gl_Position = vec4(POS[gl_VertexID], 0.0, 1.0);
}`;

export const FRAGMENT_SRC = `#version 300 es
precision highp float;
precision highp int;

uniform vec2 uResolution;
uniform float uAspect;
uniform uint uSeed;
uniform vec2 uLocalUV;
uniform float uZoomFrac;
uniform int uDepth;
uniform float uTime;

// "דופק עולמי": מודולציה עדינה ומוגבלת שמגיעה מנתונים חיים אמיתיים
// (רעידות אדמה, פעילות סולארית, מזג אוויר גלובלי, שוק הזהב — ראו
// worldpulse.js). לעולם לא משפיעה על המבנה הפרקטלי או על זמני הלידה —
// רק על גוון, זוהר, קצב תנועה וערפל אטמוספרי, בטווחים קטנים ומוגבלים.
uniform float uWorldHue;
uniform float uWorldGlow;
uniform float uWorldFlow;
uniform float uWorldWarmth;
uniform float uWorldHaze;
uniform float uWorldTurbulence;
uniform float uWorldFocus;
uniform float uWorldTension;
uniform float uWorldFracture;
uniform float uWorldAccentHue;
uniform float uWorldAccentAmount;

out vec4 fragColor;

const int SUBDIV = 3;
const int MAX_OCT = 13;
const float EPOCH = 40.0;
const float FADE = 24.0;

// --- hash: מוזיל בליל ביטים דטרמיניסטי, זהה במדויק לגרסת ה-JS ---
uint hashU32(uint x) {
  x ^= x >> 16u;
  x *= 0x7feb352du;
  x ^= x >> 15u;
  x *= 0x846ca68bu;
  x ^= x >> 16u;
  return x;
}
uint hashCombine(uint a, uint b) {
  uint hb = hashU32(b);
  uint t = a ^ (hb + 0x9e3779b9u + (a << 6u) + (a >> 2u));
  return hashU32(t);
}
uint cellKey(ivec2 c) {
  return (uint(c.x) * 0x1f1f1f1fu) ^ (uint(c.y) * 0x27220a95u);
}
float hashFloat(uint seed, uint salt) {
  return float(hashCombine(seed, salt)) / 4294967295.0;
}
vec2 hashVec2(uint seed, uint salt) {
  return vec2(hashFloat(seed, salt * 2u + 1u), hashFloat(seed, salt * 2u + 2u));
}

mat2 rot(float a) {
  float s = sin(a), c = cos(a);
  return mat2(c, -s, s, c);
}

float noise2(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  float a = fract(sin(dot(i, vec2(127.1, 311.7))) * 43758.5453);
  float b = fract(sin(dot(i + vec2(1.0, 0.0), vec2(127.1, 311.7))) * 43758.5453);
  float c = fract(sin(dot(i + vec2(0.0, 1.0), vec2(127.1, 311.7))) * 43758.5453);
  float d = fract(sin(dot(i + vec2(1.0, 1.0), vec2(127.1, 311.7))) * 43758.5453);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}
float fbm(vec2 p) {
  float v = 0.0, amp = 0.5;
  for (int i = 0; i < 4; i++) {
    v += amp * noise2(p);
    p = rot(2.0) * p * 2.02;
    amp *= 0.5;
  }
  return v;
}

// --- ששה פלטות צבע אצורות (לא RGB אקראי) ---
vec3 paletteColor(int idx, float t) {
  t = clamp(t, 0.0, 1.0);
  vec3 c0, c1, c2, c3;
  if (idx == 0) { c0=vec3(0.10,0.03,0.15); c1=vec3(0.65,0.12,0.25); c2=vec3(0.95,0.55,0.20); c3=vec3(1.0,0.9,0.6); }
  else if (idx == 1) { c0=vec3(0.02,0.02,0.08); c1=vec3(0.10,0.05,0.35); c2=vec3(0.25,0.55,0.85); c3=vec3(0.85,0.95,1.0); }
  else if (idx == 2) { c0=vec3(0.03,0.08,0.04); c1=vec3(0.08,0.28,0.12); c2=vec3(0.35,0.55,0.15); c3=vec3(0.85,0.85,0.55); }
  else if (idx == 3) { c0=vec3(0.02,0.02,0.03); c1=vec3(0.2,0.2,0.22); c2=vec3(0.55,0.53,0.5); c3=vec3(0.95,0.94,0.9); }
  else if (idx == 4) { c0=vec3(0.08,0.04,0.02); c1=vec3(0.35,0.15,0.04); c2=vec3(0.75,0.5,0.12); c3=vec3(1.0,0.92,0.65); }
  else { c0=vec3(0.01,0.03,0.08); c1=vec3(0.02,0.15,0.30); c2=vec3(0.05,0.45,0.55); c3=vec3(0.65,0.95,0.9); }
  return t < 0.33 ? mix(c0, c1, t / 0.33)
       : t < 0.66 ? mix(c1, c2, (t - 0.33) / 0.33)
                   : mix(c2, c3, (t - 0.66) / 0.34);
}

struct StyleOut { vec3 color; float alpha; };

// --- חמש "משפחות סגנון" — כל תא בוחר אחת מהן דרך ה-hash שלו ---
StyleOut styleBloom(vec2 uv, uint seed, float t) {
  vec2 p = uv - 0.5;
  float ang = atan(p.y, p.x);
  float r = length(p) * 2.0;
  float petals = 5.0 + floor(hashFloat(seed, 10u) * 6.0);
  float wob = sin(ang * petals + t * 0.3 + hashFloat(seed, 11u) * 6.28) * 0.15;
  float ring = smoothstep(0.02, 0.0, abs(r - 0.55 - wob) - 0.12);
  float core = smoothstep(0.25, 0.0, r);
  float a = clamp(ring * 0.8 + core, 0.0, 1.0);
  return StyleOut(vec3(a), a);
}
StyleOut styleVeins(vec2 uv, uint seed, float t) {
  vec2 p = (uv - 0.5) * 3.0;
  float n = fbm(p + hashVec2(seed, 20u) * 10.0 + t * 0.05);
  float lines = smoothstep(0.0, 0.02, abs(fract(n * 4.0) - 0.5) - 0.42);
  return StyleOut(vec3(1.0 - lines), 1.0 - lines);
}
StyleOut styleMosaic(vec2 uv, uint seed, float t) {
  vec2 p = uv * 4.0 + hashVec2(seed, 30u) * 8.0;
  vec2 i = floor(p);
  uint k = hashCombine(seed, cellKey(ivec2(i)));
  float shade = hashFloat(k, 1u);
  vec2 f = fract(p) - 0.5;
  float edge = smoothstep(0.0, 0.06, 0.5 - max(abs(f.x), abs(f.y)));
  return StyleOut(vec3(shade), edge);
}
StyleOut styleFlow(vec2 uv, uint seed, float t) {
  vec2 p = uv * 2.0 + hashVec2(seed, 40u) * 6.0;
  float n = fbm(p * 1.5 + vec2(t * 0.04, -t * 0.03));
  float a = smoothstep(0.2, 0.9, n);
  return StyleOut(vec3(n), a * 0.9);
}
StyleOut styleWeave(vec2 uv, uint seed, float t) {
  vec2 p = uv * 8.0 + hashVec2(seed, 50u) * 10.0;
  float w1 = sin(p.x + t * 0.1);
  float w2 = sin(p.y * 1.3 - t * 0.08);
  float a = smoothstep(0.3, 1.0, abs(w1 * w2));
  return StyleOut(vec3(a), a * 0.8);
}
// סיבוב גוון עדין (זהה במהות לפילטר hue-rotate של CSS) — בשימוש רק עם
// זוויות קטנות מאוד שמגיעות מ-uWorldHue, ולכן נשאר תמיד "עדין".
vec3 hueRotateSmall(vec3 c, float a) {
  float cosA = cos(a), sinA = sin(a);
  mat3 m = mat3(
    0.299 + 0.701 * cosA + 0.168 * sinA, 0.587 - 0.587 * cosA + 0.330 * sinA, 0.114 - 0.114 * cosA - 0.497 * sinA,
    0.299 - 0.299 * cosA - 0.328 * sinA, 0.587 + 0.413 * cosA + 0.035 * sinA, 0.114 - 0.114 * cosA + 0.292 * sinA,
    0.299 - 0.300 * cosA + 1.250 * sinA, 0.587 - 0.588 * cosA - 1.050 * sinA, 0.114 + 0.886 * cosA - 0.203 * sinA
  );
  return clamp(c * m, 0.0, 1.0);
}

StyleOut renderStyle(int family, vec2 uv, uint seed, float t) {
  if (family == 0) return styleBloom(uv, seed, t);
  if (family == 1) return styleVeins(uv, seed, t);
  if (family == 2) return styleMosaic(uv, seed, t);
  if (family == 3) return styleFlow(uv, seed, t);
  return styleWeave(uv, seed, t);
}

void main() {
  vec2 screen = (gl_FragCoord.xy / uResolution) - 0.5;
  screen.x *= uAspect;

  float scale = mix(1.0, float(SUBDIV), uZoomFrac);
  vec2 p = uLocalUV + screen / scale;

  uint seed = uSeed;
  int depth = uDepth;
  int paletteIdx = int(hashFloat(seed, 1u) * 6.0);
  float angleAccum = 0.0;
  vec3 color = vec3(0.02, 0.02, 0.035);

  // כמה פיקסלים על המסך מייצג יחידת-אורך אחת של התא הנוכחי. כל עוד היא
  // גדולה מפיקסל אחד יש טעם לצייר עוד רמת פירוט; מתחת לכך זו רק רעש
  // תת-פיקסלי, ולכן עוצרים — כך שרק זום אמיתי חושף פרטים חדשים.
  float pixelsPerCell = uResolution.y * scale;

  for (int oct = 0; oct < MAX_OCT; oct++) {
    pixelsPerCell /= float(SUBDIV);
    if (pixelsPerCell < 1.5) { break; }

    vec2 rp = rot(angleAccum) * (p - 0.5) + 0.5;
    vec2 scaledp = rp * float(SUBDIV);
    ivec2 cellIdx = ivec2(floor(scaledp));
    vec2 local = fract(scaledp);
    uint cellSeed = hashCombine(seed, cellKey(cellIdx));

    float birth = float(depth) * EPOCH + hashFloat(cellSeed, 3u) * EPOCH * 0.8;
    float reveal = smoothstep(birth, birth + FADE, uTime);
    if (reveal <= 0.002) { break; }

    if (hashFloat(cellSeed, 2u) > 0.75) {
      paletteIdx = int(hashFloat(cellSeed, 4u) * 6.0);
    }
    // בשכבות הגסות (oct נמוך) מעדיפים משפחות שיוצרות צורה גדולה וקוהרנטית;
    // ככל שמתקדמים פנימה (oct עולה) עוברים בהדרגה למשפחות מרקם עדין יותר —
    // כך שמרחוק רואים קומפוזיציה אחת, ומקרוב היא מתגלה כמורכבת מפרטים רבים.
    float fr = hashFloat(cellSeed, 6u);
    int family;
    if (oct < 2) {
      family = fr < 0.55 ? 0 : (fr < 0.85 ? 3 : 1);
    } else if (oct < 5) {
      family = int(fr * 5.0);
    } else {
      family = fr < 0.4 ? 2 : (fr < 0.7 ? 4 : 1);
    }
    float animTime = uTime * uWorldFlow + float(depth) * 13.0;

    // "חוסר שקט": עיוות עדין של הקואורדינטה שנמסרת לציור בלבד. שימו לב
    // ש-local עצמו נשאר ללא שינוי וממשיך לשמש לירידה לרמה הבאה, ולכן
    // המבנה הפרקטלי נותר דטרמיניסטי לחלוטין — רק המראה רוטט.
    vec2 drawUV = local;
    if (uWorldTurbulence > 0.001 && oct >= 3) {
      vec2 w = vec2(fbm(local * 3.0 + animTime * 0.02), fbm(local * 3.0 - animTime * 0.02));
      drawUV += (w - 0.5) * 0.06 * uWorldTurbulence;
    }
    StyleOut so = renderStyle(family, drawUV, cellSeed, animTime);
    vec3 tinted = paletteColor(paletteIdx, so.color.r * 0.7 + hashFloat(cellSeed, 8u) * 0.3);
    float blend = reveal * so.alpha * 0.6;
    color = mix(color, tinted, blend);

    angleAccum += (hashFloat(cellSeed, 7u) - 0.5) * 0.6;
    seed = cellSeed;
    p = local;
    depth += 1;
  }

  // "דופק עולמי": מגע אחרון, עדין ומוגבל, שמחבר את היצירה לרגע האמיתי
  // בעולם — לעולם לא נוגע במבנה שנוצר למעלה, רק בגימור שלו.
  color *= uWorldGlow;
  color += vec3(uWorldWarmth, uWorldWarmth * 0.3, -uWorldWarmth * 0.6);
  color = hueRotateSmall(color, uWorldHue);

  // גוון ההדגשה של "יצירת היום" — צבע דומיננטי של יצירה אנושית אמיתית,
  // מעורבב פנימה תוך שמירה על הבהירות המקורית (תיבול, לא צביעה מחדש).
  if (uWorldAccentAmount > 0.001) {
    vec3 accent = hueRotateSmall(vec3(0.8, 0.45, 0.25), uWorldAccentHue);
    float lum = dot(color, vec3(0.299, 0.587, 0.114));
    vec3 tinted = accent * (lum / max(dot(accent, vec3(0.299, 0.587, 0.114)), 0.001));
    color = mix(color, tinted, uWorldAccentAmount * 0.22);
  }

  // מתח פוליטי: ניגודיות מעט חדה יותר וצללים קרירים — אי-נוחות שקטה.
  if (uWorldTension > 0.001) {
    color = mix(color, (color - 0.5) * 1.12 + 0.5, uWorldTension * 0.5);
    color.b += (1.0 - smoothstep(0.0, 0.4, dot(color, vec3(0.333)))) * uWorldTension * 0.04;
  }

  // סדקים דקיקים: שבירות של תמונת עולם משותפת. תמיד עדין, אף פעם לא
  // הופך לרעש — ומעולם לא נוגע במבנה שמתחת.
  if (uWorldFracture > 0.001) {
    vec2 cp = gl_FragCoord.xy / uResolution.y;
    float ridge = abs(fbm(cp * 7.0 + 31.7) - 0.5);
    float crack = smoothstep(0.035, 0.0, ridge);
    color = mix(color, color * 0.35, crack * uWorldFracture * 0.35);
  }

  // ריכוזיות תשומת הלב: ככל שהעולם כולו מביט באותו סיפור, המבט מתכנס.
  if (uWorldFocus > 0.001) {
    float r = length(screen) / 0.75;
    color *= mix(1.0, 1.0 - smoothstep(0.35, 1.25, r) * 0.55, uWorldFocus);
  }

  color = mix(color, vec3(0.55, 0.56, 0.6), uWorldHaze);

  color = pow(max(color, 0.0), vec3(0.9));
  fragColor = vec4(color, 1.0);
}`;
