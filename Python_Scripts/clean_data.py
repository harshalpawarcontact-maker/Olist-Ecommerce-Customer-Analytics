"""
clean_data.py
-------------
Reads the original Olist CSV files, applies targeted cleaning steps,
and saves the cleaned results to a folder called 'cleaned_data'.

Cleaning decisions are explained inline for every file.
Original CSV files are NEVER modified or overwritten.
"""

# ── IMPORTS ───────────────────────────────────────────────────────────────────
# os     : helps us work with folders and file paths
# pandas : the main library for loading, cleaning, and saving data tables
import os
import pandas as pd


# ── CONSTANTS ─────────────────────────────────────────────────────────────────
# SEPARATOR is a visual divider line used to make the output easier to read.
SEPARATOR = "=" * 70

# SCRIPT_DIR is the folder where THIS file (clean_data.py) lives (Python_Scripts).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# PROJECT_ROOT is the parent folder containing raw CSV files and project subfolders.
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# CLEANED_DIR is where we will save all the cleaned CSV files.
# It is a subfolder called 'cleaned_data' in the project root.
CLEANED_DIR = os.path.join(PROJECT_ROOT, "cleaned_data")

# os.makedirs() creates the 'cleaned_data' folder if it doesn't exist yet.
# exist_ok=True means: "don't crash if the folder already exists."
os.makedirs(CLEANED_DIR, exist_ok=True)


# ── HELPER FUNCTION: print_separator ─────────────────────────────────────────
def print_separator():
    """Prints a full-width separator line."""
    print(SEPARATOR)


# ── HELPER FUNCTION: show_summary ────────────────────────────────────────────
def show_summary(filename, df_before, df_after, changes):
    """
    Prints a before-and-after summary for one file.

    Parameters:
        filename  : the name of the CSV file (just the name, not full path)
        df_before : the DataFrame BEFORE cleaning
        df_after  : the DataFrame AFTER cleaning
        changes   : a list of strings describing what was done
    """
    print_separator()
    print(f"  FILE : {filename}")
    print_separator()

    # df.shape[0] = number of rows, df.shape[1] = number of columns
    # {value:>7,} means: right-align the number in 7 characters, with comma separators
    print(f"  Before : {df_before.shape[0]:>7,} rows  x  {df_before.shape[1]} columns")
    print(f"  After  : {df_after.shape[0]:>7,} rows  x  {df_after.shape[1]} columns")

    # Print each cleaning action that was taken
    print("  What was done:")
    for action in changes:
        print(f"    - {action}")
    print()


# ── HELPER FUNCTION: save_cleaned ────────────────────────────────────────────
def save_cleaned(df, filename):
    """
    Saves a cleaned DataFrame as a CSV file in the cleaned_data folder.

    Parameters:
        df       : the cleaned DataFrame to save
        filename : the output filename (same name as the original)
    """
    # Build the full output path: cleaned_data/filename
    output_path = os.path.join(CLEANED_DIR, filename)

    # df.to_csv() writes the DataFrame to a CSV file.
    # index=False means: don't write the row numbers (0, 1, 2 ...) as an extra column.
    df.to_csv(output_path, index=False)

    print(f"  [SAVED] --> cleaned_data/{filename}")
    print()


# ── PRINT HEADER ──────────────────────────────────────────────────────────────
print_separator()
print("  OLIST DATA CLEANING")
print_separator()
print(f"  Source folder : {PROJECT_ROOT}")
print(f"  Output folder : {CLEANED_DIR}")
print()


# =============================================================================
# FILE 1: olist_customers_dataset.csv
# ─────────────────────────────────────────────────────────────────────────────
# Inspection result: 99,441 rows, 5 columns. No missing values. No duplicates.
# Decision: No cleaning needed. Save an identical copy to cleaned_data.
# =============================================================================

filename = "olist_customers_dataset.csv"

# Load the original file into a DataFrame
df = pd.read_csv(os.path.join(PROJECT_ROOT, filename))

