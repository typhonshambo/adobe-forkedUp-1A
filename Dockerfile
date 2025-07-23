FROM --platform=linux/amd64 python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the processing script
COPY process_pdfs.py .

# Create input and output directories
RUN mkdir -p input output

# Run the processing script
CMD ["python", "process_pdfs.py"]
