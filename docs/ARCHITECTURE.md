# Quantum AI PCB Builder - System Architecture

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         User Interface                            │
│                     (React Frontend - Port 3000)                  │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐              │
│  │  Design    │  │  Schematic  │  │   Vendor     │              │
│  │   Input    │  │  Visualizer │  │   Matching   │              │
│  └────────────┘  └─────────────┘  └──────────────┘              │
└───────────────────────────┬──────────────────────────────────────┘
                            │ HTTP/REST API
┌───────────────────────────▼──────────────────────────────────────┐
│                      API Gateway                                  │
│                  (FastAPI - Port 8000)                           │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐              │
│  │  Design    │  │ Simulation  │  │   Vendor     │              │
│  │    API     │  │     API     │  │     API      │              │
│  └────────────┘  └─────────────┘  └──────────────┘              │
└───────────────────────────┬──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│                    Message Queue                                  │
│                (RabbitMQ - Port 5672)                            │
│        Async Task Distribution & Job Management                   │
└───────────────────────────┬──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│                    Background Workers                             │
│              (Python Async Workers)                               │
│  ┌──────────────────────────────────────────────────┐            │
│  │  Design Processing | Simulation | Vendor Match   │            │
│  └──────────────────────────────────────────────────┘            │
└───────────────────────────┬──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│                    Service Layer                                  │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐              │
│  │    LLM     │  │ Simulation  │  │   Vendor     │              │
│  │  Service   │  │   Service   │  │   Service    │              │
│  └────────────┘  └─────────────┘  └──────────────┘              │
│       │               │                  │                        │
│  ┌────▼───────────────▼──────────────────▼────┐                 │
│  │         Design Storage (File System)        │                 │
│  │          /app/designs/*.json                │                 │
│  └─────────────────────────────────────────────┘                 │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    External Services                              │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐              │
│  │  OpenAI    │  │     EDA     │  │Manufacturing │              │
│  │  GPT-4     │  │   Tools     │  │   Vendors    │              │
│  └────────────┘  └─────────────┘  └──────────────┘              │
└──────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend (React)

**Technology:** React 18, Axios, Lucide Icons

**Components:**
- `DesignInput` - Natural language and code input interface
- `DesignResults` - Display generated schematics and results
- `App` - Main application orchestration

**Responsibilities:**
- User input collection
- Real-time status updates
- Schematic visualization
- Vendor comparison display

**Port:** 3000

### 2. Backend API (FastAPI)

**Technology:** FastAPI, Pydantic, Uvicorn

**Endpoints:**
- `POST /api/design/` - Create new design
- `GET /api/design/{id}` - Get design details
- `GET /api/design/` - List all designs
- `POST /api/simulation/run` - Run simulation
- `GET /api/simulation/{id}` - Get simulation results
- `POST /api/vendor/match` - Match vendors

**Responsibilities:**
- Request validation
- Authentication (future)
- Rate limiting (future)
- API documentation (Swagger/OpenAPI)

**Port:** 8000

### 3. Message Queue (RabbitMQ)

**Technology:** RabbitMQ 3 with Management Plugin

**Queues:**
- `design_tasks` - Design generation jobs
- `simulation_tasks` - Simulation jobs
- `vendor_tasks` - Vendor matching jobs

**Responsibilities:**
- Async task distribution
- Load balancing
- Job persistence
- Worker coordination

**Ports:** 5672 (AMQP), 15672 (Management UI)

### 4. Background Workers

**Technology:** Python asyncio

**Workers:**
- Design processor - Generates schematics using LLM
- Simulation processor - Runs design validation
- Vendor matcher - Finds manufacturing partners

**Responsibilities:**
- Long-running task processing
- Concurrent job execution
- Error handling and retry logic

### 5. Service Layer

#### LLM Service
**Functionality:**
- Natural language processing
- Schematic generation
- Component selection
- Connection mapping

**Integration:** OpenAI GPT-4 API (optional, falls back to mock data)

#### Simulation Service
**Functionality:**
- Design rule checking (DRC)
- Conflict detection
- Power analysis
- Signal integrity validation
- Thermal analysis

**Features:**
- Duplicate component detection
- Connection validation
- Floating pin detection
- Power supply verification

#### Vendor Service
**Functionality:**
- Vendor database management
- Price calculation
- Lead time estimation
- Capability matching
- Recommendation engine

**Vendors:**
- JLCPCB
- PCBWay
- OSH Park
- Seeed Studio
- Eurocircuits

### 6. Data Storage

**Design Storage:** File-based JSON storage
- Path: `/app/designs/*.json` (Docker) or `./designs/*.json` (local)
- Each design stored as separate JSON file
- Includes metadata, schematic, and status

**Format:**
```json
{
  "design_id": "uuid",
  "description": "...",
  "design_type": "esp32|lora|pcb|chip|custom",
  "status": "pending|processing|completed|failed",
  "schematic": {
    "components": [...],
    "connections": [...],
    "layout": "...",
    "specifications": {...}
  },
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

## Data Flow

### Design Creation Flow

1. User submits design description via frontend
2. Frontend sends POST request to `/api/design/`
3. Backend creates design record with status "pending"
4. Backend queues design task to RabbitMQ
5. Background worker picks up task
6. Worker calls LLM service to generate schematic
7. Worker updates design status to "completed"
8. Frontend polls for completion and displays results

### Simulation Flow

1. User requests simulation via frontend
2. Frontend sends POST to `/api/simulation/run`
3. Backend retrieves design schematic
4. Backend runs simulation service
5. Service checks for conflicts and warnings
6. Service calculates performance metrics
7. Backend returns simulation results
8. Frontend displays conflicts, warnings, and metrics

### Vendor Matching Flow

1. User requests vendor quotes via frontend
2. Frontend sends POST to `/api/vendor/match`
3. Backend calls vendor service
4. Service filters vendors by capabilities
5. Service calculates pricing based on quantity
6. Service ranks vendors by rating and price
7. Backend returns vendor list and recommendation
8. Frontend displays vendor comparison

## Deployment Architecture

### Docker Compose Setup

```yaml
services:
  - rabbitmq: Message queue
  - backend: FastAPI application
  - worker: Background task processor
  - frontend: React development server
```

### Container Communication

- All services in same Docker network
- Service discovery via container names
- RabbitMQ healthcheck before starting dependents
- Volume mounts for development hot-reload
- Persistent volume for design storage

## Scalability Considerations

### Horizontal Scaling

**Backend:**
- Multiple backend instances behind load balancer
- Stateless design allows easy scaling
- Shared RabbitMQ for coordination

**Workers:**
- Multiple worker instances process jobs concurrently
- RabbitMQ distributes tasks automatically
- Workers can be scaled independently

### Vertical Scaling

**Memory:**
- LLM service may require 2-4GB RAM
- Workers can process larger designs

**CPU:**
- Simulation computations benefit from multi-core
- Async operations maximize CPU utilization

## Security Considerations

### Current Implementation
- CORS enabled (configure for production)
- No authentication (add in future)
- Local file storage (migrate to database)

### Future Enhancements
- JWT authentication
- API key management
- Rate limiting per user
- Input sanitization
- SQL injection prevention (when DB added)
- Encrypted sensitive data

## Performance Characteristics

### Response Times
- Design creation: < 100ms (async processing)
- Design processing: 2-10s (LLM dependent)
- Simulation: < 1s (in-memory computation)
- Vendor matching: < 100ms (database lookup)

### Throughput
- API: 100+ req/s per instance
- Workers: 10-20 designs/min per worker
- RabbitMQ: 1000+ msg/s

### Resource Usage
- Backend: ~200MB RAM, 10% CPU
- Worker: ~500MB RAM, 20% CPU (with LLM)
- RabbitMQ: ~100MB RAM, 5% CPU
- Frontend: ~50MB RAM, varies

## Monitoring & Observability

### Health Checks
- Backend: `/health` endpoint
- RabbitMQ: Built-in management UI
- Container: Docker healthcheck

### Logs
- Backend: Uvicorn access logs
- Workers: Python logging to stdout
- RabbitMQ: Message delivery logs

### Metrics (Future)
- Prometheus integration
- Request rate and latency
- Queue depth monitoring
- Worker processing time
- Error rates

## Technology Stack Summary

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Frontend | React | 18.2 | UI Framework |
| Frontend Build | Create React App | 5.0 | Development tooling |
| Backend | FastAPI | 0.109 | REST API framework |
| Backend Server | Uvicorn | 0.27 | ASGI server |
| Message Queue | RabbitMQ | 3.x | Async task distribution |
| Language | Python | 3.11+ | Backend/Worker logic |
| Language | JavaScript | ES6+ | Frontend logic |
| AI/LLM | OpenAI GPT-4 | Latest | Schematic generation |
| Validation | Pydantic | 2.5 | Data validation |
| HTTP Client | Axios | 1.6 | API communication |
| Container | Docker | Latest | Containerization |
| Orchestration | Docker Compose | 2.x | Multi-container mgmt |

## Future Enhancements

### Short Term
1. Database integration (PostgreSQL)
2. User authentication and authorization
3. Design versioning and history
4. Real-time collaboration
5. Export to common EDA formats (KiCad, Eagle)

### Medium Term
1. Advanced EDA tool integration
2. SPICE simulation support
3. 3D PCB visualization
4. Gerber file generation
5. BOM management and costing

### Long Term
1. AI-powered design optimization
2. Machine learning for component selection
3. Automated design-for-manufacturing (DFM)
4. Marketplace for design templates
5. Mobile application
6. Real-time vendor bidding system
