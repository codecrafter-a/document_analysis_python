import time
import re
import spacy
import language_tool_python
from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.config import settings
from app.models.schemas import (
    ComplianceReport, ComplianceIssue, IssueType, 
    ComplianceLevel
)


class AIAnalyzer:
    """AI-powered document compliance analyzer using basic text analysis and OpenAI."""
    
    def __init__(self):
        """Initialize AI analyzer with required models."""
        self.openai_client = None
        self.nlp = None
        self.language_tool = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all required AI/NLP models."""
        # Initialize OpenAI client
        if settings.openai_api_key:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
        
        # Initialize spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # If model not found, download it
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        
        # Initialize LanguageTool
        try:
            self.language_tool = language_tool_python.LanguageTool('en-US')
        except Exception as e:
            print(f"Warning: LanguageTool initialization failed: {e}")
            self.language_tool = None
    
    async def analyze_document(self, text_content: str) -> ComplianceReport:
        """
        Perform comprehensive document compliance analysis.
        
        Args:
            text_content: Text content to analyze
            
        Returns:
            Comprehensive compliance report
        """
        start_time = time.time()
        
        # Collect issues from all analyzers
        all_issues = []
        
        # Grammar and spelling analysis
        grammar_issues = self._analyze_grammar_and_spelling(text_content)
        all_issues.extend(grammar_issues)
        
        # Style and clarity analysis
        style_issues = self._analyze_style_and_clarity(text_content)
        all_issues.extend(style_issues)
        
        # Structure analysis
        structure_issues = self._analyze_structure(text_content)
        all_issues.extend(structure_issues)
        
        # AI-powered analysis
        ai_issues = await self._analyze_with_ai(text_content)
        all_issues.extend(ai_issues)
        
        # Calculate overall score and compliance level
        overall_score = self._calculate_overall_score(all_issues)
        compliance_level = self._determine_compliance_level(overall_score)
        
        # Group issues by type
        issues_by_type = self._group_issues_by_type(all_issues)
        
        # Generate summary and recommendations
        summary = self._generate_summary(all_issues, overall_score)
        recommendations = self._generate_recommendations(all_issues)
        
        processing_time = time.time() - start_time
        
        return ComplianceReport(
            overall_score=overall_score,
            compliance_level=compliance_level,
            total_issues=len(all_issues),
            issues_by_type=issues_by_type,
            detailed_issues=all_issues,
            summary=summary,
            recommendations=recommendations
        )
    
    def _analyze_grammar_and_spelling(self, text: str) -> List[ComplianceIssue]:
        """Analyze grammar and spelling using LanguageTool."""
        issues = []
        
        if not self.language_tool:
            return issues
        
        try:
            matches = self.language_tool.check(text)
            
            for match in matches:
                issue = ComplianceIssue(
                    issue_type=IssueType.GRAMMAR if match.ruleId.startswith('GRAMMAR') else IssueType.SPELLING,
                    severity=self._map_language_tool_severity(match.ruleId),
                    message=match.message,
                    suggestion=match.replacements[0] if match.replacements else "",
                    line_number=match.line,
                    context=match.context
                )
                issues.append(issue)
        
        except Exception as e:
            print(f"LanguageTool analysis failed: {e}")
        
        return issues
    
    def _analyze_style_and_clarity(self, text: str) -> List[ComplianceIssue]:
        """Analyze writing style and clarity using spaCy."""
        issues = []
        
        if not self.nlp:
            return issues
        
        try:
            doc = self.nlp(text)
            
            # Check for passive voice
            passive_issues = self._check_passive_voice(doc)
            issues.extend(passive_issues)
            
            # Check for sentence length
            length_issues = self._check_sentence_length(doc)
            issues.extend(length_issues)
            
            # Check for word complexity
            complexity_issues = self._check_word_complexity(doc)
            issues.extend(complexity_issues)
            
            # Check for repetition
            repetition_issues = self._check_repetition(doc)
            issues.extend(repetition_issues)
        
        except Exception as e:
            print(f"spaCy analysis failed: {e}")
        
        return issues
    
    def _analyze_structure(self, text: str) -> List[ComplianceIssue]:
        """Analyze document structure and organization."""
        issues = []
        
        paragraphs = text.split('\n\n')
        
        # Check paragraph length
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph.strip()) > 300:  # Long paragraphs
                issues.append(ComplianceIssue(
                    issue_type=IssueType.STRUCTURE,
                    severity="medium",
                    message="Paragraph is too long and may be difficult to read",
                    suggestion="Consider breaking this paragraph into shorter, more focused paragraphs",
                    line_number=i + 1,
                    context=paragraph[:100] + "..."
                ))
        
        # Check for proper document structure
        if len(paragraphs) < 3:
            issues.append(ComplianceIssue(
                issue_type=IssueType.STRUCTURE,
                severity="low",
                message="Document structure could be improved",
                suggestion="Consider adding more paragraphs to improve readability and organization",
                context="Document structure analysis"
            ))
        
        return issues
    
    async def _analyze_with_ai(self, text: str) -> List[ComplianceIssue]:
        """Perform AI-powered analysis using OpenAI."""
        issues = []
        
        if not self.openai_client:
            return issues
        
        try:
            # Prepare prompt for AI analysis
            prompt = f"""
            Analyze the following text for writing quality, clarity, and compliance with English writing guidelines. 
            Focus on:
            1. Clarity and readability
            2. Professional tone
            3. Logical flow
            4. Appropriate language level
            5. Consistency in style
            
            Text to analyze:
            {text[:2000]}  # Limit text length for API
            
            Provide specific issues found with severity levels (low/medium/high/critical) and suggestions for improvement.
            Format as JSON with fields: issue_type, severity, message, suggestion
            """
            
            response = self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert writing consultant and English language specialist."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.max_tokens,
                temperature=0.3
            )
            
            # Parse AI response and convert to ComplianceIssue objects
            ai_analysis = response.choices[0].message.content
            # Note: In a production environment, you'd want more robust JSON parsing
            # For this assessment, we'll create a basic issue based on AI feedback
            if "improvement" in ai_analysis.lower() or "issue" in ai_analysis.lower():
                issues.append(ComplianceIssue(
                    issue_type=IssueType.CLARITY,
                    severity="medium",
                    message="AI analysis suggests improvements for clarity and style",
                    suggestion=ai_analysis[:200],
                    context="AI-powered analysis"
                ))
        
        except Exception as e:
            print(f"OpenAI analysis failed: {e}")
        
        return issues
    
    def _check_passive_voice(self, doc) -> List[ComplianceIssue]:
        """Check for passive voice usage."""
        issues = []
        passive_count = 0
        
        for token in doc:
            if token.dep_ == "auxpass":
                passive_count += 1
        
        if passive_count > len(doc) * 0.1:  # More than 10% passive voice
            issues.append(ComplianceIssue(
                issue_type=IssueType.STYLE,
                severity="medium",
                message="High usage of passive voice detected",
                suggestion="Consider using active voice to make the text more direct and engaging",
                context="Passive voice analysis"
            ))
        
        return issues
    
    def _check_sentence_length(self, doc) -> List[ComplianceIssue]:
        """Check for overly long sentences."""
        issues = []
        
        for sent in doc.sents:
            if len(sent) > 25:  # Sentences longer than 25 words
                issues.append(ComplianceIssue(
                    issue_type=IssueType.CLARITY,
                    severity="low",
                    message="Sentence is quite long and may be difficult to read",
                    suggestion="Consider breaking this sentence into shorter, clearer sentences",
                    context=str(sent)[:100] + "..."
                ))
        
        return issues
    
    def _check_word_complexity(self, doc) -> List[ComplianceIssue]:
        """Check for overly complex words."""
        issues = []
        complex_words = 0
        
        for token in doc:
            if len(token.text) > 12 and not token.is_punct:
                complex_words += 1
        
        if complex_words > len(doc) * 0.05:  # More than 5% complex words
            issues.append(ComplianceIssue(
                issue_type=IssueType.CLARITY,
                severity="low",
                message="High usage of complex words detected",
                suggestion="Consider using simpler, more accessible language where possible",
                context="Word complexity analysis"
            ))
        
        return issues
    
    def _check_repetition(self, doc) -> List[ComplianceIssue]:
        """Check for word repetition."""
        issues = []
        word_freq = {}
        
        for token in doc:
            if not token.is_punct and not token.is_space:
                word = token.text.lower()
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Check for overused words
        for word, count in word_freq.items():
            if count > 5 and len(word) > 3:  # Word used more than 5 times
                issues.append(ComplianceIssue(
                    issue_type=IssueType.STYLE,
                    severity="low",
                    message=f"Word '{word}' is used frequently",
                    suggestion="Consider using synonyms or alternative expressions to improve variety",
                    context=f"Repetition analysis: '{word}' used {count} times"
                ))
        
        return issues
    
    def _map_language_tool_severity(self, rule_id: str) -> str:
        """Map LanguageTool rule IDs to severity levels."""
        critical_rules = ['UPPERCASE_SENTENCE_START', 'DOUBLE_PUNCTUATION']
        high_rules = ['ENGLISH_WORD_REPEAT_RULE', 'EN_A_VS_AN']
        medium_rules = ['ENGLISH_WORD_REPEAT_BEGINNING_RULE']
        
        if rule_id in critical_rules:
            return "critical"
        elif rule_id in high_rules:
            return "high"
        elif rule_id in medium_rules:
            return "medium"
        else:
            return "low"
    
    def _calculate_overall_score(self, issues: List[ComplianceIssue]) -> float:
        """Calculate overall compliance score based on issues."""
        if not issues:
            return 100.0
        
        # Weight issues by severity
        severity_weights = {
            "critical": 10,
            "high": 5,
            "medium": 2,
            "low": 1
        }
        
        total_weight = sum(severity_weights.get(issue.severity, 1) for issue in issues)
        max_possible_weight = len(issues) * 10  # Assume worst case
        
        score = max(0, 100 - (total_weight / max_possible_weight) * 100)
        return round(score, 1)
    
    def _determine_compliance_level(self, score: float) -> ComplianceLevel:
        """Determine compliance level based on score."""
        if score >= 90:
            return ComplianceLevel.EXCELLENT
        elif score >= 75:
            return ComplianceLevel.GOOD
        elif score >= 60:
            return ComplianceLevel.FAIR
        else:
            return ComplianceLevel.POOR
    
    def _group_issues_by_type(self, issues: List[ComplianceIssue]) -> Dict[str, int]:
        """Group issues by their type."""
        grouped = {}
        for issue in issues:
            issue_type = issue.issue_type.value
            grouped[issue_type] = grouped.get(issue_type, 0) + 1
        return grouped
    
    def _generate_summary(self, issues: List[ComplianceIssue], score: float) -> str:
        """Generate executive summary of the analysis."""
        if not issues:
            return "Excellent! No compliance issues were found in this document."
        
        total_issues = len(issues)
        critical_issues = len([i for i in issues if i.severity == "critical"])
        high_issues = len([i for i in issues if i.severity == "high"])
        
        summary = f"Document analysis completed with {score}% compliance score. "
        summary += f"Found {total_issues} issues: {critical_issues} critical, {high_issues} high severity. "
        
        if score >= 75:
            summary += "Overall, the document demonstrates good writing quality with room for minor improvements."
        elif score >= 60:
            summary += "The document requires moderate improvements to meet professional standards."
        else:
            summary += "The document needs significant improvements to meet professional writing standards."
        
        return summary
    
    def _generate_recommendations(self, issues: List[ComplianceIssue]) -> List[str]:
        """Generate general recommendations for improvement."""
        recommendations = []
        
        # Analyze issue patterns
        grammar_count = len([i for i in issues if i.issue_type == IssueType.GRAMMAR])
        style_count = len([i for i in issues if i.issue_type == IssueType.STYLE])
        clarity_count = len([i for i in issues if i.issue_type == IssueType.CLARITY])
        
        if grammar_count > 0:
            recommendations.append("Review and correct grammar and spelling errors")
        
        if style_count > 0:
            recommendations.append("Improve writing style by varying sentence structure and word choice")
        
        if clarity_count > 0:
            recommendations.append("Enhance clarity by simplifying complex sentences and using more direct language")
        
        if not recommendations:
            recommendations.append("Continue maintaining high writing standards")
        
        return recommendations
