#!/usr/bin/env python3
"""Normalize smart punctuation that can break pasted HTML/CSS/JS code."""

from __future__ import annotations

import argparse
from pathlib import Path

REPLACEMENTS = {
    "\u2013": "-",   # en dash
    "\u2014": "--",  # em dash
    "\u2018": "'",   # left single quote
    "\u2019": "'",   # right single quote
    "\u201c": '"',   # left double quote
    "\u201d": '"',   # right double quote
    "\u00a0": " ",   # non-breaking space
}


def normalize_text(text: str) -> str:
    for src, dst in REPLACEMENTS.items():
        text = text.replace(src, dst)
    return text


def process_file(path: Path, write: bool) -> bool:
    original = path.read_text(encoding="utf-8")
    normalized = normalize_text(original)
    changed = normalized != original
    if changed and write:
        path.write_text(normalized, encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize smart punctuation in code-like text files.")
    parser.add_argument("paths", nargs="+", help="One or more file paths to process")
    parser.add_argument("--write", action="store_true", help="Write changes in place")
    args = parser.parse_args()

    changed_files = []
    for p in args.paths:
        path = Path(p)
        if not path.exists() or not path.is_file():
            print(f"skip: {path} (not a file)")
            continue

        changed = process_file(path, write=args.write)
        print(f"{'changed' if changed else 'ok'}: {path}")
        if changed:
            changed_files.append(str(path))

    if not args.write and changed_files:
        print("\nRun again with --write to apply these fixes.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
