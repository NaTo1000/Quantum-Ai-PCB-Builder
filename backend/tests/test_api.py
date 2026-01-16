"""Tests for the main API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestRootEndpoints:
    """Tests for root endpoints."""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Quantum AI PCB Builder API"
        assert data["version"] == "1.0.0"
        assert len(data["features"]) == 5

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestSchematicEndpoints:
    """Tests for schematic generation endpoints."""

    def test_generate_schematic(self, client):
        """Test generating a schematic from a prompt."""
        response = client.post(
            "/api/schematic/generate",
            json={
                "prompt": "Create an ESP32 board with LoRa module and LED indicators",
                "design_type": "pcb",
                "output_format": "rtl",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "components" in data
        assert "nets" in data
        assert "svg_preview" in data
        assert data["confidence_score"] > 0

    def test_generate_schematic_empty_prompt(self, client):
        """Test that empty prompt returns error."""
        response = client.post(
            "/api/schematic/generate",
            json={"prompt": "   "},
        )
        assert response.status_code == 400

    def test_get_schematic_not_found(self, client):
        """Test getting a non-existent schematic."""
        response = client.get("/api/schematic/nonexistent-id")
        assert response.status_code == 404


class TestDesignChecksEndpoints:
    """Tests for design check endpoints."""

    def test_run_design_checks(self, client):
        """Test running design checks on a schematic."""
        # First create a schematic
        create_response = client.post(
            "/api/schematic/generate",
            json={"prompt": "ESP32 microcontroller with power regulator"},
        )
        schematic_id = create_response.json()["id"]

        # Run checks
        response = client.post(
            "/api/checks/run",
            json={
                "schematic_id": schematic_id,
                "check_types": ["drc", "lvs", "thermal", "signal_integrity"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "passed" in data
        assert "violations" in data
        assert "summary" in data


class TestSimulationEndpoints:
    """Tests for simulation endpoints."""

    def test_run_spice_simulation(self, client):
        """Test running SPICE simulation."""
        # First create a schematic
        create_response = client.post(
            "/api/schematic/generate",
            json={"prompt": "Simple LED circuit with resistor"},
        )
        schematic_id = create_response.json()["id"]

        # Run simulation
        response = client.post(
            "/api/simulation/run",
            json={
                "schematic_id": schematic_id,
                "simulation_type": "spice",
                "parameters": {"analysis": "transient"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "simulation_id" in data
        assert "result" in data
        assert data["result"]["status"] == "completed"

    def test_run_timing_simulation(self, client):
        """Test running timing simulation."""
        create_response = client.post(
            "/api/schematic/generate",
            json={"prompt": "Digital circuit with microcontroller"},
        )
        schematic_id = create_response.json()["id"]

        response = client.post(
            "/api/simulation/run",
            json={
                "schematic_id": schematic_id,
                "simulation_type": "timing",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["timing_report"] is not None

    def test_run_power_simulation(self, client):
        """Test running power simulation."""
        create_response = client.post(
            "/api/schematic/generate",
            json={"prompt": "ESP32 with sensors and LoRa"},
        )
        schematic_id = create_response.json()["id"]

        response = client.post(
            "/api/simulation/run",
            json={
                "schematic_id": schematic_id,
                "simulation_type": "power",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["power_report"] is not None


class TestComponentEndpoints:
    """Tests for component and BOM endpoints."""

    def test_generate_bom(self, client):
        """Test generating BOM from schematic."""
        create_response = client.post(
            "/api/schematic/generate",
            json={"prompt": "ESP32 with capacitor and resistor"},
        )
        schematic_id = create_response.json()["id"]

        response = client.post(f"/api/components/bom/{schematic_id}")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total_components" in data
        assert "estimated_cost" in data

    def test_generate_component_drawing(self, client):
        """Test generating component SVG drawing."""
        response = client.post(
            "/api/components/drawing",
            json={"component_id": "esp32", "output_format": "svg"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "svg_data" in data
        assert "<svg" in data["svg_data"]


class TestVendorEndpoints:
    """Tests for vendor matching endpoints."""

    def test_list_vendors(self, client):
        """Test listing all vendors."""
        response = client.get("/api/vendors/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_list_vendors_by_type(self, client):
        """Test filtering vendors by type."""
        response = client.get("/api/vendors/?vendor_type=assembler")
        assert response.status_code == 200
        data = response.json()
        assert all(v["type"] == "assembler" for v in data)

    def test_match_vendors(self, client):
        """Test vendor matching for a schematic."""
        create_response = client.post(
            "/api/schematic/generate",
            json={"prompt": "ESP32 IoT board with sensors"},
        )
        schematic_id = create_response.json()["id"]

        response = client.post(
            "/api/vendors/match",
            json={
                "schematic_id": schematic_id,
                "quantity": 1000,
                "preferred_locations": ["USA"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "matched_vendors" in data
        assert "quotes" in data
        assert "recommended_vendor_id" in data
