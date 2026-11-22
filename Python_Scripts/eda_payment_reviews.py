"""
eda_payment_reviews.py
----------------------
Step 3: EDA - Part 3: Payment Methods and Customer Review/Satisfaction Analysis.

PART A — Payment Analysis:
1. Transaction counts by payment type.
2. Total payment value by payment type.
3. Average Payment Transaction Value by method.
4. Instalment usage analysis (credit card only).

PART B — Review / Satisfaction Analysis:
1. Overall customer satisfaction metric (average review score).
2. Distribution of scores 1–5.
3. Positive, Neutral, and Negative review rates.
4. Average review score by product category (with deduplication).
5. Association between delivery timing and review scores.

All outputs saved to 'eda_outputs_part3/'.
Does NOT modify any original or cleaned CSV files.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


# ── STEP 1: PATHS AND DIRECTORIES ──────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CLEANED_DIR  = os.path.join(PROJECT_ROOT, "cleaned_data")
OUTPUT_DIR   = os.path.join(PROJECT_ROOT, "eda_outputs_part3")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SEPARATOR = "=" * 70
def print_header(title):
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(f"{SEPARATOR}")


# ── STEP 2: LOAD ALL REQUIRED CLEANED FILES ────────────────────────────────────
print_header("1. LOADING CLEANED DATASETS")

payments_df  = pd.read_csv(os.path.join(CLEANED_DIR, "olist_order_payments_dataset.csv"))
reviews_df   = pd.read_csv(os.path.join(CLEANED_DIR, "olist_order_reviews_dataset.csv"))
orders_df    = pd.read_csv(os.path.join(CLEANED_DIR, "olist_orders_dataset.csv"))
items_df     = pd.read_csv(os.path.join(CLEANED_DIR, "olist_order_items_dataset.csv"))
products_df  = pd.read_csv(os.path.join(CLEANED_DIR, "olist_products_dataset.csv"))
trans_df     = pd.read_csv(os.path.join(CLEANED_DIR, "product_category_name_translation.csv"))

# Convert date columns to datetime
date_cols = [
    "order_purchase_timestamp",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]
for col in date_cols:
    orders_df[col] = pd.to_datetime(orders_df[col])

reviews_df["review_creation_date"] = pd.to_datetime(reviews_df["review_creation_date"])

print(f"  Payments   : {len(payments_df):>7,} rows  |  {payments_df['payment_type'].nunique()} payment types")
print(f"  Reviews    : {len(reviews_df):>7,} rows  |  {reviews_df['order_id'].nunique():,} unique orders")
print(f"  Orders     : {len(orders_df):>7,} rows")
print(f"  Order Items: {len(items_df):>7,} rows")
print(f"  Products   : {len(products_df):>7,} rows")
print(f"  Translations: {len(trans_df):>6,} rows")


# =============================================================================
#  PART A: PAYMENT ANALYSIS
# =============================================================================
print_header("2. PART A: PAYMENT ANALYSIS")

# ── A1-A3: Transaction Counts, Total Revenue & Avg Transaction Value ───────────
# We keep payments_df STANDALONE for all payment metrics.
# Joining it with order_items would cause row multiplication (dangerous).

# Number of unique orders that used each payment method
orders_by_type = payments_df.groupby("payment_type")["order_id"].nunique().reset_index()
orders_by_type.columns = ["payment_type", "unique_orders"]

# Total payment value collected per method
# Safe to sum directly: each payment row is a distinct chunk of money
revenue_by_type = payments_df.groupby("payment_type")["payment_value"].sum().reset_index()
revenue_by_type.columns = ["payment_type", "total_payment_value"]

# Average Payment Transaction Value per method
# Label: "Average Payment Transaction Value" — NOT "average order value"
# because one order can have multiple payment rows (split payments)
avg_by_type = payments_df.groupby("payment_type")["payment_value"].mean().reset_index()
avg_by_type.columns = ["payment_type", "avg_payment_transaction_value"]

# Merge all three summaries into one table
payment_summary = pd.merge(orders_by_type, revenue_by_type, on="payment_type")
payment_summary = pd.merge(payment_summary, avg_by_type, on="payment_type")

# Add a percentage share column for unique orders
total_unique_orders_all = payments_df["order_id"].nunique()
payment_summary["order_share_pct"] = (
    payment_summary["unique_orders"] / total_unique_orders_all * 100
).round(2)

# Sort by unique orders descending
payment_summary = payment_summary.sort_values("unique_orders", ascending=False).reset_index(drop=True)

# Round monetary columns for readability
payment_summary["total_payment_value"]       = payment_summary["total_payment_value"].round(2)
payment_summary["avg_payment_transaction_value"] = payment_summary["avg_payment_transaction_value"].round(2)

print("\n  Payment Method Summary:")
print(f"  {'Payment Type':<15} {'Unique Orders':>14} {'Share %':>8} {'Total Value (R$)':>18} {'Avg Txn Value (R$)':>20}")
print(f"  {'-'*15} {'-'*14} {'-'*8} {'-'*18} {'-'*20}")
for _, row in payment_summary.iterrows():
    print(
        f"  {row['payment_type']:<15} {row['unique_orders']:>14,} "
        f"{row['order_share_pct']:>7.2f}% "
        f"  R$ {row['total_payment_value']:>14,.2f} "
        f"  R$ {row['avg_payment_transaction_value']:>14,.2f}"
    )

# Disclosure note
print("\n  [NOTE] An order split across two payment methods is counted in both groups.")
print("         The 'unique_orders' column counts distinct order_ids per method,")
print("         so column totals may exceed the total unique order count.")

payment_summary.to_csv(os.path.join(OUTPUT_DIR, "payment_summary.csv"), index=False)
print("  [SAVED] --> eda_outputs_part3/payment_summary.csv")


# ── A4: Instalment Usage Analysis (Credit Card Only) ──────────────────────────
print_header("3. INSTALMENT USAGE (CREDIT CARD ONLY)")

cc_payments = payments_df[payments_df["payment_type"] == "credit_card"].copy()

print(f"  Total credit card payment rows  : {len(cc_payments):,}")
print(f"  Unique orders using credit card : {cc_payments['order_id'].nunique():,}")
print(f"  Instalment range                : {int(cc_payments['payment_installments'].min())} to {int(cc_payments['payment_installments'].max())}")
print(f"  Average instalments chosen      : {cc_payments['payment_installments'].mean():.2f}")
print(f"  Median instalments chosen       : {cc_payments['payment_installments'].median():.1f}")

# Distribution by number of instalments
instalment_dist = cc_payments["payment_installments"].value_counts().sort_index().reset_index()
instalment_dist.columns = ["instalments", "order_count"]
instalment_dist["percentage"] = (instalment_dist["order_count"] / len(cc_payments) * 100).round(2)

# Group into readable buckets for printing
single_pay  = instalment_dist[instalment_dist["instalments"] == 1]["order_count"].sum()
short_term  = instalment_dist[(instalment_dist["instalments"] >= 2) & (instalment_dist["instalments"] <= 6)]["order_count"].sum()
long_term   = instalment_dist[instalment_dist["instalments"] >= 7]["order_count"].sum()
total_cc    = len(cc_payments)

print(f"\n  Instalment buckets:")
print(f"    1 instalment (full payment)   : {single_pay:>6,} ({single_pay/total_cc*100:.1f}%)")
print(f"    2–6 instalments (short-term)  : {short_term:>6,} ({short_term/total_cc*100:.1f}%)")
print(f"    7–24 instalments (long-term)  : {long_term:>6,} ({long_term/total_cc*100:.1f}%)")

instalment_dist.to_csv(os.path.join(OUTPUT_DIR, "installment_distribution.csv"), index=False)
print("  [SAVED] --> eda_outputs_part3/installment_distribution.csv")


# =============================================================================
#  PART B: REVIEW / SATISFACTION ANALYSIS
# =============================================================================
print_header("4. PART B: REVIEW DEDUPLICATION")

# Requirement: Keep only the MOST RECENT review per order_id.
# Some orders have more than one review row (551 duplicate order_ids confirmed).
# Strategy: sort by review_creation_date descending, then drop duplicate order_ids,
# keeping the first (= most recent) row per order.

print(f"  Reviews before deduplication : {len(reviews_df):,} rows")
print(f"  Unique order_ids in reviews  : {reviews_df['order_id'].nunique():,}")

reviews_dedup = reviews_df.sort_values(
    by=["order_id", "review_creation_date"],
    ascending=[True, False]   # newest review first within each order
).drop_duplicates(
    subset=["order_id"],
    keep="first"              # keep the most recent row per order
).copy()

reviews_removed = len(reviews_df) - len(reviews_dedup)
print(f"  Reviews after deduplication  : {len(reviews_dedup):,} rows")
print(f"  Duplicate review rows removed: {reviews_removed}")
print("  [NOTE] Missing comment columns (review_comment_title,")
print("         review_comment_message) are preserved as NaN — not dropped.")


# ── B1: Overall Customer Satisfaction Metric ───────────────────────────────────
print_header("5. OVERALL CUSTOMER SATISFACTION METRIC")

total_reviews    = len(reviews_dedup)
avg_review_score = reviews_dedup["review_score"].mean()
median_review    = reviews_dedup["review_score"].median()

print(f"  Total reviews analysed         : {total_reviews:,}")
print(f"  Average Review Score           : {avg_review_score:.3f} / 5.0")
print(f"  Median Review Score            : {median_review:.1f} / 5.0")


# ── B2: Distribution of Scores 1–5 ────────────────────────────────────────────
print_header("6. REVIEW SCORE DISTRIBUTION (1 TO 5)")

score_dist = reviews_dedup["review_score"].value_counts().sort_index().reset_index()
score_dist.columns = ["review_score", "count"]
score_dist["percentage"] = (score_dist["count"] / total_reviews * 100).round(2)

print(f"\n  {'Score':<8} {'Count':>8} {'Percentage':>11}")
print(f"  {'-'*8} {'-'*8} {'-'*11}")
for _, row in score_dist.iterrows():
    bar = "#" * int(row["percentage"] / 2)  # simple ASCII bar for terminal
    print(f"  {int(row['review_score']):<8} {row['count']:>8,} {row['percentage']:>9.2f}%  {bar}")

score_dist.to_csv(os.path.join(OUTPUT_DIR, "review_score_distribution.csv"), index=False)
print("\n  [SAVED] --> eda_outputs_part3/review_score_distribution.csv")


# ── B3: Positive, Neutral, and Negative Review Rates ──────────────────────────
print_header("7. SATISFACTION SENTIMENT BREAKDOWN")

# Score definitions (clearly stated):
#   Positive : score 4 or 5  — customer satisfied or delighted
#   Neutral  : score 3       — customer indifferent
#   Negative : score 1 or 2  — customer dissatisfied

positive_count = reviews_dedup[reviews_dedup["review_score"] >= 4]["review_score"].count()
neutral_count  = reviews_dedup[reviews_dedup["review_score"] == 3]["review_score"].count()
negative_count = reviews_dedup[reviews_dedup["review_score"] <= 2]["review_score"].count()

positive_pct = positive_count / total_reviews * 100
neutral_pct  = neutral_count  / total_reviews * 100
negative_pct = negative_count / total_reviews * 100

print(f"  Score Definitions:")
print(f"    Positive = scores 4 or 5   |  Neutral = score 3   |  Negative = scores 1 or 2")
print(f"\n  Positive Reviews (score 4–5) : {positive_count:>6,}  ({positive_pct:.2f}%)")
print(f"  Neutral Reviews  (score 3)   : {neutral_count:>6,}  ({neutral_pct:.2f}%)")
print(f"  Negative Reviews (score 1–2) : {negative_count:>6,}  ({negative_pct:.2f}%)")

review_summary = pd.DataFrame({
    "Metric": [
        "Total Reviews Analysed",
        "Average Review Score",
        "Median Review Score",
        "Positive Reviews (score 4-5) Count",
        "Positive Rate (%)",
        "Neutral Reviews (score 3) Count",
        "Neutral Rate (%)",
        "Negative Reviews (score 1-2) Count",
        "Negative Rate (%)"
    ],
    "Value": [
        total_reviews,
        round(avg_review_score, 3),
        median_review,
        positive_count,
        round(positive_pct, 2),
        neutral_count,
        round(neutral_pct, 2),
        negative_count,
        round(negative_pct, 2)
    ]
})
review_summary.to_csv(os.path.join(OUTPUT_DIR, "review_summary.csv"), index=False)
print("  [SAVED] --> eda_outputs_part3/review_summary.csv")


# ── B4: Average Review Score by Product Category ──────────────────────────────
print_header("8. REVIEW SCORES BY PRODUCT CATEGORY")

# Join path: reviews_dedup -> items_df -> products_df -> trans_df
# Step 1: Join deduplicated reviews with order_items to get (order_id, product_id) pairs
reviews_with_items = pd.merge(
    reviews_dedup[["order_id", "review_score"]],
    items_df[["order_id", "product_id"]],
    on="order_id",
    how="inner"     # only orders that appear in both tables
)

# Step 2: Join with products to get Portuguese category name
reviews_with_cat = pd.merge(
    reviews_with_items,
    products_df[["product_id", "product_category_name"]],
    on="product_id",
    how="left"
)

# Step 3: Join with translations to get English category name
reviews_with_cat = pd.merge(
    reviews_with_cat,
    trans_df,
    on="product_category_name",
    how="left"
)

# Fallback: if English name is missing, use the Portuguese name
reviews_with_cat["category_english"] = reviews_with_cat["product_category_name_english"].fillna(
    reviews_with_cat["product_category_name"].fillna("Unknown")
)

print(f"  Rows after join (before deduplication) : {len(reviews_with_cat):,}")

# ── CRITICAL DEDUPLICATION: Drop duplicate (order_id, category) pairs ─────────
# An order with 3 health_beauty items would otherwise contribute 3 identical
# (order_id, health_beauty, review_score) rows, giving that order's score
# 3× the weight in the category average. We keep only 1 row per pair.

reviews_with_cat_dedup = reviews_with_cat.drop_duplicates(
    subset=["order_id", "category_english"]
).copy()

print(f"  Rows after (order_id, category) dedup  : {len(reviews_with_cat_dedup):,}")
print(f"  Duplicate (order, category) rows removed: {len(reviews_with_cat) - len(reviews_with_cat_dedup):,}")

# Group by category and calculate avg score and count of unique order-reviews
category_scores = reviews_with_cat_dedup.groupby("category_english").agg(
    avg_review_score=("review_score", "mean"),
    attributed_order_reviews=("order_id", "count")
).reset_index()

# Apply minimum threshold: only report categories with >= 50 attributed reviews
category_scores = category_scores[category_scores["attributed_order_reviews"] >= 50].copy()
category_scores["avg_review_score"] = category_scores["avg_review_score"].round(3)
category_scores = category_scores.sort_values("avg_review_score", ascending=False)

print(f"\n  Categories with >= 50 reviews: {len(category_scores)}")
print(f"\n  Top 5 Highest Rated Categories:")
print(category_scores.head(5)[["category_english","avg_review_score","attributed_order_reviews"]].to_string(index=False))
print(f"\n  Bottom 5 Lowest Rated Categories:")
print(category_scores.tail(5)[["category_english","avg_review_score","attributed_order_reviews"]].to_string(index=False))

print("\n  [DATA LIMITATION] A single review is attributed to ALL categories")
print("  in a multi-category order. Each (order_id, category) pair is")
print("  counted once only — not once per item within the category.")

category_scores.to_csv(os.path.join(OUTPUT_DIR, "category_review_scores.csv"), index=False)
print("  [SAVED] --> eda_outputs_part3/category_review_scores.csv")


# ── B5: Delivery Timing vs. Review Score (Association, Not Causation) ──────────
print_header("9. DELIVERY TIMING vs. REVIEW SCORE ASSOCIATION")

# Filter: delivered orders with both actual and estimated delivery dates present
delivered = orders_df[orders_df["order_status"] == "delivered"].copy()
valid_delivery = delivered.dropna(
    subset=["order_delivered_customer_date", "order_estimated_delivery_date"]
).copy()

print(f"  Delivered orders (status='delivered')         : {len(delivered):,}")
print(f"  Excluded (missing date)                       : {len(delivered) - len(valid_delivery)}")
print(f"  Analysis denominator                          : {len(valid_delivery):,}")

# Calculate delivery variance in fractional days:
# variance = estimated_date - actual_delivered_date
# Positive: delivered early (before estimate)
# Negative: delivered late (after estimate)
valid_delivery["variance_days"] = (
    valid_delivery["order_estimated_delivery_date"] -
    valid_delivery["order_delivered_customer_date"]
).dt.total_seconds() / (24 * 3600)

# ── DELIVERY TIMING BUCKETS (Fractional-Day Aware) ────────────────────────────
# Boundaries are non-overlapping and cover ALL real number values,
# including fractional days such as 0.5, 6.5, -6.8, etc.
#
# variance >= 7.0          → Very Early  (7 or more full days ahead of estimate)
# 1.0 <= variance <  7.0   → Early       (1 to under 7 days ahead)
# 0.0 <= variance <  1.0   → On-Time     (arrived on or up to 1 day before estimate)
# -7.0 < variance <  0.0   → Slightly Late (arrived between 0 and under 7 days after)
# variance <= -7.0         → Very Late   (7 or more days after estimate)
#
# Every possible value of variance_days (including 6.5, -0.3, -7.0) falls
# into exactly ONE bucket. The boundaries use >= and < so there is no overlap.

def assign_delivery_bucket(variance_days):
    """
    Assigns one delivery timing bucket to each order based on variance_days.
    Handles fractional days (e.g. 0.5, 6.5) by using strict numerical boundaries.
    Non-overlapping: every valid float value maps to exactly one bucket.
    """
    if variance_days >= 7.0:
        return "Very Early (7+ days ahead)"
    elif variance_days >= 1.0:
        return "Early (1 to <7 days ahead)"
    elif variance_days >= 0.0:
        return "On-Time (0 to <1 day)"
    elif variance_days > -7.0:
        return "Slightly Late (0 to <7 days late)"
    else:
        return "Very Late (7+ days late)"

valid_delivery["delivery_bucket"] = valid_delivery["variance_days"].apply(assign_delivery_bucket)

# Define the display order so charts and tables read logically from best to worst
BUCKET_ORDER = [
    "Very Early (7+ days ahead)",
    "Early (1 to <7 days ahead)",
    "On-Time (0 to <1 day)",
    "Slightly Late (0 to <7 days late)",
    "Very Late (7+ days late)"
]

# Join with deduplicated reviews to get the review score for each delivered order
delivery_reviews = pd.merge(
    valid_delivery[["order_id", "variance_days", "delivery_bucket"]],
    reviews_dedup[["order_id", "review_score"]],
    on="order_id",
    how="inner"  # only orders that have both a delivery record and a review
)

print(f"  Orders matched with a review   : {len(delivery_reviews):,}")

# Group by bucket and calculate avg review score and order count
bucket_analysis = delivery_reviews.groupby("delivery_bucket").agg(
    order_count=("order_id", "count"),
    avg_review_score=("review_score", "mean"),
    median_review_score=("review_score", "median")
).reset_index()

bucket_analysis["avg_review_score"]    = bucket_analysis["avg_review_score"].round(3)
bucket_analysis["median_review_score"] = bucket_analysis["median_review_score"].round(1)
bucket_analysis["order_share_pct"]     = (
    bucket_analysis["order_count"] / len(delivery_reviews) * 100
).round(2)

# Sort by the logical bucket order
bucket_analysis["sort_key"] = bucket_analysis["delivery_bucket"].apply(
    lambda x: BUCKET_ORDER.index(x) if x in BUCKET_ORDER else 99
)
bucket_analysis = bucket_analysis.sort_values("sort_key").drop(columns="sort_key")

print(f"\n  Delivery Timing vs. Review Score Association")
print(f"  (ASSOCIATION ONLY — not evidence of causation)")
print()
print(f"  {'Bucket':<35} {'Orders':>7} {'Share%':>7} {'Avg Score':>10} {'Median':>7}")
print(f"  {'-'*35} {'-'*7} {'-'*7} {'-'*10} {'-'*7}")
for _, row in bucket_analysis.iterrows():
    print(
        f"  {row['delivery_bucket']:<35} {row['order_count']:>7,} "
        f"{row['order_share_pct']:>6.1f}% "
        f"{row['avg_review_score']:>10.3f} "
        f"{row['median_review_score']:>7.1f}"
    )

bucket_analysis.to_csv(os.path.join(OUTPUT_DIR, "delivery_delay_review_association.csv"), index=False)
print("\n  [SAVED] --> eda_outputs_part3/delivery_delay_review_association.csv")


# =============================================================================
#  CHARTS
# =============================================================================
print_header("10. GENERATING CHARTS")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 1: Payment Method — Unique Orders (horizontal bar)
# ─────────────────────────────────────────────────────────────────────────────
payment_chart = payment_summary.sort_values("unique_orders", ascending=True)

fig, ax1 = plt.subplots(figsize=(10, 5))
colors_pay = ["#2980b9", "#27ae60", "#e67e22", "#8e44ad", "#c0392b"]
bars = ax1.barh(
    payment_chart["payment_type"],
    payment_chart["unique_orders"],
    color=colors_pay[:len(payment_chart)],
    alpha=0.85,
    edgecolor="#2c3e50"
)
ax1.set_title("Payment Methods: Unique Order Counts", fontsize=13, fontweight="bold", pad=12)
ax1.set_xlabel("Unique Orders", fontsize=11)
ax1.set_ylabel("Payment Type", fontsize=11)
ax1.grid(axis="x", linestyle="--", alpha=0.5)
for bar in bars:
    w = bar.get_width()
    ax1.text(w + 300, bar.get_y() + bar.get_height() / 2,
             f"{w:,}", va="center", fontsize=9)
ax1.set_xlim(0, payment_chart["unique_orders"].max() * 1.12)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "payment_method_distribution.png"), dpi=300)
plt.close()
print("  [SAVED CHART 1] --> eda_outputs_part3/payment_method_distribution.png")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 2: Review Score Distribution (vertical bar, colour-coded)
# ─────────────────────────────────────────────────────────────────────────────
# Colour coding: 1–2 = red (negative), 3 = amber (neutral), 4–5 = green (positive)
score_colors = {1: "#e74c3c", 2: "#e74c3c", 3: "#f39c12", 4: "#27ae60", 5: "#27ae60"}
bar_colors   = [score_colors[s] for s in score_dist["review_score"]]

plt.figure(figsize=(8, 5))
bars = plt.bar(score_dist["review_score"], score_dist["count"],
               color=bar_colors, edgecolor="#2c3e50", alpha=0.85)
plt.title("Review Score Distribution (1–5)", fontsize=13, fontweight="bold", pad=12)
plt.xlabel("Review Score", fontsize=11)
plt.ylabel("Number of Reviews", fontsize=11)
plt.xticks([1, 2, 3, 4, 5], fontsize=11)
plt.grid(axis="y", linestyle="--", alpha=0.5)
for bar in bars:
    h = bar.get_height()
    pct = h / total_reviews * 100
    plt.text(bar.get_x() + bar.get_width() / 2, h + 400,
             f"{h:,}\n({pct:.1f}%)", ha="center", fontsize=8.5)
plt.ylim(0, score_dist["count"].max() * 1.15)

# Legend
legend_patches = [
    mpatches.Patch(color="#27ae60", label="Positive (4–5)"),
    mpatches.Patch(color="#f39c12", label="Neutral (3)"),
    mpatches.Patch(color="#e74c3c", label="Negative (1–2)")
]
plt.legend(handles=legend_patches, loc="upper left", fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "review_score_distribution.png"), dpi=300)
plt.close()
print("  [SAVED CHART 2] --> eda_outputs_part3/review_score_distribution.png")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 3: Top 15 Categories by Average Review Score
# ─────────────────────────────────────────────────────────────────────────────
top15_cat = category_scores.head(15).sort_values("avg_review_score", ascending=True)

plt.figure(figsize=(11, 7))
bar_colors_cat = ["#27ae60" if s >= 4.0 else "#f39c12" if s >= 3.5 else "#e74c3c"
                  for s in top15_cat["avg_review_score"]]
bars = plt.barh(top15_cat["category_english"], top15_cat["avg_review_score"],
                color=bar_colors_cat, edgecolor="#2c3e50", alpha=0.85)
plt.axvline(avg_review_score, color="#7f8c8d", linestyle=":", linewidth=1.8,
            label=f"Overall Avg ({avg_review_score:.2f})")
plt.title("Top 15 Product Categories by Average Review Score\n(after order–category deduplication)",
          fontsize=12, fontweight="bold", pad=12)
plt.xlabel("Average Review Score (out of 5)", fontsize=11)
plt.ylabel("Product Category (English)", fontsize=10)
plt.xlim(3.0, 5.0)
plt.grid(axis="x", linestyle="--", alpha=0.5)
for bar in bars:
    w = bar.get_width()
    plt.text(w + 0.01, bar.get_y() + bar.get_height() / 2,
             f"{w:.3f}", va="center", fontsize=8.5)
plt.legend(fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "category_review_scores.png"), dpi=300)
plt.close()
print("  [SAVED CHART 3] --> eda_outputs_part3/category_review_scores.png")


# ─────────────────────────────────────────────────────────────────────────────
# CHART 4: Delivery Timing Buckets vs. Average Review Score
# ─────────────────────────────────────────────────────────────────────────────
bucket_colors = {
    "Very Early (7+ days ahead)":        "#27ae60",
    "Early (1 to <7 days ahead)":        "#2ecc71",
    "On-Time (0 to <1 day)":             "#f39c12",
    "Slightly Late (0 to <7 days late)": "#e67e22",
    "Very Late (7+ days late)":          "#e74c3c"
}
bar_cols = [bucket_colors.get(b, "#95a5a6") for b in bucket_analysis["delivery_bucket"]]

plt.figure(figsize=(11, 5))
bars = plt.bar(bucket_analysis["delivery_bucket"],
               bucket_analysis["avg_review_score"],
               color=bar_cols, edgecolor="#2c3e50", alpha=0.87)
plt.axhline(avg_review_score, color="#7f8c8d", linestyle=":",
            linewidth=1.8, label=f"Overall Avg Score ({avg_review_score:.2f})")
plt.title("Delivery Timing vs. Average Review Score\n(Association Only — Not Evidence of Causation)",
          fontsize=12, fontweight="bold", pad=12)
plt.ylabel("Average Review Score (out of 5)", fontsize=11)
plt.xlabel("Delivery Timing Bucket", fontsize=11)
plt.xticks(fontsize=8.5, rotation=12, ha="right")
plt.ylim(3.0, 5.0)
plt.grid(axis="y", linestyle="--", alpha=0.5)
for bar in bars:
    h = bar.get_height()
    plt.text(bar.get_x() + bar.get_width() / 2, h + 0.02,
             f"{h:.3f}", ha="center", fontsize=9)
plt.legend(fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "delivery_delay_vs_review.png"), dpi=300)
plt.close()
print("  [SAVED CHART 4] --> eda_outputs_part3/delivery_delay_vs_review.png")

print_header("PART 3 EDA ANALYSIS COMPLETE")
