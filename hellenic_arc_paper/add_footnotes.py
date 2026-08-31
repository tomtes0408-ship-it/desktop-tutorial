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
              "Marine Geophysical Research, 27(1), 61–75",
    "Kopf": "Kopf, A., Mascle, J., & Klaeschen, D. (2003). The Mediterranean Ridge: "
            "A mass balance across the fastest growing accretionary complex on Earth. "
            "Journal of Geophysical Research: Solid Earth, 108(B8), 2372",
    "Gunes": "Güneş, P., Aksu, A. E., & Hall, J. (2018). Internal seismic stratigraphy "
             "of the Messinian evaporites across the eastern Mediterranean Sea. "
             "Marine and Petroleum Geology, 91, 297–320",
    "Kastens": "Kastens (1991), כפי שמצוטט אצל Kopf et al. (2003)",
    "Wikimedia": "Mikenorton, Hellenic subduction zone, Wikimedia Commons, "
                 "רישיון CC BY-SA 3.0",
}
SHORT = {
    "Huguen": "Huguen et al. (2006)",
    "Kopf": "Kopf et al. (2003)",
    "Gunes": "Güneş et al. (2018)",
    "Kastens": "Kastens (1991), כפי שמצוטט אצל Kopf et al. (2003)",
    "Wikimedia": "Mikenorton, Wikimedia Commons",
}

# ציטוט מוטבע -> (מפתח המקור, הלוקטור). הלוקטורים מועתקים מעבודת הבסיס.
CITATIONS = {
    "(Huguen et al., 2006, עמ' 61)": [("Huguen", "עמ' 61")],
    "(Huguen et al., 2006, עמ' 62)": [("Huguen", "עמ' 62")],
    "(Huguen et al., 2006, עמ' 66)": [("Huguen", "עמ' 66")],
    "(Huguen et al., 2006, עמ' 67)": [("Huguen", "עמ' 67")],
    "(Huguen et al., 2006, עמ' 69)": [("Huguen", "עמ' 69")],
    "(Huguen et al., 2006, עמ' 71)": [("Huguen", "עמ' 71")],
    "(Huguen et al., 2006, עמ' 72)": [("Huguen", "עמ' 72")],
    "(Huguen et al., 2006, עמ' 73)": [("Huguen", "עמ' 73")],
    "(Huguen et al., 2006, עמ' 61, 73)": [("Huguen", "עמ' 61, 73")],
    "(Huguen et al., 2006, עמ' 66, 69)": [("Huguen", "עמ' 66, 69")],
    "(Huguen et al., 2006, עמ' 66–67)": [("Huguen", "עמ' 66–67")],
    "(Huguen et al., 2006, עמ' 72–73)": [("Huguen", "עמ' 72–73")],
    "(Kopf et al., 2003, תקציר)": [("Kopf", "תקציר")],
    "(Kopf et al., 2003, פס' 5)": [("Kopf", "פס' 5")],
    "(Kopf et al., 2003, פס' 6)": [("Kopf", "פס' 6")],
    "(Kopf et al., 2003, איור 1)": [("Kopf", "איור 1")],
    "(Kopf et al., 2003, פרק הדיון)": [("Kopf", "פרק הדיון")],
    "(Kastens, 1991, כפי שמצוטט אצל Kopf et al., 2003, פס' 3)": [("Kastens", "פס' 3")],
    "(Huguen et al., 2006, עמ' 62; Kopf et al., 2003, פס' 5)":
        [("Huguen", "עמ' 62"), ("Kopf", "פס' 5")],
}

# ציטוט נרטיבי: השנה נשארת בגוף המשפט, רק הלוקטור עובר להערה.
NARRATIVE = {"(2003, תקציר)": ("(2003)", [("Kopf", "תקציר")])}

# כיתובי האיורים: הערת שוליים נוספת בסוף הכיתוב, מעבר לשורת "מקור:" שנשארת בו.
CAPTION_NOTES = {
    "איור 1": [("Wikimedia", "")],
    "איור 2": [("Gunes", "")],
}

PUNCT = ".,;:"


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
            parts.append(f"{book}. {locator}" if first else f"{book}, {locator}")
    return "; ".join(parts) + "."


def rpr_for_reference(rpr):
    """מעתיק את מאפייני הריצה ומוסיף את סגנון סימן ההערה (rStyle חייב להיות ראשון)."""
    new = etree.fromstring(etree.tostring(rpr)) if rpr is not None else etree.SubElement(
        etree.Element(w + "r"), w + "rPr")
    style = etree.Element(w + "rStyle")
    style.set(w + "val", "FootnoteReference")
    new.insert(0, style)
    return new


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

    footnotes = []          # (id, text)
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
