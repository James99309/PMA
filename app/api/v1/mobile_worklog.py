# -*- coding: utf-8 -*-
"""移动端 工作日历/日志 — 读侧(C-BE2)

4 端点(读侧薄壳,业务逻辑全在 app/services/worklog_service,web/mobile 单一来源):
  GET /mobile/worklog/items?start=&end=&owner_id=   日历事件源 + meta
  GET /mobile/worklog/day?date=&owner_id=            某日日报(含质量评分,本地化)
  GET /mobile/worklog/month?ym=YYYY-MM&owner_id=     月热力(按类型聚合)
  GET /mobile/worklog/accounts                       可切换账户(本人/同事·本周项数)

i18n 纪律(见 CLAUDE-I18N.md 移动端纪律):数据值(31 工作类型 / 评分等级 /
改进建议)由后端按 Accept-Language 出 *_label,前端只消费,不自建中文 map。
颜色复用模型 WorkItem.TYPE_COLORS(单一来源,勿在前端硬编码)。
"""
from datetime import datetime, date, timedelta
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response, get_request_lang as _lang
from app.models.user import User
from app.models.worklog import WorkItem
from app.services import worklog_service as ws
import logging

logger = logging.getLogger(__name__)


# ─── 31 工作类型 zh/en(key 与 WorkItem.TYPE_LABELS 一致;含旧类型数据兼容) ───
_TYPE_I18N = {
    'meeting':                 {'zh': '会议',     'en': 'Meeting'},
    'internal_training':       {'zh': '内部培训', 'en': 'Internal Training'},
    'other':                   {'zh': '其他',     'en': 'Other'},
    'customer_visit':          {'zh': '拜访客户', 'en': 'Customer Visit'},
    'presales_support':        {'zh': '售前支持', 'en': 'Pre-sales Support'},
    'business_negotiation':    {'zh': '商务洽谈', 'en': 'Business Negotiation'},
    'customer_maintenance':    {'zh': '客户维护', 'en': 'Customer Maintenance'},
    'market_planning':         {'zh': '市场策划', 'en': 'Marketing Planning'},
    'brand_promotion':         {'zh': '品牌推广', 'en': 'Brand Promotion'},
    'event_execution':         {'zh': '活动执行', 'en': 'Event Execution'},
    'video_production':        {'zh': '视频制作', 'en': 'Video Production'},
    'material_design':         {'zh': '物料设计', 'en': 'Material Design'},
    'social_media_operation':  {'zh': '社媒运营', 'en': 'Social Media Operations'},
    'channel_activity':        {'zh': '渠道活动', 'en': 'Channel Activity'},
    'brand_event':             {'zh': '品牌活动', 'en': 'Brand Event'},
    'onsite_maintenance':      {'zh': '现场运维', 'en': 'On-site Maintenance'},
    'service_response':        {'zh': '服务响应', 'en': 'Service Response'},
    'technical_support':       {'zh': '技术支持', 'en': 'Technical Support'},
    'troubleshooting':         {'zh': '故障处理', 'en': 'Troubleshooting'},
    'admin_affairs':           {'zh': '行政事务', 'en': 'Administrative Affairs'},
    'office_management':       {'zh': '办公管理', 'en': 'Office Management'},
    'asset_management':        {'zh': '资产管理', 'en': 'Asset Management'},
    'hr_affairs':              {'zh': '人事事务', 'en': 'HR Affairs'},
    'recruitment':             {'zh': '招聘面试', 'en': 'Recruitment & Interview'},
    'employee_relations':      {'zh': '员工关系', 'en': 'Employee Relations'},
    'performance_management':  {'zh': '绩效管理', 'en': 'Performance Management'},
    'finance_work':            {'zh': '财务工作', 'en': 'Finance Work'},
    'expense_review':          {'zh': '报销审核', 'en': 'Expense Review'},
    'accounting':              {'zh': '账务处理', 'en': 'Accounting'},
    'product_research':        {'zh': '产品调研', 'en': 'Product Research'},
    'requirement_analysis':    {'zh': '需求分析', 'en': 'Requirement Analysis'},
    'product_planning':        {'zh': '产品规划', 'en': 'Product Planning'},
    'procurement':             {'zh': '采购管理', 'en': 'Procurement'},
    'inventory_management':    {'zh': '库存管理', 'en': 'Inventory Management'},
    'logistics':               {'zh': '物流协调', 'en': 'Logistics Coordination'},
    'quality_tracking':        {'zh': '品质跟踪', 'en': 'Quality Tracking'},
    'product_confirmation':    {'zh': '产品确认', 'en': 'Product Confirmation'},
    'task_work':               {'zh': '任务跟进', 'en': 'Task Follow-up'},
}

