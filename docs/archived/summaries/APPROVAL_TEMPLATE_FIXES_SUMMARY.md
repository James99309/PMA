# 审批模版相关问题修复总结

## 修复的问题

### 1. 报价单模版删除报错 (500 Internal Server Error)

**问题描述：**
- 删除报价单类型的审批模版时出现500内部服务器错误
- 错误原因：视图期望 `delete_approval_template` 函数返回字典格式，但实际函数只返回布尔值

**修复方案：**
- 修改 `app/helpers/approval_helpers.py` 中的 `delete_approval_template` 函数
- 将返回值从布尔值改为字典格式：`{'success': bool, 'message': str, 'instances': list}`
- 添加详细的错误信息处理和关联实例详情

**修复内容：**
```python
def delete_approval_template(template_id):
    """删除审批流程模板
    
    Returns:
        字典，包含success、message和instances字段
    """
    # 检查模板是否存在
    if not template:
        return {
            'success': False,
            'message': '审批流程模板不存在',
            'instances': []
        }
    
    # 检查关联实例并返回详细信息
    if instances:
        return {
            'success': False,
            'message': f'无法删除模板"{template.name}"，因为存在关联的审批实例。模板已被禁用。',
            'instances': instance_details
        }
    
    # 成功删除
    return {
        'success': True,
        'message': f'审批流程模板"{template.name}"删除成功',
        'instances': []
    }
```

### 2. 报价单类型审批可编辑字段缺少报价单明细字段

**问题描述：**
- 报价单类型的审批模版中，可编辑字段选项缺少报价单明细相关字段
- 无法在审批步骤中配置对报价单明细的编辑权限

**修复方案：**
- 在 `get_object_field_options` 函数中为报价单类型添加明细字段
- 在前端JavaScript中同步更新字段选项

**新增的报价单明细字段：**
- `product_name` - 产品名称
- `product_model` - 产品型号
- `product_spec` - 产品规格
- `product_brand` - 产品品牌
- `product_unit` - 产品单位
- `product_price` - 产品单价
- `discount_rate` - 折扣率
- `discounted_price` - 折后单价
- `quantity` - 数量
- `subtotal` - 小计
- `product_mn` - 产品编码
- `remark` - 备注

### 3. 审批模版字体颜色显示问题

**问题描述：**
- 审批模版中的可编辑字段、是否启动等显示内容字体颜色不够清晰
- 部分文本显示为灰色，影响可读性

**修复方案：**
- 在 `app/templates/macros/approval_config_macros.html` 中添加内联样式
- 确保关键信息文本颜色为黑色 (`#000`)
- 在 `app/templates/approval_config/template_form.html` 中添加CSS样式

**修复的显示元素：**
- 邮件通知状态显示
- 可编辑字段标签
- 邮件抄送用户标签
- 动作类型标签
- 表单中的复选框标签

**添加的CSS样式：**
```css
/* 确保表单中的文本颜色为黑色 */
.form-check-label,
.form-label,
.form-text,
.selected-field-badge,
.field-checkbox-item label {
  color: #000 !important;
}

/* 确保复选框标签文本为黑色 */
.form-check-input + .form-check-label {
  color: #000 !important;
}
```

### 4. 必填字段重复显示问题

**问题描述：**
- 在审批流程模版详情页面中，必填字段可能出现重复显示
- 数据库中可能存储了重复的字段值

**修复方案：**
- 在模版详情页面的模板中添加字段去重逻辑
- 在 `create_approval_template` 和 `update_approval_template` 函数中添加字段去重处理
- 确保保存到数据库的字段列表不包含重复项

**修复内容：**
```html
{# 对必填字段进行去重处理 #}
{% set unique_fields = template.required_fields|unique %}
{% for field_code in unique_fields %}
  <span class="badge bg-info">
    {% if field_code in field_dict %}{{ field_dict[field_code] }}{% else %}{{ field_code }}{% endif %}
  </span>
{% endfor %}
```

```python
# 去重处理，保持顺序
unique_fields = []
for field in field_list:
    if field not in unique_fields:
        unique_fields.append(field)

template.required_fields = unique_fields
```

### 5. 编辑审批步骤时可编辑字段选中状态问题

**问题描述：**
- 点击编辑已有的审批步骤时，可编辑字段中已经被选中的字段没有正确显示为勾选状态
- 用户无法看到当前步骤已配置的可编辑字段

**修复方案：**
- 改进编辑模态框的JavaScript逻辑
- 添加调试日志以便排查问题
- 确保先清除所有复选框状态，再正确设置选中状态

**修复内容：**
```javascript
// 处理可编辑字段
const editableFieldsArray = editableFields ? JSON.parse(editableFields) : [];
console.log('可编辑字段数据:', editableFieldsArray); // 调试日志

// 先清除所有复选框的选中状态
modal.querySelectorAll('input[name="editable_fields"]').forEach(function(checkbox) {
  checkbox.checked = false;
});

// 然后设置应该选中的复选框
modal.querySelectorAll('input[name="editable_fields"]').forEach(function(checkbox) {
  if (editableFieldsArray.includes(checkbox.value)) {
    checkbox.checked = true;
    console.log('设置字段选中:', checkbox.value); // 调试日志
  }
});
```

## 技术细节

### 文件修改列表

1. **app/helpers/approval_helpers.py**
   - 修改 `delete_approval_template` 函数返回值格式
   - 添加报价单明细字段到 `get_object_field_options` 函数
   - 在 `create_approval_template` 和 `update_approval_template` 函数中添加字段去重逻辑

2. **app/templates/macros/approval_config_macros.html**
   - 为审批步骤显示元素添加黑色字体样式
   - 改进编辑步骤模态框的JavaScript逻辑，修复可编辑字段选中状态问题

3. **app/templates/approval_config/template_form.html**
   - 添加CSS样式确保表单文本颜色为黑色
   - 更新JavaScript中的报价单字段选项

4. **app/templates/approval_config/template_detail.html**
   - 添加必填字段去重逻辑，防止重复显示

### 兼容性说明

- 所有修改都向后兼容
- 不影响现有审批流程的正常运行
- 新增字段选项不会影响已配置的审批模版
- 字段去重逻辑不会影响现有数据，只是在显示和保存时进行处理

### 测试建议

1. **删除功能测试：**
   - 测试删除没有关联实例的审批模版
   - 测试删除有关联实例的审批模版（应该禁用而不是删除）
   - 验证错误信息显示正确

2. **字段选项测试：**
   - 创建报价单类型的审批模版
   - 验证可编辑字段选项包含所有报价单明细字段
   - 测试字段选择和保存功能

3. **UI显示测试：**
   - 检查审批模版列表页面的文本颜色
   - 检查审批模版详情页面的显示效果
   - 验证表单中的文本可读性

4. **必填字段重复测试：**
   - 创建包含重复字段的审批模版
   - 验证详情页面不会重复显示字段
   - 测试编辑保存后字段去重是否生效

5. **编辑步骤测试：**
   - 创建包含可编辑字段的审批步骤
   - 点击编辑步骤，验证可编辑字段正确显示为选中状态
   - 修改可编辑字段选择并保存，验证更新是否正确

## 注意事项

- JavaScript中的Jinja2模板语法会产生linter警告，这是正常现象
- 修改后的删除函数返回格式与视图期望完全匹配
- 新增的报价单明细字段覆盖了报价单编辑中的所有主要字段
- CSS样式使用了 `!important` 确保优先级，避免被其他样式覆盖
- 字段去重逻辑保持原有顺序，不会影响用户的字段排列习惯
- 添加的调试日志有助于排查可编辑字段选中状态的问题 