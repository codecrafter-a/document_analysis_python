import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.document_modifier import DocumentModifier
from app.models.schemas import ComplianceIssue, IssueType, ModificationRequest


class TestDocumentModifier:
    """Test cases for DocumentModifier service."""
    
    @pytest.fixture
    def modifier(self):
        """Create DocumentModifier instance for testing."""
        return DocumentModifier()
    
    @pytest.fixture
    def sample_issues(self):
        """Sample compliance issues for testing."""
        return [
            ComplianceIssue(
                issue_type=IssueType.GRAMMAR,
                severity="medium",
                message="Grammar error found",
                suggestion="Fix grammar",
                context="Sample text"
            ),
            ComplianceIssue(
                issue_type=IssueType.STYLE,
                severity="low",
                message="Style issue found",
                suggestion="Improve style",
                context="Sample text"
            )
        ]
    
    @pytest.fixture
    def sample_modification_request(self):
        """Sample modification request for testing."""
        return ModificationRequest(
            include_grammar_fixes=True,
            include_style_improvements=True,
            include_clarity_enhancements=False,
            preserve_formatting=True
        )
    
    def test_initialization(self, modifier):
        """Test DocumentModifier initialization."""
        assert modifier is not None
    
    @pytest.mark.asyncio
    async def test_modify_document_success(self, modifier, sample_issues, sample_modification_request):
        """Test successful document modification."""
        with patch('app.services.document_modifier.FileProcessor.extract_text_from_file') as mock_extract:
            mock_extract.return_value = "Original text content"
            
            with patch.object(modifier, '_apply_modifications') as mock_apply:
                mock_apply.return_value = "Modified text content"
                
                with patch.object(modifier, '_save_modified_document') as mock_save:
                    mock_save.return_value = {
                        'modified_filename': 'test_improved.docx',
                        'modified_file_path': '/tmp/test_improved.docx'
                    }
                    
                    result = await modifier.modify_document(
                        file_path="/tmp/test.pdf",
                        file_type="pdf",
                        issues=sample_issues,
                        modification_request=sample_modification_request
                    )
        
        assert isinstance(result, dict)
        assert 'modified_filename' in result
        assert 'modified_file_path' in result
        assert 'changes_summary' in result
        assert result['modified_filename'] == 'test_improved.docx'
    
    @pytest.mark.asyncio
    async def test_modify_document_no_issues(self, modifier, sample_modification_request):
        """Test document modification with no issues."""
        with patch('app.services.document_modifier.FileProcessor.extract_text_from_file') as mock_extract:
            mock_extract.return_value = "Original text content"
            
            with patch.object(modifier, '_save_modified_document') as mock_save:
                mock_save.return_value = {
                    'modified_filename': 'test_improved.docx',
                    'modified_file_path': '/tmp/test_improved.docx'
                }
                
                result = await modifier.modify_document(
                    file_path="/tmp/test.pdf",
                    file_type="pdf",
                    issues=[],
                    modification_request=sample_modification_request
                )
        
        assert isinstance(result, dict)
        assert 'modified_filename' in result
        assert 'changes_summary' in result
        assert len(result['changes_summary']) == 0  # No changes made
    
    @pytest.mark.asyncio
    async def test_modify_document_extraction_error(self, modifier, sample_issues, sample_modification_request):
        """Test document modification with text extraction error."""
        with patch('app.services.document_modifier.FileProcessor.extract_text_from_file') as mock_extract:
            mock_extract.side_effect = Exception("Text extraction failed")
            
            with pytest.raises(Exception, match="Text extraction failed"):
                await modifier.modify_document(
                    file_path="/tmp/test.pdf",
                    file_type="pdf",
                    issues=sample_issues,
                    modification_request=sample_modification_request
                )
    
    @pytest.mark.asyncio
    async def test_modify_document_save_error(self, modifier, sample_issues, sample_modification_request):
        """Test document modification with save error."""
        with patch('app.services.document_modifier.FileProcessor.extract_text_from_file') as mock_extract:
            mock_extract.return_value = "Original text content"
            
            with patch.object(modifier, '_apply_modifications') as mock_apply:
                mock_apply.return_value = "Modified text content"
                
                with patch.object(modifier, '_save_modified_document') as mock_save:
                    mock_save.side_effect = IOError("Save failed")
                    
                    with pytest.raises(IOError, match="Save failed"):
                        await modifier.modify_document(
                            file_path="/tmp/test.pdf",
                            file_type="pdf",
                            issues=sample_issues,
                            modification_request=sample_modification_request
                        )
    
    def test_apply_modifications_grammar_fixes(self, modifier, sample_issues):
        """Test applying grammar fixes."""
        original_text = "This is a test document with grammar errors."
        
        # Mock AI service for grammar fixes
        with patch.object(modifier, '_get_ai_suggestions') as mock_ai:
            mock_ai.return_value = "This is a test document with corrected grammar."
            
            modified_text = modifier._apply_modifications(
                original_text,
                sample_issues,
                include_grammar_fixes=True,
                include_style_improvements=False,
                include_clarity_enhancements=False
            )
        
        assert modified_text == "This is a test document with corrected grammar."
        mock_ai.assert_called_once()
    
    def test_apply_modifications_style_improvements(self, modifier, sample_issues):
        """Test applying style improvements."""
        original_text = "This is a test document with style issues."
        
        # Mock AI service for style improvements
        with patch.object(modifier, '_get_ai_suggestions') as mock_ai:
            mock_ai.return_value = "This is a test document with improved style."
            
            modified_text = modifier._apply_modifications(
                original_text,
                sample_issues,
                include_grammar_fixes=False,
                include_style_improvements=True,
                include_clarity_enhancements=False
            )
        
        assert modified_text == "This is a test document with improved style."
        mock_ai.assert_called_once()
    
    def test_apply_modifications_clarity_enhancements(self, modifier, sample_issues):
        """Test applying clarity enhancements."""
        original_text = "This is a test document that needs clarity improvements."
        
        # Mock AI service for clarity enhancements
        with patch.object(modifier, '_get_ai_suggestions') as mock_ai:
            mock_ai.return_value = "This is a test document with enhanced clarity."
            
            modified_text = modifier._apply_modifications(
                original_text,
                sample_issues,
                include_grammar_fixes=False,
                include_style_improvements=False,
                include_clarity_enhancements=True
            )
        
        assert modified_text == "This is a test document with enhanced clarity."
        mock_ai.assert_called_once()
    
    def test_apply_modifications_all_options(self, modifier, sample_issues):
        """Test applying all modification options."""
        original_text = "This is a test document with multiple issues."
        
        # Mock AI service for all improvements
        with patch.object(modifier, '_get_ai_suggestions') as mock_ai:
            mock_ai.return_value = "This is a test document with comprehensive improvements."
            
            modified_text = modifier._apply_modifications(
                original_text,
                sample_issues,
                include_grammar_fixes=True,
                include_style_improvements=True,
                include_clarity_enhancements=True
            )
        
        assert modified_text == "This is a test document with comprehensive improvements."
        # Should be called multiple times for different improvements
        assert mock_ai.call_count >= 1
    
    def test_apply_modifications_no_options(self, modifier, sample_issues):
        """Test applying modifications with no options enabled."""
        original_text = "This is a test document."
        
        modified_text = modifier._apply_modifications(
            original_text,
            sample_issues,
            include_grammar_fixes=False,
            include_style_improvements=False,
            include_clarity_enhancements=False
        )
        
        # Should return original text unchanged
        assert modified_text == original_text
    
    def test_apply_modifications_empty_issues(self, modifier):
        """Test applying modifications with empty issues list."""
        original_text = "This is a test document."
        
        modified_text = modifier._apply_modifications(
            original_text,
            [],
            include_grammar_fixes=True,
            include_style_improvements=True,
            include_clarity_enhancements=True
        )
        
        # Should return original text unchanged
        assert modified_text == original_text
    
    @patch('app.services.document_modifier.OpenAI')
    def test_get_ai_suggestions_success(self, mock_openai, modifier):
        """Test successful AI suggestions."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Improved text suggestion"
        mock_response.choices = [mock_choice]
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        modifier.openai_client = mock_client
        
        suggestion = modifier._get_ai_suggestions("Original text", "grammar")
        
        assert suggestion == "Improved text suggestion"
        mock_client.chat.completions.create.assert_called_once()
    
    def test_get_ai_suggestions_no_openai(self, modifier):
        """Test AI suggestions when OpenAI is not available."""
        modifier.openai_client = None
        
        suggestion = modifier._get_ai_suggestions("Original text", "grammar")
        
        # Should return original text when OpenAI is not available
        assert suggestion == "Original text"
    
    @patch('app.services.document_modifier.OpenAI')
    def test_get_ai_suggestions_error(self, mock_openai, modifier):
        """Test AI suggestions with error."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("OpenAI error")
        mock_openai.return_value = mock_client
        
        modifier.openai_client = mock_client
        
        suggestion = modifier._get_ai_suggestions("Original text", "grammar")
        
        # Should return original text on error
        assert suggestion == "Original text"
    
    def test_save_modified_document_success(self, modifier):
        """Test successful document saving."""
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('os.path.join', return_value="/tmp/test_improved.docx"):
                result = modifier._save_modified_document(
                    "Modified content",
                    "test.pdf",
                    "docx"
                )
        
        assert isinstance(result, dict)
        assert 'modified_filename' in result
        assert 'modified_file_path' in result
        assert result['modified_filename'].endswith('.docx')
        assert 'test_improved' in result['modified_filename']
    
    def test_save_modified_document_io_error(self, modifier):
        """Test document saving with IO error."""
        with patch('builtins.open', side_effect=IOError("Write failed")):
            with pytest.raises(IOError, match="Write failed"):
                modifier._save_modified_document(
                    "Modified content",
                    "test.pdf",
                    "docx"
                )
    
    def test_generate_changes_summary(self, modifier, sample_issues):
        """Test generating changes summary."""
        summary = modifier._generate_changes_summary(sample_issues)
        
        assert isinstance(summary, dict)
        assert 'total_changes' in summary
        assert 'changes_by_type' in summary
        assert summary['total_changes'] == 2
        assert 'grammar' in summary['changes_by_type']
        assert 'style' in summary['changes_by_type']
    
    def test_generate_changes_summary_empty_issues(self, modifier):
        """Test generating changes summary with empty issues."""
        summary = modifier._generate_changes_summary([])
        
        assert isinstance(summary, dict)
        assert summary['total_changes'] == 0
        assert len(summary['changes_by_type']) == 0
    
    def test_filter_issues_by_type(self, modifier, sample_issues):
        """Test filtering issues by type."""
        grammar_issues = modifier._filter_issues_by_type(sample_issues, IssueType.GRAMMAR)
        style_issues = modifier._filter_issues_by_type(sample_issues, IssueType.STYLE)
        
        assert len(grammar_issues) == 1
        assert len(style_issues) == 1
        assert grammar_issues[0].issue_type == IssueType.GRAMMAR
        assert style_issues[0].issue_type == IssueType.STYLE
    
    def test_filter_issues_by_type_no_matches(self, modifier, sample_issues):
        """Test filtering issues by type with no matches."""
        spelling_issues = modifier._filter_issues_by_type(sample_issues, IssueType.SPELLING)
        
        assert len(spelling_issues) == 0
    
    def test_create_modification_prompt(self, modifier):
        """Test creating modification prompt."""
        issues = [
            ComplianceIssue(
                issue_type=IssueType.GRAMMAR,
                severity="medium",
                message="Grammar error",
                suggestion="Fix it",
                context="Sample text"
            )
        ]
        
        prompt = modifier._create_modification_prompt("Original text", issues, "grammar")
        
        assert isinstance(prompt, str)
        assert "Original text" in prompt
        assert "Grammar error" in prompt
        assert "grammar" in prompt.lower()
    
    def test_create_modification_prompt_empty_issues(self, modifier):
        """Test creating modification prompt with empty issues."""
        prompt = modifier._create_modification_prompt("Original text", [], "grammar")
        
        assert isinstance(prompt, str)
        assert "Original text" in prompt
        assert "grammar" in prompt.lower()
    
    def test_validate_modification_request(self, modifier, sample_modification_request):
        """Test validation of modification request."""
        # Valid request
        assert modifier._validate_modification_request(sample_modification_request) is True
        
        # Invalid request - at least one option should be enabled
        invalid_request = ModificationRequest(
            include_grammar_fixes=False,
            include_style_improvements=False,
            include_clarity_enhancements=False,
            preserve_formatting=True
        )
        
        with pytest.raises(ValueError, match="At least one modification option must be enabled"):
            modifier._validate_modification_request(invalid_request)
    
    def test_get_file_extension_for_output(self, modifier):
        """Test getting file extension for output."""
        assert modifier._get_file_extension_for_output("pdf") == "docx"
        assert modifier._get_file_extension_for_output("docx") == "docx"
        assert modifier._get_file_extension_for_output("doc") == "docx"
    
    def test_generate_output_filename(self, modifier):
        """Test generating output filename."""
        filename = modifier._generate_output_filename("test.pdf", "docx")
        
        assert isinstance(filename, str)
        assert filename.endswith('.docx')
        assert 'test_improved' in filename
    
    def test_generate_output_filename_with_metadata(self, modifier):
        """Test generating output filename with metadata."""
        filename = modifier._generate_output_filename("test_document_v2.pdf", "docx")
        
        assert isinstance(filename, str)
        assert filename.endswith('.docx')
        assert 'test_document_v2_improved' in filename
    
    def test_apply_basic_corrections(self, modifier):
        """Test applying basic text corrections."""
        original_text = "This is a test document with some basic issues."
        
        corrected_text = modifier._apply_basic_corrections(original_text)
        
        assert isinstance(corrected_text, str)
        assert len(corrected_text) > 0
    
    def test_apply_basic_corrections_empty_text(self, modifier):
        """Test applying basic corrections to empty text."""
        corrected_text = modifier._apply_basic_corrections("")
        
        assert corrected_text == ""
    
    def test_apply_basic_corrections_special_characters(self, modifier):
        """Test applying basic corrections with special characters."""
        original_text = "This is a test document with special chars: @#$%^&*()"
        
        corrected_text = modifier._apply_basic_corrections(original_text)
        
        assert isinstance(corrected_text, str)
        assert len(corrected_text) > 0
    
    def test_format_document_content(self, modifier):
        """Test formatting document content."""
        content = "This is a test document.\n\nIt has multiple paragraphs.\n\nAnd formatting."
        
        formatted_content = modifier._format_document_content(content, preserve_formatting=True)
        
        assert isinstance(formatted_content, str)
        assert "\n\n" in formatted_content  # Should preserve paragraph breaks
    
    def test_format_document_content_no_preserve(self, modifier):
        """Test formatting document content without preserving formatting."""
        content = "This is a test document.\n\nIt has multiple paragraphs.\n\nAnd formatting."
        
        formatted_content = modifier._format_document_content(content, preserve_formatting=False)
        
        assert isinstance(formatted_content, str)
        # May or may not preserve formatting based on implementation
    
    @pytest.mark.asyncio
    async def test_modify_document_preserve_formatting(self, modifier, sample_issues, sample_modification_request):
        """Test document modification with formatting preservation."""
        with patch('app.services.document_modifier.FileProcessor.extract_text_from_file') as mock_extract:
            mock_extract.return_value = "Original text content"
            
            with patch.object(modifier, '_apply_modifications') as mock_apply:
                mock_apply.return_value = "Modified text content"
                
                with patch.object(modifier, '_save_modified_document') as mock_save:
                    mock_save.return_value = {
                        'modified_filename': 'test_improved.docx',
                        'modified_file_path': '/tmp/test_improved.docx'
                    }
                    
                    result = await modifier.modify_document(
                        file_path="/tmp/test.pdf",
                        file_type="pdf",
                        issues=sample_issues,
                        modification_request=sample_modification_request
                    )
        
        assert isinstance(result, dict)
        assert 'modified_filename' in result
        assert 'modified_file_path' in result
        assert 'changes_summary' in result
    
    def test_apply_modifications_with_preserve_formatting(self, modifier, sample_issues):
        """Test applying modifications with formatting preservation."""
        original_text = "This is a test document.\n\nWith formatting."
        
        with patch.object(modifier, '_get_ai_suggestions') as mock_ai:
            mock_ai.return_value = "This is an improved test document.\n\nWith better formatting."
            
            modified_text = modifier._apply_modifications(
                original_text,
                sample_issues,
                include_grammar_fixes=True,
                include_style_improvements=False,
                include_clarity_enhancements=False
            )
        
        assert modified_text == "This is an improved test document.\n\nWith better formatting."
        assert "\n\n" in modified_text  # Should preserve paragraph breaks