# 工作类型分组(忠实 app/views/worklog.py calendar() work_type_groups:9 组,
# 旧类型 market_planning/brand_promotion/event_execution 与系统类型
# product_confirmation/task_work 不入选择器,仅用于历史数据 label 兜底)
_TYPE_GROUPS = [
    {'key': 'common',       'zh': '通用',   'en': 'General',
     'types': ['meeting', 'internal_training', 'other']},
    {'key': 'sales',        'zh': '行销',   'en': 'Sales',
     'types': ['customer_visit', 'presales_support', 'business_negotiation', 'customer_maintenance']},
    {'key': 'marketing',    'zh': '市场',   'en': 'Marketing',
     'types': ['video_production', 'material_design', 'social_media_operation', 'channel_activity', 'brand_event']},
    {'key': 'service',      'zh': '服务',   'en': 'Service',
     'types': ['onsite_maintenance', 'service_response', 'technical_support', 'troubleshooting']},
    {'key': 'admin',        'zh': '行政',   'en': 'Administration',
     'types': ['admin_affairs', 'office_management', 'asset_management']},
    {'key': 'hr',           'zh': '人事',   'en': 'Human Resources',
     'types': ['hr_affairs', 'recruitment', 'employee_relations', 'performance_management']},
    {'key': 'finance',      'zh': '财务',   'en': 'Finance',
     'types': ['finance_work', 'expense_review', 'accounting']},
    {'key': 'product',      'zh': '产品',   'en': 'Product',
     'types': ['product_research', 'requirement_analysis', 'product_planning']},
    {'key': 'supply_chain', 'zh': '供应链', 'en': 'Supply Chain',
     'types': ['procurement', 'inventory_management', 'logistics', 'quality_tracking']},
]

# 质量评分等级 zh/en(zh 与模型 WorkLog.SCORE_LEVELS.label 一致)
_SCORE_LEVEL_I18N = {
    'excellent': {'zh': '优秀',     'en': 'Excellent'},
    'good':      {'zh': '良好',     'en': 'Good'},
    'fair':      {'zh': '继续努力', 'en': 'Keep It Up'},
    'poor':      {'zh': '需改进',   'en': 'Needs Improvement'},
}

# 改进建议 zh/en(key 与模型 WorkLog.IMPROVEMENT_SUGGESTIONS 一致)
_IMPROVEMENT_I18N = {
    'few_items': {
        'issue':      {'zh': '工作项数量较少', 'en': 'Too few work items'},
        'suggestion': {'zh': '增加工作项数量，详细记录每项工作内容',
                       'en': 'Add more work items and record each in detail'},
    },
    'no_completion': {
        'issue':      {'zh': '没有完成的工作项', 'en': 'No completed work items'},
        'suggestion': {'zh': '完成工作后及时更新状态为已完成',
                       'en': 'Mark items as completed promptly when done'},
    },
    'no_customer': {
        'issue':      {'zh': '工作项未关联客户', 'en': 'Work items not linked to customers'},
        'suggestion': {'zh': '关联相关客户，便于追踪和统计',
                       'en': 'Link related customers for tracking and analytics'},
    },
    'no_project': {
        'issue':      {'zh': '工作项未关联项目', 'en': 'Work items not linked to projects'},
        'suggestion': {'zh': '关联相关项目，便于项目进度追踪',
                       'en': 'Link related projects for progress tracking'},
    },
    'short_desc': {
        'issue':      {'zh': '工作描述过于简单', 'en': 'Work descriptions too brief'},
        'suggestion': {'zh': '详细描述工作内容、目的和预期成果',
                       'en': 'Describe the content, purpose and expected outcome in detail'},
    },
    'no_notes': {
        'issue':      {'zh': '缺少执行备注', 'en': 'Missing execution notes'},
        'suggestion': {'zh': '补充执行备注说明实际工作成果',
                       'en': 'Add execution notes describing the actual results'},
    },
    'single_type': {
        'issue':      {'zh': '工作类型单一', 'en': 'Work types lack variety'},
        'suggestion': {'zh': '尝试安排多样化的工作内容',
                       'en': 'Try arranging a more diverse range of work'},
    },
    'no_system_activity': {
        'issue':      {'zh': '当天无系统操作记录', 'en': 'No system activity that day'},
        'suggestion': {'zh': '在系统中及时录入客户、项目、跟进等信息',
                       'en': 'Enter customers, projects and follow-ups in the system promptly'},
    },
    'late_submit': {
        'issue':      {'zh': '日志提交不够及时', 'en': 'Log submitted late'},
        'suggestion': {'zh': '尽量当天完成日志提交',
                       'en': 'Submit the daily log on the same day when possible'},
    },
}


