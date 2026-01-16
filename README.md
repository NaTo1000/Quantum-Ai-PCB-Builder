# Quantum AI PCB Builder

<div align="center">

![Quantum AI PCB Builder](https://img.shields.io/badge/AI-PCB%20Builder-6366f1?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)

**AI-guided chip and PCB design lab with full design-to-fabrication pipeline**

</div>

## 🚀 Overview

Quantum AI PCB Builder is an intelligent hardware design platform that revolutionizes the PCB and chip design process. Simply describe your desired hardware in natural language or code, and let our AI-powered system:

- 🎨 **Generate Schematics** - Automatically create detailed PCB/chip schematics
- 🔬 **Run Simulations** - Validate designs with comprehensive EDA simulations
- ⚠️ **Check Conflicts** - Detect design issues before fabrication
- 🏭 **Match Vendors** - Connect with manufacturing partners and get quotes
- 📊 **Manage Projects** - Track designs from concept to production

Perfect for:
- **ESP32** IoT devices
- **LoRa** communication modules
- **Custom PCBs** for any application
- **Chip design** prototypes
- **Innovation projects** with automatic vendor bidding

## 🏗️ Architecture

```
┌─────────────────┐
│   React UI      │  ← User describes hardware in natural language
└────────┬────────┘
         │
    ┌────▼────┐
    │ FastAPI │  ← REST API & Business Logic
    └────┬────┘
         │
    ┌────▼────────────┐
    │   RabbitMQ      │  ← Message Queue for async tasks
    └────┬────────────┘
         │
    ┌────▼────┐
    │ Worker  │  ← Process design generation & simulation
    └─────────┘
         │
    ┌────▼────────┐
    │  Services   │
    ├─────────────┤
    │ • LLM       │  ← AI-powered schematic generation
    │ • Simulation│  ← Conflict checking & validation
    │ • Vendor    │  ← Manufacturing partner matching
    └─────────────┘
```

## ✨ Features

### 🤖 AI-Powered Design Generation
- Natural language processing for hardware descriptions
- Code-based specification support
- Multiple design types (PCB, Chip, ESP32, LoRa, Custom)
- Automatic component selection and placement

### 🔍 Design Validation
- Real-time conflict detection
- Design rule checking (DRC)
- Power analysis and simulation
- Signal integrity validation
- Thermal analysis

### 🏪 Vendor Marketplace
- Automated vendor matching
- Competitive pricing from multiple manufacturers
- Lead time comparison
- Quality ratings and reviews
- Direct order placement

### 📱 Modern Web Interface
- Clean, intuitive design
- Real-time progress tracking
- Interactive schematic visualization
- Responsive mobile support

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: React 18 with modern hooks
- **Message Queue**: RabbitMQ
- **AI/LLM**: OpenAI GPT-4 integration
- **Containerization**: Docker & Docker Compose
- **API Communication**: REST with axios

## 📦 Installation

### Prerequisites

- Docker and Docker Compose
- (Optional) OpenAI API key for enhanced AI features

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/NaTo1000/Quantum-Ai-PCB-Builder.git
cd Quantum-Ai-PCB-Builder
```

2. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key (optional)
```

3. **Start the application**
```bash
docker-compose up --build
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- RabbitMQ Management: http://localhost:15672 (user: pcbuser, pass: pcbpass)

## 🎯 Usage

### Creating a Design

1. **Navigate to the web interface** at http://localhost:3000

2. **Select your design type**:
   - PCB - General purpose printed circuit board
   - Chip - Integrated circuit design
   - ESP32 - ESP32-based IoT device
   - LoRa - LoRa communication module
   - Custom - Any custom hardware

3. **Describe your design** in natural language:
   ```
   Example: "Create an ESP32-based temperature sensor with WiFi 
   connectivity, DHT22 sensor, and battery power management with 
   solar charging capability"
   ```

4. **Add code specifications** (optional):
   ```
   Operating voltage: 3.3V
   Battery: LiPo 3.7V 2000mAh
   Solar panel: 6V 100mA
   ```

5. **Generate and review**:
   - View generated schematic
   - Check simulation results
   - Review conflict warnings
   - Get vendor quotes

### API Usage

The system provides a RESTful API for programmatic access:

```python
import requests

# Create a design
response = requests.post('http://localhost:8000/api/design/', json={
    'description': 'ESP32 weather station with BME280 sensor',
    'design_type': 'esp32',
    'constraints': {
        'max_power': '500mW',
        'operating_temp': '-20 to 60C'
    }
})

design_id = response.json()['design_id']

# Get design status
design = requests.get(f'http://localhost:8000/api/design/{design_id}')

# Run simulation
simulation = requests.post('http://localhost:8000/api/simulation/run', json={
    'design_id': design_id,
    'simulation_type': 'full'
})

# Match vendors
vendors = requests.post('http://localhost:8000/api/vendor/match', json={
    'design_id': design_id,
    'quantity': 100
})
```

## 📚 API Documentation

### Design Endpoints

- `POST /api/design/` - Create a new design
- `GET /api/design/{design_id}` - Get design details
- `GET /api/design/` - List all designs

### Simulation Endpoints

- `POST /api/simulation/run` - Run simulation on a design
- `GET /api/simulation/{simulation_id}` - Get simulation results

### Vendor Endpoints

- `POST /api/vendor/match` - Match vendors for manufacturing

Full interactive API documentation is available at http://localhost:8000/docs

## 🏭 Supported Vendors

The system integrates with major PCB manufacturers:

- **JLCPCB** - Fast, affordable prototyping
- **PCBWay** - High-quality PCBs with flexible options
- **OSH Park** - Premium quality, USA-based
- **Seeed Studio** - IoT-focused manufacturing
- **Eurocircuits** - High-frequency and HDI boards

## 🔧 Development

### Project Structure

```
Quantum-Ai-PCB-Builder/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # Data models
│   │   ├── services/     # Business logic
│   │   ├── main.py       # FastAPI app
│   │   ├── config.py     # Configuration
│   │   └── worker.py     # Background worker
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── services/     # API clients
│   │   ├── App.js        # Main app
│   │   └── index.js      # Entry point
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

### Running Locally (Development)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

**RabbitMQ:**
```bash
docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🌟 Roadmap

- [ ] Advanced EDA tool integration (KiCad, Altium)
- [ ] SPICE simulation support
- [ ] 3D PCB visualization
- [ ] Gerber file generation
- [ ] BOM (Bill of Materials) management
- [ ] Collaboration features
- [ ] Version control for designs
- [ ] AI-powered optimization suggestions
- [ ] Mobile app
- [ ] Marketplace for design templates

## 📞 Support

- **Documentation**: [Wiki](https://github.com/NaTo1000/Quantum-Ai-PCB-Builder/wiki)
- **Issues**: [GitHub Issues](https://github.com/NaTo1000/Quantum-Ai-PCB-Builder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/NaTo1000/Quantum-Ai-PCB-Builder/discussions)

## 🙏 Acknowledgments

- FastAPI for the excellent Python web framework
- React team for the frontend library
- RabbitMQ for reliable message queuing
- OpenAI for GPT-4 API
- All PCB manufacturers for their partnership

---

<div align="center">

**Built with ❤️ by the Quantum AI PCB Builder Team**

[⭐ Star us on GitHub](https://github.com/NaTo1000/Quantum-Ai-PCB-Builder) | [🐛 Report Bug](https://github.com/NaTo1000/Quantum-Ai-PCB-Builder/issues) | [💡 Request Feature](https://github.com/NaTo1000/Quantum-Ai-PCB-Builder/issues)

</div>
