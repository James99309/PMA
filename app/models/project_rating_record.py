# -*- coding: utf-8 -*-
"""
项目评分记录模型
记录每个用户对项目的评分操作
"""

from app import db
from datetime import datetime
from sqlalchemy import UniqueConstraint

class ProjectRatingRecord(db.Model):
    """项目评分记录表"""
    __tablename__ = 'project_rating_records'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=1)  # 固定为1星
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一约束：每个用户对每个项目只能有一条评分记录
    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uq_project_user_rating'),
        db.CheckConstraint('rating = 1', name='ck_rating_value'),
    )
    
    # 关联关系
    project = db.relationship('Project', backref='rating_records')
    user = db.relationship('User', backref='rating_records')
    
    def __repr__(self):
        return f'<ProjectRatingRecord {self.id}: Project {self.project_id} by User {self.user_id}>'
    
    @classmethod
    def get_project_rating_info(cls, project_id):
        """获取项目的评分信息"""
        records = cls.query.filter_by(project_id=project_id).all()
        total_stars = len(records)
        raters = [{'id': r.user_id, 'name': r.user.real_name or r.user.username, 'created_at': r.created_at} for r in records]
        return {
            'total_stars': total_stars,
            'raters': raters,
            'records': records
        }
    
    @classmethod
    def user_has_rated(cls, project_id, user_id):
        """检查用户是否已经给项目评分"""
        return cls.query.filter_by(project_id=project_id, user_id=user_id).first() is not None
    
    @classmethod
    def add_rating(cls, project_id, user_id):
        """添加用户评分"""
        # 检查是否已经评分
        if cls.user_has_rated(project_id, user_id):
            # 如果已经评分，直接返回成功，不重复添加
            return True, "评分已存在"
        
        # 先获取当前记录数（在添加新记录之前）
        current_count = cls.query.filter_by(project_id=project_id).count()
        
        # 添加评分记录
        record = cls(project_id=project_id, user_id=user_id, rating=1)
        db.session.add(record)
        
        # 更新项目的总评分
        from app.models.project import Project
        project = Project.query.get(project_id)
        if project:
            project.rating = current_count + 1  # 原有记录数 + 新增的1条
            project.updated_at = datetime.utcnow()
        
        return True, "评分添加成功"
    
    @classmethod
    def remove_rating(cls, project_id, user_id):
        """移除用户评分"""
        record = cls.query.filter_by(project_id=project_id, user_id=user_id).first()
        if not record:
            # 如果没有评分记录，直接返回成功
            return True, "评分不存在"
        
        # 先获取当前记录数（在删除记录之前）
        current_count = cls.query.filter_by(project_id=project_id).count()
        
        # 删除评分记录
        db.session.delete(record)
        
        # 更新项目的总评分
        from app.models.project import Project
        project = Project.query.get(project_id)
        if project:
            remaining_count = current_count - 1  # 当前记录数 - 要删除的1条
            project.rating = remaining_count if remaining_count > 0 else None
            project.updated_at = datetime.utcnow()
        
        return True, "评分移除成功" 
"""
项目评分记录模型
记录每个用户对项目的评分操作
"""

from app import db
from datetime import datetime
from sqlalchemy import UniqueConstraint

