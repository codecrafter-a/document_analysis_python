import pytest
from datetime import datetime
from app.models.schemas import (
    ComplianceReport, ComplianceIssue, IssueType, ComplianceLevel,
    UploadResponse, AnalysisResponse, ModificationRequest, ModificationResponse,
    ErrorResponse, HealthCheckResponse, FileType
)


class TestComplianceIssue:
    """Test cases for ComplianceIssue model."""
    
    def test_compliance_issue_creation(self):
        """Test creating a ComplianceIssue instance."""
        issue = ComplianceIssue(
            issue_type=IssueType.GRAMMAR,
            severity="medium",
            message="Grammar error found",
            suggestion="Fix the grammar",
            context="Sample text with error"
        )
        
        assert issue.issue_type == IssueType.GRAMMAR
        assert issue.severity == "medium"
        assert issue.message == "Grammar error found"
        assert issue.suggestion == "Fix the grammar"
        assert issue.context == "Sample text with error"
        assert issue.line_number is None
    
    def test_compliance_issue_with_line_number(self):
        """Test creating a ComplianceIssue with line number."""
        issue = ComplianceIssue(
            issue_type=IssueType.STYLE,
            severity="high",
            message="Style issue",
            suggestion="Improve style",
            context="Sample text",
            line_number=5
        )
        
        assert issue.line_number == 5
    
    def test_compliance_issue_validation(self):
        """Test ComplianceIssue validation."""
        # Valid severity levels
        valid_severities = ["low", "medium", "high", "critical"]
        
        for severity in valid_severities:
            issue = ComplianceIssue(
                issue_type=IssueType.GRAMMAR,
                severity=severity,
                message="Test message",
                suggestion="Test suggestion",
                context="Test context"
            )
            assert issue.severity == severity
    
    def test_compliance_issue_issue_types(self):
        """Test all issue types."""
        issue_types = [
            IssueType.GRAMMAR,
            IssueType.SPELLING,
            IssueType.STYLE,
            IssueType.CLARITY,
            IssueType.STRUCTURE
        ]
        
        for issue_type in issue_types:
            issue = ComplianceIssue(
                issue_type=issue_type,
                severity="medium",
                message="Test message",
                suggestion="Test suggestion",
                context="Test context"
            )
            assert issue.issue_type == issue_type


class TestComplianceReport:
    """Test cases for ComplianceReport model."""
    
    def test_compliance_report_creation(self):
        """Test creating a ComplianceReport instance."""
        issues = [
            ComplianceIssue(
                issue_type=IssueType.GRAMMAR,
                severity="medium",
                message="Grammar error",
                suggestion="Fix grammar",
                context="Sample text"
            )
        ]
        
        report = ComplianceReport(
            overall_score=85.0,
            compliance_level=ComplianceLevel.GOOD,
            total_issues=1,
            issues_by_type={"grammar": 1},
            detailed_issues=issues,
            summary="Good document with minor issues",
            recommendations=["Review grammar"]
        )
        
        assert report.overall_score == 85.0
        assert report.compliance_level == ComplianceLevel.GOOD
        assert report.total_issues == 1
        assert report.issues_by_type == {"grammar": 1}
        assert len(report.detailed_issues) == 1
        assert report.summary == "Good document with minor issues"
        assert report.recommendations == ["Review grammar"]
    
    def test_compliance_report_no_issues(self):
        """Test creating a ComplianceReport with no issues."""
        report = ComplianceReport(
            overall_score=100.0,
            compliance_level=ComplianceLevel.EXCELLENT,
            total_issues=0,
            issues_by_type={},
            detailed_issues=[],
            summary="Perfect document",
            recommendations=[]
        )
        
        assert report.overall_score == 100.0
        assert report.compliance_level == ComplianceLevel.EXCELLENT
        assert report.total_issues == 0
        assert len(report.detailed_issues) == 0
    
    def test_compliance_report_validation(self):
        """Test ComplianceReport validation."""
        # Score should be between 0 and 100
        with pytest.raises(ValueError):
            ComplianceReport(
                overall_score=150.0,  # Invalid score
                compliance_level=ComplianceLevel.GOOD,
                total_issues=0,
                issues_by_type={},
                detailed_issues=[],
                summary="Test",
                recommendations=[]
            )
        
        with pytest.raises(ValueError):
            ComplianceReport(
                overall_score=-10.0,  # Invalid score
                compliance_level=ComplianceLevel.GOOD,
                total_issues=0,
                issues_by_type={},
                detailed_issues=[],
                summary="Test",
                recommendations=[]
            )
    
    def test_compliance_level_mapping(self):
        """Test compliance level mapping."""
        # Test all compliance levels
        levels = [
            ComplianceLevel.EXCELLENT,
            ComplianceLevel.GOOD,
            ComplianceLevel.FAIR,
            ComplianceLevel.POOR
        ]
        
        for level in levels:
            report = ComplianceReport(
                overall_score=85.0,
                compliance_level=level,
                total_issues=0,
                issues_by_type={},
                detailed_issues=[],
                summary="Test",
                recommendations=[]
            )
            assert report.compliance_level == level


