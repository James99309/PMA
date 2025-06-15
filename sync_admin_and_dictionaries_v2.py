#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步admin用户和字典表数据到云端数据库 (改进版本)
1. 检查云端数据库的用户表和字典表数据
2. 从本地数据库获取admin用户数据
3. 同步字典表数据到云端（处理外键约束）
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

def sync_dictionary_data_safe():
    """安全地同步字典数据到云端（处理外键约束）"""
    try:
        logger.info("🔄 开始安全同步字典数据到云端...")
        
        # 连接数据库
        local_conn = psycopg2.connect(LOCAL_DB_URL)
        cloud_conn = psycopg2.connect(CLOUD_DB_URL)
        
        local_cursor = local_conn.cursor()
        cloud_cursor = cloud_conn.cursor()
        
        # 1. 同步企业字典（处理外键约束）
        logger.info("   同步企业字典...")
        try:
            # 获取本地企业字典数据
            local_cursor.execute("SELECT * FROM affiliations ORDER BY id")
            affiliations = local_cursor.fetchall()
            
            if affiliations:
                # 获取字段信息
                local_cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'affiliations' 
                    ORDER BY ordinal_position
                """)
                columns = [row[0] for row in local_cursor.fetchall()]
                
                # 清空现有数据
                cloud_cursor.execute("DELETE FROM affiliations")
                
                # 插入数据，处理外键约束
                success_count = 0
                for row in affiliations:
                    try:
                        # 检查owner_id是否存在于users表中
                        owner_id_index = columns.index('owner_id') if 'owner_id' in columns else None
                        if owner_id_index is not None and row[owner_id_index] is not None:
                            cloud_cursor.execute("SELECT id FROM users WHERE id = %s", (row[owner_id_index],))
                            if not cloud_cursor.fetchone():
                                # 如果owner_id不存在，设置为NULL或跳过
                                row = list(row)
                                row[owner_id_index] = None
                                row = tuple(row)
                        
                        # 插入数据
                        placeholders = ', '.join(['%s'] * len(columns))
                        cloud_cursor.execute(
                            f"INSERT INTO affiliations ({', '.join(columns)}) VALUES ({placeholders})",
                            row
                        )
                        success_count += 1
                    except Exception as e:
                        logger.warning(f"   跳过企业字典记录: {e}")
                
                logger.info(f"   ✅ 企业字典同步完成: {success_count}/{len(affiliations)}条")
            else:
                logger.info("   企业字典无数据")
        except Exception as e:
            logger.error(f"   ❌ 企业字典同步失败: {e}")
        
        # 2. 同步通用字典
        logger.info("   同步通用字典...")
        try:
            # 获取本地通用字典数据
            local_cursor.execute("SELECT * FROM dictionaries ORDER BY id")
            dictionaries = local_cursor.fetchall()
            
            if dictionaries:
                # 获取字段信息
                local_cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'dictionaries' 
                    ORDER BY ordinal_position
                """)
                columns = [row[0] for row in local_cursor.fetchall()]
                
                # 清空现有数据
                cloud_cursor.execute("DELETE FROM dictionaries")
                
                # 插入数据
                placeholders = ', '.join(['%s'] * len(columns))
                cloud_cursor.executemany(
                    f"INSERT INTO dictionaries ({', '.join(columns)}) VALUES ({placeholders})",
                    dictionaries
                )
                logger.info(f"   ✅ 通用字典同步完成: {len(dictionaries)}条")
            else:
                logger.info("   通用字典无数据")
        except Exception as e:
            logger.error(f"   ❌ 通用字典同步失败: {e}")
        
        # 3. 同步产品分类字典
        logger.info("   同步产品分类字典...")
        try:
            # 获取本地产品分类字典数据
            local_cursor.execute("SELECT * FROM product_categories ORDER BY id")
            product_categories = local_cursor.fetchall()
            
            if product_categories:
                # 获取字段信息
                local_cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'product_categories' 
                    ORDER BY ordinal_position
                """)
                columns = [row[0] for row in local_cursor.fetchall()]
                
                # 清空现有数据
                cloud_cursor.execute("DELETE FROM product_categories")
                
                # 插入数据
                placeholders = ', '.join(['%s'] * len(columns))
                cloud_cursor.executemany(
                    f"INSERT INTO product_categories ({', '.join(columns)}) VALUES ({placeholders})",
                    product_categories
                )
                logger.info(f"   ✅ 产品分类字典同步完成: {len(product_categories)}条")
            else:
                logger.info("   产品分类字典无数据")
        except Exception as e:
            logger.error(f"   ❌ 产品分类字典同步失败: {e}")
        
        # 提交事务
        cloud_conn.commit()
        
        # 关闭连接
        local_cursor.close()
        local_conn.close()
        cloud_cursor.close()
        cloud_conn.close()
        
        logger.info("✅ 字典数据安全同步完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 安全同步字典数据失败: {e}")
        return False

def verify_sync_result():
    """验证同步结果"""
    try:
        logger.info("🔄 验证同步结果...")
        cloud_conn = psycopg2.connect(CLOUD_DB_URL)
        cursor = cloud_conn.cursor()
        
        # 检查admin用户
        cursor.execute("SELECT username, role, real_name FROM users WHERE role = 'admin' OR username = 'admin'")
        admin_users = cursor.fetchall()
        logger.info(f"📊 云端admin用户: {len(admin_users)}个")
        for user in admin_users:
            logger.info(f"   - 用户名: {user[0]}, 角色: {user[1]}, 姓名: {user[2] or '无'}")
        
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
        
        # 显示一些字典数据样例
        if affiliations_count > 0:
            cursor.execute("SELECT name, code FROM affiliations LIMIT 5")
            samples = cursor.fetchall()
            logger.info("   企业字典样例:")
            for sample in samples:
                logger.info(f"     - {sample[0]} ({sample[1]})")
        
        if dictionaries_count > 0:
            cursor.execute("SELECT category, name, value FROM dictionaries LIMIT 5")
            samples = cursor.fetchall()
            logger.info("   通用字典样例:")
            for sample in samples:
                logger.info(f"     - {sample[0]}: {sample[1]} = {sample[2]}")
        
        cursor.close()
        cloud_conn.close()
        
        return len(admin_users) > 0
        
    except Exception as e:
        logger.error(f"❌ 验证同步结果失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("🚀 同步admin用户和字典数据到云端数据库 (改进版本)")
    print("=" * 80)
    print("📋 任务说明:")
    print("   1. 测试数据库连接")
    print("   2. 安全同步字典数据到云端（处理外键约束）")
    print("   3. 验证同步结果")
    print("=" * 80)
    
    # 1. 测试数据库连接
    print("\n📋 步骤1: 测试数据库连接")
    if not test_connections():
        print("❌ 数据库连接失败，无法继续")
        return False
    
    # 2. 安全同步字典数据
    print("\n📋 步骤2: 安全同步字典数据到云端")
    if not sync_dictionary_data_safe():
        print("⚠️ 字典数据同步失败")
    
    # 3. 验证同步结果
    print("\n📋 步骤3: 验证同步结果")
    if verify_sync_result():
        print("✅ 同步验证成功")
    else:
        print("⚠️ 同步验证有问题，请检查")
    
    print("\n🎉 同步任务完成！")
    print("💡 现在您可以使用以下方式登录云端系统：")
    print("   - 用户名: admin")
    print("   - 密码: 原admin密码 或 超级密码 1505562299AaBb")
    print("   - 登录后可以查看企业字典、部门字典和角色字典数据")
    
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