def _type_label(key, lang):
    m = _TYPE_I18N.get(key)
    if not m:
        # 未知/历史 key 兜底:模型中文 label,再不行返回 key
        return WorkItem.TYPE_LABELS.get(key, _TYPE_I18N['other']['zh' if lang != 'en' else 'en'])
    return m.get(lang, m['zh'])


def _type_color(key):
    return WorkItem.TYPE_COLORS.get(key, WorkItem.TYPE_COLORS['other'])


def _meta(lang):
    """31 类型分组 + 评分等级 + 改进建议目录(按 lang 出 label,前端缓存复用)"""
    from app.models.worklog import WorkLog
    groups = []
    for g in _TYPE_GROUPS:
        groups.append({
            'key': g['key'],
            'label': g['en'] if lang == 'en' else g['zh'],
            'options': [
                {'value': t, 'label': _type_label(t, lang), 'color': _type_color(t)}
                for t in g['types']
            ],
        })
    score_levels = []
    for k, cfg in WorkLog.SCORE_LEVELS.items():
        i = _SCORE_LEVEL_I18N.get(k, {})
        score_levels.append({
            'key': k,
            'label': i.get(lang, i.get('zh', cfg.get('label'))),
            'min': cfg.get('min'),
            'icon': cfg.get('icon'),
            'badge_class': cfg.get('class'),
        })
    improvements = {
        k: {
            'issue': v['issue'].get(lang, v['issue']['zh']),
            'suggestion': v['suggestion'].get(lang, v['suggestion']['zh']),
        }
        for k, v in _IMPROVEMENT_I18N.items()
    }
    return {'type_groups': groups, 'score_levels': score_levels, 'improvements': improvements}


def _localize_quality(qs, lang):
    """就地本地化 get_day 返回的 quality_score(等级 label / 建议目录 / issues 明细)"""
    if not qs:
        return
    lvl = qs.get('level')
    li = _SCORE_LEVEL_I18N.get(lvl)
    if li:
        qs['label'] = li.get(lang, li['zh'])
    # suggestions: 模型给的是中文目录,换成本地化目录
    qs['suggestions'] = {
        k: {
            'issue': v['issue'].get(lang, v['issue']['zh']),
            'suggestion': v['suggestion'].get(lang, v['suggestion']['zh']),
        }
        for k, v in _IMPROVEMENT_I18N.items()
    }
    # issues 明细列表(设计:改进建议列表),按命中的 issue key 展开
    issues_detail = []
    for ik in (qs.get('issues') or []):
        v = _IMPROVEMENT_I18N.get(ik)
        if v:
            issues_detail.append({
                'key': ik,
                'issue': v['issue'].get(lang, v['issue']['zh']),
                'suggestion': v['suggestion'].get(lang, v['suggestion']['zh']),
            })
    qs['issues_detail'] = issues_detail


def _initials(name):
    if not name:
        return '?'
    name = name.strip()
    if name[0].isascii() and name[0].isalpha():
        parts = [p for p in name.split() if p]
        return ((parts[0][0] + (parts[1][0] if len(parts) > 1 else '')) or '?').upper()
    return name[-1]


def _week_bounds(today=None):
    """本周一 ~ 本周日(本地日期)"""
    today = today or date.today()
    monday = today - timedelta(days=today.weekday())
    return monday, monday + timedelta(days=6)


def _week_item_count(owner_id, monday, sunday):
    return WorkItem.query.filter(
        WorkItem.owner_id == owner_id,
        WorkItem.is_deleted == False,  # noqa: E712
        WorkItem.planned_date >= monday,
        WorkItem.planned_date <= sunday,
    ).count()


# ─── 端点 ────────────────────────────────────────────────────────────

