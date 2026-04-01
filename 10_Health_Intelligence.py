import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data import load_dataset, get_aqi_category
from utils.health_intelligence import (
    compute_health_risk_score,
    compute_safe_outdoor_hours,
    get_activity_recommendations,
    estimate_exposure_impact,
    get_daily_action_plan,
)

st.set_page_config(layout="wide")
st.title("🧠 Health Intelligence")
st.caption("Transforming air quality data into actionable health decisions")

df = load_dataset()

# --- Input Section ---
st.subheader("📍 Location & Profile")

ic1, ic2 = st.columns(2)
with ic1:
    city = st.selectbox("City", df["City"].unique().tolist())
with ic2:
    use_latest = st.checkbox("Use latest recorded AQI", value=True)

if use_latest:
    city_latest = df[df["City"] == city].sort_values("Date").iloc[-1]
    aqi = int(city_latest["AQI"])
    st.info(f"Latest AQI for {city}: **{aqi}** ({get_aqi_category(aqi)}) — recorded on {city_latest['Date'].strftime('%b %d, %Y')}")
else:
    aqi = st.slider("Enter AQI", 0, 500, 120)

category = get_aqi_category(aqi)

# --- Health Profile ---
with st.expander("👤 Your Health Profile", expanded=True):
    pc1, pc2, pc3 = st.columns(3)
    with pc1:
        age = st.number_input("Age", 1, 100, 30)
    with pc2:
        has_respiratory = st.checkbox("Asthma / Respiratory")
        has_heart = st.checkbox("Heart disease")
    with pc3:
        is_pregnant = st.checkbox("Pregnant")
        has_diabetes = st.checkbox("Diabetes")

st.divider()

# =============================================
# 1. HEALTH RISK SCORE
# =============================================
st.subheader("🎯 Your Health Risk Score")

risk_score, risk_level = compute_health_risk_score(
    aqi, age, has_respiratory, has_heart, is_pregnant
)

rs1, rs2 = st.columns([2, 3])
with rs1:
    st.metric("Risk Score", f"{risk_score} / 100")
    st.metric("Risk Level", risk_level)

    risk_colors = {"Low": "success", "Moderate": "info", "High": "warning", "Very High": "error", "Critical": "error"}
    risk_msgs = {
        "Low": "Minimal health risk. Normal activities are safe.",
        "Moderate": "Some risk for sensitive individuals. Take basic precautions.",
        "High": "Significant health risk. Reduce outdoor exposure.",
        "Very High": "Serious health risk for everyone. Stay indoors if possible.",
        "Critical": "Emergency-level risk. Immediate protective action required.",
    }
    getattr(st, risk_colors[risk_level])(risk_msgs[risk_level])

with rs2:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        title={"text": "Health Risk Score"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "darkblue"},
            "steps": [
                {"range": [0, 20], "color": "#2ecc71"},
                {"range": [20, 40], "color": "#f1c40f"},
                {"range": [40, 60], "color": "#e67e22"},
                {"range": [60, 80], "color": "#e74c3c"},
                {"range": [80, 100], "color": "#8e44ad"},
            ],
        },
    ))
    fig_gauge.update_layout(height=280, margin=dict(t=50, b=20, l=30, r=30))
    st.plotly_chart(fig_gauge, use_container_width=True)

st.divider()

# =============================================
# 2. SAFE OUTDOOR HOURS
# =============================================
st.subheader("⏱️ Safe Outdoor Duration")

safe_hours = compute_safe_outdoor_hours(aqi)
hours_df = pd.DataFrame({
    "Activity": safe_hours.keys(),
    "Safe Hours": safe_hours.values(),
})

sh1, sh2 = st.columns([3, 2])
with sh1:
    colors = ["#2ecc71" if h >= 3 else "#f39c12" if h >= 1 else "#e74c3c" for h in hours_df["Safe Hours"]]
    fig_hours = go.Figure(go.Bar(
        x=hours_df["Safe Hours"], y=hours_df["Activity"],
        orientation="h", marker_color=colors,
        text=[f"{h}h" if h > 0 else "Avoid" for h in hours_df["Safe Hours"]],
        textposition="outside",
    ))
    fig_hours.update_layout(height=300, margin=dict(t=20, b=20, l=10), xaxis_title="Hours",
                            xaxis=dict(range=[0, max(hours_df["Safe Hours"]) * 1.3 + 0.5]))
    st.plotly_chart(fig_hours, use_container_width=True)

with sh2:
    st.dataframe(hours_df, use_container_width=True, hide_index=True)

st.divider()

# =============================================
# 3. ACTIVITY SAFETY MATRIX
# =============================================
st.subheader("🏃 Activity Safety Matrix")

