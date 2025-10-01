#!/usr/bin/env python3
"""
调试产品上传API的脚本
"""

import sys
sys.path.append('.')

try:
    from app import create_app
    from app.models.product import Product
    from app.extensions import db
    from flask import url_for
    
    print("✅ 成功导入Flask应用模块")
    
    app = create_app()
    
    with app.app_context():
        # 测试数据库连接
        try:
            products = Product.query.limit(1).all()
            print(f"✅ 数据库连接正常，找到 {len(products)} 个产品")
            
            if products:
                product = products[0]
                print(f"📦 测试产品: ID={product.id}, 名称={product.name}")
                
                # 测试API路由是否存在
                try:
                    api_url = url_for('product_route.upload_product_files', product_id=product.id)
                    print(f"✅ API路由存在: {api_url}")
                except Exception as e:
                    print(f"❌ API路由不存在: {str(e)}")
            
        except Exception as e:
            print(f"❌ 数据库连接错误: {str(e)}")
            
        # 测试Supabase客户端
        try:
            from app.utils.supabase_client import get_supabase_client
            supabase_client = get_supabase_client()
            print(f"✅ Supabase客户端获取成功")
        except Exception as e:
            print(f"❌ Supabase客户端错误: {str(e)}")
            
except ImportError as e:
    print(f"❌ 导入错误: {str(e)}")
except Exception as e:
    print(f"❌ 应用初始化错误: {str(e)}")