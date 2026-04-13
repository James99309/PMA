# -*- coding: utf-8 -*-
"""CLI Agent 表分级目录(Tier 1 / Tier 2 / Tier 3)

设计原则:
- Tier 1: 核心业务表,字段通过 SQLAlchemy 反射生成,塞入 system prompt
- Tier 2: 按需表,仅在 system prompt 中给出 "表名 → 一句话用途",
          LLM 需要字段时调 describe_table 工具拉取
- Tier 3: 完全屏蔽,不出现在 prompt 中;describe_table 对其返回拒绝

权限层仍然由 cli_table_modules + check_table_access 统一管理。
本目录仅决定"什么信息给 LLM"。
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import inspect

logger = logging.getLogger(__name__)


# ───────────────────────────────────────────────────────────────────
# Tier 1: 核心业务表(20 张)
# 塞入 system prompt 的完整字段列表,中文描述 + 表用途
# ───────────────────────────────────────────────────────────────────

TIER1_TABLES: dict[str, str] = {
    'users': '用户/员工名册',
    'departments': '部门',
    'companies': '客户/供应商公司(根据 company_type 区分)',
    'contacts': '联系人(归属公司)',
    'projects': '销售项目',
    'project_customer_associations': '项目↔客户多对多关联(JOIN 必需)',
    'quotations': '报价单',
    'quotation_details': '报价明细行',
    'products': '产品库',
    'product_categories': '产品大类',
    'product_region_prices': '产品多地区面价',
    'sales_orders': '销售订单(客户下单)',
    'sales_order_details': '销售订单明细',
    'purchase_orders': '采购订单(向供应商)',
    'purchase_order_details': '采购订单明细',
    'pricing_orders': '批价单',
    'pricing_order_details': '批价单明细',
    'settlement_orders': '结算单',
    'expenses': '报销单',
}


# 敏感字段:反射生成时自动剔除
_HIDDEN_COLUMNS: dict[str, set[str]] = {
    'users': {'password_hash', 'wechat_openid', 'wechat_nickname', 'wechat_avatar'},
}


# ───────────────────────────────────────────────────────────────────
# Tier 2: 按需表(~132 张)
# 仅表名 + 一句话用途塞入 prompt;字段靠 describe_table 拉取
# ───────────────────────────────────────────────────────────────────

TIER2_CATALOG: dict[str, str] = {
    # 项目 / 评分 / 阶段
    'project_members': '项目成员',
    'project_stage_history': '项目阶段变更历史',
    'project_rating_records': '项目评级记录',
    'project_scoring_records': '项目评分记录',
    'project_scoring_config': '项目评分配置',
    'project_total_scores': '项目总分',
    'five_star_project_baselines': '五星项目基线',
    'stage_attachments': '阶段附件',
    'stage_dependencies': '阶段依赖',
    'stage_reviews': '阶段评审',

    # 产品 / 规格
    'product_subcategories': '产品子类',
    'product_regions': '产品地区',
    'product_names': '产品名称字典',
    'product_codes': '产品编码',
    'product_code_fields': '产品编码字段定义',
    'product_code_field_options': '产品编码字段选项',
    'product_code_field_values': '产品编码字段值',
    'product_config_values': '产品配置值',
    'product_configurations': '产品配置',
    'product_relations': '产品关联关系',
    'product_serial_numbers': '产品序列号',
    'product_specs': '产品规格',
    'product_tests': '产品测试',
    'product_test_details': '产品测试明细',
    'product_test_samplings': '产品测试抽样',
    'dev_products': '研发产品',
    'dev_product_specs': '研发产品规格',
    'dev_product_milestones': '研发产品里程碑',
    'specification_dictionary': '规格字典',
    'specification_options': '规格选项',
    'spec_definitions': '规格定义',
    'spec_categories': '规格分类',
    'spec_templates': '规格模板',
    'spec_template_items': '规格模板项',
    'spec_attachments': '规格附件',
    'test_method_dictionary': '测试方法字典',
    'test_condition_dictionary': '测试条件字典',

    # 订单链路
    'purchase_order_shipments': '采购订单发货',
    'purchase_order_shipment_details': '采购发货明细',
    'purchase_order_delivery_changes': '采购交期变更',
    'purchase_order_pricing_orders': '采购↔批价关联',
    'purchase_order_stage_history': '采购订单阶段历史',
    'shipments': '发货单',
    'shipment_details': '发货明细',
    'pricing_order_approval_records': '批价单审批记录',
    'settlement_order_details': '结算单明细',
    'settlement_details': '结算明细',
    'settlements': '结算流水',

    # 库存
    'inventory': '库存',
    'inventory_transactions': '库存流水',

    # 报价扩展
    'quotation_confirmation_tasks': '报价确认任务',

    # 报销
    'expense_details': '报销明细',
    'expense_budgets': '报销预算',
    'role_expense_budgets': '角色报销预算',

    # 绩效 / 薪酬
    'performance_statistics': '绩效统计',
    'performance_targets': '绩效目标',
    'performance_metrics_definition': '绩效指标定义',
    'performance_formula_templates': '绩效公式模板',
    'performance_manual_attachments': '绩效手册附件',
    'performance_manual_entries': '绩效手册条目',
    'role_performance_access': '角色绩效访问范围',
    'role_performance_config': '角色绩效配置',
    'role_performance_items': '角色绩效项',
    'role_performance_targets': '角色绩效目标',
    'user_performance_targets': '用户绩效目标',
    'quarterly_performance_data': '季度绩效数据',
    'salary_base_params': '薪酬基础参数',
    'salary_calculation_result': '薪酬计算结果',
    'salary_formula_config': '薪酬公式配置',
    'salary_grade_bandwidth': '薪酬等级带宽',
    'salary_grade_config': '薪酬等级配置',
    'salary_period_snapshots': '薪酬周期快照',
    'salary_step_rules': '薪酬步进规则',
    'employee_salary_config': '员工薪酬配置',
    'formula_templates_extended': '扩展公式模板',

    # 权限 / 归属
    'role_permissions': '角色权限',
    'role_feature_permissions': '角色功能权限',
    'permissions': '用户权限',
    'permission_modules': '权限模块',
    'permission_module_features': '权限模块功能点',
    'affiliations': '数据归属(上下级)',
    'data_affiliation': '数据归属配置',
    'access_requests': '权限申请',

    # 审批
    'approval_instance': '审批实例',
    'approval_record': '审批记录',
    'approval_process_template': '审批流程模板',
    'approval_step': '审批节点',
    'approval_branch_condition': '审批分支条件',

    # 任务 / 工作项 / 日志
    'tasks': '任务',
    'task_replies': '任务回复',
    'task_attachments': '任务附件',
    'work_items': '工作项(行动记录)',
    'actions': '客户跟进记录',
    'action_reply': '跟进回复',
    'worklogs': '工作日志',
    'worklog_comments': '工作日志评论',
    'worklog_reactions': '工作日志点赞',

    # 知识库
    'knowledge_documents': '知识库文档',
    'knowledge_wiki_articles': '知识库 Wiki 文章',
    'knowledge_document_tags': '文档标签关联',
    'knowledge_tags': '知识标签',
    'knowledge_topics': '知识主题',
    'knowledge_raw_files': '知识库原始文件',
    'knowledge_promotion_requests': '知识晋升申请',
    'knowledge_share_grants': '知识共享授权',
    'user_folders': '用户文件夹',

    # 会议
    'meeting_minutes': '会议纪要',
    'meeting_recordings': '会议录音',
    'meeting_transcripts': '会议转录',
    'meeting_action_items': '会议行动项',
    'meeting_speakers': '会议发言人',

    # 公告 / 消息
    'announcements': '公告',
    'announcement_attachments': '公告附件',
    'messages': '消息',

    # 调研 / 问卷
    'survey_questions': '问卷题目',
    'survey_responses': '问卷答复',
    'survey_templates': '问卷模板',

    # 其他业务
    'sales_team_config': '销售团队配置',
    'system_diagrams': '系统图',
    'company_assets': '公司资产',
    'user_points_ledger': '用户积分流水',
    'monthly_activity_snapshots': '月度活跃度快照',
    'user_daily_login_records': '用户日登录记录',
    'file_library': '文件库',
    'serial_number_histories': '序列号变更历史',

    # 系统配置(管理员偶尔查)
    'system_settings': '系统设置',
    'dictionaries': '数据字典',
    'cli_table_modules': 'CLI 表归属注册',
}


# ───────────────────────────────────────────────────────────────────
# Tier 3: 完全屏蔽(不出现在 prompt,describe_table 也拒绝)
# ───────────────────────────────────────────────────────────────────

TIER3_BLOCKED: set[str] = {
    # DB 迁移 / 版本元数据
    'alembic_version',
    'version_records',
    'upgrade_logs',
    'change_logs',
    'feature_changes',
    # 运维监控
    'system_metrics',
    # AI 缓存
    'ai_analysis_cache',
    # Agent 自己的会话(避免递归查询混淆)
    'chat_conversations',
    'chat_messages',
    'chat_participants',
    'chat_translations',
    # Agent 内部状态
    'cli_memories',
    'cli_sessions',
    'cli_skills',
    'user_cli_state',
    # 字段/表元数据(Agent 走 describe_table,不查这两张表)
    'data_field_config',
    'data_table_config',
    # 事件框架
    'event_registry',
    'user_event_subscriptions',
    # 已读状态(冗余)
    'worklog_reads',
    'announcement_reads',
    # 外部 token / 凭证
    'approval_external_tokens',
    'diagram_external_sessions',
    'diagram_share_tokens',
    # 向量检索内部
    'knowledge_chunks',
    'knowledge_config',
    # 邮箱凭证
    'solution_manager_email_settings',
    # 备份 / 临时表
    'pricing_order_approval_records_backup',
    'temp_products',
    # 文件引用内部
    'user_file_refs',
}


# ───────────────────────────────────────────────────────────────────
# 业务标注(提示 LLM 金额/枚举语义)
# ───────────────────────────────────────────────────────────────────

_BUSINESS_NOTES = """\
业务标注:
- 金额字段单位为元: quotations.amount, quotation_details.unit_price/total_price,
  expenses.total_amount, pricing_orders.pricing_total_amount,
  sales_orders.total_amount, purchase_orders.total_amount,
  product_region_prices.price
