import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data import load_dataset

st.set_page_config(layout="wide")
st.title("🏠 Dashboard")

df = load_dataset()

# --- AQI Categories Legend ---
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.success("**Good** · 0–50")
with col2:
    st.info("**Moderate** · 51–100")
with col3:
    st.warning("**Poor** · 101–200")
with col4:
    st.error("**Very Poor** · 201–300")
with col5:
    st.error("**Severe** · 301+")

st.divider()

# --- Latest snapshot ---
latest = df.sort_values("Date").groupby("City").last().reset_index()
latest = latest.sort_values("AQI", ascending=False)

col_table, col_chart = st.columns([2, 3])

with col_table:
    st.subheader("📍 Latest City Status")
    display_df = latest[["City", "AQI", "AQI_Category", "Dominant_Pollutant", "PM2.5", "PM10"]].copy()
    display_df.columns = ["City", "AQI", "Category", "Dominant Pollutant", "PM2.5", "PM10"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

with col_chart:
    st.subheader("📊 City AQI Comparison")
    color_map = {"Good": "#2ecc71", "Moderate": "#f1c40f", "Poor": "#e67e22", "Very Poor": "#e74c3c", "Severe": "#8e44ad"}
    fig = px.bar(latest, x="City", y="AQI", color="AQI_Category", color_discrete_map=color_map,
                 text="AQI", labels={"AQI_Category": "Category"})
    fig.update_layout(showlegend=True, height=350, margin=dict(t=20, b=20))
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Monthly AQI Trend ---
st.subheader("📈 Monthly AQI Trend")
monthly = df.groupby([df["Date"].dt.to_period("M"), "City"])["AQI"].mean().reset_index()
monthly["Date"] = monthly["Date"].dt.to_timestamp()

fig2 = px.line(monthly, x="Date", y="AQI", color="City", markers=True,
               labels={"AQI": "Avg AQI"})
fig2.update_layout(height=400, margin=dict(t=20, b=20), hovermode="x unified")
st.plotly_chart(fig2, use_container_width=True)

# --- Key Stats ---
st.subheader("📋 Key Statistics")

s1, s2, s3, s4 = st.columns(4)
worst_city = latest.iloc[0]
best_city = latest.iloc[-1]

with s1:
    st.metric("Most Polluted", worst_city["City"], delta=f"AQI {worst_city['AQI']}", delta_color="off")
with s2:
    st.metric("Cleanest City", best_city["City"], delta=f"AQI {best_city['AQI']}", delta_color="off")
with s3:
    poor_pct = round((df["AQI"] > 100).mean() * 100, 1)
    st.metric("Days > Poor AQI", f"{poor_pct}%")
with s4:
    dominant = df["Dominant_Pollutant"].value_counts().idxmax()
    st.metric("Top Pollutant", dominant)

# --- Category Distribution ---
st.subheader("🧮 AQI Category Distribution")
cat_counts = df.groupby(["City", "AQI_Category"]).size().reset_index(name="Days")
cat_order = ["Good", "Moderate", "Poor", "Very Poor", "Severe"]
cat_counts["AQI_Category"] = pd.Categorical(cat_counts["AQI_Category"], categories=cat_order, ordered=True)
cat_counts = cat_counts.sort_values("AQI_Category")

fig3 = px.bar(cat_counts, x="City", y="Days", color="AQI_Category",
              color_discrete_map=color_map, barmode="stack",
              labels={"AQI_Category": "Category"})
fig3.update_layout(height=400, margin=dict(t=20, b=20))
st.plotly_chart(fig3, use_container_width=True)
