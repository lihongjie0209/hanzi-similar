# syntax=docker/dockerfile:1.7

# --- Base image ---
FROM python:3.11-slim AS base

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
    IMAGES_DIR=/app/images \
    CHROMA_DB_PATH=/app/chroma_db \
    TOP_K=10

WORKDIR /app

# System deps (git for transformers snapshots), libgl for pillow if needed, curl for uv installer
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        libglib2.0-0 \
        libgl1 \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (Python package/deps manager)
RUN curl -fsSL https://astral.sh/uv/install.sh | sh && \
    echo 'export PATH="/root/.local/bin:$PATH"' >> /root/.profile
ENV PATH="/root/.local/bin:$PATH"
ENV UV_LINK_MODE=copy

# --- Python deps via uv + pyproject.toml (system-wide, no local venv) ---
# Use pyproject.toml as the single source of truth
COPY pyproject.toml ./
# Resolve and pin deps, then install to system site-packages
RUN uv pip install --system -r pyproject.toml


# Make models dir, pre-download model at build time to bake into the image
COPY download_model.py ./download_model.py
RUN mkdir -p "$TRANSFORMERS_CACHE" && \
    python download_model.py --model "$MODEL_NAME" --cache-dir "$TRANSFORMERS_CACHE"


# App data: include the prebuilt ChromaDB inside the image
COPY chroma_db ./chroma_db


COPY images ./images




# App code
COPY . .

# Expose default port
EXPOSE 8000

# Runtime command (can override with docker run ...)
CMD ["python", "-m", "uvicorn", "api_main:app", "--host", "0.0.0.0", "--port", "8000"]
