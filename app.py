# app.py (Streamlit Cloud Compatible – No pyttsx3)
import streamlit as st
from questions import bdi_questions

# Dummy speak function to avoid errors in Streamlit Cloud
def speak(text):
    pass  # Disabled for cloud deployment

# Page config
st.set_page_config(page_title="Mental Health Chatbot", page_icon="🧠")
st.title("🧠 AI Mental Health Chatbot")
st.write("This chatbot will help assess your mental health using the BDI-II scale. Please answer the questions below honestly.")

score = 0
responses = []

for idx, q in enumerate(bdi_questions):
    st.subheader(q['question'])
    response = st.radio("Choose one:", q['options'], key=idx)
    responses.append(response)
    score += q['options'].index(response)

if st.button("Submit"):
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

    speak(feedback)  # Will not run on cloud
