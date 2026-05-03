# -*- coding: utf-8 -*-
from pathlib import Path
import pytest
from docx import Document

FIXTURE = Path(__file__).parent / 'fixtures' / 'sample_with_images.docx'


def test_extract_returns_images_with_paragraph_anchors():
    from app.services.wiki.docx_images import extract_docx_images
    images = extract_docx_images(FIXTURE)
    # Fixture has exactly 2 images
    assert len(images) == 2
    img1, img2 = images
    # Order is 1-based and monotonic
    assert img1['order'] == 1
    assert img2['order'] == 2
    # Each image has bytes + media_type + paragraph_index
    for img in images:
        assert isinstance(img['data'], bytes)
        assert len(img['data']) > 0
        assert img['media_type'].startswith('image/')
        assert isinstance(img['paragraph_index'], int)
        assert 'original_name' in img
    # img1 sits in paragraph 1, img2 in paragraph 3 (the fixture's known layout)
    assert img1['paragraph_index'] == 1
    assert img2['paragraph_index'] == 3


def test_extract_handles_docx_without_images(tmp_path):
    from app.services.wiki.docx_images import extract_docx_images
    p = tmp_path / 'no-img.docx'
    Document().save(p)
    assert extract_docx_images(p) == []


def test_extract_handles_corrupt_or_missing_file_gracefully(tmp_path):
    """非真实 docx 文件应抛清晰异常，不要静默返回空。"""
    from app.services.wiki.docx_images import extract_docx_images
    bad = tmp_path / 'not-a-docx.txt'
    bad.write_text('hello')
    with pytest.raises(Exception):  # zipfile.BadZipFile or similar
        extract_docx_images(bad)
