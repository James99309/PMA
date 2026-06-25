# -*- coding: utf-8 -*-
"""任务类型注册表(2026-06-14)

任务类型分两组:
- daily(日常):所有人可选(general)
- position(岗位):按角色过滤,完成/审核后自动进对应绩效指标

新增岗位任务类型只需往 TASK_TYPES 加一行(code/label/组/适用角色/是否需审核)。
KPI 计数见 app/services/kpi_actual_service.py 的 _act_hr_* / 各角色计数函数(全系统唯一采集源)。
"""

# allow_link: 是否显示「关联项目/报价单」(业务类任务才需要;HR 内部事务不需要)
TASK_TYPES = [
    # 日常(所有人) —— 暂不关联项目/报价单,留待后续业务类任务
    {'code': 'general', 'label': '日常任务', 'group': 'daily', 'group_label': '日常', 'roles': None, 'require_review': False, 'allow_link': False},
    # 岗位 · 人事经理(HRBP) —— 纯内部事务,不关联项目/报价单
    {'code': 'hr_recruit',    'label': '招聘到岗',     'group': 'position', 'group_label': '人事', 'roles': ['hr_manager'], 'require_review': True,  'allow_link': False},
    {'code': 'hr_training',   'label': '培训组织',     'group': 'position', 'group_label': '人事', 'roles': ['hr_manager'], 'require_review': False, 'allow_link': False},
    {'code': 'hr_team_build', 'label': '团队建设',     'group': 'position', 'group_label': '人事', 'roles': ['hr_manager'], 'require_review': False, 'allow_link': False},
    {'code': 'hr_admin',      'label': '行政/合规事务', 'group': 'position', 'group_label': '人事', 'roles': ['hr_manager'], 'require_review': False, 'allow_link': False},
    # 岗位 · 解决方案经理
    #   技术培训:完成计数进绩效 se_training_count(纯内部,不关联项目)
    #   项目支持:关联项目/报价单可见(allow_link),SE 配合销售的项目侧任务
    {'code': 'se_tech_training',    'label': '技术培训', 'group': 'position', 'group_label': '方案', 'roles': ['solution_manager'], 'require_review': True, 'allow_link': False},
    {'code': 'se_project_support', 'label': '项目支持', 'group': 'position', 'group_label': '方案', 'roles': ['solution_manager'], 'require_review': False, 'allow_link': True},
    # 岗位 · 产品经理 —— 研发/质量需审核通过才计入绩效,上市支持完成即计
    {'code': 'pm_rd',             'label': '研发任务', 'group': 'position', 'group_label': '产品', 'roles': ['product_manager'], 'require_review': True,  'allow_link': False},
    {'code': 'pm_quality',        'label': '质量任务', 'group': 'position', 'group_label': '产品', 'roles': ['product_manager'], 'require_review': True,  'allow_link': False},
    {'code': 'pm_launch_support', 'label': '上市支持', 'group': 'position', 'group_label': '产品', 'roles': ['product_manager'], 'require_review': True, 'allow_link': False},
]

_BY_CODE = {t['code']: t for t in TASK_TYPES}


# 可见全部岗位类型的超级角色(替各岗位建任务/管理)
_SUPER_ROLES = {'admin', 'ceo'}


def task_types_for(user):
    """用户可选的任务类型:日常(所有人) + 本岗位(角色匹配)。
    admin/ceo 可见全部岗位类型(替各岗位建任务)。"""
    role = getattr(user, 'role', None)
    is_super = role in _SUPER_ROLES
    out = []
    for t in TASK_TYPES:
        if t['group'] == 'daily':
            out.append(t)
        elif is_super or (t.get('roles') and role in t['roles']):
            out.append(t)
    return out


def is_allowed_type(user, code):
    """该用户是否可创建此类型任务(防越权选别岗位类型)。"""
    if not code or code == 'general':
        return True
    return any(t['code'] == code for t in task_types_for(user))


def task_type_label(code):
    t = _BY_CODE.get(code)
    return t['label'] if t else (code or '日常任务')


def task_type_groups_for(user):
    """按 group_label 聚合用户可选类型,供分组下拉组件使用。
    返回 [{key, label, options:[{value,label}]}],保持 TASK_TYPES 原顺序。"""
    groups = []
    index = {}
    for t in task_types_for(user):
        glabel = t.get('group_label') or t['group']
        if glabel not in index:
            g = {'key': t['group'] + ':' + glabel, 'label': glabel, 'options': []}
            index[glabel] = g
            groups.append(g)
        index[glabel]['options'].append({'value': t['code'], 'label': t['label']})
    return groups


def task_type_labels_for(user):
    """{code: label} 映射(仅含用户可选类型),供下拉组件按钮回显。"""
    return {t['code']: t['label'] for t in task_types_for(user)}


def requires_review(code):
    t = _BY_CODE.get(code)
    return bool(t and t.get('require_review'))
