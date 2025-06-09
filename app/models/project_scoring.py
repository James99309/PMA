# -*- coding: utf-8 -*-
"""
项目评分系统模型
整合自动评分和人工评分的统一逻辑
"""

from app import db
from datetime import datetime
from sqlalchemy import UniqueConstraint, func
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class ProjectScoringConfig(db.Model):
    """项目评分配置表"""
    __tablename__ = 'project_scoring_config'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # information, quotation, stage, manual
    field_name = db.Column(db.String(100), nullable=False)
    field_label = db.Column(db.String(200), nullable=False)
    score_value = db.Column(db.Numeric(3, 2), nullable=False, default=0.0)
    prerequisite = db.Column(db.Text)  # 前置条件描述
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('category', 'field_name', name='uq_scoring_config'),
    )
    
    def __repr__(self):
        return f'<ProjectScoringConfig {self.category}.{self.field_name}: {self.score_value}>'

class ProjectScoringRecord(db.Model):
    """项目评分记录表"""
    __tablename__ = 'project_scoring_records'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    score_value = db.Column(db.Numeric(3, 2), nullable=False, default=0.0)
    awarded_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    auto_calculated = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('project_id', 'category', 'field_name', name='uq_scoring_record'),
    )
    
    # 关联关系
    project = db.relationship('Project', backref='scoring_records')
    awarded_by_user = db.relationship('User', backref='awarded_scores')
    
    def __repr__(self):
        return f'<ProjectScoringRecord {self.project_id}.{self.category}.{self.field_name}: {self.score_value}>'

class ProjectTotalScore(db.Model):
    """项目总评分表"""
    __tablename__ = 'project_total_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, unique=True)
    information_score = db.Column(db.Numeric(3, 2), default=0.0)
    quotation_score = db.Column(db.Numeric(3, 2), default=0.0)
    stage_score = db.Column(db.Numeric(3, 2), default=0.0)
    manual_score = db.Column(db.Numeric(3, 2), default=0.0)
    total_score = db.Column(db.Numeric(3, 2), default=0.0)
    star_rating = db.Column(db.Numeric(2, 1), default=0.0)  # 支持半星：0.0-5.0
    last_calculated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    project = db.relationship('Project', backref=db.backref('total_score', uselist=False))
    
    def __repr__(self):
        return f'<ProjectTotalScore {self.project_id}: {self.total_score} ({self.star_rating}★)>'

