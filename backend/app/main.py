"""
Quantum AI PCB Builder - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import design, simulation, vendor
from app.config import settings

app = FastAPI(
    title="Quantum AI PCB Builder",
    description="AI-guided chip and PCB design lab with natural language processing",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Configure via environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(design.router, prefix="/api/design", tags=["design"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["simulation"])
app.include_router(vendor.router, prefix="/api/vendor", tags=["vendor"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Quantum AI PCB Builder API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
