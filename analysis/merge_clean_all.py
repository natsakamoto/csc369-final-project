import duckdb
from pathlib import Path

IN_FILE = Path("../data_cleaning/merged_clean.parquet")
OUT_FILE = Path("filtered_df.parquet")

con = duckdb.connect()

con.execute(f"""
COPY (
  WITH base AS (
    SELECT
      review_id,
      review_date,
      helpful_votes,
      total_votes,
      verified_purchase,
      star_rating,

      CAST(product_category AS VARCHAR)      AS product_category_str,
      CAST(product_title AS VARCHAR)         AS product_title_str,
      CAST(review_body_blob AS VARCHAR)      AS review_body_str,
      CAST(review_headline_blob AS VARCHAR)  AS review_headline_str
    FROM read_parquet('{IN_FILE.as_posix()}')
  )
  SELECT
    review_id,
    review_date,
    star_rating,
    product_category_str AS product_category,
    helpful_votes,
    total_votes,
    CASE
      WHEN total_votes = 0 AND helpful_votes = 0 THEN 0.0
      WHEN total_votes > 0 THEN helpful_votes::DOUBLE / total_votes
      ELSE NULL
    END AS helpful_ratio,
    verified_purchase,

    CASE
      WHEN review_body_str IS NULL OR trim(review_body_str) = '' THEN 0
      ELSE array_length(regexp_extract_all(review_body_str, '[A-Za-z0-9]+'))
    END AS review_body_word_count,

    CASE
      WHEN product_title_str IS NULL OR trim(product_title_str) = '' THEN 0
      ELSE array_length(regexp_extract_all(product_title_str, '[A-Za-z0-9]+'))
    END AS product_title_word_count,

    (strpos(review_headline_str, '!') > 0) AS headline_has_exclaim

  FROM base
) TO '{OUT_FILE.as_posix()}'
  (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000);
""")

