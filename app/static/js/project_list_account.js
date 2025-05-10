/**
 * 项目列表页面账户选择器初始化
 * 确保项目列表页与账户选择器保持同步
 */
document.addEventListener('DOMContentLoaded', function() {
    // 如果AccountSelector已定义，进行初始化
    if (typeof AccountSelector !== 'undefined') {
        // 检查URL中是否有account_id参数
        const urlParams = new URLSearchParams(window.location.search);
        const accountIdParam = urlParams.get('account_id');
        
        if (accountIdParam) {
            // 设置当前账户ID
            AccountSelector.currentAccountId = parseInt(accountIdParam);
            
            // 更新账户选择器按钮文本
            const accountSelectorBtn = document.getElementById('accountSelectorBtn');
            if (accountSelectorBtn) {
                // 当账户列表加载完成后更新按钮文本
                const checkAccountLoaded = setInterval(function() {
                    if (AccountSelector.accounts && AccountSelector.accounts.length > 0) {
                        clearInterval(checkAccountLoaded);
                        
                        // 查找匹配的账户
                        const selectedAccount = AccountSelector.accounts.find(acc => acc.id === parseInt(accountIdParam));
                        if (selectedAccount) {
                            accountSelectorBtn.innerText = selectedAccount.name;
                            
                            // 更新下拉菜单项的活跃状态
                            const accountSelectorMenu = document.getElementById('accountSelectorMenu');
                            if (accountSelectorMenu) {
                                accountSelectorMenu.querySelectorAll('a.dropdown-item').forEach(item => {
                                    item.classList.remove('active');
                                    if (item.getAttribute('data-account-id') === accountIdParam) {
                                        item.classList.add('active');
                                    }
                                });
                            }
                        }
                    }
                }, 100);
            }
        }
    }
    
    // 重写accountChanged事件，使其不刷新整个页面
    window.originalAccountChangedListener = [];
    
    // 保存原有的监听器
    const originalListeners = window._events ? window._events['accountChanged'] : [];
    if (originalListeners && originalListeners.length) {
        window.originalAccountChangedListener = originalListeners;
        
        // 移除所有现有的accountChanged监听器
        document.removeEventListener('accountChanged', window.originalAccountChangedListener[0]);
    }
    
    // 添加新的处理函数
    document.addEventListener('accountChanged', function(e) {
        // 触发统计数据重新加载，但不刷新页面
        const reloadEvent = new CustomEvent('reloadStatistics', { 
            detail: { accountId: e.detail.accountId } 
        });
        document.dispatchEvent(reloadEvent);
        
        // 获取当前URL
        const currentUrl = new URL(window.location.href);
        
        // 更新URL参数
        if (e.detail.accountId) {
            currentUrl.searchParams.set('account_id', e.detail.accountId);
        } else {
            currentUrl.searchParams.delete('account_id');
        }
        
        // 使用pushState更新URL而不刷新页面
        window.history.pushState({}, '', currentUrl.toString());
        
        // 给一个小的延迟，然后创建一个表单并提交到当前URL
        setTimeout(function() {
            // 创建表单
            const form = document.createElement('form');
            form.method = 'GET';
            form.action = currentUrl.toString();
            form.style.display = 'none';
            
            // 添加keep_panel=true参数，服务端可以据此保持面板打开
            const keepPanelInput = document.createElement('input');
            keepPanelInput.type = 'hidden';
            keepPanelInput.name = 'keep_panel';
            keepPanelInput.value = 'true';
            form.appendChild(keepPanelInput);
            
            // 如果有账户ID，添加到表单
            if (e.detail.accountId) {
                const accountInput = document.createElement('input');
                accountInput.type = 'hidden';
                accountInput.name = 'account_id';
                accountInput.value = e.detail.accountId;
                form.appendChild(accountInput);
            }
            
            // 添加到文档并提交
            document.body.appendChild(form);
            form.submit();
        }, 100);
    });
}); 