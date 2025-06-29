/**
 * 客户账户选择器 - 基于权限管理的全新实现
 * 支持账户筛选和只看自己开关联动
 */

const CustomerAccountSelector = {
    // 当前状态
    currentAccountId: null,
    accounts: [],
    isMyCustomersOnly: false,
    
    // DOM元素
    elements: {
        accountBtn: null,
        accountMenu: null,
        myCustomersSwitch: null
    },
    
    // 初始化
    init: function() {
        console.log('🚀 初始化客户账户选择器...');
        
        // 获取DOM元素
        this.elements.accountBtn = document.getElementById('accountSelectorBtn');
        this.elements.accountMenu = document.getElementById('accountSelectorMenu');
        this.elements.myCustomersSwitch = document.getElementById('showMyCustomersSwitch');
        
        if (!this.elements.accountBtn || !this.elements.accountMenu) {
            console.warn('⚠️ 账户选择器元素未找到');
            return;
        }
        
        // 绑定事件
        this.bindEvents();
        
        // 加载账户列表
        this.loadAccounts();
        
        // 从URL同步状态
        this.syncFromURL();
    },
    
    // 绑定事件
    bindEvents: function() {
        // 全部账户选项点击事件
        const allAccountsItem = this.elements.accountMenu.querySelector('a[data-account-id="all"]');
        if (allAccountsItem) {
            allAccountsItem.addEventListener('click', (e) => {
                e.preventDefault();
                this.selectAccount('all', '全部账户');
            });
        }
        
        // 只看自己开关事件
        if (this.elements.myCustomersSwitch) {
            this.elements.myCustomersSwitch.addEventListener('change', (e) => {
                this.handleMyCustomersToggle(e.target.checked);
            });
        }
    },
    
    // 加载账户列表
    loadAccounts: function() {
        console.log('📡 加载账户列表...');
        
        // 显示加载状态
        this.showLoading(true);
        
        fetch('/customer/api/available_accounts')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                this.showLoading(false);
                
                if (data.success && Array.isArray(data.data)) {
                    this.accounts = data.data;
                    this.renderAccounts();
                    console.log(`✅ 成功加载 ${this.accounts.length} 个账户`);
                } else {
                    throw new Error(data.message || '返回数据格式错误');
                }
            })
            .catch(error => {
                this.showLoading(false);
                console.error('❌ 加载账户列表失败:', error);
                this.showError('加载账户列表失败: ' + error.message);
            });
    },
    
    // 渲染账户列表
    renderAccounts: function() {
        if (!this.elements.accountMenu || !Array.isArray(this.accounts)) return;
        
        // 清除现有账户项（保留全部账户选项）
        const existingItems = this.elements.accountMenu.querySelectorAll('li:not(:first-child):not(:nth-child(2))');
        existingItems.forEach(item => item.remove());
        
        // 添加账户选项
        this.accounts.forEach(account => {
            const accountItem = document.createElement('li');
            accountItem.innerHTML = `
                <a class="dropdown-item" href="#" data-account-id="${account.id}">
                    ${account.name}${account.is_current_user ? ' (我)' : ''}
                </a>
            `;
            this.elements.accountMenu.appendChild(accountItem);
            
            // 绑定点击事件
            const accountLink = accountItem.querySelector('a');
            accountLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.selectAccount(account.id.toString(), account.name);
            });
        });
    },
    
    // 选择账户
    selectAccount: function(accountId, accountName) {
        console.log(`🎯 选择账户: ${accountName} (ID: ${accountId})`);
        
        // 更新按钮文本
        this.elements.accountBtn.textContent = accountName;
        
        // 更新活跃状态
        this.elements.accountMenu.querySelectorAll('a.dropdown-item').forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-account-id') === accountId) {
                item.classList.add('active');
            }
        });
        
        // 更新内部状态
        this.currentAccountId = accountId === 'all' ? null : parseInt(accountId);
        
        // 联动处理只看自己开关
        this.syncMyCustomersSwitch();
        
        // 应用筛选
        this.applyFilter();
    },
    
    // 处理只看自己开关切换
    handleMyCustomersToggle: function(isChecked) {
        console.log(`🔄 只看自己开关: ${isChecked ? '开启' : '关闭'}`);
        
        this.isMyCustomersOnly = isChecked;
        
        if (isChecked) {
            // 开启只看自己时，自动选择当前用户账户
            const currentUserAccount = this.accounts.find(acc => acc.is_current_user);
            if (currentUserAccount) {
                this.selectAccount(currentUserAccount.id.toString(), currentUserAccount.name);
                return; // selectAccount会调用applyFilter，所以这里直接返回
            }
        }
        
        // 应用筛选
        this.applyFilter();
    },
    
    // 同步只看自己开关状态
    syncMyCustomersSwitch: function() {
        if (!this.elements.myCustomersSwitch) return;
        
        // 如果选择的是当前用户账户，开启只看自己开关
        const selectedAccount = this.accounts.find(acc => acc.id === this.currentAccountId);
        if (selectedAccount && selectedAccount.is_current_user) {
            this.elements.myCustomersSwitch.checked = true;
            this.isMyCustomersOnly = true;
        } else {
            // 选择全部账户或其他用户账户时，关闭只看自己开关
            this.elements.myCustomersSwitch.checked = false;
            this.isMyCustomersOnly = false;
        }
    },
    
    // 从URL同步状态
    syncFromURL: function() {
        const urlParams = new URLSearchParams(window.location.search);
        const accountIdParam = urlParams.get('account_id');
        const myCustomersParam = urlParams.get('my_customers');
        
        console.log('🔄 从URL同步状态:', { accountIdParam, myCustomersParam });
        
        // 同步只看自己状态
        if (myCustomersParam === '1') {
            this.isMyCustomersOnly = true;
            if (this.elements.myCustomersSwitch) {
                this.elements.myCustomersSwitch.checked = true;
            }
        }
        
        // 同步账户选择状态（需要等待账户列表加载完成）
        if (accountIdParam) {
            const checkAndSync = () => {
                if (this.accounts.length > 0) {
                    const selectedAccount = this.accounts.find(acc => acc.id === parseInt(accountIdParam));
                    if (selectedAccount) {
                        this.currentAccountId = selectedAccount.id;
                        this.elements.accountBtn.textContent = selectedAccount.name;
                        
                        // 更新下拉菜单活跃状态
                        this.elements.accountMenu.querySelectorAll('a.dropdown-item').forEach(item => {
                            item.classList.remove('active');
                            if (item.getAttribute('data-account-id') === accountIdParam) {
                                item.classList.add('active');
                            }
                        });
                    }
                } else {
                    // 如果账户还没加载完，继续等待
                    setTimeout(checkAndSync, 100);
                }
            };
            checkAndSync();
        }
    },
    
    // 应用筛选
    applyFilter: function() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // 更新账户ID参数
        if (this.currentAccountId) {
            urlParams.set('account_id', this.currentAccountId);
        } else {
            urlParams.delete('account_id');
        }
        
        // 更新只看自己参数
        if (this.isMyCustomersOnly) {
            urlParams.set('my_customers', '1');
        } else {
            urlParams.delete('my_customers');
        }
        
        // 重新加载页面
        const newUrl = window.location.pathname + '?' + urlParams.toString();
        console.log('🔄 应用筛选，跳转到:', newUrl);
        window.location.href = newUrl;
    },
    
    // 显示/隐藏加载状态
    showLoading: function(show) {
        const loadingItem = this.elements.accountMenu?.querySelector('.spinner-border-sm');
        if (loadingItem) {
            loadingItem.closest('li').style.display = show ? 'block' : 'none';
        }
    },
    
    // 显示错误信息
    showError: function(message) {
        if (!this.elements.accountMenu) return;
        
        // 移除现有错误项
        const existingError = this.elements.accountMenu.querySelector('.text-danger');
        if (existingError) {
            existingError.closest('li').remove();
        }
        
        // 添加错误项
        const errorItem = document.createElement('li');
        errorItem.innerHTML = `<a class="dropdown-item text-danger"><i class="fas fa-exclamation-triangle me-2"></i>${message}</a>`;
        this.elements.accountMenu.appendChild(errorItem);
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 延迟初始化，确保页面完全加载
    setTimeout(() => {
        CustomerAccountSelector.init();
    }, 100);
});

// 导出到全局作用域（兼容性）
window.CustomerAccountSelector = CustomerAccountSelector;
