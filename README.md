# AI Document Compliance Checker

A comprehensive AI-powered system that processes document files (PDF/Word) and checks compliance against English guidelines. The system provides detailed analysis, compliance reports, and AI-powered document modifications.

## Features

- **Document Upload**: Accepts PDF and Word documents via REST API
- **AI Compliance Analysis**: Uses multiple NLP models to check grammar, style, and writing guidelines
- **Interactive Modifications**: AI-powered document correction and improvement suggestions
- **Comprehensive Testing**: Unit and integration tests for all components
- **Secure File Handling**: Proper validation and secure file processing

## Architecture

```
assessment-pythonm/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py              # Configuration settings
│   ├── models/                # Pydantic models
│   ├── services/              # Business logic services
│   ├── api/                   # API routes
│   └── utils/                 # Utility functions
├── tests/                     # Test suite
├── uploads/                   # Temporary file storage
├── downloads/                 # Modified document storage
├── requirements.txt
└── README.md
```

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Download spaCy Model**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

3. **Environment Variables**:
   Create a `.env` file with:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

4. **Run the Application**:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints

### Document Upload and Analysis
- `POST /upload` - Upload and analyze document
- `GET /analysis/{analysis_id}` - Get analysis results
- `POST /modify/{analysis_id}` - Request AI modifications
- `GET /download/{file_id}` - Download modified document

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

## Technical Implementation

### AI Models Used
- **OpenAI GPT-4**: Advanced text analysis and modification
- **spaCy**: NLP processing and text extraction
- **LanguageTool**: Grammar and style checking

### Security Features
- File type validation
- File size limits
- Secure file handling
- Input sanitization

### Performance Optimizations
- Async file processing
- Efficient text extraction
- Caching for repeated analyses
- Background task processing

## Project Structure Details

The application follows a clean architecture pattern with:
- **API Layer**: FastAPI routes and request/response handling
- **Service Layer**: Business logic and AI processing
- **Model Layer**: Data models and validation
- **Utility Layer**: Helper functions and file processing

This demonstrates expertise in:
- Python API development
- AI/NLP integration
- Secure file handling
- Comprehensive testing
- Clean code architecture
