#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate Hanzi SVG glyphs using SvgGlyphRenderer with multithreading.

Examples:
  # Generate default ranges into ./svg
  uv run --python 3.13 generate_hanzi_svgs.py

  # Custom output and size
  uv run --python 3.13 generate_hanzi_svgs.py --out svg --size 256 --fill "#111"

  # Allow missing codepoints and continue; also limit workers
  uv run --python 3.13 generate_hanzi_svgs.py --allow-missing --workers 8

  # Generate specific codepoints only
  uv run --python 3.13 generate_hanzi_svgs.py --codes 4E00,4E8C,884C
"""

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Iterable, List, Set, Sequence

# Optional progress bar
try:
    from tqdm.auto import tqdm  # type: ignore
    _HAVE_TQDM = True
except Exception:  # pragma: no cover
    _HAVE_TQDM = False
    def tqdm(iterable=None, total=None, desc=None, unit=None):  # type: ignore
        # Minimal fallback: passthrough iterable
        return iterable if iterable is not None else []

from svg_renderer import SvgGlyphRenderer

# Default Unicode ranges (aligned with generate_hanzi_images.py)
DEFAULT_RANGES = [
    (0x2E80, 0x2EFF),  # CJK Radicals Supplement
    (0x2F00, 0x2FDF),  # Kangxi Radicals
    (0x2FF0, 0x2FFF),  # Ideographic Description Characters
    (0x3000, 0x303F),  # CJK Symbols and Punctuation
    (0x3400, 0x4DBF),  # CJK Unified Ideographs Extension A
    (0x4E00, 0x9FFF),  # CJK Unified Ideographs (main)
]


def parse_codes_arg(codes_str: str) -> List[int]:
    out: List[int] = []
    for tok in codes_str.split(','):
        tok = tok.strip()
        if not tok:
            continue
        if len(tok) == 1 and not tok.upper().startswith('U+'):
            out.append(ord(tok))
            continue
        if tok.upper().startswith('U+'):
            tok = tok[2:]
        out.append(int(tok, 16))
    return out


def iter_default_codes(ranges=DEFAULT_RANGES) -> Iterable[int]:
    for s, e in ranges:
        for cp in range(s, e + 1):
            yield cp


def shard_list(items: Sequence[int], parts: int) -> List[List[int]]:
    """Split list into at most `parts` shards with near-equal sizes (contiguous chunks)."""
    n = len(items)
    if parts <= 0:
        return [list(items)]
    parts = min(parts, n) if n > 0 else 1
    base = n // parts
    extra = n % parts
    shards: List[List[int]] = []
    start = 0
    for i in range(parts):
        size = base + (1 if i < extra else 0)
        end = start + size
        if size > 0:
            shards.append(list(items[start:end]))
        start = end
    return shards

# =====================
# Multiprocessing hooks
# =====================
_WORKER_RENDERER = None  # type: ignore[var-annotated]
_WORKER_PARAMS = None    # type: ignore[var-annotated]


def _init_worker(fonts_dir: str, size: int, padding: int, fill: str, out_dir: str):
    """Per-process initializer: build renderer and cache params in globals."""
    global _WORKER_RENDERER, _WORKER_PARAMS
    _WORKER_RENDERER = SvgGlyphRenderer(fonts_dir)
    # Preload faces/coverage to avoid re-scan per glyph
    _WORKER_RENDERER._load_faces()  # type: ignore[attr-defined]
    _WORKER_PARAMS = dict(size=size, padding=padding, fill=fill, out_dir=out_dir)


def _proc_worker(args_tuple) -> tuple[int, int, List[str]]:
    """Process worker: render a shard of codepoints.
    Returns (done_count, error_count, first_errors)
    """
    shard_index, shard = args_tuple
    local_errors = 0
    first_errs: List[str] = []
    params = _WORKER_PARAMS  # type: ignore[name-defined]
    renderer = _WORKER_RENDERER  # type: ignore[name-defined]
    for cp in shard:
        fn = os.path.join(params['out_dir'], f"{cp:04X}.svg")
        try:
            svg = renderer.render_svg(cp, size=params['size'], padding=params['padding'], fill=params['fill'])
            tmp = fn + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                f.write(svg)
            os.replace(tmp, fn)
        except Exception as e:
            local_errors += 1
            if len(first_errs) < 5:
                first_errs.append(f"U+{cp:04X}: {e}")
    return (len(shard), local_errors, first_errs)

def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Hanzi SVGs concurrently using project fonts.")
    parser.add_argument('--out', dest='out_dir', default='svg', help='Output directory for SVG files (default: svg)')
    parser.add_argument('--size', type=int, default=128, help='SVG canvas size (default: 128)')
    parser.add_argument('--padding', type=int, default=8, help='Padding inside SVG viewBox (default: 8)')
    parser.add_argument('--fill', default='#000', help='Fill color (default: #000)')
    parser.add_argument('--allow-missing', action='store_true', help='Allow missing codepoints and skip them')
    # typo-friendly alias
    parser.add_argument('--allow-missings', dest='allow_missing', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--workers', type=int, default=(os.cpu_count() or 2), help='Workers (default: CPU cores)')
    parser.add_argument('--codes', default='', help='Comma-separated codepoints (hex or chars), e.g., 4E00,4E8C,884C or 一,二')
    parser.add_argument('--fonts-dir', default=os.environ.get('FONTS_DIR') or 'fonts', help='Fonts directory (default: fonts or $FONTS_DIR)')
    parser.add_argument('--mode', choices=['process', 'thread'], default='process', help='Concurrency mode (default: process)')
    args = parser.parse_args()

    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)

    # Init renderer (will scan fonts and build coverage)
    renderer = SvgGlyphRenderer(args.fonts_dir)
    try:
        # force load faces and coverage
        renderer._load_faces()  # type: ignore[attr-defined]
    except Exception as e:
        print(f"错误: 无法加载字体目录 {args.fonts_dir}: {e}")
        return 2

    if not renderer.faces:
        print(f"错误: 字体目录 {args.fonts_dir} 中未找到可用字体。")
        return 2

    # Build coverage set for quick pre-check
    covered: Set[int] = set()
    for face in renderer.faces:
        if face.codepoints:
            covered.update(face.codepoints)

    # Determine target codepoints
    if args.codes:
        targets = parse_codes_arg(args.codes)
    else:
        targets = list(iter_default_codes())

    # Pre-check coverage
    missing = [cp for cp in targets if cp not in covered]
    if missing:
        preview = ', '.join([f"U+{cp:04X}" for cp in missing[:20]])
        if not args.allow_missing:
            print(f"发现 {len(missing)} 个码点缺失，例如: {preview}")
            print("使用 --allow-missing 可跳过缺失码点继续生成，或将覆盖字体放入 fonts 目录。")
            return 3
        # write report
        try:
            with open(os.path.join(out_dir, 'missing_codepoints.txt'), 'w', encoding='utf-8') as f:
                f.write('\n'.join([f"U+{cp:04X}" for cp in missing]))
            print(f"警告: 有 {len(missing)} 个码点缺失，已写入 {os.path.join(out_dir, 'missing_codepoints.txt')}，将跳过这些码点继续生成。")
        except Exception:
            pass
        # filter out missing
        targets = [cp for cp in targets if cp not in set(missing)]

    total = len(targets)
    print(f"准备生成 {total} 个SVG 到 {out_dir}，使用 {args.workers} 个{'进程' if args.mode=='process' else '线程'}，字体目录: {args.fonts_dir}")

    # Worker function
    def render_one(cp: int) -> tuple[int, str | None]:
        fn = os.path.join(out_dir, f"{cp:04X}.svg")
        try:
            svg = renderer.render_svg(cp, size=args.size, padding=args.padding, fill=args.fill)
            # atomic-ish write
            tmp = fn + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                f.write(svg)
            os.replace(tmp, fn)
            return (cp, None)
        except Exception as e:
            return (cp, str(e))

    errors = 0
    # Per-thread progress bars: split targets into shards and assign to workers
    num_workers = min(args.workers, max(1, len(targets)))
    shards = shard_list(targets, num_workers)

    all_first_errs: List[str] = []

    if args.mode == 'thread':
        # Per-thread bars (existing behavior)
        def worker(shard_index: int, shard: List[int]) -> tuple[int, List[str]]:
            bar = None
            if _HAVE_TQDM:
                bar = tqdm(total=len(shard), desc=f"线程#{shard_index+1}", unit="svg", position=shard_index, leave=True)
            local_errors = 0
            first_errs: List[str] = []
            try:
                for cp in shard:
                    cp_, err = render_one(cp)
                    if err is not None:
                        local_errors += 1
                        if len(first_errs) < 5:
                            first_errs.append(f"U+{cp_:04X}: {err}")
                    if bar is not None:
                        bar.update(1)
            finally:
                if bar is not None:
                    bar.close()
            return local_errors, first_errs

        with ThreadPoolExecutor(max_workers=num_workers) as ex:
            futs = [ex.submit(worker, i, shard) for i, shard in enumerate(shards) if shard]
            for fut in as_completed(futs):
                ecount, ferrs = fut.result()
                errors += ecount
                all_first_errs.extend(ferrs)

    else:
        # Use a single global progress bar in parent
        pbar = tqdm(total=total, desc="渲染SVG(多进程)", unit="svg") if _HAVE_TQDM else None
        try:
            with ProcessPoolExecutor(max_workers=num_workers, initializer=_init_worker,
                                     initargs=(args.fonts_dir, args.size, args.padding, args.fill, out_dir)) as ex:
                futs = [ex.submit(_proc_worker, (i, shard)) for i, shard in enumerate(shards) if shard]
                for fut in as_completed(futs):
                    done_count, ecount, ferrs = fut.result()
                    errors += ecount
                    all_first_errs.extend(ferrs)
                    if pbar is not None:
                        pbar.update(done_count)
        finally:
            if pbar is not None:
                pbar.close()

    # Print a few sample errors across workers
    if all_first_errs:
        print("部分失败示例 (最多10条):")
        for line in all_first_errs[:10]:
            print("  ", line)

    print(f"完成: 生成 {total - errors} 个文件，失败 {errors} 个。输出目录: {out_dir}")
    return 0 if errors == 0 else 4


if __name__ == '__main__':
    raise SystemExit(main())
