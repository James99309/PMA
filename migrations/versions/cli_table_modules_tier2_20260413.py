"""register Tier 2 tables into cli_table_modules

Revision ID: cli_tbl_tier2_20260413
Revises: wiki_topics_20260413
Create Date: 2026-04-13

Context
-------
CLI Agent 分级 schema 改造 Phase 2:把 Tier 2 目录(132 张)批量登记到
cli_table_modules,使 query_pma_database 和 describe_table 能通过表级门禁。

Tier 1 的 18 张已在 cli_permissions_20260411 迁移登记,本迁移补齐其余 ~130 张。

归属规则:
- mode='module': 作为某 CLI 权限模块的主表(例如 role_permissions → config_management)
- mode='follow': 跟随某张已登记表做权限继承(例如 quotation_details → quotations)

幂等性: 使用 ON CONFLICT (table_name) DO NOTHING。
"""
from alembic import op


revision = 'cli_tbl_tier2_20260413'
# 合并两个 head: wiki_topics 分支 + e64f8165e3c3(ai_processed)分支
down_revision = ('wiki_topics_20260413', 'e64f8165e3c3')
branch_labels = None
depends_on = None


# (table_name, mode, module_or_parent, description)
# mode='module' → 第3列是 module
# mode='follow' → 第3列是 parent_table
_ROWS = [
    # ── 项目相关 (follow projects) ──────────────────────────
    ('project_members', 'follow', 'projects', '项目成员'),
    ('project_rating_records', 'follow', 'projects', '项目评级记录'),
    ('project_scoring_records', 'follow', 'projects', '项目评分记录'),
    ('project_scoring_config', 'follow', 'projects', '项目评分配置'),
    ('project_total_scores', 'follow', 'projects', '项目总分'),
    ('five_star_project_baselines', 'follow', 'projects', '五星项目基线'),
    ('stage_attachments', 'follow', 'projects', '阶段附件'),
    ('stage_dependencies', 'follow', 'projects', '阶段依赖'),
    ('stage_reviews', 'follow', 'projects', '阶段评审'),

    # ── 客户相关 (follow companies / actions) ──────────────
    ('company_assets', 'follow', 'companies', '公司资产'),
    ('action_reply', 'follow', 'actions', '客户跟进回复'),
    ('monthly_activity_snapshots', 'follow', 'companies', '月度活跃度快照'),

    # ── 报价 (follow quotations) ───────────────────────────
    ('quotation_confirmation_tasks', 'follow', 'quotations', '报价确认任务'),

    # ── 产品 (follow products) ─────────────────────────────
    ('product_categories', 'follow', 'products', '产品大类'),
    ('product_subcategories', 'follow', 'products', '产品子类'),
    ('product_regions', 'follow', 'products', '产品地区'),
    ('product_region_prices', 'follow', 'products', '产品多地区面价'),
    ('product_names', 'follow', 'products', '产品名称字典'),
    ('product_codes', 'follow', 'products', '产品编码'),
    ('product_code_fields', 'follow', 'products', '产品编码字段定义'),
    ('product_code_field_options', 'follow', 'products', '产品编码字段选项'),
    ('product_code_field_values', 'follow', 'products', '产品编码字段值'),
    ('product_config_values', 'follow', 'products', '产品配置值'),
    ('product_configurations', 'follow', 'products', '产品配置'),
    ('product_relations', 'follow', 'products', '产品关联关系'),
    ('product_serial_numbers', 'follow', 'products', '产品序列号'),
    ('product_specs', 'follow', 'products', '产品规格'),
    ('product_tests', 'follow', 'products', '产品测试'),
    ('product_test_details', 'follow', 'products', '产品测试明细'),
    ('product_test_samplings', 'follow', 'products', '产品测试抽样'),
    ('dev_products', 'follow', 'products', '研发产品'),
    ('dev_product_specs', 'follow', 'products', '研发产品规格'),
    ('dev_product_milestones', 'follow', 'products', '研发产品里程碑'),
    ('spec_attachments', 'follow', 'products', '规格附件'),
    ('spec_categories', 'follow', 'products', '规格分类'),
    ('spec_definitions', 'follow', 'products', '规格定义'),
    ('spec_templates', 'follow', 'products', '规格模板'),
    ('spec_template_items', 'follow', 'products', '规格模板项'),
    ('specification_dictionary', 'follow', 'products', '规格字典'),
    ('specification_options', 'follow', 'products', '规格选项'),
    ('test_method_dictionary', 'follow', 'products', '测试方法字典'),
    ('test_condition_dictionary', 'follow', 'products', '测试条件字典'),
    ('serial_number_histories', 'follow', 'products', '序列号变更历史'),
    ('file_library', 'follow', 'products', '文件库'),

    # ── 订单链路 ───────────────────────────────────────────
    ('sales_order_details', 'follow', 'sales_orders', '销售订单明细'),
    ('purchase_order_details', 'follow', 'purchase_orders', '采购订单明细'),
    ('purchase_order_shipments', 'follow', 'purchase_orders', '采购订单发货'),
    ('purchase_order_shipment_details', 'follow', 'purchase_orders', '采购发货明细'),
    ('purchase_order_delivery_changes', 'follow', 'purchase_orders', '采购交期变更'),
    ('purchase_order_pricing_orders', 'follow', 'purchase_orders', '采购↔批价关联'),
    ('purchase_order_stage_history', 'follow', 'purchase_orders', '采购订单阶段历史'),
    ('shipment_details', 'follow', 'shipments', '发货明细'),
    ('inventory', 'module', 'inventory', '库存'),
    ('inventory_transactions', 'follow', 'inventory', '库存流水'),

    # ── 批价/结算 ──────────────────────────────────────────
    ('pricing_order_details', 'follow', 'pricing_orders', '批价单明细'),
    ('pricing_order_approval_records', 'follow', 'pricing_orders', '批价单审批记录'),
    ('settlement_orders', 'module', 'settlement_order', '结算单'),
    ('settlement_order_details', 'follow', 'settlement_orders', '结算单明细'),
    ('settlement_details', 'follow', 'settlement_orders', '结算明细'),
    ('settlements', 'follow', 'settlement_orders', '结算流水'),

    # ── 报销 ───────────────────────────────────────────────
    ('expense_details', 'follow', 'expenses', '报销明细'),
    ('expense_budgets', 'module', 'expense', '报销预算'),
    ('role_expense_budgets', 'follow', 'expenses', '角色报销预算'),

    # ── 工作日志 ────────────────────────────────────────────
    ('worklog_comments', 'follow', 'worklogs', '工作日志评论'),
    ('worklog_reactions', 'follow', 'worklogs', '工作日志点赞'),

    # ── 用户/员工扩展 (follow users) ──────────────────────
    ('departments', 'module', 'user_management', '部门'),
    ('affiliations', 'follow', 'users', '数据归属(上下级)'),
    ('user_daily_login_records', 'follow', 'users', '用户日登录记录'),
    ('user_points_ledger', 'follow', 'users', '用户积分流水'),
    ('user_folders', 'follow', 'users', '用户文件夹'),
    ('access_requests', 'follow', 'users', '权限申请'),

    # ── 权限 / 角色管理 (config_management) ────────────────
    ('role_permissions', 'module', 'permission_management', '角色权限'),
    ('role_feature_permissions', 'follow', 'role_permissions', '角色功能权限'),
    ('permissions', 'follow', 'role_permissions', '用户权限'),
    ('permission_modules', 'module', 'permission_management', '权限模块'),
    ('permission_module_features', 'follow', 'permission_modules', '权限模块功能点'),
    ('data_affiliation', 'module', 'permission_management', '数据归属配置'),
    ('cli_table_modules', 'module', 'config_management', 'CLI 表归属注册'),

    # ── 审批 (approval) ────────────────────────────────────
    ('approval_instance', 'module', 'approval', '审批实例'),
    ('approval_record', 'follow', 'approval_instance', '审批记录'),
    ('approval_step', 'follow', 'approval_instance', '审批节点'),
    ('approval_process_template', 'module', 'approval', '审批流程模板'),
    ('approval_branch_condition', 'follow', 'approval_process_template', '审批分支条件'),

    # ── 任务 (follow tasks 已在 T1) ────────────────────────
    ('task_replies', 'follow', 'tasks', '任务回复'),
    ('task_attachments', 'follow', 'tasks', '任务附件'),

    # ── 绩效 (performance_management) ──────────────────────
    ('performance_statistics', 'module', 'performance_management', '绩效统计'),
    ('performance_targets', 'follow', 'performance_statistics', '绩效目标'),
    ('performance_metrics_definition', 'follow', 'performance_statistics', '绩效指标定义'),
    ('performance_formula_templates', 'follow', 'performance_statistics', '绩效公式模板'),
    ('performance_manual_attachments', 'follow', 'performance_statistics', '绩效手册附件'),
    ('performance_manual_entries', 'follow', 'performance_statistics', '绩效手册条目'),
    ('user_performance_targets', 'follow', 'performance_statistics', '用户绩效目标'),
    ('quarterly_performance_data', 'follow', 'performance_statistics', '季度绩效数据'),
    ('role_performance_access', 'follow', 'performance_statistics', '角色绩效访问范围'),
    ('role_performance_config', 'follow', 'performance_statistics', '角色绩效配置'),
    ('role_performance_items', 'follow', 'performance_statistics', '角色绩效项'),
    ('role_performance_targets', 'follow', 'performance_statistics', '角色绩效目标'),

    # ── 薪酬 (performance_management) ──────────────────────
    ('salary_base_params', 'follow', 'performance_statistics', '薪酬基础参数'),
    ('salary_calculation_result', 'follow', 'performance_statistics', '薪酬计算结果'),
    ('salary_formula_config', 'follow', 'performance_statistics', '薪酬公式配置'),
    ('salary_grade_bandwidth', 'follow', 'performance_statistics', '薪酬等级带宽'),
    ('salary_grade_config', 'follow', 'performance_statistics', '薪酬等级配置'),
    ('salary_period_snapshots', 'follow', 'performance_statistics', '薪酬周期快照'),
    ('salary_step_rules', 'follow', 'performance_statistics', '薪酬步进规则'),
    ('employee_salary_config', 'follow', 'performance_statistics', '员工薪酬配置'),
    ('formula_templates_extended', 'follow', 'performance_statistics', '扩展公式模板'),

    # ── 知识库 (未建独立 module,挂 worklog 过渡) ─────────
    # TODO: 若将来有 knowledge module,迁移到独立归属
    ('knowledge_documents', 'follow', 'worklogs', '知识库文档'),
    ('knowledge_wiki_articles', 'follow', 'worklogs', '知识库 Wiki 文章'),
    ('knowledge_document_tags', 'follow', 'worklogs', '文档标签关联'),
    ('knowledge_tags', 'follow', 'worklogs', '知识标签'),
    ('knowledge_topics', 'follow', 'worklogs', '知识主题'),
    ('knowledge_raw_files', 'follow', 'worklogs', '知识库原始文件'),
    ('knowledge_promotion_requests', 'follow', 'worklogs', '知识晋升申请'),
    ('knowledge_share_grants', 'follow', 'worklogs', '知识共享授权'),

    # ── 会议 (follow worklogs 过渡) ────────────────────────
    ('meeting_minutes', 'follow', 'worklogs', '会议纪要'),
    ('meeting_recordings', 'follow', 'worklogs', '会议录音'),
    ('meeting_transcripts', 'follow', 'worklogs', '会议转录'),
    ('meeting_action_items', 'follow', 'worklogs', '会议行动项'),
    ('meeting_speakers', 'follow', 'worklogs', '会议发言人'),

    # ── 公告 / 消息 ───────────────────────────────────────
    ('announcements', 'module', 'announcement', '公告'),
    ('announcement_attachments', 'follow', 'announcements', '公告附件'),
    ('messages', 'module', 'notification', '消息'),

    # ── 调研问卷 (follow projects 过渡) ────────────────────
    ('survey_questions', 'follow', 'projects', '问卷题目'),
    ('survey_responses', 'follow', 'projects', '问卷答复'),
    ('survey_templates', 'follow', 'projects', '问卷模板'),

    # ── 销售配置 / 系统图 ──────────────────────────────────
    ('sales_team_config', 'module', 'user_management', '销售团队配置'),
    ('system_diagrams', 'module', 'system_diagram', '系统图'),

    # ── 系统配置 (config_management) ──────────────────────
    ('system_settings', 'module', 'config_management', '系统设置'),
    ('dictionaries', 'module', 'dictionary_management', '数据字典'),
]


def upgrade():
    # 用 ON CONFLICT 保证幂等
    for table_name, mode, target, description in _ROWS:
        if mode == 'module':
            op.execute(f"""
                INSERT INTO cli_table_modules
                    (table_name, display_name, mode, module, description, is_active, sort_order)
                VALUES (
                    '{table_name}',
                    '{description}',
                    'module',
                    '{target}',
                    '{description}',
                    true,
                    100
                )
                ON CONFLICT (table_name) DO NOTHING
            """)
        else:  # follow
            op.execute(f"""
                INSERT INTO cli_table_modules
                    (table_name, display_name, mode, parent_table, description, is_active, sort_order)
                VALUES (
                    '{table_name}',
                    '{description}',
                    'follow',
                    '{target}',
                    '{description}',
                    true,
                    100
                )
                ON CONFLICT (table_name) DO NOTHING
            """)


def downgrade():
    table_names = [r[0] for r in _ROWS]
    if not table_names:
        return
    quoted = ','.join(f"'{t}'" for t in table_names)
    op.execute(f"DELETE FROM cli_table_modules WHERE table_name IN ({quoted})")
