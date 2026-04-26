#!/usr/bin/env python3
"""Render each path of an icon via both parsers and save side-by-side images to spot where the bug is."""
import sys, os, re
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)

from app.utils.dxf_converter import _svg_path_to_polylines
from svgelements import SVG, Path, Shape

f = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'app/static/cad_symbols/base_station.svg')
with open(f) as fp: src = fp.read()

# Read viewBox
vb_m = re.search(r'viewBox="([^"]+)"', src)
vb = [float(v) for v in vb_m.group(1).split()]
vb_x, vb_y, vb_w, vb_h = vb

# Extract all <path d="..."> strings
path_ds = re.findall(r'd="([^"]+)"', src)
print(f'icon has {len(path_ds)} paths')

# Rendering using _svg_path_to_polylines with identity transform (just offset to 0,0)
def mk_transform(viewbox_x, viewbox_y):
    def t(x, y):
        return (x - viewbox_x, y - viewbox_y)
    return t

tr = mk_transform(vb_x, vb_y)

# Parse via svgelements for reference
svg = SVG.parse(f, reify=True)
ref_shapes = [e for e in svg.elements() if isinstance(e, Shape)]

# Draw each path individually using our parser
img_size = 220
per_row = 6
rows = (len(path_ds) + per_row - 1) // per_row
canvas_w = per_row * img_size
canvas_h = rows * img_size + 20
canvas = Image.new('RGB', (canvas_w, canvas_h), (30, 41, 59))
draw = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 12)
except Exception:
    font = ImageFont.load_default()

scale = img_size / max(vb_w, vb_h) * 0.85
off_canvas = (img_size - vb_w * scale) / 2

for idx, d in enumerate(path_ds):
    row = idx // per_row
    col = idx % per_row
    ox = col * img_size + off_canvas
    oy = row * img_size + 20 + off_canvas

    subpaths = _svg_path_to_polylines(d, tr)
    seg_count = 0
    for sp in subpaths:
        pts = sp['pts']
        if len(pts) < 2: continue
        screen = [(ox + p[0]*scale, oy + p[1]*scale) for p in pts]
        color = (34, 197, 94) if sp['closed'] else (239, 68, 68)
        for k in range(len(screen)-1):
            draw.line([screen[k], screen[k+1]], fill=color, width=1)
            seg_count += 1
        if sp['closed'] and len(screen) >= 3:
            draw.line([screen[-1], screen[0]], fill=color, width=1)
    # label path index and segment count
    draw.rectangle([col*img_size, row*img_size+20, (col+1)*img_size, (row+1)*img_size+20],
                   outline=(71,85,105), width=1)
    draw.text((col*img_size + 6, row*img_size + 22), f'#{idx+1}  {seg_count} seg',
              fill=(250,204,21), font=font)

draw.text((6, 2), os.path.basename(f), fill=(250,204,21), font=font)
out = os.path.join(ROOT, 'scripts/temp/debug_icon_render_out.png')
canvas.save(out)
print(out)
