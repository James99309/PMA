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

    // 配置数据
    let config = null;
    let MODULES = [];
    let CONTENT_FILTER_OPTIONS = {};
    let moduleMetadata = {};
    let permissionLevels = [];

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

        // 加载模块元数据
        loadModuleMetadata().then(() => {
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
     * 检查模块是否启用（即是否有任何有效权限）
     */
    function isModuleEnabled(permission) {
        if (!permission) return false;

        // 如果权限级别为 'none'，模块未启用
        if (permission.permission_level === 'none') {
            return false;
        }

        return permission.can_view ||
               permission.can_create ||
               permission.can_edit ||
               permission.can_delete;
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

            // 获取模块图标
            const icon = getModuleIcon(moduleId);

            // 创建列表项，添加禁用状态样式
            const item = document.createElement('a');
            item.href = '#';
            item.className = `list-group-item list-group-item-action ${!isEnabled ? 'module-disabled' : ''}`;
            item.dataset.moduleId = moduleId;

            item.innerHTML = `
                <div>
                    <i class="${icon} module-icon"></i>
                    <span>${module.name || moduleId}</span>
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
        document.querySelectorAll('#moduleList .list-group-item').forEach(item => {
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

        // 模块标题
        const titleHtml = `
            <h4 class="mb-3">${module.name || moduleId}</h4>
            <hr class="mb-4">
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
            <div class="permission-section" id="level_section_${moduleId}">
                <h6>数据范围</h6>
                <div class="radio-group">
                    ${renderPermissionLevelRadios(moduleId, permissionLevel)}
                </div>
            </div>

            <!-- 基础权限 -->
            <div class="permission-section">
                <div class="section-header-with-select-all">
                    <h6>基础权限</h6>
                    <div class="select-all-control">
                        <input type="checkbox" id="selectAll_basic_${moduleId}">
                        <label for="selectAll_basic_${moduleId}">全选</label>
                    </div>
                </div>
                <div class="checkbox-grid">
                    <div class="form-check">
                        <input class="form-check-input permission-checkbox" type="checkbox"
                               id="view_${moduleId}"
                               data-module="${moduleId}"
                               data-action="view"
                               ${permission.can_view ? 'checked' : ''}>
                        <label class="form-check-label" for="view_${moduleId}">
                            查看
                        </label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input permission-checkbox" type="checkbox"
                               id="create_${moduleId}"
                               data-module="${moduleId}"
                               data-action="create"
                               ${permission.can_create ? 'checked' : ''}>
                        <label class="form-check-label" for="create_${moduleId}">
                            创建
                        </label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input permission-checkbox" type="checkbox"
                               id="edit_${moduleId}"
                               data-module="${moduleId}"
                               data-action="edit"
                               ${permission.can_edit ? 'checked' : ''}>
                        <label class="form-check-label" for="edit_${moduleId}">
                            编辑
                        </label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input permission-checkbox" type="checkbox"
                               id="delete_${moduleId}"
                               data-module="${moduleId}"
                               data-action="delete"
                               ${permission.can_delete ? 'checked' : ''}>
                        <label class="form-check-label" for="delete_${moduleId}">
                            删除
                        </label>
                    </div>
                    ${hasOwnerChange ? `
                    <div class="form-check">
                        <input class="form-check-input permission-checkbox" type="checkbox"
                               id="change_owner_${moduleId}"
                               data-module="${moduleId}"
                               data-action="change_owner"
                               ${permission.can_change_owner ? 'checked' : ''}>
                        <label class="form-check-label" for="change_owner_${moduleId}">
                            修改拥有人
                        </label>
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
        const basicPermissionsSection = document.querySelector(`#permissionConfigPanel .permission-section:has(#selectAll_basic_${moduleId})`);
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
            // 个人权限模式：不应用保底规则，保持权限可编辑状态
            console.log(`✅ 模块 ${moduleId} ${level}级别 - 个人权限模式，保持可编辑`);
        }

        // 更新全选框状态
        updateSelectAllState(
            `selectAll_basic_${moduleId}`,
            `#permissionConfigPanel input.permission-checkbox[data-module="${moduleId}"]`
        );
    }

    /**
     * 渲染权限级别单选按钮
     */
    function renderPermissionLevelRadios(moduleId, currentLevel) {
        const levels = permissionLevels.length > 0 ? permissionLevels : [
            {value: 'personal', label: '本人', desc: '只能访问自己创建的数据'},
            {value: 'department', label: '本部门', desc: '可以访问本部门所有数据'},
            {value: 'company', label: '全公司', desc: '可以访问全公司所有数据'},
            {value: 'system', label: '系统级', desc: '可以访问系统所有数据'}
        ];

        return levels.map(level => `
            <div class="form-check">
                <input class="form-check-input" type="radio"
                       name="permission_level_${moduleId}"
                       id="level_${level.value}_${moduleId}"
                       value="${level.value}"
                       ${currentLevel === level.value ? 'checked' : ''}>
                <label class="form-check-label" for="level_${level.value}_${moduleId}">
                    ${level.label}
                </label>
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
                <div class="col-md-12 mb-3">
                    <label for="pricingDiscountLimit_${moduleId}" class="form-label">批价折扣下限 (%)</label>
                    <input type="number" class="form-control"
                           id="pricingDiscountLimit_${moduleId}"
                           value="${pricingLimit}"
                           placeholder="输入批价折扣下限"
                           min="0" max="100" step="0.1">
                    <small class="form-text text-muted">设置批价单的最低折扣率，低于此值需要更高权限审批</small>
                </div>
            `;
        } else if (moduleId === 'settlement_order') {
            discountInputHtml = `
                <div class="col-md-12 mb-3">
                    <label for="settlementDiscountLimit_${moduleId}" class="form-label">结算折扣下限 (%)</label>
                    <input type="number" class="form-control"
                           id="settlementDiscountLimit_${moduleId}"
                           value="${settlementLimit}"
                           placeholder="输入结算折扣下限"
                           min="0" max="100" step="0.1">
                    <small class="form-text text-muted">设置结算单的最低折扣率，低于此值需要更高权限审批</small>
                </div>
            `;
        }

        const html = `
            <div class="discount-section">
                <h6><i class="fas fa-percentage"></i> 折扣权限设置</h6>
                <div class="row">
                    ${discountInputHtml}
                </div>
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
                <div class="filter-category mb-3">
                    <div class="category-header">
                        <label class="form-label fw-bold">${label}</label>
                        <div class="select-all-control">
                            <input type="checkbox" id="selectAll_${moduleId}_${filterKey}">
                            <label for="selectAll_${moduleId}_${filterKey}">全选</label>
                        </div>
                    </div>
                    <div class="checkbox-grid">
                        ${checkboxesHtml}
                    </div>
                </div>
            `;
        });

        const html = `
            <div class="content-filter-section">
                <h6>内容筛选配置</h6>
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
                showTopNotification('权限设置已成功保存！', 'success', 3000);

                // 清空缓存
                modulePermissionsCache = {};
                hasUnsavedChanges = false;
                updateSaveButtonState();
                console.log('保存成功，已重置未保存状态');
            } else {
                console.error('保存权限失败:', data.message);
                showTopNotification(`保存权限失败: ${data.message || '未知错误'}`, 'error', 5000);
            }
        })
        .catch(error => {
            console.error('保存权限时出错:', error);
            showTopNotification('保存权限时发生错误，请稍后再试', 'error', 5000);
        })
        .finally(() => {
            if (saveButton) {
                saveButton.disabled = false;
                const btnText = config.contextType === 'role' ? '保存权限设置' : '保存个人权限';
                saveButton.innerHTML = `<i class="fas fa-save me-1"></i> ${btnText}`;
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
            if (isEnabled) {
                moduleItem.classList.remove('module-disabled');
            } else {
                moduleItem.classList.add('module-disabled');
            }
            console.log(`✅ 模块 ${moduleId} 状态已更新: ${isEnabled ? '启用' : '禁用'}`);
        }
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

        // 表单变化监听
        const permissionConfigPanel = document.getElementById('permissionConfigPanel');
        if (permissionConfigPanel) {
            permissionConfigPanel.addEventListener('change', function(e) {
                hasUnsavedChanges = true;
                updateSaveButtonState();
                console.log('检测到表单变化，标记为未保存');

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
