# PMA 项目开发规则 - Claude AI 助手指南

## 📚 文档结构

本规则文档已拆分为多个专门文件，便于查找和维护：

### **📖 主要规则文档**
- **CLAUDE.md** (本文件) - 核心原则和基础规范
- **CLAUDE-I18N.md** - 翻译与国际化规范
- **CLAUDE-COMPONENTS.md** - Bootstrap 组件和UI规范
- **CLAUDE-TW-COMPONENTS.md** - Tailwind 组件规范
- **CLAUDE-JS-TOOLS.md** - JavaScript可复用工具索引
- **CLAUDE-DATABASE.md** - 数据库备份和迁移规范
- **CLAUDE-SCRIPTS.md** - 脚本创建与管理规范
- **CLAUDE-CODE-QUALITY.md** - 代码质量与重构规范
- **CLAUDE-LOCKING.md** - 审批锁定统一规范(Lockable Protocol)
- **CLAUDE-INVENTORY.md** - 库存系统设计规范(厂商 vs 客户仓库)

### **📋 使用说明**
- **Claude AI助手**: 需要时请主动读取相应的专门规范文件
- **开发人员**: 根据具体需求查阅对应文档
- **更新维护**: 各专门规范独立更新，降低冲突

---

## 🎯 核心原则

### **优先级排序**
1. **数据安全** - 永不删除或损坏现有数据
2. **通用组件保护** - 严禁随意修改通用模组，必须遵循保护协议
3. **工具复用优先** - 实现功能前必须先检查 CLAUDE-JS-TOOLS.md 是否有可复用工具
4. **一致性** - 所有功能必须遵循统一标准
5. **国际化** - 支持中英文切换
6. **用户体验** - 简洁、直观、响应快速
7. **代码质量** - 可维护、可扩展、有文档

---

## 🎨 模板体系规范（Bootstrap → Tailwind 迁移）

### **核心规则**
- ✅ **所有新页面必须使用 Tailwind (`tw_*.html`) 模板**
- ✅ **参考现有 tw_ 模板的模式和组件用法**
- ❌ **禁止参考 `_archived/bootstrap/` 中的旧 Bootstrap 模板**
- ❌ **禁止在路由中添加 `tw=1` 条件切换逻辑**

### **已完成迁移的模块**
以下模块的列表和详情页已全面使用 Tailwind 模板，旧 Bootstrap 版本已归档到 `app/templates/_archived/bootstrap/`：
- Customer（联系人视图）
- Expense（列表 + 详情）
- User（列表 + 详情 + 部门管理 + 个人资料）
- Project（列表 + 详情）
- Quotation（列表 + 详情）
- Product（列表 + 详情）
- Approval（审批中心）
- Pricing Order（列表 + 详情）
- Product Analysis（分析仪表板）
- Backup（备份管理）

### **仍为 Bootstrap 的页面（C类 - 暂无 tw_ 版本）**
以下页面仍使用 Bootstrap，属于正常状态（未迁移），不需要归档：
- 所有表单页面：`project/add.html`、`project/edit.html`、`expense/create_expense.html`、`quotation/edit_new.html` 等
- Inventory 模块全部页面
- Admin 和权限管理页面
- Auth 页面（登录、注册）

### **`.claudeignore` 屏蔽配置**
`app/templates/_archived/` 和 `app/routes/project.py`（死代码）已加入 `.claudeignore`，AI 搜索时自动跳过。

---

## 🔒 通用组件保护协议

### **受保护文件列表**
- `app/templates/macros/ui_helpers.html` - 通用UI组件模板
- `app/static/js/data-list.js` - 通用数据列表组件
- `app/static/js/filter-search.js` - 通用筛选搜索组件
- `app/static/css/style.css` (通用组件相关样式) - 通用组件CSS样式

### **修改协议**
**禁止**直接修改上述通用组件文件。如需修改，必须：

1. **风险评估** - 详细分析修改对整个系统的影响范围
2. **获得授权** - 必须获得项目负责人明确同意
3. **充分测试** - 在多个使用该组件的页面进行测试验证
4. **记录修改** - 在 `UNIVERSAL_COMPONENTS_CHANGELOG.md` 中详细记录
5. **代码审查** - 修改后进行代码审查确认

### **替代方案**
- 优先考虑通过配置参数实现需求
- 创建专用组件而非修改通用组件
- 使用CSS覆盖而非修改通用样式

---

## 🔧 JavaScript可复用工具规范

**详细索引请参阅**: [CLAUDE-JS-TOOLS.md](./CLAUDE-JS-TOOLS.md)

### **强制检查机制**

**⚠️ 在以下情况下，Claude AI 必须先检查 CLAUDE-JS-TOOLS.md**：

#### **1. 实现新功能前**
```
需求：实现下拉选择器、搜索框、数据列表等通用功能
↓
步骤1: 必须先查阅 CLAUDE-JS-TOOLS.md 快速索引表
↓
步骤2: 如有可复用工具 → 直接使用
       如无可复用工具 → 评估是否值得创建通用工具
```

**示例场景**：
- ✅ 需要选择用户 → 查找 `*-selector.js` 类工具
- ✅ 需要搜索功能 → 查找 `*-search.js` 类工具
- ✅ 需要数据展示 → 查找 `data-list.js`, `filter-search.js`
- ✅ 需要地区选择 → 查找 `area-selector.js`, `country-region-selector.js`

