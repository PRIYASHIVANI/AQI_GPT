import streamlit as st
import pandas as pd
from utils.data import load_dataset, get_aqi_category

st.set_page_config(page_title="AQI Monitor", page_icon="🌍", layout="wide")

st.title("🌍 AQI Monitor")
st.caption("Real-time Air Quality Index Monitoring & Forecasting")

df = load_dataset()
latest = df.sort_values("Date").groupby("City").last().reset_index()

st.divider()

latest_sorted = latest.sort_values("AQI", ascending=False).reset_index(drop=True)
CITIES_PER_ROW = 5
total_cities = len(latest_sorted)
total_pages = (total_cities + CITIES_PER_ROW - 1) // CITIES_PER_ROW

page = st.select_slider(
    "Scroll to view more cities",
    options=list(range(total_pages)),
    format_func=lambda x: f"{x * CITIES_PER_ROW + 1}–{min((x + 1) * CITIES_PER_ROW, total_cities)} of {total_cities}",
    value=0,
)

start = page * CITIES_PER_ROW
end = min(start + CITIES_PER_ROW, total_cities)
page_cities = latest_sorted.iloc[start:end]

cols = st.columns(CITIES_PER_ROW)
for i, (_, row) in enumerate(page_cities.iterrows()):
    cat = row["AQI_Category"]
    icon = {"Good": "🟢", "Moderate": "🟡", "Poor": "🟠", "Very Poor": "🔴", "Severe": "☠️"}.get(cat, "⚪")
    with cols[i]:
        st.metric(row["City"], f"{row['AQI']} AQI", delta=f"{icon} {cat}", delta_color="off")
        st.caption(f"PM2.5: {row['PM2.5']} · PM10: {row['PM10']}")

st.divider()

r1, r2 = st.columns(2)
with r1:
    col1, col2 = st.columns(2)
    with col1:
        st.success("📈 **AQI Forecasting**\n\nML-powered multi-day predictions")
        st.warning("🚨 **Health Alerts**\n\nDetailed precautions & recommendations")
        st.info("⚖️ **City Comparison**\n\nSide-by-side city analysis")
    with col2:
        st.info("📊 **Data Explorer**\n\n2 years of multi-city data")
        st.error("🔬 **Pollutant Analysis**\n\nSub-index breakdown & trends")
        st.success("🧮 **AQI Calculator**\n\nCompute AQI from pollutant inputs")

with r2:
    col3, col4 = st.columns(2)
    with col3:
        st.error("📍 **Location Monitor**\n\nMap view & city deep-dive")
    with col4:
        st.warning("📄 **Reports & Downloads**\n\nExport data & generate reports")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Records", f"{len(df):,}")
    with c2:
        st.metric("Cities", df["City"].nunique())
    with c3:
        st.metric("Days Covered", f"{(df['Date'].max() - df['Date'].min()).days}")
    with c4:
        avg_aqi = round(df["AQI"].mean())
        st.metric("Avg AQI", avg_aqi)
