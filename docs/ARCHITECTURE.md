# Quantum-Ai-PCB-Builder Architecture Documentation

## Overview

This document provides detailed architecture information for the Quantum-Ai-PCB-Builder platform, an AI-orchestrated hardware design system for chip and PCB schematic generation, simulation, and vendor integration.

## Core Components

### 1. LLM Synthesis Module (`src/ai/`)

The AI synthesis module is responsible for converting natural language design prompts into structured hardware designs.

#### Components:
- **LLM Adapter** (`llm_adapter.py`): Pluggable interface for different LLM providers
  - OpenAI GPT-4
  - Anthropic Claude
  - Local LLMs (Llama, Mistral, etc.)
- **Design Synthesizer** (`synthesis.py`): Orchestrates the synthesis pipeline

#### Data Flow:
```
User Prompt → LLM Adapter → Design Synthesizer → Structured Design
```

### 2. Validation Module (`src/validation/`)

Performs rule-based design validation to ensure manufacturability.

#### Components:
- **DRC** (`drc.py`): Design Rule Check for geometric constraints
- **LVS** (`lvs.py`): Layout vs Schematic comparison
- **Analysis** (`analysis.py`): IR drop and electromigration analysis

#### Validation Stages:
1. Geometric validation (spacing, width, overlap)
2. Electrical validation (shorts, opens)
3. Reliability validation (EM, IR drop)

### 3. Simulation Module (`src/simulation/`)

Runs SPICE and timing simulations on generated designs.

#### Backends:
- **SPICE**: ngspice, Xyce, HSPICE
- **Timing**: OpenSTA, PrimeTime

#### Metrics:
- Power consumption
- Timing slack
- Signal integrity
- Thermal analysis

### 4. Vendor Matching Module (`src/vendor/`)

Matches design requirements with compatible vendors.

#### Matching Criteria:
- Process node compatibility
- Packaging capabilities
- Volume requirements
- Certification requirements

#### Supported Vendors:
- Foundries: TSMC, Samsung, GlobalFoundries
- PCB Assembly: JLCPCB, PCBWay
- Packaging: ASE, Amkor

### 5. API Layer (`src/api/`)

RESTful API for external access.

#### Endpoints:
- `GET /` - API information
- `GET /health` - Health check
- `GET /api/v1/status` - System status
- `POST /api/v1/design/synthesize` - Submit design prompt
- `POST /api/v1/design/validate` - Validate design
- `POST /api/v1/vendor/match` - Find matching vendors

### 6. Background Workers (`src/workers/`)

Asynchronous job processing for long-running tasks.

#### Job Types:
- Design synthesis
- Validation
- Simulation
- Vendor matching
- Export

## Data Models

### Design Prompt
```json
{
  "prompt": "low-power RISC-V core with HBM and 3D packaging",
  "constraints": {
    "power_budget_watts": 5.0,
    "target_frequency_mhz": 1000,
    "process_node": "7nm"
  }
}
```

### Synthesis Result
```json
{
  "architecture_description": "...",
  "rtl_stub": "module design...",
  "components": [
    {
      "name": "RISC-V Core",
      "type": "processor",
      "constraints": [...]
    }
  ]
}
```

### Vendor Quote
```json
{
  "vendor_name": "TSMC",
  "unit_cost_usd": 25.0,
  "nre_cost_usd": 50000.0,
  "lead_time_weeks": 12,
  "min_order_quantity": 10000
}
```

## Extensibility Points

### Adding a New LLM Provider

1. Create a new adapter class inheriting from `LLMAdapter`
2. Implement `generate()` and `get_model_name()` methods
3. Register in the adapter factory

### Adding a New Simulation Backend

1. Create a new simulator class inheriting from `Simulator`
2. Implement `run()` and `get_backend_name()` methods
3. Add backend configuration in settings

### Adding a New Vendor

1. Add vendor capabilities to the vendor database
2. Define process nodes and packaging types
3. Implement quote API integration if available

## Deployment Architecture

### Local Development
```
┌─────────────────┐
│   Python App    │
│  (API + Workers)│
└─────────────────┘
```

### Docker Compose
```
┌─────────────────┐   ┌─────────────────┐
│      API        │◄──│    RabbitMQ     │
└─────────────────┘   └─────────────────┘
        │                     │
        ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│     Workers     │   │     Redis       │
└─────────────────┘   └─────────────────┘
```

### Kubernetes
```
┌──────────────────────────────────────────────┐
│                  Ingress                      │
└──────────────────────────────────────────────┘
        │
        ▼
┌─────────────────┐   ┌─────────────────┐
│  API Deployment │   │ Worker Deployment│
│    (3 pods)     │   │    (5 pods)     │
└─────────────────┘   └─────────────────┘
        │                     │
        ▼                     ▼
┌─────────────────────────────────────────────┐
│            Message Queue (RabbitMQ)          │
└─────────────────────────────────────────────┘
```

## Security Considerations

1. **API Key Management**: Use environment variables or vault
2. **PDK Access**: NDA-aware modules gate sensitive data
3. **Network Security**: Internal services not exposed externally
4. **Input Validation**: All user inputs sanitized and validated

## Future Enhancements

1. **WebSocket Support**: Real-time job status updates
2. **Quantum Solvers**: Integration with quantum optimization
3. **Multi-tenancy**: User authentication and project isolation
4. **Schematic Canvas**: Real-time SVG editing in browser
