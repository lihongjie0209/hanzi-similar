import os
import pickle
import hashlib
from collections import Counter, defaultdict
from typing import List, Tuple

import numpy as np
from PIL import Image

VEC_DB = "vector_db.pkl"
IMG_DIR = "images"


def load_db():
    with open(VEC_DB, "rb") as f:
        data = pickle.load(f)
    return data["pca"], data["nbrs"], data["features"], data["filenames"]


def hex_code(ch: str) -> str:
    return f"{ord(ch):04X}"


def img_path_from_hex(code_hex: str) -> str:
    return os.path.join(IMG_DIR, f"{code_hex}.png")


def ensure_files_exist(codes: List[str]) -> List[Tuple[str, bool]]:
    return [(c, os.path.exists(img_path_from_hex(c))) for c in codes]


def get_index(filenames: List[str], code_hex: str) -> int:
    name = f"{code_hex}.png"
    if name in filenames:
        return filenames.index(name)
    return -1


def l2_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def image_hash(code_hex: str) -> str:
    p = img_path_from_hex(code_hex)
    with Image.open(p) as img:
        img = img.convert("1")  # ensure binary
        return hashlib.sha256(img.tobytes()).hexdigest()


def count_black_pixels(code_hex: str) -> int:
    p = img_path_from_hex(code_hex)
    with Image.open(p) as img:
        arr = np.array(img.convert("1"))
        # In mode '1', pixel 0 is black, 255 (True) is white when converted to uint8 via numpy
        # When kept as bool, True is white, False is black
        if arr.dtype == np.bool_:
            return int(np.count_nonzero(arr == False))
        return int(np.count_nonzero(arr == 0))


def knn_contains_target(pca, nbrs, features, filenames, src_hex: str, tgt_hex: str, ks=(5, 10, 20, 50, 100)):
    src_idx = get_index(filenames, src_hex)
    tgt_idx = get_index(filenames, tgt_hex)
    if src_idx == -1 or tgt_idx == -1:
        return {
            "src_in_db": src_idx != -1,
            "tgt_in_db": tgt_idx != -1,
            "present": {k: False for k in ks},
            "distance": None,
        }

    q = features[src_idx].reshape(1, -1)
    # Query once with largest K, then evaluate for all smaller Ks
    K = max(ks)
    dists, inds = nbrs.kneighbors(q, n_neighbors=min(K, len(filenames)))
    inds = inds[0].tolist()
    dists = dists[0].tolist()

    # map index to rank
    idx_to_rank = {idx: rank for rank, idx in enumerate(inds, start=1)}
    present = {}
    for k in ks:
        topk_inds = set(inds[:k])
        present[k] = (tgt_idx in topk_inds)

    distance = l2_distance(features[src_idx], features[tgt_idx])
    tgt_rank = idx_to_rank.get(tgt_idx)

    return {
        "src_in_db": True,
        "tgt_in_db": True,
        "present": present,
        "rank": tgt_rank,
        "distance": distance,
        "src_idx": src_idx,
        "tgt_idx": tgt_idx,
        "tgt_dist_at_rank": (dists[tgt_rank - 1] if tgt_rank else None),
    }


def scan_duplicates(range_start: int, range_end: int, sample_limit: int = 200):
    """Scan a Unicode range and report duplicate image hashes (indicating same glyph).
    Returns a summary dict and a few sample groups.
    """
    hashes = []
    codes = []
    for code in range(range_start, range_end + 1):
        code_hex = f"{code:04X}"
        p = img_path_from_hex(code_hex)
        if os.path.exists(p):
            try:
                h = image_hash(code_hex)
                hashes.append(h)
                codes.append(code_hex)
            except Exception:
                continue
    counter = Counter(hashes)
    # group codes by hash
    groups = defaultdict(list)
    for code_hex, h in zip(codes, hashes):
        groups[h].append(code_hex)

    # sort groups by size desc
    group_list = sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True)
    top_groups = group_list[:5]
    top_summary = [(len(v), v[:min(10, len(v))]) for _, v in top_groups]
    total = len(codes)
    dup_total = sum(size for size, _ in top_summary if size > 1)

    return {
        "total_checked": total,
        "num_unique_hashes": len(counter),
        "top_groups": top_summary,
        "groups": groups,
    }


def main():
    ch_full = "行"   # U+884C
    ch_rad = "⾏"   # U+2F8F
    hex_full = hex_code(ch_full)
    hex_rad = hex_code(ch_rad)

    print(f"Full: {ch_full} U+{hex_full} -> {img_path_from_hex(hex_full)}")
    print(f"Rad : {ch_rad} U+{hex_rad} -> {img_path_from_hex(hex_rad)}\n")

    # 1) Existence check
    for code_hex, exists in ensure_files_exist([hex_full, hex_rad]):
        print(f"Exists {code_hex}.png: {exists}")
    print()

    # 2) Vector DB check + retrieval presence
    try:
        pca, nbrs, features, filenames = load_db()
    except FileNotFoundError:
        print("vector_db.pkl not found. Please run vectorize_images.py first.")
        return

    res1 = knn_contains_target(pca, nbrs, features, filenames, hex_full, hex_rad)
    res2 = knn_contains_target(pca, nbrs, features, filenames, hex_rad, hex_full)

    print("[Retrieval] 行 -> ⾏")
    print(res1)
    print("[Retrieval] ⾏ -> 行")
    print(res2)
    print()

    # 3) Pixel diagnostics
    try:
        bp_full = count_black_pixels(hex_full)
        bp_rad = count_black_pixels(hex_rad)
        print(f"Black pixels 行: {bp_full}")
        print(f"Black pixels ⾏: {bp_rad}")
    except Exception as e:
        print(f"Pixel diag error: {e}")
    print()

    # 4) Duplicate hash scan in radicals ranges to detect missing glyphs rendered identically
    print("Scanning radicals ranges for duplicate images...")
    scan1 = scan_duplicates(0x2E80, 0x2EFF)
    scan2 = scan_duplicates(0x2F00, 0x2FDF)

    def print_scan(tag, scan):
        print(f"[{tag}] total_checked={scan['total_checked']}, unique_hashes={scan['num_unique_hashes']}")
        for size, sample in scan["top_groups"]:
            if size > 1:
                print(f"  dup group size {size} sample: {', '.join(sample)}")

    print_scan("CJK Radicals Supplement", scan1)
    print_scan("Kangxi Radicals", scan2)

    # 5) Is ⾏ part of a large duplicate group?
    def group_of(code_hex, scan):
        for h, codes in scan["groups"].items():
            if code_hex in codes:
                return codes
        return []

    # Try both scans since ⾏ (U+2F8F) is in Kangxi Radicals (0x2F00-0x2FDF)
    grp_rad = group_of(hex_rad, scan2) or group_of(hex_rad, scan1)
    print()
    if grp_rad:
        print(f"Group of ⾏ ({hex_rad}) size: {len(grp_rad)} e.g.: {grp_rad[:15]}")
    else:
        print(f"⾏ ({hex_rad}) not found in duplicate scan (unexpected)")


if __name__ == "__main__":
    main()
