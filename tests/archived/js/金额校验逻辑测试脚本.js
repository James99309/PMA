// 金额校验逻辑测试脚本
// 在浏览器控制台中运行此脚本来测试逻辑

console.log('=== 金额校验逻辑测试 ===');

// 模拟不同的测试场景（修正后的逻辑）
const testCases = [
    {
        name: '场景1：结算单小于批价单（应该允许审批）',
        pricingTotal: 100000,
        settlementTotal: 80000,
        expectedResult: true, // 应该返回true，允许审批
        expectedMessage: '应该通过校验'
    },
    {
        name: '场景2：结算单等于批价单（应该允许审批）',
        pricingTotal: 100000,
        settlementTotal: 100000,
        expectedResult: true, // 应该返回true，允许审批
        expectedMessage: '应该通过校验'
    },
    {
        name: '场景3：结算单大于批价单（应该阻止审批）',
        pricingTotal: 100000,
        settlementTotal: 120000,
        expectedResult: false, // 应该返回false，阻止审批
        expectedMessage: '应该显示错误提示'
    }
];

// 当前的校验逻辑（修正后）
function testValidationLogic(pricingTotal, settlementTotal) {
    console.log(`\n测试数据：批价单=${pricingTotal}, 结算单=${settlementTotal}`);
    
    // 修正后的逻辑：if (settlementTotal > pricingTotal)
    if (settlementTotal > pricingTotal) {
        console.log('❌ 校验失败：结算单总额大于批价单总额');
        return false; // 阻止审批
    }
    
    console.log('✅ 校验通过');
    return true; // 允许审批
}

// 执行测试
testCases.forEach((testCase, index) => {
    console.log(`\n${testCase.name}`);
    console.log(`批价单总额：¥${testCase.pricingTotal.toLocaleString()}`);
    console.log(`结算单总额：¥${testCase.settlementTotal.toLocaleString()}`);
    
    const result = testValidationLogic(testCase.pricingTotal, testCase.settlementTotal);
    
    console.log(`实际结果：${result}`);
    console.log(`期望结果：${testCase.expectedResult}`);
    console.log(`测试结果：${result === testCase.expectedResult ? '✅ 通过' : '❌ 失败'}`);
    console.log(`说明：${testCase.expectedMessage}`);
});

console.log('\n=== 测试总结 ===');
console.log('修正后逻辑：if (settlementTotal > pricingTotal) 阻止审批');
console.log('这意味着：');
console.log('- 结算单 < 批价单 → 允许审批 ✅');
console.log('- 结算单 = 批价单 → 允许审批 ✅');
console.log('- 结算单 > 批价单 → 阻止审批 ❌');

console.log('\n业务规则：');
console.log('✅ 允许审批：结算单总额 <= 批价单总额');
console.log('❌ 阻止审批：结算单总额 > 批价单总额');
console.log('📋 提示消息：结算单总金额不能大于批价单总金额');

// 提供快速测试函数
window.quickTest = function(pricing, settlement) {
    console.log(`\n快速测试：批价单=${pricing}, 结算单=${settlement}`);
    return testValidationLogic(pricing, settlement);
};

console.log('\n可用命令：');
console.log('quickTest(100000, 80000) - 快速测试指定金额');
console.log('例如：quickTest(100000, 120000)'); 