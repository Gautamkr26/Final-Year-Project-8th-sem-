# app.py — final, complete, cloud-friendly
import re
import io
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from typing import List
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

# Project modules (keep these files as-is: questions.py, utils.py, assessment.py)
from questions import bdi_questions
from assessment import MentalHealthAssessment
from utils import score_to_severity, severity_message, crisis_message, Severity

# ---------------- Page config ----------------
st.set_page_config(page_title="Mental Health Chatbot (BDI-II)", page_icon="🧠", layout="centered")

# ---------------- Helpers ----------------
def strip_leading_number(s: str) -> str:
    """Remove leading numbering like '1. ', '1) ', '1- ', '1.1. ' etc."""
    if not isinstance(s, str):
        return s
    return re.sub(r'^\s*\d+(?:\.\d+)?[\.\)\-]?\s*', '', s).strip()

def build_pdf_bytes(patient_name: str, patient_age: str, assessment_date: str,
                    score: int, band: str, prescription_text: str) -> io.BytesIO:
    """Produce a professional PDF report (wrapped text) using reportlab platypus."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer,
                            pagesize=A4,
                            rightMargin=inch,
                            leftMargin=inch,
                            topMargin=inch,
                            bottomMargin=inch)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], alignment=TA_CENTER,
                                 fontSize=18, leading=22)
    small = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=10, leading=12)
    normal = ParagraphStyle("Normal", parent=styles["BodyText"], alignment=TA_JUSTIFY,
                            fontSize=11, leading=14)

    elems = []
    elems.append(Paragraph("Mental Health Assessment Report (BDI-II)", title_style))
    elems.append(Spacer(1, 12))

    patient_block = (f"<b>Patient Name:</b> {patient_name}<br/>"
                     f"<b>Age:</b> {patient_age}<br/>"
                     f"<b>Assessment Date:</b> {assessment_date}<br/>"
                     f"<b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    elems.append(Paragraph(patient_block, small))
    elems.append(Spacer(1, 12))

    score_block = f"<b>Overall Score:</b> {score} / 63<br/><b>Severity Level:</b> {band}"
    elems.append(Paragraph(score_block, small))
    elems.append(Spacer(1, 12))

    elems.append(Paragraph("<b>Doctor's Prescription / Advice:</b>", small))
    elems.append(Spacer(1, 6))

    # Clean and split prescription lines into paragraphs
    pres_paras = [p.strip() for p in prescription_text.split("\n") if p.strip()]
    for p in pres_paras:
        elems.append(Paragraph(p, normal))
        elems.append(Spacer(1, 6))

    elems.append(Spacer(1, 20))
    footer = ("This report is for informational purposes and does not replace a clinical diagnosis. "
              "If you or someone is in immediate danger, contact local emergency services.")
    elems.append(Paragraph(footer, ParagraphStyle("Footer", fontSize=9, leading=11, alignment=TA_JUSTIFY)))

    doc.build(elems)
    buffer.seek(0)
    return buffer

def speak_browser_once(text: str):
    """Trigger browser SpeechSynthesis once for this unique text."""
    if not text:
        return
    # To avoid repeated speaking on reruns, store last spoken
    if st.session_state.get("_last_spoken", "") == text:
        return
    st.session_state["_last_spoken"] = text
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

# ---------------- Session state defaults ----------------
if "patient_name" not in st.session_state:
    st.session_state.patient_name = ""
if "patient_age" not in st.session_state:
    st.session_state.patient_age = ""
if "assessment_date" not in st.session_state:
    st.session_state.assessment_date = datetime.now().strftime("%Y-%m-%d")
if "details_done" not in st.session_state:
    st.session_state.details_done = False
if "mode" not in st.session_state:
    st.session_state.mode = "Step-by-step"  # default; sidebar will sync
if "step_index" not in st.session_state:
    st.session_state.step_index = 0
if "responses" not in st.session_state:
    st.session_state.responses = [None] * len(bdi_questions)
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "_last_spoken" not in st.session_state:
    st.session_state["_last_spoken"] = ""

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("⚙️ Settings")
    # sync mode both in sidebar and session_state
    chosen_mode = st.radio("Assessment mode", ["All at once", "Step-by-step"],
                          index=0 if st.session_state.mode == "All at once" else 1)
    st.session_state.mode = chosen_mode
    enable_tts = st.checkbox("Enable voice (TTS - browser)", value=False)
    st.markdown("**Note:** This is a self-assessment and not a diagnosis. For emergencies contact local services.")
    st.caption("PDF export requires 'reportlab' in requirements.txt")

# ---------------- Title ----------------
st.title("🧠 Mental Health Chatbot — BDI-II")
st.write("Please answer based on the last two weeks. Fill patient info first.")

# ---------------- Patient details page ----------------
if not st.session_state.details_done:
    st.subheader("🧾 Patient Information")
    st.session_state.patient_name = st.text_input("Full name", value=st.session_state.patient_name)
    st.session_state.patient_age = st.text_input("Age", value=st.session_state.patient_age)
    st.session_state.assessment_date = st.date_input(
        "Assessment Date",
        value=datetime.strptime(st.session_state.assessment_date, "%Y-%m-%d")
    ).strftime("%Y-%m-%d")

    st.markdown("Fill patient details and click **Next** to start the assessment.")
    col_l, col_r = st.columns([1, 1])
    with col_r:
        if st.button("➡️ Next to Assessment"):
            if not st.session_state.patient_name.strip() or not st.session_state.patient_age.strip():
                st.warning("Please enter both Name and Age to proceed.")
            else:
                st.session_state.details_done = True
                st.rerun()
    st.stop()  # stop rendering the rest until details are filled

# ---------------- Assessment helpers ----------------
assessment = MentalHealthAssessment(bdi_questions)
total_q = len(bdi_questions)

def current_index() -> int:
    # For step-by-step mode use step_index; for all-at-once view we still need navigation sometimes
    return st.session_state.step_index

# ---------------- Progress ----------------
answered_count = sum(1 for r in st.session_state.responses if r is not None)
st.progress(answered_count / total_q if total_q else 0.0)
st.markdown(f"**Progress:** {answered_count}/{total_q}")

# ---------------- Render questions ----------------
if not st.session_state.submitted:
    if st.session_state.mode == "All at once":
        st.header("📝 BDI-II Assessment (All at once)")
        # Render all questions
        for idx, q in enumerate(bdi_questions):
            clean_q = strip_leading_number(q.get("question", ""))
            st.markdown(f"**{idx+1}. {clean_q}**")

            # Clean options
            opts = [strip_leading_number(o) for o in q.get("options", [])]

            # Use integer options but display text via format_func, allow no default by passing index=None
            try:
                default_index = st.session_state.responses[idx] if st.session_state.responses[idx] is not None else None
            except Exception:
                default_index = None

            selected = st.radio(
                "",
                options=range(len(opts)),
                index=default_index,
                format_func=lambda i, _opts=opts: _opts[i],
                key=f"q_all_{idx}"
            )
            # radio may return an int index; store it
            if selected is not None:
                st.session_state.responses[idx] = int(selected)

            # If question 9 (index 8) has suicidal options selected (>=1), set crisis flag
            if st.session_state.responses[idx] is not None and idx == 8 and st.session_state.responses[idx] >= 1:
                st.session_state.crisis_flag = True

        # Submit button
        if st.button("🔎 Submit Assessment"):
            if any(r is None for r in st.session_state.responses):
                st.warning("Please answer all questions before submitting.")
            else:
                st.session_state.score = compute_score(st.session_state.responses) if 'compute_score' in globals() else sum(st.session_state.responses)
                st.session_state.severity = score_to_severity(st.session_state.score)
                st.session_state.submitted = True
                # Speak final feedback once if TTS enabled
                if enable_tts:
                    speak_browser_once(severity_message(st.session_state.severity))

    else:
        # Step-by-step mode
        st.header("🧭 BDI-II Assessment (Step-by-step)")
        i = current_index()
        q = bdi_questions[i]
        clean_q = strip_leading_number(q.get("question", ""))

        # Layout: question left, TTS toggle right
        colQ, colT = st.columns([5, 1])
        with colQ:
            st.markdown(f"**{i+1}. {clean_q}**")
        with colT:
            # Keep TTS toggle in the sidebar only (sync with enable_tts)
            st.write("")  # placeholder for alignment

        # Prepare options cleaned
        opts = [strip_leading_number(o) for o in q.get("options", [])]
        try:
            default_index = st.session_state.responses[i] if st.session_state.responses[i] is not None else None
        except Exception:
            default_index = None

        selected = st.radio(
            "",
            options=range(len(opts)),
            index=default_index,
            format_func=lambda j, _opts=opts: _opts[j],
            key=f"q_step_{i}"
        )
        if selected is not None:
            st.session_state.responses[i] = int(selected)

        # Set crisis flag if suicidal option selected
        if st.session_state.responses[i] is not None and i == 8 and st.session_state.responses[i] >= 1:
            st.session_state.crisis_flag = True

        # TTS read if enabled
        if enable_tts:
            speak_browser_once(clean_q)

        # Mobile-friendly navigation row
        col_back, col_next, col_submit = st.columns([1, 1, 1])
        with col_back:
            if st.button("⬅️ Back", disabled=(i == 0)):
                st.session_state.step_index = max(0, i - 1)
                st.rerun()
        with col_next:
            if st.button("➡️ Next", disabled=(st.session_state.responses[i] is None or i == total_q - 1)):
                st.session_state.step_index = min(total_q - 1, i + 1)
                st.rerun()
        with col_submit:
            if st.button("🔎 Submit", disabled=any(r is None for r in st.session_state.responses)):
                st.session_state.score = compute_score(st.session_state.responses) if 'compute_score' in globals() else sum(st.session_state.responses)
                st.session_state.severity = score_to_severity(st.session_state.score)
                st.session_state.submitted = True
                if enable_tts:
                    speak_browser_once(severity_message(st.session_state.severity))

# ---------------- Results & PDF ----------------
if st.session_state.submitted:
    # Safety: ensure score and severity exist
    score = st.session_state.get("score", sum(r for r in st.session_state.responses if r is not None))
    severity = st.session_state.get("severity", score_to_severity(score))
    band = severity.name.capitalize()
    feedback = severity_message(severity)

    st.success(f"✅ Your BDI-II Score: {score} out of 63")
    st.markdown(f"### Severity band: {band}")
    st.info(feedback)

    # Crisis alert
    if severity in (Severity.MODERATE, Severity.SEVERE) or st.session_state.get("crisis_flag", False):
        st.error(crisis_message())

    # PDF generation and download
    pdf_bytes = build_pdf_bytes(
        patient_name=st.session_state.patient_name,
        patient_age=st.session_state.patient_age,
        assessment_date=st.session_state.assessment_date,
        score=score,
        band=band,
        prescription_text=feedback
    )

    st.download_button(
        "📄 Download Professional PDF Report",
        data=pdf_bytes,
        file_name=f"BDI_Report_{st.session_state.patient_name.replace(' ', '_')}_{st.session_state.assessment_date}.pdf",
        mime="application/pdf"
    )

    # Restart options
    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("🧪 Take again"):
            # Reset responses but keep patient details
            st.session_state.responses = [None] * total_q
            st.session_state.submitted = False
            st.session_state.step_index = 0
            st.session_state._last_spoken = ""
            st.rerun()
    with col_b:
        if st.button("🏠 Start over (clear patient info)"):
            # Clear everything
            st.session_state.patient_name = ""
            st.session_state.patient_age = ""
            st.session_state.assessment_date = datetime.now().strftime("%Y-%m-%d")
            st.session_state.details_done = False
            st.session_state.responses = [None] * total_q
            st.session_state.submitted = False
            st.session_state.step_index = 0
            st.session_state._last_spoken = ""
            st.rerun()
