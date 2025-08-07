# app.py
import streamlit as st
from pyttsx3 import init
from questions import bdi_questions

# Text-to-speech function
def speak(text):
    try:
        engine = init()
        engine.say(text)
        engine.runAndWait()
    except:
        st.warning("Text-to-speech failed. Please check your system audio or pyttsx3 setup.")

# Streamlit page setup
st.set_page_config(page_title="Mental Health Chatbot", page_icon="🧠", layout="centered")
st.title("🧠 AI Mental Health Chatbot")
st.markdown("This chatbot helps assess your mental health using the **Beck Depression Inventory (BDI-II)**. Please answer honestly.")

# Variables
score = 0
responses = []

# Ask each question
for idx, q in enumerate(bdi_questions):
    st.subheader(f"{idx+1}. {q['question']}")
    response = st.radio(
        "Select one:", 
        q['options'], 
        key=f"q_{idx}", 
        index=None  # ✅ No default selection
    )
    if response:
        responses.append(response)
        score += q['options'].index(response)

# Submit button
if st.button("🔎 Submit Assessment"):
    st.success(f"✅ Your BDI-II Score: {score} out of 63")

    if score <= 13:
        feedback = (
            "🟢 **Minimal depression.**\n\nYou're doing well. Maintain your mental health by engaging in regular activities, "
            "staying connected with loved ones, and following a healthy routine."
        )
    elif 14 <= score <= 19:
        feedback = (
            "🟡 **Mild depression.**\n\nTry journaling, doing regular light exercises, and talk with someone you trust. "
            "Practicing mindfulness may help too."
        )
    elif 20 <= score <= 28:
        feedback = (
            "🟠 **Moderate depression.**\n\nIt’s a good time to consult a counselor or therapist. You’re not alone. "
            "Support is available and effective."
        )
    else:
        feedback = (
            "🔴 **Severe depression.**\n\nPlease speak to a licensed mental health professional or helpline as soon as possible. "
            "You deserve care and help. Don't delay."
        )

    st.markdown("### 💬 Feedback:")
    st.info(feedback)
    speak(feedback)
