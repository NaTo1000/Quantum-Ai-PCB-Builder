# 🧠 Quantum-Ai-PCB-Builder

**AI-Orchestrated Hardware Design Platform for Chip and PCB Schematic Generation, Simulation, and Vendor Integration**

Quantum-Ai-PCB-Builder is a modular, containerized, full-stack platform for AI-guided hardware design. It enables users to describe desired chip or PCB functionality in natural language or structured prompts, and orchestrates a multi-stage pipeline that synthesizes architecture, generates schematics, performs rule-based design validation, simulates performance, and surfaces vendor options for fabrication and packaging.

The platform is designed for extensibility, with pluggable adapters for LLMs, EDA tools, and foundry/vendor APIs. It is optimized for local or cloud deployment via Docker Compose or Kubernetes, and supports real-time job orchestration via RabbitMQ and background workers.

---

## 🧱 System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              User Interface                                   │
│                        (Web UI / API / CLI)                                   │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              API Gateway                                      │
│                        (src/api/)                                             │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌──────────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│   LLM Synthesis      │  │   Job Queue      │  │   Background         │
│   (src/ai/)          │  │   (RabbitMQ)     │  │   Workers            │
│                      │  │                  │  │   (src/workers/)     │
└──────────────────────┘  └──────────────────┘  └──────────────────────┘
          │                                               │
          ▼                                               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           Design Pipeline                                     │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌─────────────┐ │
│  │  Validation    │  │  Simulation    │  │  Vendor        │  │  Export     │ │
│  │  (src/        │  │  (src/         │  │  Matching      │  │  Handler    │ │
│  │  validation/) │  │  simulation/)  │  │  (src/vendor/) │  │             │ │
│  └────────────────┘  └────────────────┘  └────────────────┘  └─────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              Output Artifacts                                 │
│         (Schematic SVG/JSON, Netlist, BOM, Simulation Report, Vendor Quotes) │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Design Flow (Pipeline)

### 1. Prompt Ingestion
User submits a design intent (e.g., "low-power RISC-V core with HBM and 3D packaging") via UI or API.

### 2. LLM-Driven Synthesis
The `src/ai/` module generates:
- High-level architecture description
- RTL or analog schematic stub
- Component breakdown and constraints

### 3. Design Rule Checks
The `src/validation/` module performs:
- **DRC** (Design Rule Check)
- **LVS** (Layout vs Schematic)
- **IR drop / EM analysis** (stubbed or real)

### 4. Simulation
SPICE or timing simulation is run on the generated netlist or behavioral model. Results are scored against user-defined thresholds (e.g., ≥85% confidence).

### 5. Vendor Matching
The `src/vendor/` module surfaces compatible foundries, packaging houses, and PCB assemblers based on:
- Process node
- Packaging type (2.5D, 3D, CoWoS)
- Estimated unit cost and lead time

### 6. Export & Handoff
Final output includes:
- Schematic (SVG or JSON)
- Netlist
- BOM (Bill of Materials)
- Simulation report
- Vendor quote bundle

---

## 📁 Project Structure

```
Quantum-Ai-PCB-Builder/
├── src/
│   ├── ai/                    # LLM synthesis module
│   │   ├── __init__.py
│   │   ├── llm_adapter.py     # Pluggable LLM interface
│   │   └── synthesis.py       # Design synthesis logic
│   ├── validation/            # Design rule checks
│   │   ├── __init__.py
│   │   ├── drc.py             # Design Rule Check
│   │   ├── lvs.py             # Layout vs Schematic
│   │   └── analysis.py        # IR drop / EM analysis
│   ├── simulation/            # SPICE/timing simulation
│   │   ├── __init__.py
│   │   └── simulator.py       # Simulation engine interface
│   ├── vendor/                # Vendor matching
│   │   ├── __init__.py
│   │   └── matcher.py         # Vendor matching logic
│   ├── api/                   # API layer
│   │   ├── __init__.py
│   │   └── routes.py          # API endpoints
│   └── workers/               # Background job workers
│       ├── __init__.py
│       └── job_worker.py      # RabbitMQ job processor
├── config/                    # Configuration files
│   └── settings.py            # Application settings
├── docs/                      # Additional documentation
│   └── ARCHITECTURE.md        # Detailed architecture docs
├── docker-compose.yml         # Container orchestration
├── Dockerfile                 # Container build configuration
├── requirements.txt           # Python dependencies
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🧩 Extensibility

### LLM Integration
Swap in OpenAI, Claude, or local LLMs via `src/ai/llm_adapter.py`

### EDA Backends
Plug in open-source tools (ngspice, Magic, KLayout) or commercial APIs (Cadence Cloud, Synopsys Fusion)

### PDK Binding
Future support for PDK-aware layout and DRC via NDA-bound adapters

### Quantum Orchestration
Designed for future integration with quantum-enhanced design agents or solvers

### Multi-tenant SaaS
Add auth, billing, and usage metering for hosted deployments

---

## 🧪 Simulation & Metrics

| Metric                | Status          | Tool / Backend           |
|-----------------------|-----------------|--------------------------|
| SPICE Simulation      | Stubbed         | ngspice / Xyce           |
| Timing Analysis       | Stubbed         | OpenSTA / PrimeTime      |
| Power Estimation      | Stubbed         | Custom / Joules          |
| DRC Validation        | Stubbed         | Magic / Calibre          |
| LVS Validation        | Stubbed         | netgen / Calibre         |
| Confidence Scoring    | Implemented     | Internal ML model        |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- (Optional) RabbitMQ for job queue

### Local Development

```bash
# Clone the repository
git clone https://github.com/NaTo1000/Quantum-Ai-PCB-Builder.git
cd Quantum-Ai-PCB-Builder

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m src.api.routes
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build
```

---

## 🔐 Security & Compliance

- `.env` files excluded via `.gitignore`
- Secrets managed via environment injection or vault integration
- PDK and vendor data access gated behind NDA-aware modules
- Apache 2.0 license ensures patent protection and commercial use

---

## 🧭 Roadmap

- [ ] WebSocket job status updates
- [ ] Real-time schematic canvas with SVG overlays
- [ ] Vendor RFQ API integration (TSMC, Micron, Samsung)
- [ ] Multi-user auth and project persistence
- [ ] Quantum-enhanced constraint solver (NiA_PM25 integration)
- [ ] Open-source EDA backend (Magic + ngspice)

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests for any enhancements.

---

## 📞 Contact

For questions, issues, or collaboration opportunities, please open an issue on this repository.
