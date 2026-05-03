# -*- coding: utf-8 -*-
"""从 .docx 提取图片并标注其在文档段落流中的位置。

.docx 是 zip：
  word/media/image{N}.{ext}     ← 图片二进制
  word/document.xml             ← 段落流，<w:drawing> 锚点指向 image{N}
  word/_rels/document.xml.rels  ← rId → media 路径映射
"""
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'rels': 'http://schemas.openxmlformats.org/package/2006/relationships',
}

_EXT_TO_MEDIA = {
    'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
    'gif': 'image/gif', 'webp': 'image/webp', 'bmp': 'image/bmp',
}


def _parse_rels(zf: zipfile.ZipFile) -> dict:
    """rId → 'word/media/imageN.ext'"""
    try:
        data = zf.read('word/_rels/document.xml.rels')
    except KeyError:
        return {}
    root = ET.fromstring(data)
    out = {}
    for rel in root.findall('rels:Relationship', NS):
        if rel.attrib.get('Type', '').endswith('/image'):
            target = rel.attrib['Target']
            if not target.startswith('word/'):
                target = 'word/' + target.lstrip('/')
            out[rel.attrib['Id']] = target
    return out


def extract_docx_images(docx_path) -> list:
    """提取 .docx 中所有图片，按出现顺序标注段落锚点。

    Returns:
        [{'order': 1, 'paragraph_index': 12, 'data': bytes,
          'media_type': 'image/png', 'original_name': 'image1.png'}, ...]
    """
    docx_path = Path(docx_path)
    out: list = []
    with zipfile.ZipFile(docx_path) as zf:
        rels = _parse_rels(zf)
        try:
            doc_xml = zf.read('word/document.xml')
        except KeyError:
            return []
        root = ET.fromstring(doc_xml)
        body = root.find('w:body', NS)
        if body is None:
            return []
        order = 0
        for para_idx, p in enumerate(body.findall('.//w:p', NS)):
            for blip in p.findall('.//a:blip', NS):
                rid = blip.attrib.get(f'{{{NS["r"]}}}embed')
                if not rid or rid not in rels:
                    continue
                media_path = rels[rid]
                try:
                    data = zf.read(media_path)
                except KeyError:
                    continue
                ext = media_path.rsplit('.', 1)[-1].lower()
                media_type = _EXT_TO_MEDIA.get(ext, 'image/png')
                order += 1
                out.append({
                    'order': order,
                    'paragraph_index': para_idx,
                    'data': data,
                    'media_type': media_type,
                    'original_name': media_path.rsplit('/', 1)[-1],
                })
    return out
