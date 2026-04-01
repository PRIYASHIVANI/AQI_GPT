"""
utils/alerts.py
---------------------------------
Health Alert & Recommendation Engine
for Smart AQI Forecasting & Health Alert System

This module implements a **rule-based expert system** that converts
AQI values into:
- AQI categories
- Health risk levels
- Personalized health recommendations
- Emergency alerts

Designed to be:
- Explainable (viva-friendly)
- Extensible (easy to add new rules)
- Reusable across Streamlit pages & APIs
"""

from typing import Dict, List

# -------------------------------------------------
# AQI CATEGORY DEFINITION
# -------------------------------------------------
AQI_CATEGORIES = {
    "Good": (0, 50),
    "Moderate": (51, 100),
    "Poor": (101, 200),
    "Very Poor": (201, 300),
    "Severe": (301, 500)
}

# -------------------------------------------------
# BASIC AQI CATEGORIZATION
# -------------------------------------------------
def get_aqi_category(aqi: int) -> str:
    """
    Classify AQI value into standard AQI category
    """
    for category, (low, high) in AQI_CATEGORIES.items():
        if low <= aqi <= high:
            return category
    return "Unknown"


# -------------------------------------------------
# HEALTH RISK LEVEL MAPPING
# -------------------------------------------------
HEALTH_RISK_LEVEL = {
    "Good": "Low",
    "Moderate": "Low to Medium",
    "Poor": "Medium",
    "Very Poor": "High",
    "Severe": "Very High"
}


# -------------------------------------------------
# BASE HEALTH RECOMMENDATIONS
# -------------------------------------------------
BASE_RECOMMENDATIONS: Dict[str, List[str]] = {
    "Good": [
        "Air quality is safe for all age groups",
        "Ideal conditions for outdoor exercise",
        "No health precautions required"
    ],
    "Moderate": [
        "Sensitive individuals should reduce prolonged outdoor exertion",
        "Monitor symptoms such as coughing or irritation",
        "Maintain hydration"
    ],
    "Poor": [
        "Avoid outdoor physical activities",
        "Wear a protective mask when outdoors",
        "Children and elderly should stay indoors"
    ],
    "Very Poor": [
        "Limit outdoor exposure",
        "Use N95 or equivalent masks",
        "Consider using indoor air purifiers"
    ],
    "Severe": [
        "Stay indoors at all times",
        "Avoid travel unless absolutely necessary",
        "Seek medical advice if breathing difficulty occurs"
    ]
}


# -------------------------------------------------
# PERSONALIZED HEALTH MODIFIERS
# -------------------------------------------------
def apply_personalized_rules(
    category: str,
    age: int = None,
    has_respiratory_issue: bool = False,
    has_heart_disease: bool = False
) -> List[str]:
    """
    Modify health recommendations based on user profile
    """
    recommendations = BASE_RECOMMENDATIONS[category].copy()

    if age is not None:
        if age < 12:
            recommendations.append("Children are more vulnerable to air pollution")
        elif age > 60:
            recommendations.append("Elderly individuals should take extra precautions")

    if has_respiratory_issue:
        recommendations.append(
            "People with asthma or respiratory issues should strictly avoid polluted environments"
        )

    if has_heart_disease:
        recommendations.append(
            "People with heart conditions should minimize physical exertion"
        )

    return recommendations


# -------------------------------------------------
# EMERGENCY ALERT LOGIC
# -------------------------------------------------
def is_emergency(aqi: int) -> bool:
    """
    Determine whether AQI level requires emergency alert
    """
    return aqi >= 300


# -------------------------------------------------
# COMPLETE HEALTH ALERT PIPELINE
# -------------------------------------------------
def generate_health_alert(
    aqi: int,
    age: int = None,
    respiratory_issue: bool = False,
    heart_disease: bool = False
) -> Dict:
    """
    Generate complete health alert package
    """
    category = get_aqi_category(aqi)
    risk_level = HEALTH_RISK_LEVEL.get(category, "Unknown")

    recommendations = apply_personalized_rules(
        category,
        age,
        respiratory_issue,
        heart_disease
    )

    emergency = is_emergency(aqi)

    return {
        "AQI": aqi,
        "Category": category,
        "Risk Level": risk_level,
        "Emergency": emergency,
        "Recommendations": recommendations
    }
