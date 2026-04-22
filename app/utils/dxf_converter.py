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

logger = logging.getLogger(__name__)


def render_dxf_to_png(dxf_path, output_dir, base_name, max_dims=None):
    """将 DXF 文件渲染为多分辨率 PNG 文件

    Args:
        dxf_path: DXF 文件路径
        output_dir: 输出目录
        base_name: 输出文件名前缀
        max_dims: 分辨率列表，默认 [1000, 2000, 4000]

    Returns:
        dict: {str(max_dim): {filename, width, height}}

    Raises:
        ImportError: matplotlib 未安装
        Exception: 渲染失败
    """
    import ezdxf
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    import matplotlib.pyplot as plt
    from PIL import Image

    if max_dims is None:
        max_dims = [1000, 2000, 4000]

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    fig = plt.figure(figsize=(20, 20))
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(msp, finalize=True)

    fig.canvas.draw()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    buf.seek(0)
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


def combine_dxf_with_image(original_dxf_path, canvas_png_path,
                            output_dxf_path, canvas_width_mm, canvas_height_mm):
    """将原始 DXF 实体与画布 PNG 合并为双图层 DXF

    图层结构:
    - BACKGROUND: 原始 DXF 所有实体（从 modelspace 复制）
    - SYSTEM_DESIGN: 画布 PNG 作为 IMAGE 实体叠加在原点

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
    from ezdxf import units

    src = ezdxf.readfile(original_dxf_path)
    src_msp = src.modelspace()

    doc = ezdxf.new(dxfversion=src.dxfversion)
    doc.units = src.units if src.units else units.MM
    msp = doc.modelspace()

    doc.layers.new('BACKGROUND', dxfattribs={'color': 7})
    doc.layers.new('SYSTEM_DESIGN', dxfattribs={'color': 3})

    for entity in src_msp:
        try:
            copy = entity.copy()
            copy.dxf.layer = 'BACKGROUND'
            msp.add_entity(copy)
        except Exception as e:
            logger.warning(f"跳过无法复制的实体 {entity.dxftype()}: {e}")

    png_abs = os.path.abspath(canvas_png_path)
    image_def = doc.add_image_def(
        filename=png_abs,
        size_in_pixel=(int(canvas_width_mm * 3.78), int(canvas_height_mm * 3.78))
    )
    msp.add_image(
        insert=(0, 0, 0),
        size_in_units=(canvas_width_mm, canvas_height_mm),
        image_def=image_def,
        dxfattribs={'layer': 'SYSTEM_DESIGN'}
    )

    doc.saveas(output_dxf_path)
    return output_dxf_path


def convert_dxf_to_dwg(dxf_path, output_dir):
    """用 LibreDWG dxf2dwg 将 .dxf 文件转换为 .dwg

    如果 dxf2dwg 不可用，直接返回 None（调用方降级为输出 DXF）。

    Args:
        dxf_path: DXF 文件路径
        output_dir: 输出目录

    Returns:
        str | None: 生成的 DWG 文件路径，或 None（工具不可用时）
    """
    if not shutil.which('dxf2dwg'):
        logger.warning('dxf2dwg 不可用，将输出 DXF 格式')
        return None

    base = os.path.splitext(os.path.basename(dxf_path))[0]
    out_dwg = os.path.join(output_dir, f"{base}.dwg")

    result = subprocess.run(
        ['dxf2dwg', dxf_path, '-o', out_dwg],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0 or not os.path.exists(out_dwg):
        logger.warning(f"dxf2dwg 失败: {result.stderr}，将输出 DXF")
        return None

    return out_dwg
