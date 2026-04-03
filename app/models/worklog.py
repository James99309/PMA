# -*- coding: utf-8 -*-
"""
工作日历与日志模块 - 数据模型

WorkItem: 工作项/日历事件
WorkLog: 日志汇总
"""
import json
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Text, Date, Time, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app import db


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class WorkItem(db.Model):
    """工作项模型 - 日历事件"""
    __tablename__ = 'work_items'

    id = Column(Integer, primary_key=True)

    # 基本信息
    title = Column(String(200), nullable=False)         # 工作标题
    description = Column(Text)                          # 工作描述

    # 时间安排
    planned_date = Column(Date, nullable=False, index=True)  # 计划日期（开始日期）
    end_date = Column(Date, nullable=True)              # 结束日期（可选，跨天任务用）
    start_time = Column(Time)                           # 开始时间（可选）
    end_time = Column(Time)                             # 结束时间（可选）
    is_all_day = Column(Boolean, default=True)          # 全天事件
    estimated_hours = Column(Float)                     # 预计时长

    # 关联信息
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    project = relationship('Project', backref='work_items')

    customer_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    customer = relationship('Company', backref='work_items')

    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=True)
    contact = relationship('Contact', backref='work_items')

    work_type = Column(String(50))                      # 工作类型（visit/meeting/development/research/admin/other）

    # 执行状态
    status = Column(String(20), default='planned', index=True)  # planned, completed, cancelled
    completed_at = Column(DateTime)                     # 完成时间
    actual_hours = Column(Float)                        # 实际时长
    execution_notes = Column(Text)                      # 执行备注/补充内容

    # 日志关联
    worklog_id = Column(Integer, ForeignKey('worklogs.id'), nullable=True)
    worklog = relationship('WorkLog', back_populates='work_items')

    # 系统字段
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner = relationship('User', backref='work_items')

    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = Column(Boolean, default=False)
    is_invalidated = Column(Boolean, default=False)  # 标记为无效（中划线显示，保留记录）
    is_business_trip = Column(Boolean, default=False)  # 是否出差

    # 共享字段
    shared_with_users = Column(JSON, default=list)  # 共享用户ID列表 [3, 5, 8]

    # 附件
    attachments = Column(Text, nullable=True)  # JSON: [{filename, url, size, type, uploaded_at}]

    # 工作类型颜色映射（9个大类颜色）
    TYPE_COLORS = {
        # 通用-其他 - 灰色 #64748b
        'other': '#64748b',
        # 行销 - 绿色 #22c55e (含通用的会议)
        'meeting': '#22c55e',
        'customer_visit': '#22c55e',
        'presales_support': '#22c55e',
        'business_negotiation': '#22c55e',
        'customer_maintenance': '#22c55e',
        # 市场 - 橙色 #f59e0b
        'market_planning': '#f59e0b',      # [隐藏] 旧类型，保留数据兼容
        'brand_promotion': '#f59e0b',      # [隐藏] 旧类型，保留数据兼容
        'event_execution': '#f59e0b',      # [隐藏] 旧类型，保留数据兼容
        'video_production': '#f59e0b',     # 视频制作
        'material_design': '#f59e0b',      # 物料设计
        'social_media_operation': '#f59e0b',  # 社媒运营
        'channel_activity': '#f59e0b',     # 渠道活动
        'brand_event': '#f59e0b',          # 品牌活动
        # 服务 - 蓝色 #3b82f6
        'onsite_maintenance': '#3b82f6',
        'service_response': '#3b82f6',
        'technical_support': '#3b82f6',
        'troubleshooting': '#3b82f6',
        # 行政 - 紫色 #8b5cf6 (含通用的内部培训)
        'internal_training': '#8b5cf6',
        'admin_affairs': '#8b5cf6',
        'office_management': '#8b5cf6',
        'asset_management': '#8b5cf6',
        # 人事 - 粉色 #ec4899
        'hr_affairs': '#ec4899',
        'recruitment': '#ec4899',
        'employee_relations': '#ec4899',
        'performance_management': '#ec4899',
        # 财务 - 青色 #14b8a6
        'finance_work': '#14b8a6',
        'expense_review': '#14b8a6',
        'accounting': '#14b8a6',
        # 产品 - 橘色 #f97316
        'product_research': '#f97316',
        'requirement_analysis': '#f97316',
        'product_planning': '#f97316',
        # 供应链 - 天蓝 #06b6d4
        'procurement': '#06b6d4',
        'inventory_management': '#06b6d4',
        'logistics': '#06b6d4',
        'quality_tracking': '#06b6d4',
        # 产品确认 - 橘色（与产品类同色系）
        'product_confirmation': '#f97316',
    }

    # 工作类型标签（31个子类型，出差已改为独立勾选框）
    TYPE_LABELS = {
        # 通用
        'meeting': '会议',
        'internal_training': '内部培训',
        'other': '其他',
        # 行销
        'customer_visit': '拜访客户',
        'presales_support': '售前支持',
        'business_negotiation': '商务洽谈',
        'customer_maintenance': '客户维护',
        # 市场（旧类型保留数据兼容，新类型用于选择）
        'market_planning': '市场策划',      # [隐藏] 旧类型
        'brand_promotion': '品牌推广',      # [隐藏] 旧类型
        'event_execution': '活动执行',      # [隐藏] 旧类型
        'video_production': '视频制作',     # 新类型
        'material_design': '物料设计',      # 新类型
        'social_media_operation': '社媒运营',  # 新类型
        'channel_activity': '渠道活动',     # 新类型
        'brand_event': '品牌活动',          # 新类型
        # 服务
        'onsite_maintenance': '现场运维',
        'service_response': '服务响应',
        'technical_support': '技术支持',
        'troubleshooting': '故障处理',
        # 行政
        'admin_affairs': '行政事务',
        'office_management': '办公管理',
        'asset_management': '资产管理',
        # 人事
        'hr_affairs': '人事事务',
        'recruitment': '招聘面试',
        'employee_relations': '员工关系',
        'performance_management': '绩效管理',
        # 财务
        'finance_work': '财务工作',
        'expense_review': '报销审核',
        'accounting': '账务处理',
        # 产品
        'product_research': '产品调研',
        'requirement_analysis': '需求分析',
        'product_planning': '产品规划',
        # 供应链
        'procurement': '采购管理',
        'inventory_management': '库存管理',
        'logistics': '物流协调',
        'quality_tracking': '品质跟踪',
        # 待办任务
        'product_confirmation': '产品确认',
    }

    def to_calendar_event(self, current_user_id=None):
        """转换为 FullCalendar 事件格式

        Args:
            current_user_id: 当前用户ID，用于判断是否是所有者
        """
        is_owner = self.owner_id == current_user_id if current_user_id else True
        owner_name = self.owner.real_name or self.owner.username if self.owner else None

        event = {
            'id': self.id,
            'title': self.title,
            'start': self.planned_date.isoformat(),
            'allDay': self.is_all_day,
            'color': self.get_type_color(),
            'editable': is_owner,  # 只有所有者可以拖拽编辑
            'extendedProps': {
                'status': self.status,
                'work_type': self.work_type,
                'work_type_label': self.get_type_label(),
                'project_id': self.project_id,
                'project_name': self.project.project_name if self.project else None,
                'customer_id': self.customer_id,
                'customer_name': self.customer.company_name if self.customer else None,
                'estimated_hours': self.estimated_hours,
                'actual_hours': self.actual_hours,
                'execution_notes': self.execution_notes,
                'description': self.description,
                'end_date': self.end_date.isoformat() if self.end_date else None,
                'is_owner': is_owner,
                'owner_id': self.owner_id,
                'owner_name': owner_name,
                'shared_with_users': self.shared_with_users or [],
                'contact_id': self.contact_id,
                'contact_name': self.contact.name if self.contact else None,
                'is_invalidated': self.is_invalidated,
                'is_business_trip': self.is_business_trip
            }
        }

        # 处理跨天任务（全天事件）
        if self.end_date and self.is_all_day:
            # FullCalendar 全天事件的 end 是 exclusive，需要加一天
            event['end'] = (self.end_date + timedelta(days=1)).isoformat()
        # 添加时间信息（如果不是全天事件）
        elif not self.is_all_day and self.start_time:
            event['start'] = f"{self.planned_date.isoformat()}T{self.start_time.isoformat()}"
            if self.end_time:
                # 如果有结束日期，使用结束日期；否则使用开始日期
                end_date = self.end_date if self.end_date else self.planned_date
                event['end'] = f"{end_date.isoformat()}T{self.end_time.isoformat()}"

        # 事件样式类名
        class_names = []

        # 已完成/取消的事件添加特殊样式
        if self.status == 'completed':
            class_names.append('fc-event-completed')
            event['editable'] = False
        elif self.status == 'cancelled':
            class_names.append('fc-event-cancelled')
            event['editable'] = False

        # 共享给我的事件添加特殊样式
        if not is_owner:
            class_names.append('fc-event-shared')
            event['editable'] = False  # 共享事件不可编辑

        if class_names:
            event['classNames'] = class_names

        return event

    def get_type_color(self):
        """获取工作类型对应颜色"""
        return self.TYPE_COLORS.get(self.work_type, self.TYPE_COLORS['other'])

    def get_type_label(self):
        """获取工作类型标签"""
        return self.TYPE_LABELS.get(self.work_type, '其他')

    @property
    def attachments_list(self):
        """获取附件列表"""
        if not self.attachments:
            return []
        try:
            return json.loads(self.attachments)
        except (json.JSONDecodeError, TypeError):
            return []

    def add_attachment(self, filename, url, size, file_type):
        """添加附件"""
        attachments = self.attachments_list
        attachments.append({
            'filename': filename,
            'url': url,
            'size': size,
            'type': file_type,
            'uploaded_at': datetime.now().isoformat()
        })
        self.attachments = json.dumps(attachments)

    def remove_attachment(self, index):
        """移除指定索引的附件"""
        attachments = self.attachments_list
        if 0 <= index < len(attachments):
            attachments.pop(index)
            self.attachments = json.dumps(attachments) if attachments else None
            return True
        return False

    def get_attachment(self, index):
        """获取指定索引的附件"""
        attachments = self.attachments_list
        if 0 <= index < len(attachments):
            return attachments[index]
        return None

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'planned_date': self.planned_date.isoformat() if self.planned_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_all_day': self.is_all_day,
            'estimated_hours': self.estimated_hours,
            'project_id': self.project_id,
            'project_name': self.project.project_name if self.project else None,
            'customer_id': self.customer_id,
            'customer_name': self.customer.company_name if self.customer else None,
            'contact_id': self.contact_id,
            'contact_name': self.contact.name if self.contact else None,
            'work_type': self.work_type,
            'work_type_label': self.get_type_label(),
            'color': self.get_type_color(),
            'status': self.status,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'actual_hours': self.actual_hours,
            'execution_notes': self.execution_notes,
            'owner_id': self.owner_id,
            'owner_name': self.owner.real_name or self.owner.username if self.owner else None,
            'shared_with_users': self.shared_with_users or [],
            'is_invalidated': self.is_invalidated,
            'is_business_trip': self.is_business_trip,
            'attachments': self.attachments_list,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class WorkLog(db.Model):
    """工作日志模型"""
    __tablename__ = 'worklogs'

    id = Column(Integer, primary_key=True)

    # 日志日期
    log_date = Column(Date, nullable=False, index=True)  # 日志日期
    log_type = Column(String(20), default='daily')       # daily, weekly
    week_number = Column(Integer)                        # 周数（周报告用）
    year = Column(Integer)                               # 年份（周报告用）

    # 汇总内容（自动生成）
    summary = Column(Text)                               # 日志摘要
    total_hours = Column(Float, default=0.0)             # 总工时

    # 补充内容
    additional_notes = Column(Text)                      # 额外补充

    # 附件（JSON格式存储）
    attachments = Column(Text, nullable=True)            # JSON: [{filename, url, size, type}]

    # 状态
    status = Column(String(20), default='draft')         # draft, submitted
    submitted_at = Column(DateTime)

    # @ 和 # 引用功能
    mentioned_users = Column(JSON, default=list)         # 被 @ 的用户ID列表
    mentioned_projects = Column(JSON, default=list)      # 被 # 引用的项目ID列表

    # 匿名反馈计数（大拇指/小拇指）
    thumbs_up_count = Column(Integer, default=0)         # 大拇指（鼓励）数量
    thumbs_down_count = Column(Integer, default=0)       # 小拇指（否定）数量

    # 质量评分（持久化保存）
    quality_score = Column(Integer, nullable=True)       # 总分
    quality_issues = Column(JSON, nullable=True)         # 问题列表 ['desc_equals_action', 'bad_title']

    # 工作项关联
    work_items = relationship('WorkItem', back_populates='worklog')

    # 系统字段
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner = relationship('User', backref='worklogs')

    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)

    # 唯一约束：每人每天只有一条日志
    __table_args__ = (
        db.UniqueConstraint('owner_id', 'log_date', 'log_type', name='uq_worklog_owner_date_type'),
    )

    def calculate_statistics(self):
        """计算日志统计数据"""
        all_items = [i for i in self.work_items if not i.is_deleted]
        completed_items = [i for i in all_items if i.status == 'completed']
        pending_items = [i for i in all_items if i.status == 'planned']

        return {
            'total_items': len(all_items),
            'completed_items': len(completed_items),
            'pending_items': len(pending_items),
            'total_hours': self.calculate_smart_hours(),  # 使用智能工时计算
            'project_count': len(set(i.project_id for i in all_items if i.project_id)),
            'customer_count': len(set(i.customer_id for i in all_items if i.customer_id))
        }

    def calculate_smart_hours(self, extra_items=None):
        """
        智能计算工时：
        1. 排除跨天和全天事件
        2. 时间段去重（合并重叠）
        3. 扣除午休（12:00-13:00）
        4. 上限8小时

        参数：
        - extra_items: 额外的工作项列表（如共享工作项），会与 self.work_items 合并计算

        规则说明：
        - 排除条件：跨天工作项(end_date != planned_date)、全天事件(is_all_day=True)
        - 只计算有具体时间段(start_time, end_time)的已完成工作项
        - 午休时段：12:00-13:00（1小时）
        - 最大累计上限：8小时
        """
        # 合并工作项列表
        all_items = list(self.work_items) if self.work_items else []
        if extra_items:
            # 使用 id 去重，避免重复计算
            existing_ids = {i.id for i in all_items}
            for item in extra_items:
                if item.id not in existing_ids:
                    all_items.append(item)

        return self._calculate_hours_for_items(all_items)

    @staticmethod
    def _calculate_hours_for_items(work_items):
        """
        对工作项列表进行智能工时计算（静态方法，可复用）

        规则：
        1. 排除跨天和全天事件
        2. 时间段去重（合并重叠）
        3. 扣除午休（12:00-13:00）
        4. 上限8小时
        """
        # 时间常量
        LUNCH_START_MIN = 720   # 12:00 = 12*60
        LUNCH_END_MIN = 780     # 13:00 = 13*60
        MAX_HOURS = 8.0

        def time_to_minutes(t):
            """将 time 对象转换为从 00:00 开始的分钟数"""
            return t.hour * 60 + t.minute

        # 筛选有效工作项：非跨天、非全天、有时间段的已完成工作项
        valid_items = [
            i for i in work_items
            if i.status == 'completed'
            and not i.is_deleted
            and not i.is_all_day                                    # 排除全天事件
            and not (i.end_date and i.end_date != i.planned_date)   # 排除跨天
            and i.start_time and i.end_time                         # 必须有时间段
        ]

        if not valid_items:
            return 0.0

        # 提取所有时间段（转换为分钟数）
        intervals = []
        for item in valid_items:
            start_min = time_to_minutes(item.start_time)
            end_min = time_to_minutes(item.end_time)
            if end_min > start_min:  # 确保有效时间段
                intervals.append((start_min, end_min))

        if not intervals:
            return 0.0

        # 合并重叠时间段
        intervals.sort(key=lambda x: x[0])
        merged = []
        for start, end in intervals:
            if merged and start <= merged[-1][1]:
                # 有重叠或相邻，扩展结束时间
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))

        # 计算总时长（扣除午休重叠部分）
        def calculate_minutes_excluding_lunch(start, end):
            """计算时间段分钟数，扣除与午休(12:00-13:00)重叠的部分"""
            if end <= LUNCH_START_MIN or start >= LUNCH_END_MIN:
                # 不与午休重叠
                return end - start
            elif start >= LUNCH_START_MIN and end <= LUNCH_END_MIN:
                # 完全在午休内
                return 0
            elif start < LUNCH_START_MIN and end > LUNCH_END_MIN:
                # 跨越整个午休
                return (LUNCH_START_MIN - start) + (end - LUNCH_END_MIN)
            elif start < LUNCH_START_MIN:
                # 与午休前半段重叠（开始在午休前，结束在午休中）
                return LUNCH_START_MIN - start
            else:
                # 与午休后半段重叠（开始在午休中，结束在午休后）
                return end - LUNCH_END_MIN

        total_minutes = sum(
            calculate_minutes_excluding_lunch(start, end)
            for start, end in merged
        )

        hours = total_minutes / 60.0
        return round(min(hours, MAX_HOURS), 1)

    def to_dict(self, include_items=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'log_date': self.log_date.isoformat() if self.log_date else None,
            'log_type': self.log_type,
            'week_number': self.week_number,
            'year': self.year,
            'summary': self.summary,
            'total_hours': self.total_hours,
            'additional_notes': self.additional_notes,
            'attachments': self.attachments_list,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'mentioned_users': self.mentioned_users or [],
            'mentioned_projects': self.mentioned_projects or [],
            'owner_id': self.owner_id,
            'owner_name': self.owner.real_name or self.owner.username if self.owner else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'statistics': self.calculate_statistics()
        }

        if include_items:
            all_items = [i for i in self.work_items if not i.is_deleted]
            data['completed_items'] = [i.to_dict() for i in all_items if i.status == 'completed']
            data['pending_items'] = [i.to_dict() for i in all_items if i.status == 'planned']
            data['cancelled_items'] = [i.to_dict() for i in all_items if i.status == 'cancelled']

        return data

    @classmethod
    def get_or_create(cls, owner_id, log_date, log_type='daily'):
        """获取或创建日志"""
        worklog = cls.query.filter_by(
            owner_id=owner_id,
            log_date=log_date,
            log_type=log_type
        ).first()

        if not worklog:
            worklog = cls(
                owner_id=owner_id,
                log_date=log_date,
                log_type=log_type
            )
            db.session.add(worklog)
            db.session.flush()

        return worklog

    @property
    def attachments_list(self):
        """获取附件列表"""
        if not self.attachments:
            return []
        try:
            return json.loads(self.attachments)
        except (json.JSONDecodeError, TypeError):
            return []

    def add_attachment(self, filename, url, size, file_type):
        """添加附件"""
        attachments = self.attachments_list
        attachments.append({
            'filename': filename,
            'url': url,
            'size': size,
            'type': file_type,
            'uploaded_at': datetime.now().isoformat()
        })
        self.attachments = json.dumps(attachments)

    def remove_attachment(self, index):
        """移除指定索引的附件"""
        attachments = self.attachments_list
        if 0 <= index < len(attachments):
            attachments.pop(index)
            self.attachments = json.dumps(attachments) if attachments else None
            return True
        return False

    def get_attachment(self, index):
        """获取指定索引的附件"""
        attachments = self.attachments_list
        if 0 <= index < len(attachments):
            return attachments[index]
        return None

    # 评分等级配置（字典模式，与项目其他徽章一致）
    SCORE_LEVELS = {
        'excellent': {'min': 75, 'icon': 'sentiment_very_satisfied', 'class': 'tw-badge-green', 'label': '优秀'},
        'good': {'min': 55, 'icon': 'sentiment_satisfied', 'class': 'tw-badge-blue', 'label': '良好'},
        'fair': {'min': 35, 'icon': 'sentiment_neutral', 'class': 'tw-badge-amber', 'label': '继续努力'},
        'poor': {'min': 0, 'icon': 'sentiment_dissatisfied', 'class': 'tw-badge-gray', 'label': '需改进'}
    }

    # 改进建议配置（新版：加分制）
    IMPROVEMENT_SUGGESTIONS = {
        'few_items': {
            'issue': '工作项数量较少',
            'suggestion': '增加工作项数量，详细记录每项工作内容'
        },
        'no_completion': {
            'issue': '没有完成的工作项',
            'suggestion': '完成工作后及时更新状态为已完成'
        },
        'no_customer': {
            'issue': '工作项未关联客户',
            'suggestion': '关联相关客户，便于追踪和统计'
        },
        'no_project': {
            'issue': '工作项未关联项目',
            'suggestion': '关联相关项目，便于项目进度追踪'
        },
        'short_desc': {
            'issue': '工作描述过于简单',
            'suggestion': '详细描述工作内容、目的和预期成果'
        },
        'no_notes': {
            'issue': '缺少执行备注',
            'suggestion': '补充执行备注说明实际工作成果'
        },
        'single_type': {
            'issue': '工作类型单一',
            'suggestion': '尝试安排多样化的工作内容'
        },
        'no_system_activity': {
            'issue': '当天无系统操作记录',
            'suggestion': '在系统中及时录入客户、项目、跟进等信息'
        },
        'late_submit': {
            'issue': '日志提交不够及时',
            'suggestion': '尽量当天完成日志提交'
        }
    }

    def calculate_quality_score(self, actions=None, system_activities=None):
        """计算日志质量评分（加分制）

        参数:
            actions: 当天的跟进记录列表
            system_activities: 当天的系统操作统计 {'customers': n, 'contacts': n, 'projects': n, 'actions': n, 'quotations': n}

        返回: {
            'total': 总分,
            'level': 等级key,
            'icon': 图标名称,
            'badge_class': 徽章CSS类,
            'label': 等级标签,
            'breakdown': {
                'base': 基础分(10),
                'count': 工作项数量分(15),
                'quality': 工作项质量分(25),
                'diversity': 多样性分(15),
                'timeliness': 及时分(10),
                'activity': 系统行为分(15),
                'interaction': 互动加分
            },
            'issues': ['issue_key1', ...]
        }
        """
        score = {
            'base': 0,
            'count': 0,
            'quality': 0,
            'diversity': 0,
            'timeliness': 0,
            'activity': 0,
            'interaction': 0
        }
        issues = []

        # 获取工作项
        work_items = [i for i in self.work_items if not i.is_deleted and not i.is_invalidated]

        # === 基础分: 10分（提交即得）===
        score['base'] = 10

        # === 工作项数量: 满分15（每个+3，封顶5个）===
        item_count = len(work_items)
        score['count'] = min(item_count * 3, 15)
        if item_count < 2:
            issues.append('few_items')

        # === 工作项质量: 满分25 ===
        quality_score = 0
        has_completion = False
        has_customer = False
        has_project = False
        has_good_desc = False
        has_notes = False

        for item in work_items:
            # 完成+3
            if item.status == 'completed':
                quality_score += 3
                has_completion = True
            # 关联客户+2
            if item.customer_id:
                quality_score += 2
                has_customer = True
            # 关联项目+2
            if item.project_id:
                quality_score += 2
                has_project = True
            # 描述>30字+3
            if item.description and len(item.description) > 30:
                quality_score += 3
                has_good_desc = True
            # 有备注+2
            if item.execution_notes:
                quality_score += 2
                has_notes = True
            # 有工时+1
            if item.start_time and item.end_time:
                quality_score += 1

        score['quality'] = min(quality_score, 25)

        # 质量相关建议
        if item_count > 0:
            if not has_completion:
                issues.append('no_completion')
            if not has_customer:
                issues.append('no_customer')
            if not has_project:
                issues.append('no_project')
            if not has_good_desc:
                issues.append('short_desc')
            if not has_notes:
                issues.append('no_notes')

        # === 行程多样性: 满分15 ===
        work_types = set(item.work_type for item in work_items if item.work_type)
        type_count = len(work_types)
        if type_count >= 4:
            score['diversity'] = 15
        elif type_count == 3:
            score['diversity'] = 10
        elif type_count == 2:
            score['diversity'] = 5
        else:
            score['diversity'] = 0
            if item_count > 0:
                issues.append('single_type')

        # === 及时性: 满分10 ===
        if self.submitted_at and self.log_date:
            log_dt = datetime.combine(self.log_date, datetime.min.time())
            diff_days = (self.submitted_at - log_dt).days
            if diff_days <= 0:
                score['timeliness'] = 10  # 当天提交
            elif diff_days == 1:
                score['timeliness'] = 7   # 次日提交
            elif diff_days == 2:
                score['timeliness'] = 4   # 第三天提交
            else:
                score['timeliness'] = 1   # 更晚提交
                issues.append('late_submit')

        # === 系统行为: 满分15 ===
        activity_score = 0
        if system_activities:
            # 创建客户+3, 更新客户+1
            activity_score += system_activities.get('new_customers', 0) * 3
            activity_score += system_activities.get('updated_customers', 0) * 1
            # 创建联系人+2
            activity_score += system_activities.get('new_contacts', 0) * 2
            # 创建项目+3, 更新项目+1
            activity_score += system_activities.get('new_projects', 0) * 3
            activity_score += system_activities.get('updated_projects', 0) * 1
            # 创建跟进+2
            activity_score += system_activities.get('new_actions', 0) * 2
            # 创建报价+3
            activity_score += system_activities.get('new_quotations', 0) * 3

        score['activity'] = min(activity_score, 15)
        if activity_score == 0:
            issues.append('no_system_activity')

        # === 互动加分: 无上限 ===
        comments_count = len([c for c in self.comments if not c.is_deleted]) if self.comments else 0
        score['interaction'] = (self.thumbs_up_count or 0) * 3 + comments_count * 2

        # 计算总分（不含互动加分的基础满分是90）
        total = (score['base'] + score['count'] + score['quality'] +
                score['diversity'] + score['timeliness'] + score['activity'] +
                score['interaction'])

        # 确定等级
        level = 'poor'
        for level_key in ['excellent', 'good', 'fair', 'poor']:
            if total >= self.SCORE_LEVELS[level_key]['min']:
                level = level_key
                break

        level_config = self.SCORE_LEVELS[level]

        return {
            'total': total,
            'level': level,
            'icon': level_config['icon'],
            'badge_class': level_config['class'],
            'label': level_config['label'],
            'breakdown': score,
            'issues': issues
        }


