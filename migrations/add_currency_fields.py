#!/usr/bin/env python3
"""
数据库迁移脚本：添加货币字段
为产品表、报价单表、报价单明细表、批价单表和批价单明细表添加货币字段
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def add_currency_fields():
    """添加货币字段到相关表"""
    app = create_app()
    
    with app.app_context():
        try:
            # 1. 为产品表添加货币字段
            print("为产品表添加货币字段...")
            db.session.execute(text("""
                ALTER TABLE products 
                ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'CNY'
            """))
            
            # 2. 为报价单表添加货币字段
            print("为报价单表添加货币字段...")
            db.session.execute(text("""
                ALTER TABLE quotations 
                ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'CNY'
            """))
            
            # 3. 为报价单明细表添加货币字段
            print("为报价单明细表添加货币字段...")
            db.session.execute(text("""
                ALTER TABLE quotation_details 
                ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'CNY'
            """))
            
            # 4. 为批价单表添加货币字段
            print("为批价单表添加货币字段...")
            db.session.execute(text("""
                ALTER TABLE pricing_orders 
                ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'CNY'
            """))
            
            # 5. 为批价单明细表添加货币字段
            print("为批价单明细表添加货币字段...")
            db.session.execute(text("""
                ALTER TABLE pricing_order_details 
                ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'CNY'
            """))
            
            # 6. 为结算单明细表添加货币字段
            print("为结算单明细表添加货币字段...")
            db.session.execute(text("""
                ALTER TABLE settlement_order_details 
                ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'CNY'
            """))
            
            # 提交更改
            db.session.commit()
            print("✅ 货币字段添加成功！")
            
            # 验证字段是否添加成功
            print("\n验证字段添加情况：")
            tables = ['products', 'quotations', 'quotation_details', 'pricing_orders', 'pricing_order_details', 'settlement_order_details']
            for table in tables:
                result = db.session.execute(text(f"""
                    SELECT column_name, data_type, column_default 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = 'currency'
                """))
                row = result.fetchone()
                if row:
                    print(f"  {table}: ✅ currency {row[1]} DEFAULT {row[2]}")
                else:
                    print(f"  {table}: ❌ currency字段未找到")
                    
        except Exception as e:
            print(f"❌ 添加货币字段失败: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    add_currency_fields() 