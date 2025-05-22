/**
 * 项目列表页面账户选择器初始化
 * 确保项目列表页与账户选择器保持同步，使用客户端过滤代替页面刷新
 */
document.addEventListener('DOMContentLoaded', function() {
    // 检查URL中是否有account_id参数，并更新选择器状态
    function initAccountSelector() {
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
                
                // 应用账户筛选
                setTimeout(function() {
                    filterProjectsByAccount(parseInt(accountIdParam));
                }, 300);
            }
        }
    }
    
    // 初始化账户选择器
    initAccountSelector();
});

/**
 * 根据账户ID在客户端过滤项目
 * @param {number|null} accountId - 账户ID，为null则显示所有项目
 */
function filterProjectsByAccount(accountId) {
    console.log('客户端过滤账户:', accountId);
    
    // 获取所有行和卡片
    const tableRows = document.querySelectorAll('.table tbody tr');
    const mobileCards = document.querySelectorAll('.d-block.d-lg-none .card');
    const tableBody = document.querySelector('.table tbody');
    const mobileContainer = document.querySelector('.d-block.d-lg-none');
    
    // 如果没有指定账户ID，显示所有项目
    if (!accountId) {
        console.log('未指定账户ID，显示所有项目');
        
        // 显示所有表格行和卡片
        tableRows.forEach(row => {
            row.classList.remove('filtered');
            row.style.display = '';
        });
        
        mobileCards.forEach(card => {
            card.classList.remove('filtered');
            card.style.display = '';
        });
        
        // 按更新时间重排序
        restoreAllRecordsWithSorting(tableRows, mobileCards, tableBody, mobileContainer);
        
        // 更新按钮状态
        triggerFilterStatusUpdate();
        
        // 触发统计数据更新 - 添加统计面板刷新
        triggerStatisticsUpdate();
        
        return;
    }
    
    // 用于存储匹配和筛选的行和卡片
    const matchedRows = [];
    const filteredRows = [];
    const matchedCards = [];
    const filteredCards = [];
    
    // 检查每一行是否属于指定账户
    tableRows.forEach(row => {
        let shouldFilter = true;
        
        // 查找拥有者ID
        const ownerSpan = row.querySelector('[data-owner-id]');
        if (ownerSpan) {
            const ownerId = parseInt(ownerSpan.getAttribute('data-owner-id'));
            const memberSpan = row.querySelector('[data-member-ids]');
            
            // 检查是否属于指定账户
            if (ownerId === accountId) {
                // 如果拥有者ID匹配，则不过滤
                shouldFilter = false;
            } else if (memberSpan) {
                // 如果有团队成员，检查团队成员是否包括指定账户
                const memberIds = memberSpan.getAttribute('data-member-ids').split(',').map(Number);
                if (memberIds.includes(accountId)) {
                    shouldFilter = false;
                }
            }
        }
        
        // 根据筛选结果，分类存储
        if (shouldFilter) {
            row.classList.add('filtered');
            filteredRows.push(row);
        } else {
            row.classList.remove('filtered');
            matchedRows.push(row);
        }
    });
    
    // 检查每个卡片是否属于指定账户
    mobileCards.forEach(card => {
        let shouldFilter = true;
        
        // 查找拥有者ID
        const ownerSpan = card.querySelector('[data-owner-id]');
        if (ownerSpan) {
            const ownerId = parseInt(ownerSpan.getAttribute('data-owner-id'));
            const memberSpan = card.querySelector('[data-member-ids]');
            
            // 检查是否属于指定账户
            if (ownerId === accountId) {
                // 如果拥有者ID匹配，则不过滤
                shouldFilter = false;
            } else if (memberSpan) {
                // 如果有团队成员，检查团队成员是否包括指定账户
                const memberIds = memberSpan.getAttribute('data-member-ids').split(',').map(Number);
                if (memberIds.includes(accountId)) {
                    shouldFilter = false;
                }
            }
        }
        
        // 根据筛选结果，分类存储
        if (shouldFilter) {
            card.classList.add('filtered');
            filteredCards.push(card);
        } else {
            card.classList.remove('filtered');
            matchedCards.push(card);
        }
    });
    
    // 按更新时间对匹配项排序
    const sortByUpdatedAtDesc = (a, b) => {
        // 尝试从元素中获取更新时间
        const getUpdatedAt = (el) => {
            // 从表格行中提取更新时间（假设在倒数第二列）
            if (!el.classList.contains('card')) {
                // PC端表格视图
                const cells = el.querySelectorAll('td');
                if (cells.length > 2) {
                    const updatedAtCell = cells[cells.length - 2]; // 倒数第二列是更新时间
                    if (updatedAtCell) {
                        const dateText = updatedAtCell.textContent.trim();
                        if (dateText) {
                            return new Date(dateText).getTime();
                        }
                    }
                }
            } else {
                // 移动端卡片视图
                const updatedAtText = el.textContent.match(/更新: (\d{4}-\d{2}-\d{2})/);
                if (updatedAtText && updatedAtText[1]) {
                    return new Date(updatedAtText[1]).getTime();
                }
            }
            return 0; // 默认时间戳
        };
        
        const updatedAtA = getUpdatedAt(a);
        const updatedAtB = getUpdatedAt(b);
        return updatedAtB - updatedAtA; // 降序排列（新到旧）
    };
    
    // 对匹配的行和卡片按更新时间排序
    matchedRows.sort(sortByUpdatedAtDesc);
    matchedCards.sort(sortByUpdatedAtDesc);
    
    // 重新排列表格行：匹配的行在前，被过滤的行隐藏
    if (tableBody) {
        // 清空表格
        while (tableBody.firstChild) {
            tableBody.removeChild(tableBody.firstChild);
        }
        
        // 添加匹配的行
        matchedRows.forEach(row => {
            tableBody.appendChild(row);
            row.style.display = '';
        });
        
        // 被过滤的行不显示，但仍添加到DOM
        filteredRows.forEach(row => {
            row.style.display = 'none';
            tableBody.appendChild(row);
        });
    }
    
    // 重新排列移动端卡片：匹配的卡片在前，被过滤的卡片隐藏
    if (mobileContainer) {
        // 保存所有非卡片元素
        const nonCardElements = Array.from(mobileContainer.children).filter(el => 
            !el.classList.contains('card')
        );
        
        // 清空容器
        while (mobileContainer.firstChild) {
            mobileContainer.removeChild(mobileContainer.firstChild);
        }
        
        // 首先添加非卡片元素（如警告、提示等）
        nonCardElements.forEach(el => {
            mobileContainer.appendChild(el);
        });
        
        // 添加匹配的卡片
        matchedCards.forEach(card => {
            mobileContainer.appendChild(card);
            card.style.display = '';
        });
        
        // 被过滤的卡片不显示，但仍添加到DOM
        filteredCards.forEach(card => {
            card.style.display = 'none';
            mobileContainer.appendChild(card);
        });
    }
    
    // 更新筛选状态（返回按钮）
    if (typeof updateClearButtonState === 'function') {
        setTimeout(updateClearButtonState, 0);
    }
    
    // 触发统计数据更新 - 添加统计面板刷新
    triggerStatisticsUpdate();
    
    // 如果没有匹配项，显示提示
    if (matchedRows.length === 0 && matchedCards.length === 0) {
        console.log('没有属于该账户的项目');
        // 可以添加一个提示元素
        addNoProjectsAlert(tableBody, mobileContainer);
    }
}

