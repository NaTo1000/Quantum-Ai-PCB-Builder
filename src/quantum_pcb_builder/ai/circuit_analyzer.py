"""
AI-Powered Circuit Analyzer.

This module provides intelligent circuit analysis including:
- Design rule checking
- Signal integrity analysis
- Power analysis
- Thermal analysis
- Component placement scoring
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from quantum_pcb_builder.core.circuit import Circuit
from quantum_pcb_builder.core.component import ComponentType
from quantum_pcb_builder.core.pcb import PCBBoard


class AnalysisSeverity(Enum):
    """Severity levels for analysis findings."""

    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class AnalysisFinding:
    """A single finding from circuit analysis."""

    category: str
    message: str
    severity: AnalysisSeverity
    component_uuid: str | None = None
    location: tuple[float, float] | None = None
    recommendation: str = ""


@dataclass
class AnalysisResult:
    """Complete result of circuit analysis."""

    findings: list[AnalysisFinding] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    overall_score: float = 0.0
    passed: bool = True

    def add_finding(self, finding: AnalysisFinding) -> None:
        """Add a finding to the result."""
        self.findings.append(finding)
        if finding.severity in (AnalysisSeverity.ERROR, AnalysisSeverity.CRITICAL):
            self.passed = False

    def get_findings_by_severity(self, severity: AnalysisSeverity) -> list[AnalysisFinding]:
        """Get all findings of a specific severity."""
        return [f for f in self.findings if f.severity == severity]


class CircuitAnalyzer:
    """
    AI-powered circuit analysis engine.

    Performs comprehensive analysis of PCB designs including
    electrical, thermal, and manufacturability checks.
    """

    def __init__(
        self,
        strict_mode: bool = False,
        custom_rules: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Initialize the circuit analyzer.

        Args:
            strict_mode: Enable strict checking rules
            custom_rules: Custom analysis rules to apply
        """
        self.strict_mode = strict_mode
        self.custom_rules = custom_rules or []

    def analyze(
        self,
        circuit: Circuit,
        board: PCBBoard | None = None,
    ) -> AnalysisResult:
        """
        Perform comprehensive circuit analysis.

        Args:
            circuit: Circuit to analyze
            board: Optional PCB board for physical analysis

        Returns:
            AnalysisResult with findings and scores
        """
        result = AnalysisResult()

        # Run all analysis passes
        self._analyze_connectivity(circuit, result)
        self._analyze_component_placement(circuit, result)
        self._analyze_power_distribution(circuit, result)
        self._analyze_signal_integrity(circuit, result)

        if board:
            self._analyze_board_design(board, result)
            self._analyze_thermal_distribution(circuit, board, result)

        # Calculate overall score
        result.overall_score = self._calculate_overall_score(result)

        return result

    def _analyze_connectivity(self, circuit: Circuit, result: AnalysisResult) -> None:
        """Analyze circuit connectivity."""
        # Check for isolated components
        clusters = circuit.find_connected_clusters()

        if len(clusters) > 1:
            result.add_finding(
                AnalysisFinding(
                    category="connectivity",
                    message=f"Circuit has {len(clusters)} disconnected clusters",
                    severity=AnalysisSeverity.WARNING,
                    recommendation="Connect all components to form a single network",
                )
            )

        # Check for unconnected pins
        for component in circuit.components.values():
            connections = circuit.get_component_connections(component.uuid)
            if not connections and len(circuit.components) > 1:
                result.add_finding(
                    AnalysisFinding(
                        category="connectivity",
                        message=f"Component '{component.name}' has no connections",
                        severity=AnalysisSeverity.WARNING,
                        component_uuid=component.uuid,
                        recommendation="Connect component to circuit or remove if unused",
                    )
                )

        # Connectivity density score
        density = circuit.get_connectivity_density()
        result.scores["connectivity_density"] = density
        result.metrics["connectivity_density"] = density
        result.metrics["cluster_count"] = len(clusters)

    def _analyze_component_placement(self, circuit: Circuit, result: AnalysisResult) -> None:
        """Analyze component placement quality."""
        components = list(circuit.components.values())

        if not components:
            return

        # Check for overlaps
        overlap_count = 0
        for i, comp1 in enumerate(components):
            for comp2 in components[i + 1 :]:
                if comp1.overlaps(comp2):
                    overlap_count += 1
                    result.add_finding(
                        AnalysisFinding(
                            category="placement",
                            message=f"Components '{comp1.name}' and '{comp2.name}' overlap",
                            severity=AnalysisSeverity.ERROR,
                            component_uuid=comp1.uuid,
                            location=comp1.position,
                            recommendation="Reposition components to avoid overlap",
                        )
                    )

        # Calculate placement metrics
        wire_length = circuit.estimate_total_wire_length()
        result.metrics["total_wire_length_mm"] = wire_length
        result.metrics["overlap_count"] = overlap_count

        # Calculate centrality-based placement score
        centrality = circuit.get_component_centrality()
        if centrality:
            max_centrality = max(centrality.values())
            result.scores["centrality_utilization"] = max_centrality

        # Placement score (lower wire length is better)
        max_wire = len(components) * 100
        placement_score = 1.0 - min(1.0, wire_length / max_wire) if max_wire > 0 else 1.0
        result.scores["placement_quality"] = placement_score

    def _analyze_power_distribution(self, circuit: Circuit, result: AnalysisResult) -> None:
        """Analyze power distribution network."""
        power_nets = ["VCC", "VDD", "3V3", "5V", "GND", "VSS"]

        # Find power-related nets
        found_power_nets = []
        for net_name in circuit.nets:
            if any(p in net_name.upper() for p in power_nets):
                found_power_nets.append(net_name)

        if not found_power_nets:
            result.add_finding(
                AnalysisFinding(
                    category="power",
                    message="No power nets detected in circuit",
                    severity=AnalysisSeverity.WARNING,
                    recommendation="Ensure power and ground nets are properly named",
                )
            )

        # Check for voltage regulators
        regulators = [
            c
            for c in circuit.components.values()
            if c.component_type == ComponentType.VOLTAGE_REGULATOR
        ]

        has_regulator = len(regulators) > 0
        result.metrics["voltage_regulator_count"] = len(regulators)
        result.metrics["power_nets"] = found_power_nets

        # Power score
        power_score = 0.8 if has_regulator else 0.5
        if found_power_nets:
            power_score += 0.2
        result.scores["power_distribution"] = min(1.0, power_score)

    def _analyze_signal_integrity(self, circuit: Circuit, result: AnalysisResult) -> None:
        """Analyze signal integrity concerns."""
        # Check critical path length
        critical_path = circuit.get_critical_path_length()
        result.metrics["critical_path_length"] = critical_path

        if critical_path > 10:
            result.add_finding(
                AnalysisFinding(
                    category="signal_integrity",
                    message=f"Long critical path detected: {critical_path} nodes",
                    severity=AnalysisSeverity.INFO,
                    recommendation="Consider optimizing component placement for critical signals",
                )
            )

        # Check for high-frequency components
        high_freq_components = []
        for component in circuit.components.values():
            freq = component.properties.get("frequency_mhz", 0)
            if isinstance(freq, (int, float)) and freq > 100:
                high_freq_components.append(component)

        if high_freq_components:
            result.add_finding(
                AnalysisFinding(
                    category="signal_integrity",
                    message=f"{len(high_freq_components)} high-frequency components detected",
                    severity=AnalysisSeverity.INFO,
                    recommendation="Ensure proper decoupling capacitors near high-frequency ICs",
                )
            )

        # Signal integrity score
        base_score = 1.0
        if critical_path > 10:
            base_score -= 0.1 * (critical_path - 10) / 10
        result.scores["signal_integrity"] = max(0.0, base_score)

    def _analyze_board_design(self, board: PCBBoard, result: AnalysisResult) -> None:
        """Analyze PCB board design."""
        # Check design rule violations
        violations = board.check_design_rule_violations()

        for violation in violations:
            result.add_finding(
                AnalysisFinding(
                    category="drc",
                    message=violation,
                    severity=AnalysisSeverity.ERROR,
                    recommendation="Fix design rule violation before manufacturing",
                )
            )

        # Board metrics
        result.metrics["board_dimensions"] = (board.width_mm, board.height_mm)
        result.metrics["layer_count"] = board.layer_count
        result.metrics["component_density"] = board.get_component_density()
        result.metrics["via_count"] = board.get_via_count()
        result.metrics["total_trace_length"] = board.get_total_trace_length()

        # Board utilization score
        density = board.get_component_density()
        if density > 0.7:
            result.add_finding(
                AnalysisFinding(
                    category="density",
                    message=f"High component density ({density:.1%})",
                    severity=AnalysisSeverity.WARNING,
                    recommendation="Consider using a larger board or more layers",
                )
            )

        density_score = 1.0 - abs(density - 0.4)
        result.scores["board_utilization"] = max(0.0, density_score)

    def _analyze_thermal_distribution(
        self,
        circuit: Circuit,
        board: PCBBoard,
        result: AnalysisResult,
    ) -> None:
        """Analyze thermal distribution on the board."""
        # Identify heat-generating components
        hot_components = []

        for component in circuit.components.values():
            power_dissipation = component.properties.get("power_w", 0)
            if isinstance(power_dissipation, (int, float)) and power_dissipation > 0.5:
                hot_components.append((component, power_dissipation))

        if not hot_components:
            # Check for power ICs
            for component in circuit.components.values():
                if component.component_type in (
                    ComponentType.VOLTAGE_REGULATOR,
                    ComponentType.MICROCONTROLLER,
                ):
                    hot_components.append((component, 0.3))

        result.metrics["hot_component_count"] = len(hot_components)

        # Check thermal spacing
        if len(hot_components) >= 2:
            for i, (comp1, _) in enumerate(hot_components):
                for comp2, _ in hot_components[i + 1 :]:
                    distance = comp1.distance_to(comp2)
                    if distance < 5.0:
                        result.add_finding(
                            AnalysisFinding(
                                category="thermal",
                                message=f"Hot components '{comp1.name}' and '{comp2.name}' are too close ({distance:.1f}mm)",
                                severity=AnalysisSeverity.WARNING,
                                component_uuid=comp1.uuid,
                                recommendation="Increase spacing between heat-generating components",
                            )
                        )

        # Thermal score
        thermal_score = 1.0
        if hot_components:
            thermal_score -= 0.1 * len(hot_components) / 10
        result.scores["thermal"] = max(0.5, thermal_score)

    def _calculate_overall_score(self, result: AnalysisResult) -> float:
        """Calculate overall design score from individual scores."""
        if not result.scores:
            return 0.5

        weights = {
            "connectivity_density": 0.15,
            "placement_quality": 0.25,
            "power_distribution": 0.15,
            "signal_integrity": 0.20,
            "board_utilization": 0.15,
            "thermal": 0.10,
        }

        total_weight = 0.0
        weighted_sum = 0.0

        for key, weight in weights.items():
            if key in result.scores:
                weighted_sum += result.scores[key] * weight
                total_weight += weight

        overall = weighted_sum / total_weight if total_weight > 0 else 0.5

        # Penalty for critical/error findings
        error_count = len(result.get_findings_by_severity(AnalysisSeverity.ERROR))
        critical_count = len(result.get_findings_by_severity(AnalysisSeverity.CRITICAL))

        overall -= error_count * 0.05
        overall -= critical_count * 0.15

        return max(0.0, min(1.0, overall))


