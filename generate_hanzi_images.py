import os
import sys
import glob
import argparse
from typing import List, Dict, Tuple, Set
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont, TTCollection

# 生成汉字图片的范围（包含多个中文字符区间）
# 定义多个Unicode区间
unicode_ranges = [
    (0x2E80, 0x2EFF),  # CJK Radicals Supplement (包含 U+2F8F)
    (0x2F00, 0x2FDF),  # Kangxi Radicals
    (0x2FF0, 0x2FFF),  # Ideographic Description Characters
    (0x3000, 0x303F),  # CJK Symbols and Punctuation
    (0x3400, 0x4DBF),  # CJK Unified Ideographs Extension A
    (0x4E00, 0x9FFF),  # CJK Unified Ideographs (主要汉字区间)
]

parser = argparse.ArgumentParser(description='Generate Hanzi glyph images across Unicode ranges with multi-font fallback and strict coverage checks.')
parser.add_argument('--out', dest='output_dir', default='images', help='Output directory for images (default: images)')
parser.add_argument('--font-size', dest='font_size', type=int, default=64, help='Font size in pixels (default: 64)')
parser.add_argument('--allow-missing', action='store_true', help='Allow missing codepoints and skip them instead of failing')
args = parser.parse_args()

output_dir = args.output_dir
os.makedirs(output_dir, exist_ok=True)

"""
多字体支持说明：
- 可以在下方填写多个字体文件路径（ttf/otf/ttc）。
- 程序会优先使用第一个包含该码点字形的字体；若所有字体均不包含，则抛出错误。
- 这可避免字体缺字导致的“占位符/相同字形”问题。
"""

font_size = args.font_size

# 在此处按优先级列出字体路径（可按需调整/添加）。
FONT_PATHS: List[str] = [
    # 项目本地字体（可将字体放到 ./fonts/ 下）
    './fonts/*.ttf',
    './fonts/*.otf',
    './SourceHanSerifSC-Regular.otf',
    './msyh.ttc',

    # Windows 常见路径
    'C:/Windows/Fonts/HanaMinA.ttf',
    'C:/Windows/Fonts/HanaMinB.ttf',
    'C:/Windows/Fonts/SourceHanSansSC-Regular.otf',
    'C:/Windows/Fonts/SourceHanSerifSC-Regular.otf',
    'C:/Windows/Fonts/simhei.ttf',
    'C:/Windows/Fonts/msyh.ttc',
    'C:/Windows/Fonts/simsun.ttc',

    # Linux 常见路径（使用通配符递归搜索）
    '/usr/share/fonts/opentype/hanazono/HanaMinA.ttf',
    '/usr/share/fonts/opentype/hanazono/HanaMinB.ttf',
    '/usr/share/fonts/**/SourceHanSans*Regular*.otf',
    '/usr/share/fonts/**/SourceHanSerif*Regular*.otf',
    '/usr/share/fonts/**/NotoSansCJK*Regular*.otf',
    '/usr/share/fonts/**/NotoSansCJK*Regular*.ttc',
    '/usr/share/fonts/**/NotoSerifCJK*Regular*.otf',
    '/usr/share/fonts/**/NotoSerifCJK*Regular*.ttc',
    '/usr/share/fonts/**/HanaMin*.ttf',
]


def expand_font_paths(font_paths: List[str]) -> List[str]:
    """展开用户变量/环境变量，并处理通配符（glob）。去重且保序。"""
    expanded: List[str] = []
    for p in font_paths:
        p = os.path.expanduser(os.path.expandvars(p))
        if any(ch in p for ch in ('*', '?', '[')):
            expanded.extend(glob.glob(p, recursive=True))
        else:
            expanded.append(p)
    # 去重保序
    seen = set()
    result: List[str] = []
    for p in expanded:
        if p not in seen:
            seen.add(p)
            result.append(p)
    return result


def build_font_coverage(font_paths: List[str]) -> List[Dict]:
    """读取字体的cmap，构建每个字体可渲染的码点集合。
    支持ttf/otf/ttc。对于ttc，将展开为多个face，分别记录其覆盖。
    返回列表：[{ 'path': str, 'index': int, 'codepoints': set[int] }]
    """
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
            print(f"警告: 无法读取字体 {path}: {e}")
            continue
    return candidates


def select_font_for_codepoint(candidates: List[Dict], codepoint: int):
    """从候选字体中选择第一个覆盖该码点的字体条目。未找到则返回None。"""
    for item in candidates:
        if codepoint in item['codepoints']:
            return item
    return None

# 构建字体覆盖信息
_expanded_paths = expand_font_paths(FONT_PATHS)
print(f"候选字体路径（展开后）: {_expanded_paths.__len__()} 个")
candidates = build_font_coverage(_expanded_paths)
if not candidates:
    raise RuntimeError(
        '未找到可用字体或无法读取字体的cmap，请在 FONT_PATHS 中配置可用的字体文件路径。')

# 预加载PIL字体对象缓存： key=(path,index) -> ImageFont.FreeTypeFont
pil_font_cache: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}

missing_codes = []
total_to_generate = 0
for start, end in unicode_ranges:
    total_to_generate += (end - start + 1)

print(f"计划生成 {total_to_generate} 个字符，使用 {len(candidates)} 个字体候选。")

# 先检查覆盖以便在开始绘制之前就失败（避免生成半截）。
for start, end in unicode_ranges:
    for code in range(start, end + 1):
        if select_font_for_codepoint(candidates, code) is None:
            missing_codes.append(code)

if missing_codes:
    preview = ', '.join([f"U+{c:04X}" for c in missing_codes[:20]])
    if not args.allow_missing:
        raise RuntimeError(
            f"发现 {len(missing_codes)} 个码点在提供的字体中均无字形，例如: {preview}。\n"
            f"请安装/添加覆盖这些码点的字体到 FONT_PATHS 后重试，或使用 --allow-missing 跳过缺失码点。")
    else:
        report_path = os.path.join(output_dir, 'missing_codepoints.txt')
        with open(report_path, 'w', encoding='utf-8') as rf:
            rf.write('\n'.join([f"U+{c:04X}" for c in missing_codes]))
        print(f"警告: 有 {len(missing_codes)} 个码点缺失，已写入 {report_path}，将跳过这些码点继续生成。")

# 开始绘制
drawn = 0
for start, end in unicode_ranges:
    print(f"正在生成 U+{start:04X} 到 U+{end:04X} 的字符...")
    for code in range(start, end + 1):
        picker = select_font_for_codepoint(candidates, code)
        if picker is None:
            # 在 --allow-missing 模式下跳过
            if args.allow_missing:
                continue
            # 正常情况下不应到达此处，因为前置检查会阻止
            raise RuntimeError(f"内部错误：码点 U+{code:04X} 在渲染阶段未找到可用字体。")
        key = (picker['path'], picker['index'])
        if key not in pil_font_cache:
            pil_font_cache[key] = ImageFont.truetype(picker['path'], font_size, index=picker['index'])
        pil_font = pil_font_cache[key]

        char = chr(code)
        # 创建黑白图像
        img = Image.new('1', (font_size, font_size), color=1)  # '1'模式，1为白色
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), char, font=pil_font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((font_size - w) / 2, (font_size - h) / 2), char, font=pil_font, fill=0)
        filename = f'{code:04X}.png'
        img.save(os.path.join(output_dir, filename))
        drawn += 1

print(f"已完成绘制 {drawn}/{total_to_generate} 张字符图片。")
