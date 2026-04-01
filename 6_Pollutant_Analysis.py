import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data import load_dataset, compute_sub_index

st.set_page_config(layout="wide")
st.title("🔬 Pollutant Analysis")

df = load_dataset()
POLLUTANTS = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"]

# --- City & Date Filter ---
fc1, fc2 = st.columns(2)
with fc1:
    selected_city = st.selectbox("City", ["All Cities"] + df["City"].unique().tolist())
with fc2:
    selected_pollutant = st.selectbox("Focus Pollutant", POLLUTANTS)

if selected_city == "All Cities":
    filtered = df.copy()
else:
    filtered = df[df["City"] == selected_city].copy()

st.divider()

# --- Dominant Pollutant Distribution ---
st.subheader("🏆 Dominant Pollutant Frequency")
dom_counts = filtered["Dominant_Pollutant"].value_counts().reset_index()
dom_counts.columns = ["Pollutant", "Days"]

color_map = {"PM2.5": "#e74c3c", "PM10": "#e67e22", "NO2": "#f39c12", "SO2": "#9b59b6", "CO": "#3498db", "O3": "#2ecc71"}
fig1 = px.pie(dom_counts, values="Days", names="Pollutant", color="Pollutant",
              color_discrete_map=color_map, hole=0.4)
fig1.update_layout(height=400, margin=dict(t=20, b=20))
st.plotly_chart(fig1, use_container_width=True)

# --- Pollutant Trends ---
st.subheader(f"📈 {selected_pollutant} — Daily Trend")
if selected_city == "All Cities":
    fig2 = px.line(filtered, x="Date", y=selected_pollutant, color="City")
else:
    fig2 = px.area(filtered, x="Date", y=selected_pollutant, color_discrete_sequence=["#e74c3c"])
fig2.update_layout(height=400, margin=dict(t=20, b=20), hovermode="x unified")
st.plotly_chart(fig2, use_container_width=True)

# --- Monthly Averages ---
st.subheader(f"📅 {selected_pollutant} — Monthly Average")
monthly = filtered.copy()
monthly["Month"] = monthly["Date"].dt.to_period("M")

if selected_city == "All Cities":
    monthly_avg = monthly.groupby(["Month", "City"])[selected_pollutant].mean().reset_index()
    monthly_avg["Month"] = monthly_avg["Month"].dt.to_timestamp()
    fig3 = px.bar(monthly_avg, x="Month", y=selected_pollutant, color="City", barmode="group")
else:
    monthly_avg = monthly.groupby("Month")[selected_pollutant].mean().reset_index()
    monthly_avg["Month"] = monthly_avg["Month"].dt.to_timestamp()
    fig3 = px.bar(monthly_avg, x="Month", y=selected_pollutant,
                  color_discrete_sequence=["#e67e22"], text=selected_pollutant)
    fig3.update_traces(texttemplate="%{text:.1f}", textposition="outside")

fig3.update_layout(height=400, margin=dict(t=20, b=20))
st.plotly_chart(fig3, use_container_width=True)

# --- All Pollutants Comparison ---
st.subheader("⚖️ Pollutant Comparison — Latest Values")

if selected_city != "All Cities":
    latest = filtered.sort_values("Date").iloc[-1]
    poll_data = []
    for p in POLLUTANTS:
        sub_idx = compute_sub_index(p, latest[p])
        poll_data.append({"Pollutant": p, "Concentration": latest[p], "Sub-Index": sub_idx})
    poll_df = pd.DataFrame(poll_data).sort_values("Sub-Index", ascending=False)

    tc1, tc2 = st.columns(2)
    with tc1:
        fig4 = px.bar(poll_df, x="Pollutant", y="Concentration", color="Pollutant",
                      color_discrete_map=color_map, text="Concentration",
                      title="Raw Concentration")
        fig4.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig4.update_layout(height=400, margin=dict(t=40, b=20), showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

    with tc2:
        fig5 = px.bar(poll_df, x="Pollutant", y="Sub-Index", color="Pollutant",
                      color_discrete_map=color_map, text="Sub-Index",
                      title="AQI Sub-Index (health impact)")
        fig5.update_traces(texttemplate="%{text}", textposition="outside")
        fig5.update_layout(height=400, margin=dict(t=40, b=20), showlegend=False)
        st.plotly_chart(fig5, use_container_width=True)
else:
    latest_all = df.sort_values("Date").groupby("City").last().reset_index()
    for p in POLLUTANTS:
        latest_all[f"{p}_SI"] = latest_all[p].apply(lambda v: compute_sub_index(p, v))

    si_cols = [f"{p}_SI" for p in POLLUTANTS]
    melt = latest_all.melt(id_vars=["City"], value_vars=si_cols, var_name="Pollutant", value_name="Sub-Index")
    melt["Pollutant"] = melt["Pollutant"].str.replace("_SI", "")

    fig4 = px.bar(melt, x="City", y="Sub-Index", color="Pollutant",
                  color_discrete_map=color_map, barmode="group")
    fig4.update_layout(height=450, margin=dict(t=20, b=20))
    st.plotly_chart(fig4, use_container_width=True)

# --- Pollutant Statistics ---
st.subheader("📋 Pollutant Statistics")
stats = filtered[POLLUTANTS].describe().round(2).T
stats.columns = ["Count", "Mean", "Std", "Min", "25%", "50%", "75%", "Max"]
st.dataframe(stats, use_container_width=True)

# --- Correlation with AQI ---
st.subheader("🔗 Pollutant-AQI Correlation")
corr_with_aqi = filtered[POLLUTANTS + ["AQI"]].corr()["AQI"].drop("AQI").sort_values(ascending=False)
corr_df = pd.DataFrame({"Pollutant": corr_with_aqi.index, "Correlation": corr_with_aqi.values})

fig6 = px.bar(corr_df, x="Pollutant", y="Correlation", color="Correlation",
              color_continuous_scale="RdYlGn_r", text="Correlation")
fig6.update_traces(texttemplate="%{text:.3f}", textposition="outside")
fig6.update_layout(height=400, margin=dict(t=20, b=20))
st.plotly_chart(fig6, use_container_width=True)
