import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.ai_analyzer import AIAnalyzer
from app.models.schemas import ComplianceReport, ComplianceIssue, IssueType, ComplianceLevel


class TestAIAnalyzer:
    """Test cases for AIAnalyzer service."""
    
    @pytest.fixture
    def analyzer(self):
        """Create AIAnalyzer instance for testing."""
        return AIAnalyzer()
    
    @pytest.fixture
    def sample_text(self):
        """Sample text for testing."""
        return """
        This is a sample document for testing purposes. It contains various writing issues 
        that should be detected by the AI analyzer. The document has some grammar problems 
        and could benefit from improved clarity and style.
        
        This paragraph is quite long and contains multiple sentences that demonstrate 
        different types of writing issues. We can use this to test the analyzer's ability 
        to detect problems and provide useful feedback for improvement.
        """
    
    def test_initialization(self, analyzer):
        """Test AIAnalyzer initialization."""
        assert analyzer is not None
        # Note: Actual initialization depends on available services
    
    @patch('app.services.ai_analyzer.spacy')
    @patch('app.services.ai_analyzer.language_tool_python')
    def test_initialize_models_success(self, mock_language_tool, mock_spacy):
        """Test successful model initialization."""
        mock_spacy.load.return_value = Mock()
        mock_language_tool.LanguageTool.return_value = Mock()
        
        analyzer = AIAnalyzer()
        assert analyzer.nlp is not None
        assert analyzer.language_tool is not None
    
    @patch('app.services.ai_analyzer.spacy')
    def test_initialize_models_spacy_failure(self, mock_spacy):
        """Test spaCy initialization failure handling."""
        mock_spacy.load.side_effect = OSError("Model not found")
        mock_spacy.cli.download.return_value = None
        
        analyzer = AIAnalyzer()
        # Should handle the error gracefully
        assert analyzer is not None
    
    @patch('app.services.ai_analyzer.language_tool_python')
    def test_initialize_models_languagetool_failure(self, mock_language_tool):
        """Test LanguageTool initialization failure handling."""
        mock_language_tool.LanguageTool.side_effect = Exception("Connection failed")
        
        analyzer = AIAnalyzer()
        # Should handle the error gracefully
        assert analyzer is not None
    
    @pytest.mark.asyncio
    async def test_analyze_document_empty_text(self, analyzer):
        """Test analysis with empty text."""
        report = await analyzer.analyze_document("")
        
        assert isinstance(report, ComplianceReport)
        assert report.overall_score == 100.0
        assert report.compliance_level == ComplianceLevel.EXCELLENT
        assert report.total_issues == 0
        assert "Excellent" in report.summary
    
    @pytest.mark.asyncio
    async def test_analyze_document_basic_text(self, analyzer, sample_text):
        """Test basic document analysis."""
        report = await analyzer.analyze_document(sample_text)
        
        assert isinstance(report, ComplianceReport)
        assert 0 <= report.overall_score <= 100
        assert report.total_issues >= 0
        assert isinstance(report.issues_by_type, dict)
        assert isinstance(report.detailed_issues, list)
        assert isinstance(report.summary, str)
        assert isinstance(report.recommendations, list)
    
    def test_analyze_grammar_and_spelling_no_languagetool(self, analyzer):
        """Test grammar analysis when LanguageTool is not available."""
        analyzer.language_tool = None
        issues = analyzer._analyze_grammar_and_spelling("Sample text")
        
        assert isinstance(issues, list)
        assert len(issues) == 0
    
    @patch('app.services.ai_analyzer.language_tool_python')
    def test_analyze_grammar_and_spelling_with_languagetool(self, mock_language_tool):
        """Test grammar analysis with LanguageTool."""
        # Mock LanguageTool match
        mock_match = Mock()
        mock_match.ruleId = "GRAMMAR_RULE"
        mock_match.message = "Grammar error found"
        mock_match.replacements = ["corrected"]
        mock_match.line = 1
        mock_match.context = "Sample text"
        
        mock_tool = Mock()
        mock_tool.check.return_value = [mock_match]
        mock_language_tool.LanguageTool.return_value = mock_tool
        
        analyzer = AIAnalyzer()
        issues = analyzer._analyze_grammar_and_spelling("Sample text")
        
        assert len(issues) == 1
        assert issues[0].issue_type == IssueType.GRAMMAR
        assert issues[0].message == "Grammar error found"
    
    def test_analyze_style_and_clarity_no_spacy(self, analyzer):
        """Test style analysis when spaCy is not available."""
        analyzer.nlp = None
        issues = analyzer._analyze_style_and_clarity("Sample text")
        
        assert isinstance(issues, list)
        assert len(issues) == 0
    
    @patch('app.services.ai_analyzer.spacy')
    def test_analyze_style_and_clarity_with_spacy(self, mock_spacy):
        """Test style analysis with spaCy."""
        # Mock spaCy document
        mock_doc = Mock()
        mock_doc.sents = [Mock()]
        mock_token = Mock()
        mock_token.dep_ = "auxpass"
        mock_doc.__iter__ = lambda self: iter([mock_token])
        mock_doc.__len__ = lambda self: 10
        
        mock_spacy.load.return_value = Mock()
        mock_spacy.nlp = Mock(return_value=mock_doc)
        
        analyzer = AIAnalyzer()
        analyzer.nlp = Mock(return_value=mock_doc)
        
        issues = analyzer._analyze_style_and_clarity("Sample text")
        
        assert isinstance(issues, list)
    
    def test_analyze_structure(self, analyzer):
        """Test document structure analysis."""
        text = "Paragraph 1.\n\n" * 5  # 5 paragraphs
        issues = analyzer._analyze_structure(text)
        
        assert isinstance(issues, list)
    
    def test_analyze_structure_long_paragraph(self, analyzer):
        """Test structure analysis with long paragraph."""
        long_paragraph = "This is a very long paragraph. " * 20  # ~400 characters
        text = f"{long_paragraph}\n\nShort paragraph."
        
        issues = analyzer._analyze_structure(text)
        
        assert len(issues) > 0
        assert any(issue.issue_type == IssueType.STRUCTURE for issue in issues)
    
    @pytest.mark.asyncio
    async def test_analyze_with_ai_no_openai(self, analyzer):
        """Test AI analysis when OpenAI is not available."""
        analyzer.openai_client = None
        issues = await analyzer._analyze_with_ai("Sample text")
        
        assert isinstance(issues, list)
        assert len(issues) == 0
    
    @pytest.mark.asyncio
    @patch('app.services.ai_analyzer.OpenAI')
    async def test_analyze_with_ai_with_openai(self, mock_openai):
        """Test AI analysis with OpenAI."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "This text needs improvement for clarity."
        mock_response.choices = [mock_choice]
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        analyzer = AIAnalyzer()
        analyzer.openai_client = mock_client
        
        issues = await analyzer._analyze_with_ai("Sample text")
        
        assert isinstance(issues, list)
        mock_client.chat.completions.create.assert_called_once()
    
    def test_check_passive_voice(self, analyzer):
        """Test passive voice detection."""
        # Mock spaCy document with passive voice
        mock_doc = Mock()
        mock_token = Mock()
        mock_token.dep_ = "auxpass"
        mock_doc.__iter__ = lambda self: iter([mock_token] * 5)  # 5 passive tokens
        mock_doc.__len__ = lambda self: 50  # 50 total tokens
        
        issues = analyzer._check_passive_voice(mock_doc)
        
        assert isinstance(issues, list)
        if len(issues) > 0:
            assert issues[0].issue_type == IssueType.STYLE
    
    def test_check_sentence_length(self, analyzer):
        """Test sentence length analysis."""
        # Mock spaCy document with long sentence
        mock_doc = Mock()
        mock_sentence = Mock()
        mock_sentence.__len__ = lambda self: 30  # 30 words
        mock_doc.sents = [mock_sentence]
        
        issues = analyzer._check_sentence_length(mock_doc)
        
        assert isinstance(issues, list)
        if len(issues) > 0:
            assert issues[0].issue_type == IssueType.CLARITY
    
    def test_check_word_complexity(self, analyzer):
        """Test word complexity analysis."""
        # Mock spaCy document with complex words
        mock_doc = Mock()
        mock_token = Mock()
        mock_token.text = "supercalifragilisticexpialidocious"
        mock_token.is_punct = False
        mock_doc.__iter__ = lambda self: iter([mock_token] * 10)  # 10 complex words
        mock_doc.__len__ = lambda self: 200  # 200 total tokens
        
        issues = analyzer._check_word_complexity(mock_doc)
        
        assert isinstance(issues, list)
        if len(issues) > 0:
            assert issues[0].issue_type == IssueType.CLARITY
    
    def test_check_repetition(self, analyzer):
        """Test word repetition analysis."""
        # Mock spaCy document with repeated words
        mock_doc = Mock()
        mock_tokens = []
        for i in range(10):
            token = Mock()
            token.text = "repeated"
            token.is_punct = False
            token.is_space = False
            mock_tokens.append(token)
        
        mock_doc.__iter__ = lambda self: iter(mock_tokens)
        
        issues = analyzer._check_repetition(mock_doc)
        
        assert isinstance(issues, list)
        if len(issues) > 0:
            assert issues[0].issue_type == IssueType.STYLE
    
    def test_map_language_tool_severity(self, analyzer):
        """Test severity mapping for LanguageTool rules."""
        assert analyzer._map_language_tool_severity("UPPERCASE_SENTENCE_START") == "critical"
        assert analyzer._map_language_tool_severity("ENGLISH_WORD_REPEAT_RULE") == "high"
        assert analyzer._map_language_tool_severity("ENGLISH_WORD_REPEAT_BEGINNING_RULE") == "medium"
        assert analyzer._map_language_tool_severity("UNKNOWN_RULE") == "low"
    
    def test_calculate_overall_score_no_issues(self, analyzer):
        """Test score calculation with no issues."""
        score = analyzer._calculate_overall_score([])
        assert score == 100.0
    
    def test_calculate_overall_score_with_issues(self, analyzer):
        """Test score calculation with issues."""
        issues = [
            ComplianceIssue(
                issue_type=IssueType.GRAMMAR,
                severity="medium",
                message="Test issue",
                suggestion="Fix it",
                context="Test"
            )
        ]
        
        score = analyzer._calculate_overall_score(issues)
        assert 0 <= score < 100
    
    def test_determine_compliance_level(self, analyzer):
        """Test compliance level determination."""
        assert analyzer._determine_compliance_level(95) == ComplianceLevel.EXCELLENT
        assert analyzer._determine_compliance_level(80) == ComplianceLevel.GOOD
        assert analyzer._determine_compliance_level(70) == ComplianceLevel.FAIR
        assert analyzer._determine_compliance_level(50) == ComplianceLevel.POOR
    
    def test_group_issues_by_type(self, analyzer):
        """Test grouping issues by type."""
        issues = [
            ComplianceIssue(issue_type=IssueType.GRAMMAR, severity="low", message="", suggestion="", context=""),
            ComplianceIssue(issue_type=IssueType.GRAMMAR, severity="low", message="", suggestion="", context=""),
            ComplianceIssue(issue_type=IssueType.STYLE, severity="low", message="", suggestion="", context="")
        ]
        
        grouped = analyzer._group_issues_by_type(issues)
        
        assert grouped["grammar"] == 2
        assert grouped["style"] == 1
    
    def test_generate_summary_no_issues(self, analyzer):
        """Test summary generation with no issues."""
        summary = analyzer._generate_summary([], 100.0)
        assert "Excellent" in summary
        assert "No compliance issues" in summary
    
    def test_generate_summary_with_issues(self, analyzer):
        """Test summary generation with issues."""
        issues = [
            ComplianceIssue(issue_type=IssueType.GRAMMAR, severity="critical", message="", suggestion="", context=""),
            ComplianceIssue(issue_type=IssueType.STYLE, severity="high", message="", suggestion="", context="")
        ]
        
        summary = analyzer._generate_summary(issues, 75.0)
        assert "75.0%" in summary
        assert "2 issues" in summary
    
    def test_generate_recommendations(self, analyzer):
        """Test recommendation generation."""
        issues = [
            ComplianceIssue(issue_type=IssueType.GRAMMAR, severity="low", message="", suggestion="", context=""),
            ComplianceIssue(issue_type=IssueType.STYLE, severity="low", message="", suggestion="", context="")
        ]
        
        recommendations = analyzer._generate_recommendations(issues)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("grammar" in rec.lower() for rec in recommendations)
        assert any("style" in rec.lower() for rec in recommendations)
    
    def test_generate_recommendations_no_issues(self, analyzer):
        """Test recommendation generation with no issues."""
        recommendations = analyzer._generate_recommendations([])
        
        assert isinstance(recommendations, list)
        assert len(recommendations) == 1
        assert "maintaining high writing standards" in recommendations[0]
    
    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self, analyzer, sample_text):
        """Test complete analysis workflow."""
        report = await analyzer.analyze_document(sample_text)
        
        # Verify report structure
        assert hasattr(report, 'overall_score')
        assert hasattr(report, 'compliance_level')
        assert hasattr(report, 'total_issues')
        assert hasattr(report, 'issues_by_type')
        assert hasattr(report, 'detailed_issues')
        assert hasattr(report, 'summary')
        assert hasattr(report, 'recommendations')
        
        # Verify data types
        assert isinstance(report.overall_score, float)
        assert isinstance(report.compliance_level, ComplianceLevel)
        assert isinstance(report.total_issues, int)
        assert isinstance(report.issues_by_type, dict)
        assert isinstance(report.detailed_issues, list)
        assert isinstance(report.summary, str)
        assert isinstance(report.recommendations, list)
        
        # Verify value ranges
        assert 0 <= report.overall_score <= 100
        assert report.total_issues >= 0
        assert len(report.summary) > 0
        assert len(report.recommendations) > 0
