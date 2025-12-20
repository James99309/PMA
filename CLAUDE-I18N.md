# 翻译与国际化规范

## 🌍 翻译范围定义

### **✅ 需要翻译的内容**
- **用户界面文本**：按钮、标签、标题、提示信息
- **用户消息**：成功/错误/警告提示
- **表单字段**：输入框标签、占位符文本
- **菜单和导航**：导航栏、侧边栏、面包屑
- **数据展示标签**：表格标题、统计卡片标题
- **用户帮助文本**：说明文字、工具提示

### **❌ 不需要翻译的内容**
- **代码注释**：`// 这是注释`、`{# Jinja2 注释 #}`
- **数据库字段名**：`company_name`、`created_at`
- **技术常量**：`'primary'`、`'success'`、`'admin'`
- **API 路径**：`'/api/companies'`
- **CSS 类名**：`'btn-primary'`、`'card-header'`
- **日志消息**：`logger.info('操作完成')`
- **配置键值**：字典的 key 值映射
- **开发调试信息**：`console.log()` 中的文本
- **无用的硬编码映射**：定义了但未使用的角色映射等

## 🔍 翻译识别规则

### **模板文件(.html)识别规则**
```html
<!-- ✅ 需要翻译 -->
<h1>{{ _('仪表盘') }}</h1>
<button>{{ _('保存') }}</button>
<span>用户统计</span>  <!-- 需要包装为 {{ _('用户统计') }} -->

<!-- ❌ 不需要翻译 -->
<div class="dashboard-header">  <!-- CSS类名 -->
<!-- 这是页面头部组件 -->  <!-- 注释 -->
<script>console.log('页面加载');</script>  <!-- 调试信息 -->
{% set unused_mapping = {'key': '值'} %}  <!-- 无用映射 -->
```

### **Python 文件(.py)识别规则**
```python
# ✅ 需要翻译
flash(_('保存成功！'), 'success')
return render_template('index.html', title=_('仪表盘'))

# ❌ 不需要翻译  
logger.info('用户登录成功')  # 日志消息
ROLE_MAPPING = {'admin': '管理员'}  # 配置映射，应使用数据库或工具函数
# 这是用户管理模块  # 代码注释
```

### **JavaScript 文件(.js)和内联JS识别规则**
```javascript
// ✅ 需要翻译 - 用户可见文本
alert('请输入内容');  // 需要改为 alert(window.i18nTexts.pleaseEnterContent);
submitBtn.innerHTML = '提交中...';  // 需要改为 window.i18nTexts.submitting;
placeholder="输入回复内容...";  // 需要改为 placeholder="${window.i18nTexts.enterReply}";

// ❌ 不需要翻译
console.log('调试信息');  // 开发调试信息
const API_ENDPOINT = '/api/data';  // 技术常量
```

### **国际化文本传递规范**
```html
<!-- 正确方式：在模板中定义JavaScript国际化对象 -->
<script>
window.i18nTexts = {
    submit: '{{ _("提交") }}',
    cancel: '{{ _("取消") }}',
    confirmDelete: '{{ _("确定要删除吗？") }}',
    submitting: '{{ _("提交中...") }}',
    success: '{{ _("操作成功") }}'
};
</script>
```

## 🗂️ 数据映射规范（优先于翻译系统）

### **优先使用标准映射**
对于项目中有标准化映射的数据类型，**必须使用映射而非翻译系统**：

**项目类型映射** - 使用 `app/utils/dictionary_helpers.py` 中的 `PROJECT_TYPE_LABELS`：
```python
PROJECT_TYPE_LABELS = {
    'channel_follow': {'zh': '渠道跟进', 'en': 'Channel Follow'},
    'sales_focus': {'zh': '销售重点', 'en': 'Sales Focus'},
    'business_opportunity': {'zh': '客户服务', 'en': 'Service Opportunity'}
}
```

### **模板中使用映射的正确方式**
```jinja2
{% macro render_project_type(type) %}
  {% set type_mappings = {
    'channel_follow': {'zh': '渠道跟进', 'en': 'Channel Follow'},
    'sales_focus': {'zh': '销售重点', 'en': 'Sales Focus'}
  } %}
  
  {% set is_english = (_('搜索') == 'Search') %}
  {% set lang_code = 'en' if is_english else 'zh' %}
  
  {% if type in type_mappings %}
    {% set display_text = type_mappings[type][lang_code] %}
  {% else %}
    {% set display_text = '' %}
  {% endif %}
  
  {% if display_text %}
    <span class="badge badge-pill badge-transparent project-type-{{ type }}">
      {{ display_text }}
    </span>
  {% endif %}
{% endmacro %}
```

### **空值处理规范**
```jinja2
{# 对于映射数据类型的空值，显示为空字符串，不显示任何内容 #}
{% if not type or type == 'None' or type == '' %}
  {% set display_text = '' %}  {# 空值不显示 #}
{% elif type in type_mappings %}
  {% set display_text = type_mappings[type][lang_code] %}
{% else %}
  {% set display_text = '' %}  {# 未知类型也不显示 #}
{% endif %}

{# 只有有内容时才渲染徽章 #}
{% if display_text %}
  <span class="badge">{{ display_text }}</span>
{% endif %}
```

