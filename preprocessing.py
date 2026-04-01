import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder

FEATURE_COLS = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3", "Temperature", "Humidity", "Wind_Speed", "Traffic_Encoded", "Month", "DayOfWeek", "IsWeekend"]
TARGET_COL = "AQI"


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Month"] = df["Date"].dt.month
    df["DayOfWeek"] = df["Date"].dt.dayofweek
    df["IsWeekend"] = (df["DayOfWeek"] >= 5).astype(int)

    le = LabelEncoder()
    df["Traffic_Encoded"] = le.fit_transform(df["Traffic"])

    df["PM_Ratio"] = df["PM2.5"] / df["PM10"].replace(0, 1)
    df["Pollution_Index"] = (df["PM2.5"] + df["PM10"] + df["NO2"] + df["SO2"]) / 4

    return df


def prepare_training_data(df: pd.DataFrame):
    df = engineer_features(df)
    X = df[FEATURE_COLS].copy()
    y = df[TARGET_COL].copy()

    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=FEATURE_COLS, index=X.index)

    return X_scaled, y, scaler


def prepare_inference_input(row: dict, scaler) -> pd.DataFrame:
    traffic_map = {"Low": 0, "Medium": 1, "High": 2}
    features = {
        "PM2.5": row.get("PM2.5", 50),
        "PM10": row.get("PM10", 100),
        "NO2": row.get("NO2", 30),
        "SO2": row.get("SO2", 10),
        "CO": row.get("CO", 1.0),
        "O3": row.get("O3", 35),
        "Temperature": row.get("Temperature", 30),
        "Humidity": row.get("Humidity", 60),
        "Wind_Speed": row.get("Wind_Speed", 8),
        "Traffic_Encoded": traffic_map.get(row.get("Traffic", "Medium"), 1),
        "Month": row.get("Month", 1),
        "DayOfWeek": row.get("DayOfWeek", 0),
        "IsWeekend": row.get("IsWeekend", 0),
    }
    X = pd.DataFrame([features])
    X_scaled = pd.DataFrame(scaler.transform(X), columns=FEATURE_COLS)
    return X_scaled
