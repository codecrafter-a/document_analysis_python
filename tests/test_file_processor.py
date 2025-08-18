import pytest
import os
import tempfile
from unittest.mock import Mock, patch, mock_open
from fastapi import UploadFile
from app.utils.file_processor import FileProcessor
from app.config import settings
from unittest.mock import AsyncMock


class TestFileProcessor:
    """Test cases for FileProcessor utility."""
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Sample PDF content for testing."""
        return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n%%EOF"
    
    @pytest.fixture
    def sample_docx_content(self):
        """Sample DOCX content for testing."""
        return b"PK\x03\x04\x14\x00\x00\x00\x08\x00"  # DOCX file signature
    
    @pytest.fixture
    def mock_upload_file(self):
        """Create a mock UploadFile for testing."""
        return Mock(spec=UploadFile)
    
    def test_validate_file_pdf_success(self, mock_upload_file, sample_pdf_content):
        """Test successful PDF file validation."""
        mock_upload_file.filename = "test.pdf"
        mock_upload_file.content_type = "application/pdf"
        mock_upload_file.size = len(sample_pdf_content)
        
        file_type, safe_filename = FileProcessor.validate_file(mock_upload_file)
        
        assert file_type == "pdf"
        assert safe_filename.endswith(".pdf")
        assert "test" in safe_filename
    
    def test_validate_file_docx_success(self, mock_upload_file, sample_docx_content):
        """Test successful DOCX file validation."""
        mock_upload_file.filename = "test.docx"
        mock_upload_file.content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        mock_upload_file.size = len(sample_docx_content)
        
        file_type, safe_filename = FileProcessor.validate_file(mock_upload_file)
        
        assert file_type == "docx"
        assert safe_filename.endswith(".docx")
        assert "test" in safe_filename
    
    def test_validate_file_doc_success(self, mock_upload_file):
        """Test successful DOC file validation."""
        mock_upload_file.filename = "test.doc"
        mock_upload_file.content_type = "application/msword"
        mock_upload_file.size = 1024
        
        file_type, safe_filename = FileProcessor.validate_file(mock_upload_file)
        
        assert file_type == "doc"
        assert safe_filename.endswith(".doc")
        assert "test" in safe_filename
    
    def test_validate_file_invalid_extension(self, mock_upload_file):
        """Test validation with invalid file extension."""
        mock_upload_file.filename = "test.txt"
        mock_upload_file.content_type = "text/plain"
        mock_upload_file.size = 1024
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            FileProcessor.validate_file(mock_upload_file)
    
    def test_validate_file_no_extension(self, mock_upload_file):
        """Test validation with file without extension."""
        mock_upload_file.filename = "test"
        mock_upload_file.content_type = "application/octet-stream"
        mock_upload_file.size = 1024
        
        with pytest.raises(ValueError, match="No file extension found"):
            FileProcessor.validate_file(mock_upload_file)
    
    def test_validate_file_too_large(self, mock_upload_file):
        """Test validation with file exceeding size limit."""
        mock_upload_file.filename = "test.pdf"
        mock_upload_file.content_type = "application/pdf"
        mock_upload_file.size = settings.max_file_size + 1024  # Exceeds limit
        
        with pytest.raises(ValueError, match="File size exceeds maximum allowed"):
            FileProcessor.validate_file(mock_upload_file)
    
    def test_validate_file_empty(self, mock_upload_file):
        """Test validation with empty file."""
        mock_upload_file.filename = "test.pdf"
        mock_upload_file.content_type = "application/pdf"
        mock_upload_file.size = 0
        
        with pytest.raises(ValueError, match="File is empty"):
            FileProcessor.validate_file(mock_upload_file)
    
    def test_validate_file_no_filename(self, mock_upload_file):
        """Test validation with missing filename."""
        mock_upload_file.filename = None
        mock_upload_file.content_type = "application/pdf"
        mock_upload_file.size = 1024
        
        with pytest.raises(ValueError, match="No filename provided"):
            FileProcessor.validate_file(mock_upload_file)
    
    def test_validate_file_special_characters(self, mock_upload_file):
        """Test validation with filename containing special characters."""
        mock_upload_file.filename = "test file (1).pdf"
        mock_upload_file.content_type = "application/pdf"
        mock_upload_file.size = 1024
        
        file_type, safe_filename = FileProcessor.validate_file(mock_upload_file)
        
        assert file_type == "pdf"
        assert safe_filename.endswith(".pdf")
        # Should sanitize special characters
        assert "test_file_1" in safe_filename
    
    @pytest.mark.asyncio
    async def test_save_uploaded_file_success(self, mock_upload_file, sample_pdf_content):
        """Test successful file saving."""
        mock_upload_file.filename = "test.pdf"
        mock_upload_file.content_type = "application/pdf"
        mock_upload_file.size = len(sample_pdf_content)
        
        # Mock file reading
        mock_upload_file.read = AsyncMock(return_value=sample_pdf_content)
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.join', return_value="/tmp/test.pdf"):
                file_path = await FileProcessor.save_uploaded_file(mock_upload_file, "test.pdf")
        
        assert file_path == "/tmp/test.pdf"
        mock_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_uploaded_file_io_error(self, mock_upload_file):
        """Test file saving with IO error."""
        mock_upload_file.filename = "test.pdf"
        mock_upload_file.content_type = "application/pdf"
        mock_upload_file.size = 1024
        mock_upload_file.read = AsyncMock(side_effect=IOError("Disk full"))
        
        with pytest.raises(IOError, match="Disk full"):
            await FileProcessor.save_uploaded_file(mock_upload_file, "test.pdf")
    
    def test_extract_text_from_pdf(self, sample_pdf_content):
        """Test PDF text extraction."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(sample_pdf_content)
            temp_file_path = temp_file.name
        
        try:
            # Mock PyPDF2 or similar PDF library
            with patch('app.utils.file_processor.PyPDF2') as mock_pypdf2:
                mock_reader = Mock()
                mock_page = Mock()
                mock_page.extract_text.return_value = "Extracted text from PDF"
                mock_reader.pages = [mock_page]
                mock_pypdf2.PdfReader.return_value = mock_reader
                
                text = FileProcessor.extract_text_from_file(temp_file_path, "pdf")
                assert text == "Extracted text from PDF"
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_text_from_docx(self, sample_docx_content):
        """Test DOCX text extraction."""
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_file.write(sample_docx_content)
            temp_file_path = temp_file.name
        
        try:
            # Mock python-docx library
            with patch('app.utils.file_processor.Document') as mock_document:
                mock_doc = Mock()
                mock_paragraph = Mock()
                mock_paragraph.text = "Extracted text from DOCX"
                mock_doc.paragraphs = [mock_paragraph]
                mock_document.return_value = mock_doc
                
                text = FileProcessor.extract_text_from_file(temp_file_path, "docx")
                assert text == "Extracted text from DOCX"
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_text_from_doc(self):
        """Test DOC text extraction."""
        with tempfile.NamedTemporaryFile(suffix='.doc', delete=False) as temp_file:
            temp_file.write(b"Sample DOC content")
            temp_file_path = temp_file.name
        
        try:
            # Mock textract or similar library
            with patch('app.utils.file_processor.textract') as mock_textract:
                mock_textract.process.return_value = b"Extracted text from DOC"
                
                text = FileProcessor.extract_text_from_file(temp_file_path, "doc")
                assert text == "Extracted text from DOC"
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_text_unsupported_type(self):
        """Test text extraction with unsupported file type."""
        with pytest.raises(ValueError, match="Unsupported file type for text extraction"):
            FileProcessor.extract_text_from_file("test.txt", "txt")
    
    def test_extract_text_file_not_found(self):
        """Test text extraction with non-existent file."""
        with pytest.raises(FileNotFoundError):
            FileProcessor.extract_text_from_file("nonexistent.pdf", "pdf")
    
    def test_extract_text_extraction_error(self):
        """Test text extraction with extraction error."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"Invalid PDF content")
            temp_file_path = temp_file.name
        
        try:
            with patch('app.utils.file_processor.PyPDF2') as mock_pypdf2:
                mock_pypdf2.PdfReader.side_effect = Exception("PDF parsing error")
                
                with pytest.raises(Exception, match="PDF parsing error"):
                    FileProcessor.extract_text_from_file(temp_file_path, "pdf")
        finally:
            os.unlink(temp_file_path)
    
    def test_cleanup_file_success(self):
        """Test successful file cleanup."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        # Verify file exists
        assert os.path.exists(temp_file_path)
        
        # Clean up file
        FileProcessor.cleanup_file(temp_file_path)
        
        # Verify file is deleted
        assert not os.path.exists(temp_file_path)
    
    def test_cleanup_file_not_found(self):
        """Test file cleanup with non-existent file."""
        # Should not raise an error for non-existent files
        FileProcessor.cleanup_file("nonexistent_file.pdf")
    
    def test_cleanup_file_permission_error(self):
        """Test file cleanup with permission error."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        # Make file read-only (on Unix-like systems)
        if os.name != 'nt':  # Not Windows
            os.chmod(temp_file_path, 0o444)
        
        try:
            # Should handle permission errors gracefully
            FileProcessor.cleanup_file(temp_file_path)
        except PermissionError:
            # On some systems, this might still raise PermissionError
            pass
        finally:
            # Ensure cleanup
            try:
                os.chmod(temp_file_path, 0o666)
                os.unlink(temp_file_path)
            except:
                pass
    
    def test_get_file_size(self):
        """Test getting file size."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"Test content")
            temp_file_path = temp_file.name
        
        try:
            size = FileProcessor.get_file_size(temp_file_path)
            assert size == 12  # "Test content" is 12 bytes
        finally:
            os.unlink(temp_file_path)
    
    def test_get_file_size_not_found(self):
        """Test getting size of non-existent file."""
        with pytest.raises(FileNotFoundError):
            FileProcessor.get_file_size("nonexistent_file.pdf")
    
    def test_is_file_empty(self):
        """Test checking if file is empty."""
        # Test empty file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            assert FileProcessor.is_file_empty(temp_file_path)
            
            # Add content
            with open(temp_file_path, 'w') as f:
                f.write("content")
            
            assert not FileProcessor.is_file_empty(temp_file_path)
        finally:
            os.unlink(temp_file_path)
    
    def test_is_file_empty_not_found(self):
        """Test checking if non-existent file is empty."""
        with pytest.raises(FileNotFoundError):
            FileProcessor.is_file_empty("nonexistent_file.pdf")
    
    def test_validate_file_content_pdf(self, sample_pdf_content):
        """Test PDF content validation."""
        assert FileProcessor.validate_file_content(sample_pdf_content, "pdf")
    
    def test_validate_file_content_docx(self, sample_docx_content):
        """Test DOCX content validation."""
        assert FileProcessor.validate_file_content(sample_docx_content, "docx")
    
    def test_validate_file_content_invalid_pdf(self):
        """Test invalid PDF content validation."""
        invalid_content = b"This is not a PDF file"
        assert not FileProcessor.validate_file_content(invalid_content, "pdf")
    
    def test_validate_file_content_invalid_docx(self):
        """Test invalid DOCX content validation."""
        invalid_content = b"This is not a DOCX file"
        assert not FileProcessor.validate_file_content(invalid_content, "docx")
    
    def test_validate_file_content_unsupported_type(self):
        """Test content validation with unsupported type."""
        with pytest.raises(ValueError, match="Unsupported file type for content validation"):
            FileProcessor.validate_file_content(b"content", "txt")
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test special characters
        assert "test_file_1" in FileProcessor.sanitize_filename("test file (1).pdf")
        
        # Test multiple spaces
        assert "test_file" in FileProcessor.sanitize_filename("test   file.pdf")
        
        # Test special characters
        assert "test_file" in FileProcessor.sanitize_filename("test@#$%^&*()file.pdf")
        
        # Test unicode characters
        assert "test_file" in FileProcessor.sanitize_filename("tëst fïle.pdf")
        
        # Test path traversal attempts
        assert "test_file" in FileProcessor.sanitize_filename("../../../test/file.pdf")
    
    def test_generate_safe_filename(self):
        """Test safe filename generation."""
        filename = FileProcessor.generate_safe_filename("test.pdf", "pdf")
        
        assert filename.endswith(".pdf")
        assert "test" in filename
        assert len(filename) > 10  # Should include UUID
    
    def test_get_file_extension(self):
        """Test file extension extraction."""
        assert FileProcessor.get_file_extension("test.pdf") == "pdf"
        assert FileProcessor.get_file_extension("test.docx") == "docx"
        assert FileProcessor.get_file_extension("test.doc") == "doc"
        assert FileProcessor.get_file_extension("test.PDF") == "pdf"  # Case insensitive
        assert FileProcessor.get_file_extension("test") == ""
        assert FileProcessor.get_file_extension("") == ""
    
    def test_is_allowed_extension(self):
        """Test allowed extension checking."""
        assert FileProcessor.is_allowed_extension("pdf")
        assert FileProcessor.is_allowed_extension("docx")
        assert FileProcessor.is_allowed_extension("doc")
        assert not FileProcessor.is_allowed_extension("txt")
        assert not FileProcessor.is_allowed_extension("exe")
        assert not FileProcessor.is_allowed_extension("")
    
    def test_validate_file_size(self):
        """Test file size validation."""
        # Valid size
        assert FileProcessor.validate_file_size(1024)
        assert FileProcessor.validate_file_size(settings.max_file_size)
        
        # Invalid size
        assert not FileProcessor.validate_file_size(0)
        assert not FileProcessor.validate_file_size(-1)
        assert not FileProcessor.validate_file_size(settings.max_file_size + 1)
    
    def test_get_mime_type(self):
        """Test MIME type detection."""
        assert FileProcessor.get_mime_type("pdf") == "application/pdf"
        assert FileProcessor.get_mime_type("docx") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert FileProcessor.get_mime_type("doc") == "application/msword"
        assert FileProcessor.get_mime_type("txt") == "text/plain"
        assert FileProcessor.get_mime_type("unknown") == "application/octet-stream"
