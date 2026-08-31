# -*- coding: utf-8 -*-
"""אימות העבודה מול דרישות התרגיל ומול דרישת הערות השוליים.

הרצה:  python3 check_docx.py
"""

import re
import sys
import unicodedata
import zipfile

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DOC = "עבודת_סיכום_הקשת_ההלנית.docx"

# לוקטור תקין בהערת שוליים: עמוד, טווח עמודים, פסקה, פרק או איור
LOCATOR = re.compile(r"(עמ' \d|פס' \d|פרק |תקציר|איור \d)")
# ציטוט מוטבע שנשאר בטעות בגוף הטקסט
INLINE_CITATION = re.compile(r"\([^()]*\b(?:19|20)\d{2}\b[^()]*(?:עמ'|פס'|תקציר|פרק)[^()]*\)")


def text_of(node):
    return "".join(t.text or "" for t in node.findall(f".//{W}t"))


def prop(ppr, tag, attr):
    if ppr is None:
        return None
    el = ppr.find(f"{W}{tag}")
    return None if el is None else el.get(f"{W}{attr}")


def sort_key(s):
    stripped = unicodedata.normalize("NFKD", s)
    return "".join(c for c in stripped if not unicodedata.combining(c)).lower()


def main():
    problems = []
    z = zipfile.ZipFile(DOC)
    doc = etree.fromstring(z.read("word/document.xml"))
    notes = etree.fromstring(z.read("word/footnotes.xml"))

    body, captions, references = [], [], []
    in_refs = False
    used_markers = []
    # הערות המצורפות לכיתוב איור או לפריט ברשימת המקורות הן ייחוס של מקור,
    # ולא טענה - ולכן אין להן מספר עמוד או פרק.
    attribution_notes = set()

    for para in doc.findall(f".//{W}p"):
        txt = text_of(para).strip()
        ppr = para.find(f"{W}pPr")
        ids = [int(r.get(f"{W}id")) for r in para.findall(f".//{W}footnoteReference")]
        used_markers.extend(ids)
        if in_refs or txt.startswith("איור "):
            attribution_notes.update(ids)
        if not txt:
            continue
        if txt == "רשימת מקורות":
            in_refs = True
            continue
        if in_refs:
            references.append((txt, ppr, para))
            continue

        run = para.find(f"{W}r")
        rpr = run.find(f"{W}rPr") if run is not None else None
        sz = None if rpr is None or rpr.find(f"{W}sz") is None else \
            rpr.find(f"{W}sz").get(f"{W}val")
        entry = (txt, ppr, sz)
        (captions if txt.startswith("איור ") else body).append(entry)

        if INLINE_CITATION.search(txt):
            problems.append(f"ציטוט מוטבע שנשאר בגוף הטקסט: {txt[:60]}")

    # --- גוף הטקסט: Arial 12, רווח 1.5, יישור דו-צידי, RTL ---
    for txt, ppr, sz in body:
        if prop(ppr, "jc", "val") == "both":
            if sz != "24":
                problems.append(f"פסקת גוף שאינה בגודל 12: {txt[:45]}")
            if prop(ppr, "spacing", "line") != "360":
                problems.append(f"פסקת גוף שאינה במרווח 1.5: {txt[:45]}")
            if len(re.findall(r"[.!?]", txt)) < 3:
                problems.append(f"פסקה עם פחות משלושה משפטים: {txt[:45]}")
        if ppr is None or ppr.find(f"{W}bidi") is None:
            problems.append(f"פסקה עברית ללא כיווניות RTL: {txt[:45]}")

    # --- רשימת מקורות: Arial 11, רווח שורה בודד, סדר אלפביתי ---
    for txt, ppr, para in references:
        run = para.find(f"{W}r")
        rpr = run.find(f"{W}rPr") if run is not None else None
        sz = None if rpr is None or rpr.find(f"{W}sz") is None else \
            rpr.find(f"{W}sz").get(f"{W}val")
        if sz != "22":
            problems.append(f"מקור שאינו בגודל 11: {txt[:45]}")
        if prop(ppr, "spacing", "line") != "240":
            problems.append(f"מקור שאינו במרווח שורה בודד: {txt[:45]}")
    titles = [t for t, _, _ in references]
    if titles != sorted(titles, key=sort_key):
        problems.append("רשימת המקורות אינה בסדר אלפביתי")

    # --- הערות שוליים ---
    footnotes = {}
    for note in notes.findall(f"{W}footnote"):
        nid = int(note.get(f"{W}id"))
        if nid > 0:
            footnotes[nid] = text_of(note).strip()

    for nid, txt in footnotes.items():
        if nid in attribution_notes:
            continue        # ייחוס מקור של איור או הערה על פריט ביבליוגרפי
        if not LOCATOR.search(txt):
            problems.append(f"הערה {nid} ללא עמוד/פרק: {txt[:60]}")
    missing = sorted(set(footnotes) - set(used_markers))
    orphan = sorted(set(used_markers) - set(footnotes))
    if missing:
        problems.append(f"הערות ללא סימן בגוף המסמך: {missing}")
    if orphan:
        problems.append(f"סימנים ללא הערה מתאימה: {orphan}")

    # --- כל מקור ברשימה מופיע בלפחות הערה אחת ---
    all_notes = " ".join(footnotes.values())
    for surname in ("Huguen", "Kopf", "Güneş"):
        if surname not in all_notes:
            problems.append(f"המקור {surname} אינו מופיע באף הערת שוליים")

    print(f"פסקאות גוף:            {len(body)}")
    print(f"כיתובי איורים:         {len(captions)}")
    print(f"איורים מוטמעים:        {len(doc.findall(f'.//{W}drawing'))}")
    print(f"הערות שוליים:          {len(footnotes)} "
          f"(מהן {len(attribution_notes)} ייחוסי מקור לאיורים/ביבליוגרפיה)")
    print(f"סימני הערה בגוף:       {len(used_markers)}")
    print(f"פריטים ברשימת מקורות:  {len(references)}")

    if problems:
        print("\nבעיות שנמצאו:")
        for item in sorted(set(problems)):
            print("  -", item)
        return 1
    print("\nכל הבדיקות עברו.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
