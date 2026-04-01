import streamlit as st
import pandas as pd
from utils.data import load_dataset, get_aqi_category, compute_sub_index

st.set_page_config(layout="wide")
st.title("📄 Reports & Downloads")
st.caption("Generate city reports and download data")

df = load_dataset()

# --- Filters ---
rc1, rc2 = st.columns(2)
with rc1:
    report_city = st.selectbox("Select City", df["City"].unique().tolist())
with rc2:
    report_range = st.date_input("Date Range",
                                  value=(df["Date"].min(), df["Date"].max()),
                                  min_value=df["Date"].min(), max_value=df["Date"].max())

if len(report_range) == 2:
    start, end = report_range
    city_df = df[(df["City"] == report_city) &
                 (df["Date"] >= pd.to_datetime(start)) &
                 (df["Date"] <= pd.to_datetime(end))].sort_values("Date")
else:
    city_df = df[df["City"] == report_city].sort_values("Date")

st.divider()

# --- Summary Report ---
st.subheader(f"📋 Summary Report — {report_city}")

total_days = len(city_df)
avg_aqi = round(city_df["AQI"].mean())
max_aqi = int(city_df["AQI"].max())
min_aqi = int(city_df["AQI"].min())
max_date = city_df.loc[city_df["AQI"].idxmax(), "Date"].strftime("%b %d, %Y")
min_date = city_df.loc[city_df["AQI"].idxmin(), "Date"].strftime("%b %d, %Y")
dominant = city_df["Dominant_Pollutant"].value_counts().idxmax()

r1, r2, r3, r4 = st.columns(4)
with r1:
    st.metric("Total Days", total_days)
with r2:
    st.metric("Average AQI", avg_aqi, delta=get_aqi_category(avg_aqi), delta_color="off")
with r3:
    st.metric("Worst AQI", max_aqi, delta=max_date, delta_color="off")
with r4:
    st.metric("Best AQI", min_aqi, delta=min_date, delta_color="off")

st.divider()

# --- Category Breakdown ---
st.subheader("🧮 AQI Category Breakdown")

cat_order = ["Good", "Moderate", "Poor", "Very Poor", "Severe"]
cat_counts = city_df["AQI_Category"].value_counts().reindex(cat_order, fill_value=0)
cat_pct = (cat_counts / total_days * 100).round(1)

cat_cols = st.columns(5)
cat_colors = {"Good": "success", "Moderate": "info", "Poor": "warning", "Very Poor": "error", "Severe": "error"}
cat_icons = {"Good": "🟢", "Moderate": "🟡", "Poor": "🟠", "Very Poor": "🔴", "Severe": "☠️"}

for i, cat in enumerate(cat_order):
    with cat_cols[i]:
        days = cat_counts[cat]
        pct = cat_pct[cat]
        st.metric(f"{cat_icons[cat]} {cat}", f"{days} days", delta=f"{pct}%", delta_color="off")

st.divider()

# --- Pollutant Averages ---
st.subheader("🔬 Average Pollutant Levels")

pollutants = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"]
poll_avg = city_df[pollutants].mean().round(2)

pc = st.columns(6)
units = {"PM2.5": "µg/m³", "PM10": "µg/m³", "NO2": "µg/m³", "SO2": "µg/m³", "CO": "mg/m³", "O3": "µg/m³"}
for i, p in enumerate(pollutants):
    with pc[i]:
        st.metric(p, f"{poll_avg[p]} {units[p]}")

st.divider()

# --- Weather Summary ---
st.subheader("🌦️ Weather Summary")

wc1, wc2, wc3 = st.columns(3)
with wc1:
    avg_temp = round(city_df["Temperature"].mean(), 1)
    st.metric("Avg Temperature", f"{avg_temp}°C",
              delta=f"{city_df['Temperature'].min():.0f}° – {city_df['Temperature'].max():.0f}°", delta_color="off")
with wc2:
    avg_hum = round(city_df["Humidity"].mean(), 1)
    st.metric("Avg Humidity", f"{avg_hum}%",
              delta=f"{city_df['Humidity'].min():.0f}% – {city_df['Humidity'].max():.0f}%", delta_color="off")
