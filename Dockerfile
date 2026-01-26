# Quantum-Ai-PCB-Builder Dockerfile
# Multi-stage build for optimized production image

# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir build && \
    python -m build --wheel && \
    pip install --no-cache-dir dist/*.whl

# Stage 2: Production
FROM python:3.11-slim AS production

WORKDIR /app

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code (for reference/debugging)
COPY --chown=appuser:appgroup src/ ./src/

# Switch to non-root user
USER appuser

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from quantum_pcb_builder import __version__; print(__version__)" || exit 1

# Default command - can be overridden
CMD ["python", "-c", "from quantum_pcb_builder import __version__; print(f'Quantum PCB Builder v{__version__} is ready!')"]

# Stage 3: Development
FROM python:3.11-slim AS development

WORKDIR /app

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY tests/ ./tests/

# Install package with dev dependencies
RUN pip install --no-cache-dir -e ".[dev]"

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Default command for development - run tests
CMD ["pytest", "tests/", "-v"]
