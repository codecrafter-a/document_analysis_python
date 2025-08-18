import pytest
import tempfile
import os
from unittest.mock import Mock
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import ComplianceReport, ComplianceIssue, IssueType, ComplianceLevel


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n%%EOF"


@pytest.fixture
def sample_docx_content():
    """Sample DOCX content for testing."""
    return b"PK\x03\x04\x14\x00\x00\x00\x08\x00"  # DOCX file signature


@pytest.fixture
def sample_text_content():
    """Sample text content for testing."""
    return """
    This is a sample document for testing purposes. It contains various writing issues 
    that should be detected by the AI analyzer. The document has some grammar problems 
    and could benefit from improved clarity and style.
    
    This paragraph is quite long and contains multiple sentences that demonstrate 
    different types of writing issues. We can use this to test the analyzer's ability 
    to detect problems and provide useful feedback for improvement.
    """


@pytest.fixture
def sample_compliance_issues():
    """Sample compliance issues for testing."""
    return [
        ComplianceIssue(
            issue_type=IssueType.GRAMMAR,
            severity="medium",
            message="Grammar error found",
            suggestion="Fix the grammar",
            context="Sample text with error"
        ),
        ComplianceIssue(
            issue_type=IssueType.STYLE,
            severity="low",
            message="Style issue found",
            suggestion="Improve the style",
            context="Sample text with style issue"
        ),
        ComplianceIssue(
            issue_type=IssueType.CLARITY,
            severity="high",
            message="Clarity issue found",
            suggestion="Improve clarity",
            context="Sample text with clarity issue"
        )
    ]


@pytest.fixture
def sample_compliance_report(sample_compliance_issues):
    """Sample compliance report for testing."""
    return ComplianceReport(
        overall_score=85.0,
        compliance_level=ComplianceLevel.GOOD,
        total_issues=len(sample_compliance_issues),
        issues_by_type={"grammar": 1, "style": 1, "clarity": 1},
        detailed_issues=sample_compliance_issues,
        summary="Good document with minor issues",
        recommendations=["Review grammar", "Improve style", "Enhance clarity"]
    )


@pytest.fixture
def mock_upload_file():
    """Create a mock UploadFile for testing."""
    mock_file = Mock()
    mock_file.filename = "test.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.size = 1024
    return mock_file


@pytest.fixture
def temp_file_path():
    """Create a temporary file path for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"Test content")
        temp_file_path = temp_file.name
    
    yield temp_file_path
    
    # Cleanup
    try:
        os.unlink(temp_file_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    
    yield temp_dir
    
    # Cleanup
    try:
        import shutil
        shutil.rmtree(temp_dir)
    except FileNotFoundError:
        pass


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client for testing."""
    mock_client = Mock()
    
    # Mock response
    mock_response = Mock()
    mock_choice = Mock()
    mock_choice.message.content = "Mocked AI response"
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    
    return mock_client


@pytest.fixture
def mock_spacy_doc():
    """Create a mock spaCy document for testing."""
    mock_doc = Mock()
    
    # Mock sentences
    mock_sentence = Mock()
    mock_sentence.__len__ = lambda self: 15  # 15 words
    mock_doc.sents = [mock_sentence]
    
    # Mock tokens
    mock_token = Mock()
    mock_token.dep_ = "nsubj"  # Not passive
    mock_token.text = "test"
    mock_token.is_punct = False
    mock_token.is_space = False
    mock_doc.__iter__ = lambda self: iter([mock_token] * 10)
    mock_doc.__len__ = lambda self: 10
    
    return mock_doc


@pytest.fixture
def mock_language_tool():
    """Create a mock LanguageTool for testing."""
    mock_tool = Mock()
    
    # Mock match
    mock_match = Mock()
    mock_match.ruleId = "GRAMMAR_RULE"
    mock_match.message = "Grammar error found"
    mock_match.replacements = ["corrected"]
    mock_match.line = 1
    mock_match.context = "Sample text"
    mock_tool.check.return_value = [mock_match]
    
    return mock_tool


@pytest.fixture
def sample_modification_request():
    """Sample modification request for testing."""
    from app.models.schemas import ModificationRequest
    
    return ModificationRequest(
        include_grammar_fixes=True,
        include_style_improvements=True,
        include_clarity_enhancements=False,
        preserve_formatting=True
    )


@pytest.fixture
def mock_file_processor():
    """Create a mock FileProcessor for testing."""
    mock_processor = Mock()
    
    # Mock validation
    mock_processor.validate_file.return_value = ("pdf", "test_uuid.pdf")
    
    # Mock saving
    mock_processor.save_uploaded_file.return_value = "/tmp/test_uuid.pdf"
    
    # Mock text extraction
    mock_processor.extract_text_from_file.return_value = "Extracted text content"
    
    return mock_processor


@pytest.fixture
def mock_ai_analyzer():
    """Create a mock AIAnalyzer for testing."""
    mock_analyzer = Mock()
    
    # Mock analysis
    mock_analyzer.analyze_document.return_value = ComplianceReport(
        overall_score=85.0,
        compliance_level=ComplianceLevel.GOOD,
        total_issues=2,
        issues_by_type={"grammar": 1, "style": 1},
        detailed_issues=[],
        summary="Good document with minor issues",
        recommendations=["Review grammar"]
    )
    
    return mock_analyzer


