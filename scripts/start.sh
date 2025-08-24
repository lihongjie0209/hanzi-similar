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
# Select runner: auto | 1 (force uv) | 0 (force python)
: "${USE_UV:=auto}"
:# Optional absolute path override for uv binary
: "${UV_BIN:=}"

find_uv_bin() {
  # If UV_BIN provided and executable, honor it
  if [ -n "$UV_BIN" ] && [ -x "$UV_BIN" ]; then
    return 0
  fi

  # search common locations and PATH (for systemd PATH restrictions)
  for cand in \
    "$(command -v uv 2>/dev/null || true)" \
    "$(command -v uv.exe 2>/dev/null || true)" \
    /usr/bin/uv \
    /usr/local/bin/uv \
    "$HOME/.local/bin/uv" \
    /opt/homebrew/bin/uv \
    /snap/bin/uv
  do
    if [ -n "$cand" ] && [ -x "$cand" ]; then
      UV_BIN="$cand"
      return 0
    fi
  done
  return 1
}

echo "IMAGES_DIR=$IMAGES_DIR"
echo "CHROMA_DB_PATH=$CHROMA_DB_PATH"
echo "MODEL_NAME=$MODEL_NAME"
echo "FONTS_DIR=$FONTS_DIR"

# Optionally (re)build the advanced vector database
if [ "$BUILD_DB" = "1" ]; then
  echo "[start.sh] BUILD_DB=1 -> building vector DB..."
  if [ "$USE_UV" = "1" ]; then
    if find_uv_bin; then
      echo "[start.sh] using UV_BIN=$UV_BIN"
      "$UV_BIN" run python advanced_vectorizer.py
    else
      echo "[start.sh] ERROR: USE_UV=1 but 'uv' not found in PATH." >&2
      echo "           Install uv (https://github.com/astral-sh/uv) or set USE_UV=0 to use python." >&2
      exit 1
    fi
  else
    if find_uv_bin && [ "$USE_UV" = "auto" ]; then
      echo "[start.sh] using UV_BIN=$UV_BIN"
      "$UV_BIN" run python advanced_vectorizer.py
    else
      python advanced_vectorizer.py
    fi
  fi
fi

# Quick check: warn if chroma DB appears empty
if [ ! -f "$CHROMA_DB_PATH/chroma.sqlite3" ]; then
  echo "[start.sh] WARN: $CHROMA_DB_PATH/chroma.sqlite3 not found. API may report DB empty until you build it."
fi

# Start API
echo "[start.sh] starting API at http://$HOST:$PORT ... (USE_UV=$USE_UV)"
if [ "$USE_UV" = "1" ]; then
  if find_uv_bin; then
    echo "[start.sh] using UV_BIN=$UV_BIN"
    IMAGES_DIR="$IMAGES_DIR" CHROMA_DB_PATH="$CHROMA_DB_PATH" MODEL_NAME="$MODEL_NAME" TOP_K="$TOP_K" FONTS_DIR="$FONTS_DIR" \
      "$UV_BIN" run uvicorn api.main:app --host "$HOST" --port "$PORT"
  else
    echo "[start.sh] ERROR: USE_UV=1 but 'uv' not found in PATH." >&2
    exit 1
  fi
else
  if find_uv_bin && [ "$USE_UV" = "auto" ]; then
    echo "[start.sh] using UV_BIN=$UV_BIN"
    IMAGES_DIR="$IMAGES_DIR" CHROMA_DB_PATH="$CHROMA_DB_PATH" MODEL_NAME="$MODEL_NAME" TOP_K="$TOP_K" FONTS_DIR="$FONTS_DIR" \
      "$UV_BIN" run uvicorn api.main:app --host "$HOST" --port "$PORT"
  else
    IMAGES_DIR="$IMAGES_DIR" CHROMA_DB_PATH="$CHROMA_DB_PATH" MODEL_NAME="$MODEL_NAME" TOP_K="$TOP_K" FONTS_DIR="$FONTS_DIR" \
      python -m uvicorn api.main:app --host "$HOST" --port "$PORT"
  fi
fi