#### **2. 发现重复代码时**
```
发现：2个及以上页面有相似的JavaScript逻辑（>50行 或 复制粘贴的代码）
↓
必须：主动建议重构为可复用工具
↓
重构后：立即更新 CLAUDE-JS-TOOLS.md
```

**重复代码识别标准**（参见 CLAUDE-CODE-QUALITY.md）：
- 2次及以上出现的相同逻辑
- 15行以上的相似代码块
- 复制粘贴后仅修改少量参数的代码

#### **3. 创建新的可复用工具后**
```
创建工具后的强制步骤（不可省略）：
1. 在 CLAUDE-JS-TOOLS.md 快速索引表中添加一行
2. 在详细文档章节添加完整文档（使用模板）
3. 包含：功能描述、API文档、使用示例、已使用页面
```

### **工具创建标准**

满足以下**任一条件**即应创建可复用工具：

| 条件 | 说明 | 示例 |
|-----|------|------|
| ✅ **重复代码** | 相同逻辑在2个及以上页面出现 | `vendor-sales-manager-selector.js` 重构案例 |
| ✅ **代码量大** | 单个功能逻辑超过50行且具有通用性 | `product-selector.js` 四级联动 |
| ✅ **复用潜力** | 未来可能在其他页面使用 | 审批流程、明细管理等 |
| ✅ **业务通用** | 跨模块的通用业务逻辑 | 客户搜索、项目搜索等 |

### **文档更新模板**

每次创建新工具后，按以下格式在 `CLAUDE-JS-TOOLS.md` 中添加文档：

```markdown
#### 工具名称.js

**基本信息**
- **文件路径**: `app/static/js/xxx.js`
- **功能描述**: 一句话描述
- **使用场景**: 何时使用此工具

**已使用页面**
1. `路径/页面.html` - 页面说明
2. ...

**API文档**
```javascript
functionName(param1, param2, options)
```

**参数说明**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|

**使用示例**
```html
<!-- 完整的代码示例 -->
```

**创建日期**: YYYY-MM-DD
```

### **检查清单**

实现JavaScript功能时的检查清单：

- [ ] ✅ 已查阅 `CLAUDE-JS-TOOLS.md` 快速索引表
- [ ] ✅ 如有可复用工具，已直接使用而非重新实现
- [ ] ✅ 如发现重复代码，已建议或完成重构
- [ ] ✅ 如创建新工具，已更新 `CLAUDE-JS-TOOLS.md` 文档
- [ ] ✅ 新工具文档包含完整的API和使用示例

### **重构案例参考**

**案例**: `vendor-sales-manager-selector.js` 重构

- **重构前**: `project/add.html` (70行) + `project/edit.html` (95行) = 165行重复代码
- **重构后**: 公共工具 (134行) + 调用代码 (14行) = 148行
- **净减少**: 17行代码
- **消除重复**: 100% (165行重复代码完全消除)
- **可维护性**: 修改逻辑只需改一处
- **可扩展性**: 未来其他页面可直接复用

详细重构过程参见 `CLAUDE-CODE-QUALITY.md`

---

## 🔄 智能合并功能权限规范

### **角色权限配置**
- **管理员 (admin)**: 可访问所有客户数据的智能合并功能
- **商务助理 (business_admin)**: 仅可访问权限范围内客户数据的智能合并功能

### **API端点权限要求**
智能合并相关API端点统一使用`@permission_required('customer', 'view')`权限：
- `/api/debug-normalize` - 数据标准化调试
- `/api/detect-duplicates` - 重复客户检测
- `/api/merge-preview` - 合并预览
- `/api/execute-merge` - 执行合并

### **数据访问控制原则**
- **数据归属限制**: 商务助理只能操作其权限范围内的客户数据
- **公司范围限制**: 基于用户所属公司进行数据过滤
- **部门权限限制**: 基于用户部门管理权限进行数据控制
- **所有者权限验证**: 确保用户只能合并其有权访问的客户记录

### **权限控制实现机制**
智能合并功能的所有API端点均已实现基于数据归属的权限控制：

#### **数据查询权限控制**
```python
# 使用get_viewable_data函数过滤用户可查看的数据（包含完整的权限级别和共享机制）
from app.utils.access_control import get_viewable_data
companies_query = get_viewable_data(Company, current_user, [Company.is_deleted == False])
companies = companies_query.all()
```

#### **操作权限验证**
```python
# 使用can_view_company函数验证具体记录访问权限
from app.utils.access_control import can_view_company
if not can_view_company(current_user, target_company):
    return jsonify({'success': False, 'message': '您没有权限访问目标客户'}), 403
```

#### **权限级别说明**
- **system级权限**: 可查看所有客户数据（管理员默认拥有）
- **company级权限**: 可查看同公司所有用户创建的客户数据
- **department级权限**: 可查看同部门同公司用户创建的客户数据  
- **personal级权限**: 可查看自己创建的客户数据 + 共享给自己的数据 + 归属关系授权的数据

#### **数据访问范围**
商务助理的数据访问范围包括：
1. **自己创建的客户数据** - 通过owner_id字段控制
2. **共享给自己的客户数据** - 通过shared_with_users字段和共享机制
3. **归属关系授权的数据** - 通过Affiliation表的上下级关系
4. **联系人级别的访问权限** - 创建联系人即可查看对应公司数据
5. **权限级别范围内的数据** - 根据company/department/personal级别过滤