/**
 * 添加"无项目"提示
 */
function addNoProjectsAlert(tableBody, mobileContainer) {
    // 给PC端表格添加提示
    if (tableBody) {
        const alertRow = document.createElement('tr');
        alertRow.innerHTML = `<td colspan="20" class="text-center py-4">
            <div class="alert alert-info mb-0">
                <i class="fas fa-info-circle me-2"></i> 当前账户下没有项目
            </div>
        </td>`;
        tableBody.appendChild(alertRow);
    }
    
    // 给移动端添加提示
    if (mobileContainer) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-info my-3';
        alertDiv.innerHTML = '<i class="fas fa-info-circle me-2"></i> 当前账户下没有项目';
        mobileContainer.prepend(alertDiv);
    }
}

/**
 * 按更新时间重新排序并显示所有记录
 */
function restoreAllRecordsWithSorting(tableRows, mobileCards, tableBody, mobileContainer) {
    // 按更新时间排序的函数
    const sortByUpdatedAtDesc = (a, b) => {
        // 尝试从元素中获取更新时间
        const getUpdatedAt = (el) => {
            // 从表格行中提取更新时间（假设在倒数第二列）
            if (!el.classList.contains('card')) {
                // PC端表格视图
                const cells = el.querySelectorAll('td');
                if (cells.length > 2) {
                    const updatedAtCell = cells[cells.length - 2]; // 倒数第二列是更新时间
                    if (updatedAtCell) {
                        const dateText = updatedAtCell.textContent.trim();
                        if (dateText) {
                            return new Date(dateText).getTime();
                        }
                    }
                }
            } else {
                // 移动端卡片视图
                const updatedAtText = el.textContent.match(/更新: (\d{4}-\d{2}-\d{2})/);
                if (updatedAtText && updatedAtText[1]) {
                    return new Date(updatedAtText[1]).getTime();
                }
            }
            return 0; // 默认时间戳
        };
        
        const updatedAtA = getUpdatedAt(a);
        const updatedAtB = getUpdatedAt(b);
        return updatedAtB - updatedAtA; // 降序排列（新到旧）
    };
    
    // 复制行到数组，以便排序
    const allRows = Array.from(tableRows);
    const allCards = Array.from(mobileCards);
    
    // 按更新时间排序
    allRows.sort(sortByUpdatedAtDesc);
    allCards.sort(sortByUpdatedAtDesc);
    
    // 清空并重新填充表格
    if (tableBody) {
        while (tableBody.firstChild) {
            tableBody.removeChild(tableBody.firstChild);
        }
        
        allRows.forEach(row => {
            row.classList.remove('filtered');
            row.style.display = '';
            tableBody.appendChild(row);
        });
    }
    
    // 清空并重新填充移动容器
    if (mobileContainer) {
        // 保存所有非卡片元素
        const nonCardElements = Array.from(mobileContainer.children).filter(el => 
            !el.classList.contains('card')
        );
        
        // 清空容器
        while (mobileContainer.firstChild) {
            mobileContainer.removeChild(mobileContainer.firstChild);
        }
        
        // 首先添加非卡片元素
        nonCardElements.forEach(el => {
            mobileContainer.appendChild(el);
        });
        
        // 然后添加所有卡片
        allCards.forEach(card => {
            card.classList.remove('filtered');
            card.style.display = '';
            mobileContainer.appendChild(card);
        });
    }
}

