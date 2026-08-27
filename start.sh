#!/usr/bin/env bash
# ResuMatch AI - Production Startup Script

set -e

# Change directory to project root
cd "$(dirname "$0")"

echo "================================================================="
echo "   🚀 Starting ResuMatch AI — Semantic Resume Screening System   "
echo "================================================================="

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Ensure storage directories exist
mkdir -p storage/uploads storage/processed

# Generate sample files if not existing
if [ ! -f "samples/sample_fullstack_dev.docx" ]; then
    echo "Generating test sample resumes..."
    python backend/generate_samples.py
fi

echo "Starting FastAPI Server on http://127.0.0.1:8000..."
echo "Open your browser at: http://127.0.0.1:8000"
echo "API Swagger Documentation at: http://127.0.0.1:8000/docs"
echo "================================================================="

export PYTHONPATH=.
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
