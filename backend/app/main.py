"""
FastAPI main application for AI Legal Simplifier & Q&A Assistant
"""
import os
import uuid
import logging
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import *
from .config import *
from .services.document_processor import DocumentProcessor
from .services.clause_splitter import ClauseSplitter
from .services.simplifier import LegalSimplifier
from .services.risk_detector import RiskDetector
from .services.qa_engine import QAEngine
from .utils.embeddings import EmbeddingManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Legal Simplifier & Q&A Assistant",
    description="A privacy-first legal document simplifier using local AI",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_processor = DocumentProcessor()
clause_splitter = ClauseSplitter()
simplifier = LegalSimplifier(model_name=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
risk_detector = RiskDetector()
embedding_manager = EmbeddingManager(model_name=EMBEDDING_MODEL, vector_store_dir=VECTOR_STORE_DIR)
qa_engine = QAEngine(embedding_manager, simplifier)

# Store processed documents in memory (in production, use a database)
processed_documents = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AI Legal Simplifier & Q&A Assistant API",
        "status": "running",
        "disclaimer": LEGAL_DISCLAIMER
    }

@app.get("/test-model")
async def test_model():
    """Test if the LLM model is working properly"""
    success, message = simplifier.test_model()
    return {
        "model_working": success,
        "message": message,
        "model_name": simplifier.model_name
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    # Check Ollama connection
    ollama_status = simplifier._check_ollama_connection()
    
    return {
        "api": "healthy",
        "ollama": "connected" if ollama_status else "disconnected",
        "model": OLLAMA_MODEL,
        "embedding_model": EMBEDDING_MODEL,
        "upload_dir": str(UPLOAD_DIR),
        "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024)
    }

@app.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a legal document"""
    try:
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024 * 1024):.1f}MB"
            )
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Save uploaded file
        file_path = UPLOAD_DIR / f"{document_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Validate PDF
        is_valid, error_msg = document_processor.validate_pdf(file_path, MAX_FILE_SIZE)
        if not is_valid:
            file_path.unlink()  # Delete invalid file
            raise HTTPException(status_code=400, detail=error_msg)
        
        logger.info(f"Successfully uploaded document {document_id}: {file.filename}")
        
        return DocumentUploadResponse(
            success=True,
            message="Document uploaded successfully. Processing will begin shortly.",
            document_id=document_id,
            filename=file.filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/analyze/{document_id}", response_model=DocumentAnalysisResponse)
async def analyze_document(document_id: str):
    """Analyze uploaded document: extract text, split clauses, simplify, and detect risks"""
    try:
        # Find the uploaded file
        uploaded_files = list(UPLOAD_DIR.glob(f"{document_id}_*"))
        if not uploaded_files:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = uploaded_files[0]
        
        # Step 1: Extract text from PDF
        logger.info(f"Extracting text from {file_path.name}")
        success, extracted_text, error = document_processor.extract_text_from_pdf(file_path)
        if not success:
            raise HTTPException(status_code=400, detail=f"Text extraction failed: {error}")
        
        # Step 2: Split into clauses
        logger.info("Splitting document into clauses")
        raw_clauses = clause_splitter.split_document(extracted_text)
        if not raw_clauses:
            raise HTTPException(status_code=400, detail="No clauses could be extracted from the document")
        
        # Step 3: Process each clause (simplify + risk detection)
        logger.info(f"Processing {len(raw_clauses)} clauses")
        processed_clauses = []
        
        for raw_clause in raw_clauses:
            # Simplify clause
            success, simplified_text, error = simplifier.simplify_clause(raw_clause['text'])
            if not success:
                logger.warning(f"Failed to simplify clause {raw_clause['id']}: {error}")
                simplified_text = "Could not simplify this clause safely."
            
            # Detect risk
            risk_level, risk_reasons = risk_detector.analyze_risk(raw_clause['text'])
            
            # Create clause object
            clause = Clause(
                id=raw_clause['id'],
                original_text=raw_clause['text'],
                simplified_text=simplified_text,
                risk_level=risk_level,
                risk_reasons=risk_reasons,
                section_number=raw_clause.get('section_number')
            )
            processed_clauses.append(clause)
        
        # Step 4: Create embeddings for Q&A
        logger.info("Creating embeddings for Q&A system")
        clause_dicts = [clause.dict() for clause in processed_clauses]
        success, error = embedding_manager.create_embeddings(clause_dicts)
        if not success:
            logger.warning(f"Failed to create embeddings: {error}")
        else:
            # Save embeddings
            embedding_manager.save_index(document_id)
        
        # Calculate risk summary
        risk_summary = risk_detector.get_risk_summary(clause_dicts)
        
        # Store processed document
        processed_documents[document_id] = {
            'filename': file_path.name,
            'clauses': processed_clauses,
            'processed_at': str(Path().cwd())
        }
        
        logger.info(f"Successfully analyzed document {document_id}")
        
        return DocumentAnalysisResponse(
            success=True,
            document_id=document_id,
            total_clauses=len(processed_clauses),
            clauses=processed_clauses,
            high_risk_count=risk_summary.get('HIGH', 0),
            medium_risk_count=risk_summary.get('MEDIUM', 0),
            low_risk_count=risk_summary.get('LOW', 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/ask", response_model=QAResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question about the document"""
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Check if document exists
        if request.document_id not in processed_documents:
            raise HTTPException(status_code=404, detail="Document not found or not processed")
        
        # Answer the question
        success, answer, relevant_clause_ids, confidence = qa_engine.answer_question(
            request.document_id, 
            request.question
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Q&A failed: {answer}")
        
        return QAResponse(
            success=True,
            question=request.question,
            answer=answer,
            relevant_clauses=relevant_clause_ids,
            confidence=confidence,
            disclaimer=LEGAL_DISCLAIMER
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=f"Q&A failed: {str(e)}")

@app.get("/document/{document_id}/clauses")
async def get_document_clauses(document_id: str):
    """Get all clauses for a document"""
    if document_id not in processed_documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "document_id": document_id,
        "clauses": processed_documents[document_id]['clauses']
    }

@app.get("/document/{document_id}/summary")
async def get_document_summary(document_id: str):
    """Get a summary of the document"""
    try:
        success, summary = qa_engine.get_document_summary(document_id)
        if not success:
            raise HTTPException(status_code=500, detail=summary)
        
        return {
            "document_id": document_id,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/document/{document_id}")
async def delete_document(document_id: str):
    """Delete a processed document and its files"""
    try:
        # Remove from memory
        if document_id in processed_documents:
            del processed_documents[document_id]
        
        # Delete uploaded file
        uploaded_files = list(UPLOAD_DIR.glob(f"{document_id}_*"))
        for file_path in uploaded_files:
            file_path.unlink()
        
        # Delete vector store
        embedding_manager.delete_index(document_id)
        
        return {"success": True, "message": "Document deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

@app.get("/documents")
async def list_documents():
    """List all processed documents"""
    documents = []
    for doc_id, doc_info in processed_documents.items():
        documents.append({
            "document_id": doc_id,
            "filename": doc_info['filename'],
            "clause_count": len(doc_info['clauses']),
            "processed_at": doc_info['processed_at']
        })
    
    return {"documents": documents}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)