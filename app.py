# app.py (Final version: Voice on local, silent on cloud, radio fix)
import streamlit as st
import platform
from questions import bdi_questions

# Smart voice speak (only on local Windows)
if platform.system() == "Windows":
    from pyttsx3 import init
    def speak(text):
        engine = init()
        engine.say(text)
        engine.runAndWait()
else:
    def speak(text):
        pass  # Disabled on cloud

# Page config
st.set_page_config(page_title="Mental Health Chatbot", page_icon="🧠")
st.title("🧠 AI Mental Health Chatbot")
st.write("This chatbot will help assess your mental health using the BDI-II scale. Please answer the questions honestly.")

# Score and response tracking
score = 0
responses = []

# Questions loop
for idx, q in enumerate(bdi_questions):
    st.subheader(q['question'])
    response = st.radio("Choose one:", options=q['options'], key=idx, index=None)  # index=None fixes auto-select
    if response:
        responses.append(response)
        score += q['options'].index(response)
    else:
        responses.append(None)

# On Submit
if st.button("Submit"):
    if None in responses:
        st.warning("⚠️ Please answer all questions before submitting.")
    else:
        st.subheader(f"✅ Your BDI Score: {score}")

        if score <= 13:
            feedback = "Minimal depression. You're doing well! Keep a healthy routine, stay connected, and continue doing what you enjoy. 🌱"
        elif 14 <= score <= 19:
            feedback = "Mild depression. Try journaling, regular light exercise, and talk to someone you trust. 🗣️"
        elif 20 <= score <= 28:
            feedback = "Moderate depression. Please consider reaching out to a therapist and practice mindfulness. 🧘"
        else:
            feedback = "Severe depression. You should speak to a mental health professional or helpline immediately. You're not alone. 🚨"

        st.write("### 💬 Feedback:")
        st.success(feedback)
        speak(feedback)
