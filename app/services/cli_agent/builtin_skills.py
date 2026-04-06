# -*- coding: utf-8 -*-
"""
内置 Skill 定义与注册

应用启动时调用 register_builtin_skills(),将 5 个预定义业务查询 Skill
写入 cli_skills 表(已存在则跳过,管理员可在 DB 中自行修改)。

Skill 定义结构:
    name          — 唯一标识(英文)
    title         — 中文标题
    description   — 功能描述
    parameters    — 参数声明列表
    queries       — SQL 步骤列表(顺序执行,后步可引用前步结果)
    output_format — Markdown 输出模板

SQL 注意事项:
    - {param}          被引擎替换为 SQL 安全值(字符串带单引号)
    - {period_start}   period 参数自动产生, 格式 'YYYY-MM-DD'
    - {period_end}     同上
    - ILIKE 模式:      使用  ILIKE '%' || {keyword} || '%'
    - 敏感表(projects, companies, quotations, expenses, sales_orders,
      purchase_orders) 由 execute_safe_query 自动注入权限过滤
    - 支持软删除的表须显式 AND is_deleted = FALSE
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# =========================================================================
# 内置 Skill 定义
# =========================================================================

_BUILTIN_SKILLS: list[dict] = [

    # ------------------------------------------------------------------
    # 1. 销售行动力分析
    # ------------------------------------------------------------------
    {
        'name': 'sales_activity_report',
        'title': '销售行动力分析',
        'description': '统计指定时段内各销售人员的新建项目数、报价总额和行动记录数,综合评估销售团队活跃度。',
        'parameters': [
            {
                'name': 'period',
                'type': 'period',
                'required': True,
                'default_value': 'last_week',
                'description': '统计周期(this_week/last_week/this_month/last_month/this_quarter/last_quarter)',
            },
        ],
        'queries': [
            # Step 1: 新建项目数(按销售人员)
            {
                'as_name': 'projects',
                'description': '统计周期内各销售新建项目数',
                'sql': (
                    "SELECT u.real_name AS 销售人员, COUNT(p.id) AS 新建项目数 "
                    "FROM projects p "
                    "JOIN users u ON p.created_by = u.id "
                    "WHERE p.is_deleted = FALSE "
                    "AND p.created_at >= {period_start}::date "
                    "AND p.created_at < ({period_end}::date + INTERVAL '1 day') "
                    "GROUP BY u.real_name "
                    "ORDER BY COUNT(p.id) DESC"
                ),
            },
            # Step 2: 报价金额(按销售人员)
            {
                'as_name': 'quotations',
                'description': '统计周期内各销售报价总额',
                'sql': (
                    "SELECT u.real_name AS 销售人员, "
                    "q.currency AS 货币, "
                    "COUNT(q.id) AS 报价数, "
                    "COALESCE(SUM(q.amount), 0) AS 报价总额 "
                    "FROM quotations q "
                    "JOIN users u ON q.owner_id = u.id "
                    "WHERE q.created_at >= {period_start}::date "
                    "AND q.created_at < ({period_end}::date + INTERVAL '1 day') "
                    "GROUP BY u.real_name, q.currency "
                    "ORDER BY SUM(q.amount) DESC NULLS LAST"
                ),
            },
            # Step 3: 行动记录数(按销售人员)
            {
                'as_name': 'actions',
                'description': '统计周期内各销售行动记录数',
                'sql': (
                    "SELECT u.real_name AS 销售人员, COUNT(a.id) AS 行动记录数 "
                    "FROM actions a "
                    "JOIN users u ON a.owner_id = u.id "
                    "WHERE a.date >= {period_start}::date "
                    "AND a.date <= {period_end}::date "
                    "GROUP BY u.real_name "
                    "ORDER BY COUNT(a.id) DESC"
                ),
            },
        ],
        'output_format': (
            "## 📊 销售行动力分析 ({period_start} ~ {period_end})\n\n"
            "### 新建项目\n{projects.table}\n\n"
            "### 报价情况\n{quotations.table}\n\n"
            "### 行动记录\n{actions.table}"
        ),
    },

    # ------------------------------------------------------------------
    # 2. 客户全景
    # ------------------------------------------------------------------
    {
        'name': 'customer_overview',
        'title': '客户全景',
        'description': '根据客户名称关键词,查询客户基本信息、联系人、关联项目和报价汇总,提供 360 度客户视图。',
        'parameters': [
            {
                'name': 'keyword',
                'type': 'string',
                'required': True,
                'description': '客户名称关键词',
            },
        ],
        'queries': [
            # Step 1: 公司基本信息
            {
                'as_name': 'company',
                'description': '查询匹配的客户公司信息',
                'sql': (
                    "SELECT id, company_name AS 公司名称, "
                    "company_type AS 类型, country AS 国家, "
                    "industry AS 行业, status AS 状态 "
                    "FROM companies "
                    "WHERE company_name ILIKE '%' || {keyword} || '%' "
                    "AND is_deleted = FALSE "
                    "ORDER BY company_name "
                    "LIMIT 10"
                ),
            },
            # Step 2: 联系人
            {
                'as_name': 'contacts',
                'description': '查询客户的联系人列表',
                'sql': (
                    "SELECT c.name AS 姓名, c.department AS 部门, "
                    "c.position AS 职位, c.phone AS 电话, c.email AS 邮箱, "
                    "co.company_name AS 所属公司 "
                    "FROM contacts c "
                    "JOIN companies co ON c.company_id = co.id "
                    "WHERE co.company_name ILIKE '%' || {keyword} || '%' "
                    "AND co.is_deleted = FALSE "
                    "ORDER BY c.is_primary DESC, c.name"
                ),
            },
            # Step 3: 关联项目
            {
                'as_name': 'projects',
                'description': '查询客户关联的项目',
                'sql': (
                    "SELECT p.project_name AS 项目名称, "
                    "p.project_type AS 项目类型, "
                    "p.current_stage AS 当前阶段, "
                    "p.status AS 状态, "
                    "p.end_user AS 终端用户 "
                    "FROM projects p "
                    "JOIN project_customer_associations pca ON pca.project_id = p.id "
                    "JOIN companies co ON pca.company_id = co.id "
                    "WHERE co.company_name ILIKE '%' || {keyword} || '%' "
                    "AND co.is_deleted = FALSE "
                    "AND p.is_deleted = FALSE "
                    "ORDER BY p.created_at DESC"
                ),
            },
            # Step 4: 报价汇总
            {
                'as_name': 'quotations',
                'description': '汇总客户相关报价(通过项目关联)',
                'sql': (
                    "SELECT q.currency AS 货币, "
                    "COUNT(q.id) AS 报价数, "
                    "COALESCE(SUM(q.amount), 0) AS 报价总额 "
                    "FROM quotations q "
                    "JOIN projects p ON q.project_id = p.id "
                    "JOIN project_customer_associations pca ON pca.project_id = p.id "
                    "JOIN companies co ON pca.company_id = co.id "
                    "WHERE co.company_name ILIKE '%' || {keyword} || '%' "
                    "AND co.is_deleted = FALSE "
                    "AND p.is_deleted = FALSE "
                    "GROUP BY q.currency "
                    "ORDER BY SUM(q.amount) DESC NULLS LAST"
                ),
            },
        ],
        'output_format': (
            "## 🏢 客户全景 — 关键词: {keyword}\n\n"
            "### 公司信息\n"
            "{if company}{company.table}{endif}"
            "{if !company}未找到匹配的客户公司。{endif}\n\n"
            "### 联系人\n"
            "{if contacts}{contacts.table}{endif}"
            "{if !contacts}暂无联系人记录。{endif}\n\n"
            "### 关联项目\n"
            "{if projects}{projects.table}{endif}"
            "{if !projects}暂无关联项目。{endif}\n\n"
            "### 报价汇总\n"
            "{if quotations}{quotations.table}{endif}"
            "{if !quotations}暂无报价记录。{endif}"
        ),
    },

    # ------------------------------------------------------------------
    # 3. 项目详情
    # ------------------------------------------------------------------
    {
        'name': 'project_detail',
        'title': '项目详情',
        'description': '根据项目名称关键词,查看项目基本信息、报价列表、阶段变更历史和最近行动记录。',
        'parameters': [
            {
                'name': 'keyword',
                'type': 'string',
                'required': True,
                'description': '项目名称关键词',
            },
        ],
        'queries': [
            # Step 1: 项目基本信息
            {
                'as_name': 'project',
                'description': '查询匹配的项目基本信息',
                'sql': (
                    "SELECT p.id, p.project_name AS 项目名称, "
                    "p.project_type AS 项目类型, "
                    "p.current_stage AS 当前阶段, "
                    "p.status AS 状态, "
                    "p.end_user AS 终端用户, "
                    "p.dealer AS 经销商, "
                    "p.contractor AS 承包商, "
                    "u.real_name AS 负责人 "
                    "FROM projects p "
                    "LEFT JOIN users u ON p.owner_id = u.id "
                    "WHERE p.project_name ILIKE '%' || {keyword} || '%' "
                    "AND p.is_deleted = FALSE "
                    "ORDER BY p.created_at DESC "
                    "LIMIT 5"
                ),
            },
            # Step 2: 报价列表
            {
                'as_name': 'quotations',
                'description': '查询项目的报价列表',
                'sql': (
                    "SELECT q.quotation_number AS 报价单号, "
                    "q.amount AS 金额, "
                    "q.currency AS 货币, "
                    "q.approval_status AS 审批状态, "
                    "u.real_name AS 报价人 "
                    "FROM quotations q "
                    "JOIN projects p ON q.project_id = p.id "
                    "LEFT JOIN users u ON q.owner_id = u.id "
                    "WHERE p.project_name ILIKE '%' || {keyword} || '%' "
                    "AND p.is_deleted = FALSE "
                    "ORDER BY q.created_at DESC"
                ),
            },
            # Step 3: 阶段变更历史
            {
                'as_name': 'stage_history',
                'description': '查询项目阶段变更记录',
                'sql': (
                    "SELECT psh.from_stage AS 原阶段, "
                    "psh.to_stage AS 新阶段, "
                    "psh.change_date::date AS 变更日期, "
                    "psh.remarks AS 备注 "
                    "FROM project_stage_history psh "
                    "JOIN projects p ON psh.project_id = p.id "
                    "WHERE p.project_name ILIKE '%' || {keyword} || '%' "
                    "AND p.is_deleted = FALSE "
                    "ORDER BY psh.change_date DESC"
                ),
            },
            # Step 4: 最近行动记录
            {
                'as_name': 'actions',
                'description': '查询项目最近的行动记录',
                'sql': (
                    "SELECT a.date AS 日期, "
                    "a.communication AS 内容, "
                    "u.real_name AS 记录人 "
                    "FROM actions a "
                    "JOIN projects p ON a.project_id = p.id "
                    "LEFT JOIN users u ON a.owner_id = u.id "
                    "WHERE p.project_name ILIKE '%' || {keyword} || '%' "
                    "AND p.is_deleted = FALSE "
                    "ORDER BY a.date DESC "
                    "LIMIT 10"
                ),
            },
        ],
        'output_format': (
            "## 📋 项目详情 — 关键词: {keyword}\n\n"
            "### 项目信息\n"
            "{if project}{project.table}{endif}"
            "{if !project}未找到匹配的项目。{endif}\n\n"
            "### 报价列表\n"
            "{if quotations}{quotations.table}{endif}"
            "{if !quotations}暂无报价记录。{endif}\n\n"
            "### 阶段变更历史\n"
            "{if stage_history}{stage_history.table}{endif}"
            "{if !stage_history}暂无阶段变更记录。{endif}\n\n"
            "### 最近行动记录\n"
            "{if actions}{actions.table}{endif}"
            "{if !actions}暂无行动记录。{endif}"
        ),
    },

    # ------------------------------------------------------------------
    # 4. 项目管线分析
    # ------------------------------------------------------------------
    {
        'name': 'pipeline_analysis',
        'title': '项目管线分析',
        'description': '按项目阶段汇总项目数和报价总额,呈现销售管线全貌。',
        'parameters': [],
        'queries': [
            {
                'as_name': 'pipeline',
                'description': '按阶段汇总项目数和报价金额',
                'sql': (
                    "SELECT p.current_stage AS 阶段, "
                    "COUNT(DISTINCT p.id) AS 项目数, "
                    "COALESCE(SUM(q.amount), 0) AS 报价总额 "
                    "FROM projects p "
                    "LEFT JOIN quotations q ON q.project_id = p.id "
                    "WHERE p.is_deleted = FALSE "
                    "AND p.status != 'lost' "
                    "GROUP BY p.current_stage "
                    "ORDER BY CASE p.current_stage "
                    "  WHEN 'discover' THEN 1 "
                    "  WHEN 'embed' THEN 2 "
                    "  WHEN 'pre_tender' THEN 3 "
                    "  WHEN 'tendering' THEN 4 "
                    "  WHEN 'awarded' THEN 5 "
                    "  WHEN 'quoted' THEN 6 "
                    "  WHEN 'signed' THEN 7 "
                    "  WHEN 'lost' THEN 8 "
                    "  WHEN 'paused' THEN 9 "
                    "  ELSE 99 "
                    "END"
                ),
            },
        ],
        'output_format': (
            "## 🔄 项目管线分析\n\n"
            "{pipeline.table}\n\n"
            "共 {pipeline.count} 个阶段有活跃项目。"
        ),
    },

    # ------------------------------------------------------------------
    # 5. 周报数据汇总
    # ------------------------------------------------------------------
    {
        'name': 'weekly_summary',
        'title': '周报数据汇总',
        'description': '汇总指定时段的新建项目、报价、行动记录和工作项数据,用于编写周报/月报。可按用户姓名筛选。',
        'parameters': [
            {
                'name': 'period',
                'type': 'period',
                'required': True,
                'default_value': 'last_week',
                'description': '统计周期(this_week/last_week/this_month/last_month/this_quarter/last_quarter)',
            },
            {
                'name': 'user_name',
                'type': 'string',
                'required': False,
                'description': '指定用户姓名(可选,为空则统计所有)',
            },
        ],
        'queries': [
            # Step 1: 新建项目
            {
                'as_name': 'projects',
                'description': '周期内新建项目(数量+名称)',
                'sql': (
                    "SELECT p.project_name AS 项目名称, "
                    "u.real_name AS 创建人, "
                    "p.created_at::date AS 创建日期 "
                    "FROM projects p "
                    "JOIN users u ON p.created_by = u.id "
                    "WHERE p.is_deleted = FALSE "
                    "AND p.created_at >= {period_start}::date "
                    "AND p.created_at < ({period_end}::date + INTERVAL '1 day') "
                    "AND ('' = {user_name} OR u.real_name ILIKE '%' || {user_name} || '%') "
                    "ORDER BY p.created_at DESC"
                ),
            },
            # Step 2: 新增报价
            {
                'as_name': 'quotations',
                'description': '周期内新增报价(数量+总额)',
                'sql': (
                    "SELECT q.quotation_number AS 报价单号, "
                    "q.amount AS 金额, "
                    "q.currency AS 货币, "
                    "u.real_name AS 报价人 "
                    "FROM quotations q "
                    "JOIN users u ON q.owner_id = u.id "
                    "WHERE q.created_at >= {period_start}::date "
                    "AND q.created_at < ({period_end}::date + INTERVAL '1 day') "
                    "AND ('' = {user_name} OR u.real_name ILIKE '%' || {user_name} || '%') "
                    "ORDER BY q.created_at DESC"
                ),
            },
            # Step 3: 行动记录
            {
                'as_name': 'actions',
                'description': '周期内行动记录数',
                'sql': (
                    "SELECT u.real_name AS 负责人, "
                    "COUNT(a.id) AS 行动记录数 "
                    "FROM actions a "
                    "JOIN users u ON a.owner_id = u.id "
                    "WHERE a.date >= {period_start}::date "
                    "AND a.date <= {period_end}::date "
                    "AND ('' = {user_name} OR u.real_name ILIKE '%' || {user_name} || '%') "
                    "GROUP BY u.real_name "
                    "ORDER BY COUNT(a.id) DESC"
                ),
            },
            # Step 4: 工作项
            {
                'as_name': 'work_items',
                'description': '周期内已完成工作项(数量+总工时)',
                'sql': (
                    "SELECT u.real_name AS 负责人, "
                    "COUNT(wi.id) AS 完成数, "
                    "COALESCE(SUM(wi.actual_hours), 0) AS 总工时 "
                    "FROM work_items wi "
                    "JOIN users u ON wi.owner_id = u.id "
                    "WHERE wi.status = 'completed' "
                    "AND wi.planned_date >= {period_start}::date "
                    "AND wi.planned_date <= {period_end}::date "
                    "AND ('' = {user_name} OR u.real_name ILIKE '%' || {user_name} || '%') "
                    "GROUP BY u.real_name "
                    "ORDER BY SUM(wi.actual_hours) DESC NULLS LAST"
                ),
            },
        ],
        'output_format': (
            "## 📝 周报数据汇总 ({period_start} ~ {period_end})\n\n"
            "### 新建项目 ({projects.count}个)\n"
            "{if projects}{projects.table}{endif}"
            "{if !projects}本周期无新建项目。{endif}\n\n"
            "### 新增报价 ({quotations.count}单)\n"
            "{if quotations}{quotations.table}{endif}"
            "{if !quotations}本周期无新增报价。{endif}\n\n"
            "### 行动记录\n"
            "{if actions}{actions.table}{endif}"
            "{if !actions}本周期无行动记录。{endif}\n\n"
            "### 工作项完成情况\n"
            "{if work_items}{work_items.table}{endif}"
            "{if !work_items}本周期无已完成工作项。{endif}"
        ),
    },
]


# =========================================================================
# 注册函数
# =========================================================================

def register_builtin_skills():
    """应用启动时调用,将内置 Skill 写入数据库(已存在则跳过)。

    如果某个 name 已存在于 cli_skills 表中,则不覆盖——管理员可能已修改过
    参数或 SQL。仅在记录不存在时才插入。
    """
    from app import db
    from app.models.cli_skill import CliSkill

    added = []
    for skill_def in _BUILTIN_SKILLS:
        name = skill_def['name']
        existing = CliSkill.query.filter_by(name=name).first()
        if existing:
            continue  # 不覆盖已有的(admin 可能已修改)

        skill = CliSkill(
            name=name,
            title=skill_def['title'],
            description=skill_def['description'],
            parameters=skill_def.get('parameters', []),
            queries=skill_def['queries'],
            output_format=skill_def.get('output_format'),
            scope='global',
        )
        db.session.add(skill)
        added.append(name)

    if added:
        db.session.commit()
        logger.info(f'[BuiltinSkills] 注册了 {len(added)} 个内置 Skill: {added}')
    else:
        logger.debug('[BuiltinSkills] 所有内置 Skill 已存在,无需注册')
