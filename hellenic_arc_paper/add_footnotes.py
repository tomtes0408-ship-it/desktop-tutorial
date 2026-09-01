# -*- coding: utf-8 -*-
"""ממיר את הציטוטים המוטבעים בעבודת הבסיס להערות שוליים אמיתיות של Word.

הרציונל: ההנחיה דורשת הערת שוליים לכל טענה הנשענת על מקור, כולל עמוד ופרק.
ציטוט בסוגריים בתוך טקסט עברי גם נשבר בצורה מכוערת בין שורות, משום שסימני
הפיסוק הניטרליים בגבול עברית/לטינית נפתרים לפי אלגוריתם ה-bidi. העברת הציטוט
להערת שוליים פותרת את שתי הבעיות יחד.

השימוש בלוקטורים (עמוד / פסקה / פרק) נלקח מעבודת הבסיס כפי שהוא - שום מספר
עמוד אינו מומצא כאן.
"""

import os
import re
import shutil
import subprocess
import zipfile

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
w = f"{{{W}}}"

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "base", "עבודת_בסיס.docx")
OUT = os.path.join(HERE, "עבודת_סיכום_הקשת_ההלנית.docx")
BUILD = os.path.join(HERE, ".build")

# --- המקורות: צורה מלאה להופעה הראשונה, וצורה מקוצרת לשאר ---------------------
FULL = {
    "Huguen": "Huguen, C., Chamot-Rooke, N., Loubrieu, B., & Mascle, J. (2006). "
              "Morphology of a pre-collisional, salt-bearing, accretionary complex: "
              "The Mediterranean Ridge (Eastern Mediterranean). "
              "Marine Geophysical Researches, 27(1), 61–75",
    "Kopf": "Kopf, A., Mascle, J., & Klaeschen, D. (2003). The Mediterranean Ridge: "
            "A mass balance across the fastest growing accretionary complex on Earth. "
            "Journal of Geophysical Research: Solid Earth, 108(B8), 2372",
    "Gunes": "Güneş, P., Aksu, A. E., & Hall, J. (2018). Internal seismic stratigraphy "
             "of the Messinian evaporites across the eastern Mediterranean Sea. "
             "Marine and Petroleum Geology, 91, 297–320",
    "Royden": "Royden, L. H., & Papanikolaou, D. J. (2011). Slab segmentation and "
              "late Cenozoic disruption of the Hellenic arc. Geochemistry, Geophysics, "
              "Geosystems, 12(3), Q03010",
    "Kastens": "Kastens (1991), כפי שמצוטט אצל Kopf et al. (2003)",
    "Wikimedia": "Mikenorton, Hellenic subduction zone, Wikimedia Commons, "
                 "רישיון CC BY-SA 3.0",
}
SHORT = {
    "Huguen": "Huguen et al. (2006)",
    "Kopf": "Kopf et al. (2003)",
    "Gunes": "Güneş et al. (2018)",
    "Royden": "Royden, L. H., & Papanikolaou, D. J. (2011). Slab segmentation and "
              "late Cenozoic disruption of the Hellenic arc. Geochemistry, Geophysics, "
              "Geosystems, 12(3), Q03010",
    "Kastens": "Kastens (1991), כפי שמצוטט אצל Kopf et al. (2003)",
    "Royden": "Royden & Papanikolaou (2011)",
    "Wikimedia": "Mikenorton, Wikimedia Commons",
}

