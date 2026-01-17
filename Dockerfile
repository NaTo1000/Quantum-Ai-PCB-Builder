# Multi-stage build for optimal image size
FROM python:3.11-slim AS builder

# Set build-time environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only the files needed for installation
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Build the wheel
RUN pip install build && python -m build --wheel

# Production stage
FROM python:3.11-slim AS production

# Create non-root user for security
RUN groupadd -r quantum && useradd -r -g quantum quantum

# Set runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    QUANTUM_PCB_OUTPUT_DIR=/app/output

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy wheel from builder
COPY --from=builder /build/dist/*.whl ./

# Install the package
RUN pip install --no-cache-dir ./*.whl && rm -f ./*.whl

# Create output directory
RUN mkdir -p /app/output && chown -R quantum:quantum /app

# Switch to non-root user
USER quantum

# Set the entrypoint
ENTRYPOINT ["quantum-pcb"]

# Default command (help)
CMD ["--help"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD quantum-pcb --version || exit 1

# Labels for container metadata
LABEL org.opencontainers.image.title="Quantum AI PCB Builder" \
      org.opencontainers.image.description="Autonomous AI-powered PCB design with quantum-inspired optimization" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.source="https://github.com/NaTo1000/Quantum-Ai-PCB-Builder" \
      org.opencontainers.image.licenses="Apache-2.0"
