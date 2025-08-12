#!/usr/bin/env python3
"""
诊断 OVS 数据库连接问题
"""

import os
import psycopg2
from urllib.parse import urlparse
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('OVS诊断')

def diagnose_ovs_database():
    """诊断OVS数据库连接和数据状态"""
    
    # OVS数据库连接字符串（需要从环境变量或配置获取）
    ovs_urls = [
        # Render OVS database URLs
        "postgresql://pma_db_ovs_user:your_password@dpg-xxx-a.oregon-postgres.render.com/pma_db_ovs",
        # 其他可能的连接
    ]
    
    # 尝试从备份文件或其他配置文件中获取连接信息
    possible_config_files = [
        '/Users/nijie/Documents/PMA/config.py',
        '/Users/nijie/Documents/PMA/render_env_config.txt',
        '/Users/nijie/Documents/PMA/simple_ovs_backup.py'
    ]
    
    logger.info("=== OVS数据库连接诊断 ===")
    
    # 检查配置文件中的数据库连接
    for config_file in possible_config_files:
        if os.path.exists(config_file):
            logger.info(f"检查配置文件: {config_file}")
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'pma_db_ovs' in content:
                        logger.info(f"在 {config_file} 中找到OVS数据库配置")
                        # 提取数据库URL的行
                        for line in content.split('\n'):
                            if 'pma_db_ovs' in line and ('postgresql://' in line or 'postgres://' in line):
                                logger.info(f"数据库连接配置: {line[:50]}...")
                                
                                # 提取URL（简单方式）
                                import re
                                url_match = re.search(r'postgresql://[^\s\'"]+', line)
                                if url_match:
                                    db_url = url_match.group()
                                    logger.info(f"提取到数据库URL: {db_url[:30]}...")
                                    
                                    # 测试连接
                                    try:
                                        logger.info("尝试连接数据库...")
                                        conn = psycopg2.connect(db_url)
                                        cursor = conn.cursor()
                                        
                                        # 检查数据库连接
                                        cursor.execute('SELECT version();')
                                        version = cursor.fetchone()
                                        logger.info(f"✅ 数据库连接成功: PostgreSQL")
                                        
                                        # 检查users表
                                        cursor.execute("SELECT COUNT(*) FROM users;")
                                        user_count = cursor.fetchone()[0]
                                        logger.info(f"📊 users表记录数: {user_count}")
                                        
                                        if user_count > 0:
                                            # 检查ID为1的用户
                                            cursor.execute("SELECT id, username, is_active FROM users WHERE id = 1;")
                                            user_1 = cursor.fetchone()
                                            
                                            if user_1:
                                                logger.info(f"✅ 用户ID=1存在: ID={user_1[0]}, 用户名={user_1[1]}, 活跃={user_1[2]}")
                                            else:
                                                logger.warning("❌ 用户ID=1不存在")
                                                
                                                # 查看现有用户
                                                cursor.execute("SELECT id, username, is_active FROM users ORDER BY id LIMIT 5;")
                                                users = cursor.fetchall()
                                                logger.info("前5个用户:")
                                                for user in users:
                                                    logger.info(f"  ID={user[0]}, 用户名={user[1]}, 活跃={user[2]}")
                                        else:
                                            logger.error("❌ users表为空！")
                                            
                                            # 检查其他表的情况
                                            cursor.execute("""
                                                SELECT table_name, 
                                                       (SELECT COUNT(*) FROM information_schema.columns 
                                                        WHERE table_name = t.table_name) as column_count
                                                FROM information_schema.tables t
                                                WHERE table_schema = 'public' 
                                                AND table_type = 'BASE TABLE'
                                                ORDER BY table_name
                                                LIMIT 10;
                                            """)
                                            tables = cursor.fetchall()
                                            logger.info(f"数据库中的表 (前10个):")
                                            for table in tables:
                                                cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
                                                count = cursor.fetchone()[0]
                                                logger.info(f"  - {table[0]}: {count} 行记录")
                                        
                                        cursor.close()
                                        conn.close()
                                        return True
                                        
                                    except psycopg2.OperationalError as e:
                                        logger.error(f"❌ 数据库连接失败: {e}")
                                        logger.info("可能的原因:")
                                        logger.info("1. 数据库服务器不可达")
                                        logger.info("2. 连接参数错误或过期")
                                        logger.info("3. 网络问题")
                                        logger.info("4. 数据库服务暂停或维护中")
                                        
                                    except Exception as e:
                                        logger.error(f"❌ 其他数据库错误: {e}")
                                        
            except Exception as e:
                logger.error(f"读取配置文件失败: {e}")
    
    logger.error("❌ 无法找到或连接到OVS数据库")
    logger.info("建议解决方案:")
    logger.info("1. 检查网络连接")
    logger.info("2. 验证数据库连接参数")
    logger.info("3. 联系云服务提供商检查数据库状态")
    logger.info("4. 考虑从最新备份恢复数据库")
    
    return False

if __name__ == "__main__":
    diagnose_ovs_database()