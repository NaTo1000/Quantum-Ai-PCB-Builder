"""
Quantum-Ai-PCB-Builder Backend
FastAPI application for AI-guided chip and PCB design.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="Quantum-Ai-PCB-Builder API",
    description="AI-guided chip and PCB design lab API",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint returning API status."""
    return {"status": "ok", "message": "Quantum-Ai-PCB-Builder API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
