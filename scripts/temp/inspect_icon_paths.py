#!/usr/bin/env python3
"""Inspect each path in an icon SVG and report its bbox, area, point count."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../..'))
from svgelements import SVG, Path, Shape

f = sys.argv[1] if len(sys.argv) > 1 else 'app/static/cad_symbols/base_station.svg'
svg = SVG.parse(f, reify=True)
vb = svg.viewbox
print(f'file: {f}')
print(f'viewBox: {vb}')
shapes = []
for e in svg.elements():
    if isinstance(e, Shape):
        try:
            bb = e.bbox()
        except Exception:
            continue
        if bb is None:
            continue
        x0, y0, x1, y1 = bb
        w = x1 - x0
        h = y1 - y0
        diag = (w * w + h * h) ** 0.5
        shapes.append({
            'type': type(e).__name__,
            'bbox': bb,
            'w': w, 'h': h, 'diag': diag,
        })

# sort by diag desc
shapes.sort(key=lambda s: s['diag'], reverse=True)
# viewBox diagonal
vbd = ((vb.width) ** 2 + (vb.height) ** 2) ** 0.5
print(f'viewBox diag: {vbd:.1f}')
print(f'filter threshold at 8% = {vbd*0.08:.1f}')
print(f'filter threshold at 12% = {vbd*0.12:.1f}')
print()
print(f'{"#":>3}  {"type":12}  {"w":>7}  {"h":>7}  {"diag":>7}  {"diag%":>6}  bbox')
for i, s in enumerate(shapes, 1):
    pct = s['diag'] / vbd * 100
    print(f'{i:>3}  {s["type"]:12}  {s["w"]:7.1f}  {s["h"]:7.1f}  {s["diag"]:7.1f}  {pct:5.1f}%  {s["bbox"]}')
