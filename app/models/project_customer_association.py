from app import db
from datetime import datetime
from zoneinfo import ZoneInfo

def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)

class ProjectCustomerAssociation(db.Model):
    """项目-客户关联模型"""
    __tablename__ = 'project_customer_associations'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    customer_type = db.Column(db.String(50), nullable=False)  # end_user, design_issues, contractor, system_integrator, dealer
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 创建者ID
    created_at = db.Column(db.DateTime, default=get_local_time)
    updated_at = db.Column(db.DateTime, default=get_local_time, onupdate=get_local_time)
    
    # 关联到项目、公司和创建者
    project = db.relationship('Project', backref=db.backref('customer_associations', lazy='dynamic'))
    company = db.relationship('Company', backref=db.backref('project_associations', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by], backref=db.backref('created_associations', lazy='dynamic'), lazy='select')
    
    # 唯一约束，确保同一个项目不会重复关联同一个客户和同一种类型
    __table_args__ = (
        db.UniqueConstraint('project_id', 'company_id', 'customer_type', name='unique_project_company_type'),
    )
    
    def __repr__(self):
        return f'<ProjectCustomerAssociation {self.project.project_name if self.project else "Unknown"} - {self.company.company_name if self.company else "Unknown"} ({self.customer_type})>'
    
    @property
    def customer_type_label(self):
        """获取客户类型的中文标签"""
        type_labels = {
            'end_user': '直接用户',
            'design_issues': '设计院及顾问',
            'contractor': '总承包单位',
            'system_integrator': '系统集成商',
            'dealer': '经销商'
        }
        return type_labels.get(self.customer_type, self.customer_type)
    
    @classmethod
    def get_active_associations(cls, project_id):
        """获取项目的所有关联"""
        from app.models.customer import Company
        return cls.query.filter_by(
            project_id=project_id
        ).join(
            Company
        ).filter(
            Company.is_deleted == False
        ).all()
    
    @classmethod
    def add_association(cls, project_id, company_id, customer_type, created_by=None):
        """添加项目-客户关联"""
        # 检查是否已存在相同的关联
        existing = cls.query.filter_by(
            project_id=project_id,
            company_id=company_id,
            customer_type=customer_type
        ).first()
        
        if existing:
            return False, "该客户已经作为此类型关联到项目中"
        
        # 创建新关联
        try:
            association = cls(
                project_id=project_id,
                company_id=company_id,
                customer_type=customer_type,
                created_by=created_by
            )
        except Exception as e:
            # 如果created_by字段不存在，则不使用该字段
            association = cls(
                project_id=project_id,
                company_id=company_id,
                customer_type=customer_type
            )
        
        db.session.add(association)
        return True, association
    
    @classmethod
    def remove_association(cls, association_id):
        """移除项目-客户关联（硬删除）"""
        association = cls.query.get(association_id)
        if not association:
            return False, "关联不存在"
        
        db.session.delete(association)
        return True, "关联已移除"

# 客户类型选项
CUSTOMER_TYPE_OPTIONS = [
    ('end_user', '直接用户'),
    ('design_issues', '设计院及顾问'),
    ('contractor', '总承包单位'),
    ('system_integrator', '系统集成商'),
    ('dealer', '经销商')
]