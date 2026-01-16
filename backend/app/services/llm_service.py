"""
LLM Service for AI-guided design generation
"""
from typing import Dict, Any, Optional
import json
from openai import AsyncOpenAI
from app.config import settings

class LLMService:
    """Service for interacting with LLM for design generation"""
    
    def __init__(self):
        self.client = None
        if settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def generate_schematic(self, description: str, design_type: str, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate PCB/chip schematic from natural language description
        
        Args:
            description: Natural language description of the design
            design_type: Type of design (pcb, chip, esp32, lora, etc.)
            constraints: Optional design constraints
            
        Returns:
            Dictionary containing schematic components and connections
        """
        if not self.client:
            # Return mock data if no API key configured
            return self._generate_mock_schematic(description, design_type)
        
        try:
            # Construct prompt for LLM
            prompt = self._build_design_prompt(description, design_type, constraints)
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert electronics engineer specializing in PCB and chip design. Generate detailed schematics in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse LLM response
            schematic_data = json.loads(response.choices[0].message.content)
            return schematic_data
            
        except Exception as e:
            print(f"Error generating schematic with LLM: {e}")
            return self._generate_mock_schematic(description, design_type)
    
    def _build_design_prompt(self, description: str, design_type: str, constraints: Optional[Dict[str, Any]] = None) -> str:
        """Build prompt for LLM"""
        prompt = f"""Design a {design_type} based on the following description:

{description}

"""
        if constraints:
            prompt += f"\nConstraints:\n{json.dumps(constraints, indent=2)}\n"
        
        prompt += """
Generate a JSON schematic with the following structure:
{
  "components": [
    {"id": "component_id", "type": "component_type", "value": "value", "pins": ["pin1", "pin2"]}
  ],
  "connections": [
    {"from": {"component": "comp_id", "pin": "pin_name"}, "to": {"component": "comp_id", "pin": "pin_name"}}
  ],
  "layout": "description of physical layout",
  "specifications": {
    "power_requirements": "...",
    "dimensions": "...",
    "operating_conditions": "..."
  }
}
"""
        return prompt
    
    def _generate_mock_schematic(self, description: str, design_type: str) -> Dict[str, Any]:
        """Generate mock schematic data when LLM is not available"""
        
        # Generate basic schematic based on design type
        if design_type == "esp32":
            return {
                "components": [
                    {"id": "U1", "type": "ESP32-WROOM-32", "value": "ESP32", "pins": ["3V3", "GND", "GPIO0", "GPIO2"]},
                    {"id": "C1", "type": "Capacitor", "value": "10uF", "pins": ["1", "2"]},
                    {"id": "R1", "type": "Resistor", "value": "10K", "pins": ["1", "2"]},
                    {"id": "J1", "type": "USB-C", "value": "USB-C", "pins": ["VBUS", "GND", "D+", "D-"]}
                ],
                "connections": [
                    {"from": {"component": "J1", "pin": "VBUS"}, "to": {"component": "U1", "pin": "3V3"}},
                    {"from": {"component": "J1", "pin": "GND"}, "to": {"component": "U1", "pin": "GND"}},
                    {"from": {"component": "C1", "pin": "1"}, "to": {"component": "U1", "pin": "3V3"}},
                    {"from": {"component": "C1", "pin": "2"}, "to": {"component": "U1", "pin": "GND"}},
                    {"from": {"component": "R1", "pin": "1"}, "to": {"component": "U1", "pin": "GPIO0"}},
                    {"from": {"component": "R1", "pin": "2"}, "to": {"component": "U1", "pin": "3V3"}}
                ],
                "layout": "Standard ESP32 development board layout with USB-C connector",
                "specifications": {
                    "power_requirements": "5V USB or 3.3V regulated",
                    "dimensions": "55mm x 28mm",
                    "operating_conditions": "-40°C to 85°C"
                }
            }
        elif design_type == "lora":
            return {
                "components": [
                    {"id": "U1", "type": "RFM95W", "value": "LoRa Module", "pins": ["VCC", "GND", "MOSI", "MISO", "SCK", "NSS"]},
                    {"id": "U2", "type": "MCU", "value": "ATmega328P", "pins": ["VCC", "GND", "MOSI", "MISO", "SCK", "SS"]},
                    {"id": "ANT1", "type": "Antenna", "value": "868MHz", "pins": ["RF"]},
                    {"id": "C1", "type": "Capacitor", "value": "100nF", "pins": ["1", "2"]}
                ],
                "connections": [
                    {"from": {"component": "U2", "pin": "MOSI"}, "to": {"component": "U1", "pin": "MOSI"}},
                    {"from": {"component": "U2", "pin": "MISO"}, "to": {"component": "U1", "pin": "MISO"}},
                    {"from": {"component": "U2", "pin": "SCK"}, "to": {"component": "U1", "pin": "SCK"}},
                    {"from": {"component": "U2", "pin": "SS"}, "to": {"component": "U1", "pin": "NSS"}},
                    {"from": {"component": "U1", "pin": "RF"}, "to": {"component": "ANT1", "pin": "RF"}},
                    {"from": {"component": "C1", "pin": "1"}, "to": {"component": "U1", "pin": "VCC"}},
                    {"from": {"component": "C1", "pin": "2"}, "to": {"component": "U1", "pin": "GND"}}
                ],
                "layout": "LoRa transceiver module with MCU controller",
                "specifications": {
                    "power_requirements": "3.3V regulated, 120mA peak",
                    "dimensions": "45mm x 35mm",
                    "operating_conditions": "868MHz ISM band, -20°C to 70°C"
                }
            }
        else:
            # Generic PCB
            return {
                "components": [
                    {"id": "U1", "type": "MCU", "value": "Generic MCU", "pins": ["VCC", "GND", "IO1", "IO2"]},
                    {"id": "C1", "type": "Capacitor", "value": "10uF", "pins": ["1", "2"]},
                    {"id": "R1", "type": "Resistor", "value": "10K", "pins": ["1", "2"]},
                    {"id": "LED1", "type": "LED", "value": "Red", "pins": ["A", "K"]}
                ],
                "connections": [
                    {"from": {"component": "C1", "pin": "1"}, "to": {"component": "U1", "pin": "VCC"}},
                    {"from": {"component": "C1", "pin": "2"}, "to": {"component": "U1", "pin": "GND"}},
                    {"from": {"component": "U1", "pin": "IO1"}, "to": {"component": "R1", "pin": "1"}},
                    {"from": {"component": "R1", "pin": "2"}, "to": {"component": "LED1", "pin": "A"}},
                    {"from": {"component": "LED1", "pin": "K"}, "to": {"component": "U1", "pin": "GND"}}
                ],
                "layout": f"Custom {design_type} design based on: {description[:100]}",
                "specifications": {
                    "power_requirements": "3.3V or 5V",
                    "dimensions": "To be determined",
                    "operating_conditions": "Standard operating conditions"
                }
            }

llm_service = LLMService()
