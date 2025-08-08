# app.py (updated with responsive button alignment)
import re
import streamlit as st
from datetime import datetime
from io import BytesIO
import streamlit.components.v1 as components

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

from assessment import MentalHealthAssessment
from questions import bdi_questions
from utils import score_to_severity, severity_message, crisis_message, Severity

st.set_page_config(page_title="Mental Health Chatbot (BDI-II)", page_icon="🧠", layout="centered")

# 🔹 CSS for responsive button row
st.markdown("""
<style>
.button-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
}
.button-row button {
    flex: 1;
    min-width: 100px;
}
@media (max-width: 600px) {
    .button-row {
        flex-direction: column;
    }
}
</style>
""", unsafe_allow_html=True)

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("⚙️ Settings")
    mode = st.radio("Assessment mode", ["All at once", "Step-by-step"], index=1)
    enable_tts = st.checkbox("Enable voice (TTS - browser)", value=False)
    st.markdown("This tool is NOT a diagnosis. For emergencies contact local services.")
    st.caption("PDF export requires 'reportlab' (pip install reportlab).")

# ---------------- Utility to strip leading numbers ----------------
def strip_leading_number(s: str) -> str:
    if not isinstance(s, str):
        return s
    return re.sub(r'^\s*\d+(?:\.\d+)?[\.\)\-]?\s*', '', s).strip()

