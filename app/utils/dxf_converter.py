"""DXF/DWG 转换工具 — 用于系统图平面图背景导入与 DWG 导出

功能:
- render_dxf_to_png: 将 DXF 文件渲染为多分辨率 PNG（底图展示用）
- convert_dwg_to_dxf: 用 LibreDWG dwg2dxf 将 .dwg 转换为 .dxf
- combine_dxf_with_image: 将原始 DXF 实体 + 画布 PNG 合并为双图层 DXF
- convert_dxf_to_dwg: 用 LibreDWG dxf2dwg 将 .dxf 转换为 .dwg

依赖: ezdxf, matplotlib, LibreDWG (dwg2dxf / dxf2dwg CLI)
"""
import io
import os
import shutil
import subprocess
import logging

# Must be set before pyplot is imported anywhere — required for Flask worker threads on macOS
import matplotlib
matplotlib.use('Agg')

logger = logging.getLogger(__name__)


def _strip_dxf_objects(dxf_path, object_types, suffix='.clean.dxf'):
    """Remove specified DXF object types by line-level stripping.

    Strips any OBJECT section entry whose entity type (group 0) matches one of
    `object_types`. Used to work around LibreDWG (dwg2dxf/dxf2dwg 0.13.x) bugs
    with specific object types — e.g. SORTENTSTABLE (bad handle codes) and
    SPATIAL_FILTER (malformed Object improperly read on round-trip).

    Args:
        dxf_path: path to input DXF
        object_types: iterable of DXF object type names to strip (e.g. {'SORTENTSTABLE'})
        suffix: output file suffix

    Returns:
        Path to cleaned DXF if any stripping occurred, else the original path.
    """
    types_set = set(object_types)
    with open(dxf_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    if not any(t in content for t in types_set):
        return dxf_path

    lines = content.splitlines(keepends=True)
    out, i, skip = [], 0, False
    while i < len(lines):
        if (i + 1 < len(lines)
                and lines[i].strip() == '0'
                and lines[i + 1].strip() in types_set):
            skip = True
            i += 2
            continue
        if skip:
            if lines[i].strip() == '0':
                skip = False
                continue
            i += 1
            continue
        out.append(lines[i])
        i += 1

    clean_path = dxf_path + suffix
    with open(clean_path, 'w', encoding='utf-8') as f:
        f.writelines(out)
    logger.debug(f"Stripped {types_set} → {clean_path}")
    return clean_path


def _strip_sortentstable(dxf_path):
    """Legacy wrapper: strip SORTENTSTABLE objects (dwg2dxf 0.13.x bug)."""
    return _strip_dxf_objects(dxf_path, {'SORTENTSTABLE'})


import re as _re

# Layer name patterns that indicate equipment/overlay layers (not base floor plan)
_EQUIPMENT_LAYER_PATTERNS = [
    _re.compile(r'^0-EC-', _re.IGNORECASE),      # fire alarm / electrical equipment
    _re.compile(r'[一-鿿　-〿]'), # contains CJK characters (Chinese layer names)
    _re.compile(r'\$'),                            # xref external references
    _re.compile(r'^Drawing\d+', _re.IGNORECASE),  # temporary drawing layers
    _re.compile(r'I\.\s*LANTAI', _re.IGNORECASE), # Indonesian floor label xrefs
]


def _classify_layer(name):
    """Return 'equipment' if name matches equipment patterns, else 'base'."""
    for pat in _EQUIPMENT_LAYER_PATTERNS:
        if pat.search(name):
            return 'equipment'
    return 'base'


def extract_dxf_layers(dxf_path):
    """提取 DXF 图层列表，带自动分类（基础/设备）。

    Args:
        dxf_path: DXF 文件路径

    Returns:
        list of dicts: [{name, entity_count, category, selected}, ...]
        按 entity_count 降序排列，category 为 'base' 或 'equipment'
    """
    import ezdxf
    import ezdxf.recover

    clean_path = _strip_sortentstable(dxf_path)
    try:
        doc, _ = ezdxf.recover.readfile(clean_path)
    finally:
        if clean_path != dxf_path and os.path.exists(clean_path):
            os.remove(clean_path)

    # Count entities per layer from modelspace top-level
    layer_counts = {}
    for e in doc.modelspace():
        layer = e.dxf.get('layer', '0')
        layer_counts[layer] = layer_counts.get(layer, 0) + 1

    layers = []
    for layer in doc.layers:
        name = layer.dxf.name
        if name == 'DEFPOINTS':
            continue  # AutoCAD construction layer, never visible
        category = _classify_layer(name)
        layers.append({
            'name': name,
            'entity_count': layer_counts.get(name, 0),
            'category': category,
            'selected': category == 'base',
        })

    layers.sort(key=lambda x: (-x['entity_count'], x['name']))
    return layers


def render_dxf_to_png(dxf_path, output_dir, base_name, max_dims=None, include_layers=None):
    """将 DXF 文件渲染为多分辨率 PNG 文件

    Args:
        dxf_path: DXF 文件路径
        output_dir: 输出目录
        base_name: 输出文件名前缀
        max_dims: 分辨率列表，默认 [1000, 2000, 4000]
        include_layers: 要渲染的图层名称集合；None 表示渲染所有图层

    Returns:
        dict: {str(max_dim): {filename, width, height}}

    Raises:
        ImportError: matplotlib 未安装
        Exception: 渲染失败
    """
    import ezdxf
    import ezdxf.recover
    import matplotlib.pyplot as plt
    from PIL import Image

    if max_dims is None:
        max_dims = [1000, 2000, 4000]

    # Build a fast lookup set for layer filtering
    layer_set = set(include_layers) if include_layers is not None else None

    clean_path = _strip_sortentstable(dxf_path)
    try:
        doc, _ = ezdxf.recover.readfile(clean_path)
    finally:
        if clean_path != dxf_path and os.path.exists(clean_path):
            os.remove(clean_path)

    # Unfreeze all layers so geometry is visible
    for layer in doc.layers:
        if layer.is_frozen():
            layer.thaw()
        if layer.is_off():
            layer.on()

    msp = doc.modelspace()

    # Collect geometry by recursively expanding INSERT block references
    all_lines = []    # list of [(x,y)...]  (architectural/structural lines)
    all_dim_lines = [] # list of [(x,y)...] (dimension/axis extension lines, rendered lighter)
    all_circles = []  # list of (cx, cy, r)
    all_arcs = []     # list of (cx, cy, r, angle1_deg, angle2_deg)
    all_texts = []    # list of (x, y, text_str, height, rotation)
    all_hatches = []  # list of [(x,y)...] boundary polygons

    def _decode_cad_text(txt):
        """Convert CAD special character codes to Unicode."""
        import re
        txt = txt.replace('%%P', '±').replace('%%p', '±')
        txt = txt.replace('%%D', '°').replace('%%d', '°')
        txt = txt.replace('%%C', 'Ø').replace('%%c', 'Ø')
        return txt

    from ezdxf.math import Matrix44, Vec3
    _HA = {0:'left',1:'center',2:'right',3:'center',4:'center',5:'center'}
    _VA = {0:'bottom',1:'bottom',2:'center',3:'top'}
    _IDENTITY = Matrix44()

    def _pt(transform, p):
        """Transform a point (Vec3 or tuple) to world (x, y)."""
        if hasattr(p, 'x'):
            v = transform.transform(Vec3(p.x, p.y, getattr(p, 'z', 0) or 0))
        else:
            z = p[2] if len(p) > 2 else 0
            v = transform.transform(Vec3(p[0], p[1], z))
        return (v.x, v.y)

    def _scale_and_mirror(transform):
        """Return (uniform_scale, is_mirrored) for the given transform."""
        o = transform.transform(Vec3(0, 0, 0))
        x = transform.transform(Vec3(1, 0, 0))
        y = transform.transform(Vec3(0, 1, 0))
        dx = (x.x - o.x, x.y - o.y)
        dy = (y.x - o.x, y.y - o.y)
        sx = (dx[0]**2 + dx[1]**2) ** 0.5
        # 2D cross product: determinant sign
        cross = dx[0] * dy[1] - dx[1] * dy[0]
        return sx, cross < 0

    def _collect_attrib(attrib, transform):
        """Render an ATTRIB entity with the given accumulated transform."""
        try:
            halign = attrib.dxf.get('halign', 0)
            valign = attrib.dxf.get('valign', 0)
            if halign in (1, 2, 3, 4, 5):
                try:
                    pt_raw = attrib.dxf.align_point
                except Exception:
                    pt_raw = attrib.dxf.insert
            else:
                pt_raw = attrib.dxf.insert
            tx, ty = _pt(transform, pt_raw)
            txt = _decode_cad_text((attrib.dxf.text or '').strip())
            if not txt:
                return
            scale, mirrored = _scale_and_mirror(transform)
            h = attrib.dxf.get('height', 100) * scale
            rot = attrib.dxf.get('rotation', 0)
            if mirrored:
                rot = -rot
            all_texts.append((tx, ty, txt, h, rot,
                              _HA.get(halign, 'left'), _VA.get(valign, 'bottom')))
        except Exception:
            pass

    def _collect(entities, transform=_IDENTITY, _from_dim=False, _nested=False):
        for entity in entities:
            t = entity.dxftype()
            # Apply layer filter only at top level (not inside INSERT/DIMENSION expansions)
            if layer_set is not None and not _nested and not _from_dim:
                if entity.dxf.get('layer', '0') not in layer_set:
                    continue
            try:
                if t == 'LWPOLYLINE':
                    pts = [_pt(transform, (p[0], p[1], 0)) for p in entity.get_points()]
                    if entity.closed and pts:
                        pts.append(pts[0])
                    if len(pts) >= 2:
                        all_lines.append(pts)
                elif t == 'LINE':
                    s = _pt(transform, entity.dxf.start)
                    e = _pt(transform, entity.dxf.end)
                    if _from_dim:
                        all_dim_lines.append([s, e])
                    else:
                        all_lines.append([s, e])
                elif t == 'CIRCLE':
                    c = _pt(transform, entity.dxf.center)
                    scale, _ = _scale_and_mirror(transform)
                    r = abs(entity.dxf.radius * scale)
                    if r <= 5000:
                        all_circles.append((c[0], c[1], r))
                elif t == 'ARC':
                    c = _pt(transform, entity.dxf.center)
                    scale, mirrored = _scale_and_mirror(transform)
                    r = abs(entity.dxf.radius * scale)
                    a1 = entity.dxf.start_angle
                    a2 = entity.dxf.end_angle
                    if mirrored:
                        a1, a2 = -a2, -a1
                    all_arcs.append((c[0], c[1], r, a1, a2))
                elif t == 'SPLINE':
                    pts = [_pt(transform, (p[0], p[1], 0)) for p in entity.flattening(0.5)]
                    if len(pts) >= 2:
                        all_lines.append(pts)
                elif t in ('TEXT', 'ATTRIB'):
                    halign = entity.dxf.get('halign', 0)
                    valign = entity.dxf.get('valign', 0)
                    if halign in (1, 2, 3, 4, 5):
                        try:
                            pt_raw = entity.dxf.align_point
                        except Exception:
                            pt_raw = entity.dxf.insert
                    else:
                        pt_raw = entity.dxf.insert
                    tx, ty = _pt(transform, pt_raw)
                    txt = _decode_cad_text((entity.dxf.text or '').strip())
                    if txt:
                        scale, mirrored = _scale_and_mirror(transform)
                        h = entity.dxf.get('height', 100) * scale
                        rot = entity.dxf.get('rotation', 0)
                        if mirrored:
                            rot = -rot
                        all_texts.append((tx, ty, txt, h, rot,
                                          _HA.get(halign, 'left'), _VA.get(valign, 'bottom')))
                elif t == 'MTEXT':
                    import math
                    from ezdxf.tools.text import plain_mtext as _plain_mtext
                    ins = _pt(transform, entity.dxf.insert)
                    try:
                        txt = _decode_cad_text(entity.plain_mtext().strip())
                    except AttributeError:
                        raw = entity.dxf.get('text', '') or ''
                        txt = _decode_cad_text(_plain_mtext(raw).strip())
                    if txt:
                        scale, mirrored = _scale_and_mirror(transform)
                        h = entity.dxf.get('char_height', 100) * scale
                        td = entity.dxf.get('text_direction', None)
                        if td is not None:
                            try:
                                rot = math.degrees(math.atan2(float(td[1]), float(td[0])))
                            except (TypeError, IndexError):
                                try:
                                    rot = math.degrees(math.atan2(td.y, td.x))
                                except Exception:
                                    rot = entity.dxf.get('rotation', 0)
                        else:
                            rot = entity.dxf.get('rotation', 0)
                        if mirrored:
                            rot = -rot
                        ap = entity.dxf.get('attachment_point', 1)
                        mha = {1:'left',2:'center',3:'right',4:'left',5:'center',
                               6:'right',7:'left',8:'center',9:'right'}.get(ap, 'left')
                        mva = {1:'top',2:'top',3:'top',4:'center',5:'center',
                               6:'center',7:'bottom',8:'bottom',9:'bottom'}.get(ap, 'top')
                        all_texts.append((ins[0], ins[1], txt, h, rot, mha, mva))
                elif t == 'HATCH':
                    from ezdxf import path as _ezdxf_path
                    for path in entity.paths:
                        try:
                            p = _ezdxf_path.from_hatch_boundary_path(
                                path, ocs=entity.ocs())
                            pts = [_pt(transform, (pt.x, pt.y, 0))
                                   for pt in p.flattening(distance=50)]
                            if len(pts) >= 3:
                                all_hatches.append(pts)
                        except Exception:
                            pass
                elif t == 'DIMENSION':
                    # DIMENSION.virtual_entities() returns entities in the DIMENSION's
                    # containing space, so the same accumulated transform applies.
                    _collect(entity.virtual_entities(), transform,
                             _from_dim=True, _nested=True)
                elif t == 'INSERT':
                    # Manually compose transform: apply this INSERT's local matrix first,
                    # then the parent's accumulated transform. This fixes ezdxf's
                    # virtual_entities() bug with deeply-nested mirrored (negative-scale) blocks.
                    child_xform = entity.matrix44() @ transform
                    block = doc.blocks.get(entity.dxf.name)
                    if block is not None:
                        _collect(block, child_xform, _nested=True)
                    # ATTRIBs are stored in this INSERT's containing space (use parent transform)
                    for attrib in entity.attribs:
                        _collect_attrib(attrib, transform)
            except Exception:
                pass

    _collect(msp)

    if not all_lines and not all_circles and not all_arcs:
        raise ValueError('DXF 中未找到可渲染的几何实体')

    # Determine crop window.
    # When include_layers is set: use min/max of filtered entity coordinates.
    #   Layer filter already excludes sparse equipment — no percentile clipping needed.
    #   This ensures all selected-layer content (axis circles, titles) is fully visible.
    # When no layer filter: try $EXTMIN/$EXTMAX first, then 2-98% percentile as fallback.
    import numpy as np

    crop_x0 = crop_x1 = crop_y0 = crop_y1 = None

    # Collect coordinate samples from all rendered geometry
    all_xs, all_ys = [], []
    for seg in all_lines:
        for p in seg:
            all_xs.append(p[0]); all_ys.append(p[1])
    for seg in all_dim_lines:
        for p in seg:
            all_xs.append(p[0]); all_ys.append(p[1])
    for (cx, cy, r) in all_circles:
        all_xs += [cx - r, cx + r]; all_ys += [cy - r, cy + r]
    for (cx, cy, r, _, _) in all_arcs:
        all_xs += [cx - r, cx + r]; all_ys += [cy - r, cy + r]

    if layer_set is not None:
        # Layer-filtered render: use full min/max extent of selected-layer entities.
        # Percentile would clip the 3rd floor plan and bottom axis circles.
        if all_xs:
            x_lo, x_hi = float(min(all_xs)), float(max(all_xs))
            y_lo, y_hi = float(min(all_ys)), float(max(all_ys))
            pad_x = max((x_hi - x_lo) * 0.02, 1)
            pad_y = max((y_hi - y_lo) * 0.02, 1)
            crop_x0, crop_x1 = x_lo - pad_x, x_hi + pad_x
            crop_y0, crop_y1 = y_lo - pad_y, y_hi + pad_y
            logger.debug('crop: layer-filtered min/max (%.1f,%.1f)→(%.1f,%.1f)',
                         x_lo, y_lo, x_hi, y_hi)
    else:
        # No layer filter: try $EXTMIN/$EXTMAX first (CAD-recorded extents)
        try:
            extmin = doc.header.get('$EXTMIN')
            extmax = doc.header.get('$EXTMAX')
            if extmin and extmax:
                ex0, ey0 = float(extmin[0]), float(extmin[1])
                ex1, ey1 = float(extmax[0]), float(extmax[1])
                if ex1 > ex0 and ey1 > ey0:
                    pad_x = (ex1 - ex0) * 0.02
                    pad_y = (ey1 - ey0) * 0.02
                    crop_x0, crop_x1 = ex0 - pad_x, ex1 + pad_x
                    crop_y0, crop_y1 = ey0 - pad_y, ey1 + pad_y
                    logger.debug('crop: using $EXTMIN/$EXTMAX (%.1f,%.1f)→(%.1f,%.1f)',
                                 ex0, ey0, ex1, ey1)
        except Exception:
            pass

        if crop_x0 is None and all_xs:
            # Percentile fallback to filter sparse outliers when no layer filter
            x_lo = float(np.percentile(all_xs, 2))
            x_hi = float(np.percentile(all_xs, 98))
            y_lo = float(np.percentile(all_ys, 2))
            y_hi = float(np.percentile(all_ys, 98))
            pad_x = max((x_hi - x_lo) * 0.03, 1)
            pad_y = max((y_hi - y_lo) * 0.03, 1)
            crop_x0, crop_x1 = x_lo - pad_x, x_hi + pad_x
            crop_y0, crop_y1 = y_lo - pad_y, y_hi + pad_y
            logger.debug('crop: using percentile fallback')

    import matplotlib.patches as mpatches
    from matplotlib.collections import PatchCollection
    FIG_W, FIG_H = 50, 50
    RENDER_DPI = 300
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), facecolor='white')
    try:
        ax.set_facecolor('white')
        ax.set_aspect('equal')
        lw = 0.5

        # Render HATCH fills first (below lines) as light gray polygons
        if all_hatches:
            hatch_patches = [mpatches.Polygon(pts, closed=True) for pts in all_hatches]
            pc = PatchCollection(hatch_patches, facecolor='#d8d8d8',
                                 edgecolor='none', zorder=0)
            ax.add_collection(pc)

        # Dimension extension lines: lighter and thinner than architectural lines
        for line in all_dim_lines:
            xs = [p[0] for p in line]
            ys = [p[1] for p in line]
            ax.plot(xs, ys, color='#888888', linewidth=lw * 0.6)

        for line in all_lines:
            xs = [p[0] for p in line]
            ys = [p[1] for p in line]
            ax.plot(xs, ys, 'k-', linewidth=lw)
        for (cx, cy, r) in all_circles:
            ax.add_patch(mpatches.Circle((cx, cy), r, fill=False,
                                         edgecolor='black', linewidth=lw))
        for (cx, cy, r, a1, a2) in all_arcs:
            ax.add_patch(mpatches.Arc((cx, cy), 2*r, 2*r,
                                      angle=0, theta1=a1, theta2=a2,
                                      edgecolor='black', linewidth=lw))

        if crop_x0 is not None:
            ax.set_xlim(crop_x0, crop_x1)
            ax.set_ylim(crop_y0, crop_y1)
        else:
            ax.autoscale_view()

        # Calculate font size multiplier: model units → points
        x0, x1 = ax.get_xlim()
        data_width = max(x1 - x0, 1)
        pts_per_unit = (FIG_W * 72) / data_width  # 72 pt/inch
        for (tx, ty, txt, h, rot, ha, va) in all_texts:
            # Skip texts outside the visible window
            if crop_x0 is not None and not (crop_x0 <= tx <= crop_x1 and crop_y0 <= ty <= crop_y1):
                continue
            fs = max(3, min(h * pts_per_unit, 72))
            ax.text(tx, ty, txt, fontsize=fs,
                    color='black', rotation=rot,
                    ha=ha, va=va, clip_on=True)

        ax.axis('off')
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=RENDER_DPI, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        buf.seek(0)
    finally:
        plt.close(fig)

    base_img = Image.open(buf)
    orig_w, orig_h = base_img.size
    long_side = max(orig_w, orig_h)

    results = {}
    for max_dim in max_dims:
        scale = max_dim / long_side
        new_w = max(1, round(orig_w * scale))
        new_h = max(1, round(orig_h * scale))
        resized = base_img.resize((new_w, new_h), Image.LANCZOS)

        out_name = f"{base_name}_{max_dim}px.png"
        out_path = os.path.join(output_dir, out_name)
        resized.save(out_path, 'PNG')

        results[str(max_dim)] = {
            'filename': out_name,
            'width': new_w,
            'height': new_h,
        }

    return results


