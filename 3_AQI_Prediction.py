import os
import json
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

from utils.data import load_dataset, get_aqi_category, compute_sub_index
from utils.preprocessing import FEATURE_COLS, prepare_inference_input
from utils.health_intelligence import compute_health_risk_score, get_activity_recommendations

st.set_page_config(layout="wide")
st.title("🤖 AQI Prediction")

MODEL_DIR = "models"

@st.cache_resource
def load_models():
    models = {}
    for name in ["random_forest", "gradient_boosting", "ridge"]:
        path = os.path.join(MODEL_DIR, f"{name}.pkl")
        if os.path.exists(path):
            models[name] = joblib.load(path)
    nn_path = os.path.join(MODEL_DIR, "neural_network.pkl")
    nn_bundle = None
    if os.path.exists(nn_path):
        nn_bundle = joblib.load(nn_path)
        models["neural_network"] = nn_bundle
    scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
    metrics = {}
    metrics_path = os.path.join(MODEL_DIR, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            metrics = json.load(f)
    return models, scaler, metrics

models, scaler, metrics = load_models()
df = load_dataset()

# --- Model Performance ---
st.subheader("📊 Model Performance")
mc = st.columns(len(metrics))
model_labels = {
    "random_forest": "Random Forest",
    "gradient_boosting": "Gradient Boosting",
    "ridge": "Ridge Regression",
    "neural_network": "Neural Network (MLP)",
}
for col, (name, m) in zip(mc, metrics.items()):
    with col:
        label = model_labels.get(name, name)
        st.metric(label, f"R² = {m['r2']}")
        st.caption(f"MAE: {m['mae']} · RMSE: {m['rmse']}")

st.divider()

# --- Prediction Inputs ---
st.subheader("🧾 Prediction Inputs")
c1, c2, c3 = st.columns(3)
with c1:
    city = st.selectbox("City", df["City"].unique().tolist())
with c2:
    model_choice = st.selectbox("Model", list(model_labels.values()))
    model_key = {v: k for k, v in model_labels.items()}[model_choice]
with c3:
    forecast_days = st.slider("Forecast Days", 1, 14, 5)

st.subheader("🌡️ Environmental Parameters")
p1, p2, p3, p4 = st.columns(4)

city_latest = df[df["City"] == city].sort_values("Date").iloc[-1]

with p1:
    pm25 = st.number_input("PM2.5 (µg/m³)", 0.0, 500.0, float(city_latest["PM2.5"]), 5.0)
    pm10 = st.number_input("PM10 (µg/m³)", 0.0, 600.0, float(city_latest["PM10"]), 10.0)
with p2:
    no2 = st.number_input("NO2 (µg/m³)", 0.0, 400.0, float(city_latest["NO2"]), 5.0)
    so2 = st.number_input("SO2 (µg/m³)", 0.0, 800.0, float(city_latest["SO2"]), 2.0)
with p3:
    co = st.number_input("CO (mg/m³)", 0.0, 50.0, float(city_latest["CO"]), 0.1)
    o3 = st.number_input("O3 (µg/m³)", 0.0, 500.0, float(city_latest["O3"]), 5.0)
with p4:
    temp = st.number_input("Temperature (°C)", 0.0, 50.0, float(city_latest["Temperature"]), 1.0)
    humidity = st.number_input("Humidity (%)", 10.0, 100.0, float(city_latest["Humidity"]), 5.0)

wc1, wc2 = st.columns(2)
with wc1:
    wind = st.number_input("Wind Speed (km/h)", 0.0, 50.0, float(city_latest["Wind_Speed"]), 1.0)
with wc2:
    traffic = st.selectbox("Traffic Level", ["Low", "Medium", "High"], index=1)

st.divider()

# --- Run Prediction ---
if st.button("🚀 Run Prediction", type="primary", use_container_width=True):
    is_nn = model_key == "neural_network"
    if is_nn:
        nn_bundle = models[model_key]
        model = nn_bundle["model"]
        y_scaler = nn_bundle["y_scaler"]
    else:
        model = models[model_key]

    rng = np.random.default_rng(42)
    predictions = []
    base_date = df[df["City"] == city]["Date"].max()

    for day in range(forecast_days):
        day_offset = day + 1
        variation = rng.normal(0, 0.05)
        row = {
            "PM2.5": pm25 * (1 + variation), "PM10": pm10 * (1 + variation),
            "NO2": no2 * (1 + variation * 0.8), "SO2": so2 * (1 + variation * 0.5),
            "CO": co * (1 + variation * 0.6), "O3": o3 * (1 - variation * 0.3),
            "Temperature": temp + rng.normal(0, 1),
            "Humidity": np.clip(humidity + rng.normal(0, 3), 20, 98),
            "Wind_Speed": max(0.5, wind + rng.normal(0, 1.5)),
            "Traffic": traffic,
            "Month": (base_date + timedelta(days=day_offset)).month,
            "DayOfWeek": (base_date + timedelta(days=day_offset)).weekday(),
            "IsWeekend": int((base_date + timedelta(days=day_offset)).weekday() >= 5),
        }
        X = prepare_inference_input(row, scaler)
        raw_pred = model.predict(X)[0]
        if is_nn:
            raw_pred = y_scaler.inverse_transform([[raw_pred]])[0][0]
        pred_aqi = max(0, round(raw_pred))
        predictions.append({
            "Date": base_date + timedelta(days=day_offset),
            "Predicted AQI": pred_aqi,
            "Category": get_aqi_category(pred_aqi),
        })

    forecast_df = pd.DataFrame(predictions)

    # --- Forecast Chart ---
    st.subheader("📈 Forecast Results")

    hist = df[df["City"] == city].sort_values("Date").tail(30)[["Date", "AQI"]].copy()
    hist.rename(columns={"AQI": "Value"}, inplace=True)
    hist["Type"] = "Historical"

    fcast = forecast_df[["Date", "Predicted AQI"]].copy()
    fcast.rename(columns={"Predicted AQI": "Value"}, inplace=True)
    fcast["Type"] = "Forecast"

    combined = pd.concat([hist, fcast])

    fig = px.line(combined, x="Date", y="Value", color="Type",
                  color_discrete_map={"Historical": "#3498db", "Forecast": "#e74c3c"},
                  labels={"Value": "AQI"}, markers=True)
    fig.update_layout(height=400, margin=dict(t=20, b=20), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # --- Forecast Table ---
    st.subheader("📋 Day-by-Day Forecast")
    st.dataframe(forecast_df, use_container_width=True, hide_index=True)

    # --- Summary Metrics ---
    st.subheader("📌 Summary")
    avg_pred = round(forecast_df["Predicted AQI"].mean())
    worst_day = forecast_df.loc[forecast_df["Predicted AQI"].idxmax()]
    best_day = forecast_df.loc[forecast_df["Predicted AQI"].idxmin()]

    sm1, sm2, sm3, sm4 = st.columns(4)
    with sm1:
        st.metric("Average AQI", avg_pred, delta=get_aqi_category(avg_pred), delta_color="off")
    with sm2:
        st.metric("Worst Day", f"{worst_day['Predicted AQI']} AQI",
                  delta=worst_day["Date"].strftime("%b %d"), delta_color="off")
    with sm3:
        st.metric("Best Day", f"{best_day['Predicted AQI']} AQI",
                  delta=best_day["Date"].strftime("%b %d"), delta_color="off")
    with sm4:
        st.metric("Model Used", model_choice)

    # --- Feature Importance ---
    if model_key in metrics and metrics[model_key].get("feature_importance"):
        st.subheader("🔑 Feature Importance")
        imp = metrics[model_key]["feature_importance"]
        imp_df = pd.DataFrame({"Feature": imp.keys(), "Importance": imp.values()})
        imp_df = imp_df.sort_values("Importance", ascending=True)

        fig_imp = px.bar(imp_df, x="Importance", y="Feature", orientation="h",
                         color="Importance", color_continuous_scale="YlOrRd")
        fig_imp.update_layout(height=450, margin=dict(t=20, b=20), showlegend=False)
        st.plotly_chart(fig_imp, use_container_width=True)

    # --- Sub-Index Breakdown ---
    st.subheader("🔬 Pollutant Sub-Index Breakdown")
    sub_indices = {
        "PM2.5": compute_sub_index("PM2.5", pm25),
        "PM10": compute_sub_index("PM10", pm10),
        "NO2": compute_sub_index("NO2", no2),
        "SO2": compute_sub_index("SO2", so2),
        "CO": compute_sub_index("CO", co),
        "O3": compute_sub_index("O3", o3),
    }
    si_df = pd.DataFrame({"Pollutant": sub_indices.keys(), "Sub-Index": sub_indices.values()})
    si_df = si_df.sort_values("Sub-Index", ascending=False)

    color_map = {"PM2.5": "#e74c3c", "PM10": "#e67e22", "NO2": "#f39c12", "SO2": "#9b59b6", "CO": "#3498db", "O3": "#2ecc71"}
    fig_si = px.bar(si_df, x="Pollutant", y="Sub-Index", color="Pollutant",
                    color_discrete_map=color_map, text="Sub-Index")
    fig_si.update_traces(textposition="outside")
    fig_si.update_layout(height=350, margin=dict(t=20, b=20), showlegend=False)
    st.plotly_chart(fig_si, use_container_width=True)

    # --- Health Impact of Prediction ---
    st.divider()
    st.subheader("🧠 Predicted Health Impact")

    risk_score, risk_level = compute_health_risk_score(avg_pred)
    activities = get_activity_recommendations(avg_pred)

    hi1, hi2 = st.columns(2)
    with hi1:
        risk_colors = {"Low": "success", "Moderate": "info", "High": "warning", "Very High": "error", "Critical": "error"}
        st.metric("Health Risk Score", f"{risk_score} / 100")
        st.metric("Risk Level", risk_level)
        getattr(st, risk_colors[risk_level])(
            f"Based on the average predicted AQI of **{avg_pred}**, "
            f"the health risk level is **{risk_level}** for the forecast period."
        )

    with hi2:
        safe_acts = [a for a in activities if a["safety"] == "Safe"]
        caution_acts = [a for a in activities if a["safety"] == "Caution"]
        avoid_acts = [a for a in activities if a["safety"] == "Avoid"]

        if safe_acts:
            st.success("**Safe Activities:** " + ", ".join(f"{a['icon']} {a['activity']}" for a in safe_acts))
        if caution_acts:
            st.warning("**Use Caution:** " + ", ".join(f"{a['icon']} {a['activity']}" for a in caution_acts))
        if avoid_acts:
            st.error("**Avoid:** " + ", ".join(f"{a['icon']} {a['activity']}" for a in avoid_acts))
