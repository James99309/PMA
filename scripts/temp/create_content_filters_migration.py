#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""创建content_filters字段的数据库迁移"""
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
from flask_migrate import migrate as flask_migrate, upgrade

def main():
    """创建并应用迁移"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("📝 创建数据库迁移：add content_filters field to permissions table")
        print("=" * 60)

        try:
            # 生成迁移
            print("\n🔄 正在生成迁移文件...")
            flask_migrate(message="add content_filters field to permissions table")
            print("✅ 迁移文件生成成功")

            # 应用迁移
            print("\n🔄 正在应用迁移...")
            upgrade()
            print("✅ 迁移应用成功")

            print("\n" + "=" * 60)
            print("🎉 数据库迁移完成！")
            print("=" * 60)

        except Exception as e:
            print(f"\n❌ 迁移失败: {e}")
            import traceback
            traceback.print_exc()
            return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
