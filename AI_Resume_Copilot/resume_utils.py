from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

# Models
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# -------- TEXT PROCESSING --------
def clean_text(text):
    text = text.replace("\n", " ")
    text = " ".join(text.split())
    return text


# -------- CHUNKING --------
def chunk_text(text, chunk_size=200, overlap=50):
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)

    return chunks


# -------- FAISS --------
def create_faiss_index(chunks):
    embeddings = embedding_model.encode(chunks)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))

    return index, embeddings


def search(query, index, chunks, k=8):
    query_embedding = embedding_model.encode([query])
    distances, indices = index.search(np.array(query_embedding), k)

    results = [chunks[i] for i in indices[0]]
    return results


# -------- LLM ANSWERING --------
def generate_answer(query, context):
    prompt = f"""
You are an intelligent AI Resume Copilot.

Your job is to answer the user's question using ONLY the resume context provided.

STRICT RULES:
- Use ALL relevant information from the context
- Combine multiple parts if needed
- Do NOT hallucinate
- If not present, say: Not mentioned in the resume
- Give structured answers

Context:
{context}

Question:
{query}

Answer:
"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# -------- SKILL EXTRACTION --------
def extract_skills(text):
    prompt = f"""
Extract all technical skills from the text below.

Return ONLY a comma-separated list.
Do NOT add explanations.

Text:
{text}
"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    skills = response.choices[0].message.content
    return [s.strip().lower() for s in skills.split(",") if s.strip()]


# -------- SKILL COMPARISON --------
def compare_skills(resume_skills, jd_skills):
    matched = list(set(resume_skills) & set(jd_skills))
    missing = list(set(jd_skills) - set(resume_skills))

    score = int((len(matched) / len(jd_skills)) * 100) if jd_skills else 0

    return matched, missing, score


# -------- SUGGESTIONS --------
def generate_suggestions(missing_skills):
    if not missing_skills:
        return "Your resume is well aligned with the job description."

    prompt = f"""
A candidate is missing these skills:

{missing_skills}

Give actionable suggestions to improve their resume.
"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content