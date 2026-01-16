"""
Design Service for managing PCB/chip designs
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from app.config import settings
from app.models.schemas import DesignStatus, SchematicData
from app.services.llm_service import llm_service

class DesignService:
    """Service for managing design operations"""
    
    def __init__(self):
        self.designs_dir = Path(settings.designs_dir)
        self.designs_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_design(self, description: str, design_type: str, constraints: Optional[Dict[str, Any]] = None, code_input: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new design
        
        Args:
            description: Natural language description
            design_type: Type of design
            constraints: Optional constraints
            code_input: Optional code-based specification
            
        Returns:
            Design data dictionary
        """
        design_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        design_data = {
            "design_id": design_id,
            "description": description,
            "design_type": design_type,
            "constraints": constraints,
            "code_input": code_input,
            "status": DesignStatus.PENDING.value,
            "created_at": timestamp.isoformat(),
            "updated_at": timestamp.isoformat(),
            "schematic": None
        }
        
        # Save design data
        self._save_design(design_id, design_data)
        
        return design_data
    
    async def process_design(self, design_id: str) -> Dict[str, Any]:
        """
        Process a design using LLM to generate schematic
        
        Args:
            design_id: ID of the design to process
            
        Returns:
            Updated design data
        """
        design_data = self.get_design(design_id)
        if not design_data:
            raise ValueError(f"Design {design_id} not found")
        
        # Update status to processing
        design_data["status"] = DesignStatus.PROCESSING.value
        self._save_design(design_id, design_data)
        
        try:
            # Generate schematic using LLM
            schematic = await llm_service.generate_schematic(
                description=design_data["description"],
                design_type=design_data["design_type"],
                constraints=design_data.get("constraints")
            )
            
            design_data["schematic"] = schematic
            design_data["status"] = DesignStatus.COMPLETED.value
            design_data["updated_at"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            design_data["status"] = DesignStatus.FAILED.value
            design_data["error"] = str(e)
            design_data["updated_at"] = datetime.utcnow().isoformat()
        
        self._save_design(design_id, design_data)
        return design_data
    
    def get_design(self, design_id: str) -> Optional[Dict[str, Any]]:
        """Get design by ID"""
        design_file = self.designs_dir / f"{design_id}.json"
        if not design_file.exists():
            return None
        
        try:
            with open(design_file, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error reading design file {design_id}: {e}")
            return None
    
    def list_designs(self) -> list:
        """List all designs"""
        designs = []
        for design_file in self.designs_dir.glob("*.json"):
            try:
                with open(design_file, 'r') as f:
                    designs.append(json.load(f))
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error reading design file {design_file}: {e}")
                continue
        return designs
    
    def _save_design(self, design_id: str, design_data: Dict[str, Any]):
        """Save design data to file with error handling"""
        design_file = self.designs_dir / f"{design_id}.json"
        try:
            # Write to temporary file first, then rename for atomic operation
            temp_file = design_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(design_data, f, indent=2)
            # Atomic rename (on most filesystems)
            temp_file.replace(design_file)
        except (IOError, OSError) as e:
            print(f"Error saving design file {design_id}: {e}")
            raise

design_service = DesignService()
