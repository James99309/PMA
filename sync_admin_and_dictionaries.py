#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步admin用户和字典表数据到云端数据库
1. 检查云端数据库的用户表和字典表数据
2. 从本地数据库获取admin用户数据
3. 同步字典表数据到云端
"""

import psycopg2
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
LOCAL_DB_URL = "postgresql://nijie@localhost:5432/pma_local"
CLOUD_DB_URL = "postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs"

def test_connections():
    """测试数据库连接"""
    try:
        # 测试本地连接
        local_conn = psycopg2.connect(LOCAL_DB_URL)
        local_conn.close()
        logger.info("✅ 本地数据库连接成功")
        
        # 测试云端连接
        cloud_conn = psycopg2.connect(CLOUD_DB_URL)
        cloud_conn.close()
        logger.info("✅ 云端数据库连接成功")
        
        return True
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return False

def check_cloud_data():
    """检查云端数据库的数据情况"""
    try:
        logger.info("🔍 检查云端数据库数据情况...")
        cloud_conn = psycopg2.connect(CLOUD_DB_URL)
        cursor = cloud_conn.cursor()
        
        # 检查用户表数据
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        logger.info(f"📊 云端用户数量: {user_count}")
        
        # 检查字典表数据
        dictionary_tables = [
            'affiliations',      # 企业字典
            'dictionaries',      # 通用字典
            'product_categories' # 产品分类字典
        ]
        
        dict_data = {}
        for table in dictionary_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                dict_data[table] = count
                logger.info(f"📊 云端{table}表数据: {count}条")
            except Exception as e:
                logger.warning(f"⚠️ 检查{table}表失败: {e}")
                dict_data[table] = 0
        
        cursor.close()
        cloud_conn.close()
        
        return user_count, dict_data
        
    except Exception as e:
        logger.error(f"❌ 检查云端数据失败: {e}")
        return 0, {}

def get_local_admin_user():
    """获取本地admin用户数据"""
    try:
        logger.info("🔍 获取本地admin用户数据...")
        local_conn = psycopg2.connect(LOCAL_DB_URL)
        cursor = local_conn.cursor()
        
        # 查找admin用户
        cursor.execute("""
            SELECT id, username, password_hash, real_name, company_name, email, 
                   phone, department, is_department_manager, role, is_profile_complete,
                   wechat_openid, wechat_nickname, wechat_avatar, is_active, 
                   created_at, last_login, updated_at
            FROM users 
            WHERE username = 'admin' OR role = 'admin'
            ORDER BY id
        """)
        
        admin_users = cursor.fetchall()
        logger.info(f"📊 找到本地admin用户: {len(admin_users)}个")
        
        for user in admin_users:
            logger.info(f"   - ID: {user[0]}, 用户名: {user[1]}, 角色: {user[9]}")
        
        cursor.close()
        local_conn.close()
        
        return admin_users
        
    except Exception as e:
        logger.error(f"❌ 获取本地admin用户失败: {e}")
        return []

def sync_admin_users(admin_users):
    """同步admin用户到云端"""
    if not admin_users:
        logger.warning("⚠️ 没有找到admin用户，跳过同步")
        return False
    
    try:
        logger.info("🔄 开始同步admin用户到云端...")
        cloud_conn = psycopg2.connect(CLOUD_DB_URL)
        cursor = cloud_conn.cursor()
        
        synced_count = 0
        for user in admin_users:
            try:
                # 检查用户是否已存在
                cursor.execute("SELECT id FROM users WHERE username = %s", (user[1],))
                existing = cursor.fetchone()
                
                if existing:
                    logger.info(f"   用户 {user[1]} 已存在，跳过")
                    continue
                
                # 插入用户数据
                cursor.execute("""
                    INSERT INTO users (
                        username, password_hash, real_name, company_name, email,
                        phone, department, is_department_manager, role, is_profile_complete,
                        wechat_openid, wechat_nickname, wechat_avatar, is_active,
                        created_at, last_login, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user[1], user[2], user[3], user[4], user[5],
                    user[6], user[7], user[8], user[9], user[10],
                    user[11], user[12], user[13], user[14],
                    user[15], user[16], user[17]
                ))
                
                synced_count += 1
                logger.info(f"   ✅ 同步用户: {user[1]} (角色: {user[9]})")
                
            except Exception as e:
                logger.error(f"   ❌ 同步用户 {user[1]} 失败: {e}")
        
        cloud_conn.commit()
        cursor.close()
        cloud_conn.close()
        
        logger.info(f"✅ admin用户同步完成，共同步 {synced_count} 个用户")
        return synced_count > 0
        
    except Exception as e:
        logger.error(f"❌ 同步admin用户失败: {e}")
        return False

