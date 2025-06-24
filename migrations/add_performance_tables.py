#!/usr/bin/env python3
"""
添加绩效系统表
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.performance import PerformanceTarget, PerformanceStatistics, FiveStarProjectBaseline

def create_performance_tables():
    """创建绩效系统表"""
    app = create_app()
    
    with app.app_context():
        try:
            # 创建绩效目标表
            db.create_all()
            print("✅ 绩效系统表创建成功")
            
            # 检查表是否存在
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            performance_tables = [
                'performance_targets',
                'performance_statistics', 
                'five_star_project_baselines'
            ]
            
            for table in performance_tables:
                if table in tables:
                    print(f"✅ 表 {table} 已存在")
                else:
                    print(f"❌ 表 {table} 不存在")
            
        except Exception as e:
            print(f"❌ 创建绩效表失败: {e}")
            return False
            
    return True

if __name__ == '__main__':
    success = create_performance_tables()
    if success:
        print("🎉 绩效表迁移完成")
    else:
        print("💥 绩效表迁移失败")
        sys.exit(1) 