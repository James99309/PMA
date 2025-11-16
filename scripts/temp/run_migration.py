#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简单的数据库迁移执行脚本"""
import sys
import os

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

project_root = get_project_root()
sys.path.insert(0, project_root)

# 设置环境变量
os.chdir(project_root)

# 使用alembic直接运行迁移
from alembic.config import Config
from alembic import command

try:
    print("📋 开始执行数据库迁移...")

    alembic_ini_path = os.path.join(project_root, "alembic.ini")
    alembic_cfg = Config(alembic_ini_path)

    # 显示当前版本
    print("\n当前数据库版本：")
    command.current(alembic_cfg)

    # 执行升级
    print("\n执行迁移升级...")
    command.upgrade(alembic_cfg, "head")

    print("\n✅ 数据库迁移完成")

    # 显示新版本
    print("\n新的数据库版本：")
    command.current(alembic_cfg)

except Exception as e:
    print(f"\n❌ 迁移失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
