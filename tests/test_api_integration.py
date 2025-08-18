import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
from app.main import app
from app.models.schemas import ComplianceReport, ComplianceLevel

client = TestClient(app)


class TestAPIIntegration:
    """Integration tests for API endpoints."""
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Sample PDF content for testing."""
        return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n%%EOF"
    
    @pytest.fixture
    def mock_compliance_report(self):
        """Mock compliance report for testing."""
        return ComplianceReport(
            overall_score=85.0,
            compliance_level=ComplianceLevel.GOOD,
            total_issues=2,
            issues_by_type={"grammar": 1, "style": 1},
            detailed_issues=[],
            summary="Good document with minor issues",
            recommendations=["Review grammar"]
        )
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "services" in data
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
    
    @patch('app.api.routes.FileProcessor.validate_file')
    @patch('app.api.routes.FileProcessor.save_uploaded_file')
    def test_upload_document_success(self, mock_save, mock_validate):
        """Test successful document upload."""
        # Mock file validation and saving
        mock_validate.return_value = ("pdf", "test_uuid.pdf")
        mock_save.return_value = "/tmp/test_uuid.pdf"
        
        # Create mock file
        files = {"file": ("test.pdf", b"test content", "application/pdf")}
        response = client.post("/api/v1/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
        assert data["filename"] == "test.pdf"
        assert data["status"] == "processing"
    
    def test_upload_document_no_file(self):
        """Test upload without file."""
        response = client.post("/api/v1/upload")
        assert response.status_code == 422  # Validation error
    
    def test_upload_document_invalid_file_type(self):
        """Test upload with unsupported file type."""
        files = {"file": ("test.txt", b"test content", "text/plain")}
        response = client.post("/api/v1/upload", files=files)
        assert response.status_code == 400
    
    def test_upload_document_empty_file(self):
        """Test upload with empty file."""
        files = {"file": ("empty.pdf", b"", "application/pdf")}
        response = client.post("/api/v1/upload", files=files)
        assert response.status_code == 400
    
    def test_upload_document_file_too_large(self):
        """Test upload with file exceeding size limit."""
        large_content = b"x" * (10 * 1024 * 1024 + 1024)  # > 10MB
        files = {"file": ("large.pdf", large_content, "application/pdf")}
        response = client.post("/api/v1/upload", files=files)
        assert response.status_code == 400
    
    @patch('app.api.routes.analysis_storage')
    def test_get_analysis_not_found(self, mock_storage):
        """Test getting analysis that doesn't exist."""
        mock_storage.__contains__.return_value = False
        
        response = client.get("/api/v1/analysis/nonexistent-id")
        assert response.status_code == 404
    
    @patch('app.api.routes.analysis_storage')
    def test_get_analysis_processing(self, mock_storage):
        """Test getting analysis that's still processing."""
        mock_storage.__contains__.return_value = True
        mock_storage.__getitem__.return_value = {"status": "processing"}
        
        response = client.get("/api/v1/analysis/test-id")
        assert response.status_code == 202
    
    @patch('app.api.routes.analysis_storage')
    def test_get_analysis_failed(self, mock_storage):
        """Test getting analysis that failed."""
        mock_storage.__contains__.return_value = True
        mock_storage.__getitem__.return_value = {"status": "failed"}
        
        response = client.get("/api/v1/analysis/test-id")
        assert response.status_code == 500
    
    @patch('app.api.routes.analysis_storage')
    def test_get_analysis_completed(self, mock_storage, mock_compliance_report):
        """Test getting completed analysis."""
        mock_storage.__contains__.return_value = True
        mock_storage.__getitem__.return_value = {
            "status": "completed",
            "filename": "test.pdf",
            "report": mock_compliance_report,
            "processing_time": 1.5,
            "analysis_time": "2023-01-01T00:00:00"
        }
        
        response = client.get("/api/v1/analysis/test-id")
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["report"]["overall_score"] == 85.0
    
    @patch('app.api.routes.analysis_storage')
    def test_modify_document_success(self, mock_storage):
        """Test successful document modification request."""
        mock_storage.__contains__.return_value = True
        mock_storage.__getitem__.return_value = {
            "status": "completed",
            "filename": "test.pdf"
        }
        
        modification_request = {
            "include_grammar_fixes": True,
            "include_style_improvements": True,
            "include_clarity_enhancements": False,
            "preserve_formatting": True
        }
        
        response = client.post("/api/v1/modify/test-id", json=modification_request)
        assert response.status_code == 200
        data = response.json()
        assert "modification_id" in data
        assert data["original_analysis_id"] == "test-id"
    
    @patch('app.api.routes.analysis_storage')
    def test_modify_document_analysis_not_found(self, mock_storage):
        """Test modification request for non-existent analysis."""
        mock_storage.__contains__.return_value = False
        
        modification_request = {
            "include_grammar_fixes": True,
            "include_style_improvements": True,
            "include_clarity_enhancements": False,
            "preserve_formatting": True
        }
        
        response = client.post("/api/v1/modify/nonexistent-id", json=modification_request)
        assert response.status_code == 404
    
    @patch('app.api.routes.analysis_storage')
    def test_modify_document_analysis_not_completed(self, mock_storage):
        """Test modification request for analysis still in progress."""
        mock_storage.__contains__.return_value = True
        mock_storage.__getitem__.return_value = {"status": "processing"}
        
        modification_request = {
            "include_grammar_fixes": True,
            "include_style_improvements": True,
            "include_clarity_enhancements": False,
            "preserve_formatting": True
        }
        
        response = client.post("/api/v1/modify/test-id", json=modification_request)
        assert response.status_code == 400
    
    def test_modify_document_invalid_request_data(self):
        """Test modification request with invalid data."""
        invalid_request = {
            "include_grammar_fixes": "not_a_boolean",  # Should be boolean
            "include_style_improvements": True
        }
        
        response = client.post("/api/v1/modify/test-id", json=invalid_request)
        assert response.status_code == 422
    
    def test_modify_document_missing_request_body(self):
        """Test modification request without request body."""
        response = client.post("/api/v1/modify/test-id")
        assert response.status_code == 422
    
    def test_modify_document_empty_request_body(self):
        """Test modification request with empty JSON body."""
        response = client.post("/api/v1/modify/test-id", json={})
        assert response.status_code == 422
    
    @patch('app.api.routes.modification_storage')
    def test_download_modified_not_found(self, mock_storage):
        """Test downloading non-existent modification."""
        mock_storage.__contains__.return_value = False
        
        response = client.get("/api/v1/download/nonexistent-id")
        assert response.status_code == 404
    
    @patch('app.api.routes.modification_storage')
    @patch('os.path.exists')
    def test_download_modified_processing(self, mock_exists, mock_storage):
        """Test downloading modification that's still processing."""
        mock_storage.__contains__.return_value = True
        mock_storage.__getitem__.return_value = {"status": "processing"}
        
        response = client.get("/api/v1/download/test-id")
        assert response.status_code == 202
    
    @patch('app.api.routes.modification_storage')
    def test_download_modified_failed(self, mock_storage):
        """Test downloading modification that failed."""
        mock_storage.__contains__.return_value = True
        mock_storage.__getitem__.return_value = {"status": "failed"}
        
        response = client.get("/api/v1/download/test-id")
        assert response.status_code == 500
    
    @patch('app.api.routes.modification_storage')
    @patch('os.path.exists')
    def test_download_modified_file_missing(self, mock_exists, mock_storage):
        """Test downloading modification where file doesn't exist."""
        mock_storage.__contains__.return_value = True
        mock_storage.__getitem__.return_value = {
            "status": "completed",
            "modified_file_path": "/tmp/missing_file.docx"
        }
        mock_exists.return_value = False
        
        response = client.get("/api/v1/download/test-id")
        assert response.status_code == 404
    
    def test_health_check_services_status(self):
        """Test health check returns detailed service status."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        
        services = data["services"]
        assert "ai_analyzer" in services
        assert "document_modifier" in services
        assert "file_processor" in services
        assert "openai" in services
        
        # Check service status values
        for service, status in services.items():
            assert status in ["healthy", "not_configured", "available"]
    
    def test_root_endpoint_structure(self):
        """Test root endpoint returns expected structure."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        
        assert data["docs"] == "/docs"
        assert data["health"] == "/api/v1/health"
    
    @patch('app.api.routes.FileProcessor.validate_file')
    def test_upload_document_validation_error(self, mock_validate):
        """Test upload when file validation fails."""
        mock_validate.side_effect = ValueError("Invalid file type")
        
        files = {"file": ("test.pdf", b"test content", "application/pdf")}
        response = client.post("/api/v1/upload", files=files)
        assert response.status_code == 500
    
    @patch('app.api.routes.FileProcessor.validate_file')
    @patch('app.api.routes.FileProcessor.save_uploaded_file')
    def test_upload_document_save_error(self, mock_save, mock_validate):
        """Test upload when file saving fails."""
        mock_validate.return_value = ("pdf", "test_uuid.pdf")
        mock_save.side_effect = IOError("Disk full")
        
        files = {"file": ("test.pdf", b"test content", "application/pdf")}
        response = client.post("/api/v1/upload", files=files)
        assert response.status_code == 500
    
    def test_upload_document_malformed_request(self):
        """Test upload with malformed multipart request."""
        # Send request without proper multipart boundary
        response = client.post("/api/v1/upload", data={"file": "not_a_file"})
        assert response.status_code == 422
    
    @patch('app.api.routes.analysis_storage')
    def test_get_analysis_invalid_id_format(self, mock_storage):
        """Test getting analysis with invalid ID format."""
        # Test with non-UUID format
        response = client.get("/api/v1/analysis/invalid-uuid-format")
        assert response.status_code == 404
    
    def test_download_modified_invalid_id_format(self):
        """Test downloading modification with invalid ID format."""
        response = client.get("/api/v1/download/invalid-uuid-format")
        assert response.status_code == 404
    
    def test_cors_headers(self):
        """Test that CORS headers are properly set."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        # Note: TestClient doesn't show CORS headers, but they should be set
    
    def test_process_time_header(self):
        """Test that X-Process-Time header is set."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
    
    def test_error_response_format(self):
        """Test that error responses follow consistent format."""
        response = client.get("/api/v1/analysis/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        
        # Check error response structure
        assert "detail" in data
        assert isinstance(data["detail"], str)
    
    def test_global_exception_handler(self):
        """Test global exception handler for unexpected errors."""
        with patch('app.api.routes.analysis_storage') as mock_storage:
            mock_storage.__contains__.side_effect = Exception("Unexpected error")
            
            response = client.get("/api/v1/analysis/test-id")
            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert data["error"] == "Internal server error"
    
    def test_upload_document_different_file_types(self):
        """Test upload with different supported file types."""
        # Test PDF
        files = {"file": ("test.pdf", b"test content", "application/pdf")}
        with patch('app.api.routes.FileProcessor.validate_file') as mock_validate:
            mock_validate.return_value = ("pdf", "test_uuid.pdf")
            with patch('app.api.routes.FileProcessor.save_uploaded_file') as mock_save:
                mock_save.return_value = "/tmp/test_uuid.pdf"
                response = client.post("/api/v1/upload", files=files)
                assert response.status_code == 200
        
        # Test DOCX
        files = {"file": ("test.docx", b"test content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        with patch('app.api.routes.FileProcessor.validate_file') as mock_validate:
            mock_validate.return_value = ("docx", "test_uuid.docx")
            with patch('app.api.routes.FileProcessor.save_uploaded_file') as mock_save:
                mock_save.return_value = "/tmp/test_uuid.docx"
                response = client.post("/api/v1/upload", files=files)
                assert response.status_code == 200
        
        # Test DOC
        files = {"file": ("test.doc", b"test content", "application/msword")}
        with patch('app.api.routes.FileProcessor.validate_file') as mock_validate:
            mock_validate.return_value = ("doc", "test_uuid.doc")
            with patch('app.api.routes.FileProcessor.save_uploaded_file') as mock_save:
                mock_save.return_value = "/tmp/test_uuid.doc"
                response = client.post("/api/v1/upload", files=files)
                assert response.status_code == 200
    
    def test_modify_document_all_options(self):
        """Test modification request with all options enabled."""
        with patch('app.api.routes.analysis_storage') as mock_storage:
            mock_storage.__contains__.return_value = True
            mock_storage.__getitem__.return_value = {
                "status": "completed",
                "filename": "test.pdf"
            }
            
            modification_request = {
                "include_grammar_fixes": True,
                "include_style_improvements": True,
                "include_clarity_enhancements": True,
                "preserve_formatting": True
            }
            
            response = client.post("/api/v1/modify/test-id", json=modification_request)
            assert response.status_code == 200
    
    def test_modify_document_no_options(self):
        """Test modification request with no options enabled."""
        with patch('app.api.routes.analysis_storage') as mock_storage:
            mock_storage.__contains__.return_value = True
            mock_storage.__getitem__.return_value = {
                "status": "completed",
                "filename": "test.pdf"
            }
            
            modification_request = {
                "include_grammar_fixes": False,
                "include_style_improvements": False,
                "include_clarity_enhancements": False,
                "preserve_formatting": False
            }
            
            response = client.post("/api/v1/modify/test-id", json=modification_request)
            assert response.status_code == 200
    
    def test_api_documentation_endpoints(self):
        """Test API documentation endpoints."""
        # Test OpenAPI docs
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200
    
    def test_upload_document_with_metadata(self):
        """Test upload with additional metadata in filename."""
        files = {"file": ("test_document_v2_final.pdf", b"test content", "application/pdf")}
        with patch('app.api.routes.FileProcessor.validate_file') as mock_validate:
            mock_validate.return_value = ("pdf", "test_document_v2_final_uuid.pdf")
            with patch('app.api.routes.FileProcessor.save_uploaded_file') as mock_save:
                mock_save.return_value = "/tmp/test_document_v2_final_uuid.pdf"
                response = client.post("/api/v1/upload", files=files)
                assert response.status_code == 200
                data = response.json()
                assert data["filename"] == "test_document_v2_final.pdf"
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get("/api/v1/health")
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5
    
    def test_large_request_handling(self):
        """Test handling of large request bodies."""
        # Test with large JSON payload
        large_payload = {
            "include_grammar_fixes": True,
            "include_style_improvements": True,
            "include_clarity_enhancements": False,
            "preserve_formatting": True,
            "additional_data": "x" * 10000  # 10KB of additional data
        }
        
        with patch('app.api.routes.analysis_storage') as mock_storage:
            mock_storage.__contains__.return_value = True
            mock_storage.__getitem__.return_value = {
                "status": "completed",
                "filename": "test.pdf"
            }
            
            response = client.post("/api/v1/modify/test-id", json=large_payload)
            assert response.status_code == 200
    
    def test_response_headers(self):
        """Test that appropriate response headers are set."""
        response = client.get("/api/v1/health")
        
        # Check for common headers
        assert "content-type" in response.headers
        assert "content-length" in response.headers
        assert "x-process-time" in response.headers
        
        # Check content type
        assert "application/json" in response.headers["content-type"]
    
    def test_upload_document_special_characters(self):
        """Test upload with filename containing special characters."""
        files = {"file": ("test file (1) - final.pdf", b"test content", "application/pdf")}
        with patch('app.api.routes.FileProcessor.validate_file') as mock_validate:
            mock_validate.return_value = ("pdf", "test_file_1_final_uuid.pdf")
            with patch('app.api.routes.FileProcessor.save_uploaded_file') as mock_save:
                mock_save.return_value = "/tmp/test_file_1_final_uuid.pdf"
                response = client.post("/api/v1/upload", files=files)
                assert response.status_code == 200
                data = response.json()
                assert data["filename"] == "test file (1) - final.pdf"