#### **已实现的权限控制点**
1. **重复检测API** (`/api/detect-duplicates`): 仅检测用户权限范围内的重复客户
2. **合并预览API** (`/api/merge-preview`): 验证目标和源客户的访问权限
3. **执行合并API** (`/api/execute-merge`): 验证所有相关客户的操作权限
4. **调试标准化API** (`/api/debug-normalize`): 仅显示用户可访问的客户数据

---

## 🌍 翻译与国际化规则

**详细规范请参阅**: [CLAUDE-I18N.md](./CLAUDE-I18N.md)

### **核心原则**
- ✅ **所有配置文本使用中文作为 msgid**
- ✅ **英文作为翻译值存储在 messages.po 中**
- ❌ **禁止在 Python 代码中硬编码英文字符串**
- ❌ **禁止在模板中硬编码英文文本**
- ✅ **优先使用标准映射而非翻译系统**

### **常用操作**
```bash
# 编译翻译文件
pybabel compile -d app/translations

# 提取新的翻译文本
pybabel extract -F babel.cfg -k _l -o messages.pot .
pybabel update -i messages.pot -d app/translations
```

---

## 📄 页面结构与组件规范

**详细规范请参阅**: [CLAUDE-COMPONENTS.md](./CLAUDE-COMPONENTS.md)

### **核心要求**
- **页面结构**：主要功能页面使用 `page-with-fixed-nav` 结构，简单表单使用 `container mt-4` 结构
- **按钮组件**：必须使用 `render_button()` 和 `render_confirm_cancel()` 组件
- **筛选搜索**：必须使用 `render_filter_search_form()` 组件，遵循统一配置格式
- **徽章组件**：必须使用已定义的徽章宏，禁止直接编写HTML
- **通用列表**：优先使用 `render_data_list()` 完整组件

### **必需的 CSS 类**
- `page-with-fixed-nav` - 主要功能页面的根容器
- `page-header-with-actions` - 页面头部区域
- `btn-toolbar justify-content-end` - 操作按钮容器
- `d-grid gap-2 d-md-flex justify-content-md-end` - 表单按钮容器

---

## 🗂️ 数据库与模型规则

**详细规范请参阅**: [CLAUDE-DATABASE.md](./CLAUDE-DATABASE.md)

### **字段规范**
- **时间字段**：使用 UTC 存储，显示时转换为本地时间
- **金额字段**：数据库存储分（整数），显示时除以100转换为元
- **大金额显示**：除以10000显示为万元，格式化为2位小数
- **软删除**：使用 `is_deleted` 布尔字段，默认 `False`

### **查询规范**
```python
# 正确 ✅ - 排除已删除记录
query = Model.query.filter(Model.is_deleted == False)

# 正确 ✅ - 金额转换
total_amount = order.total_amount / 10000  # 转换为万元
```

### **备份工具**
- **通用备份**: `python3 backup_current_database.py` (独立 CLI，从 DATABASE_URL 读取配置)
- **Web 管理**: `/backup/` 页面 (Tailwind 版，含自动备份 + 清理 + 通知)

### **迁移升级工具**
- **SP8D标准升级**: `python3 standard_migration_upgrade.py`
- **OVS标准升级**: `python3 standard_migration_upgrade_ovs.py`
- **冲突修复**: `python3 fix_migration_conflicts.py`

---

## 🔒 权限与安全规则

### **权限检查**
- 所有路由必须使用 `@permission_required` 装饰器
- 模板中使用 `{% if has_permission('module', 'action') %}`
- API 端点必须验证 CSRF token

### **报销单特殊权限规则**

**重要**: 报销单（Expense）的权限控制与业务数据（Customer、Project等）**完全不同**，不使用数据归属机制。

#### **原则**
- 报销单属于**个人财务数据**，涉及财务隐私保护
- **禁止**使用公司级或部门级的数据归属共享机制
- 仅允许基于角色和审批流程的访问控制

#### **访问权限规则**
```python
# 在 app/utils/access_control.py 中的实现

1. 财务、管理员、CEO：可以查看所有报销单
   - 角色: finance_director, finace_director, finance, admin, ceo
   - 用途: 财务审核、管理监督

2. 普通用户：只能查看自己和直属下属的报销单
   - 自己的报销单: 通过 owner_id 匹配
   - 直属下属的报销单: 通过 Affiliation 表查询一级下属
   - 用途: 个人报销管理、审批流程需要
```

#### **与业务数据的区别**

| 数据类型 | 权限机制 | 共享范围 | 原因 |
|---------|---------|---------|------|
| **报销单 (Expense)** | 基于角色和审批关系 | 自己 + 直属下属 + 财务/管理员 | 财务隐私保护 |
| **客户 (Customer)** | 数据归属机制 | 公司/部门/个人级别 + 共享 | 业务协作需要 |
| **项目 (Project)** | 数据归属机制 | 公司/部门/个人级别 + 共享 | 业务协作需要 |
| **报价 (Quotation)** | 数据归属机制 | 公司/部门/个人级别 + 共享 | 业务协作需要 |

#### **代码实现位置**
- 文件: `app/utils/access_control.py`
- 函数: `get_viewable_data()`
- 特殊处理: 第580-622行

#### **注意事项**
- ❌ **禁止**将报销单改为使用数据归属机制
- ❌ **禁止**让同部门用户看到彼此的报销单
- ✅ **必须**保持基于角色和审批关系的权限控制
- ✅ **必须**确保只有财务和直属上级能看到他人报销单

