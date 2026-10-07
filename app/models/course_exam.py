# -*- coding: utf-8 -*-
"""课程考核:题库 + 每人每课学习进度。设计见 docs/plans/2026-10-07-course-exam-bank-design.md"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index

from app import db
from app.models.training import get_local_time


class CourseQuizQuestion(db.Model):
    __tablename__ = 'course_quiz_questions'

    id = Column(Integer, primary_key=True)
    course_key = Column(String(80), nullable=False, index=True)
    qtype = Column(String(10), nullable=False)               # single / multi / judge
    difficulty = Column(Integer, nullable=False, default=2)   # 1 易 / 2 中 / 3 难(生效值)
    ai_difficulty = Column(Integer, nullable=True)            # 复核 AI 独立评级
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)                     # judge 为空
    answer = Column(JSON, nullable=False)                     # int / [int] / bool,原始下标
    explain = Column(Text, nullable=True)
    source_page = Column(Integer, nullable=True)
    status = Column(String(10), nullable=False, default='active', index=True)  # active/review/disabled
    origin = Column(String(10), nullable=False, default='ai')  # ai / edited / legacy
    review_note = Column(Text, nullable=True)                 # 复核 AI 给出的存疑理由
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=get_local_time, nullable=False)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time, nullable=False)

    __table_args__ = (Index('ix_cqq_course_status', 'course_key', 'status'),)

    def as_logic(self):
        """转成 logic.py 用的 dict。"""
        return {'id': self.id, 'qtype': self.qtype, 'difficulty': self.difficulty,
                'options': self.options or [], 'answer': self.answer}

    def to_admin_dict(self):
        return {'id': self.id, 'qtype': self.qtype, 'difficulty': self.difficulty,
                'ai_difficulty': self.ai_difficulty, 'question': self.question,
                'options': self.options or [], 'answer': self.answer, 'explain': self.explain or '',
                'source_page': self.source_page, 'status': self.status, 'origin': self.origin,
                'review_note': self.review_note or ''}


class CourseLearningProgress(db.Model):
    __tablename__ = 'course_learning_progress'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    course_key = Column(String(80), nullable=False, index=True)

    page_seconds = Column(JSON, nullable=False, default=dict)  # {"1": 35, ...}
    last_ping_at = Column(DateTime, nullable=True)
    unlocked_at = Column(DateTime, nullable=True)

    score = Column(Integer, nullable=False, default=0)
    current_question_id = Column(Integer, nullable=True)
    current_option_order = Column(JSON, nullable=True)
    current_answered = Column(Boolean, nullable=False, default=False)
    current_result = Column(JSON, nullable=True)               # 已提交未点下一题时的结果快照
    passed_at = Column(DateTime, nullable=True)
    perfect_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=get_local_time, nullable=False)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time, nullable=False)

    __table_args__ = (Index('ix_clp_user_course', 'user_id', 'course_key', unique=True),)
