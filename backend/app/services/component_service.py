"""Component and BOM service for drawing generation and BOM integration."""

import uuid
from typing import Optional

from app.schemas.components import (
    BOMItem,
    BOMResponse,
    ComponentDrawingResponse,
    ComponentSpec,
)
from app.schemas.schematic import SchematicResponse


class ComponentService:
    """Service for component drawings and BOM generation."""

    def __init__(self):
        self._component_library: dict[str, ComponentSpec] = self._init_library()

    def _init_library(self) -> dict[str, ComponentSpec]:
        """Initialize component library with common parts."""
        return {
            "esp32": ComponentSpec(
                id="esp32-wroom-32",
                name="ESP32-WROOM-32",
                type="mcu",
                manufacturer="Espressif",
                part_number="ESP32-WROOM-32",
                description="WiFi and Bluetooth combo module",
                datasheet_url="https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32_datasheet_en.pdf",
                footprint="QFN-48",
            ),
            "lora": ComponentSpec(
                id="sx1276",
                name="SX1276",
                type="rf_module",
                manufacturer="Semtech",
                part_number="SX1276",
                description="Long range LoRa transceiver",
                datasheet_url="https://www.semtech.com/products/wireless-rf/lora-transceivers/sx1276",
                footprint="QFN-24",
            ),
            "regulator": ComponentSpec(
                id="ams1117-3.3",
                name="AMS1117-3.3",
                type="voltage_regulator",
                manufacturer="AMS",
                part_number="AMS1117-3.3",
                description="3.3V 1A LDO voltage regulator",
                footprint="SOT-223",
            ),
            "capacitor_100nf": ComponentSpec(
                id="cap-100nf",
                name="100nF Capacitor",
                type="passive",
                manufacturer="Generic",
                part_number="CAP-0805-100NF",
                description="100nF ceramic capacitor",
                footprint="0805",
            ),
            "resistor_10k": ComponentSpec(
                id="res-10k",
                name="10K Resistor",
                type="passive",
                manufacturer="Generic",
                part_number="RES-0805-10K",
                description="10K ohm resistor",
                footprint="0805",
            ),
        }

    async def generate_bom(self, schematic: SchematicResponse) -> BOMResponse:
        """
        Generate Bill of Materials from schematic.

        Args:
            schematic: The schematic to generate BOM for

        Returns:
            BOMResponse with component list and pricing
        """
        bom_items = []
        component_counts: dict[str, list[str]] = {}

        # Group components by type
        for comp in schematic.components:
            comp_key = comp.name.lower()
            if comp_key not in component_counts:
                component_counts[comp_key] = []
            component_counts[comp_key].append(comp.id)

        # Create BOM items
        unit_prices = {
            "esp32": 4.50,
            "lora": 8.00,
            "microcontroller": 3.00,
            "regulator": 0.50,
            "capacitor": 0.02,
            "resistor": 0.01,
            "led": 0.05,
            "sensor": 2.00,
            "antenna": 1.50,
            "crystal": 0.30,
            "usb": 0.80,
            "power": 5.00,
        }

        total_cost = 0.0
        for comp_name, ref_desigs in component_counts.items():
            quantity = len(ref_desigs)
            unit_price = unit_prices.get(comp_name, 1.00)
            total_price = unit_price * quantity
            total_cost += total_price

            # Get or create component spec
            spec = self._component_library.get(comp_name)
            if not spec:
                spec = ComponentSpec(
                    id=str(uuid.uuid4())[:8],
                    name=comp_name.upper(),
                    type="component",
                    manufacturer="TBD",
                )

            bom_items.append(
                BOMItem(
                    component_id=spec.id,
                    quantity=quantity,
                    reference_designators=ref_desigs,
                    component_spec=spec,
                    unit_price=unit_price,
                    total_price=total_price,
                )
            )

        return BOMResponse(
            schematic_id=schematic.id,
            items=bom_items,
            total_components=len(schematic.components),
            estimated_cost=round(total_cost, 2),
        )

    async def generate_drawing(
        self, component_id: str, output_format: str = "svg"
    ) -> ComponentDrawingResponse:
        """
        Generate component drawing in SVG format.

        Args:
            component_id: ID of the component
            output_format: Output format (svg)

        Returns:
            ComponentDrawingResponse with SVG data
        """
        # Get component spec
        spec = None
        for key, comp_spec in self._component_library.items():
            if comp_spec.id == component_id or key == component_id:
                spec = comp_spec
                break

        if not spec:
            # Create generic component drawing
            spec = ComponentSpec(
                id=component_id,
                name=component_id.upper(),
                type="component",
            )

        # Generate SVG based on component type
        svg_data = self._generate_component_svg(spec)

        return ComponentDrawingResponse(
            component_id=component_id,
            svg_data=svg_data,
            width=200,
            height=150,
        )

    def _generate_component_svg(self, spec: ComponentSpec) -> str:
        """Generate SVG drawing for a component."""
        width, height = 200, 150

        # Component-specific drawings
        if spec.type == "mcu":
            return self._draw_mcu_svg(spec, width, height)
        elif spec.type == "passive":
            return self._draw_passive_svg(spec, width, height)
        elif spec.type == "rf_module":
            return self._draw_rf_svg(spec, width, height)
        else:
            return self._draw_generic_svg(spec, width, height)

    def _draw_mcu_svg(self, spec: ComponentSpec, width: int, height: int) -> str:
        """Draw MCU component."""
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect x="50" y="25" width="100" height="100" fill="#2c3e50" stroke="#34495e" stroke-width="2" rx="5"/>
  <circle cx="65" cy="40" r="5" fill="#e74c3c"/>
  <text x="100" y="80" text-anchor="middle" fill="#ecf0f1" font-family="Arial" font-size="12">{spec.name}</text>
  <text x="100" y="95" text-anchor="middle" fill="#bdc3c7" font-family="Arial" font-size="8">{spec.footprint or "QFN"}</text>
  <!-- Pins -->
  <line x1="50" y1="50" x2="30" y2="50" stroke="#3498db" stroke-width="2"/>
  <line x1="50" y1="70" x2="30" y2="70" stroke="#3498db" stroke-width="2"/>
  <line x1="50" y1="90" x2="30" y2="90" stroke="#3498db" stroke-width="2"/>
  <line x1="150" y1="50" x2="170" y2="50" stroke="#3498db" stroke-width="2"/>
  <line x1="150" y1="70" x2="170" y2="70" stroke="#3498db" stroke-width="2"/>
  <line x1="150" y1="90" x2="170" y2="90" stroke="#3498db" stroke-width="2"/>
