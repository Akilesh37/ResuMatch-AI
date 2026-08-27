# ResuMatch AI — Semantic Resume Screening & Ranking System

An enterprise-grade AI-powered candidate screening and resume ranking platform built with FastAPI, Optical Character Recognition (OCR), NLP skill taxonomy parsing, transformer semantic embeddings, and an asynchronous queue-driven processing pipeline.

![Architecture Diagram](https://img.shields.io/badge/Architecture-Queue%20%7C%20OCR%20%7C%20NLP%20%7C%20Transformer-6366f1?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-MiniLM--L6--v2-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![Tesseract](https://img.shields.io/badge/OCR-Tesseract%205.0-blue?style=for-the-badge)

---

## 🏛️ System Architecture

The system implements an asynchronous, modular micro-pipeline matching this flow:

```
                          ┌───────────────────────────────┐
                          │      Frontend (Web App)       │
                          │  - Job Manager & Presets      │
                          │  - Drag & Drop Batch Dropzone │
                          │  - Real-Time Queue Monitor    │
                          │  - Candidate Ranking Board    │
                          │  - OCR Inspector & Drill-down │
                          └──────────────┬────────────────┘
                                         │ HTTP / REST / SSE Stream
                                         ▼
                          ┌───────────────────────────────┐
                          │          Backend API          │
                          │     (FastAPI REST Core)       │
                          └──────┬─────────────────┬──────┘
                                 │                 │
                 (Job Profiles)  │                 │  (Enqueue Resumes)
                                 ▼                 ▼
                 ┌───────────────────┐    ┌───────────────────┐
                 │      Job DB       │    │   Resume Queue    │
                 │ (SQLite/SQLAlchemy│    │ (Async In-Memory  │
                 │  Specs & Weights) │    │ & Task Broadcast) │
                 └───────────────────┘    └────────┬──────────┘
                                                   │
                                                   ▼
                                 ┌───────────────────────────┐
                                 │     Processing Worker     │
                                 │  (Async Background Worker)│
                                 └─────────────┬─────────────┘
                                               │
                           ┌───────────────────┴───────────────────┐
                           ▼                                       ▼
               ┌───────────────────────┐               ┌───────────────────────┐
               │    Text Extraction    │               │     OCR Pipeline      │
               │  - PDF (pdfplumber)   │  (if empty/   │  - Tesseract Engine   │
               │  - DOCX (python-docx) │   scanned)    │  - PIL Preprocessing  │
               │  - Plaintext / UTF-8  │──────────────>│    (Grayscale/Thresh) │
               └───────────┬───────────┘               └───────────┬───────────┘
                           │                                       │
                           └───────────────────┬───────────────────┘
                                               │ Extracted Text & Metadata
                                               ▼
                               ┌───────────────────────────────┐
                               │        NLP Processing         │
                               │  - 1000+ Skill Taxonomy Match │
                               │  - Experience Timeline Parser │
                               │  - Contact & Section Segments │
                               └───────────────┬───────────────┘
                                               │ Normalized Features
                                               ▼
                               ┌───────────────────────────────┐
                               │        Embedding Model        │
                               │  - SentenceTransformer Model  │
                               │    (all-MiniLM-L6-v2)         │
                               │  - Dense Semantic Embeddings  │
                               └───────────────┬───────────────┘
                                               │ Vector Embeddings
                                               ▼
                               ┌───────────────────────────────┐
                               │       Similarity Engine       │
                               │  - Cosine Vector Similarity   │
                               │  - Skill Overlap Scoring      │
                               │  - Experience Gap Penalty     │
                               │  - Custom Weight Composite    │
                               └───────────────┬───────────────┘
                                               │ Final Scores & AI Analysis
                                               ▼
                               ┌───────────────────────────────┐
                               │          Ranking DB           │
                               │  (Ranked Candidates, Badges,  │
                               │   Explanations, Status)       │
                               └───────────────┬───────────────┘
                                               │
                                               ▼
                               ┌───────────────────────────────┐
                               │            Results            │
                               │  - Interactive Leaderboard    │
                               │  - Deep-Dive Modal Inspector  │
                               │  - CSV / JSON Report Export   │
                               └───────────────────────────────┘
```

---

## ✨ Key Features & Capabilities

1. **Multi-Format Ingestion with Automatic OCR Fallback**:
   - Supports **PDF**, **DOCX**, **TXT**, and **Images** (`.png`, `.jpg`, `.jpeg`, `.tiff`).
   - Automatically detects scanned/image-based PDFs or image resumes and routes them through the **Tesseract OCR Pipeline** with image binarization and contrast enhancement.

2. **NLP Engine & Comprehensive Skill Taxonomy**:
   - Boundary-safe keyword extraction matching over 1,000 technical, cloud, AI, data science, database, DevOps, and soft skills with automatic alias normalization (e.g. `k8s` ➔ `kubernetes`, `react.js` ➔ `react`).
   - Parses date intervals and employment timelines to accurately calculate candidate years of experience.

3. **Dense Transformer Semantic Embeddings**:
   - Leverages `sentence-transformers` (`all-MiniLM-L6-v2`) to capture deep contextual semantics between job requirements and candidate profiles beyond simple keyword matching.

4. **Multi-Factor Hybrid Similarity Engine**:
   - Combines 4 orthogonal dimensions:
     - **Semantic Fit** ($40\%$ default)
     - **Skill Alignment** ($35\%$ default)
     - **Experience Alignment** ($15\%$ default)
     - **Keyword & Action Verb Strength** ($10\%$ default)
   - Scoring weights are fully customizable per job opening.

5. **Asynchronous Resume Queue & Live SSE Stream**:
   - Batch uploads are enqueued without blocking the web application.
   - Real-time pipeline status updates (Extracting ➔ OCR ➔ NLP ➔ Embedding ➔ Scoring ➔ Completed) stream straight into the browser using Server-Sent Events (SSE).

6. **Rich Interactive Recruiter Dashboard**:
   - Leaderboard with gold/silver/bronze rankings, score vector progress bars, skill match chips, and eligibility indicators.
   - Deep-dive candidate inspector with full OCR raw text viewer, AI strength/gap analysis, and recruiter decision buttons (Shortlist, Under Review, Reject).
   - 1-click export to CSV / JSON reports.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Python 3.13 supported)
