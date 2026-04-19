# -*- coding: utf-8 -*-
"""积分行为注册表 — 系统所有可触发行为的唯一定义来源。

数据库（PointsBehaviorConfig）只存管理员可调的运行时配置（积分值/上限/开关）。
钩子的身份信息（名称、触发说明、分类、默认值）定义在此处。

新增行为步骤：
  1. 在 BEHAVIOR_REGISTRY 中添加一条记录
  2. 在对应视图/服务文件中调用 award_points(behavior_code=...)
  3. 应用启动时 sync_registry_to_db() 自动将缺失条目写入数据库
"""

BEHAVIOR_REGISTRY: dict[str, dict] = {
    # ── Wiki 知识库 ──────────────────────────────────────────────
    'wiki_create': {
        'name': '创建知识库文章',
        'category': 'knowledge',
        'trigger': '文章首次在知识库中创建时自动触发',
        'default_points': 5,
        'default_daily_cap': None,
    },
    'wiki_share': {
        'name': '公开分享知识',
        'category': 'knowledge',
        'trigger': '文章首次从私有变为公司/全局可见时触发',
        'default_points': 10,
        'default_daily_cap': None,
    },
    'wiki_cited': {
        'name': 'Wiki文章被引用',
        'category': 'knowledge',
        'trigger': '文章内容被其他Wiki页面引用时触发',
        'default_points': 5,
        'default_daily_cap': 50,
    },
    'wiki_cited_qa': {
        'name': '问答引用我的文章',
        'category': 'knowledge',
        'trigger': 'Wiki问答将文章作为答案来源引用时触发（过滤自引）',
        'default_points': 5,
        'default_daily_cap': 30,
    },
    'wiki_link_opened': {
        'name': '引用链接被点击',
        'category': 'knowledge',
        'trigger': '问答中引用链接被他人点击查看原文时触发（过滤作者本人）',
        'default_points': 5,
        'default_daily_cap': 20,
    },
    # ── 内容创作 ─────────────────────────────────────────────────
    'daily_log_submit': {
        'name': '提交工作日志',
        'category': 'content',
        'trigger': '每次提交工作日志时自动触发',
        'default_points': 10,
        'default_daily_cap': 10,
    },
    # ── 任务达成 ─────────────────────────────────────────────────
    'task_create': {
        'name': '创建任务',
        'category': 'task',
        'trigger': '新建任务时，创建人获得积分',
        'default_points': 5,
        'default_daily_cap': 15,
    },
    'subtask_complete': {
        'name': '完成任务节点',
        'category': 'task',
        'trigger': '子任务/节点状态变为已完成时，节点被指派人获得积分',
        'default_points': 15,
        'default_daily_cap': None,
    },
    'task_milestone_confirmed': {
        'name': '里程碑节点通过',
        'category': 'task',
        'trigger': '里程碑节点被确认人确认通过时，节点被指派人获得积分',
        'default_points': 20,
        'default_daily_cap': None,
    },
    'task_complete': {
        'name': '完成任务',
        'category': 'task',
        'trigger': '任务状态变为已完成时，被指派人获得积分',
        'default_points': 30,
        'default_daily_cap': None,
    },
    'task_review_approved': {
        'name': '任务审计通过',
        'category': 'approval',
        'trigger': '审计人确认通过任务时，审计人获得积分',
        'default_points': 5,
        'default_daily_cap': None,
    },
    # ── 业务推进 ─────────────────────────────────────────────────
    'project_create': {
        'name': '新建项目',
        'category': 'business',
        'trigger': '新建项目时自动触发',
        'default_points': 30,
        'default_daily_cap': None,
    },
    'project_stage_advance': {
        'name': '项目阶段推进',
        'category': 'business',
        'trigger': '项目阶段向前推进时，项目负责人获得积分',
        'default_points': 25,
        'default_daily_cap': None,
    },
    'customer_create': {
        'name': '发现新客户',
        'category': 'business',
        'trigger': '新建客户公司时自动触发',
        'default_points': 20,
        'default_daily_cap': None,
    },
    'project_approved': {
        'name': '项目审批通过',
        'category': 'business',
        'trigger': '项目审批流程全部通过时，项目负责人获得积分（含获得授权编号场景）',
        'default_points': 50,
        'default_daily_cap': None,
    },
    'project_approver_acted': {
        'name': '参与项目审批',
        'category': 'approval',
        'trigger': '审批人对某项目审批做出同意操作时触发，同一项目同一审批人只计一次',
        'default_points': 5,
        'default_daily_cap': None,
    },
    'pricing_order_approver_acted': {
        'name': '参与批价单审批',
        'category': 'approval',
        'trigger': '审批人对某批价单审批做出同意操作时触发，同一批价单同一审批人只计一次',
        'default_points': 5,
        'default_daily_cap': None,
    },
    'pricing_order_approved': {
        'name': '批价单审批通过',
        'category': 'business',
        'trigger': '批价单审批流程全部通过时，批价单创建人获得积分',
        'default_points': 40,
        'default_daily_cap': None,
    },
    'contact_create': {
        'name': '创建联系人',
        'category': 'business',
        'trigger': '在客户公司下新建联系人时自动触发',
        'default_points': 10,
        'default_daily_cap': 30,
    },
    'action_record_create': {
        'name': '创建跟进记录',
        'category': 'business',
        'trigger': '在项目或客户下创建行动跟进记录时触发，同一项目/客户同天只计一次',
        'default_points': 10,
        'default_daily_cap': 30,
    },
}
