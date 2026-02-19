#!/usr/bin/env python3
"""
Merge + clean all Amazon review parquet files into ONE parquet.

Run:
  python merge_clean_all.py --data_dir data --out merged_clean.parquet
"""

from __future__ import annotations
import argparse
import glob
import os
import duckdb


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", required=True, help="Folder containing amazon_reviews_*.snappy.parquet")
    ap.add_argument("--out", default="merged_clean.parquet", help="Output parquet file")
    ap.add_argument("--drop_blank_category", action="store_true", help="Drop rows with blank product_category")
    ap.add_argument("--drop_blank_body", action="store_true", help="Drop rows with blank review_body")
    args = ap.parse_args()

    pattern = os.path.join(args.data_dir, "amazon_reviews_*.snappy.parquet")
    files = sorted(glob.glob(pattern))
    if not files:
        raise SystemExit(f"No files matched: {pattern}")

    con = duckdb.connect(database=":memory:")


    base_scan = f"read_parquet('{pattern}', filename=true)"

    where_clauses = [
        "helpful_votes IS NULL OR total_votes IS NULL OR helpful_votes <= total_votes",
        "star_rating IS NULL OR (star_rating BETWEEN 1 AND 5)",
    ]
    if args.drop_blank_category:
        where_clauses.append("product_category IS NOT NULL AND TRIM(product_category) <> ''")
    if args.drop_blank_body:
        where_clauses.append("review_body IS NOT NULL AND TRIM(review_body) <> ''")

    where_sql = " AND ".join(where_clauses)

    out_escaped = args.out.replace("'", "''")

    con.execute(f"""
    COPY (
      WITH base AS (
        SELECT
          *,
          -- Safe string versions for filtering; NULL if invalid UTF-8
          try_cast(product_category AS VARCHAR) AS product_category_txt,
          try_cast(review_body AS VARCHAR) AS review_body_txt,
          filename AS source_file
        FROM read_parquet('{pattern}', filename=true)
      )
      SELECT
        (DATE '1970-01-01' + CAST(review_date AS INTEGER)) AS review_date,
        EXTRACT(YEAR FROM (DATE '1970-01-01' + CAST(review_date AS INTEGER)))::INTEGER AS review_year,

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

        -- store as bytes so output never crashes on encoding
        CAST(review_headline AS BLOB) AS review_headline_blob,
        CAST(review_body     AS BLOB) AS review_body_blob,

        source_file
      FROM base
      WHERE
        -- core cleaning
        (helpful_votes IS NULL OR total_votes IS NULL OR helpful_votes <= total_votes)
        AND (star_rating IS NULL OR star_rating BETWEEN 1 AND 5)

        -- optional blanks (only apply if you want them always; otherwise gate these in Python)
        AND product_category_txt IS NOT NULL AND TRIM(product_category_txt) <> ''
        AND review_body_txt IS NOT NULL AND TRIM(review_body_txt) <> ''
    ) TO '{out_escaped}'
      (FORMAT PARQUET, CODEC 'SNAPPY')
    """)

    print(f"✅ Wrote merged + cleaned parquet: {args.out}")
    print(f"   Input files: {len(files)}")
    print("   Text columns saved as BLOB (decode later in Python).")


if __name__ == "__main__":
    main()
