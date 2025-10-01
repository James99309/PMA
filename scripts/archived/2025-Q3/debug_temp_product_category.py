#!/usr/bin/env python3
"""
临时产品类别信息调试脚本
用于排查临时产品保存和显示问题
"""

from app import create_app
from app import db
from app.models.temp_product import TempProduct
from collections import defaultdict

def main():
    app = create_app()
    with app.app_context():
        print("🔍 临时产品类别信息诊断报告")
        print("=" * 50)
        
        # 1. 检查所有临时产品的类别信息
        all_products = TempProduct.query.filter_by(is_deleted=False).order_by(TempProduct.created_at.desc()).all()
        
        print(f"📊 总计临时产品数量: {len(all_products)}")
        print("\n📋 所有临时产品详情:")
        
        category_stats = defaultdict(int)
        empty_category_products = []
        
        for i, product in enumerate(all_products, 1):
            category = product.category or "(空)"
            category_stats[category] += 1
            
            print(f"{i:2d}. {product.product_name} - {product.product_model}")
            print(f"    类别: '{product.category}' | 路径: '{product.category_path}'")
            print(f"    用户: {product.created_by} | 使用: {product.usage_count}次 | 价格: {product.reference_price or 0}")
            print(f"    创建时间: {product.created_at}")
            
            if not product.category:
                empty_category_products.append(product)
            print()
        
        # 2. 类别统计
        print("📈 类别统计:")
        for category, count in category_stats.items():
            print(f"  {category}: {count}个产品")
        
        # 3. 显示空类别产品
        if empty_category_products:
            print(f"\n⚠️  发现 {len(empty_category_products)} 个没有类别的产品:")
            for product in empty_category_products:
                print(f"  - {product.product_name} ({product.product_model}) [ID: {product.id}]")
        
        # 4. 模拟前端API查询
        print("\n🔄 模拟前端API查询:")
        
        # 查询基站类别
        basestation_query = TempProduct.query.filter_by(
            category='基站',
            is_deleted=False,
            created_by=5  # 假设用户ID为5
        ).order_by(TempProduct.usage_count.desc()).all()
        
        print(f"基站类别查询结果: {len(basestation_query)}个产品")
        
        # 按产品名称分组
        product_groups = defaultdict(list)
        for product in basestation_query:
            product_groups[product.product_name].append(product)
        
        print("基站类别产品分组:")
        for product_name, products in product_groups.items():
            total_usage = sum(p.usage_count for p in products)
            print(f"  📦 {product_name} (总使用{total_usage}次):")
            for p in products:
                print(f"     └─ {p.product_model} (使用{p.usage_count}次)")
        
        # 5. 检查特定产品
        famst_products = TempProduct.query.filter(
            TempProduct.product_model.like('%FAMST1000%'),
            TempProduct.is_deleted == False
        ).all()
        
        print(f"\n🎯 FAMST1000产品检查: 找到{len(famst_products)}个")
        for product in famst_products:
            print(f"  产品名称: '{product.product_name}'")
            print(f"  产品型号: '{product.product_model}'")
            print(f"  类别: '{product.category}'")
            print(f"  是否在基站类别: {'✅' if product.category == '基站' else '❌'}")
        
        print("\n" + "=" * 50)
        print("🏁 诊断完成")

if __name__ == "__main__":
    main()