class TestUploadResponse:
    """Test cases for UploadResponse model."""
    
    def test_upload_response_creation(self):
        """Test creating an UploadResponse instance."""
        response = UploadResponse(
            analysis_id="test-uuid-123",
            filename="test.pdf",
            file_type=FileType.PDF,
            file_size=1024,
            upload_time=datetime.now(),
            status="processing"
        )
        
        assert response.analysis_id == "test-uuid-123"
        assert response.filename == "test.pdf"
        assert response.file_type == FileType.PDF
        assert response.file_size == 1024
        assert response.status == "processing"
    
    def test_upload_response_file_types(self):
        """Test all file types."""
        file_types = [FileType.PDF, FileType.DOCX, FileType.DOC]
        
        for file_type in file_types:
            response = UploadResponse(
                analysis_id="test-uuid",
                filename="test.file",
                file_type=file_type,
                file_size=1024,
                upload_time=datetime.now(),
                status="processing"
            )
            assert response.file_type == file_type
    
    def test_upload_response_status_values(self):
        """Test status values."""
        status_values = ["processing", "completed", "failed"]
        
        for status in status_values:
            response = UploadResponse(
                analysis_id="test-uuid",
                filename="test.pdf",
                file_type=FileType.PDF,
                file_size=1024,
                upload_time=datetime.now(),
                status=status
            )
            assert response.status == status


class TestAnalysisResponse:
    """Test cases for AnalysisResponse model."""
    
    def test_analysis_response_creation(self):
        """Test creating an AnalysisResponse instance."""
        report = ComplianceReport(
            overall_score=85.0,
            compliance_level=ComplianceLevel.GOOD,
            total_issues=1,
            issues_by_type={"grammar": 1},
            detailed_issues=[],
            summary="Good document",
            recommendations=["Review grammar"]
        )
        
        response = AnalysisResponse(
            analysis_id="test-uuid-123",
            filename="test.pdf",
            report=report,
            processing_time=1.5,
            analysis_time=datetime.now()
        )
        
        assert response.analysis_id == "test-uuid-123"
        assert response.filename == "test.pdf"
        assert response.report == report
        assert response.processing_time == 1.5
    
    def test_analysis_response_validation(self):
        """Test AnalysisResponse validation."""
        report = ComplianceReport(
            overall_score=85.0,
            compliance_level=ComplianceLevel.GOOD,
            total_issues=0,
            issues_by_type={},
            detailed_issues=[],
            summary="Test",
            recommendations=[]
        )
        
        # Processing time should be non-negative
        with pytest.raises(ValueError):
            AnalysisResponse(
                analysis_id="test-uuid",
                filename="test.pdf",
                report=report,
                processing_time=-1.0,  # Invalid time
                analysis_time=datetime.now()
            )


class TestModificationRequest:
    """Test cases for ModificationRequest model."""
    
    def test_modification_request_creation(self):
        """Test creating a ModificationRequest instance."""
        request = ModificationRequest(
            include_grammar_fixes=True,
            include_style_improvements=True,
            include_clarity_enhancements=False,
            preserve_formatting=True
        )
        
        assert request.include_grammar_fixes is True
        assert request.include_style_improvements is True
        assert request.include_clarity_enhancements is False
        assert request.preserve_formatting is True
    
    def test_modification_request_all_false(self):
        """Test ModificationRequest with all options disabled."""
        request = ModificationRequest(
            include_grammar_fixes=False,
            include_style_improvements=False,
            include_clarity_enhancements=False,
            preserve_formatting=False
        )
        
        assert request.include_grammar_fixes is False
        assert request.include_style_improvements is False
        assert request.include_clarity_enhancements is False
        assert request.preserve_formatting is False
    
    def test_modification_request_validation(self):
        """Test ModificationRequest validation."""
        # At least one modification option should be enabled
        with pytest.raises(ValueError):
            ModificationRequest(
                include_grammar_fixes=False,
                include_style_improvements=False,
                include_clarity_enhancements=False,
                preserve_formatting=False
            )


