"""Tests for circuit functionality."""

import pytest

from quantum_pcb_builder.core.circuit import Circuit, Net
from quantum_pcb_builder.core.component import Component, ComponentType, Footprint


class TestNet:
    """Tests for Net class."""

    def test_net_creation(self) -> None:
        """Test basic net creation."""
        net = Net(name="VCC", net_class="power")
        assert net.name == "VCC"
        assert net.net_class == "power"
        assert len(net.connections) == 0

    def test_add_connection(self) -> None:
        """Test adding connections to net."""
        net = Net(name="DATA")
        net.add_connection("comp1", "pin1")
        net.add_connection("comp2", "pin2")

        assert net.get_pin_count() == 2
        assert ("comp1", "pin1") in net.connections

    def test_net_defaults(self) -> None:
        """Test net default values."""
        net = Net(name="SIG")
        assert net.net_class == "signal"
        assert net.width_mm == 0.25


class TestCircuit:
    """Tests for Circuit class."""

    def test_circuit_creation(self) -> None:
        """Test basic circuit creation."""
        circuit = Circuit(name="Test Circuit")
        assert circuit.name == "Test Circuit"
        assert len(circuit.components) == 0
        assert len(circuit.nets) == 0

    def test_add_component(self) -> None:
        """Test adding components to circuit."""
        circuit = Circuit()
        comp = Component(name="R1", component_type=ComponentType.RESISTOR)

        uuid = circuit.add_component(comp)

        assert uuid == comp.uuid
        assert comp.uuid in circuit.components
        assert len(circuit) == 1

    def test_remove_component(self) -> None:
        """Test removing components from circuit."""
        circuit = Circuit()
        comp = Component(name="R1", component_type=ComponentType.RESISTOR)
        circuit.add_component(comp)

        result = circuit.remove_component(comp.uuid)

        assert result is True
        assert comp.uuid not in circuit.components
        assert len(circuit) == 0

    def test_remove_nonexistent_component(self) -> None:
        """Test removing non-existent component."""
        circuit = Circuit()
        result = circuit.remove_component("nonexistent-uuid")
        assert result is False

    def test_add_net(self) -> None:
        """Test adding nets to circuit."""
        circuit = Circuit()
        net = Net(name="VCC")

        uuid = circuit.add_net(net)

        assert uuid == net.uuid
        assert "VCC" in circuit.nets

    def test_connect_components(self) -> None:
        """Test connecting two components."""
        circuit = Circuit()
        comp1 = Component(name="U1", component_type=ComponentType.IC)
        comp2 = Component(name="R1", component_type=ComponentType.RESISTOR)

        circuit.add_component(comp1)
        circuit.add_component(comp2)

        net = circuit.connect(comp1.uuid, "OUT", comp2.uuid, "IN", "SIGNAL")

        assert net.name == "SIGNAL"
        assert net.get_pin_count() == 2
        assert "SIGNAL" in circuit.nets

    def test_connect_auto_net_name(self) -> None:
        """Test connection with auto-generated net name."""
        circuit = Circuit()
        comp1 = Component(name="U1", component_type=ComponentType.IC)
        comp2 = Component(name="R1", component_type=ComponentType.RESISTOR)

        circuit.add_component(comp1)
        circuit.add_component(comp2)

        net = circuit.connect(comp1.uuid, "OUT", comp2.uuid, "IN")

        assert net.name.startswith("NET_")

    def test_connect_invalid_component(self) -> None:
        """Test connecting with invalid component UUID."""
        circuit = Circuit()
        comp = Component(name="U1", component_type=ComponentType.IC)
        circuit.add_component(comp)

        with pytest.raises(ValueError, match="not found"):
            circuit.connect(comp.uuid, "OUT", "invalid-uuid", "IN")

    def test_get_component_connections(self) -> None:
        """Test getting component connections."""
        circuit = Circuit()
        comp1 = Component(name="U1", component_type=ComponentType.IC)
        comp2 = Component(name="R1", component_type=ComponentType.RESISTOR)
        comp3 = Component(name="C1", component_type=ComponentType.CAPACITOR)

        circuit.add_component(comp1)
        circuit.add_component(comp2)
        circuit.add_component(comp3)

        circuit.connect(comp1.uuid, "OUT1", comp2.uuid, "IN", "NET1")
        circuit.connect(comp1.uuid, "OUT2", comp3.uuid, "IN", "NET2")

        connections = circuit.get_component_connections(comp1.uuid)
        assert len(connections) == 2

    def test_find_connected_clusters(self) -> None:
        """Test finding connected component clusters."""
        circuit = Circuit()
        comp1 = Component(name="U1", component_type=ComponentType.IC)
        comp2 = Component(name="R1", component_type=ComponentType.RESISTOR)
        comp3 = Component(name="C1", component_type=ComponentType.CAPACITOR)

        circuit.add_component(comp1)
        circuit.add_component(comp2)
        circuit.add_component(comp3)

        circuit.connect(comp1.uuid, "OUT", comp2.uuid, "IN")

        clusters = circuit.find_connected_clusters()

        assert len(clusters) == 2

    def test_estimate_wire_length(self) -> None:
        """Test wire length estimation."""
        circuit = Circuit()

        comp1 = Component(name="U1", component_type=ComponentType.IC)
        comp1.position = (0.0, 0.0)

        comp2 = Component(name="R1", component_type=ComponentType.RESISTOR)
        comp2.position = (30.0, 40.0)

        circuit.add_component(comp1)
        circuit.add_component(comp2)
        circuit.connect(comp1.uuid, "OUT", comp2.uuid, "IN")

        wire_length = circuit.estimate_total_wire_length()

        assert wire_length == pytest.approx(50.0, rel=0.01)

    def test_connectivity_density(self) -> None:
        """Test connectivity density calculation."""
        circuit = Circuit()

        for i in range(5):
            comp = Component(name=f"C{i}", component_type=ComponentType.CAPACITOR)
            circuit.add_component(comp)

        comps = list(circuit.components.values())
        circuit.connect(comps[0].uuid, "1", comps[1].uuid, "1")
        circuit.connect(comps[1].uuid, "2", comps[2].uuid, "1")

        density = circuit.get_connectivity_density()

        assert 0 < density < 1

    def test_validate_circuit(self) -> None:
        """Test circuit validation."""
        circuit = Circuit()

        comp1 = Component(name="U1", component_type=ComponentType.IC)
        comp2 = Component(name="R1", component_type=ComponentType.RESISTOR)

        circuit.add_component(comp1)
        circuit.add_component(comp2)

        errors = circuit.validate()

        assert len(errors) > 0

    def test_validate_overlapping_components(self) -> None:
        """Test validation detects overlapping components."""
        circuit = Circuit()

        fp = Footprint("TEST", 10.0, 10.0, 4)
        comp1 = Component(name="U1", component_type=ComponentType.IC, footprint=fp)
        comp1.position = (10.0, 10.0)

        comp2 = Component(name="U2", component_type=ComponentType.IC, footprint=fp)
        comp2.position = (12.0, 12.0)

        circuit.add_component(comp1)
        circuit.add_component(comp2)

        errors = circuit.validate()

        assert any("overlap" in e.lower() for e in errors)

    def test_to_adjacency_matrix(self) -> None:
        """Test adjacency matrix generation."""
        circuit = Circuit()

        comp1 = Component(name="A", component_type=ComponentType.IC)
        comp2 = Component(name="B", component_type=ComponentType.IC)
        comp3 = Component(name="C", component_type=ComponentType.IC)

        circuit.add_component(comp1)
        circuit.add_component(comp2)
        circuit.add_component(comp3)

        circuit.connect(comp1.uuid, "1", comp2.uuid, "1")
        circuit.connect(comp2.uuid, "2", comp3.uuid, "1")

        nodes, matrix = circuit.to_adjacency_matrix()

        assert len(nodes) == 3
        assert len(matrix) == 3
        assert len(matrix[0]) == 3

    def test_repr(self) -> None:
        """Test string representation of circuit."""
        circuit = Circuit(name="Test")
        comp = Component(name="R1", component_type=ComponentType.RESISTOR)
        circuit.add_component(comp)

        repr_str = repr(circuit)

        assert "Test" in repr_str
        assert "components=1" in repr_str
