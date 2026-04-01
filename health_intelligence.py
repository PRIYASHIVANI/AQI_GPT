"""
Health Intelligence Engine — converts AQI values into
actionable health metrics: risk scores, safe outdoor hours,
activity-specific advice, and exposure impact estimation.
"""
from typing import Dict, List, Tuple


def compute_health_risk_score(aqi: int, age: int = 30,
                               respiratory: bool = False,
                               heart: bool = False,
                               pregnant: bool = False) -> Tuple[float, str]:
    """
    Compute a 0-100 health risk score based on AQI and personal profile.
    Higher = more dangerous.
    """
    if aqi <= 50:
        base = aqi * 0.3
    elif aqi <= 100:
        base = 15 + (aqi - 50) * 0.4
    elif aqi <= 200:
        base = 35 + (aqi - 100) * 0.3
    elif aqi <= 300:
        base = 65 + (aqi - 200) * 0.2
    else:
        base = 85 + min(15, (aqi - 300) * 0.075)

    multiplier = 1.0
    if age < 12:
        multiplier += 0.15
    elif age > 60:
        multiplier += 0.20
    if respiratory:
        multiplier += 0.25
    if heart:
        multiplier += 0.15
    if pregnant:
        multiplier += 0.10

    score = min(100, base * multiplier)

    if score <= 20:
        level = "Low"
    elif score <= 40:
        level = "Moderate"
    elif score <= 60:
        level = "High"
    elif score <= 80:
        level = "Very High"
    else:
        level = "Critical"

    return round(score, 1), level


def compute_safe_outdoor_hours(aqi: int) -> Dict[str, float]:
    """
    Estimate safe outdoor duration (hours) for different activity levels.
    Based on exposure guidelines.
    """
    if aqi <= 50:
        return {"Light Walk": 8, "Jogging": 4, "Cycling": 4, "Outdoor Sports": 3, "Commuting": 8}
    elif aqi <= 100:
        return {"Light Walk": 4, "Jogging": 2, "Cycling": 2, "Outdoor Sports": 1.5, "Commuting": 6}
    elif aqi <= 200:
        return {"Light Walk": 2, "Jogging": 0.5, "Cycling": 0.5, "Outdoor Sports": 0, "Commuting": 3}
    elif aqi <= 300:
        return {"Light Walk": 0.5, "Jogging": 0, "Cycling": 0, "Outdoor Sports": 0, "Commuting": 1}
    else:
        return {"Light Walk": 0, "Jogging": 0, "Cycling": 0, "Outdoor Sports": 0, "Commuting": 0.5}


def get_activity_recommendations(aqi: int) -> List[Dict]:
    """
    Activity-specific recommendations with safety ratings.
    """
    activities = [
        {"activity": "Morning Walk", "icon": "🚶"},
        {"activity": "Jogging / Running", "icon": "🏃"},
        {"activity": "Cycling", "icon": "🚴"},
        {"activity": "Outdoor Sports", "icon": "⚽"},
        {"activity": "Children Outdoor Play", "icon": "🧒"},
        {"activity": "Commuting (Open Vehicle)", "icon": "🛵"},
        {"activity": "Commuting (Closed Vehicle)", "icon": "🚗"},
        {"activity": "Outdoor Work", "icon": "👷"},
    ]

    if aqi <= 50:
        safety = ["Safe", "Safe", "Safe", "Safe", "Safe", "Safe", "Safe", "Safe"]
        colors = ["🟢"] * 8
    elif aqi <= 100:
        safety = ["Safe", "Caution", "Caution", "Caution", "Safe", "Caution", "Safe", "Caution"]
        colors = ["🟢", "🟡", "🟡", "🟡", "🟢", "🟡", "🟢", "🟡"]
    elif aqi <= 200:
        safety = ["Caution", "Avoid", "Avoid", "Avoid", "Avoid", "Avoid", "Caution", "Reduce"]
        colors = ["🟡", "🔴", "🔴", "🔴", "🔴", "🔴", "🟡", "🟠"]
    elif aqi <= 300:
        safety = ["Avoid", "Avoid", "Avoid", "Avoid", "Avoid", "Avoid", "Caution", "Avoid"]
        colors = ["🔴", "🔴", "🔴", "🔴", "🔴", "🔴", "🟡", "🔴"]
    else:
        safety = ["Avoid", "Avoid", "Avoid", "Avoid", "Avoid", "Avoid", "Reduce", "Avoid"]
        colors = ["🔴"] * 6 + ["🟠", "🔴"]

    for i, act in enumerate(activities):
        act["safety"] = safety[i]
        act["indicator"] = colors[i]

    return activities


