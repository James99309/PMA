#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速版本修复脚本

专门针对云端部署版本不一致问题的快速修复脚本。
适用场景：云端显示v1.0.1，实际应该是v1.3.5

使用方法：
1. 上传此脚本到云端服务器
2. python quick_version_fix.py
3. 重启应用服务

特点：
- 无需复杂配置
- 自动检测版本文件
- 快速修复数据库记录
- 提供详细的操作日志
"""

import os
import sys
import json
import logging
from datetime import datetime

# 简单的日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def quick_fix():
    """快速修复版本不一致问题"""
    
    print("=" * 60)
    print("🚀 PMA 云端版本快速修复工具")
    print("=" * 60)
    
    try:
        # 1. 读取app_version.json
        version_file = 'app_version.json'
        if not os.path.exists(version_file):
            print(f"❌ 错误：找不到版本文件 {version_file}")
            return False
        
        with open(version_file, 'r') as f:
            version_data = json.load(f)
            target_version = version_data.get('app_version', '1.3.5')
        
        print(f"📖 读取到目标版本：{target_version}")
        
        # 2. 初始化Flask应用（简化版）
        print("🔧 初始化应用环境...")
        
        # 添加项目路径
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        # 导入必要模块
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.models.version_management import VersionRecord, UpgradeLog
            from app.extensions import db
            
            # 3. 检查当前数据库版本
            current_version = VersionRecord.get_current_version()
            if current_version:
                current_ver = current_version.version_number
                print(f"📊 当前数据库版本：{current_ver}")
                
                if current_ver == target_version:
                    print("✅ 版本已经正确，无需修复")
                    return True
            else:
                current_ver = "无版本记录"
                print("⚠️  数据库中没有当前版本记录")
            
            # 4. 执行快速修复
            print(f"🔄 开始修复：{current_ver} → {target_version}")
            
            # 检查目标版本是否存在
            existing_version = VersionRecord.query.filter_by(version_number=target_version).first()
            
            if existing_version:
                print(f"✅ 找到现有版本记录，设置为当前版本")
                # 设置为当前版本
                VersionRecord.query.update({'is_current': False})
                existing_version.is_current = True
                version_record = existing_version
            else:
                print(f"🔧 创建新版本记录：{target_version}")
                # 创建新版本
                VersionRecord.query.update({'is_current': False})
                
                version_record = VersionRecord(
                    version_number=target_version,
                    version_name=f'PMA项目管理系统 {target_version}',
                    description=f'云端版本修复：从 {current_ver} 更新到 {target_version}。包含最新的功能改进、界面优化和系统增强。',
                    is_current=True,
                    environment='production',
                    release_date=datetime.now()
                )
                db.session.add(version_record)
                db.session.flush()  # 获取ID
            
            # 5. 创建升级日志
            print("📝 创建升级日志...")
            upgrade_log = UpgradeLog(
                version_id=version_record.id,
                from_version=current_ver if current_ver != "无版本记录" else None,
                to_version=target_version,
                upgrade_type='quick_fix',
                status='success',
                operator_name='快速修复工具',
                environment='production',
                upgrade_notes=f'云端版本快速修复：解决版本显示不一致问题',
                upgrade_date=datetime.now()
            )
            db.session.add(upgrade_log)
            
            # 6. 提交更改
            db.session.commit()
            print("✅ 数据库更新成功")
            
            # 7. 验证修复结果
            verify_version = VersionRecord.get_current_version()
            if verify_version and verify_version.version_number == target_version:
                print(f"🎉 修复成功！当前版本：{verify_version.version_number}")
                print(f"📅 发布日期：{verify_version.release_date}")
                return True
            else:
                print("❌ 修复验证失败")
                return False
                
    except Exception as e:
        print(f"❌ 修复失败：{str(e)}")
        logger.error(f"详细错误：{str(e)}", exc_info=True)
        return False

def main():
    """主函数"""
    success = quick_fix()
    
    if success:
        print("")
        print("=" * 60)
        print("✅ 版本修复完成！")
        print("=" * 60)
        print("")
        print("📋 后续操作：")
        print("1. 重启应用服务（如：sudo systemctl restart pma-app）")
        print("2. 访问版本管理页面验证显示")
        print("3. 检查仪表盘版本号显示")
        print("4. 确认升级信息加载正常")
        print("")
        return 0
    else:
        print("")
        print("=" * 60)
        print("❌ 版本修复失败！")
        print("=" * 60)
        print("")
        print("🔧 排查建议：")
        print("1. 检查数据库连接是否正常")
        print("2. 确认app_version.json文件存在")
        print("3. 检查文件权限和环境变量")
        print("4. 查看详细错误日志")
        print("")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)