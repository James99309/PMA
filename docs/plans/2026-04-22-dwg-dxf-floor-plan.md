# DWG/DXF Floor Plan Import & Export Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让系统图编辑器支持导入 DWG/DXF 文件作为楼层底图，并在该楼层导出时提供"导出 DWG"选项，将画布设计层叠加在原始 DXF 上输出为 DWG 文件。

**Architecture:**
- **Import**: 用户上传 .dwg/.dxf → 服务端转换（DWG→DXF via LibreDWG dwg2dxf）→ ezdxf+matplotlib 渲染 DXF→PNG → PNG 作为楼层背景展示，原始 DXF 文件路径存入 `fp.background.dxf_filename`
- **Export**: 前端捕获画布为 PNG → 服务端用 ezdxf 将原始 DXF 实体放入 BACKGROUND 图层 + 画布 PNG 作为 IMAGE 实体放入 SYSTEM_DESIGN 图层 → 生成新 DXF → LibreDWG dxf2dwg 转换为 DWG → 打包 ZIP（DWG + canvas PNG）返回下载
- **条件显示**: "导出 DWG" 仅当 `fp.background.bg_type === 'dxf'` 时出现在导出菜单

**Tech Stack:** `ezdxf` 1.4.2（已安装）、`matplotlib`（需添加）、`Pillow` 11.2.1（已安装）、LibreDWG `libredwg-tools`（需在 Dockerfile 添加）

---

## 文件索引

| 操作 | 文件 |
|------|------|
| Create | `app/utils/dxf_converter.py` |
| Modify | `app/views/system_diagram.py` |
| Modify | `app/static/js/system-diagram-floorplan.js` |
| Modify | `app/static/js/system-diagram-core.js` |
| Modify | `app/templates/system_diagram/tw_editor.html` |
| Modify | `requirements.txt` |
| Modify | `Dockerfile`, `deploy/synology/Dockerfile`, `deploy/synology-cn/Dockerfile`, `deploy/synology-sa/Dockerfile` |

---

### Task 1: 添加依赖

**Files:**
- Modify: `requirements.txt`
- Modify: `Dockerfile` (及 deploy/ 下的三个变体)

**Step 1: 在 requirements.txt 末尾添加 matplotlib**

```
matplotlib>=3.7.0
```

**Step 2: 在所有 Dockerfile 的 apt-get install 块中添加 libredwg-tools**

在 `apt-get install -y` 块中加入（已有 `curl` 等行后面）：
```dockerfile
    libredwg-tools \
```

四个文件都要改：`./Dockerfile`、`deploy/synology/Dockerfile`、`deploy/synology-cn/Dockerfile`、`deploy/synology-sa/Dockerfile`

**Step 3: 本地安装 matplotlib**

```bash
pip install matplotlib
```

Expected: Successfully installed matplotlib-...

**Step 4: 验证依赖可用**

```bash
python3 -c "import matplotlib; import ezdxf; from ezdxf.addons.drawing.matplotlib import MatplotlibBackend; print('OK')"
```

Expected: `OK`

**Step 5: commit**

```bash
git add requirements.txt Dockerfile deploy/synology/Dockerfile deploy/synology-cn/Dockerfile deploy/synology-sa/Dockerfile
git commit -m "deps: add matplotlib for DXF rendering, libredwg-tools for DWG conversion"
```

---

### Task 2: 创建 dxf_converter.py 工具模块

**Files:**
- Create: `app/utils/dxf_converter.py`

该模块提供四个函数，结构类似现有的 `pdf_converter.py`。

**Step 1: 创建文件**

```python
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

    # 渲染到内存中的 matplotlib figure
    fig = plt.figure(figsize=(20, 20))
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(msp, finalize=True)

    # 获取渲染尺寸
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

    # 读取原始 DXF
    src = ezdxf.readfile(original_dxf_path)
    src_msp = src.modelspace()

    # 新建输出 DXF，继承原始文档设置
    doc = ezdxf.new(dxfversion=src.dxfversion)
    doc.units = src.units if src.units else units.MM
    msp = doc.modelspace()

    # 确保 BACKGROUND 和 SYSTEM_DESIGN 图层存在
    doc.layers.new('BACKGROUND', dxfattribs={'color': 7})   # 白色/黑色（CAD 默认）
    doc.layers.new('SYSTEM_DESIGN', dxfattribs={'color': 3}) # 绿色

    # 将原始 modelspace 实体复制到 BACKGROUND 图层
    for entity in src_msp:
        try:
            copy = entity.copy()
            copy.dxf.layer = 'BACKGROUND'
            msp.add_entity(copy)
        except Exception as e:
            logger.warning(f"跳过无法复制的实体 {entity.dxftype()}: {e}")

    # 在 SYSTEM_DESIGN 图层添加画布 PNG 为 IMAGE 实体
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
```

