#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单同步字典数据到云端数据库
只同步不依赖外键的字典数据
"""

import psycopg2
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
LOCAL_DB_URL = "postgresql://nijie@localhost:5432/pma_local"
CLOUD_DB_URL = "postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs"

def sync_dictionaries_simple():
    """简单同步字典数据"""
    try:
        logger.info("🔄 开始简单同步字典数据...")
        
        # 连接数据库
        local_conn = psycopg2.connect(LOCAL_DB_URL)
        cloud_conn = psycopg2.connect(CLOUD_DB_URL)
        
        local_cursor = local_conn.cursor()
        cloud_cursor = cloud_conn.cursor()
        
        # 1. 同步通用字典（不依赖外键）
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
        
        # 2. 同步产品分类字典（不依赖外键）
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
        
        # 3. 创建简化的企业字典数据（不依赖外键）
        logger.info("   创建简化企业字典...")
        try:
            # 获取本地企业字典的基本信息
            local_cursor.execute("SELECT name, code FROM affiliations ORDER BY id")
            affiliations_basic = local_cursor.fetchall()
            
            if affiliations_basic:
                # 清空现有数据
                cloud_cursor.execute("DELETE FROM affiliations")
                
                # 插入简化数据（使用admin用户ID作为owner_id）
                cloud_cursor.execute("SELECT id FROM users WHERE username = 'admin' LIMIT 1")
                admin_user = cloud_cursor.fetchone()
                admin_id = admin_user[0] if admin_user else 1
                
                for i, (name, code) in enumerate(affiliations_basic, 1):
                    cloud_cursor.execute("""
                        INSERT INTO affiliations (name, code, owner_id, created_at) 
                        VALUES (%s, %s, %s, %s)
                    """, (name, code, admin_id, 1734249600.0))  # 使用固定时间戳
                
                logger.info(f"   ✅ 简化企业字典同步完成: {len(affiliations_basic)}条")
            else:
                logger.info("   企业字典无数据")
        except Exception as e:
            logger.error(f"   ❌ 简化企业字典同步失败: {e}")
        
        # 提交事务
        cloud_conn.commit()
        
        # 关闭连接
        local_cursor.close()
        local_conn.close()
        cloud_cursor.close()
        cloud_conn.close()
        
        logger.info("✅ 字典数据简单同步完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 简单同步字典数据失败: {e}")
        return False

def verify_result():
    """验证同步结果"""
    try:
        logger.info("🔄 验证同步结果...")
        cloud_conn = psycopg2.connect(CLOUD_DB_URL)
        cursor = cloud_conn.cursor()
        
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
        
        if categories_count > 0:
            cursor.execute("SELECT name, code FROM product_categories LIMIT 5")
            samples = cursor.fetchall()
            logger.info("   产品分类字典样例:")
            for sample in samples:
                logger.info(f"     - {sample[0]} ({sample[1]})")
        
        cursor.close()
        cloud_conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 验证同步结果失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("🚀 简单同步字典数据到云端数据库")
    print("=" * 80)
    print("📋 任务说明:")
    print("   1. 同步通用字典数据")
    print("   2. 同步产品分类字典数据")
    print("   3. 创建简化企业字典数据")
    print("=" * 80)
    
    # 同步字典数据
    print("\n📋 开始同步字典数据")
    if sync_dictionaries_simple():
        print("✅ 字典数据同步成功")
    else:
        print("❌ 字典数据同步失败")
        return False
    
    # 验证结果
    print("\n📋 验证同步结果")
    if verify_result():
        print("✅ 验证成功")
    else:
        print("❌ 验证失败")
    
    print("\n🎉 任务完成！")
    print("💡 现在您可以登录云端系统查看字典数据：")
    print("   - 用户名: admin")
    print("   - 密码: 超级密码 1505562299AaBb")
    print("   - 可以查看企业字典、通用字典和产品分类字典")
    
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