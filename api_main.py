from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel
import os
import numpy as np

# Use the advanced vectorizer (ChromaDB + ViT/CLIP)
from vector_db import ChromaVectorDB
from svg_renderer import SvgGlyphRenderer

IMAGES_DIR = os.environ.get("IMAGES_DIR", "images")
CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "./chroma_db")
MODEL_NAME = os.environ.get("MODEL_NAME", "google/vit-base-patch16-224")
TOP_K_DEFAULT = int(os.environ.get("TOP_K", "10"))
FONTS_DIR = os.environ.get("FONTS_DIR")

app = FastAPI(title="Hanzi Similarity API", version="0.2.0")

# Globals
vector_db: ChromaVectorDB | None = None
svg_renderer: SvgGlyphRenderer | None = None


class QueryChar(BaseModel):
    char: str
    top_k: int | None = None


class QueryUnicode(BaseModel):
    unicode: str  # e.g., "U+4E00" or "4E00"
    top_k: int | None = None


class ResultItem(BaseModel):
    char: str
    unicode: str
    distance: float


class SearchResponse(BaseModel):
    query: str
    results: List[ResultItem]


@app.on_event("startup")
async def startup_event():
    global vector_db, svg_renderer
    # allow memory fallback to avoid Windows path ACL issues
    vector_db = ChromaVectorDB(db_path=CHROMA_DB_PATH, allow_memory_fallback=True)

    # Mount static UI and images if available
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
    if os.path.isdir(static_dir):
        try:
            app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="ui")
        except Exception:
            pass
    if os.path.isdir(IMAGES_DIR):
        try:
            app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")
        except Exception:
            pass
    # Prepare SVG renderer with project fonts (configurable)
    fonts_dir = FONTS_DIR or os.path.abspath(os.path.join(os.path.dirname(__file__), "fonts"))
    if os.path.isdir(fonts_dir):
        svg_renderer = SvgGlyphRenderer(fonts_dir)


def _ensure_ready():
    if vector_db is None:
        raise HTTPException(503, detail="Vector service not initialized")
    # Ensure collection has data
    try:
        stats = vector_db.get_stats()
        if stats.get("total_images", 0) == 0:
            raise HTTPException(503, detail="Vector database is empty. Build it with advanced_vectorizer.py first.")
    except Exception as e:
        raise HTTPException(500, detail=f"Vector DB error: {e}")


def _find_similar_by_unicode_hex(uhex: str, top_k: int) -> List[ResultItem]:
    assert vector_db is not None
    # 从向量数据库中取出该字符的向量，而不是在API中做模型推理
    try:
        data = vector_db.collection.get(
            where={"unicode_code": uhex}, include=["embeddings", "metadatas"]
        )
    except Exception as e:
        raise HTTPException(500, detail=f"load embedding error: {e}")

    # 注意：Chroma返回的embeddings可能是numpy数组，避免使用布尔上下文判断
    embeddings = data.get("embeddings", [])
    metadatas = data.get("metadatas", [])
    try:
        embeddings = list(embeddings)
    except Exception:
        embeddings = []
    try:
        metadatas = list(metadatas)
    except Exception:
        metadatas = []
    if len(embeddings) == 0:
        raise HTTPException(404, detail=f"embedding not found for U+{uhex}")

    emb = np.asarray(embeddings[0], dtype=float)
    meta0 = metadatas[0] if metadatas else {"unicode_code": uhex}
    this_id = str(meta0.get("unicode_code", uhex)).upper()

    # 查询相似，取 top_k+1 并跳过自身
    try:
        res = vector_db.collection.query(query_embeddings=[emb.tolist()], n_results=top_k + 1)
    except Exception as e:
        raise HTTPException(500, detail=f"similarity query error: {e}")

    r_ids = (res.get("ids") or [[]])[0]
    r_dists = (res.get("distances") or [[]])[0]
    r_metas = (res.get("metadatas") or [[]])[0]

    out: List[ResultItem] = []
    for rid, dist, m in zip(r_ids, r_dists, r_metas):
        rid_s = str(rid).upper()
        if rid_s == this_id:
            continue
        try:
            ch = chr(int(rid_s, 16))
        except Exception:
            ch = m.get("character") if isinstance(m, dict) else "?"
        out.append(ResultItem(char=ch, unicode=f"U+{rid_s}", distance=float(dist)))
        if len(out) >= top_k:
            break
    return out


@app.post("/search/char", response_model=SearchResponse)
async def search_by_char(payload: QueryChar):
    _ensure_ready()
    if not payload.char or len(payload.char) != 1:
        raise HTTPException(400, detail="char must be a single character")
    top_k = payload.top_k or TOP_K_DEFAULT
    code_hex = f"{ord(payload.char):04X}"
    results = _find_similar_by_unicode_hex(code_hex, top_k)
    return SearchResponse(query=payload.char, results=results)


@app.post("/search/unicode", response_model=SearchResponse)
async def search_by_unicode(payload: QueryUnicode):
    _ensure_ready()
    u = payload.unicode.upper().replace("U+", "").strip()
    if not u or any(c not in '0123456789ABCDEF' for c in u):
        raise HTTPException(400, detail="invalid unicode hex")
    top_k = payload.top_k or TOP_K_DEFAULT
    results = _find_similar_by_unicode_hex(u, top_k)
    try:
        ch = chr(int(u, 16))
    except Exception:
        ch = "?"
    return SearchResponse(query=ch, results=results)


@app.get("/healthz")
async def healthz():
    try:
        _ensure_ready()
        return {"ok": True}
    except HTTPException as he:
        return {"ok": False, "detail": he.detail}


@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/ui/")


@app.get("/glyph/svg/{uhex}")
async def glyph_svg(uhex: str, size: int = 128, fill: str = "#000"):
    # uhex: e.g. '884C' or 'U+884C'
    u = uhex.upper().replace("U+", "").strip()
    if not u or any(c not in '0123456789ABCDEF' for c in u):
        raise HTTPException(400, detail="invalid unicode hex")
    cp = int(u, 16)
    global svg_renderer
    if svg_renderer is None:
        raise HTTPException(503, detail="SVG renderer not initialized (fonts directory missing)")
    try:
        svg = svg_renderer.render_svg(cp, size=size, padding=8, fill=fill)
        return Response(content=svg, media_type="image/svg+xml")
    except FileNotFoundError as e:
        raise HTTPException(404, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"svg render error: {e}")