**Step 2: 验证模块可导入**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && python3 -c "
import sys; sys.path.insert(0, '.')
from app.utils.dxf_converter import render_dxf_to_png, convert_dwg_to_dxf, combine_dxf_with_image, convert_dxf_to_dwg
print('dxf_converter OK')
"
```

Expected: `dxf_converter OK`

**Step 3: 写集成测试（需要一个简单 DXF 文件）**

```python
# tests/test_dxf_converter.py
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def make_simple_dxf(path):
    """生成一个最小的 DXF 文件用于测试"""
    import ezdxf
    doc = ezdxf.new()
    msp = doc.modelspace()
    msp.add_line((0, 0), (100, 100))
    msp.add_circle((50, 50), radius=20)
    doc.saveas(path)

def test_render_dxf_to_png():
    from app.utils.dxf_converter import render_dxf_to_png
    with tempfile.TemporaryDirectory() as tmpdir:
        dxf_path = os.path.join(tmpdir, 'test.dxf')
        make_simple_dxf(dxf_path)
        results = render_dxf_to_png(dxf_path, tmpdir, 'test', max_dims=[500, 1000])
        assert '500' in results
        assert '1000' in results
        for dim, info in results.items():
            assert os.path.exists(os.path.join(tmpdir, info['filename']))
            assert info['width'] > 0 and info['height'] > 0
        print('test_render_dxf_to_png PASSED')

def test_combine_dxf_with_image():
    from app.utils.dxf_converter import combine_dxf_with_image
    from PIL import Image
    with tempfile.TemporaryDirectory() as tmpdir:
        dxf_path = os.path.join(tmpdir, 'test.dxf')
        make_simple_dxf(dxf_path)
        # 创建假画布 PNG
        png_path = os.path.join(tmpdir, 'canvas.png')
        img = Image.new('RGBA', (800, 600), (255, 0, 0, 128))
        img.save(png_path)
        out_dxf = os.path.join(tmpdir, 'output.dxf')
        result = combine_dxf_with_image(dxf_path, png_path, out_dxf, 297, 210)
        assert os.path.exists(out_dxf)
        # 验证输出 DXF 包含两个图层
        import ezdxf
        doc = ezdxf.readfile(out_dxf)
        layer_names = {layer.dxf.name for layer in doc.layers}
        assert 'BACKGROUND' in layer_names
        assert 'SYSTEM_DESIGN' in layer_names
        print('test_combine_dxf_with_image PASSED')

if __name__ == '__main__':
    test_render_dxf_to_png()
    test_combine_dxf_with_image()
    print('All tests passed')
```

**Step 4: 运行测试**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && python3 tests/test_dxf_converter.py
```

Expected: `All tests passed`

**Step 5: commit**

```bash
git add app/utils/dxf_converter.py tests/test_dxf_converter.py
git commit -m "feat(dxf): add dxf_converter utility — render/convert/combine DXF layers"
```

---

### Task 3: 后端 — analyze_dxf 导入端点

**Files:**
- Modify: `app/views/system_diagram.py`

在 `ALLOWED_BG_EXTENSIONS` 行（第271行）和 `analyze_pdf_api` 函数附近添加。

**Step 1: 扩展 ALLOWED_BG_EXTENSIONS**

找到：
```python
ALLOWED_BG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
```

改为：
```python
ALLOWED_BG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'dxf', 'dwg'}
```

**Step 2: 在 `render_pdf_pages` 函数之后（约第 519 行）添加 `analyze_dxf_api` 端点**

