"""
שורת פקודה: תמלול וסיכום של קובץ אודיו קיים.

שימוש:
    python -m smart_recorder.cli meeting.mp3
    python -m smart_recorder.cli lecture.m4a --language he --out lecture.md
    python -m smart_recorder.cli call.wav --no-summary
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .summarizer import Summarizer, SummaryError, summary_to_markdown
from .transcriber import Transcriber


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="תמלול אוטומטי + סיכום חכם + נקודות מפתח")
    p.add_argument("audio", help="קובץ אודיו/וידאו (mp3, wav, m4a, webm, mp4 ...)")
    p.add_argument("--language", default=None, help="שפת ההקלטה (he/en/...). ברירת מחדל: זיהוי אוטומטי")
    p.add_argument("--summary-language", default="he", help="שפת הסיכום (ברירת מחדל: he)")
    p.add_argument("--context", default="", help="הקשר על ההקלטה (למשל: 'ישיבת צוות שיווק')")
    p.add_argument("--model", default=None, help="מודל Whisper (ברירת מחדל: large-v3)")
    p.add_argument("--no-summary", action="store_true", help="תמלול בלבד, ללא סיכום")
    p.add_argument("--out", default=None, help="קובץ פלט Markdown (ברירת מחדל: לצד קובץ האודיו)")
    args = p.parse_args(argv)

    audio = Path(args.audio)
    if not audio.exists():
        print(f"❌ הקובץ לא נמצא: {audio}", file=sys.stderr)
        return 1

    t = Transcriber(args.model) if args.model else Transcriber()
    print(f"🎧 מתמלל עם Whisper {t.model_size}...", file=sys.stderr)
    transcript = t.transcribe(str(audio), language=args.language,
                              on_progress=lambda pct: print(f"\r   {pct}%", end="", file=sys.stderr))
    print(f"\n✅ תומלל: {transcript.duration:.0f} שניות, שפה: {transcript.language}", file=sys.stderr)

    summary = {"title": audio.stem}
    if not args.no_summary:
        print("🧠 מסכם ומחלץ נקודות מפתח...", file=sys.stderr)
        try:
            summary = Summarizer().summarize(transcript.timestamped_text(),
                                             output_language=args.summary_language,
                                             context=args.context)
        except SummaryError as e:
            print(f"⚠️  הסיכום נכשל: {e}", file=sys.stderr)

    md = summary_to_markdown(summary, transcript.timestamped_text())
    out = Path(args.out) if args.out else audio.with_suffix(".md")
    out.write_text(md, encoding="utf-8")
    print(md)
    print(f"\n💾 נשמר: {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
