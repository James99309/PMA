/**
 * 通用审批字段控制工具
 *
 * 通过模板属性 data-field-code 自动控制字段的启用/禁用状态
 * 用于审批流程中限制用户只能编辑特定字段
 *
 * 使用方式:
 * 1. 在模板控件上添加 data-field-code="字段代码" 属性
 * 2. 调用 ApprovalFieldControl.apply(container, editableFields)
 *
 * 模板属性说明:
 * - data-field-code: 字段代码，与审批模板配置一致
 * - data-field-role: 控件角色（可选）
 *   - search: 搜索输入框
 *   - value: 隐藏值字段
 *   - clear: 清除按钮
 *   - upload: 文件上传
 *   - delete-preview: 删除预览按钮
 *
 * 特殊字段代码:
 * - __add_row__: 添加行按钮（审批模式下始终禁用）
 * - __delete_row__: 删除行按钮（审批模式下始终禁用）
 *
 * @version 1.0.0
 * @date 2025-12-11
 */
(function(window) {
    'use strict';

    // 默认配置
    const defaultOptions = {
        // 可编辑样式
        editableClasses: ['bg-amber-50', 'dark:bg-amber-900/20'],
        // 不可编辑样式
        disabledClasses: ['bg-slate-100', 'dark:bg-slate-700', 'cursor-not-allowed', 'opacity-60'],
        // 按钮禁用样式
        buttonDisabledClasses: ['opacity-50', 'cursor-not-allowed'],
        // 是否隐藏禁用的清除按钮
        hideClearButtons: true,
        // 是否隐藏禁用的删除按钮
        hideDeleteButtons: true,
        // 是否禁用操作按钮（添加行、删除行）
        disableActionButtons: true,
        // 调试模式
        debug: false
    };

    // 操作按钮的特殊字段代码
    const ACTION_FIELD_CODES = ['__add_row__', '__delete_row__'];

    /**
     * 解析容器元素
     */
    function resolveContainer(container) {
        if (typeof container === 'string') {
            return document.querySelector(container);
        }
        return container;
    }

    /**
     * 按字段代码分组元素
     */
    function groupByFieldCode(elements) {
        const groups = {};
        elements.forEach(el => {
            const code = el.dataset.fieldCode;
            if (!groups[code]) {
                groups[code] = [];
            }
            groups[code].push(el);
        });
        return groups;
    }

    /**
     * 移除元素的样式类
     */
    function removeClasses(element, classes) {
        classes.forEach(cls => element.classList.remove(cls));
    }

    /**
     * 添加元素的样式类
     */
    function addClasses(element, classes) {
        classes.forEach(cls => element.classList.add(cls));
    }

    /**
     * 启用元素
     */
    function enableElement(element, role, options) {
        const tagName = element.tagName.toLowerCase();

        // 根据角色处理
        switch (role) {
            case 'clear':
            case 'delete-preview':
                // 清除/删除预览按钮：显示
                element.classList.remove('hidden');
                element.disabled = false;
                break;
            case 'value':
                // 隐藏值字段：不做样式处理
                break;
            case 'search':
            case 'upload':
            default:
                // 普通输入控件：启用并添加高亮
                element.disabled = false;
                removeClasses(element, options.disabledClasses);
                addClasses(element, options.editableClasses);
                break;
        }

        // 按钮特殊处理
        if (tagName === 'button') {
            element.disabled = false;
            removeClasses(element, options.buttonDisabledClasses);
            element.style.pointerEvents = '';
        }
    }

    /**
     * 禁用元素
     */
    function disableElement(element, role, options) {
        const tagName = element.tagName.toLowerCase();

        // 根据角色处理
        switch (role) {
            case 'clear':
                // 清除按钮：隐藏或禁用
                if (options.hideClearButtons) {
                    element.classList.add('hidden');
                } else {
                    element.disabled = true;
                    addClasses(element, options.buttonDisabledClasses);
                }
                break;
            case 'delete-preview':
                // 删除预览按钮：隐藏或禁用
                if (options.hideDeleteButtons) {
                    element.classList.add('hidden');
                } else {
                    element.disabled = true;
                    addClasses(element, options.buttonDisabledClasses);
                }
                break;
            case 'value':
                // 隐藏值字段：不做样式处理
                break;
            case 'search':
            case 'upload':
            default:
                // 普通输入控件：禁用并添加灰色背景
                element.disabled = true;
                removeClasses(element, options.editableClasses);
                addClasses(element, options.disabledClasses);
                break;
        }

        // 按钮特殊处理
        if (tagName === 'button') {
            element.disabled = true;
            addClasses(element, options.buttonDisabledClasses);
            element.style.pointerEvents = 'none';
        }
    }

    /**
     * 处理操作按钮（添加行、删除行等）
     */
    function processActionButtons(container, options) {
        ACTION_FIELD_CODES.forEach(code => {
            const buttons = container.querySelectorAll(`[data-field-code="${code}"]`);
            buttons.forEach(btn => {
                btn.disabled = true;
                addClasses(btn, options.buttonDisabledClasses);
                btn.style.pointerEvents = 'none';

                if (options.debug) {
                    console.log(`[ApprovalFieldControl] Action button disabled: ${code}`);
                }
            });
        });
    }

    const ApprovalFieldControl = {
        /**
         * 应用字段控制
         * @param {HTMLElement|string} container - 容器元素或选择器
         * @param {Array<string>} editableFields - 可编辑字段代码列表
         * @param {Object} options - 可选配置
         * @returns {Object} - { success: boolean, stats: object }
         */
        apply: function(container, editableFields, options = {}) {
            const opts = Object.assign({}, defaultOptions, options);
            const containerEl = resolveContainer(container);

            if (!containerEl) {
                console.error('[ApprovalFieldControl] Container not found');
                return { success: false, stats: null };
            }

            const editableSet = new Set(editableFields || []);
            const stats = { total: 0, enabled: 0, disabled: 0, groups: {} };

            if (opts.debug) {
                console.log('[ApprovalFieldControl] Applying field control');
                console.log('[ApprovalFieldControl] Editable fields:', editableFields);
            }

            // 1. 查找所有带 data-field-code 的元素
            const elements = containerEl.querySelectorAll('[data-field-code]');
            stats.total = elements.length;

            // 2. 按字段代码分组
            const groups = groupByFieldCode(elements);

            // 3. 遍历每个字段组
            for (const [fieldCode, groupElements] of Object.entries(groups)) {
                // 跳过操作按钮，后面单独处理
                if (ACTION_FIELD_CODES.includes(fieldCode)) {
                    continue;
                }

                const isEditable = editableSet.has(fieldCode);
                stats.groups[fieldCode] = { count: groupElements.length, editable: isEditable };

                // 4. 处理每个元素
                for (const element of groupElements) {
                    const role = element.dataset.fieldRole || '';

                    if (isEditable) {
                        enableElement(element, role, opts);
                        stats.enabled++;
                    } else {
                        disableElement(element, role, opts);
                        stats.disabled++;
                    }

                    if (opts.debug) {
                        console.log(`[ApprovalFieldControl] Field ${fieldCode} (role=${role}): ${isEditable ? 'ENABLED' : 'DISABLED'}`);
                    }
                }
            }

            // 5. 处理操作按钮（始终禁用）
            if (opts.disableActionButtons) {
                processActionButtons(containerEl, opts);
            }

            if (opts.debug) {
                console.log('[ApprovalFieldControl] Stats:', stats);
            }

            return { success: true, stats: stats };
        },

        /**
         * 应用明细行控制（用于动态添加的行）
         * @param {HTMLElement} row - 明细行元素
         * @param {Array<string>} editableFields - 可编辑字段代码列表
         * @param {Object} options - 可选配置
         */
        applyToRow: function(row, editableFields, options = {}) {
            const opts = Object.assign({}, defaultOptions, options);
            const editableSet = new Set(editableFields || []);

            if (opts.debug) {
                console.log('[ApprovalFieldControl] Applying to row');
                console.log('[ApprovalFieldControl] Row:', row);
                console.log('[ApprovalFieldControl] Editable fields:', editableFields);
            }

            // 查找行内所有带 data-field-code 的元素
            const elements = row.querySelectorAll('[data-field-code]');

            elements.forEach(element => {
                const fieldCode = element.dataset.fieldCode;
                const role = element.dataset.fieldRole || '';

                // 操作按钮（如删除行）始终禁用
                if (ACTION_FIELD_CODES.includes(fieldCode)) {
                    disableElement(element, role, opts);
                    if (opts.debug) {
                        console.log(`[ApprovalFieldControl] Action button in row disabled: ${fieldCode}`);
                    }
                    return;
                }

                const isEditable = editableSet.has(fieldCode);

                if (isEditable) {
                    enableElement(element, role, opts);
                } else {
                    disableElement(element, role, opts);
                }

                if (opts.debug) {
                    console.log(`[ApprovalFieldControl] Row field ${fieldCode} (role=${role}): ${isEditable ? 'ENABLED' : 'DISABLED'}`);
                }
            });
        },

        /**
         * 重置字段状态（恢复为可编辑）
         * @param {HTMLElement|string} container - 容器元素或选择器
         */
        reset: function(container) {
            const containerEl = resolveContainer(container);

            if (!containerEl) {
                console.error('[ApprovalFieldControl] Container not found');
                return;
            }

            const elements = containerEl.querySelectorAll('[data-field-code]');

            elements.forEach(element => {
                const role = element.dataset.fieldRole || '';
                const tagName = element.tagName.toLowerCase();

                // 移除所有控制样式
                removeClasses(element, defaultOptions.editableClasses);
                removeClasses(element, defaultOptions.disabledClasses);
                removeClasses(element, defaultOptions.buttonDisabledClasses);

                // 恢复启用状态
                element.disabled = false;
                element.classList.remove('hidden');

                if (tagName === 'button') {
                    element.style.pointerEvents = '';
                }
            });
        }
    };

    // 暴露到全局
    window.ApprovalFieldControl = ApprovalFieldControl;

})(window);