```python
@system_diagram.route('/api/<int:diagram_id>/floor-plan/analyze-dxf', methods=['POST'])
@login_required
@permission_required('system_diagram', 'edit')
def analyze_dxf_api(diagram_id):
    """上传 DWG/DXF 文件，转换并渲染为多分辨率 PNG 底图

    流程:
    1. 接收 DWG/DXF 文件
    2. 若为 DWG，用 dwg2dxf 转换为 DXF
    3. 用 ezdxf+matplotlib 渲染 DXF 为多分辨率 PNG
    4. 保存 DXF 文件供后续导出使用
    5. 返回 PNG URLs + DXF 文件名
    """
    diagram = SystemDiagram.query.get_or_404(diagram_id)
    if diagram.is_deleted or not _can_edit_diagram(diagram):
        return jsonify({'success': False, 'message': _('无权限')}), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': _('请选择文件')}), 400

    file = request.files['file']
    floor_id = request.form.get('floor_id', '')
    if not file.filename or not floor_id:
        return jsonify({'success': False, 'message': _('缺少参数')}), 400

    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in ('dxf', 'dwg'):
        return jsonify({'success': False, 'message': _('仅支持 DXF/DWG 格式')}), 400

    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > MAX_BG_SIZE:
        return jsonify({'success': False, 'message': _('文件大小不能超过 12MB')}), 400

    upload_dir = _get_bg_upload_dir()
    uid = uuid.uuid4().hex[:8]
    uploaded_path = os.path.join(upload_dir, f"{diagram_id}_{floor_id}_{uid}.{ext}")

    try:
        file.save(uploaded_path)

        from app.utils.dxf_converter import render_dxf_to_png, convert_dwg_to_dxf

        # DWG → DXF 转换
        if ext == 'dwg':
            try:
                dxf_path = convert_dwg_to_dxf(uploaded_path, upload_dir)
                os.remove(uploaded_path)  # 删除原始 DWG，只保留 DXF
            except FileNotFoundError:
                return jsonify({
                    'success': False,
                    'message': _('服务器未安装 dwg2dxf，请先将 DWG 另存为 DXF 后上传')
                }), 500
        else:
            dxf_path = uploaded_path

        # 渲染 DXF → 多分辨率 PNG
        base_name = f"{diagram_id}_{floor_id}_{uid}"
        resolutions = render_dxf_to_png(dxf_path, upload_dir, base_name,
                                         max_dims=[1000, 2000, 4000])

        # 构建 URL 映射
        res_with_urls = {}
        all_png_filenames = []
        for dim_key, info in resolutions.items():
            res_with_urls[dim_key] = {
                'url': url_for('system_diagram.serve_floor_bg', filename=info['filename']),
                'width': info['width'],
                'height': info['height'],
            }
            all_png_filenames.append(info['filename'])

        default_res = res_with_urls.get('2000', list(res_with_urls.values())[0])
        dxf_filename = os.path.basename(dxf_path)

        return jsonify({
            'success': True,
            'url': default_res['url'],
            'width': default_res['width'],
            'height': default_res['height'],
            'resolutions': res_with_urls,
            'filenames': all_png_filenames,
            'dxf_filename': dxf_filename,   # 供导出 DWG 使用
        })

    except ImportError:
        return jsonify({'success': False, 'message': 'matplotlib 未安装，无法渲染 DXF'}), 500
    except Exception as e:
        logger.error(f"DXF 导入失败: {e}")
        # 清理已上传文件
        for f_path in [uploaded_path]:
            if os.path.exists(f_path):
                try:
                    os.remove(f_path)
                except Exception:
                    pass
        return jsonify({'success': False, 'message': str(e)}), 500
```

**Step 3: 更新 `delete_floor_bg` — 同时删除 DXF 文件**

在 `delete_floor_bg` 函数中，在现有文件删除循环之后（约第370行 `for fn in filenames:` 循环之后）添加：

```python
    # 同时删除关联的 DXF 文件（如果有）
    dxf_filename = data.get('dxf_filename', '')
    if dxf_filename:
        dxf_path = os.path.join(upload_dir, os.path.basename(dxf_filename))
        if os.path.exists(dxf_path):
            try:
                os.remove(dxf_path)
            except Exception as e:
                logger.warning(f"删除 DXF 文件失败: {e}")
```

**Step 4: commit**

```bash
git add app/views/system_diagram.py
git commit -m "feat(dxf): add analyze_dxf_api endpoint and DXF cleanup on delete"
```

---

### Task 4: 后端 — export_dwg 导出端点

**Files:**
- Modify: `app/views/system_diagram.py`

在文件末尾（第 1080 行后）添加。

**Step 1: 添加 import（文件顶部已有的 import 块中）**

确认文件顶部已有 `import tempfile`，如无则添加：
```python
import tempfile
import zipfile
```

**Step 2: 添加 export_dwg_api 端点**

