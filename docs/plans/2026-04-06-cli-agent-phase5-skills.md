# PMA CLI Agent 阶段 5 — Skill 系统

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让用户和 AI 在对话中创建可复用的业务查询 Skill，确保同样的问题永远得到一致、准确的结果。

**Architecture:** Skill 存储在数据库（`cli_skills` 表），通过 `invoke_skill` 工具调用。每个 Skill 包含预定义的 SQL 模板和输出格式，LLM 只负责意图识别和参数填充。支持 AI 对话中创建 Skill（`save_skill` 工具）。

**Tech Stack:** PostgreSQL JSONB, Flask Blueprint, 现有 ToolRegistry 扩展

---

### Task 1: Skill 数据模型

**Files:**
- Create: `app/models/cli_skill.py`
- Create: `migrations/versions/c1i5ki110001_add_cli_skills_table.py`

**模型字段:**
```python
class CliSkill(db.Model):
    __tablename__ = 'cli_skills'
    
    id            = Column(Integer, primary_key=True)
    name          = Column(String(80), unique=True, nullable=False)   # 英文标识: sales_activity_report
    title         = Column(String(120), nullable=False)               # 中文标题: 销售行动力分析
    description   = Column(Text, nullable=False)                      # 描述 + 触发词
    parameters    = Column(JSONB, default=list)                       # [{name, type, required, default, description}]
    queries       = Column(JSONB, nullable=False)                     # [{sql, as_name, description}]
    output_format = Column(Text)                                      # Markdown 模板，用 {step_name.field} 引用
    scope         = Column(String(20), default='global')              # global / team / personal
    is_active     = Column(Boolean, default=True)
    created_by    = Column(Integer, ForeignKey('users.id'))
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

### Task 2: Skill 执行引擎

**Files:**
- Create: `app/services/cli_agent/skill_engine.py`

**职责:**
1. 加载 Skill 定义
2. 填充 SQL 模板参数（安全参数化，防注入）
3. 按顺序执行多条 SQL，前一步结果可传给后一步
4. 用 output_format 模板格式化最终结果

```python
class SkillEngine:
    def execute(skill: CliSkill, params: dict, user) -> dict:
        """执行一个 Skill，返回格式化结果"""
        results = {}
        for query_def in skill.queries:
            sql = _render_sql(query_def['sql'], params, results)
            rows = execute_safe_query(sql, user)
            results[query_def['as_name']] = rows
        
        output = _render_output(skill.output_format, results, params)
        return {'formatted_output': output, 'raw_results': results}
```

参数安全处理：
- 字符串参数：自动转义单引号 + ILIKE 包裹
- 日期参数：解析 `last_week` / `last_month` 为具体日期范围
- 数字参数：强制类型转换

---

### Task 3: invoke_skill 工具

**Files:**
- Create: `app/services/cli_agent/tools/invoke_skill.py`
- Modify: `app/services/cli_agent/tools/__init__.py`（注册）

**工具定义:**
```python
name = 'invoke_skill'
description = '调用预定义的业务 Skill。当用户请求匹配已有 Skill 时优先使用，比 query_pma_database 更准确。'
input_schema = {
    "type": "object",
    "properties": {
        "skill_name": {"type": "string", "description": "Skill 标识名"},
        "parameters": {"type": "object", "description": "Skill 参数键值对"}
    },
    "required": ["skill_name"]
}
```

---

### Task 4: save_skill 工具（AI 对话中创建 Skill）

**Files:**
- Create: `app/services/cli_agent/tools/save_skill.py`
- Modify: `app/services/cli_agent/tools/__init__.py`（注册）

**工具定义:**
```python
name = 'save_skill'
description = '创建或更新一个业务 Skill。当用户说"帮我做一个Skill"或"保存这个查询为模板"时使用。'
input_schema = {
    "type": "object",
    "properties": {
        "name":          {"type": "string"},
        "title":         {"type": "string"},
        "description":   {"type": "string"},
        "parameters":    {"type": "array"},
        "queries":       {"type": "array"},
        "output_format": {"type": "string"}
    },
    "required": ["name", "title", "queries"]
}
```

**权限:** 仅 admin 可创建 global Skill，普通用户只能创建 personal Skill。

---

### Task 5: 提示词集成

**Files:**
- Modify: `app/services/cli_agent/prompt_builder.py`

**改动:**
1. 在动态段注入可用 Skill 列表
2. 更新路由规则：优先匹配 Skill → 其次 query_pma_database → 最后 web_search

```python
def _skill_section(user) -> str:
    """从数据库加载当前用户可用的 Skill，生成提示描述"""
    skills = CliSkill.query.filter(
        CliSkill.is_active == True,
        or_(CliSkill.scope == 'global', CliSkill.created_by == user.id)
    ).all()
    if not skills:
        return ''
    lines = ['[可用 Skill（优先使用 invoke_skill 调用）]']
    for s in skills:
        params = ', '.join(p['name'] for p in (s.parameters or []))
        lines.append(f'- {s.name}: {s.title}（参数: {params or "无"}）')
    return '\n'.join(lines)
```

路由规则更新：
```
3. **路由清晰** — 先检查是否匹配已有 Skill → invoke_skill；
   PMA 内部数据 → query_pma_database；
   外部公开信息 → web_search；
   创建 Skill → save_skill；闲聊 → 婉拒。
```

---

### Task 6: 内置首批 Skill

**Files:**
- Create: `app/services/cli_agent/builtin_skills.py`

**5 个首批 Skill（应用启动时写入数据库，已存在则跳过）:**

1. **sales_activity_report** — 销售行动力分析
   - 参数: period (last_week/last_month)
   - 3 条 SQL: 新建项目数 + 报价金额 + 行动记录数，按销售人员分组

2. **customer_overview** — 客户全景
   - 参数: company_name
   - 4 条 SQL: 公司基本信息 + 联系人 + 关联项目 + 报价汇总

3. **project_detail** — 项目详情
   - 参数: project_name
   - 4 条 SQL: 项目基本信息 + 报价列表 + 阶段变更历史 + 行动记录

4. **pipeline_analysis** — 项目管线分析
   - 参数: owner (可选)
   - 1 条 SQL: 按阶段分组统计项目数和金额

5. **weekly_summary** — 周报数据汇总
   - 参数: user_name, period
   - 4 条 SQL: 新建项目 + 报价 + 行动记录 + 工作项

---

### Task 7: Skill 管理 API

**Files:**
- Modify: `app/views/cli.py`（新增 API 端点）

```
GET  /cli/api/skills              列出当前用户可用的 Skill
POST /cli/api/skills              创建 Skill（admin only for global）
GET  /cli/api/skills/:id          获取 Skill 详情
PUT  /cli/api/skills/:id          更新 Skill
DELETE /cli/api/skills/:id        删除 Skill
```

---

### 验证方式

1. `/new` 新开会话，问"上周销售行动力分析" → 应调用 invoke_skill 而非 query_pma_database
2. 同样问题重复问 3 次 → 结果完全一致
3. 问"华为技术的客户全景" → 调用 customer_overview Skill
4. 对话中说"帮我做一个 Skill，统计每月各部门的报销总额" → AI 调用 save_skill 创建
5. 再次问"上月各部门报销汇总" → 调用刚创建的 Skill
