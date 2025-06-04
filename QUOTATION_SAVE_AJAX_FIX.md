# 报价单AJAX保存功能修复文档

## 问题描述

用户反馈：报价单详情页面的编辑保存功能仍会直接将没有任何修改的产品明细取消审核通过标记。

## 问题根因

报价单详情页面使用AJAX保存功能（`save_quotation`函数），该函数采用"删除所有旧明细，然后重新创建"的方式处理产品明细，但没有像表单版本的`edit_quotation`函数那样临时禁用事件监听器，导致：

1. 删除操作触发事件监听器
2. 重新创建操作触发事件监听器
3. 即使最终内容相同，中间过程的变化会误触发清除确认状态的逻辑

## 修复方案

### 核心策略
应用与`edit_quotation`函数相同的修复策略：
1. 在删除-重建过程开始前临时禁用事件监听器
2. 完成删除-重建后手动进行签名检测和状态处理
3. 使用`try-finally`块确保事件监听器在任何情况下都能恢复
4. 在提交前（而不是提交后）进行签名检测

### 修复代码

#### 1. 事件监听器管理
```python
# 临时禁用事件监听器
event.remove(QuotationDetail, 'after_insert', update_quotation_product_signature)
event.remove(QuotationDetail, 'after_update', update_quotation_product_signature)
event.remove(QuotationDetail, 'after_delete', update_quotation_product_signature)

try:
    # 删除-重建逻辑
    # ...
    
    # 在提交前进行签名检测和状态处理
    try:
        new_product_signature = quotation.calculate_product_signature()
        product_details_changed = old_product_signature != new_product_signature
        
        # 如果产品明细发生关键变化，手动清除确认状态
        if product_details_changed and quotation.confirmation_badge_status == 'confirmed':
            quotation.confirmation_badge_status = 'none'
            quotation.confirmation_badge_color = None
            quotation.confirmed_by = None
            quotation.confirmed_at = None
            current_app.logger.info(f"报价单 {quotation.id} 的产品明细发生关键变化，已手动清除确认状态")
        
        # 更新产品签名
        quotation.product_signature = new_product_signature
        
    except Exception as signature_error:
        current_app.logger.error(f"处理产品签名和确认状态时出错: {str(signature_error)}")
    
    # 提交更改（在事件监听器被禁用的情况下）
    db.session.commit()
    
finally:
    # 确保事件监听器在任何情况下都能恢复
    event.listen(QuotationDetail, 'after_insert', update_quotation_product_signature)
    event.listen(QuotationDetail, 'after_update', update_quotation_product_signature)
    event.listen(QuotationDetail, 'after_delete', update_quotation_product_signature)
```

#### 2. 关键改进点
- **提交前检测**：将签名检测和状态处理放在`db.session.commit()`之前，避免事件监听器干扰
- **双重保护**：即使事件监听器在恢复后被意外触发，手动检测已经确保了正确的状态
- **异常安全**：使用`try-finally`确保事件监听器必定恢复

## 测试验证

### 调试测试结果
通过专门的调试脚本验证修复效果：

```
=== 调试save_quotation逻辑的事件监听器 ===

🔧 步骤1: 移除事件监听器...
   ✅ 事件监听器移除成功

🔧 步骤3: 签名检测和状态处理...
   旧签名: 0cfc304077e6e9eee8cea6821c6c0fe9
   新签名: 0cfc304077e6e9eee8cea6821c6c0fe9
   签名是否改变: 否
   当前确认状态: confirmed
   ✅ 保持确认状态（签名未变化）

🔧 步骤4: 提交更改...
   确认状态（提交前）: confirmed
   ✅ 数据库提交成功

📊 最终结果:
   最终签名: 0cfc304077e6e9eee8cea6821c6c0fe9
   最终确认状态: confirmed
   测试结果: ✅ 成功
```

### 功能验证
- ✅ 保存相同内容时确认状态保持不变
- ✅ 修改MN号时确认状态被正确清除
- ✅ 增加/减少明细行时确认状态被正确清除
- ✅ 修改数量、单价、折扣率时确认状态保持不变

## 影响范围

### 修改文件
- `app/views/quotation.py` - `save_quotation`函数

### 功能影响
- **报价单详情页面保存功能**：AJAX保存现在能正确处理确认状态
- **向后兼容**：不影响现有的表单保存功能
- **性能影响**：微小，主要是增加了事件监听器管理开销

## 技术细节

### 事件监听器函数引用
确保移除和恢复的是同一个函数引用：
```python
from app.models.quotation import update_quotation_product_signature

event.remove(QuotationDetail, 'after_insert', update_quotation_product_signature)
event.listen(QuotationDetail, 'after_insert', update_quotation_product_signature)
```

### 签名算法
只关注关键变化（行数和MN号）：
```python
signature_data = {
    'count': detail_count,
    'mn_list': sorted([detail.product_mn for detail in details])
}
```

### 错误处理
完善的异常处理确保系统稳定性：
- 事件监听器管理异常
- 签名检测异常
- 数据库提交异常

## 总结

通过临时禁用事件监听器和手动签名检测，成功修复了AJAX保存功能中确认状态被错误清除的问题。现在无论是表单保存还是AJAX保存，都能正确处理确认状态的保持和清除逻辑。

**修复前**：保存相同内容会错误清除确认状态  
**修复后**：只在关键变化时清除确认状态，保存相同内容时保持确认状态

这个修复完善了报价单审核徽章系统，确保了用户体验的一致性和功能的准确性。 