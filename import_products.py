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
        
        # 读取表头行，建立列名到索引的映射
        header_row = list(ws.rows)[1]  # 假设第2行为表头
        header_map = {cell.value.strip(): idx for idx, cell in enumerate(header_row) if cell.value}
        
        # 需要的字段名
        FIELD_MAP = {
            'type': ['类型', 'Type'],
            'category': ['类别', 'Category'],
            'product_mn': ['MN', '产品编码', 'Product MN'],
            'product_name': ['产品名称', '名称', 'Product Name'],
            'model': ['型号', 'Model'],
            'specification': ['规格', 'Specification'],
            'brand': ['品牌', 'Brand'],
            'unit': ['单位', 'Unit'],
            'retail_price': ['零售价', '零售价格', 'Retail Price'],
            'is_discontinued': ['已停产', '停产', 'Discontinued']
        }
        
        def get_col_idx(field_key):
            for name in FIELD_MAP[field_key]:
                if name in header_map:
                    return header_map[name]
            return None
        
        # 创建Flask应用上下文
        app = create_app()
        with app.app_context():
            # 遍历每一行数据
            for row in list(ws.rows)[2:]:  # 从第3行开始(跳过空行和标题行)
                # 按表头名取产品名称
                name_idx = get_col_idx('product_name')
                if name_idx is None or not row[name_idx].value:
                    continue
                product = Product(
                    type=row[get_col_idx('type')].value if get_col_idx('type') is not None else None,
                    category=row[get_col_idx('category')].value if get_col_idx('category') is not None else None,
                    product_mn=row[get_col_idx('product_mn')].value if get_col_idx('product_mn') is not None else None,
                    product_name=row[name_idx].value,
                    model=row[get_col_idx('model')].value if get_col_idx('model') is not None else None,
                    specification=row[get_col_idx('specification')].value if get_col_idx('specification') is not None else None,
                    brand=row[get_col_idx('brand')].value if get_col_idx('brand') is not None else None,
                    unit=row[get_col_idx('unit')].value if get_col_idx('unit') is not None else None,
                    retail_price=row[get_col_idx('retail_price')].value if get_col_idx('retail_price') is not None else None,
                    is_discontinued=bool(row[get_col_idx('is_discontinued')].value) if get_col_idx('is_discontinued') is not None and row[get_col_idx('is_discontinued')].value is not None else False
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