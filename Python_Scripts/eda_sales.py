"""
eda_sales.py
------------
Step 3: Exploratory Data Analysis (EDA) - Part 1: Sales Analysis.

Calculates:
1. High-level Sales KPIs (Delivered Orders, Product Revenue, Freight, AOV).
2. Monthly Sales Revenue Trend.
3. Top 10 Products by Revenue (including total units sold).
4. Top 10 Product Categories by Revenue (in English).

Saves all tables and charts to the 'eda_outputs' directory.
Does NOT modify any original or cleaned CSV files.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt


# ── STEP 1: SET UP PATHS & DIRECTORIES ─────────────────────────────────────────
# Locate the current folder where this script lives (Python_Scripts)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Project root folder (parent of Python_Scripts)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Folder where our cleaned CSV files are stored in the project root
CLEANED_DIR = os.path.join(PROJECT_ROOT, "cleaned_data")

# Dedicated output folder for EDA tables and charts in the project root
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "eda_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Visual divider for clean console output
SEPARATOR = "=" * 70

def print_header(title):
    """Prints a clear, formatted header banner."""
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(f"{SEPARATOR}")


# ── STEP 2: LOAD REQUIRED CLEANED FILES ────────────────────────────────────────
print_header("1. LOADING CLEANED DATASETS FOR SALES ANALYSIS")

# 1. Orders table: gives us order_id, order_status, and purchase timestamp
orders_path = os.path.join(CLEANED_DIR, "olist_orders_dataset.csv")
orders_df = pd.read_csv(orders_path)
orders_df["order_purchase_timestamp"] = pd.to_datetime(orders_df["order_purchase_timestamp"])
print(f"  Loaded orders: {len(orders_df):,} rows")

# 2. Order items table: gives us order_id, product_id, price, and freight_value
items_path = os.path.join(CLEANED_DIR, "olist_order_items_dataset.csv")
items_df = pd.read_csv(items_path)
print(f"  Loaded order items: {len(items_df):,} rows")

# 3. Products table: gives us product_id and product_category_name
products_path = os.path.join(CLEANED_DIR, "olist_products_dataset.csv")
products_df = pd.read_csv(products_path)
print(f"  Loaded products: {len(products_df):,} rows")

# 4. Translations table: translates Portuguese category names into English
trans_path = os.path.join(CLEANED_DIR, "product_category_name_translation.csv")
trans_df = pd.read_csv(trans_path)
print(f"  Loaded translations: {len(trans_df):,} rows")


# ── STEP 3: FILTER VALID DELIVERED ORDERS & MERGE (AVOIDING DOUBLE COUNTING) ───
print_header("2. PREPARING SALES DATA & PREVENTING DOUBLE COUNTING")

# We only consider completed sales (order_status == 'delivered').
# Cancelled or unavailable orders should not be reported as achieved revenue.
delivered_orders = orders_df[orders_df["order_status"] == "delivered"].copy()
total_delivered_orders = delivered_orders["order_id"].nunique()
print(f"  Delivered orders (unique): {total_delivered_orders:,} out of {len(orders_df):,} total orders")

# SAFE MERGE:
# Each row in delivered_orders is 1 unique order_id.
# Each row in items_df is 1 item purchased.
# By joining items_df with ONLY 'order_id' and 'order_purchase_timestamp' from delivered_orders,
# we attach the purchase date to each sold item WITHOUT duplicating any rows or revenue!
sales_items_df = pd.merge(
    items_df,
    delivered_orders[["order_id", "order_purchase_timestamp"]],
    on="order_id",
    how="inner"  # 'inner' keeps only items that belong to delivered orders
)

print(f"  Total items sold across delivered orders: {len(sales_items_df):,} records")


# ── STEP 4: CALCULATE OVERALL SALES KPIS ───────────────────────────────────────
print_header("3. OVERALL SALES KPIS")

# Product Revenue: what customers paid strictly for the items
total_product_revenue = sales_items_df["price"].sum()

# Freight Charges: shipping fees paid by customers
total_freight_value = sales_items_df["freight_value"].sum()

# Total Customer Spend: Product Revenue + Freight
total_gross_outlay = total_product_revenue + total_freight_value

# Average Order Value (AOV): Product revenue per unique delivered order
aov_product_revenue = total_product_revenue / total_delivered_orders

print(f"  Total Delivered Orders             : {total_delivered_orders:,}")
print(f"  Total Product Sales Revenue        : R$ {total_product_revenue:,.2f}")
print(f"  Total Freight Charges              : R$ {total_freight_value:,.2f}")
print(f"  Total Customer Outlay (Items+Ship) : R$ {total_gross_outlay:,.2f}")
print(f"  Avg Product Revenue / Delivered Order (AOV): R$ {aov_product_revenue:,.2f}")

# Save KPIs to a CSV file
kpis_summary = pd.DataFrame({
    "Metric": [
        "Total Delivered Orders",
        "Total Product Sales Revenue (R$)",
        "Total Freight Charges (R$)",
        "Total Customer Outlay (R$)",
        "Average Product Revenue per Delivered Order (AOV) (R$)"
    ],
    "Value": [
        total_delivered_orders,
        round(total_product_revenue, 2),
        round(total_freight_value, 2),
        round(total_gross_outlay, 2),
        round(aov_product_revenue, 2)
    ]
})
kpis_summary.to_csv(os.path.join(OUTPUT_DIR, "sales_kpis.csv"), index=False)
print(f"  [SAVED] --> eda_outputs/sales_kpis.csv")


# ── STEP 5: MONTHLY SALES REVENUE ANALYSIS ─────────────────────────────────────
print_header("4. MONTHLY SALES REVENUE ANALYSIS")

# Create a 'year_month' column formatted as 'YYYY-MM' (e.g., '2017-05')
sales_items_df["year_month"] = sales_items_df["order_purchase_timestamp"].dt.strftime("%Y-%m")

# Group by year_month and calculate monthly metrics:
# - Sum of price (Monthly Product Revenue)
# - Sum of freight_value (Monthly Freight)
# - Count of unique orders (Monthly Orders)
monthly_sales = sales_items_df.groupby("year_month").agg(
    delivered_orders=("order_id", "nunique"),
    product_revenue=("price", "sum"),
    freight_revenue=("freight_value", "sum")
).reset_index()

# Sort chronologically
monthly_sales = monthly_sales.sort_values("year_month")

# Save to CSV
monthly_sales.to_csv(os.path.join(OUTPUT_DIR, "monthly_sales.csv"), index=False)
print("  First 5 months:")
print(monthly_sales.head().to_string(index=False))
print(f"\n  [SAVED] --> eda_outputs/monthly_sales.csv")


# ── STEP 6: TOP 10 PRODUCTS BY REVENUE & UNITS SOLD ───────────────────────────
print_header("5. TOP 10 PRODUCTS BY SALES REVENUE")

# Group by product_id:
# - sum 'price' to get total revenue generated by that product
# - count 'order_item_id' to get total units sold
top_products = sales_items_df.groupby("product_id").agg(
    units_sold=("order_item_id", "count"),
    total_revenue=("price", "sum")
).reset_index()

# Sort descending by total_revenue and pick top 10
top_10_products = top_products.sort_values(by="total_revenue", ascending=False).head(10).copy()

# Add a readable short product label for printing / display
top_10_products["short_product_id"] = top_10_products["product_id"].str[:8] + "..."

print(top_10_products[["short_product_id", "units_sold", "total_revenue"]].to_string(index=False))

# Save to CSV (with full product_id)
top_10_products.to_csv(os.path.join(OUTPUT_DIR, "top_10_products.csv"), index=False)
print(f"\n  [SAVED] --> eda_outputs/top_10_products.csv")


# ── STEP 7: TOP 10 PRODUCT CATEGORIES BY REVENUE ──────────────────────────────
print_header("6. TOP 10 PRODUCT CATEGORIES BY REVENUE")

# Merge sales items with products catalog (to get category name)
items_with_products = pd.merge(
    sales_items_df,
    products_df[["product_id", "product_category_name"]],
    on="product_id",
    how="left"
)

# Merge with category translation (to get English category name)
items_full = pd.merge(
    items_with_products,
    trans_df,
    on="product_category_name",
    how="left"
)

# If category translation is missing or Unknown, fill with 'Unknown / Uncategorized'
items_full["product_category_name_english"] = items_full["product_category_name_english"].fillna(
    items_full["product_category_name"].fillna("Unknown")
)

# Group by English category name:
# - sum 'price' for revenue
# - count 'order_item_id' for items sold
category_sales = items_full.groupby("product_category_name_english").agg(
    total_revenue=("price", "sum"),
    items_sold=("order_item_id", "count")
).reset_index()

top_10_categories = category_sales.sort_values(by="total_revenue", ascending=False).head(10).copy()

print(top_10_categories.to_string(index=False))

# Save to CSV
top_10_categories.to_csv(os.path.join(OUTPUT_DIR, "top_10_categories.csv"), index=False)
print(f"\n  [SAVED] --> eda_outputs/top_10_categories.csv")


# ── STEP 8: CHARTS WITH MATPLOTLIB ─────────────────────────────────────────────
print_header("7. GENERATING & SAVING CHARTS")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 1: Monthly Product Sales Trend (Line Chart)
# ─────────────────────────────────────────────────────────────────────────────
plt.figure(figsize=(12, 6))

# Plot revenue in thousands for easier chart reading (R$ in Thousands)
plt.plot(
    monthly_sales["year_month"],
    monthly_sales["product_revenue"] / 1000,
    marker="o",
    color="#1f77b4",
    linewidth=2.5,
    markersize=6
)

plt.title("Monthly Product Sales Revenue (Delivered Orders)", fontsize=14, fontweight="bold", pad=15)
plt.xlabel("Purchase Month (Year-Month)", fontsize=11, labelpad=10)
plt.ylabel("Product Revenue (R$ in Thousands)", fontsize=11, labelpad=10)
plt.xticks(rotation=45, ha="right", fontsize=9)
plt.yticks(fontsize=10)
plt.grid(axis="y", linestyle="--", alpha=0.6)
plt.tight_layout()

chart1_path = os.path.join(OUTPUT_DIR, "monthly_sales_trend.png")
plt.savefig(chart1_path, dpi=300)
plt.close()
print(f"  [SAVED CHART 1] --> eda_outputs/monthly_sales_trend.png")

# ─────────────────────────────────────────────────────────────────────────────
# CHART 2: Top 10 Product Categories by Revenue (Horizontal Bar Chart)
# ─────────────────────────────────────────────────────────────────────────────
# Sort ascending so the top category appears at the top of the horizontal bar chart
top_10_categories_sorted = top_10_categories.sort_values(by="total_revenue", ascending=True)

plt.figure(figsize=(11, 6))

bars = plt.barh(
    top_10_categories_sorted["product_category_name_english"],
    top_10_categories_sorted["total_revenue"] / 1000,
    color="#2ca02c",
    edgecolor="#1e7e1e",
    alpha=0.85
)

plt.title("Top 10 Product Categories by Revenue", fontsize=14, fontweight="bold", pad=15)
plt.xlabel("Total Product Revenue (R$ in Thousands)", fontsize=11, labelpad=10)
plt.ylabel("Product Category (English)", fontsize=11, labelpad=10)
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)
plt.grid(axis="x", linestyle="--", alpha=0.6)

# Add text labels on the bars showing exact values
for bar in bars:
    width = bar.get_width()
    plt.text(
        width + 10,  # slight offset to the right of the bar
        bar.get_y() + bar.get_height() / 2,
        f"R$ {width:,.0f}k",
        va="center",
        ha="left",
        fontsize=9,
        color="#333333"
    )

plt.tight_layout()

chart2_path = os.path.join(OUTPUT_DIR, "top_10_categories.png")
plt.savefig(chart2_path, dpi=300)
plt.close()
print(f"  [SAVED CHART 2] --> eda_outputs/top_10_categories.png")

print_header("EDA SALES ANALYSIS COMPLETE")