- Tesseract OCR (Pre-installed on macOS via `brew install tesseract` or Ubuntu via `apt-get install tesseract-ocr`)

### 2. Installation & Run
```bash
# Clone the repository
git clone https://github.com/Akilesh37/Semantic-Resume-Screening-System.git
cd Semantic-Resume-Screening-System

# Run the 1-click start script (creates venv, installs requirements, launches server)
./start.sh
```

Or run manually:
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Accessing the System
- **Web UI Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **API Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Testing with Pre-built Samples

The system includes realistic multi-format sample resumes in `samples/`:
- `sample_ai_engineer.txt` — Senior AI/ML Engineer profile
- `sample_fullstack_dev.docx` — Full-Stack Developer Microsoft Word document
- `sample_devops_engineer.txt` — Cloud DevOps & Infrastructure specialist
- `sample_scanned_resume.png` — Scanned image resume for OCR testing

You can also click the **Instant Test with Samples** buttons directly inside the web UI on the **Batch Resume Ingestion** page!

---

## 📂 Project Structure

```
ai-resume-checker/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI Application entrypoint & routes
│   │   ├── config.py                # System paths, OCR configs, scoring weights
│   │   ├── database.py              # SQLite & SQLAlchemy session management
│   │   ├── models.py                # Database models (Job, Candidate, Evaluation, QueueTask)
│   │   ├── schemas.py               # Pydantic validation schemas
│   │   ├── queue/
│   │   │   └── task_queue.py        # Async Resume Queue & SSE event broadcaster
│   │   ├── worker/
│   │   │   └── processing_worker.py # Background pipeline orchestrator
│   │   ├── extraction/
│   │   │   ├── text_extractor.py    # Multi-format parser (PDF, DOCX, TXT)
│   │   │   └── ocr_engine.py        # Tesseract OCR & image enhancement
│   │   ├── nlp/
│   │   │   ├── nlp_processor.py     # Section segmentation & experience timeline parsing
│   │   │   └── skill_matcher.py     # 1000+ skill taxonomy & synonym matcher
│   │   ├── embeddings/
│   │   │   └── embedding_model.py   # Sentence-Transformers semantic embeddings
│   │   ├── engine/
│   │   │   └── similarity_engine.py # Hybrid multi-factor scoring algorithm
│   │   └── routes/
│   │       ├── jobs.py              # Job DB CRUD & industry templates
│   │       ├── resumes.py           # Batch resume upload & ingestion
│   │       ├── rankings.py          # Candidate rankings, details, and export
│   │       └── queue_status.py      # Real-time SSE stream & queue stats
│   ├── tests/
│   │   └── test_pipeline.py         # Complete automated test suite
│   └── generate_samples.py          # Sample resume generator
├── frontend/
│   ├── index.html                   # Modern glassmorphism single-page UI
│   ├── css/
│   │   └── styles.css               # Design system, micro-animations, responsive layout
│   └── js/
│       ├── api.js                   # API & SSE client
│       ├── app.js                   # Main application controller
│       └── components/
│           ├── jobManager.js        # Job DB & criteria manager
│           ├── uploader.js          # Drag & drop batch uploader
│           ├── queueMonitor.js      # Visual real-time queue tracker
│           ├── rankingBoard.js      # Leaderboard table, filters & sorting
│           └── candidateModal.js    # OCR text inspector & recruiter actions
├── samples/                         # Sample test resumes (.txt, .docx, .png)
├── storage/                         # Persistent SQLite DB & uploaded documents
├── requirements.txt                 # Python dependencies
├── start.sh                         # 1-click startup shell script
└── README.md                        # Project documentation
```

---

## 🛠️ REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/jobs` | List all job openings with candidate counts |
| `POST` | `/api/jobs` | Create a new job requirement & precalculate embedding |
| `GET` | `/api/jobs/templates` | Retrieve preset industry job requirement templates |
| `POST` | `/api/resumes/upload` | Upload batch resumes and enqueue into Resume Queue |
| `GET` | `/api/queue/status` | Get queue metrics and active processing tasks |
| `GET` | `/api/queue/stream` | Server-Sent Events (SSE) live task progress stream |
| `GET` | `/api/jobs/{id}/rankings` | Get ranked candidates evaluated for a job |
| `GET` | `/api/candidates/{id}` | Get candidate details, extracted text, and OCR status |
| `PATCH`| `/api/evaluations/{id}/status` | Update candidate shortlisting status |
| `GET` | `/api/jobs/{id}/export` | Export ranking leaderboard as CSV or JSON report |

---

## 📜 License
MIT License. Built for enterprise semantic recruitment and automated resume screening.
