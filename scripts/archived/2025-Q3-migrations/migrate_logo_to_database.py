#!/usr/bin/env python3
"""
Logo数据库迁移脚本
用于云端部署时自动初始化Logo到数据库
"""

import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_logo():
    """迁移Logo到数据库"""
    try:
        from app import create_app, db
        from app.services.logo_service import LogoService
        
        app = create_app()
        
        with app.app_context():
            # 创建数据库表
            db.create_all()
            
            # 初始化默认Logo
            logo = LogoService.init_default_logo()
            
            if logo:
                print(f"✅ Logo迁移成功: {logo.asset_name}")
                return True
            else:
                print("❌ Logo迁移失败")
                return False
                
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("请确保所有依赖项已安装")
        return False
    except Exception as e:
        print(f"❌ Logo迁移过程出错: {e}")
        return False

if __name__ == '__main__':
    print("🔄 开始Logo数据库迁移...")
    success = migrate_logo()
    
    if success:
        print("🎉 Logo数据库迁移完成!")
    else:
        print("⚠️ Logo数据库迁移失败")
    
    sys.exit(0 if success else 1)