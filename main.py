from src.database import load_tables
from src.wrangling import wrangle_data
from src.merge import merge_dataframes
from src.utils import database_insight
from warnings import filterwarnings
from app import dashboard
import streamlit as st


filterwarnings("ignore")  # Suppress warnings for cleaner output

def main():

    # 1. Load raw tables from DB
    dfs = load_tables()

    # 2. Wrangle & clean the raw tables
    dfs = wrangle_data(dfs)

    # 3. Merge & generate final DataFrames
    flight_merged_df, booking_df, airline_merged_df = merge_dataframes(dfs)

    # 4. Display summary of final DataFrames using utility
    # database_insight(flight_merged_df, name="Flight Merged DataFrame")
    # database_insight(booking_df, name="Booking DataFrame")
    # database_insight(airline_merged_df, name="Airline Merged DataFrame")

    dashboard(booking_df, rating = airline_merged_df)


if __name__ == "__main__":
    main()

