"""
load_to_sql.py
--------------
Imports the remaining 7 cleaned Olist CSV files into SQL Server (.\\SQLEXPRESS)
under the database 'Olist_Ecommerce'.

Key Highlights:
- Monetary columns use exact DECIMAL(10, 2) instead of approximate FLOAT.
- seller_zip_code_prefix is stored as NVARCHAR(10) to preserve leading zeros.
- Automatically detects the best installed SQL Server ODBC driver.
- Pre-verifies that all 7 required CSV files exist before starting any import.
- Skips the 2 tables already imported ('customers', 'geolocation').
- Uses fast_executemany for high-speed bulk insertion.
- Verifies row counts across all tables at the end.
- Does NOT modify original or cleaned CSV files.
"""

import os
import sys
import urllib
import pyodbc
import pandas as pd
from sqlalchemy import create_engine, inspect, types
from sqlalchemy.dialects.mssql import DATETIME2

# ── 1. CONFIGURATION & DIRECTORIES ───────────────────────────────────────────
SERVER_NAME   = r".\SQLEXPRESS"
DATABASE_NAME = "Olist_Ecommerce"
SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT  = os.path.dirname(SCRIPT_DIR)
CLEANED_DIR   = os.path.join(PROJECT_ROOT, "cleaned_data")

# ── 2. SCHEMA & EXPLICIT SQL DATA TYPES FOR THE 7 REMAINING FILES ────────────
FILES_TO_IMPORT = {
    # 1. Order Items (monetary values as DECIMAL(10, 2))
    "olist_order_items_dataset.csv": {
        "table_name": "order_items",
        "date_cols": ["shipping_limit_date"],
        "dtypes": {
            "order_id": types.NVARCHAR(50),
            "order_item_id": types.INTEGER(),
            "product_id": types.NVARCHAR(50),
            "seller_id": types.NVARCHAR(50),
            "shipping_limit_date": DATETIME2(),
            "price": types.DECIMAL(precision=10, scale=2),
            "freight_value": types.DECIMAL(precision=10, scale=2),
        }
    },

    # 2. Order Payments (monetary value as DECIMAL(10, 2))
    "olist_order_payments_dataset.csv": {
        "table_name": "order_payments",
        "date_cols": [],
        "dtypes": {
            "order_id": types.NVARCHAR(50),
            "payment_sequential": types.INTEGER(),
            "payment_type": types.NVARCHAR(30),
            "payment_installments": types.INTEGER(),
            "payment_value": types.DECIMAL(precision=10, scale=2),
        }
    },

    # 3. Order Reviews (long text as NVARCHAR(MAX), dates as DATETIME2)
    "olist_order_reviews_dataset.csv": {
        "table_name": "order_reviews",
        "date_cols": ["review_creation_date", "review_answer_timestamp"],
        "dtypes": {
            "review_id": types.NVARCHAR(50),
            "order_id": types.NVARCHAR(50),
            "review_score": types.INTEGER(),
            "review_comment_title": types.NVARCHAR(255),
            "review_comment_message": types.NVARCHAR(None),  # None generates NVARCHAR(MAX)
            "review_creation_date": DATETIME2(),
            "review_answer_timestamp": DATETIME2(),
        }
    },

    # 4. Orders (all milestones as DATETIME2)
    "olist_orders_dataset.csv": {
        "table_name": "orders",
        "date_cols": [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date"
        ],
        "dtypes": {
            "order_id": types.NVARCHAR(50),
            "customer_id": types.NVARCHAR(50),
            "order_status": types.NVARCHAR(30),
            "order_purchase_timestamp": DATETIME2(),
            "order_approved_at": DATETIME2(),
            "order_delivered_carrier_date": DATETIME2(),
            "order_delivered_customer_date": DATETIME2(),
            "order_estimated_delivery_date": DATETIME2(),
        }
    },

    # 5. Products (dimensions & weight as FLOAT, category as NVARCHAR(100))
    "olist_products_dataset.csv": {
        "table_name": "products",
        "date_cols": [],
        "dtypes": {
            "product_id": types.NVARCHAR(50),
            "product_category_name": types.NVARCHAR(100),
            "product_name_lenght": types.FLOAT(),
            "product_description_lenght": types.FLOAT(),
            "product_photos_qty": types.FLOAT(),
            "product_weight_g": types.FLOAT(),
            "product_length_cm": types.FLOAT(),
            "product_height_cm": types.FLOAT(),
            "product_width_cm": types.FLOAT(),
        }
    },

    # 6. Sellers (seller_zip_code_prefix as NVARCHAR(10) to preserve leading zeros)
    "olist_sellers_dataset.csv": {
        "table_name": "sellers",
        "date_cols": [],
        "dtypes": {
            "seller_id": types.NVARCHAR(50),
            "seller_zip_code_prefix": types.NVARCHAR(10),
            "seller_city": types.NVARCHAR(100),
            "seller_state": types.NVARCHAR(10),
        }
    },

    # 7. Category Translation (clean text mapping)
    "product_category_name_translation.csv": {
        "table_name": "category_translation",
        "date_cols": [],
        "dtypes": {
            "product_category_name": types.NVARCHAR(100),
            "product_category_name_english": types.NVARCHAR(100),
        }
    }
}

