/**
 * 厂商销售负责人选择器工具
 * 提供统一的厂商销售负责人加载和显示逻辑
 */

/**
 * 获取部门优先级
 * @param {string} department - 部门名称
 * @returns {number} 优先级数字（越小越优先）
 */
function getDepartmentPriority(department) {
    if (department === '销售部') return 1;
    if (department === '服务部') return 2;
    return 3;
}

/**
 * 按部门优先级和姓名排序用户列表
 * @param {Array} users - 用户列表
 * @returns {Array} 排序后的用户列表
 */
function sortUsersByDepartmentPriority(users) {
    return users.sort((a, b) => {
        const priorityA = getDepartmentPriority(a.department);
        const priorityB = getDepartmentPriority(b.department);

        // 先按部门优先级排序
        if (priorityA !== priorityB) {
            return priorityA - priorityB;
        }

        // 同一优先级内按姓名排序
        const nameA = a.real_name || a.name || '';
        const nameB = b.real_name || b.name || '';
        return nameA.localeCompare(nameB, 'zh-CN');
    });
}

/**
 * 从API响应数据中收集所有用户
 * @param {Array} companies - 公司数据列表
 * @returns {Array} 所有用户的扁平列表
 */
function collectAllUsers(companies) {
    const allUsers = [];
    companies.forEach(company => {
        if (company.users && company.users.length > 0) {
            company.users.forEach(user => {
                allUsers.push(user);
            });
        }
    });
    return allUsers;
}

/**
 * 格式化用户显示文本
 * @param {Object} user - 用户对象
 * @returns {string} 格式化后的显示文本 "姓名 (部门)"
 */
function formatUserDisplayText(user) {
    const displayName = user.real_name || user.name;
    const department = user.department || '未知部门';
    return `${displayName} (${department})`;
}

/**
 * 加载厂商销售负责人到下拉选择器
 * @param {string} selectElementId - 选择器元素ID
 * @param {Object} options - 配置选项
 * @param {number} options.selectedUserId - 当前选中的用户ID（编辑模式使用）
 * @param {boolean} options.autoSelectCurrentUser - 是否自动选择当前用户（当前用户是厂商时）
 * @param {number} options.currentUserId - 当前登录用户ID
 * @param {boolean} options.currentUserIsVendor - 当前用户是否是厂商
 * @param {string} options.emptyText - 默认选项文本，默认为"请选择厂商销售负责人"
 * @returns {Promise<void>}
 */
async function loadVendorSalesManagers(selectElementId, options = {}) {
    const {
        selectedUserId = null,
        autoSelectCurrentUser = false,
        currentUserId = null,
        currentUserIsVendor = false,
        emptyText = '请选择厂商销售负责人'
    } = options;

    try {
        // 调用API获取厂商用户数据
        const response = await fetch('/api/users/hierarchical?vendor_only=true');
        const data = await response.json();

        const vendorSelect = document.getElementById(selectElementId);
        if (!vendorSelect) {
            console.error(`找不到ID为 ${selectElementId} 的选择器元素`);
            return;
        }

        // 清空并设置默认选项
        vendorSelect.innerHTML = `<option value="">${emptyText}</option>`;

        if (data.success && data.data) {
            // 收集所有用户
            const allUsers = collectAllUsers(data.data);

            // 按部门优先级排序
            const sortedUsers = sortUsersByDepartmentPriority(allUsers);

            // 显示排序后的用户列表
            sortedUsers.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.textContent = formatUserDisplayText(user);

                // 编辑模式：选中指定的用户
                if (selectedUserId && user.id === selectedUserId) {
                    option.selected = true;
                    console.log(`选中负责人: ${option.textContent} (ID: ${user.id})`);
                }

                vendorSelect.appendChild(option);
            });

            // 自动选择当前用户（仅在创建模式且当前用户是厂商时）
            if (autoSelectCurrentUser && currentUserIsVendor && currentUserId) {
                vendorSelect.value = currentUserId;
                console.log(`自动选择当前厂商用户作为负责人 (ID: ${currentUserId})`);
            }
        } else {
            console.warn('API响应格式不正确或没有数据:', data);
        }
    } catch (error) {
        console.error('加载厂商销售负责人失败:', error);
    }
}
