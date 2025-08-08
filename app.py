# app.py — Final Mobile-Friendly Version
import re
import io
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

from questions import bdi_questions
from assessment import MentalHealthAssessment
from utils import score_to_severity, severity_message, crisis_message, Severity

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="Mental Health Chatbot (BDI-II)", page_icon="🧠", layout="centered")

# ---------------------- HELPERS ----------------------
def strip_leading_number(s: str) -> str:
    return re.sub(r'^\s*\d+(?:\.\d+)?[\.\)\-]?\s*', '', s).strip() if isinstance(s, str) else s

def build_pdf(patient_name, patient_age, assessment_date, score, severity_band, prescription):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=18, leading=22)
    small = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=10, leading=12)
    normal = ParagraphStyle("Normal", parent=styles["BodyText"], alignment=TA_JUSTIFY, fontSize=11, leading=14)

    elems = [
        Paragraph("Mental Health Assessment Report (BDI-II)", title),
        Spacer(1, 12),
        Paragraph(f"<b>Patient Name:</b> {patient_name}<br/><b>Age:</b> {patient_age}<br/>"
                  f"<b>Assessment Date:</b> {assessment_date}<br/>"
                  f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", small),
        Spacer(1, 12),
        Paragraph(f"<b>Score:</b> {score} / 63<br/><b>Severity:</b> {severity_band}", small),
        Spacer(1, 12),
        Paragraph("<b>Doctor's Prescription / Advice:</b>", small),
        Spacer(1, 6)
    ]

    for p in [line.strip() for line in prescription.split("\n") if line.strip()]:
        elems.append(Paragraph(p, normal))
        elems.append(Spacer(1, 6))

    elems.append(Spacer(1, 20))
    elems.append(Paragraph(
        "This report is for informational purposes only and does not replace a professional diagnosis.",
        ParagraphStyle("Footer", fontSize=9, leading=11, alignment=TA_JUSTIFY)
    ))

    doc.build(elems)
    buffer.seek(0)
    return buffer

def speak_browser_once(text: str):
    if not text or st.session_state.get("_last_spoken") == text:
        return
    st.session_state["_last_spoken"] = text
    escaped = text.replace('"', '\\"').replace("\n", "\\n")
    components.html(f"""
    <script>
    var u = new SpeechSynthesisUtterance("{escaped}");
    u.lang = 'en-US';
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
    </script>
    """, height=0)

# ---------------------- STATE INIT ----------------------
if "patient_name" not in st.session_state:
    st.session_state.update({
        "patient_name": "",
        "patient_age": "",
        "assessment_date": datetime.now().strftime("%Y-%m-%d"),
        "details_done": False,
        "mode": "Step-by-step",
        "step_index": 0,
        "responses": [None] * len(bdi_questions),
        "submitted": False,
        "_last_spoken": ""
    })

# ---------------------- SIDEBAR ----------------------
with st.sidebar:
    st.header("⚙️ Settings")
    st.session_state.mode = st.radio("Assessment mode", ["All at once", "Step-by-step"], index=1)
    enable_tts = st.checkbox("Enable voice (TTS - browser)", value=False)
    st.markdown("This is a self-assessment. For emergencies contact local services.")

# ---------------------- TITLE ----------------------
st.title("🧠 Mental Health Chatbot — BDI-II")

# ---------------------- PATIENT DETAILS ----------------------
if not st.session_state.details_done:
    st.subheader("🧾 Patient Information")
    st.session_state.patient_name = st.text_input("Full name", value=st.session_state.patient_name)
    st.session_state.patient_age = st.text_input("Age", value=st.session_state.patient_age)
    st.session_state.assessment_date = st.date_input(
        "Assessment Date", datetime.strptime(st.session_state.assessment_date, "%Y-%m-%d")
    ).strftime("%Y-%m-%d")

    if st.button("➡️ Next to Assessment"):
        if not st.session_state.patient_name.strip() or not st.session_state.patient_age.strip():
            st.warning("Please enter both Name and Age.")
        else:
            st.session_state.details_done = True
            st.rerun()
    st.stop()

# ---------------------- ASSESSMENT ----------------------
assessment = MentalHealthAssessment(bdi_questions)
total_q = len(bdi_questions)
answered = sum(1 for r in st.session_state.responses if r is not None)
st.progress(answered / total_q)
st.markdown(f"**Progress:** {answered}/{total_q}")

# ---- ALL AT ONCE MODE ----
if not st.session_state.submitted and st.session_state.mode == "All at once":
    st.header("📝 Assessment — All at once")
    for idx, q in enumerate(bdi_questions):
        clean_q = strip_leading_number(q["question"])
        st.markdown(f"**{idx+1}. {clean_q}**")
        opts = [strip_leading_number(o) for o in q["options"]]
        default = st.session_state.responses[idx] if st.session_state.responses[idx] is not None else None
        selected = st.radio("", options=range(len(opts)), index=default,
                            format_func=lambda i, _opts=opts: _opts[i], key=f"q_all_{idx}")
        if selected is not None:
            st.session_state.responses[idx] = int(selected)

    if st.button("🔍 Submit Assessment"):
        if None in st.session_state.responses:
            st.warning("Please answer all questions.")
        else:
            st.session_state.score = sum(st.session_state.responses)
            st.session_state.severity = score_to_severity(st.session_state.score)
            st.session_state.submitted = True
            if enable_tts:
                speak_browser_once(severity_message(st.session_state.severity))

# ---- STEP BY STEP MODE ----
elif not st.session_state.submitted:
    st.header("🧭 Assessment — Step-by-step")
    i = st.session_state.step_index
    q = bdi_questions[i]
    clean_q = strip_leading_number(q["question"])
    st.markdown(f"**{i+1}. {clean_q}**")
    opts = [strip_leading_number(o) for o in q["options"]]
    default = st.session_state.responses[i] if st.session_state.responses[i] is not None else None
    selected = st.radio("", options=range(len(opts)), index=default,
                        format_func=lambda j, _opts=opts: _opts[j], key=f"q_step_{i}")
    if selected is not None:
        st.session_state.responses[i] = int(selected)
    if enable_tts:
        speak_browser_once(clean_q)

    # ---- MOBILE-FRIENDLY BUTTONS ----
    st.markdown("""
    <style>
    .button-row { display: flex; justify-content: space-between; gap: 8px; }
    .button-row button { flex: 1; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="button-row">', unsafe_allow_html=True)
    if st.button("⬅️ Back", disabled=(i == 0)):
        st.session_state.step_index = max(0, i - 1)
        st.rerun()
    if st.button("➡️ Next", disabled=(st.session_state.responses[i] is None or i == total_q - 1)):
        st.session_state.step_index = min(total_q - 1, i + 1)
        st.rerun()
    if st.button("🔍 Submit", disabled=any(r is None for r in st.session_state.responses)):
        st.session_state.score = sum(st.session_state.responses)
        st.session_state.severity = score_to_severity(st.session_state.score)
        st.session_state.submitted = True
        if enable_tts:
            speak_browser_once(severity_message(st.session_state.severity))
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------- RESULTS ----------------------
if st.session_state.submitted:
    score = st.session_state.score
    severity = st.session_state.severity
    band = severity.name.capitalize()

    st.success(f"✅ Your Score: {score}/63")
    st.info(severity_message(severity))
    if severity in (Severity.MODERATE, Severity.SEVERE):
        st.error(crisis_message())

    pdf_data = build_pdf(
        st.session_state.patient_name, st.session_state.patient_age, st.session_state.assessment_date,
        score, band, severity_message(severity)
    )

    st.download_button("📄 Download PDF Report", data=pdf_data,
                       file_name=f"BDI_Report_{st.session_state.patient_name.replace(' ', '_')}.pdf",
                       mime="application/pdf")

    if st.button("🧪 Take Again"):
        st.session_state.responses = [None] * total_q
        st.session_state.submitted = False
        st.session_state.step_index = 0
        st.rerun()

    if st.button("🏠 Start Over"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