- projects.quotation_customer 是"报价客户名称"(字符串),不是金额
- 枚举字段展示时用 Schema 末尾的中文标签
- 软删除表(companies/projects/expenses 等)查询必须加 is_deleted = false\
"""


_TABLE_RELATIONS = """\
表关系:
- 项目↔客户: project_customer_associations(project_id, company_id) 多对多
- 联系人→公司: contacts.company_id
- 报价→项目/客户: quotations.project_id / quotations.customer_id
- 报价明细→报价: quotation_details.quotation_id
- 报销→项目/客户: expenses.project_id / expenses.customer_id
- 批价单→项目: pricing_orders.project_id
- 批价明细→批价单: pricing_order_details.pricing_order_id
- 销售订单→批价单/项目: sales_orders.pricing_order_id / sales_orders.project_id
- 销售订单明细→销售订单: sales_order_details.sales_order_id
- 采购订单→供应商(公司)/项目: purchase_orders.company_id / purchase_orders.project_id
- 采购明细→采购订单: purchase_order_details.purchase_order_id
- 产品地区面价→产品: product_region_prices.product_id
- 用户→部门: users.department_id\
"""


_QUERY_EXAMPLES = """\
常见查询模板:
- 查某公司关联的项目: SELECT p.project_name, p.current_stage FROM projects p
    JOIN project_customer_associations pca ON pca.project_id=p.id
    JOIN companies c ON pca.company_id=c.id
    WHERE c.company_name ILIKE '%关键词%' AND p.is_deleted=false