def get_local_dictionary_data():
    """获取本地字典表数据"""
    try:
        logger.info("🔍 获取本地字典表数据...")
        local_conn = psycopg2.connect(LOCAL_DB_URL)
        cursor = local_conn.cursor()
        
        dictionary_data = {}
        
        # 获取企业字典数据
        try:
            cursor.execute("SELECT * FROM affiliations ORDER BY id")
            affiliations = cursor.fetchall()
            dictionary_data['affiliations'] = affiliations
            logger.info(f"📊 本地企业字典: {len(affiliations)}条")
        except Exception as e:
            logger.warning(f"⚠️ 获取企业字典失败: {e}")
            dictionary_data['affiliations'] = []
        
        # 获取通用字典数据
        try:
            cursor.execute("SELECT * FROM dictionaries ORDER BY id")
            dictionaries = cursor.fetchall()
            dictionary_data['dictionaries'] = dictionaries
            logger.info(f"📊 本地通用字典: {len(dictionaries)}条")
        except Exception as e:
            logger.warning(f"⚠️ 获取通用字典失败: {e}")
            dictionary_data['dictionaries'] = []
        
        # 获取产品分类字典数据
        try:
            cursor.execute("SELECT * FROM product_categories ORDER BY id")
            product_categories = cursor.fetchall()
            dictionary_data['product_categories'] = product_categories
            logger.info(f"📊 本地产品分类字典: {len(product_categories)}条")
        except Exception as e:
            logger.warning(f"⚠️ 获取产品分类字典失败: {e}")
            dictionary_data['product_categories'] = []
        
        cursor.close()
        local_conn.close()
        
        return dictionary_data
        
    except Exception as e:
        logger.error(f"❌ 获取本地字典数据失败: {e}")
        return {}

