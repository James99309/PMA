/**
 * 规格编辑管理器 - 可复用组件
 *
 * 用于产品详情页和研发产品详情页的规格编辑功能
 *
 * 使用示例:
 * const specEditor = new SpecEditor({
 *     productId: 123,
 *     apiEndpoint: '/product-management/api/rd-products/123/specs',
 *     containerId: 'productSpecsContainer',
 *     listId: 'productSpecsList',
 *     emptyMessageId: 'emptySpecsMessage',
 *     buttons: {
 *         edit: 'editSpecsBtn',
 *         apply: 'applySpecsBtn',
 *         cancel: 'cancelSpecsBtn',
 *         add: 'addSpecBtn'
 *     },
 *     i18n: { ... },
 *     csrfToken: 'xxx',
 *     onSaveSuccess: function() { window.location.reload(); },
 *
 *     // 产品库特有功能配置
 *     features: {
 *         descriptionControl: true,   // 是否启用描述包含控制
 *         codePreview: true,          // 是否启用编码预览
 *         addNewSpec: false           // 是否启用添加新规格（研发产品用）
 *     },
 *     previewEndpoint: '/api/products/123/specs/preview',  // 预览API
 *     onShowPreview: function(data, confirmFn) { ... },     // 显示预览模态框
 *     onShowConflict: function(data) { ... },               // 显示冲突模态框
 *     onPartialRefresh: function(result) { ... }            // 局部刷新DOM
 * });
 * specEditor.init();
 */
class SpecEditor {
    constructor(options) {
        this.productId = options.productId;
        this.apiEndpoint = options.apiEndpoint;
        this.containerId = options.containerId || 'productSpecsContainer';
        this.listId = options.listId || 'productSpecsList';
        this.emptyMessageId = options.emptyMessageId || 'emptySpecsMessage';
        this.buttons = options.buttons || {};
        this.csrfToken = options.csrfToken || '';
        this.onSaveSuccess = options.onSaveSuccess || function() { window.location.reload(); };

        // 功能开关配置
        this.features = Object.assign({
            descriptionControl: false,   // 是否启用描述包含控制（产品库用）
            codePreview: false,          // 是否启用编码预览（产品库用）
            addNewSpec: true             // 是否启用添加新规格（研发产品用）
        }, options.features || {});

        // 编码预览相关配置（产品库用）
        this.previewEndpoint = options.previewEndpoint || null;
        this.onShowPreview = options.onShowPreview || null;
        this.onShowConflict = options.onShowConflict || null;
        this.onPartialRefresh = options.onPartialRefresh || null;

        // 模态框 ID 配置
        this.modals = Object.assign({
            preview: 'specMnPreviewModal',
            conflict: 'specConflictModal'
        }, options.modals || {});

        // 预览确认回调
        this._previewConfirmCallback = null;

        // 子分类ID（用于获取该分类可用的非编码规格）
        this.subcategoryId = options.subcategoryId || null;

        // 国际化文本
        this.i18n = Object.assign({
            edit: '编辑',
            apply: '应用',
            cancel: '取消',
            delete: '删除',
            saveSuccess: '保存成功',
            saveError: '保存失败',
            loading: '加载中...',
            selectSpec: '选择规格',
            selectSpecFirst: '请先选择规格',
            noAvailableSpecs: '没有可添加的规格',
            noAvailableOptions: '暂无可用选项',
            emptySpecs: '暂无规格信息',
            notSet: '未设置',
            includeInDesc: '包含在描述中',
            excludeFromDesc: '从描述中排除',
            missingCodes: '以下规格缺少编码，无法保存：',
            loadingSpecs: '加载规格字段中...'
        }, options.i18n || {});

        // 状态
        this.isEditMode = false;
        this.pendingChanges = { modified: [], added: [], deleted: [], descriptionChanged: [] };
        this.originalData = [];
        this.specOptionsCache = {};
    }

    /**
     * 初始化
     */
    init() {
        // 绑定按钮事件
        this._bindButtonEvents();
        // 绑定模板渲染的缺失规格下拉框事件
        this._bindMissingSpecSelects();
    }

    /**
     * 绑定模板渲染的缺失规格下拉框事件
     * 用于处理 __MANAGE_OPTIONS__ 选择
     */
    _bindMissingSpecSelects() {
        const self = this;
        const container = document.getElementById(this.listId);
        if (!container) return;

        // 查找所有缺失规格的下拉框
        const missingRows = container.querySelectorAll('.spec-row[data-is-missing="true"]');
        missingRows.forEach(row => {
            const select = row.querySelector('.value-select');
            if (!select || select.dataset.manageListenerAdded) return;

            select.dataset.manageListenerAdded = 'true';
            const fieldName = row.dataset.fieldName;

            select.addEventListener('change', function(e) {
                if (e.target.value === '__MANAGE_OPTIONS__') {
                    // 恢复之前的选择
                    e.target.value = '';

                    if (typeof SpecOptionsModal !== 'undefined') {
                        const fieldId = row.dataset.fieldId;
                        // 使用子分类模式打开模态框
                        SpecOptionsModal.open(fieldName, {
                            subcategoryId: self.subcategoryId,
                            fieldId: fieldId,
                            mode: 'subcategory',
                            onOptionAdded: async function(updatedFieldName) {
                                // 重新加载选项
                                await self._reloadMissingSpecOptions(select, fieldName, fieldId);
                            }
                        });
                    }
                }
            });
        });
    }

    /**
     * 重新加载缺失规格的选项
     */
    async _reloadMissingSpecOptions(select, fieldName, fieldId) {
        try {
            if (!this.subcategoryId) return;

            const response = await fetch(`/product-management/api/subcategory/${this.subcategoryId}/spec-fields`);
            const data = await response.json();
            if (!data.spec_fields) return;

            const spec = data.spec_fields.find(f => f.name === fieldName || f.id == fieldId);
            if (!spec || !spec.options) return;

            // 保存当前选中值
            const currentValue = select.value;

            // 清空并重新填充选项
            select.innerHTML = '';

            const defaultOpt = document.createElement('option');
            defaultOpt.value = '';
            defaultOpt.textContent = `-- ${this.i18n.selectSpec || '请选择'} --`;
            select.appendChild(defaultOpt);

            spec.options.forEach(opt => {
                const option = document.createElement('option');
                option.value = opt.value;
                option.textContent = opt.value;
                option.dataset.code = opt.code || '';
                select.appendChild(option);
            });

            // 添加分隔线和管理选项
            const separator = document.createElement('option');
            separator.disabled = true;
            separator.textContent = '──────────';
            select.appendChild(separator);

            const manageOption = document.createElement('option');
            manageOption.value = '__MANAGE_OPTIONS__';
            manageOption.textContent = '+ 管理规格选项';
            select.appendChild(manageOption);

            // 尝试恢复之前的选择
            if (currentValue) {
                select.value = currentValue;
            }
        } catch (e) {
            console.error('重新加载规格选项失败:', e);
        }
    }

