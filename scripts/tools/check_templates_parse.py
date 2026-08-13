#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全仓 Jinja 模板语法体检 —— 逐个 parse app/templates 下所有 .html。

起因:ui_helpers.html 把 {# 注释 #} 写进了 {% set %} 表达式内部,Jinja 无法解析,
整个文件报废(91 个模板 import 它),但因为模板是**惰性编译**的,只有真去访问那些页面
才会 500,所以在生产里躺了一段时间才被发现。这类错误必须全量扫。

运行:export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
      python3 scripts/tools/check_templates_parse.py
"""
import os
import sys

PROJECT_ROOT = '/Users/nijie/Documents/PMA'
TEMPLATE_DIR = os.path.join(PROJECT_ROOT, 'app', 'templates')
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from jinja2 import Environment, FileSystemLoader   # noqa: E402
from jinja2.exceptions import TemplateSyntaxError  # noqa: E402

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR),
                  extensions=['jinja2.ext.i18n', 'jinja2.ext.do', 'jinja2.ext.loopcontrols'])
env.install_null_translations()

scanned, archived, errors = 0, 0, []

for root, _dirs, files in os.walk(TEMPLATE_DIR):
    for fn in sorted(files):
        if not fn.endswith('.html'):
            continue
        path = os.path.join(root, fn)
        rel = os.path.relpath(path, TEMPLATE_DIR)
        if '_archived' in rel.split(os.sep):
            archived += 1
            continue
        scanned += 1
        try:
            with open(path, encoding='utf-8') as f:
                env.parse(f.read(), filename=rel)
        except TemplateSyntaxError as e:
            errors.append((rel, e.lineno, str(e)))
        except Exception as e:                      # 编码等其它问题
            errors.append((rel, '-', f'{type(e).__name__}: {e}'))

print(f'扫描 {scanned} 个模板(跳过 _archived {archived} 个)')
if errors:
    print(f'\n✗ {len(errors)} 个模板语法错误:')
    for rel, lineno, msg in errors:
        print(f'  {rel}:{lineno}  {msg}')
    sys.exit(1)
print('✓ 全部解析通过')
