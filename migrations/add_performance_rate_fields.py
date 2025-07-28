#!/usr/bin/env python3
"""
添加绩效目标合格值字段
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

def add_performance_rate_fields():
    """添加绩效目标合格值字段"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查表是否存在
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'performance_targets' not in tables:
                print("❌ performance_targets 表不存在，请先运行基础表创建")
                return False
            
            # 检查字段是否已存在
            columns = [col['name'] for col in inspector.get_columns('performance_targets')]
            
            rate_fields = [
                'implant_rate',
                'sales_rate', 
                'customers_rate',
                'projects_rate'
            ]
            
            # 添加缺失的字段
            for field in rate_fields:
                if field not in columns:
                    try:
                        # 使用原生SQL添加字段
                        sql = f"""
                        ALTER TABLE performance_targets 
                        ADD COLUMN {field} INTEGER DEFAULT 0;
                        """
                        db.session.execute(db.text(sql))
                        db.session.commit()
                        print(f"✅ 已添加字段: {field}")
                    except Exception as e:
                        print(f"❌ 添加字段 {field} 失败: {e}")
                        db.session.rollback()
                        return False
                else:
                    print(f"✅ 字段 {field} 已存在")
            
            # 验证所有字段
            updated_columns = [col['name'] for col in inspector.get_columns('performance_targets')]
            for field in rate_fields:
                if field in updated_columns:
                    print(f"✅ 验证字段: {field}")
                else:
                    print(f"❌ 验证失败，字段不存在: {field}")
                    return False
            
            print("🎉 绩效合格值字段添加完成")
            return True
            
        except Exception as e:
            print(f"❌ 迁移失败: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = add_performance_rate_fields()
    if success:
        print("🎉 绩效合格值字段迁移完成")
    else:
        print("💥 绩效合格值字段迁移失败")
        sys.exit(1)