"""Schematic generation service using AI."""

import uuid
from typing import Optional

from app.schemas.schematic import Component, Net, SchematicResponse


class SchematicService:
    """Service for generating schematics from natural language prompts."""

    def __init__(self):
        self._schematics: dict[str, SchematicResponse] = {}

    async def generate_from_prompt(
        self, prompt: str, design_type: str = "pcb", output_format: str = "rtl"
    ) -> SchematicResponse:
        """
        Generate a schematic from a natural language prompt.

        Args:
            prompt: Natural language description of the desired design
            design_type: Type of design (pcb, chip, analog, digital)
            output_format: Output format (rtl, analog, mixed-signal)

        Returns:
            SchematicResponse with generated components and nets
        """
        schematic_id = str(uuid.uuid4())

        # Parse prompt to identify components and connections
        components, nets = self._parse_prompt(prompt, design_type)

        # Generate SVG preview
        svg_preview = self._generate_svg_preview(components, nets)

        schematic = SchematicResponse(
            id=schematic_id,
            components=components,
            nets=nets,
            metadata={
                "prompt": prompt,
                "design_type": design_type,
                "output_format": output_format,
            },
            svg_preview=svg_preview,
            confidence_score=self._calculate_confidence(prompt, components),
        )

        self._schematics[schematic_id] = schematic
        return schematic

    def _parse_prompt(
        self, prompt: str, design_type: str
    ) -> tuple[list[Component], list[Net]]:
        """Parse natural language prompt to extract components and nets."""
        components = []
        nets = []

        # Basic keyword extraction for component identification
        prompt_lower = prompt.lower()

        # Identify common component types from prompt
        component_keywords = {
            "microcontroller": {"type": "mcu", "package": "QFP-64"},
            "esp32": {"type": "mcu", "package": "QFN-48"},
            "lora": {"type": "rf_module", "package": "SMD"},
            "sensor": {"type": "sensor", "package": "SMD"},
            "capacitor": {"type": "passive", "value": "100nF"},
            "resistor": {"type": "passive", "value": "10k"},
            "led": {"type": "indicator", "package": "0805"},
            "power": {"type": "power_supply", "package": "module"},
            "regulator": {"type": "voltage_regulator", "package": "SOT-223"},
            "antenna": {"type": "rf_component", "package": "SMD"},
            "crystal": {"type": "oscillator", "package": "HC49"},
            "usb": {"type": "connector", "package": "USB-C"},
        }

        x_pos = 100
        for keyword, props in component_keywords.items():
            if keyword in prompt_lower:
                comp_id = str(uuid.uuid4())[:8]
                components.append(
                    Component(
                        id=comp_id,
                        name=keyword.upper(),
                        type=props["type"],
                        value=props.get("value"),
                        package=props.get("package"),
                        pins=[
                            {"name": "VCC", "number": 1},
                            {"name": "GND", "number": 2},
                            {"name": "IO", "number": 3},
                        ],
                        position={"x": x_pos, "y": 100},
                    )
                )
                x_pos += 150

        # Generate power and ground nets if components exist
        if components:
            nets.append(
                Net(
                    id=str(uuid.uuid4())[:8],
                    name="VCC",
                    source={"component": "power", "pin": 1},
                    destination={"component": "all", "pin": "VCC"},
                    net_class="power",
                )
            )
            nets.append(
                Net(
                    id=str(uuid.uuid4())[:8],
                    name="GND",
                    source={"component": "power", "pin": 2},
                    destination={"component": "all", "pin": "GND"},
                    net_class="power",
                )
            )

        return components, nets

    def _generate_svg_preview(
        self, components: list[Component], nets: list[Net]
    ) -> str:
        """Generate an SVG preview of the schematic."""
        width = max((c.position.get("x", 0) for c in components), default=0) + 200
        height = 300

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
            '<style>.component { fill: #f0f0f0; stroke: #333; stroke-width: 2; }',
            '.text { font-family: Arial; font-size: 12px; }</style>',
        ]

        # Draw components
        for comp in components:
            x = comp.position.get("x", 0)
            y = comp.position.get("y", 0)
            svg_parts.append(
                f'<rect class="component" x="{x}" y="{y}" width="100" height="60" rx="5"/>'
            )
            svg_parts.append(
                f'<text class="text" x="{x + 50}" y="{y + 35}" text-anchor="middle">{comp.name}</text>'
            )

        # Draw connection lines for nets
        for i, net in enumerate(nets):
            y_offset = 180 + i * 20
            svg_parts.append(
                f'<line x1="50" y1="{y_offset}" x2="{width - 50}" y2="{y_offset}" '
                f'stroke="#0066cc" stroke-width="2"/>'
            )
            svg_parts.append(
                f'<text class="text" x="10" y="{y_offset + 5}">{net.name}</text>'
            )

        svg_parts.append("</svg>")
        return "".join(svg_parts)

    def _calculate_confidence(
        self, prompt: str, components: list[Component]
    ) -> float:
        """Calculate confidence score for the generated schematic."""
        if not components:
            return 0.0

        # Base confidence on prompt clarity and component count
        word_count = len(prompt.split())
        component_count = len(components)

        # More specific prompts with more components get higher scores
        base_score = min(0.5 + (word_count * 0.02) + (component_count * 0.05), 0.95)
        return round(base_score, 2)

    def get_schematic(self, schematic_id: str) -> Optional[SchematicResponse]:
        """Get a schematic by ID."""
        return self._schematics.get(schematic_id)


# Singleton instance
schematic_service = SchematicService()
