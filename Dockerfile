# ──────────────────────────────────────────────
# Stage 1: Build image with virtual environment
# ──────────────────────────────────────────────
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set up virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirement files
COPY requirements-docker.txt requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements-docker.txt && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# ──────────────────────────────────────────────
# Stage 2: Runtime Image
# ──────────────────────────────────────────────
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    HF_HUB_CACHE=/app/.cache/huggingface \
    TORCH_HOME=/app/.cache/torch \
    NLTK_DATA=/app/.cache/nltk_data

# Set working directory
WORKDIR /app

# Create required cache directories
RUN mkdir -p .cache/huggingface .cache/torch .cache/nltk_data

# Create a non-root user for safety
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Ensure utils directory is properly structured
RUN touch utils/__init__.py

# Pre-download models to speed up runtime
RUN python -c "import nltk; nltk.download('punkt', download_dir='.cache/nltk_data'); nltk.download('stopwords', download_dir='.cache/nltk_data')" && \
    python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; SentenceTransformer('all-MiniLM-L6-v2'); CrossEncoder('cross-encoder/ms-marco-MiniLM-L6-v2')" && \
    chown -R appuser:appuser /app/.cache

# Switch to non-root user
USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.append('/app'); from utils.extractor import PDFExtractor; print('healthy')" || exit 1

# Run the processing script in auto mode
ENTRYPOINT ["python", "process_pdfs.py"]
CMD ["--auto"]