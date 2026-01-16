# Quantum AI PCB Builder

A fully autonomous AI-powered platform for designing chips, PCBs, and innovative electronics. Describe your desired chip or board in natural language — the system generates architecture, RTL, or analog schematics in real time. Connect with foundries and assemblers to bring your innovations to market.

## 🔧 Key Features

### Prompt-to-Schematic AI Engine
Describe your desired chip or board in natural language or code — the system generates architecture, RTL, or analog schematics in real time.

### Automated Design Checks
Built-in rule engines for:
- **DRC (Design Rule Check)** - Validate component spacing and design rules
- **LVS (Layout vs Schematic)** - Ensure layout matches schematic
- **Thermal Analysis** - Identify components requiring thermal relief
- **Signal Integrity** - Check RF impedance matching and high-speed signals

### Simulation Pipeline
Run simulations with confidence scoring and visual feedback:
- **SPICE Simulation** - Transient and DC analysis with waveform visualization
- **Timing Analysis** - Setup/hold times, propagation delays, and critical paths
- **Power Analysis** - Power consumption, current draw, and thermal dissipation

### Component-Level Drawing Generator
Auto-generates each block to spec:
- SVG previews for all components
- BOM (Bill of Materials) integration with pricing
- Component library with datasheet links

### Vendor Matching & Quoting
Suggests compatible vendors with estimated pricing:
- **Foundries** - TSMC, GlobalFoundries
- **PCB Assemblers** - JLCPCB, PCBWay, OSH Park
- **Packaging Houses** - Amkor, ASE Group
- Price-per-unit and delivery timeline estimates

### Modular Architecture
- **Backend**: FastAPI (Python) with async endpoints
- **Frontend**: React with TypeScript
- **Message Queue**: RabbitMQ for job processing
- **Containerization**: Docker Compose for easy deployment

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)

### Run with Docker Compose

```bash
# Clone the repository
git clone https://github.com/NaTo1000/Quantum-Ai-PCB-Builder.git
cd Quantum-Ai-PCB-Builder

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# RabbitMQ Management: http://localhost:15672
```

### Local Development

#### Backend (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --port 8000
```

#### Frontend (React)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### Run Tests

```bash
cd backend

# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/ -v
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/schematic/generate` | POST | Generate schematic from natural language prompt |
| `/api/checks/run` | POST | Run DRC, LVS, thermal, and signal integrity checks |
| `/api/simulation/run` | POST | Run SPICE, timing, or power simulation |
| `/api/components/bom/{id}` | POST | Generate Bill of Materials |
| `/api/components/drawing` | POST | Generate component SVG drawing |
| `/api/vendors/match` | POST | Find matching vendors with quotes |

### Example: Generate a Schematic

```bash
curl -X POST http://localhost:8000/api/schematic/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create an ESP32-based IoT board with LoRa module, temperature sensor, and USB-C power",
    "design_type": "pcb",
    "output_format": "rtl"
  }'
```

## 🏗️ Project Structure

```
Quantum-Ai-PCB-Builder/
├── backend/
│   ├── app/
│   │   ├── api/routes/        # API endpoint handlers
│   │   ├── core/              # Configuration
│   │   ├── models/            # Data models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   └── main.py            # FastAPI application
│   ├── tests/                 # Backend tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API client
│   │   ├── pages/             # Page components
│   │   ├── App.tsx            # Main application
│   │   └── index.tsx          # Entry point
│   ├── public/
│   ├── Dockerfile
│   └── package.json
├── docker/                    # Docker configurations
├── docker-compose.yml         # Multi-service orchestration
└── README.md
```

## 🔌 Supported Components

The AI engine recognizes and generates schematics for:
- **Microcontrollers**: ESP32, general MCUs
- **RF Modules**: LoRa, antenna systems
- **Sensors**: Temperature, humidity, motion
- **Power**: Voltage regulators, power supplies
- **Passive**: Capacitors, resistors
- **Indicators**: LEDs
- **Connectors**: USB-C, general purpose
- **Oscillators**: Crystals

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with FastAPI, React, and RabbitMQ
- Component symbols inspired by industry standards
- Vendor data for illustration purposes only
