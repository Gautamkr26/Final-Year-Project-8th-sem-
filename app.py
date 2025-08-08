import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from questions import bdi_questions
from assessment import MentalHealthAssessment
from utils import severity_message, crisis_message
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# ------------------ Session state init ------------------
if "patient_name" not in st.session_state:
    st.session_state.patient_name = ""
if "patient_age" not in st.session_state:
    st.session_state.patient_age = ""
if "assessment_date" not in st.session_state:
    st.session_state.assessment_date = datetime.today().strftime("%Y-%m-%d")
if "details_done" not in st.session_state:
    st.session_state.details_done = False
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "responses" not in st.session_state:
    st.session_state.responses = [None] * len(bdi_questions)

# ------------------ Title ------------------
st.title("🧠 Mental Health Chatbot – BDI-II")

# ------------------ Patient Details ------------------
if not st.session_state.details_done:
    st.subheader("📋 Patient Information")
    st.session_state.patient_name = st.text_input("Full name", value=st.session_state.patient_name)
    st.session_state.patient_age = st.text_input("Age", value=st.session_state.patient_age)
    st.session_state.assessment_date = st.date_input(
        "Assessment Date",
        value=datetime.strptime(st.session_state.assessment_date, "%Y-%m-%d")
    ).strftime("%Y-%m-%d")

    st.markdown("Fill patient details and click **Next** to start the assessment.")
    if st.button("➡️ Next to Assessment"):
        if not st.session_state.patient_name.strip() or not st.session_state.patient_age.strip():
            st.warning("Please enter both Name and Age to proceed.")
        else:
            st.session_state.details_done = True
            st.experimental_rerun()
    st.stop()

# ------------------ Assessment ------------------
assessment = MentalHealthAssessment(bdi_questions)
current_index = st.session_state.current_index
current_question = bdi_questions[current_index]["question"]

# Progress bar
progress = (current_index) / len(bdi_questions)
st.progress(progress)
st.markdown(f"**Progress:** {current_index}/{len(bdi_questions)}")

# Question with TTS toggle
colA, colB = st.columns([4, 1])
with colA:
    st.subheader(f"{current_index + 1}. {current_question}")
with colB:
    tts_enabled = st.checkbox("🔊", value=False)

# Play TTS if enabled
if tts_enabled:
    components.html(f"""
        <script>
        var utterance = new SpeechSynthesisUtterance("{current_question}");
        window.speechSynthesis.speak(utterance);
        </script>
    """, height=0)

# Options
selected_option = st.radio(
    label="Select an option",
    options=bdi_questions[current_index]["options"],
    index=st.session_state.responses[current_index]
    if st.session_state.responses[current_index] is not None else None,
    label_visibility="hidden"
)

# Save response
if selected_option is not None:
    st.session_state.responses[current_index] = bdi_questions[current_index]["options"].index(selected_option)

# Navigation buttons
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("⬅️ Back") and current_index > 0:
        st.session_state.current_index -= 1
        st.experimental_rerun()
with col2:
    if st.button("➡️ Next") and current_index < len(bdi_questions) - 1:
        st.session_state.current_index += 1
        st.experimental_rerun()
with col3:
    if st.button("🔍 Submit"):
        if None in st.session_state.responses:
            st.warning("Please answer all questions before submitting.")
        else:
            score, severity = assessment.evaluate(st.session_state.responses)

            # Show results
            st.success(f"Total Score: {score}")
            st.info(severity_message(severity))
            st.warning(crisis_message())

            # Generate PDF report
            buffer = io.BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=A4)
            pdf.setTitle("BDI-II Assessment Report")

            # Header
            pdf.setFont("Helvetica-Bold", 20)
            pdf.drawString(200, 800, "BDI-II Assessment Report")
            pdf.setFont("Helvetica", 12)
            pdf.drawString(50, 770, f"Patient Name: {st.session_state.patient_name}")
            pdf.drawString(50, 750, f"Age: {st.session_state.patient_age}")
            pdf.drawString(50, 730, f"Assessment Date: {st.session_state.assessment_date}")

            # Result
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, 700, f"Total Score: {score}")
            pdf.drawString(50, 680, f"Severity: {severity.name}")

            # Recommendation
            pdf.setFont("Helvetica", 12)
            pdf.drawString(50, 650, "Recommendation:")
            text = pdf.beginText(50, 630)
            text.setFont("Helvetica", 12)
            text.textLines(severity_message(severity))
            pdf.drawText(text)

            # Crisis Info
            text = pdf.beginText(50, 580)
            text.setFont("Helvetica-Oblique", 10)
            text.textLines(crisis_message())
            pdf.drawText(text)

            pdf.showPage()
            pdf.save()
            buffer.seek(0)

            st.download_button(
                label="📄 Download PDF Report",
                data=buffer,
                file_name="BDI-II_Report.pdf",
                mime="application/pdf"
            )
