#!/usr/bin/env python3
"""
更新临时产品MN号格式的脚本
将现有的 TEMP-{随机码} 格式更新为新的 TP{YYMMDDHHMM} 格式
"""

import sys
import os

# 添加项目路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.temp_product import TempProduct
from datetime import datetime

def update_temp_product_mn_format():
    """更新现有临时产品的MN号格式"""
    app = create_app()
    
    with app.app_context():
        try:
            # 查找所有使用旧格式MN号的临时产品
            products_with_old_mn = TempProduct.query.filter(
                TempProduct.product_mn.like('TEMP-%'),
                TempProduct.is_deleted == False
            ).all()
            
            print(f"🔍 找到 {len(products_with_old_mn)} 个使用旧格式MN号的临时产品:")
            
            if not products_with_old_mn:
                print("✅ 没有找到使用旧格式的临时产品MN号")
                return
            
            updated_count = 0
            failed_count = 0
            
            for product in products_with_old_mn:
                try:
                    old_mn = product.product_mn
                    print(f"  • ID: {product.id}, 型号: {product.product_model}, 旧MN: {old_mn}")
                    
                    # 使用产品的创建时间来生成新的MN号
                    creation_time = product.created_at
                    new_mn = TempProduct.generate_unique_mn(creation_time)
                    
                    # 更新MN号
                    product.product_mn = new_mn
                    product.updated_at = datetime.utcnow()
                    
                    print(f"    ✅ 更新MN号: {old_mn} -> {new_mn}")
                    updated_count += 1
                    
                except Exception as e:
                    print(f"    ❌ 更新MN号失败: {str(e)}")
                    failed_count += 1
                    continue
            
            # 批量提交所有更改
            if updated_count > 0:
                db.session.commit()
                print(f"\n🎉 更新完成!")
                print(f"  ✅ 成功更新: {updated_count} 个MN号")
                if failed_count > 0:
                    print(f"  ❌ 失败: {failed_count} 个")
                    
                # 验证更新结果
                remaining_old_format = TempProduct.query.filter(
                    TempProduct.product_mn.like('TEMP-%'),
                    TempProduct.is_deleted == False
                ).count()
                
                if remaining_old_format == 0:
                    print("  🎯 所有临时产品现在都使用新格式MN号了!")
                else:
                    print(f"  ⚠️ 仍有 {remaining_old_format} 个产品使用旧格式MN号")
            else:
                print("\n⚠️ 没有产品需要更新")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ 更新过程中发生错误: {str(e)}")
            raise

def display_mn_format_summary():
    """显示MN号格式汇总"""
    app = create_app()
    
    with app.app_context():
        # 统计各种格式的MN号
        total_temp_products = TempProduct.query.filter(
            TempProduct.is_deleted == False
        ).count()
        
        old_format_count = TempProduct.query.filter(
            TempProduct.product_mn.like('TEMP-%'),
            TempProduct.is_deleted == False
        ).count()
        
        new_format_count = TempProduct.query.filter(
            TempProduct.product_mn.like('TP%'),
            TempProduct.is_deleted == False
        ).count()
        
        no_mn_count = TempProduct.query.filter(
            TempProduct.product_mn.is_(None),
            TempProduct.is_deleted == False
        ).count()
        
        print("\n📊 临时产品MN号格式统计:")
        print("=" * 40)
        print(f"  总临时产品数: {total_temp_products}")
        print(f"  新格式 (TP...): {new_format_count}")
        print(f"  旧格式 (TEMP-...): {old_format_count}")
        print(f"  无MN号: {no_mn_count}")
        print("=" * 40)
        
        if old_format_count == 0 and no_mn_count == 0:
            print("✅ 所有临时产品都使用正确的新格式MN号!")
        elif old_format_count > 0:
            print("⚠️ 仍有产品使用旧格式MN号，需要更新")
        elif no_mn_count > 0:
            print("⚠️ 仍有产品缺少MN号，需要生成")

if __name__ == '__main__':
    print("🔧 开始更新临时产品MN号格式...")
    print("=" * 50)
    
    # 显示当前状态
    display_mn_format_summary()
    
    print("\n" + "=" * 50)
    print("🔄 执行MN号格式更新...")
    
    # 更新MN号格式
    update_temp_product_mn_format()
    
    print("\n" + "=" * 50)
    print("📊 更新后状态:")
    
    # 显示更新后状态
    display_mn_format_summary()
    
    print("\n✅ 脚本执行完成")