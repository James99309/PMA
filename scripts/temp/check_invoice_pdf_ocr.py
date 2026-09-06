#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""联网实测:PDF/图片发票走真实视觉端点识别(2026-09-06 PDF 静默失效修复验证)

用法(key 从环境变量取,别写进脚本):
    export CLAUDE_VISION_BASE_URL=https://mac-smart.jamesgpone.win   # SG 走 mac-smart
    export CLAUDE_VISION_API_KEY=cp-xxx
    export CLAUDE_VISION_USE_BEARER=true
    export CLAUDE_VISION_MODEL=claude-haiku-4-5-20251001             # SG 的默认模型
    python3 scripts/temp/check_invoice_pdf_ocr.py 发票.pdf [更多文件...]
"""
import sys
import os
import json

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from app.services.claude_vision_ocr import detect_image_type, pdf_to_png_pages
from app.services.expense_invoice_ocr import extract_invoice


def main(paths, lang='zh'):
    print('端点: %s' % (os.environ.get('CLAUDE_VISION_BASE_URL')
                        or os.environ.get('ANTHROPIC_BASE_URL') or '(未配置)'))
    print('模型: %s' % os.environ.get('CLAUDE_VISION_MODEL', 'claude-haiku-4-5-20251001'))
    print('lang: %s\n' % lang)

    failed = 0
    for path in paths:
        blob = open(path, 'rb').read()
        kind = detect_image_type(blob)
        extra = ''
        if kind == 'application/pdf':
            extra = ' → 栅格化 %d 页' % len(pdf_to_png_pages(blob))
        print('── %s  (%s, %.1f KB%s)' % (os.path.basename(path), kind, len(blob) / 1024, extra))

        res = extract_invoice(blob, lang=lang)
        if not res.get('success'):
            failed += 1
            print('   ❌ %s\n' % res.get('message'))
            continue
        d = res['data']
        print('   ✅ seller=%s | no=%s | date=%s | %s %s | tax=%s | cat=%s'
              % (d.get('seller'), d.get('invoice_no'), d.get('date'),
                 d.get('currency'), d.get('invoice_amount'), d.get('tax_amount'),
                 d.get('category')))
        print('      desc=%s' % d.get('description'))
        print('      confidence=%s\n' % json.dumps(d.get('confidence', {}), ensure_ascii=False))

    print('=' * 60)
    print('%d/%d 识别成功' % (len(paths) - failed, len(paths)))
    return 1 if failed else 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1:], lang=os.environ.get('OCR_LANG', 'zh')))