# הלוקטורים אומתו אחד-אחד מול קובצי ה-PDF של המאמרים. הפרק מצוין לצד העמוד.
# Huguen et al. הוא מאמר ממוספר עמודים (61–75); Kopf et al. הוא מאמר AGU
# הממוספר בפסקאות, ולכן הלוקטור שלו הוא מספר פסקה וסעיף.
H = {
    "61": "עמ' 61 (תקציר ומבוא)",
    "62": "עמ' 62 (מבוא)",
    "66": "עמ' 66 (סעיף General morphologic and backscatter characteristics)",
    "67": "עמ' 67 (סעיף The Western Mediterranean Ridge)",
    "69": "עמ' 69 (סעיף The Western Mediterranean Ridge)",
    "71": "עמ' 71 (סעיף The Central Mediterranean Ridge)",
    "72": "עמ' 72 (סעיף The Central Mediterranean Ridge)",
    "73": "עמ' 73 (סעיף Conclusion)",
    "61,73": "עמ' 61 ו-73 (תקציר וסעיף Conclusion)",
    "61,65": "עמ' 61 ו-65 (תקציר ומבוא)",
    "66,69": "עמ' 66 ו-69 (הסעיפים General morphologic "
             "ו-The Western Mediterranean Ridge)",
    "66-67": "עמ' 66–67 (סעיף General morphologic and backscatter characteristics)",
    "72-73": "עמ' 72–73 (הסעיפים The Eastern Mediterranean Ridge ו-Conclusion)",
}
K = {
    "abs": "תקציר (פס' 1)",
    "5": "פס' 5 (סעיף 2.1, Accretionary Complex)",
    "6": "פס' 6 (סעיף 2.1, Accretionary Complex)",
    "42": "פס' 42 (סעיף 6, Discussion)",
    "fig1": "איור 1a",
}

R = {
    "abs": "תקציר (פס' 1)",
    "7": "פס' 7 (סעיף 2.1, Active Subduction)",
    "38": "פס' 38 (סעיף 3.2.2, Model Results)",
}

CITATIONS = {
    "(Huguen et al., 2006, עמ' 61)": [("Huguen", H["61"])],
    "(Huguen et al., 2006, עמ' 62)": [("Huguen", H["62"])],
    "(Huguen et al., 2006, עמ' 66)": [("Huguen", H["66"])],
    "(Huguen et al., 2006, עמ' 67)": [("Huguen", H["67"])],
    "(Huguen et al., 2006, עמ' 69)": [("Huguen", H["69"])],
    "(Huguen et al., 2006, עמ' 71)": [("Huguen", H["71"])],
    "(Huguen et al., 2006, עמ' 72)": [("Huguen", H["72"])],
    "(Huguen et al., 2006, עמ' 73)": [("Huguen", H["73"])],
    "(Huguen et al., 2006, עמ' 61, 73)": [("Huguen", H["61,73"])],
    "(Huguen et al., 2006, עמ' 66, 69)": [("Huguen", H["66,69"])],
    "(Huguen et al., 2006, עמ' 66–67)": [("Huguen", H["66-67"])],
    "(Huguen et al., 2006, עמ' 72–73)": [("Huguen", H["72-73"])],
    "(Royden & Papanikolaou, 2011, תקציר)": [("Royden", R["abs"])],
    "(Royden & Papanikolaou, 2011, פס' 7)": [("Royden", R["7"])],
    "(Royden & Papanikolaou, 2011, פס' 38)": [("Royden", R["38"])],
    "(Kopf et al., 2003, תקציר)": [("Kopf", K["abs"])],
    "(Kopf et al., 2003, פס' 5)": [("Kopf", K["5"])],
    "(Kopf et al., 2003, פס' 6)": [("Kopf", K["6"])],
    "(Kopf et al., 2003, איור 1)": [("Kopf", K["fig1"])],
    "(Kopf et al., 2003, פרק הדיון)": [("Kopf", K["42"])],
    "(Kastens, 1991, כפי שמצוטט אצל Kopf et al., 2003, פס' 3)":
        [("Kastens", "פס' 2 (סעיף 1, Introduction)")],
    "(Huguen et al., 2006, עמ' 62; Kopf et al., 2003, פס' 5)":
        [("Huguen", H["62"]), ("Kopf", K["5"])],
}