```python
@system_diagram.route('/api/<int:diagram_id>/export-dwg', methods=['POST'])
@login_required
@permission_required('system_diagram', 'view')
def export_dwg_api(diagram_id):
    """将系统图画布叠加到原始 DXF 上，导出为 DWG 文件（ZIP 包）

    请求体 (JSON):
        canvas_png: base64 编码的画布截图 PNG
        dxf_filename: fp.background.dxf_filename（服务端存储的 DXF 文件名）
        canvas_width_mm: 画布实际宽度（毫米）
        canvas_height_mm: 画布实际高度（毫米）
        diagram_name: 用于输出文件命名

    返回:
        ZIP 文件（含 .dwg 或 .dxf + canvas_overlay.png）
    """
    import base64
    import tempfile
    import zipfile

    diagram = SystemDiagram.query.get_or_404(diagram_id)
    if diagram.is_deleted:
        return jsonify({'success': False, 'message': _('系统图不存在')}), 404

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': _('无效请求')}), 400

    canvas_png_b64 = data.get('canvas_png', '')
    dxf_filename = data.get('dxf_filename', '')
    canvas_width_mm = float(data.get('canvas_width_mm', 297))
    canvas_height_mm = float(data.get('canvas_height_mm', 210))
    diagram_name = data.get('diagram_name', 'system_diagram')

    if not canvas_png_b64 or not dxf_filename:
        return jsonify({'success': False, 'message': _('缺少参数')}), 400

    upload_dir = _get_bg_upload_dir()
    dxf_path = os.path.join(upload_dir, os.path.basename(dxf_filename))
    if not os.path.exists(dxf_path):
        return jsonify({'success': False, 'message': _('DXF 源文件不存在，请重新导入底图')}), 404

    try:
        from app.utils.dxf_converter import combine_dxf_with_image, convert_dxf_to_dwg

        with tempfile.TemporaryDirectory() as tmpdir:
            # 解码画布 PNG
            if canvas_png_b64.startswith('data:'):
                canvas_png_b64 = canvas_png_b64.split(',', 1)[1]
            canvas_png_bytes = base64.b64decode(canvas_png_b64)
            canvas_png_path = os.path.join(tmpdir, 'canvas_overlay.png')
            with open(canvas_png_path, 'wb') as f:
                f.write(canvas_png_bytes)

            # 合并 DXF + 画布图层
            safe_name = ''.join(c for c in diagram_name if c.isalnum() or c in '-_ ')[:40].strip() or 'diagram'
            combined_dxf_path = os.path.join(tmpdir, f"{safe_name}_combined.dxf")
            combine_dxf_with_image(
                dxf_path, canvas_png_path, combined_dxf_path,
                canvas_width_mm, canvas_height_mm
            )

            # DXF → DWG（若工具可用）
            dwg_path = convert_dxf_to_dwg(combined_dxf_path, tmpdir)
            main_file = dwg_path if dwg_path else combined_dxf_path
            main_ext = 'dwg' if dwg_path else 'dxf'

            # 打包为 ZIP（DWG/DXF + canvas PNG）
            zip_name = f"{safe_name}.zip"
            zip_path = os.path.join(tmpdir, zip_name)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(main_file, f"{safe_name}.{main_ext}")
                zf.write(canvas_png_path, 'canvas_overlay.png')

            zip_bytes = open(zip_path, 'rb').read()

        from flask import Response
        return Response(
            zip_bytes,
            mimetype='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename="{zip_name}"',
                'Content-Length': len(zip_bytes),
            }
        )

    except Exception as e:
        logger.error(f"导出 DWG 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
```

**Step 3: commit**

```bash
git add app/views/system_diagram.py
git commit -m "feat(dxf): add export_dwg_api endpoint — combine DXF layers and package as ZIP"
```

---

### Task 5: 前端 — DXF 上传处理（system-diagram-floorplan.js）

**Files:**
- Modify: `app/static/js/system-diagram-floorplan.js`

**Step 1: 更新 uploadFloorBg 函数，接受 .dxf/.dwg 并路由到新处理器**

找到 `uploadFloorBg` 函数（第 2253 行）中的这一行：
```javascript
  input.accept='image/png,image/jpeg,image/jpg,application/pdf';
```

改为：
```javascript
  input.accept='image/png,image/jpeg,image/jpg,application/pdf,.dxf,.dwg';
```

