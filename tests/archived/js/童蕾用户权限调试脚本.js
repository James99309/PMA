// 童蕾用户退回审批按钮权限调试脚本
// 在童蕾账户登录的浏览器控制台中执行此脚本

console.log('=== 童蕾用户权限调试脚本 ===');
console.log('执行时间:', new Date().toLocaleString());

// 1. 检查退回审批按钮是否存在
const rollbackButton = document.querySelector('button[onclick="showAdminRollbackModal()"]');
console.log('1. 退回审批按钮检查:');
console.log('   按钮是否存在:', !!rollbackButton);
if (rollbackButton) {
    console.log('   按钮文本:', rollbackButton.textContent.trim());
    console.log('   按钮样式:', rollbackButton.className);
    console.log('   按钮是否可见:', rollbackButton.style.display !== 'none');
    console.log('   按钮是否禁用:', rollbackButton.disabled);
}

// 2. 检查JavaScript函数是否存在
console.log('2. JavaScript函数检查:');
console.log('   showAdminRollbackModal函数是否存在:', typeof showAdminRollbackModal !== 'undefined');
if (typeof showAdminRollbackModal !== 'undefined') {
    console.log('   函数类型:', typeof showAdminRollbackModal);
} else {
    console.log('   ✅ 函数不存在，这是正确的（权限不足）');
}

// 3. 检查模态框是否存在
const rollbackModal = document.getElementById('adminRollbackModal');
console.log('3. 退回审批模态框检查:');
console.log('   模态框是否存在:', !!rollbackModal);

// 4. 检查当前用户信息（如果可用）
console.log('4. 用户信息检查:');
try {
    // 尝试从页面中获取用户信息
    const userElements = document.querySelectorAll('[data-user-role], .user-info, .current-user');
    if (userElements.length > 0) {
        userElements.forEach((el, index) => {
            console.log(`   用户信息元素 ${index + 1}:`, el.textContent.trim());
        });
    } else {
        console.log('   页面中未找到明显的用户信息元素');
    }
} catch (e) {
    console.log('   获取用户信息时出错:', e.message);
}

// 5. 检查权限相关的全局变量
console.log('5. 权限变量检查:');
console.log('   window.currentUser:', typeof window.currentUser !== 'undefined' ? window.currentUser : '未定义');
console.log('   window.userRole:', typeof window.userRole !== 'undefined' ? window.userRole : '未定义');
console.log('   window.isAdmin:', typeof window.isAdmin !== 'undefined' ? window.isAdmin : '未定义');

// 6. 检查页面URL和状态
console.log('6. 页面状态检查:');
console.log('   当前URL:', window.location.href);
console.log('   页面标题:', document.title);

// 7. 尝试点击按钮测试（如果存在）
if (rollbackButton) {
    console.log('7. 按钮点击测试:');
    console.log('   ⚠️  检测到退回审批按钮存在，这可能是权限问题！');
    console.log('   尝试点击测试（模拟）...');
    
    try {
        // 不实际点击，只是测试事件
        const clickEvent = new Event('click');
        console.log('   点击事件创建成功');
        
        // 检查onclick属性
        const onclickAttr = rollbackButton.getAttribute('onclick');
        console.log('   onclick属性:', onclickAttr);
        
        // 模拟点击但不实际执行
        console.log('   模拟点击结果: 如果函数不存在，实际点击会报错');
    } catch (e) {
        console.log('   点击测试出错:', e.message);
    }
} else {
    console.log('7. 按钮点击测试:');
    console.log('   ✅ 未检测到退回审批按钮，权限控制正常');
}

// 8. 生成问题报告
console.log('8. 问题诊断报告:');
const hasButton = !!rollbackButton;
const hasFunction = typeof showAdminRollbackModal !== 'undefined';

if (!hasButton && !hasFunction) {
    console.log('   ✅ 状态正常：按钮和函数都不存在，权限控制正确');
} else if (hasButton && !hasFunction) {
    console.log('   ❌ 发现问题：按钮存在但函数不存在');
    console.log('   原因分析：可能是浏览器缓存问题或模板渲染不一致');
    console.log('   建议操作：');
    console.log('   1. 清理浏览器缓存（Ctrl+Shift+Del）');
    console.log('   2. 强制刷新页面（Ctrl+F5）');
    console.log('   3. 重新登录');
} else if (!hasButton && hasFunction) {
    console.log('   ⚠️  异常状态：函数存在但按钮不存在');
    console.log('   这种情况比较少见，可能是JavaScript缓存问题');
} else {
    console.log('   ❌ 严重问题：按钮和函数都存在');
    console.log('   这意味着权限检查完全失效');
    console.log('   需要立即检查服务器端权限逻辑');
}

console.log('=== 调试脚本执行完成 ===');
console.log('');
console.log('📋 复制以下信息发送给技术支持：');
console.log(`按钮存在: ${hasButton}, 函数存在: ${hasFunction}, URL: ${window.location.href}, 时间: ${new Date().toISOString()}`); 