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
# work_summary render 函数（模块级，避免多行字符串转义地狱）
# =========================================================================

_WORK_SUMMARY_RENDER = '''\
def render(results, params):
    SALES_ROLES = frozenset([
        'sales', 'sales_director', 'sales_manager',
        'channel_manager', 'solution_manager', 'business_admin',
    ])

    def tbl(step, limit=None):
        d = results.get(step, {})
        c = d.get('columns', [])
        r = d.get('rows', [])
        if not c or not r:
            return None
        show = r[:limit] if limit else r
        lines = ['| ' + ' | '.join(str(x) for x in c) + ' |',
                 '| ' + ' | '.join(['---'] * len(c)) + ' |']
        for row in show:
            lines.append('| ' + ' | '.join(str(v or \'\') for v in row) + ' |')
        if limit and len(r) >= limit:
            lines.append(f\'> _仅显示前 {limit} 条_\')
        return \'\\n\'.join(lines)

    def cnt(step):
        return results.get(step, {}).get(\'row_count\', 0)

    ui = results.get(\'user_info\', {})
    ur = ui.get(\'rows\', [])
    uc = ui.get(\'columns\', [])
    if not ur:
        uname = params.get(\'user_name\', \'\')
        return f\'未找到用户"{uname}"，请确认姓名是否正确。\'

    def col(row, name):
        return row[uc.index(name)] if name in uc else \'\'

    name  = col(ur[0], \'姓名\') or params.get(\'user_name\', \'\')
    role  = str(col(ur[0], \'角色\') or \'\')
    dept  = col(ur[0], \'部门\') or \'\'
    period = params.get(\'period\', \'\')
    is_sales = role in SALES_ROLES
    out = []

    out.append(f\'## {name} 工作总结 · {period}\')
    out.append(f\'**{dept}** | 角色：**{role}**\')
    out.append(\'\')

    # ── 活跃度（每日分布 + 最近3条日志内容）──────────────────────────
    out.append(\'### 📅 活跃度\')
    t = tbl(\'daily_dist\')
    if t:
        out.append(t)
    out.append(\'\')
    wl_d    = results.get(\'worklogs\', {})
    wl_rows = wl_d.get(\'rows\', [])
    wl_cols = wl_d.get(\'columns\', [])
    if wl_rows:
        ci = wl_cols.index(\'内容\') if \'内容\' in wl_cols else -1
        di = wl_cols.index(\'日期\') if \'日期\' in wl_cols else 0
        if ci >= 0:
            out.append(\'**最近日志摘要：**\')
            for row in wl_rows[:3]:
                d = str(row[di] or \'\')
                content = str(row[ci] or \'\').strip()
                if content:
                    out.append(f\'- **{d}**：{content[:300]}\')
            out.append(\'\')

    # ── 工作项（类型统计 + 最近3天明细）──────────────────────────────
    wi_d    = results.get(\'work_items\', {})
    wi_rows = wi_d.get(\'rows\', [])
    wi_cols = wi_d.get(\'columns\', [])
    wi_total = cnt(\'work_items\')
    out.append(f\'### ✅ 工作项（{wi_total} 条）\')
    if wi_rows:
        type_idx = wi_cols.index(\'类型\') if \'类型\' in wi_cols else -1
        date_idx = wi_cols.index(\'计划日期\') if \'计划日期\' in wi_cols else 0
        if type_idx >= 0:
            type_map = {
                \'presales_support\': \'售前支持\', \'customer_visit\': \'客户拜访\',
                \'customer_maintenance\': \'客户维护\', \'meeting\': \'会议\', \'admin\': \'行政\',
            }
            tc = {}
            for row in wi_rows:
                k = type_map.get(str(row[type_idx] or \'\'), str(row[type_idx] or \'其他\'))
                tc[k] = tc.get(k, 0) + 1
            out.append(\'  \'.join(f\'{k} {v}项\' for k, v in sorted(tc.items(), key=lambda x: -x[1])))
            out.append(\'\')
        all_dates = sorted({str(row[date_idx]) for row in wi_rows if row[date_idx]}, reverse=True)
        last3 = set(all_dates[:3])
        recent = [row for row in wi_rows if str(row[date_idx]) in last3]
        if recent:
            out.append(\'**最近3天明细：**\')
            show = recent[:15]
            hdr = \'| \' + \' | \'.join(str(x) for x in wi_cols) + \' |\'
            sep = \'| \' + \' | \'.join([\'---\'] * len(wi_cols)) + \' |\'
            body = \'\\n\'.join(\'| \' + \' | \'.join(str(v or \'\') for v in row) + \' |\' for row in show)
            out.append(hdr + \'\\n\' + sep + \'\\n\' + body)
    else:
        out.append(\'_本期无工作项_\')
    out.append(\'\')

    if is_sales:
        out.append(\'---\\n## 销售业务\\n\')

        # ── 新增业务摘要行 ──────────────────────────────────────────────
        np_c  = cnt(\'new_projects\')
        nc_c  = cnt(\'new_customers\')
        nct_c = cnt(\'new_contacts\')
        q_c   = cnt(\'quotations\')
        biz = []
        if np_c:  biz.append(f\'新建项目 **{np_c}** 个\')
        if nc_c:  biz.append(f\'新建客户 **{nc_c}** 个\')
        if nct_c: biz.append(f\'新建联系人 **{nct_c}** 个\')
        if q_c:   biz.append(f\'报价 **{q_c}** 份\')
        out.append(\'### 📈 新增业务\')
        out.append(\'　\'.join(biz) if biz else \'_本期无新增业务_\')
        out.append(\'\')
        for step, label in [(\'new_projects\', \'新建项目\'), (\'new_customers\', \'新建客户\'),
                             (\'new_contacts\', \'新建联系人\'), (\'quotations\', \'报价\')]:
            t = tbl(step)
            if t:
                out.append(f\'**{label}：**\')
                out.append(t)
                out.append(\'\')

        # ── 项目阶段推动 ────────────────────────────────────────────────
        sc_c = cnt(\'stage_changes\')
        out.append(f\'### 🔄 项目阶段推动（{sc_c} 次）\')
        t = tbl(\'stage_changes\')
        out.append(t if t else \'_本期无项目阶段变化_\')
        out.append(\'\')

        # ── 搁置/失败（有数据才显示）───────────────────────────────────
        lp_c = cnt(\'lost_paused\')
        if lp_c > 0:
            out.append(f\'### ❌ 近期搁置/失败（{lp_c} 个）\')
            t = tbl(\'lost_paused\')
            if t:
                out.append(t)
            out.append(\'\')

        # ── 在途项目零行动风险（排除签约）─────────────────────────────
        rp_c = cnt(\'risk_pipeline\')
        out.append(f\'### ⚠️ 在途项目零行动（{rp_c} 个）\')
        t = tbl(\'risk_pipeline\', 15)
        if t:
            out.append(\'以下在途项目本期无行动记录（签约项目已排除）：\')
            out.append(t)
        else:
            out.append(\'_✓ 本期在途项目均有跟进_\')
        out.append(\'\')

        # ── 绩效目标 ────────────────────────────────────────────────────
        if cnt(\'perf_targets\') > 0:
            out.append(\'### 🎯 绩效目标（本季度）\')
            t = tbl(\'perf_targets\')
            if t:
                out.append(\'**目标设定：**\\n\' + t)
                out.append(\'\')
            t2 = tbl(\'quarter_actual\')
            if t2:
                out.append(\'**本季度累计：**\\n\' + t2)
                out.append(\'\')

        out.append(\'---\\n### 🔍 分析建议\')
        out.append(\'请基于以上数据，从以下维度给出简要分析（每条1-2句）：\')
        out.append(\'- **活跃度**：日志覆盖天数，是否有连续空白工作日\')
        out.append(\'- **销售进展**：新增项目/客户/报价趋势\')
        out.append(\'- **风险**：搁置/失败项目情况；在途零行动项目是否需立即跟进\')
    else:
        out.append(\'---\\n## 任务执行情况\\n\')
        out.append(\'### 📋 工作项统计（按状态/类型）\')
        t = tbl(\'task_stats\')
        out.append(t if t else \'_本期无工作项记录_\')
        out.append(\'\')
        out.append(\'---\\n### 🔍 分析建议\')
        out.append(\'请基于以上数据，从以下维度给出简要分析（每条1-2句）：\')
        out.append(\'- **工作量**：日志填写频率，工作项完成率\')
        out.append(\'- **任务管理**：待办/完成比例，是否有积压\')
        out.append(\'- **异常情况**：连续无日志的工作日\')

    return \'\\n\'.join(out)
'''

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
    # 5. 通用工作总结（取代 sales_weekly_review）
    # ------------------------------------------------------------------
    {
        'name': 'work_summary',
        'title': '工作总结（通用）',
        'description': (
            '查询任意员工在指定时间段内的工作总结，包括工作日志明细、工作项、每日活动分布；'
            '销售类角色额外展示新建项目/客户/联系人、项目推动情况、报价和绩效目标；'
            '其他角色展示工作项统计。'
            '触发词：工作总结、工作情况、工作汇报、查一下XX的工作、XX最近工作怎么样、'
            '周报、月报、工作报告、检查工作。'
            '重要：如果用户未明确指定时间范围，必须先向用户询问确认时间范围，再调用此 Skill。'
        ),
        'parameters': [
            {
                'name': 'user_name',
                'type': 'string',
                'required': True,
                'description': '被查询人姓名',
            },
            {
                'name': 'period',
                'type': 'period',
                'required': True,
                'description': '统计周期。如用户未明确指定，必须先询问再调用。',
            },
        ],
        'queries': [
            # Step 1: 用户基本信息（获取 role 用于后续分支）
            {
                'as_name': 'user_info',
                'description': '获取用户角色和部门',
                'sql': (
                    "SELECT COALESCE(u.real_name, u.username) AS 姓名, "
                    "u.role AS 角色, COALESCE(u.department, '未分配') AS 部门 "
                    "FROM users u "
                    "WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    "OR u.username ILIKE '%' || {user_name} || '%' "
                    "LIMIT 1"
                ),
            },
            # Step 2: 工作日志明细
            {
                'as_name': 'worklogs',
                'description': '期间工作日志明细',
                'sql': (
                    "SELECT wl.log_date AS 日期, "
                    "CASE wl.log_type WHEN 'weekly' THEN '周报' ELSE '日报' END AS 类型, "
                    "CASE wl.status WHEN 'submitted' THEN '已提交' ELSE '草稿' END AS 状态, "
                    "COALESCE(wl.total_hours, 0) AS 工时, "
                    "LEFT(COALESCE(wl.summary, wl.additional_notes, ''), 500) AS 内容 "
                    "FROM worklogs wl "
                    "JOIN users u ON wl.owner_id = u.id "
                    "WHERE (u.real_name ILIKE '%' || {user_name} || '%' "
                    "   OR u.username ILIKE '%' || {user_name} || '%') "
                    "AND wl.log_date >= {period_start}::date "
                    "AND wl.log_date <= {period_end}::date "
                    "ORDER BY wl.log_date DESC"
                ),
            },
            # Step 3: 工作项明细
            {
                'as_name': 'work_items',
                'description': '期间工作项明细',
                'sql': (
                    "SELECT wi.planned_date AS 计划日期, "
                    "wi.title AS 工作项, "
                    "wi.work_type AS 类型, "
                    "CASE wi.status "
                    "  WHEN 'completed' THEN '✓ 完成' "
                    "  WHEN 'planned' THEN '待办' "
                    "  WHEN 'cancelled' THEN '已取消' "
                    "  ELSE wi.status END AS 状态, "
                    "COALESCE(p.project_name, '-') AS 关联项目 "
                    "FROM work_items wi "
                    "JOIN users u ON wi.owner_id = u.id "
                    "LEFT JOIN projects p ON wi.project_id = p.id "
                    "WHERE (u.real_name ILIKE '%' || {user_name} || '%' "
                    "   OR u.username ILIKE '%' || {user_name} || '%') "
                    "AND wi.planned_date >= {period_start}::date "
                    "AND wi.planned_date <= {period_end}::date "
                    "AND wi.is_deleted = FALSE "
                    "ORDER BY wi.planned_date DESC, wi.id LIMIT 30"
                ),
            },
            # Step 4: 每日活动分布
            {
                'as_name': 'daily_dist',
                'description': '每日活动分布（工作日）',
                'sql': (
                    "SELECT d.day::date AS 日期, "
                    "COALESCE(ac.action_count, 0) AS 行动数, "
                    "COALESCE(wi.item_count, 0) AS 工作项数, "
                    "COALESCE(wl.log_status, '无') AS 日志状态, "
                    "CASE WHEN COALESCE(ac.action_count,0)=0 AND COALESCE(wi.item_count,0)=0 THEN '⚪ 空白' "
                    "     WHEN COALESCE(ac.action_count,0)>0 THEN '🟢 活跃' ELSE '🔵 仅工作项' END AS 备注 "
                    "FROM generate_series({period_start}::date, {period_end}::date, '1 day'::interval) d(day) "
                    "LEFT JOIN ( "
                    "  SELECT a.date, COUNT(*) AS action_count "
                    "  FROM actions a JOIN users u ON a.owner_id = u.id "
                    "  WHERE u.real_name ILIKE '%' || {user_name} || '%' GROUP BY a.date "
                    ") ac ON ac.date = d.day::date "
                    "LEFT JOIN ( "
                    "  SELECT wi.planned_date, COUNT(*) AS item_count "
                    "  FROM work_items wi JOIN users u ON wi.owner_id = u.id "
                    "  WHERE u.real_name ILIKE '%' || {user_name} || '%' AND wi.is_deleted=FALSE "
                    "  GROUP BY wi.planned_date "
                    ") wi ON wi.planned_date = d.day::date "
                    "LEFT JOIN ( "
                    "  SELECT wl.log_date, "
                    "  CASE wl.status WHEN 'submitted' THEN '已提交' ELSE '草稿' END AS log_status "
                    "  FROM worklogs wl JOIN users u ON wl.owner_id = u.id "
                    "  WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    ") wl ON wl.log_date = d.day::date "
                    "WHERE EXTRACT(DOW FROM d.day) NOT IN (0, 6) "
                    "ORDER BY d.day"
                ),
            },
            # Step 5: 新建项目（销售用）
            {
                'as_name': 'new_projects',
                'description': '期间新建项目（销售角色用）',
                'sql': (
                    "SELECT p.project_name AS 项目名称, "
                    "p.project_type AS 类型, "
                    "p.current_stage AS 当前阶段, "
                    "p.end_user AS 终端用户, "
                    "p.created_at::date AS 创建日期 "
                    "FROM projects p "
                    "JOIN users u ON p.created_by = u.id "
                    "WHERE (u.real_name ILIKE '%' || {user_name} || '%' "
                    "   OR u.username ILIKE '%' || {user_name} || '%') "
                    "AND p.is_deleted = FALSE "
                    "AND p.created_at >= {period_start}::date "
                    "AND p.created_at < ({period_end}::date + INTERVAL '1 day') "
                    "ORDER BY p.created_at DESC"
                ),
            },
            # Step 6: 新建客户（销售用）
            {
                'as_name': 'new_customers',
                'description': '期间新建客户公司（销售角色用）',
                'sql': (
                    "SELECT co.company_name AS 公司名称, "
                    "co.company_type AS 类型, "
                    "co.country AS 国家, "
                    "co.created_at::date AS 创建日期 "
                    "FROM companies co "
                    "JOIN users u ON co.owner_id = u.id "
                    "WHERE (u.real_name ILIKE '%' || {user_name} || '%' "
                    "   OR u.username ILIKE '%' || {user_name} || '%') "
                    "AND co.is_deleted = FALSE "
                    "AND co.created_at >= {period_start}::date "
                    "AND co.created_at < ({period_end}::date + INTERVAL '1 day') "
                    "ORDER BY co.created_at DESC"
                ),
            },
            # Step 7: 新建联系人（销售用）
            {
                'as_name': 'new_contacts',
                'description': '期间新建联系人（销售角色用）',
                'sql': (
                    "SELECT c.name AS 姓名, "
                    "c.position AS 职位, "
                    "co.company_name AS 所属公司, "
                    "c.created_at::date AS 创建日期 "
                    "FROM contacts c "
                    "JOIN companies co ON c.company_id = co.id "
                    "JOIN users u ON c.owner_id = u.id "
                    "WHERE (u.real_name ILIKE '%' || {user_name} || '%' "
                    "   OR u.username ILIKE '%' || {user_name} || '%') "
                    "AND co.is_deleted = FALSE "
                    "AND c.created_at >= {period_start}::date "
                    "AND c.created_at < ({period_end}::date + INTERVAL '1 day') "
                    "ORDER BY c.created_at DESC"
                ),
            },
            # Step 8: 项目阶段推动（销售用）
            {
                'as_name': 'stage_changes',
                'description': '期间有阶段推动的项目（来自 project_stage_history，销售角色用）',
                'sql': (
                    "SELECT DISTINCT ON (sh.project_id, sh.from_stage, sh.to_stage, sh.change_date::date) "
                    "p.project_name AS 项目, "
                    "sh.from_stage AS 原阶段, "
                    "sh.to_stage AS 新阶段, "
                    "sh.change_date::date AS 变更日期, "
                    "LEFT(COALESCE(la.communication, ''), 100) AS 最近行动 "
                    "FROM project_stage_history sh "
                    "JOIN projects p ON sh.project_id = p.id "
                    "JOIN users u ON p.owner_id = u.id "
                    "LEFT JOIN LATERAL ( "
                    "  SELECT a.communication FROM actions a "
                    "  WHERE a.project_id = p.id "
                    "  ORDER BY a.date DESC, a.id DESC LIMIT 1 "
                    ") la ON true "
                    "WHERE (u.real_name ILIKE '%' || {user_name} || '%' "
                    "   OR u.username ILIKE '%' || {user_name} || '%') "
                    "AND sh.change_date >= {period_start}::date "
                    "AND sh.change_date < ({period_end}::date + INTERVAL '1 day') "
                    "AND sh.to_stage NOT IN ('lost', 'paused') "
                    "ORDER BY sh.project_id, sh.from_stage, sh.to_stage, sh.change_date::date, sh.id DESC "
                    "LIMIT 10"
                ),
            },
            # Step 9: 近期搁置/失败项目（销售用）
            {
                'as_name': 'lost_paused',
                'description': '期间变为搁置或失败的项目（销售角色用）',
                'sql': (
                    "SELECT DISTINCT ON (sh.project_id, sh.to_stage, sh.change_date::date) "
                    "p.project_name AS 项目, "
                    "CASE sh.to_stage WHEN 'lost' THEN '❌ 失败' ELSE '⏸ 搁置' END AS 结果, "
                    "sh.from_stage AS 原阶段, "
                    "sh.change_date::date AS 变更日期, "
                    "LEFT(COALESCE(sh.remarks, ''), 100) AS 备注 "
                    "FROM project_stage_history sh "
                    "JOIN projects p ON sh.project_id = p.id "
                    "JOIN users u ON p.owner_id = u.id "
                    "WHERE (u.real_name ILIKE '%' || {user_name} || '%' "
                    "   OR u.username ILIKE '%' || {user_name} || '%') "
                    "AND sh.change_date >= {period_start}::date "
                    "AND sh.change_date < ({period_end}::date + INTERVAL '1 day') "
                    "AND sh.to_stage IN ('lost', 'paused') "
                    "ORDER BY sh.project_id, sh.to_stage, sh.change_date::date, sh.id DESC "
                    "LIMIT 10"
                ),
            },
            # Step 10: 在途项目零行动风险（销售用，排除签约）
            {
                'as_name': 'risk_pipeline',
                'description': '在途项目零行动风险：排除 awarded/signed（销售角色用）',
                'sql': (
                    "SELECT p.project_name AS 项目, "
                    "p.current_stage AS 阶段 "
                    "FROM projects p "
                    "JOIN users u ON p.owner_id = u.id "
                    "LEFT JOIN ( "
                    "  SELECT a.project_id, COUNT(*) AS action_count "
                    "  FROM actions a "
                    "  WHERE a.date >= {period_start}::date AND a.date <= {period_end}::date "
                    "  GROUP BY a.project_id "
                    ") ac ON ac.project_id = p.id "
                    "WHERE (u.real_name ILIKE '%' || {user_name} || '%' "
                    "   OR u.username ILIKE '%' || {user_name} || '%') "
                    "AND p.is_deleted = FALSE "
                    "AND p.current_stage NOT IN ('lost', 'paused', 'signed', 'awarded') "
                    "AND COALESCE(ac.action_count, 0) = 0 "
                    "ORDER BY CASE p.current_stage "
                    "  WHEN 'tendering' THEN 1 WHEN 'pre_tender' THEN 2 "
                    "  WHEN 'embed' THEN 3 WHEN 'discover' THEN 4 ELSE 9 END "
                    "LIMIT 15"
                ),
            },
            # Step 11: 报价明细（销售用）
            {
                'as_name': 'quotations',
                'description': '期间报价明细（销售角色用）',
                'sql': (
                    "SELECT q.quotation_number AS 报价单号, "
                    "COALESCE(p.project_name, '-') AS 项目, "
                    "q.amount AS 金额, q.currency AS 货币, "
                    "q.approval_status AS 状态 "
                    "FROM quotations q "
                    "JOIN users u ON q.owner_id = u.id "
                    "LEFT JOIN projects p ON q.project_id = p.id "
                    "WHERE (u.real_name ILIKE '%' || {user_name} || '%' "
                    "   OR u.username ILIKE '%' || {user_name} || '%') "
                    "AND q.created_at >= {period_start}::date "
                    "AND q.created_at < ({period_end}::date + INTERVAL '1 day') "
                    "ORDER BY q.created_at DESC"
                ),
            },
            # Step 10: 绩效目标（销售用）
            {
                'as_name': 'perf_targets',
                'description': '绩效目标设定（销售角色用）',
                'sql': (
                    "SELECT COALESCE(pmd.metric_name, upt.item_code) AS 指标, "
                    "upt.annual_target_override AS 年度目标, "
                    "CASE EXTRACT(QUARTER FROM {period_end}::date) "
                    "  WHEN 1 THEN upt.q1_target_override "
                    "  WHEN 2 THEN upt.q2_target_override "
                    "  WHEN 3 THEN upt.q3_target_override "
                    "  WHEN 4 THEN upt.q4_target_override "
                    "END AS 本季度目标 "
                    "FROM user_performance_targets upt "
                    "JOIN users u ON upt.user_id = u.id "
                    "LEFT JOIN performance_metrics_definition pmd ON pmd.metric_code = upt.item_code "
                    "WHERE (u.real_name ILIKE '%' || {user_name} || '%' "
                    "   OR u.username ILIKE '%' || {user_name} || '%') "
                    "AND upt.year = EXTRACT(YEAR FROM {period_end}::date)::int "
                    "ORDER BY upt.item_code"
                ),
            },
            # Step 11: 季度累计实际（销售用）
            {
                'as_name': 'quarter_actual',
                'description': '本季度累计实际数据（销售角色用）',
                'sql': (
                    "WITH qr AS ( "
                    "  SELECT DATE_TRUNC('quarter', {period_end}::date)::date AS q_start, "
                    "         (DATE_TRUNC('quarter', {period_end}::date) + INTERVAL '3 months - 1 day')::date AS q_end "
                    ") "
                    "SELECT '报价总额' AS 指标, "
                    "ROUND((COALESCE(SUM(q.amount),0)/10000)::numeric,2) AS 本季度累计, '万元' AS 单位 "
                    "FROM quotations q JOIN users u ON q.owner_id=u.id CROSS JOIN qr "
                    "WHERE (u.real_name ILIKE '%' || {user_name} || '%' OR u.username ILIKE '%' || {user_name} || '%') "
                    "AND q.created_at >= qr.q_start AND q.created_at < qr.q_end + INTERVAL '1 day' "
                    "GROUP BY 1,3 "
                    "UNION ALL "
                    "SELECT '新建项目' AS 指标, COUNT(*)::numeric, '个' FROM projects p "
                    "JOIN users u ON p.created_by=u.id CROSS JOIN qr "
                    "WHERE (u.real_name ILIKE '%' || {user_name} || '%' OR u.username ILIKE '%' || {user_name} || '%') "
                    "AND p.is_deleted=FALSE AND p.created_at >= qr.q_start AND p.created_at < qr.q_end + INTERVAL '1 day' "
                    "GROUP BY 1,3 "
                    "UNION ALL "
                    "SELECT '新建客户' AS 指标, COUNT(DISTINCT co.id)::numeric, '个' FROM companies co "
                    "JOIN users u ON co.owner_id=u.id CROSS JOIN qr "
                    "WHERE (u.real_name ILIKE '%' || {user_name} || '%' OR u.username ILIKE '%' || {user_name} || '%') "
                    "AND co.is_deleted=FALSE AND co.created_at >= qr.q_start AND co.created_at < qr.q_end + INTERVAL '1 day' "
                    "GROUP BY 1,3"
                ),
            },
            # Step 12: 工作项统计（非销售用）
            {
                'as_name': 'task_stats',
                'description': '工作项按状态和类型统计（非销售角色用）',
                'sql': (
                    "SELECT "
                    "CASE wi.status "
                    "  WHEN 'completed' THEN '✓ 已完成' "
                    "  WHEN 'planned' THEN '待办' "
                    "  WHEN 'cancelled' THEN '已取消' "
                    "  ELSE wi.status END AS 状态, "
                    "COALESCE(wi.work_type, '其他') AS 类型, "
                    "COUNT(*) AS 数量 "
                    "FROM work_items wi "
                    "JOIN users u ON wi.owner_id = u.id "
                    "WHERE (u.real_name ILIKE '%' || {user_name} || '%' "
                    "   OR u.username ILIKE '%' || {user_name} || '%') "
                    "AND wi.planned_date >= {period_start}::date "
                    "AND wi.planned_date <= {period_end}::date "
                    "AND wi.is_deleted = FALSE "
                    "GROUP BY wi.status, wi.work_type "
                    "ORDER BY wi.status, wi.work_type"
                ),
            },
        ],
        'skill_body': _WORK_SUMMARY_RENDER,
    },

    # ------------------------------------------------------------------
    # 6. 销售人员周报分析（已被 work_summary 取代，保留数据结构）
    # ------------------------------------------------------------------
    {
        'name': 'sales_weekly_review',
        'title': '销售人员周报分析',
        'description': '生成指定销售人员的周度工作分析报告。触发词：周报、周报分析、上周周报、weekly review、销售周报。包含行动记录明细、每日活动分布、项目管线状态和报价活动。',
        'parameters': [
            {'name': 'user_name', 'type': 'string', 'required': True, 'description': '销售人员姓名'},
            {'name': 'period', 'type': 'period', 'required': True, 'default_value': 'last_week', 'description': '统计周期'},
        ],
        'queries': [
            # Step 1: 概览统计（一行汇总）
            {
                'as_name': 'summary',
                'description': '周度概览统计',
                'sql': (
                    "SELECT "
                    "(SELECT COUNT(*) FROM actions a JOIN users u ON a.owner_id=u.id "
                    "  WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    "  AND a.date >= {period_start}::date AND a.date <= {period_end}::date) AS 行动记录数, "
                    "(SELECT COUNT(DISTINCT a.date) FROM actions a JOIN users u ON a.owner_id=u.id "
                    "  WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    "  AND a.date >= {period_start}::date AND a.date <= {period_end}::date) AS 活跃天数, "
                    "(SELECT COUNT(*) FROM quotations q JOIN users u ON q.owner_id=u.id "
                    "  WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    "  AND q.created_at >= {period_start}::date AND q.created_at < ({period_end}::date + INTERVAL '1 day')) AS 报价数, "
                    "(SELECT COALESCE(SUM(q.amount),0) FROM quotations q JOIN users u ON q.owner_id=u.id "
                    "  WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    "  AND q.created_at >= {period_start}::date AND q.created_at < ({period_end}::date + INTERVAL '1 day')) AS 报价总额, "
                    "(SELECT COUNT(*) FROM projects p JOIN users u ON p.owner_id=u.id "
                    "  WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    "  AND p.is_deleted=FALSE AND p.current_stage NOT IN ('lost','paused','signed')) AS 活跃项目数"
                ),
            },
            # Step 2: 行动记录明细（加类型列）
            {
                'as_name': 'actions',
                'description': '周期内行动记录明细',
                'sql': (
                    "SELECT a.date AS 日期, "
                    "COALESCE(co.company_name, '-') AS 客户, "
                    "COALESCE(p.project_name, '-') AS 项目, "
                    "LEFT(a.communication, 150) AS 内容摘要 "
                    "FROM actions a "
                    "JOIN users u ON a.owner_id = u.id "
                    "LEFT JOIN companies co ON a.company_id = co.id "
                    "LEFT JOIN projects p ON a.project_id = p.id "
                    "WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    "AND a.date >= {period_start}::date "
                    "AND a.date <= {period_end}::date "
                    "ORDER BY a.date, a.id"
                ),
            },
            # Step 3: 每日活动分布（加日志状态）
            {
                'as_name': 'daily',
                'description': '每日行动分布+日志状态',
                'sql': (
                    "SELECT d.day::date AS 日期, "
                    "COALESCE(ac.action_count, 0) AS 行动数, "
                    "COALESCE(wi.item_count, 0) AS 工作项数, "
                    "COALESCE(wl.log_status, '无') AS 日志状态, "
                    "CASE WHEN COALESCE(ac.action_count,0)=0 AND COALESCE(wi.item_count,0)=0 THEN '空白' "
                    "     WHEN COALESCE(ac.action_count,0)>0 THEN '活跃' ELSE '仅工作项' END AS 备注 "
                    "FROM generate_series({period_start}::date, {period_end}::date, '1 day'::interval) d(day) "
                    "LEFT JOIN ( "
                    "  SELECT a.date, COUNT(*) AS action_count "
                    "  FROM actions a JOIN users u ON a.owner_id = u.id "
                    "  WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    "  GROUP BY a.date "
                    ") ac ON ac.date = d.day::date "
                    "LEFT JOIN ( "
                    "  SELECT wi.planned_date, COUNT(*) AS item_count "
                    "  FROM work_items wi JOIN users u ON wi.owner_id = u.id "
                    "  WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    "  GROUP BY wi.planned_date "
                    ") wi ON wi.planned_date = d.day::date "
                    "LEFT JOIN ( "
                    "  SELECT wl.log_date, wl.status AS log_status "
                    "  FROM worklogs wl JOIN users u ON wl.owner_id = u.id "
                    "  WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    ") wl ON wl.log_date = d.day::date "
                    "WHERE EXTRACT(DOW FROM d.day) NOT IN (0, 6) "
                    "ORDER BY d.day"
                ),
            },
            # Step 4: 项目管线（只显示本周有行动的 + 招标/标前阶段零行动的风险项）
            {
                'as_name': 'pipeline',
                'description': '重点项目管线（有行动+风险项）',
                'sql': (
                    "SELECT p.project_name AS 项目, "
                    "p.current_stage AS 阶段, "
                    "p.status AS 状态, "
                    "COALESCE(ac.action_count, 0) AS 本周行动数, "
                    "CASE WHEN COALESCE(ac.action_count,0)=0 AND p.current_stage IN ('tendering','pre_tender','awarded') "
                    "     THEN '⚠ 零行动' "
                    "     WHEN COALESCE(ac.action_count,0)>0 THEN '✓ 有跟进' "
                    "     ELSE '-' END AS 本周进展 "
                    "FROM projects p "
                    "JOIN users u ON p.owner_id = u.id "
                    "LEFT JOIN ( "
                    "  SELECT a.project_id, COUNT(*) AS action_count "
                    "  FROM actions a "
                    "  WHERE a.date >= {period_start}::date AND a.date <= {period_end}::date "
                    "  GROUP BY a.project_id "
                    ") ac ON ac.project_id = p.id "
                    "WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    "AND p.is_deleted = FALSE "
                    "AND p.current_stage NOT IN ('lost', 'paused', 'signed') "
                    "AND (COALESCE(ac.action_count,0) > 0 "
                    "     OR p.current_stage IN ('tendering','pre_tender','awarded')) "
                    "ORDER BY CASE p.current_stage "
                    "  WHEN 'awarded' THEN 1 WHEN 'tendering' THEN 2 "
                    "  WHEN 'pre_tender' THEN 3 WHEN 'embed' THEN 4 "
                    "  WHEN 'discover' THEN 5 ELSE 9 END, "
                    "COALESCE(ac.action_count,0) DESC"
                ),
            },
            # Step 5: 报价明细
            {
                'as_name': 'quotations',
                'description': '周期内报价明细',
                'sql': (
                    "SELECT q.quotation_number AS 报价单号, "
                    "COALESCE(p.project_name, '-') AS 项目, "
                    "q.amount AS 金额, "
                    "q.currency AS 货币, "
                    "q.approval_status AS 状态 "
                    "FROM quotations q "
                    "JOIN users u ON q.owner_id = u.id "
                    "LEFT JOIN projects p ON q.project_id = p.id "
                    "WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    "AND q.created_at >= {period_start}::date "
                    "AND q.created_at < ({period_end}::date + INTERVAL '1 day') "
                    "ORDER BY q.created_at DESC"
                ),
            },
            # Step 6: 绩效目标（从 user_performance_targets 动态读取）
            {
                'as_name': 'targets',
                'description': '被评估人的绩效目标',
                'sql': (
                    "SELECT COALESCE(pmd.metric_name, upt.item_code) AS 指标, "
                    "upt.annual_target_override AS 年度目标, "
                    "CASE EXTRACT(QUARTER FROM {period_end}::date) "
                    "  WHEN 1 THEN upt.q1_target_override "
                    "  WHEN 2 THEN upt.q2_target_override "
                    "  WHEN 3 THEN upt.q3_target_override "
                    "  WHEN 4 THEN upt.q4_target_override "
                    "END AS 本季度目标 "
                    "FROM user_performance_targets upt "
                    "JOIN users u ON upt.user_id = u.id "
                    "LEFT JOIN performance_metrics_definition pmd ON pmd.metric_code = upt.item_code "
                    "WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    "AND upt.year = EXTRACT(YEAR FROM {period_end}::date)::int "
                    "ORDER BY upt.item_code"
                ),
            },
            # Step 7: 本季度累计实际（对比目标用）
            {
                'as_name': 'quarter_actual',
                'description': '本季度累计实际数据',
                'sql': (
                    "WITH quarter_range AS ( "
                    "  SELECT DATE_TRUNC('quarter', {period_end}::date)::date AS q_start, "
                    "         (DATE_TRUNC('quarter', {period_end}::date) + INTERVAL '3 months' - INTERVAL '1 day')::date AS q_end "
                    ") "
                    "SELECT COALESCE(pmd.metric_name, 'sales_target') AS 指标, "
                    "ROUND((COALESCE(SUM(q.amount),0)/10000)::numeric, 2) AS 本季度累计, "
                    "COALESCE(pmd.default_unit, '万元') AS 单位 "
                    "FROM quotations q "
                    "JOIN users u ON q.owner_id = u.id "
                    "CROSS JOIN quarter_range qr "
                    "LEFT JOIN performance_metrics_definition pmd ON pmd.metric_code = 'sales_target' "
                    "WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    "AND q.created_at >= qr.q_start AND q.created_at < qr.q_end + INTERVAL '1 day' "
                    "GROUP BY pmd.metric_name, pmd.default_unit "
                    "UNION ALL "
                    "SELECT COALESCE(pmd2.metric_name, 'new_projects'), COUNT(*)::numeric, COALESCE(pmd2.default_unit, '个') "
                    "FROM projects p "
                    "JOIN users u ON p.created_by = u.id "
                    "CROSS JOIN quarter_range qr "
                    "LEFT JOIN performance_metrics_definition pmd2 ON pmd2.metric_code = 'new_projects' "
                    "WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    "AND p.is_deleted = FALSE "
                    "AND p.created_at >= qr.q_start AND p.created_at < qr.q_end + INTERVAL '1 day' "
                    "GROUP BY pmd2.metric_name, pmd2.default_unit "
                    "UNION ALL "
                    "SELECT COALESCE(pmd3.metric_name, 'new_customers'), COUNT(DISTINCT co.id)::numeric, COALESCE(pmd3.default_unit, '个') "
                    "FROM companies co "
                    "JOIN users u ON co.owner_id = u.id "
                    "CROSS JOIN quarter_range qr "
                    "LEFT JOIN performance_metrics_definition pmd3 ON pmd3.metric_code = 'new_customers' "
                    "WHERE u.real_name ILIKE '%' || {user_name} || '%' "
                    "AND co.is_deleted = FALSE "
                    "AND co.created_at >= qr.q_start AND co.created_at < qr.q_end + INTERVAL '1 day' "
                    "GROUP BY pmd3.metric_name, pmd3.default_unit"
                ),
            },
        ],
        'output_format': (
            "## {user_name} 销售周报 ({period_start} ~ {period_end})\n\n"
            "### 概览\n{summary.table}\n\n"
            "### 1. 行动记录明细 ({actions.count}条)\n"
            "{if actions}{actions.table}{endif}"
            "{if !actions}本周无行动记录。{endif}\n\n"
            "### 2. 每日活动分布\n{daily.table}\n\n"
            "### 3. 项目管线（重点项目）\n"
            "{if pipeline}{pipeline.table}{endif}"
            "{if !pipeline}暂无重点项目。{endif}\n\n"
            "### 4. 本周报价 ({quotations.count}份)\n"
            "{if quotations}{quotations.table}{endif}"
            "{if !quotations}本周无新报价。{endif}\n\n"
            "### 5. 绩效目标达成进度\n"
            "{if targets}**个人目标设定:**\n{targets.table}\n\n"
            "**本季度累计实际:**\n{quarter_actual.table}{endif}"
            "{if !targets}暂无绩效目标数据。{endif}\n\n"
            "---\n"
            "### 6. 分析与风险提示\n"
            "请基于以上数据，从以下维度给出简要分析（每条1-2句话）：\n"
            "- **活跃度评估**：本周行动天数/总工作日，是否有连续空白日\n"
            "- **项目风险**：招标中/标前/已中标阶段零行动的项目数量及风险\n"
            "- **报价进展**：报价数量和金额是否匹配季度目标节奏\n"
            "- **绩效差距**：本季度累计 vs 季度目标的达成率，哪些指标落后\n"
            "- **重点关注**：需要立即跟进的项目或客户\n"
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

    特殊逻辑:
    - 当 work_summary 成功注册时,自动将 sales_weekly_review 标为 is_active=False。
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
            skill_body=skill_def.get('skill_body'),
            scope='global',
        )
        db.session.add(skill)
        added.append(name)

    if added:
        db.session.commit()
        logger.info(f'[BuiltinSkills] 注册了 {len(added)} 个内置 Skill: {added}')

        # work_summary 上线后，自动停用被替代的 sales_weekly_review
        if 'work_summary' in added:
            old = CliSkill.query.filter_by(name='sales_weekly_review').first()
            if old and old.is_active:
                old.is_active = False
                db.session.commit()
                logger.info('[BuiltinSkills] sales_weekly_review 已自动停用（被 work_summary 取代）')
    else:
        logger.debug('[BuiltinSkills] 所有内置 Skill 已存在,无需注册')
