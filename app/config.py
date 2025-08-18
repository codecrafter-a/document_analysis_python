import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # API Configuration
    app_name: str = "AI Document Compliance Checker"
    version: str = "1.0.0"
    debug: bool = False
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    
    # File Upload Settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: list = [".pdf", ".docx", ".doc"]
    upload_folder: str = "uploads"
    download_folder: str = "downloads"
    
    # AI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    max_tokens: int = 4000
    
    # LanguageTool Configuration
    language_tool_url: str = "http://localhost:8081"
    
    # Processing Settings
    max_processing_time: int = 300  # 5 minutes
    cache_timeout: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.upload_folder, exist_ok=True)
os.makedirs(settings.download_folder, exist_ok=True)