# df.copy() creates a separate copy of the original data.
# We store it as df_before so we can compare it in the summary later.
# Without .copy(), df_before would just be another name pointing to the same
# table -- any changes to df would also change df_before.
df_before = df.copy()

changes = ["No issues found. Saved as a clean copy without modification."]

show_summary(filename, df_before, df, changes)
save_cleaned(df, filename)


# =============================================================================
# FILE 2: olist_geolocation_dataset.csv
# ─────────────────────────────────────────────────────────────────────────────
# Inspection result: 1,000,163 rows. No missing values. 261,831 DUPLICATES.
# Decision: Drop all exact duplicate rows.
# Reason: A duplicate here means the exact same (zip code + lat + lng + city +
#         state) appears more than once. There is no new information in a
#         repeated row. Keeping duplicates would skew any geographic analysis
#         (e.g., a zip code appearing 10 times would look 10x more common).
# =============================================================================

filename = "olist_geolocation_dataset.csv"
df = pd.read_csv(os.path.join(PROJECT_ROOT, filename))
df_before = df.copy()

# Count duplicates BEFORE removing them (for the summary message)
duplicates_found = df.duplicated().sum()

# df.drop_duplicates() removes rows that are identical to a previous row.
# It keeps the FIRST occurrence and removes all later copies.
# We reassign the result back to df (the cleaned version).
df = df.drop_duplicates()

changes = [
    f"Dropped {duplicates_found:,} exact duplicate rows.",
    "Kept the first occurrence of each unique location record.",
    "Reason: Repeated (zip + lat + lng + city + state) rows add no new information.",
]

show_summary(filename, df_before, df, changes)
save_cleaned(df, filename)


# =============================================================================
# FILE 3: olist_order_items_dataset.csv
# ─────────────────────────────────────────────────────────────────────────────
# Inspection result: 112,650 rows. No missing values. No duplicates.
# 'shipping_limit_date' column type was 'object' (text), not datetime.
# Decision: Convert the date column to proper datetime format.
# Reason: When dates are stored as text, Python treats "2017-10-01" as just
#         letters. You cannot subtract dates, sort them correctly, or do time
#         calculations. Converting to datetime unlocks all date operations.
# =============================================================================

filename = "olist_order_items_dataset.csv"
df = pd.read_csv(os.path.join(PROJECT_ROOT, filename))
df_before = df.copy()

# pd.to_datetime() converts a column of text dates into real datetime values.
# We overwrite the column in-place with the converted values.
df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"])

changes = [
    "Converted 'shipping_limit_date' from text (object) to datetime64 format.",
    "Reason: Enables date arithmetic, sorting, and time-based analysis.",
]

show_summary(filename, df_before, df, changes)
save_cleaned(df, filename)


# =============================================================================
# FILE 4: olist_order_payments_dataset.csv
# ─────────────────────────────────────────────────────────────────────────────
# Inspection result: 103,886 rows. No missing values. No duplicates.
# Decision: No cleaning needed. Save as-is.
# =============================================================================

filename = "olist_order_payments_dataset.csv"
df = pd.read_csv(os.path.join(PROJECT_ROOT, filename))
df_before = df.copy()

changes = ["No issues found. Saved as a clean copy without modification."]

show_summary(filename, df_before, df, changes)
save_cleaned(df, filename)


# =============================================================================
# FILE 5: olist_order_reviews_dataset.csv
# ─────────────────────────────────────────────────────────────────────────────
# Inspection result: 99,224 rows.
# Missing: review_comment_title (88.3%), review_comment_message (58.7%).
# Two date columns stored as text.
#
# Decision A: LEAVE the missing comment columns as-is (NaN).
# Reason: Review comments are optional. A customer who gives 5 stars but
#         writes nothing is a valid data point. Deleting 88% of rows just
#         because no comment was written would destroy most of the review data.
#
# Decision B: Convert both date columns from text to datetime.
# =============================================================================

