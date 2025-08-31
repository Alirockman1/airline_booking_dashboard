import pandas as pd
import numpy as np
from .utils import replace_empty_with_nan, remove_duplicates
import streamlit as st

@st.cache_data
def wrangle_data(dfs):
    """
    Perform full data wrangling: common cleaning + table-specific transformations.
    """

    ## ------------------------- COMMON CLEANING ------------------------- ##
    for table_name, df in dfs.items():
        df = replace_empty_with_nan(df)
        df = remove_duplicates(df, exclude_tables=['passenger_feedback'], table_name=table_name)
        dfs[table_name] = df

    ## ------------------------- TABLE-SPECIFIC WRANGLING ------------------------- ##
    # ------------------------- Booking ------------------------- #
    booking = dfs['booking']

    # Fill missing passenger_age with mean
    if 'passenger_age' in booking.columns:
        booking['passenger_age'].fillna(booking['passenger_age'].mean(), inplace=True)

    # Drop unnecessary columns
    for col in ['passenger_email', 'passenger_nationality']:
        if col in booking.columns:
            booking.drop(columns=col, inplace=True)

    # Extract booking year and month
    if 'booking_date' in booking.columns:
        booking['booking_date'] = pd.to_datetime(booking['booking_date'], errors='coerce')
        booking['booking_year'] = booking['booking_date'].dt.year
        booking['booking_month'] = booking['booking_date'].dt.month_name()

    dfs['booking'] = booking

    # ------------------------- Airplane Type ------------------------- #
    airplane_type = dfs['airplane_type']

    if 'max_range' in airplane_type.columns:
        airplane_type['haul'] = airplane_type['max_range'].apply(
            lambda x: 'Short Haul' if x <= 1200 else 'Medium Haul' if x < 8000 else 'Long Haul'
        )
        airplane_type.drop(columns='max_range', inplace=True)

    if 'description' in airplane_type.columns:
        airplane_type.drop(columns='description', inplace=True)

    dfs['airplane_type'] = airplane_type

    # ------------------------- Airline ------------------------- #
    airline = dfs['airline']
    feedback = dfs.get('passenger_feedback', pd.DataFrame())

    if not feedback.empty:
        avg_ratings = feedback.groupby('preferred_airline')['rating'].mean().reset_index()
        for iata_code in avg_ratings['preferred_airline']:
            if iata_code in airline['iata'].values:
                airline.loc[airline['iata'] == iata_code, 'rating'] = \
                    avg_ratings.loc[avg_ratings['preferred_airline'] == iata_code, 'rating'].values[0]

    if 'base_airport' in airline.columns:
        airline.drop(columns='base_airport', inplace=True)

    dfs['airline'] = airline

    # ------------------------- Flight ------------------------- #
    flight = dfs['flight']

    if 'expected_departure' in flight.columns:
        flight['expected_departure'] = pd.to_datetime(flight['expected_departure'], errors='coerce')
        flight['actual_departure'] = pd.to_datetime(flight['actual_departure'], errors='coerce')
        flight['arrival'] = pd.to_datetime(flight['arrival'], errors='coerce')

        flight['delay'] = flight['actual_departure'] - flight['expected_departure']
        flight['trip_duration'] = flight['arrival'] - flight['actual_departure']
        flight['departure_month'] = flight['actual_departure'].dt.month_name()
        flight['departure_year'] = flight['actual_departure'].dt.year

        flight.drop(columns=['expected_departure','arrival'], inplace=True)

    dfs['flight'] = flight

    # ------------------------- Booking - Age Groups ------------------------- #
    try:
        bins = [13, 19, 30, 65, 105]
        labels = ['Teen', 'Young Adult', 'Adult', 'Senior']
        if 'passenger_age' in dfs['booking'].columns:
            dfs['booking']['passenger_age'] = pd.cut(dfs['booking']['passenger_age'], bins=bins, labels=labels)
    except Exception as e:
        print(f"Error categorizing age groups in 'booking' table: {e}'")

    # ------------------------- Flight - Load Factor ------------------------- #
    try:
        if 'flight' in dfs:
            dfs['flight']['load_factor'] = np.random.uniform(0.6, 0.95, size=len(dfs['flight']))
    except Exception as e:
        print(f"Error computing load factor in 'flight' table: {e}")

    # ------------------------- Booking - Passengers & Agent ------------------------- #
    booking = dfs['booking']
    flight = dfs['flight']
    airplane = dfs['airplane']
    airplane_type = dfs['airplane_type']

    # --- Add columns if not exist ---
    if 'num_passengers' not in booking.columns:
        booking['num_passengers'] = 1
    if 'is_agent' not in booking.columns:
        booking['is_agent'] = False

    # --- Prepare airplane + airplane_type ---
    # airplane_id is index in airplane
    airplane = airplane.copy()
    airplane['airplane_id'] = airplane.index  # make it a column
    # airplane_type index is type_id
    airplane_type = airplane_type.copy()
    airplane_type['type_id'] = airplane_type.index

    # --- Merge flight -> airplane -> airplane_type to get seats_capacity ---
    flight_merged = flight.copy()
    flight_merged = flight_merged.merge(
        airplane['type_id'],
        left_on='airplane_id',
        right_index=True,
        how='left'
    )
    flight_merged = flight_merged.merge(
        airplane_type['capacity'],
        left_on='type_id',
        right_index=True,
        how='left'
    )

    # --- Merge booking with flight info ---
    booking = booking.merge(
        flight_merged[['dest_airport_id','capacity','actual_departure']],
        left_on='flight_id',
        right_index=True,
        how='left'
    )

    # --- Assign num_passengers based on domestic/international & COVID restriction ---
    for idx, row in booking.iterrows():
        if pd.notna(row['actual_departure']) and row['actual_departure'].year in [2020, 2021]:
            booking.at[idx,'num_passengers'] = 1  # COVID: only single traveler
        elif row['dest_airport_id'] > 5:  # Domestic
            booking.at[idx,'num_passengers'] = int(np.floor(1 + np.random.rand() * 4))
        else:  # International
            booking.at[idx,'num_passengers'] = int(np.floor(1 + np.random.rand() * 6))

    # --- Assign is_agent based on domestic/international ---
    for idx, row in booking.iterrows():
        if row['dest_airport_id'] > 5:  # Domestic
            booking.at[idx,'is_agent'] = np.random.rand() < 0.4
        else:  # International
            booking.at[idx,'is_agent'] = np.random.rand() < 0.7

    # --- Ensure bookings do not exceed seat capacity ---
    booking['cumulative_passengers'] = booking.groupby('flight_id')['num_passengers'].cumsum()
    booking.loc[booking['cumulative_passengers'] > booking['capacity'], 'num_passengers'] = 0

    # --- Drop helper columns ---
    booking.drop(columns=['dest_airport_id','actual_departure','capacity','cumulative_passengers'], inplace=True)

    dfs['booking'] = booking

    dfs['booking']['is_agent'] = dfs['booking']['is_agent'].astype(bool)

    return dfs