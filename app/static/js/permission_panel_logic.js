/**
 * 通用权限面板JavaScript逻辑
 *
 * 功能：提供权限配置面板的通用功能，支持角色权限和个人权限两种模式
 *
 * 使用方式：
 * 1. 在页面中包含此脚本
 * 2. 确保页面已通过 permissionPanelConfig 注入配置数据
 * 3. 调用 PermissionPanel.init(configKey) 初始化面板
 */

const PermissionPanel = (function() {
    'use strict';

    // 私有变量
    let currentRole = null;
    let currentPermissions = [];
    let currentSelectedModule = null;
    let modulePermissionsCache = {};
    let hasUnsavedChanges = false;
    let pendingRoleSwitch = null;
    let isEditMode = false;          // 是否处于编辑模式
    let panelInitialized = false;    // 编辑面板是否已初始化

    // 配置数据
    let config = null;
    let MODULES = [];
    let CONTENT_FILTER_OPTIONS = {};
    let moduleMetadata = {};
    let permissionLevels = [];

    /**
     * 显示通知消息（兼容 Bootstrap 和 Tailwind 页面）
     * 如果页面已定义 showNotification 则使用它，否则使用内置的 Tailwind 风格通知
     */
    function showNotification(message, type = 'info', duration = 3000) {
        // 如果页面已有 showNotification 函数，则使用它
        if (typeof window.showNotification === 'function') {
            window.showNotification(message, type, duration);
            return;
        }

        // 否则使用内置的 Tailwind 风格通知
        const typeStyles = {
            success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 border-green-200 dark:border-green-800',
            error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300 border-red-200 dark:border-red-800',
            warning: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300 border-amber-200 dark:border-amber-800',
            info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 border-blue-200 dark:border-blue-800'
        };

        const icons = {
            success: 'check_circle',
            error: 'error',
            warning: 'warning',
            info: 'info'
        };

        // 移除已有的通知
        const existing = document.getElementById('permissionPanelNotification');
        if (existing) existing.remove();

        // 创建通知元素
        const notification = document.createElement('div');
        notification.id = 'permissionPanelNotification';
        notification.className = `fixed top-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 px-4 py-3 rounded-lg border shadow-lg transition-all duration-300 ${typeStyles[type] || typeStyles.info}`;
        notification.innerHTML = `
            <span class="material-symbols-outlined text-xl">${icons[type] || icons.info}</span>
            <span class="text-sm font-medium">${message}</span>
            <button onclick="this.parentElement.remove()" class="ml-2 opacity-60 hover:opacity-100">
                <span class="material-symbols-outlined text-lg">close</span>
            </button>
        `;

        document.body.appendChild(notification);

        // 自动移除
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.style.opacity = '0';
                    notification.style.transform = 'translate(-50%, -20px)';
                    setTimeout(() => notification.remove(), 300);
                }
            }, duration);
        }
    }

    /**
     * 初始化权限面板
     * @param {String} configKey - 配置键名（格式：contextType_contextId）
     */
    function init(configKey) {
        // 加载配置
        if (!window.permissionPanelConfig || !window.permissionPanelConfig[configKey]) {
            console.error('未找到权限面板配置:', configKey);
            return;
        }

        config = window.permissionPanelConfig[configKey];
        MODULES = config.modules || [];
        currentPermissions = config.permissions || [];
        CONTENT_FILTER_OPTIONS = config.filterConfigs || {};

        console.log('权限面板初始化:', config.contextType, config.contextId);

        // 绑定模式切换事件（立即绑定，不依赖元数据加载）
        attachModeToggleListeners();

        // 注意：编辑面板的初始化延迟到进入编辑模式时执行
        // 这样可以在查看模式下避免不必要的API调用和DOM操作
    }

    /**
     * 初始化编辑面板（进入编辑模式时调用）
     */
    function initEditPanel() {
        if (panelInitialized) {
            console.log('编辑面板已初始化，跳过');
            return Promise.resolve();
        }

        console.log('初始化编辑面板...');

        // 加载模块元数据
        return loadModuleMetadata().then(() => {
            // 渲染模块列表
            renderModuleList();

            // 自动选择第一个模块
            if (MODULES && MODULES.length > 0) {
                selectModule(MODULES[0].id);
            }

            // 绑定事件监听器
            attachEventListeners();

            // 初始化保存按钮状态
            updateSaveButtonState();

            panelInitialized = true;
            console.log('✅ 编辑面板初始化完成');
        });
    }

    /**
     * 加载模块元数据
     */
    async function loadModuleMetadata() {
        try {
            const response = await fetch('/api/v1/permissions/module-metadata');
            const data = await response.json();

            if (data.success) {
                moduleMetadata = data.data.modules;
                permissionLevels = data.data.levels;
                console.log('✅ 模块元数据加载成功:', Object.keys(moduleMetadata).length, '个模块');
                return true;
            } else {
                console.error('❌ 加载模块元数据失败:', data.message);
                return false;
            }
        } catch (error) {
            console.error('❌ 加载模块元数据异常:', error);
            return false;
        }
    }

    /**
     * 获取模块图标
     */
    function getModuleIcon(moduleId) {
        return moduleMetadata[moduleId]?.icon || 'fas fa-cube';
    }

    /**
     * 获取模块名称
     */
    function getModuleName(moduleId) {
        return moduleMetadata[moduleId]?.name || moduleId;
    }

    /**
     * 检查模块是否支持折扣权限
     */
    function hasDiscountPermission(moduleId) {
        return moduleMetadata[moduleId]?.supports_discount === true;
    }

    /**
     * 检查模块是否支持拥有人修改权限
     */
    function hasOwnerChangePermission(moduleId) {
        return moduleMetadata[moduleId]?.supports_owner_change === true;
    }

    /**
     * 检查模块是否启用
     * 只有权限级别为 'none' 时才算未启用
     * 其他级别（personal/department/company/system）都视为启用，因为用户至少可以查看自己的数据
     */
    function isModuleEnabled(permission) {
        if (!permission) return false;

        // 只有权限级别为 'none' 时，模块才算未启用
        return permission.permission_level !== 'none';
    }

    /**
     * 获取 Material Symbols 图标名称（从 FontAwesome 映射）
     */
    function getMaterialIcon(moduleId) {
        const iconMap = {
            'customer': 'business',
            'project': 'work',
            'quotation': 'request_quote',
            'pricing_order': 'sell',
            'settlement_order': 'receipt_long',
            'expense': 'payments',
            'product': 'inventory_2',
            'inventory': 'warehouse',
            'user_management': 'manage_accounts',
            'role_management': 'admin_panel_settings',
            'system_settings': 'settings',
            'approval': 'approval',
            'report': 'analytics',
            'performance': 'insights',
            'vendor': 'factory'
        };
        return iconMap[moduleId] || 'apps';
    }

    /**
     * 渲染模块列表
     */
    function renderModuleList() {
        const moduleList = document.getElementById('moduleList');
        if (!moduleList || !MODULES || !Array.isArray(MODULES)) {
            console.error('无法渲染模块列表');
            return;
        }

        // 清空列表
        moduleList.innerHTML = '';

        // 添加模块项
        MODULES.forEach(module => {
            if (!module || !module.id) return;

            const moduleId = module.id;
            const modulePermission = currentPermissions.find(p => p.module === moduleId);

            // 检查模块是否启用
            const isEnabled = isModuleEnabled(modulePermission);

            // 获取 Material 图标
            const materialIcon = getMaterialIcon(moduleId);

            // 创建列表项，添加禁用状态样式
            const item = document.createElement('a');
            item.href = '#';
            item.className = `tw-module-item ${!isEnabled ? 'module-disabled' : ''}`;
            item.dataset.moduleId = moduleId;

            item.innerHTML = `
                <div class="tw-module-item-content">
                    <span class="material-symbols-outlined tw-module-icon">${materialIcon}</span>
                    <span class="tw-module-name">${module.name || moduleId}</span>
                </div>
                <div class="tw-module-status">
                    ${isEnabled
                        ? '<span class="tw-status-dot tw-status-enabled"></span>'
                        : '<span class="tw-status-dot tw-status-disabled"></span>'
                    }
                </div>
            `;

            // 添加点击事件
            item.addEventListener('click', function(e) {
                e.preventDefault();
                selectModule(moduleId);
            });

            moduleList.appendChild(item);
        });
    }

    /**
     * 选择模块
     */
    function selectModule(moduleId) {
        if (!moduleId) return;

        // 在切换模块前，先保存当前模块的数据到缓存
        if (currentSelectedModule && currentSelectedModule !== moduleId) {
            const currentModule = MODULES.find(m => m.id === currentSelectedModule);
            if (currentModule) {
                const cachedData = collectModulePermissionFromDOM(currentSelectedModule, currentModule);
                if (cachedData) {
                    modulePermissionsCache[currentSelectedModule] = cachedData;
                    console.log('已缓存模块数据:', currentSelectedModule);
                }
            }
        }

        currentSelectedModule = moduleId;

        // 更新左侧选中状态
        document.querySelectorAll('#moduleList .tw-module-item').forEach(item => {
            if (item.dataset.moduleId === moduleId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // 渲染右侧配置面板
        renderConfigPanel(moduleId);
    }

    /**
     * 渲染配置面板
     */
    function renderConfigPanel(moduleId) {
        const permissionConfigPanel = document.getElementById('permissionConfigPanel');
        if (!moduleId || !permissionConfigPanel) return;

        const module = MODULES.find(m => m.id === moduleId);
        if (!module) return;

        // 优先使用缓存数据
        let modulePermission;
        if (modulePermissionsCache[moduleId]) {
            modulePermission = modulePermissionsCache[moduleId];
            console.log('从缓存恢复模块数据:', moduleId);
        } else {
            modulePermission = currentPermissions.find(p => p.module === moduleId) || {
                module: moduleId,
                can_view: false,
                can_create: false,
                can_edit: false,
                can_delete: false,
                can_change_owner: false,
                permission_level: 'personal'
            };
        }

        // 清空面板
        permissionConfigPanel.innerHTML = '';

        // 模块标题 - 使用新设计
        const materialIcon = getMaterialIcon(moduleId);
        const titleHtml = `
            <div class="tw-config-header">
                <div class="tw-config-header-icon">
                    <span class="material-symbols-outlined">${materialIcon}</span>
                </div>
                <div class="tw-config-header-info">
                    <h4 class="tw-config-title">${module.name || moduleId}</h4>
                    <p class="tw-config-desc">${module.description || '配置此模块的访问权限'}</p>
                </div>
            </div>
        `;
        permissionConfigPanel.insertAdjacentHTML('beforeend', titleHtml);

        // 检查是否为开关式权限模块
        if (module.type === 'switch') {
            renderSwitchPermission(moduleId, modulePermission);
        } else {
            renderStandardPermission(moduleId, modulePermission);
        }

        // 如果模块支持折扣权限,显示折扣权限配置
        if (hasDiscountPermission(moduleId)) {
            renderDiscountPermission(moduleId, modulePermission);
        }

        // 内容筛选配置
        renderContentFilter(moduleId, modulePermission);
    }

    /**
     * 渲染开关式权限
     */
    function renderSwitchPermission(moduleId, permission) {
        const permissionConfigPanel = document.getElementById('permissionConfigPanel');
        const isEnabled = permission.can_create === true;
        const permissionLevel = permission.permission_level || 'personal';

        const html = `
            <!-- 数据范围 -->
            <div class="permission-section" id="level_section_${moduleId}">
                <h6>数据范围</h6>
                <div class="radio-group">
                    ${renderPermissionLevelRadios(moduleId, permissionLevel)}
                </div>
            </div>

            <!-- 功能开关 -->
            <div class="permission-section">
                <h6>功能开关</h6>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox"
                           id="switch_${moduleId}"
                           data-module="${moduleId}"
                           ${isEnabled ? 'checked' : ''}>
                    <label class="form-check-label" for="switch_${moduleId}">
                        ${isEnabled ? '已启用' : '已禁用'}
                    </label>
                </div>
            </div>
        `;

        permissionConfigPanel.insertAdjacentHTML('beforeend', html);

        // 添加开关事件监听
        const switchInput = document.getElementById(`switch_${moduleId}`);
        if (switchInput) {
            switchInput.addEventListener('change', function() {
                const label = this.nextElementSibling;
                label.textContent = this.checked ? '已启用' : '已禁用';
            });
        }
    }

    /**
     * 渲染标准权限
     */
    function renderStandardPermission(moduleId, permission) {
        const permissionConfigPanel = document.getElementById('permissionConfigPanel');
        const permissionLevel = permission.permission_level || 'personal';
        const hasOwnerChange = hasOwnerChangePermission(moduleId);

        const html = `
            <!-- 数据范围 -->
            <div class="tw-config-section" id="level_section_${moduleId}">
                <div class="tw-section-header">
                    <span class="material-symbols-outlined tw-section-icon">tune</span>
                    <h6 class="tw-section-title">数据范围</h6>
                </div>
                <div class="tw-radio-group">
                    ${renderPermissionLevelRadios(moduleId, permissionLevel)}
                </div>
            </div>

            <!-- 基础权限 -->
            <div class="tw-config-section">
                <div class="tw-section-header">
                    <span class="material-symbols-outlined tw-section-icon">security</span>
                    <h6 class="tw-section-title">基础权限</h6>
                    <label class="tw-select-all">
                        <input type="checkbox" id="selectAll_basic_${moduleId}">
                        <span>全选</span>
                    </label>
                </div>
                <div class="tw-checkbox-grid">
                    <div class="form-check">
                        <input class="form-check-input permission-checkbox" type="checkbox"
                               id="view_${moduleId}"
                               data-module="${moduleId}"
                               data-action="view"
                               ${permission.can_view ? 'checked' : ''}>
                        <label class="form-check-label" for="view_${moduleId}">查看</label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input permission-checkbox" type="checkbox"
                               id="create_${moduleId}"
                               data-module="${moduleId}"
                               data-action="create"
                               ${permission.can_create ? 'checked' : ''}>
                        <label class="form-check-label" for="create_${moduleId}">创建</label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input permission-checkbox" type="checkbox"
                               id="edit_${moduleId}"
                               data-module="${moduleId}"
                               data-action="edit"
                               ${permission.can_edit ? 'checked' : ''}>
                        <label class="form-check-label" for="edit_${moduleId}">编辑</label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input permission-checkbox" type="checkbox"
                               id="delete_${moduleId}"
                               data-module="${moduleId}"
                               data-action="delete"
                               ${permission.can_delete ? 'checked' : ''}>
                        <label class="form-check-label" for="delete_${moduleId}">删除</label>
                    </div>
                    ${hasOwnerChange ? `
                    <div class="form-check">
                        <input class="form-check-input permission-checkbox" type="checkbox"
                               id="change_owner_${moduleId}"
                               data-module="${moduleId}"
                               data-action="change_owner"
                               ${permission.can_change_owner ? 'checked' : ''}>
                        <label class="form-check-label" for="change_owner_${moduleId}">修改拥有人</label>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;

        permissionConfigPanel.insertAdjacentHTML('beforeend', html);

        // 绑定基础权限全选功能
        attachSelectAllHandler(
            `selectAll_basic_${moduleId}`,
            `#permissionConfigPanel input.permission-checkbox[data-module="${moduleId}"]`
        );

        // 绑定权限级别变化事件
        const levelRadios = document.querySelectorAll(`input[name="permission_level_${moduleId}"]`);
        levelRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                updatePermissionUIByLevel(moduleId, this.value);
            });
        });

        // 初始化UI状态
        updatePermissionUIByLevel(moduleId, permissionLevel);
    }

    /**
     * 根据权限级别更新UI状态
     *
     * 关键功能：当level='none'时，强制清空所有权限复选框
     * 这样可以防止保存时出现level='none'但权限为true的矛盾数据
     */
    function updatePermissionUIByLevel(moduleId, level) {
        const viewCheckbox = document.getElementById(`view_${moduleId}`);
        const createCheckbox = document.getElementById(`create_${moduleId}`);
        const editCheckbox = document.getElementById(`edit_${moduleId}`);
        const deleteCheckbox = document.getElementById(`delete_${moduleId}`);
        const changeOwnerCheckbox = document.getElementById(`change_owner_${moduleId}`);
        // 兼容新旧两种 CSS 类名
        const basicPermissionsSection = document.querySelector(`#permissionConfigPanel .tw-config-section:has(#selectAll_basic_${moduleId})`) ||
                                        document.querySelector(`#permissionConfigPanel .permission-section:has(#selectAll_basic_${moduleId})`);
        const contentFilterSection = document.querySelector('#permissionConfigPanel .content-filter-section');
        const discountSection = document.querySelector('#permissionConfigPanel .discount-section');

        if (level === 'none') {
            // 未启用级别：对所有模式都生效 - 隐藏所有权限区域，强制清空所有权限和扩展配置

            // 隐藏基础权限区域
            if (basicPermissionsSection) {
                basicPermissionsSection.style.display = 'none';
            }

            // 隐藏内容筛选区域
            if (contentFilterSection) {
                contentFilterSection.style.display = 'none';
            }

            // 隐藏折扣权限区域
            if (discountSection) {
                discountSection.style.display = 'none';
            }

            // 关键：强制清空所有权限复选框，防止保存时出现矛盾数据
            if (viewCheckbox) viewCheckbox.checked = false;
            if (createCheckbox) createCheckbox.checked = false;
            if (editCheckbox) editCheckbox.checked = false;
            if (deleteCheckbox) deleteCheckbox.checked = false;
            if (changeOwnerCheckbox) changeOwnerCheckbox.checked = false;

            // 清空所有内容筛选复选框
            const contentFilterCheckboxes = document.querySelectorAll(
                `#permissionConfigPanel input.content-filter-checkbox[data-module="${moduleId}"]`
            );
            contentFilterCheckboxes.forEach(cb => cb.checked = false);

            // 清空折扣输入框
            const pricingInput = document.getElementById(`pricingDiscountLimit_${moduleId}`);
            const settlementInput = document.getElementById(`settlementDiscountLimit_${moduleId}`);
            if (pricingInput) pricingInput.value = '';
            if (settlementInput) settlementInput.value = '';

            console.log(`✅ 模块 ${moduleId} 未启用级别 - 已隐藏并清空所有权限配置`);
            return; // 处理完直接返回
        }

        // 显示所有区域（对 personal 和其他级别都需要）
        if (basicPermissionsSection) {
            basicPermissionsSection.style.display = '';
        }
        if (contentFilterSection) {
            contentFilterSection.style.display = '';
        }
        if (discountSection) {
            discountSection.style.display = '';
        }

        // 只在角色权限模式下应用保底规则和禁用逻辑
        if (config.contextType === 'role') {
            if (level === 'personal') {
                // 个人级别：强制全选并禁用所有基础权限（保底规则）
                if (viewCheckbox) {
                    viewCheckbox.checked = true;
                    viewCheckbox.disabled = true;
                }
                if (createCheckbox) {
                    createCheckbox.checked = true;
                    createCheckbox.disabled = true;
                }
                if (editCheckbox) {
                    editCheckbox.checked = true;
                    editCheckbox.disabled = true;
                }
                if (deleteCheckbox) {
                    deleteCheckbox.checked = true;
                    deleteCheckbox.disabled = true;
                }
                if (changeOwnerCheckbox) {
                    changeOwnerCheckbox.disabled = false;
                }

                console.log(`✅ 模块 ${moduleId} 个人级别 - 已自动开启所有基础权限（保底规则）`);
            } else {
                // 其他级别：所有权限都可以自由选择
                if (viewCheckbox) viewCheckbox.disabled = false;
                if (createCheckbox) createCheckbox.disabled = false;
                if (editCheckbox) editCheckbox.disabled = false;
                if (deleteCheckbox) deleteCheckbox.disabled = false;
                if (changeOwnerCheckbox) changeOwnerCheckbox.disabled = false;

                console.log(`✅ 模块 ${moduleId} ${level}级别 - 所有权限可自由选择`);
            }
        } else {
            // 个人权限模式的联动逻辑
            //
            // 设计原则：
            // - 个人级(personal)：只操作自己的数据，应该有完整 CRUD 权限
            // - 部门/公司/系统级：扩大数据可见范围
            //   - view/create：保留（创建新数据不涉及"他人数据"）
            //   - edit/delete：取消（对他人数据默认不给编辑/删除权限）
            //   - 注：edit/delete 有"基本权限保障"，用户仍可编辑/删除自己的数据
            //
            if (level === 'personal') {
                // 个人级别：自动勾选所有基础权限
                if (viewCheckbox) viewCheckbox.checked = true;
                if (createCheckbox) createCheckbox.checked = true;
                if (editCheckbox) editCheckbox.checked = true;
                if (deleteCheckbox) deleteCheckbox.checked = true;
                console.log(`✅ 模块 ${moduleId} 个人级别 - 已自动勾选全部权限`);
            } else {
                // 部门/公司/系统级别：保留查看和创建，取消编辑/删除
                // - create：创建新数据不涉及"他人数据"，应该保留
                // - edit/delete：有基本保障，用户仍可操作自己的数据
                if (viewCheckbox) viewCheckbox.checked = true;
                if (createCheckbox) createCheckbox.checked = true;
                if (editCheckbox) editCheckbox.checked = false;
                if (deleteCheckbox) deleteCheckbox.checked = false;
                console.log(`✅ 模块 ${moduleId} ${level}级别 - 保留查看/创建，取消编辑/删除他人数据`);
            }
        }

        // 更新全选框状态
        updateSelectAllState(
            `selectAll_basic_${moduleId}`,
            `#permissionConfigPanel input.permission-checkbox[data-module="${moduleId}"]`
        );
    }

    /**
     * 渲染权限级别单选按钮 - 简洁样式
     */
    function renderPermissionLevelRadios(moduleId, currentLevel) {
        // 本地定义的级别配置
        const levelConfig = {
            'none': {label: '未启用'},
            'personal': {label: '本人'},
            'department': {label: '本部门'},
            'company': {label: '全公司'},
            'system': {label: '系统级'}
        };

        // 使用服务器返回的级别顺序
        let levels;
        if (permissionLevels && permissionLevels.length > 0) {
            levels = permissionLevels.map(serverLevel => {
                const local = levelConfig[serverLevel.value] || {};
                return {
                    value: serverLevel.value,
                    label: serverLevel.label || local.label || serverLevel.value
                };
            });
        } else {
            // 服务器未返回数据时使用默认配置
            levels = Object.entries(levelConfig).map(([value, config]) => ({
                value,
                label: config.label
            }));
        }

        return levels.map(level => `
            <div class="form-check">
                <input class="form-check-input" type="radio"
                       name="permission_level_${moduleId}"
                       id="level_${level.value}_${moduleId}"
                       value="${level.value}"
                       ${currentLevel === level.value ? 'checked' : ''}>
                <label class="form-check-label" for="level_${level.value}_${moduleId}">${level.label}</label>
            </div>
        `).join('');
    }

    /**
     * 渲染折扣权限
     */
    function renderDiscountPermission(moduleId, permission) {
        const permissionConfigPanel = document.getElementById('permissionConfigPanel');
        const pricingLimit = permission.pricing_discount_limit !== null && permission.pricing_discount_limit !== undefined
            ? permission.pricing_discount_limit : '';
        const settlementLimit = permission.settlement_discount_limit !== null && permission.settlement_discount_limit !== undefined
            ? permission.settlement_discount_limit : '';

        let discountInputHtml = '';

        if (moduleId === 'pricing_order') {
            discountInputHtml = `
                <div class="tw-input-group">
                    <label for="pricingDiscountLimit_${moduleId}" class="tw-input-label">批价折扣下限 (%)</label>
                    <input type="number" class="tw-input"
                           id="pricingDiscountLimit_${moduleId}"
                           value="${pricingLimit}"
                           placeholder="输入批价折扣下限"
                           min="0" max="100" step="0.1">
                    <p class="tw-input-hint">设置批价单的最低折扣率，低于此值需要更高权限审批</p>
                </div>
            `;
        } else if (moduleId === 'settlement_order') {
            discountInputHtml = `
                <div class="tw-input-group">
                    <label for="settlementDiscountLimit_${moduleId}" class="tw-input-label">结算折扣下限 (%)</label>
                    <input type="number" class="tw-input"
                           id="settlementDiscountLimit_${moduleId}"
                           value="${settlementLimit}"
                           placeholder="输入结算折扣下限"
                           min="0" max="100" step="0.1">
                    <p class="tw-input-hint">设置结算单的最低折扣率，低于此值需要更高权限审批</p>
                </div>
            `;
        }

        const html = `
            <div class="tw-config-section discount-section">
                <div class="tw-section-header">
                    <span class="material-symbols-outlined tw-section-icon">percent</span>
                    <h6 class="tw-section-title">折扣权限设置</h6>
                </div>
                ${discountInputHtml}
            </div>
        `;

        permissionConfigPanel.insertAdjacentHTML('beforeend', html);
    }

    /**
     * 渲染内容筛选配置
     */
    function renderContentFilter(moduleId, permission) {
        const permissionConfigPanel = document.getElementById('permissionConfigPanel');

        if (!CONTENT_FILTER_OPTIONS || !CONTENT_FILTER_OPTIONS[moduleId]) {
            return;
        }

        const filterConfig = CONTENT_FILTER_OPTIONS[moduleId];
        const filterKeys = Object.keys(filterConfig);

        if (filterKeys.length === 0) {
            return;
        }

        let filterSectionsHtml = '';

        filterKeys.forEach(filterKey => {
            const config = filterConfig[filterKey];
            const label = config.label || filterKey;
            const options = config.options || [];

            if (options.length === 0) return;

            const checkboxesHtml = renderCheckboxGroup(
                options,
                `filter_${moduleId}_${filterKey}`,
                {
                    'module': moduleId,
                    'filter-type': filterKey
                },
                false,
                'content-filter-checkbox'
            );

            filterSectionsHtml += `
                <div class="tw-filter-category">
                    <div class="tw-filter-header">
                        <span class="tw-filter-label">${label}</span>
                        <label class="tw-select-all">
                            <input type="checkbox" id="selectAll_${moduleId}_${filterKey}">
                            <span>全选</span>
                        </label>
                    </div>
                    <div class="tw-checkbox-grid">
                        ${checkboxesHtml}
                    </div>
                </div>
            `;
        });

        const html = `
            <div class="tw-config-section content-filter-section">
                <div class="tw-section-header">
                    <span class="material-symbols-outlined tw-section-icon">filter_list</span>
                    <h6 class="tw-section-title">内容筛选配置</h6>
                </div>
                ${filterSectionsHtml}
            </div>
        `;

        permissionConfigPanel.insertAdjacentHTML('beforeend', html);

        // 绑定全选功能
        filterKeys.forEach(filterKey => {
            attachSelectAllHandler(
                `selectAll_${moduleId}_${filterKey}`,
                `input.content-filter-checkbox[data-module="${moduleId}"][data-filter-type="${filterKey}"]`
            );
        });

        // 恢复筛选状态
        if (permission.content_filters && CONTENT_FILTER_OPTIONS[moduleId]) {
            const contentFilters = permission.content_filters;
            const savedFilterKeys = Object.keys(contentFilters);

            savedFilterKeys.forEach(filterKey => {
                const selectedValues = contentFilters[filterKey];
                if (Array.isArray(selectedValues) && selectedValues.length > 0) {
                    selectedValues.forEach(value => {
                        const checkbox = document.querySelector(
                            `input.content-filter-checkbox[data-module="${moduleId}"][data-filter-type="${filterKey}"][data-value="${value}"]`
                        );
                        if (checkbox) {
                            checkbox.checked = true;
                        }
                    });

                    updateSelectAllState(
                        `selectAll_${moduleId}_${filterKey}`,
                        `input.content-filter-checkbox[data-module="${moduleId}"][data-filter-type="${filterKey}"]`
                    );
                }
            });
        }
    }

    /**
     * 渲染筛选复选框组 - 新设计
     */
    function renderFilterCheckboxGroup(options, idPrefix, moduleId, filterKey) {
        if (!options || options.length === 0) return '';

        return options.map(opt => {
            const value = opt[0] || opt.value;
            const label = opt[1] || opt.label;

            return `
                <label class="tw-filter-item">
                    <input type="checkbox" class="tw-filter-checkbox content-filter-checkbox"
                           id="${idPrefix}_${value}"
                           data-module="${moduleId}"
                           data-filter-type="${filterKey}"
                           data-value="${value}">
                    <span class="tw-filter-item-check">
                        <span class="material-symbols-outlined">check</span>
                    </span>
                    <span class="tw-filter-item-label">${label}</span>
                </label>
            `;
        }).join('');
    }

    /**
     * 通用复选框组渲染函数
     */
    function renderCheckboxGroup(options, idPrefix, dataAttrs = {}, disabled = false, cssClass = '') {
        if (!options || options.length === 0) return '';

        return options.map(opt => {
            const value = opt[0] || opt.value;
            const label = opt[1] || opt.label;

            const dataAttrStr = Object.entries(dataAttrs)
                .map(([k, v]) => `data-${k}="${v}"`)
                .join(' ');

            return `
                <div class="form-check">
                    <input class="form-check-input ${cssClass}" type="checkbox"
                           id="${idPrefix}_${value}"
                           ${dataAttrStr}
                           data-value="${value}"
                           ${disabled ? 'disabled' : ''}>
                    <label class="form-check-label" for="${idPrefix}_${value}">
                        ${label}
                    </label>
                </div>
            `;
        }).join('');
    }

    /**
     * 绑定全选功能
     */
    function attachSelectAllHandler(selectAllId, targetSelector) {
        const selectAllCheckbox = document.getElementById(selectAllId);
        if (!selectAllCheckbox) return;

        selectAllCheckbox.addEventListener('change', function() {
            const targetCheckboxes = document.querySelectorAll(targetSelector);
            targetCheckboxes.forEach(cb => {
                if (!cb.disabled) {
                    cb.checked = this.checked;
                }
            });
        });

        const targetCheckboxes = document.querySelectorAll(targetSelector);
        targetCheckboxes.forEach(cb => {
            cb.addEventListener('change', function() {
                updateSelectAllState(selectAllId, targetSelector);
            });
        });

        updateSelectAllState(selectAllId, targetSelector);
    }

    /**
     * 更新全选复选框状态
     */
    function updateSelectAllState(selectAllId, targetSelector) {
        const selectAllCheckbox = document.getElementById(selectAllId);
        if (!selectAllCheckbox) return;

        const targetCheckboxes = Array.from(document.querySelectorAll(targetSelector));
        const enabledCheckboxes = targetCheckboxes.filter(cb => !cb.disabled);

        if (enabledCheckboxes.length === 0) return;

        const checkedCount = enabledCheckboxes.filter(cb => cb.checked).length;

        if (checkedCount === 0) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        } else if (checkedCount === enabledCheckboxes.length) {
            selectAllCheckbox.checked = true;
            selectAllCheckbox.indeterminate = false;
        } else {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = true;
        }
    }

    /**
     * 从DOM收集模块权限数据
     */
    function collectModulePermissionFromDOM(moduleId, module) {
        if (!module) return null;

        const levelRadio = document.querySelector(`input[name="permission_level_${moduleId}"]:checked`);
        const permissionLevel = levelRadio ? levelRadio.value : 'personal';

        // 关键：如果level='none'，强制清空所有扩展字段，确保数据一致性
        if (permissionLevel === 'none') {
            return {
                module: moduleId,
                can_view: false,
                can_create: false,
                can_edit: false,
                can_delete: false,
                can_change_owner: false,
                permission_level: 'none',
                pricing_discount_limit: null,
                settlement_discount_limit: null,
                content_filters: null
            };
        }

        // 非none级别：正常收集所有配置
        const { pricingLimit, settlementLimit } = extractDiscountLimits(moduleId);
        const contentFilters = extractContentFilters(moduleId);

        if (module.type === 'switch') {
            const switchInput = document.getElementById(`switch_${moduleId}`);
            const hasPermission = switchInput ? switchInput.checked : false;

            return {
                module: moduleId,
                can_view: false,
                can_create: hasPermission,
                can_edit: false,
                can_delete: false,
                can_change_owner: false,
                permission_level: permissionLevel,
                pricing_discount_limit: pricingLimit,
                settlement_discount_limit: settlementLimit,
                content_filters: contentFilters
            };
        } else {
            const viewCheckbox = document.getElementById(`view_${moduleId}`);
            const createCheckbox = document.getElementById(`create_${moduleId}`);
            const editCheckbox = document.getElementById(`edit_${moduleId}`);
            const deleteCheckbox = document.getElementById(`delete_${moduleId}`);
            const changeOwnerCheckbox = document.getElementById(`change_owner_${moduleId}`);

            return {
                module: moduleId,
                can_view: viewCheckbox ? viewCheckbox.checked : false,
                can_create: createCheckbox ? createCheckbox.checked : false,
                can_edit: editCheckbox ? editCheckbox.checked : false,
                can_delete: deleteCheckbox ? deleteCheckbox.checked : false,
                can_change_owner: changeOwnerCheckbox ? changeOwnerCheckbox.checked : false,
                permission_level: permissionLevel,
                pricing_discount_limit: pricingLimit,
                settlement_discount_limit: settlementLimit,
                content_filters: contentFilters
            };
        }
    }

    /**
     * 提取折扣限额
     */
    function extractDiscountLimits(moduleId) {
        let pricingLimit = null;
        let settlementLimit = null;

        if (hasDiscountPermission(moduleId)) {
            const pricingInput = document.getElementById(`pricingDiscountLimit_${moduleId}`);
            const settlementInput = document.getElementById(`settlementDiscountLimit_${moduleId}`);
            pricingLimit = pricingInput && pricingInput.value ? parseFloat(pricingInput.value) : null;
            settlementLimit = settlementInput && settlementInput.value ? parseFloat(settlementInput.value) : null;
        }

        return { pricingLimit, settlementLimit };
    }

    /**
     * 提取内容筛选数据
     */
    function extractContentFilters(moduleId) {
        if (!CONTENT_FILTER_OPTIONS || !CONTENT_FILTER_OPTIONS[moduleId]) {
            return null;
        }

        const filterConfig = CONTENT_FILTER_OPTIONS[moduleId];
        const filterKeys = Object.keys(filterConfig);

        if (filterKeys.length === 0) {
            return null;
        }

        const contentFilters = {};
        let hasAnyFilter = false;

        filterKeys.forEach(filterKey => {
            const checkboxes = document.querySelectorAll(
                `input.content-filter-checkbox[data-module="${moduleId}"][data-filter-type="${filterKey}"]:checked`
            );

            if (checkboxes.length > 0) {
                const selectedValues = Array.from(checkboxes).map(cb => cb.dataset.value);
                contentFilters[filterKey] = selectedValues;
                hasAnyFilter = true;
            }
        });

        return hasAnyFilter ? contentFilters : null;
    }

    /**
     * 筛选权限（角色模式返回所有，个人模式也返回所有 - 完整保存模式）
     */
    function filterPersonalPermissions(allPermissions) {
        // 新逻辑：不论角色模式还是个人模式，都返回完整权限状态
        // 后端会保存完整状态，使个人权限表成为权威数据源
        console.log('保存完整权限状态（不过滤差异）:', allPermissions);
        return allPermissions;
    }

    /**
     * 保存权限
     */
    function savePermissions() {
        const saveButton = document.getElementById('savePermissions');

        // 禁用保存按钮
        if (saveButton) {
            saveButton.disabled = true;
            saveButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> 保存中...';
        }

        // 先保存当前模块到缓存
        if (currentSelectedModule) {
            const currentModule = MODULES.find(m => m.id === currentSelectedModule);
            if (currentModule) {
                const cachedData = collectModulePermissionFromDOM(currentSelectedModule, currentModule);
                if (cachedData) {
                    modulePermissionsCache[currentSelectedModule] = cachedData;
                    console.log('保存前缓存当前模块:', currentSelectedModule);
                }
            }
        }

        // 收集所有模块权限
        const permissions = [];

        MODULES.forEach(module => {
            const moduleId = module.id;

            let moduleData;
            if (modulePermissionsCache[moduleId]) {
                moduleData = modulePermissionsCache[moduleId];
                console.log(`模块 ${moduleId} 使用缓存数据`);
            } else {
                moduleData = currentPermissions.find(p => p.module === moduleId) || {
                    module: moduleId,
                    can_view: false,
                    can_create: false,
                    can_edit: false,
                    can_delete: false,
                    can_change_owner: false,
                    permission_level: 'personal',
                    pricing_discount_limit: null,
                    settlement_discount_limit: null,
                    content_filters: null
                };
                console.log(`模块 ${moduleId} 使用服务器数据`);
            }

            permissions.push(moduleData);
        });

        // 🆕 个人权限模式：筛选出差异权限
        const finalPermissions = filterPersonalPermissions(permissions);

        console.log('准备保存权限，模块数:', MODULES.length, '权限数:', finalPermissions.length);

        // 检查权限数组是否为空
        if (!finalPermissions || finalPermissions.length === 0) {
            console.warn('权限数组为空，无需保存');
            showNotification('没有权限数据需要保存', 'warning', 3000);
            if (saveButton) {
                saveButton.disabled = false;
                const btnText = config.contextType === 'role' ? '保存权限设置' : '保存个人权限';
                saveButton.innerHTML = `<span class="material-symbols-outlined text-lg">save</span> ${btnText}`;
            }
            return;
        }

        // 构建请求数据
        const requestData = config.contextType === 'role'
            ? { role: config.contextId, permissions: finalPermissions }
            : { user_id: config.contextId, permissions: finalPermissions };

        const apiUrl = config.contextType === 'role'
            ? '/api/v1/permissions/roles/update'
            : '/api/v1/users/' + config.contextId + '/permissions';

        // 发送请求
        fetch(apiUrl, {
            method: config.contextType === 'role' ? 'POST' : 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRFToken': config.csrfToken
            },
            credentials: 'same-origin',
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP错误 ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showNotification('权限设置已成功保存！', 'success', 3000);

                // 清空缓存
                modulePermissionsCache = {};
                hasUnsavedChanges = false;
                updateSaveButtonState();
                console.log('保存成功，已重置未保存状态');
            } else {
                console.error('保存权限失败:', data.message);
                showNotification(`保存权限失败: ${data.message || '未知错误'}`, 'error', 5000);
            }
        })
        .catch(error => {
            console.error('保存权限时出错:', error);
            showNotification('保存权限时发生错误，请稍后再试', 'error', 5000);
        })
        .finally(() => {
            if (saveButton) {
                saveButton.disabled = false;
                const btnText = config.contextType === 'role' ? '保存权限设置' : '保存个人权限';
                saveButton.innerHTML = `<span class="material-symbols-outlined text-lg">save</span> ${btnText}`;
            }
        });
    }

    /**
     * 恢复角色设置
     */
    function resetAllModulesToRole() {
        showConfirmDialog({
            title: '恢复角色设置',
            message: '此操作将清除所有个人权限修改，恢复为角色默认设置。\n您仍需点击"保存"按钮来应用更改。\n\n是否继续？',
            type: 'warning',
            confirmText: '确认恢复',
            cancelText: '取消',
            confirmColor: 'warning',
            onConfirm: function() {
                // 清空缓存
                modulePermissionsCache = {};

                // 使用角色权限替换当前权限（深拷贝避免引用问题）
                // 防御性检查：确保 rolePermissions 是数组
                if (Array.isArray(config.rolePermissions)) {
                    currentPermissions = JSON.parse(JSON.stringify(config.rolePermissions));
                } else {
                    console.error('❌ 角色权限数据格式错误，应为数组:', config.rolePermissions);
                    showNotification('恢复失败：角色权限数据格式错误', 'error', 3000);
                    return;
                }

                // 显示提示
                const notice = document.getElementById('roleDefaultNotice');
                if (notice) {
                    notice.style.display = 'block';
                }

                // 标记未保存
                hasUnsavedChanges = true;
                updateSaveButtonState();

                // 刷新UI
                renderModuleList();
                if (currentSelectedModule) {
                    renderConfigPanel(currentSelectedModule);
                }

                console.log('✅ 已恢复为角色默认设置');
            }
        });
    }

    /**
     * 更新保存按钮状态
     */
    function updateSaveButtonState() {
        const saveButton = document.getElementById('savePermissions');
        if (!saveButton) return;

        if (hasUnsavedChanges) {
            saveButton.disabled = false;
            saveButton.classList.add('active-state');
        } else {
            saveButton.disabled = true;
            saveButton.classList.remove('active-state');
        }
    }

    /**
     * 更新模块列表中指定模块的启用/禁用状态
     */
    function updateModuleListItemState(moduleId) {
        const module = MODULES.find(m => m.id === moduleId);
        if (!module) return;

        // 从DOM收集当前模块的权限数据
        const cachedData = collectModulePermissionFromDOM(moduleId, module);
        const isEnabled = isModuleEnabled(cachedData);

        // 更新列表项的样式
        const moduleItem = document.querySelector(`#moduleList [data-module-id="${moduleId}"]`);
        if (moduleItem) {
            // 更新禁用样式
            if (isEnabled) {
                moduleItem.classList.remove('module-disabled');
            } else {
                moduleItem.classList.add('module-disabled');
            }

            // 更新状态指示器
            const statusContainer = moduleItem.querySelector('.tw-module-status');
            if (statusContainer) {
                statusContainer.innerHTML = isEnabled
                    ? '<span class="tw-status-dot tw-status-enabled"></span>'
                    : '<span class="tw-status-dot tw-status-disabled"></span>';
            }

            console.log(`✅ 模块 ${moduleId} 状态已更新: ${isEnabled ? '启用' : '禁用'}`);
        }
    }

    /**
     * 绑定模式切换事件监听器
     */
    function attachModeToggleListeners() {
        // 进入编辑模式按钮
        const enterEditBtn = document.getElementById('enterEditMode');
        if (enterEditBtn) {
            enterEditBtn.addEventListener('click', enterEditMode);
        }

        // 退出编辑模式按钮
        const exitEditBtn = document.getElementById('exitEditMode');
        if (exitEditBtn) {
            exitEditBtn.addEventListener('click', exitEditMode);
        }
    }

    /**
     * 进入编辑模式
     */
    function enterEditMode() {
        console.log('进入编辑模式');
        isEditMode = true;

        // 切换显示状态
        const viewMode = document.getElementById('permissionViewMode');
        const editMode = document.getElementById('permissionEditMode');
        const enterBtn = document.getElementById('enterEditMode');
        const editBtns = document.getElementById('editModeButtons');

        if (viewMode) viewMode.classList.add('hidden');
        if (editMode) editMode.classList.remove('hidden');
        if (enterBtn) enterBtn.classList.add('hidden');
        if (editBtns) editBtns.classList.remove('hidden');

        // 初始化编辑面板（如果还没初始化）
        initEditPanel();
    }

    /**
     * 退出编辑模式
     */
    function exitEditMode() {
        // 如果有未保存的更改，提示用户
        if (hasUnsavedChanges) {
            if (!confirm('您有未保存的更改，确定要放弃吗？')) {
                return;
            }
        }

        doExitEditMode();
    }

    /**
     * 执行退出编辑模式
     */
    function doExitEditMode() {
        console.log('退出编辑模式');
        isEditMode = false;

        // 切换显示状态
        const viewMode = document.getElementById('permissionViewMode');
        const editMode = document.getElementById('permissionEditMode');
        const enterBtn = document.getElementById('enterEditMode');
        const editBtns = document.getElementById('editModeButtons');

        if (viewMode) viewMode.classList.remove('hidden');
        if (editMode) editMode.classList.add('hidden');
        if (enterBtn) enterBtn.classList.remove('hidden');
        if (editBtns) editBtns.classList.add('hidden');

        // 重置未保存状态
        hasUnsavedChanges = false;
        modulePermissionsCache = {};
        updateSaveButtonState();
    }

    /**
     * 绑定事件监听器
     */
    function attachEventListeners() {
        // 保存按钮事件
        const saveButton = document.getElementById('savePermissions');
        if (saveButton) {
            saveButton.addEventListener('click', savePermissions);
        }

        // 恢复角色设置按钮事件
        const resetButton = document.getElementById('resetAllToRole');
        if (resetButton) {
            resetButton.addEventListener('click', resetAllModulesToRole);
        }

        // 表单变化监听
        const permissionConfigPanel = document.getElementById('permissionConfigPanel');
        if (permissionConfigPanel) {
            permissionConfigPanel.addEventListener('change', function(e) {
                hasUnsavedChanges = true;
                updateSaveButtonState();
                console.log('检测到表单变化，标记为未保存');

                // 隐藏角色默认提示
                const notice = document.getElementById('roleDefaultNotice');
                if (notice && notice.style.display !== 'none') {
                    notice.style.display = 'none';
                }

                // 实时更新模块列表中当前模块的状态
                if (currentSelectedModule) {
                    updateModuleListItemState(currentSelectedModule);
                }
            });

            permissionConfigPanel.addEventListener('input', function(e) {
                const target = e.target;
                if (target.tagName === 'INPUT' && (target.type === 'number' || target.type === 'text')) {
                    hasUnsavedChanges = true;
                    updateSaveButtonState();
                    console.log('检测到输入变化，标记为未保存');
                }
            });
        }
    }

    /**
     * 获取未保存状态
     */
    function getHasUnsavedChanges() {
        return hasUnsavedChanges;
    }

    /**
     * 重置未保存状态（用于切换角色/用户后）
     */
    function resetUnsavedState() {
        hasUnsavedChanges = false;
        modulePermissionsCache = {};
        updateSaveButtonState();
        console.log('已重置未保存状态');
    }

    // 公开API
    return {
        init: init,
        savePermissions: savePermissions,
        getHasUnsavedChanges: getHasUnsavedChanges,
        resetUnsavedState: resetUnsavedState
    };
})();
