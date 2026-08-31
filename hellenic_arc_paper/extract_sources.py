# -*- coding: utf-8 -*-
"""סורק את קובצי ה-PDF שצורפו, ומכין את חומרי הגלם לעבודה.

שימוש:
    python3 extract_sources.py                 # סקירה: מסמכים, עמודים, איורים
    python3 extract_sources.py --text <קובץ>   # טקסט מלא לפי עמוד (לאיתור ציטוטים)
    python3 extract_sources.py --figure <קובץ> <עמוד> [<x0> <y0> <x1> <y1>]

הסקירה מדפיסה לכל עמוד את מספרי האיורים שזוהו בכיתובים ("Fig. 3", "Figure 3"),
כדי שאפשר יהיה לבחור איורים לפי מיקומם האמיתי במאמר.
"""

import argparse
import os
import re
import sys

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
ATTACH_DIRS = ["/mnt/attach", "/mnt/user-data/working", os.path.join(HERE, "sources")]
FIG_DIR = os.path.join(HERE, "figures")

CAPTION_RE = re.compile(r"\b(?:Fig(?:ure)?\.?)\s*(\d+)", re.I)


def find_pdfs():
    found = []
    for directory in ATTACH_DIRS:
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if name.lower().endswith(".pdf"):
                found.append(os.path.join(directory, name))
    return found


def resolve(name):
    """מאתר PDF לפי שם מלא או חלקי."""
    if os.path.isfile(name):
        return name
    for path in find_pdfs():
        if name.lower() in os.path.basename(path).lower():
            return path
    sys.exit(f"לא נמצא PDF בשם {name!r}. זמינים:\n  " +
             "\n  ".join(find_pdfs()) or "  (אין)")


def survey():
    pdfs = find_pdfs()
    if not pdfs:
        print("לא נמצאו קובצי PDF. חיפשתי ב:")
        for directory in ATTACH_DIRS:
            print("  -", directory, "(קיים)" if os.path.isdir(directory) else "(לא קיים)")
        return
    for path in pdfs:
        doc = pymupdf.open(path)
        meta = doc.metadata or {}
        print("=" * 78)
        print(os.path.basename(path))
        print(f"  עמודים: {doc.page_count}   כותרת: {(meta.get('title') or '').strip()[:70]}")
        # מספר העמוד המודפס הראשון, אם מופיע בטקסט
        first = doc[0].get_text().strip().splitlines()
        print("  שורות פותחות:", " | ".join(s.strip() for s in first[:3])[:150])
        for i, page in enumerate(doc):
            text = page.get_text()
            figs = sorted(set(CAPTION_RE.findall(text)), key=int)
            images = page.get_images(full=True)
            drawings = len(page.get_drawings())
            if figs or images or drawings > 40:
                print(f"    עמ' {i + 1:>3}: איורים בכיתוב={figs or '-':<14} "
                      f"תמונות מוטמעות={len(images):<3} ציורים וקטוריים={drawings}")
        doc.close()


def dump_text(name):
    path = resolve(name)
    doc = pymupdf.open(path)
    for i, page in enumerate(doc):
        print(f"\n{'=' * 30} עמ' {i + 1} (PDF) {'=' * 30}")
        print(page.get_text())
    doc.close()


def extract_figure(name, page_no, box=None):
    """שומר איור: התמונה המוטמעת הגדולה ביותר, או חיתוך של אזור מוגדר."""
    path = resolve(name)
    doc = pymupdf.open(path)
    page = doc[page_no - 1]
    stem = f"{os.path.splitext(os.path.basename(path))[0][:28]}_p{page_no}"
    os.makedirs(FIG_DIR, exist_ok=True)
    out = []

    if box:
        clip = pymupdf.Rect(*box)
        pix = page.get_pixmap(clip=clip, dpi=300)
        dest = os.path.join(FIG_DIR, f"{stem}_clip.png")
        pix.save(dest)
        out.append((dest, pix.width, pix.height))
    else:
        for idx, info in enumerate(page.get_images(full=True)):
            xref = info[0]
            pix = pymupdf.Pixmap(doc, xref)
            if pix.n - pix.alpha >= 4:            # CMYK -> RGB
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            if pix.width < 200 or pix.height < 200:
                continue                           # לוגו או קישוט
            dest = os.path.join(FIG_DIR, f"{stem}_img{idx}.png")
            pix.save(dest)
            out.append((dest, pix.width, pix.height))
        if not out:
            # איור וקטורי: מרנדרים את העמוד כדי לבחור ממנו תיבת חיתוך
            pix = page.get_pixmap(dpi=150)
            dest = os.path.join(FIG_DIR, f"{stem}_fullpage.png")
            pix.save(dest)
            out.append((dest, pix.width, pix.height))
            print(f"אין תמונה מוטמעת בעמוד. גודל העמוד בנקודות: "
                  f"{page.rect.width:.0f} x {page.rect.height:.0f} "
                  f"(העבירו x0 y0 x1 y1 כדי לחתוך אזור).")

    for dest, w, h in out:
        print(f"{dest}  ({w}x{h})")
    doc.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--text", metavar="PDF")
    parser.add_argument("--figure", nargs="+", metavar="ARG")
    args = parser.parse_args()

    if args.text:
        dump_text(args.text)
    elif args.figure:
        name, page_no, *rest = args.figure
        box = [float(v) for v in rest] if len(rest) == 4 else None
        extract_figure(name, int(page_no), box)
    else:
        survey()
