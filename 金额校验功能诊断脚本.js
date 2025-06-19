// 批价单金额校验功能诊断脚本
// 请在批价单编辑页面的浏览器控制台中运行此脚本

console.log('=== 批价单金额校验功能诊断开始 ===');

// 1. 检查必要的DOM元素
console.log('\n1. DOM元素检查:');
const pricingTotalElement = document.getElementById('pricingTotalAmount');
const settlementTotalElement = document.getElementById('settlementTotalAmount');

console.log('批价单总金额元素存在:', !!pricingTotalElement);
console.log('结算单总金额元素存在:', !!settlementTotalElement);

if (pricingTotalElement) {
    console.log('批价单总金额文本:', pricingTotalElement.textContent);
} else {
    console.log('❌ 批价单总金额元素不存在');
}

if (settlementTotalElement) {
    console.log('结算单总金额文本:', settlementTotalElement.textContent);
} else {
    console.log('❌ 结算单总金额元素不存在');
}

// 2. 检查权限变量
console.log('\n2. 权限检查:');
console.log('can_view_settlement:', typeof can_view_settlement !== 'undefined' ? can_view_settlement : '未定义');

// 3. 检查函数是否存在
console.log('\n3. 函数检查:');
console.log('validateAmountBeforeApproval函数存在:', typeof validateAmountBeforeApproval === 'function');
console.log('openApprovalModal函数存在:', typeof openApprovalModal === 'function');
console.log('showStandardAlert函数存在:', typeof showStandardAlert === 'function');

// 4. 检查审批按钮
console.log('\n4. 审批按钮检查:');
const approveButtons = document.querySelectorAll('[onclick*="openApprovalModal(\'approve\')"]');
console.log('找到通过按钮数量:', approveButtons.length);
approveButtons.forEach((btn, index) => {
    console.log(`通过按钮${index + 1}:`, btn.textContent.trim(), '可见:', btn.offsetParent !== null);
});

// 5. 测试金额提取逻辑
console.log('\n5. 金额提取测试:');
if (pricingTotalElement && settlementTotalElement) {
    const pricingText = pricingTotalElement.textContent;
    const settlementText = settlementTotalElement.textContent;
    
    // 测试不同的正则表达式
    const regex1 = /[^\\d.-]/g;  // 错误的写法（双反斜杠）
    const regex2 = /[^\d.-]/g;   // 正确的写法
    
    console.log('使用错误正则表达式提取批价单金额:', parseFloat(pricingText.replace(regex1, '')) || 0);
    console.log('使用正确正则表达式提取批价单金额:', parseFloat(pricingText.replace(regex2, '')) || 0);
    
    console.log('使用错误正则表达式提取结算单金额:', parseFloat(settlementText.replace(regex1, '')) || 0);
    console.log('使用正确正则表达式提取结算单金额:', parseFloat(settlementText.replace(regex2, '')) || 0);
}

// 6. 手动测试金额校验函数
console.log('\n6. 手动测试金额校验:');
if (typeof validateAmountBeforeApproval === 'function') {
    try {
        const result = validateAmountBeforeApproval();
        console.log('金额校验结果:', result);
    } catch (error) {
        console.log('❌ 金额校验函数执行出错:', error.message);
    }
} else {
    console.log('❌ 金额校验函数不存在');
}

// 7. 模拟点击通过按钮
console.log('\n7. 模拟测试（如果按钮存在）:');
if (approveButtons.length > 0 && typeof openApprovalModal === 'function') {
    console.log('可以手动测试: openApprovalModal("approve")');
    console.log('注意：这会触发实际的审批流程，请谨慎使用');
} else {
    console.log('无法进行模拟测试：按钮不存在或函数不可用');
}

// 8. 检查页面标签切换状态
console.log('\n8. 页面标签检查:');
const settlementTab = document.getElementById('settlement-tab');
const settlementContent = document.getElementById('settlement-content');
console.log('结算单标签存在:', !!settlementTab);
console.log('结算单内容存在:', !!settlementContent);
if (settlementTab) {
    console.log('结算单标签可见:', settlementTab.offsetParent !== null);
    console.log('结算单标签类名:', settlementTab.className);
}
if (settlementContent) {
    console.log('结算单内容可见:', settlementContent.offsetParent !== null);
    console.log('结算单内容类名:', settlementContent.className);
}

console.log('\n=== 诊断完成 ===');
console.log('\n如果发现问题，请截图控制台输出发送给开发人员。');

// 提供手动测试函数
window.manualTestValidation = function() {
    console.log('\n=== 手动金额校验测试 ===');
    if (typeof validateAmountBeforeApproval === 'function') {
        return validateAmountBeforeApproval();
    } else {
        console.log('❌ 函数不存在');
        return false;
    }
};

console.log('\n可用的手动测试命令:');
console.log('manualTestValidation() - 手动执行金额校验');
console.log('openApprovalModal("approve") - 模拟点击通过按钮（谨慎使用）'); 