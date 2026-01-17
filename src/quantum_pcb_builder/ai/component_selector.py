"""
AI-Powered Component Selection System.

This module provides intelligent component selection based on:
- Design requirements analysis
- Component compatibility checking
- Cost optimization
- Availability scoring
- Performance matching
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

import numpy as np

from quantum_pcb_builder.core.component import Component, ComponentType, Footprint


class OptimizationGoal(Enum):
    """Goals for component selection optimization."""

    COST = auto()
    PERFORMANCE = auto()
    AVAILABILITY = auto()
    SIZE = auto()
    POWER_EFFICIENCY = auto()
    RELIABILITY = auto()


@dataclass
class SelectionCriteria:
    """Criteria for component selection."""

    component_type: ComponentType
    min_value: float | None = None
    max_value: float | None = None
    package_preferences: list[str] = field(default_factory=list)
    max_cost: float | None = None
    min_availability_score: float = 0.5
    optimization_goals: list[OptimizationGoal] = field(
        default_factory=lambda: [OptimizationGoal.COST]
    )
    required_properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentCandidate:
    """A candidate component for selection."""

    component: Component
    score: float = 0.0
    cost: float = 0.0
    availability_score: float = 1.0
    performance_score: float = 0.0
    size_score: float = 0.0


@dataclass
class ComponentDatabase:
    """
    In-memory component database for selection.

    In production, this would connect to a real component database API.
    """

    components: dict[str, Component] = field(default_factory=dict)
    pricing: dict[str, float] = field(default_factory=dict)
    availability: dict[str, float] = field(default_factory=dict)

    def add_component(
        self,
        component: Component,
        price: float = 0.0,
        availability: float = 1.0,
    ) -> None:
        """Add a component to the database."""
        self.components[component.uuid] = component
        self.pricing[component.uuid] = price
        self.availability[component.uuid] = availability

    def query(self, component_type: ComponentType | None = None) -> list[Component]:
        """Query components by type."""
        if component_type is None:
            return list(self.components.values())
        return [c for c in self.components.values() if c.component_type == component_type]


class ComponentSelector:
    """
    AI-powered component selection engine.

    Uses multi-criteria decision analysis (MCDA) with weighted
    scoring to select optimal components for a design.
    """

    def __init__(
        self,
        database: ComponentDatabase | None = None,
        weights: dict[OptimizationGoal, float] | None = None,
    ) -> None:
        """
        Initialize component selector.

        Args:
            database: Component database to search
            weights: Weights for optimization goals
        """
        self.database = database or self._create_default_database()
        self.weights = weights or {
            OptimizationGoal.COST: 0.3,
            OptimizationGoal.PERFORMANCE: 0.25,
            OptimizationGoal.AVAILABILITY: 0.2,
            OptimizationGoal.SIZE: 0.15,
            OptimizationGoal.POWER_EFFICIENCY: 0.1,
        }

    def select(
        self,
        criteria: SelectionCriteria,
        max_results: int = 5,
    ) -> list[ComponentCandidate]:
        """
        Select components matching the given criteria.

        Args:
            criteria: Selection criteria
            max_results: Maximum number of candidates to return

        Returns:
            List of ComponentCandidate objects, sorted by score
        """
        # Query candidates
        candidates = self._query_candidates(criteria)

        # Score each candidate
        scored_candidates = []
        for component in candidates:
            candidate = self._score_candidate(component, criteria)
            if self._meets_requirements(candidate, criteria):
                scored_candidates.append(candidate)

        # Sort by score (descending)
        scored_candidates.sort(key=lambda c: c.score, reverse=True)

        return scored_candidates[:max_results]

    def select_for_circuit(
        self,
        requirements: list[SelectionCriteria],
    ) -> dict[str, list[ComponentCandidate]]:
        """
        Select components for an entire circuit.

        Args:
            requirements: List of selection criteria for each component type

        Returns:
            Dictionary mapping requirement index to selected candidates
        """
        results = {}

        for i, criteria in enumerate(requirements):
            key = f"{criteria.component_type.name}_{i}"
            results[key] = self.select(criteria)

        return results

    def optimize_bom(
        self,
        selected_components: list[Component],
        budget: float,
    ) -> list[Component]:
        """
        Optimize Bill of Materials within budget constraints.

        Args:
            selected_components: Initially selected components
            budget: Maximum total cost

        Returns:
            Optimized list of components
        """
        optimized = []
        remaining_budget = budget

        for component in selected_components:
            price = self.database.pricing.get(component.uuid, 0.0)

            if price <= remaining_budget:
                optimized.append(component)
                remaining_budget -= price
            else:
                # Try to find a cheaper alternative
                cheaper = self._find_cheaper_alternative(component, remaining_budget)
                if cheaper:
                    optimized.append(cheaper)
                    remaining_budget -= self.database.pricing.get(cheaper.uuid, 0.0)

        return optimized

    def _query_candidates(self, criteria: SelectionCriteria) -> list[Component]:
        """Query database for matching candidates."""
        candidates = self.database.query(criteria.component_type)

        # Filter by package preference
        if criteria.package_preferences:
            candidates = [
                c for c in candidates if c.package in criteria.package_preferences or not c.package
            ]

        return candidates

    def _score_candidate(
        self,
        component: Component,
        criteria: SelectionCriteria,
    ) -> ComponentCandidate:
        """Score a candidate component."""
        uuid = component.uuid

        # Get raw scores
        cost = self.database.pricing.get(uuid, 0.0)
        availability = self.database.availability.get(uuid, 1.0)

        # Normalize scores
        cost_score = 1.0 / (1.0 + cost) if cost >= 0 else 0.0
        availability_score = availability

        # Size score (smaller is better)
        area = component.get_area()
        size_score = 1.0 / (1.0 + area / 100.0)

        # Performance score based on properties
        performance_score = self._calculate_performance_score(component, criteria)

        # Calculate weighted total score
        total_score = 0.0
        for goal in criteria.optimization_goals:
            weight = self.weights.get(goal, 0.0)
            if goal == OptimizationGoal.COST:
                total_score += weight * cost_score
            elif goal == OptimizationGoal.AVAILABILITY:
                total_score += weight * availability_score
            elif goal == OptimizationGoal.SIZE:
                total_score += weight * size_score
            elif goal == OptimizationGoal.PERFORMANCE:
                total_score += weight * performance_score

        return ComponentCandidate(
            component=component,
            score=total_score,
            cost=cost,
            availability_score=availability_score,
            performance_score=performance_score,
            size_score=size_score,
        )

    def _calculate_performance_score(
        self,
        component: Component,
        criteria: SelectionCriteria,
    ) -> float:
        """Calculate performance score based on component properties."""
        if not criteria.required_properties:
            return 1.0

        matches = 0
        total = len(criteria.required_properties)

        for prop_name, required_value in criteria.required_properties.items():
            actual_value = component.properties.get(prop_name)

            if actual_value is None:
                continue

            if isinstance(required_value, bool):
                if actual_value == required_value:
                    matches += 1
            elif isinstance(required_value, (int, float)):
                if actual_value >= required_value:
                    matches += 1
            elif actual_value == required_value:
                matches += 1

        return matches / total if total > 0 else 1.0

    def _meets_requirements(
        self,
        candidate: ComponentCandidate,
        criteria: SelectionCriteria,
    ) -> bool:
        """Check if candidate meets minimum requirements."""
        if criteria.max_cost is not None and candidate.cost > criteria.max_cost:
            return False

        return candidate.availability_score >= criteria.min_availability_score

    def _find_cheaper_alternative(
        self,
        component: Component,
        max_price: float,
    ) -> Component | None:
        """Find a cheaper alternative for a component."""
        alternatives = self.database.query(component.component_type)

        for alt in alternatives:
            price = self.database.pricing.get(alt.uuid, float("inf"))
            if price <= max_price:
                return alt

        return None

    def _create_default_database(self) -> ComponentDatabase:
        """Create a default component database with common components."""
        db = ComponentDatabase()

        # ESP32 variants
        esp32_wroom = Component(
            name="ESP32-WROOM-32",
            component_type=ComponentType.MICROCONTROLLER,
            package="SMD",
            footprint=Footprint("ESP32-WROOM-32", 18.0, 25.5, 38),
            properties={
                "cpu": "Xtensa LX6",
                "frequency_mhz": 240,
                "flash_mb": 4,
                "ram_kb": 520,
                "wifi": True,
                "bluetooth": True,
            },
        )
        db.add_component(esp32_wroom, price=2.50, availability=0.95)

        esp32_c3 = Component(
            name="ESP32-C3-MINI",
            component_type=ComponentType.MICROCONTROLLER,
            package="SMD",
            footprint=Footprint("ESP32-C3-MINI", 13.2, 16.6, 36),
            properties={
                "cpu": "RISC-V",
                "frequency_mhz": 160,
                "flash_mb": 4,
                "ram_kb": 400,
                "wifi": True,
                "bluetooth": True,
            },
        )
        db.add_component(esp32_c3, price=1.80, availability=0.90)

        # LoRa modules
        sx1276 = Component(
            name="SX1276",
            component_type=ComponentType.RF_MODULE,
            package="QFN-28",
            footprint=Footprint("QFN-28", 6.0, 6.0, 28),
            properties={
                "frequency_mhz": 868,
                "protocol": "LoRa",
                "sensitivity_dbm": -148,
                "tx_power_dbm": 20,
            },
        )
        db.add_component(sx1276, price=3.20, availability=0.85)

        # Voltage regulators
        ams1117 = Component(
            name="AMS1117-3.3",
            component_type=ComponentType.VOLTAGE_REGULATOR,
            package="SOT-223",
            footprint=Footprint("SOT-223", 6.5, 3.5, 3),
            properties={
                "voltage_in_max": 15.0,
                "voltage_out": 3.3,
                "current_max_ma": 1000,
                "dropout_v": 1.3,
            },
        )
        db.add_component(ams1117, price=0.15, availability=0.98)

        # Resistors
        for value in ["1k", "10k", "100k", "4.7k"]:
            resistor = Component(
                name=f"R_{value}",
                component_type=ComponentType.RESISTOR,
                value=value,
                package="0805",
                footprint=Footprint("0805", 2.0, 1.25, 2),
            )
            db.add_component(resistor, price=0.01, availability=0.99)

        # Capacitors
        for value in ["100nF", "10uF", "100uF"]:
            capacitor = Component(
                name=f"C_{value}",
                component_type=ComponentType.CAPACITOR,
                value=value,
                package="0805",
                footprint=Footprint("0805", 2.0, 1.25, 2),
            )
            db.add_component(capacitor, price=0.02, availability=0.99)

        return db


class ComponentRecommender:
    """
    Neural network-inspired component recommender.

    Uses a simple similarity-based recommendation approach
    that mimics collaborative filtering.
    """

    def __init__(self, database: ComponentDatabase) -> None:
        """Initialize recommender with component database."""
        self.database = database
        self._build_feature_matrix()

    def _build_feature_matrix(self) -> None:
        """Build feature matrix for similarity calculation."""
        components = list(self.database.components.values())
        n_components = len(components)

        if n_components == 0:
            self.feature_matrix = np.array([])
            self.component_ids = []
            return

        # Extract features
        features = []
        for comp in components:
            feat = self._extract_features(comp)
            features.append(feat)

        self.feature_matrix = np.array(features)
        self.component_ids = [c.uuid for c in components]

    def _extract_features(self, component: Component) -> list[float]:
        """Extract numerical features from a component."""
        features = [
            float(component.component_type.value),
            component.get_area(),
            self.database.pricing.get(component.uuid, 0.0),
            self.database.availability.get(component.uuid, 1.0),
        ]

        # Add property features
        for key in ["frequency_mhz", "flash_mb", "ram_kb"]:
            val = component.properties.get(key, 0)
            features.append(float(val) if isinstance(val, (int, float)) else 0.0)

        return features

    def recommend_similar(
        self,
        component: Component,
        n_recommendations: int = 3,
    ) -> list[Component]:
        """
        Recommend similar components.

        Args:
            component: Reference component
            n_recommendations: Number of recommendations

        Returns:
            List of similar components
        """
        if len(self.feature_matrix) == 0:
            return []

        # Calculate query features
        query_features = np.array(self._extract_features(component))

        # Normalize
        norms = np.linalg.norm(self.feature_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1
        normalized_matrix = self.feature_matrix / norms

        query_norm = np.linalg.norm(query_features)
        normalized_query = query_features / query_norm if query_norm > 0 else query_features

        # Calculate cosine similarity
        similarities = normalized_matrix @ normalized_query

        # Get top indices
        top_indices = np.argsort(similarities)[::-1]

        recommendations = []
        for idx in top_indices:
            comp_id = self.component_ids[idx]
            if comp_id != component.uuid:
                recommendations.append(self.database.components[comp_id])
                if len(recommendations) >= n_recommendations:
                    break

        return recommendations