class TestModificationResponse:
    """Test cases for ModificationResponse model."""
    
    def test_modification_response_creation(self):
        """Test creating a ModificationResponse instance."""
        response = ModificationResponse(
            modification_id="mod-uuid-123",
            original_analysis_id="analysis-uuid-123",
            filename="test_improved.docx",
            download_url="/download/mod-uuid-123",
            changes_summary={"total_changes": 2, "changes_by_type": {"grammar": 1, "style": 1}},
            processing_time=2.5,
            modification_time=datetime.now()
        )
        
        assert response.modification_id == "mod-uuid-123"
        assert response.original_analysis_id == "analysis-uuid-123"
        assert response.filename == "test_improved.docx"
        assert response.download_url == "/download/mod-uuid-123"
        assert response.changes_summary["total_changes"] == 2
        assert response.processing_time == 2.5
    
    def test_modification_response_validation(self):
        """Test ModificationResponse validation."""
        # Processing time should be non-negative
        with pytest.raises(ValueError):
            ModificationResponse(
                modification_id="mod-uuid",
                original_analysis_id="analysis-uuid",
                filename="test.docx",
                download_url="/download/mod-uuid",
                changes_summary={},
                processing_time=-1.0,  # Invalid time
                modification_time=datetime.now()
            )


class TestErrorResponse:
    """Test cases for ErrorResponse model."""
    
    def test_error_response_creation(self):
        """Test creating an ErrorResponse instance."""
        response = ErrorResponse(
            error="File not found",
            detail="The requested file could not be found",
            timestamp=datetime.now()
        )
        
        assert response.error == "File not found"
        assert response.detail == "The requested file could not be found"
    
    def test_error_response_with_code(self):
        """Test creating an ErrorResponse with status code."""
        response = ErrorResponse(
            error="Validation error",
            detail="Invalid input data",
            status_code=400,
            timestamp=datetime.now()
        )
        
        assert response.error == "Validation error"
        assert response.status_code == 400


class TestHealthCheckResponse:
    """Test cases for HealthCheckResponse model."""
    
    def test_health_check_response_creation(self):
        """Test creating a HealthCheckResponse instance."""
        services = {
            "ai_analyzer": "healthy",
            "document_modifier": "healthy",
            "file_processor": "healthy",
            "openai": "available"
        }
        
        response = HealthCheckResponse(
            status="healthy",
            version="1.0.0",
            services=services
        )
        
        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.services == services
    
    def test_health_check_response_status_values(self):
        """Test health check status values."""
        status_values = ["healthy", "unhealthy", "degraded"]
        
        for status in status_values:
            response = HealthCheckResponse(
                status=status,
                version="1.0.0",
                services={}
            )
            assert response.status == status


class TestFileType:
    """Test cases for FileType enum."""
    
    def test_file_type_values(self):
        """Test FileType enum values."""
        assert FileType.PDF == "pdf"
        assert FileType.DOCX == "docx"
        assert FileType.DOC == "doc"
    
    def test_file_type_members(self):
        """Test FileType enum members."""
        assert FileType.PDF in FileType
        assert FileType.DOCX in FileType
        assert FileType.DOC in FileType
        assert "txt" not in FileType


class TestModelSerialization:
    """Test cases for model serialization."""
    
    def test_compliance_issue_serialization(self):
        """Test ComplianceIssue serialization."""
        issue = ComplianceIssue(
            issue_type=IssueType.GRAMMAR,
            severity="medium",
            message="Grammar error",
            suggestion="Fix grammar",
            context="Sample text"
        )
        
        # Convert to dict
        issue_dict = issue.dict()
        
        assert issue_dict["issue_type"] == "grammar"
        assert issue_dict["severity"] == "medium"
        assert issue_dict["message"] == "Grammar error"
        assert issue_dict["suggestion"] == "Fix grammar"
        assert issue_dict["context"] == "Sample text"
    
    def test_compliance_report_serialization(self):
        """Test ComplianceReport serialization."""
        report = ComplianceReport(
            overall_score=85.0,
            compliance_level=ComplianceLevel.GOOD,
            total_issues=1,
            issues_by_type={"grammar": 1},
            detailed_issues=[],
            summary="Good document",
            recommendations=["Review grammar"]
        )
        
        # Convert to dict
        report_dict = report.dict()
        
        assert report_dict["overall_score"] == 85.0
        assert report_dict["compliance_level"] == "good"
        assert report_dict["total_issues"] == 1
        assert report_dict["issues_by_type"] == {"grammar": 1}
        assert report_dict["summary"] == "Good document"
        assert report_dict["recommendations"] == ["Review grammar"]
    
    def test_upload_response_serialization(self):
        """Test UploadResponse serialization."""
        response = UploadResponse(
            analysis_id="test-uuid",
            filename="test.pdf",
            file_type=FileType.PDF,
            file_size=1024,
            upload_time=datetime.now(),
            status="processing"
        )
        
        # Convert to dict
        response_dict = response.dict()
        
        assert response_dict["analysis_id"] == "test-uuid"
        assert response_dict["filename"] == "test.pdf"
        assert response_dict["file_type"] == "pdf"
        assert response_dict["file_size"] == 1024
        assert response_dict["status"] == "processing"
    
    def test_modification_request_serialization(self):
        """Test ModificationRequest serialization."""
        request = ModificationRequest(
            include_grammar_fixes=True,
            include_style_improvements=True,
            include_clarity_enhancements=False,
            preserve_formatting=True
        )
        
        # Convert to dict
        request_dict = request.dict()
        
        assert request_dict["include_grammar_fixes"] is True
        assert request_dict["include_style_improvements"] is True
        assert request_dict["include_clarity_enhancements"] is False
        assert request_dict["preserve_formatting"] is True


