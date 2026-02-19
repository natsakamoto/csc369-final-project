#!/usr/bin/env python3
"""
Sample N rows from EACH Parquet file in a folder and write them into ONE combined Parquet file.

"""

from __future__ import annotations

import argparse
import glob
import os
from typing import List

import duckdb


def find_parquet_files(data_dir: str) -> List[str]:
    pattern = os.path.join(data_dir, "amazon_reviews_*.snappy.parquet")
    files = sorted(glob.glob(pattern))
    return files


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", required=True, help="Folder containing amazon_reviews_*.snappy.parquet files")
    ap.add_argument("--n", type=int, default=5000, help="Rows to sample per file")
    ap.add_argument("--out", default="combined_sample.parquet", help="Output combined parquet file")
    args = ap.parse_args()

    files = find_parquet_files(args.data_dir)
    if not files:
        raise SystemExit(
            f"No files found. Expected something like:\n"
            f"  {os.path.join(args.data_dir, 'amazon_reviews_2010.snappy.parquet')}\n"
            f"Check --data_dir and filenames."
        )

    con = duckdb.connect(database=":memory:")


    selects: List[str] = []
    for f in files:
        f_escaped = f.replace("'", "''")
        selects.append(
            f"""
(
  SELECT
    -- Convert "days since 1970-01-01" to a real DATE
    (DATE '1970-01-01' + CAST(review_date AS INTEGER)) AS review_date,

    marketplace,
    customer_id,
    review_id,
    product_id,
    product_parent,
    product_title,
    product_category,
    star_rating,
    helpful_votes,
    total_votes,
    vine,
    verified_purchase,

    -- Store as raw bytes to avoid invalid UTF-8 crashing DuckDB
    CAST(review_headline AS BLOB) AS review_headline_blob,
    CAST(review_body     AS BLOB) AS review_body_blob,

    -- Helpful for debugging / provenance:
    '{os.path.basename(f_escaped)}' AS source_file
  FROM read_parquet('{f_escaped}')
  ORDER BY hash(review_id)   -- deterministic "random-ish" sample
  LIMIT {args.n}
)
""".strip()
        )

    union_query = "\nUNION ALL\n".join(selects)

    out_escaped = args.out.replace("'", "''")

    con.execute(
        f"""
COPY (
  {union_query}
) TO '{out_escaped}'
  (FORMAT PARQUET, CODEC 'SNAPPY')
"""
    )

    print(f"✅ Wrote combined sample to: {args.out}")
    print(f"   Files sampled: {len(files)}")
    print(f"   Rows per file: {args.n}")
    print(f"   Total rows (expected): {len(files) * args.n}")
    print("   Note: review_headline/body saved as BLOB to avoid invalid UTF-8 errors.")


if __name__ == "__main__":
    main()
