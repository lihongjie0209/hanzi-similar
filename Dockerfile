# syntax=docker/dockerfile:1.7

# --- Base image ---
FROM python:3.13-slim AS base

# Build-time overrides
ARG MODEL_NAME=google/vit-base-patch16-224
ARG TRANSFORMERS_CACHE=/models

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    \
    # Default model and cache (can still be overridden at runtime)
    MODEL_NAME=${MODEL_NAME} \
    TRANSFORMERS_CACHE=${TRANSFORMERS_CACHE} \
    # App defaults
    CHROMA_DB_PATH=/app/chroma_db \
    FONTS_DIR=/app/fonts \
    TOP_K=10

WORKDIR /app

# System deps - minimal for fonttools
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
    && rm -rf /var/lib/apt/lists/* || true

# Upgrade pip
RUN pip install --upgrade pip

# --- Python deps via pip + pyproject.toml (prod dependencies only) ---
# Use pyproject.toml as the single source of truth for dependency management
COPY pyproject.toml ./

# Copy the Python source files needed for editable install
COPY *.py ./

# Install only production dependencies to keep image lean
RUN pip install -e ".[prod]"




# App data: include the prebuilt ChromaDB inside the image
COPY chroma_db ./chroma_db

# Copy fonts directory for SVG rendering
COPY fonts ./fonts

# Copy static files for web UI
COPY static ./static

# Copy scripts directory if it exists
COPY scripts ./scripts



# Ensure proper permissions and verify chroma_db directory
RUN echo "=== Checking chroma_db after copy ===" && \
    ls -la /app/ && \
    echo "=== chroma_db contents ===" && \
    ls -la /app/chroma_db/ && \
    echo "=== Setting permissions ===" && \
    chmod -R 755 /app/chroma_db && \
    chown -R root:root /app/chroma_db && \
    echo "=== Final verification ===" && \
    ls -la /app/chroma_db/ && \
    echo "=== Testing write access ===" && \
    touch /app/chroma_db/.write_test && \
    rm /app/chroma_db/.write_test && \
    echo "Write test successful"

# Expose default port
EXPOSE 8000
# Copy and set up entrypoint script with proper permissions
COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x ./docker-entrypoint.sh

# Set entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]

# Runtime command using Gunicorn for production
CMD ["gunicorn", "api_main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]
