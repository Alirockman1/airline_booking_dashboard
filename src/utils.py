import numpy as np
import pandas as pd

def report_missing(df, name="DataFrame"):
    """Print missing value report for a DataFrame."""
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        print(f"\n{name} missing values:\n{missing}")
    else:
        print(f"\n{name} has no missing values.")

def replace_empty_with_nan(df):
    """
    Replace empty strings with NaN for all columns in a DataFrame.
    """
    return df.replace("", np.nan)

def remove_duplicates(df, exclude_tables=None, table_name=None):
    """
    Remove duplicate rows from a DataFrame. Optionally exclude certain tables.
    """
    if exclude_tables is None:
        exclude_tables = []
    
    if table_name in exclude_tables:
        return df
    
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        print(f"Duplicate rows in table '{table_name}': {duplicates}")
        df = df.drop_duplicates()
    return df

def database_insight(df, name: str):
    """
    Display a visually appealing, comprehensive summary of a DataFrame,
    including numeric, timedelta, and object columns.

    Args:
        df (pd.DataFrame): The DataFrame to inspect.
        name (str): Name of the database/table.
    """
    line = "═" * 80
    print(f"\n╔{line}╗")
    print(f"║ {'DATABASE INSIGHT: ' + name.upper():^78} ║")
    print(f"╚{line}╝\n")

    # Shape
    print(f"📊 Shape: {df.shape[0]} rows x {df.shape[1]} columns\n")

    # Data types
    print("📝 Column Data Types:")
    for col, dtype in df.dtypes.items():
        print(f"  - {col}: {dtype}")

    # Missing values
    missing = df.isnull().sum()
    if missing.any():
        print("\n⚠️ Missing Values:")
        for col, count in missing[missing > 0].items():
            print(f"  - {col}: {count}")
    else:
        print("\n✅ Missing Values: None")

    # Numeric descriptive stats
    numeric_df = df.select_dtypes(include=['int64', 'float64'])
    print("\n📈 Descriptive Statistics (numeric columns):")
    if not numeric_df.empty:
        desc = numeric_df.describe().T
        for col, row in desc.iterrows():
            print(f"  - {col}:")
            print(f"      count={int(row['count'])}, mean={row['mean']:.2f}, std={row['std']:.2f}, min={row['min']}, 25%={row['25%']}, 50%={row['50%']}, 75%={row['75%']}, max={row['max']}")
    else:
        print("  No numeric columns to describe.")

    # Timedelta descriptive stats
    timedelta_df = df.select_dtypes(include='timedelta64[ns]')
    if not timedelta_df.empty:
        print("\n⏱ Descriptive Statistics (timedelta columns):")
        for col in timedelta_df.columns:
            print(f"  - {col}: min={timedelta_df[col].min()}, max={timedelta_df[col].max()}, mean={timedelta_df[col].mean()}")

    # Head
    print("\n👀 First 5 rows:")
    print(df.head())

    print("\n" + "═" * 80 + "\n")
