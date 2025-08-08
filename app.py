# app.py (Final version)
import streamlit as st
import platform
from questions import bdi_questions
from assessment import get_feedback
from speech import speak

# Page config
st.set_page_config(page_title="Mental Health Chatbot", page_icon="🧠")
st.title("🧠 AI Mental Health Chatbot")
st.write("This chatbot will help assess your mental health using the **BDI-II scale**. Please answer all questions honestly.")

# Track responses
responses = [None] * len(bdi_questions)

# Progress
progress = st.progress(0)

# Question loop
for idx, q in enumerate(bdi_questions):
    st.subheader(f"{idx+1}. {q['question']}")
    responses[idx] = st.radio("Choose one:", options=q['options'], key=idx, index=None)
    progress.progress(int(((idx+1)/len(bdi_questions))*100))

# Submit
if st.button("Submit"):
    if None in responses:
        st.warning("⚠️ Please answer all questions before submitting.")
    else:
        score = sum(bdi_questions[i]['options'].index(responses[i]) for i in range(len(bdi_questions)))
        st.subheader(f"✅ Your BDI Score: {score}")

        feedback = get_feedback(score)
        st.write("### 💬 Feedback:")
        st.success(feedback)
        speak(feedback)

        st.markdown("---")
        st.markdown("📞 **Mental Health Resources:**\n"
                    "- 🇮🇳 India Helpline: 1800-599-0019\n"
                    "- 🌍 [Find a helpline worldwide](https://findahelpline.com)\n"
                    "- 🧠 [WHO Mental Health Resources](https://www.who.int/health-topics/mental-health)")

        if st.button("Restart Test"):
            st.experimental_rerun()