找到这段 PDF 判断逻辑（第 2263 行）：
```javascript
    const isPdf=file.name.toLowerCase().endsWith('.pdf');
    if(isPdf){
      await _handlePdfUpload(file,fpId);
      return;
    }
```

改为：
```javascript
    const fname=file.name.toLowerCase();
    if(fname.endsWith('.pdf')){
      await _handlePdfUpload(file,fpId);
      return;
    }
    if(fname.endsWith('.dxf')||fname.endsWith('.dwg')){
      await _handleDxfUpload(file,fpId);
      return;
    }
```

**Step 2: 在 `_handlePdfUpload` 函数之前（第 2373 行前）插入 `_handleDxfUpload` 函数**

```javascript
// ====== DXF/DWG IMPORT ======

async function _handleDxfUpload(file, fpId) {
  if (!DIAGRAM_CONFIG.diagramId) {
    await saveDiagram();
    if (!DIAGRAM_CONFIG.diagramId) { showToast(_t('保存失败，无法上传')); return; }
  }

  const isDwg = file.name.toLowerCase().endsWith('.dwg');
  showToast(isDwg ? _t('转换 DWG 中...') : _t('渲染 DXF 中...'));

  const formData = new FormData();
  formData.append('file', file, file.name);
  formData.append('floor_id', fpId);

  try {
    const resp = await fetch(
      DIAGRAM_CONFIG.apiFloorBgBase + DIAGRAM_CONFIG.diagramId + '/floor-plan/analyze-dxf',
      { method: 'POST', headers: { 'X-CSRFToken': DIAGRAM_CONFIG.csrfToken }, body: formData }
    );
    const result = await resp.json();
    if (!result.success) { showToast(result.message || _t('DXF 导入失败')); return; }

    const fp = getFloorPlan(fpId);
    if (!fp) return;
    _cleanupOldBgFiles(fp);

    fp.background = {
      is_multi_res: true,
      url: result.url,
      width: result.width,
      height: result.height,
      resolutions: result.resolutions,
      filenames: result.filenames,
      offset_x: 0, offset_y: 0, opacity: 0.3,
      bg_type: 'dxf',                     // 标记为 DXF 底图，启用"导出 DWG"
      dxf_filename: result.dxf_filename,  // 服务端存储的 DXF 文件名
    };

    hasUnsavedChanges = true;
    renderAll();
    showFloorPlanProps(fpId);
    showToast(_t('DXF 底图已导入'));
    updateFloorBgButton(fpId);
    updateDwgExportMenuItem(); // 刷新导出菜单
    if (!fp.calibration) _offerCalibrationInheritance(fpId);
  } catch (err) {
    showToast(_t('DXF 导入失败') + ': ' + err.message);
  }
}
```

**Step 3: 更新 `deleteFloorBg` 中的请求体，传递 dxf_filename**

找到 `deleteFloorBg` 函数中的（第 2322 行）：
```javascript
  const body={floor_id:fpId};
  if(fp.background.filenames&&fp.background.filenames.length){
    body.filenames=fp.background.filenames;
  } else {
    body.filename=fp.background.filename||'';
  }
```

改为：
```javascript
  const body={floor_id:fpId};
  if(fp.background.filenames&&fp.background.filenames.length){
    body.filenames=fp.background.filenames;
  } else {
    body.filename=fp.background.filename||'';
  }
  // 若为 DXF 底图，同时传递 DXF 文件名以便服务端清理
  if(fp.background.bg_type==='dxf'&&fp.background.dxf_filename){
    body.dxf_filename=fp.background.dxf_filename;
  }
```

**Step 4: commit**

```bash
git add app/static/js/system-diagram-floorplan.js
git commit -m "feat(dxf): handle DXF/DWG upload in floor plan background flow"
```

---

### Task 6: 前端 — 导出 DWG 菜单项 + exportDWG 函数

**Files:**
- Modify: `app/static/js/system-diagram-core.js`
- Modify: `app/templates/system_diagram/tw_editor.html`

**Step 1: 在 system-diagram-core.js 的 `toggleExportMenu` 函数（第 1124 行）之前添加辅助函数和 exportDWG**

