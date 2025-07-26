from app import db
from datetime import datetime, timedelta
from sqlalchemy import Index, or_
import random
import string

class TempProduct(db.Model):
    """
    临时产品模型
    用于存储用户手动输入的临时产品信息
    支持按分类组织和使用频次统计
    """
    __tablename__ = 'temp_products'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 基础产品信息
    product_name = db.Column(db.String(100), nullable=False, comment='产品名称')
    product_model = db.Column(db.String(100), nullable=False, comment='产品型号')
    product_desc = db.Column(db.Text, comment='产品描述/规格')
    brand = db.Column(db.String(50), comment='品牌')
    unit = db.Column(db.String(20), default='个', comment='单位')
    product_mn = db.Column(db.String(50), comment='临时产品MN号，格式为TEMP-{8位随机码}')
    
    # 分类关联
    category = db.Column(db.String(50), comment='关联的三级分类')
    category_path = db.Column(db.String(200), comment='完整分类路径，如：基站/近端设备/室内型')
    
    # 用户关联
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='创建用户ID')
    
    # 价格信息（参考价格）
    reference_price = db.Column(db.Float, comment='参考价格（保存时的单价）')
    
    # 使用统计
    usage_count = db.Column(db.Integer, default=0, comment='使用次数')
    last_used_at = db.Column(db.DateTime, comment='最后使用时间')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 软删除
    is_deleted = db.Column(db.Boolean, default=False, comment='是否已删除')
    
    # 关联关系
    creator = db.relationship('User', backref=db.backref('temp_products', lazy='dynamic'))
    
    # 索引定义
    __table_args__ = (
        Index('idx_temp_product_category', 'category'),
        Index('idx_temp_product_creator', 'created_by'),
        Index('idx_temp_product_model_creator', 'product_model', 'created_by'),
        Index('idx_temp_product_usage', 'usage_count'),
        Index('idx_temp_product_deleted', 'is_deleted'),
    )
    
    def to_dict(self):
        """转换为字典格式，用于API返回"""
        return {
            'id': self.id,
            'product_name': self.product_name,
            'product_model': self.product_model,
            'product_desc': self.product_desc,
            'brand': self.brand,
            'unit': self.unit,
            'product_mn': self.product_mn,  # 临时产品MN号
            'category': self.category,
            'category_path': self.category_path,
            'reference_price': self.reference_price or 0,  # 参考价格
            'usage_count': self.usage_count,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat(),
            'is_temp': True,  # 标识这是临时产品
            'market_price': self.reference_price or 0,  # 使用参考价格作为市场价
            'status': 'temp'  # 特殊状态标识
        }
    
    def increment_usage(self):
        """增加使用次数"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def get_by_category(cls, category, user_id, include_deleted=False):
        """根据分类获取临时产品"""
        query = cls.query.filter_by(category=category, created_by=user_id)
        
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        
        return query.order_by(cls.usage_count.desc(), cls.updated_at.desc()).all()
    
    @classmethod
    def get_by_user(cls, user_id, limit=None, include_deleted=False):
        """获取用户的所有临时产品"""
        query = cls.query.filter_by(created_by=user_id)
        
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        
        query = query.order_by(cls.usage_count.desc(), cls.updated_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def find_similar(cls, product_model, user_id):
        """查找相似的产品型号"""
        return cls.query.filter_by(
            product_model=product_model,
            created_by=user_id,
            is_deleted=False
        ).first()
    
    @classmethod
    def get_popular_by_category(cls, category, user_id, limit=10):
        """获取该分类下最常用的临时产品"""
        return cls.query.filter_by(
            category=category,
            created_by=user_id,
            is_deleted=False
        ).filter(cls.usage_count > 0).order_by(
            cls.usage_count.desc(),
            cls.last_used_at.desc()
        ).limit(limit).all()
    
    def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.updated_at = datetime.utcnow()
    
    def restore(self):
        """恢复删除"""
        self.is_deleted = False
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def generate_unique_mn(cls, creation_time=None):
        """
        生成唯一的临时产品MN号
        格式: TP{YYMMDDHHMM}，例如：TP2504101012
        如果同一分钟内有重复，则在末尾添加序号
        """
        from app.models.product import Product
        
        # 使用传入的时间或当前时间
        if creation_time is None:
            creation_time = datetime.utcnow()
        
        # 生成基础MN号：TP + YYMMDDHHMM
        time_str = creation_time.strftime('%y%m%d%H%M')
        base_mn = f'TP{time_str}'
        
        # 检查基础MN号是否已存在
        temp_exists = cls.query.filter_by(product_mn=base_mn, is_deleted=False).first()
        regular_exists = Product.query.filter_by(product_mn=base_mn).first()
        
        if not temp_exists and not regular_exists:
            return base_mn
        
        # 如果基础MN号已存在，添加两位数字序号
        for i in range(1, 100):  # 支持同一分钟内最多99个临时产品
            mn_code = f'{base_mn}{i:02d}'
            
            # 检查是否与临时产品MN号重复
            temp_exists = cls.query.filter_by(product_mn=mn_code, is_deleted=False).first()
            if temp_exists:
                continue
                
            # 检查是否与常规产品MN号重复
            regular_exists = Product.query.filter_by(product_mn=mn_code).first()
            if regular_exists:
                continue
                
            # 找到唯一的MN号
            return mn_code
        
        # 如果99个序号都被占用，抛出异常
        raise ValueError(f'同一分钟内临时产品MN号已达上限，请稍后重试')
    
    def generate_mn(self):
        """为当前临时产品生成MN号"""
        if not self.product_mn:
            self.product_mn = self.generate_unique_mn()
            self.updated_at = datetime.utcnow()
    
    @classmethod
    def cleanup_old_records(cls, days=90):
        """清理超过指定天数且使用次数为0的记录"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_records = cls.query.filter(
            cls.created_at < cutoff_date,
            cls.usage_count == 0,
            cls.is_deleted == False
        ).all()
        
        count = 0
        for record in old_records:
            record.soft_delete()
            count += 1
        
        if count > 0:
            db.session.commit()
        
        return count
    
    def __repr__(self):
        return f'<TempProduct {self.product_name} ({self.product_model})>'