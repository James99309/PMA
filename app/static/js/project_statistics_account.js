/**
 * 项目统计账户切换功能模块
 * 用于处理统计面板中的账户切换相关功能
 */

// 账户选择器管理器
const AccountSelector = {
    // 当前选中的账户ID
    currentAccountId: null,
    
    // 可用账户列表
    accounts: [],
    
    // 初始化账户选择器
    init: function() {
        const accountSelectorBtn = document.getElementById('accountSelectorBtn');
        const accountSelectorMenu = document.getElementById('accountSelectorMenu');
        
        if (!accountSelectorBtn || !accountSelectorMenu) return;
        
        // 监听全部账户选项的点击
        const allAccountsItem = accountSelectorMenu.querySelector('a[data-account-id="all"]');
        if (allAccountsItem) {
            allAccountsItem.addEventListener('click', function(e) {
                e.preventDefault();
                
                // 更新账户选择器按钮文本
                accountSelectorBtn.innerText = this.textContent;
                
                // 更新活跃状态
                accountSelectorMenu.querySelectorAll('a.dropdown-item').forEach(item => {
                    item.classList.remove('active');
                });
                this.classList.add('active');
                
                // 切换到全部账户并重新加载数据
                AccountSelector.currentAccountId = null;
                
                // 触发账户变更事件
                const event = new CustomEvent('accountChanged', { 
                    detail: { accountId: null } 
                });
                document.dispatchEvent(event);
            });
        }
        
        // 加载账户列表
        this.loadAccountsList();
    },
    
    // 加载账户列表
    loadAccountsList: function() {
        const accountSelectorMenu = document.getElementById('accountSelectorMenu');
        if (!accountSelectorMenu) return;
        
        // 清除现有账户列表，保留"全部账户"选项和加载指示器
        const allAccountsItem = accountSelectorMenu.querySelector('a[data-account-id="all"]');
        const loadingItem = accountSelectorMenu.querySelector('.spinner-border-sm');
        const loadingItemParent = loadingItem ? loadingItem.closest('li') : null;
        
        // 账户列表的分隔线
        const divider = accountSelectorMenu.querySelector('hr.dropdown-divider');
        const dividerParent = divider ? divider.closest('li') : null;
        
        // 清除已有账户条目
        accountSelectorMenu.querySelectorAll('li').forEach(li => {
            if (li !== allAccountsItem.parentElement && li !== loadingItemParent && li !== dividerParent) {
                li.remove();
            }
        });
        
        // 显示加载指示器
        if (loadingItemParent) {
            loadingItemParent.style.display = 'block';
        }
        
        // 请求账户列表数据
        fetch(`/projectpm/statistics/api/available_accounts`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('请求失败');
                }
                return response.json();
            })
            .then(data => {
                // 隐藏加载指示器
                if (loadingItemParent) {
                    loadingItemParent.style.display = 'none';
                }
                
                if (data.success && data.data) {
                    this.accounts = data.data;
                    
                    // 如果没有账户数据，显示提示
                    if (this.accounts.length === 0) {
                        const noAccountsItem = document.createElement('li');
                        noAccountsItem.innerHTML = '<a class="dropdown-item text-muted fst-italic">无可用账户数据</a>';
                        accountSelectorMenu.appendChild(noAccountsItem);
                        return;
                    }
                    
                    // 添加账户列表
                    this.accounts.forEach(account => {
                        const accountItem = document.createElement('li');
                        accountItem.innerHTML = `<a class="dropdown-item" href="#" data-account-id="${account.id}">${account.name}</a>`;
                        accountSelectorMenu.appendChild(accountItem);
                        
                        // 添加点击事件
                        const accountLink = accountItem.querySelector('a');
                        accountLink.addEventListener('click', (e) => {
                            e.preventDefault();
                            
                            // 获取账户ID
                            const accountId = accountLink.getAttribute('data-account-id');
                            
                            // 更新账户选择器按钮文本
                            document.getElementById('accountSelectorBtn').innerText = accountLink.textContent;
                            
                            // 更新活跃状态
                            accountSelectorMenu.querySelectorAll('a.dropdown-item').forEach(item => {
                                item.classList.remove('active');
                            });
                            accountLink.classList.add('active');
                            
                            // 切换账户
                            this.currentAccountId = parseInt(accountId);
                            
                            // 触发账户变更事件
                            const event = new CustomEvent('accountChanged', { 
                                detail: { accountId: this.currentAccountId } 
                            });
                            document.dispatchEvent(event);
                        });
                    });
                } else {
                    // 显示错误提示
                    const errorItem = document.createElement('li');
                    errorItem.innerHTML = '<a class="dropdown-item text-danger"><i class="fas fa-exclamation-triangle me-1"></i> 加载账户列表失败</a>';
                    accountSelectorMenu.appendChild(errorItem);
                }
            })
            .catch(error => {
                console.error('加载账户列表失败:', error);
                
                // 隐藏加载指示器
                if (loadingItemParent) {
                    loadingItemParent.style.display = 'none';
                }
                
                // 显示错误提示
                const errorItem = document.createElement('li');
                errorItem.innerHTML = '<a class="dropdown-item text-danger"><i class="fas fa-exclamation-triangle me-1"></i> 加载账户列表失败</a>';
                accountSelectorMenu.appendChild(errorItem);
            });
    },
    
    // 获取当前选中的账户ID
    getCurrentAccountId: function() {
        return this.currentAccountId;
    },
    
    // 为URL添加账户参数
    appendAccountParam: function(url) {
        if (this.currentAccountId) {
            const separator = url.includes('?') ? '&' : '?';
            return `${url}${separator}account_id=${this.currentAccountId}`;
        }
        return url;
    }
};

// 文档加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化账户选择器
    AccountSelector.init();
    
    // 监听账户变更事件，重新加载数据
    document.addEventListener('accountChanged', function(e) {
        // 触发重新加载数据的自定义事件
        const reloadEvent = new CustomEvent('reloadStatistics', { 
            detail: { accountId: e.detail.accountId } 
        });
        document.dispatchEvent(reloadEvent);
        
        // 获取当前URL信息
        const currentUrl = new URL(window.location.href);
        
        // 清除现有的account_id参数
        currentUrl.searchParams.delete('account_id');
        
        // 如果选择了特定账户，则添加参数
        if (e.detail.accountId) {
            currentUrl.searchParams.set('account_id', e.detail.accountId);
        }
        
        // 更新URL但不刷新页面
        window.history.pushState({}, '', currentUrl.toString());
        
        // 如果存在客户端过滤函数，则应用账户筛选
        if (typeof filterProjectsByAccount === 'function') {
            filterProjectsByAccount(e.detail.accountId);
        }
    });
}); 