    /**
     * 绑定按钮事件
     */
    _bindButtonEvents() {
        const self = this;

        // 编辑按钮
        const editBtn = document.getElementById(this.buttons.edit);
        if (editBtn) {
            editBtn.addEventListener('click', () => self.toggleEditMode());
        }

        // 应用按钮
        const applyBtn = document.getElementById(this.buttons.apply);
        if (applyBtn) {
            applyBtn.addEventListener('click', () => self.applyChanges());
        }

        // 取消按钮
        const cancelBtn = document.getElementById(this.buttons.cancel);
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => self.cancelEditMode());
        }

        // 添加按钮
        const addBtn = document.getElementById(this.buttons.add);
        if (addBtn) {
            addBtn.addEventListener('click', () => self.addNewSpecRow());
        }
    }

    /**
     * 初始化原始数据
     */
    _initOriginalData() {
        this.originalData = [];
        document.querySelectorAll('.spec-row').forEach(row => {
            this.originalData.push({
                id: row.dataset.specId,
                field_name: row.dataset.fieldName,
                field_value: row.dataset.fieldValue,
                field_code: row.dataset.fieldCode || '',
                unit: row.dataset.unit,
                include_in_description: row.dataset.includeInDesc === 'true'
            });
        });
    }

    /**
     * 更新应用按钮状态
     */
    updateApplyButtonState() {
        const applyBtn = document.getElementById(this.buttons.apply);
        if (!applyBtn) return;

        // 检查是否有未确认的新行
        const hasUnfinishedNewRow = document.querySelector('.spec-row-new-input') !== null;

        // 检查是否有正在编辑中的已有规格
        const editingRows = document.querySelectorAll('.spec-row:not(.spec-row-new-input) .value-select:not(.hidden)');
        const hasEditingRow = editingRows.length > 0;

        const shouldDisable = hasUnfinishedNewRow || hasEditingRow;

        if (shouldDisable) {
            applyBtn.disabled = true;
            applyBtn.classList.add('opacity-50', 'cursor-not-allowed', 'pointer-events-none');
            applyBtn.classList.remove('hover:text-green-700', 'text-green-600');
            applyBtn.classList.add('text-slate-400');
        } else {
            applyBtn.disabled = false;
            applyBtn.classList.remove('opacity-50', 'cursor-not-allowed', 'pointer-events-none', 'text-slate-400');
            applyBtn.classList.add('hover:text-green-700', 'text-green-600');
        }
    }

    /**
     * 切换编辑模式
     */
    toggleEditMode() {
        this.isEditMode = true;
        this._initOriginalData();
        this.pendingChanges = { modified: [], added: [], deleted: [], descriptionChanged: [] };

        // 切换按钮显示
        document.getElementById(this.buttons.edit)?.classList.add('hidden');
        document.getElementById(this.buttons.apply)?.classList.remove('hidden');
        document.getElementById(this.buttons.cancel)?.classList.remove('hidden');

        // 只有启用添加新规格功能时才显示添加按钮
        if (this.features.addNewSpec) {
            document.getElementById(this.buttons.add)?.classList.remove('hidden');
        }

        // 显示操作按钮
        document.querySelectorAll('.spec-actions').forEach(el => el.classList.remove('hidden'));

        // 加载缺失的编码规格
        if (this.subcategoryId) {
            this._loadMissingCodedSpecs();
        }

        // 更新应用按钮状态
        this.updateApplyButtonState();
    }

    /**
     * 加载缺失的编码规格（use_in_code=true，包含继承）
     */
    async _loadMissingCodedSpecs() {
        try {
            const response = await fetch(`/product-management/api/subcategory/${this.subcategoryId}/spec-fields`);
            const data = await response.json();
            if (!data.spec_fields) return;

            // 获取已存在的规格名称
            const existingNames = new Set();
            document.querySelectorAll('.spec-row .spec-name').forEach(el => {
                existingNames.add(el.textContent.trim());
            });

            // 过滤缺失的编码规格
            const missing = data.spec_fields.filter(f => f.use_in_code && !existingNames.has(f.name));
            if (missing.length === 0) return;

            // 隐藏空消息
            const emptyMsg = document.getElementById(this.emptyMessageId);
            if (emptyMsg) emptyMsg.style.display = 'none';

            // 获取或创建列表容器
            let specsList = document.getElementById(this.listId);
            if (!specsList) {
                const container = document.getElementById(this.containerId);
                if (!container) return;
                specsList = document.createElement('dl');
                specsList.id = this.listId;
                container.appendChild(specsList);
            }

            for (const spec of missing) {
                this._createCodedSpecRow(specsList, spec);
            }
        } catch (e) {
            console.error('加载编码规格失败:', e);
        }
    }

    /**
     * 创建编码规格行（与已有规格行UI一致）
     */
    _createCodedSpecRow(container, spec) {
        const row = document.createElement('div');
        row.className = 'spec-row px-6 py-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors border-t border-slate-100 dark:border-slate-800';
        row.dataset.new = 'true';
        row.dataset.fieldName = spec.name;
        row.dataset.fieldId = spec.id;  // 存储字段ID
        row.dataset.fieldValue = '';
        row.dataset.fieldCode = '';
        row.dataset.includeInDesc = 'true';
        row.dataset.isMissing = 'true';  // 标记为缺失规格

        const unit = spec.unit || '';

        row.innerHTML = `
            <div class="flex-1 grid grid-cols-3 gap-4">
                <dt class="text-sm font-medium text-slate-500 dark:text-slate-400">
                    <span class="spec-name">${spec.name}</span>
                </dt>
                <dd class="spec-value text-sm text-slate-900 dark:text-slate-200 col-span-2 mt-0 flex items-center gap-2">
                    <span class="value-display hidden"></span>
                    <span class="unit-display hidden text-slate-400">${unit}</span>
                    <select class="value-select w-32 px-2 py-1 text-sm border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-200" data-field-name="${spec.name}">
                        <option value="">-- 请选择 --</option>
                    </select>
                    <span class="unit-edit text-slate-400">${unit}</span>
                </dd>
            </div>
            <div class="spec-actions flex items-center gap-1 ml-4">
                <button type="button" class="spec-confirm-btn p-1.5 text-slate-400 hover:text-green-500 rounded hover:bg-slate-100 dark:hover:bg-slate-700" title="${this.i18n.apply}">
                    <span class="material-symbols-outlined text-lg">check</span>
                </button>
                <button type="button" class="spec-visibility-btn p-1.5 text-slate-400 hover:text-amber-500 rounded hover:bg-slate-100 dark:hover:bg-slate-700" title="${this.i18n.excludeFromDesc || '从描述中排除'}">
                    <span class="material-symbols-outlined text-lg">visibility</span>
                </button>
            </div>
        `;
        container.appendChild(row);

        const select = row.querySelector('.value-select');
        const self = this;

        // 填充选项（包括管理选项）
        this._populateCodedSpecOptions(select, spec);

        // 值变化事件
        select.addEventListener('change', function(e) {
            // 处理管理选项
            if (e.target.value === '__MANAGE_OPTIONS__') {
                e.target.value = row.dataset.fieldValue || '';
                if (typeof SpecOptionsModal !== 'undefined') {
                    // 使用子分类模式打开模态框
                    SpecOptionsModal.open(spec.name, {
                        subcategoryId: self.subcategoryId,
                        fieldId: spec.id,
                        mode: 'subcategory',
                        onOptionAdded: async function(updatedFieldName) {
                            // 重新加载选项
                            await self._reloadCodedSpecOptions(select, spec);
                        }
                    });
                }
                return;
            }

            const selectedOption = select.options[select.selectedIndex];
            const code = selectedOption?.dataset?.code || '';
            row.dataset.fieldValue = select.value;
            row.dataset.fieldCode = code;
            self._trackCodedSpecChange(spec.name, select.value, code, row.dataset.includeInDesc === 'true');
        });

        // 确认按钮 - 确认选择并显示值
        const confirmBtn = row.querySelector('.spec-confirm-btn');
        const valueDisplay = row.querySelector('.value-display');

        const unitDisplay = row.querySelector('.unit-display');
        const unitEdit = row.querySelector('.unit-edit');

        confirmBtn?.addEventListener('click', function() {
            if (select.value && select.value !== '__MANAGE_OPTIONS__') {
                // 显示已选值和单位
                valueDisplay.textContent = select.value;
                valueDisplay.classList.remove('hidden');
                unitDisplay.classList.remove('hidden');
                select.classList.add('hidden');
                unitEdit.classList.add('hidden');

                // 更新按钮状态为已确认
                const icon = this.querySelector('.material-symbols-outlined');
                icon.textContent = 'edit';
                this.classList.remove('text-slate-400', 'hover:text-green-500');
                this.classList.add('text-green-500');
                this.title = self.i18n.edit || '编辑';

                self.updateApplyButtonState();
            }
        });

        // 点击已确认的值可以重新编辑
        valueDisplay?.addEventListener('click', function() {
            if (self.isEditMode) {
                this.classList.add('hidden');
                unitDisplay.classList.add('hidden');
                select.classList.remove('hidden');
                unitEdit.classList.remove('hidden');
                select.focus();
                const icon = confirmBtn.querySelector('.material-symbols-outlined');
                icon.textContent = 'check';
                confirmBtn.classList.remove('text-green-500');
                confirmBtn.classList.add('text-slate-400', 'hover:text-green-500');
            }
        });

        // 可见性切换
        row.querySelector('.spec-visibility-btn')?.addEventListener('click', function() {
            const icon = this.querySelector('.material-symbols-outlined');
            const isVisible = icon.textContent === 'visibility';
            icon.textContent = isVisible ? 'visibility_off' : 'visibility';
            row.dataset.includeInDesc = isVisible ? 'false' : 'true';
            self._trackCodedSpecChange(spec.name, select.value, row.dataset.fieldCode, !isVisible);
        });
    }

    /**
     * 填充编码规格选项（包括管理选项）
     */
    _populateCodedSpecOptions(select, spec) {
        select.innerHTML = '<option value="">-- 请选择 --</option>';

        // 添加已有选项
        (spec.options || []).forEach(o => {
            const opt = document.createElement('option');
            opt.value = o.value;
            opt.textContent = o.value;
            opt.dataset.code = o.code || '';
            select.appendChild(opt);
        });

        // 添加分隔线和管理选项
        const separator = document.createElement('option');
        separator.disabled = true;
        separator.textContent = '──────────';
        select.appendChild(separator);

        const manageOption = document.createElement('option');
        manageOption.value = '__MANAGE_OPTIONS__';
        manageOption.textContent = '+ 管理规格选项';
        select.appendChild(manageOption);
    }

    /**
     * 重新加载编码规格选项
     */
    async _reloadCodedSpecOptions(select, spec) {
        try {
            const response = await fetch(`/product-management/api/subcategory/${this.subcategoryId}/spec-fields`);
            const data = await response.json();
            if (!data.spec_fields) return;

            const updatedSpec = data.spec_fields.find(f => f.name === spec.name);
            if (updatedSpec) {
                const currentValue = select.value;
                this._populateCodedSpecOptions(select, updatedSpec);
                // 尝试恢复之前的选择
                if (currentValue) {
                    select.value = currentValue;
                }
            }
        } catch (e) {
            console.error('重新加载选项失败:', e);
        }
    }

    _trackCodedSpecChange(name, value, code, include) {
        const idx = (this.pendingChanges.added || []).findIndex(i => i.field_name === name);
        const data = { field_name: name, field_value: value, field_code: code, include_in_description: include ?? true };
        if (idx >= 0) this.pendingChanges.added[idx] = data;
        else (this.pendingChanges.added = this.pendingChanges.added || []).push(data);
        this.updateApplyButtonState();
    }

    /**
     * 取消编辑模式
     */
    cancelEditMode() {
        this.isEditMode = false;

        // 恢复原始数据
        this._restoreOriginalState();

        // 移除所有新添加的行
        document.querySelectorAll('.spec-row[data-new="true"]').forEach(row => row.remove());
        document.querySelectorAll('.spec-row-new-input').forEach(row => row.remove());

        // 切换按钮显示
        document.getElementById(this.buttons.edit)?.classList.remove('hidden');
        document.getElementById(this.buttons.apply)?.classList.add('hidden');
        document.getElementById(this.buttons.cancel)?.classList.add('hidden');
        document.getElementById(this.buttons.add)?.classList.add('hidden');

        // 隐藏操作按钮
        document.querySelectorAll('.spec-actions').forEach(el => el.classList.add('hidden'));

        // 隐藏所有编辑选择框
        document.querySelectorAll('.value-select').forEach(el => el.classList.add('hidden'));
        document.querySelectorAll('.unit-edit').forEach(el => el.classList.add('hidden'));
        document.querySelectorAll('.value-display').forEach(el => el.classList.remove('hidden'));
        document.querySelectorAll('.unit-display').forEach(el => el.classList.remove('hidden'));

        // 重置编辑按钮图标
        document.querySelectorAll('.spec-row button[onclick*="toggleSpecEdit"]').forEach(btn => {
            const icon = btn.querySelector('.material-symbols-outlined');
            if (icon) icon.textContent = 'edit';
            btn.classList.remove('text-green-500');
            btn.classList.add('text-slate-400');
        });

        // 检查空状态
        this._checkEmptyState();
    }

    /**
     * 恢复原始状态
     */
    _restoreOriginalState() {
        document.querySelectorAll('.spec-row').forEach(row => {
            const original = this.originalData.find(d => d.id === row.dataset.specId);
            if (original) {
                const select = row.querySelector('.value-select');
                const display = row.querySelector('.value-display');
                if (select) select.value = original.field_value;
                if (display) display.textContent = original.field_value;
                row.dataset.fieldValue = original.field_value;
                row.dataset.fieldCode = original.field_code || '';

                // 恢复描述包含状态
                if (this.features.descriptionControl) {
                    row.dataset.includeInDesc = original.include_in_description ? 'true' : 'false';
                    this._updateDescriptionIcon(row);
                }
            }
        });
    }

    /**
     * 切换单个规格编辑状态
     */
    async toggleSpecEdit(btn) {
        const row = btn.closest('.spec-row');
        const valueDisplay = row.querySelector('.value-display');
        const unitDisplay = row.querySelector('.unit-display');
        const valueSelect = row.querySelector('.value-select');
        const unitEdit = row.querySelector('.unit-edit');
        const icon = btn.querySelector('.material-symbols-outlined');

        if (valueSelect.classList.contains('hidden')) {
            // 进入编辑
            const fieldName = row.dataset.fieldName;
            await this.loadSpecOptions(valueSelect, fieldName, row.dataset.fieldValue);

            valueDisplay.classList.add('hidden');
            if (unitDisplay) unitDisplay.classList.add('hidden');
            valueSelect.classList.remove('hidden');
            if (unitEdit) unitEdit.classList.remove('hidden');
            valueSelect.focus();

            icon.textContent = 'check';
            btn.classList.remove('text-slate-400');
            btn.classList.add('text-green-500');

            this.updateApplyButtonState();
        } else {
            // 保存编辑
            const newValue = valueSelect.value;
            const selectedOption = valueSelect.options[valueSelect.selectedIndex];
            const newCode = selectedOption?.dataset?.code || '';

            if (newValue !== row.dataset.fieldValue) {
                const existingIdx = this.pendingChanges.modified.findIndex(m => m.id === row.dataset.specId);
                if (existingIdx >= 0) {
                    this.pendingChanges.modified[existingIdx].field_value = newValue;
                    this.pendingChanges.modified[existingIdx].field_code = newCode;
                } else {
                    this.pendingChanges.modified.push({
                        id: row.dataset.specId,
                        field_value: newValue,
                        field_code: newCode
                    });
                }
                row.dataset.fieldValue = newValue;
                row.dataset.fieldCode = newCode;
            }

            valueDisplay.textContent = newValue;
            valueDisplay.classList.remove('hidden');
            if (unitDisplay) unitDisplay.classList.remove('hidden');
            valueSelect.classList.add('hidden');
            if (unitEdit) unitEdit.classList.add('hidden');

            icon.textContent = 'edit';
            btn.classList.add('text-slate-400');
            btn.classList.remove('text-green-500');

            this.updateApplyButtonState();
        }
    }

    /**
     * 确认缺失的编码规格选择
     * 用于模板渲染的缺失编码规格行，用户选择值后点击确认
     */
    confirmMissingSpec(btn) {
        const row = btn.closest('.spec-row');
        const select = row.querySelector('.value-select');
        const value = select.value;

        if (!value || value === '__MANAGE_OPTIONS__') {
            alert(this.i18n.selectSpecFirst);
            return;
        }

        // 获取选中的编码
        const selectedOption = select.options[select.selectedIndex];
        const code = selectedOption?.dataset?.code || '';

        // 更新数据属性
        row.dataset.fieldValue = value;
        row.dataset.fieldCode = code;
        row.dataset.isMissing = 'false';

        // 记录为新增规格
        const fieldId = row.dataset.fieldId;
        const fieldName = row.dataset.fieldName;
        this.pendingChanges.added.push({
            field_name: fieldName,
            field_value: value,
            field_code: code,
            field_id: fieldId,
            include_in_description: true
        });

        // 切换到显示模式
        const valueDisplay = row.querySelector('.value-display');
        const unitDisplay = row.querySelector('.unit-display');
        const unitEdit = row.querySelector('.unit-edit');

        valueDisplay.textContent = value;
        valueDisplay.classList.remove('hidden');
        if (unitDisplay) unitDisplay.classList.remove('hidden');

        select.classList.add('hidden');
        if (unitEdit) unitEdit.classList.add('hidden');

        // 隐藏确认按钮
        const confirmBtn = row.querySelector('.spec-confirm-btn');
        if (confirmBtn) confirmBtn.classList.add('hidden');

        // 隐藏操作按钮区域（非编辑模式）
        const actionsDiv = row.querySelector('.spec-actions');
        if (actionsDiv && !this.isEditMode) {
            actionsDiv.classList.add('hidden');
        }

        this.updateApplyButtonState();
    }

    /**
     * 删除规格（统一方法）
     * 自动判断是新添加的规格还是已有的规格，执行相应的删除逻辑
     * @param {HTMLElement} btnOrRow - 触发按钮或规格行元素
     * @param {Object} options - 可选配置
     * @param {boolean} options.showStrikethrough - 是否显示删除线样式（默认false，直接隐藏）
     */
    deleteSpec(btnOrRow, options = {}) {
        // 支持传入按钮或直接传入行
        const row = btnOrRow.classList?.contains('spec-row') ? btnOrRow : btnOrRow.closest('.spec-row');
        if (!row) return;

        const specId = row.dataset.specId;
        const isNewRow = row.dataset.new === 'true' || (specId && specId.startsWith('new_'));

        if (isNewRow) {
            // 新添加的规格：从 pendingChanges.added 中移除
            const idx = this.pendingChanges.added.findIndex(a => a.tempId === specId);
            if (idx >= 0) {
                this.pendingChanges.added.splice(idx, 1);
            }
            row.remove();
            this._checkEmptyState();
        } else if (specId) {
            // 已有的规格：标记为待删除
            this._executeDelete(row, specId, options);
        } else {
            // 没有任何ID的行，直接移除
            row.remove();
            this._checkEmptyState();
        }

        this.updateApplyButtonState();
    }

    /**
     * 执行删除逻辑（供外部确认后调用）
     */
    _executeDelete(row, specId, options = {}) {
        // 标记为待删除
        if (!this.pendingChanges.deleted.includes(specId)) {
            this.pendingChanges.deleted.push(specId);
        }
        row.dataset.deleted = 'true';

        if (options.showStrikethrough) {
            // 显示删除线样式
            row.classList.add('deleted', 'opacity-50');
            row.querySelector('.value-display')?.classList.add('line-through');
        } else {
            // 直接隐藏
            row.style.display = 'none';
        }
    }

    /**
     * 删除新添加的规格（别名，保持向后兼容）
     * @deprecated 请使用 deleteSpec 方法
     */
    deleteNewSpec(row) {
        this.deleteSpec(row);
    }

    // ==================== 模态框公共方法 ====================

    /**
     * 关闭规格预览模态框
     */
    closePreviewModal() {
        const modal = document.getElementById(this.modals.preview);
        if (modal) modal.classList.add('hidden');
    }

    /**
     * 确认规格预览并执行保存
     */
    confirmPreview() {
        this.closePreviewModal();
        if (this._previewConfirmCallback) {
            this._previewConfirmCallback();
            this._previewConfirmCallback = null;
        }
    }

    /**
     * 关闭编码冲突模态框
     */
    closeConflictModal() {
        const modal = document.getElementById(this.modals.conflict);
        if (modal) modal.classList.add('hidden');
    }

    /**
     * 设置预览确认回调
     * @param {Function} callback - 确认后执行的回调函数
     */
    setPreviewConfirmCallback(callback) {
        this._previewConfirmCallback = callback;
    }

    /**
     * 显示规格MN预览模态框
     * @param {Object} previewData - 预览数据
     * @param {Function} confirmCallback - 确认回调
     */
    showPreviewModal(previewData, confirmCallback) {
        document.getElementById('previewProductMnBefore').textContent = previewData.current_product_mn || '-';
        document.getElementById('previewSpecMnBefore').textContent = previewData.current_spec_mn || '-';

        const productMnAfter = document.getElementById('previewProductMnAfter');
        const specMnAfter = document.getElementById('previewSpecMnAfter');

        // 产品MN：锁定时不更新（研发库没有此字段，走else分支）
        if (previewData.is_mn_locked) {
            productMnAfter.textContent = previewData.current_product_mn || '-';
            productMnAfter.className = 'font-mono text-sm text-slate-700 dark:text-slate-300';
            document.getElementById('previewProductMnResult').innerHTML = '<span class="material-symbols-outlined text-slate-400 text-xl" title="不更新">block</span>';
        } else {
            productMnAfter.textContent = previewData.new_spec_mn || '-';
            productMnAfter.className = 'font-mono text-sm text-slate-900 dark:text-white font-medium';
            document.getElementById('previewProductMnResult').innerHTML = '<span class="material-symbols-outlined text-emerald-500 text-xl" title="将更新">check_circle</span>';
        }

        // 规格MN：总是更新
        specMnAfter.textContent = previewData.new_spec_mn || '-';
        specMnAfter.className = 'font-mono text-sm text-slate-900 dark:text-white font-medium';
        document.getElementById('previewSpecMnResult').innerHTML = '<span class="material-symbols-outlined text-emerald-500 text-xl" title="将更新">check_circle</span>';

        this.setPreviewConfirmCallback(confirmCallback);
        document.getElementById(this.modals.preview).classList.remove('hidden');
    }

    /**
     * 显示编码冲突模态框
     * @param {Object} result - 冲突结果
     * @param {Object} currentProduct - 当前产品信息 {name, model, code}
     */
    showConflictModal(result, currentProduct = {}) {
        const newCode = result.new_spec_mn;
        const conflictProduct = result.conflict_product;
        const currentSpecs = result.current_specs;

        // 格式化规格列表为HTML
        function formatSpecs(specsList) {
            if (!specsList || specsList.length === 0) return '<span class="text-slate-400">-</span>';
            return specsList.map(s => `<div>${s.name}: ${s.value}</div>`).join('');
        }

        // 当前产品信息
        document.getElementById('conflictCurrentName').textContent = currentProduct.name || '-';
        document.getElementById('conflictCurrentModel').textContent = currentProduct.model || '-';
        document.getElementById('conflictCurrentCode').textContent = currentProduct.code || '-';
        document.getElementById('conflictNewCode').textContent = newCode || '-';
        document.getElementById('conflictCurrentSpecs').innerHTML = formatSpecs(currentSpecs);

        // 冲突产品信息
        document.getElementById('conflictProductName').textContent = conflictProduct.product_name || '-';
        document.getElementById('conflictProductModel').textContent = conflictProduct.model || '-';
        document.getElementById('conflictProductMn').textContent = conflictProduct.product_mn || '-';
        document.getElementById('conflictSpecMn').textContent = conflictProduct.spec_mn || '-';
        document.getElementById('conflictProductSpecs').innerHTML = formatSpecs(conflictProduct.specs);
        document.getElementById('conflictProductSource').textContent = conflictProduct.source || '';

        document.getElementById(this.modals.conflict).classList.remove('hidden');
    }

    /**
     * 切换规格是否包含在描述中（产品库用）
     */
    toggleSpecInDescription(btn) {
        if (!this.features.descriptionControl) return;

        const row = btn.closest('.spec-row');
        const includeInDesc = row.dataset.includeInDesc === 'true';
        row.dataset.includeInDesc = includeInDesc ? 'false' : 'true';

        const specId = row.dataset.specId;

        // 记录变更
        const existingIdx = this.pendingChanges.descriptionChanged.findIndex(c => c.id === specId);
        if (existingIdx >= 0) {
            this.pendingChanges.descriptionChanged[existingIdx].include_in_description = row.dataset.includeInDesc === 'true';
        } else {
            this.pendingChanges.descriptionChanged.push({
                id: specId,
                include_in_description: row.dataset.includeInDesc === 'true'
            });
        }

        this._updateDescriptionIcon(row);
    }

    /**
     * 更新描述包含图标
     */
    _updateDescriptionIcon(row) {
        const btn = row.querySelector('[onclick*="toggleSpecInDescription"], .toggle-desc-btn');
        if (!btn) return;

        const icon = btn.querySelector('.material-symbols-outlined');
        const includeInDesc = row.dataset.includeInDesc === 'true';

        if (icon) {
            icon.textContent = includeInDesc ? 'visibility' : 'visibility_off';
        }
        btn.title = includeInDesc ? this.i18n.excludeFromDesc : this.i18n.includeInDesc;
    }

    /**
     * 加载规格选项
     * 优先使用子分类过滤的API，获取继承关系下的正确选项
     */
    async loadSpecOptions(selectElement, fieldName, currentValue) {
        // 缓存键：如果有subcategoryId，按子分类缓存；否则按规格名称全局缓存
        const cacheKey = this.subcategoryId ? `${this.subcategoryId}_${fieldName}` : fieldName;

        if (!this.specOptionsCache[cacheKey]) {
            try {
                // 优先使用子分类过滤的API
                if (this.subcategoryId) {
                    const response = await fetch(`/product-management/api/spec-field-options?subcategory_id=${this.subcategoryId}&spec_name=${encodeURIComponent(fieldName)}`);
                    const result = await response.json();
                    if (result.options && result.options.length > 0) {
                        this.specOptionsCache[cacheKey] = result.options;
                    }
                }

                // 如果没有子分类或获取失败，回退到全局规格字典
                if (!this.specOptionsCache[cacheKey]) {
                    const specsResponse = await fetch('/api/spec-dictionary');
                    const specsResult = await specsResponse.json();
                    if (specsResult.success) {
                        const spec = specsResult.data.find(s => s.name === fieldName);
                        if (spec) {
                            const optionsResponse = await fetch(`/api/spec-dictionary/${spec.id}/options`);
                            const optionsResult = await optionsResponse.json();
                            if (optionsResult.success) {
                                this.specOptionsCache[cacheKey] = optionsResult.data;
                            }
                        }
                    }
                }
            } catch (error) {
                console.error('加载规格选项失败:', error);
            }
        }

        const options = this.specOptionsCache[cacheKey] || [];
        selectElement.innerHTML = '';

        if (options.length > 0) {
            options.forEach(opt => {
                const option = document.createElement('option');
                option.value = opt.value;
                option.textContent = opt.value;
                option.dataset.code = opt.code || '';  // 存储规格编码
                if (opt.value === currentValue) {
                    option.selected = true;
                }
                selectElement.appendChild(option);
            });
        } else {
            const option = document.createElement('option');
            option.value = currentValue;
            option.textContent = currentValue;
            option.dataset.code = '';
            option.selected = true;
            selectElement.appendChild(option);
        }

        // 添加管理选项
        const separator = document.createElement('option');
        separator.disabled = true;
        separator.textContent = '──────────';
        selectElement.appendChild(separator);

        const manageOption = document.createElement('option');
        manageOption.value = '__MANAGE_OPTIONS__';
        manageOption.textContent = '+ 管理规格选项';
        manageOption.className = 'text-primary font-medium';
        selectElement.appendChild(manageOption);

        // 监听管理选项
        if (!selectElement.dataset.manageListenerAdded) {
            selectElement.dataset.manageListenerAdded = 'true';
            selectElement.dataset.fieldName = fieldName;
            const self = this;

            selectElement.addEventListener('change', function(e) {
                if (e.target.value === '__MANAGE_OPTIONS__') {
                    const row = e.target.closest('.spec-row');
                    const curValue = row ? row.dataset.fieldValue : currentValue;
                    const fieldId = row ? row.dataset.fieldId : null;
                    e.target.value = curValue;

                    if (typeof SpecOptionsModal !== 'undefined') {
                        const specName = e.target.dataset.fieldName;
                        // 如果有子分类ID和字段ID，使用子分类模式
                        if (self.subcategoryId && fieldId) {
                            SpecOptionsModal.open(specName, {
                                subcategoryId: self.subcategoryId,
                                fieldId: fieldId,
                                mode: 'subcategory',
                                onOptionAdded: async function(updatedFieldName) {
                                    delete self.specOptionsCache[updatedFieldName];
                                    if (updatedFieldName === specName) {
                                        await self.loadSpecOptions(e.target, updatedFieldName, curValue);
                                    }
                                }
                            });
                        } else {
                            // 全局模式
                            SpecOptionsModal.open(specName, async function(updatedFieldName) {
                                delete self.specOptionsCache[updatedFieldName];
                                if (updatedFieldName === specName) {
                                    await self.loadSpecOptions(e.target, updatedFieldName, curValue);
                                }
                            });
                        }
                    }
                }
            });
        }
    }

    /**
     * 添加新规格行
     */
    async addNewSpecRow() {
        let specsList = document.getElementById(this.listId);
        if (!specsList) {
            const container = document.getElementById(this.containerId);
            const emptyMsg = document.getElementById(this.emptyMessageId);
            if (emptyMsg) emptyMsg.remove();

            specsList = document.createElement('dl');
            specsList.id = this.listId;
            container.appendChild(specsList);
        }

        // 检查已有未完成行
        const existingNewRow = specsList.querySelector('.spec-row-new-input');
        if (existingNewRow) {
            existingNewRow.querySelector('.new-spec-name')?.focus();
            return;
        }

        // 获取已使用规格
        const usedNames = new Set();
        document.querySelectorAll('.spec-row:not(.deleted)').forEach(row => {
            usedNames.add(row.dataset.fieldName);
        });

        // 加载可用规格
        // 如果配置了subcategoryId，则只加载该子分类的非编码规格
        // 否则加载所有规格字典
        let availableSpecsData = [];
        try {
            let apiUrl = '/api/spec-dictionary';
            if (this.subcategoryId) {
                apiUrl = `/api/spec-dictionary/available-for-subcategory/${this.subcategoryId}`;
            }
            const response = await fetch(apiUrl);
            const result = await response.json();
            if (result.success) {
                availableSpecsData = result.data.filter(spec => !usedNames.has(spec.name));
            }
        } catch (error) {
            console.error('加载可用规格失败:', error);
        }

        if (availableSpecsData.length === 0) {
            alert(this.i18n.noAvailableSpecs);
            return;
        }

        // 创建新行
        const tempId = 'new_' + Date.now();
        const newRow = document.createElement('div');
        newRow.className = 'spec-row spec-row-new-input px-6 py-4 flex items-center justify-between transition-colors border-t border-slate-100 dark:border-slate-800';
        newRow.dataset.specId = tempId;
        newRow.dataset.new = 'true';

        let specOptionsHtml = `<option value="">${this.i18n.selectSpec}</option>`;
        availableSpecsData.forEach(spec => {
            specOptionsHtml += `<option value="${spec.id}" data-name="${spec.name}" data-unit="${spec.unit || ''}">${spec.name}${spec.unit ? ' (' + spec.unit + ')' : ''}</option>`;
        });

        newRow.innerHTML = `
            <div class="flex-1 grid grid-cols-3 gap-4">
                <dt class="text-sm font-medium text-slate-500 dark:text-slate-400">
                    <select class="new-spec-name w-full px-2 py-1 text-sm border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-200">
                        ${specOptionsHtml}
                    </select>
                </dt>
                <dd class="spec-value text-sm text-slate-900 dark:text-slate-200 col-span-2 mt-0 flex items-center gap-2">
                    <select class="new-spec-value w-32 px-2 py-1 text-sm border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-200" disabled>
                        <option value="">${this.i18n.selectSpecFirst}</option>
                    </select>
                    <span class="new-spec-unit text-slate-400"></span>
                </dd>
            </div>
            <div class="spec-actions flex items-center gap-1 ml-4">
                <button type="button" class="confirm-new-spec p-1.5 text-slate-400 hover:text-green-500 rounded hover:bg-slate-100 dark:hover:bg-slate-700" title="${this.i18n.apply}">
                    <span class="material-symbols-outlined text-lg">check</span>
                </button>
                <button type="button" class="cancel-new-spec p-1.5 text-slate-400 hover:text-red-500 rounded hover:bg-slate-100 dark:hover:bg-slate-700" title="${this.i18n.cancel}">
                    <span class="material-symbols-outlined text-lg">close</span>
                </button>
            </div>
        `;

        specsList.appendChild(newRow);
        this.updateApplyButtonState();

        // 绑定事件
        const nameSelect = newRow.querySelector('.new-spec-name');
        const valueSelect = newRow.querySelector('.new-spec-value');
        const unitSpan = newRow.querySelector('.new-spec-unit');
        const self = this;

        nameSelect.addEventListener('change', async function() {
            const selectedOption = this.options[this.selectedIndex];
            const specId = this.value;

            if (!specId) {
                valueSelect.innerHTML = `<option value="">${self.i18n.selectSpecFirst}</option>`;
                valueSelect.disabled = true;
                unitSpan.textContent = '';
                return;
            }

            unitSpan.textContent = selectedOption.dataset.unit || '';
            valueSelect.innerHTML = `<option value="">${self.i18n.loading}</option>`;
            valueSelect.disabled = true;

            try {
                const specName = selectedOption.dataset.name;
                // 缓存键：如果有subcategoryId，按子分类缓存
                const cacheKey = self.subcategoryId ? `${self.subcategoryId}_${specName}` : specId;

                if (!self.specOptionsCache[cacheKey]) {
                    // 优先使用子分类过滤的API
                    if (self.subcategoryId && specName) {
                        const response = await fetch(`/product-management/api/spec-field-options?subcategory_id=${self.subcategoryId}&spec_name=${encodeURIComponent(specName)}`);
                        const result = await response.json();
                        if (result.options && result.options.length > 0) {
                            self.specOptionsCache[cacheKey] = result.options;
                        }
                    }

                    // 如果没有子分类或获取失败，回退到全局规格字典
                    if (!self.specOptionsCache[cacheKey]) {
                        const response = await fetch(`/api/spec-dictionary/${specId}/options`);
                        const result = await response.json();
                        if (result.success) {
                            self.specOptionsCache[cacheKey] = result.data;
                        }
                    }
                }

                const options = self.specOptionsCache[cacheKey] || [];
                valueSelect.innerHTML = '';

                if (options.length === 0) {
                    // 即使没有选项，也添加一个占位符
                    const emptyOpt = document.createElement('option');
                    emptyOpt.value = '';
                    emptyOpt.textContent = self.i18n.noAvailableOptions;
                    valueSelect.appendChild(emptyOpt);
                } else {
                    options.forEach(opt => {
                        const option = document.createElement('option');
                        option.value = opt.value;
                        option.textContent = opt.value;
                        option.dataset.code = opt.code || '';
                        valueSelect.appendChild(option);
                    });
                }

                // 添加管理规格选项
                const separator = document.createElement('option');
                separator.disabled = true;
                separator.textContent = '──────────';
                valueSelect.appendChild(separator);

                const manageOption = document.createElement('option');
                manageOption.value = '__MANAGE_OPTIONS__';
                manageOption.textContent = '+ 管理规格选项';
                manageOption.className = 'text-primary font-medium';
                valueSelect.appendChild(manageOption);

                // 启用下拉框（无论是否有选项，都需要能选择"管理规格选项"）
                valueSelect.disabled = false;

                // 绑定管理选项事件
                if (!valueSelect.dataset.manageListenerAdded) {
                    valueSelect.dataset.manageListenerAdded = 'true';
                    valueSelect.dataset.specId = specId;
                    valueSelect.dataset.specName = selectedOption.dataset.name;

                    valueSelect.addEventListener('change', function(e) {
                        if (e.target.value === '__MANAGE_OPTIONS__') {
                            // 恢复之前的选择
                            const firstOpt = e.target.querySelector('option:not([disabled])');
                            if (firstOpt) e.target.value = firstOpt.value;

                            if (typeof SpecOptionsModal !== 'undefined') {
                                const specName = e.target.dataset.specName;
                                const specIdForRefresh = e.target.dataset.specId;
                                SpecOptionsModal.open(specName, async function(updatedFieldName) {
                                    // 刷新选项缓存 - 使用正确的缓存键格式
                                    const cacheKeyToDelete = self.subcategoryId ? `${self.subcategoryId}_${specName}` : specIdForRefresh;
                                    delete self.specOptionsCache[cacheKeyToDelete];
                                    // 重新触发规格选择以刷新选项
                                    nameSelect.dispatchEvent(new Event('change'));
                                });
                            }
                        }
                    });
                }
            } catch (error) {
                console.error('加载指标选项失败:', error);
                valueSelect.innerHTML = '';

                const emptyOpt = document.createElement('option');
                emptyOpt.value = '';
                emptyOpt.textContent = self.i18n.noAvailableOptions;
                valueSelect.appendChild(emptyOpt);

                // 即使出错也添加管理规格选项
                const separator = document.createElement('option');
                separator.disabled = true;
                separator.textContent = '──────────';
                valueSelect.appendChild(separator);

                const manageOption = document.createElement('option');
                manageOption.value = '__MANAGE_OPTIONS__';
                manageOption.textContent = '+ 管理规格选项';
                manageOption.className = 'text-primary font-medium';
                valueSelect.appendChild(manageOption);

                valueSelect.disabled = false;

                // 绑定管理选项事件
                if (!valueSelect.dataset.manageListenerAdded) {
                    valueSelect.dataset.manageListenerAdded = 'true';
                    valueSelect.dataset.specId = specId;
                    valueSelect.dataset.specName = selectedOption.dataset.name;

                    valueSelect.addEventListener('change', function(e) {
                        if (e.target.value === '__MANAGE_OPTIONS__') {
                            const firstOpt = e.target.querySelector('option:not([disabled])');
                            if (firstOpt) e.target.value = firstOpt.value;

                            if (typeof SpecOptionsModal !== 'undefined') {
                                const specName = e.target.dataset.specName;
                                const specIdForRefresh = e.target.dataset.specId;
                                SpecOptionsModal.open(specName, async function() {
                                    // 刷新选项缓存 - 使用正确的缓存键格式
                                    const cacheKeyToDelete = self.subcategoryId ? `${self.subcategoryId}_${specName}` : specIdForRefresh;
                                    delete self.specOptionsCache[cacheKeyToDelete];
                                    nameSelect.dispatchEvent(new Event('change'));
                                });
                            }
                        }
                    });
                }
            }
        });

        // 确认按钮
        newRow.querySelector('.confirm-new-spec').addEventListener('click', () => {
            this.confirmNewSpecRow(newRow);
        });

        // 取消按钮
        newRow.querySelector('.cancel-new-spec').addEventListener('click', () => {
            this.cancelNewSpecRow(newRow);
        });

        nameSelect.focus();
    }

    /**
     * 确认新规格行
     */
    confirmNewSpecRow(row) {
        const nameSelect = row.querySelector('.new-spec-name');
        const valueSelect = row.querySelector('.new-spec-value');
        const unitSpan = row.querySelector('.new-spec-unit');

        const selectedNameOption = nameSelect.options[nameSelect.selectedIndex];
        const selectedValue = valueSelect.value;

        if (!nameSelect.value || !selectedValue) {
            nameSelect.focus();
            return;
        }

        const specName = selectedNameOption.dataset.name;
        const specUnit = selectedNameOption.dataset.unit || '';

        row.dataset.fieldName = specName;
        row.dataset.fieldValue = selectedValue;
        row.dataset.unit = specUnit;
        row.classList.remove('spec-row-new-input');

        this.pendingChanges.added.push({
            tempId: row.dataset.specId,
            field_name: specName,
            field_value: selectedValue,
            unit: specUnit
        });

        const self = this;
        row.innerHTML = `
            <div class="flex-1 grid grid-cols-3 gap-4">
                <dt class="text-sm font-medium text-slate-500 dark:text-slate-400 spec-name">${specName}</dt>
                <dd class="spec-value text-sm text-slate-900 dark:text-slate-200 col-span-2 mt-0 flex items-center gap-2">
                    <span class="value-display">${selectedValue}</span>
                    <span class="unit-display text-slate-400">${specUnit}</span>
                    <select class="value-select hidden w-32 px-2 py-1 text-sm border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-200">
                        <option value="${selectedValue}">${selectedValue}</option>
                    </select>
                    <span class="unit-edit hidden text-slate-400">${specUnit}</span>
                </dd>
            </div>
            <div class="spec-actions flex items-center gap-1 ml-4">
                <button type="button" class="edit-spec p-1.5 text-slate-400 hover:text-primary rounded hover:bg-slate-100 dark:hover:bg-slate-700" title="${this.i18n.edit}">
                    <span class="material-symbols-outlined text-lg">edit</span>
                </button>
                <button type="button" class="delete-new-spec p-1.5 text-slate-400 hover:text-red-500 rounded hover:bg-slate-100 dark:hover:bg-slate-700" title="${this.i18n.delete}">
                    <span class="material-symbols-outlined text-lg">delete</span>
                </button>
            </div>
        `;

        // 绑定编辑按钮
        row.querySelector('.edit-spec').addEventListener('click', function() {
            self.toggleSpecEdit(this);
        });

        // 绑定删除按钮
        row.querySelector('.delete-new-spec').addEventListener('click', function() {
            self.deleteNewSpec(row);
        });

        this.updateApplyButtonState();
    }

    /**
     * 取消新规格行
     */
    cancelNewSpecRow(row) {
        row.remove();
        this.updateApplyButtonState();
        this._checkEmptyState();
    }

    /**
     * 检查空状态
     */
    _checkEmptyState() {
        const specsList = document.getElementById(this.listId);
        if (specsList && specsList.querySelectorAll('.spec-row').length === 0) {
            const container = document.getElementById(this.containerId);
            specsList.remove();
            if (!document.getElementById(this.emptyMessageId)) {
                const emptyDiv = document.createElement('div');
                emptyDiv.id = this.emptyMessageId;
                emptyDiv.className = 'px-6 py-8 text-center text-sm text-slate-500 dark:text-slate-400';
                emptyDiv.innerHTML = `<span class="material-symbols-outlined text-4xl text-slate-300 dark:text-slate-600 mb-2 block">list</span>${this.i18n.emptySpecs}`;
                container.appendChild(emptyDiv);
            }
        }
    }

    /**
     * 应用更改
     */
    async applyChanges() {
        const applyBtn = document.getElementById(this.buttons.apply);
        if (applyBtn && applyBtn.disabled) {
            return;
        }

        // 检查未完成行
        const unfinishedRow = document.querySelector('.spec-row-new-input');
        if (unfinishedRow) {
            unfinishedRow.querySelector('.new-spec-name')?.focus();
            return;
        }

        // 检查是否有预加载的新规格被填充了值
        let hasNewSpecsWithValue = false;
        document.querySelectorAll('.spec-row[data-new="true"]').forEach(row => {
            if (row.dataset.fieldValue && row.dataset.fieldValue.trim() !== '') {
                hasNewSpecsWithValue = true;
            }
        });

        const hasChanges = this.pendingChanges.modified.length > 0 ||
                          this.pendingChanges.added.length > 0 ||
                          this.pendingChanges.deleted.length > 0 ||
                          this.pendingChanges.descriptionChanged.length > 0 ||
                          hasNewSpecsWithValue;

        if (!hasChanges) {
            this.cancelEditMode();
            return;
        }

        // 收集规格数据
        const specs = this._collectSpecsData();

        // 如果启用了编码预览功能
        if (this.features.codePreview && this.previewEndpoint) {
            await this._previewAndSave(specs);
        } else {
            await this._saveChanges(specs);
        }
    }

    /**
     * 收集规格数据
     */
    _collectSpecsData() {
        const specs = [];
        document.querySelectorAll('.spec-row:not(.deleted):not(.spec-row-new-input)').forEach(row => {
            const select = row.querySelector('.value-select');
            let fieldValue = row.dataset.fieldValue;
            let fieldCode = row.dataset.fieldCode || null;

            if (select && !select.classList.contains('hidden')) {
                fieldValue = select.value;
                const selectedOption = select.options[select.selectedIndex];
                fieldCode = selectedOption?.dataset?.code || null;
            }

            const specId = row.dataset.specId;
            const isNew = specId && specId.startsWith('new_');

            const specData = {
                id: isNew ? null : parseInt(specId),
                field_name: row.dataset.fieldName,
                field_value: fieldValue,
                field_code: fieldCode,
                is_new: isNew
            };

            // 如果启用描述控制，添加 include_in_description
            if (this.features.descriptionControl) {
                specData.include_in_description = row.dataset.includeInDesc === 'true';
            }

            specs.push(specData);
        });
        return specs;
    }

    /**
     * 预览并保存（产品库用）
     */
    async _previewAndSave(specs) {
        try {
            // 调用预览API
            const response = await fetch(this.previewEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ specs: specs })
            });

            const result = await response.json();

            if (!result.success) {
                alert(result.message || this.i18n.saveError);
                return;
            }

            // 检查是否有缺少编码的规格
            if (result.missing_codes && result.missing_codes.length > 0) {
                const missingList = result.missing_codes.join('、');
                alert(this.i18n.missingCodes + missingList);
                return;
            }

            // 检查是否有编码冲突
            if (result.conflict_product && this.onShowConflict) {
                this.onShowConflict(result);
                return;
            }

            // 检查是否有编码变化
            const hasCodeChange = result.new_spec_mn && result.new_spec_mn !== result.current_spec_mn;

            if (hasCodeChange && this.onShowPreview) {
                // 有编码变化，显示预览模态框
                const self = this;
                this.onShowPreview(result, function() {
                    self._saveChanges(specs);
                });
            } else {
                // 无编码变化，直接保存
                await this._saveChanges(specs);
            }
        } catch (error) {
            console.error('预览规格失败:', error);
            alert(this.i18n.saveError);
        }
    }

    /**
     * 保存规格更改
     */
    async _saveChanges(specs) {
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    specs: specs,
                    deleted: this.pendingChanges.deleted
                })
            });

            const result = await response.json();

            if (result.success) {
                this._exitEditMode();

                // 如果提供了局部刷新回调，使用它；否则调用 onSaveSuccess
                if (this.onPartialRefresh) {
                    this.onPartialRefresh(result);
                } else {
                    this.onSaveSuccess(result);
                }
            } else {
                alert(result.message || this.i18n.saveError);
            }
        } catch (error) {
            console.error('保存规格失败:', error);
            alert(this.i18n.saveError);
        }
    }

    /**
     * 退出编辑模式（不还原数据）
     */
    _exitEditMode() {
        this.isEditMode = false;
        this.pendingChanges = { modified: [], added: [], deleted: [], descriptionChanged: [] };

        document.getElementById(this.buttons.edit)?.classList.remove('hidden');
        document.getElementById(this.buttons.apply)?.classList.add('hidden');
        document.getElementById(this.buttons.cancel)?.classList.add('hidden');
        document.getElementById(this.buttons.add)?.classList.add('hidden');

        document.querySelectorAll('.spec-actions').forEach(el => el.classList.add('hidden'));

        // 隐藏编辑控件
        document.querySelectorAll('.value-select').forEach(el => el.classList.add('hidden'));
        document.querySelectorAll('.unit-edit').forEach(el => el.classList.add('hidden'));
        document.querySelectorAll('.value-display').forEach(el => el.classList.remove('hidden'));
        document.querySelectorAll('.unit-display').forEach(el => el.classList.remove('hidden'));

        // 重置编辑按钮图标
        document.querySelectorAll('.spec-row button[onclick*="toggleSpecEdit"], .spec-row .edit-spec').forEach(btn => {
            const icon = btn.querySelector('.material-symbols-outlined');
            if (icon) icon.textContent = 'edit';
            btn.classList.add('text-slate-400');
            btn.classList.remove('text-green-500');
        });
    }

    /**
     * 清除选项缓存
     */
    clearCache(fieldName) {
        if (fieldName) {
            delete this.specOptionsCache[fieldName];
        } else {
            this.specOptionsCache = {};
        }
    }

    /**
     * 重建规格列表（用于局部刷新）
     * @param {Array} specs - 规格数据数组
     * @param {Object} options - 可选配置
     * @param {string} options.rowClass - 行的额外 CSS 类
     */
    rebuildSpecsList(specs, options = {}) {
        const specsList = document.getElementById(this.listId);
        if (!specsList) return;

        // 清空现有内容
        specsList.innerHTML = '';

        // 默认添加边框样式
        const defaultRowClass = 'border-t border-slate-100 dark:border-slate-800 first:border-t-0';

        // 重建每一行
        specs.forEach(spec => {
            const row = document.createElement('div');
            row.className = 'spec-row px-6 py-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors ' + defaultRowClass + (options.rowClass ? ' ' + options.rowClass : '');
            row.dataset.specId = spec.id;
            row.dataset.fieldName = spec.field_name;
            row.dataset.fieldId = spec.field_id || '';  // 字段ID
            row.dataset.fieldValue = spec.field_value;
            row.dataset.fieldCode = spec.field_code || '';
            row.dataset.unit = spec.unit || '';
            row.dataset.includeInDesc = spec.include_in_description ? 'true' : 'false';

            const hasCode = !!spec.field_code;
            const visibilityIcon = spec.include_in_description ? 'visibility' : 'visibility_off';
            const visibilityTitle = spec.include_in_description ? this.i18n.excludeFromDesc : this.i18n.includeInDesc;

            row.innerHTML = `
                <div class="flex-1 grid grid-cols-3 gap-4">
                    <dt class="text-sm font-medium text-slate-500 dark:text-slate-400 spec-name">${spec.field_name}</dt>
                    <dd class="spec-value text-sm text-slate-900 dark:text-slate-200 col-span-2 mt-0 flex items-center gap-2">
                        <span class="value-display">${spec.field_value}</span>
                        <span class="unit-display text-slate-400">${spec.unit || ''}</span>
                        <select class="value-select hidden w-32 px-2 py-1 text-sm border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-200">
                            <option value="${spec.field_value}">${spec.field_value}</option>
                        </select>
                        <span class="unit-edit hidden text-slate-400">${spec.unit || ''}</span>
                    </dd>
                </div>
                <div class="spec-actions hidden flex items-center gap-1 ml-4">
                    <button type="button" onclick="toggleSpecEdit(this)" class="p-1.5 text-slate-400 hover:text-primary rounded hover:bg-slate-100 dark:hover:bg-slate-700" title="${this.i18n.edit}">
                        <span class="material-symbols-outlined text-lg">edit</span>
                    </button>
                    ${!hasCode ? `<button type="button" onclick="deleteSpec(this)" class="p-1.5 text-slate-400 hover:text-red-500 rounded hover:bg-slate-100 dark:hover:bg-slate-700" title="${this.i18n.delete}">
                        <span class="material-symbols-outlined text-lg">delete</span>
                    </button>` : ''}
                    <button type="button" onclick="toggleSpecInDescription(this)" class="p-1.5 text-slate-400 hover:text-amber-500 rounded hover:bg-slate-100 dark:hover:bg-slate-700" title="${visibilityTitle}">
                        <span class="material-symbols-outlined text-lg">${visibilityIcon}</span>
                    </button>
                </div>
            `;

            specsList.appendChild(row);
        });
    }
}

// 导出到全局
window.SpecEditor = SpecEditor;
