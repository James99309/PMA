# 优化的数据库二进制存储模型示例
from datetime import datetime
from sqlalchemy import ForeignKey, Column, Integer, String, Text, Float, DateTime, Boolean, LargeBinary
from sqlalchemy.orm import relationship, deferred
from app import db

class DevProduct(db.Model):
    __tablename__ = 'dev_products'
    
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('product_categories.id'))
    subcategory_id = Column(Integer, ForeignKey('product_subcategories.id'))
    region_id = Column(Integer, ForeignKey('product_regions.id'))
    name = Column(String(100))
    model = Column(String(100))
    status = Column(String(50))
    unit = Column(String(20))
    retail_price = Column(Float)
    currency = Column(String(10), default='CNY')
    description = Column(Text)
    
    # 文件元数据（经常查询）
    has_image = Column(Boolean, default=False)          # 是否有图片
    image_filename = Column(String(255))                # 原始文件名
    image_content_type = Column(String(100))            # MIME类型
    image_size = Column(Integer)                        # 文件大小
    
    has_pdf = Column(Boolean, default=False)            # 是否有PDF
    pdf_filename = Column(String(255))                  # 原始文件名
    pdf_content_type = Column(String(100))              # MIME类型
    pdf_size = Column(Integer)                          # 文件大小
    
    # 文件二进制数据（延迟加载）
    image_data = deferred(Column(LargeBinary))          # 图片数据 - 延迟加载
    pdf_data = deferred(Column(LargeBinary))            # PDF数据 - 延迟加载
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey('users.id'))
    created_by = Column(Integer, ForeignKey('users.id'))
    mn_code = Column(String(20))
    
    # 关联关系
    category = relationship("ProductCategory", foreign_keys=[category_id])
    subcategory = relationship("ProductSubcategory", foreign_keys=[subcategory_id])
    region = relationship("ProductRegion", foreign_keys=[region_id])
    owner = relationship("User", foreign_keys=[owner_id])
    creator = relationship("User", foreign_keys=[created_by])
    specs = relationship("DevProductSpec", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DevProduct {self.model}>"

# 优化的查询示例
class DevProductQueries:
    
    @staticmethod
    def get_list_data():
        """获取列表数据（不包含文件）"""
        return DevProduct.query.with_entities(
            DevProduct.id,
            DevProduct.name,
            DevProduct.model,
            DevProduct.status,
            DevProduct.has_image,      # 只查询是否有文件
            DevProduct.has_pdf,
            DevProduct.image_filename,
            DevProduct.pdf_filename
        ).all()
    
    @staticmethod
    def get_product_with_image(product_id):
        """获取产品和图片数据"""
        return DevProduct.query.options(
            # 显式加载图片数据
            db.undefer(DevProduct.image_data)
        ).filter_by(id=product_id).first()
    
    @staticmethod
    def get_product_with_pdf(product_id):
        """获取产品和PDF数据"""
        return DevProduct.query.options(
            # 显式加载PDF数据
            db.undefer(DevProduct.pdf_data)
        ).filter_by(id=product_id).first()

# 文件大小配置
FILE_SIZE_LIMITS = {
    'image': {
        'max_size': 2 * 1024 * 1024,    # 2MB
        'allowed_types': ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    },
    'pdf': {
        'max_size': 8 * 1024 * 1024,    # 8MB  
        'allowed_types': ['application/pdf']
    }
}

# 优化的文件处理函数
def save_file_to_db(file, file_type='image'):
    """保存文件到数据库的优化函数"""
    if not file or file.filename == '':
        return None, "没有选择文件"
    
    # 获取文件内容
    file.seek(0)
    file_data = file.read()
    file_size = len(file_data)
    
    # 检查文件大小
    max_size = FILE_SIZE_LIMITS[file_type]['max_size']
    if file_size > max_size:
        return None, f"文件大小超过限制 ({max_size // (1024*1024)}MB)"
    
    # 检查文件类型
    import magic
    detected_type = magic.from_buffer(file_data, mime=True)
    if detected_type not in FILE_SIZE_LIMITS[file_type]['allowed_types']:
        return None, f"不支持的文件类型: {detected_type}"
    
    return {
        'data': file_data,
        'filename': file.filename,
        'content_type': detected_type,
        'size': file_size
    }, None