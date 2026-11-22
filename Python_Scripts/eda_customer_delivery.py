"""
eda_customer_delivery.py
------------------------
Step 3: Exploratory Data Analysis (EDA) - Part 2:
Customer Behaviour and Delivery Performance Analysis.

Analyses:
PART A - Customer Behaviour:
1. Unique customer counts and comparison with transaction IDs.
2. New vs. Repeat customers and repeat purchase rate.
3. Distribution of orders per customer.
4. Multi-state customer audit and geographic distribution by state.
5. Purchasing frequency (days between purchases for repeat buyers).

PART B - Delivery Performance:
1. Average and median actual delivery lead time (days).
2. Estimated vs. actual delivery comparison (on-time vs. late rates).
3. Clear reporting of the delivered orders denominator.
4. Monthly trend of average delivery days.
5. Delivery speed and on-time performance by customer state.

Saves all tables and charts in 'eda_outputs_part2'.
Does NOT modify any original or cleaned CSV files.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt


# ── STEP 1: SET UP PATHS & DIRECTORIES ─────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CLEANED_DIR = os.path.join(PROJECT_ROOT, "cleaned_data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "eda_outputs_part2")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SEPARATOR = "=" * 70

def print_header(title):
    """Prints a clear, formatted header banner."""
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(f"{SEPARATOR}")


# ── STEP 2: LOAD REQUIRED CLEANED FILES ────────────────────────────────────────
print_header("1. LOADING CLEANED DATASETS")

# 1. Orders dataset
orders_path = os.path.join(CLEANED_DIR, "olist_orders_dataset.csv")
orders_df = pd.read_csv(orders_path)

# Convert all date columns to datetime
date_cols = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]
for col in date_cols:
    orders_df[col] = pd.to_datetime(orders_df[col])

print(f"  Loaded orders: {len(orders_df):,} rows")

# 2. Customers dataset
customers_path = os.path.join(CLEANED_DIR, "olist_customers_dataset.csv")
customers_df = pd.read_csv(customers_path)
print(f"  Loaded customers: {len(customers_df):,} rows")


# =============================================================================
# PART A: CUSTOMER BEHAVIOUR ANALYSIS
# =============================================================================
print_header("2. PART A: CUSTOMER BEHAVIOUR ANALYSIS")

# ── A1. Unique Customer Counts ───────────────────────────────────────────────
total_transactions = customers_df["customer_id"].nunique()
total_unique_customers = customers_df["customer_unique_id"].nunique()

print(f"  Total Transaction Accounts (customer_id)      : {total_transactions:,}")
print(f"  Total Unique Human Customers (customer_unique_id): {total_unique_customers:,}")
print(f"  Insight: The presence of fewer unique customers ({total_unique_customers:,})")
print(f"           than transactions ({total_transactions:,}) proves repeat purchasing exists.")

# ── A2 & A3. Order Frequency & Repeat Customer Rate ──────────────────────────
# Group by customer_unique_id and count how many orders each person placed
customer_order_counts = customers_df.groupby("customer_unique_id")["customer_id"].count().reset_index()
customer_order_counts.columns = ["customer_unique_id", "order_count"]

# Count one-time vs repeat customers
one_time_buyers = (customer_order_counts["order_count"] == 1).sum()
repeat_buyers = (customer_order_counts["order_count"] > 1).sum()
repeat_rate = (repeat_buyers / total_unique_customers) * 100

print(f"\n  One-Time Buyers (1 order placed)               : {one_time_buyers:,} ({one_time_buyers/total_unique_customers*100:.2f}%)")
print(f"  Repeat Buyers (2+ orders placed)               : {repeat_buyers:,} ({repeat_rate:.2f}%)")
print(f"  Repeat Purchase Rate                           : {repeat_rate:.2f}%")

# Distribution of order counts: 1, 2, 3, 4, 5+ orders
def bucket_orders(count):
    if count == 1:
        return "1 Order"
    elif count == 2:
        return "2 Orders"
    elif count == 3:
        return "3 Orders"
    else:
        return "4+ Orders"

customer_order_counts["order_bucket"] = customer_order_counts["order_count"].apply(bucket_orders)
orders_distribution = customer_order_counts["order_bucket"].value_counts().reindex(
    ["1 Order", "2 Orders", "3 Orders", "4+ Orders"]
).reset_index()
orders_distribution.columns = ["Order Bucket", "Customer Count"]
orders_distribution["Percentage"] = (orders_distribution["Customer Count"] / total_unique_customers) * 100

print("\n  Orders per Customer Distribution:")
for _, row in orders_distribution.iterrows():
    print(f"    {row['Order Bucket']:<12}: {row['Customer Count']:>6,} customers ({row['Percentage']:.2f}%)")

orders_distribution.to_csv(os.path.join(OUTPUT_DIR, "orders_per_customer.csv"), index=False)
print("  [SAVED] --> eda_outputs_part2/orders_per_customer.csv")

# ── A4. Multi-State Customer Audit & Customer Geographic Distribution ────────
print_header("3. MULTI-STATE CUSTOMER AUDIT & STATE DISTRIBUTION")

# Requirement: Check whether any customer_unique_id appears in multiple states
customer_states = customers_df.groupby("customer_unique_id")["customer_state"].nunique()
multi_state_customers = customer_states[customer_states > 1]
num_multi_state = len(multi_state_customers)

print(f"  Checking multi-state customer IDs:")
print(f"  Total unique customers                 : {total_unique_customers:,}")
print(f"  Customers associated with >1 state     : {num_multi_state:,} ({num_multi_state/total_unique_customers*100:.3f}%)")
print("  Analytical Note:")
print("    39 repeat customers ordered to different states (e.g. relocated or shipped gifts).")
print("    To prevent silent arbitrary state assignment, we link each customer to their")
print("    MOST RECENT order purchase date to determine their primary active state.")

# Attach order purchase dates to customer records so we can identify the latest state
cust_with_orders = pd.merge(
    customers_df[["customer_id", "customer_unique_id", "customer_state"]],
    orders_df[["order_id", "customer_id", "order_purchase_timestamp"]],
    on="customer_id",
    how="left"
)

# Sort by customer_unique_id and purchase timestamp descending, then keep the first (latest)
latest_customer_state = cust_with_orders.sort_values(
    by=["customer_unique_id", "order_purchase_timestamp"],
    ascending=[True, False]
).drop_duplicates(subset=["customer_unique_id"]).copy()

# Group by the resolved primary state
state_customers = latest_customer_state["customer_state"].value_counts().reset_index()
state_customers.columns = ["State", "Unique Customers"]
state_customers["Percentage"] = (state_customers["Unique Customers"] / total_unique_customers) * 100

print("\n  Top 10 States by Unique Customer Count:")
print(state_customers.head(10).to_string(index=False))

state_customers.to_csv(os.path.join(OUTPUT_DIR, "top_customer_states.csv"), index=False)
print("\n  [SAVED] --> eda_outputs_part2/top_customer_states.csv")

# ── A5. Purchasing Frequency (Time Between Orders for Repeat Buyers) ──────────
print_header("4. PURCHASING FREQUENCY (REPEAT BUYERS)")

# Get all orders placed by repeat customers
repeat_customer_ids = customer_order_counts[customer_order_counts["order_count"] > 1]["customer_unique_id"]

repeat_orders = pd.merge(
    orders_df[["order_id", "customer_id", "order_purchase_timestamp"]],
    customers_df[customers_df["customer_unique_id"].isin(repeat_customer_ids)][["customer_id", "customer_unique_id"]],
    on="customer_id",
    how="inner"
)

# Sort by customer and purchase timestamp
repeat_orders = repeat_orders.sort_values(by=["customer_unique_id", "order_purchase_timestamp"])

# Calculate difference in days between consecutive purchases
repeat_orders["prev_purchase"] = repeat_orders.groupby("customer_unique_id")["order_purchase_timestamp"].shift(1)
repeat_orders["days_between_orders"] = (
    repeat_orders["order_purchase_timestamp"] - repeat_orders["prev_purchase"]
).dt.total_seconds() / (24 * 3600)

# Filter valid intervals (first order has NaN for prev_purchase)
reorder_intervals = repeat_orders["days_between_orders"].dropna()

median_days_reorder = reorder_intervals.median()
mean_days_reorder = reorder_intervals.mean()

print(f"  Total reorder events analyzed : {len(reorder_intervals):,}")
print(f"  Median days between purchases : {median_days_reorder:.1f} days")
print(f"  Average days between purchases: {mean_days_reorder:.1f} days")
print(f"  Insight: The typical repeat customer returns after ~{median_days_reorder:.0f} days (around 2.5 to 3 months).")

# Save customer KPI summary
customer_kpis = pd.DataFrame({
    "Metric": [
        "Total Unique Customers",
        "One-Time Buyers",
        "Repeat Buyers",
        "Repeat Purchase Rate (%)",
        "Customers in Multiple States",
        "Median Days Between Repeat Orders"
    ],
    "Value": [
        total_unique_customers,
        one_time_buyers,
        repeat_buyers,
        round(repeat_rate, 2),
        num_multi_state,
        round(median_days_reorder, 1)
    ]
})
customer_kpis.to_csv(os.path.join(OUTPUT_DIR, "customer_kpis.csv"), index=False)
print("  [SAVED] --> eda_outputs_part2/customer_kpis.csv")


# =============================================================================
# PART B: DELIVERY PERFORMANCE ANALYSIS
# =============================================================================
print_header("5. PART B: DELIVERY PERFORMANCE ANALYSIS")

# ── B1, B2 & B3. Lead Times, On-Time vs. Late Rates & Denominator ────────────
# Requirement: Calculate delivery performance ONLY on delivered orders with
# BOTH actual delivery date and estimated delivery date available.
delivered_all = orders_df[orders_df["order_status"] == "delivered"].copy()
total_delivered_status = len(delivered_all)

# Drop any rows where actual or estimated date is missing
valid_delivery = delivered_all.dropna(
    subset=["order_delivered_customer_date", "order_estimated_delivery_date"]
).copy()
denominator_delivery = len(valid_delivery)
missing_delivery_dates = total_delivered_status - denominator_delivery

print(f"  Delivery Performance Denominator Reporting:")
print(f"    Total orders with status 'delivered'         : {total_delivered_status:,}")
print(f"    Delivered orders missing actual delivery date: {missing_delivery_dates} (excluded)")
print(f"    ANALYSIS DENOMINATOR (Delivered + Valid Dates): {denominator_delivery:,}")

# 1. Actual Delivery Lead Time (Purchase Date to Actual Delivery Date)
valid_delivery["actual_delivery_days"] = (
    valid_delivery["order_delivered_customer_date"] - valid_delivery["order_purchase_timestamp"]
).dt.total_seconds() / (24 * 3600)

avg_delivery_days = valid_delivery["actual_delivery_days"].mean()
median_delivery_days = valid_delivery["actual_delivery_days"].median()

print(f"\n  Actual Delivery Lead Time:")
print(f"    Average Delivery Time : {avg_delivery_days:.1f} days")
print(f"    Median Delivery Time  : {median_delivery_days:.1f} days")
print(f"    (Median is lower than average due to long-tail delivery outliers in remote regions)")

# 2. On-Time vs. Late Performance
# delivery_variance = estimated_date - actual_delivered_date
# Positive (> 0) means delivered BEFORE estimated date (Early)
# Exactly 0 means delivered on the estimated date (On-Time)
# Negative (< 0) means delivered AFTER estimated date (Late)
valid_delivery["delivery_variance_days"] = (
    valid_delivery["order_estimated_delivery_date"] - valid_delivery["order_delivered_customer_date"]
).dt.total_seconds() / (24 * 3600)

valid_delivery["is_late"] = valid_delivery["delivery_variance_days"] < 0

late_orders_count = valid_delivery["is_late"].sum()
on_time_orders_count = denominator_delivery - late_orders_count

late_rate = (late_orders_count / denominator_delivery) * 100
on_time_rate = (on_time_orders_count / denominator_delivery) * 100

# For on-time orders, how many days early on average?
avg_days_early = valid_delivery[~valid_delivery["is_late"]]["delivery_variance_days"].mean()

# For late orders, how many days late on average?
avg_days_late = valid_delivery[valid_delivery["is_late"]]["delivery_variance_days"].abs().mean()

print(f"\n  Fulfillment Reliability (Denominator = {denominator_delivery:,} orders):")
print(f"    On-Time / Early Orders : {on_time_orders_count:,} ({on_time_rate:.2f}%)")
print(f"    Late Orders            : {late_orders_count:,} ({late_rate:.2f}%)")
print(f"    Average Days Early (when on time): {avg_days_early:.1f} days ahead of estimate")
print(f"    Average Days Late (when delayed) : {avg_days_late:.1f} days behind estimate")

# Save delivery KPI summary
delivery_kpis = pd.DataFrame({
    "Metric": [
        "Delivered Orders Analyzed (Denominator)",
        "Delivered Orders Excluded (Missing Date)",
        "Average Delivery Time (Days)",
        "Median Delivery Time (Days)",
        "On-Time Orders Count",
        "On-Time Delivery Rate (%)",
        "Late Orders Count",
        "Late Delivery Rate (%)",
        "Average Days Early (On-Time Orders)",
        "Average Days Late (Delayed Orders)"
    ],
    "Value": [
        denominator_delivery,
        missing_delivery_dates,
        round(avg_delivery_days, 1),
        round(median_delivery_days, 1),
        on_time_orders_count,
        round(on_time_rate, 2),
        late_orders_count,
        round(late_rate, 2),
        round(avg_days_early, 1),
        round(avg_days_late, 1)
    ]
})
delivery_kpis.to_csv(os.path.join(OUTPUT_DIR, "delivery_kpis.csv"), index=False)
print("  [SAVED] --> eda_outputs_part2/delivery_kpis.csv")

# ── B4. Monthly Average Delivery Time Trend ───────────────────────────────────
print_header("6. MONTHLY DELIVERY TIME TREND")

valid_delivery["purchase_year_month"] = valid_delivery["order_purchase_timestamp"].dt.strftime("%Y-%m")

monthly_delivery = valid_delivery.groupby("purchase_year_month").agg(
    delivered_orders=("order_id", "count"),
    avg_delivery_days=("actual_delivery_days", "mean"),
    on_time_rate=("is_late", lambda x: ((~x).sum() / len(x)) * 100)
).reset_index()

monthly_delivery = monthly_delivery.sort_values("purchase_year_month")
# Round for clean viewing
monthly_delivery["avg_delivery_days"] = monthly_delivery["avg_delivery_days"].round(1)
monthly_delivery["on_time_rate"] = monthly_delivery["on_time_rate"].round(2)

print(monthly_delivery.head(8).to_string(index=False))

monthly_delivery.to_csv(os.path.join(OUTPUT_DIR, "monthly_delivery_trend.csv"), index=False)
print("\n  [SAVED] --> eda_outputs_part2/monthly_delivery_trend.csv")

# ── B5. Delivery Performance by Customer State ────────────────────────────────
print_header("7. DELIVERY PERFORMANCE BY CUSTOMER STATE")

# Merge valid delivery records with customer location (customer_state)
delivery_with_cust = pd.merge(
    valid_delivery,
    customers_df[["customer_id", "customer_state"]],
    on="customer_id",
    how="left"
)

state_delivery = delivery_with_cust.groupby("customer_state").agg(
    total_orders=("order_id", "count"),
    avg_delivery_days=("actual_delivery_days", "mean"),
    median_delivery_days=("actual_delivery_days", "median"),
    on_time_rate=("is_late", lambda x: ((~x).sum() / len(x)) * 100)
).reset_index()

state_delivery["avg_delivery_days"] = state_delivery["avg_delivery_days"].round(1)
state_delivery["median_delivery_days"] = state_delivery["median_delivery_days"].round(1)
state_delivery["on_time_rate"] = state_delivery["on_time_rate"].round(2)

# Sort by fastest to slowest delivery
state_delivery = state_delivery.sort_values("avg_delivery_days")

print("  Fastest 5 States for Delivery:")
print(state_delivery.head(5).to_string(index=False))

print("\n  Slowest 5 States for Delivery (Remote / North / Northeast):")
print(state_delivery.tail(5).to_string(index=False))

state_delivery.to_csv(os.path.join(OUTPUT_DIR, "state_delivery_performance.csv"), index=False)
print("\n  [SAVED] --> eda_outputs_part2/state_delivery_performance.csv")


# =============================================================================
# PART C: GENERATE VISUALIZATIONS
# =============================================================================
print_header("8. GENERATING CHARTS")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 1: Customer Order Distribution (Bar Chart)
# ─────────────────────────────────────────────────────────────────────────────
plt.figure(figsize=(8, 5))
bars = plt.bar(
    orders_distribution["Order Bucket"],
    orders_distribution["Customer Count"],
    color="#4c72b0",
    edgecolor="#2b4c7e",
    alpha=0.85
)

plt.title("Distribution of Orders per Customer", fontsize=13, fontweight="bold", pad=15)
plt.xlabel("Order Frequency Bucket", fontsize=11, labelpad=10)
plt.ylabel("Number of Customers", fontsize=11, labelpad=10)
plt.grid(axis="y", linestyle="--", alpha=0.6)

# Add text labels on top of bars
for bar in bars:
    height = bar.get_height()
    pct = (height / total_unique_customers) * 100
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height + 1200,
        f"{height:,}\n({pct:.1f}%)",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#333333"
    )

plt.ylim(0, total_unique_customers * 1.12)
plt.tight_layout()
chart1_path = os.path.join(OUTPUT_DIR, "customer_order_distribution.png")
plt.savefig(chart1_path, dpi=300)
plt.close()
print(f"  [SAVED CHART 1] --> eda_outputs_part2/customer_order_distribution.png")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 2: Top 10 States by Unique Customer Count (Horizontal Bar Chart)
# ─────────────────────────────────────────────────────────────────────────────
top_10_states = state_customers.head(10).sort_values("Unique Customers", ascending=True)

plt.figure(figsize=(10, 6))
bars = plt.barh(
    top_10_states["State"],
    top_10_states["Unique Customers"],
    color="#3498db",
    edgecolor="#21618c",
    alpha=0.85
)

plt.title("Top 10 Brazilian States by Unique Customer Count", fontsize=13, fontweight="bold", pad=15)
plt.xlabel("Unique Customer Count", fontsize=11, labelpad=10)
plt.ylabel("Brazilian State Code", fontsize=11, labelpad=10)
plt.grid(axis="x", linestyle="--", alpha=0.6)

for bar in bars:
    width = bar.get_width()
    pct = (width / total_unique_customers) * 100
    plt.text(
        width + 500,
        bar.get_y() + bar.get_height() / 2,
        f"{width:,} ({pct:.1f}%)",
        va="center",
        ha="left",
        fontsize=9,
        color="#333333"
    )

plt.xlim(0, top_10_states["Unique Customers"].max() * 1.15)
plt.tight_layout()
chart2_path = os.path.join(OUTPUT_DIR, "top_customer_states.png")
plt.savefig(chart2_path, dpi=300)
plt.close()
print(f"  [SAVED CHART 2] --> eda_outputs_part2/top_customer_states.png")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 3: Monthly Average Delivery Time Trend (Line Chart)
# ─────────────────────────────────────────────────────────────────────────────
plt.figure(figsize=(12, 5))
plt.plot(
    monthly_delivery["purchase_year_month"],
    monthly_delivery["avg_delivery_days"],
    marker="s",
    color="#e74c3c",
    linewidth=2.2,
    markersize=6
)

plt.title("Monthly Average Delivery Time (Days from Purchase to Delivery)", fontsize=13, fontweight="bold", pad=15)
plt.xlabel("Purchase Month (Year-Month)", fontsize=11, labelpad=10)
plt.ylabel("Average Delivery Time (Days)", fontsize=11, labelpad=10)
plt.xticks(rotation=45, ha="right", fontsize=9)
plt.yticks(fontsize=10)
plt.grid(axis="y", linestyle="--", alpha=0.6)

# Highlight overall average reference line
plt.axhline(avg_delivery_days, color="#7f8c8d", linestyle=":", label=f"Overall Avg ({avg_delivery_days:.1f} days)")
plt.legend(loc="upper right", fontsize=10)

plt.tight_layout()
chart3_path = os.path.join(OUTPUT_DIR, "monthly_delivery_trend.png")
plt.savefig(chart3_path, dpi=300)
plt.close()
print(f"  [SAVED CHART 3] --> eda_outputs_part2/monthly_delivery_trend.png")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 4: Average Delivery Time by State (Horizontal Bar Chart)
# ─────────────────────────────────────────────────────────────────────────────
# Display top 5 fastest and top 5 slowest states for a focused comparison
fastest_5 = state_delivery.head(5).copy()
fastest_5["category"] = "Fastest States"
slowest_5 = state_delivery.tail(5).copy()
slowest_5["category"] = "Slowest States"
comparison_states = pd.concat([fastest_5, slowest_5]).sort_values("avg_delivery_days", ascending=True)

colors = ["#27ae60" if cat == "Fastest States" else "#e67e22" for cat in comparison_states["category"]]

plt.figure(figsize=(10, 6))
bars = plt.barh(
    comparison_states["customer_state"],
    comparison_states["avg_delivery_days"],
    color=colors,
    alpha=0.85
)

plt.title("Delivery Speed Disparities: 5 Fastest vs. 5 Slowest States", fontsize=13, fontweight="bold", pad=15)
plt.xlabel("Average Delivery Time (Days)", fontsize=11, labelpad=10)
plt.ylabel("Customer State Code", fontsize=11, labelpad=10)
plt.grid(axis="x", linestyle="--", alpha=0.6)

for bar in bars:
    width = bar.get_width()
    plt.text(
        width + 0.5,
        bar.get_y() + bar.get_height() / 2,
        f"{width:.1f} days",
        va="center",
        ha="left",
        fontsize=9,
        color="#333333"
    )

plt.xlim(0, comparison_states["avg_delivery_days"].max() * 1.15)
plt.tight_layout()
chart4_path = os.path.join(OUTPUT_DIR, "delivery_by_state.png")
plt.savefig(chart4_path, dpi=300)
plt.close()
print(f"  [SAVED CHART 4] --> eda_outputs_part2/delivery_by_state.png")

print_header("PART 2 EDA ANALYSIS COMPLETE")
