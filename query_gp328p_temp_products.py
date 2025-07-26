#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询所有product_model为"GP328P"的临时产品记录（包括已删除的）
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.temp_product import TempProduct
from app.models.user import User
from sqlalchemy import text
from datetime import datetime

def query_gp328p_temp_products():
    """查询所有GP328P临时产品记录"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("查询所有product_model为'GP328P'的临时产品记录")
        print("=" * 80)
        
        try:
            # 查询所有GP328P记录（包括已删除的）
            records = db.session.query(
                TempProduct.id,
                TempProduct.product_name,
                TempProduct.product_model,
                TempProduct.product_desc,
                TempProduct.brand,
                TempProduct.unit,
                TempProduct.product_mn,
                TempProduct.category,
                TempProduct.category_path,
                TempProduct.reference_price,
                TempProduct.usage_count,
                TempProduct.last_used_at,
                TempProduct.created_at,
                TempProduct.updated_at,
                TempProduct.is_deleted,
                TempProduct.created_by,
                User.username,
                User.real_name
            ).join(
                User, TempProduct.created_by == User.id
            ).filter(
                TempProduct.product_model == 'GP328P'
            ).order_by(
                TempProduct.created_at.desc()
            ).all()
            
            if not records:
                print("❌ 未找到任何product_model为'GP328P'的临时产品记录")
                return
            
            print(f"✅ 找到 {len(records)} 条记录:")
            print()
            
            # 统计信息
            active_count = sum(1 for record in records if not record.is_deleted)
            deleted_count = sum(1 for record in records if record.is_deleted)
            
            print(f"📊 统计信息:")
            print(f"   - 活跃记录: {active_count} 条")
            print(f"   - 已删除记录: {deleted_count} 条")
            print(f"   - 总记录数: {len(records)} 条")
            print()
            
            # 显示详细记录
            for i, record in enumerate(records, 1):
                print(f"📋 记录 #{i}:")
                print(f"   ID: {record.id}")
                print(f"   产品名称: {record.product_name or '未设置'}")
                print(f"   产品型号: {record.product_model}")
                print(f"   产品描述: {record.product_desc or '未设置'}")
                print(f"   品牌: {record.brand or '未设置'}")
                print(f"   单位: {record.unit or '个'}")
                print(f"   产品MN号: {record.product_mn or '未生成'}")
                print(f"   分类: {record.category or '未分类'}")
                print(f"   分类路径: {record.category_path or '未设置'}")
                print(f"   参考价格: {record.reference_price or 0.0} 元")
                print(f"   使用次数: {record.usage_count}")
                print(f"   最后使用: {record.last_used_at.strftime('%Y-%m-%d %H:%M:%S') if record.last_used_at else '从未使用'}")
                print(f"   创建时间: {record.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   更新时间: {record.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   创建用户: {record.username} ({record.real_name or '未设置姓名'})")
                print(f"   状态: {'🗑️ 已删除' if record.is_deleted else '✅ 活跃'}")
                print("-" * 60)
            
            # 检查是否有重复记录
            print("\n🔍 重复性分析:")
            
            # 按创建用户分组
            user_groups = {}
            for record in records:
                user_key = f"{record.username} ({record.real_name or '未知'})"
                if user_key not in user_groups:
                    user_groups[user_key] = []
                user_groups[user_key].append(record)
            
            if len(user_groups) > 1:
                print(f"   ⚠️  发现多个用户创建了相同型号的临时产品:")
                for user, user_records in user_groups.items():
                    print(f"      - {user}: {len(user_records)} 条记录")
            else:
                print(f"   ✅ 所有记录都是由同一用户创建的")
            
            # 检查同一用户的重复记录
            for user, user_records in user_groups.items():
                if len(user_records) > 1:
                    print(f"   ⚠️  用户 {user} 创建了 {len(user_records)} 条相同型号的记录:")
                    for record in user_records:
                        status = "已删除" if record.is_deleted else "活跃"
                        print(f"      - ID:{record.id} ({status}) - 创建于 {record.created_at.strftime('%Y-%m-%d %H:%M')}")
            
            # 原始SQL查询验证
            print("\n🔧 原始SQL查询验证:")
            sql_query = text("""
                SELECT 
                    tp.id,
                    tp.product_name,
                    tp.product_model,
                    tp.created_at,
                    tp.is_deleted,
                    u.username,
                    u.real_name
                FROM temp_products tp
                JOIN users u ON tp.created_by = u.id
                WHERE tp.product_model = 'GP328P'
                ORDER BY tp.created_at DESC
            """)
            
            sql_results = db.session.execute(sql_query).fetchall()
            print(f"   SQL查询结果: {len(sql_results)} 条记录")
            
            if len(sql_results) != len(records):
                print(f"   ⚠️  ORM查询与SQL查询结果数量不一致!")
                print(f"   ORM: {len(records)} 条, SQL: {len(sql_results)} 条")
            else:
                print(f"   ✅ ORM查询与SQL查询结果一致")
                
        except Exception as e:
            print(f"❌ 查询过程中出现错误: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    query_gp328p_temp_products()