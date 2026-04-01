import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.data import load_dataset, compute_sub_index

st.set_page_config(layout="wide")
st.title("⚖️ City Comparison")
st.caption("Side-by-side analysis of two cities across all metrics")

df = load_dataset()
cities = df["City"].unique().tolist()

c1, c2 = st.columns(2)
with c1:
    city_a = st.selectbox("City A", cities, index=0)
with c2:
    default_b = 1 if len(cities) > 1 else 0
    city_b = st.selectbox("City B", cities, index=default_b)

df_a = df[df["City"] == city_a].sort_values("Date")
df_b = df[df["City"] == city_b].sort_values("Date")
latest_a = df_a.iloc[-1]
latest_b = df_b.iloc[-1]

st.divider()

# --- Current Status Side-by-Side ---
st.subheader("📊 Current Status")

icon_map = {"Good": "🟢", "Moderate": "🟡", "Poor": "🟠", "Very Poor": "🔴", "Severe": "☠️"}

sa, sb = st.columns(2)
with sa:
    st.markdown(f"### {city_a}")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("AQI", int(latest_a["AQI"]))
    with m2:
        cat_a = latest_a["AQI_Category"]
        st.metric("Category", f"{icon_map.get(cat_a, '')} {cat_a}")
    with m3:
        st.metric("Dominant", latest_a["Dominant_Pollutant"])

with sb:
    st.markdown(f"### {city_b}")
    m4, m5, m6 = st.columns(3)
    with m4:
        st.metric("AQI", int(latest_b["AQI"]))
    with m5:
        cat_b = latest_b["AQI_Category"]
        st.metric("Category", f"{icon_map.get(cat_b, '')} {cat_b}")
    with m6:
        st.metric("Dominant", latest_b["Dominant_Pollutant"])

st.divider()

# --- AQI Trend Overlay ---
st.subheader("📈 AQI Trend Comparison")

combined = pd.concat([
    df_a[["Date", "AQI"]].assign(City=city_a),
    df_b[["Date", "AQI"]].assign(City=city_b),
])
fig1 = px.line(combined, x="Date", y="AQI", color="City", markers=False,
               color_discrete_sequence=["#3498db", "#e74c3c"])
fig1.update_layout(height=400, margin=dict(t=20, b=20), hovermode="x unified")
st.plotly_chart(fig1, use_container_width=True)

# --- Pollutant Comparison ---
st.subheader("🔬 Pollutant Levels — Latest")

pollutants = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"]
poll_data = []
for p in pollutants:
    poll_data.append({"Pollutant": p, "Value": latest_a[p], "City": city_a})
    poll_data.append({"Pollutant": p, "Value": latest_b[p], "City": city_b})

poll_df = pd.DataFrame(poll_data)
fig2 = px.bar(poll_df, x="Pollutant", y="Value", color="City", barmode="group",
              color_discrete_sequence=["#3498db", "#e74c3c"], text="Value")
fig2.update_traces(texttemplate="%{text:.1f}", textposition="outside")
fig2.update_layout(height=400, margin=dict(t=20, b=20))
st.plotly_chart(fig2, use_container_width=True)

# --- Sub-Index Comparison ---
st.subheader("📐 Sub-Index Comparison")

si_data = []
for p in pollutants:
    si_data.append({"Pollutant": p, "Sub-Index": compute_sub_index(p, latest_a[p]), "City": city_a})
    si_data.append({"Pollutant": p, "Sub-Index": compute_sub_index(p, latest_b[p]), "City": city_b})

si_df = pd.DataFrame(si_data)
fig3 = px.bar(si_df, x="Pollutant", y="Sub-Index", color="City", barmode="group",
              color_discrete_sequence=["#3498db", "#e74c3c"], text="Sub-Index")
fig3.update_traces(textposition="outside")
fig3.update_layout(height=400, margin=dict(t=20, b=20))
st.plotly_chart(fig3, use_container_width=True)

# --- Weather Comparison ---
st.subheader("🌦️ Weather Conditions — Latest")

weather_params = ["Temperature", "Humidity", "Wind_Speed"]
weather_labels = {"Temperature": "Temp (°C)", "Humidity": "Humidity (%)", "Wind_Speed": "Wind (km/h)"}

wc = st.columns(3)
for i, param in enumerate(weather_params):
    with wc[i]:
        st.metric(f"{weather_labels[param]} — {city_a}", f"{latest_a[param]}")
        st.metric(f"{weather_labels[param]} — {city_b}", f"{latest_b[param]}")

# --- Monthly Average Comparison ---
st.subheader("📅 Monthly Average AQI")

monthly_a = df_a.groupby(df_a["Date"].dt.to_period("M"))["AQI"].mean().reset_index()
monthly_a["Date"] = monthly_a["Date"].dt.to_timestamp()
monthly_a["City"] = city_a

monthly_b = df_b.groupby(df_b["Date"].dt.to_period("M"))["AQI"].mean().reset_index()
monthly_b["Date"] = monthly_b["Date"].dt.to_timestamp()
monthly_b["City"] = city_b

monthly_combined = pd.concat([monthly_a, monthly_b])
fig4 = px.bar(monthly_combined, x="Date", y="AQI", color="City", barmode="group",
              color_discrete_sequence=["#3498db", "#e74c3c"])
fig4.update_layout(height=400, margin=dict(t=20, b=20))
st.plotly_chart(fig4, use_container_width=True)

# --- Category Distribution ---
st.subheader("🧮 AQI Category Distribution")

cat_order = ["Good", "Moderate", "Poor", "Very Poor", "Severe"]

cat_a = df_a["AQI_Category"].value_counts().reindex(cat_order, fill_value=0)
cat_b = df_b["AQI_Category"].value_counts().reindex(cat_order, fill_value=0)

cat_compare = pd.DataFrame({
    "Category": cat_order,
    city_a: cat_a.values,
    city_b: cat_b.values,
})

dc1, dc2 = st.columns(2)

with dc1:
    fig5a = px.pie(values=cat_a.values, names=cat_order, title=city_a, hole=0.4,
                   color=cat_order, color_discrete_map={
                       "Good": "#2ecc71", "Moderate": "#f1c40f", "Poor": "#e67e22",
                       "Very Poor": "#e74c3c", "Severe": "#8e44ad"})
    fig5a.update_layout(height=350, margin=dict(t=40, b=20))
    st.plotly_chart(fig5a, use_container_width=True)

with dc2:
    fig5b = px.pie(values=cat_b.values, names=cat_order, title=city_b, hole=0.4,
                   color=cat_order, color_discrete_map={
                       "Good": "#2ecc71", "Moderate": "#f1c40f", "Poor": "#e67e22",
                       "Very Poor": "#e74c3c", "Severe": "#8e44ad"})
    fig5b.update_layout(height=350, margin=dict(t=40, b=20))
    st.plotly_chart(fig5b, use_container_width=True)

# --- Stats Table ---
st.subheader("📋 Statistical Comparison")

stats_cols = ["AQI"] + pollutants
stats_a = df_a[stats_cols].describe().T[["mean", "min", "max", "std"]].round(1)
stats_b = df_b[stats_cols].describe().T[["mean", "min", "max", "std"]].round(1)

stats_a.columns = [f"{city_a} Mean", f"{city_a} Min", f"{city_a} Max", f"{city_a} Std"]
stats_b.columns = [f"{city_b} Mean", f"{city_b} Min", f"{city_b} Max", f"{city_b} Std"]

stats_combined = pd.concat([stats_a, stats_b], axis=1)
st.dataframe(stats_combined, use_container_width=True)
