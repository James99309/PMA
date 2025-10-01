#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新云端数据库products表的type字段
根据brand字段的值来设置type字段：
- brand为"Evertac Solutions"的记录，type设为"channel"
- 其他记录的type设为"third-party"
"""

import psycopg2
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# 云端数据库连接信息
CLOUD_DB_URL = "postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs"

def update_product_types():
    """更新产品类型字段"""
    logger.info("🔄 开始更新产品类型字段...")
    
    try:
        # 连接云端数据库
        conn = psycopg2.connect(CLOUD_DB_URL)
        conn.autocommit = False
        
        with conn.cursor() as cur:
            # 首先查看当前的数据分布
            logger.info("📊 查看当前数据分布...")
            cur.execute("""
                SELECT brand, COUNT(*) as count 
                FROM products 
                GROUP BY brand 
                ORDER BY count DESC
            """)
            brand_stats = cur.fetchall()
            logger.info("品牌分布:")
            for brand, count in brand_stats:
                logger.info(f"   {brand}: {count}条记录")
            
            # 更新Evertac Solutions的记录为channel
            logger.info("🔄 更新Evertac Solutions品牌的记录type为'channel'...")
            cur.execute("""
                UPDATE products 
                SET type = 'channel', updated_at = %s
                WHERE LOWER(brand) = LOWER('Evertac Solutions')
            """, (datetime.now(),))
            evertac_updated = cur.rowcount
            logger.info(f"✅ 已更新{evertac_updated}条Evertac Solutions记录")
            
            # 更新其他品牌的记录为third-party
            logger.info("🔄 更新其他品牌的记录type为'third-party'...")
            cur.execute("""
                UPDATE products 
                SET type = 'third-party', updated_at = %s
                WHERE LOWER(brand) != LOWER('Evertac Solutions')
            """, (datetime.now(),))
            other_updated = cur.rowcount
            logger.info(f"✅ 已更新{other_updated}条其他品牌记录")
            
            # 提交事务
            conn.commit()
            logger.info("✅ 所有更新已提交")
            
            # 验证更新结果
            logger.info("📊 验证更新结果...")
            cur.execute("""
                SELECT type, COUNT(*) as count 
                FROM products 
                GROUP BY type 
                ORDER BY count DESC
            """)
            type_stats = cur.fetchall()
            logger.info("类型分布:")
            for type_name, count in type_stats:
                logger.info(f"   {type_name}: {count}条记录")
            
            # 显示一些示例记录
            logger.info("📋 示例记录:")
            cur.execute("""
                SELECT product_mn, product_name, brand, type, updated_at 
                FROM products 
                ORDER BY type, id 
                LIMIT 10
            """)
            sample_records = cur.fetchall()
            for record in sample_records:
                logger.info(f"   MN:{record[0]} | 名称:{record[1]} | 品牌:{record[2]} | 类型:{record[3]} | 更新时间:{record[4]}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ 更新产品类型失败: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("🚀 更新云端数据库产品类型字段")
    print("=" * 80)
    print("📋 任务说明:")
    print("   1. 连接云端pma_db_ovs数据库")
    print("   2. 将brand为'Evertac Solutions'的记录type设为'channel'")
    print("   3. 将其他品牌的记录type设为'third-party'")
    print("   4. 更新updated_at字段为当前时间")
    print("=" * 80)
    print()
    
    try:
        # 执行更新操作
        success = update_product_types()
        
        if success:
            print("✅ 产品类型更新成功")
            print()
            print("🎉 任务完成！")
            print("💡 现在您可以登录云端系统查看更新后的产品数据：")
            print("   - 用户名: admin")
            print("   - 密码: 超级密码 1505562299AaBb")
            print("   - 可以在产品管理模块查看更新后的产品类型")
            print()
            print("✅ 任务完成")
            return True
        else:
            print("❌ 产品类型更新失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 执行过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 