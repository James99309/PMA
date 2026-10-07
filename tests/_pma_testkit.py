# -*- coding: utf-8 -*-
"""tests/ 下脚本共用的最小骨架:定位项目根 + 在本机 pma_local 上建 app。

复制自 scripts/temp/_report_flow_testkit.make_app,避免 tests/ 依赖临时脚本目录。
禁用 run.py 路径:.env.*.local 里废弃的 Supabase 生产串会 override 掉本地库。
"""
import os
import sys


def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")


def make_app(db_type='sp8d'):
    root = get_project_root()
    if root not in sys.path:
        sys.path.insert(0, root)
    os.chdir(root)
    from dotenv import load_dotenv
    load_dotenv(os.path.join(root, '.env.nas'), override=True)
    os.environ['DATABASE_URL'] = 'postgresql://nijie@localhost:5432/pma_local'
    os.environ['PMA_DB_TYPE'] = db_type
    os.environ['FORCE_LOCAL_STORAGE'] = 'true'
    from config import LocalConfig
    from app import create_app
    return create_app(LocalConfig)