### **数据验证**
- 所有用户输入必须验证和清理
- 数据库操作使用事务处理
- 敏感操作记录审计日志

---

## ☁️ 存储与部署架构

### **当前架构（2026-02起）**
- **Render.com** — 已停止（NAS 完全取代）
- **Supabase** — 已停止（数据库和文件存储均由 NAS 本地服务取代）
- **生产环境**: 中国 NAS (SP8D) + 新加坡 NAS (OVS)，各自运行 Docker Flask + PostgreSQL 17 + NAS WebDAV
- **外网访问**: Cloudflare Tunnel

### **数据库类型标识**
环境变量 `PMA_DB_TYPE` 用于标识数据库类型（兼容旧变量名 `SUPABASE_DB_TYPE`）：
- `sp8d` → 人民币/万元，中国 NAS
- `ovs` → 美元/M，新加坡 NAS

### **文件存储**
所有文件存储使用 NAS WebDAV（发票、产品图片、会议录音等），不再使用 Supabase Storage。
- 中国 NAS: `FORCE_LOCAL_STORAGE=true`, `PMA_DB_TYPE=sp8d`
- 新加坡 NAS: `FORCE_LOCAL_STORAGE=true`, `PMA_DB_TYPE=ovs`

### **启动方式**
```bash
# 统一启动脚本（推荐）
./start.sh

# 交互式选择:
#  1. 自动检测数据库配置
#  2. 选择文件存储方式（本地/NAS WebDAV）
#  3. 显示完整配置摘要
#  4. 确认后启动

# 快速启动（使用默认配置：本地数据库 + 本地存储）
python run.py
```

---

## 📁 文件组织规范

### **根目录规则**

**✅ 只允许以下类型的文件存在于根目录**：

#### 1. **核心运维脚本** (.sh)
- `start.sh` - 统一启动脚本（交互式选择数据库和存储配置）
- `upgrade_*.sh` - 数据库升级脚本
- `deploy_*.sh` - 部署相关脚本
- `execute_*.sh` - 执行脚本

#### 2. **环境配置文件**
- `.env.*` - 环境变量配置
- `alembic.ini` - 数据库迁移配置
- `babel.cfg` - 翻译配置
- `Procfile` - 部署进程配置
- `gunicorn.conf.py` - Web服务器配置

#### 3. **核心Python文件**
- `run.py`, `config.py`, `wsgi.py` - 应用核心文件
- `backup_current_database.py` - 通用数据库备份工具（从DATABASE_URL读取配置）
- `standard_migration_upgrade.py` - SP8D迁移升级工具
- `standard_migration_upgrade_ovs.py` - OVS迁移升级工具

#### 4. **核心文档**
- `CLAUDE-*.md` - 项目规范文档
- `README.md` - 项目说明文档
- `requirements.txt`, `package.json` - 依赖清单

#### 5. **版本配置文件**
- `app_version.json` - 应用版本信息

### **❌ 不允许在根目录存放**

**严格禁止以下文件存在于根目录**：

- **临时脚本** → 必须放入 `scripts/temp/`
- **测试脚本** → 必须放入 `tests/`
- **日志文件** → 必须放入 `logs/` 或 `logs/archived/`
- **数据导出** → 必须放入 `data/` 或 `data/archived/`
- **临时文档** → 必须放入 `docs/temp/`
- **迁移脚本** → 完成后移至 `scripts/archived/YYYY-QX/`

### **自动分类指南（Claude AI使用）**

#### **创建新脚本时**
```python
调试/检查/修复脚本 (debug_*, check_*, fix_*)
  → scripts/temp/
  → 完成后询问用户：删除或归档

测试脚本 (test_*)
  → tests/

数据库备份工具 (backup_*, simple_*_backup.py)
  → 保留在根目录

数据库迁移工具 (standard_migration_upgrade*.py)
  → 保留在根目录

临时迁移脚本 (apply_*, migrate_*, migration_*, sp8d_*, ovs_*)
  → 完成后移至 scripts/archived/YYYY-QX-migrations/

部署脚本 (deploy_*.sh, upgrade_*.sh)
  → 保留在根目录
```

#### **生成数据文件时**
```
临时导出/分析 (*.json, *_analysis_*.json)
  → data/temp/
  → 定期清理（保留30天）

重要数据备份 (backup_*.sql, *.dump)
  → data/backups/ 或 cloud_db_backups/

配置数据 (app_version.json, user_module_version.json最新版)
  → 保留在根目录或 data/config/
```

#### **生成日志时**
```
应用日志 (app.log, flask.log, pma.log)
  → logs/
  → 自动轮转（日志系统配置）

历史日志 (*.log 旧文件)
  → logs/archived/
  → 按月归档
```

#### **生成文档时**
```
核心规范文档 (CLAUDE-*.md, README.md)
  → 保留在根目录

临时任务总结 (*_SUMMARY.md, *_FIX.md, *_REPORT.md)
  → ❌ 禁止生成（除非用户明确要求）
  → 如果必须生成 → docs/temp/

有价值的文档 (guides/, references/)
  → docs/guides/ 或 docs/references/
```

### **定期维护规则**

**自动清理策略**：

1. **每月维护**
   - 清理 `scripts/temp/` 中30天前的脚本
   - 归档 `logs/` 中30天前的日志到 `logs/archived/`
   - 检查根目录是否有新增的临时文件

