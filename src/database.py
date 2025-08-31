from tqdm import tqdm
import pandas as pd
import pymysql as mysql
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )

@st.cache_data
def load_tables(chunk_size=1000):
    """
    Load all tables from the database into pandas DataFrames with per-table progress bars.
    
    Args:
        chunk_size: number of rows to fetch per chunk for smooth progress bar updates.
    
    Returns:
        dfs: dictionary of table_name -> DataFrame
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    tables = [t[0] for t in cursor.fetchall()]
    
    dfs = {}

    print("\nLoading tables from the database:\n")

    for table in tables:
        # Get number of rows for progress calculation
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        total_rows = cursor.fetchone()[0]

        df_chunks = []
        pbar = tqdm(total=total_rows, desc=f"Loading {table}", ncols=100, unit="rows", colour="cyan")
        
        # Load table in chunks
        for chunk in pd.read_sql(f"SELECT * FROM {table};", conn, chunksize=chunk_size):
            df_chunks.append(chunk)
            pbar.update(len(chunk))
        
        pbar.close()
        df = pd.concat(df_chunks, ignore_index=True)

        # Automatically set index if first column is *_id
        first_col = df.columns[0]
        if "_id" in first_col:
            df.set_index(first_col, inplace=True)

        dfs[table] = df
        print(f"✅ Completed loading '{table}' ({total_rows} rows)\n")

    print("All tables loaded successfully into DataFrames.")
    return dfs
