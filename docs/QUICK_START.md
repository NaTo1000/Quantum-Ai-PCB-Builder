# Quick Start Guide

## Prerequisites

- Docker and Docker Compose installed
- (Optional) OpenAI API key for enhanced AI features

## Getting Started

### 1. Clone and Configure

```bash
# Clone the repository
git clone https://github.com/NaTo1000/Quantum-Ai-PCB-Builder.git
cd Quantum-Ai-PCB-Builder

# Copy environment file
cp .env.example .env

# (Optional) Edit .env and add your OpenAI API key
# nano .env
```

### 2. Start the Application

```bash
# Start all services with Docker Compose
docker compose up --build
```

Wait for all services to start. You should see:
- ✓ RabbitMQ started on port 5672
- ✓ Backend API started on port 8000
- ✓ Frontend started on port 3000

### 3. Access the Application

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15672 (user: `pcbuser`, pass: `pcbpass`)

## Creating Your First Design

1. Open http://localhost:3000 in your browser
2. Select a design type (e.g., ESP32)
3. Enter a description:
   ```
   Create an ESP32-based temperature sensor with WiFi connectivity,
   DHT22 sensor, and battery power management
   ```
4. Click "Generate Design"
5. Wait for the AI to generate the schematic
6. Review the:
   - Generated schematic with components and connections
   - Simulation results and conflict warnings
   - Vendor recommendations with pricing

## Example Designs

### ESP32 IoT Device
```
Design Type: ESP32
Description: WiFi-enabled temperature and humidity monitor with 
OLED display, powered by USB-C with battery backup
```

### LoRa Communication Module
```
Design Type: LoRa
Description: Long-range wireless sensor node with LoRa radio, 
solar charging, and low-power sleep mode
```

### Custom PCB
```
Design Type: PCB
Description: LED matrix controller with shift registers, 
PWM brightness control, and SPI interface
```

## Stopping the Application

```bash
# Stop all services
docker compose down

# Stop and remove volumes (clears all data)
docker compose down -v
```

## Troubleshooting

### Services won't start
- Check if ports 3000, 8000, 5672, or 15672 are already in use
- Run `docker compose logs` to see error messages

### RabbitMQ connection errors
- Wait 30 seconds after starting for RabbitMQ to fully initialize
- Check `docker compose logs rabbitmq`

### Design generation fails
- If no OpenAI API key is configured, the system uses mock data
- Check backend logs: `docker compose logs backend`

### Frontend can't connect to backend
- Ensure backend is running: `docker compose ps`
- Check backend health: http://localhost:8000/health

## Development Mode

### Backend Development
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### RabbitMQ (separate terminal)
```bash
docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

## Next Steps

- Read the full [README.md](../README.md) for detailed documentation
- Explore the API documentation at http://localhost:8000/docs
- Check out the [API examples](API_EXAMPLES.md)
- Join our [GitHub Discussions](https://github.com/NaTo1000/Quantum-Ai-PCB-Builder/discussions)
