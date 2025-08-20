/**
 * 审批配置管理 - 干净重构版本
 * 移除所有重复函数和补丁代码, 使用现代ES6+语法
 */

class ApprovalConfigManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initSortable();
        console.log('✅ 审批配置管理初始化完成');
    }

    /**
     * 绑定所有事件
     */
    bindEvents() {
        // 使用事件委托，避免重复绑定
        document.addEventListener('click', this.handleClick.bind(this));
        document.addEventListener('DOMContentLoaded', this.handleDOMReady.bind(this));
    }

    /**
     * 统一的点击事件处理
     */
    handleClick(event) {
        const target = event.target.closest('button, a');
        if (!target) return;

        // 删除步骤按钮
        if (target.classList.contains('delete-step-btn') || 
            (target.dataset.stepId && target.textContent.includes('删除'))) {
            event.preventDefault();
            const stepId = target.dataset.stepId;
            const stepName = target.dataset.stepName;
            this.confirmDeleteStep(stepId, stepName);
            return;
        }

        // 编辑步骤按钮 - 多重检测
        if (target.classList.contains('edit-step-btn') || 
            target.dataset.bsToggle === 'modal' ||
            (target.dataset.stepId && target.textContent.includes('编辑'))) {
            event.preventDefault();
            
            try {
                const stepData = this.extractStepData(target);
                this.handleEditStep(stepData);
            } catch (error) {
                console.error('处理编辑步骤时出错:', error);
                // 降级处理：如果数据提取失败，尝试显示空模态框
                this.showEditModal(target.dataset.stepId, target.dataset.stepName);
            }
            return;
        }

        // 删除分支条件按钮
        if (target.classList.contains('delete-condition-btn')) {
            event.preventDefault();
            event.stopPropagation();
            const stepId = target.dataset.stepId;
            const conditionIndex = target.dataset.conditionIndex;
            this.confirmDeleteCondition(stepId, conditionIndex);
            return;
        }

        // 编辑分支条件
        if (target.closest('.branch-step-button')) {
            const button = target.closest('.branch-step-button');
            const stepId = button.dataset.stepId;
            const conditionIndex = button.dataset.conditionIndex;
            this.editBranchCondition(stepId, conditionIndex);
            return;
        }
    }

    /**
     * DOM准备就绪事件处理
     */
    handleDOMReady() {
        // 初始化模态框事件
        this.initModalEvents();
    }

    /**
     * 确认删除步骤
     */
    confirmDeleteStep(stepId, stepName) {
        if (typeof window.showConfirmDialog === 'function') {
            window.showConfirmDialog({
                title: '确认删除审批步骤',
                message: `确定要删除步骤 "${stepName || '该步骤'}" 吗？\n\n删除后无法恢复，请谨慎操作。`,
                type: 'danger',
                confirmText: '确认删除',
                cancelText: '取消',
                dialogId: 'stepDeleteDialog',
                onConfirm: () => this.executeDeleteStep(stepId)
            });
        } else {
            // 使用内置的确认对话框实现
            this.showBuiltinConfirmDialog({
                title: '确认删除审批步骤',
                message: `确定要删除步骤 "${stepName || '该步骤'}" 吗？\n\n删除后无法恢复，请谨慎操作。`,
                onConfirm: () => this.executeDeleteStep(stepId)
            });
        }
    }

    /**
     * 执行删除步骤
     */
    executeDeleteStep(stepId) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/approval/step/${stepId}/delete`;
        
        const csrfToken = document.createElement('input');
        csrfToken.type = 'hidden';
        csrfToken.name = 'csrf_token';
        csrfToken.value = document.querySelector('meta[name="csrf-token"]')?.content || '';
        form.appendChild(csrfToken);
        
        document.body.appendChild(form);
        form.submit();
    }

    /**
     * 确认删除分支条件
     */
    confirmDeleteCondition(stepId, conditionIndex) {
        if (typeof window.showConfirmDialog === 'function') {
            window.showConfirmDialog({
                title: '确认删除分支条件',
                message: '确定要删除此分支条件吗？\n\n删除后无法恢复。',
                type: 'danger',
                confirmText: '确认删除',
                cancelText: '取消',
                dialogId: 'conditionDeleteDialog',
                onConfirm: () => this.executeDeleteCondition(stepId, conditionIndex)
            });
        } else {
            if (confirm('确定要删除此分支条件吗？')) {
                this.executeDeleteCondition(stepId, conditionIndex);
            }
        }
    }

    /**
     * 执行删除分支条件
     */
    executeDeleteCondition(stepId, conditionIndex) {
        // TODO: 实现删除分支条件的API调用
        console.log(`删除分支条件: 步骤${stepId}, 条件${conditionIndex}`);
        alert('删除分支条件功能正在开发中');
    }

    /**
     * 编辑分支条件
     */
    editBranchCondition(stepId, conditionIndex) {
        // TODO: 实现编辑分支条件的功能
        console.log(`编辑分支条件: 步骤${stepId}, 条件${conditionIndex}`);
        alert('编辑分支条件功能正在开发中');
    }

    /**
     * 处理编辑步骤
     */
    handleEditStep(stepData) {
        console.log('🔧 处理编辑步骤:', stepData);
        
        const modal = document.getElementById('editStepModal');
        if (!modal) {
            console.error('❌ 找不到编辑步骤模态框 #editStepModal');
            // 尝试查找其他可能的模态框
            const modals = document.querySelectorAll('.modal[id*="edit"], .modal[id*="Step"]');
            console.log('🔍 找到的相关模态框:', modals);
            return;
        }

        // 填充表单数据
        this.populateEditForm(modal, stepData);
        
        // 显示模态框
        this.showModal(modal);
    }

    /**
     * 降级显示编辑模态框
     */
    showEditModal(stepId, stepName) {
        console.log('🔧 降级显示编辑模态框');
        
        const modal = document.getElementById('editStepModal');
        if (!modal) {
            console.error('❌ 找不到模态框，无法降级处理');
            return;
        }

        // 基础数据填充
        const form = modal.querySelector('#editStepForm');
        if (form && stepId) {
            form.action = `/admin/approval/step/${stepId}/edit`;
        }

        const nameField = modal.querySelector('#edit_step_name');
        if (nameField && stepName) {
            nameField.value = stepName;
        }

        this.showModal(modal);
    }

    /**
     * 统一的模态框显示方法
     */
    showModal(modal) {
        console.log('📋 显示模态框:', modal.id);
        
        try {
            if (typeof bootstrap !== 'undefined') {
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
                console.log('✅ 使用Bootstrap显示模态框');
            } else if (typeof $ !== 'undefined') {
                $(modal).modal('show');
                console.log('✅ 使用jQuery显示模态框');
            } else {
                // 最后的降级处理
                modal.style.display = 'block';
                modal.classList.add('show');
                console.log('✅ 使用原生方法显示模态框');
            }
        } catch (error) {
            console.error('❌ 显示模态框失败:', error);
        }
    }

    /**
     * 提取步骤数据
     */
    extractStepData(button) {
        // 安全解析JSON数据
        const safeParseJSON = (jsonStr, defaultValue = []) => {
            try {
                if (!jsonStr || jsonStr === 'null' || jsonStr === 'undefined') {
                    return defaultValue;
                }
                
                // 检查是否为不完整的JSON字符串
                if (jsonStr === '[' || jsonStr === '{' || jsonStr.endsWith(',')) {
                    console.warn('检测到不完整的JSON字符串:', jsonStr);
                    return defaultValue;
                }
                
                return JSON.parse(jsonStr);
            } catch (error) {
                console.warn('JSON解析失败:', jsonStr, error);
                return defaultValue;
            }
        };

        return {
            stepId: button.dataset.stepId,
            stepName: button.dataset.stepName,
            approverId: button.dataset.approverId,
            approverType: button.dataset.approverType,
            sendEmail: button.dataset.sendEmail,
            actionType: button.dataset.actionType,
            editableFields: safeParseJSON(button.dataset.editableFields, []),
            ccUsers: safeParseJSON(button.dataset.ccUsers, []),
            ccEnabled: button.dataset.ccEnabled
        };
    }

    /**
     * 填充编辑表单
     */
    populateEditForm(modal, stepData) {
        // 设置表单action - 使用正确的路由路径
        const form = modal.querySelector('#editStepForm');
        if (form && stepData.stepId) {
            form.action = `/admin/approval/step/${stepData.stepId}/edit`;
        }

        // 填充字段
        const fields = {
            'edit_step_name': stepData.stepName,
            'edit_approver_selection': stepData.approverType === 'next_level' ? 'next_level' : `user_${stepData.approverId}`,
            'edit_action_type': stepData.actionType,
            'edit_send_email': stepData.sendEmail
        };

        Object.entries(fields).forEach(([fieldId, value]) => {
            const field = modal.querySelector(`#${fieldId}`);
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = value === 'true' || value === true;
                } else {
                    field.value = value || '';
                }
            }
        });
    }

    /**
     * 初始化排序功能
     */
    initSortable() {
        const stepList = document.getElementById('stepList');
        if (stepList && typeof Sortable !== 'undefined') {
            new Sortable(stepList, {
                handle: '.handle',
                animation: 150,
                onEnd: (evt) => this.handleStepReorder(evt)
            });
        }
    }

    /**
     * 处理步骤重新排序
     */
    handleStepReorder(evt) {
        const stepOrders = Array.from(evt.to.children).map((li, index) => ({
            stepId: li.dataset.stepId,
            order: index + 1
        }));

        // TODO: 发送到后端更新排序
        console.log('步骤重新排序:', stepOrders);
    }

    /**
     * 初始化模态框事件
     */
    initModalEvents() {
        // 审批人选择变化事件
        const approverSelects = document.querySelectorAll('[id*="approver_selection"]');
        approverSelects.forEach(select => {
            select.addEventListener('change', this.handleApproverSelection.bind(this));
        });

        // 步骤类型选择变化事件
        const stepTypeSelects = document.querySelectorAll('#step_type, #edit_step_type');
        stepTypeSelects.forEach(select => {
            select.addEventListener('change', this.handleStepTypeChange.bind(this));
        });

        // 分支字段选择变化事件  
        const branchFieldSelects = document.querySelectorAll('#branch_field, #edit_branch_field');
        branchFieldSelects.forEach(select => {
            select.addEventListener('change', this.handleBranchFieldChange.bind(this));
        });

        // 分支操作符选择变化事件
        const branchOperatorSelects = document.querySelectorAll('#branch_operator, #edit_branch_operator');
        branchOperatorSelects.forEach(select => {
            select.addEventListener('change', this.handleBranchOperatorChange.bind(this));
        });

        // 抄送开关切换事件
        const ccToggles = document.querySelectorAll('#cc_enabled, #edit_cc_enabled');
        ccToggles.forEach(checkbox => {
            checkbox.addEventListener('change', this.handleCcToggle.bind(this));
        });

        // 可编辑字段选择事件
        const editableFieldSelects = document.querySelectorAll('#editable_fields_select, #edit_editable_fields_select');
        editableFieldSelects.forEach(select => {
            select.addEventListener('change', (event) => {
                const fieldCode = event.target.value;
                const fieldName = event.target.selectedOptions[0]?.textContent;
                if (fieldCode && fieldName) {
                    const containerId = event.target.id.includes('edit_') ? 'edit_selected_fields' : 'selected_fields';
                    this.addFieldBadge(fieldCode, fieldName, containerId);
                    event.target.value = ''; // 重置选择框
                }
            });
        });
    }

    /**
     * 处理审批人选择
     */
    handleApproverSelection(event) {
        const select = event.target;
        const value = select.value;
        
        // 确定是添加还是编辑模式
        const isEditMode = select.id.includes('edit_');
        const infoSectionId = isEditMode ? 'edit_next_level_info_section' : 'next_level_info_section';
        
        // 显示/隐藏上级领导说明
        const infoSection = document.getElementById(infoSectionId);
        if (infoSection) {
            infoSection.style.display = value === 'next_level' ? 'block' : 'none';
        }

        // 更新隐藏字段
        this.updateHiddenApproverFields(select.closest('.modal, form'), value, isEditMode);
    }

    /**
     * 处理步骤类型选择变化
     */
    handleStepTypeChange(event) {
        const select = event.target;
        const value = select.value;
        const modal = select.closest('.modal');
        
        // 显示/隐藏分支条件配置区域
        const prefix = select.id.includes('edit_') ? 'edit_' : '';
        const branchConfigId = `${prefix}branchConfigSection`;
        const branchConfig = modal.querySelector(`#${branchConfigId}`);
        
        console.log('步骤类型选择变化:', value, '查找分支配置区域:', branchConfigId);
        
        if (branchConfig) {
            branchConfig.style.display = value === 'branch' ? 'block' : 'none';
            console.log('分支配置区域已', value === 'branch' ? '显示' : '隐藏');
            
            // 如果切换到分支类型，加载字段选项
            if (value === 'branch') {
                this.loadBranchFieldOptions(modal, prefix);
            }
        } else {
            console.error('找不到分支配置区域:', branchConfigId);
        }
    }

    /**
     * 加载分支字段选项
     */
    loadBranchFieldOptions(modal, prefix = '') {
        const fieldSelect = modal.querySelector(`#${prefix}branch_field`);
        if (!fieldSelect) {
            console.error('找不到分支字段选择器:', `#${prefix}branch_field`);
            return;
        }
        
        // 获取模板ID和对象类型
        const templateIdInput = modal.querySelector('input[name="template_id"]');
        const objectTypeInput = modal.querySelector('input[name="object_type"]');
        const templateId = templateIdInput ? templateIdInput.value : '';
        const objectType = objectTypeInput ? objectTypeInput.value : '';
        
        console.log('获取到模板信息:', {templateId, objectType});
        
        if (!templateId) {
            console.error('无法获取模板ID');
            return;
        }
        
        if (!objectType) {
            console.error('无法获取对象类型');
            return;
        }
        
        // 调用API获取字段选项
        fetch(`/admin/approval/api/get-field-options?object_type=${objectType}&template_id=${templateId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.fields) {
                this.populateFieldOptions(fieldSelect, data.fields);
            } else {
                console.error('获取字段选项失败:', data.message);
            }
        })
        .catch(error => {
            console.error('加载字段选项时发生错误:', error);
        });
    }

    /**
     * 填充字段选项到下拉框
     */
    populateFieldOptions(selectElement, fields) {
        // 清空现有选项，保留第一个默认选项
        selectElement.innerHTML = '<option value="">请选择字段</option>';
        
        if (!fields) {
            console.warn('字段选项为空');
            return;
        }
        
        // 检查API返回格式：{master: {}, detail: {}}
        if (fields && typeof fields === 'object' && (fields.master || fields.detail)) {
            // 主记录字段
            if (fields.master && typeof fields.master === 'object') {
                const masterGroup = document.createElement('optgroup');
                masterGroup.label = '主记录字段';
                Object.entries(fields.master).forEach(([fieldCode, fieldName]) => {
                    const option = document.createElement('option');
                    option.value = fieldCode;
                    option.textContent = fieldName;
                    masterGroup.appendChild(option);
                });
                selectElement.appendChild(masterGroup);
            }
            
            // 明细字段
            if (fields.detail && typeof fields.detail === 'object') {
                const detailGroup = document.createElement('optgroup');
                detailGroup.label = '明细字段';
                Object.entries(fields.detail).forEach(([fieldCode, fieldName]) => {
                    const option = document.createElement('option');
                    option.value = fieldCode;
                    option.textContent = fieldName;
                    detailGroup.appendChild(option);
                });
                selectElement.appendChild(detailGroup);
            }
        } else if (fields && typeof fields === 'object') {
            // 简单对象格式：{field_code: field_name}
            Object.entries(fields).forEach(([fieldCode, fieldName]) => {
                const option = document.createElement('option');
                option.value = fieldCode;
                option.textContent = fieldName;
                selectElement.appendChild(option);
            });
        } else if (Array.isArray(fields)) {
            // 数组格式处理
            fields.forEach(field => {
                const option = document.createElement('option');
                if (Array.isArray(field) && field.length >= 2) {
                    option.value = field[0];
                    option.textContent = field[1];
                } else if (typeof field === 'object' && field.name && field.display_name) {
                    option.value = field.name;
                    option.textContent = field.display_name;
                }
                selectElement.appendChild(option);
            });
        }
        
        console.log('字段选项已加载:', selectElement.options.length - 1, '个字段');
    }

    /**
     * 处理分支字段选择变化
     */
    handleBranchFieldChange(event) {
        const select = event.target;
        const fieldName = select.value;
        const modal = select.closest('.modal');
        
        // 根据字段类型更新操作符选项
        this.updateOperatorOptions(modal, fieldName);
        
        // 清空值输入框
        const fieldSelect = event.target;
        const prefix = fieldSelect.id.includes('edit_') ? 'edit_' : '';
        const valueInput = modal.querySelector(`#${prefix}branch_value`);
        if (valueInput) {
            valueInput.value = '';
        }
        
        console.log('分支字段选择变化:', fieldName);
    }

    /**
     * 处理分支操作符变化
     */
    handleBranchOperatorChange(event) {
        const select = event.target;
        const operator = select.value;
        const modal = select.closest('.modal');
        
        // 根据操作符类型更新值输入方式
        this.updateValueInput(modal, operator);
        
        console.log('分支操作符选择变化:', operator);
    }

    /**
     * 更新操作符选项
     */
    updateOperatorOptions(modal, fieldName) {
        const fieldSelect = modal.querySelector('#branch_field, #edit_branch_field');
        const prefix = fieldSelect && fieldSelect.id.includes('edit_') ? 'edit_' : '';
        const operatorSelect = modal.querySelector(`#${prefix}branch_operator`);
        if (!operatorSelect) return;
        
        // 清空现有选项
        operatorSelect.innerHTML = '';
        
        let operators = [];
        
        // 根据字段类型确定可用操作符
        if (fieldName === 'total_amount' || fieldName === 'quantity' || fieldName === 'amount' || 
            fieldName === 'pricing_total_amount' || fieldName === 'settlement_total_amount' || 
            fieldName === 'market_price' || fieldName === 'unit_price' || fieldName === 'total_price') {
            // 数值字段
            operators = [
                ['equals', '等于'],
                ['not_equals', '不等于'],
                ['greater_than', '大于'],
                ['less_than', '小于'],
                ['greater_equal', '大于等于'],
                ['less_equal', '小于等于']
            ];
        } else if (fieldName === 'project_type' || fieldName === 'status' || fieldName === 'approval_status' || 
                   fieldName === 'currency' || fieldName === 'project_stage' || fieldName === 'expense_category' ||
                   fieldName === 'brand' || fieldName === 'unit') {
            // 枚举字段
            operators = [
                ['equals', '等于'],
                ['not_equals', '不等于'],
                ['in_list', '属于'],
                ['not_in_list', '不属于'],
                ['from_field_list', '从字段列表选择']
            ];
        } else if (fieldName === 'created_at' || fieldName === 'updated_at' || fieldName === 'expense_date') {
            // 日期字段
            operators = [
                ['equals', '等于'],
                ['not_equals', '不等于'],
                ['greater_than', '晚于'],
                ['less_than', '早于'],
                ['greater_equal', '不早于'],
                ['less_equal', '不晚于']
            ];
        } else {
            // 文本字段
            operators = [
                ['equals', '等于'],
                ['not_equals', '不等于'],
                ['contains', '包含'],
                ['not_contains', '不包含'],
                ['starts_with', '以...开头'],
                ['ends_with', '以...结尾'],
                ['from_field_list', '从字段列表选择']
            ];
        }
        
        // 添加选项
        operators.forEach(([value, text]) => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = text;
            operatorSelect.appendChild(option);
        });
    }

    /**
     * 更新值输入方式
     */
    updateValueInput(modal, operator) {
        const operatorSelect = modal.querySelector('#branch_operator, #edit_branch_operator');
        const prefix = operatorSelect && operatorSelect.id.includes('edit_') ? 'edit_' : '';
        const valueContainer = modal.querySelector(`#${prefix}branchValueContainer`);
        if (!valueContainer) return;
        
        let inputHtml = '';
        
        if (operator === 'from_field_list') {
            // 从字段列表选择（复选框模式）
            inputHtml = `
                <div class="field-values-container">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <small class="text-muted">加载字段值选项中...</small>
                        <button type="button" class="btn btn-sm btn-outline-primary" onclick="loadFieldValues('${prefix}')">
                            <i class="fas fa-sync-alt"></i> 刷新
                        </button>
                    </div>
                    <div id="${prefix}field_values_container" class="border rounded p-2" style="max-height: 200px; overflow-y: auto;">
                        <div class="text-center text-muted">请先选择字段和操作符</div>
                    </div>
                    <input type="hidden" id="${prefix}branch_value" name="branch_value">
                </div>
            `;
        } else if (operator === 'in_list' || operator === 'not_in_list') {
            // 多选输入
            inputHtml = `
                <input type="text" class="form-control" id="${prefix}branch_value" name="branch_value" 
                       placeholder="请输入多个值，用逗号分隔" 
                       title="多个值用逗号分隔，例如：值1,值2,值3">
                <small class="form-text text-muted">多个值用逗号分隔</small>
            `;
        } else if (operator === 'greater_than' || operator === 'less_than' || 
                   operator === 'greater_equal' || operator === 'less_equal') {
            // 数值输入
            inputHtml = `
                <input type="number" class="form-control" id="${prefix}branch_value" name="branch_value" 
                       placeholder="请输入数值" step="0.01">
            `;
        } else {
            // 单值输入
            inputHtml = `
                <input type="text" class="form-control" id="${prefix}branch_value" name="branch_value" 
                       placeholder="请输入比较值">
            `;
        }
        
        valueContainer.innerHTML = inputHtml;
        
        // 如果是从字段列表选择，自动加载字段值
        if (operator === 'from_field_list') {
            this.loadFieldValues(prefix);
        }
    }

    /**
     * 加载字段值选项（用于从字段列表选择）
     */
    loadFieldValues(prefix = '') {
        const modal = document.querySelector('.modal.show') || document.querySelector('.modal');
        if (!modal) return;
        
        const fieldSelect = modal.querySelector(`#${prefix}branch_field`);
        const fieldName = fieldSelect ? fieldSelect.value : '';
        
        if (!fieldName) {
            this.showFieldValuesError(prefix, '请先选择条件字段');
            return;
        }
        
        const container = modal.querySelector(`#${prefix}field_values_container`);
        if (!container) return;
        
        // 显示加载状态
        container.innerHTML = `
            <div class="text-center">
                <i class="fas fa-spinner fa-spin"></i> 加载字段值选项中...
            </div>
        `;
        
        // 获取模板信息
        const templateIdInput = modal.querySelector('input[name="template_id"]');
        const templateId = templateIdInput ? templateIdInput.value : '';
        
        if (!templateId) {
            this.showFieldValuesError(prefix, '无法获取模板信息');
            return;
        }
        
        // 调用API获取字段值
        fetch(`/admin/approval/field-values?template_id=${templateId}&field_name=${fieldName}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.values) {
                this.renderFieldValuesCheckboxes(prefix, data.values, fieldName);
            } else {
                this.showFieldValuesError(prefix, data.message || '获取字段值失败');
            }
        })
        .catch(error => {
            console.error('加载字段值失败:', error);
            this.showFieldValuesError(prefix, '网络错误，请重试');
        });
    }

    /**
     * 渲染字段值复选框
     */
    renderFieldValuesCheckboxes(prefix, values, fieldName) {
        const container = document.querySelector(`#${prefix}field_values_container`);
        if (!container || !values || values.length === 0) {
            this.showFieldValuesError(prefix, '该字段暂无可选值');
            return;
        }
        
        let html = `<div class="mb-2"><strong>选择 ${fieldName} 的值：</strong></div>`;
        
        values.forEach((value, index) => {
            const checkboxId = `${prefix}field_value_${index}`;
            html += `
                <div class="form-check">
                    <input class="form-check-input field-value-checkbox" 
                           type="checkbox" 
                           id="${checkboxId}" 
                           value="${value}" 
                           onchange="updateSelectedFieldValues('${prefix}')">
                    <label class="form-check-label" for="${checkboxId}">
                        ${value}
                    </label>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }

    /**
     * 显示字段值加载错误
     */
    showFieldValuesError(prefix, message) {
        const container = document.querySelector(`#${prefix}field_values_container`);
        if (container) {
            container.innerHTML = `
                <div class="text-center text-danger">
                    <i class="fas fa-exclamation-triangle"></i> ${message}
                </div>
            `;
        }
    }

    /**
     * 更新选中的字段值
     */
    updateSelectedFieldValues(prefix) {
        const checkboxes = document.querySelectorAll(`#${prefix}field_values_container .field-value-checkbox:checked`);
        const selectedValues = Array.from(checkboxes).map(cb => cb.value);
        
        const hiddenInput = document.querySelector(`#${prefix}branch_value`);
        if (hiddenInput) {
            hiddenInput.value = selectedValues.join(',');
        }
        
        console.log('选中的字段值:', selectedValues);
    }

    /**
     * 添加可编辑字段徽章
     */
    addFieldBadge(fieldCode, fieldName, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // 检查是否已存在
        if (container.querySelector(`[data-field-code="${fieldCode}"]`)) {
            return;
        }
        
        const badge = document.createElement('span');
        badge.className = 'badge bg-info text-white me-2 mb-2 editable-field-badge';
        badge.setAttribute('data-field-code', fieldCode);
        badge.innerHTML = `
            ${fieldName}
            <button type="button" class="btn-close btn-close-white ms-1" 
                    onclick="this.parentElement.remove()" 
                    aria-label="移除"></button>
            <input type="hidden" name="editable_fields" value="${fieldCode}">
        `;
        
        container.appendChild(badge);
    }

    /**
     * 处理抄送开关切换
     */
    handleCcToggle(event) {
        const checkbox = event.target;
        const modal = checkbox.closest('.modal');
        const prefix = checkbox.id.includes('edit_') ? 'edit_' : '';
        const ccSection = modal.querySelector(`#${prefix}ccUsersSection`);
        
        if (ccSection) {
            ccSection.style.display = checkbox.checked ? 'block' : 'none';
        }
    }

    /**
     * 更新隐藏的审批人字段
     */
    updateHiddenApproverFields(container, value, isEditMode = false) {
        const prefix = isEditMode ? 'edit_' : '';
        const approverTypeField = container.querySelector(`#${prefix}approver_type`) || 
                                  container.querySelector('[name="approver_type"]');
        const approverIdField = container.querySelector(`#${prefix}approver_id`) || 
                               container.querySelector('[name="approver_id"]');

        if (value === 'next_level') {
            if (approverTypeField) approverTypeField.value = 'next_level';
            if (approverIdField) approverIdField.value = '';
        } else if (value.startsWith('user_')) {
            const userId = value.replace('user_', '');
            if (approverTypeField) approverTypeField.value = 'user';
            if (approverIdField) approverIdField.value = userId;
        }
    }

    /**
     * 内置确认对话框实现
     */
    showBuiltinConfirmDialog(options) {
        const { title, message, onConfirm, onCancel } = options;
        
        if (confirm(`${title}\n\n${message}`)) {
            if (onConfirm) onConfirm();
        } else {
            if (onCancel) onCancel();
        }
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    window.approvalConfig = new ApprovalConfigManager();
});

// 为了向后兼容，提供全局函数
window.confirmDeleteStep = function(stepId, stepName) {
    if (window.approvalConfig) {
        window.approvalConfig.confirmDeleteStep(stepId, stepName);
    }
};

window.editBranchCondition = function(stepId, conditionIndex) {
    if (window.approvalConfig) {
        window.approvalConfig.editBranchCondition(stepId, conditionIndex);
    }
};

window.deleteBranchCondition = function(stepId, conditionIndex) {
    if (window.approvalConfig) {
        window.approvalConfig.confirmDeleteCondition(stepId, conditionIndex);
    }
};

// 全局审批人选择处理函数
window.handleApproverSelection = function() {
    if (window.approvalConfig) {
        const event = window.event || event;
        window.approvalConfig.handleApproverSelection(event);
    }
};

// 全局步骤类型变化处理函数
window.handleStepTypeChange = function() {
    if (window.approvalConfig) {
        const event = window.event || event;
        window.approvalConfig.handleStepTypeChange(event);
    }
};

// 全局分支字段变化处理函数
window.handleBranchFieldChange = function() {
    if (window.approvalConfig) {
        const event = window.event || event;
        window.approvalConfig.handleBranchFieldChange(event);
    }
};

// 全局分支操作符变化处理函数
window.handleBranchOperatorChange = function() {
    if (window.approvalConfig) {
        const event = window.event || event;
        window.approvalConfig.handleBranchOperatorChange(event);
    }
};

// 全局可编辑字段添加函数
window.addFieldBadge = function(fieldCode, fieldName, containerId) {
    if (window.approvalConfig) {
        window.approvalConfig.addFieldBadge(fieldCode, fieldName, containerId);
    }
};

// 全局抄送开关处理函数
window.handleCcToggle = function() {
    if (window.approvalConfig) {
        const event = window.event || event;
        window.approvalConfig.handleCcToggle(event);
    }
};

// 全局字段值加载函数
window.loadFieldValues = function(prefix = '') {
    if (window.approvalConfig) {
        window.approvalConfig.loadFieldValues(prefix);
    }
};

// 全局更新选中字段值函数
window.updateSelectedFieldValues = function(prefix) {
    if (window.approvalConfig) {
        window.approvalConfig.updateSelectedFieldValues(prefix);
    }
};