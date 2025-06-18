#!/usr/bin/env python3
"""
修复PO202506-020的折扣率显示问题并测试权限检查
"""

from app import create_app
from app.models.user import User
from app.models.pricing_order import PricingOrder, PricingOrderDetail
from app.services.discount_permission_service import DiscountPermissionService
from app import db

def fix_discount_permission_display():
    app = create_app()
    with app.app_context():
        print("=== 修复PO202506-020折扣权限实时提示问题 ===\n")
        
        # 1. 获取用户和批价单
        user = User.query.filter_by(username='lihuawei').first()
        po = PricingOrder.query.filter_by(order_number='PO202506-020').first()
        
        if not user or not po:
            print("❌ 用户或批价单未找到")
            return
        
        # 2. 获取权限配置
        limits = DiscountPermissionService.get_user_discount_limits(user)
        limit = limits.get('pricing_discount_limit', 0)
        
        print(f"✅ 基本信息:")
        print(f"   用户: {user.username} ({user.role})")
        print(f"   批价单: {po.order_number}")
        print(f"   权限下限: {limit}%")
        
        # 3. 检查明细折扣率的实际值
        print(f"\n=== 检查明细折扣率数值格式 ===")
        details = PricingOrderDetail.query.filter_by(
            pricing_order_id=po.id
        ).order_by(PricingOrderDetail.id).all()
        
        print(f"数据库中的折扣率格式:")
        for i, detail in enumerate(details[:3]):  # 只检查前3个
            raw_value = detail.discount_rate
            percent_value = raw_value * 100 if raw_value else 0
            print(f"   明细{i+1}: 原始值={raw_value}, 百分比={percent_value:.1f}%")
            
            # 检查是否需要修正（如果值大于1，说明是百分比格式，需要转换）
            if raw_value and raw_value > 1:
                print(f"   ⚠️  发现异常：折扣率 {raw_value} 大于1，可能是百分比格式")
                correct_value = raw_value / 100
                print(f"   🔧 建议修正为: {correct_value}")
                
                # 询问是否修正
                print(f"   是否修正明细{i+1}的折扣率? (数据库值: {raw_value} -> {correct_value})")
                
        # 4. 生成前端测试代码
        print(f"\n=== 前端测试代码 ===")
        print(f"请在浏览器控制台中执行以下代码来测试权限功能：")
        print(f"""
// 1. 确保权限数据正确设置
window.discountLimits = {{
    pricing_discount_limit: {limit},
    settlement_discount_limit: null
}};
console.log('手动设置权限数据:', window.discountLimits);

// 2. 测试权限检查函数
function testCheckDiscountPermission(inputElement, testValue) {{
    inputElement.value = testValue;
    
    const discountRate = parseFloat(inputElement.value);
    const orderType = inputElement.closest('#pricing-content') ? 'pricing' : 'settlement';
    const limit = orderType === 'pricing' ? 
        window.discountLimits.pricing_discount_limit : 
        window.discountLimits.settlement_discount_limit;
    
    console.log('测试值:', testValue);
    console.log('解析后的折扣率:', discountRate);
    console.log('权限下限:', limit);
    console.log('是否应该警告:', discountRate < limit);
    
    if (discountRate < limit) {{
        inputElement.classList.add('discount-warning');
        console.log('✅ 已添加红色警告样式');
    }} else {{
        inputElement.classList.remove('discount-warning');
        console.log('✅ 已移除警告样式');
    }}
}}

// 3. 获取第一个折扣率输入框并测试
const firstInput = document.querySelector('input.discount-rate');
if (firstInput) {{
    console.log('找到第一个折扣率输入框:', firstInput);
    
    // 测试不同的值
    console.log('\\n=== 测试30% (应该显示红色) ===');
    testCheckDiscountPermission(firstInput, 30);
    
    setTimeout(() => {{
        console.log('\\n=== 测试50% (应该显示正常) ===');
        testCheckDiscountPermission(firstInput, 50);
    }}, 2000);
}} else {{
    console.log('❌ 未找到折扣率输入框');
}}
""")
        
        # 5. 检查CSS样式
        print(f"\n=== CSS样式检查 ===")
        print(f"确保以下CSS样式已定义（应该在页面的<style>标签中）：")
        print(f"""
.discount-warning {{
    background-color: #dc3545 !important;
    color: white !important;
    border-color: #dc3545 !important;
}}

.discount-warning:focus {{
    background-color: #dc3545 !important;
    color: white !important;
    border-color: #dc3545 !important;
    box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25) !important;
}}
""")
        
        return True

if __name__ == '__main__':
    fix_discount_permission_display() 