@pytest.fixture
def mock_document_modifier():
    """Create a mock DocumentModifier for testing."""
    mock_modifier = Mock()
    
    # Mock modification
    mock_modifier.modify_document.return_value = {
        'modified_filename': 'test_improved.docx',
        'modified_file_path': '/tmp/test_improved.docx',
        'changes_summary': {
            'total_changes': 2,
            'changes_by_type': {'grammar': 1, 'style': 1}
        }
    }
    
    return mock_modifier


@pytest.fixture
def test_analysis_id():
    """Sample analysis ID for testing."""
    return "test-analysis-uuid-123"


@pytest.fixture
def test_modification_id():
    """Sample modification ID for testing."""
    return "test-modification-uuid-456"


@pytest.fixture
def mock_analysis_storage(test_analysis_id, sample_compliance_report):
    """Mock analysis storage for testing."""
    storage = {
        test_analysis_id: {
            'analysis_id': test_analysis_id,
            'filename': 'test.pdf',
            'file_type': 'pdf',
            'file_path': '/tmp/test.pdf',
            'file_size': 1024,
            'upload_time': '2023-01-01T00:00:00',
            'status': 'completed',
            'report': sample_compliance_report,
            'processing_time': 1.5,
            'analysis_time': '2023-01-01T00:00:00'
        }
    }
    return storage


@pytest.fixture
def mock_modification_storage(test_modification_id, test_analysis_id):
    """Mock modification storage for testing."""
    storage = {
        test_modification_id: {
            'modification_id': test_modification_id,
            'original_analysis_id': test_analysis_id,
            'filename': 'test_improved.docx',
            'file_path': '/tmp/test_improved.docx',
            'status': 'completed',
            'modified_filename': 'test_improved.docx',
            'modified_file_path': '/tmp/test_improved.docx',
            'changes_summary': {
                'total_changes': 2,
                'changes_by_type': {'grammar': 1, 'style': 1}
            },
            'processing_time': 2.5,
            'modification_time': '2023-01-01T00:00:00'
        }
    }
    return storage


@pytest.fixture
def sample_large_text():
    """Sample large text for testing performance."""
    return "This is a large text document. " * 1000  # ~30KB of text


@pytest.fixture
def sample_malformed_pdf():
    """Sample malformed PDF content for testing error handling."""
    return b"This is not a valid PDF file content"


@pytest.fixture
def sample_corrupted_docx():
    """Sample corrupted DOCX content for testing error handling."""
    return b"This is not a valid DOCX file content"


@pytest.fixture
def mock_background_tasks():
    """Mock background tasks for testing."""
    mock_tasks = Mock()
    mock_tasks.add_task = Mock()
    return mock_tasks


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their names."""
    for item in items:
        # Mark API integration tests
        if "test_api_integration" in item.nodeid:
            item.add_marker(pytest.mark.api)
            item.add_marker(pytest.mark.integration)
        
        # Mark unit tests
        elif any(x in item.nodeid for x in ["test_ai_analyzer", "test_file_processor", "test_document_modifier", "test_models"]):
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests
        if any(x in item.nodeid for x in ["test_large", "test_performance", "test_concurrent"]):
            item.add_marker(pytest.mark.slow)


# Test data generators
@pytest.fixture
def generate_test_files():
    """Generate test files for different scenarios."""
    def _generate_files():
        files = {}
        
        # Valid PDF
        files['valid_pdf'] = {
            'content': b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n%%EOF",
            'filename': 'test.pdf',
            'content_type': 'application/pdf'
        }
        
        # Valid DOCX
        files['valid_docx'] = {
            'content': b"PK\x03\x04\x14\x00\x00\x00\x08\x00",
            'filename': 'test.docx',
            'content_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        # Large file
        files['large_file'] = {
            'content': b"x" * (5 * 1024 * 1024),  # 5MB
            'filename': 'large.pdf',
            'content_type': 'application/pdf'
        }
        
        # Empty file
        files['empty_file'] = {
            'content': b"",
            'filename': 'empty.pdf',
            'content_type': 'application/pdf'
        }
        
        # Invalid file type
        files['invalid_file'] = {
            'content': b"Text content",
            'filename': 'test.txt',
            'content_type': 'text/plain'
        }
        
        return files
    
    return _generate_files


@pytest.fixture
def generate_test_issues():
    """Generate test compliance issues for different scenarios."""
    def _generate_issues():
        issues = {
            'grammar_issues': [
                ComplianceIssue(
                    issue_type=IssueType.GRAMMAR,
                    severity="medium",
                    message="Subject-verb agreement error",
                    suggestion="Fix subject-verb agreement",
                    context="The team are working hard"
                )
            ],
            'style_issues': [
                ComplianceIssue(
                    issue_type=IssueType.STYLE,
                    severity="low",
                    message="Passive voice detected",
                    suggestion="Use active voice",
                    context="The document was written by the author"
                )
            ],
            'clarity_issues': [
                ComplianceIssue(
                    issue_type=IssueType.CLARITY,
                    severity="high",
                    message="Complex sentence structure",
                    suggestion="Simplify sentence structure",
                    context="The aforementioned aforementioned aforementioned"
                )
            ],
            'mixed_issues': [
                ComplianceIssue(
                    issue_type=IssueType.GRAMMAR,
                    severity="critical",
                    message="Critical grammar error",
                    suggestion="Fix immediately",
                    context="Critical error context"
                ),
                ComplianceIssue(
                    issue_type=IssueType.STYLE,
                    severity="medium",
                    message="Style improvement needed",
                    suggestion="Improve style",
                    context="Style context"
                )
            ]
        }
        return issues
    
    return _generate_issues
