#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识库内容发布包的路径常量。

包自带全部输入（转换包源、译文、React UMD、封面），不依赖 data/temp，
所以在 NAS 容器里 checkout 出来就能直接跑，构建结果可复现。
"""
import os

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # deploy/knowledge-content
ASSETS = os.path.join(PKG, 'assets')
SRC = os.path.join(ASSETS, 'src')                  # 阅读器源包（dc.html / support.js / content.js）
DOC_JSON = os.path.join(SRC, 'doc.json')  # 结构化全文（译文与表格都按它的节点序号索引）
EN = os.path.join(ASSETS, 'en')                    # translations.json / glossary.json
VENDOR = os.path.join(ASSETS, 'vendor')            # React UMD（内网拉不到 unpkg，必须随包走）
COVERS = os.path.join(ASSETS, 'covers')

# 构建产物：不进 git，落在包外的临时目录
BUILD = os.environ.get('DGTJ_BUILD_DIR') or os.path.join(PKG, '.build')


def project_root():
    """PMA 仓库根（app/ 与 run.py 所在）。"""
    cur = PKG
    while cur != '/':
        if os.path.exists(os.path.join(cur, 'app')) and os.path.exists(os.path.join(cur, 'run.py')):
            return cur
        cur = os.path.dirname(cur)
    raise RuntimeError('无法找到项目根目录')


COURSE_ASSETS = lambda: os.path.join(project_root(), 'app', 'course_assets')
