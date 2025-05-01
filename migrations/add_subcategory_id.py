from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app import create_app, db
from app.models.product_code import ProductCode, ProductCategory, ProductSubcategory

app = create_app()

def run_migration():
    with app.app_context():
        # 1. 添加新列
        db.session.execute('ALTER TABLE product_codes ADD COLUMN subcategory_id INTEGER REFERENCES product_subcategories(id)')
        
        # 2. 获取所有产品编码
        product_codes = db.session.query(ProductCode).all()
        
        # 3. 更新每个产品编码的subcategory_id
        for code in product_codes:
            # 根据编码的前两个字符获取分类和子分类信息
            if code.full_code and len(code.full_code) >= 2:
                category_letter = code.full_code[0]
                subcategory_letter = code.full_code[1]
                
                # 查找对应的分类和子分类
                category = db.session.query(ProductCategory).filter_by(code_letter=category_letter).first()
                if category:
                    subcategory = db.session.query(ProductSubcategory).filter_by(
                        category_id=category.id, 
                        code_letter=subcategory_letter
                    ).first()
                    
                    if subcategory:
                        # 更新subcategory_id
                        code.subcategory_id = subcategory.id
        
        # 4. 提交更改
        db.session.commit()
        
        print("迁移完成: 已添加subcategory_id字段到product_codes表并填充现有数据")

if __name__ == '__main__':
    run_migration() 