# Hanzi Similar Search

A small service that renders Chinese characters as images, builds embeddings, and searches for visually similar characters. It exposes a FastAPI server with a simple web UI.

## Features
- Image generation for CJK codepoints (PNG)
- Advanced embedding (ViT/CLIP via transformers) + ChromaDB vector store
- FastAPI with endpoints to search by char or Unicode
- Frontend UI at `/ui` (Google-like search), tiling results grid
- Crisp glyph rendering with on-the-fly SVG from local fonts (`/glyph/svg/{UHEX}`)

## Requirements
- Python 3.11+
- uv (recommended), or pip
- Fonts covering the desired codepoints placed in `fonts/` (ttf/otf/ttc/otc)

## Quick start
```sh
# optional: create vector DB if not already built
uv run python advanced_vectorizer.py

# start API (uses env vars below)
sh scripts/start.sh
```

Environment variables (with defaults):
- `IMAGES_DIR=images`
- `CHROMA_DB_PATH=./chroma_db`
- `MODEL_NAME=google/vit-base-patch16-224`
- `TOP_K=10`
- `FONTS_DIR=fonts`
- `HOST=0.0.0.0`
- `PORT=8000`
- `BUILD_DB=0` (set to `1` to rebuild DB at startup)

Open UI: http://127.0.0.1:8000/ui/

## REST API
- `POST /search/char` body: `{ "char": "行", "top_k": 12 }`
- `POST /search/unicode` body: `{ "unicode": "884C", "top_k": 12 }`
- `GET /glyph/svg/{UHEX}` render a character as SVG using local fonts

## Docker
```sh
docker build -t hanzi-similar:latest .
# mount fonts and chroma db if not baked into image
docker run --rm -p 18080:8000 \
  -e FONTS_DIR=/app/fonts \
  -e IMAGES_DIR=/app/images \
  -e CHROMA_DB_PATH=/app/chroma_db \
  -v "$PWD/fonts":/app/fonts:ro \
  -v "$PWD/images":/app/images:ro \
  -v "$PWD/chroma_db":/app/chroma_db \
  hanzi-similar:latest
```

## Development
- Generate images: `uv run python generate_hanzi_images.py`
- Build DB (advanced): `uv run python advanced_vectorizer.py`
- Run server: `uv run uvicorn api.main:app --reload`

## Publish to GitHub
This repo is ready to push. If you use GitHub CLI (`gh`):
```sh
gh repo create <owner>/<repo> --source . --private --disable-issues --disable-wiki --confirm
# or public: remove --private

git add -A
git commit -m "feat: initial commit"
git branch -M main
git push -u origin main
```

> Note: CI pipelines are not required. You can add them later if needed.