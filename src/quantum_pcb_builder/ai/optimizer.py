"""Layout optimization for PCB designs."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from quantum_pcb_builder.pcb.layout import PCBLayout, Position


class OptimizationGoal(Enum):
    """Goals for layout optimization."""

    MINIMIZE_SIZE = "minimize_size"
    MINIMIZE_TRACE_LENGTH = "minimize_trace_length"
    MAXIMIZE_SPACING = "maximize_spacing"
    THERMAL_DISTRIBUTION = "thermal_distribution"
    SIGNAL_INTEGRITY = "signal_integrity"


@dataclass
class OptimizationResult:
    """Result of an optimization run."""

    success: bool
    iterations: int
    improvement_percent: float
    metrics_before: dict[str, float]
    metrics_after: dict[str, float]
    message: str = ""


class LayoutOptimizer:
    """Optimizer for PCB layouts."""

    def __init__(self, max_iterations: int = 1000) -> None:
        """Initialize the optimizer."""
        self.max_iterations = max_iterations

    def optimize(
        self,
        layout: PCBLayout,
        goals: list[OptimizationGoal],
    ) -> OptimizationResult:
        """Optimize a PCB layout based on specified goals."""
        metrics_before = self._calculate_metrics(layout)

        # Apply optimization strategies based on goals
        iterations = 0
        improved = False

        for goal in goals:
            if goal == OptimizationGoal.MINIMIZE_TRACE_LENGTH:
                improved = self._optimize_trace_length(layout) or improved
                iterations += 1
            elif goal == OptimizationGoal.MAXIMIZE_SPACING:
                improved = self._optimize_spacing(layout) or improved
                iterations += 1
            elif goal == OptimizationGoal.THERMAL_DISTRIBUTION:
                improved = self._optimize_thermal(layout) or improved
                iterations += 1

        metrics_after = self._calculate_metrics(layout)

        # Calculate improvement
        improvement = 0.0
        if metrics_before.get("total_trace_length", 0) > 0:
            improvement = (
                (metrics_before["total_trace_length"] - metrics_after["total_trace_length"])
                / metrics_before["total_trace_length"]
                * 100
            )

        return OptimizationResult(
            success=improved,
            iterations=iterations,
            improvement_percent=improvement,
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            message="Optimization completed" if improved else "No improvements found",
        )

    def _calculate_metrics(self, layout: PCBLayout) -> dict[str, float]:
        """Calculate layout metrics."""
        placed = layout.get_placed_components()

        # Calculate total trace length
        total_trace_length = 0.0
        for conn in layout.get_connections():
            source_pos = layout.get_placement(conn.source_component_id)
            target_pos = layout.get_placement(conn.target_component_id)
            if source_pos and target_pos:
                total_trace_length += source_pos.distance_to(target_pos)

        # Calculate average component spacing
        avg_spacing = 0.0
        spacing_count = 0
        for i, pc_a in enumerate(placed):
            for pc_b in placed[i + 1 :]:
                avg_spacing += pc_a.position.distance_to(pc_b.position)
                spacing_count += 1
        if spacing_count > 0:
            avg_spacing /= spacing_count

        # Calculate board utilization
        component_area = len(placed) * 100  # Simplified: assume 100 sq mm per component
        board_area = layout.width_mm * layout.height_mm
        utilization = component_area / board_area * 100 if board_area > 0 else 0

        return {
            "total_trace_length": total_trace_length,
            "average_spacing": avg_spacing,
            "component_count": len(placed),
            "board_utilization": utilization,
        }

    def _optimize_trace_length(self, layout: PCBLayout) -> bool:
        """Optimize component placement to minimize trace length."""
        improved = False
        connections = layout.get_connections()
        layout.get_placed_components()

        # Simple greedy optimization: move heavily connected components closer
        connection_count: dict[str, int] = {}
        for conn in connections:
            connection_count[conn.source_component_id] = (
                connection_count.get(conn.source_component_id, 0) + 1
            )
            connection_count[conn.target_component_id] = (
                connection_count.get(conn.target_component_id, 0) + 1
            )

        # Find the most connected component (hub)
        if connection_count:
            hub_id = max(connection_count, key=lambda k: connection_count[k])
            hub_pos = layout.get_placement(hub_id)

            if hub_pos:
                # Move hub towards center if not already there
                center_x = layout.width_mm / 2
                center_y = layout.height_mm / 2
                current_distance = (
                    (hub_pos.x - center_x) ** 2 + (hub_pos.y - center_y) ** 2
                ) ** 0.5

                if current_distance > layout.width_mm * 0.1:
                    # Move 10% closer to center
                    new_x = hub_pos.x + (center_x - hub_pos.x) * 0.1
                    new_y = hub_pos.y + (center_y - hub_pos.y) * 0.1
                    layout._placements[hub_id] = Position(
                        x=new_x, y=new_y, rotation=hub_pos.rotation, layer=hub_pos.layer
                    )
                    improved = True

        return improved

    def _optimize_spacing(self, layout: PCBLayout) -> bool:
        """Optimize component spacing."""
        improved = False
        placed = layout.get_placed_components()
        min_spacing = 5.0  # Minimum 5mm spacing

        # Check each pair and push apart if too close
        for i, pc_a in enumerate(placed):
            for pc_b in placed[i + 1 :]:
                distance = pc_a.position.distance_to(pc_b.position)
                if distance < min_spacing:
                    # Calculate push vector
                    dx = pc_b.position.x - pc_a.position.x
                    dy = pc_b.position.y - pc_a.position.y

                    if distance > 0:
                        # Normalize and apply minimum spacing
                        push = (min_spacing - distance) / 2
                        nx = dx / distance if distance > 0 else 1
                        ny = dy / distance if distance > 0 else 0

                        # Update positions
                        pos_a = layout.get_placement(pc_a.component.component_id)
                        pos_b = layout.get_placement(pc_b.component.component_id)

                        if pos_a and pos_b:
                            new_a = Position(
                                x=max(0, min(layout.width_mm, pos_a.x - nx * push)),
                                y=max(0, min(layout.height_mm, pos_a.y - ny * push)),
                                rotation=pos_a.rotation,
                                layer=pos_a.layer,
                            )
                            new_b = Position(
                                x=max(0, min(layout.width_mm, pos_b.x + nx * push)),
                                y=max(0, min(layout.height_mm, pos_b.y + ny * push)),
                                rotation=pos_b.rotation,
                                layer=pos_b.layer,
                            )
                            layout._placements[pc_a.component.component_id] = new_a
                            layout._placements[pc_b.component.component_id] = new_b
                            improved = True

        return improved

    def _optimize_thermal(self, layout: PCBLayout) -> bool:
        """Optimize for thermal distribution."""
        improved = False

        # Identify high-power components
        high_power_components = []
        for comp in layout.components:
            specs = comp.specifications
            if specs.get("power_consumption_mw", 0) > 100:
                high_power_components.append(comp)

        # Spread high-power components apart
        if len(high_power_components) >= 2:
            # Calculate optimal positions (evenly distributed)
            for i, comp in enumerate(high_power_components):
                angle = i * (360 / len(high_power_components))
                radius = min(layout.width_mm, layout.height_mm) * 0.3
                center_x = layout.width_mm / 2
                center_y = layout.height_mm / 2

                import math

                new_x = center_x + radius * math.cos(math.radians(angle))
                new_y = center_y + radius * math.sin(math.radians(angle))

                current_pos = layout.get_placement(comp.component_id)
                if current_pos:
                    new_pos = Position(
                        x=new_x, y=new_y, rotation=current_pos.rotation, layer=current_pos.layer
                    )
                    layout._placements[comp.component_id] = new_pos
                    improved = True

        return improved

    def analyze(self, layout: PCBLayout) -> dict[str, Any]:
        """Analyze a layout and provide recommendations."""
        metrics = self._calculate_metrics(layout)
        recommendations: list[str] = []

        # Check trace length
        if metrics["total_trace_length"] > layout.width_mm * 5:
            recommendations.append("Consider reorganizing components to reduce trace length")

        # Check spacing
        if metrics["average_spacing"] < 5.0:
            recommendations.append("Components are closely packed, consider increasing board size")

        # Check utilization
        if metrics["board_utilization"] > 70:
            recommendations.append("High board utilization may cause manufacturing issues")
        elif metrics["board_utilization"] < 20:
            recommendations.append("Consider reducing board size to save costs")

        return {
            "metrics": metrics,
            "recommendations": recommendations,
        }
