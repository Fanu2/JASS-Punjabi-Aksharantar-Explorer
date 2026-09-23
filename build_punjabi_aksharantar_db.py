import sqlite3
import zipfile
import json
from pathlib import Path

BASE = Path(r"C:\Users\singh\Downloads\Punjabi_Aksharantar")
ZIP = BASE / "pan.zip"
DB = BASE / "JASS_Punjabi_Aksharantar.db"

print("Punjabi Aksharantar Database Builder")
print("=" * 50)

if not ZIP.exists():
    raise FileNotFoundError(f"ZIP not found: {ZIP}")

if DB.exists():
    print(f"Database already exists:")
    print(DB)
    print("Delete it first if you want to rebuild it.")
    raise SystemExit

con = sqlite3.connect(DB)

con.execute("""
CREATE TABLE entries (
    id INTEGER PRIMARY KEY,
    unique_identifier TEXT NOT NULL,
    native_word TEXT NOT NULL,
    romanized_word TEXT NOT NULL,
    source TEXT,
    score REAL,
    split TEXT NOT NULL
)
""")

con.execute("""
CREATE VIRTUAL TABLE entries_fts USING fts5(
    native_word,
    romanized_word,
    content='entries',
    content_rowid='id'
)
""")

datasets = [
    ("pan_train.json", "train"),
    ("pan_valid.json", "valid"),
    ("pan_test.json", "test"),
]

total = 0

with zipfile.ZipFile(ZIP, "r") as z:

    for filename, split in datasets:

        print(f"\nProcessing {filename}...")

        count = 0
        batch = []

        with z.open(filename) as f:

            for raw in f:

                if not raw.strip():
                    continue

                record = json.loads(raw.decode("utf-8"))

                batch.append((
                    record.get("unique_identifier"),
                    record.get("native word"),
                    record.get("english word"),
                    record.get("source"),
                    record.get("score"),
                    split
                ))

                if len(batch) >= 5000:

                    con.executemany("""
                    INSERT INTO entries
                    (
                        unique_identifier,
                        native_word,
                        romanized_word,
                        source,
                        score,
                        split
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, batch)

                    count += len(batch)
                    total += len(batch)
                    batch.clear()

            if batch:

                con.executemany("""
                INSERT INTO entries
                (
                    unique_identifier,
                    native_word,
                    romanized_word,
                    source,
                    score,
                    split
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """, batch)

                count += len(batch)
                total += len(batch)

        print(f"  Records: {count:,}")

print("\nBuilding FTS5 index...")

con.execute("""
INSERT INTO entries_fts(rowid, native_word, romanized_word)
SELECT id, native_word, romanized_word
FROM entries
""")

print("Creating indexes...")

con.execute("""
CREATE INDEX idx_native
ON entries(native_word)
""")

con.execute("""
CREATE INDEX idx_romanized
ON entries(romanized_word)
""")

con.execute("""
CREATE INDEX idx_source
ON entries(source)
""")

con.execute("""
CREATE INDEX idx_split
ON entries(split)
""")

con.commit()

print("\n" + "=" * 50)
print("DATABASE CREATED SUCCESSFULLY")
print("=" * 50)

print(f"Database : {DB}")
print(f"Records  : {total:,}")
print(f"Size     : {DB.stat().st_size / 1024 / 1024:.2f} MB")

print("\nSplit statistics:")

for split in ("train", "valid", "test"):

    n = con.execute(
        "SELECT COUNT(*) FROM entries WHERE split=?",
        (split,)
    ).fetchone()[0]

    print(f"  {split:8} {n:,}")

print("\nSample records:")

rows = con.execute("""
SELECT native_word, romanized_word, source, split
FROM entries
LIMIT 10
""").fetchall()

for row in rows:
    print(row)

con.close()

print("\nFinished.")