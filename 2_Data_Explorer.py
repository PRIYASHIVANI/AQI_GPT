import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.figure_factory as ff
from utils.data import load_dataset

st.set_page_config(layout="wide")
st.title("📊 Data Explorer")

df = load_dataset()

# --- Filters ---
st.subheader("🔍 Filters")
fc1, fc2, fc3 = st.columns(3)

with fc1:
    selected_cities = st.multiselect("Cities", df["City"].unique().tolist(), default=df["City"].unique().tolist())
with fc2:
    date_range = st.date_input("Date Range", value=(df["Date"].min(), df["Date"].max()),
                               min_value=df["Date"].min(), max_value=df["Date"].max())
with fc3:
    pollutant_focus = st.selectbox("Highlight Pollutant", ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"])

if len(date_range) == 2:
    start, end = date_range
    filtered = df[(df["City"].isin(selected_cities)) &
                  (df["Date"] >= pd.to_datetime(start)) &
                  (df["Date"] <= pd.to_datetime(end))]
else:
    filtered = df[df["City"].isin(selected_cities)]

st.caption(f"Showing {len(filtered):,} records")

st.divider()

# --- Dataset Preview ---
st.subheader("📄 Dataset")
st.dataframe(filtered.head(200), use_container_width=True, hide_index=True)

# --- AQI Trend ---
st.subheader("📈 AQI Trend Over Time")
fig1 = px.line(filtered, x="Date", y="AQI", color="City", labels={"AQI": "AQI Value"})
fig1.update_layout(height=400, margin=dict(t=20, b=20), hovermode="x unified")
st.plotly_chart(fig1, use_container_width=True)

# --- Pollutant Trend ---
st.subheader(f"🔬 {pollutant_focus} Trend")
fig_poll = px.line(filtered, x="Date", y=pollutant_focus, color="City")
fig_poll.update_layout(height=350, margin=dict(t=20, b=20), hovermode="x unified")
st.plotly_chart(fig_poll, use_container_width=True)

# --- Correlation Matrix ---
st.subheader("🔗 Correlation Matrix")
numeric_cols = ["AQI", "PM2.5", "PM10", "NO2", "SO2", "CO", "O3", "Temperature", "Humidity", "Wind_Speed"]
corr = filtered[numeric_cols].corr()

fig2 = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                 labels={"color": "Correlation"}, aspect="auto")
fig2.update_layout(height=500, margin=dict(t=20, b=20))
st.plotly_chart(fig2, use_container_width=True)

# --- Weather vs AQI ---
st.subheader("🌦️ Weather vs AQI")
wc1, wc2, wc3 = st.columns(3)

with wc1:
    fig3 = px.scatter(filtered, x="Temperature", y="AQI", color="City", opacity=0.5,
                      labels={"Temperature": "Temperature (°C)"})
    fig3.update_layout(height=350, margin=dict(t=20, b=20), showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

with wc2:
    fig4 = px.scatter(filtered, x="Humidity", y="AQI", color="City", opacity=0.5,
                      labels={"Humidity": "Humidity (%)"})
    fig4.update_layout(height=350, margin=dict(t=20, b=20), showlegend=False)
    st.plotly_chart(fig4, use_container_width=True)

with wc3:
    fig5 = px.scatter(filtered, x="Wind_Speed", y="AQI", color="City", opacity=0.5,
                      labels={"Wind_Speed": "Wind Speed (km/h)"})
    fig5.update_layout(height=350, margin=dict(t=20, b=20), showlegend=False)
    st.plotly_chart(fig5, use_container_width=True)

# --- Traffic Impact ---
st.subheader("🚦 Traffic Impact on AQI")
traffic_order = ["Low", "Medium", "High"]
fig6 = px.box(filtered, x="Traffic", y="AQI", color="Traffic",
              category_orders={"Traffic": traffic_order},
              color_discrete_sequence=["#2ecc71", "#f39c12", "#e74c3c"])
fig6.update_layout(height=400, margin=dict(t=20, b=20), showlegend=False)
st.plotly_chart(fig6, use_container_width=True)

# --- Statistical Summary ---
st.subheader("📋 Statistical Summary")
summary = filtered.groupby("City")[numeric_cols].agg(["mean", "min", "max", "std"]).round(1)
summary.columns = [f"{col} ({stat})" for col, stat in summary.columns]
st.dataframe(summary, use_container_width=True)
