#!/usr/bin/env python3
"""
修复临时产品缺失MN号的脚本
为所有没有product_mn字段的临时产品生成唯一的MN号
"""

import sys
import os

# 添加项目路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.temp_product import TempProduct

def fix_missing_mn_numbers():
    """为缺失MN号的临时产品生成MN号"""
    app = create_app()
    
    with app.app_context():
        try:
            # 查找所有没有MN号的活跃临时产品
            products_without_mn = TempProduct.query.filter(
                TempProduct.product_mn.is_(None),
                TempProduct.is_deleted == False
            ).all()
            
            print(f"🔍 找到 {len(products_without_mn)} 个缺失MN号的临时产品:")
            
            if not products_without_mn:
                print("✅ 所有活跃的临时产品都已有MN号")
                return
            
            fixed_count = 0
            failed_count = 0
            
            for product in products_without_mn:
                try:
                    print(f"  • ID: {product.id}, 型号: {product.product_model}, 名称: {product.product_name}")
                    
                    # 为产品生成MN号
                    product.generate_mn()
                    
                    print(f"    ✅ 生成MN号: {product.product_mn}")
                    fixed_count += 1
                    
                except Exception as e:
                    print(f"    ❌ 生成MN号失败: {str(e)}")
                    failed_count += 1
                    continue
            
            # 批量提交所有更改
            if fixed_count > 0:
                db.session.commit()
                print(f"\n🎉 修复完成!")
                print(f"  ✅ 成功生成: {fixed_count} 个MN号")
                if failed_count > 0:
                    print(f"  ❌ 失败: {failed_count} 个")
                    
                # 验证修复结果
                remaining_without_mn = TempProduct.query.filter(
                    TempProduct.product_mn.is_(None),
                    TempProduct.is_deleted == False
                ).count()
                
                if remaining_without_mn == 0:
                    print("  🎯 所有临时产品现在都有MN号了!")
                else:
                    print(f"  ⚠️ 仍有 {remaining_without_mn} 个产品缺少MN号")
            else:
                print("\n⚠️ 没有产品需要修复")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ 修复过程中发生错误: {str(e)}")
            raise

def verify_mn_uniqueness():
    """验证所有MN号的唯一性"""
    app = create_app()
    
    with app.app_context():
        # 检查临时产品MN号重复
        from sqlalchemy import func
        
        duplicates = db.session.query(
            TempProduct.product_mn,
            func.count(TempProduct.id).label('count')
        ).filter(
            TempProduct.product_mn.isnot(None),
            TempProduct.is_deleted == False
        ).group_by(TempProduct.product_mn).having(
            func.count(TempProduct.id) > 1
        ).all()
        
        if duplicates:
            print("⚠️ 发现重复的临时产品MN号:")
            for mn, count in duplicates:
                print(f"  • {mn}: {count}个产品使用")
        else:
            print("✅ 所有临时产品MN号都是唯一的")
        
        # 检查与常规产品的冲突
        from app.models.product import Product
        
        temp_mns = set([p.product_mn for p in TempProduct.query.filter(
            TempProduct.product_mn.isnot(None),
            TempProduct.is_deleted == False
        ).all()])
        
        regular_mns = set([p.product_mn for p in Product.query.filter(
            Product.product_mn.isnot(None)
        ).all()])
        
        conflicts = temp_mns.intersection(regular_mns)
        
        if conflicts:
            print("⚠️ 发现与常规产品冲突的MN号:")
            for mn in conflicts:
                print(f"  • {mn}")
        else:
            print("✅ 临时产品MN号与常规产品无冲突")

if __name__ == '__main__':
    print("🔧 开始修复临时产品缺失的MN号...")
    print("=" * 50)
    
    # 修复缺失的MN号
    fix_missing_mn_numbers()
    
    print("\n" + "=" * 50)
    print("🔍 验证MN号唯一性...")
    
    # 验证唯一性
    verify_mn_uniqueness()
    
    print("\n✅ 脚本执行完成")