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

# 运行开发服务器
python run.py

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

- **2025-08-03**: 重构文档结构，拆分为专门规范文件，优化主文档
- **2025-08-01**: 添加OVS数据库迁移升级规范，包含完整的工具链和实战验证案例
- **2025-07-30**: 添加云端数据库备份工具规范
- **2025-07-20**: 创建初始规则文档
- **版本**: 2.0.0
- **最后更新**: 2025-08-03

---

## 💡 注意事项

**Claude AI 助手在每次对话开始时应该：**
1. 自动读取并遵循本规则文档和相关专门规范文件
2. 在不确定时主动询问而非假设
3. 始终优先保证数据安全和代码一致性
4. 完成任务后验证是否符合本规则要求
5. 统一使用中文进行会话

**本文档是活文档，应根据项目发展持续更新完善。**