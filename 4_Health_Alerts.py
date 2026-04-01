import streamlit as st
from utils.alerts import generate_health_alert, HEALTH_RISK_LEVEL

st.set_page_config(layout="wide")

st.title("🚨 Health Alerts")

# --- Input Section ---
col1, col2 = st.columns(2)

with col1:
    city = st.selectbox("City", [
        "Delhi", "Mumbai", "Chennai", "Bengaluru", "Hyderabad", "Kolkata",
        "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Patna", "Chandigarh",
        "Visakhapatnam", "Thiruvananthapuram",
    ])

with col2:
    aqi_value = st.slider("AQI Value", min_value=0, max_value=500, value=120)

# --- Personalized Health Profile ---
with st.expander("👤 Personal Health Profile (for tailored recommendations)", expanded=False):
    pc1, pc2 = st.columns(2)
    with pc1:
        age = st.number_input("Age", 1, 100, 30)
        is_pregnant = st.checkbox("Pregnant")
    with pc2:
        has_respiratory = st.checkbox("Asthma / Respiratory condition")
        has_heart = st.checkbox("Heart disease / Cardiovascular condition")
        has_diabetes = st.checkbox("Diabetes")

ALERT_CONFIG = {
    "Good": {
        "icon": "🟢", "color": "success",
        "summary": "Air quality is excellent. Safe for all outdoor activities.",
    },
    "Moderate": {
        "icon": "🟡", "color": "info",
        "summary": "Air quality is acceptable. Some pollutants may be a concern for sensitive individuals.",
    },
    "Poor": {
        "icon": "🟠", "color": "warning",
        "summary": "Air quality is unhealthy for sensitive groups. General public may begin to feel effects.",
    },
    "Very Poor": {
        "icon": "🔴", "color": "error",
        "summary": "Health alert — everyone may experience serious health effects.",
    },
    "Severe": {
        "icon": "☠️", "color": "error",
        "summary": "Health emergency — entire population is at risk of being affected.",
    },
}

PRECAUTIONS = {
    "Good": {
        "🏃 Outdoor Activity": [
            "All outdoor activities are safe",
            "Great conditions for jogging, cycling, and sports",
        ],
        "🏠 Indoor": ["Normal ventilation — open windows freely"],
        "🩺 Health": ["No precautions needed"],
    },
    "Moderate": {
        "🏃 Outdoor Activity": [
            "Limit prolonged heavy exertion outdoors",
            "Take more breaks during outdoor exercise",
            "Schedule strenuous activities for early morning or evening",
        ],
        "🏠 Indoor": [
            "Keep windows open for ventilation during low-traffic hours",
            "Avoid burning candles, incense, or smoking indoors",
        ],
        "🩺 Health": [
            "Watch for coughing, throat irritation, or shortness of breath",
            "Keep quick-relief inhaler accessible if you have asthma",
            "Stay hydrated — drink plenty of water",
        ],
    },
    "Poor": {
        "🏃 Outdoor Activity": [
            "Avoid jogging, cycling, or any heavy outdoor exercise",
            "Limit outdoor time to essential trips only",
            "Wear a surgical or N95 mask when stepping out",
            "Avoid areas near heavy traffic or construction",
        ],
        "🏠 Indoor": [
            "Keep windows and doors closed",
            "Use an air purifier if available",
            "Run exhaust fans in kitchens while cooking",
            "Avoid indoor pollution sources (smoking, aerosol sprays, frying)",
        ],
        "🩺 Health": [
            "Monitor for wheezing, chest tightness, or persistent cough",
            "Take prescribed respiratory medication as directed",
            "Gargle with warm salt water to soothe throat irritation",
            "Use saline nasal spray to clear irritants",
        ],
    },
    "Very Poor": {
        "🏃 Outdoor Activity": [
            "Avoid all outdoor exercise and sports",
            "Use N95/KN95 masks for any outdoor exposure",
            "Limit outdoor time to under 15 minutes when possible",
            "Keep car windows closed and use recirculate mode for AC",
        ],
        "🏠 Indoor": [
            "Seal windows and doors — use damp towels under gaps",
            "Run air purifiers continuously in occupied rooms",
            "Avoid vacuum cleaning — it resuspends particles",
            "Use damp mopping instead of dry sweeping",
        ],
        "🩺 Health": [
            "Have emergency medications readily available",
            "Monitor oxygen saturation if you have a pulse oximeter",
            "Stay hydrated — drink warm fluids regularly",
            "Avoid cold drinks — warm water, soups, and herbal teas are better",
            "Consult a doctor if you experience persistent headache or dizziness",
        ],
    },
    "Severe": {
        "🏃 Outdoor Activity": [
            "Do NOT go outdoors unless absolutely unavoidable",
            "If you must go out, wear a properly fitted N95 mask",
            "Avoid all physical exertion — even walking",
            "Postpone travel plans if possible",
        ],
        "🏠 Indoor": [
            "Seal all openings — windows, doors, vents",
            "Run air purifiers at maximum setting",
            "Create a clean-air room with sealed entry and purifier",
            "Avoid cooking methods that produce smoke (frying, grilling)",
            "Use wet cloths on window grills to trap particles",
        ],
        "🩺 Health": [
            "Seek immediate medical help for breathing difficulty or chest pain",
            "Keep emergency inhalers and medications within reach",
            "Monitor for nausea, fatigue, or irregular heartbeat",
            "Do not self-medicate — consult a doctor for any symptoms",
            "Keep emergency numbers saved and accessible",
        ],
    },
}