2. **每季度维护**
   - 清理 `data/temp/` 中90天前的数据
   - 归档 `scripts/temp/` 中有价值的脚本到 `scripts/archived/YYYY-QX/`
   - 压缩 `logs/archived/` 中超过90天的日志

3. **手动审核**
   - 根目录Python脚本数量超过20个时触发审核
   - 根目录文档数量超过15个时触发审核
   - 项目总大小超过1GB时触发全面清理

### **目录结构规范**

```
PMA/
├── app/                      # 应用核心代码
├── migrations/               # 数据库迁移文件
├── tests/                    # 测试脚本
│   └── archived/            # 历史测试脚本
├── scripts/                  # 脚本目录
│   ├── temp/                # 临时脚本（30天清理）
│   ├── active/              # 活跃工具脚本
│   ├── tools/               # 可复用工具
│   └── archived/            # 历史归档
│       ├── 2025-Q2/        # 按季度归档
│       ├── 2025-Q3/
│       └── 2025-Q3-migrations/  # 迁移类脚本专用
├── logs/                     # 日志目录
│   └── archived/            # 历史日志
├── data/                     # 数据目录
│   ├── temp/                # 临时数据（90天清理）
│   ├── backups/             # 数据备份
│   ├── config/              # 配置数据
│   └── archived/            # 历史数据
├── docs/                     # 文档目录
│   ├── temp/                # 临时文档
│   ├── guides/              # 使用指南
│   ├── references/          # 参考文档
│   └── archived/            # 历史文档
├── cloud_db_backups/         # 云端数据库备份
├── venv/                     # Python虚拟环境
├── run.py                    # ✅ 应用启动文件
├── config.py                 # ✅ 配置文件
├── wsgi.py                   # ✅ WSGI入口
├── backup_current_database.py # ✅ 通用数据库备份工具
├── standard_migration_upgrade.py      # ✅ SP8D迁移工具
├── standard_migration_upgrade_ovs.py  # ✅ OVS迁移工具
├── start.sh                  # ✅ 统一启动脚本
├── CLAUDE.md                 # ✅ 核心规范文档
├── CLAUDE-*.md               # ✅ 专项规范文档
├── README.md                 # ✅ 项目说明
├── requirements.txt          # ✅ Python依赖
└── app_version.json          # ✅ 版本信息
```

### **违规检测**

**Claude AI在每次会话开始时应检查**：

```python
# 伪代码示例
root_files = list_files('.', exclude=['venv', 'app', 'migrations'])

violations = []
for file in root_files:
    if file.endswith('.log'):
        violations.append(f"日志文件 {file} 应移至 logs/")
    elif file matches '*_SUMMARY.md' or '*_FIX.md':
        violations.append(f"临时文档 {file} 应移至 docs/temp/ 或删除")
    elif file matches 'test_*.py':
        violations.append(f"测试脚本 {file} 应移至 tests/")
    elif file matches 'debug_*.py' or 'check_*.py' or 'fix_*.py':
        violations.append(f"临时脚本 {file} 应移至 scripts/temp/")
    elif file matches '*_analysis_*.json' or '*_20250*.json':
        violations.append(f"临时数据 {file} 应移至 data/temp/")

if violations:
    print("⚠️ 检测到违反文件组织规范的文件：")
    for v in violations:
        print(f"  - {v}")
    prompt_user_to_clean()
```

### **清理确认流程**

当检测到根目录文件过多时：

1. **分析文件** - 识别文件类型和用途
2. **生成报告** - 列出可移动文件清单
3. **风险评估** - 标注关键文件（不可移动）
4. **用户确认** - 展示清理方案并等待批准
5. **创建备份** - 执行前创建tar.gz备份
6. **执行清理** - 按分类移动文件
7. **验证结果** - 确认关键文件完好

---

## 🔄 审批组件使用规范

### **组件版本**

| 组件类型 | 文件位置 | 适用场景 |
|---------|---------|---------|
| **Bootstrap 版** | `macros/approval_flow.html` | Bootstrap 风格页面 |
| **Tailwind 版** | `components/tw_approval_flow.html` | Tailwind 风格页面 |

---

### **Tailwind 审批流程组件（推荐）**

**适用于**: 所有 `tw_*.html` 风格的详情页面

#### **模板导入**
```jinja2
{% from 'components/tw_approval_flow.html' import render_tw_approval_flow_card, render_tw_approval_flow_script, render_tw_approval_modals %}
```

#### **使用步骤**

**1. 渲染审批流程卡片**（放在页面主内容区）
```jinja2
{{ render_tw_approval_flow_card(expense.status, container_id='approvalFlowContainer') }}
```

**2. 渲染确认模态框**（放在模态框区域）
```jinja2
{{ render_tw_approval_modals() }}
```

**3. 渲染审批流程脚本**（放在脚本区域）
```jinja2
{{ render_tw_approval_flow_script(
    'expense',                                    # 对象类型
    expense.id,                                   # 对象ID
    expense.status,                               # 对象状态
    expense.owner.real_name or expense.owner.username,  # 创建人名称
    '/expense/api/approval',                      # API基础路径
    'approvalFlowContainer'                       # 容器ID
) }}
```

