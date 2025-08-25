#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Demo: query a stored embedding for a given character (or code point) from ChromaDB,
then use that embedding to search for similar images.

Usage:
    # Fetch embedding and print top-10 similar items
    uv run query_embedding.py 行

    # Specify top-k, accept hex code forms
    uv run query_embedding.py --top-k 15 U+2F00
    uv run query_embedding.py --top-k 8 2F00
"""

import sys
import argparse
import numpy as np
from vector_db import ChromaVectorDB


def parse_arg_to_code_and_char(arg: str):
    arg = arg.strip()
    if not arg:
        raise ValueError("输入为空")

    if arg.startswith(("U+", "u+")):
        code = arg[2:].upper()
        ch = chr(int(code, 16))
        return code, ch

    if len(arg) == 1:
        code = f"{ord(arg):04X}"
        return code, arg

    # treat as hex code like 2F00
    code = arg.upper()
    ch = chr(int(code, 16))
    return code, ch


def main():
    parser = argparse.ArgumentParser(description="Fetch an embedding and search similar images from ChromaDB")
    parser.add_argument("query", help="字符或Unicode十六进制码，如 行 / U+4E00 / 4E00")
    parser.add_argument("--top-k", type=int, default=10, dest="top_k", help="返回的相似结果数 (默认: 10)")
    parser.add_argument("--include-self", action="store_true", help="包含自身结果 (默认跳过自身)")
    args = parser.parse_args()

    try:
        code, ch = parse_arg_to_code_and_char(args.query)
    except Exception as e:
        print(f"参数解析失败: {e}")
        return 2

    db = ChromaVectorDB()

    data = db.collection.get(
        where={"unicode_code": code},
        include=["metadatas", "embeddings"],
    )

    # Chroma may include ids by default; normalize and avoid numpy truthiness
    ids = data.get("ids", [])
    embeddings = data.get("embeddings", [])
    metadatas = data.get("metadatas", [])

    # Ensure python lists
    try:
        ids = list(ids)
    except Exception:
        ids = []
    try:
        embeddings = list(embeddings)
    except Exception:
        embeddings = []
    try:
        metadatas = list(metadatas)
    except Exception:
        metadatas = []

    if len(embeddings) == 0:
        print(f"未在集合中找到 U+{code} ({ch}) 的记录")
        return 3

    emb = np.asarray(embeddings[0], dtype=np.float32)
    meta = metadatas[0] if metadatas else {"unicode_code": code, "character": ch}
    this_id = ids[0] if ids else meta.get("unicode_code", code)

    print(f"找到记录: ID={this_id} 字符={ch} U+{code}")
    print(f"元数据: {meta}")
    print(f"向量维度: {emb.shape[0]}  L2范数: {np.linalg.norm(emb):.4f}")
    print("前16维:", np.array2string(emb[:16], precision=5, separator=", "))

    # Use embedding to search similar images
    results = db.collection.query(query_embeddings=[emb.tolist()], n_results=args.top_k + 1)
    r_ids = results.get("ids", [[]])[0]
    r_dists = results.get("distances", [[]])[0]
    r_metas = results.get("metadatas", [[]])[0]

    out_rows = []
    for rid, dist, m in zip(r_ids, r_dists, r_metas):
        if not args.include_self and str(rid).upper() == str(this_id).upper():
            continue
        try:
            ch2 = chr(int(str(rid), 16))
        except Exception:
            ch2 = m.get("character") if isinstance(m, dict) else "?"
        out_rows.append({
            "id": rid,
            "unicode": f"U+{rid}",
            "char": ch2,
            "distance": float(dist),
            "similarity": float(1.0 - float(dist)),
            "metadata": m,
        })
        if len(out_rows) >= args.top_k:
            break

    print("相似结果 (按相似度降序，基于余弦距离 1 - d):")
    for i, row in enumerate(out_rows, 1):
        md = row["metadata"] or {}
        char_disp = md.get("character", row["char"]) if isinstance(md, dict) else row["char"]
        print(
            f"{i:2d}. {row['unicode']} 字符: {char_disp} 距离: {row['distance']:.4f} 相似度: {row['similarity']:.4f}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
