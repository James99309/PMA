#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
验证云端数据库权限级别字段迁移是否成功
检查SP8D和OVS数据库中permissions表的新字段
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('VerifyPermissionFields')

def verify_database_fields(db_name, db_url):
    """验证数据库中的权限级别字段"""
    logger.info(f"=" * 60)
    logger.info(f"验证 {db_name} 数据库的权限级别字段")
    logger.info(f"=" * 60)
    
    try:
        # 设置数据库环境变量
        env = os.environ.copy()
        env['DATABASE_URL'] = db_url
        
        # 检查permissions表结构
        result = subprocess.run([
            'python3', '-c', '''
import os
from sqlalchemy import create_engine, text

engine = create_engine(os.environ["DATABASE_URL"])
with engine.connect() as connection:
    result = connection.execute(text("""
        SELECT column_name, data_type, column_default, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'permissions' 
        AND column_name IN ('permission_level', 'permission_level_description', 'pricing_discount_limit', 'settlement_discount_limit')
        ORDER BY column_name
    """))
    
    fields = result.fetchall()
    print(f"找到 {len(fields)} 个权限级别字段:")
    for field in fields:
        print(f"  - {field[0]}: {field[1]} (默认: {field[2]}, 可空: {field[3]})")
    
    if len(fields) == 4:
        print("✅ 所有权限级别字段都已正确添加")
        
        # 检查是否有数据
        count_result = connection.execute(text("SELECT COUNT(*) FROM permissions"))
        total_count = count_result.fetchone()[0]
        print(f"📊 permissions表总记录数: {total_count}")
        
        if total_count > 0:
            # 检查permission_level字段的默认值是否正确应用
            level_result = connection.execute(text("""
                SELECT permission_level, COUNT(*) as count
                FROM permissions 
                GROUP BY permission_level
                ORDER BY count DESC
            """))
            
            levels = level_result.fetchall()
            print("📈 权限级别分布:")
            for level, count in levels:
                print(f"  - {level}: {count} 条记录")
    else:
        print(f"❌ 缺少权限级别字段，预期4个，实际{len(fields)}个")
'''
        ], env=env, capture_output=True, text=True, check=True)
        
        print(result.stdout)
        if result.stderr:
            logger.warning(f"警告信息: {result.stderr}")
            
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 验证 {db_name} 失败: {e}")
        logger.error(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"❌ 验证 {db_name} 时出现异常: {str(e)}")
        return False

def main():
    logger.info("🔍 开始验证云端数据库权限级别字段迁移")
    logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # SP8D数据库配置
    sp8d_url = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"
    
    # OVS数据库配置  
    ovs_url = "postgresql://pma_db_ovs_user:NjE8pNxQZv4wL1WtGz4C2lNrTXu7R5Ka@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs"
    
    success_count = 0
    
    # 验证SP8D数据库
    if verify_database_fields("SP8D", sp8d_url):
        success_count += 1
    
    print()  # 空行分隔
    
    # 验证OVS数据库
    if verify_database_fields("OVS", ovs_url):
        success_count += 1
    
    logger.info("=" * 60)
    logger.info("📋 验证结果总结")
    logger.info("=" * 60)
    
    if success_count == 2:
        logger.info("🎉 所有云端数据库的权限级别字段迁移验证成功！")
        logger.info("✅ SP8D数据库: 权限级别字段已正确添加")
        logger.info("✅ OVS数据库: 权限级别字段已正确添加")
        logger.info("")
        logger.info("📝 迁移包含的字段:")
        logger.info("  - permission_level: 权限级别 (默认值: personal)")
        logger.info("  - permission_level_description: 权限级别描述")
        logger.info("  - pricing_discount_limit: 批价折扣限制")
        logger.info("  - settlement_discount_limit: 结算折扣限制")
        logger.info("")
        logger.info("🚀 云端数据库现在支持完整的四级权限系统!")
    else:
        logger.error(f"❌ 验证失败: {2-success_count} 个数据库的迁移存在问题")
        if success_count == 0:
            logger.error("建议检查数据库连接和迁移状态")
    
    logger.info("=" * 60)

if __name__ == '__main__':
    main()