# תיקונים לפי מספר ההופעה במסמך. ארבע טענות צוטטו מן התקציר בלבד, אף שהן
# מבוססות גם בגוף המאמר או בסעיף המסקנות - שם הן נחשבות מבוססות, ולא רק מוצהרות.
OVERRIDES = {
    # שולי היבשת שכמעט נפגשים: תקציר עמ' 61, ושוב בסעיף המסקנות עמ' 73.
    "(Huguen et al., 2006, עמ' 73)": {0: [("Huguen", H["61,73"])]},
    "(Huguen et al., 2006, עמ' 61)": {
        5: [("Huguen", H["61,73"])],   # התכנסות חזיתית מול אלכסונית - גם במסקנות
        6: [("Huguen", H["61,65"])],   # שיטות הסקר - מפורטות בגוף המבוא בעמ' 65
        7: [("Huguen", H["61,73"])],   # שלושת הגורמים - נמנים שוב במסקנות
    },
}

# ציטוט נרטיבי: השנה נשארת בגוף המשפט, רק הלוקטור עובר להערה.
NARRATIVE = {"(2003, תקציר)": ("(2003)", [("Kopf", "תקציר (פס' 1); איור 1a")])}

# כיתובי האיורים: הערת שוליים נוספת בסוף הכיתוב, מעבר לשורת "מקור:" שנשארת בו.
CAPTION_NOTES = {
    "איור 1": [("Wikimedia", "")],
    "איור 2": [("Gunes", "איור 21, עמ' 315; הפאנל המערבי שבו לקוח "
                         "אצל המחברים מ-Dal Cin et al. (2016)")],
}

PUNCT = ".,;:"

# תיקוני טקסט שחלים על כל המסמך, כולל רשימת המקורות.
# שם כתב העת של Huguen et al. הוא "Marine Geophysical Researches" - כך הוא
# מודפס בראש עמ' 61 של המאמר. השם השתנה ל-"Research" רק ב-2010.
TEXT_FIX = {
    "Marine Geophysical Research,": "Marine Geophysical Researches,",
    "מקור: Güneş et al. (2018), Marine and Petroleum Geology.":
        "מקור: Güneş et al. (2018), איור 21, עמ' 315.",
}


def make_footnote_text(entries, used):
    """בונה את טקסט ההערה. הופעה ראשונה של מקור - הפניה מלאה; לאחריה - מקוצרת."""
    parts = []
    for key, locator in entries:
        first = key not in used
        book = FULL[key] if first else SHORT[key]
        used.add(key)
        if not locator:
            parts.append(book)
        else:
            # אחרי הפניה ביבליוגרפית מלאה הלוקטור הוא משפט נפרד; אחרי צורה
            # מקוצרת הוא ממשיך את המשפט.
            joiner = ". " if first and book[-1].isdigit() else ", "
            parts.append(book + joiner + locator)
    return "; ".join(parts) + "."


def rpr_for_reference(rpr):
    """מעתיק את מאפייני הריצה ומוסיף את סגנון סימן ההערה (rStyle חייב להיות ראשון)."""
    new = etree.fromstring(etree.tostring(rpr)) if rpr is not None else etree.SubElement(
        etree.Element(w + "r"), w + "rPr")
    style = etree.Element(w + "rStyle")
    style.set(w + "val", "FootnoteReference")
    new.insert(0, style)
    return new


