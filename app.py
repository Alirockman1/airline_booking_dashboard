import streamlit as st
import plotly.express as px
import calendar
import pandas as pd
import statsmodels.api as sm
import io
import os
import plotly.io as pio
import json
import pathlib


def dashboard(database, title = "FlightHub Pakistan", save_dir = "E:/MyFolder/MyGitHub/Aviation_Analysis/save_folder", rating = []):
    # -----------------------------
    # Dashboard Layout
    # -----------------------------

    # Apply custom CSS
    with open("config/theme.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # Apply Plotly theme
    with open("config/plotly_theme.json") as f:
        plotly_theme = json.load(f)
    pio.templates["custom"] = plotly_theme
    pio.templates.default = "custom"

    st.set_page_config(page_title=title, layout="wide")

    # Title
    st.markdown("<h1 style='padding-top: 0rem; text-align: center;'>✈️ AirTravel Pakistan Insights</h1>", unsafe_allow_html=True)

    month_order = list(calendar.month_name)[1:]  # ['January', 'February', ..., 'December']

    # -----------------------------
    # Sidebar Filters
    # -----------------------------
    st.sidebar.header("🔍 Filters")

    # Always start from the full dataset
    df = database.copy()

    # ---------------- Year filter ----------------
    year_options = sorted(df["departure_year"].unique())
    year_filter = st.sidebar.multiselect("Year", year_options)

    if year_filter:
        df = df[df["departure_year"].isin(year_filter)]

    # Define month order explicitly
    month_order = list(calendar.month_name)[1:]  # ['January', ..., 'December']

    # ---------------- Month filter ----------------
    if year_filter:  # only show month if year is selected
        available_months = df["departure_month"].unique()
        # keep order according to month_order
        month_options = [m for m in month_order if m in available_months]

        month_filter = st.sidebar.multiselect("Month", month_options, default=month_options)
        if month_filter:
            df = df[df["departure_month"].isin(month_filter)]
    else:
        month_filter = []

    # ---------------- Destination filter ----------------
    if month_filter:  # only show destination if month is selected
        destination_options = sorted(df["destination_city"].unique())
        destination_filter = st.sidebar.multiselect("Destination", destination_options)
        if destination_filter:
            df = df[df["destination_city"].isin(destination_filter)]
    else:
        destination_filter = []

    # ---------------- Age filter ----------------
    if destination_filter:  # only show age if destination is selected
        age_options = df["passenger_age"].cat.categories
        age_filter = st.sidebar.multiselect("Age Group", age_options)
        if age_filter:
            df = df[df["passenger_age"].isin(age_filter)]
    else:
        age_filter = []

    # ---------------- Airline filter ----------------
    if age_filter:  # only show airline if age is selected
        airline_options = sorted(df["airline_name"].unique())
        airline_filter = st.sidebar.multiselect("Airline", airline_options)
        if airline_filter:
            df = df[df["airline_name"].isin(airline_filter)]
    else:
        airline_filter = []

    booking_filtered = df

    # -----------------------------
    # KPI Box
    # -----------------------------
    col1, col2, col3, col4 = st.columns(4)  # adjust width ratios

    total_travelers = booking_filtered['booking_count'].sum()
    total_flights = len(booking_filtered)
    dest_count = booking_filtered.groupby('destination_city')['booking_count'].sum().reset_index()
    preferred_destination = dest_count.loc[dest_count['booking_count'].idxmax(), 'destination_city']
    
    # Get current month (latest month in your data)
    # Make sure booking_date is datetime
    booking_filtered['booking_date'] = pd.to_datetime(booking_filtered['booking_date'])

    # Extract normalized month (first day of each month)
    booking_filtered['month'] = booking_filtered['booking_date'].dt.to_period('M').dt.to_timestamp()

    # Find current and previous months
    current_month = booking_filtered['month'].max()
    previous_month = current_month - pd.DateOffset(months=1)

    # Aggregate bookings by month
    monthly_bookings = booking_filtered.groupby('month')['booking_count'].sum()

    # Lookup values
    current_month_bookings = monthly_bookings.get(current_month, 0)
    previous_month_bookings = monthly_bookings.get(previous_month, 0)

    # Growth %
    if previous_month_bookings > 0:
        growth_pct = ((current_month_bookings - previous_month_bookings) / previous_month_bookings) * 100
    else:
        growth_pct = None

    # Display metric
    col1.metric("👥 Total Travelers", f"{total_travelers:,}")
    col2.metric("🛫 Total Flights", f"{total_flights:,}")
    col3.metric("🏝️ Preferred Destination", preferred_destination)
    col4.metric("📈 Booking Growth", f"{current_month_bookings:,}", f"{growth_pct:+.1f}% vs last month")

    # ----------------------------
    # Graphics
    # ----------------------------
    col1, col2 = st.columns(2)  # adjust width ratios
    # Pie chart for age demographic
    with col1:
        # Subheader with minimal margin
        st.subheader("Passenger Age")

        # Pie chart
        fig = px.pie(
            booking_filtered,
            values='booking_count',
            names='passenger_age',
            hole=0.3
        )
        fig.update_traces(textposition='inside', textinfo='label+percent')
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True, height=200)

        # ---------------- Metric box ----------------
        # Find the age group with maximum passengers
        max_row = booking_filtered.loc[booking_filtered['booking_count'].idxmax()]
        max_age_group = max_row['passenger_age']
        
        # Sum of passengers for that age group only
        max_count = booking_filtered.loc[booking_filtered['passenger_age'] == max_age_group, 'booking_count'].sum()

        with st.expander('View Matrics'):
            st.write(f"Most Frequent Age Group: {max_age_group}")
            st.write(f"Number of Passenger: {max_count}")

    with col2:
        # Bar Graph for number of bookings per destination
        st.subheader("Bookings per Destination")
        fig_dest = px.bar(dest_count, x='destination_city', y='booking_count', color='destination_city', text='booking_count')
        fig_dest.update_layout(showlegend=False, xaxis_title='Destination', yaxis_title='Bookings')
        st.plotly_chart(fig_dest, use_container_width=True, height=300)
        
    # Line graph for monthly bookings (seperate line in the same graph for the year filter applied) -> there should be coloured bins in the chart showing Quaterly division of the year
    st.subheader("Monthly Bookings")

    # Convert to categorical with order
    booking_filtered['departure_month'] = pd.Categorical(
        booking_filtered['departure_month'],
        categories=month_order,
        ordered=True
    )

    # Now your line chart will respect month order
    fig = px.line(
        booking_filtered.groupby('departure_month')['booking_count'].sum().reset_index(),
        x='departure_month',
        y='booking_count',
        markers=True
    )
    # Add quarterly shaded regions
    quarters = [(0, 2), (3, 5), (6, 8), (9, 11)]  # 0-indexed positions
    colors = ["grey", "green"]  # alternate colors

    for i, (start, end) in enumerate(quarters):
        fig.add_vrect(
            x0=month_order[start],
            x1=month_order[end],
            fillcolor=colors[i % 2],
            opacity=0.1,
            line_width=0
        )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Number of Passengers"
    )

    st.plotly_chart(fig, use_container_width=True, height=300)

    # Metrics under the chart
    with st.expander("View Monthly Booking Metrics"):
        # Group by month for metrics
        month_group = booking_filtered.groupby('departure_month')['booking_count'].sum()
        max_month = month_group.idxmax()
        min_month = month_group.idxmin()
        avg_month = month_group.mean()
        
        st.write(f"Month with Maximum Bookings: {max_month} ({month_group[max_month]} bookings)")
        st.write(f"Month with Minimum Bookings: {min_month} ({month_group[min_month]} bookings)")
        st.write(f"Average Bookings per Month: {avg_month:.1f}")
        
        # Quarterly totals
        quarters = {
            "Q1": ['January','February','March'],
            "Q2": ['April','May','June'],
            "Q3": ['July','August','September'],
            "Q4": ['October','November','December']
        }
        st.write("Total Bookings per Quarter:")
        for q, months in quarters.items():
            q_total = month_group.loc[month_group.index.intersection(months)].sum()
            st.write(f"{q}: {q_total}")
        
    # bar garph for preffered airline based on number of bookings (col 1)
    st.subheader("Bookings per Airline")
    airline_count = booking_filtered.groupby('airline_name')['booking_count'].sum().reset_index()
    fig_airline = px.bar(airline_count, x='airline_name', y='booking_count', color='airline_name', text='booking_count')
    fig_airline.update_layout(showlegend=False, xaxis_title='Airline', yaxis_title='Bookings')
    st.plotly_chart(fig_airline, use_container_width=True, height=300)

    with st.expander("View Airline ratings"):
        st.table(rating[['airline_name', 'rating']])

    col1, col2 = st.columns(2)

    # ------------------ Left Column: Ticket Type Preference ------------------
    with col1:
        st.markdown("#### Ticket Type Preference by Age Group")

        ticket_pref = booking_filtered.groupby(
            ['passenger_age', 'ticket_type']
        )['booking_count'].sum().reset_index()

        fig_ticket = px.bar(
            ticket_pref,
            x='passenger_age',
            y='booking_count',
            color='ticket_type',
            barmode='stack',
            text='booking_count'
        )
        fig_ticket.update_layout(
            xaxis_title="Age Group",
            yaxis_title="Number of Tickets",
            legend_title="Ticket Type"
        )
        st.plotly_chart(fig_ticket, use_container_width=True, height=400)

    # ------------------ Right Column: Add-on Preferences ------------------
    with col2:
        st.markdown("#### Add-on Preferences by Age Group")

        # Convert Y/N → 1/0
        addon_cols = ['business_lounge', 'inflight_entertainment', 'inflight_food']
        booking_filtered[addon_cols] = booking_filtered[addon_cols].applymap(lambda x: 1 if str(x).lower() == 'y' else 0)

        # Handle extra weight: define typical allowance
        allowance = {'Economy': 23, 'Business': 30, 'First': 40}
        booking_filtered['extra_weight'] = booking_filtered.apply(
            lambda row: max(row['weight_kg'] - allowance.get(row['seat_class'], 23), 0), axis=1
        )
        booking_filtered['extra_weight_flag'] = booking_filtered['extra_weight'].apply(lambda x: 1 if x > 0 else 0)

        # Add this as another "add-on"
        addon_cols_extended = addon_cols + ['extra_weight_flag']

        addon_pref = booking_filtered.groupby('passenger_age')[addon_cols_extended].mean().reset_index()
        addon_pref = addon_pref.melt(id_vars='passenger_age', var_name='addon', value_name='preference_rate')

        fig_addon = px.bar(
            addon_pref,
            x='passenger_age',
            y='preference_rate',
            color='addon',
            barmode='group',
            text_auto=True
        )
        fig_addon.update_layout(
            xaxis_title="Age Group",
            yaxis_title="Preference Rate (0–1)",
            legend_title="Add-on"
        )
        st.plotly_chart(fig_addon, use_container_width=True, height=400)

    with st.expander("View Customer Preferance Metrics"):
        most_popular_ticket = booking_filtered['ticket_type'].mode()[0]
        avg_price_per_type = booking_filtered.groupby('ticket_type')['price'].mean().round(2)
        ticket_stats = pd.DataFrame({
            "Statistic": [
                "Most Popular Ticket Type",
                "Highest Average Price Ticket",
                "Lowest Average Price Ticket"
            ],
            "Value": [
                most_popular_ticket,
                avg_price_per_type.idxmax() + f" (${avg_price_per_type.max()})",
                avg_price_per_type.idxmin() + f" (${avg_price_per_type.min()})"
            ]
        })

        st.markdown("Key Ticket Insights")
        st.table(ticket_stats)

        # Stats table for add-ons
        addon_mean = booking_filtered[addon_cols_extended].mean().sort_values(ascending=False).round(2)
        most_popular_addon = addon_mean.index[0]
        avg_extra_weight = booking_filtered['extra_weight'].mean().round(1)

        addon_stats = pd.DataFrame({
            "Statistic": [
                "Most Popular Add-on",
                "Average Extra Weight Purchased (kg)",
                "Add-on with Lowest Uptake"
            ],
            "Value": [
                most_popular_addon,
                str(avg_extra_weight) + " kg",
                addon_mean.index[-1]
            ]
        })

        st.markdown("Key Add-on Insights")
        st.table(addon_stats)

    col1, col2 = st.columns([9,3])

    with col2:
        # Let user select format
        format_option = st.radio("Select file format to download:", ["CSV", "TXT"], horizontal=True)

        # Ensure folder exists
        os.makedirs(save_dir, exist_ok=True)

        # Set filename and MIME type
        if format_option == "CSV":
            file_name = "booking_data.csv"
            mime = "text/csv"
            full_path = os.path.join(save_dir, file_name)

            # Save to disk
            database.to_csv(full_path, index=False)

            # Save to buffer for download
            buffer = io.BytesIO()
            database.to_csv(buffer, index=False)

        else:  # TXT
            file_name = "booking_data.txt"
            mime = "text/plain"
            full_path = os.path.join(save_dir, file_name)

            # Save to disk
            database.to_csv(full_path, index=False, sep="\t")

            # Save to buffer for download
            buffer = io.BytesIO()
            database.to_csv(buffer, index=False, sep="\t")

        # Download button
        st.download_button(
            label=f"Download Booking Data as {format_option}",
            data=buffer.getvalue(),
            file_name=file_name,
            mime=mime
        )
