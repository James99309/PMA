# -*- coding: utf-8 -*-
"""
培训系统模型 — 供 pma-training skill (v2.0+) 使用

四张表:
- TrainingModuleState: 学员每模块进度
- TrainingQuizAttempt: 答题记录(含错题本间隔重现调度)
- TrainingStreak: 全局连续学习 streak (per user)
- TrainingApplicationSubmission: 应用任务交付归档

设计原则:
- 课程内容(modules/chapters)定义在 skill 包内 curriculum.md, 不在 DB
- DB 只存"用户动态状态" — 进度/答题/streak/任务交付
- 章节用 wiki article slug 引用, 不复制内容
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, Boolean, ForeignKey, JSON, Index,
)

from app import db


def get_local_time():
    """本地时间(北京时区), naive datetime"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# 1. 模块进度
# ---------------------------------------------------------------------------

class TrainingModuleState(db.Model):
    """学员在某门课的某个模块的进度状态.

    一个 (user_id, course_slug, module_slug) 组合唯一一条记录.
    """
    __tablename__ = 'training_module_state'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)

    # 课程 / 模块 slug — 与 curriculum.md 文件里的 slug 对应
    course_slug = Column(String(80), nullable=False, index=True)
    module_slug = Column(String(80), nullable=False, index=True)

    # 状态: not_started / in_progress / passed / failed / skipped
    status = Column(String(20), nullable=False, default='not_started', index=True)

    # 学员"卡在哪" — 用于下次进来续上
    current_chapter = Column(Integer, default=0)        # 0 表示还没开始第 1 章
    current_section = Column(Integer, default=0)        # 节内位置(章内子段)

    # 已通过的章节列表
    # 结构: [{"chapter": 1, "score": 90, "passed_at": "2026-05-13T10:00:00"}, ...]
    chapters_passed = Column(JSON, default=list, nullable=False)

    # 模块综合考核
    final_exam_score = Column(Integer, nullable=True)
    final_exam_passed_at = Column(DateTime, nullable=True)

    # 徽章
    badge_awarded = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=get_local_time, nullable=False)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time, nullable=False)

    __table_args__ = (
        Index('ix_tms_user_course_module', 'user_id', 'course_slug', 'module_slug', unique=True),
        Index('ix_tms_user_status', 'user_id', 'status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_slug': self.course_slug,
            'module_slug': self.module_slug,
            'status': self.status,
            'current_chapter': self.current_chapter,
            'current_section': self.current_section,
            'chapters_passed': self.chapters_passed or [],
            'final_exam_score': self.final_exam_score,
            'final_exam_passed_at': self.final_exam_passed_at.isoformat() if self.final_exam_passed_at else None,
            'badge_awarded': self.badge_awarded,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ---------------------------------------------------------------------------
# 2. 答题记录 + 错题本调度
# ---------------------------------------------------------------------------

class TrainingQuizAttempt(db.Model):
    """每次答题一条记录.

    既是答题日志(便于数据分析), 又是错题本调度表(scheduled_review_at 字段).
    """
    __tablename__ = 'training_quiz_attempt'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)

    course_slug = Column(String(80), nullable=False)
    module_slug = Column(String(80), nullable=False, index=True)
    chapter = Column(Integer, nullable=False)        # 1-based

    # 题目唯一标识 — AI 生成的题用 hash, 后续判断是不是同题
    question_id = Column(String(64), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=True)  # single / multi / judge / scenario

    user_answer = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=False)

    attempted_at = Column(DateTime, default=get_local_time, nullable=False, index=True)

    # 错题本调度 — 错过的题进重现队列
    # scheduled_review_at = NULL 表示已升级出错题本(连续答对 3 次后)
    scheduled_review_at = Column(DateTime, nullable=True, index=True)
    reviewed_count = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index('ix_tqa_user_due_review', 'user_id', 'scheduled_review_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_slug': self.course_slug,
            'module_slug': self.module_slug,
            'chapter': self.chapter,
            'question_id': self.question_id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'user_answer': self.user_answer,
            'correct_answer': self.correct_answer,
            'is_correct': self.is_correct,
            'attempted_at': self.attempted_at.isoformat() if self.attempted_at else None,
            'scheduled_review_at': self.scheduled_review_at.isoformat() if self.scheduled_review_at else None,
            'reviewed_count': self.reviewed_count,
        }


# ---------------------------------------------------------------------------
# 3. 全局 streak
# ---------------------------------------------------------------------------

class TrainingStreak(db.Model):
    """连续学习天数 — 每用户一条, 全局(跨课程/模块)统计.

    每天有任意培训动作 → maintain_streak() 维持
    错过一整天 → 归 0
    """
    __tablename__ = 'training_streak'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    last_learned_date = Column(Date, nullable=True)
    current_streak = Column(Integer, nullable=False, default=0)
    longest_streak = Column(Integer, nullable=False, default=0)

    # streak freeze 券(类似 Duolingo): 用户休一天 freeze 不归零
    streak_freeze_count = Column(Integer, nullable=False, default=0)

    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time, nullable=False)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'last_learned_date': self.last_learned_date.isoformat() if self.last_learned_date else None,
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'streak_freeze_count': self.streak_freeze_count,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ---------------------------------------------------------------------------
# 4. 应用任务交付
# ---------------------------------------------------------------------------

class TrainingApplicationSubmission(db.Model):
    """模块末应用任务的学员交付存档.

    主管可在 PMA 后台查阅 (reviewed_by 字段供未来扩展).
    """
    __tablename__ = 'training_application_submission'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)

    course_slug = Column(String(80), nullable=False)
    module_slug = Column(String(80), nullable=False, index=True)
    task_id = Column(String(80), nullable=False)        # 任务的唯一标识(curriculum.md 里的章节/任务名)

    submission_text = Column(Text, nullable=False)
    ai_feedback = Column(Text, nullable=True)

    submitted_at = Column(DateTime, default=get_local_time, nullable=False)

    # 主管复核(未来扩展, 现暂时 NULL)
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_comment = Column(Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_slug': self.course_slug,
            'module_slug': self.module_slug,
            'task_id': self.task_id,
            'submission_text': self.submission_text,
            'ai_feedback': self.ai_feedback,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewer_comment': self.reviewer_comment,
        }
