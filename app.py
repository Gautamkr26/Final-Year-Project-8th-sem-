import streamlit as st
from questions import bdi_questions  # Import questions list

# Streamlit page settings
st.set_page_config(page_title="Mental Health Chatbot", page_icon="🧠")
st.title("🧠 AI based Mental Health Chatbot")
st.write("This chatbot helps assess your mental health using the BDI-II scale. Please answer all questions honestly.")

# Initialize response list
responses = [None] * len(bdi_questions)

# Render questions with no default selection
for idx, q in enumerate(bdi_questions):
    st.subheader(q["question"])
    responses[idx] = st.radio("Choose one:", q["options"], key=idx, index=None)

# Submit button
if st.button("Submit"):
    if None in responses:
        st.error("❌ Please answer all questions before submitting.")
    else:
        score = 0
        for i, response in enumerate(responses):
            score += bdi_questions[i]["options"].index(response)

        st.subheader(f"✅ Your BDI Score: {score}")

        # Score-based feedback
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

        # Text-to-speech removed for compatibility with Streamlit Cloud