# ---------------- Session defaults ----------------
defaults = {
    "assessment": MentalHealthAssessment(bdi_questions),
    "responses": [None] * len(bdi_questions),
    "submitted": False,
    "step_index": 0,
    "crisis_flag": False,
    "score": 0,
    "severity": Severity.MINIMAL,
    "patient_name": "",
    "patient_age": "",
    "assessment_date": datetime.now().strftime("%Y-%m-%d"),
    "details_done": False,
    "last_spoken": ""
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def reset_assessment():
    for k, v in defaults.items():
        st.session_state[k] = v

def suicidal_option_selected(selected_idx, q_index):
    return q_index == 8 and selected_idx is not None and selected_idx >= 1

def compute_score(responses):
    return sum(sel for sel in responses if sel is not None)

def speak_browser(text):
    if not enable_tts or not text:
        return
    if st.session_state.get("last_spoken") == text:
        return
    st.session_state["last_spoken"] = text
    escaped = text.replace('"', '\\"').replace("\n", "\\n")
    js = f"""
    <script>
    const u = new SpeechSynthesisUtterance("{escaped}");
    u.lang = 'en-US';
    u.rate = 1;
    u.pitch = 1;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
    </script>
    """
    components.html(js, height=0)

# ---------------- Patient details ----------------
st.title("🧠 Mental Health Chatbot — BDI-II")

if not st.session_state.details_done:
    st.subheader("🧾 Patient Information")
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
            st.rerun()
    st.stop()

# ---------------- Progress ----------------
total_q = len(bdi_questions)
answered = sum(1 for r in st.session_state.responses if r is not None)
st.progress(answered / total_q if total_q else 0.0, text=f"Progress: {answered}/{total_q}")

# ---------------- Questions ----------------
if not st.session_state.submitted:
    if mode == "All at once":
        st.header("📝 BDI-II Assessment")
        for idx, q in enumerate(bdi_questions):
            clean_question = strip_leading_number(q.get("question", ""))
            st.markdown(f"**{idx+1}. {clean_question}**")
            cleaned_opts = [strip_leading_number(opt) for opt in q.get("options", [])]
            selected_idx = st.radio(
                "",
                options=range(len(cleaned_opts)),
                index=st.session_state.responses[idx] if st.session_state.responses[idx] is not None else None,
                format_func=lambda i, opts=cleaned_opts: opts[i],
                key=f"q_{idx}_all",
            )
            if selected_idx is not None:
                st.session_state.responses[idx] = selected_idx
                if suicidal_option_selected(selected_idx, idx):
                    st.session_state.crisis_flag = True

        if st.button("🔎 Submit Assessment"):
            if any(r is None for r in st.session_state.responses):
                st.warning("Please answer all questions before submitting.")
            else:
                st.session_state.score = compute_score(st.session_state.responses)
                st.session_state.severity = score_to_severity(st.session_state.score)
                st.session_state.submitted = True
                speak_browser(severity_message(st.session_state.severity))

    else:
        nav_action = st.session_state.get("nav_action", None)
        if nav_action == "next" and st.session_state.step_index < total_q - 1:
            st.session_state.step_index += 1
        elif nav_action == "back" and st.session_state.step_index > 0:
            st.session_state.step_index -= 1
        st.session_state.nav_action = None

        i = st.session_state.step_index
        q = bdi_questions[i]
        st.header("Step-by-step Assessment")
        clean_question = strip_leading_number(q.get("question", ""))
        st.markdown(f"**{i+1}. {clean_question}**")
        cleaned_opts = [strip_leading_number(opt) for opt in q.get("options", [])]
        selected_idx = st.radio(
            "",
            options=range(len(cleaned_opts)),
            index=st.session_state.responses[i] if st.session_state.responses[i] is not None else None,
            format_func=lambda j, opts=cleaned_opts: opts[j],
            key=f"q_step_{i}",
        )
        if selected_idx is not None:
            st.session_state.responses[i] = selected_idx
            if suicidal_option_selected(selected_idx, i):
                st.session_state.crisis_flag = True

        if enable_tts:
            speak_browser(clean_question)

        # ✅ Responsive Button Row
        st.markdown('<div class="button-row">', unsafe_allow_html=True)
        if st.button("⬅️ Back", disabled=(i == 0)):
            st.session_state.nav_action = "back"
            st.rerun()
        if st.button("➡️ Next", disabled=(st.session_state.responses[i] is None or i == total_q - 1)):
            st.session_state.nav_action = "next"
            st.rerun()
        if st.button("🔎 Submit", disabled=any(r is None for r in st.session_state.responses)):
            st.session_state.score = compute_score(st.session_state.responses)
            st.session_state.severity = score_to_severity(st.session_state.score)
            st.session_state.submitted = True
            speak_browser(severity_message(st.session_state.severity))
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Results & PDF ----------------
if st.session_state.submitted:
    score = st.session_state.score
    severity = st.session_state.severity
    band = severity.name.capitalize()
    feedback = severity_message(severity)

    st.success(f"✅ Result: {score} / 63")
    st.markdown(f"**Severity:** {band}")
    st.info(feedback)

    if severity in (Severity.MODERATE, Severity.SEVERE) or st.session_state.crisis_flag:
        st.error(crisis_message())

    def build_pdf_bytes(patient_name, patient_age, assessment_date, score, band, prescription_text):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("Title", parent=styles["Heading1"],
                                     alignment=TA_CENTER, fontSize=18, leading=22)
        normal = ParagraphStyle("Normal", parent=styles["BodyText"],
                                alignment=TA_JUSTIFY, fontSize=11, leading=14)
        small = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=10, leading=12)

        elems = [
            Paragraph("Mental Health Assessment Report (BDI-II)", title_style),
            Spacer(1, 12),
            Paragraph(f"<b>Patient Name:</b> {patient_name}<br/><b>Age:</b> {patient_age}<br/><b>Assessment Date:</b> {assessment_date}<br/><b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", small),
            Spacer(1, 12),
            Paragraph(f"<b>Overall Score:</b> {score} / 63<br/><b>Severity Level:</b> {band}", small),
            Spacer(1, 12),
            Paragraph("<b>Doctor's Prescription / Advice:</b>", small),
            Spacer(1, 6)
        ]

        for p in [line.strip() for line in prescription_text.split("\n") if line.strip()]:
            elems.append(Paragraph(p, normal))
            elems.append(Spacer(1, 6))

        elems.append(Spacer(1, 20))
        elems.append(Paragraph("This report is for informational purposes and does not replace a clinical diagnosis. If you or someone is in immediate danger, contact local emergency services.", ParagraphStyle("Footer", fontSize=9, leading=11, alignment=TA_JUSTIFY)))

        doc.build(elems)
        buffer.seek(0)
        return buffer

    pdf_bytes = build_pdf_bytes(
        st.session_state.patient_name,
        st.session_state.patient_age,
        st.session_state.assessment_date,
        score, band, feedback
    )

    st.download_button("📄 Download Professional PDF Report",
                       data=pdf_bytes,
                       file_name=f"BDI_Report_{st.session_state.patient_name.replace(' ', '_')}_{st.session_state.assessment_date}.pdf",
                       mime="application/pdf")

    if st.button("🧪 Take again"):
        reset_assessment()
        st.rerun()
