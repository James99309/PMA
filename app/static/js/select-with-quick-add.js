/**
 * 通用选择器快速添加组件
 *
 * 功能：为任何下拉选择器提供快速添加新选项的能力
 * 支持：产品指标、产品名称、销售区域等
 * 特点：配置驱动、统一模态框、自动刷新列表、中英文支持
 *
 * @author Claude AI
 * @version 2.0.0
 * @created 2025-11-08
 * @file app/static/js/select-with-quick-add.js
 */

(function() {
    'use strict';

    /**
     * 通用选择器快速添加工具
     */
    window.SelectWithQuickAdd = {

        // 配置注册表 - 存储不同类型的配置
        configs: {},

        // 当前激活的配置
        activeConfig: null,

        // 当前上下文
        context: {
            targetRow: null,  // 触发添加的行元素（用于指标）
            targetSelect: null,  // 触发添加的select元素（用于产品名称、区域）
            relatedId: null  // 相关ID（如subcategory_id）
        },

        // 当前字段的单位
        currentFieldUnit: '',

        /**
         * 注册配置
         * @param {string} type - 配置类型（如 'indicator', 'subcategory', 'region'）
         * @param {object} config - 配置对象
         *
         * 配置对象结构：
         * {
         *   modalId: 模态框ID
         *   apiEndpoint: API端点
         *   valueFieldLabel: 值字段标签
         *   descriptionFieldLabel: 描述字段标签（可选）
         *   getRelatedId: 获取相关ID的函数（如获取subcategory_id）
         *   getExistingItemsUrl: 获取已有项目列表的URL构建函数
         *   refreshTarget: 刷新目标的函数
         *   permissionCheck: 权限检查函数（可选）
         *   onSuccess: 成功回调
         *   onError: 错误回调
         * }
         */
        register: function(type, config) {
            // 必需字段验证
            const requiredFields = ['modalId', 'apiEndpoint', 'valueFieldLabel'];
            for (let field of requiredFields) {
                if (!config[field]) {
                    console.error(`配置缺少必需字段: ${field}`);
                    return false;
                }
            }

            // 设置默认值
            config.type = type;
            config.descriptionFieldLabel = config.descriptionFieldLabel || '备注';
            config.permissionCheck = config.permissionCheck || (() => true);

            this.configs[type] = config;
            console.log(`已注册配置: ${type}`, config);
            return true;
        },

        /**
         * 显示快速添加模态框
         * @param {string} type - 配置类型
         * @param {object} context - 上下文信息
         */
        showModal: function(type, context) {
            const config = this.configs[type];
            if (!config) {
                console.error(`未找到配置: ${type}`);
                return;
            }

            // 权限检查
            if (!config.permissionCheck()) {
                this.showMessage('您没有权限执行此操作', 'warning');
                return;
            }

            // 保存当前配置和上下文
            this.activeConfig = config;
            this.context = Object.assign({}, context);

            // 获取相关ID
            if (config.getRelatedId) {
                this.context.relatedId = config.getRelatedId();
                if (!this.context.relatedId) {
                    this.showMessage(config.relatedIdErrorMsg || '无法获取必要的关联信息，请检查表单', 'error');
                    return;
                }
            }

            console.log('显示快速添加模态框:', { type, context: this.context });

            // 更新模态框标题和字段标签
            this.updateModalLabels(config, context);

            // 清空表单
            this.resetForm();

            // 加载已有项目列表
            if (config.getExistingItemsUrl) {
                this.loadExistingItems();
            }

            // 显示模态框
            const modalElement = document.getElementById(config.modalId);
            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();

                // 聚焦到输入框并添加搜索监听
                modalElement.addEventListener('shown.bs.modal', function() {
                    const valueInput = document.getElementById('quickAddValue');
                    if (valueInput) {
                        valueInput.focus();

                        // 添加实时搜索功能
                        valueInput.addEventListener('input', function(e) {
                            SelectWithQuickAdd.filterSuggestions(e.target.value);
                            // 清除选中状态（因为用户开始输入了）
                            SelectWithQuickAdd.selectedExistingItem = null;
                            // 移除所有高亮
                            document.querySelectorAll('.quick-add-suggestion').forEach(s => {
                                s.classList.remove('active');
                            });
                        });
                    }
                }, { once: true });
            } else {
                console.error('找不到模态框元素:', config.modalId);
            }
        },

        /**
         * 更新模态框标签
         */
        updateModalLabels: function(config, context) {
            // 更新模态框标题
            const modalTitle = document.querySelector(`#${config.modalId} .modal-title`);
            if (modalTitle && context.displayName) {
                // 如果提供了displayName（如指标名称），显示在标题中
                const titleText = modalTitle.textContent;
                const updatedTitle = titleText.replace(/：.*$/, `：${context.displayName}`);
                modalTitle.textContent = updatedTitle;
            }

            // 更新字段标签
            const valueLabel = document.querySelector(`#${config.modalId} label[for="quickAddValue"]`);
            if (valueLabel) {
                valueLabel.textContent = config.valueFieldLabel;
            }

            const descLabel = document.querySelector(`#${config.modalId} label[for="quickAddDescription"]`);
            if (descLabel) {
                descLabel.textContent = config.descriptionFieldLabel;
            }
        },

        /**
         * 重置表单
         */
        resetForm: function() {
            const valueInput = document.getElementById('quickAddValue');
            const descInput = document.getElementById('quickAddDescription');

            if (valueInput) valueInput.value = '';
            if (descInput) descInput.value = '';

            // 清空已有项目列表
            const existingList = document.getElementById('existingItemsList');
            if (existingList) {
                existingList.innerHTML = '';
            }

            // 清除选中标记
            this.selectedExistingItem = null;
        },

        /**
         * 加载并显示已有项目列表
         */
        loadExistingItems: function() {
            const config = this.activeConfig;
            const container = document.getElementById('existingItemsList');
            if (!container) return;

            // 显示加载状态
            container.innerHTML = '<small class="text-muted"><span class="spinner-border spinner-border-sm me-1"></span>加载中...</small>';

            // 调试日志：显示context内容
            console.log('[SelectWithQuickAdd] loadExistingItems调用', {
                type: this.type,
                context: this.context,
                config: config
            });

            const url = config.getExistingItemsUrl(this.context);
            console.log('[SelectWithQuickAdd] getExistingItemsUrl返回:', url);

            if (!url) {
                console.warn('[SelectWithQuickAdd] URL为空，无法加载列表', {
                    context: this.context
                });
                container.innerHTML = '<small class="text-muted">无法加载列表</small>';
                return;
            }

            console.log('[SelectWithQuickAdd] 开始fetch请求:', url);

            fetch(url)
                .then(response => {
                    console.log('[SelectWithQuickAdd] 收到响应:', {
                        status: response.status,
                        statusText: response.statusText,
                        ok: response.ok
                    });
                    if (!response.ok) {
                        console.error('[SelectWithQuickAdd] HTTP响应错误:', response.status, response.statusText);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('[SelectWithQuickAdd] 解析后的数据:', data);

                    // 保存字段单位并更新显示（兼容多种API格式）
                    // - 旧格式: { field_unit: 'MHz', options: [...] }
                    // - 新格式（规格字典API）: { success: true, data: [...], spec: { unit: 'MHz' } }
                    this.currentFieldUnit = data.field_unit || (data.spec && data.spec.unit) || '';
                    this.updateUnitDisplay(this.currentFieldUnit);

                    // 兼容多种API返回格式
                    let items = data.options || data.data || data.items || [];
                    console.log('[SelectWithQuickAdd] 提取的items数组:', items);
                    console.log('[SelectWithQuickAdd] items原始数量:', items.length);

                    // 客户端过滤已选择的指标（排除excludeIds中的项目）
                    if (SelectWithQuickAdd.context.excludeIds && SelectWithQuickAdd.context.excludeIds.length > 0) {
                        const excludeSet = new Set(SelectWithQuickAdd.context.excludeIds.map(id => parseInt(id)));
                        items = items.filter(item => !excludeSet.has(parseInt(item.id)));
                        console.log('[SelectWithQuickAdd] 过滤后items数量:', items.length, '(排除了', excludeSet.size, '个已选择的)');
                    }

                    if (items.length === 0) {
                        console.warn('[SelectWithQuickAdd] items为空，显示提示信息');
                        container.innerHTML = '<small class="text-muted">暂无可选指标（所有指标已被选择）</small>';
                        return;
                    }

                    // 显示为可点击列表
                    console.log('[SelectWithQuickAdd] 开始生成列表HTML');
                    const listHtml = items.map(item => {
                        const displayText = item.value || item.name || item.code_name;
                        const displayUnit = item.unit ? ` ${item.unit}` : '';
                        const displayCode = item.code ? `<small class="text-muted">${item.code}</small>` : '';
                        const displayDesc = item.description ? `<small class="text-muted d-block">${item.description}</small>` : '';
                        const disabledClass = item.is_active === false ? 'disabled text-muted' : '';
                        const disabledText = item.is_active === false ? ' [已禁用]' : '';

                        return `
                        <a href="#" class="list-group-item list-group-item-action quick-add-suggestion ${disabledClass}"
                           data-id="${item.id}"
                           data-value="${displayText}"
                           data-unit="${item.unit || ''}"
                           data-code="${item.code || ''}"
                           data-description="${item.description || ''}">
                          <div class="d-flex justify-content-between align-items-start">
                            <div>
                              <span class="fw-medium">${displayText}${displayUnit}${disabledText}</span>
                              ${displayDesc}
                            </div>
                            ${displayCode}
                          </div>
                        </a>`;
                    }).join('');

                    console.log('[SelectWithQuickAdd] 生成的HTML长度:', listHtml.length);
                    container.innerHTML = listHtml;

                    // 绑定点击事件
                    console.log('[SelectWithQuickAdd] 绑定点击事件');
                    SelectWithQuickAdd.bindSuggestionClicks();
                })
                .catch(error => {
                    console.error('[SelectWithQuickAdd] 加载项目列表失败:', error);
                    console.error('[SelectWithQuickAdd] 错误堆栈:', error.stack);
                    container.innerHTML = '<small class="text-danger">加载失败</small>';
                });
        },

        /**
         * 绑定建议项点击事件
         */
        bindSuggestionClicks: function() {
            const suggestions = document.querySelectorAll('.quick-add-suggestion');
            suggestions.forEach(item => {
                item.addEventListener('click', (e) => this.handleSuggestionClick(e));
            });
        },

        /**
         * 处理建议项点击
         */
        handleSuggestionClick: function(event) {
            event.preventDefault();

            // 禁用的项不可选
            if (event.currentTarget.classList.contains('disabled')) {
                this.showMessage('该指标已禁用，无法选择', 'warning');
                return;
            }

            const item = event.currentTarget;
            const value = item.dataset.value;
            const unit = item.dataset.unit;
            const id = item.dataset.id;
            const description = item.dataset.description;

            // 填充到输入框
            const valueInput = document.getElementById('quickAddValue');
            const descInput = document.getElementById('quickAddDescription');

            if (valueInput) valueInput.value = value;
            if (descInput && description) descInput.value = description;

            // 更新单位显示
            this.updateUnitDisplay(unit);

            // 标记为选择已有项（不需要创建新的）
            this.selectedExistingItem = {
                id: parseInt(id),
                value: value,
                code: item.dataset.code,
                description: description,
                unit: unit
            };

            // 高亮选中的项
            document.querySelectorAll('.quick-add-suggestion').forEach(s => {
                s.classList.remove('active');
            });
            item.classList.add('active');

            console.log('选择了已有指标:', this.selectedExistingItem);
        },

        /**
         * 搜索过滤建议列表
         */
        filterSuggestions: function(keyword) {
            const suggestions = document.querySelectorAll('.quick-add-suggestion');
            const lowerKeyword = keyword.toLowerCase();

            suggestions.forEach(item => {
                const text = item.textContent.toLowerCase();
                if (text.includes(lowerKeyword)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        },

        /**
         * 提交新项目
         */
        submit: function() {
            const config = this.activeConfig;
            if (!config) {
                console.error('未找到激活的配置');
                return;
            }

            const valueInput = document.getElementById('quickAddValue');
            const descInput = document.getElementById('quickAddDescription');
            const saveBtn = document.getElementById('quickAddSaveBtn');

            if (!valueInput) {
                console.error('找不到值输入框');
                return;
            }

            const value = valueInput.value.trim();
            const description = descInput ? descInput.value.trim() : '';

            // 验证
            if (!value) {
                this.showMessage(`请输入${config.valueFieldLabel}`, 'warning');
                valueInput.focus();
                return;
            }

            // 记录是否选择了已有项（用于日志）
            const isSelectingExisting = !!this.selectedExistingItem;
            if (isSelectingExisting) {
                console.log('选择已有项并添加:', this.selectedExistingItem);
            } else {
                console.log('创建新项:', value);
            }

            // 禁用按钮，显示加载状态
            if (saveBtn) {
                saveBtn.disabled = true;
                saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>保存中...';
            }

            // 构建请求数据
            const requestData = {
                value: value,
                description: description
            };

            // 如果选择了已有的规格指标，传递 spec_option_id
            if (this.selectedExistingItem && this.selectedExistingItem.id) {
                requestData.spec_option_id = this.selectedExistingItem.id;
                console.log('传递已有指标引用, spec_option_id:', this.selectedExistingItem.id);
            }

            // 添加相关ID（如果需要）
            if (this.context.relatedId) {
                requestData.related_id = this.context.relatedId;
            }

            // 添加额外的上下文数据
            if (config.buildRequestData) {
                Object.assign(requestData, config.buildRequestData(this.context));
            }

            console.log('提交新项目:', requestData);

            // 获取CSRF token（兼容input和meta标签）
            const csrfToken = document.querySelector('input[name="csrf_token"]') ||
                              document.querySelector('meta[name="csrf-token"]');
            if (!csrfToken) {
                console.error('找不到CSRF token');
                this.restoreSaveButton(saveBtn);
                this.showMessage('系统错误：找不到CSRF token', 'error');
                return;
            }

            // 获取token值（兼容input的value和meta的content）
            const tokenValue = csrfToken.value || csrfToken.getAttribute('content');

            // 发送请求
            fetch(config.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': tokenValue
                },
                body: JSON.stringify(requestData)
            })
            .then(response => response.json())
            .then(data => {
                console.log('API响应:', data);

                if (data.success) {
                    // 关闭模态框
                    const modalElement = document.getElementById(config.modalId);
                    if (modalElement) {
                        const modal = bootstrap.Modal.getInstance(modalElement);
                        if (modal) {
                            modal.hide();
                        }
                    }

                    // 刷新目标
                    if (config.refreshTarget && data.new_item) {
                        config.refreshTarget(this.context, data.new_item);
                    }

                    // 成功回调
                    if (config.onSuccess) {
                        config.onSuccess(data);
                    }

                    // 清除选中标记（无论是选择已有还是创建新的，都已成功添加）
                    if (this.selectedExistingItem) {
                        this.selectedExistingItem = null;
                    }

                    // 提示成功
                    const codeInfo = data.new_item && data.new_item.code ? `，编码：${data.new_item.code}` : '';
                    const actionText = isSelectingExisting ? '选择并添加' : '添加';
                    this.showMessage(`${config.valueFieldLabel} "${value}" ${actionText}成功${codeInfo}`, 'success');
                } else {
                    throw new Error(data.message || '添加失败');
                }
            })
            .catch(error => {
                console.error('添加失败:', error);

                // 错误回调
                if (config.onError) {
                    config.onError(error);
                }

                this.showMessage('添加失败：' + error.message, 'error');
            })
            .finally(() => {
                // 恢复按钮状态
                this.restoreSaveButton(saveBtn);
            });
        },

        /**
         * 恢复保存按钮状态
         */
        restoreSaveButton: function(button) {
            if (button) {
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-check me-1"></i>保存并选择';
            }
        },

        /**
         * 更新输入框右侧的单位显示
         * @param {string} unit - 单位文本
         */
        updateUnitDisplay: function(unit) {
            const unitElement = document.getElementById('quickAddValueUnit');
            if (!unitElement) return;

            if (unit && unit.trim() !== '') {
                unitElement.textContent = unit;
                unitElement.style.display = '';  // 显示
            } else {
                unitElement.textContent = '';
                unitElement.style.display = 'none';  // 隐藏
            }
        },

        /**
         * 显示消息
         */
        showMessage: function(message, type) {
            // 类型映射
            const typeMap = {
                'success': 'success',
                'error': 'danger',
                'warning': 'warning',
                'info': 'info'
            };
            const alertType = typeMap[type] || 'info';

            // 尝试使用通用通知
            if (typeof showTopNotification === 'function') {
                const duration = type === 'error' ? 0 : 5000;
                showTopNotification(message, type, duration);
                return;
            }

            // 尝试使用Toast
            if (typeof window.showToast === 'function') {
                window.showToast(type, message);
                return;
            }

            // 尝试使用Bootstrap Toast
            const toastContainer = document.querySelector('.toast-container');
            if (toastContainer && typeof bootstrap !== 'undefined' && bootstrap.Toast) {
                const toastHtml = `
                    <div class="toast align-items-center text-bg-${alertType} border-0" role="alert" aria-live="assertive">
                        <div class="d-flex">
                            <div class="toast-body">
                                ${type === 'success' ? '<i class="fas fa-check-circle me-2"></i>' : ''}
                                ${type === 'error' ? '<i class="fas fa-exclamation-circle me-2"></i>' : ''}
                                ${type === 'warning' ? '<i class="fas fa-exclamation-triangle me-2"></i>' : ''}
                                ${message}
                            </div>
                            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                        </div>
                    </div>
                `;
                toastContainer.insertAdjacentHTML('beforeend', toastHtml);
                const toastElement = toastContainer.lastElementChild;
                const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 3000 });
                toast.show();

                setTimeout(() => toastElement.remove(), 3500);
                return;
            }

            // 降级到console和alert
            console.log(`[${type.toUpperCase()}] ${message}`);
            if (type === 'error') {
                alert(message);
            }
        },

        /**
         * 初始化
         */
        init: function() {
            console.log('SelectWithQuickAdd tool loaded');

            // 绑定模态框隐藏事件（使用事件委托）
            document.addEventListener('hidden.bs.modal', (e) => {
                const modal = e.target;
                if (modal && this.activeConfig && modal.id === this.activeConfig.modalId) {
                    this.resetForm();
                }
            });

            // 绑定保存按钮点击事件
            const saveBtn = document.getElementById('quickAddSaveBtn');
            if (saveBtn) {
                saveBtn.addEventListener('click', () => this.submit());
            }

            // 支持Enter键提交
            const valueInput = document.getElementById('quickAddValue');
            if (valueInput) {
                valueInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        this.submit();
                    }
                });
            }
        }
    };

    /**
     * 预设配置：产品规格指标
     */
    SelectWithQuickAdd.register('indicator', {
        modalId: 'selectQuickAddModal',
        apiEndpoint: '/product-management/api/spec-field-options/add',
        valueFieldLabel: '指标名称',
        descriptionFieldLabel: '指标描述',
        relatedIdErrorMsg: '无法获取产品分类信息，请先选择产品分类',

        getRelatedId: function() {
            const subcategoryIdInput = document.getElementById('subcategory_id') ||
                                      document.querySelector('input[name="subcategory_id"]');
            return subcategoryIdInput ? subcategoryIdInput.value : null;
        },

        getExistingItemsUrl: function(context) {
            // 只需要规格名称即可获取全局指标（从规格字典获取）
            if (!context.specName) return null;

            // 使用规格字典API获取全局指标，不依赖subcategory_id
            const url = new URL(`/api/spec-dictionary/options/by-name/${encodeURIComponent(context.specName)}`, window.location.origin);
            url.searchParams.append('active_only', 'true');  // 只显示启用的指标

            return url.toString();
        },

        buildRequestData: function(context) {
            return {
                subcategory_id: context.relatedId,
                spec_name: context.specName,
                field_id: context.specFieldId || ''
            };
        },

        refreshTarget: function(context, newItem) {
            if (!context.targetRow) {
                console.warn('未指定目标行，无法自动刷新');
                return;
            }

            const row = context.targetRow;
            const indicatorSelect = row.querySelector('.indicator-select');
            const indicatorInput = row.querySelector('.indicator-input');
            const indicatorTextInput = row.querySelector('.indicator-text-input');

            if (indicatorSelect) {
                // 编辑页面：select下拉框
                refreshSelectIndicator(indicatorSelect, newItem);
            } else if (indicatorInput || indicatorTextInput) {
                // 创建页面：自定义输入框
                refreshCustomIndicator(row, newItem);
            }
        }
    });

    /**
     * 预设配置：产品名称（子分类）
     */
    SelectWithQuickAdd.register('subcategory', {
        modalId: 'selectQuickAddModal',
        apiEndpoint: '/product-code/api/subcategories/quick-add',
        valueFieldLabel: '产品名称',
        descriptionFieldLabel: '名称描述',
        relatedIdErrorMsg: '请先选择产品分类',

        getRelatedId: function() {
            const categoryIdInput = document.getElementById('category_id') ||
                                   document.querySelector('select[name="category_id"]');
            return categoryIdInput ? categoryIdInput.value : null;
        },

        getExistingItemsUrl: function(context) {
            if (!context.relatedId) return null;
            const url = new URL('/product-code/api/subcategories', window.location.origin);
            url.searchParams.append('category_id', context.relatedId);
            return url.toString();
        },

        buildRequestData: function(context) {
            return {
                category_id: context.relatedId
            };
        },

        refreshTarget: function(context, newItem) {
            if (!context.targetSelect) {
                console.warn('未指定目标select，无法自动刷新');
                return;
            }

            refreshSelectOption(context.targetSelect, newItem, '__ADD_NEW_SUBCATEGORY__');
        }
    });

    /**
     * 预设配置：销售区域
     */
    SelectWithQuickAdd.register('region', {
        modalId: 'selectQuickAddModal',
        apiEndpoint: '/product-code/api/regions/quick-add',
        valueFieldLabel: '区域名称',
        descriptionFieldLabel: '区域描述',

        getExistingItemsUrl: function(context) {
            return '/product-code/api/regions';  // 已经是字符串，无需修改
        },

        refreshTarget: function(context, newItem) {
            if (!context.targetSelect) {
                console.warn('未指定目标select，无法自动刷新');
                return;
            }

            refreshSelectOption(context.targetSelect, newItem, '__ADD_NEW_REGION__');
        }
    });

    /**
     * 辅助函数：刷新select选项
     */
    function refreshSelectOption(selectElement, newItem, addNewValue) {
        const option = document.createElement('option');
        // 修复：使用实际值作为option的value，而不是数据库ID
        // 这样可以确保change事件读取到正确的值，而不是ID
        option.value = newItem.value || newItem.name;
        const displayText = newItem.name || newItem.value;
        const displayUnit = newItem.unit ? ` ${newItem.unit}` : '';
        option.textContent = `${displayText}${displayUnit}`;
        if (newItem.code) option.dataset.code = newItem.code;
        if (newItem.code_letter) option.dataset.letter = newItem.code_letter;
        if (newItem.id) option.dataset.id = newItem.id;

        // 查找"添加新XXX"特殊选项
        const addNewOption = Array.from(selectElement.options).find(opt => opt.value === addNewValue);
        if (addNewOption) {
            selectElement.insertBefore(option, addNewOption);
        } else {
            selectElement.appendChild(option);
        }

        // 自动选中新添加的选项（使用value值，而不是ID）
        selectElement.value = newItem.value || newItem.name;
        selectElement.dispatchEvent(new Event('change', { bubbles: true }));

        console.log('已添加并选中:', newItem.name || newItem.value);
    }

    /**
     * 辅助函数：刷新select类型的指标选择器
     */
    function refreshSelectIndicator(selectElement, newItem) {
        refreshSelectOption(selectElement, newItem, '__ADD_NEW_INDICATOR__');
    }

    /**
     * 辅助函数：刷新自定义输入框类型的指标选择器
     */
    function refreshCustomIndicator(row, newItem) {
        // 更新文本输入框的值
        const textInput = row.querySelector('.indicator-text-input');
        if (textInput) {
            textInput.value = newItem.value;
            textInput.dispatchEvent(new Event('input', { bubbles: true }));
        }

        // 更新隐藏字段
        const valueHidden = row.querySelector('input[name="indicator_value[]"]');
        const codeHidden = row.querySelector('input[name="indicator_code[]"]');

        if (valueHidden) valueHidden.value = newItem.value;
        if (codeHidden && newItem.code) codeHidden.value = newItem.code;

        // 如果存在下拉菜单，添加新选项
        const dropdown = row.querySelector('.indicator-dropdown');
        if (dropdown) {
            const itemHtml = `
                <div class="indicator-dropdown-item"
                     data-option-id="${newItem.id || ''}"
                     data-option-value="${newItem.value}"
                     data-option-code="${newItem.code || '0'}">
                    <span class="indicator-value">${newItem.value}</span>
                    ${newItem.code && newItem.code !== '0' ?
                      `<span class="indicator-code ms-2 text-muted">[${newItem.code}]</span>` : ''}
                </div>
            `;
            const addButton = dropdown.querySelector('.indicator-dropdown-item-add');
            if (addButton) {
                addButton.insertAdjacentHTML('beforebegin', itemHtml);
            } else {
                dropdown.insertAdjacentHTML('beforeend', itemHtml);
            }
        }

        console.log('已设置指标值:', newItem.value);
    }

    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.SelectWithQuickAdd.init();
        });
    } else {
        window.SelectWithQuickAdd.init();
    }

    // 向后兼容：保留原IndicatorQuickAdd接口
    window.IndicatorQuickAdd = {
        showQuickAddModal: function(specName, specFieldId, rowElement, excludeIds) {
            window.SelectWithQuickAdd.showModal('indicator', {
                specName: specName,
                specFieldId: specFieldId,
                targetRow: rowElement,
                displayName: specName,
                excludeIds: excludeIds || []  // 传递已选择的指标ID列表（用于排除）
            });
        },
        configure: function(options) {
            if (options && typeof options === 'object') {
                console.log('[IndicatorQuickAdd] 应用自定义配置', options);
                const indicatorConfig = window.SelectWithQuickAdd.configs.indicator;
                if (indicatorConfig) {
                    // 使用逐属性赋值确保函数属性正确覆盖
                    Object.keys(options).forEach(key => {
                        console.log(`[IndicatorQuickAdd] 覆盖配置属性: ${key}`, typeof options[key]);
                        indicatorConfig[key] = options[key];
                    });
                    console.log('[IndicatorQuickAdd] 配置覆盖完成', indicatorConfig);
                } else {
                    console.error('[IndicatorQuickAdd] 找不到indicator配置对象');
                }
            }
        }
    };

})();
