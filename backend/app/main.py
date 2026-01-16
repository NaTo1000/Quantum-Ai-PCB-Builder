"""Main FastAPI application for Quantum AI PCB Builder."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import schematic, design_checks, simulation, components, vendors

app = FastAPI(
    title="Quantum AI PCB Builder",
    description="AI-powered PCB and chip design platform with automated design checks, simulation, and vendor matching.",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(schematic.router, prefix="/api/schematic", tags=["Schematic"])
app.include_router(design_checks.router, prefix="/api/checks", tags=["Design Checks"])
app.include_router(simulation.router, prefix="/api/simulation", tags=["Simulation"])
app.include_router(components.router, prefix="/api/components", tags=["Components"])
app.include_router(vendors.router, prefix="/api/vendors", tags=["Vendors"])


@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "Quantum AI PCB Builder API",
        "version": "1.0.0",
        "features": [
            "Prompt-to-Schematic AI Engine",
            "Automated Design Checks (DRC, LVS, Thermal, Signal Integrity)",
            "Simulation Pipeline (SPICE, Timing, Power)",
            "Component-Level Drawing Generator with SVG Previews",
            "Vendor Matching & Quoting",
        ],
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