class ProjectScoringEngine:
    """项目评分引擎"""
    
    @classmethod
    def calculate_project_score(cls, project_id, commit=True):
        """
        计算项目总评分
        
        Args:
            project_id: 项目ID
            commit: 是否提交事务，默认为True。如果在更大的事务中调用，应设为False
        
        Returns:
            dict: 评分结果字典，包含各项得分和总分
        """
        try:
            from app.models.project import Project
            from app.models.quotation import Quotation
            
            # 在新的会话中执行评分计算，避免事务冲突
            if commit:
                session = db.session
            else:
                session = db.session
                
            try:
                project = session.query(Project).get(project_id)
                if not project:
                    return None
                
                # 获取或创建总评分记录
                total_score = session.query(ProjectTotalScore).filter_by(project_id=project_id).first()
                if not total_score:
                    total_score = ProjectTotalScore(project_id=project_id)
                    session.add(total_score)
                
                # 1. 计算信息完整性得分
                information_score = cls._calculate_information_score(project)
                
                # 2. 计算报价完整性得分
                quotation_score = cls._calculate_quotation_score(project)
                
                # 3. 计算阶段得分
                stage_score = cls._calculate_stage_score(project)
                
                # 4. 计算手动奖励得分
                manual_score = cls._calculate_manual_score(project_id)
                
                # 5. 计算总分和星级 - 统一转换为Decimal类型
                information_decimal = Decimal(str(information_score))
                quotation_decimal = Decimal(str(quotation_score))
                stage_decimal = Decimal(str(stage_score))
                manual_decimal = Decimal(str(manual_score))
                
                total_decimal = information_decimal + quotation_decimal + stage_decimal + manual_decimal
                total = float(total_decimal)
                
                # 星级计算：支持半星评分
                if total <= 0:
                    star_rating = 0.0
                else:
                    # 每0.5分为半星，最低0.5星，最高5.0星
                    star_rating = min(5.0, max(0.5, round(total * 2) / 2))
                
                # 更新总评分记录
                total_score.information_score = information_decimal
                total_score.quotation_score = quotation_decimal
                total_score.stage_score = stage_decimal
                total_score.manual_score = manual_decimal
                total_score.total_score = total_decimal
                total_score.star_rating = star_rating
                total_score.last_calculated = datetime.utcnow()
                
                # 同步更新项目表的rating字段（保持兼容性）
                project.rating = star_rating
                
                # 由调用者控制是否提交事务
                if commit:
                    session.commit()
                    logger.info(f"项目 {project.project_name} 评分计算完成: {total:.2f}分 ({star_rating}星)")
                
                result = {
                    'project_id': project_id,
                    'information_score': float(information_decimal),
                    'quotation_score': float(quotation_decimal),
                    'stage_score': float(stage_decimal),
                    'manual_score': float(manual_decimal),
                    'total_score': total,
                    'star_rating': float(star_rating)
                }
                
                # 提交事务
                pass
                
                return result
            except Exception as e:
                # 内部异常处理
                if commit:
                    session.rollback()
                raise e
        except Exception as e:
            logger.error(f"计算项目评分失败: {str(e)}")
            if commit:
                db.session.rollback()
            return None
    
    @classmethod
    def _calculate_information_score(cls, project):
        """计算信息完整性得分 - 修正版：累加各项实际得分"""
        score = Decimal('0.0')
        config = ProjectScoringConfig.query.filter_by(category='information', is_active=True).all()
        
        for item in config:
            field_score = Decimal('0.0')
            
            if item.field_name == 'project_stage' and getattr(project, 'current_stage', None):
                field_score = item.score_value
            elif item.field_name == 'project_category' and getattr(project, 'project_type', None):
                field_score = item.score_value
            elif item.field_name == 'design_consultant' and getattr(project, 'design_issues', None):
                # 需要授权编号才能得分
                if getattr(project, 'authorization_code', None):
                    field_score = item.score_value
            elif item.field_name == 'user_info' and getattr(project, 'end_user', None):
                field_score = item.score_value
            elif item.field_name == 'general_contractor' and getattr(project, 'contractor', None):
                field_score = item.score_value
            elif item.field_name == 'system_integrator' and getattr(project, 'system_integrator', None):
                field_score = item.score_value
            
            score += field_score
            
            # 记录或更新评分记录
            cls._update_scoring_record(
                project.id, 'information', item.field_name, 
                field_score, auto_calculated=True
            )
        
        # 信息完整性阈值逻辑：需要达到0.5分才给予半星奖励
        if score >= Decimal('0.5'):
            return Decimal('0.5')
        else:
            return Decimal('0.0')
    
    @classmethod
    def _calculate_quotation_score(cls, project):
        """计算报价完整性得分"""
        from app.models.quotation import Quotation
        
        score = Decimal('0.0')
        
        # 检查是否有报价单（暂时简化，后续可以添加审核状态检查）
        quotations_count = Quotation.query.filter_by(project_id=project.id).count()
        
        if quotations_count > 0:
            config = ProjectScoringConfig.query.filter_by(
                category='quotation', 
                field_name='approved_quotation',
                is_active=True
            ).first()
            
            if config:
                score = config.score_value
                cls._update_scoring_record(
                    project.id, 'quotation', 'approved_quotation',
                    score, auto_calculated=True
                )
        
        return score
    
    @classmethod
    def _calculate_stage_score(cls, project):
        """计算阶段得分"""
        try:
            stage_configs = ProjectScoringConfig.query.filter_by(
                category='stage', is_active=True
            ).all()
            
            if not stage_configs:
                return Decimal('0.0')
            
            # 获取项目当前阶段
            current_stage = getattr(project, 'current_stage', None)
            if not current_stage:
                return Decimal('0.0')
            
            # 阶段层级定义（从低到高）
            stage_hierarchy = {
                'tendering': 0.5,    # 招投标
                'awarded': 1.0,      # 中标  
                'quoted': 1.5,       # 批价
                'signed': 1.5        # 签约（等同于批价，最高1.5分）
            }
            
            # 获取当前阶段对应的分数
            stage_score = stage_hierarchy.get(current_stage, 0.0)
            
            # 同时记录所有已完成的阶段（用于前端显示）
            cls._update_stage_records(project.id, current_stage, stage_hierarchy)
            
            return Decimal(str(stage_score))
            
        except Exception as e:
            logger.error(f"计算阶段得分失败: {str(e)}")
            return Decimal('0.0')
    
    @classmethod
    def _update_stage_records(cls, project_id, current_stage, stage_hierarchy):
        """更新阶段记录，标记已完成的所有阶段"""
        # 阶段顺序
        stage_order = ['tendering', 'awarded', 'quoted', 'signed']
        
        # 获取当前阶段在顺序中的位置
        try:
            current_index = stage_order.index(current_stage)
        except ValueError:
            # 如果当前阶段不在已知阶段中，不做任何处理
            return
        
        # 映射到配置表中的字段名
        field_mapping = {
            'tendering': 'tender',
            'awarded': 'awarded', 
            'quoted': 'final_pricing'
        }
        
        # 清除所有阶段记录
        for field_name in field_mapping.values():
            cls._update_scoring_record(
                project_id, 'stage', field_name, 
                Decimal('0.0'), auto_calculated=True
            )
        
        # 标记已完成的阶段（用于前端显示打勾）
        for i in range(current_index + 1):
            stage = stage_order[i]
            field_name = field_mapping.get(stage)
            if field_name:
                # 已完成的阶段标记为已完成（前端显示用）
                cls._update_scoring_record(
                    project_id, 'stage', field_name, 
                    Decimal('1.0'), auto_calculated=True  # 用1.0标记已完成
                )
    
    @classmethod
    def _calculate_manual_score(cls, project_id):
        """计算手动奖励得分"""
        manual_records = ProjectScoringRecord.query.filter_by(
            project_id=project_id,
            category='manual',
            auto_calculated=False
        ).all()
        
        total = Decimal('0.0')
        for record in manual_records:
            total += Decimal(str(record.score_value))
        
        return total
    
    @classmethod
    def _update_scoring_record(cls, project_id, category, field_name, score_value, auto_calculated=True, awarded_by=None, notes=None):
        """更新或创建评分记录"""
        record = ProjectScoringRecord.query.filter_by(
            project_id=project_id,
            category=category,
            field_name=field_name
        ).first()
        
        if record:
            record.score_value = score_value
            record.updated_at = datetime.utcnow()
            if awarded_by:
                record.awarded_by = awarded_by
            if notes:
                record.notes = notes
        else:
            record = ProjectScoringRecord(
                project_id=project_id,
                category=category,
                field_name=field_name,
                score_value=score_value,
                auto_calculated=auto_calculated,
                awarded_by=awarded_by,
                notes=notes
            )
            db.session.add(record)
    
    @classmethod
    def add_manual_award(cls, project_id, user_id, award_type='supervisor_award', notes=None):
        """添加手动奖励"""
        config = ProjectScoringConfig.query.filter_by(
            category='manual',
            field_name=award_type,
            is_active=True
        ).first()
        
        if not config:
            return False, "奖励类型不存在"
        
        # 检查是否已经有相同的手动奖励
        existing = ProjectScoringRecord.query.filter_by(
            project_id=project_id,
            category='manual',
            field_name=award_type,
            awarded_by=user_id
        ).first()
        
        if existing:
            return False, "已经给予过此类奖励"
        
        # 添加手动奖励记录
        cls._update_scoring_record(
            project_id, 'manual', award_type,
            config.score_value, auto_calculated=False,
            awarded_by=user_id, notes=notes
        )
        
        # 重新计算项目总分
        cls.calculate_project_score(project_id)
        
        return True, "奖励添加成功"
    
    @classmethod
    def remove_manual_award(cls, project_id, user_id, award_type='supervisor_award'):
        """移除手动奖励"""
        record = ProjectScoringRecord.query.filter_by(
            project_id=project_id,
            category='manual',
            field_name=award_type,
            awarded_by=user_id
        ).first()
        
        if not record:
            return False, "奖励记录不存在"
        
        db.session.delete(record)
        
        # 重新计算项目总分
        cls.calculate_project_score(project_id)
        
        return True, "奖励移除成功" 