def convert_dwg_to_dxf(dwg_path, output_dir):
    """用 LibreDWG dwg2dxf 将 .dwg 文件转换为 .dxf

    Args:
        dwg_path: DWG 文件路径
        output_dir: 输出目录

    Returns:
        str: 生成的 DXF 文件路径

    Raises:
        FileNotFoundError: dwg2dxf 命令不可用
        RuntimeError: 转换失败
    """
    if not shutil.which('dwg2dxf'):
        raise FileNotFoundError(
            'dwg2dxf 命令不可用。请在 Docker 中安装 libredwg-tools。'
        )

    base = os.path.splitext(os.path.basename(dwg_path))[0]
    out_dxf = os.path.join(output_dir, f"{base}.dxf")

    result = subprocess.run(
        ['dwg2dxf', dwg_path, '-o', out_dxf],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise RuntimeError(f"dwg2dxf 转换失败: {result.stderr}")
    if not os.path.exists(out_dxf):
        raise RuntimeError('dwg2dxf 未生成输出文件')

    return out_dxf


def _compute_msp_bbox(msp, doc):
    """计算 modelspace 的实际 bbox，展开嵌套 INSERT 块并应用变换矩阵。

    返回有 extmin/extmax 属性的对象，或 None。
    ezdxf 自带的 bbox.extents 对深度嵌套的 INSERT 不够准确（fast=True 漏算，
    fast=False 对负缩放嵌套 INSERT 依然有坐标问题），所以这里手动遍历。
    """
    from ezdxf.math import Matrix44, Vec3

    xs, ys = [], []

    def _add(v):
        xs.append(v.x); ys.append(v.y)

    def _recurse(entities, transform):
        for e in entities:
            try:
                t = e.dxftype()
                if t == 'LINE':
                    _add(transform.transform(Vec3(e.dxf.start.x, e.dxf.start.y, 0)))
                    _add(transform.transform(Vec3(e.dxf.end.x, e.dxf.end.y, 0)))
                elif t == 'CIRCLE':
                    c = e.dxf.center; r = e.dxf.radius
                    for dx in (-r, r):
                        _add(transform.transform(Vec3(c.x + dx, c.y, 0)))
                        _add(transform.transform(Vec3(c.x, c.y + dx, 0)))
                elif t == 'ARC':
                    c = e.dxf.center; r = e.dxf.radius
                    for dx in (-r, r):
                        _add(transform.transform(Vec3(c.x + dx, c.y, 0)))
                        _add(transform.transform(Vec3(c.x, c.y + dx, 0)))
                elif t == 'LWPOLYLINE':
                    for p in e.get_points():
                        _add(transform.transform(Vec3(p[0], p[1], 0)))
                elif t in ('TEXT', 'ATTRIB', 'MTEXT'):
                    pt = e.dxf.insert
                    _add(transform.transform(Vec3(pt.x, pt.y, 0)))
                elif t == 'INSERT':
                    child = e.matrix44() @ transform
                    block = doc.blocks.get(e.dxf.name)
                    if block is not None:
                        _recurse(block, child)
            except Exception:
                pass

    _recurse(msp, Matrix44())

    if not xs:
        return None

    class _Ext:
        pass
    r = _Ext()
    r.has_data = True
    r.extmin = Vec3(min(xs), min(ys), 0)
    r.extmax = Vec3(max(xs), max(ys), 0)
    return r


def combine_dxf_with_image(original_dxf_path, canvas_png_path,
                            output_dxf_path, canvas_width_mm, canvas_height_mm):
    """在原始 DXF 基础上追加 SYSTEM_DESIGN 图层（画布 PNG），保持所有原始实体和资源引用

    策略：直接在原 DXF 文档上操作（不复制实体到空白文档），保留原有的材质、线型、文字
    样式、块引用等完整依赖，避免 dxf2dwg 转换时出现 "Object improperly read" 错误。

    Args:
        original_dxf_path: 原始 DXF 文件路径
        canvas_png_path: 画布截图 PNG 路径
        output_dxf_path: 输出 DXF 路径
        canvas_width_mm: 画布宽度（毫米），用于 IMAGE 实体定位
        canvas_height_mm: 画布高度（毫米）

    Returns:
        str: output_dxf_path
    """
    import ezdxf
    import ezdxf.recover

    clean_path = _strip_sortentstable(original_dxf_path)
    try:
        doc, _ = ezdxf.recover.readfile(clean_path)
    finally:
        if clean_path != original_dxf_path and os.path.exists(clean_path):
            os.remove(clean_path)
    msp = doc.modelspace()

    if 'SYSTEM_DESIGN' not in doc.layers:
        doc.layers.new('SYSTEM_DESIGN', dxfattribs={'color': 3})

    # 计算原始 DXF 内容的实际边界，让图像叠加与平面图对齐
    # 且设置正确的视口范围，使 CAD 软件打开时自动缩放到内容
    ext = _compute_msp_bbox(msp, doc)

    _PX_PER_MM = 96 / 25.4  # 96 DPI px/mm conversion

    # 使用相对路径让 DXF 能在任何位置找到 PNG（只要两个文件在同一目录）
    # 绝对路径会随服务器临时目录消失而失效
    png_rel = 'canvas_overlay.png'
    image_def = doc.add_image_def(
        filename=png_rel,
        size_in_pixel=(int(canvas_width_mm * _PX_PER_MM), int(canvas_height_mm * _PX_PER_MM))
    )

    # 图像放置位置：尽量与 modelspace 内容重合（保持画布宽高比）
    if ext is not None and getattr(ext, 'has_data', False):
        x_min, y_min = float(ext.extmin.x), float(ext.extmin.y)
        x_max, y_max = float(ext.extmax.x), float(ext.extmax.y)
        world_w = x_max - x_min
        world_h = y_max - y_min
        canvas_aspect = canvas_width_mm / canvas_height_mm if canvas_height_mm > 0 else 1
        world_aspect = world_w / world_h if world_h > 0 else 1
        if canvas_aspect >= world_aspect:
            img_w = world_w
            img_h = world_w / canvas_aspect
        else:
            img_h = world_h
            img_w = world_h * canvas_aspect
        # 图像居中于 modelspace bbox
        insert_x = x_min + (world_w - img_w) / 2
        insert_y = y_min + (world_h - img_h) / 2
        img_insert = (insert_x, insert_y, 0)
        img_size = (img_w, img_h)
    else:
        img_insert = (0, 0, 0)
        img_size = (canvas_width_mm, canvas_height_mm)

    msp.add_image(
        insert=img_insert,
        size_in_units=img_size,
        image_def=image_def,
        dxfattribs={'layer': 'SYSTEM_DESIGN'}
    )

    doc.saveas(output_dxf_path)

    # 更新 $EXTMIN/$EXTMAX 头变量，使 CAD 软件打开时 "Zoom to Extents" 正确定位。
    # ezdxf 在 saveas 时会按内部算法重新计算 extents（对嵌套镜像 INSERT 不准确），
    # 所以我们在保存后直接改写文件里的这几个 header 值。
    if ext is not None and getattr(ext, 'has_data', False):
        _patch_dxf_extents(output_dxf_path,
                            (float(ext.extmin.x), float(ext.extmin.y)),
                            (float(ext.extmax.x), float(ext.extmax.y)))

    return output_dxf_path


def _patch_dxf_extents(dxf_path, extmin, extmax):
    """在已保存的 DXF 文件中改写 $EXTMIN / $EXTMAX / $LIMMIN / $LIMMAX 的值。

    DXF header 中每个变量按以下 7 行格式存储：
        $EXTMIN\n 10\n<x>\n 20\n<y>\n 30\n<z>\n
    本函数用文本替换修正 X/Y 值（Z 保持 0），让 CAD 软件打开时能对准内容。
    """
    try:
        with open(dxf_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        logger.debug(f'读取 DXF 文件失败: {e}')
        return

    def _patch(var_name, x, y, has_z=True):
        for i, line in enumerate(lines):
            if line.strip() != var_name:
                continue
            # Expected: line i = var_name, i+1 = '10', i+2 = x_val, i+3 = '20',
            #           i+4 = y_val, optionally i+5 = '30', i+6 = z_val
            if (i + 4 < len(lines)
                    and lines[i + 1].strip() == '10'
                    and lines[i + 3].strip() == '20'):
                lines[i + 2] = f'{x}\n'
                lines[i + 4] = f'{y}\n'
                if has_z and i + 6 < len(lines) and lines[i + 5].strip() == '30':
                    lines[i + 6] = '0\n'
            return

    _patch('$EXTMIN', extmin[0], extmin[1], has_z=True)
    _patch('$EXTMAX', extmax[0], extmax[1], has_z=True)
    _patch('$LIMMIN', extmin[0], extmin[1], has_z=False)
    _patch('$LIMMAX', extmax[0], extmax[1], has_z=False)

    try:
        with open(dxf_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    except Exception as e:
        logger.debug(f'写入 DXF 文件失败: {e}')


def convert_dxf_to_dwg(dxf_path, output_dir):
    """用 LibreDWG dxf2dwg 将 .dxf 文件转换为 .dwg

    如果 dxf2dwg 不可用，直接返回 None（调用方降级为输出 DXF）。

    Args:
        dxf_path: DXF 文件路径
        output_dir: 输出目录

    Returns:
        str | None: 生成的 DWG 文件路径，或 None（工具不可用时）
    """
    # 优先使用 ODA File Converter（免费专业转换器，生成的 DWG 完全兼容 AutoCAD）
    oda_bin = shutil.which('ODAFileConverter') or shutil.which('TeighaFileConverter')
    if oda_bin:
        try:
            import tempfile
            in_dir = tempfile.mkdtemp(prefix='oda_in_')
            out_dir_oda = tempfile.mkdtemp(prefix='oda_out_')
            base = os.path.splitext(os.path.basename(dxf_path))[0]
            tmp_in = os.path.join(in_dir, f'{base}.dxf')
            shutil.copy2(dxf_path, tmp_in)
            # ODA: input_dir output_dir output_version output_type recurse audit
            subprocess.run(
                [oda_bin, in_dir, out_dir_oda, 'ACAD2018', 'DWG', '0', '1'],
                capture_output=True, text=True, timeout=120
            )
            oda_dwg = os.path.join(out_dir_oda, f'{base}.dwg')
            if os.path.exists(oda_dwg):
                final_dwg = os.path.join(output_dir, f'{base}.dwg')
                shutil.move(oda_dwg, final_dwg)
                shutil.rmtree(in_dir, ignore_errors=True)
                shutil.rmtree(out_dir_oda, ignore_errors=True)
                return final_dwg
            shutil.rmtree(in_dir, ignore_errors=True)
            shutil.rmtree(out_dir_oda, ignore_errors=True)
        except Exception as e:
            logger.warning(f'ODA 转换失败: {e}')

    # LibreDWG dxf2dwg 0.13.x 生成的 DWG 在 AutoCAD 等软件中无法正常打开
    # (AcDbMaterial / AcDbSpatialFilter / AcDbBlockTableRecord 等对象无法正确序列化)。
    # 在可靠的转换器可用前，直接降级输出 DXF — AutoCAD/BricsCAD/LibreCAD 都能原生
    # 打开 DXF，数据无损，用户可在 CAD 软件里用"另存为"得到 DWG。
    logger.info('ODA/可靠的 DWG 转换器不可用，输出 DXF 格式')
    return None


def _purge_objects_via_ezdxf(dxf_path, types_to_purge, output_dir):
    """用 ezdxf 从 OBJECTS 段删除指定类型的对象，保持引用完整。

    策略：
    1. 收集匹配类型的对象句柄
    2. 从其 owner dict 中解除引用
    3. 删除对象本身
    4. 运行 audit 清理其他悬空引用
    5. 保存到临时 DXF

    失败或无匹配时返回原路径。
    """
    import ezdxf
    import ezdxf.recover
    try:
        doc, _ = ezdxf.recover.readfile(dxf_path)
    except Exception as e:
        logger.warning(f'ezdxf 读取失败，跳过 purge: {e}')
        return dxf_path

    to_delete = []
    for obj in doc.objects:
        try:
            if obj.dxftype() in types_to_purge:
                to_delete.append(obj)
        except Exception:
            pass

    if not to_delete:
        return dxf_path

    for obj in to_delete:
        try:
            handle = obj.dxf.handle
            owner_handle = obj.dxf.get('owner', None)
            # Remove from owner dictionary's entries
            if owner_handle:
                owner = doc.entitydb.get(owner_handle)
                if owner is not None and hasattr(owner, 'discard'):
                    try:
                        owner.discard(handle)
                    except Exception:
                        pass
            # Delete the object itself
            doc.objects.delete_entity(obj)
        except Exception as e:
            logger.debug(f'删除 {obj.dxftype()} 时忽略错误: {e}')

    try:
        doc.audit()
    except Exception:
        pass

    clean_path = os.path.join(output_dir, os.path.basename(dxf_path) + '.purged.dxf')
    try:
        doc.saveas(clean_path)
        logger.debug(f'Purged {len(to_delete)} objects → {clean_path}')
        return clean_path
    except Exception as e:
        logger.warning(f'保存 purged DXF 失败，使用原文件: {e}')
        return dxf_path


def overlay_system_design_on_dxf(original_dxf_path, output_path, elements):
    """在原 DXF 上追加 SYSTEM_DESIGN 图层（设备/连线/区域/覆盖圆），不改动原实体。

    将前端结构化的 nodes/routes/areas 数据转换为原生 DXF 矢量实体
    （CIRCLE / LWPOLYLINE / TEXT），加到新图层上。保持原 DXF 的所有实体不变。

    Args:
        original_dxf_path: 原始 DXF 路径（图层选择导入后保存的文件）
        output_path: 输出 DXF 路径
        elements: dict，包含：
            bg_width_px, bg_height_px: 背景 PNG 像素尺寸（用于坐标换算）
            offset_x, offset_y: 背景在编辑器里的偏移（通常 0）
            nodes: [{id, x, y, w, h, label, model, iconKey, rotation, qty, coverage}]
            routes: [{id, sourceNodeId, targetNodeId, waypoints, label, dash, cableType}]
            areas: [{id, x, y, width, height, label}]

    Returns:
        str: output_path
    """
    import ezdxf
    import ezdxf.recover

    clean_path = _strip_sortentstable(original_dxf_path)
    try:
        doc, _ = ezdxf.recover.readfile(clean_path)
    finally:
        if clean_path != original_dxf_path and os.path.exists(clean_path):
            try:
                os.remove(clean_path)
            except OSError:
                pass
    msp = doc.modelspace()

    # 1. 打开所有图层（dwg2dxf 转换得到的原 DXF 里图层默认是 off 状态，
    #    在 CAD 软件里默认不可见 —— 用户会看到空白）
    for layer in doc.layers:
        try:
            if layer.is_frozen():
                layer.thaw()
            if layer.is_off():
                layer.on()
        except Exception:
            pass

    # 2. 文字样式：优先用原 DXF 已有的 ARIAL25/ARIAL40 样式（Windows/Mac CAD 软件都容易找到 arial.ttf）；
    #    配合 bigfont=gbcbig.shx（CAD 行业标准简体中文 SHX 字体）处理中文/CJK。
    _TEXT_STYLE = 'SYSDESIGN_TEXT'
    if _TEXT_STYLE not in doc.styles:
        try:
            doc.styles.new(_TEXT_STYLE, dxfattribs={
                'font': 'arial.ttf',       # 主字体（拉丁字符）
                'bigfont': 'gbcbig.shx',   # 副字体（简体中文）
            })
        except Exception:
            pass

    # 3. 新建图层（都带 "系统图_" 前缀，方便 CAD 里单独切换显示/隐藏）
    layer_defs = {
        '系统图_设备': 3,           # 绿色 —— 设备图标
        '系统图_连线': 3,           # 绿色 —— 电缆走线
        '系统图_标签': 2,           # 黄色 —— 文字标签
        '系统图_覆盖_强信号': 3,    # 绿色 —— 内圈 -65 dBm 强覆盖区（实线）
        '系统图_覆盖_上行边界': 92, # 浅绿色 —— 外圈 -85 dBm 上行边界（虚线）
        '系统图_区域': 5,           # 蓝色 —— 区域/房间框
    }
    for lname, color in layer_defs.items():
        if lname not in doc.layers:
            doc.layers.new(lname, dxfattribs={'color': color})

    # 确保 DASHED 线型存在（供外圈覆盖圆使用）
    # pattern 单位是绘图单位(mm)，用小值 + entity ltscale 来适配不同比例
    if 'DASHED' not in doc.linetypes:
        try:
            doc.linetypes.add('DASHED', pattern=[0.5, -0.25],
                               description='Dashed _ _ _ _ _')
        except Exception:
            pass

    L_DEVICE = '系统图_设备'
    L_ROUTE = '系统图_连线'
    L_LABEL = '系统图_标签'
    L_COVERAGE_INNER = '系统图_覆盖_强信号'
    L_COVERAGE_OUTER = '系统图_覆盖_上行边界'
    L_AREA = '系统图_区域'

    # 2. 通过原 DXF bbox + 背景 PNG 尺寸建立编辑器像素 → 世界坐标的映射
    ext = _compute_msp_bbox(msp, doc)
    if ext is None or not getattr(ext, 'has_data', False):
        raise RuntimeError('无法确定 DXF 坐标范围，请重新导入底图')

    bg_w = float(elements.get('bg_width_px', 0)) or 1
    bg_h = float(elements.get('bg_height_px', 0)) or 1
    off_x = float(elements.get('offset_x', 0))
    off_y = float(elements.get('offset_y', 0))
    x_min, y_min = float(ext.extmin.x), float(ext.extmin.y)
    x_max, y_max = float(ext.extmax.x), float(ext.extmax.y)
    world_w = x_max - x_min
    world_h = y_max - y_min

    def to_world(cx, cy):
        """编辑器画布像素 → DXF 世界坐标（mm）。Y 翻转。"""
        norm_x = (cx - off_x) / bg_w
        norm_y = (cy - off_y) / bg_h
        return (x_min + norm_x * world_w,
                y_max - norm_y * world_h)

    # 1 编辑器 px 对应多少世界毫米（用于缩放节点大小、字高等）
    px_to_mm_x = world_w / bg_w
    px_to_mm_y = world_h / bg_h
    px_to_mm = (px_to_mm_x + px_to_mm_y) / 2

    # 3. 建 node_id → (world_x, world_y) 字典（连线会用）
    node_world_pos = {}
    node_half_h_mm = {}
    node_half_w_mm = {}

    def _add_text_unicode(txt, x, y, height, layer, align_center=True):
        """把文字转为 LWPOLYLINE 矢量轮廓（text2path），彻底摆脱 CAD 阅读器字体依赖。

        对比直接用 TEXT 实体：
        - 优点：完美渲染中文/Unicode；任何 CAD 软件无字体也能看到
        - 缺点：不能在 CAD 里编辑文字内容（但仍可选中/删除）
        """
        if not txt or not txt.strip():
            return
        try:
            from ezdxf.addons import text2path
            from ezdxf.fonts.fonts import FontFace

            # 用系统里能渲染 CJK 的字体（会自动 fallback）
            font_face = FontFace(family='Arial Unicode MS')
            paths = text2path.make_paths_from_str(
                txt.strip(), font=font_face, size=height,
            )
            if not paths:
                return

            # text2path 返回的 path 以 (0,0) 为基线左端；需要平移到 (x,y)
            # align_center=True 时先计算总宽度居中
            all_x, all_y = [], []
            polylines = []
            for p in paths:
                pts = [(v.x, v.y) for v in p.flattening(distance=height * 0.05)]
                polylines.append(pts)
                for px, py in pts:
                    all_x.append(px); all_y.append(py)

            if not all_x:
                return

            # 默认 left-baseline。居中对齐时把 bbox 中心对齐到 (x, y)
            if align_center:
                ox = x - (min(all_x) + max(all_x)) / 2
                oy = y - (min(all_y) + max(all_y)) / 2
            else:
                ox = x - min(all_x)
                oy = y - min(all_y)

            # 用 HATCH 实心填充 glyph，避免镂空外轮廓。
            # style=0 (Normal/Nested) = 奇偶绕线 → 中文"口/田/回"与拉丁"O/A"的内孔都会正确保留
            hatch = msp.add_hatch(color=256, dxfattribs={'layer': layer})
            hatch.set_solid_fill(style=0)
            added = 0
            for pts in polylines:
                if len(pts) >= 3:
                    translated = [(px + ox, py + oy) for px, py in pts]
                    hatch.paths.add_polyline_path(translated, is_closed=True)
                    added += 1
            if added == 0:
                # 没有可填充的闭合轮廓 → 移除空 hatch
                msp.delete_entity(hatch)
        except Exception as e:
            logger.debug(f'text2path 失败，退回 TEXT 实体: {e}')
            try:
                t = msp.add_text(txt, dxfattribs={
                    'layer': layer, 'height': height,
                    'style': _TEXT_STYLE, 'insert': (x, y, 0),
                })
                if align_center:
                    try: t.set_placement((x, y), align=_TEXT_CENTER)
                    except Exception: pass
            except Exception:
                pass

    def _add_node_icon(node, cx, cy, size):
        """用节点实际的 SVG iconData 画矢量图标。失败时回退到基础形状。

        iconData: {viewBox: [x,y,w,h], paths: [{d: '...'}, ...]}
        编辑器的 Y 轴朝下，CAD 朝上 —— 转换时做 Y 翻转。
        """
        icon_data = node.get('iconData')
        if icon_data and isinstance(icon_data, dict):
            vb = icon_data.get('viewBox') or [0, 0, 64, 64]
            try:
                vb_x, vb_y, vb_w, vb_h = float(vb[0]), float(vb[1]), float(vb[2]), float(vb[3])
                if vb_w > 0 and vb_h > 0:
                    # 缩放：把 viewBox 统一映射到目标 size（保持宽高比）
                    s = size / max(vb_w, vb_h)
                    # viewBox 左上角 (vb_x, vb_y) 对应图标左上角 (cx - vb_w*s/2, cy + vb_h*s/2)
                    # 编辑器 Y 向下，CAD Y 向上 —— 要做 Y 翻转
                    offset_x = cx - vb_w * s / 2 - vb_x * s
                    offset_y_top = cy + vb_h * s / 2 - vb_y * s  # 编辑器 y=0 对应 cy + vb_h*s/2

                    def pt_transform(px, py):
                        wx = offset_x + px * s
                        wy = offset_y_top - py * s  # Y 翻转
                        return (wx, wy)

                    # 过滤阈值：sub-path bbox 对角 < icon 尺寸 * 8% 的细节路径跳过
                    # 原因：设计师原图含大量细小装饰（螺丝/logo/EVERTAC 文字/充电槽位），
                    # 在 CAD 小尺寸下转成 lwpolyline 线框会互相穿插成乱线团
                    min_extent = size * 0.08
                    rendered = False
                    for path in icon_data.get('paths') or []:
                        d = path.get('d', '')
                        if not d:
                            continue
                        subpaths = _svg_path_to_polylines(d, pt_transform)
                        for sub in subpaths:
                            pts = sub['pts']
                            if len(pts) < 2:
                                continue
                            xs = [p[0] for p in pts]
                            ys = [p[1] for p in pts]
                            bw = max(xs) - min(xs)
                            bh = max(ys) - min(ys)
                            if (bw * bw + bh * bh) ** 0.5 < min_extent:
                                continue
                            msp.add_lwpolyline(pts,
                                               close=sub['closed'],
                                               dxfattribs={'layer': L_DEVICE})
                            rendered = True
                    if rendered:
                        return  # 已用真实 SVG 绘制，不做回退
            except Exception as e:
                logger.debug(f'SVG 图标解析失败 → 回退简化形状: {e}')

        # 回退：根据 iconKey 画简化几何
        icon_key = node.get('iconKey') or ''
        half = size / 2
        if icon_key in ('antenna_indoor', 'antenna_outdoor', 'antenna'):
            h = size * 0.866
            msp.add_lwpolyline([(cx, cy + h*2/3),
                                (cx - half, cy - h/3),
                                (cx + half, cy - h/3)],
                                close=True, dxfattribs={'layer': L_DEVICE})
        else:
            msp.add_circle((cx, cy), half, dxfattribs={'layer': L_DEVICE})

    # 4. 绘制节点
    for node in elements.get('nodes', []):
        try:
            wx, wy = to_world(float(node.get('x', 0)), float(node.get('y', 0)))
            half_w = float(node.get('w', 32)) / 2 * px_to_mm_x
            half_h = float(node.get('h', 32)) / 2 * px_to_mm_y
            node_world_pos[node.get('id')] = (wx, wy)
            node_half_h_mm[node.get('id')] = half_h
            node_half_w_mm[node.get('id')] = half_w

            # 设备符号（优先用节点的 SVG iconData 画矢量图标）
            size = max(half_w, half_h) * 2
            _add_node_icon(node, wx, wy, size)

            # 节点标签
            label_lines = []
            name = (node.get('label') or node.get('name') or '').strip()
            model = (node.get('model') or '').strip()
            if name:
                label_lines.append(name)
            if model and model != name:
                label_lines.append(model)
            text_h = 11 * px_to_mm
            line_gap = text_h * 0.4
            label_y = wy - half_h - text_h
            for idx, line in enumerate(label_lines):
                ly = label_y - idx * (text_h + line_gap)
                _add_text_unicode(line, wx, ly, text_h, L_LABEL)

            # 数量徽章
            qty = int(node.get('qty', 1) or 1)
            if qty > 1:
                _add_text_unicode(f'x{qty}', wx + half_w, wy + half_h,
                                   9 * px_to_mm, L_LABEL, align_center=False)

            # 覆盖圆（半径单位是米，需转为 mm）
            # 内圈 -65 dBm 强信号区：实线绿色；外圈 -85 dBm 上行边界：虚线浅绿
            cov = node.get('coverage')
            if cov and cov.get('radii'):
                visible = cov.get('visible') or [True, True]
                raw_radii = cov['radii'][:2]
                # 解析为 (index, r_mm) 并过滤无效值
                valid = []
                for i, radius_m in enumerate(raw_radii):
                    try:
                        r_m = float(radius_m)
                    except (TypeError, ValueError):
                        continue
                    if i < len(visible) and not visible[i]:
                        continue
                    r_mm = r_m * 1000
                    if r_mm > 0:
                        valid.append((i, r_mm))
                # 按半径大小排序：小的=内圈，大的=外圈
                valid.sort(key=lambda t: t[1])
                cov_labels = [('-65 dBm', L_COVERAGE_INNER), ('-85 dBm', L_COVERAGE_OUTER)]
                for ring_idx, (orig_i, r_mm) in enumerate(valid):
                    dBm_label, layer_name = cov_labels[ring_idx] if ring_idx < 2 else ('-85 dBm', L_COVERAGE_OUTER)
                    circle = msp.add_circle((wx, wy), r_mm, dxfattribs={'layer': layer_name})
                    # 外圈：虚线 + 灰色（color 9 = 浅灰），ltscale 按圆半径缩放确保虚线可见
                    if layer_name == L_COVERAGE_OUTER:
                        try:
                            circle.dxf.linetype = 'DASHED'
                            circle.dxf.ltscale = max(r_mm / 30.0, 1.0)
                            circle.dxf.color = 9  # 浅灰色
                        except Exception:
                            pass
                    # 圆顶标签（纯 ASCII，用普通 TEXT 实体，避免 text2path 的空心轮廓）
                    try:
                        r_label_m = round(r_mm / 1000, 1)
                        r_label_m = int(r_label_m) if r_label_m == int(r_label_m) else r_label_m
                        cov_text = f'{dBm_label} R={r_label_m}m'
                        label_h = max(9 * px_to_mm, 200)
                        label_y = wy + r_mm + label_h * 0.6
                        t = msp.add_text(cov_text, dxfattribs={
                            'layer': L_LABEL,
                            'height': label_h,
                            'style': _TEXT_STYLE,
                        })
                        if hasattr(t, 'set_placement'):
                            t.set_placement((wx, label_y), align=_TEXT_CENTER)
                        else:
                            t.dxf.insert = (wx, label_y, 0)
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f'绘制节点 {node.get("id")} 失败: {e}')

    # 5. 绘制连线：严格匹配浏览器的端口锚点 + routeMode 逻辑
    def _port_anchor(cx, cy, half_w, port, gap_mm):
        """port = top/right/bottom/left/top-left/top-right/bottom-left/bottom-right。
        浏览器 getPortPos 用 R = node.w/2 + 8px，所有 port 都用同一个 R（以 w 为基准）。
        返回 CAD 世界坐标（Y 已翻转过）。"""
        R = half_w + gap_mm
        D = R * 0.7071
        # 浏览器 Y 朝下，CAD Y 朝上 → 上下方向反转
        if port == 'top':          return (cx, cy + R)
        if port == 'bottom':       return (cx, cy - R)
        if port == 'right':        return (cx + R, cy)
        if port == 'left':         return (cx - R, cy)
        if port == 'top-left':     return (cx - D, cy + D)
        if port == 'top-right':    return (cx + D, cy + D)
        if port == 'bottom-left':  return (cx - D, cy - D)
        if port == 'bottom-right': return (cx + D, cy - D)
        # 未指定 port → 回退到中心
        return (cx, cy)

    def _snap_direction_to_port(cx, cy, half_w, half_h, tx, ty):
        """没有 port 信息时按朝向吸附到 4 主方向之一，返回 port 名。"""
        dx = tx - cx; dy = ty - cy
        if half_w <= 0: half_w = 1
        if half_h <= 0: half_h = 1
        if abs(dx) * half_h >= abs(dy) * half_w:
            return 'right' if dx >= 0 else 'left'
        # CAD Y 向上：dy > 0 → 目标在上方 → top 端口
        return 'top' if dy >= 0 else 'bottom'

    # midPos 在一个轴上（editor 像素）转世界坐标（仅该轴有效）
    def _midpos_to_world(mid_pos, is_horizontal):
        if mid_pos is None:
            return None
        try:
            v = float(mid_pos)
        except (TypeError, ValueError):
            return None
        if is_horizontal:
            return x_min + (v - off_x) / bg_w * world_w  # midX
        return y_max - (v - off_y) / bg_h * world_h      # midY (Y 翻转)

    port_gap_mm = 8 * px_to_mm  # 浏览器 +8 px 端口间距

    for route in elements.get('routes', []):
        try:
            src_id = route.get('sourceNodeId')
            tgt_id = route.get('targetNodeId')
            s_center = node_world_pos.get(src_id)
            t_center = node_world_pos.get(tgt_id)
            if not s_center or not t_center:
                continue

            # 解析 waypoints
            waypoints = []
            for wp in route.get('waypoints') or []:
                try:
                    waypoints.append(to_world(float(wp['x']), float(wp['y'])))
                except (KeyError, TypeError, ValueError):
                    continue

            src_port = route.get('sourcePort')
            tgt_port = route.get('targetPort')
            s_hw = node_half_w_mm.get(src_id, 0)
            s_hh = node_half_h_mm.get(src_id, 0)
            t_hw = node_half_w_mm.get(tgt_id, 0)
            t_hh = node_half_h_mm.get(tgt_id, 0)

            # 若没有 port 数据，按朝向推算
            if not src_port:
                ref = waypoints[0] if waypoints else t_center
                src_port = _snap_direction_to_port(s_center[0], s_center[1], s_hw, s_hh, ref[0], ref[1])
            if not tgt_port:
                ref = waypoints[-1] if waypoints else s_center
                tgt_port = _snap_direction_to_port(t_center[0], t_center[1], t_hw, t_hh, ref[0], ref[1])

            s_anchor = _port_anchor(s_center[0], s_center[1], s_hw, src_port, port_gap_mm)
            t_anchor = _port_anchor(t_center[0], t_center[1], t_hw, tgt_port, port_gap_mm)

            # 生成 pts —— 严格匹配浏览器 buildEdgePath 逻辑
            route_mode = (route.get('routeMode') or 'bezier').lower()
            is_h_port = src_port in ('left', 'right', 'top-left', 'top-right', 'bottom-left', 'bottom-right')

            if waypoints:
                # 有显式 waypoints → 起点 + waypoints + 终点 的折线（90° 直角路径，不做 spline 平滑）
                pts = [s_anchor] + waypoints + [t_anchor]
                msp.add_lwpolyline(pts, dxfattribs={'layer': L_ROUTE})
            elif route_mode == 'straight':
                pts = [s_anchor, t_anchor]
                msp.add_lwpolyline(pts, dxfattribs={'layer': L_ROUTE})
            elif route_mode == 'ortho2':
                # L 形 1 个拐角
                corner = (t_anchor[0], s_anchor[1]) if is_h_port else (s_anchor[0], t_anchor[1])
                pts = [s_anchor, corner, t_anchor]
                msp.add_lwpolyline(pts, dxfattribs={'layer': L_ROUTE})
            elif route_mode == 'ortho3':
                # S 形 2 个拐角
                mid = _midpos_to_world(route.get('midPos'), is_h_port)
                if is_h_port:
                    mid_x = mid if mid is not None else (s_anchor[0] + t_anchor[0]) / 2
                    pts = [s_anchor, (mid_x, s_anchor[1]), (mid_x, t_anchor[1]), t_anchor]
                else:
                    mid_y = mid if mid is not None else (s_anchor[1] + t_anchor[1]) / 2
                    pts = [s_anchor, (s_anchor[0], mid_y), (t_anchor[0], mid_y), t_anchor]
                msp.add_lwpolyline(pts, dxfattribs={'layer': L_ROUTE})
            else:
                # bezier 或未知模式 → 用端口方向生成控制点，导出三次贝塞尔 spline
                def _port_dir_world(port):
                    tbl = {
                        'top':    (0, 1), 'bottom': (0, -1),
                        'right':  (1, 0), 'left':   (-1, 0),
                        'top-left':    (-0.707, 0.707), 'top-right':    (0.707, 0.707),
                        'bottom-left': (-0.707, -0.707),'bottom-right': (0.707, -0.707),
                    }
                    return tbl.get(port or '', (0, 0))
                sd = _port_dir_world(src_port); td = _port_dir_world(tgt_port)
                tension = max(40 * px_to_mm,
                              min(abs(t_anchor[0] - s_anchor[0]),
                                  abs(t_anchor[1] - s_anchor[1]),
                                  120 * px_to_mm) * 0.5)
                cp1 = (s_anchor[0] + sd[0] * tension, s_anchor[1] + sd[1] * tension)
                cp2 = (t_anchor[0] + td[0] * tension, t_anchor[1] + td[1] * tension)
                try:
                    msp.add_spline(control_points=[s_anchor, cp1, cp2, t_anchor],
                                   degree=3,
                                   dxfattribs={'layer': L_ROUTE})
                except Exception:
                    msp.add_lwpolyline([s_anchor, t_anchor], dxfattribs={'layer': L_ROUTE})
                # 标签定位：用 4 个控制点中段
                pts = [s_anchor, cp1, cp2, t_anchor]

            # 连线标签：放在中段
            lbl = (route.get('label') or '').strip()
            if lbl and len(pts) >= 2:
                mid_idx = len(pts) // 2
                a, b = pts[mid_idx - 1], pts[mid_idx]
                mx = (a[0] + b[0]) / 2
                my = (a[1] + b[1]) / 2
                _add_text_unicode(lbl, mx, my, 9 * px_to_mm, L_LABEL,
                                   align_center=False)
        except Exception as e:
            logger.warning(f'绘制连线 {route.get("id")} 失败: {e}')

    # 6. 绘制区域框：闭合 LWPOLYLINE + 标题
    for a in elements.get('areas', []):
        try:
            x = float(a.get('x', 0)); y = float(a.get('y', 0))
            w = float(a.get('width', 0)); h = float(a.get('height', 0))
            if w <= 0 or h <= 0:
                continue
            corners = [to_world(x, y), to_world(x + w, y),
                       to_world(x + w, y + h), to_world(x, y + h)]
            msp.add_lwpolyline(corners, close=True,
                                dxfattribs={'layer': L_AREA})
            lbl = (a.get('label') or '').strip()
            if lbl:
                lx, ly = to_world(x + w / 2, y + 12)
                _add_text_unicode(lbl, lx, ly, 11 * px_to_mm, L_LABEL)
        except Exception as e:
            logger.warning(f'绘制区域 {a.get("id")} 失败: {e}')

    # 7. 保存
    doc.saveas(output_path)

    # 8. 修正 $EXTMIN/$EXTMAX —— ezdxf 在 saveas 时会错误重算 header 变量，
    # 导致 CAD 软件打开时 "Zoom to Extents" 定位到空白区。
    # 用 bbox + 新加实体的范围一起作为最终范围。
    new_xs, new_ys = [], []
    for node in elements.get('nodes', []):
        try:
            wx, wy = to_world(float(node.get('x', 0)), float(node.get('y', 0)))
            new_xs.append(wx); new_ys.append(wy)
        except Exception:
            pass
    for a in elements.get('areas', []):
        try:
            new_xs.append(to_world(float(a.get('x', 0)), float(a.get('y', 0)))[0])
            new_ys.append(to_world(float(a.get('x', 0)), float(a.get('y', 0)))[1])
        except Exception:
            pass
    final_xmin = min([x_min] + new_xs)
    final_ymin = min([y_min] + new_ys)
    final_xmax = max([x_max] + new_xs)
    final_ymax = max([y_max] + new_ys)
    _patch_dxf_extents(output_path,
                        (final_xmin, final_ymin),
                        (final_xmax, final_ymax))

    return output_path


# TextEntityAlignment 在 ezdxf 不同版本位置不同，做一个兼容导入
try:
    from ezdxf.enums import TextEntityAlignment as _TEA
    _TEXT_CENTER = _TEA.MIDDLE_CENTER
except Exception:
    try:
        from ezdxf.lldxf import const as _LLDXF
        _TEXT_CENTER = getattr(_LLDXF, 'MTEXT_MIDDLE_CENTER', 'MIDDLE_CENTER')
    except Exception:
        _TEXT_CENTER = 'MIDDLE_CENTER'


# SVG path 解析：支持 M/L/H/V/C/Q/A/Z (大小写) —— 覆盖内置图标库的常见用法
_SVG_TOKEN = _re.compile(r'([MmLlHhVvCcQqSsTtAaZz])|(-?\d+\.?\d*(?:[eE][+-]?\d+)?)')


def _arc_endpoint_to_polyline(x1, y1, rx, ry, phi, large_arc, sweep, x2, y2, segs=20):
    """SVG 椭圆弧的 endpoint 形式 → 采样成折线。

    参考: https://www.w3.org/TR/SVG11/implnote.html#ArcImplementationNotes
    """
    import math
    cos_phi = math.cos(phi); sin_phi = math.sin(phi)
    # Step 1: 端点变换到坐标中心
    dx = (x1 - x2) / 2; dy = (y1 - y2) / 2
    x1p = cos_phi * dx + sin_phi * dy
    y1p = -sin_phi * dx + cos_phi * dy

    # Step 2: 修正 rx/ry 使其足够覆盖端点
    lam = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if lam > 1:
        s = math.sqrt(lam)
        rx *= s; ry *= s

    # Step 3: 计算中心
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    factor = math.sqrt(max(num / den, 0)) if den > 1e-12 else 0
    sign = -1 if large_arc == sweep else 1
    cxp = sign * factor * (rx * y1p) / ry if ry > 1e-12 else 0
    cyp = sign * factor * -(ry * x1p) / rx if rx > 1e-12 else 0

    cx = cos_phi * cxp - sin_phi * cyp + (x1 + x2) / 2
    cy = sin_phi * cxp + cos_phi * cyp + (y1 + y2) / 2

    # Step 4: 计算 start/end 角度
    def _ang(ux, uy, vx, vy):
        dot = ux * vx + uy * vy
        norm = math.sqrt((ux*ux+uy*uy) * (vx*vx+vy*vy))
        if norm < 1e-12: return 0
        c = max(-1, min(1, dot / norm))
        sign = 1 if (ux * vy - uy * vx) >= 0 else -1
        return sign * math.acos(c)

    theta1 = _ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    delta = _ang((x1p - cxp) / rx, (y1p - cyp) / ry,
                 (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and delta > 0:
        delta -= 2 * math.pi
    elif sweep and delta < 0:
        delta += 2 * math.pi

    # Step 5: 采样
    pts = []
    for k in range(segs + 1):
        t = theta1 + delta * k / segs
        ex = cx + rx * math.cos(t) * cos_phi - ry * math.sin(t) * sin_phi
        ey = cy + rx * math.cos(t) * sin_phi + ry * math.sin(t) * cos_phi
        pts.append((ex, ey))
    return pts


def _svg_path_to_polylines(d, transform):
    """解析 SVG path 的 d 属性，返回子路径列表。

    每个子路径: {'pts': [(x, y), ...], 'closed': bool}
    坐标经 transform(x, y) 转换后返回。曲线按折线近似（Q/C: 12 段）。
    仅支持核心命令 M/L/H/V/C/Q/Z，其他命令跳过。
    """
    tokens = _SVG_TOKEN.findall(d or '')
    subs = []
    cur_pts = []
    current = (0.0, 0.0)
    start = (0.0, 0.0)
    last_cmd = None
    seen_moveto = False  # 整个 path 是否出现过任何 M/m
    i = 0

    def _pt(x, y):
        return transform(x, y)

    def _close():
        nonlocal cur_pts
        if cur_pts:
            subs.append({'pts': list(cur_pts), 'closed': True})
            cur_pts = []

    def _flush():
        nonlocal cur_pts
        if cur_pts:
            subs.append({'pts': list(cur_pts), 'closed': False})
            cur_pts = []

    def _read_n(count):
        """读 count 个数字，返回 list[float]，推进 i"""
        nonlocal i
        vals = []
        while len(vals) < count and i < len(tokens):
            cmd_tok, num_tok = tokens[i]
            if cmd_tok:
                break
            vals.append(float(num_tok))
            i += 1
        return vals

    while i < len(tokens):
        cmd_tok, num_tok = tokens[i]
        if cmd_tok:
            cmd = cmd_tok
            i += 1
        else:
            # 隐式命令：M 后续默认为 L，m 后续默认为 l
            cmd = 'L' if last_cmd in ('M', 'L') else ('l' if last_cmd in ('m', 'l') else last_cmd)
            if cmd is None:
                i += 1
                continue

        if cmd in ('M', 'm'):
            vals = _read_n(2)
            if len(vals) < 2: break
            # SVG 规范：只有整个 path 的第一个 moveto（无论 M 还是 m）当绝对
            # 之后的 m（包含 Z 之后的）均当相对于 current 处理
            if cmd == 'M' or not seen_moveto:
                x, y = vals[0], vals[1]
            else:
                x, y = current[0] + vals[0], current[1] + vals[1]
            _flush()
            current = (x, y); start = (x, y)
            cur_pts.append(_pt(x, y))
            seen_moveto = True
            last_cmd = cmd
        elif cmd in ('L', 'l'):
            vals = _read_n(2)
            if len(vals) < 2: break
            if cmd == 'L':
                x, y = vals[0], vals[1]
            else:
                x, y = current[0] + vals[0], current[1] + vals[1]
            current = (x, y)
            cur_pts.append(_pt(x, y))
            last_cmd = cmd
        elif cmd in ('H', 'h'):
            vals = _read_n(1)
            if not vals: break
            x = vals[0] if cmd == 'H' else current[0] + vals[0]
            y = current[1]
            current = (x, y)
            cur_pts.append(_pt(x, y))
            last_cmd = cmd
        elif cmd in ('V', 'v'):
            vals = _read_n(1)
            if not vals: break
            x = current[0]
            y = vals[0] if cmd == 'V' else current[1] + vals[0]
            current = (x, y)
            cur_pts.append(_pt(x, y))
            last_cmd = cmd
        elif cmd in ('Q', 'q'):
            # 二次贝塞尔：近似成 12 段折线
            vals = _read_n(4)
            if len(vals) < 4: break
            if cmd == 'Q':
                c1x, c1y, ex, ey = vals
            else:
                c1x = current[0] + vals[0]; c1y = current[1] + vals[1]
                ex  = current[0] + vals[2]; ey  = current[1] + vals[3]
            segs = 12
            for k in range(1, segs + 1):
                t = k / segs
                # 二次贝塞尔 B(t) = (1-t)²P0 + 2(1-t)t P1 + t² P2
                mt = 1 - t
                bx = mt*mt*current[0] + 2*mt*t*c1x + t*t*ex
                by = mt*mt*current[1] + 2*mt*t*c1y + t*t*ey
                cur_pts.append(_pt(bx, by))
            current = (ex, ey)
            last_cmd = cmd
        elif cmd in ('C', 'c'):
            # 三次贝塞尔：近似成 12 段折线
            vals = _read_n(6)
            if len(vals) < 6: break
            if cmd == 'C':
                c1x, c1y, c2x, c2y, ex, ey = vals
            else:
                c1x = current[0] + vals[0]; c1y = current[1] + vals[1]
                c2x = current[0] + vals[2]; c2y = current[1] + vals[3]
                ex  = current[0] + vals[4]; ey  = current[1] + vals[5]
            segs = 12
            for k in range(1, segs + 1):
                t = k / segs
                # 三次贝塞尔 B(t)
                mt = 1 - t
                bx = mt**3*current[0] + 3*mt**2*t*c1x + 3*mt*t**2*c2x + t**3*ex
                by = mt**3*current[1] + 3*mt**2*t*c1y + 3*mt*t**2*c2y + t**3*ey
                cur_pts.append(_pt(bx, by))
            current = (ex, ey)
            last_cmd = cmd
        elif cmd in ('A', 'a'):
            # SVG 椭圆弧：a rx ry x-rot large-arc sweep dx dy
            vals = _read_n(7)
            if len(vals) < 7: break
            rx = abs(vals[0]); ry = abs(vals[1])
            phi = vals[2] * 3.141592653589793 / 180.0  # x-axis rotation 弧度
            large_arc = bool(int(vals[3]))
            sweep = bool(int(vals[4]))
            if cmd == 'A':
                ex, ey = vals[5], vals[6]
            else:
                ex = current[0] + vals[5]; ey = current[1] + vals[6]
            if rx < 1e-9 or ry < 1e-9:
                # 退化为直线
                current = (ex, ey)
                cur_pts.append(_pt(ex, ey))
            else:
                arc_pts = _arc_endpoint_to_polyline(current[0], current[1],
                                                     rx, ry, phi,
                                                     large_arc, sweep, ex, ey,
                                                     segs=20)
                for (px, py) in arc_pts[1:]:  # 跳过起点避免重复
                    cur_pts.append(_pt(px, py))
                current = (ex, ey)
            last_cmd = cmd
        elif cmd in ('Z', 'z'):
            if cur_pts:
                cur_pts.append(_pt(start[0], start[1]))
            current = start
            _close()
            last_cmd = cmd
        else:
            # 不支持的命令（S/T 等）：跳过参数
            while i < len(tokens) and not tokens[i][0]:
                i += 1
            last_cmd = cmd

    _flush()
    return subs
