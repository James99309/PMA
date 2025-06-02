# 客户删除时联系人保护逻辑

## 问题描述

在之前的客户删除逻辑中，虽然设置了 `cascade='all, delete-orphan'`，删除客户时会自动删除相关联系人，但这可能导致重要的联系人数据意外丢失。用户要求增加一个保护机制，在删除客户之前必须先处理（转移或删除）所有关联的联系人。

## 解决方案

### 1. 单个客户删除保护

在 `app/views/customer.py` 的 `delete_company()` 函数中增加联系人检查逻辑：

```python
# === 新增：检查是否存在关联的联系人 ===
existing_contacts = Contact.query.filter_by(company_id=company_id).all()
if existing_contacts:
    contact_names = [contact.name for contact in existing_contacts]
    flash(f'删除失败：该客户下还有 {len(existing_contacts)} 个联系人，请先转移或删除这些联系人后再删除客户。联系人列表：{", ".join(contact_names)}', 'danger')
    return redirect(url_for('customer.view_company', company_id=company_id))
```

### 2. 批量删除保护

在 `batch_delete_companies()` 函数中增加相同的检查逻辑：

```python
companies_with_contacts = []  # === 新增：记录有联系人的客户 ===

for company in companies:
    if can_edit_data(company, current_user):
        # === 新增：检查是否存在关联的联系人 ===
        existing_contacts = Contact.query.filter_by(company_id=company.id).all()
        if existing_contacts:
            contact_names = [contact.name for contact in existing_contacts]
            companies_with_contacts.append(f"{company.company_name}({len(existing_contacts)}个联系人)")
        else:
            deletable_companies.append(company)
    else:
        unauthorized_companies.append(company.company_name)
```

### 3. 错误消息和反馈

**单个删除时的错误消息：**
```
删除失败：该客户下还有 1 个联系人，请先转移或删除这些联系人后再删除客户。联系人列表：唐宝军
```

**批量删除时的反馈消息：**
```
成功删除2个企业，跳过有联系人的企业: 企业A(3个联系人), 企业B(1个联系人)
```

## 实施效果

### 测试数据统计（当前系统）

- **总客户数**: 473
- **总联系人数**: 665  
- **有联系人的客户数**: 360
- **没有联系人的客户数**: 113

### 保护机制效果

1. **✅ 成功阻止意外删除**: 有联系人的客户（360个）无法直接删除
2. **✅ 清晰的错误提示**: 显示具体的联系人名单和数量
3. **✅ 引导用户操作**: 提示用户先处理联系人
4. **✅ 支持批量操作**: 批量删除时自动跳过有联系人的客户

## 用户操作流程

### 删除有联系人的客户的正确流程：

1. **查看客户详情** → 确认要保留或转移的联系人
2. **处理联系人**：
   - **转移联系人**: 使用联系人的"更改所有者"功能将联系人转移到其他客户
   - **删除联系人**: 对于不需要的联系人直接删除
3. **确认无联系人** → 系统允许删除客户
4. **删除客户** → 成功删除

### 批量删除时：

1. **选择要删除的客户列表**
2. **执行批量删除** → 系统自动跳过有联系人的客户
3. **查看反馈消息** → 了解哪些客户被跳过及原因
4. **单独处理被跳过的客户** → 按单个删除流程处理

## 数据安全保障

1. **防止数据丢失**: 避免重要联系人信息意外删除
2. **明确操作提示**: 用户清楚知道删除被阻止的原因
3. **保持数据一致性**: 确保联系人-客户关系的完整性
4. **支持数据迁移**: 鼓励用户在删除前做好数据迁移

## 技术实现要点

1. **检查时机**: 在实际删除操作之前进行检查
2. **事务安全**: 检查失败时及时回滚，不影响数据库状态
3. **用户体验**: 提供详细的错误信息和操作建议
4. **性能考虑**: 使用简单的 `filter_by` 查询，避免复杂的 JOIN 操作

## 相关文件

- `app/views/customer.py` - 客户删除逻辑主文件
- `test_customer_deletion_with_contacts.py` - 测试脚本
- `app/models/customer.py` - 客户和联系人模型定义

## 注意事项

1. 这个保护机制是**强制性**的，管理员也不能绕过
2. 联系人的**转移功能**需要确保正常工作
3. 建议在删除客户前先做好**数据备份**
4. 对于大量数据操作，建议分批处理避免超时 