/**
 * 触发按钮状态更新，可以在统计面板中调用
 */
function triggerFilterStatusUpdate() {
    if (typeof window.updateClearButtonState === 'function') {
        setTimeout(window.updateClearButtonState, 0);
    }
}

/**
 * 触发统计面板数据重新加载
 */
function triggerStatisticsUpdate() {
    // 触发统计数据重新加载事件
    const event = new CustomEvent('reloadStatistics', {
        detail: { refresh: true }
    });
    document.dispatchEvent(event);
    
    // 清除统计卡片的筛选状态
    const statisticsCards = [
        document.getElementById('validProjectsCard'),
        document.getElementById('tenderingProjectsCard'),
        document.getElementById('wonProjectsCard'),
        document.getElementById('updatedProjectsCard')
    ];
    
    statisticsCards.forEach(card => {
        if (card) {
            card.classList.remove('active-filter');
        }
    });
    
    // 清除业务推进筛选URL参数，如果存在
    if (window.location.search.includes('filter_updated_this_month')) {
        const updatedParams = new URLSearchParams(window.location.search);
        updatedParams.delete('filter_updated_this_month');
        window.history.replaceState(null, '', window.location.pathname + 
          (updatedParams.toString() ? '?' + updatedParams.toString() : ''));
    }
} 