#### **组件功能**
- ✅ **纯 Tailwind 样式** - 无需引入额外 CSS
- ✅ **竖向时间线** - 清晰展示审批进度
- ✅ **内联审批操作** - 审批人可直接在时间线中操作
- ✅ **动画效果** - 当前节点脉冲动画
- ✅ **暗色模式** - 完整的 dark mode 支持
- ✅ **国际化** - 完整的中英文支持

#### **当前使用的页面**
- `app/templates/project/tw_project_detail.html` - 项目详情
- `app/templates/expense/tw_expense_detail.html` - 报销单详情

---

### **Bootstrap 审批流程组件**

**适用于**: Bootstrap 风格的详情页面

#### **模板导入**
```jinja2
{% from 'macros/approval_flow.html' import render_complete_approval_section %}
```

#### **基本调用**
```jinja2
{{ render_complete_approval_section(
    object_type='order',          # 对象类型
    object_id=order.id,           # 对象ID
    object_status=order.status,   # 对象状态
    current_user_id=current_user.id,
    creator_id=order.created_by.id,
    container_id='approvalFlowSection',
    options={
        'operation_title': '审批操作',
        'flow_title': '审批流程'
    }
) }}
```

#### **必需的前端资源**
```html
<!-- CSS 文件 -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/approval_flow.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/approval_timeline.css') }}">

<!-- JavaScript 文件 -->
<script src="{{ url_for('static', filename='js/approval_flow.js') }}"></script>
<script src="{{ url_for('static', filename='js/approval_flow_utils.js') }}"></script>
```

#### **当前使用的页面**
- `app/templates/project/detail.html` - 项目详情（Bootstrap版）
- `app/templates/expense/expense_detail.html` - 报销单详情（Bootstrap版）
- `app/templates/inventory/order_detail.html` - 订单详情

---

### **通用注意事项**

#### **权限要求**
- 只有**创建人**可以看到提交/召回/重新提交按钮
- 审批流程图对所有有查看权限的用户可见
- 当前审批人可以在时间线中直接操作同意/驳回

#### **状态一致性**
- 对象状态必须与审批系统状态保持同步
- 使用标准状态名称：`draft`, `pending`, `approved`, `rejected`, `recalled`

#### **API 端点**
审批流程需要后端提供以下 API 端点：
- `GET /{object_type}/api/approval/{id}/flow` - 获取审批流程数据
- `POST /{object_type}/api/approval/{id}/submit` - 提交审批
- `POST /{object_type}/api/approval/{id}/recall` - 召回审批
- `POST /{object_type}/api/approval/{id}/resubmit` - 重新提交
- `POST /approval/approve/{instance_id}` - 审批人执行审批操作

---

## 🎨 前端交互规则

### **动态元素控制**
- **重置按钮**：默认隐藏（`display: none`），JavaScript 控制显示
- **加载状态**：统一使用 `.loading` 类
- **自动筛选**：下拉框变化时自动提交，搜索框需点击搜索按钮

### **用户体验**
- **响应时间**：操作反馈在 200ms 内显示
- **加载提示**：超过 1 秒的操作必须显示加载状态
- **错误处理**：所有 AJAX 请求必须有错误处理

---

## 🚀 性能优化规则

### **数据库查询**
- 避免 N+1 查询，使用 `joinedload()` 或 `subqueryload()`
- 大数据集使用分页：`paginate(page, per_page, error_out=False)`
- 复杂查询使用原生 SQL 或视图

### **前端优化**
- 静态资源使用 CDN
- 大型列表实现虚拟滚动或分页加载
- 图片使用懒加载

---

## 🧪 测试规范

### **必测场景**
- 筛选搜索功能：自动筛选、重置按钮、翻译切换
- 权限控制：无权限时的页面行为
- 数据完整性：CRUD 操作的数据一致性
- 国际化：中英文切换的完整性

### **测试数据**
- 使用种子数据进行开发测试
- 不在生产环境测试

---

## 🛠️ 开发工作流

### **代码修改流程**
1. **读取需求** - 仔细理解用户需求
2. **检查现有实现** - 避免重复造轮子
3. **遵循规范** - 按照本文档规则实现
4. **测试验证** - 确保功能正常且符合规范
5. **文档更新** - 必要时更新本规则文档

### **提交前检查清单**
- [ ] 翻译文件已更新和编译
- [ ] 标准化组件配置一致
- [ ] JavaScript 初始化参数正确
- [ ] **如创建了新的可复用JS工具，已更新 CLAUDE-JS-TOOLS.md**
- [ ] **实现功能前已检查 CLAUDE-JS-TOOLS.md 是否有可复用工具**
- [ ] 权限检查完整
- [ ] 错误处理完善
- [ ] 代码注释清晰
- [ ] 临时脚本已清理或归档（参见 CLAUDE-SCRIPTS.md）

### **脚本管理规范**
**详细规范请参阅**: [CLAUDE-SCRIPTS.md](./CLAUDE-SCRIPTS.md)

#### **核心规则**
- ❌ **禁止在根目录创建临时脚本**
- ✅ **临时脚本放入 `scripts/temp/`**
- ✅ **测试脚本放入 `tests/`**
- ✅ **所有脚本必须包含路径修正代码**
- ✅ **完成任务后询问删除或归档**

#### **脚本存放位置**
```
tests/              # 测试脚本 (test_*.py)
scripts/
  ├── temp/         # 临时脚本 (debug_*.py, check_*.py, fix_*.py)
  ├── active/       # 核心工具 (backup_*.py, 迁移工具等)
  ├── tools/        # 可复用工具脚本
  └── archived/     # 历史归档脚本
```

