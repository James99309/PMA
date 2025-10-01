# 销售经理折扣权限检查调试指南

## 🎯 问题描述
用户反馈：PO202506-018批价单在lihuawei账号（销售经理）编辑时，没有对他的角色做出低于权限时的提示颜色。

## 🔍 问题分析结果

### 后端权限设置 ✅ 正常
```
👤 用户lihuawei信息：
  用户名: lihuawei
  角色: sales_manager
  ID: 15

📊 通过服务获取的折扣权限：
  批价折扣下限: 45.0
  结算折扣下限: None

🧪 折扣权限检查测试：
  30%: 批价单 ❌ 超出权限, 结算单 ✅ 权限内
  35%: 批价单 ❌ 超出权限, 结算单 ✅ 权限内
  40%: 批价单 ❌ 超出权限, 结算单 ✅ 权限内
  45%: 批价单 ✅ 权限内, 结算单 ✅ 权限内
  50%: 批价单 ✅ 权限内, 结算单 ✅ 权限内
```

### 后端数据传递 ✅ 正常
路由中已正确获取并传递折扣权限：
```python
# 获取用户的折扣权限
discount_limits = DiscountPermissionService.get_user_discount_limits(current_user)

return render_template('pricing_order/edit_pricing_order.html',
                     discount_limits=discount_limits)
```

### 前端JavaScript代码 ✅ 正常
```javascript
// 折扣权限配置
window.discountLimits = {
    pricing_discount_limit: {{ discount_limits.pricing_discount_limit|default('null') }},
    settlement_discount_limit: {{ discount_limits.settlement_discount_limit|default('null') }}
};

// 检查单个输入框的折扣权限
function checkDiscountPermission(inputElement) {
    if (!inputElement || !window.discountLimits) return;
    
    const discountRate = parseFloat(inputElement.value);
    if (isNaN(discountRate) || discountRate === '') {
        inputElement.classList.remove('discount-warning');
        return;
    }
    
    // 判断是批价单还是结算单
    const orderType = inputElement.closest('#pricing-content') ? 'pricing' : 'settlement';
    const limit = orderType === 'pricing' ? 
        window.discountLimits.pricing_discount_limit : 
        window.discountLimits.settlement_discount_limit;
    
    // 如果没有设置权限下限，则不检查
    if (limit === null || limit === undefined) {
        inputElement.classList.remove('discount-warning');
        return;
    }
    
    // 检查是否超出权限（折扣率低于下限）
    if (discountRate < limit) {
        inputElement.classList.add('discount-warning');
    } else {
        inputElement.classList.remove('discount-warning');
    }
}
```

## 🐛 可能的原因

### 1. 前端JavaScript未被触发
- **检查方式**：打开浏览器开发者工具，查看Console是否有错误
- **确认方式**：在Console中输入 `window.discountLimits` 查看是否有数据

### 2. CSS样式问题
- **检查方式**：查看`.discount-warning`样式是否存在
- **确认方式**：手动在输入框上添加class验证样式

### 3. 输入框选择器问题
- **检查方式**：确认折扣率输入框是否使用了`discount-rate`类
- **确认方式**：查看HTML源码中的输入框类名

## 🧪 调试步骤

### 步骤1：检查前端数据
1. 使用lihuawei账号登录
2. 进入PO202506-018批价单编辑页面
3. 打开浏览器开发者工具（F12）
4. 在Console中执行：
   ```javascript
   console.log('折扣权限数据:', window.discountLimits);
   ```
   **预期结果**：应该显示 `{pricing_discount_limit: 45, settlement_discount_limit: null}`

### 步骤2：检查CSS样式
1. 在Console中执行：
   ```javascript
   const style = document.createElement('style');
   style.textContent = '.test-warning { background-color: #dc3545 !important; color: white !important; }';
   document.head.appendChild(style);
   
   const input = document.querySelector('input.discount-rate');
   if (input) {
       input.classList.add('test-warning');
       console.log('测试样式已添加到输入框');
   } else {
       console.log('没有找到折扣率输入框');
   }
   ```
   **预期结果**：输入框应该显示红色背景

### 步骤3：检查输入框选择器
1. 在Console中执行：
   ```javascript
   const discountInputs = document.querySelectorAll('input.discount-rate');
   console.log('找到的折扣率输入框:', discountInputs.length);
   discountInputs.forEach((input, index) => {
       console.log(`输入框${index + 1}:`, input.id, input.className, input.value);
   });
   ```
   **预期结果**：应该找到多个输入框

### 步骤4：手动触发权限检查
1. 在Console中执行：
   ```javascript
   const input = document.querySelector('input.discount-rate');
   if (input) {
       input.value = '30';  // 设置一个低于45%的值
       checkDiscountPermission(input);
       console.log('权限检查已触发，输入框类名:', input.className);
   }
   ```
   **预期结果**：输入框应该包含`discount-warning`类并显示红色背景

### 步骤5：检查事件绑定
1. 在Console中执行：
   ```javascript
   const input = document.querySelector('input.discount-rate');
   if (input) {
       input.value = '30';
       input.dispatchEvent(new Event('input'));
       console.log('input事件已触发');
   }
   ```
   **预期结果**：应该自动显示红色警告

## 🎨 CSS样式确认

确认以下CSS样式存在：
```css
.discount-warning {
    background-color: #dc3545 !important;
    color: white !important;
    border-color: #dc3545 !important;
}
```

## 📝 解决方案

### 如果window.discountLimits为null或undefined：
- 检查后端路由是否正确传递数据
- 检查模板渲染是否有错误

### 如果CSS样式不生效：
- 检查CSS优先级
- 确认样式定义位置
- 验证选择器正确性

### 如果输入框选择器找不到元素：
- 检查HTML中输入框的类名
- 确认JavaScript选择器正确
- 验证页面加载时机

### 如果事件未绑定：
- 检查`initializeDiscountPermissionCheck()`是否被调用
- 确认DOM加载完成时机
- 验证事件监听器添加成功

## 🔧 临时解决方案

如果问题持续存在，可以在Console中手动执行以下代码临时启用权限检查：
```javascript
// 手动初始化权限检查
window.discountLimits = {
    pricing_discount_limit: 45,
    settlement_discount_limit: null
};

// 手动绑定事件
document.querySelectorAll('input.discount-rate').forEach(input => {
    input.addEventListener('input', function() {
        const discountRate = parseFloat(this.value);
        if (discountRate < 45) {
            this.classList.add('discount-warning');
        } else {
            this.classList.remove('discount-warning');
        }
    });
});

console.log('手动权限检查已启用');
```

## 📋 检查清单

- [ ] 后端折扣权限数据正确：sales_manager = 45%
- [ ] 路由正确传递discount_limits到模板
- [ ] 前端JavaScript正确接收折扣权限数据
- [ ] CSS样式`.discount-warning`存在且正确
- [ ] 输入框选择器`input.discount-rate`找到元素
- [ ] 事件监听器正确绑定
- [ ] 权限检查函数正确执行
- [ ] 输入低于45%的值显示红色警告
- [ ] 输入45%或以上的值显示正常样式 