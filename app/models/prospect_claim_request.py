from app import db
from datetime import datetime
from sqlalchemy import (Column, Integer, String, Text, DateTime, ForeignKey,
                        UniqueConstraint, Index)
from sqlalchemy.orm import relationship


class ProspectClaimRequest(db.Model):
    """申请参与流失项目的记录。

    业务约束：同一申请人对同一项目永久去重（uniqueness on (project_id, applicant_id)）。
    系统不维护审批结果，原负责人收到 Message 后线下处理。
    """
    __tablename__ = 'prospect_claim_requests'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    applicant_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default='pending', nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship('Project', foreign_keys=[project_id])
    applicant = relationship('User', foreign_keys=[applicant_id])

    __table_args__ = (
        UniqueConstraint('project_id', 'applicant_id',
                         name='uq_claim_project_applicant'),
        Index('ix_claim_project', 'project_id'),
        Index('ix_claim_applicant', 'applicant_id'),
    )