# ── 3. SAFETY PRE-CHECK: VERIFY ALL 7 CSV FILES EXIST ─────────────────────────
print("=" * 70)
print("  STEP 1: PRE-CHECKING SOURCE CSV FILES IN 'cleaned_data'")
print("=" * 70)

missing_files = []
for filename in FILES_TO_IMPORT.keys():
    file_path = os.path.join(CLEANED_DIR, filename)
    if not os.path.isfile(file_path):
        missing_files.append(filename)

if missing_files:
    print("\n  [ERROR] Cannot proceed. The following required files are missing:")
    for mf in missing_files:
        print(f"    - {mf}")
    print(f"\n  Looked in folder: {CLEANED_DIR}")
    print("  Stopping execution before touching the database.")
    sys.exit(1)

print("  [OK] All 7 required CSV files are present in 'cleaned_data'.")


# ── 4. DYNAMIC DRIVER SELECTION & CONNECTION ─────────────────────────────────
print("\n" + "=" * 70)
print(f"  STEP 2: CONNECTING TO SQL SERVER ({SERVER_NAME}) -> {DATABASE_NAME}")
print("=" * 70)

installed_drivers = pyodbc.drivers()
preferred_drivers = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 13 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server"
]

chosen_driver = None
for d in preferred_drivers:
    if d in installed_drivers:
        chosen_driver = d
        break

if not chosen_driver:
    print(f"\n  [ERROR] No compatible SQL Server ODBC driver found.")
    print(f"  Installed drivers: {installed_drivers}")
    sys.exit(1)

print(f"  Using Detected ODBC Driver: {chosen_driver}")

extra_params = ";TrustServerCertificate=yes" if "Driver 18" in chosen_driver else ""
connection_string = (
    f"Driver={{{chosen_driver}}};"
    f"Server={SERVER_NAME};"
    f"Database={DATABASE_NAME};"
    f"Trusted_Connection=yes;"
    f"{extra_params}"
)

params = urllib.parse.quote_plus(connection_string)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}", fast_executemany=True)


# ── 5. EXECUTE IMPORT LOOP ───────────────────────────────────────────────────
print("\n" + "=" * 70)
print("  STEP 3: IMPORTING TABLES")
print("=" * 70)

inspector = inspect(engine)
existing_tables = inspector.get_table_names()

print(f"  Existing tables in database : {existing_tables}\n")

imported_tables = []
skipped_tables = []

for filename, config in FILES_TO_IMPORT.items():
    table_name = config["table_name"]

    # Safety Check: If the table already exists, skip it
    if table_name in existing_tables:
        print(f"  [SKIPPED] Table '{table_name}' already exists in database.")
        skipped_tables.append(table_name)
        continue

    file_path = os.path.join(CLEANED_DIR, filename)
    print(f"  Reading file : {filename} ...")
    
    # Preserve leading zeros for zip codes by reading as text
    dtype_overrides = {}
    if "seller_zip_code_prefix" in config["dtypes"]:
        dtype_overrides["seller_zip_code_prefix"] = str

    df = pd.read_csv(file_path, dtype=dtype_overrides)

    # Convert date columns to native datetime so SQL Server receives DATETIME2
    for d_col in config["date_cols"]:
        df[d_col] = pd.to_datetime(df[d_col])

    # Bulk insert into SQL Server
    print(f"  Inserting    : {len(df):,} rows into table '{table_name}' ...")
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="fail",   # Fails safely rather than overwriting
        index=False,        # Do not write Pandas index numbers
        dtype=config["dtypes"]
    )
    print(f"  [SUCCESS] Created table '{table_name}' ({len(df):,} rows inserted).\n")
    imported_tables.append(table_name)


# ── 6. VERIFY ALL DATABASE TABLES & ROW COUNTS ───────────────────────────────
print("=" * 70)
print("  STEP 4: DATABASE VERIFICATION — ALL TABLES & ROW COUNTS")
print("=" * 70)

verification_query = """
SELECT 
    t.name AS table_name,
    p.rows AS total_rows
FROM sys.tables t
JOIN sys.partitions p ON t.object_id = p.object_id
WHERE p.index_id IN (0, 1)
ORDER BY t.name;
"""

with engine.connect() as conn:
    verification_df = pd.read_sql(verification_query, conn)

print(verification_df.to_string(index=False))

print("\n" + "=" * 70)
print("  IMPORT PROCESS COMPLETE")
print("=" * 70)
print(f"  Tables Imported Now : {imported_tables}")
print(f"  Tables Skipped      : {skipped_tables}")
print("  Original & cleaned CSV files were NOT modified (read-only operations).")
