from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Job Schemas ---
class JobBase(BaseModel):
    title: str = Field(..., json_schema_extra={"example": "Senior AI / ML Engineer"})
    department: Optional[str] = Field("Engineering", json_schema_extra={"example": "Engineering"})
    description: str = Field(..., json_schema_extra={"example": "Looking for an experienced AI engineer skilled in Python, PyTorch, LLMs, and MLOps."})
    required_skills: List[str] = Field(default_factory=list, json_schema_extra={"example": ["python", "pytorch", "transformers", "fastapi", "docker"]})
    preferred_skills: List[str] = Field(default_factory=list, json_schema_extra={"example": ["kubernetes", "langchain", "aws"]})
    min_experience: float = Field(0.0, ge=0.0, le=50.0, json_schema_extra={"example": 3.0})
    threshold: float = Field(50.0, ge=0.0, le=100.0, json_schema_extra={"example": 65.0})
    
    # Custom Weights
    weight_semantic: float = Field(0.40, ge=0.0, le=1.0)
    weight_skills: float = Field(0.35, ge=0.0, le=1.0)
    weight_experience: float = Field(0.15, ge=0.0, le=1.0)
    weight_keywords: float = Field(0.10, ge=0.0, le=1.0)

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    min_experience: Optional[float] = None
    threshold: Optional[float] = None
    weight_semantic: Optional[float] = None
    weight_skills: Optional[float] = None
    weight_experience: Optional[float] = None
    weight_keywords: Optional[float] = None

class JobResponse(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_candidates: int = 0
    shortlisted_count: int = 0


# --- Candidate Schemas ---
class CandidateBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    total_experience_years: float = 0.0
    extracted_skills: List[str] = []
    education: List[str] = []
    is_ocr_used: bool = False
    ocr_confidence: Optional[float] = None
    original_filename: str
    file_type: str
    file_size_bytes: int = 0

class CandidateResponse(CandidateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    raw_text: str
    clean_text: str
    created_at: datetime


# --- Evaluation & Ranking Schemas ---
class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    candidate_id: int
    candidate_name: str
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None
    candidate_experience: float
    original_filename: str
    file_type: str
    is_ocr_used: bool
    
    overall_score: float
    semantic_score: float
    skill_score: float
    experience_score: float
    keyword_score: float
    
    matched_skills: List[str]
    missing_skills: List[str]
    extra_skills: List[str]
    status: str
    explanation: Dict[str, Any]
    created_at: datetime


# --- Queue Task Schemas ---
class QueueTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: int
    candidate_id: Optional[int] = None
    filename: str
    file_type: str
    status: str
    progress: int
    step_message: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# --- Upload Response ---
class BatchUploadResponse(BaseModel):
    job_id: int
    enqueued_count: int
    tasks: List[QueueTaskResponse]
    message: str


# --- Status Update Schema ---
class EvaluationStatusUpdate(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "SHORTLISTED"})
