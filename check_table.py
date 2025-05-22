#!/usr/bin/env python3
# 检查表结构
from app import create_app, db
from sqlalchemy import inspect

def check_table():
    app = create_app()
    with app.app_context():
        # 获取表结构信息
        inspector = inspect(db.engine)
        cols = inspector.get_columns('approval_record')
        
        # 打印所有列信息
        for col in cols:
            print(f"列名: {col['name']}, 类型: {col['type']}, 可为空: {col.get('nullable')}")
        
        # 特别查看action列的类型
        action_col = next((c for c in cols if c['name'] == 'action'), None)
        if action_col:
            print("\n特别检查action列:")
            print(f"类型: {action_col['type']}")
            print(f"类型名称: {action_col['type'].__class__.__name__}")
            if hasattr(action_col['type'], 'enums'):
                print(f"枚举值: {action_col['type'].enums}")

if __name__ == "__main__":
    check_table() 