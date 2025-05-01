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
    role = db.Column(db.String(50), nullable=False, default='member')  # 成员在项目中的角色，如 'member', 'editor', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 定义关系
    project = db.relationship('Project', backref=db.backref('members', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('project_memberships', lazy='dynamic'))
    
    def __init__(self, project_id, user_id, role='member'):
        self.project_id = project_id
        self.user_id = user_id
        self.role = role
    
    def __repr__(self):
        return f'<ProjectMember {self.id}: {self.user_id} in project {self.project_id} as {self.role}>' 