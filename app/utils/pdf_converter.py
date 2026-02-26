"""PDF 转换工具 — 用于系统图平面图背景导入

支持 PDF 页面分析（缩略图 + 书签名称）和多分辨率 PNG 渲染。
依赖: PyMuPDF (fitz)
"""
import base64
import os
import logging

logger = logging.getLogger(__name__)


def analyze_pdf(pdf_path):
    """分析 PDF，返回页数和每页信息（缩略图 base64、书签名称、尺寸）

    Returns:
        list[dict]: 每页 {index, name, thumbnail, width, height}
    """
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    try:
        # 提取书签 → 页码映射（页码从1开始）
        bookmarks = {}
        try:
            for item in doc.get_toc():  # [level, title, page_number]
                page_num = item[2]
                if page_num not in bookmarks:
                    bookmarks[page_num] = item[1]
        except Exception:
            pass

        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        pages = []

        for i, page in enumerate(doc):
            # 生成缩略图 (~300px 宽)
            thumb_pix = page.get_pixmap(dpi=36)
            thumb_bytes = thumb_pix.tobytes("png")
            thumb_base64 = base64.b64encode(thumb_bytes).decode()

            # 页面名称: 书签 > "{文件名}-{页码}"
            name = bookmarks.get(i + 1, None)
            if not name:
                name = f"{pdf_name}-{i + 1}"

            pages.append({
                'index': i,
                'name': name,
                'thumbnail': f"data:image/png;base64,{thumb_base64}",
                'width': page.rect.width,
                'height': page.rect.height
            })

        return pages
    finally:
        doc.close()


def convert_pdf_page_to_images(pdf_path, page_index, output_dir, base_name,
                                max_dims=None):
    """将 PDF 指定页渲染为多分辨率 PNG 文件

    Args:
        pdf_path: PDF 文件路径
        page_index: 页码索引 (0-based)
        output_dir: 输出目录
        base_name: 输出文件名前缀
        max_dims: 分辨率列表，默认 [1000, 2000, 4000]

    Returns:
        dict: {str(max_dim): {filename, width, height}}
    """
    import fitz  # PyMuPDF

    if max_dims is None:
        max_dims = [1000, 2000, 4000]

    doc = fitz.open(pdf_path)
    try:
        if page_index < 0 or page_index >= len(doc):
            raise ValueError(f"Page index {page_index} out of range (0-{len(doc)-1})")

        page = doc[page_index]
        page_rect = page.rect
        long_side = max(page_rect.width, page_rect.height)

        results = {}
        for max_dim in max_dims:
            dpi = int(max_dim / long_side * 72)
            dpi = max(72, min(dpi, 600))

            pix = page.get_pixmap(dpi=dpi)
            out_name = f"{base_name}_{max_dim}px.png"
            out_path = os.path.join(output_dir, out_name)
            pix.save(out_path)

            results[str(max_dim)] = {
                'filename': out_name,
                'width': pix.width,
                'height': pix.height
            }

        return results
    finally:
        doc.close()