# פסקאות חדשות. כל פסקה מוכנסת אחרי הפסקה שהעוגן מזהה, ונבנית בשכפול העיצוב
# של אותה פסקה - כך שאין הגדרת עיצוב חדשה שעלולה לסטות מן הקיים. הציטוטים
# נכתבים בתחביר המוטבע הרגיל, ועוברים דרך אותו צינור המרה להערות שוליים.
INSERTIONS = [
    (
        "הקינמטיקה של המערכת אינה אחידה לאורך הקשת",
        "השונות הקינמטית הזו אינה שרירותית, ומקורה בהרכב הליתוספרה הנכנסת "
        "להפחתה. מדידות GPS מראות התכנסות של כ-35 מ\"מ לשנה לרוחב ההלנידים "
        "הדרומיים, בין אפריקה לבין נקודות בלוח האגאי הרוכב "
        "(Royden & Papanikolaou, 2011, פס' 7). קצב זה אינו אחיד לאורך הקשת. "
        "מצפון לאזור העתק קפלוניה שוקעת ליתוספרה יבשתית אדריאטית בקצב של "
        "5–10 מ\"מ לשנה בלבד, ואילו מדרומו שוקעת ליתוספרה אוקיינית יונית, "
        "צפופה הרבה יותר, בקצב של כ-35 מ\"מ לשנה "
        "(Royden & Papanikolaou, 2011, תקציר). ההבדל בין המקטעים גדול דיו כדי "
        "להסיט את חזית ההפחתה עצמה: היא מוסטת בהיסט ימני של 100–120 ק\"מ "
        "לרוחב אזור העתק קפלוניה (Royden & Papanikolaou, 2011, תקציר). השונות "
        "לאורך הקשת מתחילה אפוא בציפת הלוח השוקע, ולא רק בכיסוי הסדימנטרי "
        "שמעליו."
    ),
    (
        "שלושת הגורמים מסבירים היטב את התצפיות שהוצגו",
        "שלושת הגורמים הללו נוגעים לפני השטח ולכיסוי הסדימנטרי, ומתחתם עומד "
        "גורם עמוק יותר. פילוח הלוח השוקע לפי ציפתו הוא שמייצר מלכתחילה את "
        "ההבדל בקצבי ההפחתה, שהקינמטיקה האזורית רק מבטאת: ליתוספרה יבשתית "
        "וציפה מצפון מול ליתוספרה אוקיינית וצפופה מדרום "
        "(Royden & Papanikolaou, 2011, תקציר). הגבול בין שני המקטעים, אזור "
        "העתק קפלוניה, הוא צעיר יחסית. מודלים גיאודינמיים מתארכים את היווצרותו "
        "ל-6–8 מיליון שנה, ורוב ההפרדה בין חזיתות ההפחתה התרחשה אחרי 5 מיליון "
        "שנה (Royden & Papanikolaou, 2011, פס' 38) — פרק זמן החופף להתפתחותה "
        "הפוסט-מסינית של המנסרה. הגורם הקינמטי אינו עומד אפוא בפני עצמו, אלא "
        "הוא עצמו תוצאה של מה שנכנס לתעלת ההפחתה."
    ),
    (
        "Kopf, A., Mascle, J., & Klaeschen, D. (2003)",
        "Royden, L. H., & Papanikolaou, D. J. (2011). Slab segmentation and late "
        "Cenozoic disruption of the Hellenic arc. Geochemistry, Geophysics, "
        "Geosystems, 12(3), Q03010. https://doi.org/10.1029/2010GC003280 "
        "[מאמר בפורמט AGU, הממוספר בפסקאות ולא בעמודים]"
    ),
]


def apply_insertions(root):
    """מוסיף את הפסקאות החדשות, בשכפול עיצובה של פסקת העוגן."""
    for anchor, body in INSERTIONS:
        target = None
        for para in root.iter(w + "p"):
            text = "".join(t.text or "" for t in para.findall(f".//{w}t"))
            if anchor in text:
                target = para
                break
        if target is None:
            raise SystemExit(f"לא נמצאה פסקת עוגן: {anchor[:40]!r}")

        new_para = etree.fromstring(etree.tostring(target))
        for run in new_para.findall(f"{w}r"):
            new_para.remove(run)
        source_run = target.find(f"{w}r")
        run = etree.SubElement(new_para, w + "r")
        rpr = source_run.find(f"{w}rPr") if source_run is not None else None
        if rpr is not None:
            run.append(etree.fromstring(etree.tostring(rpr)))
        node = etree.SubElement(run, w + "t")
        node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        node.text = body
        target.addnext(new_para)


