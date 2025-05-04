import msoffcrypto
import io
from openpyxl import load_workbook
from app import create_app, db
from app.models.product import Product

def import_products_from_excel(file_path, password):
    try:
        print("开始导入产品数据...")
        
        # 创建一个临时的字节流来存储解密后的文件
        decrypted = io.BytesIO()
        
        # 打开加密的文件
        with open(file_path, 'rb') as file:
            office_file = msoffcrypto.OfficeFile(file)
            office_file.load_key(password=password)
            office_file.decrypt(decrypted)
        
        # 将字节流的位置重置到开始
        decrypted.seek(0)
        
        # 使用openpyxl读取解密后的内容
        wb = load_workbook(filename=decrypted, data_only=True)
        ws = wb['Pricelist']  # 获取Pricelist工作表
        
        # 跳过标题行
        rows = list(ws.rows)[2:]  # 从第3行开始(跳过空行和标题行)
        
        # 创建Flask应用上下文
        app = create_app()
        with app.app_context():
            # 遍历每一行数据
            for row in rows:
                # 如果行为空或者产品名称为空，跳过
                if not row[5].value:
                    continue
                    
                # 创建新的产品记录
                product = Product(
                    type=row[1].value,
                    category=row[3].value,
                    product_mn=row[4].value,
                    product_name=row[5].value,
                    model=row[6].value,
                    specification=row[7].value,
                    brand=row[8].value,
                    unit=row[9].value,
                    retail_price=row[10].value,
                    is_discontinued=bool(row[11].value) if row[11].value is not None else False
                )
                
                # 添加到数据库会话
                db.session.add(product)
                
                print(f"添加产品: {product.product_name} ({product.product_mn})")
            
            # 提交所有更改
            db.session.commit()
            print("产品数据导入完成！")
            
    except Exception as e:
        print(f"导入数据时出错: {str(e)}")
        if 'db' in locals():
            db.session.rollback()
    finally:
        if 'wb' in locals():
            wb.close()
        if 'decrypted' in locals():
            decrypted.close()

if __name__ == "__main__":
    file_path = "evertac-pricelist.xlsm"
    password = "1505562299AaBb"
    import_products_from_excel(file_path, password) 