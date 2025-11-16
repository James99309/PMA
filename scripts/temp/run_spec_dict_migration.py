#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""运行规格字典迁移脚本"""
import sys
import os

# 路径修正 - 支持从任何位置运行
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

from app import create_app, db
from flask_migrate import upgrade

# 创建应用上下文
app = create_app()

with app.app_context():
    print("🔄 开始运行数据库迁移...")
    try:
        # 运行迁移
        upgrade()
        print("✅ 数据库迁移完成！")

        # 验证表是否创建成功
        from app.models.product_code import SpecificationDictionary
        count = SpecificationDictionary.query.count()
        print(f"✅ 规格字典表创建成功，当前有 {count} 条记录")

        # 显示前5条记录
        specs = SpecificationDictionary.query.limit(5).all()
        print("\n前5条规格记录：")
        for spec in specs:
            unit_str = f" ({spec.unit})" if spec.unit else ""
            print(f"  - {spec.name}{unit_str}")

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
