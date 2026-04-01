import os
import numpy as np
import pandas as pd
from typing import Tuple

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATASET_PATH = os.path.join(DATA_DIR, "aqi_dataset.csv")

CITIES = [
    "Delhi", "Mumbai", "Chennai", "Bengaluru", "Hyderabad", "Kolkata",
    "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Patna", "Chandigarh",
    "Visakhapatnam", "Thiruvananthapuram",
]

CITY_PROFILES = {
    "Delhi":              {"pm25_base": 140, "pm10_base": 220, "no2_base": 55, "so2_base": 18, "co_base": 1.8, "o3_base": 45, "winter_mult": 2.2},
    "Patna":              {"pm25_base": 130, "pm10_base": 210, "no2_base": 50, "so2_base": 16, "co_base": 1.7, "o3_base": 42, "winter_mult": 2.1},
    "Lucknow":            {"pm25_base": 120, "pm10_base": 195, "no2_base": 48, "so2_base": 15, "co_base": 1.5, "o3_base": 40, "winter_mult": 2.0},
    "Kolkata":            {"pm25_base": 85,  "pm10_base": 150, "no2_base": 40, "so2_base": 14, "co_base": 1.3, "o3_base": 40, "winter_mult": 1.7},
    "Ahmedabad":          {"pm25_base": 78,  "pm10_base": 140, "no2_base": 42, "so2_base": 15, "co_base": 1.2, "o3_base": 42, "winter_mult": 1.6},
    "Jaipur":             {"pm25_base": 75,  "pm10_base": 160, "no2_base": 38, "so2_base": 13, "co_base": 1.2, "o3_base": 38, "winter_mult": 1.7},
    "Mumbai":             {"pm25_base": 65,  "pm10_base": 120, "no2_base": 38, "so2_base": 12, "co_base": 1.1, "o3_base": 38, "winter_mult": 1.3},
    "Pune":               {"pm25_base": 55,  "pm10_base": 100, "no2_base": 30, "so2_base": 10, "co_base": 0.9, "o3_base": 34, "winter_mult": 1.3},
    "Hyderabad":          {"pm25_base": 58,  "pm10_base": 110, "no2_base": 32, "so2_base": 11, "co_base": 1.0, "o3_base": 36, "winter_mult": 1.4},
    "Chandigarh":         {"pm25_base": 62,  "pm10_base": 115, "no2_base": 35, "so2_base": 12, "co_base": 1.0, "o3_base": 35, "winter_mult": 1.8},
    "Chennai":            {"pm25_base": 50,  "pm10_base": 95,  "no2_base": 28, "so2_base": 10, "co_base": 0.9, "o3_base": 35, "winter_mult": 1.2},
    "Visakhapatnam":      {"pm25_base": 45,  "pm10_base": 85,  "no2_base": 26, "so2_base": 9,  "co_base": 0.8, "o3_base": 32, "winter_mult": 1.2},
    "Bengaluru":          {"pm25_base": 42,  "pm10_base": 80,  "no2_base": 25, "so2_base": 8,  "co_base": 0.7, "o3_base": 30, "winter_mult": 1.1},
    "Thiruvananthapuram": {"pm25_base": 30,  "pm10_base": 60,  "no2_base": 18, "so2_base": 6,  "co_base": 0.5, "o3_base": 25, "winter_mult": 1.0},
}

# Indian NAQI breakpoints: (concentration_low, concentration_high) -> (index_low, index_high)
AQI_BREAKPOINTS = {
    "PM2.5": [(0, 30, 0, 50), (31, 60, 51, 100), (61, 90, 101, 200), (91, 120, 201, 300), (121, 250, 301, 400), (251, 500, 401, 500)],
    "PM10":  [(0, 50, 0, 50), (51, 100, 51, 100), (101, 250, 101, 200), (251, 350, 201, 300), (351, 430, 301, 400), (431, 600, 401, 500)],
    "NO2":   [(0, 40, 0, 50), (41, 80, 51, 100), (81, 180, 101, 200), (181, 280, 201, 300), (281, 400, 301, 400), (401, 800, 401, 500)],
    "SO2":   [(0, 40, 0, 50), (41, 80, 51, 100), (81, 380, 101, 200), (381, 800, 201, 300), (801, 1600, 301, 400), (1601, 2400, 401, 500)],
    "CO":    [(0, 1, 0, 50), (1.1, 2, 51, 100), (2.1, 10, 101, 200), (10.1, 17, 201, 300), (17.1, 34, 301, 400), (34.1, 50, 401, 500)],
    "O3":    [(0, 50, 0, 50), (51, 100, 51, 100), (101, 168, 101, 200), (169, 208, 201, 300), (209, 748, 301, 400), (749, 1000, 401, 500)],
}