def normalize_reference_list(root, footnotes, next_id, rpr_sample):
    """הופך את פריטי רשימת המקורות לפסקאות משמאל לימין.

    הפריטים לטיניים כמעט לחלוטין. פסקה מימין לשמאל עם יישור דו-צדדי מותחת אותם
    ומזיזה את ההערה העברית שבסופם אל אמצע השורה. יישור לשמאל פותר את שניהם;
    גודל הגופן (11) ומרווח השורה הבודד נשמרים כפי שהם.
    """
    in_references = False
    for para in root.iter(w + "p"):
        text = "".join(t.text or "" for t in para.findall(f".//{w}t"))
        if text.strip() == "רשימת מקורות":
            in_references = True
            continue
        if not in_references or not text.strip():
            continue

        ppr = para.find(f"{w}pPr")
        if ppr is None:
            continue
        bidi = ppr.find(f"{w}bidi")
        if bidi is not None:
            ppr.remove(bidi)
        jc = ppr.find(f"{w}jc")
        if jc is not None:
            jc.set(w + "val", "left")
        ind = ppr.find(f"{w}ind")
        if ind is not None and ind.get(w + "right"):
            ind.set(w + "left", ind.get(w + "right"))
            del ind.attrib[w + "right"]
        local_rpr = None
        for run in para.findall(f"{w}r"):
            rpr = run.find(f"{w}rPr")
            if rpr is not None:
                local_rpr = rpr
                rtl = rpr.find(f"{w}rtl")
                if rtl is None:
                    rtl = etree.SubElement(rpr, w + "rtl")
                rtl.set(w + "val", "0")

        node = para.findall(f".//{w}t")[-1]
        match = re.search(r"\s*\[([^\[\]]+)\]\s*$", node.text or "")
        if match:
            node.text = node.text[:match.start()]
            ref = etree.Element(w + "r")
            ref.append(rpr_for_reference(local_rpr if local_rpr is not None
                                        else rpr_sample))
            marker = etree.SubElement(ref, w + "footnoteReference")
            marker.set(w + "id", str(next_id))
            para.append(ref)
            footnotes.append((next_id, match.group(1).strip()))
            next_id += 1
    return next_id


