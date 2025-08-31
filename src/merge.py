# merge.py
import pandas as pd
import numpy as np
import streamlit as st

@st.cache_data
def merge_dataframes(dfs):
    """
    Merge the raw dfs into three main DataFrames:
    - flight_merged_df
    - booking_df
    - airline_merged_df
    """
    # ------------------------- Airline Merged DataFrame ------------------------- #
    airline_merged_df = dfs['airline'].copy()

    # ------------------------- Airplane Merged DataFrame ------------------------- #
    airplane_merged_df = dfs['airplane'].merge(
        dfs['airplane_type'],
        left_on='type_id',
        right_index=True,
        how='inner'
    )

    airplane_merged_df = airplane_merged_df.merge(
        dfs['airline'][['iata', 'airline_name', 'type']],
        left_on='airline_id',
        right_index=True,
        how='inner'
    )

    airplane_merged_df.drop(columns=['type_id', 'registration'], inplace=True)

    # ------------------------- Flight Merged DataFrame ------------------------- #
    flight_merged_df = dfs['flight'].merge(
        airplane_merged_df,
        left_on='airplane_id',
        right_index=True,
        how='inner'
    )

    # Clean airline_id columns
    if 'airline_id_y' in flight_merged_df.columns:
        flight_merged_df.drop(columns=['airline_id_y'], inplace=True)
    if 'airline_id_x' in flight_merged_df.columns:
        flight_merged_df.rename(columns={'airline_id_x': 'airline_id'}, inplace=True)

    # Merge airport info
    flight_merged_df = flight_merged_df.merge(
        dfs['airport'][['city', 'country']],
        left_on='origin_airport_id',
        right_index=True,
        how='left'
    ).rename(columns={"city": "origin_city", "country": "origin_country"})

    flight_merged_df = flight_merged_df.merge(
        dfs['airport'][['city', 'country']],
        left_on='dest_airport_id',
        right_index=True,
        how='left'
    ).rename(columns={"city": "destination_city", "country": "destination_country"})

    # Drop unnecessary ID columns
    flight_merged_df.drop(columns=['airline_id', 'airplane_id', 'origin_airport_id', 'dest_airport_id'], inplace=True)

    # Add booking counts
    # Add booking counts based on passengers
    booking_counts = dfs['booking'].groupby('flight_id')['num_passengers'].sum().reset_index(name='booking_count')
    flight_merged_df = flight_merged_df.merge(
        booking_counts,
        left_index=True,
        right_on='flight_id',
        how='left'
    )
    flight_merged_df.drop(columns='flight_id', inplace=True)

    # ------------------------- Booking Merged DataFrame ------------------------- #
    booking_df = dfs['booking'].merge(
        flight_merged_df,
        left_on='flight_id',
        right_index=True,
        how='inner'
    )

    # Drop redundant columns
    drop_cols = ['flight_id', 'iata', 'maker', 'max_altitude', 'actual_departure', 'origin_country']
    booking_df.drop(columns=[c for c in drop_cols if c in booking_df.columns], inplace=True)

    return flight_merged_df, booking_df, airline_merged_df
