import os
from typing import List, Dict, Set
from fontTools.ttLib import TTFont, TTCollection

# 与 generate_hanzi_images.py 中保持一致（可按需调整）
FONT_PATHS: List[str] = [
    'C:/Windows/Fonts/HanaMinA.ttf',
    'C:/Windows/Fonts/HanaMinB.ttf',
    'C:/Windows/Fonts/SourceHanSansSC-Regular.otf',
    'C:/Windows/Fonts/SourceHanSerifSC-Regular.otf',
    'C:/Windows/Fonts/simhei.ttf',
    'C:/Windows/Fonts/msyh.ttc',
    'C:/Windows/Fonts/simsun.ttc',
]

CODEPOINT = 0x2F8F  # ⾏


def build_font_coverage(font_paths: List[str]) -> List[Dict]:
    candidates: List[Dict] = []
    for path in font_paths:
        if not os.path.exists(path):
            continue
        try:
            if path.lower().endswith('.ttc'):
                coll = TTCollection(path)
                for idx, font in enumerate(coll.fonts):
                    cps: Set[int] = set()
                    if 'cmap' in font:
                        for table in font['cmap'].tables:
                            cps.update(table.cmap.keys())
                    if cps:
                        candidates.append({'path': path, 'index': idx, 'codepoints': cps})
            else:
                font = TTFont(path, lazy=True)
                cps: Set[int] = set()
                if 'cmap' in font:
                    for table in font['cmap'].tables:
                        cps.update(table.cmap.keys())
                if cps:
                    candidates.append({'path': path, 'index': 0, 'codepoints': cps})
        except Exception as e:
            print(f"warn: cannot read {path}: {e}")
            continue
    return candidates


def select_font_for_codepoint(candidates: List[Dict], codepoint: int):
    for item in candidates:
        if codepoint in item['codepoints']:
            return item
    return None


def main():
    candidates = build_font_coverage(FONT_PATHS)
    print(f"font candidates: {len(candidates)}")

    item = select_font_for_codepoint(candidates, CODEPOINT)
    if item is None:
        print("result: MISSING — no font can render U+2F8F")
    else:
        print("result: COVERED")
        print(f"by: {item['path']} [face index {item['index']}]")

    img_path = os.path.join('images', f"{CODEPOINT:04X}.png")
    print(f"image exists: {os.path.exists(img_path)} -> {img_path}")

if __name__ == '__main__':
    main()