def build():
    if os.path.isdir(BUILD):
        shutil.rmtree(BUILD)
    os.makedirs(BUILD)
    with zipfile.ZipFile(BASE) as z:
        names = z.namelist()
        z.extractall(BUILD)

    doc_path = os.path.join(BUILD, "word", "document.xml")
    tree = etree.parse(doc_path)
    root = tree.getroot()

    apply_insertions(root)

    for node in root.iter(w + "t"):
        for old, new in TEXT_FIX.items():
            if node.text and old in node.text:
                node.text = node.text.replace(old, new)

    footnotes = []          # (id, text)
    seen_counts = {}        # לספירת הופעות, עבור OVERRIDES
    used_sources = set()
    next_id = 1
    in_references = False

    for para in root.iter(w + "p"):
        text_nodes = para.findall(f".//{w}t")
        para_text = "".join(t.text or "" for t in text_nodes)

        if para_text.strip() == "רשימת מקורות":
            in_references = True
        if in_references:
            continue        # רשימת המקורות נשארת ללא נגיעה

        caption_key = next((k for k in CAPTION_NOTES
                            if para_text.strip().startswith(k + ":")), None)

        for run in list(para.findall(f"{w}r")):
            t = run.find(f"{w}t")
            if t is None or not t.text:
                continue
            text = t.text
            hits = []
            for cite in sorted(list(CITATIONS) + list(NARRATIVE), key=len, reverse=True):
                start = 0
                while True:
                    i = text.find(cite, start)
                    if i < 0:
                        break
                    if not any(s <= i < e for s, e, *_ in hits):
                        hits.append((i, i + len(cite), cite))
                    start = i + 1
            if not hits and caption_key is None:
                continue
            hits.sort()

            rpr = run.find(f"{w}rPr")
            pieces = []         # ("text", str) או ("fn", id)
            cursor = 0
            for start, end, cite in hits:
                keep = ""
                cut = start
                if cite in NARRATIVE:
                    keep, entries = NARRATIVE[cite]
                else:
                    entries = CITATIONS[cite]
                    seen_counts[cite] = seen_counts.get(cite, -1) + 1
                    override = OVERRIDES.get(cite, {}).get(seen_counts[cite])
                    if override:
                        entries = override
                    if cut > 0 and text[cut - 1] == " ":
                        cut -= 1        # גם הרווח שלפני הסוגריים יורד
                tail = end
                trailing = ""
                if cite not in NARRATIVE and tail < len(text) and text[tail] in PUNCT:
                    trailing = text[tail]
                    tail += 1
                pieces.append(("text", text[cursor:cut] + keep + trailing))
                pieces.append(("fn", next_id))
                footnotes.append((next_id, make_footnote_text(entries, used_sources)))
                next_id += 1
                cursor = tail
            rest = text[cursor:]
            if caption_key is not None:
                pieces.append(("text", rest))
                pieces.append(("fn", next_id))
                footnotes.append(
                    (next_id, make_footnote_text(CAPTION_NOTES[caption_key],
                                                 used_sources)))
                next_id += 1
                caption_key = None
            else:
                pieces.append(("text", rest))

            index = list(para).index(run)
            para.remove(run)
            for offset, (kind, value) in enumerate(pieces):
                if kind == "text":
                    if not value:
                        continue
                    new_run = etree.Element(w + "r")
                    if rpr is not None:
                        new_run.append(etree.fromstring(etree.tostring(rpr)))
                    node = etree.SubElement(new_run, w + "t")
                    node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                    node.text = value
                else:
                    new_run = etree.Element(w + "r")
                    new_run.append(rpr_for_reference(rpr))
                    ref = etree.SubElement(new_run, w + "footnoteReference")
                    ref.set(w + "id", str(value))
                para.insert(index + offset, new_run)

    body_rpr = root.find(f".//{w}p/{w}r/{w}rPr")
    next_id = normalize_reference_list(root, footnotes, next_id, body_rpr)
    tree.write(doc_path, xml_declaration=True, encoding="UTF-8", standalone=True)

    # --- כתיבת חלק הערות השוליים -------------------------------------------
    fn_path = os.path.join(BUILD, "word", "footnotes.xml")
    fn_tree = etree.parse(fn_path)
    fn_root = fn_tree.getroot()
    for fid, body in footnotes:
        note = etree.SubElement(fn_root, w + "footnote")
        note.set(w + "id", str(fid))
        p = etree.SubElement(note, w + "p")
        ppr = etree.SubElement(p, w + "pPr")
        style = etree.SubElement(ppr, w + "pStyle")
        style.set(w + "val", "FootnoteText")
        etree.SubElement(ppr, w + "bidi")

        marker = etree.SubElement(p, w + "r")
        mpr = etree.SubElement(marker, w + "rPr")
        mstyle = etree.SubElement(mpr, w + "rStyle")
        mstyle.set(w + "val", "FootnoteReference")
        etree.SubElement(marker, w + "footnoteRef")

        run = etree.SubElement(p, w + "r")
        rpr = etree.SubElement(run, w + "rPr")
        fonts = etree.SubElement(rpr, w + "rFonts")
        for attr in ("ascii", "hAnsi", "cs", "eastAsia"):
            fonts.set(w + attr, "Arial")
        sz = etree.SubElement(rpr, w + "sz")
        sz.set(w + "val", "20")
        szcs = etree.SubElement(rpr, w + "szCs")
        szcs.set(w + "val", "20")
        etree.SubElement(rpr, w + "rtl")
        node = etree.SubElement(run, w + "t")
        node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        node.text = " " + body
    fn_tree.write(fn_path, xml_declaration=True, encoding="UTF-8", standalone=True)

    # --- אריזה מחדש --------------------------------------------------------
    if os.path.exists(OUT):
        os.remove(OUT)
    subprocess.run(["zip", "-Xrq", OUT, "."], cwd=BUILD, check=True)
    shutil.rmtree(BUILD)
    return OUT, footnotes


if __name__ == "__main__":
    path, notes = build()
    print(f"{path}\nהערות שוליים שנוצרו: {len(notes)}\n")
    for fid, body in notes:
        print(f"{fid:>3}. {body}")
