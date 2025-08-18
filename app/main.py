from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
from app.api.routes import router
from app.config import settings

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="""
    AI-powered Document Compliance Checker API
    
    This API provides comprehensive document analysis and modification capabilities:
    
    ## Features
    * **Document Upload**: Accept PDF and Word documents for analysis
    * **AI Compliance Analysis**: Multi-model analysis using OpenAI, spaCy, and LanguageTool
    * **Interactive Modifications**: AI-powered document improvement suggestions
    * **Secure File Handling**: Proper validation and secure processing
    
    ## Endpoints
    * `POST /upload` - Upload and analyze documents
    * `GET /analysis/{analysis_id}` - Get analysis results
    * `POST /modify/{analysis_id}` - Request AI modifications
    * `GET /download/{modification_id}` - Download improved documents
    * `GET /health` - Health check and service status
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["Document Analysis"])

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Document Compliance Checker API",
        "version": settings.version,
        "docs": "/docs",
        "health": "/api/v1/health"
    }

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "detail": f"HTTP {exc.status_code} error occurred",
            "timestamp": time.time()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "timestamp": time.time()
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    print(f"Starting {settings.app_name} v{settings.version}")
    print("Initializing AI models and services...")
    
    # Ensure directories exist
    import os
    os.makedirs(settings.upload_folder, exist_ok=True)
    os.makedirs(settings.download_folder, exist_ok=True)
    
    print("Application startup complete!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    print("Shutting down AI Document Compliance Checker...")
    print("Cleaning up resources...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
