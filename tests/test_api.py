"""
Tests for the API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


class TestRootEndpoints:
    """Test suite for root API endpoints."""
    
    def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "Quantum AI PCB Builder"
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestDesignEndpoints:
    """Test suite for design-related endpoints."""
    
    def test_generate_design(self, client):
        """Test design generation endpoint."""
        response = client.post(
            "/api/v1/design",
            json={
                "prompt": "ESP32 board with WiFi and temperature sensor",
                "run_validation": True,
                "run_simulation": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "design_intent" in data
        assert "schematic" in data
        assert "validation" in data
    
    def test_generate_design_with_simulation(self, client):
        """Test design generation with simulations."""
        response = client.post(
            "/api/v1/design",
            json={
                "prompt": "Simple LED controller",
                "run_validation": True,
                "run_simulation": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "simulations" in data
        assert len(data["simulations"]) > 0
    
    def test_parse_prompt(self, client):
        """Test prompt parsing endpoint."""
        response = client.post(
            "/api/v1/parse",
            params={"prompt": "Arduino board with motor control"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "board_type" in data
        assert "features" in data


class TestVendorEndpoints:
    """Test suite for vendor-related endpoints."""
    
    def test_list_vendors(self, client):
        """Test listing vendors."""
        response = client.get("/api/v1/vendors")
        
        assert response.status_code == 200
        data = response.json()
        assert "vendors" in data
        assert len(data["vendors"]) > 0
    
    def test_filter_vendors_by_capability(self, client):
        """Test filtering vendors by capability."""
        response = client.get(
            "/api/v1/vendors",
            params={"capability": "pcb_prototype"}
        )
        
        assert response.status_code == 200
        data = response.json()
        for vendor in data["vendors"]:
            assert "pcb_prototype" in vendor["capabilities"]
    
    def test_get_specific_vendor(self, client):
        """Test getting a specific vendor."""
        # First get list of vendors
        list_response = client.get("/api/v1/vendors")
        vendors = list_response.json()["vendors"]
        vendor_id = vendors[0]["vendor_id"]
        
        response = client.get(f"/api/v1/vendors/{vendor_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["vendor_id"] == vendor_id
    
    def test_get_nonexistent_vendor(self, client):
        """Test getting a non-existent vendor returns 404."""
        response = client.get("/api/v1/vendors/nonexistent-id")
        
        assert response.status_code == 404


class TestQuoteEndpoints:
    """Test suite for quote-related endpoints."""
    
    def test_get_quotes(self, client):
        """Test getting quotes from multiple vendors."""
        response = client.post(
            "/api/v1/quote",
            json={
                "width_mm": 50,
                "height_mm": 30,
                "layers": 2,
                "quantity": 10,
                "surface_finish": "HASL"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "quotes" in data
        assert len(data["quotes"]) > 0
    
    def test_get_vendor_specific_quote(self, client):
        """Test getting a quote from a specific vendor."""
        # First get a vendor ID
        vendors_response = client.get("/api/v1/vendors")
        vendors = vendors_response.json()["vendors"]
        
        # Find a vendor with PCB capability
        vendor_id = None
        for v in vendors:
            if "pcb_prototype" in v["capabilities"]:
                vendor_id = v["vendor_id"]
                break
        
        if vendor_id:
            response = client.get(
                f"/api/v1/quote/{vendor_id}",
                params={
                    "width_mm": 50,
                    "height_mm": 30,
                    "layers": 2,
                    "quantity": 10
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "quote_id" in data
            assert "unit_price_usd" in data
