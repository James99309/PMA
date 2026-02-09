"""
关系模型模块
用于定义各种实体间的关联关系
"""
from app import db
from datetime import datetime

class ProjectMember(db.Model):
    """
    项目成员关联模型
    用于记录项目与成员之间的关系
    """
    __tablename__ = 'project_members'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='member')  # member, solution_engineer, product_manager
    source = db.Column(db.String(50), default='manual', comment='关联来源: manual, retroactive')
    source_workitem_id = db.Column(db.Integer, db.ForeignKey('work_items.id'), nullable=True)
    first_associated_at = db.Column(db.DateTime, nullable=True, comment='首次关联时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('project_id', 'user_id', 'role', name='uq_project_member_user_role'),
    )

    # 定义关系
    project = db.relationship('Project', backref=db.backref('members', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('project_memberships', lazy='dynamic'))
    source_workitem = db.relationship('WorkItem', foreign_keys=[source_workitem_id])

    def __init__(self, project_id, user_id, role='member', source='manual',
                 source_workitem_id=None, first_associated_at=None):
        self.project_id = project_id
        self.user_id = user_id
        self.role = role
        self.source = source
        self.source_workitem_id = source_workitem_id
        self.first_associated_at = first_associated_at

    def __repr__(self):
        return f'<ProjectMember {self.id}: {self.user_id} in project {self.project_id} as {self.role}>'
