from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"


class ComplianceLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class IssueType(str, Enum):
    GRAMMAR = "grammar"
    SPELLING = "spelling"
    STYLE = "style"
    CLARITY = "clarity"
    STRUCTURE = "structure"


class ComplianceIssue(BaseModel):
    """Represents a single compliance issue found in the document."""
    issue_type: IssueType
    severity: str = Field(..., description="Severity level: low, medium, high, critical")
    message: str = Field(..., description="Description of the issue")
    suggestion: str = Field(..., description="Suggested correction")
    line_number: Optional[int] = Field(None, description="Line number where issue occurs")
    context: Optional[str] = Field(None, description="Context around the issue")


class ComplianceReport(BaseModel):
    """Complete compliance analysis report."""
    overall_score: float = Field(..., ge=0, le=100, description="Overall compliance score")
    compliance_level: ComplianceLevel
    total_issues: int = Field(..., ge=0, description="Total number of issues found")
    issues_by_type: Dict[str, int] = Field(..., description="Issues grouped by type")
    detailed_issues: List[ComplianceIssue] = Field(..., description="Detailed list of issues")
    summary: str = Field(..., description="Executive summary of the analysis")
    recommendations: List[str] = Field(..., description="General recommendations for improvement")


class UploadResponse(BaseModel):
    """Response model for document upload."""
    analysis_id: str = Field(..., description="Unique identifier for the analysis")
    filename: str = Field(..., description="Original filename")
    file_type: FileType = Field(..., description="Type of uploaded file")
    file_size: int = Field(..., description="File size in bytes")
    upload_time: datetime = Field(..., description="Upload timestamp")
    status: str = Field(..., description="Processing status")


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""
    analysis_id: str = Field(..., description="Analysis identifier")
    filename: str = Field(..., description="Original filename")
    report: ComplianceReport = Field(..., description="Compliance analysis report")
    processing_time: float = Field(..., description="Processing time in seconds")
    analysis_time: datetime = Field(..., description="Analysis completion timestamp")


class ModificationRequest(BaseModel):
    """Request model for document modification."""
    include_grammar_fixes: bool = Field(True, description="Include grammar corrections")
    include_style_improvements: bool = Field(True, description="Include style improvements")
    include_clarity_enhancements: bool = Field(True, description="Include clarity enhancements")
    preserve_formatting: bool = Field(True, description="Preserve original formatting")
    custom_instructions: Optional[str] = Field(None, description="Additional modification instructions")


class ModificationResponse(BaseModel):
    """Response model for document modification."""
    modification_id: str = Field(..., description="Unique identifier for the modification")
    original_analysis_id: str = Field(..., description="Original analysis identifier")
    filename: str = Field(..., description="Modified filename")
    download_url: str = Field(..., description="URL to download modified document")
    changes_summary: Dict[str, int] = Field(..., description="Summary of changes made")
    processing_time: float = Field(..., description="Processing time in seconds")
    modification_time: datetime = Field(..., description="Modification completion timestamp")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.now)
    services: Dict[str, str] = Field(..., description="Status of dependent services")
