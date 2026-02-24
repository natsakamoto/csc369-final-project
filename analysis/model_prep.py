import duckdb

con = duckdb.connect()

con.execute("""
CREATE OR REPLACE TABLE prep AS
SELECT
  *,
  strftime(CAST(review_date AS TIMESTAMP), '%Y-%m') AS ym,
  ln(1 + greatest(review_body_word_count, 0)) AS log_review_words,
  ln(total_votes) AS log_total_votes,
  CAST(verified_purchase AS INTEGER) AS verified_purchase_int
FROM read_parquet('filtered_df.parquet')
WHERE
   product_category IN (
  'Apparel',
  'Beauty',
  'Jewelry',
  'Video Games',
  'Health & Personal Care'
)
  AND review_date IS NOT NULL
  AND helpful_votes IS NOT NULL
  AND total_votes IS NOT NULL
  AND star_rating IS NOT NULL
  AND product_category IS NOT NULL
  AND total_votes > 0;
""")

con.execute("""
COPY prep TO 'prep_for_model.parquet'
  (FORMAT PARQUET, COMPRESSION ZSTD);
""")

