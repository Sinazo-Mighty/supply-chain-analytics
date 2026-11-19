"""
Step 2: load the processed CSVs into Postgres (Supabase).
Run from the repo root:  python scripts/02_load_to_supabase.py

Needs a DATABASE_URL environment variable (see README / chat for how to get it).
Safe to re-run: it empties the tables first, then reloads them.
"""
import csv
import os
import sys
from pathlib import Path

import psycopg2

DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    sys.exit("DATABASE_URL is not set. See setup notes.")

PROCESSED = Path("data/processed")
# Dimensions first, fact last (the fact table has foreign keys to the dimensions).
LOAD_ORDER = ["dim_customer", "dim_product", "dim_location", "dim_date", "fact_order_item"]

conn = psycopg2.connect(DB_URL)
conn.autocommit = False
try:
    with conn.cursor() as cur:
        # Empty everything first so the script can be re-run safely.
        cur.execute("TRUNCATE " + ", ".join(reversed(LOAD_ORDER)) + " CASCADE;")

        for table in LOAD_ORDER:
            path = PROCESSED / f"{table}.csv"
            with open(path, newline="", encoding="utf-8") as f:
                columns = next(csv.reader(f))          # header row
                f.seek(0)
                cur.copy_expert(
                    f"COPY {table} ({', '.join(columns)}) FROM STDIN WITH (FORMAT csv, HEADER true)",
                    f,
                )
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            print(f"{table:16s} {cur.fetchone()[0]:>9,} rows loaded")
    conn.commit()
    print("Done.")
except Exception:
    conn.rollback()
    raise
finally:
    conn.close()