class ProjectRatingRecord(db.Model):
    """项目评分记录表"""
    __tablename__ = 'project_rating_records'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=1)  # 固定为1星
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一约束：每个用户对每个项目只能有一条评分记录
    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uq_project_user_rating'),
        db.CheckConstraint('rating = 1', name='ck_rating_value'),
    )
    
    # 关联关系
    project = db.relationship('Project', backref='rating_records')
    user = db.relationship('User', backref='rating_records')
    
    def __repr__(self):
        return f'<ProjectRatingRecord {self.id}: Project {self.project_id} by User {self.user_id}>'
    
    @classmethod
    def get_project_rating_info(cls, project_id):
        """获取项目的评分信息"""
        records = cls.query.filter_by(project_id=project_id).all()
        total_stars = len(records)
        raters = [{'id': r.user_id, 'name': r.user.real_name or r.user.username, 'created_at': r.created_at} for r in records]
        return {
            'total_stars': total_stars,
            'raters': raters,
            'records': records
        }
    
    @classmethod
    def user_has_rated(cls, project_id, user_id):
        """检查用户是否已经给项目评分"""
        return cls.query.filter_by(project_id=project_id, user_id=user_id).first() is not None
    
    @classmethod
    def add_rating(cls, project_id, user_id):
        """添加用户评分"""
        # 检查是否已经评分
        if cls.user_has_rated(project_id, user_id):
            # 如果已经评分，直接返回成功，不重复添加
            return True, "评分已存在"
        
        # 先获取当前记录数（在添加新记录之前）
        current_count = cls.query.filter_by(project_id=project_id).count()
        
        # 添加评分记录
        record = cls(project_id=project_id, user_id=user_id, rating=1)
        db.session.add(record)
        
        # 更新项目的总评分
        from app.models.project import Project
        project = Project.query.get(project_id)
        if project:
            project.rating = current_count + 1  # 原有记录数 + 新增的1条
            project.updated_at = datetime.utcnow()
        
        return True, "评分添加成功"
    
    @classmethod
    def remove_rating(cls, project_id, user_id):
        """移除用户评分"""
        record = cls.query.filter_by(project_id=project_id, user_id=user_id).first()
        if not record:
            # 如果没有评分记录，直接返回成功
            return True, "评分不存在"
        
        # 先获取当前记录数（在删除记录之前）
        current_count = cls.query.filter_by(project_id=project_id).count()
        
        # 删除评分记录
        db.session.delete(record)
        
        # 更新项目的总评分
        from app.models.project import Project
        project = Project.query.get(project_id)
        if project:
            remaining_count = current_count - 1  # 当前记录数 - 要删除的1条
            project.rating = remaining_count if remaining_count > 0 else None
            project.updated_at = datetime.utcnow()
        
        return True, "评分移除成功" 
"""
项目评分记录模型
记录每个用户对项目的评分操作
"""

from app import db
from datetime import datetime
from sqlalchemy import UniqueConstraint

class ProjectRatingRecord(db.Model):
    """项目评分记录表"""
    __tablename__ = 'project_rating_records'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=1)  # 固定为1星
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一约束：每个用户对每个项目只能有一条评分记录
    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uq_project_user_rating'),
        db.CheckConstraint('rating = 1', name='ck_rating_value'),
    )
    
    # 关联关系
    project = db.relationship('Project', backref='rating_records')
    user = db.relationship('User', backref='rating_records')
    
    def __repr__(self):
        return f'<ProjectRatingRecord {self.id}: Project {self.project_id} by User {self.user_id}>'
    
    @classmethod
    def get_project_rating_info(cls, project_id):
        """获取项目的评分信息"""
        records = cls.query.filter_by(project_id=project_id).all()
        total_stars = len(records)
        raters = [{'id': r.user_id, 'name': r.user.real_name or r.user.username, 'created_at': r.created_at} for r in records]
        return {
            'total_stars': total_stars,
            'raters': raters,
            'records': records
        }
    
    @classmethod
    def user_has_rated(cls, project_id, user_id):
        """检查用户是否已经给项目评分"""
        return cls.query.filter_by(project_id=project_id, user_id=user_id).first() is not None
    
    @classmethod
    def add_rating(cls, project_id, user_id):
        """添加用户评分"""
        # 检查是否已经评分
        if cls.user_has_rated(project_id, user_id):
            # 如果已经评分，直接返回成功，不重复添加
            return True, "评分已存在"
        
        # 先获取当前记录数（在添加新记录之前）
        current_count = cls.query.filter_by(project_id=project_id).count()
        
        # 添加评分记录
        record = cls(project_id=project_id, user_id=user_id, rating=1)
        db.session.add(record)
        
        # 更新项目的总评分
        from app.models.project import Project
        project = Project.query.get(project_id)
        if project:
            project.rating = current_count + 1  # 原有记录数 + 新增的1条
            project.updated_at = datetime.utcnow()
        
        return True, "评分添加成功"
    
    @classmethod
    def remove_rating(cls, project_id, user_id):
        """移除用户评分"""
        record = cls.query.filter_by(project_id=project_id, user_id=user_id).first()
        if not record:
            # 如果没有评分记录，直接返回成功
            return True, "评分不存在"
        
        # 先获取当前记录数（在删除记录之前）
        current_count = cls.query.filter_by(project_id=project_id).count()
        
        # 删除评分记录
        db.session.delete(record)
        
        # 更新项目的总评分
        from app.models.project import Project
        project = Project.query.get(project_id)
        if project:
            remaining_count = current_count - 1  # 当前记录数 - 要删除的1条
            project.rating = remaining_count if remaining_count > 0 else None
            project.updated_at = datetime.utcnow()
        
        return True, "评分移除成功" 
