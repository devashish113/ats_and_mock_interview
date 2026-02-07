"""
FastAPI Main Application for ATS Resume Converter.
Entry point for the backend API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routes import resume, mock_interview
from app.config import GENERATED_DIR, UPLOAD_DIR

# Create FastAPI application
app = FastAPI(
    title="ATS Resume Converter API",
    description="Convert normal resumes to ATS-friendly format with AI-powered analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories for file serving
app.mount("/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")

# Include resume routes
app.include_router(resume.router, tags=["Resume Operations"])

# Include mock interview routes
app.include_router(mock_interview.router, prefix="/mock", tags=["Mock Interview"])


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "ATS Resume Converter API is running",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "upload_dir": UPLOAD_DIR.exists(),
            "generated_dir": GENERATED_DIR.exists()
        }
    }


if __name__ == "__main__":
    import uvicorn
    from app.config import HOST, PORT
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
