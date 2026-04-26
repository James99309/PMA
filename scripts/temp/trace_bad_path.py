#!/usr/bin/env python3
"""Trace bad path #1 in base_station.svg — dump subpath bboxes to find outlier points."""
import sys, os, re
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)
from app.utils.dxf_converter import _svg_path_to_polylines

with open(os.path.join(ROOT, 'app/static/cad_symbols/base_station.svg')) as f: src = f.read()
path_ds = re.findall(r'd="([^"]+)"', src)
d = path_ds[0]

print(f'path #1 length = {len(d)} chars')
print(f'first 300: {d[:300]!r}')
print()

# Count commands
cmds = re.findall(r'[A-Za-z]', d)
from collections import Counter
print('command counts:', dict(Counter(cmds)))

def tr(x, y): return (x - 1598.46, y - 545.5)
subpaths = _svg_path_to_polylines(d, tr)
print(f'\n{len(subpaths)} subpaths:')
for i, sp in enumerate(subpaths):
    pts = sp['pts']
    if not pts:
        print(f'  #{i+1}  empty'); continue
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    print(f'  #{i+1}  {len(pts):4d} pts  closed={sp["closed"]:1}  '
          f'x=[{min(xs):7.1f}..{max(xs):7.1f}]  y=[{min(ys):7.1f}..{max(ys):7.1f}]')
