import os
import uuid
import aiofiles
from typing import Tuple, Optional
from pathlib import Path
import PyPDF2
from docx import Document
from fastapi import UploadFile, HTTPException
from app.config import settings


class FileProcessor:
    """Handles file upload, validation, and text extraction."""
    
    @staticmethod
    def validate_file(file: UploadFile) -> Tuple[str, str]:
        """
        Validate uploaded file and return file type and safe filename.
        
        Args:
            file: Uploaded file object
            
        Returns:
            Tuple of (file_type, safe_filename)
            
        Raises:
            HTTPException: If file validation fails
        """
        # Check file size
        if file.size and file.size > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum limit of {settings.max_file_size} bytes"
            )
        
        # Check file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(settings.allowed_extensions)}"
            )
        
        # Generate safe filename
        safe_filename = f"{uuid.uuid4()}{file_extension}"
        
        return file_extension[1:], safe_filename
    
    @staticmethod
    async def save_uploaded_file(file: UploadFile, filename: str) -> str:
        """
        Save uploaded file to disk.
        
        Args:
            file: Uploaded file object
            filename: Safe filename to save as
            
        Returns:
            Full path to saved file
        """
        file_path = os.path.join(settings.upload_folder, filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return file_path
    
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """
        Extract text content from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
            
        Raises:
            HTTPException: If PDF processing fails
        """
        try:
            text_content = []
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content.append(page.extract_text())
            
            return '\n'.join(text_content)
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract text from PDF: {str(e)}"
            )
    
    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """
        Extract text content from Word document.
        
        Args:
            file_path: Path to Word document
            
        Returns:
            Extracted text content
            
        Raises:
            HTTPException: If Word document processing fails
        """
        try:
            doc = Document(file_path)
            text_content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            return '\n'.join(text_content)
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract text from Word document: {str(e)}"
            )
    
    @staticmethod
    def extract_text_from_file(file_path: str, file_type: str) -> str:
        """
        Extract text from file based on its type.
        
        Args:
            file_path: Path to the file
            file_type: Type of file (pdf, docx, doc)
            
        Returns:
            Extracted text content
        """
        if file_type == 'pdf':
            return FileProcessor.extract_text_from_pdf(file_path)
        elif file_type in ['docx', 'doc']:
            return FileProcessor.extract_text_from_docx(file_path)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_type}"
            )
    
    @staticmethod
    def cleanup_file(file_path: str) -> None:
        """
        Remove temporary file from disk.
        
        Args:
            file_path: Path to file to remove
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            # Log error but don't raise exception for cleanup failures
            print(f"Failed to cleanup file {file_path}: {str(e)}")
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """
        Get basic information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        if not os.path.exists(file_path):
            return {}
        
        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'path': file_path
        }
