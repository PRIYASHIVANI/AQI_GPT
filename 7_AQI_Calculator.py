import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data import compute_sub_index, get_aqi_category

st.set_page_config(layout="wide")
st.title("🧮 AQI Calculator")
st.caption("Enter pollutant concentrations to compute the Air Quality Index in real-time")

st.divider()

POLLUTANT_UNITS = {
    "PM2.5": "µg/m³", "PM10": "µg/m³", "NO2": "µg/m³",
    "SO2": "µg/m³", "CO": "mg/m³", "O3": "µg/m³",
}
POLLUTANT_MAX = {
    "PM2.5": 500.0, "PM10": 600.0, "NO2": 800.0,
    "SO2": 2400.0, "CO": 50.0, "O3": 1000.0,
}
POLLUTANT_DEFAULTS = {
    "PM2.5": 75.0, "PM10": 130.0, "NO2": 45.0,
    "SO2": 12.0, "CO": 1.2, "O3": 40.0,
}
COLOR_MAP = {
    "PM2.5": "#e74c3c", "PM10": "#e67e22", "NO2": "#f39c12",
    "SO2": "#9b59b6", "CO": "#3498db", "O3": "#2ecc71",
}

# --- Pollutant Inputs ---
st.subheader("🌡️ Enter Pollutant Concentrations")

cols = st.columns(3)
values = {}
for i, (pollutant, unit) in enumerate(POLLUTANT_UNITS.items()):
    with cols[i % 3]:
        step = 0.1 if pollutant == "CO" else 5.0
        values[pollutant] = st.number_input(
            f"{pollutant} ({unit})", 0.0, POLLUTANT_MAX[pollutant],
            POLLUTANT_DEFAULTS[pollutant], step,
        )

st.divider()

# --- Compute Sub-Indices ---
sub_indices = {}
for pollutant, conc in values.items():
    sub_indices[pollutant] = compute_sub_index(pollutant, conc)

overall_aqi = max(sub_indices.values())
dominant = max(sub_indices, key=sub_indices.get)
category = get_aqi_category(overall_aqi)
icon = {"Good": "🟢", "Moderate": "🟡", "Poor": "🟠", "Very Poor": "🔴", "Severe": "☠️"}.get(category, "⚪")

# --- Result Banner ---
st.subheader("📊 Result")

r1, r2, r3 = st.columns(3)
with r1:
    st.metric("Overall AQI", overall_aqi)
with r2:
    st.metric("Category", f"{icon} {category}")
with r3:
    st.metric("Dominant Pollutant", dominant)

alert_fn = {
    "Good": st.success, "Moderate": st.info, "Poor": st.warning,
    "Very Poor": st.error, "Severe": st.error,
}
messages = {
    "Good": "Air quality is satisfactory. No health risk.",
    "Moderate": "Acceptable air quality. Sensitive individuals should be cautious.",
    "Poor": "Unhealthy for sensitive groups. Limit outdoor exertion.",
    "Very Poor": "Unhealthy for all. Avoid prolonged outdoor exposure.",
    "Severe": "Hazardous. Stay indoors and take protective measures immediately.",
}
alert_fn[category](f"**{category}** — {messages[category]}")

st.divider()

# --- Sub-Index Breakdown ---
st.subheader("🔬 Sub-Index Breakdown")

si_df = pd.DataFrame({
    "Pollutant": list(sub_indices.keys()),
    "Sub-Index": list(sub_indices.values()),
    "Concentration": [values[p] for p in sub_indices],
    "Unit": [POLLUTANT_UNITS[p] for p in sub_indices],
})
si_df = si_df.sort_values("Sub-Index", ascending=False)
si_df["Is Dominant"] = si_df["Pollutant"] == dominant

chart_col, table_col = st.columns([3, 2])

with chart_col:
    fig = go.Figure()

    for _, row in si_df.iterrows():
        color = COLOR_MAP[row["Pollutant"]]
        fig.add_trace(go.Bar(
            x=[row["Pollutant"]], y=[row["Sub-Index"]],
            name=row["Pollutant"], marker_color=color,
            text=[row["Sub-Index"]], textposition="outside",
        ))

    fig.add_hline(y=50, line_dash="dot", line_color="green", annotation_text="Good", annotation_position="right")
    fig.add_hline(y=100, line_dash="dot", line_color="gold", annotation_text="Moderate", annotation_position="right")
    fig.add_hline(y=200, line_dash="dot", line_color="orange", annotation_text="Poor", annotation_position="right")
    fig.add_hline(y=300, line_dash="dot", line_color="red", annotation_text="Very Poor", annotation_position="right")

    fig.update_layout(height=450, margin=dict(t=20, b=20), showlegend=False,
                      yaxis_title="Sub-Index Value")
    st.plotly_chart(fig, use_container_width=True)

with table_col:
    display_df = si_df[["Pollutant", "Concentration", "Unit", "Sub-Index"]].copy()
    display_df["Concentration"] = display_df["Concentration"].round(2)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.caption("**How AQI is calculated:** Each pollutant concentration is converted to a "
               "sub-index using Indian NAQI breakpoints. The overall AQI equals the highest sub-index.")

# --- Gauge ---
st.subheader("📈 AQI Gauge")

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=overall_aqi,
    delta={"reference": 100, "position": "bottom"},
    title={"text": "Air Quality Index"},
    gauge={
        "axis": {"range": [0, 500], "tickwidth": 1},
        "bar": {"color": "darkblue"},
        "steps": [
            {"range": [0, 50], "color": "#2ecc71"},
            {"range": [50, 100], "color": "#f1c40f"},
            {"range": [100, 200], "color": "#e67e22"},
            {"range": [200, 300], "color": "#e74c3c"},
            {"range": [300, 500], "color": "#8e44ad"},
        ],
        "threshold": {
            "line": {"color": "black", "width": 4},
            "thickness": 0.75,
            "value": overall_aqi,
        },
    },
))
fig_gauge.update_layout(height=350, margin=dict(t=60, b=20))
st.plotly_chart(fig_gauge, use_container_width=True)

# --- Quick Reference ---
st.subheader("📖 AQI Breakpoint Reference")

ref_data = {
    "Category": ["Good", "Moderate", "Poor", "Very Poor", "Severe"],
    "AQI Range": ["0–50", "51–100", "101–200", "201–300", "301–500"],
    "PM2.5": ["0–30", "31–60", "61–90", "91–120", "121–250"],
    "PM10": ["0–50", "51–100", "101–250", "251–350", "351–430"],
    "NO2": ["0–40", "41–80", "81–180", "181–280", "281–400"],
    "SO2": ["0–40", "41–80", "81–380", "381–800", "801–1600"],
    "CO": ["0–1.0", "1.1–2.0", "2.1–10", "10.1–17", "17.1–34"],
    "O3": ["0–50", "51–100", "101–168", "169–208", "209–748"],
}
st.dataframe(pd.DataFrame(ref_data), use_container_width=True, hide_index=True)
