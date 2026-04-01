"""
Gemini-powered AQI chat assistant.
Uses live app data as context so the AI gives accurate, data-driven answers.
Includes automatic model fallback and retry on rate limits.
"""
import time
from google import genai
from google.genai import types
from utils.data import load_dataset, CITIES

MODELS = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

MAX_RETRIES = 2
RETRY_DELAY = 5


def _build_system_context() -> str:
    """Build a system prompt with live AQI data from the dataset."""
    df = load_dataset()
    latest = df.sort_values("Date").groupby("City").last().reset_index()
    latest = latest.sort_values("AQI", ascending=False)

    city_summary = ""
    for _, row in latest.iterrows():
        city_summary += (
            f"- {row['City']}: AQI={int(row['AQI'])} ({row['AQI_Category']}), "
            f"PM2.5={row['PM2.5']}, PM10={row['PM10']}, NO2={row['NO2']}, "
            f"SO2={row['SO2']}, CO={row['CO']}, O3={row['O3']}, "
            f"Temp={row['Temperature']}°C, Humidity={row['Humidity']}%, "
            f"Wind={row['Wind_Speed']}km/h, Dominant={row['Dominant_Pollutant']}\n"
        )

    avg_by_city = df.groupby("City")["AQI"].mean().round(0).sort_values(ascending=False)
    avg_summary = ", ".join(f"{city}: {int(aqi)}" for city, aqi in avg_by_city.items())

    total_records = len(df)
    date_range = f"{df['Date'].min().strftime('%b %Y')} to {df['Date'].max().strftime('%b %Y')}"

    return f"""You are an expert AQI (Air Quality Index) health assistant integrated into a Smart AQI Monitoring web application. You help users understand air quality data, health risks, precautions, and make safe decisions.

IMPORTANT RULES:
- Use the LIVE DATA below to answer questions about specific cities — never make up AQI values.
- When asked about a city, provide its actual current AQI, category, pollutant levels, and health advice.
- Give practical, actionable health recommendations based on the AQI level.
- Be concise but thorough. Use markdown formatting (bold, tables, bullet points).
- If asked about a city not in the data, say so and suggest available cities.
- For health questions, consider vulnerable groups (children, elderly, pregnant, asthmatic).

AQI CATEGORIES (Indian NAQI Standard):
- Good (0-50): Safe for all
- Moderate (51-100): Sensitive groups cautious
- Poor (101-200): Breathing discomfort possible
- Very Poor (201-300): Health warnings for all
- Severe (301-500): Health emergency

CURRENT DATA ({total_records} records, {date_range}):

Latest AQI readings per city:
{city_summary}
Historical averages: {avg_summary}

Available cities: {', '.join(CITIES)}

When giving health advice, structure your response with:
1. Current status (AQI value and category)
2. Health risk assessment
3. Specific precautions/recommendations
4. Special advice for vulnerable groups if relevant"""


_client = None
_chats = {}
_system_ctx = None


def init_gemini(api_key: str):
    """Initialize the Gemini client."""
    global _client, _chats, _system_ctx
    _client = genai.Client(api_key=api_key)
    _chats = {}
    _system_ctx = _build_system_context()


def _get_chat(model_name: str):
    """Get or create a chat session for the given model."""
    if model_name not in _chats:
        _chats[model_name] = _client.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=_system_ctx,
                temperature=0.7,
                max_output_tokens=1024,
            ),
        )
    return _chats[model_name]


def send_message(user_message: str) -> str:
    """Send a message, trying multiple models if rate limited."""
    if _client is None:
        raise RuntimeError("Gemini not initialized. Call init_gemini(api_key) first.")

    last_error = None

    for model_name in MODELS:
        for attempt in range(MAX_RETRIES + 1):
            try:
                chat = _get_chat(model_name)
                response = chat.send_message(user_message)
                text = response.text
                # Ensure clean unicode string
                if isinstance(text, bytes):
                    text = text.decode("utf-8", errors="replace")
                return text
            except Exception as e:
                try:
                    error_str = repr(e)
                except Exception:
                    error_str = "Unknown error"
                last_error = error_str

                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY)
                        continue
                    break
                else:
                    raise

    raise RuntimeError(
        f"All models are rate-limited. Please wait a minute and try again."
    )