class WorkLogComment(db.Model):
    """工作日志评论模型"""
    __tablename__ = 'worklog_comments'

    id = Column(Integer, primary_key=True)

    # 关联的日志
    worklog_id = Column(Integer, ForeignKey('worklogs.id'), nullable=False, index=True)
    worklog = relationship('WorkLog', backref='comments')

    # 评论内容
    content = Column(Text, nullable=False)

    # 评论者
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner = relationship('User', backref='worklog_comments')

    # 系统字段
    created_at = Column(DateTime, default=get_local_time, index=True)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = Column(Boolean, default=False)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'worklog_id': self.worklog_id,
            'content': self.content,
            'owner_id': self.owner_id,
            'owner_name': self.owner.real_name or self.owner.username if self.owner else None,
            'created_at': self.created_at.strftime('%Y-%m-%dT%H:%M:%SZ') if self.created_at else None,
            'can_delete': False  # 由 API 动态设置
        }


class WorkLogReaction(db.Model):
    """日志反馈记录（匿名点赞/点踩）

    记录用户对日志的反馈，用于：
    1. 判断当前用户是否已反馈及反馈类型
    2. 防止重复反馈

    注意：前端只显示计数，不显示谁点的（匿名）
    """
    __tablename__ = 'worklog_reactions'

    id = Column(Integer, primary_key=True)

    # 关联的日志（级联删除：删除日志时自动删除关联的反馈）
    worklog_id = Column(Integer, ForeignKey('worklogs.id', ondelete='CASCADE'), nullable=False, index=True)
    worklog = relationship('WorkLog', backref=db.backref('reactions', lazy='dynamic', cascade='all, delete-orphan', passive_deletes=True))

    # 反馈用户
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    user = relationship('User', backref='worklog_reactions')

    # 反馈类型：'up'（大拇指/鼓励）或 'down'（小拇指/否定）
    reaction_type = Column(String(10), nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=get_local_time)

    # 唯一约束：每个用户对每个日志只能有一条反馈记录
    __table_args__ = (
        db.UniqueConstraint('worklog_id', 'user_id', name='uq_worklog_user_reaction'),
    )