class TestModelValidation:
    """Test cases for model validation."""
    
    def test_compliance_issue_required_fields(self):
        """Test ComplianceIssue required fields."""
        # Should work with all required fields
        issue = ComplianceIssue(
            issue_type=IssueType.GRAMMAR,
            severity="medium",
            message="Test message",
            suggestion="Test suggestion",
            context="Test context"
        )
        assert issue is not None
    
    def test_compliance_report_required_fields(self):
        """Test ComplianceReport required fields."""
        # Should work with all required fields
        report = ComplianceReport(
            overall_score=85.0,
            compliance_level=ComplianceLevel.GOOD,
            total_issues=0,
            issues_by_type={},
            detailed_issues=[],
            summary="Test summary",
            recommendations=[]
        )
        assert report is not None
    
    def test_upload_response_required_fields(self):
        """Test UploadResponse required fields."""
        # Should work with all required fields
        response = UploadResponse(
            analysis_id="test-uuid",
            filename="test.pdf",
            file_type=FileType.PDF,
            file_size=1024,
            upload_time=datetime.now(),
            status="processing"
        )
        assert response is not None
    
    def test_analysis_response_required_fields(self):
        """Test AnalysisResponse required fields."""
        report = ComplianceReport(
            overall_score=85.0,
            compliance_level=ComplianceLevel.GOOD,
            total_issues=0,
            issues_by_type={},
            detailed_issues=[],
            summary="Test",
            recommendations=[]
        )
        
        response = AnalysisResponse(
            analysis_id="test-uuid",
            filename="test.pdf",
            report=report,
            processing_time=1.0,
            analysis_time=datetime.now()
        )
        assert response is not None


class TestModelEdgeCases:
    """Test cases for model edge cases."""
    
    def test_compliance_issue_empty_strings(self):
        """Test ComplianceIssue with empty strings."""
        issue = ComplianceIssue(
            issue_type=IssueType.GRAMMAR,
            severity="medium",
            message="",
            suggestion="",
            context=""
        )
        
        assert issue.message == ""
        assert issue.suggestion == ""
        assert issue.context == ""
    
    def test_compliance_report_zero_score(self):
        """Test ComplianceReport with zero score."""
        report = ComplianceReport(
            overall_score=0.0,
            compliance_level=ComplianceLevel.POOR,
            total_issues=10,
            issues_by_type={"grammar": 5, "style": 5},
            detailed_issues=[],
            summary="Poor document",
            recommendations=["Major improvements needed"]
        )
        
        assert report.overall_score == 0.0
        assert report.compliance_level == ComplianceLevel.POOR
    
    def test_compliance_report_max_score(self):
        """Test ComplianceReport with maximum score."""
        report = ComplianceReport(
            overall_score=100.0,
            compliance_level=ComplianceLevel.EXCELLENT,
            total_issues=0,
            issues_by_type={},
            detailed_issues=[],
            summary="Perfect document",
            recommendations=[]
        )
        
        assert report.overall_score == 100.0
        assert report.compliance_level == ComplianceLevel.EXCELLENT
    
    def test_upload_response_large_file(self):
        """Test UploadResponse with large file size."""
        response = UploadResponse(
            analysis_id="test-uuid",
            filename="large_file.pdf",
            file_type=FileType.PDF,
            file_size=100 * 1024 * 1024,  # 100MB
            upload_time=datetime.now(),
            status="processing"
        )
        
        assert response.file_size == 100 * 1024 * 1024
    
    def test_modification_response_long_filename(self):
        """Test ModificationResponse with long filename."""
        long_filename = "very_long_filename_that_exceeds_normal_length_limits_for_testing_purposes.docx"
        
        response = ModificationResponse(
            modification_id="mod-uuid",
            original_analysis_id="analysis-uuid",
            filename=long_filename,
            download_url="/download/mod-uuid",
            changes_summary={},
            processing_time=1.0,
            modification_time=datetime.now()
        )
        
        assert response.filename == long_filename