class DesignOptimizer:
    """
    AI-powered design optimizer.

    Uses analysis results to suggest and apply optimizations.
    """

    def __init__(self, analyzer: CircuitAnalyzer | None = None) -> None:
        """Initialize optimizer with analyzer."""
        self.analyzer = analyzer or CircuitAnalyzer()

    def suggest_optimizations(
        self,
        circuit: Circuit,
        board: PCBBoard | None = None,
    ) -> list[dict[str, Any]]:
        """
        Suggest optimizations for the design.

        Args:
            circuit: Circuit to optimize
            board: Optional PCB board

        Returns:
            List of optimization suggestions
        """
        result = self.analyzer.analyze(circuit, board)
        suggestions = []

        # Generate suggestions from findings
        for finding in result.findings:
            if finding.severity in (AnalysisSeverity.WARNING, AnalysisSeverity.ERROR):
                suggestions.append(
                    {
                        "category": finding.category,
                        "issue": finding.message,
                        "recommendation": finding.recommendation,
                        "priority": "high"
                        if finding.severity == AnalysisSeverity.ERROR
                        else "medium",
                        "component_uuid": finding.component_uuid,
                    }
                )

        # Add score-based suggestions
        if result.scores.get("placement_quality", 1.0) < 0.6:
            suggestions.append(
                {
                    "category": "placement",
                    "issue": "Poor component placement detected",
                    "recommendation": "Use placement optimizer to reduce wire length",
                    "priority": "high",
                }
            )

        if result.scores.get("thermal", 1.0) < 0.7:
            suggestions.append(
                {
                    "category": "thermal",
                    "issue": "Thermal concerns detected",
                    "recommendation": "Add thermal relief pads or heat sinks",
                    "priority": "medium",
                }
            )

        return suggestions

    def auto_optimize(
        self,
        circuit: Circuit,
        board: PCBBoard | None = None,
        max_iterations: int = 10,
    ) -> tuple[Circuit, AnalysisResult]:
        """
        Automatically apply optimizations to improve design.

        Args:
            circuit: Circuit to optimize
            board: Optional PCB board
            max_iterations: Maximum optimization iterations

        Returns:
            Tuple of (optimized_circuit, final_analysis)
        """
        best_score = 0.0
        best_circuit = circuit

        for _ in range(max_iterations):
            result = self.analyzer.analyze(circuit, board)

            if result.overall_score > best_score:
                best_score = result.overall_score
                best_circuit = circuit

            if result.overall_score > 0.9:
                break

            # Apply automatic optimizations based on findings
            self._apply_auto_fixes(circuit, result)

        final_result = self.analyzer.analyze(best_circuit, board)
        return best_circuit, final_result

    def _apply_auto_fixes(self, circuit: Circuit, result: AnalysisResult) -> None:
        """Apply automatic fixes for common issues."""
        # This is a placeholder for automatic optimization logic
        # In a full implementation, this would:
        # - Adjust component positions to reduce wire length
        # - Add decoupling capacitors
        # - Optimize thermal spacing
        pass
