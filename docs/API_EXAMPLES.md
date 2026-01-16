# API Examples

## Table of Contents
- [Design API](#design-api)
- [Simulation API](#simulation-api)
- [Vendor API](#vendor-api)
- [Complete Workflow](#complete-workflow)

## Design API

### Create a New Design

**Endpoint:** `POST /api/design/`

**Request:**
```json
{
  "description": "ESP32-based temperature sensor with WiFi connectivity and DHT22 sensor",
  "design_type": "esp32",
  "constraints": {
    "max_power": "500mW",
    "operating_temp": "-20 to 60C",
    "size": "50x30mm"
  },
  "code_input": "// Optional technical specifications\nVCC: 3.3V\nSensor: DHT22"
}
```

**Response:**
```json
{
  "design_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Design created successfully and queued for processing",
  "created_at": "2024-01-16T10:30:00Z"
}
```

### Get Design Details

**Endpoint:** `GET /api/design/{design_id}`

**Response:**
```json
{
  "design_id": "550e8400-e29b-41d4-a716-446655440000",
  "description": "ESP32-based temperature sensor with WiFi connectivity and DHT22 sensor",
  "design_type": "esp32",
  "status": "completed",
  "schematic": {
    "components": [
      {
        "id": "U1",
        "type": "ESP32-WROOM-32",
        "value": "ESP32",
        "pins": ["3V3", "GND", "GPIO0", "GPIO2"]
      },
      {
        "id": "U2",
        "type": "DHT22",
        "value": "Temperature Sensor",
        "pins": ["VCC", "GND", "DATA"]
      }
    ],
    "connections": [
      {
        "from": {"component": "U1", "pin": "3V3"},
        "to": {"component": "U2", "pin": "VCC"}
      }
    ],
    "layout": "ESP32 development board with DHT22 sensor",
    "specifications": {
      "power_requirements": "5V USB or 3.3V regulated",
      "dimensions": "55mm x 28mm",
      "operating_conditions": "-20°C to 60°C"
    }
  },
  "created_at": "2024-01-16T10:30:00Z",
  "updated_at": "2024-01-16T10:30:15Z"
}
```

### List All Designs

**Endpoint:** `GET /api/design/`

**Response:**
```json
[
  {
    "design_id": "550e8400-e29b-41d4-a716-446655440000",
    "description": "ESP32-based temperature sensor",
    "design_type": "esp32",
    "status": "completed",
    "created_at": "2024-01-16T10:30:00Z",
    "updated_at": "2024-01-16T10:30:15Z"
  }
]
```

## Simulation API

### Run Simulation

**Endpoint:** `POST /api/simulation/run`

**Request:**
```json
{
  "design_id": "550e8400-e29b-41d4-a716-446655440000",
  "simulation_type": "full",
  "parameters": {
    "temperature": 25,
    "voltage": 3.3
  }
}
```

**Response:**
```json
{
  "simulation_id": "750e8400-e29b-41d4-a716-446655440000",
  "design_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "results": {
    "simulation_type": "full",
    "status": "passed",
    "metrics": {
      "power_consumption": "150mW (estimated)",
      "operating_voltage": "3.3V",
      "max_current": "45mA",
      "thermal_dissipation": "Low"
    },
    "performance": {
      "signal_integrity": "Good",
      "noise_margin": "High",
      "timing_analysis": "Passed"
    }
  },
  "conflicts": [],
  "warnings": [
    "Unconnected pin: U1.GPIO15",
    "No decoupling capacitors found - consider adding for power stability"
  ],
  "timestamp": "2024-01-16T10:30:20Z"
}
```

### Get Simulation Results

**Endpoint:** `GET /api/simulation/{simulation_id}`

**Response:** Same as "Run Simulation" response above.

## Vendor API

### Match Vendors

**Endpoint:** `POST /api/vendor/match`

**Request:**
```json
{
  "design_id": "550e8400-e29b-41d4-a716-446655440000",
  "quantity": 100,
  "requirements": {
    "capabilities": ["PCB", "SMT Assembly"],
    "location": "China",
    "min_rating": 4.5
  }
}
```

**Response:**
```json
{
  "design_id": "550e8400-e29b-41d4-a716-446655440000",
  "vendors": [
    {
      "vendor_id": "vendor_001",
      "name": "JLCPCB",
      "price_per_unit": 1.6,
      "lead_time_days": 8,
      "capabilities": ["PCB", "SMT Assembly", "2-layer", "4-layer", "6-layer"],
      "rating": 4.8
    },
    {
      "vendor_id": "vendor_002",
      "name": "PCBWay",
      "price_per_unit": 2.0,
      "lead_time_days": 10,
      "capabilities": ["PCB", "SMT Assembly", "2-layer", "4-layer", "Flexible PCB"],
      "rating": 4.7
    }
  ],
  "recommended_vendor": {
    "vendor_id": "vendor_001",
    "name": "JLCPCB",
    "price_per_unit": 1.6,
    "lead_time_days": 8,
    "capabilities": ["PCB", "SMT Assembly", "2-layer", "4-layer", "6-layer"],
    "rating": 4.8
  }
}
```

## Complete Workflow

### Python Example

```python
import requests
import time

BASE_URL = "http://localhost:8000"

# 1. Create a design
design_response = requests.post(f"{BASE_URL}/api/design/", json={
    "description": "ESP32 weather station with BME280 sensor",
    "design_type": "esp32",
    "constraints": {
        "max_power": "500mW",
        "operating_temp": "-20 to 60C"
    }
})

design_id = design_response.json()["design_id"]
print(f"Design created: {design_id}")

# 2. Wait for design to complete
while True:
    design = requests.get(f"{BASE_URL}/api/design/{design_id}").json()
    if design["status"] == "completed":
        print("Design completed!")
        break
    elif design["status"] == "failed":
        print("Design failed!")
        break
    time.sleep(2)

# 3. Run simulation
sim_response = requests.post(f"{BASE_URL}/api/simulation/run", json={
    "design_id": design_id,
    "simulation_type": "full"
})

simulation = sim_response.json()
print(f"Simulation completed: {simulation['status']}")
print(f"Conflicts: {len(simulation['conflicts'])}")
print(f"Warnings: {len(simulation['warnings'])}")

# 4. Match vendors
vendor_response = requests.post(f"{BASE_URL}/api/vendor/match", json={
    "design_id": design_id,
    "quantity": 100
})

vendors = vendor_response.json()
print(f"Found {len(vendors['vendors'])} vendors")
if vendors["recommended_vendor"]:
    rec = vendors["recommended_vendor"]
    print(f"Recommended: {rec['name']} - ${rec['price_per_unit']}/unit")
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

async function createAndProcessDesign() {
  // 1. Create design
  const designResponse = await axios.post(`${BASE_URL}/api/design/`, {
    description: 'ESP32 weather station with BME280 sensor',
    design_type: 'esp32',
    constraints: {
      max_power: '500mW',
      operating_temp: '-20 to 60C'
    }
  });

  const designId = designResponse.data.design_id;
  console.log(`Design created: ${designId}`);

  // 2. Wait for completion
  let design;
  while (true) {
    const response = await axios.get(`${BASE_URL}/api/design/${designId}`);
    design = response.data;
    
    if (design.status === 'completed') {
      console.log('Design completed!');
      break;
    } else if (design.status === 'failed') {
      console.log('Design failed!');
      return;
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  // 3. Run simulation
  const simResponse = await axios.post(`${BASE_URL}/api/simulation/run`, {
    design_id: designId,
    simulation_type: 'full'
  });

  console.log(`Simulation: ${simResponse.data.status}`);
  console.log(`Conflicts: ${simResponse.data.conflicts.length}`);

  // 4. Match vendors
  const vendorResponse = await axios.post(`${BASE_URL}/api/vendor/match`, {
    design_id: designId,
    quantity: 100
  });

  console.log(`Found ${vendorResponse.data.vendors.length} vendors`);
  if (vendorResponse.data.recommended_vendor) {
    const rec = vendorResponse.data.recommended_vendor;
    console.log(`Recommended: ${rec.name} - $${rec.price_per_unit}/unit`);
  }
}

createAndProcessDesign().catch(console.error);
```

### cURL Examples

```bash
# Create design
curl -X POST http://localhost:8000/api/design/ \
  -H "Content-Type: application/json" \
  -d '{
    "description": "ESP32 temperature sensor",
    "design_type": "esp32"
  }'

# Get design
curl http://localhost:8000/api/design/{design_id}

# Run simulation
curl -X POST http://localhost:8000/api/simulation/run \
  -H "Content-Type: application/json" \
  -d '{
    "design_id": "{design_id}",
    "simulation_type": "full"
  }'

# Match vendors
curl -X POST http://localhost:8000/api/vendor/match \
  -H "Content-Type: application/json" \
  -d '{
    "design_id": "{design_id}",
    "quantity": 100
  }'
```

## Design Types

Available design types:
- `pcb` - General purpose PCB
- `chip` - Integrated circuit
- `esp32` - ESP32-based IoT device
- `lora` - LoRa communication module
- `custom` - Custom hardware design

## Simulation Types

Available simulation types:
- `full` - Complete simulation with all checks
- `power` - Power consumption analysis
- `thermal` - Thermal analysis
- `signal` - Signal integrity check
