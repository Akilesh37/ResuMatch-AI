import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.extraction.text_extractor import extract_resume_content
from backend.app.extraction.ocr_engine import extract_text_from_image
from backend.app.nlp.nlp_processor import process_resume_nlp
from backend.app.nlp.skill_matcher import match_skills, extract_skills_from_text
from backend.app.embeddings.embedding_model import generate_embedding
from backend.app.engine.similarity_engine import evaluate_candidate_match, compute_cosine_similarity
from backend.app.database import init_db

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SAMPLES_DIR = BASE_DIR / "samples"

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_text_extraction_txt():
    txt_path = SAMPLES_DIR / "sample_ai_engineer.txt"
    with open(txt_path, "rb") as f:
        bytes_data = f.read()
    res = extract_resume_content(bytes_data, "sample_ai_engineer.txt", "text/plain")
    assert res["success"] is True
    assert "Elena Rostova" in res["text"] or "ELENA ROSTOVA" in res["text"]
    assert res["is_ocr"] is False

def test_text_extraction_docx():
    docx_path = SAMPLES_DIR / "sample_fullstack_dev.docx"
    with open(docx_path, "rb") as f:
        bytes_data = f.read()
    res = extract_resume_content(bytes_data, "sample_fullstack_dev.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    assert res["success"] is True
    assert "DAVID MILLER" in res["text"]
    assert "React" in res["text"]
    assert res["is_ocr"] is False

def test_ocr_extraction_image():
    png_path = SAMPLES_DIR / "sample_scanned_resume.png"
    if png_path.exists():
        with open(png_path, "rb") as f:
            bytes_data = f.read()
        res = extract_text_from_image(bytes_data)
        assert res["success"] is True
        assert "MICHAEL" in res["text"] or "CHANG" in res["text"] or "Data Scientist" in res["text"]

def test_nlp_processor():
    raw_text = """
    JOHN DOE
    Email: john.doe@example.com | Phone: 555-019-2834
    
    EXPERIENCE
    Software Engineer | Tech Corp (2020 - 2024)
    - Developed web services using Python, FastAPI, and Docker.
    
    SKILLS
    Python, FastAPI, Docker, Kubernetes, PostgreSQL, Git
    
    EDUCATION
    B.Tech in Computer Science (2020)
    """
    nlp = process_resume_nlp(raw_text, "John_Doe_Resume.pdf")
    assert nlp["email"] == "john.doe@example.com"
    assert nlp["phone"] is not None
    assert nlp["experience_years"] >= 3.0
    assert "python" in nlp["skills"]
    assert "fastapi" in nlp["skills"]
    assert "docker" in nlp["skills"]

def test_skill_matching():
    required = ["python", "pytorch", "docker"]
    preferred = ["kubernetes", "aws"]
    candidate = ["python", "pytorch", "docker", "fastapi", "git"]
    
    matched, missing, extra, score = match_skills(required, preferred, candidate)
    assert "python" in matched
    assert "pytorch" in matched
    assert "docker" in matched
    assert len(missing) == 0
    assert score >= 85.0

def test_embeddings_and_cosine_similarity():
    text1 = "Senior Machine Learning Engineer with PyTorch and Transformers experience"
    text2 = "AI Researcher specializing in deep learning and NLP models"
    text3 = "Pastry chef with baking and culinary experience"
    
    vec1 = generate_embedding(text1)
    vec2 = generate_embedding(text2)
    vec3 = generate_embedding(text3)
    
    sim_tech = compute_cosine_similarity(vec1, vec2)
    sim_unrelated = compute_cosine_similarity(vec1, vec3)
    
    assert sim_tech > sim_unrelated

def test_api_jobs_and_rankings_lifecycle():
    with TestClient(app) as client:
        # 1. Get templates
        res = client.get("/api/jobs/templates")
        assert res.status_code == 200
        templates = res.json()
        assert len(templates) > 0
        
        # 2. Create or verify Job
        res = client.get("/api/jobs")
        assert res.status_code == 200
        jobs = res.json()
        if len(jobs) == 0:
            tmpl = templates[0]
            create_res = client.post("/api/jobs", json=tmpl)
            assert create_res.status_code == 200
            test_job_id = create_res.json()["id"]
        else:
            test_job_id = jobs[0]["id"]
        
        # 3. Upload a resume
        sample_file_path = SAMPLES_DIR / "sample_ai_engineer.txt"
        with open(sample_file_path, "rb") as f:
            files = [("files", ("Elena_Rostova.txt", f, "text/plain"))]
            upload_res = client.post(
                "/api/resumes/upload",
                data={"job_id": test_job_id},
                files=files
            )
        assert upload_res.status_code == 200
        assert upload_res.json()["enqueued_count"] == 1
        
        # 4. Check queue status
        queue_res = client.get("/api/queue/status")
        assert queue_res.status_code == 200
        assert "stats" in queue_res.json()
