# PMA 项目开发规则 - Claude AI 助手指南

## 📚 文档结构

本规则文档已拆分为多个专门文件，便于查找和维护：

### **📖 主要规则文档**
- **CLAUDE.md** (本文件) - 核心原则和基础规范
- **CLAUDE-I18N.md** - 翻译与国际化规范
- **CLAUDE-COMPONENTS.md** - 组件和UI规范  
- **CLAUDE-DATABASE.md** - 数据库备份和迁移规范

### **📋 使用说明**
- **Claude AI助手**: 需要时请主动读取相应的专门规范文件
- **开发人员**: 根据具体需求查阅对应文档
- **更新维护**: 各专门规范独立更新，降低冲突

---

## 🎯 核心原则

### **优先级排序**
1. **数据安全** - 永不删除或损坏现有数据
2. **通用组件保护** - 严禁随意修改通用模组，必须遵循保护协议
3. **一致性** - 所有功能必须遵循统一标准
4. **国际化** - 支持中英文切换
5. **用户体验** - 简洁、直观、响应快速
6. **代码质量** - 可维护、可扩展、有文档

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
- **SP8D数据库**: `python3 backup_cloud_pma_db.py`
- **OVS数据库**: `python3 simple_ovs_backup.py`

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

### **数据验证**
- 所有用户输入必须验证和清理
- 数据库操作使用事务处理
- 敏感操作记录审计日志

---

## ☁️ 本地开发云端存储规范

### **核心原则**
- **测试一致性** - 本地开发必须使用生产环境Supabase存储
- **数据真实性** - 确保本地测试和云端生产环境完全一致
- **下载功能验证** - 消除本地文件存储与云端存储的行为差异

### **配置要求**
1. **生产环境配置文件** - 使用 `.env.supabase.prod` 配置生产环境Supabase
2. **强制云端存储** - 设置 `FORCE_CLOUD_UPLOAD=true` 强制本地使用云端存储
3. **多存储桶支持** - 配置发票、产品、研发产品等专用存储桶

### **启动方式**
```bash
# 使用生产环境Supabase存储启动本地开发
./run_with_supabase_prod.sh

# 或手动加载配置
export $(cat .env.supabase.prod | grep -v '^#' | xargs)
python run.py
```

### **配置文件结构**
`.env.supabase.prod` 必须包含：
```bash
# Supabase 项目配置
SUPABASE_URL=https://pqzviljbpfoqvyfulakl.supabase.co
SUPABASE_KEY=your-service-role-key

# 存储桶配置
SUPABASE_BUCKET_INVOICE=invoice-images
SUPABASE_BUCKET_PRODUCT=product-images  
SUPABASE_BUCKET_RD_PRODUCT=rd-product-images

# 强制云端存储
FORCE_CLOUD_UPLOAD=true
```

### **验证要求**
- **连接测试** - 启动前自动运行Supabase连接测试
- **存储桶访问** - 验证所有配置的存储桶可正常访问
- **上传下载测试** - 确保文件上传和下载功能完全正常
- **权限验证** - 验证存储桶的RLS策略配置正确

### **重要提醒**
- **生产数据谨慎** - 本地开发使用生产存储，避免上传测试数据
- **网络依赖** - 本地开发需要稳定的网络连接访问Supabase
- **安全配置** - 确保 `.env.supabase.prod` 在 `.gitignore` 中
- **定期更新** - 定期更新密钥确保安全性

---

## 🔄 审批组件使用规范

### **新版通用审批组件**
- **使用组件**：`render_complete_approval_section` (来自 `macros/approval_flow.html`)
- **组件来源**：从订单审批发展而来的统一标准审批组件
- **替代组件**：完全替代旧版 `render_approval_section` (来自 `macros/approval_macros.html`)

### **标准使用模式**

#### **模板导入**
```jinja2
{% from 'macros/approval_flow.html' import render_complete_approval_section %}
```

#### **基本调用**
```jinja2
{{ render_complete_approval_section(
    object_type='order',          # 对象类型：'order', 'project', 'expense' 等
    object_id=order.id,           # 对象ID
    object_status=order.status,   # 对象状态：'draft', 'pending', 'approved', 'rejected' 等
    current_user_id=current_user.id,     # 当前用户ID
    creator_id=order.created_by.id,      # 创建人ID
    container_id='approvalFlowSection',  # 容器ID（可选）
    options={                     # 选项配置（可选）
        'operation_title': '审批操作',
        'flow_title': '审批流程',
        'description': '创建完成，可以提交审批流程。',
        'warning': '提交后将进入审批流程，无法直接修改。'
    }
) }}
```

