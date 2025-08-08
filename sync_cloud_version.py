#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
云端版本同步脚本

此脚本用于解决云端部署版本不一致问题：
1. 读取app_version.json文件获取实际版本
2. 同步数据库中的版本记录
3. 创建升级日志记录
4. 集成升级说明文档

使用场景：
- 云端部署后版本显示不正确
- 数据库版本与应用版本不匹配
- 需要强制同步版本状态

运行方式：
python sync_cloud_version.py
"""

import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# 添加项目路径到sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sync_cloud_version.log')
    ]
)
logger = logging.getLogger(__name__)

def read_app_version():
    """读取app_version.json文件获取当前版本信息"""
    try:
        version_file = os.path.join(project_root, 'app_version.json')
        if not os.path.exists(version_file):
            logger.error(f"版本文件不存在: {version_file}")
            return None
            
        with open(version_file, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
            
        logger.info(f"读取到版本信息: {version_data.get('app_version', 'unknown')}")
        return version_data
        
    except Exception as e:
        logger.error(f"读取版本文件失败: {str(e)}")
        return None

def get_git_commit_info():
    """获取当前Git提交信息"""
    try:
        import subprocess
        
        # 获取最新提交哈希
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                              capture_output=True, text=True, cwd=project_root)
        if result.returncode == 0:
            commit_hash = result.stdout.strip()
            
            # 获取提交日期
            result = subprocess.run(['git', 'show', '-s', '--format=%ci', commit_hash],
                                  capture_output=True, text=True, cwd=project_root)
            if result.returncode == 0:
                commit_date_str = result.stdout.strip()
                commit_date = datetime.strptime(commit_date_str[:19], '%Y-%m-%d %H:%M:%S')
                
                return {
                    'hash': commit_hash,
                    'date': commit_date
                }
        
        logger.warning("无法获取Git提交信息")
        return None
        
    except Exception as e:
        logger.error(f"获取Git信息失败: {str(e)}")
        return None

def generate_upgrade_description(from_version, to_version):
    """生成升级说明描述"""
    
    # 尝试使用release_notes_generator生成智能说明
    try:
        from app.utils.release_notes_generator import create_release_notes_for_version
        
        # 生成基于变更的升级说明
        release_notes = create_release_notes_for_version(to_version)
        if release_notes:
            return f"## 版本升级：{from_version} → {to_version}\n\n{release_notes}"
            
    except Exception as e:
        logger.warning(f"自动生成升级说明失败: {str(e)}")
    
    # 回退到手动说明
    return f"""## PMA 项目管理系统 {to_version} 升级说明

### 📅 升级信息
- **升级版本**: {from_version} → {to_version}
- **升级时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
- **升级类型**: 云端版本同步

### 🎯 升级内容
此次升级主要是同步云端部署的版本状态，确保：
- ✅ 版本号显示一致性
- ✅ 数据库记录准确性  
- ✅ 升级日志完整性
- ✅ 功能模块正常运行

### 🚀 功能特性
- **完整项目管理功能**: 项目创建、跟踪、评估
- **客户关系管理**: 客户信息、项目关联
- **报价管理系统**: 智能报价、模板管理
- **产品管理**: 产品库存、规格管理
- **用户权限管理**: 角色分配、权限控制
- **版本管理系统**: 升级追踪、变更记录

### 📋 技术改进
- 统一版本管理机制
- 优化数据库版本同步
- 改进云端部署流程
- 增强版本一致性检查

---

*升级完成后，请验证各功能模块正常运行*
"""

def sync_version_to_database():
    """将版本信息同步到数据库"""
    try:
        # 初始化Flask应用
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.models.version_management import VersionRecord, UpgradeLog
            from app.extensions import db
            
            # 读取版本信息
            version_data = read_app_version()
            if not version_data:
                return False
                
            target_version = version_data.get('app_version', '1.3.5')
            logger.info(f"目标同步版本: {target_version}")
            
            # 获取当前数据库版本
            current_db_version = VersionRecord.get_current_version()
            if current_db_version:
                current_version_number = current_db_version.version_number
                logger.info(f"当前数据库版本: {current_version_number}")
                
                if current_version_number == target_version:
                    logger.info("版本已经是最新，无需同步")
                    return True
            else:
                current_version_number = "1.0.0"
                logger.info("数据库中没有当前版本记录")
            
            # 检查目标版本是否已存在
            existing_version = VersionRecord.query.filter_by(version_number=target_version).first()
            
            if existing_version:
                # 版本存在，设置为当前版本
                logger.info(f"版本 {target_version} 已存在，设置为当前版本")
                VersionRecord.query.update({'is_current': False})
                existing_version.is_current = True
                target_version_record = existing_version
            else:
                # 创建新版本记录
                logger.info(f"创建新版本记录: {target_version}")
                
                # 获取Git信息
                git_info = get_git_commit_info()
                
                # 设置所有现有版本为非当前版本
                VersionRecord.query.update({'is_current': False})
                
                # 创建新版本
                target_version_record = VersionRecord(
                    version_number=target_version,
                    version_name=f'PMA项目管理系统 {target_version}',
                    description=generate_upgrade_description(current_version_number, target_version),
                    is_current=True,
                    environment=version_data.get('environment', 'production'),
                    git_commit=git_info['hash'] if git_info else None,
                    release_date=git_info['date'] if git_info else datetime.now(),
                    total_features=0,  # 实际值需要分析代码变更获得
                    total_fixes=0,
                    total_improvements=0
                )
                
                db.session.add(target_version_record)
            
            # 创建升级日志
            upgrade_log = UpgradeLog(
                version_id=target_version_record.id,
                from_version=current_version_number,
                to_version=target_version,
                upgrade_type='deployment_sync',
                status='success',
                operator_name='云端同步系统',
                environment=version_data.get('environment', 'production'),
                upgrade_notes=f'云端版本同步：数据库版本从 {current_version_number} 同步至 {target_version}',
                upgrade_date=datetime.now()
            )
            
            db.session.add(upgrade_log)
            db.session.commit()
            
            logger.info(f"✅ 版本同步成功: {current_version_number} → {target_version}")
            logger.info("✅ 升级日志已记录")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ 版本同步失败: {str(e)}")
        try:
            db.session.rollback()
        except:
            pass
        return False

def validate_version_sync():
    """验证版本同步结果"""
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.models.version_management import VersionRecord
            
            # 验证当前版本
            current_version = VersionRecord.get_current_version()
            if current_version:
                logger.info(f"✅ 当前数据库版本: {current_version.version_number}")
                logger.info(f"✅ 发布日期: {current_version.release_date}")
                logger.info(f"✅ 是否为当前版本: {current_version.is_current}")
                return True
            else:
                logger.error("❌ 验证失败：没有找到当前版本记录")
                return False
                
    except Exception as e:
        logger.error(f"❌ 验证版本同步失败: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🚀 开始云端版本同步")
    logger.info("=" * 60)
    
    try:
        # 执行版本同步
        success = sync_version_to_database()
        if not success:
            logger.error("❌ 版本同步失败")
            return 1
            
        # 验证同步结果
        success = validate_version_sync()
        if not success:
            logger.error("❌ 版本验证失败")
            return 1
            
        logger.info("=" * 60)
        logger.info("✅ 云端版本同步完成")
        logger.info("=" * 60)
        logger.info("")
        logger.info("下一步操作建议:")
        logger.info("1. 重新启动应用服务")
        logger.info("2. 访问版本管理页面验证显示")
        logger.info("3. 检查升级日志记录")
        logger.info("4. 确认所有功能模块正常")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ 云端版本同步异常: {str(e)}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)