- 查某项目的报价: SELECT q.quotation_number, q.amount, q.currency FROM quotations q
    JOIN projects p ON q.project_id=p.id WHERE p.project_name ILIKE '%关键词%'
- 查某公司的联系人: SELECT name, position, phone FROM contacts
    WHERE company_id=(SELECT id FROM companies WHERE company_name ILIKE '%关键词%' LIMIT 1)\
"""


# ───────────────────────────────────────────────────────────────────
# SQLAlchemy 反射: 读 Tier 1 表的真实字段
# ───────────────────────────────────────────────────────────────────

def _reflect_columns(table_name: str) -> list[str]:
    """用 SQLAlchemy inspect 读取真实列名,剔除敏感字段。

    任何异常静默,返回空列表(调用方降级处理)。
    """
    try:
        from app import db
        insp = inspect(db.engine)
        cols = [c['name'] for c in insp.get_columns(table_name)]
    except Exception as e:
        logger.warning(f'[table_catalog] 反射 {table_name} 失败: {e}')
        return []

    hidden = _HIDDEN_COLUMNS.get(table_name, set())
    return [c for c in cols if c not in hidden]


def _reflect_columns_with_types(table_name: str) -> list[dict]:
    """反射列名 + 类型 + 是否 pk / fk / nullable,供 describe_table 工具使用。"""
    try:
        from app import db
        insp = inspect(db.engine)
        raw_cols = insp.get_columns(table_name)
        pks = set(insp.get_pk_constraint(table_name).get('constrained_columns', []))
        fks = {}
        for fk in insp.get_foreign_keys(table_name):
            for col in fk.get('constrained_columns') or []:
                ref_tbl = fk.get('referred_table')
                ref_cols = fk.get('referred_columns') or []
                ref_col = ref_cols[0] if ref_cols else 'id'
                fks[col] = f'{ref_tbl}.{ref_col}'
    except Exception as e:
        logger.warning(f'[table_catalog] 反射 {table_name} 详细列失败: {e}')
        return []

    hidden = _HIDDEN_COLUMNS.get(table_name, set())
    result = []
    for c in raw_cols:
        if c['name'] in hidden:
            continue
        entry = {
            'name': c['name'],
            'type': str(c['type']),
            'nullable': bool(c.get('nullable', True)),
        }
        if c['name'] in pks:
            entry['pk'] = True
        if c['name'] in fks:
            entry['fk'] = fks[c['name']]
        result.append(entry)
    return result


# ───────────────────────────────────────────────────────────────────
# 构建 prompt schema 段(分级版)
# ───────────────────────────────────────────────────────────────────

_schema_cache: str | None = None
_schema_cache_ts: float = 0.0
_SCHEMA_CACHE_TTL = 3600  # 1 小时


def build_tiered_schema_section() -> str:
    """生成 system prompt 中的 DB schema 段(分级版)。

    - Tier 1 给完整字段列表
    - Tier 2 给"表名 → 描述"清单,提示用 describe_table
    - 末尾带表关系 / 业务标注 / 查询模板 / 枚举标签
    """
    global _schema_cache, _schema_cache_ts
    import time
    now = time.time()
    if _schema_cache and (now - _schema_cache_ts) < _SCHEMA_CACHE_TTL:
        return _schema_cache

    lines: list[str] = []

    # Tier 1
    lines.append('【Tier 1 核心业务表(字段已完整列出)】')
    for table, desc in TIER1_TABLES.items():
        cols = _reflect_columns(table)
        if not cols:
            # 反射失败,跳过该表(不留假字段列)
            lines.append(f'{table}({desc}): [字段反射失败,请调 describe_table 查询]')
            continue
        fields = ', '.join(cols)
        lines.append(f'{table}({desc}): {fields}')

    # Tier 2
    lines.append('')
    lines.append('【Tier 2 按需查询表(字段未列出,需要时调 describe_table 工具)】')
    for table, desc in TIER2_CATALOG.items():
        lines.append(f'- {table}: {desc}')

    lines.append('')
    lines.append(_TABLE_RELATIONS)
    lines.append('')
    lines.append(_BUSINESS_NOTES)
    lines.append('')
    lines.append(_QUERY_EXAMPLES)

    # 枚举标签段(复用旧实现)
    try:
        from app.services.chat_db_query import _build_enum_labels_section
        enum_section = _build_enum_labels_section()
        if enum_section:
            lines.append('')
            lines.append(enum_section)
    except Exception:
        pass

    _schema_cache = '\n'.join(lines)
    _schema_cache_ts = now
    return _schema_cache


def invalidate_schema_cache():
    """用于测试或 schema 变更后强制刷新"""
    global _schema_cache, _schema_cache_ts
    _schema_cache = None
    _schema_cache_ts = 0.0


# ───────────────────────────────────────────────────────────────────
# describe_table 工具支撑: 判定可见性
# ───────────────────────────────────────────────────────────────────

def is_table_visible(table_name: str) -> bool:
    """表是否出现在 LLM 可见目录(Tier 1 ∪ Tier 2)"""
    return table_name in TIER1_TABLES or table_name in TIER2_CATALOG


def is_table_blocked(table_name: str) -> bool:
    """表是否在硬屏蔽清单(Tier 3)"""
    return table_name in TIER3_BLOCKED


def get_table_description(table_name: str) -> str:
    return TIER1_TABLES.get(table_name) or TIER2_CATALOG.get(table_name) or ''
