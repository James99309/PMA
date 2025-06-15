#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入Evertac产品价格表到云端数据库
将Excel文件中的产品数据导入到云端pma_db_ovs数据库的products表中
"""

import os
import sys
import pandas as pd
import psycopg2
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# 云端数据库连接信息
CLOUD_DB_URL = "postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs"

def get_admin_user_id(conn):
    """获取admin用户的ID"""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = 'admin' LIMIT 1")
            result = cur.fetchone()
            if result:
                return result[0]
            else:
                logger.error("❌ 未找到admin用户")
                return None
    except Exception as e:
        logger.error(f"❌ 获取admin用户ID失败: {e}")
        return None

def clean_and_validate_data(df):
    """清理和验证数据"""
    logger.info("🔄 清理和验证Excel数据...")
    
    # 创建字段映射
    field_mapping = {
        'Type': 'type',
        'Category': 'category', 
        'product_mn': 'product_mn',
        'product_name': 'product_name',
        'Model': 'model',
        'Specitication': 'specification',  # 注意Excel中的拼写错误
        'Brand': 'brand',
        'unit': 'unit',
        'retail_price': 'retail_price',
        'status': 'status'
    }
    
    # 重命名列
    df_clean = df.rename(columns=field_mapping)
    
    # 删除ID列（数据库会自动生成）
    if 'ID' in df_clean.columns:
        df_clean = df_clean.drop('ID', axis=1)
    
    # 数据类型转换和清理
    df_clean['type'] = df_clean['type'].astype(str)
    df_clean['category'] = df_clean['category'].astype(str)
    df_clean['product_mn'] = df_clean['product_mn'].astype(str)
    df_clean['product_name'] = df_clean['product_name'].astype(str)
    df_clean['model'] = df_clean['model'].astype(str)
    df_clean['specification'] = df_clean['specification'].astype(str)
    df_clean['brand'] = df_clean['brand'].astype(str)
    df_clean['unit'] = df_clean['unit'].astype(str)
    
    # 处理价格字段
    df_clean['retail_price'] = pd.to_numeric(df_clean['retail_price'], errors='coerce')
    
    # 处理状态字段
    df_clean['status'] = df_clean['status'].astype(str)
    
    # 添加时间戳和拥有者字段
    current_time = datetime.now()
    df_clean['created_at'] = current_time
    df_clean['updated_at'] = current_time
    
    # 移除空行
    df_clean = df_clean.dropna(subset=['product_mn', 'product_name'])
    
    logger.info(f"✅ 数据清理完成，有效记录数: {len(df_clean)}")
    return df_clean

def import_products_to_cloud(df, admin_user_id):
    """将产品数据导入到云端数据库"""
    logger.info("🔄 开始导入产品数据到云端数据库...")
    
    try:
        # 连接云端数据库
        conn = psycopg2.connect(CLOUD_DB_URL)
        conn.autocommit = False
        
        with conn.cursor() as cur:
            # 清空现有产品数据（可选）
            logger.info("🔄 清空现有产品数据...")
            cur.execute("DELETE FROM products")
            logger.info("✅ 现有产品数据已清空")
            
            # 准备插入语句
            insert_sql = """
                INSERT INTO products (
                    type, category, product_mn, product_name, model, 
                    specification, brand, unit, retail_price, status,
                    created_at, updated_at, owner_id
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            # 批量插入数据
            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    cur.execute(insert_sql, (
                        row['type'],
                        row['category'],
                        row['product_mn'],
                        row['product_name'],
                        row['model'],
                        row['specification'],
                        row['brand'],
                        row['unit'],
                        row['retail_price'],
                        row['status'],
                        row['created_at'],
                        row['updated_at'],
                        admin_user_id
                    ))
                    success_count += 1
                except Exception as e:
                    logger.error(f"❌ 插入第{index+1}行数据失败: {e}")
                    logger.error(f"   数据: {row.to_dict()}")
                    error_count += 1
                    continue
            
            # 提交事务
            conn.commit()
            logger.info(f"✅ 产品数据导入完成: 成功{success_count}条，失败{error_count}条")
            
            # 验证导入结果
            cur.execute("SELECT COUNT(*) FROM products")
            total_count = cur.fetchone()[0]
            logger.info(f"📊 云端数据库products表总记录数: {total_count}")
            
            # 显示前几条记录
            cur.execute("""
                SELECT id, product_mn, product_name, brand, retail_price, created_at 
                FROM products 
                ORDER BY id 
                LIMIT 5
            """)
            sample_records = cur.fetchall()
            logger.info("📋 前5条记录:")
            for record in sample_records:
                logger.info(f"   ID:{record[0]} | MN:{record[1]} | 名称:{record[2]} | 品牌:{record[3]} | 价格:{record[4]} | 创建时间:{record[5]}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ 导入产品数据失败: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("🚀 导入Evertac产品价格表到云端数据库")
    print("=" * 80)
    print("📋 任务说明:")
    print("   1. 读取Evertac-Pricelist- APAC.xlsx文件")
    print("   2. 清理和验证数据")
    print("   3. 导入到云端pma_db_ovs数据库的products表")
    print("   4. 设置拥有者为admin用户")
    print("   5. 设置创建时间和更新时间为当前时间")
    print("=" * 80)
    print()
    
    # 检查Excel文件是否存在
    excel_file = "Evertac-Pricelist- APAC.xlsx"
    if not os.path.exists(excel_file):
        logger.error(f"❌ Excel文件不存在: {excel_file}")
        return False
    
    try:
        # 连接云端数据库获取admin用户ID
        logger.info("🔄 连接云端数据库...")
        conn = psycopg2.connect(CLOUD_DB_URL)
        admin_user_id = get_admin_user_id(conn)
        conn.close()
        
        if not admin_user_id:
            logger.error("❌ 无法获取admin用户ID，导入终止")
            return False
        
        logger.info(f"✅ 获取admin用户ID: {admin_user_id}")
        
        # 读取Excel文件
        logger.info(f"🔄 读取Excel文件: {excel_file}")
        df = pd.read_excel(excel_file)
        logger.info(f"✅ Excel文件读取成功，原始记录数: {len(df)}")
        
        # 清理和验证数据
        df_clean = clean_and_validate_data(df)
        
        # 导入到云端数据库
        success = import_products_to_cloud(df_clean, admin_user_id)
        
        if success:
            print("✅ 产品数据导入成功")
            print()
            print("🎉 任务完成！")
            print("💡 现在您可以登录云端系统查看产品数据：")
            print("   - 用户名: admin")
            print("   - 密码: 超级密码 1505562299AaBb")
            print("   - 可以在产品管理模块查看导入的产品")
            print()
            print("✅ 任务完成")
            return True
        else:
            print("❌ 产品数据导入失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 执行过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 