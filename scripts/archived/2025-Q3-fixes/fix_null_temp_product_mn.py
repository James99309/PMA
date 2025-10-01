#!/usr/bin/env python3
"""
修复MN号为NULL的临时产品
为所有product_mn字段为NULL的临时产品生成MN号
"""

import sys
import os

# 添加项目路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.temp_product import TempProduct

def fix_null_mn_products():
    """为MN号为NULL的临时产品生成MN号"""
    app = create_app()
    
    with app.app_context():
        try:
            # 查找所有MN号为NULL的活跃临时产品
            products_without_mn = TempProduct.query.filter(
                TempProduct.product_mn.is_(None),
                TempProduct.is_deleted == False
            ).all()
            
            print(f"🔍 找到 {len(products_without_mn)} 个MN号为NULL的临时产品:")
            
            if not products_without_mn:
                print("✅ 所有活跃的临时产品都已有MN号")
                return
            
            fixed_count = 0
            failed_count = 0
            
            for product in products_without_mn:
                try:
                    print(f"  • ID: {product.id}, 型号: {product.product_model}, 名称: {product.product_name}")
                    print(f"    创建时间: {product.created_at}")
                    
                    # 使用产品的创建时间生成MN号
                    new_mn = TempProduct.generate_unique_mn(product.created_at)
                    product.product_mn = new_mn
                    
                    print(f"    ✅ 生成MN号: {new_mn}")
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

def display_current_status():
    """显示当前临时产品MN号状态"""
    app = create_app()
    
    with app.app_context():
        # 查询所有活跃的临时产品
        all_products = TempProduct.query.filter_by(is_deleted=False).order_by(TempProduct.created_at.desc()).all()
        
        print("\n📊 所有活跃临时产品MN号状态:")
        print("=" * 80)
        
        for product in all_products:
            created_time = product.created_at.strftime('%Y-%m-%d %H:%M')
            mn_display = product.product_mn or 'NULL'
            print(f"• ID: {product.id:2d} | 型号: {product.product_model:15s} | MN: {mn_display:15s} | 创建: {created_time}")
        
        print("=" * 80)
        
        # 统计
        total = len(all_products)
        with_mn = len([p for p in all_products if p.product_mn])
        without_mn = total - with_mn
        
        print(f"总计: {total} | 有MN号: {with_mn} | 缺少MN号: {without_mn}")
        
        if without_mn == 0:
            print("✅ 所有临时产品都有MN号")
        else:
            print(f"⚠️ 有 {without_mn} 个产品缺少MN号")

if __name__ == '__main__':
    print("🔧 开始修复MN号为NULL的临时产品...")
    print("=" * 60)
    
    # 显示当前状态
    display_current_status()
    
    print("\n" + "=" * 60)
    print("🔄 执行MN号修复...")
    
    # 修复NULL的MN号
    fix_null_mn_products()
    
    print("\n" + "=" * 60)
    print("📊 修复后状态:")
    
    # 显示修复后状态
    display_current_status()
    
    print("\n✅ 脚本执行完成")