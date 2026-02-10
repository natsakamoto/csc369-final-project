# CSC 369 Final Project Proposal


# Project Proposal — What makes an Amazon review “helpful”?

## 1) Research question

**Question:**  
What factors best predict whether an Amazon product review receives more
“helpful” votes?

## 2) Why this question is worth answering?

I shop a lot on Amazon, from karaoke machines to beanies, I’ll buy it
all. It’s important to me that I’m buying the best possible item, and so
i read the reviews. Understanding what is considered “helpful” is useful
because customers want to find trustworthy reviews quicker, Amazon wants
a better review ranking system, and sellers want to know what
information customers value.

## 3) Hypothesis

**Hypothesis:**  
1) Reviews that are verified purchases and more detailed text will
receive **more** helpful votes, on average, after controlling for star
rating, category, and time.

  
**Why:** People are more likely to trust a review if it looks like the
person actually bought and used the product. A detailed review give
potential buyers more information so they are more likely to mark
“helpful”.

### Variables of interest

**target:**

- helpful_votes: number of times review was marked as “helpful” (int)

**features:**

- verified_purchase - Whether the reviewer purchased the item (bool)

- review_body - Written review of item (str)

## 4) Primary dataset

**Primary dataset:** ClickHouse “Amazon Customer Review” dataset  
Contains over 150M customer reviews of Amazon products. The data is in
snappy-compressed Parquet files in AWS S3 that total 49GB in size
(compressed).

**Link to Dataset:**
<https://clickhouse.com/docs/getting-started/example-datasets/amazon-reviews?utm_source=chatgpt.com#loading-the-dataset>

I plan on only using a fraction of this data set (around 16-20 GB).
