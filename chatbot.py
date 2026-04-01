"""
AQI Assistant Chatbot Engine
Rule-based NLP chatbot that uses the app's dataset and health intelligence
to answer user queries about air quality, health risks, and precautions.
"""
import re
from typing import Optional
import pandas as pd

from utils.data import load_dataset, get_aqi_category, CITIES, compute_sub_index
from utils.health_intelligence import (
    compute_health_risk_score,
    compute_safe_outdoor_hours,
    get_activity_recommendations,
    estimate_exposure_impact,
)
from utils.alerts import generate_health_alert, HEALTH_RISK_LEVEL

_df: Optional[pd.DataFrame] = None


def _get_df() -> pd.DataFrame:
    global _df
    if _df is None:
        _df = load_dataset()
    return _df


def _get_latest() -> pd.DataFrame:
    df = _get_df()
    return df.sort_values("Date").groupby("City").last().reset_index()


def _find_city(text: str) -> Optional[str]:
    text_lower = text.lower()
    for city in CITIES:
        if city.lower() in text_lower:
            return city
    # Fuzzy short names
    aliases = {
        "bangalore": "Bengaluru", "vizag": "Visakhapatnam",
        "trivandrum": "Thiruvananthapuram", "tvm": "Thiruvananthapuram",
        "hyd": "Hyderabad", "blr": "Bengaluru", "chn": "Chennai",
        "mum": "Mumbai", "del": "Delhi", "cal": "Kolkata",
        "ccj": "Chandigarh",
    }
    for alias, city in aliases.items():
        if alias in text_lower:
            return city
    return None


def _find_pollutant(text: str) -> Optional[str]:
    text_lower = text.lower()
    pollutant_map = {
        "pm2.5": "PM2.5", "pm 2.5": "PM2.5", "pm25": "PM2.5",
        "pm10": "PM10", "pm 10": "PM10",
        "no2": "NO2", "nitrogen dioxide": "NO2",
        "so2": "SO2", "sulfur dioxide": "SO2", "sulphur dioxide": "SO2",
        "co ": "CO", "carbon monoxide": "CO",
        "o3": "O3", "ozone": "O3",
    }
    for key, val in pollutant_map.items():
        if key in text_lower:
            return val
    return None


def _detect_intent(text: str) -> str:
    t = text.lower().strip()

    # Check compare/data intents before greetings to avoid "hi" in city names like "Delhi"
    if any(w in t for w in ["compare", "versus", "vs", "difference between", "better"]):
        return "compare"
    if any(w in t for w in ["worst", "most polluted", "highest aqi", "dirtiest"]):
        return "worst_city"
    if any(w in t for w in ["best", "cleanest", "lowest aqi", "least polluted"]):
        return "best_city"
    if any(w in t for w in ["rank", "ranking", "all cities", "list cities", "overview"]):
        return "ranking"

    if any(w in t for w in ["safe to", "can i go", "should i go", "outdoor", "jogging", "running", "cycling", "exercise", "walk", "sport"]):
        return "activity_safety"
    if any(w in t for w in ["precaution", "protect", "what should i do", "stay safe", "recommendation", "advice"]):
        return "precautions"
    if any(w in t for w in ["risk", "danger", "health score", "how dangerous"]):
        return "risk_score"
    if any(w in t for w in ["emergency", "severe", "hazardous", "critical"]):
        return "emergency"
    if any(w in t for w in ["mask", "n95", "purifier", "air filter"]):
        return "protective_gear"

    # Greetings — checked after city/data intents to avoid false matches
    words = t.split()
    first = re.sub(r"[^a-z]", "", words[0]) if words else ""
    if first in ("hello", "hey", "hi") or any(w in t for w in ["good morning", "good evening"]):
        return "greeting"
    if any(w in t for w in ["help", "what can you", "what do you", "how to use", "features"]):
        return "help"
    if any(w in t for w in ["thank", "thanks", "bye", "goodbye"]):
        return "goodbye"

    if any(w in t for w in ["what is aqi", "what does aqi", "aqi mean", "explain aqi", "about aqi"]):
        return "explain_aqi"
    if any(w in t for w in ["what is pm", "what does pm", "explain pm", "about pm"]):
        return "explain_pollutant"
    if any(w in t for w in ["category", "categories", "good moderate poor"]):
        return "explain_categories"
    if _find_pollutant(t):
        return "pollutant_info"

    if _find_city(t) and any(w in t for w in ["aqi", "quality", "pollution", "how is", "status", "level"]):
        return "city_aqi"
    if _find_city(t):
        return "city_aqi"

    return "general"


