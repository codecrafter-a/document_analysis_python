import time
import uuid
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from app.models.schemas import (
    UploadResponse, AnalysisResponse, ModificationRequest, 
    ModificationResponse, ErrorResponse, HealthCheckResponse,
    FileType
)
from app.services.ai_analyzer import AIAnalyzer
from app.services.document_modifier import DocumentModifier
from app.utils.file_processor import FileProcessor
from app.config import settings
import os

# In-memory storage for demo purposes
# In production, use a proper database
analysis_storage: Dict[str, Dict[str, Any]] = {}
modification_storage: Dict[str, Dict[str, Any]] = {}

router = APIRouter()

# Initialize services
ai_analyzer = AIAnalyzer()
document_modifier = DocumentModifier()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    services_status = {
        "ai_analyzer": "healthy",
        "document_modifier": "healthy",
        "file_processor": "healthy"
    }
    
    # Check if OpenAI is available
    if not settings.openai_api_key:
        services_status["openai"] = "not_configured"
    else:
        services_status["openai"] = "available"
    
    return HealthCheckResponse(
        status="healthy",
        version=settings.version,
        services=services_status
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload and analyze a document for compliance checking.
    
    Supports PDF and Word documents (DOCX, DOC).
    """
    try:
        # Validate and save file
        file_type, safe_filename = FileProcessor.validate_file(file)
        file_path = await FileProcessor.save_uploaded_file(file, safe_filename)
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Store basic information
        analysis_storage[analysis_id] = {
            'analysis_id': analysis_id,
            'filename': file.filename,
            'file_type': file_type,
            'file_path': file_path,
            'file_size': file.size,
            'upload_time': datetime.now(),
            'status': 'processing'
        }
        
        # Start background analysis
        background_tasks.add_task(
            process_document_analysis,
            analysis_id,
            file_path,
            file_type
        )
        
        return UploadResponse(
            analysis_id=analysis_id,
            filename=file.filename,
            file_type=FileType(file_type),
            file_size=file.size,
            upload_time=datetime.now(),
            status="processing"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_results(analysis_id: str):
    """
    Get the results of document analysis.
    
    Returns detailed compliance report with issues and recommendations.
    """
    if analysis_id not in analysis_storage:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis_data = analysis_storage[analysis_id]
    
    if analysis_data['status'] == 'processing':
        raise HTTPException(status_code=202, detail="Analysis still in progress")
    
    if analysis_data['status'] == 'failed':
        raise HTTPException(status_code=500, detail="Analysis failed")
    
    return AnalysisResponse(
        analysis_id=analysis_id,
        filename=analysis_data['filename'],
        report=analysis_data['report'],
        processing_time=analysis_data.get('processing_time', 0),
        analysis_time=analysis_data['analysis_time']
    )


@router.post("/modify/{analysis_id}", response_model=ModificationResponse)
async def modify_document(
    analysis_id: str,
    modification_request: ModificationRequest,
    background_tasks: BackgroundTasks
):
    """
    Request AI-powered modifications to improve document compliance.
    
    Uses the analysis results to generate an improved version of the document.
    """
    if analysis_id not in analysis_storage:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis_data = analysis_storage[analysis_id]
    
    if analysis_data['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Analysis must be completed before modification")
    
    # Generate modification ID
    modification_id = str(uuid.uuid4())
    
    # Store modification request
    modification_storage[modification_id] = {
        'modification_id': modification_id,
        'original_analysis_id': analysis_id,
        'request': modification_request,
        'status': 'processing'
    }
    
    # Start background modification
    background_tasks.add_task(
        process_document_modification,
        modification_id,
        analysis_id,
        modification_request
    )
    
    return ModificationResponse(
        modification_id=modification_id,
        original_analysis_id=analysis_id,
        filename=f"{analysis_data['filename']}_improved",
        download_url=f"/download/{modification_id}",
        changes_summary={},
        processing_time=0,
        modification_time=datetime.now()
    )


@router.get("/download/{modification_id}")
async def download_modified_document(modification_id: str):
    """
    Download the modified document.
    
    Returns the improved version of the original document.
    """
    if modification_id not in modification_storage:
        raise HTTPException(status_code=404, detail="Modification not found")
    
    modification_data = modification_storage[modification_id]
    
    if modification_data['status'] == 'processing':
        raise HTTPException(status_code=202, detail="Modification still in progress")
    
    if modification_data['status'] == 'failed':
        raise HTTPException(status_code=500, detail="Modification failed")
    
    file_path = modification_data['modified_file_path']
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Modified file not found")
    
    return FileResponse(
        path=file_path,
        filename=modification_data['modified_filename'],
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


# Background task functions
async def process_document_analysis(analysis_id: str, file_path: str, file_type: str):
    """Background task to process document analysis."""
    try:
        start_time = time.time()
        
        # Extract text from document
        text_content = FileProcessor.extract_text_from_file(file_path, file_type)
        
        # Perform AI analysis
        report = await ai_analyzer.analyze_document(text_content)
        
        processing_time = time.time() - start_time
        
        # Update storage
        analysis_storage[analysis_id].update({
            'report': report,
            'processing_time': processing_time,
            'analysis_time': datetime.now(),
            'status': 'completed'
        })
        
        # Clean up original file after successful analysis
        FileProcessor.cleanup_file(file_path)
        
    except Exception as e:
        analysis_storage[analysis_id].update({
            'status': 'failed',
            'error': str(e)
        })
        print(f"Analysis failed for {analysis_id}: {e}")


async def process_document_modification(
    modification_id: str, 
    analysis_id: str, 
    modification_request: ModificationRequest
):
    """Background task to process document modification."""
    try:
        start_time = time.time()
        
        analysis_data = analysis_storage[analysis_id]
        file_path = analysis_data['file_path']
        file_type = analysis_data['file_type']
        issues = analysis_data['report'].detailed_issues
        
        # Perform document modification
        modification_result = await document_modifier.modify_document(
            file_path,
            file_type,
            issues,
            modification_request
        )
        
        processing_time = time.time() - start_time
        
        # Update storage
        modification_storage[modification_id].update({
            'modified_filename': modification_result['modified_filename'],
            'modified_file_path': modification_result['modified_file_path'],
            'changes_summary': modification_result['changes_summary'],
            'processing_time': processing_time,
            'modification_time': datetime.now(),
            'status': 'completed'
        })
        
    except Exception as e:
        modification_storage[modification_id].update({
            'status': 'failed',
            'error': str(e)
        })
        print(f"Modification failed for {modification_id}: {e}")


# Note: Exception handlers should be registered at the app level, not router level
# These are handled in main.py
