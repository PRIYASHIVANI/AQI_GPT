import os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import streamlit as st
from utils.chatbot import respond as rule_based_respond

st.set_page_config(layout="wide", page_title="AQI Assistant")
st.title("💬 AQI Assistant")

# --- Sidebar: API key & mode selection ---
with st.sidebar:
    st.subheader("⚙️ Assistant Mode")

    mode = st.radio("Choose mode", ["AI (Google Gemini)", "Offline (Rule-based)"],
                    index=0, help="AI mode requires a Gemini API key")

    gemini_key = None
    if mode == "AI (Google Gemini)":
        gemini_key = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="Paste your API key here",
            help="Get a free key at https://aistudio.google.com/apikey",
        )
        if not gemini_key:
            st.caption("Paste your Gemini API key above to enable AI mode")
        else:
            st.success("API key configured")

    st.divider()
    st.subheader("💡 Try asking")

    quick_questions = [
        "What's the AQI in Delhi?",
        "Is it safe to go jogging today?",
        "Which city has the cleanest air?",
        "Compare Delhi and Bengaluru",
        "What precautions for Patna?",
        "What is PM2.5?",
        "I have asthma, is it safe outside?",
        "Suggest best city to visit",
        "Explain AQI categories",
    ]

    for q in quick_questions:
        if st.button(q, use_container_width=True, key=f"q_{q}"):
            st.session_state.pending_question = q
            st.rerun()

# --- Determine if Gemini is available ---
use_gemini = mode == "AI (Google Gemini)" and bool(gemini_key)

if use_gemini:
    st.caption("Powered by **Google Gemini AI** — responses use your app's live AQI data")
else:
    st.caption("Offline mode — rule-based responses from your app's data")

# --- Initialize session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "gemini_ready" not in st.session_state:
    st.session_state.gemini_ready = False

if "gemini_key_used" not in st.session_state:
    st.session_state.gemini_key_used = None

# --- Initialize/reinitialize Gemini when key changes ---
if use_gemini and gemini_key != st.session_state.gemini_key_used:
    try:
        from utils.gemini_chat import init_gemini
        init_gemini(gemini_key)
        st.session_state.gemini_ready = True
        st.session_state.gemini_key_used = gemini_key
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {e}")
        st.session_state.gemini_ready = False
        use_gemini = False

if not use_gemini:
    st.session_state.gemini_ready = False

# --- Welcome message ---
if not st.session_state.messages:
    welcome = (
        "Hello! I'm your **AQI Assistant**. "
        + ("I'm powered by **Google Gemini AI** and have access to live air quality data for 14 Indian cities.\n\n"
           if use_gemini and st.session_state.gemini_ready
           else "I'm running in **offline mode** with rule-based responses.\n\n")
        + "Ask me anything about:\n"
        "- 📍 Air quality in any city\n"
        "- 🏃 Whether it's safe for outdoor activities\n"
        "- 🛡️ Health precautions and recommendations\n"
        "- ⚖️ City comparisons and rankings\n"
        "- 📖 Pollutant information and AQI education\n\n"
        "Go ahead, ask me anything!"
    )
    st.session_state.messages.append({"role": "assistant", "content": welcome})

# --- Display chat history ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def get_response(user_msg: str) -> str:
    """Route to Gemini or rule-based depending on mode."""
    if use_gemini and st.session_state.gemini_ready:
        try:
            from utils.gemini_chat import send_message
            return send_message(user_msg)
        except Exception as e:
            try:
                error_str = repr(e).encode("utf-8", errors="replace").decode("utf-8")
            except Exception:
                error_str = "Unknown error"

            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "rate" in error_str.lower():
                offline = rule_based_respond(user_msg)
                return (
                    "AI models are temporarily rate-limited. "
                    "Responding with offline data instead:\n\n---\n\n" + offline
                )
            offline = rule_based_respond(user_msg)
            return f"AI encountered an issue. Here's an offline response:\n\n---\n\n{offline}"
    return rule_based_respond(user_msg)


# --- Handle pending question from sidebar ---
if "pending_question" in st.session_state:
    pending = st.session_state.pending_question
    del st.session_state.pending_question

    st.session_state.messages.append({"role": "user", "content": pending})
    with st.chat_message("user"):
        st.markdown(pending)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_response(pending)
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

# --- Chat input ---
if prompt := st.chat_input("Ask about air quality, health risks, cities..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_response(prompt)
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
