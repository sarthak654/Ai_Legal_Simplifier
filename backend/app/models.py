"""
Pydantic models for API requests and responses
"""
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    document_id: str
    filename: str

class Clause(BaseModel):
    id: int
    original_text: str
    simplified_text: str
    risk_level: RiskLevel
    risk_reasons: List[str]
    section_number: Optional[str] = None

class DocumentAnalysisResponse(BaseModel):
    success: bool
    document_id: str
    total_clauses: int
    clauses: List[Clause]
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int

class QuestionRequest(BaseModel):
    document_id: str
    question: str

class QAResponse(BaseModel):
    success: bool
    question: str
    answer: str
    relevant_clauses: List[int]  # Clause IDs
    confidence: float
    disclaimer: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None