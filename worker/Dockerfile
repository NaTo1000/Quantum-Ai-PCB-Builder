FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY simulator/ ./simulator/

# Run the worker
CMD ["python", "simulator/run_sim.py"]
