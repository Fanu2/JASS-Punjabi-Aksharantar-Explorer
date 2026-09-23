"""
JASS Punjabi Literature Corpus Inspector v1.0
Read-only inspector for a folder of Punjabi .txt literary works.

Reports:
- file inventory
- size
- encoding detected (best effort)
- line / paragraph / word / character counts
- Gurmukhi and Shahmukhi character counts
- duplicate-file hash detection
- corpus totals

It does NOT modify the source .txt files.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from datetime import datetime

try:
    import chardet
except ImportError:
    chardet = None

FOLDER = Path(r"C:\Users\singh\Downloads\1762611761169-MEDIAMEN's Punjabi Literature Corpus")
OUTPUT = FOLDER / "punjabi_literature_inspection_report.txt"

GURMUKHI_RE = re.compile(r"[\u0A00-\u0A7F]")
SHAHMUKHI_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def decode_bytes(data: bytes) -> tuple[str, str]:
    # Prefer UTF-8, then common Punjabi/Urdu encodings.
    for enc in ("utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            pass

    if chardet:
        result = chardet.detect(data)
        enc = result.get("encoding")
        if enc:
            try:
                return data.decode(enc), f"{enc} (detected)"
            except (UnicodeDecodeError, LookupError):
                pass

    return data.decode("utf-8", errors="replace"), "utf-8 (replacement characters)"


def word_count(text: str) -> int:
    # Unicode-aware approximation: whitespace-separated tokens.
    return len(re.findall(r"\S+", text))


def paragraph_count(text: str) -> int:
    blocks = [p for p in re.split(r"\n\s*\n+", text) if p.strip()]
    return len(blocks)


def main() -> None:
    print("JASS PUNJABI LITERATURE CORPUS INSPECTOR v1.0")
    print("=" * 48)
    print(f"Folder: {FOLDER}")
    print("Mode: READ-ONLY")
    print()

    if not FOLDER.exists():
        print("ERROR: Folder not found.")
        print("Edit FOLDER at the top of this script to match the actual folder name.")
        return

    files = sorted(FOLDER.glob("*.txt"), key=lambda p: p.name.lower())

    if not files:
        print("ERROR: No .txt files found.")
        return

    print(f"Text files found: {len(files)}")
    print("Scanning...")
    print()

    rows = []
    hash_map = {}

    total_bytes = 0
    total_chars = 0
    total_words = 0
    total_lines = 0
    total_paragraphs = 0
    total_gurmukhi = 0
    total_shahmukhi = 0

    for i, path in enumerate(files, 1):
        data = path.read_bytes()
        text, encoding = decode_bytes(data)

        size = len(data)
        chars = len(text)
        words = word_count(text)
        lines = len(text.splitlines())
        paragraphs = paragraph_count(text)
        gur = len(GURMUKHI_RE.findall(text))
        shah = len(SHAHMUKHI_RE.findall(text))
        digest = sha256(path)

        row = {
            "name": path.name,
            "size": size,
            "encoding": encoding,
            "lines": lines,
            "paragraphs": paragraphs,
            "words": words,
            "chars": chars,
            "gurmukhi": gur,
            "shahmukhi": shah,
            "sha256": digest,
        }
        rows.append(row)
        hash_map.setdefault(digest, []).append(path.name)

        total_bytes += size
        total_chars += chars
        total_words += words
        total_lines += lines
        total_paragraphs += paragraphs
        total_gurmukhi += gur
        total_shahmukhi += shah

        print(f"  [{i:02d}/{len(files):02d}] {path.name} — {words:,} words")

    duplicate_groups = [names for names in hash_map.values() if len(names) > 1]

    def mb(n: int) -> float:
        return n / (1024 * 1024)

    report = []
    report.append("JASS PUNJABI LITERATURE CORPUS INSPECTION REPORT v1.0")
    report.append("=" * 58)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Source folder: {FOLDER}")
    report.append("Mode: READ-ONLY")
    report.append("")
    report.append("CORPUS SUMMARY")
    report.append("-" * 58)
    report.append(f"Text files:          {len(files):,}")
    report.append(f"Total size:          {mb(total_bytes):,.2f} MB")
    report.append(f"Total words:         {total_words:,}")
    report.append(f"Total characters:    {total_chars:,}")
    report.append(f"Total lines:         {total_lines:,}")
    report.append(f"Total paragraphs:    {total_paragraphs:,}")
    report.append(f"Gurmukhi characters: {total_gurmukhi:,}")
    report.append(f"Shahmukhi/Arabic:    {total_shahmukhi:,}")
    report.append(f"Duplicate groups:    {len(duplicate_groups):,}")
    report.append("")

    report.append("FILE INVENTORY")
    report.append("-" * 58)

    for idx, r in enumerate(rows, 1):
        report.append(f"{idx:02d}. {r['name']}")
        report.append(f"    Size:       {mb(r['size']):,.2f} MB ({r['size']:,} bytes)")
        report.append(f"    Encoding:   {r['encoding']}")
        report.append(f"    Words:      {r['words']:,}")
        report.append(f"    Characters: {r['chars']:,}")
        report.append(f"    Lines:      {r['lines']:,}")
        report.append(f"    Paragraphs:  {r['paragraphs']:,}")
        report.append(f"    Gurmukhi:   {r['gurmukhi']:,}")
        report.append(f"    Shahmukhi:  {r['shahmukhi']:,}")
        report.append(f"    SHA-256:    {r['sha256']}")
        report.append("")

    report.append("DUPLICATES")
    report.append("-" * 58)
    if duplicate_groups:
        for n, names in enumerate(duplicate_groups, 1):
            report.append(f"Group {n}:")
            for name in names:
                report.append(f"  {name}")
    else:
        report.append("No exact duplicate files detected by SHA-256.")

    report.append("")
    report.append("NOTES")
    report.append("-" * 58)
    report.append("Counts are informational and use Unicode text processing.")
    report.append("The source .txt files were opened read-only and were not modified.")
    report.append("This inspection is a preparation step for a possible SQLite/FTS5")
    report.append("JASS Punjabi Literature database and Explorer.")

    OUTPUT.write_text("\n".join(report), encoding="utf-8")

    print()
    print("JASS PUNJABI LITERATURE INSPECTION COMPLETE")
    print("=" * 48)
    print(f"Files:              {len(files):,}")
    print(f"Total size:         {mb(total_bytes):,.2f} MB")
    print(f"Total words:        {total_words:,}")
    print(f"Total characters:   {total_chars:,}")
    print(f"Gurmukhi chars:     {total_gurmukhi:,}")
    print(f"Shahmukhi/Arabic:   {total_shahmukhi:,}")
    print(f"Duplicate groups:   {len(duplicate_groups):,}")
    print()
    print(f"Report written to:  {OUTPUT}")


if __name__ == "__main__":
    main()