### **组件功能特性**

#### **自动包含的功能**
- ✅ **审批操作区域** - 提交、召回、重新提交等操作
- ✅ **审批流程图** - 可视化流程展示和状态跟踪
- ✅ **权限控制** - 基于用户角色和创建权限的操作控制
- ✅ **状态管理** - 自动处理草稿、待审批、已批准、已拒绝等状态
- ✅ **确认模态框** - 标准化的审批确认和召回确认对话框
- ✅ **国际化支持** - 完整的中英文切换支持

#### **必需的前端资源**
```html
<!-- CSS 文件 -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/approval_flow.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/approval_timeline.css') }}">

<!-- JavaScript 文件 -->
<script src="{{ url_for('static', filename='js/approval_flow.js') }}"></script>
<script src="{{ url_for('static', filename='js/approval_flow_utils.js') }}"></script>
```

### **当前使用的页面**
- **项目详情页面** - `app/templates/project/detail.html`
- **报销单详情页面** - `app/templates/expense/expense_detail.html`  
- **订单详情页面** - `app/templates/inventory/order_detail.html`

### **迁移指南**

#### **从旧版审批组件迁移**
```jinja2
<!-- 旧版用法 ❌ -->
{% from 'macros/approval_macros.html' import render_approval_section %}
{{ render_approval_section('customer', company.id, approval_instance, current_user) }}

<!-- 新版用法 ✅ -->
{% from 'macros/approval_flow.html' import render_complete_approval_section %}
{{ render_complete_approval_section('customer', company.id, company.status, current_user.id, company.owner_id) }}
```

#### **清理无用导入**
```jinja2
<!-- 需要移除 ❌ -->
{% from 'macros/approval_macros.html' import render_approval_section %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/approval_timeline.css') }}">

<!-- 保留使用 ✅ -->
{% from 'macros/approval_flow.html' import render_complete_approval_section %}
```

### **注意事项**

#### **权限要求**
- 只有**创建人**可以看到审批操作区域
- 审批流程图对所有有查看权限的用户可见
- 确保页面有正确的权限检查装饰器

#### **状态一致性**
- 对象状态必须与审批系统状态保持同步
- 使用标准状态名称：`draft`, `pending`, `approved`, `rejected`, `recalled`

#### **样式兼容性**
- 组件使用 Bootstrap 5 样式系统
- 自动适配移动端和桌面端显示
- 支持现有的页面布局结构

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
- [ ] 权限检查完整
- [ ] 错误处理完善
- [ ] 代码注释清晰

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
- **翻译问题** → 查阅 [CLAUDE-I18N.md](./CLAUDE-I18N.md)
- **组件使用** → 查阅 [CLAUDE-COMPONENTS.md](./CLAUDE-COMPONENTS.md)
- **数据库操作** → 查阅 [CLAUDE-DATABASE.md](./CLAUDE-DATABASE.md)

### **常用命令**
```bash
# 编译翻译文件
pybabel compile -d app/translations

# 运行开发服务器（推荐使用云端存储）
./run_with_supabase_prod.sh           # 使用生产环境Supabase存储
python run.py                         # 使用本地存储（不推荐）

# 云端存储配置
export $(cat .env.supabase.prod | grep -v '^#' | xargs)  # 手动加载配置
python3 test_supabase_prod_connection.py                # 测试Supabase连接

# 数据库备份
python3 backup_cloud_pma_db.py        # SP8D
python3 simple_ovs_backup.py          # OVS

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
- **版本**: 2.3.0
- **最后更新**: 2025-08-18

---

## 💡 注意事项

**Claude AI 助手在每次对话开始时应该：**
1. 自动读取并遵循本规则文档和相关专门规范文件
2. 在不确定时主动询问而非假设
3. 始终优先保证数据安全和代码一致性
4. 完成任务后验证是否符合本规则要求
5. 统一使用中文进行会话

**本文档是活文档，应根据项目发展持续更新完善。**