def respond(user_message: str) -> str:
    intent = _detect_intent(user_message)
    city = _find_city(user_message)
    latest = _get_latest()

    if intent == "greeting":
        return (
            "Hello! I'm your **AQI Assistant**. I can help you with:\n\n"
            "- Current air quality in any city\n"
            "- Health risk assessments\n"
            "- Safe outdoor activity advice\n"
            "- City comparisons\n"
            "- Pollution & precaution information\n\n"
            "Just ask me anything about air quality!"
        )

    if intent == "help":
        return (
            "Here's what I can help you with:\n\n"
            "**City AQI:** *\"What's the AQI in Delhi?\"*\n"
            "**Safety:** *\"Is it safe to go jogging?\"*\n"
            "**Precautions:** *\"What precautions should I take in Mumbai?\"*\n"
            "**Risk Score:** *\"How dangerous is the air in Patna?\"*\n"
            "**Compare:** *\"Compare Delhi and Bengaluru\"*\n"
            "**Rankings:** *\"Which city has the worst air?\"*\n"
            "**Learn:** *\"What is PM2.5?\"* or *\"Explain AQI categories\"*\n"
            "**Gear:** *\"When should I wear a mask?\"*\n\n"
            f"I have data for **{len(CITIES)} cities** across India."
        )

    if intent == "goodbye":
        return "Goodbye! Stay safe and breathe clean. Feel free to come back anytime."

    if intent == "city_aqi":
        if not city:
            return f"Which city would you like to know about? I have data for: {', '.join(CITIES)}"
        row = latest[latest["City"] == city].iloc[0]
        aqi = int(row["AQI"])
        cat = row["AQI_Category"]
        icon = {"Good": "🟢", "Moderate": "🟡", "Poor": "🟠", "Very Poor": "🔴", "Severe": "☠️"}.get(cat, "⚪")
        alert = generate_health_alert(aqi)

        response = (
            f"**{city}** — {icon} **AQI {aqi}** ({cat})\n\n"
            f"| Pollutant | Value |\n|---|---|\n"
            f"| PM2.5 | {row['PM2.5']} µg/m³ |\n"
            f"| PM10 | {row['PM10']} µg/m³ |\n"
            f"| NO2 | {row['NO2']} µg/m³ |\n"
            f"| SO2 | {row['SO2']} µg/m³ |\n"
            f"| CO | {row['CO']} mg/m³ |\n"
            f"| O3 | {row['O3']} µg/m³ |\n\n"
            f"**Dominant Pollutant:** {row['Dominant_Pollutant']}\n\n"
            f"**Health Risk:** {alert['Risk Level']}\n\n"
        )
        for rec in alert["Recommendations"]:
            response += f"- {rec}\n"
        return response

    if intent == "activity_safety":
        target_city = city
        if not target_city:
            target_city = "Delhi"
        row = latest[latest["City"] == target_city].iloc[0]
        aqi = int(row["AQI"])
        activities = get_activity_recommendations(aqi)
        safe_hours = compute_safe_outdoor_hours(aqi)

        response = f"**Activity Safety for {target_city}** (AQI {aqi}):\n\n"
        for act in activities:
            response += f"- {act['indicator']} **{act['activity']}**: {act['safety']}\n"

        response += f"\n**Safe outdoor durations:**\n"
        for activity, hours in safe_hours.items():
            label = f"{hours}h" if hours > 0 else "Avoid"
            response += f"- {activity}: {label}\n"
        return response

    if intent == "precautions":
        target_city = city or "Delhi"
        row = latest[latest["City"] == target_city].iloc[0]
        aqi = int(row["AQI"])
        cat = row["AQI_Category"]
        alert = generate_health_alert(aqi)

        precautions = {
            "Good": ["No special precautions needed", "Enjoy outdoor activities freely"],
            "Moderate": ["Sensitive individuals should limit prolonged outdoor exertion", "Keep quick-relief inhaler if asthmatic", "Stay hydrated"],
            "Poor": ["Wear a mask outdoors", "Avoid jogging or cycling", "Keep windows closed", "Use air purifier if available", "Children and elderly should stay indoors"],
            "Very Poor": ["Use N95 masks for any outdoor exposure", "Seal windows and doors", "Run air purifiers continuously", "Limit outdoor time to under 15 minutes", "Monitor for breathing difficulty"],
            "Severe": ["Stay indoors — do NOT go outside", "Seal all openings in your home", "Run air purifier at maximum", "Seek medical help if breathing issues occur", "Keep emergency numbers ready"],
        }

        response = f"**Precautions for {target_city}** (AQI {aqi} — {cat}):\n\n"
        for p in precautions.get(cat, []):
            response += f"- {p}\n"
        return response

    if intent == "risk_score":
        target_city = city or "Delhi"
        row = latest[latest["City"] == target_city].iloc[0]
        aqi = int(row["AQI"])
        score, level = compute_health_risk_score(aqi)
        exposure = estimate_exposure_impact(aqi, 2.0)

        return (
            f"**Health Risk Assessment for {target_city}:**\n\n"
            f"- **AQI:** {aqi} ({row['AQI_Category']})\n"
            f"- **Risk Score:** {score}/100\n"
            f"- **Risk Level:** {level}\n"
            f"- **2-hour outdoor exposure:** ~{exposure['inhaled_pm25_ug']} µg PM2.5 inhaled ({exposure['impact_level']} impact)\n\n"
            f"{'⚠️ Take protective measures immediately.' if score > 60 else '✅ Manageable with basic precautions.' if score > 30 else '✅ Low risk — normal activities are safe.'}"
        )

    if intent == "compare":
        cities_found = []
        for c in CITIES:
            if c.lower() in user_message.lower():
                cities_found.append(c)
        if len(cities_found) < 2:
            return "Please mention two cities to compare, e.g., *\"Compare Delhi and Bengaluru\"*"

        c1, c2 = cities_found[0], cities_found[1]
        r1 = latest[latest["City"] == c1].iloc[0]
        r2 = latest[latest["City"] == c2].iloc[0]

        return (
            f"**{c1} vs {c2}:**\n\n"
            f"| Metric | {c1} | {c2} |\n|---|---|---|\n"
            f"| AQI | {int(r1['AQI'])} | {int(r2['AQI'])} |\n"
            f"| Category | {r1['AQI_Category']} | {r2['AQI_Category']} |\n"
            f"| PM2.5 | {r1['PM2.5']} | {r2['PM2.5']} |\n"
            f"| PM10 | {r1['PM10']} | {r2['PM10']} |\n"
            f"| Dominant | {r1['Dominant_Pollutant']} | {r2['Dominant_Pollutant']} |\n"
            f"| Temperature | {r1['Temperature']}°C | {r2['Temperature']}°C |\n\n"
            f"{'**' + c1 + '** has worse air quality.' if r1['AQI'] > r2['AQI'] else '**' + c2 + '** has worse air quality.' if r2['AQI'] > r1['AQI'] else 'Both cities have similar air quality.'}"
        )

    if intent == "worst_city":
        worst = latest.sort_values("AQI", ascending=False).iloc[0]
        top5 = latest.sort_values("AQI", ascending=False).head(5)
        response = f"**Most polluted city:** {worst['City']} (AQI {int(worst['AQI'])} — {worst['AQI_Category']})\n\n**Top 5 most polluted:**\n"
        for i, (_, r) in enumerate(top5.iterrows(), 1):
            response += f"{i}. {r['City']} — AQI {int(r['AQI'])} ({r['AQI_Category']})\n"
        return response

    if intent == "best_city":
        best = latest.sort_values("AQI").iloc[0]
        top5 = latest.sort_values("AQI").head(5)
        response = f"**Cleanest city:** {best['City']} (AQI {int(best['AQI'])} — {best['AQI_Category']})\n\n**Top 5 cleanest:**\n"
        for i, (_, r) in enumerate(top5.iterrows(), 1):
            response += f"{i}. {r['City']} — AQI {int(r['AQI'])} ({r['AQI_Category']})\n"
        return response

    if intent == "ranking":
        ranked = latest.sort_values("AQI", ascending=False)
        response = "**City AQI Rankings** (worst → best):\n\n"
        for i, (_, r) in enumerate(ranked.iterrows(), 1):
            icon = {"Good": "🟢", "Moderate": "🟡", "Poor": "🟠", "Very Poor": "🔴", "Severe": "☠️"}.get(r["AQI_Category"], "⚪")
            response += f"{i}. {icon} **{r['City']}** — AQI {int(r['AQI'])} ({r['AQI_Category']})\n"
        return response

    if intent == "explain_aqi":
        return (
            "**Air Quality Index (AQI)** is a standardized indicator for reporting air quality.\n\n"
            "It's calculated from concentrations of 6 pollutants: PM2.5, PM10, NO2, SO2, CO, and O3.\n\n"
            "Each pollutant gets a **sub-index** using standard breakpoints. The overall AQI equals the **highest sub-index** among all pollutants.\n\n"
            "| AQI Range | Category | Health Impact |\n|---|---|---|\n"
            "| 0–50 | 🟢 Good | Minimal risk |\n"
            "| 51–100 | 🟡 Moderate | Sensitive groups cautious |\n"
            "| 101–200 | 🟠 Poor | Breathing discomfort |\n"
            "| 201–300 | 🔴 Very Poor | Health warnings |\n"
            "| 301–500 | ☠️ Severe | Serious health effects |\n"
        )

    if intent == "explain_categories":
        return (
            "**AQI Categories:**\n\n"
            "🟢 **Good (0–50):** Air quality is excellent. Safe for everyone.\n\n"
            "🟡 **Moderate (51–100):** Acceptable. Sensitive people should be slightly cautious.\n\n"
            "🟠 **Poor (101–200):** Unhealthy for sensitive groups. Avoid heavy exercise.\n\n"
            "🔴 **Very Poor (201–300):** Everyone affected. Limit outdoor exposure. Use N95 masks.\n\n"
            "☠️ **Severe (301–500):** Health emergency. Stay indoors. Seek medical help if symptomatic."
        )

    if intent == "explain_pollutant" or intent == "pollutant_info":
        pollutant = _find_pollutant(user_message)
        info = {
            "PM2.5": ("**PM2.5** — Fine Particulate Matter (≤2.5 µm)", "The most dangerous air pollutant. These tiny particles penetrate deep into lungs and enter the bloodstream. Major sources: vehicle exhaust, industrial emissions, crop burning. Safe limit: ≤30 µg/m³ (24-hr avg)."),
            "PM10": ("**PM10** — Coarse Particulate Matter (≤10 µm)", "Larger particles from dust, construction, and road traffic. Can irritate eyes, nose, and throat. Safe limit: ≤50 µg/m³ (24-hr avg)."),
            "NO2": ("**NO2** — Nitrogen Dioxide", "Reddish-brown gas from vehicle engines and power plants. Causes airway inflammation and worsens asthma. Safe limit: ≤40 µg/m³ (annual avg)."),
            "SO2": ("**SO2** — Sulfur Dioxide", "Produced by burning fossil fuels (coal, oil). Causes breathing difficulty and aggravates existing respiratory diseases. Safe limit: ≤40 µg/m³ (24-hr avg)."),
            "CO": ("**CO** — Carbon Monoxide", "Odorless, colorless gas from incomplete combustion. Reduces blood's oxygen-carrying capacity. Dangerous in enclosed spaces. Safe limit: ≤1 mg/m³ (8-hr avg)."),
            "O3": ("**O3** — Ground-level Ozone", "Formed by sunlight reacting with vehicle/industrial emissions. Causes chest pain, coughing, and throat irritation. Worse on hot, sunny days. Safe limit: ≤50 µg/m³ (8-hr avg)."),
        }
        if pollutant and pollutant in info:
            title, desc = info[pollutant]
            return f"{title}\n\n{desc}"
        return "Which pollutant would you like to know about? I can explain: PM2.5, PM10, NO2, SO2, CO, or O3."

    if intent == "emergency":
        severe_cities = latest[latest["AQI"] >= 300]
        if len(severe_cities) == 0:
            very_poor = latest[latest["AQI"] >= 200].sort_values("AQI", ascending=False)
            if len(very_poor) > 0:
                response = "No cities currently at **Severe** level, but these are **Very Poor**:\n\n"
                for _, r in very_poor.iterrows():
                    response += f"- 🔴 {r['City']} — AQI {int(r['AQI'])}\n"
                response += "\n**Precautions:** Use N95 masks, limit outdoor time, run air purifiers."
                return response
            return "✅ No cities are currently at emergency pollution levels."
        response = "🚨 **EMERGENCY — Severe Pollution:**\n\n"
        for _, r in severe_cities.iterrows():
            response += f"- ☠️ {r['City']} — AQI {int(r['AQI'])}\n"
        response += "\n**Immediate actions:** Stay indoors, seal windows, run air purifier, avoid all outdoor activity, seek medical help if symptomatic."
        return response

    if intent == "protective_gear":
        return (
            "**When to use protective gear:**\n\n"
            "| AQI Level | Mask Type | Air Purifier |\n|---|---|---|\n"
            "| 0–100 | Not needed | Optional |\n"
            "| 101–200 | Surgical mask outdoors | Recommended |\n"
            "| 201–300 | **N95/KN95 mandatory** | **Run continuously** |\n"
            "| 301+ | **N95 even for short trips** | **Maximum setting, sealed room** |\n\n"
            "**Tips:**\n"
            "- Ensure N95 mask fits snugly with no gaps\n"
            "- Replace masks every 8 hours of use\n"
            "- HEPA filter purifiers are most effective for PM2.5\n"
            "- Place purifier in the room where you spend the most time"
        )

    # Fallback
    return (
        "I'm not sure I understood that. Here are some things you can ask me:\n\n"
        "- *\"What's the AQI in Chennai?\"*\n"
        "- *\"Is it safe to go jogging in Delhi?\"*\n"
        "- *\"Which city has the cleanest air?\"*\n"
        "- *\"Compare Mumbai and Pune\"*\n"
        "- *\"What is PM2.5?\"*\n"
        "- *\"What precautions should I take?\"*\n\n"
        f"I have data for {len(CITIES)} cities: {', '.join(CITIES[:7])}..."
    )