def compute_sub_index(pollutant: str, concentration: float) -> int:
    breakpoints = AQI_BREAKPOINTS.get(pollutant, [])
    for c_lo, c_hi, i_lo, i_hi in breakpoints:
        if c_lo <= concentration <= c_hi:
            return round(((i_hi - i_lo) / (c_hi - c_lo)) * (concentration - c_lo) + i_lo)
    return 500


def compute_aqi(row: pd.Series) -> Tuple[int, str]:
    sub_indices = {
        "PM2.5": compute_sub_index("PM2.5", row["PM2.5"]),
        "PM10":  compute_sub_index("PM10", row["PM10"]),
        "NO2":   compute_sub_index("NO2", row["NO2"]),
        "SO2":   compute_sub_index("SO2", row["SO2"]),
        "CO":    compute_sub_index("CO", row["CO"]),
        "O3":    compute_sub_index("O3", row["O3"]),
    }
    aqi = max(sub_indices.values())
    dominant = max(sub_indices, key=sub_indices.get)
    return aqi, dominant


def get_aqi_category(aqi: int) -> str:
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 200:
        return "Poor"
    elif aqi <= 300:
        return "Very Poor"
    else:
        return "Severe"


def _seasonal_factor(month: int, winter_mult: float) -> float:
    """Higher in winter (Nov-Feb), lower in monsoon (Jul-Sep)."""
    seasonal = {
        1: winter_mult, 2: winter_mult * 0.9,
        3: 1.1, 4: 0.9, 5: 0.85, 6: 0.75,
        7: 0.6, 8: 0.55, 9: 0.65,
        10: 1.0, 11: winter_mult * 0.85, 12: winter_mult * 0.95,
    }
    return seasonal.get(month, 1.0)


def generate_city_data(city: str, start_date: str = "2022-01-01", n_days: int = 730) -> pd.DataFrame:
    rng = np.random.default_rng(hash(city) % (2**31))
    profile = CITY_PROFILES[city]
    dates = pd.date_range(start=start_date, periods=n_days, freq="D")

    rows = []
    for date in dates:
        month = date.month
        dow = date.dayofweek
        sf = _seasonal_factor(month, profile["winter_mult"])
        weekday_boost = 1.08 if dow < 5 else 0.88

        temp = rng.normal(loc=32 - abs(month - 6) * 1.5, scale=2.5)
        humidity = rng.normal(loc=55 + (15 if month in (7, 8, 9) else 0), scale=10)
        wind = max(0.5, rng.normal(loc=8 - sf * 1.5, scale=3))
        wind_factor = max(0.4, 1.0 - (wind - 5) * 0.04)

        pm25 = max(5, rng.normal(loc=profile["pm25_base"] * sf * weekday_boost * wind_factor, scale=profile["pm25_base"] * 0.2))
        pm10 = max(10, rng.normal(loc=profile["pm10_base"] * sf * weekday_boost * wind_factor, scale=profile["pm10_base"] * 0.2))
        no2 = max(2, rng.normal(loc=profile["no2_base"] * sf * weekday_boost, scale=profile["no2_base"] * 0.25))
        so2 = max(1, rng.normal(loc=profile["so2_base"] * sf, scale=profile["so2_base"] * 0.3))
        co = max(0.1, rng.normal(loc=profile["co_base"] * sf * weekday_boost, scale=profile["co_base"] * 0.25))
        o3 = max(5, rng.normal(loc=profile["o3_base"] * (2.0 - sf * 0.5), scale=profile["o3_base"] * 0.2))

        traffic = rng.choice(["Low", "Medium", "High"], p=[0.15, 0.45, 0.4] if dow < 5 else [0.4, 0.4, 0.2])

        rows.append({
            "Date": date, "City": city,
            "PM2.5": round(pm25, 1), "PM10": round(pm10, 1),
            "NO2": round(no2, 1), "SO2": round(so2, 1),
            "CO": round(co, 2), "O3": round(o3, 1),
            "Temperature": round(temp, 1), "Humidity": round(np.clip(humidity, 20, 98), 1),
            "Wind_Speed": round(wind, 1), "Traffic": traffic,
        })

    df = pd.DataFrame(rows)
    aqi_results = df.apply(compute_aqi, axis=1)
    df["AQI"] = [r[0] for r in aqi_results]
    df["Dominant_Pollutant"] = [r[1] for r in aqi_results]
    df["AQI_Category"] = df["AQI"].apply(get_aqi_category)
    return df


def generate_full_dataset() -> pd.DataFrame:
    frames = [generate_city_data(city) for city in CITIES]
    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values(["Date", "City"]).reset_index(drop=True)
    return df


def load_dataset() -> pd.DataFrame:
    if os.path.exists(DATASET_PATH):
        df = pd.read_csv(DATASET_PATH, parse_dates=["Date"])
        return df
    df = generate_full_dataset()
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(DATASET_PATH, index=False)
    return df
