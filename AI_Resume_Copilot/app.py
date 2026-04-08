import streamlit as st
import PyPDF2

from resume_utils import (
    clean_text, chunk_text, create_faiss_index, search,
    generate_answer, extract_skills, compare_skills, generate_suggestions
)

st.set_page_config(page_title="AI Resume Copilot", layout="wide")

st.title("🚀 AI Resume Copilot")

# -------- FILE UPLOAD --------
resume_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
jd_file = st.file_uploader("Upload Job Description (PDF or TXT)", type=["pdf", "txt"])


# -------- EXTRACT TEXT --------
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text

    return text


def extract_text_from_jd(file):
    if file.type == "application/pdf":
        return extract_text_from_pdf(file)
    else:
        return file.read().decode("utf-8")


# -------- MAIN LOGIC --------
if resume_file:
    st.success("Resume uploaded!")

    resume_text = extract_text_from_pdf(resume_file)
    resume_text = clean_text(resume_text)

    # RAG setup
    chunks = chunk_text(resume_text)
    index, _ = create_faiss_index(chunks)

    # Show resume
    st.subheader("📄 Resume Content")
    st.text_area("Text", resume_text, height=200)

    # -------- JD MATCHING --------
    if jd_file:
        jd_text = extract_text_from_jd(jd_file)
        jd_text = clean_text(jd_text)

        st.subheader("📊 Resume vs Job Description Analysis")

        with st.spinner("Analyzing match..."):
            resume_skills = extract_skills(resume_text)
            jd_skills = extract_skills(jd_text)

            matched, missing, score = compare_skills(resume_skills, jd_skills)
            suggestions = generate_suggestions(missing)

        # VISUALS
        st.metric("🎯 Match Score", f"{score}%")
        st.progress(score / 100)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("✅ Matched Skills")
            st.write(matched)

        with col2:
            st.subheader("❌ Missing Skills")
            st.write(missing)

        st.subheader("💡 Suggestions")
        st.write(suggestions)

    # -------- Q&A --------
    st.subheader("💬 Ask Questions About Resume")

    query = st.text_input("Enter your question")

    if query:
        with st.spinner("Thinking..."):
            results = search(query, index, chunks, k=10)
            context = "\n".join(results)

            answer = generate_answer(query, context)

        st.subheader("Answer")
        st.write(answer)