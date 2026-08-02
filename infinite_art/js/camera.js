// יקום אמנותי אינסופי — מצלמת הזום האינסופי
//
// הרעיון המרכזי: המצב הנשמר של "היכן נמצאים בתוך היקום" הוא O(1) —
// לא רשימת פיקסלים ולא היסטוריה, אלא זרע (seed) מספרי בודד שנוצר על ידי
// שרשור hash-ים לאורך המסלול מהמרכז ועד לתא הנוכחי, בתוספת מיקום שברירי
// מקומי בתוך אותו תא. בכל פעם שחוצים גבול תא (מתחילים "זום" עמוק יותר),
// המיקום השברירי מתאפס (fract) והחלק השלם נבלע לתוך ה-seed — כך שהדיוק
// הנומרי אף פעם לא נשחק, וניתן להעמיק לרמות זום כמעט בלתי מוגבלות מבלי
// שכמות המידע המאוחסן תגדל.
//
// אפשר גם לזום *החוצה* מעבר לנקודת ההתחלה: כל רמה חיצונית חדשה נוצרת
// באופן דטרמיניסטי (פונקציה טהורה של מספר הרמה), כך שהיקום ניתן לשחזור
// זהה בכל פעם שחוזרים לאותה נקודה — הוא "גדול יותר" מכל מסך אחד, אך
// עדיין עקבי ובעל היגיון פנימי.
//
// ה-hash כאן חייב להיות זהה סיבית-לסיבית לזה שבשיידר (shaders.js), כדי
// שהמעבר בין רמות זום יהיה חלק ורציף מבחינה חזותית.

const SUBDIV = 3;
const OUTER_MARKER = 0x0a17ceed;

function u32(x) {
  return x >>> 0;
}
function mulU32(a, b) {
  return Math.imul(a, b) >>> 0;
}
export function hashU32(x) {
  x = u32(x);
  x ^= x >>> 16;
  x = mulU32(x, 0x7feb352d);
  x ^= x >>> 15;
  x = mulU32(x, 0x846ca68b);
  x ^= x >>> 16;
  return u32(x);
}
export function hashCombine(a, b) {
  a = u32(a);
  const hb = hashU32(b);
  const t = u32(a ^ u32(hb + 0x9e3779b9 + u32(a << 6) + (a >>> 2)));
  return hashU32(t);
}
function cellKey(cx, cy) {
  return u32(mulU32(u32(cx), 0x1f1f1f1f) ^ mulU32(u32(cy), 0x27220a95));
}
export function hashFloat(seed, salt) {
  return hashCombine(seed, salt) / 4294967295;
}

// ה"שורש" של היקום — זהות קבועה של היצירה.
export const ROOT_SEED = hashU32(0x494e4649); // "INFI"

export class FractalCamera {
  constructor() {
    this.depth = 0;
    this.seed = ROOT_SEED;
    this.localUV = { x: 0.5, y: 0.5 };
    this.zoomFrac = 0; // 0..1, התקדמות רציפה לעבר התא הבא
    // transitions.get(d) מתאר את הצעד מ-depth d אל depth d+1:
    // { childIndex: {x,y}, seedBefore }  כאשר seedBefore == seed בעומק d
    this.transitions = new Map();
  }

  get continuousDepth() {
    return this.depth + this.zoomFrac;
  }

  _entryForTransition(d) {
    let entry = this.transitions.get(d);
    if (entry) return entry;
    // d < 0 תמיד כאן: רמה חיצונית שטרם נחקרה — יוצרים אותה באופן דטרמיניסטי
    const level = -d;
    const parentSeed = hashCombine(ROOT_SEED, hashU32(OUTER_MARKER + level));
    const cx = Math.floor(hashFloat(parentSeed, 90) * SUBDIV);
    const cy = Math.floor(hashFloat(parentSeed, 91) * SUBDIV);
    entry = { childIndex: { x: cx, y: cy }, seedBefore: parentSeed };
    this.transitions.set(d, entry);
    return entry;
  }

  _commitDeeper() {
    const scaled = { x: this.localUV.x * SUBDIV, y: this.localUV.y * SUBDIV };
    const childIndex = { x: Math.floor(scaled.x), y: Math.floor(scaled.y) };
    this.transitions.set(this.depth, { childIndex, seedBefore: this.seed });
    this.seed = hashCombine(this.seed, cellKey(childIndex.x, childIndex.y));
    this.localUV = { x: scaled.x - childIndex.x, y: scaled.y - childIndex.y };
    this.depth += 1;
  }

  _commitShallower() {
    const d = this.depth - 1;
    const entry = this._entryForTransition(d);
    this.localUV = {
      x: (entry.childIndex.x + this.localUV.x) / SUBDIV,
      y: (entry.childIndex.y + this.localUV.y) / SUBDIV,
    };
    this.seed = entry.seedBefore;
    this.depth = d;
  }

  // amount: יחידות "אוקטבה" רציפות (חיובי = פנימה, שלילי = החוצה)
  zoomBy(amount) {
    this.zoomFrac += amount;
    let guard = 0;
    while (this.zoomFrac >= 1 && guard++ < 500) {
      this._commitDeeper();
      this.zoomFrac -= 1;
    }
    guard = 0;
    while (this.zoomFrac < 0 && guard++ < 500) {
      this._commitShallower();
      this.zoomFrac += 1;
    }
  }

  // dx, dy ביחידות מסך מנורמלות (כמו uv), כבר מותאמות לזום הנוכחי
  pan(dx, dy) {
    const scale = 1 + this.zoomFrac * (SUBDIV - 1);
    this.localUV.x -= dx / scale;
    this.localUV.y -= dy / scale;
  }

  reset() {
    this.depth = 0;
    this.seed = ROOT_SEED;
    this.localUV = { x: 0.5, y: 0.5 };
    this.zoomFrac = 0;
    this.transitions.clear();
  }

  teleportRandom(extraOctaves = 6) {
    for (let i = 0; i < extraOctaves; i++) {
      this.localUV = { x: Math.random(), y: Math.random() };
      this.zoomBy(1);
    }
  }

  uniforms() {
    return {
      seed: this.seed,
      localUV: this.localUV,
      zoomFrac: this.zoomFrac,
      depth: this.depth,
    };
  }
}