VULNERABLE_GROUPS = {
    "Good": [],
    "Moderate": [
        ("🧒 Children", "Reduce extended outdoor play if symptoms appear"),
        ("👴 Elderly", "Limit strenuous outdoor walks"),
        ("🫁 Asthma / Respiratory", "Carry inhaler; avoid dusty areas"),
    ],
    "Poor": [
        ("🧒 Children", "Keep indoors — avoid school outdoor activities"),
        ("👴 Elderly", "Stay indoors — avoid morning walks"),
        ("🫁 Asthma / Respiratory", "Strictly avoid outdoor exposure; use preventive inhaler"),
        ("🤰 Pregnant Women", "Stay indoors — prolonged exposure can affect fetal health"),
    ],
    "Very Poor": [
        ("🧒 Children", "No outdoor activities; schools should suspend outdoor PE"),
        ("👴 Elderly", "Stay in air-purified rooms; monitor blood pressure"),
        ("🫁 Asthma / Respiratory", "Use prescribed steroids/inhalers proactively"),
        ("🤰 Pregnant Women", "Avoid any outdoor exposure; consult doctor if discomfort"),
        ("❤️ Heart Conditions", "Minimize all physical exertion; monitor heart rate"),
    ],
    "Severe": [
        ("🧒 Children", "Complete indoor isolation; watch for coughing or fever"),
        ("👴 Elderly", "Medical check-up recommended; stay in sealed rooms"),
        ("🫁 Asthma / Respiratory", "Emergency action plan should be activated"),
        ("🤰 Pregnant Women", "Seek medical guidance; use air purifier in bedroom"),
        ("❤️ Heart Conditions", "Watch for chest pain or palpitations — call doctor immediately"),
    ],
}

SYMPTOMS_TO_WATCH = {
    "Good": [],
    "Moderate": ["Mild throat irritation", "Sneezing", "Watery eyes"],
    "Poor": ["Persistent cough", "Shortness of breath", "Throat dryness", "Headache", "Eye irritation"],
    "Very Poor": ["Wheezing", "Chest tightness", "Dizziness", "Nausea", "Difficulty breathing", "Fatigue"],
    "Severe": ["Severe breathlessness", "Chest pain", "Confusion or disorientation", "Bluish lips or fingertips", "Irregular heartbeat", "Fainting"],
}

# --- Generate alert with personalization ---
alert = generate_health_alert(aqi_value, age=age, respiratory_issue=has_respiratory, heart_disease=has_heart)
category = alert["Category"]
risk_level = alert["Risk Level"]
is_emergency = alert["Emergency"]
config = ALERT_CONFIG.get(category, ALERT_CONFIG["Good"])

st.divider()

# --- Alert banner ---
mcol1, mcol2, mcol3 = st.columns(3)
with mcol1:
    st.metric("AQI", aqi_value)
with mcol2:
    st.metric("Category", f"{config['icon']} {category}")
with mcol3:
    st.metric("Risk Level", risk_level)

alert_fn = {"success": st.success, "info": st.info, "warning": st.warning, "error": st.error}
alert_fn[config["color"]](f"**{config['summary']}**")

if is_emergency:
    st.error("🚨 **EMERGENCY ALERT** — AQI has crossed dangerous levels. Take immediate protective action.")

# --- Personalized Recommendations ---
st.subheader("👤 Your Personalized Recommendations")

personalized_recs = alert["Recommendations"]
for rec in personalized_recs:
    st.markdown(f"- {rec}")

# Additional profile-based warnings
profile_warnings = []
if age < 12 and category not in ("Good",):
    profile_warnings.append(f"🧒 **Child (age {age})** — Children's lungs are still developing. Extra protection is critical at {category} AQI levels.")
elif age > 60 and category not in ("Good",):
    profile_warnings.append(f"👴 **Senior (age {age})** — Age-related reduced lung capacity increases vulnerability. Avoid outdoor exposure.")

if has_respiratory and category not in ("Good", "Moderate"):
    profile_warnings.append("🫁 **Respiratory Condition** — Use preventive inhaler before any outdoor exposure. Keep rescue medication accessible at all times.")

if has_heart and category not in ("Good", "Moderate"):
    profile_warnings.append("❤️ **Heart Condition** — Air pollution increases cardiovascular strain. Monitor blood pressure and heart rate closely.")

if has_diabetes and category not in ("Good", "Moderate"):
    profile_warnings.append("💉 **Diabetes** — Poor air quality can worsen blood sugar control. Monitor glucose levels more frequently.")

if is_pregnant and category not in ("Good",):
    profile_warnings.append("🤰 **Pregnancy** — Fetal development is sensitive to air pollution. Minimize all outdoor exposure and use air purification indoors.")

if profile_warnings:
    st.divider()
    st.subheader("⚠️ Profile-Specific Warnings")
    for warning in profile_warnings:
        st.warning(warning)

st.divider()

# --- Precautions ---
st.subheader("🛡️ Precautions")

precaution_data = PRECAUTIONS[category]
tabs = st.tabs(list(precaution_data.keys()))

for tab, (section, items) in zip(tabs, precaution_data.items()):
    with tab:
        for item in items:
            st.markdown(f"- {item}")

# --- Vulnerable Groups ---
vulnerable = VULNERABLE_GROUPS[category]
if vulnerable:
    st.subheader("⚠️ Vulnerable Groups")
    for group_icon, advice in vulnerable:
        st.warning(f"**{group_icon}** — {advice}")

# --- Symptoms ---
symptoms = SYMPTOMS_TO_WATCH[category]
if symptoms:
    st.subheader("🔍 Symptoms to Watch For")
    scols = st.columns(min(len(symptoms), 3))
    for i, symptom in enumerate(symptoms):
        with scols[i % len(scols)]:
            st.info(f"• {symptom}")