filename = "olist_order_reviews_dataset.csv"
df = pd.read_csv(os.path.join(PROJECT_ROOT, filename))
df_before = df.copy()

# Convert both date columns
df["review_creation_date"]    = pd.to_datetime(df["review_creation_date"])
df["review_answer_timestamp"] = pd.to_datetime(df["review_answer_timestamp"])

changes = [
    "Converted 'review_creation_date' from text to datetime64.",
    "Converted 'review_answer_timestamp' from text to datetime64.",
    "Left 'review_comment_title' missing values as NaN (not changed).",
    "Left 'review_comment_message' missing values as NaN (not changed).",
    "Reason: Review comments are optional. NaN = customer chose not to write one.",
    "Deleting those rows would remove 88% of reviews for no valid reason.",
]

show_summary(filename, df_before, df, changes)
save_cleaned(df, filename)


# =============================================================================
# FILE 6: olist_orders_dataset.csv
# ─────────────────────────────────────────────────────────────────────────────
# Inspection result: 99,441 rows.
# Missing: order_approved_at (160), order_delivered_carrier_date (1,783),
#          order_delivered_customer_date (2,965).
# Five columns stored as text dates.
#
# Decision A: Convert all five date columns from text to datetime.
# Decision B: LEAVE missing delivery dates as NaT (Not a Time).
# Reason: Cancelled orders and orders still in transit have no delivery date
#         yet. That missing value IS the information. Filling it with a fake
#         date or deleting the row would corrupt the data.
# =============================================================================

filename = "olist_orders_dataset.csv"
df = pd.read_csv(os.path.join(PROJECT_ROOT, filename))
df_before = df.copy()

# We store the column names that need conversion in a list,
# then loop through that list. This is cleaner than writing
# pd.to_datetime() five separate times.
date_columns = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

for col in date_columns:
    # pd.to_datetime() handles NaN automatically -- it converts them to NaT,
    # which is pandas' version of "missing date" (Not a Time).
    df[col] = pd.to_datetime(df[col])

changes = [
    "Converted 5 date columns from text (object) to datetime64 format:",
    "  order_purchase_timestamp, order_approved_at,",
    "  order_delivered_carrier_date, order_delivered_customer_date,",
    "  order_estimated_delivery_date.",
    "Left missing delivery dates as NaT (pandas equivalent of missing date).",
    "Reason: Missing delivery dates belong to cancelled/undelivered orders.",
    "These rows are important business records and must not be deleted.",
]

show_summary(filename, df_before, df, changes)
save_cleaned(df, filename)


# =============================================================================
# FILE 7: olist_products_dataset.csv
# ─────────────────────────────────────────────────────────────────────────────
# Inspection result: 32,951 rows.
# Missing values in multiple columns:
#   - product_category_name      : 610 rows  (1.9%)
#   - product_name_lenght        : 610 rows  (1.9%)  [typo in original data]
#   - product_description_lenght : 610 rows  (1.9%)  [typo in original data]
#   - product_photos_qty         : 610 rows  (1.9%)
#   - product_weight_g           :   2 rows  (0.0%)
#   - product_length_cm          :   2 rows  (0.0%)
#   - product_height_cm          :   2 rows  (0.0%)
#   - product_width_cm           :   2 rows  (0.0%)
#
# These are TWO separate groups of missing rows (confirmed by the counts):
#   Group A: 610 rows missing category + metadata (name length, desc length, photos)
#   Group B:   2 rows missing physical dimensions (weight, length, height, width)
#
# Decision A: Fill 'product_category_name' with the string "Unknown".
# Reason: "Unknown" is honest. We know the product exists (it was sold),
#         we just don't know its category. This is better than deleting 610 rows.
#
# Decision B: Fill the 3 numeric metadata columns with their column MEDIAN.
# Reason: We cannot know the actual values. The median is the middle value in
#         a sorted list -- it's a fair, neutral estimate that isn't skewed by
#         extreme outliers (unlike the average/mean).
#
# Decision C: KEEP the 2 rows missing physical dimensions. Leave NaN as-is.
# Reason: Physical dimensions (weight, size) are logistics data, not customer
#         or sales data. This project focuses on sales trends, customer
#         behaviour, and geographic analysis -- none of which uses weight or
#         size. These 2 products were actually ordered 18 times, so dropping
#         them would silently remove real sales records from our analysis.
# =============================================================================

