from __future__ import annotations

import os
import glob
from dataclasses import dataclass
from typing import List, Optional, Tuple

try:
    from fontTools.ttLib import TTFont, TTCollection
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.boundsPen import BoundsPen
except Exception:  # pragma: no cover
    TTFont = None  # type: ignore
    TTCollection = None  # type: ignore
    SVGPathPen = None  # type: ignore
    BoundsPen = None  # type: ignore


@dataclass
class FontFace:
    path: str
    ttc_index: Optional[int] = None  # for collections
    units_per_em: int = 1000
    codepoints: Optional[set[int]] = None


class SvgGlyphRenderer:
    def __init__(self, fonts_dir: str):
        self.fonts_dir = fonts_dir
        self.faces: List[FontFace] = []
        self._initialized = False

    def _list_font_paths(self) -> List[str]:
        patterns = ["*.ttf", "*.otf", "*.ttc", "*.otc"]
        paths: List[str] = []
        for pat in patterns:
            paths.extend(glob.glob(os.path.join(self.fonts_dir, pat)))
        return paths

    def _load_faces(self):
        if TTFont is None:
            raise RuntimeError("fonttools is not installed. Please install 'fonttools'.")
        paths = self._list_font_paths()
        faces: List[FontFace] = []
        for p in paths:
            ext = os.path.splitext(p)[1].lower()
            try:
                if ext in (".ttc", ".otc"):
                    coll = TTCollection(p, lazy=True)
                    for idx, f in enumerate(coll.fonts):
                        try:
                            cmap = f.getBestCmap() or {}
                            upm = int(f["head"].unitsPerEm)
                            faces.append(FontFace(path=p, ttc_index=idx, units_per_em=upm, codepoints=set(cmap.keys())))
                        except Exception:
                            continue
                else:
                    f = TTFont(p, lazy=True)
                    cmap = f.getBestCmap() or {}
                    upm = int(f["head"].unitsPerEm)
                    faces.append(FontFace(path=p, ttc_index=None, units_per_em=upm, codepoints=set(cmap.keys())))
            except Exception:
                # skip problematic fonts
                continue
        # prioritize by filename order
        self.faces = faces
        self._initialized = True

    def _open_font(self, face: FontFace):
        if face.ttc_index is not None:
            coll = TTCollection(face.path, lazy=True)
            return coll.fonts[face.ttc_index]
        return TTFont(face.path, lazy=True)

    def _select_face(self, cp: int) -> Optional[FontFace]:
        if not self._initialized:
            self._load_faces()
        for face in self.faces:
            if face.codepoints and cp in face.codepoints:
                return face
        return None

    def render_svg(self, cp: int, size: int = 128, padding: int = 8, fill: str = "#000") -> str:
        if TTFont is None:
            raise RuntimeError("fonttools is not installed. Please install 'fonttools'.")
        face = self._select_face(cp)
        if not face:
            raise FileNotFoundError(f"No font in '{self.fonts_dir}' covers U+{cp:04X}")

        font = self._open_font(face)
        cmap = font.getBestCmap() or {}
        glyph_name = cmap.get(cp)
        if not glyph_name:
            raise FileNotFoundError(f"Glyph not found for U+{cp:04X}")

        glyph_set = font.getGlyphSet()
        glyph = glyph_set[glyph_name]

        # Compute bounds
        bpen = BoundsPen(glyph_set)
        glyph.draw(bpen)
        bounds = bpen.bounds  # (xMin, yMin, xMax, yMax)
        if not bounds:
            # Empty glyph (e.g., space): draw a small placeholder box
            return f"""
<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' viewBox='0 0 {size} {size}'>
  <rect x='0' y='0' width='{size}' height='{size}' fill='white'/>
  <rect x='{size/2-8}' y='{size/2-8}' width='16' height='16' fill='{fill}'/>
</svg>"""

        xMin, yMin, xMax, yMax = bounds
        w = max(1.0, xMax - xMin)
        h = max(1.0, yMax - yMin)
        view = size
        pad = padding
        scale = min((view - 2 * pad) / w, (view - 2 * pad) / h)
        # Centering offsets (account for y-flip)
        dx = (view - scale * w) / 2.0
        dy = (view - scale * h) / 2.0

        # Path data
        spen = SVGPathPen(glyph_set)
        glyph.draw(spen)
        d = spen.getCommands()

        # Compose SVG: flip Y via scale(..., -...), translate to center
        # Transform order: move glyph to origin -> scale/flip -> move into view
        transform = f"translate({dx:.3f} {view - dy:.3f}) scale({scale:.6f} {-scale:.6f}) translate({-xMin:.3f} {-yMin:.3f})"

        svg = f"""
<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' viewBox='0 0 {view} {view}'>
  <rect x='0' y='0' width='{view}' height='{view}' fill='white'/>
  <path d='{d}' transform='{transform}' fill='{fill}'/>
</svg>"""
        return svg.strip()
