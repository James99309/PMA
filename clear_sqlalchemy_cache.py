#!/usr/bin/env python3
# 刷新SQLAlchemy缓存
# 使用方法: python3 clear_sqlalchemy_cache.py

from app import create_app, db
from app.models.approval import ApprovalStep

def clear_cache():
    """重置SQLAlchemy映射的表元数据"""
    app = create_app()
    with app.app_context():
        # 刷新数据库模型的表格元数据
        db.Model.metadata.clear()
        db.Model.metadata.reflect(bind=db.engine)
        
        # 打印ApprovalStep表的字段
        if 'approval_step' in db.Model.metadata.tables:
            table = db.Model.metadata.tables['approval_step']
            print(f"ApprovalStep表字段: {', '.join(column.name for column in table.columns)}")
        else:
            print("找不到approval_step表")
        
        return True

if __name__ == "__main__":
    clear_cache() 