def sync_dictionary_data(dictionary_data):
    """同步字典数据到云端"""
    if not dictionary_data:
        logger.warning("⚠️ 没有字典数据，跳过同步")
        return False
    
    try:
        logger.info("🔄 开始同步字典数据到云端...")
        cloud_conn = psycopg2.connect(CLOUD_DB_URL)
        cursor = cloud_conn.cursor()
        
        # 同步企业字典
        if dictionary_data.get('affiliations'):
            logger.info("   同步企业字典...")
            # 先清空现有数据
            cursor.execute("DELETE FROM affiliations")
            
            # 获取字段信息
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'affiliations' 
                ORDER BY ordinal_position
            """)
            columns = [row[0] for row in cursor.fetchall()]
            
            # 插入数据
            placeholders = ', '.join(['%s'] * len(columns))
            cursor.executemany(
                f"INSERT INTO affiliations ({', '.join(columns)}) VALUES ({placeholders})",
                dictionary_data['affiliations']
            )
            logger.info(f"   ✅ 企业字典同步完成: {len(dictionary_data['affiliations'])}条")
        
        # 同步通用字典
        if dictionary_data.get('dictionaries'):
            logger.info("   同步通用字典...")
            # 先清空现有数据
            cursor.execute("DELETE FROM dictionaries")
            
            # 获取字段信息
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'dictionaries' 
                ORDER BY ordinal_position
            """)
            columns = [row[0] for row in cursor.fetchall()]
            
            # 插入数据
            placeholders = ', '.join(['%s'] * len(columns))
            cursor.executemany(
                f"INSERT INTO dictionaries ({', '.join(columns)}) VALUES ({placeholders})",
                dictionary_data['dictionaries']
            )
            logger.info(f"   ✅ 通用字典同步完成: {len(dictionary_data['dictionaries'])}条")
        
        # 同步产品分类字典
        if dictionary_data.get('product_categories'):
            logger.info("   同步产品分类字典...")
            # 先清空现有数据
            cursor.execute("DELETE FROM product_categories")
            
            # 获取字段信息
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'product_categories' 
                ORDER BY ordinal_position
            """)
            columns = [row[0] for row in cursor.fetchall()]
            
            # 插入数据
            placeholders = ', '.join(['%s'] * len(columns))
            cursor.executemany(
                f"INSERT INTO product_categories ({', '.join(columns)}) VALUES ({placeholders})",
                dictionary_data['product_categories']
            )
            logger.info(f"   ✅ 产品分类字典同步完成: {len(dictionary_data['product_categories'])}条")
        
        cloud_conn.commit()
        cursor.close()
        cloud_conn.close()
        
        logger.info("✅ 字典数据同步完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 同步字典数据失败: {e}")
        return False

def verify_sync_result():
    """验证同步结果"""
    try:
        logger.info("🔄 验证同步结果...")
        cloud_conn = psycopg2.connect(CLOUD_DB_URL)
        cursor = cloud_conn.cursor()
        
        # 检查admin用户
        cursor.execute("SELECT username, role FROM users WHERE role = 'admin' OR username = 'admin'")
        admin_users = cursor.fetchall()
        logger.info(f"📊 云端admin用户: {len(admin_users)}个")
        for user in admin_users:
            logger.info(f"   - 用户名: {user[0]}, 角色: {user[1]}")
        
        # 检查字典数据
        cursor.execute("SELECT COUNT(*) FROM affiliations")
        affiliations_count = cursor.fetchone()[0]
        logger.info(f"📊 云端企业字典: {affiliations_count}条")
        
        cursor.execute("SELECT COUNT(*) FROM dictionaries")
        dictionaries_count = cursor.fetchone()[0]
        logger.info(f"📊 云端通用字典: {dictionaries_count}条")
        
        cursor.execute("SELECT COUNT(*) FROM product_categories")
        categories_count = cursor.fetchone()[0]
        logger.info(f"📊 云端产品分类字典: {categories_count}条")
        
        cursor.close()
        cloud_conn.close()
        
        return len(admin_users) > 0 and (affiliations_count > 0 or dictionaries_count > 0 or categories_count > 0)
        
    except Exception as e:
        logger.error(f"❌ 验证同步结果失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("🚀 同步admin用户和字典数据到云端数据库")
    print("=" * 80)
    print("📋 任务说明:")
    print("   1. 检查云端数据库的用户表和字典表数据")
    print("   2. 从本地数据库获取admin用户数据")
    print("   3. 同步字典表数据到云端")
    print("=" * 80)
    
    # 1. 测试数据库连接
    print("\n📋 步骤1: 测试数据库连接")
    if not test_connections():
        print("❌ 数据库连接失败，无法继续")
        return False
    
    # 2. 检查云端数据情况
    print("\n📋 步骤2: 检查云端数据情况")
    user_count, dict_data = check_cloud_data()
    
    # 3. 获取本地admin用户
    print("\n📋 步骤3: 获取本地admin用户")
    admin_users = get_local_admin_user()
    
    # 4. 同步admin用户
    print("\n📋 步骤4: 同步admin用户到云端")
    if not sync_admin_users(admin_users):
        print("⚠️ admin用户同步失败或跳过")
    
    # 5. 获取本地字典数据
    print("\n📋 步骤5: 获取本地字典数据")
    dictionary_data = get_local_dictionary_data()
    
    # 6. 同步字典数据
    print("\n📋 步骤6: 同步字典数据到云端")
    if not sync_dictionary_data(dictionary_data):
        print("⚠️ 字典数据同步失败或跳过")
    
    # 7. 验证同步结果
    print("\n📋 步骤7: 验证同步结果")
    if verify_sync_result():
        print("✅ 同步验证成功")
    else:
        print("⚠️ 同步验证有问题，请检查")
    
    print("\n🎉 同步任务完成！")
    print("💡 现在您可以使用以下方式登录云端系统：")
    print("   - 用户名: admin")
    print("   - 密码: 原admin密码 或 超级密码 1505562299AaBb")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ 任务完成")
        else:
            print("\n❌ 任务失败")
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n💥 发生未预期的错误: {e}")
        import traceback
        traceback.print_exc() 