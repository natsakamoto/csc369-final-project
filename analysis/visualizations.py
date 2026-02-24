import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_parquet("prep_for_model.parquet").copy()


df["helpful_ratio"] = df["helpful_votes"] / df["total_votes"]

# hist
plt.figure()
plt.hist(df["helpful_votes"], bins=200)
plt.yscale("log")
plt.xlabel("helpful_votes")
plt.ylabel("count (log scale)")
plt.title("Figure 1: Distribution of helpful_votes")
plt.tight_layout()
plt.savefig("fig1_helpful_votes_hist.png", dpi=200)

# bar plots
plt.figure()
data0 = df.loc[df["verified_purchase_int"] == 0, "helpful_ratio"].dropna()
data1 = df.loc[df["verified_purchase_int"] == 1, "helpful_ratio"].dropna()
plt.boxplot([data0.sample(min(len(data0), 50000), random_state=0),
             data1.sample(min(len(data1), 50000), random_state=0)],
            labels=["Not verified", "Verified"],
            showfliers=False)
plt.ylabel("helpful_ratio")
plt.title("Figure 2: Helpfulness rate by verified purchase")
plt.tight_layout()
plt.savefig("fig2_helpful_ratio_verified.png", dpi=200)

# word count vs helpful ratio
bins = [0, 20, 50, 100, 200, 500, 10_000]
labels = ["0-20", "21-50", "51-100", "101-200", "201-500", "500+"]
df["word_bin"] = pd.cut(df["review_body_word_count"], bins=bins, labels=labels, include_lowest=True)
grp = df.groupby("word_bin")["helpful_ratio"].mean()

plt.figure()
plt.plot(grp.index.astype(str), grp.values, marker="o")
plt.xticks(rotation=30, ha="right")
plt.ylabel("mean helpful_ratio")
plt.xlabel("review_body_word_count bin")
plt.title("Figure 3: Mean helpfulness rate vs review detail")
plt.tight_layout()
plt.savefig("fig3_helpful_ratio_wordbins.png", dpi=200)

# time series
df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
df["ym"] = df["review_date"].dt.to_period("M").astype(str)
monthly = df.groupby("ym")["helpful_ratio"].mean()

plt.figure()
plt.plot(monthly.index, monthly.values)
plt.xticks(rotation=60, ha="right")
plt.ylabel("mean helpful_ratio")
plt.xlabel("month")
plt.title("Figure 4: Helpfulness rate over time")
plt.tight_layout()
plt.savefig("fig4_helpful_ratio_time.png", dpi=200)

print("Saved figures: fig1_...png through fig4_...png")