def estimate_exposure_impact(aqi: int, hours_outdoor: float) -> Dict:
    """
    Estimate health impact of outdoor exposure at given AQI for given hours.
    """
    if aqi <= 50:
        pm25_equiv = aqi * 0.6
    elif aqi <= 100:
        pm25_equiv = 30 + (aqi - 50) * 0.6
    elif aqi <= 200:
        pm25_equiv = 60 + (aqi - 100) * 0.3
    else:
        pm25_equiv = 90 + (aqi - 200) * 0.5

    # Rough estimate of inhaled PM2.5 (µg) assuming 15 L/min breathing rate
    breathing_rate_m3_per_hour = 0.9  # average adult at light activity
    inhaled_pm25 = pm25_equiv * breathing_rate_m3_per_hour * hours_outdoor

    if inhaled_pm25 < 20:
        impact_level = "Negligible"
        color = "success"
    elif inhaled_pm25 < 50:
        impact_level = "Low"
        color = "info"
    elif inhaled_pm25 < 100:
        impact_level = "Moderate"
        color = "warning"
    elif inhaled_pm25 < 200:
        impact_level = "High"
        color = "error"
    else:
        impact_level = "Very High"
        color = "error"

    return {
        "pm25_concentration": round(pm25_equiv, 1),
        "hours": hours_outdoor,
        "inhaled_pm25_ug": round(inhaled_pm25, 1),
        "impact_level": impact_level,
        "color": color,
    }


def get_daily_action_plan(aqi: int, category: str) -> List[Dict]:
    """
    Generate a time-of-day action plan.
    """
    if category == "Good":
        return [
            {"time": "6 AM – 9 AM", "action": "Ideal for morning exercise or walk", "icon": "🌅"},
            {"time": "9 AM – 12 PM", "action": "Safe for all outdoor activities", "icon": "☀️"},
            {"time": "12 PM – 4 PM", "action": "Stay hydrated; outdoor activity fine", "icon": "🌤️"},
            {"time": "4 PM – 7 PM", "action": "Great time for evening sports", "icon": "🌇"},
            {"time": "7 PM – 10 PM", "action": "Safe for outdoor dining or walking", "icon": "🌙"},
        ]
    elif category == "Moderate":
        return [
            {"time": "6 AM – 8 AM", "action": "Best window for outdoor exercise", "icon": "🌅"},
            {"time": "8 AM – 12 PM", "action": "Limit strenuous activity; breaks recommended", "icon": "☀️"},
            {"time": "12 PM – 4 PM", "action": "Reduce outdoor time; traffic peaks", "icon": "🌤️"},
            {"time": "4 PM – 7 PM", "action": "Light walks okay; avoid heavy exercise", "icon": "🌇"},
            {"time": "7 PM – 10 PM", "action": "Indoor activities preferred", "icon": "🌙"},
        ]
    elif category == "Poor":
        return [
            {"time": "6 AM – 8 AM", "action": "Short walks only with mask; avoid exercise", "icon": "🌅"},
            {"time": "8 AM – 12 PM", "action": "Stay indoors; use air purifier", "icon": "☀️"},
            {"time": "12 PM – 4 PM", "action": "Minimize outdoor exposure; mask mandatory", "icon": "🌤️"},
            {"time": "4 PM – 7 PM", "action": "Indoor exercise only; ventilate briefly", "icon": "🌇"},
            {"time": "7 PM – 10 PM", "action": "Stay indoors; seal windows", "icon": "🌙"},
        ]
    elif category == "Very Poor":
        return [
            {"time": "6 AM – 8 AM", "action": "Do not go outdoors; pollution is trapped", "icon": "🌅"},
            {"time": "8 AM – 12 PM", "action": "Stay sealed indoors; run air purifier", "icon": "☀️"},
            {"time": "12 PM – 4 PM", "action": "Essential travel only with N95 mask", "icon": "🌤️"},
            {"time": "4 PM – 7 PM", "action": "Continue indoor isolation; monitor symptoms", "icon": "🌇"},
            {"time": "7 PM – 10 PM", "action": "Keep all openings sealed; no outdoor time", "icon": "🌙"},
        ]
    else:
        return [
            {"time": "All Day", "action": "STAY INDOORS — emergency-level pollution", "icon": "🚨"},
            {"time": "If Travel Necessary", "action": "N95 mask mandatory; minimize time outside", "icon": "😷"},
            {"time": "Indoor", "action": "Sealed room with air purifier running continuously", "icon": "🏠"},
            {"time": "Medical", "action": "Monitor for symptoms; seek help if breathing difficulty", "icon": "🏥"},
            {"time": "Hydration", "action": "Warm fluids every hour; avoid cold beverages", "icon": "💧"},
        ]
