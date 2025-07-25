# syntax=docker/dockerfile:1.4

FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

# Install only necessary system build tools (gcc, g++) for compiling packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies with pip cache and clean up build tools after
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y gcc g++ && apt-get autoremove -y

# Copy project files after dependencies to avoid cache invalidation
COPY process_pdfs.py .
COPY utils/ ./utils/

# Create input/output folders
RUN mkdir -p input output

# Default command
CMD ["python", "process_pdfs.py"]
