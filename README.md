# Quantum AI PCB Builder

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

**AI-Orchestrated Chip and PCB Design Lab — from Natural Language to Fabrication**

Quantum-Ai-PCB-Builder is a full-stack, AI-guided hardware design platform that empowers engineers, researchers, and innovators to design custom chips and PCBs using natural language or structured prompts. It transforms high-level intent into manufacturable schematics, simulates performance, checks for design conflicts, and connects users with real-world fabrication vendors — all within a modular, containerized environment.

## 🚀 Features

### Natural Language Design
- **Intent Parsing**: Describe your design in plain English - "ESP32 board with WiFi, temperature sensor, and battery power"
- **Component Extraction**: Automatically identifies required components, connectivity, and features
- **Board Type Recognition**: Supports ESP32, LoRa, Arduino, Raspberry Pi, and custom designs

### Schematic Generation
- **Automatic Component Selection**: Generates appropriate components based on your requirements
- **Smart Net Generation**: Creates power, ground, and signal nets automatically
- **Reference Designator Management**: Unique, standardized component references

### Design Validation
- **Electrical Rule Checks (ERC)**: Detects floating pins, power shorts, and missing connections
- **Design Rule Checks (DRC)**: Validates clearances, trace widths, and component placement
- **Component Validation**: Ensures all components have proper values and footprints

### Performance Simulation
- **Power Analysis**: Estimate power consumption and efficiency
- **Signal Integrity**: Analyze rise/fall times, impedance, and crosstalk
- **Thermal Analysis**: Identify hot spots and thermal gradients
- **Timing Analysis**: Clock frequency and timing constraints
- **EMC Analysis**: Electromagnetic compatibility risk assessment

### Fabrication Integration
- **Vendor Registry**: Access multiple PCB fabrication vendors
- **Quote Comparison**: Get and compare quotes from multiple sources
- **Order Management**: Track orders from placement to delivery

## 📦 Installation

### Prerequisites
- Python 3.12 or higher
- Docker (optional, for containerized deployment)

### Local Installation

```bash
# Clone the repository
git clone https://github.com/NaTo1000/Quantum-Ai-PCB-Builder.git
cd Quantum-Ai-PCB-Builder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Docker Installation

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t quantum-pcb-builder .
docker run -p 8000:8000 quantum-pcb-builder
```

## 🎯 Quick Start

### Start the API Server

```bash
# Development mode with hot reload
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### API Usage Examples

#### Generate a Design from Natural Language

```bash
curl -X POST "http://localhost:8000/api/v1/design" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "ESP32 board with WiFi, temperature sensor, and USB connectivity",
    "run_validation": true,
    "run_simulation": true
  }'
```

#### Get Fabrication Quotes

```bash
curl -X POST "http://localhost:8000/api/v1/quote" \
  -H "Content-Type: application/json" \
  -d '{
    "width_mm": 50,
    "height_mm": 30,
    "layers": 2,
    "quantity": 10
  }'
```

#### List Available Vendors

```bash
curl "http://localhost:8000/api/v1/vendors?capability=pcb_prototype"
```

### Python SDK Usage

```python
from src.core.nlp.intent_parser import IntentParser
from src.core.design.schematic_generator import SchematicGenerator
from src.core.design.validator import DesignValidator
from src.core.simulation.engine import SimulationEngine, SimulationType

# Parse natural language design intent
parser = IntentParser()
intent = parser.parse("ESP32 IoT sensor with WiFi and battery power")

# Generate schematic
generator = SchematicGenerator()
schematic = generator.generate(intent)

# Validate design
validator = DesignValidator()
validation = validator.validate(schematic)

print(f"Design valid: {validation.is_valid}")
print(f"Warnings: {validation.summary['warnings']}")

# Run simulations
engine = SimulationEngine()
power_result = engine.run_simulation(schematic, SimulationType.POWER_ANALYSIS)

print(f"Power consumption: {power_result.results['total_power_consumption_mw']} mW")
```

## 📁 Project Structure

```
Quantum-Ai-PCB-Builder/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py              # FastAPI application
│   ├── core/
│   │   ├── nlp/
│   │   │   ├── __init__.py
│   │   │   └── intent_parser.py # Natural language parsing
│   │   ├── design/
│   │   │   ├── __init__.py
│   │   │   ├── schematic_generator.py  # Schematic generation
│   │   │   └── validator.py     # Design validation
│   │   ├── simulation/
│   │   │   ├── __init__.py
│   │   │   └── engine.py        # Simulation engine
│   │   └── fabrication/
│   │       ├── __init__.py
│   │       └── vendor.py        # Vendor integration
│   └── utils/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── test_intent_parser.py
│   ├── test_schematic_generator.py
│   ├── test_validator.py
│   ├── test_simulation.py
│   ├── test_fabrication.py
│   └── test_api.py
├── docker/
├── frontend/
│   └── static/
├── docs/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## 🧪 Testing

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test file
pytest tests/test_intent_parser.py -v
```

## 🔌 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| POST | `/api/v1/design` | Generate design from natural language |
| POST | `/api/v1/parse` | Parse prompt without full generation |
| POST | `/api/v1/validate` | Validate existing schematic |
| POST | `/api/v1/simulate` | Run simulations on schematic |
| GET | `/api/v1/vendors` | List fabrication vendors |
| GET | `/api/v1/vendors/{id}` | Get vendor details |
| POST | `/api/v1/quote` | Get quotes from multiple vendors |
| GET | `/api/v1/quote/{vendor_id}` | Get quote from specific vendor |

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment mode | `development` |
| `LOG_LEVEL` | Logging level | `info` |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🔮 Roadmap

- [ ] Quantum-enhanced optimization algorithms
- [ ] KiCad/Altium export support
- [ ] Real-time collaboration features
- [ ] AI-powered component recommendation
- [ ] 3D PCB visualization
- [ ] Integration with commercial EDA tools
- [ ] Machine learning for design optimization

## 📞 Support

For questions and support, please open an issue on GitHub or contact the maintainers.

---

**Built for rapid prototyping, educational use, and future integration with quantum-enhanced orchestration engines and commercial EDA workflows.**
