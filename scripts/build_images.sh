#!/bin/bash

# Build script for Quantum-Ai-PCB-Builder Docker images

set -e

echo "Building Quantum-Ai-PCB-Builder Docker images..."

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Build backend image
echo "Building backend image..."
docker build -t quantum-ai-pcb-builder/backend:latest "$PROJECT_ROOT/backend"

# Build worker image
echo "Building worker image..."
docker build -t quantum-ai-pcb-builder/worker:latest "$PROJECT_ROOT/worker"

# Build frontend image
echo "Building frontend image..."
docker build -t quantum-ai-pcb-builder/frontend:latest "$PROJECT_ROOT/frontend"

echo "All images built successfully!"
echo ""
echo "To start all services, run:"
echo "  cd $PROJECT_ROOT/infra && docker-compose up -d"
