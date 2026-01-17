# Quantum AI PCB Builder

[![CI](https://github.com/NaTo1000/Quantum-Ai-PCB-Builder/actions/workflows/ci.yml/badge.svg)](https://github.com/NaTo1000/Quantum-Ai-PCB-Builder/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

> **Autonomous AI-powered PCB design platform with quantum-inspired optimization algorithms**

A fully autonomous AI builder for chips, PCBs, and electronic innovations. Design ESP32, LoRa, or any custom electronics with advanced algorithmic optimization, then list your products on the integrated marketplace for bidding from manufacturing companies.

## 🚀 Features

### Core Capabilities

- **🔬 Quantum-Inspired Optimization**: Simulated Quantum Annealing (SQA) and Quantum Evolutionary Algorithms for superior component placement
- **🧬 Genetic Algorithms**: Multi-objective optimization with NSGA-II for Pareto-optimal designs
- **🛣️ Advanced Routing**: A*, Lee's algorithm, and maze routing with via minimization
- **🤖 AI-Powered Analysis**: Intelligent circuit analysis, signal integrity checks, and design rule validation

### Design & Manufacturing

- **📐 Component Library**: Pre-defined templates for ESP32, LoRa modules, and common electronics
- **📊 Cost Estimation**: Real-time manufacturing cost calculation with quantity discounts
- **📁 Export Formats**: Gerber RS-274X, Excellon drill files, BOM (CSV/JSON), Pick & Place files
- **🔍 Design Rule Checking**: Automated DRC with configurable rules

### Marketplace Integration

- **🏪 Product Listings**: Create and publish PCB designs with licensing options
- **💰 Bidding System**: Auction-style bidding from manufacturing companies
- **📜 Licensing**: Support for proprietary, open-source, and commercial licenses

## 📦 Installation

### Using pip

```bash
pip install quantum-pcb-builder
```

### From source

```bash
git clone https://github.com/NaTo1000/Quantum-Ai-PCB-Builder.git
cd Quantum-Ai-PCB-Builder
pip install -e ".[dev]"
```

### Using Docker

```bash
# Build the image
docker build -t quantum-pcb-builder .

# Run a demo
docker run --rm quantum-pcb-builder demo --type esp32

# Run with mounted volumes
docker run --rm -v $(pwd)/designs:/app/designs -v $(pwd)/output:/app/output \
    quantum-pcb-builder optimize /app/designs/my_design.json -o /app/output/optimized.json
```

## 🎯 Quick Start

### Initialize a Project

```bash
quantum-pcb init my_project --width 100 --height 80 --layers 2
```

### Run a Demo

```bash
# ESP32 IoT demo
quantum-pcb demo --type esp32

# LoRa sensor node demo
quantum-pcb demo --type lora

# Simple LED circuit demo
quantum-pcb demo --type simple
```

### Optimize a Design

```bash
# Using quantum-inspired optimization
quantum-pcb optimize design.json --algorithm quantum --iterations 1000

# Using genetic algorithm
quantum-pcb optimize design.json --algorithm genetic --iterations 500
```

### Analyze Design Quality

```bash
quantum-pcb analyze design.json --strict --output analysis_report.json
```

### Export for Manufacturing

```bash
quantum-pcb export design.json --format all --output ./manufacturing
```

### Get Cost Quote

```bash
quantum-pcb quote design.json --quantity 100
```

## 🏗️ Architecture

```
quantum_pcb_builder/
├── core/                    # Core data structures
│   ├── component.py         # Component definitions
│   ├── circuit.py           # Circuit with graph connectivity
│   └── pcb.py               # PCB board representation
├── algorithms/              # Optimization algorithms
│   ├── quantum_optimizer.py # SQA, QIEA implementations
│   ├── genetic_algorithm.py # GA, NSGA-II implementations
│   └── routing.py           # A*, Lee, maze routing
├── ai/                      # AI-powered features
│   ├── component_selector.py # Intelligent component selection
│   └── circuit_analyzer.py   # Design analysis engine
├── manufacturing/           # Manufacturing integration
│   ├── exporter.py          # Gerber, BOM exporters
│   └── cost_estimator.py    # Cost estimation engine
├── marketplace/             # Marketplace system
│   ├── bidding.py           # Auction and bidding
│   └── product.py           # Product catalog
├── utils/                   # Utilities
│   ├── config.py            # Configuration management
│   └── validation.py        # Design validation
└── cli.py                   # Command-line interface
```

## 🔬 Algorithms

### Quantum-Inspired Optimization

The **Simulated Quantum Annealing (SQA)** algorithm uses concepts from quantum mechanics:

- **Transverse field** enables quantum tunneling through energy barriers
- **Trotter slices** represent parallel solution explorations
- **Temperature annealing** controls solution convergence

```python
from quantum_pcb_builder.algorithms import SimulatedQuantumAnnealing
from quantum_pcb_builder.core import Circuit, Component, ComponentType

# Create circuit
circuit = Circuit(name="My Design")
circuit.add_component(Component(name="U1", component_type=ComponentType.MICROCONTROLLER))
circuit.add_component(Component(name="R1", component_type=ComponentType.RESISTOR))

# Optimize placement
optimizer = SimulatedQuantumAnnealing(max_iterations=1000, random_seed=42)
result = optimizer.optimize(circuit, board_width=100.0, board_height=80.0)

print(f"Best cost: {result.best_cost}")
print(f"Optimized positions: {result.best_solution}")
```

### Genetic Algorithm (NSGA-II)

Multi-objective optimization balancing:
- Wire length minimization
- Component overlap avoidance
- Signal integrity requirements

```python
from quantum_pcb_builder.algorithms import GeneticAlgorithm, NSGA2

# Single-objective optimization
ga = GeneticAlgorithm(population_size=100, max_generations=200)
result = ga.optimize(circuit, 100.0, 80.0)

# Multi-objective Pareto optimization
nsga2 = NSGA2(population_size=50, max_generations=100)
pareto_result = nsga2.optimize(circuit, 100.0, 80.0)
```

### Routing Algorithms

```python
from quantum_pcb_builder.algorithms import AStarRouter, LeeRouter, RoutingGrid

# Create routing grid from board
grid = RoutingGrid.from_pcb_board(board, resolution_mm=0.25)

# A* routing (fast, heuristic-guided)
router = AStarRouter(via_cost=10.0, turn_cost=1.0)
path = router.route(grid, start=(10, 10, 0), end=(90, 50, 0))

# Lee's algorithm (guaranteed shortest path)
lee_router = LeeRouter()
path = lee_router.route(grid, start, end)
```

## 🏭 Manufacturing Export

```python
from quantum_pcb_builder.manufacturing import GerberExporter, CostEstimator, ManufacturingSpecs

# Export Gerber files
exporter = GerberExporter()
result = exporter.export(board)
for filename, content in result.files.items():
    with open(f"output/{filename}", "w") as f:
        f.write(content)

# Get manufacturing quote
estimator = CostEstimator()
specs = ManufacturingSpecs(quantity=100, finish=FinishType.ENIG)
quote = estimator.estimate(board, specs)
print(f"Unit price: ${quote.unit_price:.2f}")
print(f"Total: ${quote.total_price:.2f}")
```

## 🏪 Marketplace Integration

```python
from quantum_pcb_builder.marketplace import BiddingSystem, ProductCatalog, Product, ProductCategory

# Create product catalog
catalog = ProductCatalog()
product = Product(
    name="ESP32 IoT Sensor Board",
    description="Complete temperature/humidity sensor with WiFi",
    category=ProductCategory.IOT_DEVICE,
    seller_id="seller-123",
)
catalog.add_product(product)

# Create auction
bidding = BiddingSystem()
auction = bidding.create_auction(
    product_id=product.uuid,
    seller_id="seller-123",
    title="ESP32 IoT Sensor Board",
    description="Manufacturing rights for sensor board",
    starting_price=500.0,
    duration_days=7,
)
bidding.start_auction(auction.uuid)

# Place bids
success, msg = bidding.place_bid(auction.uuid, "manufacturer-1", 750.0)
```

## 🐳 Docker Usage

### Docker Compose

```bash
# Run demo
docker-compose up quantum-pcb

# Run tests
docker-compose --profile test up test

# Development mode
docker-compose --profile dev up quantum-pcb-dev
```

### Production Deployment

```bash
# Build production image
docker build -t quantum-pcb-builder:latest .

# Run with persistent output
docker run -d --name quantum-pcb \
    -v /data/designs:/app/designs:ro \
    -v /data/output:/app/output \
    quantum-pcb-builder:latest optimize /app/designs/board.json
```

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src/quantum_pcb_builder --cov-report=html

# Run specific test module
pytest tests/test_algorithms.py -v
```

### Linting & Type Checking

```bash
# Lint with Ruff
ruff check src/ tests/

# Format code
ruff format src/ tests/

# Type checking
mypy src/quantum_pcb_builder
```

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🌟 Roadmap

- [ ] Web-based design interface
- [ ] Real-time collaborative editing
- [ ] Integration with popular EDA tools (KiCad, Eagle)
- [ ] Machine learning-based component recommendation
- [ ] Automated schematic generation from descriptions
- [ ] 3D visualization of PCB designs
- [ ] Integration with component distributors (DigiKey, Mouser)
