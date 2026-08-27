import os
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import STATIC_DIR
from .database import init_db, SessionLocal
from .models import Job
from .worker.processing_worker import processing_worker
from .embeddings.embedding_model import generate_embedding, serialize_embedding
from .routes.jobs import router as jobs_router, PRESET_TEMPLATES
from .routes.resumes import router as resumes_router
from .routes.rankings import router as rankings_router
from .routes.queue_status import router as queue_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ai_resume_system")

def seed_initial_templates():
    """Populate default job templates into Job DB if empty."""
    db = SessionLocal()
    try:
        count = db.query(Job).count()
        if count == 0:
            logger.info("Seeding initial job templates into Job DB...")
            for tmpl in PRESET_TEMPLATES:
                job_embed_text = f"{tmpl['title']} {tmpl['description']} Required Skills: {', '.join(tmpl['required_skills'])}"
                embed_vec = generate_embedding(job_embed_text)
                
                job = Job(
                    title=tmpl["title"],
                    department=tmpl["department"],
                    description=tmpl["description"],
                    required_skills=json.dumps(tmpl["required_skills"]),
                    preferred_skills=json.dumps(tmpl["preferred_skills"]),
                    min_experience=tmpl["min_experience"],
                    threshold=tmpl["threshold"],
                    weight_semantic=tmpl["weight_semantic"],
                    weight_skills=tmpl["weight_skills"],
                    weight_experience=tmpl["weight_experience"],
                    weight_keywords=tmpl["weight_keywords"],
                    embedding=serialize_embedding(embed_vec)
                )
                db.add(job)
            db.commit()
            logger.info("Seeded 4 industry job templates successfully.")
    except Exception as e:
        logger.warning(f"Failed to seed job templates: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle manager."""
    logger.info("Initializing Database...")
    init_db()
    
    logger.info("Checking initial templates...")
    seed_initial_templates()
    
    logger.info("Starting Background Processing Worker...")
    processing_worker.start()
    
    yield
    
    logger.info("Shutting down Background Processing Worker...")
    await processing_worker.stop()

app = FastAPI(
    title="Semantic Resume Screening System API",
    description="Enterprise-grade AI-powered resume screening, OCR, NLP skill extraction, and transformer semantic ranking engine.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(jobs_router)
app.include_router(resumes_router)
app.include_router(rankings_router)
app.include_router(queue_router)

# Mount Static Files (Frontend)
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Semantic Resume Screening System API is active. Visit /docs for API documentation."}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Semantic Resume Screening System",
        "version": "2.0.0"
    }
