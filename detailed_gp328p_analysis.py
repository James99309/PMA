#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细分析GP328P相关的所有数据记录
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models.temp_product import TempProduct
from app.models.user import User
from sqlalchemy import text, or_
from datetime import datetime

def detailed_gp328p_analysis():
    """详细分析GP328P相关的所有数据"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 100)
        print("GP328P 临时产品详细分析报告")
        print("=" * 100)
        
        try:
            # 1. 精确匹配GP328P的记录
            print("🎯 1. 精确匹配 product_model = 'GP328P' 的记录:")
            exact_records = db.session.query(TempProduct).filter(
                TempProduct.product_model == 'GP328P'
            ).all()
            
            print(f"   找到 {len(exact_records)} 条精确匹配记录")
            
            for record in exact_records:
                print(f"   📋 ID: {record.id}")
                print(f"      产品名称: {record.product_name}")
                print(f"      产品型号: {record.product_model}")
                print(f"      创建时间: {record.created_at}")
                print(f"      状态: {'已删除' if record.is_deleted else '活跃'}")
                print(f"      使用次数: {record.usage_count}")
                print()
            
            # 2. 模糊匹配包含GP328P的记录
            print("🔍 2. 模糊匹配包含 'GP328P' 的记录:")
            fuzzy_records = db.session.query(TempProduct).filter(
                or_(
                    TempProduct.product_model.ilike('%GP328P%'),
                    TempProduct.product_name.ilike('%GP328P%'),
                    TempProduct.product_desc.ilike('%GP328P%')
                )
            ).all()
            
            print(f"   找到 {len(fuzzy_records)} 条模糊匹配记录")
            
            for record in fuzzy_records:
                print(f"   📋 ID: {record.id}")
                print(f"      产品名称: {record.product_name}")
                print(f"      产品型号: {record.product_model}")
                print(f"      产品描述: {record.product_desc or '无'}")
                print(f"      匹配字段: ", end="")
                matches = []
                if 'GP328P' in (record.product_model or ''):
                    matches.append("产品型号")
                if 'GP328P' in (record.product_name or ''):
                    matches.append("产品名称")
                if 'GP328P' in (record.product_desc or ''):
                    matches.append("产品描述")
                print(", ".join(matches))
                print(f"      创建时间: {record.created_at}")
                print(f"      状态: {'已删除' if record.is_deleted else '活跃'}")
                print()
            
            # 3. 查看摩托罗拉品牌的所有记录
            print("📱 3. 摩托罗拉品牌的所有临时产品记录:")
            motorola_records = db.session.query(TempProduct).filter(
                or_(
                    TempProduct.brand.ilike('%摩托罗拉%'),
                    TempProduct.brand.ilike('%motorola%'),
                    TempProduct.brand.ilike('%MOTOROLA%')
                )
            ).order_by(TempProduct.created_at.desc()).all()
            
            print(f"   找到 {len(motorola_records)} 条摩托罗拉品牌记录")
            
            for record in motorola_records:
                print(f"   📋 ID: {record.id}")
                print(f"      产品名称: {record.product_name}")
                print(f"      产品型号: {record.product_model}")
                print(f"      品牌: {record.brand}")
                print(f"      创建时间: {record.created_at}")
                print(f"      状态: {'已删除' if record.is_deleted else '活跃'}")
                print(f"      使用次数: {record.usage_count}")
                print()
            
            # 4. 查看对讲机分类的所有记录
            print("📻 4. 对讲机分类的所有临时产品记录:")
            radio_records = db.session.query(TempProduct).filter(
                or_(
                    TempProduct.category.ilike('%对讲机%'),
                    TempProduct.category_path.ilike('%对讲机%'),
                    TempProduct.product_name.ilike('%对讲机%'),
                    TempProduct.product_desc.ilike('%对讲机%')
                )
            ).order_by(TempProduct.created_at.desc()).all()
            
            print(f"   找到 {len(radio_records)} 条对讲机相关记录")
            
            for record in radio_records:
                print(f"   📋 ID: {record.id}")
                print(f"      产品名称: {record.product_name}")
                print(f"      产品型号: {record.product_model}")
                print(f"      分类: {record.category}")
                print(f"      分类路径: {record.category_path}")
                print(f"      创建时间: {record.created_at}")
                print(f"      状态: {'已删除' if record.is_deleted else '活跃'}")
                print(f"      使用次数: {record.usage_count}")
                print()
            
            # 5. 查看admin用户创建的所有临时产品
            print("👤 5. admin用户创建的所有临时产品记录:")
            admin_user = db.session.query(User).filter(User.username == 'admin').first()
            if admin_user:
                admin_records = db.session.query(TempProduct).filter(
                    TempProduct.created_by == admin_user.id
                ).order_by(TempProduct.created_at.desc()).all()
                
                print(f"   找到 {len(admin_records)} 条admin用户创建的记录")
                
                for record in admin_records:
                    print(f"   📋 ID: {record.id}")
                    print(f"      产品名称: {record.product_name}")
                    print(f"      产品型号: {record.product_model}")
                    print(f"      创建时间: {record.created_at}")
                    print(f"      状态: {'已删除' if record.is_deleted else '活跃'}")
                    print(f"      使用次数: {record.usage_count}")
                    print()
            else:
                print("   ❌ 未找到admin用户")
            
            # 6. 原始SQL查询，确保没有遗漏
            print("🔧 6. 原始SQL查询验证:")
            
            # 查询所有GP328P相关记录的原始SQL
            sql_queries = [
                ("精确匹配GP328P", "SELECT * FROM temp_products WHERE product_model = 'GP328P'"),
                ("模糊匹配GP328P", "SELECT * FROM temp_products WHERE product_model ILIKE '%GP328P%' OR product_name ILIKE '%GP328P%' OR product_desc ILIKE '%GP328P%'"),
                ("所有临时产品总数", "SELECT COUNT(*) FROM temp_products"),
                ("活跃临时产品总数", "SELECT COUNT(*) FROM temp_products WHERE is_deleted = FALSE"),
                ("已删除临时产品总数", "SELECT COUNT(*) FROM temp_products WHERE is_deleted = TRUE")
            ]
            
            for desc, sql in sql_queries:
                try:
                    result = db.session.execute(text(sql))
                    if "COUNT" in sql:
                        count = result.scalar()
                        print(f"   {desc}: {count}")
                    else:
                        rows = result.fetchall()
                        print(f"   {desc}: {len(rows)} 条记录")
                except Exception as e:
                    print(f"   {desc}: 查询失败 - {str(e)}")
            
            # 7. 检查是否有同名但不同ID的记录
            print("\n🔄 7. 重复性检查:")
            
            all_gp328p = db.session.query(TempProduct).filter(
                TempProduct.product_model == 'GP328P'
            ).all()
            
            if len(all_gp328p) > 1:
                print(f"   ⚠️  发现 {len(all_gp328p)} 条相同型号的记录，可能存在重复:")
                for i, record in enumerate(all_gp328p, 1):
                    print(f"      {i}. ID:{record.id} - 创建于 {record.created_at} - {'已删除' if record.is_deleted else '活跃'}")
            else:
                print(f"   ✅ 只有 {len(all_gp328p)} 条GP328P记录，无重复")
            
            # 8. 检查历史数据变更
            print("\n📊 8. 数据概览:")
            total_temp_products = db.session.query(TempProduct).count()
            active_temp_products = db.session.query(TempProduct).filter(TempProduct.is_deleted == False).count()
            deleted_temp_products = db.session.query(TempProduct).filter(TempProduct.is_deleted == True).count()
            
            print(f"   总临时产品记录: {total_temp_products}")
            print(f"   活跃记录: {active_temp_products}")
            print(f"   已删除记录: {deleted_temp_products}")
            
            # 最新和最旧的记录
            newest = db.session.query(TempProduct).order_by(TempProduct.created_at.desc()).first()
            oldest = db.session.query(TempProduct).order_by(TempProduct.created_at.asc()).first()
            
            if newest:
                print(f"   最新记录: ID:{newest.id} - {newest.product_name} ({newest.product_model}) - {newest.created_at}")
            if oldest:
                print(f"   最旧记录: ID:{oldest.id} - {oldest.product_name} ({oldest.product_model}) - {oldest.created_at}")
                
        except Exception as e:
            print(f"❌ 分析过程中出现错误: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    detailed_gp328p_analysis()