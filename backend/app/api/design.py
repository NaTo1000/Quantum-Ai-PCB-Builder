"""
Design API endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from app.models.schemas import DesignRequest, DesignResponse, DesignDetail, DesignStatus
from app.services.design_service import design_service
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=DesignResponse)
async def create_design(design_request: DesignRequest, background_tasks: BackgroundTasks):
    """
    Create a new PCB/chip design from natural language or code description
    
    Args:
        design_request: Design request with description and parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        Design response with ID and status
        
    Note:
        Currently uses FastAPI BackgroundTasks for simplicity.
        TODO: For production scale, integrate RabbitMQ message queue
        via rabbitmq_service for better reliability and scalability.
    """
    try:
        # Create design record
        design_data = await design_service.create_design(
            description=design_request.description,
            design_type=design_request.design_type.value,
            constraints=design_request.constraints,
            code_input=design_request.code_input
        )
        
        # Queue design processing task
        background_tasks.add_task(process_design_task, design_data["design_id"])
        
        return DesignResponse(
            design_id=design_data["design_id"],
            status=DesignStatus(design_data["status"]),
            message="Design created successfully and queued for processing",
            created_at=datetime.fromisoformat(design_data["created_at"])
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating design: {str(e)}")

@router.get("/{design_id}", response_model=DesignDetail)
async def get_design(design_id: str):
    """
    Get design details by ID
    
    Args:
        design_id: ID of the design
        
    Returns:
        Detailed design information
    """
    design_data = design_service.get_design(design_id)
    
    if not design_data:
        raise HTTPException(status_code=404, detail=f"Design {design_id} not found")
    
    return DesignDetail(
        design_id=design_data["design_id"],
        description=design_data["description"],
        design_type=design_data["design_type"],
        status=DesignStatus(design_data["status"]),
        schematic=design_data.get("schematic"),
        created_at=datetime.fromisoformat(design_data["created_at"]),
        updated_at=datetime.fromisoformat(design_data["updated_at"])
    )

@router.get("/", response_model=List[DesignDetail])
async def list_designs():
    """
    List all designs
    
    Returns:
        List of all designs
    """
    designs = design_service.list_designs()
    
    return [
        DesignDetail(
            design_id=d["design_id"],
            description=d["description"],
            design_type=d["design_type"],
            status=DesignStatus(d["status"]),
            schematic=d.get("schematic"),
            created_at=datetime.fromisoformat(d["created_at"]),
            updated_at=datetime.fromisoformat(d["updated_at"])
        )
        for d in designs
    ]

async def process_design_task(design_id: str):
    """Background task to process design"""
    try:
        await design_service.process_design(design_id)
    except Exception as e:
        print(f"Error processing design {design_id}: {e}")