```javascript
// ====== DWG EXPORT ======

function currentFloorHasDwg() {
  if (currentView === 'topology') return false;
  const fp = typeof getFloorPlan === 'function' ? getFloorPlan(currentView) : null;
  return !!(fp && fp.background && fp.background.bg_type === 'dxf' && fp.background.dxf_filename);
}

function updateDwgExportMenuItem() {
  const item = document.getElementById('exportDwgItem');
  if (!item) return;
  item.style.display = currentFloorHasDwg() ? 'flex' : 'none';
}

async function exportDWG() {
  if (!currentFloorHasDwg()) { showToast(_t('当前楼层无 DXF 底图')); return; }
  const fp = getFloorPlan(currentView);
  document.getElementById('exportMenu').style.display = 'none';

  showToast(_t('准备导出 DWG...'));

  try {
    // 捕获画布为 PNG（复用 PDF 导出的 SVG→canvas 流程）
    const { clone, w, h } = await prepareExportSVG(null, exportBlackMode);
    const maxPixels = 25000000;
    let scale = 1;
    if (w * h > maxPixels) scale = Math.sqrt(maxPixels / (w * h));
    const cw = Math.round(w * scale);
    const ch = Math.round(h * scale);

    const cvs = document.createElement('canvas');
    cvs.width = cw; cvs.height = ch;
    const ctx = cvs.getContext('2d');
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, cw, ch);
    if (scale !== 1) ctx.scale(scale, scale);

    const svgData = new XMLSerializer().serializeToString(clone);
    await new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => { ctx.drawImage(img, 0, 0, w, h); resolve(); };
      img.onerror = reject;
      img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgData);
    });

    const canvasPngB64 = cvs.toDataURL('image/png');

    // 估算画布实际尺寸（毫米）—— 使用 A3 横向比例作为默认
    const aspectRatio = w / h;
    const widthMm = 420;  // A3 宽
    const heightMm = widthMm / aspectRatio;

    showToast(_t('生成 DWG 文件中...'));

    const resp = await fetch(
      (DIAGRAM_CONFIG.apiLoadBase || '') + DIAGRAM_CONFIG.diagramId + '/export-dwg',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': DIAGRAM_CONFIG.csrfToken },
        body: JSON.stringify({
          canvas_png: canvasPngB64,
          dxf_filename: fp.background.dxf_filename,
          canvas_width_mm: widthMm,
          canvas_height_mm: heightMm,
          diagram_name: document.getElementById('diagramNameInput')?.value || 'diagram',
        })
      }
    );

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ message: resp.statusText }));
      showToast(_t('导出失败') + ': ' + (err.message || resp.statusText));
      return;
    }

    // 触发下载
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const name = document.getElementById('diagramNameInput')?.value || 'diagram';
    a.download = name + '.zip';
    a.click();
    URL.revokeObjectURL(url);
    showToast(_t('已导出 DWG'));
  } catch (err) {
    showToast(_t('导出失败') + ': ' + err.message);
  }
}
```

**Step 2: 更新 toggleExportMenu，打开时刷新 DWG 菜单项**

找到 `toggleExportMenu` 函数（第 1124 行）：
```javascript
function toggleExportMenu(){
  const menu=document.getElementById('exportMenu');
  if(menu.style.display==='block'){menu.style.display='none'}
  else{menu.style.display='block';...}
}
```

在 `menu.style.display='block'` 之后、`setTimeout` 之前添加：
```javascript
  updateDwgExportMenuItem();
```

**Step 3: 在 tw_editor.html 的导出菜单中添加 DWG 菜单项**

找到导出菜单中"框选导出 PNG"那一项（最后一个 `<div onclick="startCropExport()"...`），在它**之前**的分隔线之后插入：

```html
<div id="exportDwgItem" onclick="exportDWG()" style="display:none;padding:8px 14px;font-size:12px;color:var(--text-secondary);cursor:pointer;align-items:center;gap:8px;transition:background .15s;" onmouseenter="this.style.background='var(--item-hover)'" onmouseleave="this.style.background=''">
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
  DWG {{ _('工程图') }}
</div>
```

**Step 4: 在 tw_editor.html 的 SD_I18N 字典（第 616 行区域）中添加翻译条目**

在 `'已导出 PDF':` 附近添加：
```javascript
'准备导出 DWG...': {zh:'准备导出 DWG...',en:'Preparing DWG export...'},
'生成 DWG 文件中...': {zh:'生成 DWG 文件中...',en:'Generating DWG file...'},
'已导出 DWG': {zh:'已导出 DWG',en:'DWG exported'},
'当前楼层无 DXF 底图': {zh:'当前楼层无 DXF 底图',en:'No DXF background on this floor'},
'DXF 底图已导入': {zh:'DXF 底图已导入',en:'DXF background imported'},
'转换 DWG 中...': {zh:'转换 DWG 中...',en:'Converting DWG...'},
'渲染 DXF 中...': {zh:'渲染 DXF 中...',en:'Rendering DXF...'},
'DXF 导入失败': {zh:'DXF 导入失败',en:'DXF import failed'},
'工程图': {zh:'工程图',en:'Engineering'},
```

