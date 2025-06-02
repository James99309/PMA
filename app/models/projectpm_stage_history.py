from app import db
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, text
from sqlalchemy.sql import func
from app.models.project import Project
from datetime import datetime
from zoneinfo import ZoneInfo

class ProjectStageHistory(db.Model):
    """项目阶段历史记录表
    
    记录项目阶段的变更历史，用于统计分析项目阶段趋势
    """
    __tablename__ = 'project_stage_history'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True)
    from_stage = Column(String(64), nullable=True)  # 变更前阶段
    to_stage = Column(String(64), nullable=False)   # 变更后阶段
    change_date = Column(DateTime, nullable=False)  # 变更时间
    change_week = Column(Integer, nullable=True)    # 变更周（年周数，便于周统计）
    change_month = Column(Integer, nullable=True)   # 变更月（年月，便于月统计）
    change_year = Column(Integer, nullable=True)    # 变更年
    account_id = Column(Integer, nullable=True)     # 账户ID，用于支持按账户切换统计
    remarks = Column(Text, nullable=True)           # 备注说明
    
    created_at = Column(DateTime, server_default=func.now())
    
    # 与项目的关联关系
    project = db.relationship('Project', backref=db.backref('stage_history', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ProjectStageHistory {self.project_id} {self.from_stage} -> {self.to_stage}>'
    
    @staticmethod
    def add_history_record(project_id, from_stage, to_stage, change_date=None, remarks=None, account_id=None, commit=True):
        """添加阶段变更记录，并同步更新项目的更新时间（北京时间）"""
        if change_date is None:
            change_date = func.now()
            
        # 计算年周数和年月
        if isinstance(change_date, datetime):
            change_week = int(change_date.strftime('%Y%W'))
            change_month = int(change_date.strftime('%Y%m'))
            change_year = change_date.year
        else:
            # 如果是 SQL 函数，则在插入后通过触发器或后处理更新
            change_week = None
            change_month = None
            change_year = None
            
        record = ProjectStageHistory(
            project_id=project_id,
            from_stage=from_stage,
            to_stage=to_stage,
            change_date=change_date,
            change_week=change_week,
            change_month=change_month,
            change_year=change_year,
            remarks=remarks,
            account_id=account_id
        )
        
        db.session.add(record)
        
        # 同步更新项目的updated_at字段（北京时间）
        try:
            now = datetime.now(ZoneInfo('Asia/Shanghai'))
            sql = text("UPDATE projects SET updated_at = :now WHERE id = :project_id")
            db.session.execute(sql, {"now": now, "project_id": project_id})
        except Exception as e:
            print(f"同步更新项目更新时间失败: {str(e)}")
        
        # 只在需要时提交事务
        if commit:
            db.session.commit()
            
        return record 
            
        return record 
            
        return record 
            
        return record 