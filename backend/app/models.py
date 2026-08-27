import datetime
import json
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    department = Column(String(255), default="General")
    description = Column(Text, nullable=False)
    
    # Skills stored as JSON strings: '["python", "fastapi", "docker"]'
    required_skills = Column(Text, default="[]")
    preferred_skills = Column(Text, default="[]")
    
    min_experience = Column(Float, default=0.0)
    threshold = Column(Float, default=50.0)
    
    # Custom scoring weights
    weight_semantic = Column(Float, default=0.40)
    weight_skills = Column(Float, default=0.35)
    weight_experience = Column(Float, default=0.15)
    weight_keywords = Column(Float, default=0.10)
    
    # Serialized embedding vector
    embedding = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    evaluations = relationship("EvaluationResult", back_populates="job", cascade="all, delete-orphan")
    queue_tasks = relationship("QueueTask", back_populates="job", cascade="all, delete-orphan")

    def get_required_skills_list(self):
        try:
            return json.loads(self.required_skills) if self.required_skills else []
        except Exception:
            return []

    def get_preferred_skills_list(self):
        try:
            return json.loads(self.preferred_skills) if self.preferred_skills else []
        except Exception:
            return []


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), default="Anonymous Candidate")
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(100), nullable=True)
    
    total_experience_years = Column(Float, default=0.0)
    
    # Stored as JSON strings
    extracted_skills = Column(Text, default="[]")
    education = Column(Text, default="[]")
    work_history = Column(Text, default="[]")
    
    raw_text = Column(Text, nullable=False)
    clean_text = Column(Text, nullable=False)
    
    is_ocr_used = Column(Boolean, default=False)
    ocr_confidence = Column(Float, nullable=True)
    
    file_path = Column(String(512), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    
    # Serialized embedding vector
    embedding = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    evaluations = relationship("EvaluationResult", back_populates="candidate", cascade="all, delete-orphan")
    queue_tasks = relationship("QueueTask", back_populates="candidate")

    def get_skills_list(self):
        try:
            return json.loads(self.extracted_skills) if self.extracted_skills else []
        except Exception:
            return []

    def get_education_list(self):
        try:
            return json.loads(self.education) if self.education else []
        except Exception:
            return []


class EvaluationResult(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    
    overall_score = Column(Float, nullable=False, index=True)  # 0 to 100
    semantic_score = Column(Float, nullable=False)            # 0 to 100
    skill_score = Column(Float, nullable=False)               # 0 to 100
    experience_score = Column(Float, nullable=False)          # 0 to 100
    keyword_score = Column(Float, nullable=False)             # 0 to 100
    
    # Stored as JSON strings
    matched_skills = Column(Text, default="[]")
    missing_skills = Column(Text, default="[]")
    extra_skills = Column(Text, default="[]")
    
    # Status: 'SHORTLISTED', 'ELIGIBLE', 'UNDER_REVIEW', 'REJECTED'
    status = Column(String(50), default="UNDER_REVIEW", index=True)
    
    # JSON breakdown & explanations
    explanation = Column(Text, default="{}")
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="evaluations")
    candidate = relationship("Candidate", back_populates="evaluations")

    def get_matched_skills_list(self):
        try:
            return json.loads(self.matched_skills) if self.matched_skills else []
        except Exception:
            return []

    def get_missing_skills_list(self):
        try:
            return json.loads(self.missing_skills) if self.missing_skills else []
        except Exception:
            return []

    def get_explanation_dict(self):
        try:
            return json.loads(self.explanation) if self.explanation else {}
        except Exception:
            return {}


class QueueTask(Base):
    __tablename__ = "queue_tasks"

    id = Column(String(64), primary_key=True, index=True)  # UUID or task token
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True)
    
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    
    # Status: 'QUEUED', 'EXTRACTING', 'OCR', 'NLP_PROCESSING', 'EMBEDDING', 'SCORING', 'COMPLETED', 'FAILED'
    status = Column(String(50), default="QUEUED", index=True)
    progress = Column(Integer, default=0)  # 0 - 100%
    step_message = Column(String(255), default="Task queued")
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="queue_tasks")
    candidate = relationship("Candidate", back_populates="queue_tasks")