filename = "olist_products_dataset.csv"
df = pd.read_csv(os.path.join(PROJECT_ROOT, filename))
df_before = df.copy()

changes = []   # We'll add to this list as we make each change

# ── Action A: Fill missing category name with "Unknown" ───────────────────────
missing_cat_count = df["product_category_name"].isnull().sum()

# .fillna(value) replaces every NaN in that column with the given value.
# We reassign the result back to the same column.
df["product_category_name"] = df["product_category_name"].fillna("Unknown")

changes.append(
    f"Filled {missing_cat_count} missing 'product_category_name' with 'Unknown'."
)

# ── Action B: Fill numeric metadata with column median ────────────────────────
# These 3 columns have the same 610 missing rows as the category column.
# Note: 'lenght' is a typo in the original Olist dataset. We keep it as-is
# to match the original column names.
metadata_columns = [
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
]

for col in metadata_columns:
    missing_count = df[col].isnull().sum()

    if missing_count > 0:
        # .median() calculates the middle value of all non-missing values in the column.
        # We store it in a variable so we can print it in the summary message.
        median_value = df[col].median()

        # Fill missing values with the median
        df[col] = df[col].fillna(median_value)

        changes.append(
            f"Filled {missing_count} missing '{col}' values with column median ({median_value:.1f})."
        )

# ── Action C: Keep physical dimension columns as-is (NaN stays NaN) ──────────
# We do NOT call dropna() here.
# The 2 rows with missing weight/size are valid product records.
# Their product_id values appear in 18 real order rows, so they represent
# real sales. Since this project does not use physical dimensions for any
# analysis, leaving these values as NaN causes no harm at all.
# A NaN in an unused column is harmless. A deleted row is a permanent loss.
changes.append(
    "Kept 2 rows with missing physical dimensions (weight/size) as-is."
)
changes.append(
    "Reason: Dimensions unused in sales/customer analytics."
    " Dropping them would erase 18 real order records from analysis."
)

show_summary(filename, df_before, df, changes)
save_cleaned(df, filename)


# =============================================================================
# FILE 8: olist_sellers_dataset.csv
# ─────────────────────────────────────────────────────────────────────────────
# Inspection result: 3,095 rows. No missing values. No duplicates.
# Decision: No cleaning needed. Save as-is.
# =============================================================================

filename = "olist_sellers_dataset.csv"
df = pd.read_csv(os.path.join(PROJECT_ROOT, filename))
df_before = df.copy()

changes = ["No issues found. Saved as a clean copy without modification."]

show_summary(filename, df_before, df, changes)
save_cleaned(df, filename)


# =============================================================================
# FILE 9: product_category_name_translation.csv
# ─────────────────────────────────────────────────────────────────────────────
# Inspection result: 71 rows. No missing values. No duplicates.
# Decision: No cleaning needed. Save as-is.
# =============================================================================

filename = "product_category_name_translation.csv"
df = pd.read_csv(os.path.join(PROJECT_ROOT, filename))
df_before = df.copy()

changes = ["No issues found. Saved as a clean copy without modification."]

show_summary(filename, df_before, df, changes)
save_cleaned(df, filename)


# ── FOOTER ────────────────────────────────────────────────────────────────────
print_separator()
print("  DATA CLEANING COMPLETE")
print(f"  Cleaned files saved to: {CLEANED_DIR}")
print("  Original CSV files were NOT modified.")
print_separator()