</svg>'''

    def _draw_passive_svg(self, spec: ComponentSpec, width: int, height: int) -> str:
        """Draw passive component (resistor/capacitor)."""
        if "capacitor" in spec.name.lower() or "cap" in spec.id.lower():
            return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <line x1="30" y1="75" x2="85" y2="75" stroke="#3498db" stroke-width="2"/>
  <line x1="85" y1="45" x2="85" y2="105" stroke="#3498db" stroke-width="3"/>
  <line x1="95" y1="45" x2="95" y2="105" stroke="#3498db" stroke-width="3"/>
  <line x1="95" y1="75" x2="170" y2="75" stroke="#3498db" stroke-width="2"/>
  <text x="100" y="130" text-anchor="middle" fill="#2c3e50" font-family="Arial" font-size="10">{spec.name}</text>
</svg>'''
        else:
            return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <line x1="30" y1="75" x2="60" y2="75" stroke="#3498db" stroke-width="2"/>
  <path d="M60,75 L70,55 L90,95 L110,55 L130,95 L140,75" fill="none" stroke="#e67e22" stroke-width="2"/>
  <line x1="140" y1="75" x2="170" y2="75" stroke="#3498db" stroke-width="2"/>
  <text x="100" y="130" text-anchor="middle" fill="#2c3e50" font-family="Arial" font-size="10">{spec.name}</text>
</svg>'''

    def _draw_rf_svg(self, spec: ComponentSpec, width: int, height: int) -> str:
        """Draw RF module component."""
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect x="40" y="30" width="120" height="80" fill="#1abc9c" stroke="#16a085" stroke-width="2" rx="3"/>
  <text x="100" y="65" text-anchor="middle" fill="#fff" font-family="Arial" font-size="11">{spec.name}</text>
  <text x="100" y="80" text-anchor="middle" fill="#ecf0f1" font-family="Arial" font-size="8">RF Module</text>
  <!-- Antenna symbol -->
  <line x1="100" y1="30" x2="100" y2="15" stroke="#e74c3c" stroke-width="2"/>
  <line x1="90" y1="15" x2="110" y2="15" stroke="#e74c3c" stroke-width="2"/>
  <line x1="95" y1="10" x2="105" y2="10" stroke="#e74c3c" stroke-width="2"/>
</svg>'''

    def _draw_generic_svg(self, spec: ComponentSpec, width: int, height: int) -> str:
        """Draw generic component."""
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect x="40" y="35" width="120" height="80" fill="#95a5a6" stroke="#7f8c8d" stroke-width="2" rx="5"/>
  <text x="100" y="75" text-anchor="middle" fill="#2c3e50" font-family="Arial" font-size="12">{spec.name}</text>
  <text x="100" y="95" text-anchor="middle" fill="#34495e" font-family="Arial" font-size="9">{spec.type}</text>
</svg>'''

    def get_component_spec(self, component_id: str) -> Optional[ComponentSpec]:
        """Get component specification by ID."""
        for key, spec in self._component_library.items():
            if spec.id == component_id or key == component_id:
                return spec
        return None


# Singleton instance
component_service = ComponentService()