activities = get_activity_recommendations(aqi)

act_cols = st.columns(4)
for i, act in enumerate(activities):
    with act_cols[i % 4]:
        safety_color = {"Safe": "success", "Caution": "warning", "Avoid": "error", "Reduce": "warning"}
        getattr(st, safety_color.get(act["safety"], "info"))(
            f"{act['icon']} **{act['activity']}**\n\n{act['indicator']} {act['safety']}"
        )

st.divider()

# =============================================
# 4. EXPOSURE CALCULATOR
# =============================================
st.subheader("📐 Exposure Impact Calculator")
st.caption("Estimate the health impact of spending time outdoors at current AQI")

ec1, ec2 = st.columns(2)
with ec1:
    outdoor_hours = st.slider("Hours spent outdoors today", 0.0, 12.0, 2.0, 0.5)

exposure = estimate_exposure_impact(aqi, outdoor_hours)

with ec2:
    st.metric("Estimated PM2.5 Inhaled", f"{exposure['inhaled_pm25_ug']} µg")
    st.metric("Impact Level", exposure["impact_level"])

getattr(st, exposure["color"])(
    f"**{exposure['impact_level']} Impact** — At AQI {aqi}, spending {outdoor_hours}h outdoors "
    f"results in inhaling approximately {exposure['inhaled_pm25_ug']} µg of PM2.5 "
    f"(ambient concentration: ~{exposure['pm25_concentration']} µg/m³)."
)

# Comparison chart: impact at different durations
durations = [0.5, 1, 2, 4, 6, 8]
impacts = [estimate_exposure_impact(aqi, h) for h in durations]
impact_df = pd.DataFrame({
    "Hours Outdoor": durations,
    "PM2.5 Inhaled (µg)": [i["inhaled_pm25_ug"] for i in impacts],
    "Impact": [i["impact_level"] for i in impacts],
})

fig_exp = px.bar(impact_df, x="Hours Outdoor", y="PM2.5 Inhaled (µg)",
                 color="Impact", text="PM2.5 Inhaled (µg)",
                 color_discrete_map={"Negligible": "#2ecc71", "Low": "#3498db",
                                     "Moderate": "#f39c12", "High": "#e74c3c",
                                     "Very High": "#8e44ad"})
fig_exp.update_traces(texttemplate="%{text:.0f}", textposition="outside")
fig_exp.update_layout(height=350, margin=dict(t=20, b=20))
st.plotly_chart(fig_exp, use_container_width=True)

st.divider()

# =============================================
# 5. DAILY ACTION PLAN
# =============================================
st.subheader("📅 Today's Action Plan")

plan = get_daily_action_plan(aqi, category)

for item in plan:
    st.info(f"{item['icon']} **{item['time']}** — {item['action']}")

st.divider()

# =============================================
# 6. HISTORICAL RISK TREND
# =============================================
st.subheader("📈 Historical Health Risk Trend")

city_df = df[df["City"] == city].sort_values("Date").tail(90).copy()
city_df["Risk_Score"] = city_df["AQI"].apply(
    lambda a: compute_health_risk_score(int(a), age, has_respiratory, has_heart, is_pregnant)[0]
)

fig_trend = px.area(city_df, x="Date", y="Risk_Score",
                    labels={"Risk_Score": "Health Risk Score"},
                    color_discrete_sequence=["#e74c3c"])
fig_trend.add_hline(y=20, line_dash="dot", line_color="green", annotation_text="Low Risk")
fig_trend.add_hline(y=60, line_dash="dot", line_color="orange", annotation_text="High Risk")
fig_trend.add_hline(y=80, line_dash="dot", line_color="red", annotation_text="Critical")
fig_trend.update_layout(height=400, margin=dict(t=20, b=20))
st.plotly_chart(fig_trend, use_container_width=True)

# Risk distribution
risk_cats = city_df["Risk_Score"].apply(
    lambda s: "Low" if s <= 20 else "Moderate" if s <= 40 else "High" if s <= 60 else "Very High" if s <= 80 else "Critical"
)
risk_dist = risk_cats.value_counts()
risk_order = ["Low", "Moderate", "High", "Very High", "Critical"]
risk_dist = risk_dist.reindex(risk_order, fill_value=0)

fig_dist = px.pie(values=risk_dist.values, names=risk_dist.index, hole=0.4,
                  color=risk_dist.index,
                  color_discrete_map={"Low": "#2ecc71", "Moderate": "#f1c40f",
                                      "High": "#e67e22", "Very High": "#e74c3c",
                                      "Critical": "#8e44ad"})
fig_dist.update_layout(height=350, margin=dict(t=20, b=20))
st.plotly_chart(fig_dist, use_container_width=True)
