# Quantum-Ai-PCB-Builder

An AI-guided chip and PCB design lab that lets users describe their desired hardware in natural language or code, then generates schematics, runs simulations, checks for design conflicts, and matches vendors for manufacturing. Built with FastAPI, React, Docker, and RabbitMQ, it orchestrates the full design-to-fabrication pipeline with LLM and EDA integration.

## Features

- **Natural Language Design**: Describe your hardware in plain English or code
- **Schematic Generation**: AI-powered schematic generation from descriptions
- **EDA Integration**: Run Design Rule Checks (DRC) and Electrical Rule Checks (ERC)
- **Simulation**: Validate designs with integrated simulation tools
- **Vendor Matching**: Find manufacturing partners based on design specifications
- **Full Pipeline**: From concept to fabrication-ready files

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│     Backend     │────▶│    RabbitMQ     │
│   (React App)   │     │   (FastAPI)     │     │   (Message Q)   │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │     Worker      │
                                                │  (Simulation)   │
                                                └─────────────────┘
```

## Project Structure

```
├── backend/                  # FastAPI backend service
│   ├── app/
│   │   ├── api/             # API routes
│   │   ├── services/        # Business logic services
│   │   │   ├── llm_adapter.py      # LLM integration
│   │   │   ├── queue.py            # RabbitMQ service
│   │   │   ├── eda_runner.py       # EDA tool integration
│   │   │   └── vendor_matcher.py   # Vendor matching
│   │   ├── main.py          # FastAPI application
│   │   ├── models.py        # Pydantic models
│   │   └── config.py        # Configuration settings
│   ├── Dockerfile
│   └── requirements.txt
├── worker/                   # Simulation worker service
│   ├── simulator/
│   │   └── run_sim.py       # Simulation runner
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── App.js           # Main React component
│   │   └── index.js         # Entry point
│   ├── public/
│   │   └── index.html       # HTML template
│   ├── Dockerfile
│   └── package.json
├── infra/                    # Infrastructure configuration
│   └── docker-compose.yml   # Docker Compose setup
├── scripts/                  # Utility scripts
│   └── build_images.sh      # Docker image build script
└── README.md
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Running with Docker Compose

1. Clone the repository:
   ```bash
   git clone https://github.com/NaTo1000/Quantum-Ai-PCB-Builder.git
   cd Quantum-Ai-PCB-Builder
   ```

2. Copy environment files:
   ```bash
   cp backend/.env.example backend/.env
   cp worker/.env.example worker/.env
   ```

3. Build and start all services:
   ```bash
   cd infra
   docker-compose up -d
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - RabbitMQ Management: http://localhost:15672

### Local Development

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

#### Worker
```bash
cd worker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python simulator/run_sim.py
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API status check |
| `/health` | GET | Health check endpoint |

## Configuration

Configuration is managed through environment variables. See the `.env.example` files in each service directory for available options.

### Backend Configuration
- `API_HOST`: API host address (default: 0.0.0.0)
- `API_PORT`: API port (default: 8000)
- `RABBITMQ_HOST`: RabbitMQ host
- `LLM_API_KEY`: API key for LLM service
- `LLM_MODEL`: LLM model to use (default: gpt-4)

### Worker Configuration
- `RABBITMQ_HOST`: RabbitMQ host
- `SIMULATION_QUEUE`: Queue name for simulation jobs

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