**Step 5: commit**

```bash
git add app/static/js/system-diagram-core.js app/templates/system_diagram/tw_editor.html
git commit -m "feat(dxf): add exportDWG function and conditional DWG menu item"
```

---

### Task 7: 手动测试验证

**Step 1: 启动服务**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && python3 run.py
```

**Step 2: 创建测试 DXF 文件**

```bash
python3 -c "
import ezdxf
doc = ezdxf.new()
msp = doc.modelspace()
msp.add_line((0, 0), (1000, 0))
msp.add_line((1000, 0), (1000, 800))
msp.add_line((1000, 800), (0, 800))
msp.add_line((0, 800), (0, 0))
msp.add_circle((500, 400), radius=150)
msp.add_text('Test Room', dxfattribs={'height': 50, 'insert': (400, 380)})
doc.saveas('/tmp/test_floor.dxf')
print('DXF created at /tmp/test_floor.dxf')
"
```

**Step 3: UI 测试流程**

1. 打开浏览器，进入系统图编辑器，新建一个系统图
2. 添加楼层（点击"+ 添加楼层"）
3. 点击"背景图"按钮，选择 `/tmp/test_floor.dxf`
4. 验证：
   - 底图渲染并显示在画布上 ✓
   - "背景图"按钮变为"移除背景" ✓
   - 导出菜单中出现"DWG 工程图"选项 ✓
5. 切换到系统图（topology）视图：确认"DWG 工程图"选项不显示 ✓
6. 切换回楼层视图：确认"DWG 工程图"选项重新显示 ✓
7. 在底图上添加几个设备图标和连线
8. 点击"导出 DWG 工程图"
9. 验证：
   - 浏览器下载一个 `.zip` 文件 ✓
   - ZIP 内含 `*.dxf/dwg` + `canvas_overlay.png` ✓
   - 用 ezdxf 打开 DXF 确认含 BACKGROUND + SYSTEM_DESIGN 两个图层 ✓
10. 移除底图 → 确认"DWG 工程图"选项消失 ✓

**Step 4: 验证 ZIP 内容**

```bash
# 解压下载的 ZIP 验证
cd ~/Downloads && ls -la *.zip
unzip -l <downloaded>.zip

python3 -c "
import ezdxf, sys
doc = ezdxf.readfile(sys.argv[1])
layers = {l.dxf.name for l in doc.layers}
print('图层:', layers)
assert 'BACKGROUND' in layers, '缺少 BACKGROUND 图层'
assert 'SYSTEM_DESIGN' in layers, '缺少 SYSTEM_DESIGN 图层'
print('验证通过')
" <path-to-dxf-in-zip>
```

Expected: `图层: {'0', 'BACKGROUND', 'SYSTEM_DESIGN'}` + `验证通过`

**Step 5: 最终 commit**

```bash
git add -A
git commit -m "feat(system-diagram): DWG/DXF floor plan import and DWG export complete"
```

---

## 降级策略

| 工具缺失 | 降级行为 |
|----------|----------|
| `dwg2dxf` 不可用 | 拒绝 .dwg 上传，提示用户将 DWG 另存为 DXF |
| `dxf2dwg` 不可用 | 输出 DXF 而非 DWG，ZIP 内为 .dxf |
| `matplotlib` 未安装 | 返回 500 提示"matplotlib 未安装" |

---

## Docker 部署说明

四个 Dockerfile 均已在 Task 1 中修改，包含 `libredwg-tools`。在 NAS 上重新构建镜像：

```bash
# 在 NAS 上执行
cd /volume1/docker/pma
./update.sh
```

`libredwg-tools` 在 Debian 11（Bullseye）+ 可通过 apt 安装。如果基础镜像是 Debian 10 (Buster)，需要先添加 backports：
```dockerfile
RUN echo "deb http://deb.debian.org/debian buster-backports main" >> /etc/apt/sources.list \
    && apt-get update && apt-get install -y -t buster-backports libredwg-tools
```