with wc3:
    avg_wind = round(city_df["Wind_Speed"].mean(), 1)
    st.metric("Avg Wind Speed", f"{avg_wind} km/h",
              delta=f"{city_df['Wind_Speed'].min():.0f} – {city_df['Wind_Speed'].max():.0f} km/h", delta_color="off")

st.divider()

# --- Monthly Breakdown Table ---
st.subheader("📅 Monthly Breakdown")

monthly = city_df.copy()
monthly["Month"] = monthly["Date"].dt.strftime("%Y-%m")
monthly_summary = monthly.groupby("Month").agg(
    Avg_AQI=("AQI", "mean"),
    Max_AQI=("AQI", "max"),
    Min_AQI=("AQI", "min"),
    Avg_PM25=("PM2.5", "mean"),
    Avg_PM10=("PM10", "mean"),
    Avg_Temp=("Temperature", "mean"),
    Days=("AQI", "count"),
).round(1).reset_index()

monthly_summary.columns = ["Month", "Avg AQI", "Max AQI", "Min AQI", "Avg PM2.5", "Avg PM10", "Avg Temp (°C)", "Days"]
st.dataframe(monthly_summary, use_container_width=True, hide_index=True)

st.divider()

# --- Download Section ---
st.subheader("⬇️ Download Data")

dc1, dc2, dc3 = st.columns(3)

with dc1:
    csv_full = city_df.to_csv(index=False)
    st.download_button(
        "📥 Full City Data (CSV)",
        csv_full,
        file_name=f"{report_city}_aqi_data.csv",
        mime="text/csv",
        use_container_width=True,
    )

with dc2:
    csv_monthly = monthly_summary.to_csv(index=False)
    st.download_button(
        "📥 Monthly Summary (CSV)",
        csv_monthly,
        file_name=f"{report_city}_monthly_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )

with dc3:
    all_csv = df.to_csv(index=False)
    st.download_button(
        "📥 All Cities Data (CSV)",
        all_csv,
        file_name="all_cities_aqi_data.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.divider()

# --- Text Report ---
st.subheader("📝 Text Report")

report_text = f"""
AQI MONITORING REPORT — {report_city}
{'=' * 50}
Period: {city_df['Date'].min().strftime('%b %d, %Y')} to {city_df['Date'].max().strftime('%b %d, %Y')}
Total Days Monitored: {total_days}

AIR QUALITY SUMMARY
  Average AQI: {avg_aqi} ({get_aqi_category(avg_aqi)})
  Worst AQI: {max_aqi} on {max_date}
  Best AQI: {min_aqi} on {min_date}
  Dominant Pollutant: {dominant}

CATEGORY DISTRIBUTION
  Good (0-50):       {cat_counts.get('Good', 0)} days ({cat_pct.get('Good', 0)}%)
  Moderate (51-100): {cat_counts.get('Moderate', 0)} days ({cat_pct.get('Moderate', 0)}%)
  Poor (101-200):    {cat_counts.get('Poor', 0)} days ({cat_pct.get('Poor', 0)}%)
  Very Poor (201-300): {cat_counts.get('Very Poor', 0)} days ({cat_pct.get('Very Poor', 0)}%)
  Severe (301+):     {cat_counts.get('Severe', 0)} days ({cat_pct.get('Severe', 0)}%)

AVERAGE POLLUTANT LEVELS
  PM2.5: {poll_avg['PM2.5']} µg/m³
  PM10:  {poll_avg['PM10']} µg/m³
  NO2:   {poll_avg['NO2']} µg/m³
  SO2:   {poll_avg['SO2']} µg/m³
  CO:    {poll_avg['CO']} mg/m³
  O3:    {poll_avg['O3']} µg/m³

WEATHER CONDITIONS
  Temperature: {avg_temp}°C (Range: {city_df['Temperature'].min():.0f}°C – {city_df['Temperature'].max():.0f}°C)
  Humidity: {avg_hum}% (Range: {city_df['Humidity'].min():.0f}% – {city_df['Humidity'].max():.0f}%)
  Wind Speed: {avg_wind} km/h
"""

st.code(report_text, language=None)

st.download_button(
    "📥 Download Text Report",
    report_text,
    file_name=f"{report_city}_aqi_report.txt",
    mime="text/plain",
    use_container_width=True,
)
