"""Interactive dashboard: change the station settings and see the results live.

Run from the repository root:
    streamlit run app/streamlit_app.py
"""
import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from citibike_twin import Policy, hourly_rates, load_trips, simulate, summarize

st.set_page_config(page_title="Citi Bike digital twin", layout="wide")
st.title("Citi Bike station digital twin")
st.caption("Built from Citi Bike's public trip data. Change the settings on the left and compare policies.")

DATA = "data/JC-202306-citibike-tripdata.csv"


@st.cache_data
def get_trips(path):
    return load_trips(path)


if not os.path.exists(DATA):
    st.error(f"Data file not found: {DATA}. See data/README.md for how to download it.")
    st.stop()

trips = get_trips(DATA)
stations = trips["start_station_name"].value_counts().index.tolist()

with st.sidebar:
    station = st.selectbox("Station", stations, index=0)
    capacity = st.slider("Number of docks", 10, 80, 40)
    days = st.slider("Simulated weekdays", 50, 500, 150, step=50)
    st.subheader("Redesigned policy")
    use_trucks = st.checkbox("Sensor triggered trucks", True)
    low, high = st.slider("Truck alert thresholds (fill level)", 0.0, 1.0, (0.15, 0.85))
    delay = st.slider("Truck delay (minutes)", 5, 60, 20)
    nudge = st.slider("Share of riders reacting to incentives", 0.0, 0.6, 0.3)

rates = hourly_rates(trips, station)
policy = Policy(threshold=(low, high) if use_trucks else None, delay=delay, nudge=nudge)

with st.spinner("Simulating..."):
    base_days, base_path = simulate(rates, Policy(), capacity=capacity, n_days=days)
    new_days, new_path = simulate(rates, policy, capacity=capacity, n_days=days)

base, new = summarize(base_days), summarize(new_days)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Riders affected/day, no intervention", f"{base['Riders affected/day']:.1f}")
c2.metric("Riders affected/day, your policy", f"{new['Riders affected/day']:.1f}",
          f"{new['Riders affected/day'] - base['Riders affected/day']:.1f}", delta_color="inverse")
c3.metric("Truck visits/day", f"{new['Truck visits/day']:.1f}")
c4.metric("Riders nudged/day", f"{new['Riders nudged/day']:.1f}")

st.subheader("One simulated weekday")
st.line_chart(pd.DataFrame({"No intervention": base_path, "Your policy": new_path},
                           index=[m / 60 for m in range(len(base_path))]))
st.subheader("Demand learned from the data (average per weekday hour)")
st.bar_chart(rates.rename(columns={"dep": "Bikes taken", "arr": "Bikes returned"}))
st.subheader("All KPIs")
st.dataframe(pd.DataFrame({"No intervention": base, "Your policy": new}).round(1))