### **标准映射类型清单**

| 数据类型 | 映射常量 | 使用场景 |
|---------|----------|----------|
| 项目类型 | `PROJECT_TYPE_LABELS` | 项目类型徽章、筛选器 |
| 项目阶段 | `PROJECT_STAGE_LABELS` | 项目阶段徽章、筛选器 |
| 报备来源 | `REPORT_SOURCE_LABELS` | 来源徽章、筛选器 |
| 公司类型 | `COMPANY_TYPE_LABELS` | 公司类型显示 |
| 产品状态 | `PRODUCT_SITUATION_LABELS` | 产品状态徽章 |

### **语言感知过滤器规范（make_i18n_filter）**

所有 `*_label` 类过滤器已通过 `make_i18n_filter` 工厂函数包装，**自动检测当前语言**。

**工厂函数位置**：`app/utils/dictionary_helpers.py`

```python
def make_i18n_filter(label_func):
    """创建语言感知的 Jinja2 过滤器包装器"""
    def wrapper(key, lang=None):
        if lang is None:
            lang = get_current_language() or 'zh'
        return label_func(key, lang)
    return wrapper
```

**✅ 正确用法（不传参数，自动检测语言）**：
```jinja2
{{ project.report_source | report_source_label }}
{{ project.product_situation | product_situation_label }}
{{ project.current_stage | project_stage_label }}
```

**❌ 错误用法（硬编码语言）**：
```jinja2
{{ project.report_source | report_source_label('zh') }}  {# 禁止！ #}
```

**已包装的过滤器清单**：

| 过滤器 | 映射常量 | 用途 |
|-------|---------|------|
| `report_source_label` | `REPORT_SOURCE_LABELS` | 报备来源 |
| `authorization_status_label` | `AUTHORIZATION_STATUS_LABELS` | 授权状态 |
| `company_type_label` | `COMPANY_TYPE_LABELS` | 公司类型 |
| `product_situation_label` | `PRODUCT_SITUATION_LABELS` | 品牌植入状态 |
| `industry_label` | `INDUSTRY_LABELS` | 行业分类 |
| `status_label` | `STATUS_LABELS` | 通用状态 |
| `share_permission_label` | - | 共享权限 |
| `approval_status_label` | `APPROVAL_STATUS_LABELS` | 审批状态 |
| `product_type_label` | `PRODUCT_TYPE_LABELS` | 产品类型 |
| `product_status_label` | `PRODUCT_STATUS_LABELS` | 产品状态 |
| `dev_product_status_label` | `DEV_PRODUCT_STATUS_LABELS` | 研发产品状态 |
| `active_status_label` | `ACTIVE_STATUS_LABELS` | 启用状态 |

**新增 label 函数时**：
1. 在 `dictionary_helpers.py` 中定义映射常量和 label 函数
2. 在 `__init__.py` 中用 `make_i18n_filter` 包装后注册为过滤器
3. 模板中直接使用 `{{ value | xxx_label }}`，无需传参

## 🔄 避免重复翻译的策略

### **翻译前强制检查流程**
1. **搜索现有翻译**：在 `messages.po` 中搜索是否已存在相同的 msgid
2. **命令行检查**：使用 `grep "msgid \"搜索\"" app/translations/en/LC_MESSAGES/messages.po` 检查重复
3. **标准化用词**：优先使用标准术语表中的统一用词

### **重复检测规则**
- ❌ **严禁添加重复的 msgid**：每个中文文本只能在翻译文件中出现一次
- ✅ **发现重复时必须复用**：使用已存在的翻译，不要添加新条目
- ✅ **定期清理重复**：发现重复翻译时立即清理，保留第一个出现的条目

### **常用标准化术语表**
```python
STANDARD_TERMS = {
    '企业': 'Company',           # 不使用 Corporation, Enterprise
    '客户': 'Customer',          # 不使用 Client
    '联系人': 'Contact',         # 不使用 Contact Person
    '项目': 'Project',           # 不使用 Program
    '保存': 'Save',              # 不使用 Submit
    '删除': 'Delete',            # 不使用 Remove
    '编辑': 'Edit',              # 不使用 Modify
    '查看': 'View',              # 不使用 See, Look
}
```

## 📋 强制规则
- ✅ **所有配置文本使用中文作为 msgid**
- ✅ **英文作为翻译值存储在 messages.po 中**
- ❌ **禁止在 Python 代码中硬编码英文字符串**
- ❌ **禁止在模板中硬编码英文文本**
- ❌ **禁止创建无用的硬编码映射**
- ✅ **在放入翻译文件中时，先检查是否有重复的中文，只放入中文不重复的英文翻译**

## 🛠️ 翻译文件管理

### **基本操作**
1. 添加新翻译后必须执行：`pybabel compile -d app/translations`
2. 翻译文件路径：`app/translations/en/LC_MESSAGES/messages.po`
3. 模板中使用：`{{ _('中文文本') }}`
4. Python 中使用：`from flask_babel import gettext as _; _('中文文本')`

