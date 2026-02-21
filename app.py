import streamlit as st
import pdfplumber
from docx import Document

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="Resume Checker", layout="centered")
st.title("Resume Checker")

# -------------------- SESSION STATE INIT --------------------
if "page" not in st.session_state:
    st.session_state.page = 1   # 1 = Requirements, 2 = Upload, 3 = Score

# -------------------- TEXT EXTRACTION FUNCTION --------------------
@st.cache_data(show_spinner=False)
def extract_resume_text(file_bytes, file_type):
    text = ""
    try:
        if file_type == "application/pdf":
            with pdfplumber.open(file_bytes) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(file_bytes)
            text = "\n".join(
                para.text for para in doc.paragraphs if para.text.strip()
            )
    except Exception as e:
        return f"Error: {e}"

    return " ".join(text.lower().split())


# -------------------- PAGE 1: JOB REQUIREMENTS --------------------
if st.session_state.page == 1:
    st.header("📋 Job Requirements (Admin)")

    job_title = st.text_input("Job Title")

    required_skills = st.text_area(
        "Required Skills (comma separated)",
        placeholder="python, django, sql"
    )

    min_experience = st.number_input(
        "Minimum Experience (Years)",
        min_value=0,
        max_value=20
    )

    threshold = st.slider(
        "Shortlisting Threshold",
        min_value=0,
        max_value=100,
        value=25
    )

    if st.button("Next → Upload Resume"):
        st.session_state.job = {
            "title": job_title,
            "skills": [s.strip().lower() for s in required_skills.split(",")],
            "experience": min_experience,
            "threshold": threshold
        }
        st.session_state.page = 2
        st.rerun()


# -------------------- PAGE 2: RESUME UPLOAD --------------------
elif st.session_state.page == 2:
    st.header("📄 Upload Resume")

    uploaded_file = st.file_uploader(
        "Upload Resume (PDF or DOCX)",
        type=["pdf", "docx"]
    )

    if uploaded_file:
        with st.spinner("Extracting resume text..."):
            resume_text = extract_resume_text(
                uploaded_file,
                uploaded_file.type
            )

        if resume_text.startswith("Error"):
            st.error(resume_text)
        else:
            st.success("Text extracted successfully!")

            st.text_area(
                "Extracted Resume Text",
                resume_text,
                height=250
            )

            if st.button("Next → Calculate Score"):
                st.session_state.resume_text = resume_text
                st.session_state.page = 3
                st.rerun()

    if st.button("⬅ Back to Requirements"):
        st.session_state.page = 1
        st.rerun()


# -------------------- PAGE 3: SCORING PAGE --------------------
elif st.session_state.page == 3:
    st.header("📊 Resume Evaluation Result")

    resume_text = st.session_state.resume_text
    job = st.session_state.job

    score = 0

    # Skill Matching (60 Marks)
    matched_skills = [
        skill for skill in job["skills"] if skill in resume_text
    ]

    if job["skills"]:
        score += int((len(matched_skills) / len(job["skills"])) * 60)

    # Experience Match (20 Marks)
    if job["experience"] == 0 or str(job["experience"]) in resume_text:
        score += 20

    # Keyword Strength (20 Marks)
    keywords = ["project", "internship", "experience", "developed", "built"]
    keyword_hits = sum(1 for k in keywords if k in resume_text)
    score += min(keyword_hits * 4, 20)

    # Status
    status = "✅ ELIGIBLE" if score >= job["threshold"] else "❌ NOT ELIGIBLE"

    # -------------------- DISPLAY --------------------
    st.metric("Final Score", f"{score} / 100")
    st.subheader(status)

    st.write("### Matched Skills")
    st.write(", ".join(matched_skills) if matched_skills else "None")

    if st.button("⬅ Upload Another Resume"):
        st.session_state.page = 2
        st.rerun()

    if st.button("🔁 Start New Job Requirement"):
        st.session_state.page = 1
        st.rerun()
