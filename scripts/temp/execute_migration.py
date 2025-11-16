#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""执行数据库迁移脚本"""
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

sys.path.insert(0, get_project_root())

# 避免导入有问题的模块
import importlib.util

# 临时禁用 pdf_generator 的导入
def block_pdf_imports():
    """临时屏蔽PDF相关导入"""
    import sys
    from unittest.mock import MagicMock

    # 创建mock模块
    mock_weasyprint = MagicMock()
    mock_pdf_generator = MagicMock()

    sys.modules['weasyprint'] = mock_weasyprint
    sys.modules['app.services.pdf_generator'] = mock_pdf_generator

# 执行屏蔽
block_pdf_imports()

# 现在可以导入Flask应用
from flask_migrate import upgrade
from app import create_app, db

def main():
    """执行迁移"""
    print("=" * 60)
    print("🚀 开始执行数据库迁移")
    print("=" * 60)

    # 创建应用上下文
    app = create_app()

    with app.app_context():
        try:
            # 执行迁移到特定版本
            target_revision = '20251026_product_spec_base'
            print(f"\n📝 执行迁移到版本: {target_revision}...")
            upgrade(revision=target_revision)

            print("\n✅ 迁移执行成功！")
            return True

        except Exception as e:
            print(f"\n❌ 迁移执行失败: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
