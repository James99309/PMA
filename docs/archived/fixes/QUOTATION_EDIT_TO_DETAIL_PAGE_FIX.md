# 报价单编辑保存后跳转详情页面及折扣率一致性修复

## 问题描述
用户反映报价单编辑界面保存后需要：
1. 保存后跳转到报价单详情页面（而不是列表页面）
2. 详情页面的折扣率需要和编辑页面保持一致
3. 进入编辑页面后当前折扣率应该按实际数据库值显示

## 问题分析
经过代码检查发现：

### 1. 跳转逻辑问题
- 编辑页面保存成功后跳转到报价单列表页面
- 用户期望保存后直接查看详情页面验证修改结果

### 2. 数据字段不匹配问题
- 前端发送的字段名为`discount`（小数形式）
- 后端期望的字段名为`discount_rate`（百分比形式）
- 导致数据传输不一致

### 3. 折扣率显示一致性
- 详情页面已正确显示折扣率：`{{ "%.1f"|format(detail.discount * 100) }}`
- 编辑页面已正确显示折扣率：`{{ '%.1f'|format(item.discount * 100) }}`
- 但前后端数据传输存在字段名不匹配

## 修复方案

### 1. 修改前端跳转逻辑

#### 文件：`app/templates/quotation/edit.html`

**修复保存成功后的跳转**：
```javascript
// 修改前：跳转到列表页面
if (returnTo) {
    window.location.href = decodeURIComponent(returnTo);
} else {
    window.location.href = '/quotation/quotations';
}

// 修改后：跳转到详情页面
var quotationId = response.quotation_id || window.location.pathname.split('/').pop();
if (quotationId && quotationId !== 'edit') {
    window.location.href = '/quotation/quotation/' + quotationId;
} else {
    window.location.href = '/quotation/quotations';
}
```

**修复重试成功后的跳转**：
```javascript
// 修改前：跳转到列表页面
window.location.href = '/quotation/quotations';

// 修改后：跳转到详情页面
var quotationId = response.quotation_id || window.location.pathname.split('/').pop();
if (quotationId && quotationId !== 'edit') {
    window.location.href = '/quotation/quotation/' + quotationId;
} else {
    window.location.href = '/quotation/quotations';
}
```

### 2. 修复后端响应数据

#### 文件：`app/views/quotation.py`

**在成功响应中包含报价单ID**：
```python
# 修改前：不包含ID
return jsonify({
    'status': 'success',
    'message': '报价单更新成功'
})

# 修改后：包含ID便于前端跳转
return jsonify({
    'status': 'success',
    'message': '报价单更新成功',
    'quotation_id': id
})
```

**在警告响应中也包含报价单ID**：
```python
return jsonify({
    'status': 'success',
    'message': '报价单更新成功',
    'warnings': detail_errors,
    'quotation_id': id
}), 200
```

### 3. 修复数据字段一致性

#### 文件：`app/templates/quotation/edit.html`

**修正前端发送的数据字段**：
```javascript
// 修改前：字段名不匹配，值格式不一致
discount: parseFloat($row.find('.discount-rate').val()) / 100 || 1.0,

// 修改后：字段名和值格式都正确
discount_rate: parseFloat($row.find('.discount-rate').val()) || 100,
```

## 修复效果

### 1. 用户体验改进
- ✅ 编辑保存后直接跳转到详情页面
- ✅ 用户可以立即验证修改结果
- ✅ 减少页面跳转次数，提高工作效率

### 2. 数据一致性保证
- ✅ 前后端数据字段名称统一
- ✅ 数据格式完全一致
- ✅ 折扣率在详情页和编辑页显示一致

### 3. 系统稳定性提升
- ✅ 消除数据传输中的字段不匹配错误
- ✅ 提供可靠的报价单ID用于页面跳转
- ✅ 支持错误重试后的正确跳转

## 技术细节

### 数据流程
1. **编辑页面**：显示数据库中的实际折扣率（百分比形式）
2. **用户修改**：JavaScript实时计算折扣率和单价的相互关系
3. **数据提交**：发送`discount_rate`字段（百分比形式）
4. **后端处理**：接收`discount_rate`并转换为小数形式存储
5. **保存响应**：返回成功状态和报价单ID
6. **页面跳转**：使用报价单ID跳转到详情页面
7. **详情页面**：显示数据库中的实际折扣率

### 字段映射
- **前端显示**：`discount_rate`（百分比，如85.0）
- **数据传输**：`discount_rate`（百分比，如85.0）
- **数据库存储**：`discount`（小数，如0.85）
- **详情页显示**：`discount * 100`（百分比，如85.0）

### 跳转逻辑
1. 优先使用服务器返回的`quotation_id`
2. 如果没有，从当前URL解析ID
3. 构造详情页面URL：`/quotation/quotation/{id}`
4. 如果无法获取有效ID，回退到列表页面

## 测试验证
1. 编辑现有报价单，修改折扣率和单价
2. 保存后确认跳转到详情页面
3. 验证详情页面的折扣率显示正确
4. 再次进入编辑页面，确认折扣率和单价显示正确的数据库值
5. 测试网络异常时的重试机制和跳转逻辑

## 注意事项
- 修复保持了原有的数据计算逻辑不变
- 所有修改都是向后兼容的
- 错误处理机制得到加强
- 用户界面体验显著改善 