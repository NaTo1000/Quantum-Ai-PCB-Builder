"""
Circuit representation for PCB design.

This module provides the Circuit class which represents a complete
electrical circuit with components, nets, and connectivity information.
"""

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import networkx as nx

from quantum_pcb_builder.core.component import Component


@dataclass
class Net:
    """
    Represents an electrical net connecting multiple pins.

    A net is a collection of electrically connected pins that must
    be routed together on the PCB.
    """

    name: str
    connections: list[tuple[str, str]] = field(default_factory=list)
    net_class: str = "signal"
    width_mm: float = 0.25
    properties: dict[str, Any] = field(default_factory=dict)
    uuid: str = field(default_factory=lambda: str(uuid4()))

    def add_connection(self, component_uuid: str, pin_name: str) -> None:
        """Add a pin connection to this net."""
        self.connections.append((component_uuid, pin_name))

    def get_pin_count(self) -> int:
        """Return the number of pins in this net."""
        return len(self.connections)


class Circuit:
    """
    Represents a complete electronic circuit.

    This class manages components, nets, and provides graph-based
    analysis capabilities for circuit optimization.

    Attributes:
        name: Circuit name/identifier
        components: Dictionary of components by UUID
        nets: Dictionary of nets by name
        connectivity_graph: NetworkX graph for circuit analysis
    """

    def __init__(self, name: str = "Untitled Circuit") -> None:
        """Initialize an empty circuit."""
        self.name = name
        self.components: dict[str, Component] = {}
        self.nets: dict[str, Net] = {}
        self.connectivity_graph: nx.Graph = nx.Graph()
        self._uuid = str(uuid4())

    @property
    def uuid(self) -> str:
        """Return the unique identifier for this circuit."""
        return self._uuid

    def add_component(self, component: Component) -> str:
        """
        Add a component to the circuit.

        Args:
            component: Component to add

        Returns:
            UUID of the added component
        """
        self.components[component.uuid] = component
        self.connectivity_graph.add_node(
            component.uuid,
            component=component,
            component_type=component.component_type.name,
        )
        return component.uuid

    def remove_component(self, component_uuid: str) -> bool:
        """
        Remove a component from the circuit.

        Args:
            component_uuid: UUID of component to remove

        Returns:
            True if component was removed, False if not found
        """
        if component_uuid not in self.components:
            return False

        # Remove from connectivity graph
        if self.connectivity_graph.has_node(component_uuid):
            self.connectivity_graph.remove_node(component_uuid)

        # Remove from nets
        for net in self.nets.values():
            net.connections = [
                (c_uuid, pin) for c_uuid, pin in net.connections if c_uuid != component_uuid
            ]

        del self.components[component_uuid]
        return True

    def add_net(self, net: Net) -> str:
        """
        Add a net to the circuit.

        Args:
            net: Net to add

        Returns:
            UUID of the added net
        """
        self.nets[net.name] = net
        self._update_connectivity_from_net(net)
        return net.uuid

    def connect(
        self,
        component1_uuid: str,
        pin1: str,
        component2_uuid: str,
        pin2: str,
        net_name: str | None = None,
    ) -> Net:
        """
        Create a connection between two component pins.

        Args:
            component1_uuid: UUID of first component
            pin1: Pin name on first component
            component2_uuid: UUID of second component
            pin2: Pin name on second component
            net_name: Optional net name (auto-generated if not provided)

        Returns:
            The Net object containing this connection
        """
        if component1_uuid not in self.components:
            raise ValueError(f"Component {component1_uuid} not found")
        if component2_uuid not in self.components:
            raise ValueError(f"Component {component2_uuid} not found")

        if net_name is None:
            net_name = f"NET_{len(self.nets)}"

        if net_name in self.nets:
            net = self.nets[net_name]
        else:
            net = Net(name=net_name)
            self.nets[net_name] = net

        net.add_connection(component1_uuid, pin1)
        net.add_connection(component2_uuid, pin2)

        # Update connectivity graph
        self.connectivity_graph.add_edge(
            component1_uuid,
            component2_uuid,
            net=net_name,
            pin1=pin1,
            pin2=pin2,
        )

        return net

    def _update_connectivity_from_net(self, net: Net) -> None:
        """Update the connectivity graph based on a net."""
        connections = net.connections
        for i, (uuid1, pin1) in enumerate(connections):
            for uuid2, pin2 in connections[i + 1 :]:
                if uuid1 in self.components and uuid2 in self.components:
                    self.connectivity_graph.add_edge(
                        uuid1, uuid2, net=net.name, pin1=pin1, pin2=pin2
                    )

    def get_component_connections(self, component_uuid: str) -> list[tuple[str, str, str]]:
        """
        Get all connections for a component.

        Args:
            component_uuid: UUID of the component

        Returns:
            List of (connected_uuid, net_name, pin_name) tuples
        """
        if component_uuid not in self.components:
            return []

        connections = []
        for net_name, net in self.nets.items():
            for conn_uuid, pin_name in net.connections:
                if conn_uuid == component_uuid:
                    for other_uuid, _ in net.connections:
                        if other_uuid != component_uuid:
                            connections.append((other_uuid, net_name, pin_name))

        return connections

    def get_critical_path_length(self) -> int:
        """
        Calculate the critical path length in the circuit graph.

        Returns:
            Length of the longest path in the connectivity graph
        """
        if len(self.connectivity_graph) == 0:
            return 0

        # For general graphs, find the longest shortest path
        try:
            path_lengths = dict(nx.all_pairs_shortest_path_length(self.connectivity_graph))
            max_length = 0
            for source_paths in path_lengths.values():
                for length in source_paths.values():
                    max_length = max(max_length, length)
            return max_length
        except nx.NetworkXError:
            return 0

    def get_connectivity_density(self) -> float:
        """
        Calculate the connectivity density of the circuit.

        Returns:
            Ratio of actual connections to possible connections
        """
        n = len(self.components)
        if n <= 1:
            return 0.0

        max_edges = n * (n - 1) / 2
        actual_edges = self.connectivity_graph.number_of_edges()
        return actual_edges / max_edges

    def get_component_centrality(self) -> dict[str, float]:
        """
        Calculate betweenness centrality for all components.

        Components with high centrality are critical routing points
        that should be optimally placed.

        Returns:
            Dictionary mapping component UUID to centrality score
        """
        if len(self.connectivity_graph) == 0:
            return {}

        return nx.betweenness_centrality(self.connectivity_graph)

    def find_connected_clusters(self) -> list[set[str]]:
        """
        Find clusters of connected components.

        Returns:
            List of sets, each containing UUIDs of connected components
        """
        return [set(cc) for cc in nx.connected_components(self.connectivity_graph)]

    def to_adjacency_matrix(self) -> tuple[list[str], list[list[int]]]:
        """
        Convert circuit connectivity to an adjacency matrix.

        Returns:
            Tuple of (component_uuids, adjacency_matrix)
        """
        nodes = list(self.components.keys())
        n = len(nodes)
        matrix = [[0] * n for _ in range(n)]

        node_index = {uuid: i for i, uuid in enumerate(nodes)}

        for u, v in self.connectivity_graph.edges():
            if u in node_index and v in node_index:
                i, j = node_index[u], node_index[v]
                matrix[i][j] = 1
                matrix[j][i] = 1

        return nodes, matrix

    def estimate_total_wire_length(self) -> float:
        """
        Estimate total wire length based on component positions.

        Returns:
            Estimated total wire length in mm
        """
        total_length = 0.0
        for net in self.nets.values():
            positions = []
            for comp_uuid, _ in net.connections:
                if comp_uuid in self.components:
                    positions.append(self.components[comp_uuid].position)

            # Calculate minimum spanning tree length
            if len(positions) >= 2:
                for i, pos1 in enumerate(positions):
                    for pos2 in positions[i + 1 :]:
                        dx = pos1[0] - pos2[0]
                        dy = pos1[1] - pos2[1]
                        total_length += (dx * dx + dy * dy) ** 0.5

        return total_length

    def validate(self) -> list[str]:
        """
        Validate circuit integrity.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check for orphan components
        isolated = list(nx.isolates(self.connectivity_graph))
        if isolated:
            errors.append(
                f"Isolated components (no connections): {[self.components[u].name for u in isolated if u in self.components]}"
            )

        # Check for empty nets
        for net_name, net in self.nets.items():
            if net.get_pin_count() < 2:
                errors.append(f"Net '{net_name}' has fewer than 2 connections")

        # Check for component overlaps
        comp_list = list(self.components.values())
        for i, comp1 in enumerate(comp_list):
            for comp2 in comp_list[i + 1 :]:
                if comp1.overlaps(comp2):
                    errors.append(f"Components '{comp1.name}' and '{comp2.name}' overlap")

        return errors

    def __len__(self) -> int:
        """Return the number of components in the circuit."""
        return len(self.components)

    def __repr__(self) -> str:
        """Return string representation of the circuit."""
        return (
            f"Circuit(name='{self.name}', components={len(self.components)}, nets={len(self.nets)})"
        )
