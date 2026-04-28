from app import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

PROSPECT_STAGES = {
    'planning': '规划中',
    'designing': '设计中',
    'construction': '在建',
    'completed': '竣工',
}

STAKEHOLDER_TYPES = {
    'owner': '建设单位',
    'consultant': '机电/安防顾问',
    'design': '设计院',
    'main_contractor': '主承包商',
    'system_integrator': '系统集成商',
    'epc': 'EPC/总承包',
    'construction': '施工单位',
    'other': '其他',
}

INFO_SOURCES = {
    'eia': '环评公示',
    'tender': '招标公告',
    'ai': 'AI调研',
    'manual': '人工录入',
}


class ProspectProject(db.Model):
    __tablename__ = 'prospect_projects'

    id = Column(Integer, primary_key=True)
    project_name = Column(String(200), nullable=False, index=True)
    industry = Column(String(50), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    stage = Column(String(20), nullable=False, default='planning')
    total_investment = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    progress = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)
    source = Column(String(20), nullable=True)
    # link_type: 标识 prospect 与 project 的关联语义
    #   'converted' = 该线索已转化为 converted_project_id 指向的项目（原用法）
    #   'research'  = 该记录是为已存在项目反向调研产生的补全数据
    link_type = Column(String(20), nullable=False, default='converted',
                       server_default='converted', index=True)

    claimed_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    claimed_at = Column(DateTime, nullable=True)

    converted_project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)

    info_updated_at = Column(DateTime, nullable=True)
    info_updated_by = Column(String(50), nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    claimed_by = relationship('User', foreign_keys=[claimed_by_id])
    converted_project = relationship('Project', foreign_keys=[converted_project_id])
    stakeholders = relationship('ProspectStakeholder', backref='prospect',
                                cascade='all, delete-orphan', lazy='dynamic')

    @property
    def stage_label(self):
        return PROSPECT_STAGES.get(self.stage, self.stage)

    @property
    def is_claimed(self):
        return self.claimed_by_id is not None

    @property
    def is_converted(self):
        return self.converted_project_id is not None


class ProspectStakeholder(db.Model):
    __tablename__ = 'prospect_stakeholders'

    id = Column(Integer, primary_key=True)
    prospect_id = Column(Integer, ForeignKey('prospect_projects.id'), nullable=False, index=True)
    stakeholder_type = Column(String(20), nullable=False)
    company_name = Column(String(200), nullable=False)
    department = Column(String(100), nullable=True)
    address = Column(String(300), nullable=True)
    phone = Column(String(50), nullable=True)
    contact_person = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    website = Column(String(300), nullable=True)
    business_scope = Column(Text, nullable=True)
    alternative_addresses = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    @property
    def type_label(self):
        return STAKEHOLDER_TYPES.get(self.stakeholder_type, self.stakeholder_type)


class ProspectResearchLog(db.Model):
    """调研任务日志 — 双用途：并发跟踪 + 批量调研每日配额。"""
    __tablename__ = 'prospect_research_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    job_type = Column(String(20), nullable=False)   # 'batch' | 'intel' | 'lost'
    status = Column(String(20), nullable=False, default='running')  # 'running' | 'done' | 'failed'
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    user = relationship('User', foreign_keys=[user_id])
