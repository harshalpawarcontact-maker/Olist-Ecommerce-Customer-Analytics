"""
inspect_data.py
---------------
Inspects all Olist CSV files in the project folder.
Prints: filename, shape (rows x columns), column names, data types,
        missing values, and duplicate rows.

Does NOT modify any original CSV files.
"""

#  IMPORTS 
# 'os' is a built-in Python module that helps us work with files and folders.
# 'pandas' is a popular data analysis library. We import it with the short
# nickname 'pd' so we don't have to type 'pandas' every time.
import os
import pandas as pd


#  CONSTANTS 
# A constant is a variable whose value we never change after setting it.
# We use ALL_CAPS names for constants by convention (it's not enforced by
# Python, but it signals to other developers: "don't change this").

SEPARATOR = "=" * 70


#  STEP 1: FIND THE PROJECT ROOT FOLDER 
# __file__ is a special Python variable that holds the full path of THIS script.
# os.path.abspath() converts it to an absolute path (just to be safe).
# os.path.dirname() strips the filename and keeps only the folder path (Python_Scripts).
# A second os.path.dirname() moves one level up to the PROJECT_ROOT.
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)


#  STEP 2: BUILD A LIST OF ALL CSV FILES IN THAT FOLDER 
# os.listdir() returns a list of every file and folder name in PROJECT_ROOT.
# We loop through all of them and only keep the ones that end with ".csv".
# We use .endswith(".csv") to check if a filename ends with that extension.
# We skip library CSV files inside ".venv" because those are inside subfolders
# and os.listdir() (non-recursive) only sees files directly in PROJECT_ROOT.

csv_files = []  # Start with an empty list

for filename in os.listdir(PROJECT_ROOT):
    if filename.endswith(".csv"):       
        csv_files.append(filename)      

csv_files.sort()  # Sort alphabetically so output is in a predictable order


#  HELPER FUNCTION: print_separator 
# A function is a named, reusable block of code.
# Instead of copy-pasting the same print lines everywhere, we write them once
# inside a function and just call the function whenever we need it.

def print_separator():
    """Prints a full-width separator line."""
    print(SEPARATOR)


#  HELPER FUNCTION: inspect_file 
# This function receives the full path to one CSV file and prints all its info.
# By putting all inspection logic inside one function, the main code at the
# bottom becomes much easier to read.

def inspect_file(filepath):
    """
    Loads a single CSV file and prints:
    - Filename
    - Number of rows and columns
    - Column names
    - Data type of each column
    - Missing value count per column
    - Number of duplicate rows
    """

    # --- Load the CSV file into a DataFrame -----------------------------------
    # pd.read_csv() reads the file and creates a DataFrame (df).
    # A DataFrame is like a table in Python -- rows and columns, just like Excel.
    # We only READ the file here. We never write to it, so the original is safe.
    df = pd.read_csv(filepath)

    # Get just the filename (not the full folder path) for display.
    # Example: "C:/project/olist_orders.csv" -> "olist_orders.csv"
    filename = os.path.basename(filepath)

    # --- Print file header ----------------------------------------------------
    print()
    print_separator()
    print("  FILE :", filename)
    print_separator()

    # --- Shape: rows and columns ----------------------------------------------
    # df.shape is a tuple (pair) of two numbers: (number_of_rows, number_of_columns).
    # We unpack it into two separate variables: rows and cols.
    rows = df.shape[0]   # First value in the tuple = number of rows
    cols = df.shape[1]   # Second value in the tuple = number of columns

    # f-string formatting:
    #   {rows:,}  -- adds a comma as a thousands separator (e.g. 99441 -> 99,441)
    print(f"\n  Shape          : {rows:,} rows  x  {cols} columns")

    # --- Column names ---------------------------------------------------------
    # df.columns gives us the list of column names.
    # enumerate() lets us loop with a counter (1, 2, 3 ...) alongside each item.
    # start=1 makes the counter begin at 1 instead of Python's default 0.
    print("\n  Column Names   :")
    counter = 1
    for col_name in df.columns:
        # {counter:>2} right-aligns the number in a space of 2 characters.
        # This keeps the list looking neat even if the number goes from 1 to 10+.
        print(f"    {counter:>2}. {col_name}")
        counter = counter + 1

    # --- Data types -----------------------------------------------------------
    # df.dtypes is a pandas Series where each column name maps to its data type.
    # .items() gives us pairs of (column_name, data_type) we can loop over.
    # Common types:
    #   object  = text (string)
    #   int64   = whole number (integer)
    #   float64 = decimal number (floating-point)
    print("\n  Data Types     :")
    for col_name, data_type in df.dtypes.items():
        # {col_name:<45} left-aligns the name in a 45-character-wide space.
        # This makes all the data type labels line up neatly in a column.
        print(f"    {col_name:<45} {data_type}")

    # --- Missing values -------------------------------------------------------
    # df.isnull() returns a DataFrame of True/False for every cell.
    #   True  = the cell is empty (missing/NaN)
    #   False = the cell has a value
    # .sum() counts the True values (empty cells) for each column.
    missing_counts = df.isnull().sum()

    # .sum() on the result adds up the missing counts across all columns.
    total_missing = missing_counts.sum()

    print(f"\n  Missing Values : {total_missing:,} total")

    if total_missing > 0:
        print("    Columns with missing data:")
        # Loop through each column and its missing count.
        for col_name, count in missing_counts.items():
            if count > 0:   # Only print columns that actually have missing data
                # Calculate what percentage of the column is missing.
                # count / rows gives a fraction (e.g. 0.088).
                # Multiplying by 100 gives the percentage (e.g. 8.8).
                percentage = count / rows * 100
                # {count:>6,}  -- right-aligns the count in 6 chars, with commas
                # {percentage:.1f}  -- shows one decimal place
                print(f"    [X]  {col_name:<43} {count:>6,}  ({percentage:.1f}%)")
    else:
        print("    [OK] No missing values found.")

    # --- Duplicate rows -------------------------------------------------------
    # df.duplicated() returns a True/False list -- True if that row is a
    # duplicate of an earlier row. .sum() counts how many Trues there are.
    duplicate_count = df.duplicated().sum()

    print(f"\n  Duplicate Rows : {duplicate_count:,}")

    if duplicate_count > 0:
        print("    [!] Duplicate rows detected -- consider cleaning before analysis.")
    else:
        print("    [OK] No duplicate rows found.")


#  MAIN PROGRAM 
# This is the code that actually runs when you execute the script.
# Everything above was just setting up tools (constants and functions).
# Now we USE those tools here.

# Print the header banner
print_separator()
print("  OLIST E-COMMERCE DATASET INSPECTION")
print_separator()
print(f"  Folder  : {PROJECT_ROOT}")
print(f"  CSV files found: {len(csv_files)}")
print_separator()

# Loop through every CSV file and inspect it.
# os.path.join() combines the folder path and the filename safely.
# Example: os.path.join("C:/project", "orders.csv") -> "C:/project/orders.csv"
for filename in csv_files:
    full_path = os.path.join(PROJECT_ROOT, filename)
    inspect_file(full_path)

# Print the footer
print()
print_separator()
print("  INSPECTION COMPLETE  --  No original files were modified.")
print_separator()