#### **标准脚本模板**
所有新脚本必须包含：
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""脚本功能说明"""
import sys, os

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())
from app import create_app, db
```

---

## 🚨 常见错误与解决方案

### **翻译问题**
- **问题**：界面显示英文而非中文
- **解决**：检查配置是否使用中文 msgid，确认翻译文件已编译

### **筛选功能不一致**
- **问题**：不同列表页面行为不同
- **解决**：使用统一的 filter_config 格式和 JavaScript 配置

### **重置按钮显示异常**
- **问题**：重置按钮一直显示或不显示
- **解决**：检查 CSS `.filter-reset-button { display: none; }` 和 JavaScript 控制逻辑

### **权限错误**
- **问题**：用户看到不应该看到的内容
- **解决**：添加 `@permission_required` 装饰器和模板权限检查

---

## 📋 快速参考

### **文档查阅指南**
- **核心规范** → 项目根目录 CLAUDE-*.md 文档
- **完整文档索引** → 查阅 [docs/README.md](docs/README.md)
- **翻译问题** → 查阅 [CLAUDE-I18N.md](./CLAUDE-I18N.md)
- **Bootstrap组件** → 查阅 [CLAUDE-COMPONENTS.md](./CLAUDE-COMPONENTS.md)
- **Tailwind组件** → 查阅 [CLAUDE-TW-COMPONENTS.md](./CLAUDE-TW-COMPONENTS.md)
- **JavaScript工具** → 查阅 [CLAUDE-JS-TOOLS.md](./CLAUDE-JS-TOOLS.md) ⚠️ **实现功能前必查**
- **数据库操作** → 查阅 [CLAUDE-DATABASE.md](./CLAUDE-DATABASE.md)
- **脚本管理** → 查阅 [CLAUDE-SCRIPTS.md](./CLAUDE-SCRIPTS.md)
- **代码质量** → 查阅 [CLAUDE-CODE-QUALITY.md](./CLAUDE-CODE-QUALITY.md)

### **⚠️ 本地命令执行规范（Claude AI 必读）**

**重要**：在本地 macOS 环境执行任何涉及 Flask 应用的 Python 命令时，**必须**先设置 WeasyPrint 所需的动态库路径。

**原因**：WeasyPrint（PDF生成库）依赖 Homebrew 安装的系统库（GLib/Pango/Cairo），但默认库搜索路径不包含 `/opt/homebrew/lib`。

**强制规范**：
```bash
# ✅ 正确方式 - 所有 Flask/Python 命令前必须设置环境变量
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db upgrade
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && python3 run.py
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && python3 some_script.py

# ❌ 错误方式 - 直接执行会因 WeasyPrint 导入失败
flask db upgrade
python3 run.py
```

**适用场景**：
- 数据库迁移：`flask db upgrade`, `flask db migrate`
- 运行脚本：任何需要导入 Flask 应用的 Python 脚本
- 启动应用：`python run.py`（推荐使用 `./start.sh`）

### **常用命令**
```bash
# 编译翻译文件
pybabel compile -d app/translations

# 启动应用
./start.sh                            # 统一启动脚本（推荐）
python run.py                         # 快速启动（默认配置）

# 数据库备份
python3 backup_current_database.py    # 通用备份（从 DATABASE_URL 读取配置）

# 数据库迁移升级
python3 standard_migration_upgrade.py     # SP8D标准升级
python3 standard_migration_upgrade_ovs.py # OVS标准升级
```

### **标准路由模板**
```python
@blueprint.route('/list')
@login_required
@permission_required('module', 'view')
def list_view():
    search = request.args.get('search', '').strip()
    query = Model.query.filter(Model.is_deleted == False)
    if search:
        query = query.filter(Model.name.ilike(f'%{search}%'))
    items = query.order_by(Model.created_at.desc()).all()
    
    filter_config = {
        'action_url': url_for('blueprint.list_view'),
        'form_id': 'listFilterForm',
        'search_field': {
            'name': 'search',
            'label': '搜索',
            'placeholder': '搜索提示',
            'value': search
        }
    }
    
    return render_template('template.html', items=items, filter_config=filter_config)
```

---

## 📝 规则更新日志

- **2025-12-12**: 📚 **拆分组件文档**
  - 创建 `CLAUDE-TW-COMPONENTS.md` 独立文档，包含所有 Tailwind 组件规范
  - `CLAUDE-COMPONENTS.md` 从 3100+ 行减少到 1657 行，仅保留 Bootstrap 组件规范
  - 更新文档索引和快速参考
- **2025-12-12**: 🔄 **创建 Tailwind 审批流程组件**
  - 创建 `components/tw_approval_flow.html` 组件，从项目详情页提取
  - 提供三个宏：`render_tw_approval_flow_card`、`render_tw_approval_flow_script`、`render_tw_approval_modals`
  - 纯 Tailwind 样式，无需引入额外 CSS
  - 更新 `tw_expense_detail.html` 使用新组件
  - 删除旧版 `render_tw_complete_approval_section`、`render_tw_approval_flow_container`、`render_tw_approval_confirm_modal`
  - 更新审批组件使用规范文档，区分 Bootstrap 版和 Tailwind 版
- **2025-10-22**: 🔒 **添加报销单特殊权限规则文档**
  - 明确报销单不使用数据归属机制，属于个人财务数据
  - 详细说明访问权限规则：财务/管理员全部可见，普通用户仅自己+直属下属
  - 对比业务数据（Customer、Project等）与报销单的权限机制差异
  - 记录代码实现位置（access_control.py:580-622）和注意事项
- **2025-10-21**: 🔧 **创建JavaScript可复用工具索引系统**（CLAUDE-JS-TOOLS.md）
  - 建立强制检查机制：实现功能前必须先查阅工具索引
  - 在核心原则中添加"工具复用优先"原则（优先级#3）
  - 制定工具创建标准和文档更新模板
  - 完成 vendor-sales-manager-selector.js 重构并建立完整文档（消除165行重复代码）
  - 在提交前检查清单中添加JS工具相关检查项
- **2025-10-12**: 📚 **添加代码质量与重构规范**（CLAUDE-CODE-QUALITY.md），基于审批流程重构案例总结
  - 定义DRY原则和逻辑先行原则
  - 制定文件大小控制标准（Python 1500行、JS 1200行、HTML 800行警告阈值）
  - 建立重复代码识别标准（2次重复或15行以上）
  - 详细记录审批流程重构实战案例（68行→34行，消除47行重复）
  - 创建代码提交前检查清单
- **2025-09-30**: 📚 **完善文档索引系统**，创建docs/README.md统一文档入口，重命名前端规范目录为frontend-specs
- **2025-09-30**: 📁 **添加完整文件组织规范**，包括根目录规则、自动分类指南、定期维护策略和违规检测机制
- **2025-09-30**: 执行根目录数据和日志清理，移动17个JSON文件到data/archived/，移动25个日志文件到logs/archived/
- **2025-09-30**: 执行根目录迁移脚本清理，移动27个迁移类脚本到scripts/archived/2025-Q3-migrations/
- **2025-09-30**: 根目录Python脚本从160个减少到133个，总清理进度：658→133 (80%↓)
- **2025-09-30**: 🚨 **禁止自动生成任务总结MD文档**，除非用户明确要求。Git commit已足够记录变更。
- **2025-09-30**: 执行根目录文档大清理，移动423个临时文档到归档，根目录MD从435个减少到13个（97%↓）
- **2025-09-30**: 添加脚本创建与管理规范（CLAUDE-SCRIPTS.md），包括脚本存放位置、命名规范、标准模板和生命周期管理
- **2025-09-30**: 执行根目录脚本整理，移动498个历史脚本到归档目录，根目录从658个减少到160个（76%↓）
- **2025-08-18**: 添加新版通用审批组件使用规范，包含从订单审批发展而来的`render_complete_approval_section`标准用法、迁移指南和注意事项
- **2025-08-15**: 添加本地开发云端存储规范，包括生产环境Supabase配置、启动脚本和测试一致性要求
- **2025-08-15**: 修复云端PDF下载问题，将重定向下载改为代理下载确保强制下载行为
- **2025-08-12**: 修复项目模块中商务助理权限控制问题，确保商务助理能查看部门内所有账户的项目数据
- **2025-08-12**: 添加智能合并功能权限规范，包括角色权限配置和数据访问控制原则
- **2025-08-07**: 添加共享功能组件完整规范到CLAUDE-COMPONENTS.md，包括树状用户选择器、权限控制、服务器端状态渲染等v2.0功能
- **2025-08-03**: 重构文档结构，拆分为专门规范文件，优化主文档
- **2025-08-01**: 添加OVS数据库迁移升级规范，包含完整的工具链和实战验证案例
- **2025-07-30**: 添加云端数据库备份工具规范
- **2025-07-20**: 创建初始规则文档
- **版本**: 2.5.0
- **最后更新**: 2025-09-30

---

## 💡 注意事项

**Claude AI 助手在每次对话开始时应该：**
1. 自动读取并遵循本规则文档和相关专门规范文件
2. 在不确定时主动询问而非假设
3. 始终优先保证数据安全和代码一致性
4. 完成任务后验证是否符合本规则要求
5. 统一使用中文进行会话
6. **❌ 不再自动生成任务总结MD文档**，除非用户明确要求

### 📝 关于任务总结文档的规则

**重要变更（2025-09-30）**：

#### ❌ 禁止自动生成
- 不再在任务完成后自动创建 *_SUMMARY.md, *_FIX.md, *_REPORT.md 等文档
- 这些文档多数仅为一次性记录，实际价值有限
- Git commit历史已足够记录修改内容

#### ✅ 推荐做法
```
任务完成 → 简短口头总结 → 用户需要时再生成文档
```

**示例对话**：
```
用户：修复XXX问题
助手：✅ 已修复XXX问题

      修改内容：
      - 文件A: 修复了YYY
      - 文件B: 添加了ZZZ
      - 测试：已通过验证

      （不自动生成文档）
      如需详细报告，请告诉我。
```

#### 📋 例外情况：仅在以下情况生成文档

1. **用户明确要求** - "帮我修复XXX并生成报告"
2. **重大架构变更** - 需要详细记录设计决策
3. **复杂问题排查** - 过程复杂，需要文档化
4. **知识沉淀需要** - 用户明确表示需要保留参考

#### 📂 文档存放位置

如果确需生成文档：
- 临时记录 → `docs/temp/` （定期清理）
- 有价值的文档 → `docs/guides/` 或 `docs/references/`
- ❌ 不要放在项目根目录

**本文档是活文档，应根据项目发展持续更新完善。**