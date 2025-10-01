#!/usr/bin/env python3
"""
强制刷新SQLAlchemy模型元数据
清除可能的字段缓存问题
"""

import os
import sys

def force_model_refresh():
    """强制刷新模型元数据"""
    try:
        # 设置Flask应用上下文
        from app import create_app, db
        from app.models.project import Project
        
        app = create_app()
        
        with app.app_context():
            print("正在强制刷新Project模型元数据...")
            
            # 清除SQLAlchemy元数据缓存
            db.metadata.clear()
            
            # 重新反射数据库结构
            db.metadata.reflect(bind=db.engine)
            
            # 检查Project表的实际列
            project_table = db.metadata.tables.get('projects')
            if project_table is not None:
                print("数据库中projects表的实际列:")
                for column in project_table.columns:
                    print(f"  - {column.name}: {column.type}")
                
                # 检查是否还有dealer_manager_id
                if 'dealer_manager_id' in [col.name for col in project_table.columns]:
                    print("❌ 警告: dealer_manager_id字段仍然存在于数据库中!")
                else:
                    print("✅ 确认: dealer_manager_id字段已从数据库中删除")
            
            # 尝试简单查询来测试模型
            try:
                count = Project.query.count()
                print(f"✅ 模型查询测试成功，共有 {count} 个项目")
                return True
            except Exception as e:
                print(f"❌ 模型查询测试失败: {str(e)}")
                return False
                
    except Exception as e:
        print(f"错误: 刷新模型失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = force_model_refresh()
    sys.exit(0 if success else 1) 