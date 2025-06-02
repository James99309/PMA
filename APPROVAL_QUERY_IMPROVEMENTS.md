# 审批查询逻辑改进说明

## 问题背景

在审批中心发现显示了已删除项目的审批实例（如 APV-0066），这些实例对应的业务对象已不存在，但审批实例仍然显示在审批中心列表中，造成"孤立实例"问题。

## 改进方案

### 修改的函数

在 `app/helpers/approval_helpers.py` 中改进了以下三个核心查询函数：

1. **`get_user_created_approvals()`** - "我发起的"审批查询
2. **`get_user_pending_approvals()`** - "待我审批的"查询  
3. **`get_all_approvals()`** - "全部审批"查询（管理员）

### 改进内容

#### 1. 添加业务对象存在性检查

原来的查询只检查审批实例本身，现在增加了与业务对象的 JOIN 验证：

```python
# 针对特定业务类型的查询
if object_type == 'project':
    query = query.join(Project, ApprovalInstance.object_id == Project.id).filter(
        ApprovalInstance.object_type == 'project'
    )
elif object_type == 'quotation':
    query = query.join(Quotation, ApprovalInstance.object_id == Quotation.id).filter(
        ApprovalInstance.object_type == 'quotation'
    )
elif object_type == 'customer':
    query = query.join(Company, ApprovalInstance.object_id == Company.id).filter(
        ApprovalInstance.object_type == 'customer'
    )
```

#### 2. 混合类型查询的子查询过滤

当不指定具体业务类型时，使用子查询确保所有返回的审批实例都有对应的业务对象：

```python
else:
    # 为每种业务类型创建子查询
    project_subquery = db.session.query(ApprovalInstance.id).filter(
        ApprovalInstance.object_type == 'project'
    ).join(Project, ApprovalInstance.object_id == Project.id)
    
    quotation_subquery = db.session.query(ApprovalInstance.id).filter(
        ApprovalInstance.object_type == 'quotation'
    ).join(Quotation, ApprovalInstance.object_id == Quotation.id)
    
    customer_subquery = db.session.query(ApprovalInstance.id).filter(
        ApprovalInstance.object_type == 'customer'
    ).join(Company, ApprovalInstance.object_id == Company.id)
    
    # 只返回存在于任一子查询中的审批实例
    query = query.filter(
        or_(
            ApprovalInstance.id.in_(project_subquery),
            ApprovalInstance.id.in_(quotation_subquery),
            ApprovalInstance.id.in_(customer_subquery)
        )
    )
```

#### 3. 修复 SQLAlchemy 警告

解决了 `joinedload` 中使用字符串导致的警告，简化了复杂的关联查询。

## 测试验证

### 测试结果

通过创建孤立实例进行测试，验证了改进效果：

- **孤立实例检测**：成功识别了3个孤立实例（项目、报价单、客户各1个）
- **"我发起的"查询**：从3个实例过滤到0个，成功过滤所有孤立实例
- **"全部审批"查询**：从22个实例过滤到19个，过滤掉3个孤立实例
- **按类型过滤**：每种类型都成功过滤掉对应的孤立实例

### 测试脚本

- `test_improved_approval_queries.py` - 验证查询改进效果
- `create_test_orphaned_instances.py` - 创建和清理测试用孤立实例

## 效果

### ✅ 已解决的问题

1. **防止显示孤立实例**：审批中心不再显示对应业务对象已删除的审批实例
2. **提高数据一致性**：确保显示的审批实例都有有效的业务对象关联
3. **改善用户体验**：用户不会再看到无法访问的审批记录
4. **消除 SQLAlchemy 警告**：修复了查询中的技术警告

### ⚠️ 注意事项

1. **性能影响**：添加了 JOIN 操作，对于大量数据可能有轻微性能影响
2. **向后兼容**：保持了原有API接口不变，只是内部查询逻辑改进
3. **数据清理**：建议定期运行数据一致性检查，清理孤立的审批实例

## 后续建议

### 1. 数据清理策略

建议定期运行清理脚本，删除孤立的审批实例：

```bash
python check_approval_consistency.py --cleanup
```

### 2. 级联删除优化

考虑在删除业务对象时，自动清理相关的审批实例，防止产生新的孤立实例。

### 3. 监控机制

可以添加定期监控，及时发现和报告数据一致性问题。

## 更新日志

- **2025-06-02**：完成审批查询逻辑改进，添加业务对象存在性验证
- **2025-06-02**：修复 SQLAlchemy 查询警告
 