@api_v1_bp.route('/mobile/worklog/items', methods=['GET'])
@jwt_required()
def mobile_worklog_items():
    """日历事件源(自己/共享 或 owner_id 他人)+ meta(类型分组/评分/建议)"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    start_date, end_date = ws.parse_calendar_range(
        request.args.get('start'), request.args.get('end')
    )
    owner_id = request.args.get('owner_id', type=int)
    try:
        result = ws.get_viewable_items(user, start_date, end_date, owner_id)
    except ws.WorklogUserNotFound:
        return api_response(success=False, code=404, message='用户不存在')
    except ws.WorklogPermissionDenied:
        return api_response(success=False, code=403, message='无权查看该用户日历')

    lang = _lang()
    for ev in result.get('events', []):
        ep = ev.get('extendedProps') or {}
        ep['work_type_label'] = _type_label(ep.get('work_type'), lang)
    result['meta'] = _meta(lang)
    return api_response(success=True, message='获取成功', data=result)


@api_v1_bp.route('/mobile/worklog/day', methods=['GET'])
@jwt_required()
def mobile_worklog_day():
    """某日日报:工作项分类 + 智能工时 + 行动记录 + 质量评分(已本地化)"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    date_str = (request.args.get('date') or '').strip()
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return api_response(success=False, code=400, message='日期格式无效')

    owner_id = request.args.get('owner_id', type=int)
    data = ws.get_day(user, target_date, owner_id)

    lang = _lang()
    for key in ('completed_items', 'pending_items', 'cancelled_items'):
        for d in data.get(key, []) or []:
            d['work_type_label'] = _type_label(d.get('work_type'), lang)
    _localize_quality(data.get('quality_score'), lang)
    data['meta'] = _meta(lang)
    return api_response(success=True, message='获取成功', data=data)


@api_v1_bp.route('/mobile/worklog/month', methods=['GET'])
@jwt_required()
def mobile_worklog_month():
    """月视图热力:按日期聚合 类型分布(色点)+ 项数 + 日志状态点"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    ym = (request.args.get('ym') or '').strip()
    try:
        first = datetime.strptime(ym, '%Y-%m').date().replace(day=1)
    except ValueError:
        first = date.today().replace(day=1)
    nxt = (first.replace(day=28) + timedelta(days=4)).replace(day=1)  # 下月 1 号

    owner_id = request.args.get('owner_id', type=int)
    try:
        # 轻量聚合源(只取 planned_date+work_type,不构建全事件/不触关系 N+1)
        result = ws.get_month_overview(user, first, nxt, owner_id)
    except ws.WorklogUserNotFound:
        return api_response(success=False, code=404, message='用户不存在')
    except ws.WorklogPermissionDenied:
        return api_response(success=False, code=403, message='无权查看该用户日历')

    lang = _lang()
    days = {}
    for d, wt in result.get('items', []):
        if not d:
            continue
        wt = wt or 'other'
        slot = days.setdefault(d, {'count': 0, 'types': {}})
        slot['count'] += 1
        t = slot['types'].setdefault(wt, {'type': wt, 'color': _type_color(wt),
                                          'label': _type_label(wt, lang), 'count': 0})
        t['count'] += 1
    days_out = {
        d: {'count': v['count'], 'types': list(v['types'].values())}
        for d, v in days.items()
    }

    used_types = sorted({wt for v in days.values() for wt in v['types']})
    legend = [{'type': t, 'color': _type_color(t), 'label': _type_label(t, lang)}
              for t in used_types]

    return api_response(success=True, message='获取成功', data={
        'ym': first.strftime('%Y-%m'),
        'days': days_out,
        'legend': legend,
        'datesWithSubmittedLogs': result.get('datesWithSubmittedLogs', []),
        'datesWithUnreadLogs': result.get('datesWithUnreadLogs', []),
        'datesWithReadLogs': result.get('datesWithReadLogs', []),
        'datesWithItems': result.get('datesWithItems', []),
    })


@api_v1_bp.route('/mobile/worklog/accounts', methods=['GET'])
@jwt_required()
def mobile_worklog_accounts():
    """可切换日历账户:本人 + 归属下属 + 其他可见账户,各含本周项数"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    viewable = ws.list_viewable_account_ids(user)
    sub_ids = set(ws.get_subordinate_user_ids(user)) & viewable
    us = {u.id: u for u in User.query.filter(User.id.in_(list(viewable))).all()}
    monday, sunday = _week_bounds()

    def _ent(u):
        nm = u.real_name or u.username
        return {
            'id': u.id,
            'name': nm,
            'short': _initials(nm),
            'department': u.department or '',
            'week_count': _week_item_count(u.id, monday, sunday),
        }

    me = _ent(user)
    me['is_self'] = True
    subs = [_ent(us[i]) for i in sub_ids if i in us and i != uid]
    other_ids = [i for i in viewable if i != uid and i not in sub_ids]
    others = [_ent(us[i]) for i in other_ids if i in us]
    subs.sort(key=lambda e: (-e['week_count'], e['name']))
    others.sort(key=lambda e: (-e['week_count'], e['name']))

    return api_response(success=True, message='获取成功', data={
        'self': me,
        'subordinates': subs,
        'others': others,
        'week_range': {'start': monday.isoformat(), 'end': sunday.isoformat()},
    })
