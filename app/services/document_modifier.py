import time
import uuid
import os
from typing import Dict, List, Optional
from docx import Document
from docx.shared import Inches
from openai import OpenAI
from app.config import settings
from app.models.schemas import ComplianceIssue, ModificationRequest
from app.utils.file_processor import FileProcessor


class DocumentModifier:
    """AI-powered document modification service."""
    
    def __init__(self):
        """Initialize document modifier."""
        self.openai_client = None
        if settings.openai_api_key:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
    
    async def modify_document(
        self, 
        original_file_path: str, 
        file_type: str,
        issues: List[ComplianceIssue],
        modification_request: ModificationRequest
    ) -> Dict[str, any]:
        """
        Modify document based on compliance issues and user preferences.
        
        Args:
            original_file_path: Path to original document
            file_type: Type of document (pdf, docx, doc)
            issues: List of compliance issues found
            modification_request: User's modification preferences
            
        Returns:
            Dictionary with modification results
        """
        start_time = time.time()
        
        # Extract text from original document
        original_text = FileProcessor.extract_text_from_file(original_file_path, file_type)
        
        # Generate improved text using AI
        improved_text = await self._generate_improved_text(
            original_text, 
            issues, 
            modification_request
        )
        
        # Create modified document
        modified_filename = self._generate_modified_filename(original_file_path)
        modified_file_path = os.path.join(settings.download_folder, modified_filename)
        
        if file_type in ['docx', 'doc']:
            self._create_modified_docx(original_file_path, improved_text, modified_file_path)
        else:
            # For PDFs, create a Word document with the improved text
            self._create_docx_from_text(improved_text, modified_file_path)
        
        # Calculate changes summary
        changes_summary = self._calculate_changes_summary(original_text, improved_text, issues)
        
        processing_time = time.time() - start_time
        
        return {
            'modification_id': str(uuid.uuid4()),
            'modified_filename': modified_filename,
            'modified_file_path': modified_file_path,
            'changes_summary': changes_summary,
            'processing_time': processing_time
        }
    
    async def _generate_improved_text(
        self, 
        original_text: str, 
        issues: List[ComplianceIssue],
        modification_request: ModificationRequest
    ) -> str:
        """
        Generate improved text using AI based on compliance issues.
        
        Args:
            original_text: Original document text
            issues: List of compliance issues
            modification_request: User's modification preferences
            
        Returns:
            Improved text content
        """
        if not self.openai_client:
            # Fallback: return original text with basic improvements
            return self._apply_basic_improvements(original_text, issues)
        
        try:
            # Prepare issues summary for AI
            issues_summary = self._prepare_issues_summary(issues, modification_request)
            
            # Create AI prompt
            prompt = f"""
            Please improve the following text based on the identified writing issues and user preferences.
            
            Original text:
            {original_text[:3000]}  # Limit text length for API
            
            Issues to address:
            {issues_summary}
            
            User preferences:
            - Include grammar fixes: {modification_request.include_grammar_fixes}
            - Include style improvements: {modification_request.include_style_improvements}
            - Include clarity enhancements: {modification_request.include_clarity_enhancements}
            - Preserve formatting: {modification_request.preserve_formatting}
            
            Custom instructions: {modification_request.custom_instructions or 'None'}
            
            Please provide the improved version of the text, maintaining the original meaning and structure while addressing the identified issues.
            """
            
            response = self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert writing consultant and editor. Improve the text while maintaining its original meaning and professional tone."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.max_tokens,
                temperature=0.3
            )
            
            improved_text = response.choices[0].message.content
            
            # Clean up the response
            improved_text = self._clean_ai_response(improved_text)
            
            return improved_text if improved_text.strip() else original_text
            
        except Exception as e:
            print(f"AI text improvement failed: {e}")
            # Fallback to basic improvements
            return self._apply_basic_improvements(original_text, issues)
    
    def _prepare_issues_summary(
        self, 
        issues: List[ComplianceIssue], 
        modification_request: ModificationRequest
    ) -> str:
        """Prepare a summary of issues for AI processing."""
        if not issues:
            return "No specific issues identified."
        
        # Filter issues based on user preferences
        filtered_issues = []
        for issue in issues:
            if (issue.issue_type.value == 'grammar' and modification_request.include_grammar_fixes) or \
               (issue.issue_type.value == 'style' and modification_request.include_style_improvements) or \
               (issue.issue_type.value == 'clarity' and modification_request.include_clarity_enhancements):
                filtered_issues.append(issue)
        
        if not filtered_issues:
            return "No issues to address based on user preferences."
        
        # Create summary
        summary_parts = []
        for issue in filtered_issues[:10]:  # Limit to first 10 issues
            summary_parts.append(f"- {issue.severity.upper()}: {issue.message} (Suggestion: {issue.suggestion})")
        
        return "\n".join(summary_parts)
    
    def _apply_basic_improvements(self, text: str, issues: List[ComplianceIssue]) -> str:
        """Apply basic text improvements without AI."""
        improved_text = text
        
        # Apply basic grammar fixes
        grammar_issues = [i for i in issues if i.issue_type.value == 'grammar']
        for issue in grammar_issues:
            if issue.suggestion and issue.suggestion in improved_text:
                # Simple replacement (in production, you'd want more sophisticated logic)
                improved_text = improved_text.replace(issue.suggestion, issue.suggestion)
        
        return improved_text
    
    def _clean_ai_response(self, response: str) -> str:
        """Clean up AI response text."""
        # Remove common AI response artifacts
        lines = response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip lines that look like AI instructions or formatting
            if not any(skip in line.lower() for skip in ['improved text:', 'here is the', 'the improved version']):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _generate_modified_filename(self, original_path: str) -> str:
        """Generate filename for modified document."""
        base_name = os.path.splitext(os.path.basename(original_path))[0]
        return f"{base_name}_improved.docx"
    
    def _create_modified_docx(self, original_path: str, improved_text: str, output_path: str):
        """Create modified Word document."""
        try:
            # Load original document to preserve formatting
            doc = Document(original_path)
            
            # Clear existing content and add improved text
            for paragraph in doc.paragraphs:
                paragraph.clear()
            
            # Add improved text as new paragraphs
            paragraphs = improved_text.split('\n\n')
            for i, para_text in enumerate(paragraphs):
                if i < len(doc.paragraphs):
                    doc.paragraphs[i].text = para_text.strip()
                else:
                    doc.add_paragraph(para_text.strip())
            
            # Save modified document
            doc.save(output_path)
            
        except Exception as e:
            print(f"Failed to create modified DOCX: {e}")
            # Fallback: create new document
            self._create_docx_from_text(improved_text, output_path)
    
    def _create_docx_from_text(self, text: str, output_path: str):
        """Create new Word document from text."""
        try:
            doc = Document()
            
            # Add title
            title = doc.add_heading('Improved Document', 0)
            
            # Add improved text
            paragraphs = text.split('\n\n')
            for para_text in paragraphs:
                if para_text.strip():
                    doc.add_paragraph(para_text.strip())
            
            # Save document
            doc.save(output_path)
            
        except Exception as e:
            print(f"Failed to create DOCX from text: {e}")
            # Last resort: save as text file
            with open(output_path.replace('.docx', '.txt'), 'w', encoding='utf-8') as f:
                f.write(text)
    
    def _calculate_changes_summary(self, original_text: str, improved_text: str, issues: List[ComplianceIssue]) -> Dict[str, int]:
        """Calculate summary of changes made."""
        summary = {
            'grammar_fixes': 0,
            'style_improvements': 0,
            'clarity_enhancements': 0,
            'total_changes': 0
        }
        
        # Count issues by type
        for issue in issues:
            if issue.issue_type.value == 'grammar':
                summary['grammar_fixes'] += 1
            elif issue.issue_type.value == 'style':
                summary['style_improvements'] += 1
            elif issue.issue_type.value == 'clarity':
                summary['clarity_enhancements'] += 1
        
        summary['total_changes'] = sum(summary.values())
        
        # Calculate text similarity (basic approach)
        original_words = set(original_text.lower().split())
        improved_words = set(improved_text.lower().split())
        word_changes = len(original_words.symmetric_difference(improved_words))
        
        summary['word_changes'] = word_changes
        
        return summary
