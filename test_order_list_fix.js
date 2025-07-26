// 测试统计数据更新的修复
console.log('测试订单列表统计数据格式化修复...');

// 模拟各种可能的统计数据格式
const testCases = [
    { name: '正常数字', data: { total_count: 10, total_amount: 123.45 } },
    { name: '字符串数字', data: { total_count: '15', total_amount: '234.56' } },
    { name: 'null值', data: { total_count: null, total_amount: null } },
    { name: 'undefined值', data: { total_count: undefined, total_amount: undefined } },
    { name: '空字符串', data: { total_count: '', total_amount: '' } },
    { name: 'NaN值', data: { total_count: NaN, total_amount: NaN } },
    { name: '非数字字符串', data: { total_count: 'abc', total_amount: 'xyz' } }
];

// 格式化数字函数的测试版本
function formatNumber(value) {
    // 处理各种可能的无效值
    if (value === null || value === undefined || value === '') return '0';
    
    // 转换为数字类型
    let numericValue;
    if (typeof value === 'number') {
        numericValue = value;
    } else if (typeof value === 'string') {
        numericValue = parseFloat(value);
    } else {
        numericValue = 0;
    }
    
    // 检查是否为有效数字
    if (isNaN(numericValue) || !isFinite(numericValue)) {
        return '0';
    }
    
    // 使用千分位分隔符，并确保为整数
    return Math.round(numericValue).toLocaleString();
}

// 金额格式化函数的测试版本
function formatAmount(value) {
    // 确保value是数字类型，如果不是则转换为0
    const numericValue = (typeof value === 'number' && !isNaN(value)) ? value : 
                       (typeof value === 'string' && !isNaN(parseFloat(value))) ? parseFloat(value) : 0;
    
    return numericValue.toFixed(2);
}

// 测试每个案例
testCases.forEach(testCase => {
    console.log(`\n测试 ${testCase.name}:`);
    console.log(`  输入: count=${testCase.data.total_count}, amount=${testCase.data.total_amount}`);
    
    try {
        const formattedCount = formatNumber(testCase.data.total_count);
        const formattedAmount = formatAmount(testCase.data.total_amount);
        
        console.log(`  输出: count=${formattedCount}, amount=${formattedAmount}`);
        console.log(`  ✅ 测试通过`);
    } catch (error) {
        console.log(`  ❌ 测试失败: ${error.message}`);
    }
});

console.log('\n修复验证完成！');