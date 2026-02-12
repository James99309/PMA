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

        // 引入产品标记（引入产品的编码规格不可编辑）
        this.isImportedProduct = false;
    }

    /**
     * 设置是否是引入产品
     * 引入产品的编码规格在编辑模式下会灰显不可编辑
     */
    setImportedProduct(isImported) {
        this.isImportedProduct = isImported;
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

            const response = await fetch(`/product-code/api/subcategory/${this.subcategoryId}/spec-fields`);
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

            // 添加分隔线和管理选项（仅在 SpecOptionsModal 可用时）
            if (typeof SpecOptionsModal !== 'undefined') {
                const separator = document.createElement('option');
                separator.disabled = true;
                separator.textContent = '──────────';
                select.appendChild(separator);

                const manageOption = document.createElement('option');
                manageOption.value = '__MANAGE_OPTIONS__';
                manageOption.textContent = '+ 管理规格选项';
                select.appendChild(manageOption);
            }

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

        // 显示操作按钮和拖拽手柄
        document.querySelectorAll('.spec-actions').forEach(el => el.classList.remove('hidden'));
        document.querySelectorAll('.spec-drag-handle').forEach(el => el.classList.remove('hidden'));

        // 初始化拖拽排序
        this._initDragAndDrop();

        // 更新应用按钮状态
        this.updateApplyButtonState();

        // 如果是引入产品，应用编辑限制
        if (this.isImportedProduct) {
            this._applyImportedProductRestrictions();
        }
    }

    /**
     * 加载缺失的编码规格（use_in_code=true，包含继承）
     */
    async _loadMissingCodedSpecs() {
        try {
            const response = await fetch(`/product-code/api/subcategory/${this.subcategoryId}/spec-fields`);
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
            <span class="spec-drag-handle cursor-grab active:cursor-grabbing text-slate-300 hover:text-slate-500 mr-1 shrink-0">
                <span class="material-symbols-outlined text-lg">drag_indicator</span>
            </span>
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

        // 添加分隔线和管理选项（仅在 SpecOptionsModal 可用时）
        if (typeof SpecOptionsModal !== 'undefined') {
            const separator = document.createElement('option');
            separator.disabled = true;
            separator.textContent = '──────────';
            select.appendChild(separator);

            const manageOption = document.createElement('option');
            manageOption.value = '__MANAGE_OPTIONS__';
            manageOption.textContent = '+ 管理规格选项';
            select.appendChild(manageOption);
        }
    }

    /**
     * 重新加载编码规格选项
     */
    async _reloadCodedSpecOptions(select, spec) {
        try {
            const response = await fetch(`/product-code/api/subcategory/${this.subcategoryId}/spec-fields`);
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

        // 清理引入产品限制状态
        if (this.isImportedProduct) {
            this._clearImportedProductRestrictions();
        }

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

        // 隐藏操作按钮和拖拽手柄
        document.querySelectorAll('.spec-actions').forEach(el => el.classList.add('hidden'));
        document.querySelectorAll('.spec-drag-handle').forEach(el => el.classList.add('hidden'));

        // 销毁拖拽排序
        this._destroyDragAndDrop();

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
     * 直接从规格字典获取（唯一真实来源）
     */
    async loadSpecOptions(selectElement, fieldName, currentValue) {
        const cacheKey = fieldName;

        if (!this.specOptionsCache[cacheKey]) {
            try {
                const response = await fetch(
                    `/api/spec-dictionary/options/by-name/${encodeURIComponent(fieldName)}?active_only=true`
                );
                const result = await response.json();
                if (result.success && result.data && result.data.length > 0) {
                    this.specOptionsCache[cacheKey] = result.data;
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

        // 添加管理选项（仅在 SpecOptionsModal 可用时）
        if (typeof SpecOptionsModal !== 'undefined') {
            const separator = document.createElement('option');
            separator.disabled = true;
            separator.textContent = '──────────';
            selectElement.appendChild(separator);

            const manageOption = document.createElement('option');
            manageOption.value = '__MANAGE_OPTIONS__';
            manageOption.textContent = '+ 管理规格选项';
            manageOption.className = 'text-primary font-medium';
            selectElement.appendChild(manageOption);
        }

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
     * 添加新规格行 - 打开分类树形多选模态框
     */
    async addNewSpecRow() {
        this._showAddSpecModal();
    }

    /**
     * 显示添加规格的树形多选模态框
     */
    async _showAddSpecModal() {
        // 收集已有规格名
        const usedNames = new Set();
        document.querySelectorAll('.spec-row:not(.deleted)').forEach(row => {
            if (row.dataset.fieldName) usedNames.add(row.dataset.fieldName);
        });

        // 调用树形 API
        const excludeParam = usedNames.size > 0 ? `&exclude=${encodeURIComponent([...usedNames].join(','))}` : '';
        const subcatParam = this.subcategoryId ? `subcategory_id=${this.subcategoryId}` : '';
        const url = `/api/spec-dictionary/tree?${subcatParam}${excludeParam}`;

        let treeData = [];
        try {
            const response = await fetch(url);
            const result = await response.json();
            if (result.success) {
                treeData = result.data;
            }
        } catch (error) {
            console.error('加载规格树失败:', error);
        }

        if (treeData.length === 0) {
            alert(this.i18n.noAvailableSpecs);
            return;
        }

        // 创建模态框
        this._renderAddSpecModal(treeData);
    }

    /**
     * 渲染添加规格模态框
     */
    _renderAddSpecModal(treeData) {
        // 移除已存在的模态框
        const existingModal = document.getElementById('addSpecTreeModal');
        if (existingModal) existingModal.remove();

        const self = this;
        const selectedSpecs = new Set();

        // 构建分类树 HTML
        let treeHtml = '';
        treeData.forEach(cat => {
            const specCount = cat.specs.length;
            treeHtml += `
                <div class="spec-tree-category" data-cat-id="${cat.id}">
                    <button type="button" class="spec-tree-toggle w-full flex items-center gap-2 px-4 py-2.5 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors text-left"
                            onclick="this.closest('.spec-tree-category').classList.toggle('expanded')">
                        <span class="material-symbols-outlined text-base text-slate-400 transition-transform toggle-icon" style="font-size:18px">chevron_right</span>
                        <span class="text-sm font-semibold text-slate-700 dark:text-slate-300 flex-1">${cat.name}</span>
                        ${cat.name_en ? `<span class="text-xs text-slate-400 dark:text-slate-500 mr-1">${cat.name_en}</span>` : ''}
                        <span class="text-xs text-slate-400 bg-slate-100 dark:bg-slate-700 px-1.5 py-0.5 rounded">${specCount}</span>
                    </button>
                    <div class="spec-tree-items hidden pl-4">
                        ${cat.specs.map(spec => `
                            <label class="spec-tree-item flex items-center gap-3 px-4 py-2 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
                                   data-spec-id="${spec.id}" data-spec-name="${spec.name}" data-spec-name-en="${spec.name_en || ''}"
                                   data-spec-unit="${spec.unit || ''}" data-field-id="${spec.field_id || ''}">
                                <input type="checkbox" class="spec-tree-checkbox w-4 h-4 rounded border-slate-300 dark:border-slate-600 text-primary focus:ring-primary/50"
                                       value="${spec.id}">
                                <span class="text-sm text-slate-700 dark:text-slate-300">${spec.name}</span>
                                ${spec.unit ? `<span class="text-xs text-slate-400">(${spec.unit})</span>` : ''}
                            </label>
                        `).join('')}
                    </div>
                </div>
            `;
        });

        // 创建模态框
        const modal = document.createElement('div');
        modal.id = 'addSpecTreeModal';
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4';
        modal.innerHTML = `
            <div class="absolute inset-0 bg-black/50" onclick="document.getElementById('addSpecTreeModal')?.remove()"></div>
            <div class="relative bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-700 w-full max-w-lg max-h-[80vh] flex flex-col">
                <!-- Header -->
                <div class="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-700">
                    <h3 class="text-base font-semibold text-slate-900 dark:text-white">${this.i18n.addSpecTitle || '添加规格'}</h3>
                    <button type="button" onclick="document.getElementById('addSpecTreeModal')?.remove()"
                            class="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700">
                        <span class="material-symbols-outlined text-xl">close</span>
                    </button>
                </div>
                <!-- Search -->
                <div class="px-5 py-3 border-b border-slate-100 dark:border-slate-800">
                    <div class="relative">
                        <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-lg">search</span>
                        <input type="text" id="addSpecSearchInput" placeholder="${this.i18n.searchSpec || '搜索规格...'}"
                               class="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 dark:border-slate-700 rounded-lg bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary">
                    </div>
                </div>
                <!-- Tree content -->
                <div class="flex-1 overflow-y-auto min-h-0" id="addSpecTreeContent">
                    ${treeHtml}
                    <div id="addSpecNoMatch" class="hidden py-8 text-center text-sm text-slate-400">
                        <span class="material-symbols-outlined text-3xl text-slate-300 dark:text-slate-600 block mb-2">search_off</span>
                        ${this.i18n.noMatchingSpecs || '没有匹配的规格'}
                    </div>
                </div>
                <!-- Footer -->
                <div class="flex items-center justify-between px-5 py-3 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 rounded-b-xl">
                    <span id="addSpecSelectedCount" class="text-sm text-slate-500 dark:text-slate-400">
                        ${this.i18n.selectedCount || '已选'} <strong>0</strong> ${this.i18n.items || '项'}
                    </span>
                    <div class="flex gap-2">
                        <button type="button" onclick="document.getElementById('addSpecTreeModal')?.remove()"
                                class="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-600 transition-colors">
                            ${this.i18n.cancel}
                        </button>
                        <button type="button" id="addSpecConfirmBtn" disabled
                                class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                            ${this.i18n.addSelected || '添加选中规格'}
                        </button>
                    </div>
                </div>
            </div>
            <style>
                .spec-tree-category.expanded .toggle-icon { transform: rotate(90deg); }
                .spec-tree-category.expanded .spec-tree-items { display: block !important; }
                .spec-tree-item.filtered-out { display: none !important; }
                .spec-tree-category.filtered-out { display: none !important; }
            </style>
        `;

        document.body.appendChild(modal);

        // 绑定搜索过滤
        const searchInput = modal.querySelector('#addSpecSearchInput');
        const noMatchEl = modal.querySelector('#addSpecNoMatch');
        searchInput.addEventListener('input', function() {
            const keyword = this.value.trim().toLowerCase();
            let hasVisible = false;
            modal.querySelectorAll('.spec-tree-category').forEach(cat => {
                let catHasVisible = false;
                cat.querySelectorAll('.spec-tree-item').forEach(item => {
                    const name = (item.dataset.specName || '').toLowerCase();
                    const nameEn = (item.dataset.specNameEn || '').toLowerCase();
                    const match = !keyword || name.includes(keyword) || nameEn.includes(keyword);
                    item.classList.toggle('filtered-out', !match);
                    if (match) catHasVisible = true;
                });
                cat.classList.toggle('filtered-out', !catHasVisible);
                // 搜索时自动展开匹配的分类
                if (keyword && catHasVisible) {
                    cat.classList.add('expanded');
                } else if (!keyword) {
                    cat.classList.remove('expanded');
                }
                if (catHasVisible) hasVisible = true;
            });
            noMatchEl.classList.toggle('hidden', hasVisible);
        });

        // 绑定复选框事件
        const updateCount = () => {
            const count = selectedSpecs.size;
            modal.querySelector('#addSpecSelectedCount').innerHTML =
                `${self.i18n.selectedCount || '已选'} <strong>${count}</strong> ${self.i18n.items || '项'}`;
            modal.querySelector('#addSpecConfirmBtn').disabled = count === 0;
        };

        modal.querySelectorAll('.spec-tree-checkbox').forEach(cb => {
            cb.addEventListener('change', function() {
                const item = this.closest('.spec-tree-item');
                const specData = {
                    id: parseInt(item.dataset.specId),
                    name: item.dataset.specName,
                    name_en: item.dataset.specNameEn || '',
                    unit: item.dataset.specUnit || '',
                    field_id: item.dataset.fieldId || null
                };
                if (this.checked) {
                    selectedSpecs.add(JSON.stringify(specData));
                } else {
                    selectedSpecs.delete(JSON.stringify(specData));
                }
                updateCount();
            });
        });

        // 绑定确认按钮
        modal.querySelector('#addSpecConfirmBtn').addEventListener('click', () => {
            const specs = [...selectedSpecs].map(s => JSON.parse(s));
            modal.remove();
            specs.forEach(spec => self._createSpecRowFromDefinition(spec));
            self.updateApplyButtonState();
        });

        // 聚焦搜索框
        searchInput.focus();
    }

    /**
     * 从 SpecDefinition 创建规格行
     * 新行创建后立即显示 select 下拉框，等待用户选择指标
     * 确认后显示值文字和可见性按钮
     */
    _createSpecRowFromDefinition(spec) {
        let specsList = document.getElementById(this.listId);
        if (!specsList) {
            const container = document.getElementById(this.containerId);
            const emptyMsg = document.getElementById(this.emptyMessageId);
            if (emptyMsg) emptyMsg.style.display = 'none';

            specsList = document.createElement('dl');
            specsList.id = this.listId;
            container.appendChild(specsList);
        }

        // 隐藏空消息
        const emptyMsg = document.getElementById(this.emptyMessageId);
        if (emptyMsg) emptyMsg.style.display = 'none';

        const tempId = 'new_' + Date.now() + '_' + spec.id;
        const unit = spec.unit || '';

        const row = document.createElement('div');
        row.className = 'spec-row px-6 py-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors border-t border-slate-100 dark:border-slate-800';
        row.dataset.specId = tempId;
        row.dataset.new = 'true';
        row.dataset.fieldName = spec.name;
        row.dataset.fieldId = spec.field_id || '';
        row.dataset.fieldValue = '';
        row.dataset.fieldCode = '';
        row.dataset.unit = unit;
        row.dataset.includeInDesc = 'true';

        row.innerHTML = `
            <span class="spec-drag-handle cursor-grab active:cursor-grabbing text-slate-300 hover:text-slate-500 mr-1 shrink-0">
                <span class="material-symbols-outlined text-lg">drag_indicator</span>
            </span>
            <div class="flex-1 grid grid-cols-3 gap-4">
                <dt class="text-sm font-medium text-slate-500 dark:text-slate-400 spec-name">${spec.name}</dt>
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
                <button type="button" class="spec-confirm-btn p-1.5 text-slate-400 hover:text-green-500 rounded hover:bg-slate-100 dark:hover:bg-slate-700" title="${this.i18n.apply || '确认'}">
                    <span class="material-symbols-outlined text-lg">check</span>
                </button>
                <button type="button" class="delete-new-spec p-1.5 text-slate-400 hover:text-red-500 rounded hover:bg-slate-100 dark:hover:bg-slate-700" title="${this.i18n.delete}">
                    <span class="material-symbols-outlined text-lg">delete</span>
                </button>
                <button type="button" class="spec-visibility-btn hidden p-1.5 text-slate-400 hover:text-amber-500 rounded hover:bg-slate-100 dark:hover:bg-slate-700" title="${this.i18n.excludeFromDesc || '从描述中排除'}">
                    <span class="material-symbols-outlined text-lg">visibility</span>
                </button>
            </div>
        `;

        specsList.appendChild(row);

        const self = this;
        const select = row.querySelector('.value-select');
        const valueDisplay = row.querySelector('.value-display');
        const unitDisplay = row.querySelector('.unit-display');
        const unitEdit = row.querySelector('.unit-edit');
        const confirmBtn = row.querySelector('.spec-confirm-btn');
        const visibilityBtn = row.querySelector('.spec-visibility-btn');

        // 记入 pendingChanges.added
        this.pendingChanges.added.push({
            tempId: tempId,
            field_name: spec.name,
            field_value: '',
            field_id: spec.field_id || null,
            unit: unit,
            include_in_description: true
        });

        // 立即加载选项
        this.loadSpecOptions(select, spec.name, '').then(() => {
            select.focus();
        });

        // 确认按钮：选择值后确认
        confirmBtn.addEventListener('click', function() {
            const icon = this.querySelector('.material-symbols-outlined');

            if (icon.textContent === 'check') {
                // 确认模式：验证并确认选择
                if (!select.value || select.value === '__MANAGE_OPTIONS__') return;

                const selectedOption = select.options[select.selectedIndex];
                const code = selectedOption?.dataset?.code || '';

                // 更新数据
                row.dataset.fieldValue = select.value;
                row.dataset.fieldCode = code;

                // 更新 pendingChanges
                const addedItem = self.pendingChanges.added.find(a => a.tempId === tempId);
                if (addedItem) {
                    addedItem.field_value = select.value;
                    addedItem.field_code = code;
                }

                // 切换到显示模式
                valueDisplay.textContent = select.value;
                valueDisplay.classList.remove('hidden');
                unitDisplay.classList.remove('hidden');
                select.classList.add('hidden');
                unitEdit.classList.add('hidden');

                // 显示可见性按钮
                visibilityBtn.classList.remove('hidden');

                // 切换图标为编辑
                icon.textContent = 'edit';
                this.classList.remove('text-slate-400', 'hover:text-green-500');
                this.classList.add('text-green-500');
                this.title = self.i18n.edit || '编辑';

                self.updateApplyButtonState();
            } else {
                // 编辑模式：重新打开选择
                valueDisplay.classList.add('hidden');
                unitDisplay.classList.add('hidden');
                select.classList.remove('hidden');
                unitEdit.classList.remove('hidden');
                select.focus();

                // 切换图标为确认
                icon.textContent = 'check';
                this.classList.remove('text-green-500');
                this.classList.add('text-slate-400', 'hover:text-green-500');
                this.title = self.i18n.apply || '确认';

                self.updateApplyButtonState();
            }
        });

        // 删除按钮
        row.querySelector('.delete-new-spec').addEventListener('click', function() {
            self.deleteNewSpec(row);
        });

        // 可见性切换
        visibilityBtn.addEventListener('click', function() {
            const icon = this.querySelector('.material-symbols-outlined');
            const isVisible = icon.textContent === 'visibility';
            icon.textContent = isVisible ? 'visibility_off' : 'visibility';
            row.dataset.includeInDesc = isVisible ? 'false' : 'true';
            this.title = isVisible ? (self.i18n.includeInDesc || '包含在描述中') : (self.i18n.excludeFromDesc || '从描述中排除');

            // 更新 pendingChanges
            const addedItem = self.pendingChanges.added.find(a => a.tempId === tempId);
            if (addedItem) {
                addedItem.include_in_description = !isVisible;
            }
        });
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
            <span class="spec-drag-handle cursor-grab active:cursor-grabbing text-slate-300 hover:text-slate-500 mr-1 shrink-0">
                <span class="material-symbols-outlined text-lg">drag_indicator</span>
            </span>
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

        // 引入产品跳过编码预览（编码已锁定，不会改变）
        // 或者如果未启用编码预览功能，直接保存
        if (this.isImportedProduct || !this.features.codePreview || !this.previewEndpoint) {
            await this._saveChanges(specs);
        } else {
            await this._previewAndSave(specs);
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
        document.querySelectorAll('.spec-drag-handle').forEach(el => el.classList.add('hidden'));

        // 销毁拖拽排序
        this._destroyDragAndDrop();

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

    // ==================== 拖拽排序 ====================

    /**
     * 初始化拖拽排序
     * 使用 HTML5 Drag and Drop API，仅通过拖拽手柄触发
     */
    _initDragAndDrop() {
        const container = document.getElementById(this.listId);
        if (!container) return;

        this._dragState = { draggedRow: null };
        const state = this._dragState;

        // 通过 mousedown 在拖拽手柄上启用行的 draggable
        this._onHandleMouseDown = (e) => {
            const handle = e.target.closest('.spec-drag-handle');
            if (!handle) return;
            const row = handle.closest('.spec-row');
            if (row) row.draggable = true;
        };

        // mouseup 时禁用 draggable（防止非手柄区域拖拽）
        this._onMouseUp = () => {
            container.querySelectorAll('.spec-row[draggable="true"]').forEach(r => r.draggable = false);
        };

        this._onDragStart = (e) => {
            const row = e.target.closest('.spec-row');
            if (!row || !row.draggable) { e.preventDefault(); return; }
            state.draggedRow = row;
            row.classList.add('opacity-40');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', '');
        };

        this._onDragOver = (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            if (!state.draggedRow) return;

            const afterEl = this._getDragAfterElement(container, e.clientY);
            if (afterEl) {
                container.insertBefore(state.draggedRow, afterEl);
            } else {
                container.appendChild(state.draggedRow);
            }
        };

        this._onDragEnd = () => {
            if (state.draggedRow) {
                state.draggedRow.classList.remove('opacity-40');
                state.draggedRow.draggable = false;
                state.draggedRow = null;
            }
        };

        container.addEventListener('mousedown', this._onHandleMouseDown);
        document.addEventListener('mouseup', this._onMouseUp);
        container.addEventListener('dragstart', this._onDragStart);
        container.addEventListener('dragover', this._onDragOver);
        container.addEventListener('dragend', this._onDragEnd);
    }

    /**
     * 获取拖拽后的插入位置
     * 返回鼠标位置之后的第一个 spec-row 元素
     */
    _getDragAfterElement(container, y) {
        const rows = [...container.querySelectorAll('.spec-row:not(.opacity-40)')];
        let closest = null;
        let closestOffset = Number.NEGATIVE_INFINITY;

        rows.forEach(row => {
            const box = row.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            if (offset < 0 && offset > closestOffset) {
                closestOffset = offset;
                closest = row;
            }
        });
        return closest;
    }

    /**
     * 销毁拖拽排序
     */
    _destroyDragAndDrop() {
        const container = document.getElementById(this.listId);
        if (!container) return;

        if (this._onHandleMouseDown) container.removeEventListener('mousedown', this._onHandleMouseDown);
        if (this._onMouseUp) document.removeEventListener('mouseup', this._onMouseUp);
        if (this._onDragStart) container.removeEventListener('dragstart', this._onDragStart);
        if (this._onDragOver) container.removeEventListener('dragover', this._onDragOver);
        if (this._onDragEnd) container.removeEventListener('dragend', this._onDragEnd);

        // 清理所有 draggable 属性
        container.querySelectorAll('.spec-row[draggable]').forEach(r => r.removeAttribute('draggable'));
        this._dragState = null;
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
                <span class="spec-drag-handle hidden cursor-grab active:cursor-grabbing text-slate-300 hover:text-slate-500 mr-1 shrink-0">
                    <span class="material-symbols-outlined text-lg">drag_indicator</span>
                </span>
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
                    <button type="button" onclick="deleteSpec(this)" class="p-1.5 text-slate-400 hover:text-red-500 rounded hover:bg-slate-100 dark:hover:bg-slate-700" title="${this.i18n.delete}">
                        <span class="material-symbols-outlined text-lg">delete</span>
                    </button>
                    <button type="button" onclick="toggleSpecInDescription(this)" class="p-1.5 text-slate-400 hover:text-amber-500 rounded hover:bg-slate-100 dark:hover:bg-slate-700" title="${visibilityTitle}">
                        <span class="material-symbols-outlined text-lg">${visibilityIcon}</span>
                    </button>
                </div>
            `;

            specsList.appendChild(row);
        });
    }

    /**
     * 重建规格列表（分组版本，按分类显示）
     * @param {Array} specCategories - 分类数据数组，每个分类包含 id, name, name_en, specs
     * @param {Object} options - 可选配置
     */
    rebuildSpecsListGrouped(specCategories, options = {}) {
        const specsList = document.getElementById(this.listId);
        if (!specsList) return;

        // 清空现有内容
        specsList.innerHTML = '';

        // 检查是否有数据
        const totalSpecs = specCategories.reduce((sum, cat) => sum + (cat.specs?.length || 0), 0);
        if (totalSpecs === 0) {
            // 显示空消息
            const emptyMsg = document.getElementById('emptySpecsMessage');
            if (emptyMsg) {
                emptyMsg.style.display = 'block';
            }
            return;
        }

        // 隐藏空消息
        const emptyMsg = document.getElementById('emptySpecsMessage');
        if (emptyMsg) {
            emptyMsg.style.display = 'none';
        }

        // 遍历每个分类
        specCategories.forEach(category => {
            if (!category.specs || category.specs.length === 0) return;

            // 创建分类标题
            const categoryHeader = document.createElement('div');
            categoryHeader.className = 'spec-category-header px-6 py-3 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-100 dark:border-slate-800 first:border-t-0';
            categoryHeader.dataset.categoryId = category.id;
            categoryHeader.innerHTML = `
                <span class="text-sm font-semibold text-slate-700 dark:text-slate-300">${category.name}</span>
                ${category.name_en ? `<span class="text-xs text-slate-400 dark:text-slate-500 ml-2">${category.name_en}</span>` : ''}
            `;
            specsList.appendChild(categoryHeader);

            // 创建该分类下的规格行
            category.specs.forEach(spec => {
                const row = document.createElement('div');
                row.className = 'spec-row px-6 py-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors border-t border-slate-100 dark:border-slate-800';
                row.dataset.specId = spec.id;
                row.dataset.fieldName = spec.field_name;
                row.dataset.fieldId = spec.field_id || '';
                row.dataset.fieldValue = spec.field_value;
                row.dataset.fieldCode = spec.field_code || '';
                row.dataset.unit = spec.unit || '';
                row.dataset.includeInDesc = spec.include_in_description ? 'true' : 'false';
                row.dataset.categoryId = category.id;

                const hasCode = !!spec.field_code;
                const visibilityIcon = spec.include_in_description ? 'visibility' : 'visibility_off';
                const visibilityTitle = spec.include_in_description ? this.i18n.excludeFromDesc : this.i18n.includeInDesc;

                row.innerHTML = `
                    <span class="spec-drag-handle hidden cursor-grab active:cursor-grabbing text-slate-300 hover:text-slate-500 mr-1 shrink-0">
                        <span class="material-symbols-outlined text-lg">drag_indicator</span>
                    </span>
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
                        <button type="button" onclick="deleteSpec(this)" class="p-1.5 text-slate-400 hover:text-red-500 rounded hover:bg-slate-100 dark:hover:bg-slate-700" title="${this.i18n.delete}">
                            <span class="material-symbols-outlined text-lg">delete</span>
                        </button>
                        <button type="button" onclick="toggleSpecInDescription(this)" class="p-1.5 text-slate-400 hover:text-amber-500 rounded hover:bg-slate-100 dark:hover:bg-slate-700" title="${visibilityTitle}">
                            <span class="material-symbols-outlined text-lg">${visibilityIcon}</span>
                        </button>
                    </div>
                `;

                specsList.appendChild(row);
            });
        });
    }

    /**
     * 应用引入产品的编辑限制
     * 引入产品的所有规格都不可编辑，不能添加新规格
     * 只保留"是否作为描述"勾选功能
     */
    _applyImportedProductRestrictions() {
        // 1. 隐藏"添加"按钮（不能添加新规格）
        const addBtn = document.getElementById(this.buttons.add);
        if (addBtn) {
            addBtn.style.display = 'none';
        }

        // 2. 所有规格灰显，不可编辑
        const container = document.getElementById(this.containerId);
        if (!container) return;

        const rows = container.querySelectorAll('.spec-row');
        rows.forEach(row => {
            // 所有规格都灰显
            row.classList.add('spec-disabled');

            // 禁用值编辑
            const valueSelect = row.querySelector('.value-select');
            const valueInput = row.querySelector('.spec-value-input');
            if (valueSelect) valueSelect.disabled = true;
            if (valueInput) valueInput.disabled = true;

            // 隐藏编辑和删除按钮
            const editBtn = row.querySelector('button[onclick*="toggleSpecEdit"]');
            const deleteBtn = row.querySelector('button[onclick*="deleteSpec"]');
            if (editBtn) editBtn.style.display = 'none';
            if (deleteBtn) deleteBtn.style.display = 'none';

            // "是否作为描述"勾选功能保持不变
        });
    }

    /**
     * 清理引入产品编辑限制状态
     */
    _clearImportedProductRestrictions() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        const rows = container.querySelectorAll('.spec-row');
        rows.forEach(row => {
            row.classList.remove('spec-disabled');

            // 恢复编辑和删除按钮显示
            const editBtn = row.querySelector('button[onclick*="toggleSpecEdit"]');
            const deleteBtn = row.querySelector('button[onclick*="deleteSpec"]');
            if (editBtn) editBtn.style.display = '';
            if (deleteBtn) deleteBtn.style.display = '';

            // 恢复值编辑
            const valueSelect = row.querySelector('.value-select');
            const valueInput = row.querySelector('.spec-value-input');
            if (valueSelect) valueSelect.disabled = false;
            if (valueInput) valueInput.disabled = false;
        });
    }
}

// 导出到全局
window.SpecEditor = SpecEditor;
