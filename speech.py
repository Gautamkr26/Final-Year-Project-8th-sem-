import platform
import streamlit as st

def speak(text):
    if platform.system() == "Windows":
        try:
            from pyttsx3 import init
            engine = init()
            engine.say(text)
            engine.runAndWait()
        except:
            pass
    else:
        # Streamlit browser voice using JavaScript
        st.markdown(
            f"""
            <script>
            var msg = new SpeechSynthesisUtterance("{text}");
            window.speechSynthesis.speak(msg);
            </script>
            """,
            unsafe_allow_html=True
        )
