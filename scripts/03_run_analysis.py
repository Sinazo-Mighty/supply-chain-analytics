"""
Step 3: run the SQL analysis locally on the processed CSVs (no database needed).
Run from the repo root:  py -3.13 scripts/03_run_analysis.py
Needs:  py -3.13 -m pip install duckdb pandas
Prints each result and saves it as a CSV in reports/ (handy for Power BI and your README).
"""
import re
from pathlib import Path

import duckdb

PROCESSED = Path("data/processed")
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)

con = duckdb.connect()
for table in ["dim_customer", "dim_product", "dim_location", "dim_date", "fact_order_item"]:
    con.execute(f"CREATE VIEW {table} AS SELECT * FROM read_csv_auto('{PROCESSED / table}.csv')")

sql_text = Path("sql/02_analysis.sql").read_text(encoding="utf-8")
# Split the file into queries at each "-- name: <query_name>" marker.
parts = re.split(r"^-- name:\s*(\w+)\s*$", sql_text, flags=re.MULTILINE)

for name, query in zip(parts[1::2], parts[2::2]):
    result = con.execute(query.strip().rstrip(";")).fetchdf()
    result.to_csv(REPORTS / f"{name}.csv", index=False)
    print(f"\n=== {name} ===")
    print(result.to_string(index=False))