"""
项目评分记录模型
记录每个用户对项目的评分操作
"""

from app import db
from datetime import datetime
from sqlalchemy import UniqueConstraint

class ProjectRatingRecord(db.Model):
    """项目评分记录表"""
    __tablename__ = 'project_rating_records'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=1)  # 固定为1星
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一约束：每个用户对每个项目只能有一条评分记录
    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uq_project_user_rating'),
        db.CheckConstraint('rating = 1', name='ck_rating_value'),
    )
    
    # 关联关系
    project = db.relationship('Project', backref='rating_records')
    user = db.relationship('User', backref='rating_records')
    
    def __repr__(self):
        return f'<ProjectRatingRecord {self.id}: Project {self.project_id} by User {self.user_id}>'
    
    @classmethod
    def get_project_rating_info(cls, project_id):
        """获取项目的评分信息"""
        records = cls.query.filter_by(project_id=project_id).all()
        total_stars = len(records)
        raters = [{'id': r.user_id, 'name': r.user.real_name or r.user.username, 'created_at': r.created_at} for r in records]
        return {
            'total_stars': total_stars,
            'raters': raters,
            'records': records
        }
    
    @classmethod
    def user_has_rated(cls, project_id, user_id):
        """检查用户是否已经给项目评分"""
        return cls.query.filter_by(project_id=project_id, user_id=user_id).first() is not None
    
    @classmethod
    def add_rating(cls, project_id, user_id):
        """添加用户评分"""
        # 检查是否已经评分
        if cls.user_has_rated(project_id, user_id):
            # 如果已经评分，直接返回成功，不重复添加
            return True, "评分已存在"
        
        # 先获取当前记录数（在添加新记录之前）
        current_count = cls.query.filter_by(project_id=project_id).count()
        
        # 添加评分记录
        record = cls(project_id=project_id, user_id=user_id, rating=1)
        db.session.add(record)
        
        # 更新项目的总评分
        from app.models.project import Project
        project = Project.query.get(project_id)
        if project:
            project.rating = current_count + 1  # 原有记录数 + 新增的1条
            project.updated_at = datetime.utcnow()
        
        return True, "评分添加成功"
    
    @classmethod
    def remove_rating(cls, project_id, user_id):
        """移除用户评分"""
        record = cls.query.filter_by(project_id=project_id, user_id=user_id).first()
        if not record:
            # 如果没有评分记录，直接返回成功
            return True, "评分不存在"
        
        # 先获取当前记录数（在删除记录之前）
        current_count = cls.query.filter_by(project_id=project_id).count()
        
        # 删除评分记录
        db.session.delete(record)
        
        # 更新项目的总评分
        from app.models.project import Project
        project = Project.query.get(project_id)
        if project:
            remaining_count = current_count - 1  # 当前记录数 - 要删除的1条
            project.rating = remaining_count if remaining_count > 0 else None
            project.updated_at = datetime.utcnow()
        
        return True, "评分移除成功" 