import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data import load_dataset

st.set_page_config(layout="wide")
st.title("📍 Location AQI")

df = load_dataset()

CITY_COORDS = {
    "Delhi":              {"lat": 28.6139, "lon": 77.2090},
    "Mumbai":             {"lat": 19.0760, "lon": 72.8777},
    "Chennai":            {"lat": 13.0827, "lon": 80.2707},
    "Bengaluru":          {"lat": 12.9716, "lon": 77.5946},
    "Hyderabad":          {"lat": 17.3850, "lon": 78.4867},
    "Kolkata":            {"lat": 22.5726, "lon": 88.3639},
    "Pune":               {"lat": 18.5204, "lon": 73.8567},
    "Ahmedabad":          {"lat": 23.0225, "lon": 72.5714},
    "Jaipur":             {"lat": 26.9124, "lon": 75.7873},
    "Lucknow":            {"lat": 26.8467, "lon": 80.9462},
    "Patna":              {"lat": 25.6093, "lon": 85.1376},
    "Chandigarh":         {"lat": 30.7333, "lon": 76.7794},
    "Visakhapatnam":      {"lat": 17.6868, "lon": 83.2185},
    "Thiruvananthapuram": {"lat": 8.5241,  "lon": 76.9366},
}

# --- Map View ---
st.subheader("🗺️ AQI Map")

latest = df.sort_values("Date").groupby("City").last().reset_index()
latest["lat"] = latest["City"].map(lambda c: CITY_COORDS[c]["lat"])
latest["lon"] = latest["City"].map(lambda c: CITY_COORDS[c]["lon"])

color_map = {"Good": "#2ecc71", "Moderate": "#f1c40f", "Poor": "#e67e22", "Very Poor": "#e74c3c", "Severe": "#8e44ad"}

fig_map = px.scatter_mapbox(
    latest, lat="lat", lon="lon", size="AQI", color="AQI_Category",
    color_discrete_map=color_map, hover_name="City",
    hover_data={"AQI": True, "PM2.5": True, "PM10": True, "AQI_Category": True, "lat": False, "lon": False},
    size_max=40, zoom=4, center={"lat": 20.5, "lon": 78.9},
    mapbox_style="carto-positron",
    labels={"AQI_Category": "Category"},
)
fig_map.update_layout(height=500, margin=dict(t=0, b=0, l=0, r=0))
st.plotly_chart(fig_map, use_container_width=True)

st.divider()

# --- All Cities Overview ---
st.subheader("🏙️ All Cities — Latest Status")

latest = latest.sort_values("AQI", ascending=False)

icon_map = {"Good": "🟢", "Moderate": "🟡", "Poor": "🟠", "Very Poor": "🔴", "Severe": "☠️"}

cols = st.columns(len(latest))
for col, (_, row) in zip(cols, latest.iterrows()):
    cat = row["AQI_Category"]
    with col:
        st.metric(row["City"], f"{row['AQI']} AQI")
        st.caption(f"{icon_map.get(cat, '')} {cat}")

st.divider()

# --- City Deep Dive ---
st.subheader("🔎 City Details")
city = st.selectbox("Select City", df["City"].unique().tolist())
city_df = df[df["City"] == city].sort_values("Date")

c1, c2, c3, c4 = st.columns(4)
city_latest = city_df.iloc[-1]
city_avg = round(city_df["AQI"].mean())
city_max = city_df["AQI"].max()
city_min = city_df["AQI"].min()

with c1:
    st.metric("Current AQI", int(city_latest["AQI"]),
              delta=f"{icon_map.get(city_latest['AQI_Category'], '')} {city_latest['AQI_Category']}", delta_color="off")
with c2:
    st.metric("Avg AQI (All Time)", city_avg)
with c3:
    st.metric("Peak AQI", int(city_max))
with c4:
    st.metric("Best AQI", int(city_min))

# --- 30-Day Trend ---
st.subheader("📈 Last 30 Days — AQI Trend")
last30 = city_df.tail(30)
fig1 = px.area(last30, x="Date", y="AQI", labels={"AQI": "AQI Value"},
               color_discrete_sequence=["#e74c3c"])
fig1.update_layout(height=350, margin=dict(t=20, b=20))
st.plotly_chart(fig1, use_container_width=True)

# --- Pollutant Breakdown ---
st.subheader("🔬 Current Pollutant Levels")
pollutants = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"]
poll_values = [city_latest[p] for p in pollutants]
poll_df = pd.DataFrame({"Pollutant": pollutants, "Value": poll_values})

color_seq = ["#e74c3c", "#e67e22", "#f39c12", "#9b59b6", "#3498db", "#2ecc71"]
fig2 = px.bar(poll_df, x="Pollutant", y="Value", color="Pollutant",
              color_discrete_sequence=color_seq, text="Value")
fig2.update_traces(textposition="outside")
fig2.update_layout(height=350, margin=dict(t=20, b=20), showlegend=False)
st.plotly_chart(fig2, use_container_width=True)

# --- Weather Context ---
st.subheader("🌦️ Weather Conditions")
wc1, wc2, wc3 = st.columns(3)
with wc1:
    st.metric("Temperature", f"{city_latest['Temperature']}°C")
with wc2:
    st.metric("Humidity", f"{city_latest['Humidity']}%")
with wc3:
    st.metric("Wind Speed", f"{city_latest['Wind_Speed']} km/h")

# --- Health Alert ---
st.subheader("🚨 Health Alert")
cat = city_latest["AQI_Category"]
alerts = {
    "Good": ("success", "Air quality is good. Safe for all outdoor activities."),
    "Moderate": ("info", "Sensitive individuals should limit prolonged outdoor exertion."),
    "Poor": ("warning", "Avoid outdoor exercise. Wearing a mask is recommended."),
    "Very Poor": ("error", "Limit outdoor exposure. Use N95 masks if necessary."),
    "Severe": ("error", "Severe pollution — stay indoors and avoid all outdoor activity."),
}
level, msg = alerts.get(cat, ("info", ""))
getattr(st, level)(msg)

# --- Multi-City Comparison ---
st.divider()
st.subheader("📊 City Comparison — AQI Distribution")

fig3 = px.box(df, x="City", y="AQI", color="City",
              color_discrete_sequence=px.colors.qualitative.Set2)
fig3.update_layout(height=400, margin=dict(t=20, b=20), showlegend=False)
st.plotly_chart(fig3, use_container_width=True)

# --- Monthly Heatmap ---
st.subheader("📅 Monthly AQI Heatmap")
city_monthly = city_df.copy()
city_monthly["Month"] = city_monthly["Date"].dt.strftime("%b")
city_monthly["Year"] = city_monthly["Date"].dt.year
pivot = city_monthly.groupby(["Year", "Month"])["AQI"].mean().reset_index()
month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
pivot["Month"] = pd.Categorical(pivot["Month"], categories=month_order, ordered=True)
pivot = pivot.sort_values(["Year", "Month"])
pivot_table = pivot.pivot(index="Year", columns="Month", values="AQI")

fig4 = px.imshow(pivot_table, text_auto=".0f", color_continuous_scale="YlOrRd",
                 labels={"color": "Avg AQI"}, aspect="auto")
fig4.update_layout(height=250, margin=dict(t=20, b=20))
st.plotly_chart(fig4, use_container_width=True)
