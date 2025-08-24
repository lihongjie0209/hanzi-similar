#!/usr/bin/env sh
set -eu

# Config (override with env vars before running)
: "${IMAGES_DIR:=images}"
: "${CHROMA_DB_PATH:=./chroma_db}"
: "${MODEL_NAME:=google/vit-base-patch16-224}"
: "${TOP_K:=10}"
: "${FONTS_DIR:=fonts}"
: "${HOST:=0.0.0.0}"
: "${PORT:=8000}"
: "${BUILD_DB:=0}"

echo "IMAGES_DIR=$IMAGES_DIR"
echo "CHROMA_DB_PATH=$CHROMA_DB_PATH"
echo "MODEL_NAME=$MODEL_NAME"
echo "FONTS_DIR=$FONTS_DIR"

# Optionally (re)build the advanced vector database
if [ "$BUILD_DB" = "1" ]; then
  echo "[start.sh] BUILD_DB=1 -> building vector DB..."
  if command -v uv >/dev/null 2>&1; then
    uv run python advanced_vectorizer.py
  else
    python advanced_vectorizer.py
  fi
fi

# Quick check: warn if chroma DB appears empty
if [ ! -f "$CHROMA_DB_PATH/chroma.sqlite3" ]; then
  echo "[start.sh] WARN: $CHROMA_DB_PATH/chroma.sqlite3 not found. API may report DB empty until you build it."
fi

# Start API
echo "[start.sh] starting API at http://$HOST:$PORT ..."
if command -v uv >/dev/null 2>&1; then
  IMAGES_DIR="$IMAGES_DIR" CHROMA_DB_PATH="$CHROMA_DB_PATH" MODEL_NAME="$MODEL_NAME" TOP_K="$TOP_K" FONTS_DIR="$FONTS_DIR" \
  uv run uvicorn api.main:app --host "$HOST" --port "$PORT"
else
  IMAGES_DIR="$IMAGES_DIR" CHROMA_DB_PATH="$CHROMA_DB_PATH" MODEL_NAME="$MODEL_NAME" TOP_K="$TOP_K" FONTS_DIR="$FONTS_DIR" \
  python -m uvicorn api.main:app --host "$HOST" --port "$PORT"
fi