### **翻译文件结构规范**
```po
# 用户界面 - 通用按钮
msgid "保存"
msgstr "Save"

msgid "取消" 
msgstr "Cancel"

# 用户界面 - 仪表盘
msgid "仪表盘"
msgstr "Dashboard"

msgid "数据统计"
msgstr "Data Statistics"
```

## 🚨 常见问题与解决方案

### **问题：英文翻译全部失效，显示中文**

**症状**：
- 切换到英文环境后，导航菜单和列表标题仍显示中文
- messages.po 文件中所有翻译条目带有 `#~` 前缀（obsolete标记）
- 翻译条目从活跃状态变为 obsolete 状态

**根本原因**：
使用了错误的 `pybabel extract` 命令参数：
```bash
# ❌ 错误命令 - 导致所有翻译失效
pybabel extract -F babel.cfg -k _l -o messages.pot .
```

**为什么会失效**：
1. `-k _l` 参数告诉 Babel **只提取 `_l()` 函数调用**
2. 但项目中实际使用的是 `_()` 函数（2,622 处使用）
3. 项目中 `_l()` 函数使用次数：**0 次**
4. 结果：提取了 0 个翻译字符串，生成空的 messages.pot
5. 运行 `pybabel update` 后，Babel 认为所有旧翻译都过时，全部标记为 obsolete

**修复步骤**：

1. **从 Git 恢复完好的翻译版本**（如果有）：
   ```bash
   # 查找最后一个完好的版本
   git log --oneline -- app/translations/en/LC_MESSAGES/messages.po

   # 恢复完好版本（例如 970e5c2）
   git show 970e5c2:app/translations/en/LC_MESSAGES/messages.po > app/translations/en/LC_MESSAGES/messages.po
   ```

2. **修正 babel.cfg 配置**：
   ```
   [python: **.py]
   [jinja2: **/templates/**.html]
   extensions=jinja2.ext.i18n
   ```

3. **使用正确的命令重新提取**：
   ```bash
   # ✅ 正确命令 - 使用默认关键字
   pybabel extract -F babel.cfg -o messages.pot app/
   ```

4. **更新翻译文件**（合并新旧翻译）：
   ```bash
   pybabel update -i messages.pot -d app/translations
   ```

5. **编译翻译文件**：
   ```bash
   pybabel compile -d app/translations
   ```

6. **重启应用并验证**

---

### **❌ 永远不要使用的错误命令**

```bash
# ❌ 错误 1：使用 -k _l 参数（项目中未使用 _l()）
pybabel extract -F babel.cfg -k _l -o messages.pot .

# ❌ 错误 2：提取根目录所有文件（包含语法错误的临时脚本）
pybabel extract -F babel.cfg -o messages.pot .

# ❌ 错误 3：使用 --no-default-keywords（会忽略 _ 和 gettext）
pybabel extract -F babel.cfg --no-default-keywords -o messages.pot app/
```

---

### **✅ 标准翻译管理命令**

#### **提取新的翻译文本**
```bash
# 从 app/ 目录提取翻译（推荐）
pybabel extract -F babel.cfg -o messages.pot app/
```

#### **更新翻译文件**
```bash
# 将新提取的翻译合并到现有翻译文件
pybabel update -i messages.pot -d app/translations
```

#### **编译翻译文件**
```bash
# 编译 .po 文件为 .mo 二进制文件
pybabel compile -d app/translations
```

#### **完整更新流程**
```bash
# 1. 提取翻译
pybabel extract -F babel.cfg -o messages.pot app/

# 2. 更新翻译文件
pybabel update -i messages.pot -d app/translations

# 3. 手工翻译新增条目（编辑 messages.po 文件）

# 4. 编译翻译文件
pybabel compile -d app/translations

# 5. 重启应用
```

---

### **Babel 默认提取关键字**

不使用 `-k` 参数时，Babel 会提取以下函数调用：
- `_()` - 最常用的翻译函数
- `gettext()` - 标准翻译函数
- `ngettext()` - 复数翻译函数
- `ugettext()` - Unicode 翻译函数
- `N_()` - 延迟翻译函数
- `pgettext()` - 上下文翻译函数
- 等等...

**项目使用情况**：
- `_()` 函数：2,622 处（主要在模板中）
- `gettext()` 函数：若干处（Python 代码中）
- `_l()` 函数：**0 处**

---

### **预防措施**

1. **记录标准命令**：在团队文档中明确记录正确的翻译管理命令
2. **代码审查**：提交翻译文件变更时，检查是否有大量 obsolete 标记
3. **自动化脚本**：创建标准化脚本避免手动输入错误命令
4. **Git 保护**：定期备份 messages.po 文件
5. **测试验证**：翻译更新后必须测试英文环境

---

**历史案例**：2025-10-19 翻译失效事件
- **触发**: 使用 `pybabel extract -k _l` 命令
- **影响**: 1,278 个翻译全部标记为 obsolete
- **修复**: 从 Git 提交 970e5c2 恢复，重新提取并更新
- **教训**: 严格遵循标准命令，不随意使用 `-k` 参数