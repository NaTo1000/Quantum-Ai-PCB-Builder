# Quantum-Ai-PCB-Builder

[![CI](https://github.com/NaTo1000/Quantum-Ai-PCB-Builder/actions/workflows/ci.yml/badge.svg)](https://github.com/NaTo1000/Quantum-Ai-PCB-Builder/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A fully autonomous AI-powered PCB builder for chips, PCBs, and IoT innovation. Design with ESP32, LoRa, or any hardware you can imagine, then list your designs on the integrated marketplace for bidding from manufacturers or use in-house production facilities.

## Features

- **AI-Powered Design Generation**: Automatically generate PCB layouts based on requirements
- **Component Library**: Pre-built library of common components (ESP32, LoRa modules, sensors, etc.)
- **Layout Optimization**: AI-driven optimization for trace length, spacing, and thermal distribution
- **Design Validation**: Comprehensive validation with compatibility checking
- **Marketplace Integration**: List designs for bidding and sales
- **Production Management**: Track orders through in-house or partner manufacturing
- **Workflow Orchestration**: End-to-end pipeline from ideation to production

## Installation

```bash
# Clone the repository
git clone https://github.com/NaTo1000/Quantum-Ai-PCB-Builder.git
cd Quantum-Ai-PCB-Builder

# Install the package
pip install -e ".[dev]"
```

## Quick Start

```python
from quantum_pcb_builder.ai.designer import AIDesigner, DesignRequirements, ApplicationDomain, CommunicationType
from quantum_pcb_builder.workflow.pipeline import DesignPipeline

# Define your requirements
requirements = DesignRequirements(
    name="IoT Weather Station",
    description="Remote weather monitoring with long-range communication",
    domain=ApplicationDomain.IOT,
    communication_types=[CommunicationType.LORA, CommunicationType.WIFI],
    sensor_types=["temperature", "humidity"],
    power_source="battery",
)

# Run the full design pipeline
pipeline = DesignPipeline()
context = pipeline.run_full_design_pipeline(requirements)

# Access the generated design
design = context.design
print(f"Generated design with {len(design.components)} components")

# List on marketplace
result = pipeline.run_listing(context, seller_id="your_id", min_price=100.0)
print(f"Listed with ID: {result['listing_id']}")
```

## Architecture

```
quantum_pcb_builder/
├── core/           # Base classes, protocols, and event system
├── pcb/            # PCB components, layout, and validation
├── ai/             # AI designer and layout optimizer
├── marketplace/    # Listings, bidding, and sales
└── workflow/       # Orchestration and pipeline management
```

### Core Module

- **Protocols**: Type-safe interfaces for components, designs, marketplace, and workflows
- **Base Classes**: `BaseComponent`, `BaseDesign`, `ValidationResult`
- **Event System**: Decoupled communication via `EventBus`

### PCB Module

- **Components**: Microcontrollers, sensors, communication modules, power modules
- **Layout**: Position tracking, connections, multi-layer PCB support
- **Validators**: Design validation and component compatibility checking

### AI Module

- **Designer**: Generate designs from requirements, get suggestions, brainstorm ideas
- **Optimizer**: Optimize layouts for trace length, spacing, thermal distribution

### Marketplace Module

- **Listings**: Create, manage, and search design listings
- **Bidding**: Place and manage bids on listings
- **Sales**: Complete sales and manage production orders

### Workflow Module

- **Orchestrator**: Manage complex multi-step workflows
- **Pipeline**: End-to-end design-to-production pipeline

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run linting
ruff check src/ tests/

# Run type checking
mypy src/

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=src/quantum_pcb_builder
```

## Docker

Build and run with Docker:

```bash
# Build production image
docker build -t quantum-pcb-builder:latest --target production .

# Build development image
docker build -t quantum-pcb-builder:dev --target development .

# Run production container
docker run --rm quantum-pcb-builder:latest

# Run tests in container
docker run --rm quantum-pcb-builder:dev pytest tests/ -v

# Using docker-compose
docker-compose up quantum-pcb-builder    # Production
docker-compose up dev                     # Development with tests
docker-compose up test                    # Run tests with coverage
docker-compose up lint                    # Run linting
```

### Docker Images

| Target | Description | Use Case |
|--------|-------------|----------|
| `production` | Minimal image with installed package | Deployment |
| `development` | Full image with dev dependencies | Testing & Development |

## CI/CD

This project uses GitHub Actions for continuous integration:

- **Lint**: Ruff linting and formatting checks, mypy type checking
- **Test**: pytest across Python 3.9, 3.10, 3.11, and 3.12
- **Build**: Package building and artifact upload

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details
