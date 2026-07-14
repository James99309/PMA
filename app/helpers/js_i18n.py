# -*- coding: utf-8 -*-
"""客户端 JS i18n:扫描已接入的 JS 文件里的 t('中文') 调用,
运行时用 gettext 生成 {中文: 英文} 字典注入 window.I18N(随当前 locale)。

新增需要 i18n 的 JS:加入 _JS_FILES,并把 'x' 改成 t('x')。"""
import os
import re
from functools import lru_cache

_JS_FILES = [
    'at-item-table.js',
    'at-product-picker.js',
    'product-detail-manager.js',
    'product-config-modal.js',
    'at-approval-dropdown.js',
    'at-ai-research.js',
    'at-file-preview.js',
    'at-worklog-calendar.js',
    'at-rich-note.js',
    'at-comments.js',
    'at-file-manager.js',
    'at-file-manager-admin.js',
    'at-task-detail.js',
    'at-expense-form.js',
    'at-target-sheet.js',
    'favorite-star.js',
]
# 匹配 t('..') 与 _t('..')(带兜底前缀);均不被 \w/.$ 前导,避免命中 format( 等
_PAT = re.compile(r"""(?<![\w.$])_?t\(\s*(['"])(.*?)\1""")


def _has_cjk(s):
    return any('一' <= c <= '鿿' for c in s)


@lru_cache(maxsize=1)
def js_i18n_keys():
    base = os.path.join(os.path.dirname(__file__), '..', 'static', 'js')
    keys = set()
    for fn in _JS_FILES:
        p = os.path.join(base, fn)
        if not os.path.exists(p):
            continue
        try:
            txt = open(p, encoding='utf-8').read()
        except Exception:
            continue
        for m in _PAT.finditer(txt):
            s = m.group(2)
            if _has_cjk(s):
                keys.add(s)
    return tuple(sorted(keys))


def js_i18n_map():
    """{中文: 当前 locale 译文};供模板渲染 window.I18N。"""
    from flask_babel import gettext
    return {k: gettext(k) for k in js_i18n_keys()}
