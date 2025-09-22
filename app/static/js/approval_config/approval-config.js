/**
 * 审批配置管理 - 干净重构版本
 * 移除所有重复函数和补丁代码, 使用现代ES6+语法
 */

class ApprovalConfigManager {
    constructor() {
        // 字段管理状态
        this.selectedFields = [];
        this.editSelectedFields = [];
        // 防重复绑定标志
        this.eventsBound = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.initSortable();
        this.initialized = true; // 添加初始化标志
        console.log('✅ 审批配置管理初始化完成');
    }

    /**
     * 绑定所有事件
     */
    bindEvents() {
        // 防重复绑定检查
        if (this.eventsBound) {
            console.log('🔄 事件已绑定，跳过重复绑定');
            return;
        }

        // 使用事件委托，避免重复绑定
        document.addEventListener('click', this.handleClick.bind(this));
        document.addEventListener('DOMContentLoaded', this.handleDOMReady.bind(this));
        
        // 添加表单提交事件监听，用于调试分支条件数据
        document.addEventListener('submit', this.handleFormSubmit.bind(this));
        
        // 标记事件已绑定
        this.eventsBound = true;
        console.log('✅ 事件绑定完成，已设置防重复标志');
    }

    /**
     * 表单提交事件处理 - AJAX异步提交
     */
    async handleFormSubmit(event) {
        const form = event.target || event;
        
        // 处理所有步骤表单：addStepForm, editStepForm等
        if (!form.id || (!form.id.includes('StepForm') && !form.id.includes('stepForm'))) {
            return;
        }

        // 阻止默认的同步表单提交（如果是事件对象）
        if (event && event.preventDefault) {
            event.preventDefault();
        }
        
        // 调试信息：记录所有表单提交
        console.log('🔍 === AJAX表单提交开始 ===');
        console.log('📤 表单ID:', form.id);
        console.log('📤 表单目标URL:', form.action);
        console.log('📤 表单方法:', form.method);
        
        try {
            // 显示提交加载状态
            this.showFormLoading(form, true);
            
            // 执行预提交验证
            const validationResult = await this.preSubmitValidation(form);
            
            if (validationResult.hasConflict) {
                console.log('⚠️ [调试] 检测到冲突，显示警告对话框');
                
                // 隐藏加载状态
                this.showFormLoading(form, false);
                
                // 显示冲突提示对话框
                this.showConflictDialog(validationResult.conflictInfo);
                
                return; // 停止提交，等待用户处理冲突
            }
            
            // 获取表单数据
            const formData = new FormData(form);
            
            // 🔍 调试：详细记录表单数据
            console.log('🔍 === 表单数据调试 ===');
            console.log('📋 表单元素数量:', form.elements.length);
            
            // 记录所有表单字段
            const formDataEntries = {};
            for (let [key, value] of formData.entries()) {
                if (formDataEntries[key]) {
                    // 如果键已存在，转换为数组
                    if (Array.isArray(formDataEntries[key])) {
                        formDataEntries[key].push(value);
                    } else {
                        formDataEntries[key] = [formDataEntries[key], value];
                    }
                } else {
                    formDataEntries[key] = value;
                }
            }
            console.log('📋 表单数据详情:', formDataEntries);
            
            // 特别关注可编辑字段相关数据 - 增强验证和同步
            const editableFieldsInput = form.querySelector('input[name="editable_fields"]') || 
                                       form.querySelector('#editable_fields_input') ||
                                       form.querySelector('#edit_editable_fields_input');
            if (editableFieldsInput) {
                // 🔍 表单提交前确保可编辑字段数据同步
                const isEditMode = editableFieldsInput.id.includes('edit_');
                const currentFields = isEditMode ? this.editSelectedFields : this.selectedFields;
                const expectedValue = JSON.stringify(currentFields);
                
                console.log('🔍 [提交前验证] 可编辑字段同步检查:', {
                    id: editableFieldsInput.id,
                    name: editableFieldsInput.name,
                    currentValue: editableFieldsInput.value,
                    expectedValue: expectedValue,
                    isSync: editableFieldsInput.value === expectedValue,
                    isEditMode: isEditMode,
                    fieldsArray: currentFields
                });
                
                // 如果不同步，更新隐藏字段值
                if (editableFieldsInput.value !== expectedValue) {
                    console.warn('⚠️ [提交前修复] 隐藏字段值不同步，正在更新');
                    editableFieldsInput.value = expectedValue;
                    console.log('✅ [提交前修复] 隐藏字段已更新为:', expectedValue);
                }
                
                console.log('🔍 [提交前验证] 最终可编辑字段数据:', {
                    id: editableFieldsInput.id,
                    name: editableFieldsInput.name,
                    value: editableFieldsInput.value,
                    isJSON: editableFieldsInput.value.startsWith('[') || editableFieldsInput.value.startsWith('{')
                });
            } else {
                console.warn('⚠️ [提交前验证] 未找到可编辑字段隐藏输入框');
            }
            
            // 特别关注动作类型
            const actionTypeInput = form.querySelector('select[name="action_type"]') || 
                                   form.querySelector('#action_type') ||
                                   form.querySelector('#edit_action_type');
            if (actionTypeInput) {
                console.log('🔍 执行动作类型:', {
                    id: actionTypeInput.id,
                    name: actionTypeInput.name,
                    value: actionTypeInput.value,
                    selectedText: actionTypeInput.selectedOptions[0]?.text
                });
            }
            
            // 发送AJAX请求
            const response = await fetch(form.action, {
                method: form.method || 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                // 检查是否是409冲突错误
                if (response.status === 409) {
                    const errorData = await response.json();
                    console.log('⚠️ [调试] 服务器返回冲突错误:', errorData);
                    
                    // 隐藏加载状态
                    this.showFormLoading(form, false);
                    
                    // 如果服务器返回冲突信息，显示冲突对话框
                    if (errorData.conflict?.has_conflict) {
                        this.showConflictDialog(errorData.conflict);
                        return;
                    }
                }
                
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('✅ 表单提交成功:', result);
            
            // 处理成功响应
            this.handleFormSuccess(form, result);
            
        } catch (error) {
            console.error('❌ 表单提交失败:', error);
            this.handleFormError(form, error);
        } finally {
            // 隐藏加载状态
            this.showFormLoading(form, false);
        }
    }

    /**
     * 显示表单加载状态
     */
    showFormLoading(form, isLoading) {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            if (isLoading) {
                submitButton.disabled = true;
                const originalText = submitButton.textContent;
                submitButton.dataset.originalText = originalText;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 处理中...';
            } else {
                submitButton.disabled = false;
                const originalText = submitButton.dataset.originalText;
                if (originalText) {
                    submitButton.textContent = originalText;
                }
            }
        }
    }

    /**
     * 处理表单成功响应
     */
    handleFormSuccess(form, result) {
        if (result.success) {
            // 显示成功消息
            this.showSuccessMessage(result.message || '操作成功');
            
            // 关闭模态框 - 使用与现有代码一致的方式
            const modal = form.closest('.modal');
            if (modal) {
                this.hideModal(modal);
            }
            
            // 刷新页面数据 - 延迟执行确保模态框完全关闭
            setTimeout(() => {
                window.location.reload();
            }, 500);
            
        } else {
            // 显示服务器返回的错误消息
            this.showErrorMessage(result.message || '操作失败');
        }
    }

    /**
     * 处理表单错误响应
     */
    handleFormError(form, error) {
        const errorMessage = error.message || '网络错误，请重试';
        this.showErrorMessage(errorMessage);
    }

    /**
     * 显示成功消息
     */
    showSuccessMessage(message) {
        if (typeof window.showToast === 'function') {
            window.showToast('success', message);
        } else {
            alert('✅ ' + message);
        }
    }

    /**
     * 显示错误消息
     */
    showErrorMessage(message) {
        if (typeof window.showToast === 'function') {
            window.showToast('error', message);
        } else {
            alert('❌ ' + message);
        }
    }

    /**
     * 统一的点击事件处理
     */
    handleClick(event) {
        console.log('🔍 [调试] 点击事件触发:', {
            target: event.target.tagName + (event.target.className ? '.' + event.target.className.split(' ').join('.') : ''),
            targetText: event.target.textContent?.trim().substring(0, 50),
            targetDataset: event.target.dataset,
            hasAddStepText: event.target.textContent?.includes('添加步骤'),
            hasBsTarget: !!event.target.dataset.bsTarget,
            bsTargetValue: event.target.dataset.bsTarget
        });

        // 首先检查添加分支条件按钮
        if (event.target.closest('.branch-add-button')) {
            const button = event.target.closest('.branch-add-button');
            const stepId = button.dataset.stepId;
            
            event.preventDefault();
            this.addBranchCondition(stepId);
            return;
        }

        // 然后检查分支条件按钮（div元素）
        if (event.target.closest('.branch-step-button')) {
            const button = event.target.closest('.branch-step-button');
            const stepId = button.dataset.stepId;
            const conditionIndex = button.dataset.conditionIndex;
            const conditionId = button.dataset.conditionId; // 新表格式的条件ID
            
            // 检查是否是删除按钮
            if (event.target.closest('.delete-condition-btn')) {
                event.preventDefault();
                event.stopPropagation();
                const deleteBtn = event.target.closest('.delete-condition-btn');
                const stepId = deleteBtn.dataset.stepId;
                const conditionIndex = deleteBtn.dataset.conditionIndex;
                const conditionId = deleteBtn.dataset.conditionId; // 新表格式的条件ID
                this.confirmDeleteCondition(stepId, conditionIndex, conditionId);
                return;
            }
            
            this.editBranchCondition(stepId, conditionIndex, conditionId);
            return;
        }
        
        // 然后处理其他按钮和链接
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

        // 添加步骤按钮 - 只拦截模态框触发按钮，不拦截表单提交按钮
        if (target.dataset.bsTarget === '#addStepModal' ||
            (target.textContent && target.textContent.includes('添加步骤') && 
             target.type !== 'submit' && !target.closest('.modal'))) {
            
            console.log('🔍 [调试] 拦截添加步骤按钮，当前模态框状态:', {
                modalExists: !!document.getElementById('addStepModal'),
                modalVisible: document.getElementById('addStepModal')?.style.display,
                modalClasses: document.getElementById('addStepModal')?.className,
                existingBackdrops: document.querySelectorAll('.modal-backdrop').length,
                bodyHasModalOpen: document.body.classList.contains('modal-open')
            });
            
            event.preventDefault();
            console.log('🔧 拦截添加步骤按钮，使用自定义处理');
            
            const modal = document.getElementById('addStepModal');
            if (modal) {
                // 先清空表单数据，再显示模态框
                console.log('🧹 显示前清空添加步骤表单数据');
                this.resetAddStepModal();
                this.showModal(modal);
            } else {
                console.error('❌ 找不到添加步骤模态框');
            }
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

        // 模态框关闭按钮
        if (target.classList.contains('modal-close-btn')) {
            event.preventDefault();
            const modal = target.closest('.modal');
            if (modal) {
                console.log('🔧 手动关闭模态框:', modal.id);
                this.hideModal(modal);
            }
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
     * 确认删除步骤 - 使用通用确认对话框组件
     */
    confirmDeleteStep(stepId, stepName) {
        if (typeof window.showConfirmDialog === 'function') {
            window.showConfirmDialog({
                title: '确认删除审批步骤',
                message: `确定要删除步骤 "${stepName || '该步骤'}" 吗？\n\n删除后无法恢复，快照机制保护运行中流程不受影响。`,
                type: 'danger',
                confirmText: '确认删除',
                cancelText: '取消',
                dialogId: 'stepDeleteDialog',
                onConfirm: () => this.executeDeleteStep(stepId)
            });
        } else {
            // 降级到原生确认对话框（向后兼容）
            if (confirm(`确认删除审批步骤\n\n确定要删除步骤 "${stepName || '该步骤'}" 吗？\n\n删除后无法恢复，快照机制保护运行中流程不受影响。`)) {
                this.executeDeleteStep(stepId);
            }
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
    confirmDeleteCondition(stepId, conditionIndex, conditionId = null) {
        if (typeof window.showConfirmDialog === 'function') {
            window.showConfirmDialog({
                title: '确认删除分支条件',
                message: '确定要删除此分支条件吗？\n\n删除后无法恢复。',
                type: 'danger',
                confirmText: '确认删除',
                cancelText: '取消',
                dialogId: 'branchDeleteDialog',
                onConfirm: () => this.executeDeleteCondition(stepId, conditionIndex, conditionId)
            });
        } else {
            if (confirm('确定要删除此分支条件吗？')) {
                this.executeDeleteCondition(stepId, conditionIndex, conditionId);
            }
        }
    }

    /**
     * 执行删除分支条件
     */
    async executeDeleteCondition(stepId, conditionIndex, conditionId = null) {
        console.log(`执行删除分支条件: 步骤${stepId}, 条件${conditionIndex}, ID${conditionId || '未设置'}`);
        
        try {
            let url;
            if (conditionId) {
                // 使用新表格式的删除API
                url = `/admin/approval/step/${stepId}/condition/by-id/${conditionId}/delete`;
                console.log('🆕 使用新表格式删除API:', url);
            } else {
                // 使用旧格式的删除API
                url = `/admin/approval/step/${stepId}/condition/${conditionIndex}/delete`;
                console.log('🔙 使用旧格式删除API:', url);
            }
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
                }
            });
            
            if (!response.ok) {
                throw new Error('网络请求失败');
            }
            
            const data = await response.json();
            if (data.success) {
                // 显示成功消息
                this.showSuccessMessage(data.message || '分支条件删除成功');
                
                // 延迟刷新页面以显示更新结果
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                this.showErrorMessage(data.message || '删除失败');
            }
        } catch (error) {
            console.error('删除分支条件失败:', error);
            this.showErrorMessage('网络错误，请重试');
        }
    }

    /**
     * 添加分支条件
     */
    addBranchCondition(stepId) {
        console.log(`添加分支条件: 步骤${stepId}`);
        
        // 使用编辑步骤模态框来添加分支条件
        const modal = document.getElementById('editStepModal');
        if (!modal) {
            console.error('找不到编辑步骤模态框');
            return;
        }

        // 获取步骤的分支条件统计信息
        this.loadStepBranchStats(stepId)
            .then(statsData => {
                // 计算新条件的索引（基于现有条件数量）
                const conditionIndex = statsData.conditions_count;
                console.log(`🔍 [调试] 准备添加第${conditionIndex + 1}个分支条件`);
                
                // 获取步骤数据以便预填充其他字段
                return this.loadStepData(stepId).then(stepApiData => {
                    return {
                        stats: statsData,
                        step: stepApiData.step,
                        conditionIndex: conditionIndex
                    };
                });
            })
            .then(data => {
                this.showAddBranchConditionModal(modal, stepId, data.step, data.stats, data.conditionIndex);
            })
            .catch(error => {
                console.error('加载分支条件数据失败:', error);
                // 降级处理：使用旧逻辑
                this.loadStepData(stepId)
                    .then(apiData => {
                        this.showAddBranchConditionModal(modal, stepId, apiData.step, null, 0);
                    })
                    .catch(() => {
                        this.showAddBranchConditionModal(modal, stepId, null, null, 0);
                    });
            });
    }

    /**
     * 显示添加分支条件模态框
     */
    showAddBranchConditionModal(modal, stepId, stepData, statsData, conditionIndex) {
        console.log(`🔍 [调试] 显示添加分支条件模态框: 步骤${stepId}, 条件索引${conditionIndex}`, {
            hasStatsData: !!statsData,
            conditionsCount: statsData?.conditions_count,
            unifiedField: statsData?.unified_field
        });
        
        // 重置表单
        this.resetEditForm(modal);
        
        // 设置表单为添加分支条件模式
        const form = modal.querySelector('#editStepForm');
        if (form) {
            form.action = `/admin/approval/step/${stepId}/edit`;
        }

        // 添加隐藏字段标识这是添加分支条件
        let hiddenInput = modal.querySelector('#edit_is_branch_condition_add');
        if (!hiddenInput) {
            hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.id = 'edit_is_branch_condition_add';
            hiddenInput.name = 'is_branch_condition_add';
            hiddenInput.value = 'true';
            form.appendChild(hiddenInput);
        }

        // 设置标题
        const title = modal.querySelector('.modal-title');
        if (title) {
            title.textContent = '添加分支条件';
        }

        // 计算条件序号并自动生成步骤名称
        const conditionNumber = conditionIndex + 1;
        const stepNameField = modal.querySelector('#edit_step_name');
        if (stepNameField) {
            stepNameField.value = `分支条件 ${conditionNumber}`;
            stepNameField.readOnly = true; // 设置为只读，不可编辑
        }

        // 添加模板信息隐藏字段（复用添加/编辑步骤的成熟机制）
        this.ensureTemplateFields(modal, form);

        // 设置步骤类型为分支并禁用编辑
        const stepTypeField = modal.querySelector('#edit_step_type');
        if (stepTypeField) {
            stepTypeField.value = 'branch';
            stepTypeField.disabled = true;
            // 触发变化事件显示分支配置区域
            const event = new Event('change');
            stepTypeField.dispatchEvent(event);
        }

        // 延迟处理分支条件字段的预加载和锁定
        setTimeout(() => {
            this.handleBranchFieldLockingForAdd(modal, stepId, conditionIndex, statsData);
        }, 500);

        // 显示模态框
        this.showModal(modal);
    }

    /**
     * 处理添加分支条件时的条件字段锁定逻辑
     */
    handleBranchFieldLockingForAdd(modal, stepId, conditionIndex, statsData) {
        const branchField = modal.querySelector('#edit_branch_field');
        if (!branchField) {
            console.warn('⚠️ 找不到分支条件字段选择器');
            return;
        }

        // 判断是否需要锁定条件字段
        const shouldLock = conditionIndex > 0; // 非第一个条件需要锁定
        const unifiedField = statsData?.unified_field;

        console.log(`🔍 [调试] 条件字段锁定判断: 条件索引=${conditionIndex}, 需要锁定=${shouldLock}, 统一字段=${unifiedField}`);

        if (shouldLock && unifiedField) {
            // 锁定字段并预填充
            branchField.value = unifiedField;
            branchField.disabled = true;
            branchField.style.backgroundColor = '#f8f9fa';
            branchField.style.cursor = 'not-allowed';
            
            // 添加锁定提示
            this.addFieldLockWarning(branchField, `第${conditionIndex + 1}个条件必须使用与第一个条件相同的字段`);
            
            console.log(`🔒 [调试] 已锁定条件字段: ${unifiedField}`);
            
        } else if (!shouldLock) {
            // 第一个条件可编辑
            branchField.disabled = false;
            branchField.style.backgroundColor = '';
            branchField.style.cursor = '';
            this.removeFieldLockWarning(branchField);
            
            console.log(`✅ [调试] 条件字段可编辑（第一个条件）`);
        }
    }

    /**
     * 加载步骤分支条件统计信息
     */
    async loadStepBranchStats(stepId) {
        try {
            const response = await fetch(`/admin/approval/step/${stepId}/branch-stats`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
                }
            });
            
            if (!response.ok) {
                throw new Error('网络请求失败');
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || '获取分支统计失败');
            }
            
            console.log(`🔍 [调试] 步骤${stepId}分支统计:`, data);
            return data;
            
        } catch (error) {
            console.error('加载分支统计失败:', error);
            throw error;
        }
    }

    /**
     * 加载分支字段锁定状态
     */
    async loadBranchFieldLockStatus(stepId, conditionIndex) {
        try {
            const response = await fetch(`/admin/approval/step/${stepId}/branch-lock-status/${conditionIndex}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
                }
            });
            
            if (!response.ok) {
                throw new Error('网络请求失败');
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || '获取锁定状态失败');
            }
            
            console.log(`🔍 [调试] 步骤${stepId}条件${conditionIndex}锁定状态:`, data);
            return data;
            
        } catch (error) {
            console.error('加载锁定状态失败:', error);
            throw error;
        }
    }

    /**
     * 添加字段锁定警告提示
     */
    addFieldLockWarning(fieldElement, message) {
        // 移除现有警告（如果有）
        this.removeFieldLockWarning(fieldElement);
        
        // 创建警告元素
        const warning = document.createElement('div');
        warning.className = 'field-lock-warning alert alert-info mt-2 mb-0';
        warning.innerHTML = `
            <i class="fas fa-lock"></i>
            <small>${message}</small>
        `;
        warning.id = `lock-warning-${fieldElement.id}`;
        
        // 插入到字段后面
        fieldElement.parentNode.insertBefore(warning, fieldElement.nextSibling);
    }

    /**
     * 移除字段锁定警告提示
     */
    removeFieldLockWarning(fieldElement) {
        const warningId = `lock-warning-${fieldElement.id}`;
        const existingWarning = document.getElementById(warningId);
        if (existingWarning) {
            existingWarning.remove();
        }
    }

    /**
     * 为编辑模式应用分支字段锁定逻辑
     */
    async applyBranchFieldLockingForEdit(branchField, stepId, conditionIndex) {
        try {
            console.log(`🔍 [调试] 应用编辑模式字段锁定: 步骤${stepId}, 条件索引${conditionIndex}`);
            
            // 获取锁定状态
            const lockData = await this.loadBranchFieldLockStatus(stepId, conditionIndex);
            
            if (lockData.should_lock) {
                // 锁定字段
                branchField.disabled = true;
                branchField.style.backgroundColor = '#f8f9fa';
                branchField.style.cursor = 'not-allowed';
                branchField.title = lockData.lock_reason || '字段已锁定';
                
                // 添加锁定提示
                this.addFieldLockWarning(branchField, lockData.lock_reason);
                
                console.log(`🔒 [调试] 已锁定编辑模式字段: ${lockData.lock_reason}`);
                
            } else {
                // 解锁字段
                branchField.disabled = false;
                branchField.style.backgroundColor = '';
                branchField.style.cursor = '';
                branchField.title = '';
                
                // 移除锁定提示
                this.removeFieldLockWarning(branchField);
                
                console.log(`✅ [调试] 编辑模式字段可编辑: ${lockData.lock_reason}`);
            }
            
        } catch (error) {
            console.error('应用字段锁定失败:', error);
            // 出错时默认可编辑
            branchField.disabled = false;
            branchField.style.backgroundColor = '';
            branchField.style.cursor = '';
            this.removeFieldLockWarning(branchField);
        }
    }

    /**
     * 确保模态框包含template_id和object_type隐藏字段
     * 复用添加/编辑步骤的成熟机制
     */
    ensureTemplateFields(modal, form) {
        console.log('🔍 [调试] ensureTemplateFields 开始');

        // 尝试从页面获取模板信息
        const templateId = this.getTemplateIdFromPage();
        const objectType = this.getObjectTypeFromPage();

        console.log('🔍 [调试] 获取的模板信息:', {
            templateId: templateId,
            objectType: objectType
        });

        if (!templateId || !objectType) {
            console.warn('⚠️ [调试] 无法获取模板信息，可能影响字段值加载');
            return;
        }

        // 添加或更新 template_id 字段
        let templateInput = modal.querySelector('input[name="template_id"]');
        if (!templateInput) {
            templateInput = document.createElement('input');
            templateInput.type = 'hidden';
            templateInput.name = 'template_id';
            form.appendChild(templateInput);
            console.log('✅ [调试] 创建新的 template_id 隐藏字段');
        }
        templateInput.value = templateId;

        // 添加或更新 object_type 字段  
        let objectTypeInput = modal.querySelector('input[name="object_type"]');
        if (!objectTypeInput) {
            objectTypeInput = document.createElement('input');
            objectTypeInput.type = 'hidden';
            objectTypeInput.name = 'object_type';
            form.appendChild(objectTypeInput);
            console.log('✅ [调试] 创建新的 object_type 隐藏字段');
        }
        objectTypeInput.value = objectType;

        console.log('✅ [调试] 模板信息隐藏字段设置完成:', {
            templateId: templateInput.value,
            objectType: objectTypeInput.value
        });
    }

    /**
     * 从页面获取模板ID
     */
    getTemplateIdFromPage() {
        // 方法1: 从URL获取
        const urlMatch = window.location.pathname.match(/template\/(\d+)/);
        if (urlMatch) {
            return urlMatch[1];
        }

        // 方法2: 从页面的现有隐藏字段获取
        const existingInput = document.querySelector('input[name="template_id"]');
        if (existingInput && existingInput.value) {
            return existingInput.value;
        }

        // 方法3: 从页面数据属性获取
        const templateData = document.querySelector('[data-template-id]');
        if (templateData) {
            return templateData.dataset.templateId;
        }

        console.warn('⚠️ [调试] 无法从页面获取模板ID');
        return null;
    }

    /**
     * 从页面获取对象类型
     */
    getObjectTypeFromPage() {
        // 方法1: 从现有隐藏字段获取
        const existingInput = document.querySelector('input[name="object_type"]');
        if (existingInput && existingInput.value) {
            return existingInput.value;
        }

        // 方法2: 从页面数据属性获取
        const objectTypeData = document.querySelector('[data-object-type]');
        if (objectTypeData) {
            return objectTypeData.dataset.objectType;
        }

        console.warn('⚠️ [调试] 无法从页面获取对象类型');
        return null;
    }

    /**
     * 编辑分支条件
     */
    editBranchCondition(stepId, conditionIndex, conditionId = null) {
        console.log(`编辑分支条件: 步骤${stepId}, 条件${conditionIndex}, ID${conditionId || '未设置'}`);
        
        // 获取分支条件数据 - 根据是否有conditionId选择API端点
        this.loadBranchConditionData(stepId, conditionIndex, conditionId)
            .then(apiData => {
                console.log('📱 [调试] editBranchCondition接收到的数据:', apiData);
                // 使用现有的编辑步骤模态框
                this.showEditStepModalForBranchCondition(stepId, apiData, conditionIndex, conditionId);
            })
            .catch(error => {
                console.error('获取分支条件数据失败:', error);
                showConfirmDialog({
                    title: '数据加载失败',
                    message: '获取分支条件数据失败，请重试',
                    type: 'danger',
                    dialogId: 'branchErrorDialog',
                    confirmText: '确定',
                    showCancel: false
                });
            });
    }

    /**
     * 加载步骤数据 - 用于编辑步骤表单
     */
    async loadStepData(stepId) {
        try {
            const response = await fetch(`/admin/approval/step/${stepId}/data`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
                }
            });
            
            if (!response.ok) {
                throw new Error('网络请求失败');
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || '获取步骤数据失败');
            }
            
            return data;
            
        } catch (error) {
            console.error('加载步骤数据失败:', error);
            throw error;
        }
    }

    /**
     * 加载分支条件数据
     */
    async loadBranchConditionData(stepId, conditionIndex, conditionId = null) {
        try {
            let url;
            if (conditionId) {
                // 使用新表格式的API（基于条件ID）
                url = `/admin/approval/step/${stepId}/condition/by-id/${conditionId}/data`;
                console.log('🆕 使用新表格式API:', url);
            } else {
                // 使用旧格式的API（基于索引）
                url = `/admin/approval/step/${stepId}/condition/${conditionIndex}/data`;
                console.log('🔙 使用旧格式API:', url);
            }
            
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
                }
            });
            
            if (!response.ok) {
                throw new Error('网络请求失败');
            }
            
            const data = await response.json();
            console.log('🌐 [调试] API完整响应:', data);
            console.log('📋 [调试] 条件数据:', data.condition);
            console.log('🔧 [调试] 步骤数据:', data.step);
            
            if (!data.success) {
                throw new Error(data.message || '获取数据失败');
            }
            
            // 注意：这里应该返回完整的数据，不只是condition
            return data;
        } catch (error) {
            console.error('加载分支条件数据错误:', error);
            throw error;
        }
    }

    /**
     * 为分支条件编辑显示编辑步骤模态框
     */
    showEditStepModalForBranchCondition(stepId, apiData, conditionIndex, conditionId) {
        console.log('📱 [调试] 模态框接收到的数据:', apiData);
        console.log('📱 [调试] 数据结构检查:', {
            hasCondition: !!apiData.condition,
            hasStep: !!apiData.step,
            stepFields: apiData.step?.editable_fields,
            conditionValue: apiData.condition?.value,
            conditionDisplayValue: apiData.condition?.display_value
        });
        
        const modal = document.getElementById('editStepModal');
        if (!modal) {
            console.error('❌ 找不到编辑步骤模态框');
            return;
        }

        // 设置模态框标题
        const title = modal.querySelector('.modal-title');
        if (title) {
            title.textContent = '编辑分支条件';
        }

        // 设置表单action - 优先使用条件ID路由
        const form = modal.querySelector('#editStepForm');
        if (form) {
            if (conditionId) {
                // 使用新表格式的API（基于条件ID）
                form.action = `/admin/approval/step/${stepId}/condition/by-id/${conditionId}/edit`;
                console.log('🔄 [调试] 使用条件ID路由:', form.action);
            } else {
                // 使用旧格式的API（基于索引）
                form.action = `/admin/approval/step/${stepId}/condition/${conditionIndex}/edit`;
                console.log('🔄 [调试] 使用条件索引路由:', form.action);
            }
        }

        // 填充分支条件数据
        this.populateBranchConditionForm(modal, apiData, stepId, conditionIndex, conditionId);
        
        // 显示模态框
        this.showModal(modal);
    }

    /**
     * 填充分支条件表单数据
     */
    populateBranchConditionForm(modal, apiData, stepId, conditionIndex, conditionId) {
        console.log('🔍 [调试] DOM元素存在性检查:', {
            modal: !!modal,
            branchField: !!modal.querySelector('#edit_branch_field'),
            branchOperator: !!modal.querySelector('#edit_branch_operator'), 
            branchValue: !!modal.querySelector('#edit_branch_value'),
            editableFieldsSelect: !!modal.querySelector('#edit_editable_fields_select'),
            selectedFieldsContainer: !!modal.querySelector('#edit_selected_fields'),
            sendEmail: !!modal.querySelector('#edit_send_email'),
            ccEnabled: !!modal.querySelector('#edit_cc_enabled')
        });
        
        // 从API数据中提取condition和step
        const conditionData = apiData.condition;
        const stepData = apiData.step;
        // 添加隐藏字段标识这是分支条件编辑
        let hiddenInput = modal.querySelector('#edit_branch_mode');
        if (!hiddenInput) {
            hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.id = 'edit_branch_mode';
            hiddenInput.name = 'branch_mode';
            hiddenInput.value = 'true';
            modal.querySelector('form').appendChild(hiddenInput);
        }

        let conditionIndexInput = modal.querySelector('#edit_condition_index');
        if (!conditionIndexInput) {
            conditionIndexInput = document.createElement('input');
            conditionIndexInput.type = 'hidden';
            conditionIndexInput.id = 'edit_condition_index';
            conditionIndexInput.name = 'condition_index';
            modal.querySelector('form').appendChild(conditionIndexInput);
        }
        conditionIndexInput.value = conditionIndex;

        // 填充基本数据
        const fields = {
            'edit_step_name': '分支条件 ' + (parseInt(conditionIndex) + 1),
            'edit_approver_selection': `user_${conditionData.approver_id}`,
            'edit_action_type': conditionData.action || conditionData.action_type,
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

        // 设置步骤类型为分支并禁用编辑
        const stepTypeField = modal.querySelector('#edit_step_type');
        if (stepTypeField) {
            stepTypeField.value = 'branch';
            stepTypeField.disabled = true;  // 禁用编辑
            stepTypeField.style.backgroundColor = '#f8f9fa';  // 视觉提示
            stepTypeField.style.cursor = 'not-allowed';
            // 触发变化事件显示分支配置区域
            const event = new Event('change');
            stepTypeField.dispatchEvent(event);
        }

        // 填充分支条件详细信息
        setTimeout(() => {
            const branchField = modal.querySelector('#edit_branch_field');
            const branchOperator = modal.querySelector('#edit_branch_operator');
            const branchValue = modal.querySelector('#edit_branch_value');

            if (branchField && conditionData.field) {
                // 详细调试条件字段赋值
                const availableOptions = Array.from(branchField.options).map(opt => ({
                    value: opt.value,
                    text: opt.textContent
                }));
                
                console.log('🔍 [调试] 条件字段赋值分析:', {
                    targetValue: conditionData.field,
                    availableOptions: availableOptions,
                    optionCount: branchField.options.length,
                    matchFound: !!branchField.querySelector(`option[value="${conditionData.field}"]`),
                    currentValue: branchField.value
                });
                
                branchField.value = conditionData.field;
                
                // 验证赋值是否成功
                console.log('🎯 [验证] 字段赋值结果:', {
                    expectedValue: conditionData.field,
                    actualValue: branchField.value,
                    assignmentSuccessful: branchField.value === conditionData.field
                });
                
                // 应用新的字段锁定逻辑
                this.applyBranchFieldLockingForEdit(branchField, stepId, conditionIndex);
            } else {
                console.warn('⚠️ [警告] 条件字段赋值失败:', {
                    hasBranchField: !!branchField,
                    hasFieldData: !!conditionData.field,
                    fieldData: conditionData.field
                });
            }
            if (branchOperator && conditionData.operator) {
                // 操作符映射：数据库存储值 -> 前端显示值
                const operatorMapping = {
                    'equals': 'from_field_list',  // 对于枚举字段，equals对应"从字段列表选择"
                    'not_equals': 'not_equals',
                    'contains': 'contains',
                    'not_contains': 'not_contains',
                    'greater_than': 'greater_than',
                    'less_than': 'less_than',
                    'in': 'in_list',
                    'not_in': 'not_in_list',
                    'starts_with': 'starts_with',
                    'ends_with': 'ends_with'
                };
                
                // 检查字段类型，如果是project_type等枚举字段，使用特殊映射
                const fieldName = conditionData.field;
                let displayOperator = conditionData.operator;
                
                if (fieldName === 'project_type' && (conditionData.operator === 'equals' || conditionData.operator === 'in')) {
                    // 对于项目类型字段，equals 和 in 操作符都显示为字段列表选择
                    displayOperator = 'from_field_list';
                    console.log('🔄 [映射] 操作符映射:', conditionData.operator, '-> from_field_list (项目类型字段)');
                } else {
                    displayOperator = operatorMapping[conditionData.operator] || conditionData.operator;
                    console.log('🔄 [映射] 操作符映射:', conditionData.operator, '->', displayOperator);
                }
                
                branchOperator.value = displayOperator;
            }
            if (branchValue) {
                // 优先使用映射后的显示值，如果没有则使用原始值
                const valueToShow = conditionData.display_value || conditionData.value;
                
                console.log('🎯 [调试] 分支条件值设置:', {
                    field: conditionData.field,
                    original_value: conditionData.value,
                    display_value: conditionData.display_value,
                    final_value: valueToShow,
                    has_display_value: !!conditionData.display_value
                });
                
                branchValue.value = valueToShow;
                
                // 处理复选框回显（针对从字段列表选择的情况）
                if (branchOperator && branchOperator.value === 'from_field_list') {
                    console.log('🔍 检测到字段列表选择，准备回显复选框');
                    this.loadEditConditionValues(conditionData, 'edit_');
                }
            }
        }, 100);
        
        // 加载可编辑字段配置
        if (stepData && stepData.editable_fields && stepData.editable_fields.length > 0) {
            console.log('⚙️ [调试] 准备加载可编辑字段:', {
                fieldCount: stepData.editable_fields.length,
                fields: stepData.editable_fields
            });
            
            // 直接加载，移除延迟调用（与主要修复保持一致）
            console.log('⚙️ [调试] 分支条件表单 - 直接加载字段（移除延迟）:', {
                selector: !!document.getElementById('edit_editable_fields_select'),
                container: !!document.getElementById('edit_selected_fields')
            });
            this.populateEditableFields(stepData.editable_fields, true);
            console.log('✅ [调试] 分支条件可编辑字段加载完成');
        } else {
            console.log('❌ [调试] 无可编辑字段数据:', {
                hasStep: !!stepData,
                hasFields: !!(stepData?.editable_fields),
                fieldCount: stepData?.editable_fields?.length || 0
            });
        }
        
        // 加载其他步骤配置
        if (stepData) {
            console.log('🔧 [调试] 加载其他步骤配置:', {
                sendEmail: stepData.send_email,
                ccEnabled: stepData.cc_enabled,
                ccUsers: stepData.cc_users
            });
            
            // 邮件发送配置
            const sendEmailField = modal.querySelector('#edit_send_email');
            if (sendEmailField) {
                sendEmailField.checked = stepData.send_email || false;
                console.log('📧 [调试] 邮件发送配置已设置:', stepData.send_email);
            }
            
            // 抄送开关配置
            const ccEnabledField = modal.querySelector('#edit_cc_enabled');
            if (ccEnabledField) {
                ccEnabledField.checked = stepData.cc_enabled || false;
                console.log('📬 [调试] 抄送开关已设置:', stepData.cc_enabled);
            }
            
            // CC用户配置（如果有对应的多选框）
            if (stepData.cc_users && stepData.cc_users.length > 0) {
                const ccUsersSelect = modal.querySelector('#edit_cc_users');
                if (ccUsersSelect && ccUsersSelect.multiple) {
                    // 清空现有选择
                    Array.from(ccUsersSelect.options).forEach(option => {
                        option.selected = stepData.cc_users.includes(parseInt(option.value));
                    });
                    console.log('👥 [调试] CC用户配置已设置:', stepData.cc_users);
                }
            }
        } else {
            console.log('❌ [调试] 无步骤配置数据');
        }
    }

    /**
     * 处理编辑步骤 - 使用API获取完整数据（增强调试版）
     */
    handleEditStep(stepData) {
        console.log('🔧 [编辑调试] 开始处理编辑步骤:', stepData);
        
        const modal = document.getElementById('editStepModal');
        if (!modal) {
            console.error('❌ [编辑调试] 找不到编辑步骤模态框');
            return;
        }

        console.log('🔧 [编辑调试] 模态框元素检查:', {
            hasModal: !!modal,
            modalId: modal.id,
            isVisible: modal.style.display !== 'none'
        });

        // 使用API获取完整步骤数据
        console.log('📡 [编辑调试] 开始API调用获取步骤数据...');
        this.loadStepData(stepData.stepId)
            .then(apiData => {
                console.log('📡 [编辑调试] API调用成功，返回数据:', apiData);
                console.log('🔧 [编辑调试] 准备填充表单（不包括可编辑字段）...');
                this.populateEditFormFromAPI(modal, apiData.step, false); // false = 暂时跳过可编辑字段
                console.log('🔧 [编辑调试] 准备显示模态框...');
                this.showModal(modal);
                console.log('🔧 [编辑调试] 模态框显示后，延迟处理可编辑字段...');
                // 使用Bootstrap模态框事件确保DOM完全可用
                $(modal).one('shown.bs.modal', () => {
                    console.log('🔧 [编辑调试] 模态框已完全显示，现在填充可编辑字段...');
                    
                    // 验证模态框DOM结构
                    validateModalDOMStructure(true);
                    
                    this.populateEditableFieldsAfterModalShown(apiData.step);
                });
                console.log('✅ [编辑调试] 编辑步骤处理完成');
            })
            .catch(error => {
                console.error('❌ [编辑调试] 加载步骤数据失败，使用降级方案:', error);
                console.log('🔧 [编辑调试] 使用降级方案填充表单...');
                this.populateEditForm(modal, stepData);
                this.showModal(modal);
                console.log('⚠️ [编辑调试] 降级处理完成');
            });
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
     * 统一的模态框显示方法 - 使用jQuery方式避免冲突
     */
    showModal(modal) {
        console.log('🔍 [调试] 显示模态框前状态:', {
            modalId: modal.id,
            modalDisplay: modal.style.display,
            modalClasses: modal.className,
            existingBackdrops: document.querySelectorAll('.modal-backdrop').length,
            bodyClasses: document.body.className.split(' '),
            jQueryAvailable: typeof $ !== 'undefined'
        });
        
        console.log('📋 显示模态框:', modal.id);
        
        try {
            if (typeof $ !== 'undefined') {
                $(modal).modal('show');
                console.log('✅ 使用jQuery显示模态框');
            } else {
                // 降级处理
                modal.style.display = 'block';
                modal.classList.add('show');
                modal.setAttribute('aria-hidden', 'false');
                document.body.classList.add('modal-open');
                console.log('✅ 使用原生方法显示模态框');
            }
            
            // 显示后状态检查
            setTimeout(() => {
                console.log('🔍 [调试] 显示模态框后状态:', {
                    modalDisplay: modal.style.display,
                    modalClasses: modal.className,
                    newBackdrops: document.querySelectorAll('.modal-backdrop').length,
                    visibleModals: document.querySelectorAll('.modal.show').length,
                    bodyClasses: document.body.className.split(' ')
                });
            }, 100);
            
        } catch (error) {
            console.error('❌ 显示模态框失败:', error);
        }
    }

    /**
     * 隐藏模态框
     */
    hideModal(modal) {
        console.log('🔧 隐藏模态框:', modal.id);
        
        try {
            if (typeof $ !== 'undefined') {
                $(modal).modal('hide');
                console.log('✅ 使用jQuery隐藏模态框');
            } else {
                // 降级处理
                modal.style.display = 'none';
                modal.classList.remove('show');
                modal.setAttribute('aria-hidden', 'true');
                document.body.classList.remove('modal-open');
                
                // 手动移除背景
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.remove();
                }
                console.log('✅ 使用原生方法隐藏模态框');
            }
        } catch (error) {
            console.error('❌ 隐藏模态框失败:', error);
        }
    }

    /**
     * 重置编辑表单
     */
    resetEditForm(modal) {
        console.log('🔧 resetEditForm: 调用完整的编辑模态框重置逻辑');
        
        // 直接调用完善的resetEditStepModal函数，避免重复代码
        this.resetEditStepModal();
        
        console.log('✅ resetEditForm: 已通过resetEditStepModal完成完整重置');
    }

    /**
     * 提取步骤数据 - 简化版本，只提取基本信息
     */
    extractStepData(button) {
        return {
            stepId: button.dataset.stepId,
            stepName: button.dataset.stepName
        };
    }

    /**
     * 填充编辑表单 - 使用API数据（优化版：统一加载逻辑）
     */
    populateEditFormFromAPI(modal, stepData, includeEditableFields = true) {
        console.log('🔧 [优化] 统一填充编辑表单 - 开始');
        console.log('🔧 [优化] 接收到的步骤数据:', stepData);
        
        // 🔍 [DOM调试] 检查模态框和核心DOM元素的渲染状态
        const modalVisible = modal && modal.offsetParent !== null;
        const editFieldsSelect = document.getElementById('edit_editable_fields_select');
        const editSelectedFields = document.getElementById('edit_selected_fields');
        const editFieldsInput = document.getElementById('edit_editable_fields_input');
        
        console.log('🔍 [DOM调试] 模态框渲染状态检查:', {
            模态框存在: !!modal,
            模态框可见: modalVisible,
            模态框ID: modal ? modal.id : null,
            字段选择器存在: !!editFieldsSelect,
            字段容器存在: !!editSelectedFields,
            隐藏输入存在: !!editFieldsInput,
            DOM准备就绪: document.readyState
        });
        
        // 先执行完整重置，确保从干净状态开始（解决模态框状态残留问题）
        this.resetEditStepModal();
        
        console.log('📋 [优化] 开始填充编辑表单数据');
        
        // 设置表单action
        const form = modal.querySelector('#editStepForm');
        if (form && stepData.id) {
            form.action = `/admin/approval/step/${stepData.id}/edit`;
            console.log('🔧 [优化] 设置表单action:', form.action);
        }

        // 填充基础字段
        const fields = {
            'edit_step_name': stepData.step_name,
            'edit_approver_selection': stepData.approver_type === 'next_level' ? 'next_level' : `user_${stepData.approver_user_id}`,
            'edit_action_type': stepData.action_type,
            'edit_send_email': stepData.send_email
        };
        
        console.log('🔧 [优化] 基础字段数据:', fields);

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

        // 填充可编辑字段 - 根据参数决定是否执行
        if (includeEditableFields && stepData.editable_fields && Array.isArray(stepData.editable_fields) && stepData.editable_fields.length > 0) {
            // 🔍 [DOM调试] 可编辑字段加载前的状态检查
            console.log('🔍 [DOM调试] 准备直接加载可编辑字段（移除延迟）:', {
                字段数据: stepData.editable_fields,
                字段数量: stepData.editable_fields.length,
                模态框状态: {
                    模态框存在: !!modal,
                    字段选择器可用: !!document.getElementById('edit_editable_fields_select'),
                    字段容器可用: !!document.getElementById('edit_selected_fields'),
                    隐藏输入可用: !!document.getElementById('edit_editable_fields_input')
                },
                当前时间: new Date().toISOString()
            });
            
            // 直接执行，移除延迟调用
            this.populateEditableFields(stepData.editable_fields, true);
        } else if (!includeEditableFields) {
            console.log('🔧 [编辑调试] 跳过可编辑字段填充，将在模态框显示后处理');
        } else {
            // 🔍 [DOM调试] 无可编辑字段的情况
            console.log('🔍 [DOM调试] 无可编辑字段数据:', {
                stepData_editable_fields: stepData.editable_fields,
                是否为数组: Array.isArray(stepData.editable_fields),
                数组长度: stepData.editable_fields ? stepData.editable_fields.length : 'N/A'
            });
            
            this.editSelectedFields = [];
            const container = modal.querySelector('#edit_selected_fields');
            if (container) {
                container.innerHTML = '<small class="text-muted">使用下拉框选择字段后会在此显示</small>';
            }
        }

        // 处理抄送相关字段
        if (stepData.cc_enabled === true || stepData.cc_enabled === 'true') {
            const ccCheckbox = modal.querySelector('#edit_cc_enabled');
            if (ccCheckbox) {
                ccCheckbox.checked = true;
            }
            
            // 设置抄送用户
            if (stepData.cc_users && stepData.cc_users.length > 0) {
                const ccUsersSelect = modal.querySelector('#edit_cc_users');
                if (ccUsersSelect && ccUsersSelect.multiple) {
                    Array.from(ccUsersSelect.options).forEach(option => {
                        option.selected = stepData.cc_users.includes(parseInt(option.value));
                    });
                }
            }
        }
    }

    /**
     * 填充编辑表单 - 使用DOM数据（降级方案）
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

        // 填充可编辑字段徽章 - 优化版：直接加载，无需setTimeout
        console.log('🔧 [优化] 开始处理可编辑字段:', {
            hasFields: !!(stepData?.editable_fields),
            isArray: Array.isArray(stepData?.editable_fields),
            length: stepData?.editable_fields?.length,
            data: stepData?.editable_fields
        });
        
        if (stepData.editable_fields && Array.isArray(stepData.editable_fields) && stepData.editable_fields.length > 0) {
            console.log('🔧 [优化] 直接加载可编辑字段 - 无延迟:', stepData.editable_fields);
            
            // 确保DOM已准备好
            const selector = modal.querySelector('#edit_editable_fields_select');
            const container = modal.querySelector('#edit_selected_fields');
            const hiddenInput = modal.querySelector('#edit_editable_fields_input');
            
            console.log('🔧 [优化] DOM元素检查:', {
                hasSelector: !!selector,
                hasContainer: !!container,
                hasHiddenInput: !!hiddenInput
            });
            
            if (selector && container && hiddenInput) {
                // 直接调用，不使用延迟
                this.populateEditableFields(stepData.editable_fields, true); // true 表示编辑模式
                console.log('🔧 [优化] 可编辑字段加载完成');
            } else {
                console.warn('⚠️ [优化] DOM元素缺失，无法加载可编辑字段');
            }
        } else {
            // 确保编辑字段区域为空状态
            console.log('🔧 [优化] 清空可编辑字段区域');
            this.editSelectedFields = [];
            const container = modal.querySelector('#edit_selected_fields');
            if (container) {
                container.innerHTML = '<small class="text-muted">使用下拉框选择字段后会在此显示</small>';
            }
            const hiddenInput = modal.querySelector('#edit_editable_fields_input');
            if (hiddenInput) {
                hiddenInput.value = '';
            }
        }

        // 处理抄送相关字段
        if (stepData.ccEnabled === 'true' || stepData.ccEnabled === true) {
            console.log('🔧 恢复抄送功能状态');
            const ccCheckbox = modal.querySelector('#edit_cc_enabled');
            if (ccCheckbox) {
                ccCheckbox.checked = true;
                // 显示抄送用户选择区域
                const ccSection = modal.querySelector('#edit_ccUsersSection');
                if (ccSection) {
                    ccSection.style.display = 'block';
                }
            }
        }
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

        // 添加模态框隐藏事件监听器
        this.setupModalHiddenEvents();

        // 可编辑字段选择事件（统一使用内置方法）
        const editableFieldSelects = document.querySelectorAll('#editable_fields_select, #edit_editable_fields_select');
        editableFieldSelects.forEach(select => {
            select.addEventListener('change', (event) => {
                if (event.target.value) {
                    if (event.target.id.includes('edit_')) {
                        this.addEditFieldBadge();
                    } else {
                        this.addFieldBadge();
                    }
                }
            });
        });
    }

    /**
     * 设置模态框隐藏事件监听器
     */
    setupModalHiddenEvents() {
        console.log('🔍 [调试] 设置模态框事件监听器开始');
        
        const addStepModal = document.getElementById('addStepModal');
        const editStepModal = document.getElementById('editStepModal');

        console.log('🔍 [调试] 模态框元素检查:', {
            addStepModalExists: !!addStepModal,
            editStepModalExists: !!editStepModal,
            jQueryAvailable: typeof $ !== 'undefined'
        });

        if (addStepModal) {
            console.log('🔍 [调试] 设置添加步骤模态框事件监听器');
            // 先解绑旧事件，避免重复绑定
            $(addStepModal).off('hidden.bs.modal');
            $(addStepModal).on('hidden.bs.modal', () => {
                console.log('🔧 添加步骤模态框隐藏，执行清理');
                setTimeout(() => this.resetAddStepModal(), 100);
            });
            
            // 添加显示事件监听
            $(addStepModal).off('shown.bs.modal');
            $(addStepModal).on('shown.bs.modal', () => {
                console.log('🔍 [调试] 添加步骤模态框已显示');
            });
        }

        if (editStepModal) {
            // 先解绑旧事件，避免重复绑定
            $(editStepModal).off('hidden.bs.modal');
            $(editStepModal).on('hidden.bs.modal', () => {
                console.log('🔧 编辑步骤模态框隐藏，执行清理');
                setTimeout(() => this.resetEditStepModal(), 100);
            });
        }

        console.log('🔍 [调试] 模态框事件监听器设置完成');
    }

    /**
     * 处理审批人选择
     */
    handleApproverSelection(event) {
        const select = event.target;
        const value = select.value;
        
        // 调试信息：记录审批人选择触发
        console.log('🔍 [调试] handleApproverSelection 触发:', {
            selectId: select.id,
            selectName: select.name,
            selectedValue: value,
            event: event
        });
        
        // 确定是添加还是编辑模式
        const isEditMode = select.id.includes('edit_');
        const infoSectionId = isEditMode ? 'edit_next_level_info_section' : 'next_level_info_section';
        
        console.log('🔍 [调试] 模式检测:', {
            isEditMode: isEditMode,
            infoSectionId: infoSectionId
        });
        
        // 显示/隐藏上级领导说明
        const infoSection = document.getElementById(infoSectionId);
        if (infoSection) {
            infoSection.style.display = value === 'next_level' ? 'block' : 'none';
        }

        // 更新隐藏字段
        console.log('🔍 [调试] 即将调用 updateHiddenApproverFields');
        this.updateHiddenApproverFields(select.closest('.modal, form'), value, isEditMode);
        console.log('🔍 [调试] handleApproverSelection 完成');
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
        // 保存当前选中的值
        const currentValue = selectElement.value;
        console.log('保存当前选中的字段值:', currentValue);
        
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
        
        // 恢复之前选中的值（如果该值在新选项中存在）
        if (currentValue) {
            // 检查当前值是否在新选项中存在
            const optionExists = Array.from(selectElement.options).some(option => option.value === currentValue);
            if (optionExists) {
                selectElement.value = currentValue;
                console.log('已恢复字段选中值:', currentValue);
            } else {
                console.warn('之前选中的字段值不存在于新选项中:', currentValue);
            }
        }
    }

    /**
     * 处理分支字段选择变化
     */
    handleBranchFieldChange(event) {
        console.log('🔍 [调试] handleBranchFieldChange 开始:', {
            event: event,
            target: event.target,
            targetId: event.target.id,
            targetValue: event.target.value
        });

        const select = event.target;
        const fieldName = select.value;
        const modal = select.closest('.modal');
        
        console.log('🔍 [调试] 字段选择详情:', {
            fieldName: fieldName,
            selectElement: select,
            modalElement: modal,
            modalId: modal ? modal.id : 'null'
        });

        try {
            // 根据字段类型更新操作符选项
            console.log('🔍 [调试] 开始更新操作符选项...');
            this.updateOperatorOptions(modal, fieldName);
            console.log('✅ [调试] 操作符选项更新完成');
            
            // 清空值输入框
            const fieldSelect = event.target;
            const prefix = fieldSelect.id.includes('edit_') ? 'edit_' : '';
            console.log('🔍 [调试] 字段前缀:', prefix);
            
            const valueInput = modal.querySelector(`#${prefix}branch_value`);
            console.log('🔍 [调试] 值输入框:', {
                selector: `#${prefix}branch_value`,
                element: valueInput,
                currentValue: valueInput ? valueInput.value : 'null'
            });
            
            if (valueInput) {
                valueInput.value = '';
                console.log('✅ [调试] 值输入框已清空');
            } else {
                console.warn('⚠️ [调试] 未找到值输入框');
            }
            
            console.log('✅ [调试] 分支字段选择变化处理完成:', fieldName);
        } catch (error) {
            console.error('❌ [调试] handleBranchFieldChange 处理失败:', error);
            console.error('❌ [调试] 错误详情:', {
                message: error.message,
                stack: error.stack,
                fieldName: fieldName,
                modal: modal
            });
        }
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
        console.log('🔍 [调试] updateOperatorOptions 开始:', {
            fieldName: fieldName,
            modal: modal,
            timestamp: new Date().toLocaleTimeString()
        });

        const fieldSelect = modal.querySelector('#branch_field, #edit_branch_field');
        console.log('🔍 [调试] 字段选择器查找结果:', {
            fieldSelect: fieldSelect,
            fieldSelectId: fieldSelect ? fieldSelect.id : null
        });

        const prefix = fieldSelect && fieldSelect.id.includes('edit_') ? 'edit_' : '';
        console.log('🔍 [调试] 确定前缀:', {
            prefix: prefix,
            isEditMode: fieldSelect ? fieldSelect.id.includes('edit_') : false
        });

        const operatorSelectId = `#${prefix}branch_operator`;
        const operatorSelect = modal.querySelector(operatorSelectId);
        console.log('🔍 [调试] 操作符选择器查找结果:', {
            operatorSelectId: operatorSelectId,
            operatorSelect: operatorSelect,
            operatorSelectExists: !!operatorSelect
        });

        if (!operatorSelect) {
            console.error('❌ [调试] 操作符选择器未找到');
            return;
        }
        
        // 清空现有选项
        operatorSelect.innerHTML = '';
        console.log('✅ [调试] 操作符选择器已清空');
        
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
            console.log('🔍 [调试] 识别为数值字段');
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
            console.log('🔍 [调试] 识别为枚举字段 (project_type等)');
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
            console.log('🔍 [调试] 识别为日期字段');
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
            console.log('🔍 [调试] 识别为文本字段');
        }
        
        console.log('🔍 [调试] 可用操作符列表:', {
            operators: operators,
            operatorCount: operators.length
        });
        
        // 添加选项
        operators.forEach(([value, text]) => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = text;
            operatorSelect.appendChild(option);
        });

        console.log('✅ [调试] updateOperatorOptions 完成:', {
            totalOptionsAdded: operators.length,
            operatorSelectOptionsCount: operatorSelect.options.length
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
     * 根据选择的值数量智能确定操作符
     * 用于"从字段列表选择"场景的智能操作符判断
     */
    determineOperatorBySelection(prefix = '') {
        const operatorSelect = document.querySelector(`#${prefix}branch_operator`);
        if (!operatorSelect || operatorSelect.value !== 'from_field_list') {
            return operatorSelect ? operatorSelect.value : 'equals'; // 非字段列表选择，直接返回当前值
        }
        
        // 获取选中的复选框
        const fieldValuesContainer = document.querySelector(`#${prefix}field_values_container`);
        if (!fieldValuesContainer) {
            console.log('🔍 determineOperatorBySelection: 未找到字段值容器');
            return 'equals'; // 默认精确匹配
        }
        
        const checkedBoxes = fieldValuesContainer.querySelectorAll('input[type="checkbox"]:checked');
        const selectedCount = checkedBoxes.length;
        
        console.log('🔍 determineOperatorBySelection: 选中数量 =', selectedCount);
        
        if (selectedCount === 1) {
            console.log('✅ 单选 → 使用 equals 操作符');
            return 'equals';  // 单选使用精确匹配
        } else if (selectedCount > 1) {
            console.log('✅ 多选 → 使用 in 操作符');
            return 'in';      // 多选使用包含匹配
        } else {
            console.log('ℹ️  未选择 → 默认使用 equals 操作符');
            return 'equals';  // 默认精确匹配
        }
    }

    /**
     * 获取选中的字段值（支持单选和多选）
     */
    getSelectedFieldValues(prefix = '') {
        const fieldValuesContainer = document.querySelector(`#${prefix}field_values_container`);
        if (!fieldValuesContainer) {
            return [];
        }
        
        const checkedBoxes = fieldValuesContainer.querySelectorAll('input[type="checkbox"]:checked');
        const selectedValues = Array.from(checkedBoxes).map(checkbox => checkbox.value);
        
        console.log('🔍 getSelectedFieldValues: 选中的值 =', selectedValues);
        return selectedValues;
    }

    /**
     * 设置复选框选中状态（用于编辑时的值回显）
     */
    setCheckboxSelection(selectedValues, prefix = '') {
        const fieldValuesContainer = document.querySelector(`#${prefix}field_values_container`);
        if (!fieldValuesContainer) {
            console.log('🔍 setCheckboxSelection: 未找到字段值容器');
            return;
        }
        
        // 确保selectedValues是数组
        const valuesArray = Array.isArray(selectedValues) ? selectedValues : [selectedValues];
        console.log('🔍 setCheckboxSelection: 要选中的值 =', valuesArray);
        
        // 清除所有选中状态
        const allCheckboxes = fieldValuesContainer.querySelectorAll('input[type="checkbox"]');
        allCheckboxes.forEach(checkbox => checkbox.checked = false);
        
        // 设置选中状态
        valuesArray.forEach(value => {
            if (value) {
                const checkbox = fieldValuesContainer.querySelector(`input[type="checkbox"][value="${value}"]`);
                if (checkbox) {
                    checkbox.checked = true;
                    console.log('✅ setCheckboxSelection: 已选中', value);
                } else {
                    console.log('⚠️ setCheckboxSelection: 未找到复选框', value);
                }
            }
        });
        
        // 更新隐藏字段的值
        const hiddenInput = document.querySelector(`#${prefix}branch_value`);
        if (hiddenInput) {
            hiddenInput.value = valuesArray.join(',');
            console.log('🔍 setCheckboxSelection: 更新隐藏字段值 =', hiddenInput.value);
        }
    }

    /**
     * 根据操作符和值设置编辑时的复选框状态
     */
    loadEditConditionValues(conditionData, prefix = '') {
        if (!conditionData.value) {
            console.log('🔍 loadEditConditionValues: 无值需要回显');
            return;
        }
        
        console.log('🔍 loadEditConditionValues: 开始回显', {
            operator: conditionData.operator,
            value: conditionData.value
        });
        
        // 等待复选框加载完成
        setTimeout(() => {
            if (conditionData.operator === 'equals') {
                // 单选：只选中一个值
                this.setCheckboxSelection([conditionData.value], prefix);
                console.log('✅ loadEditConditionValues: equals 单选回显完成');
            } else if (conditionData.operator === 'in') {
                // 多选：选中逗号分隔的多个值
                const values = conditionData.value.split(',').map(v => v.trim()).filter(v => v);
                this.setCheckboxSelection(values, prefix);
                console.log('✅ loadEditConditionValues: in 多选回显完成', values);
            } else {
                console.log('ℹ️ loadEditConditionValues: 其他操作符，不处理复选框');
            }
        }, 800); // 等待字段值加载完成
    }

    /**
     * 加载字段值选项（用于从字段列表选择）
     */
    loadFieldValues(prefix = '') {
        console.log('🔍 [调试] loadFieldValues 开始:', {
            prefix: prefix,
            timestamp: new Date().toLocaleTimeString()
        });

        const modal = document.querySelector('.modal.show') || document.querySelector('.modal');
        console.log('🔍 [调试] 查找模态框:', {
            modal: modal,
            modalClassList: modal ? Array.from(modal.classList) : null
        });

        if (!modal) {
            console.warn('⚠️ [调试] 未找到打开的模态框');
            return;
        }
        
        const fieldSelect = modal.querySelector(`#${prefix}branch_field`);
        const fieldName = fieldSelect ? fieldSelect.value : '';
        
        console.log('🔍 [调试] 字段选择元素状态:', {
            fieldSelectId: `#${prefix}branch_field`,
            fieldSelect: fieldSelect,
            fieldName: fieldName,
            fieldSelectValue: fieldSelect ? fieldSelect.value : 'N/A'
        });
        
        if (!fieldName) {
            console.warn('⚠️ [调试] 字段名为空，显示错误消息');
            this.showFieldValuesError(prefix, '请先选择条件字段');
            return;
        }
        
        const container = modal.querySelector(`#${prefix}field_values_container`);
        console.log('🔍 [调试] 字段值容器:', {
            containerId: `#${prefix}field_values_container`,
            container: container,
            containerExists: !!container
        });

        if (!container) {
            console.warn('⚠️ [调试] 字段值容器未找到');
            return;
        }
        
        // 显示加载状态
        container.innerHTML = `
            <div class="text-center">
                <i class="fas fa-spinner fa-spin"></i> 加载字段值选项中...
            </div>
        `;
        console.log('✅ [调试] 已设置加载状态');
        
        // 获取模板信息
        const templateIdInput = modal.querySelector('input[name="template_id"]');
        const templateId = templateIdInput ? templateIdInput.value : '';
        
        console.log('🔍 [调试] 模板信息:', {
            templateIdInput: templateIdInput,
            templateId: templateId,
            templateInputExists: !!templateIdInput
        });
        
        if (!templateId) {
            console.warn('⚠️ [调试] 模板ID为空');
            this.showFieldValuesError(prefix, '无法获取模板信息');
            return;
        }
        
        const apiUrl = `/admin/approval/field-values?template_id=${templateId}&field_name=${fieldName}`;
        console.log('🔍 [调试] 准备发起API请求 (使用成熟的字段值获取API):', {
            url: apiUrl,
            templateId: templateId,
            fieldName: fieldName,
            note: '复用现有的成熟API，已支持project_type等枚举字段'
        });
        
        // 调用API获取字段值（使用成熟的字段值获取API）
        fetch(apiUrl, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            }
        })
        .then(response => {
            console.log('🔍 [调试] API响应状态:', {
                status: response.status,
                statusText: response.statusText,
                ok: response.ok
            });
            return response.json();
        })
        .then(data => {
            console.log('🔍 [调试] API响应数据:', {
                data: data,
                success: data.success,
                values: data.values,
                valuesLength: data.values ? data.values.length : 0,
                message: data.message
            });

            if (data.success && data.values) {
                console.log('✅ [调试] API请求成功，准备渲染字段值');
                this.renderFieldValuesCheckboxes(prefix, data.values, fieldName);
            } else {
                console.error('❌ [调试] API请求失败或无数据:', data.message || '获取字段值失败');
                this.showFieldValuesError(prefix, data.message || '获取字段值失败');
            }
        })
        .catch(error => {
            console.error('❌ [调试] API请求异常:', {
                error: error,
                message: error.message,
                stack: error.stack
            });
            this.showFieldValuesError(prefix, '网络错误，请重试');
        });
    }

    /**
     * 渲染字段值复选框
     */
    renderFieldValuesCheckboxes(prefix, values, fieldName) {
        console.log('🔍 [调试] renderFieldValuesCheckboxes 开始:', {
            prefix: prefix,
            values: values,
            fieldName: fieldName,
            valuesType: typeof values,
            valuesLength: values ? values.length : 0
        });

        const container = document.querySelector(`#${prefix}field_values_container`);
        console.log('🔍 [调试] 渲染容器状态:', {
            containerId: `#${prefix}field_values_container`,
            container: container,
            containerExists: !!container
        });

        if (!container) {
            console.error('❌ [调试] 渲染容器未找到');
            return;
        }

        if (!values || values.length === 0) {
            console.warn('⚠️ [调试] 字段值为空或无数据:', {
                values: values,
                valuesIsArray: Array.isArray(values),
                valuesLength: values ? values.length : 0
            });
            this.showFieldValuesError(prefix, '该字段暂无可选值');
            return;
        }
        
        let html = ``;
        console.log('🔍 [调试] 开始生成复选框HTML...');
        
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
        
        console.log('🔍 [调试] 生成的HTML长度:', html.length);
        console.log('🔍 [调试] 准备设置容器HTML内容...');
        
        container.innerHTML = html;
        
        console.log('✅ [调试] 字段值复选框渲染完成:', {
            containerHTML: container.innerHTML.substring(0, 100) + '...',
            checkboxCount: container.querySelectorAll('.field-value-checkbox').length
        });
    }

    /**
     * 显示字段值加载错误
     */
    showFieldValuesError(prefix, message) {
        console.log('🔍 [调试] showFieldValuesError 调用:', {
            prefix: prefix,
            message: message
        });

        const container = document.querySelector(`#${prefix}field_values_container`);
        console.log('🔍 [调试] 错误显示容器:', {
            containerId: `#${prefix}field_values_container`,
            container: container,
            containerExists: !!container
        });

        if (container) {
            container.innerHTML = `
                <div class="text-center text-danger">
                    <i class="fas fa-exclamation-triangle"></i> ${message}
                </div>
            `;
            console.log('✅ [调试] 错误消息已设置:', message);
        } else {
            console.error('❌ [调试] 错误显示容器未找到');
        }
    }

    /**
     * 更新选中的字段值
     */
    updateSelectedFieldValues(prefix) {
        console.log('🔍 [调试] updateSelectedFieldValues 开始:', {
            prefix: prefix,
            timestamp: new Date().toLocaleTimeString()
        });

        const checkboxesSelector = `#${prefix}field_values_container .field-value-checkbox:checked`;
        console.log('🔍 [调试] 复选框选择器:', checkboxesSelector);

        const checkboxes = document.querySelectorAll(checkboxesSelector);
        console.log('🔍 [调试] 选中的复选框:', {
            selector: checkboxesSelector,
            checkboxes: checkboxes,
            checkboxCount: checkboxes.length,
            checkboxList: Array.from(checkboxes).map(cb => ({
                id: cb.id,
                value: cb.value,
                checked: cb.checked
            }))
        });

        const selectedValues = Array.from(checkboxes).map(cb => cb.value);
        console.log('🔍 [调试] 提取的选中值:', {
            selectedValues: selectedValues,
            valuesCount: selectedValues.length
        });
        
        const hiddenInputSelector = `#${prefix}branch_value`;
        const hiddenInput = document.querySelector(hiddenInputSelector);
        console.log('🔍 [调试] 隐藏输入字段:', {
            selector: hiddenInputSelector,
            hiddenInput: hiddenInput,
            hiddenInputExists: !!hiddenInput
        });

        if (hiddenInput) {
            const joinedValue = selectedValues.join(',');
            hiddenInput.value = joinedValue;
            console.log('✅ [调试] 隐藏字段值已更新:', {
                oldValue: hiddenInput.value,
                newValue: joinedValue
            });
        } else {
            console.error('❌ [调试] 隐藏输入字段未找到');
        }
        
        console.log('✅ [调试] updateSelectedFieldValues 完成:', {
            finalSelectedValues: selectedValues,
            hiddenInputValue: hiddenInput ? hiddenInput.value : 'N/A'
        });
    }

    /**
     * 创建字段徽章HTML
     */
    createFieldBadge(fieldCode, fieldName, group = 'master') {
        const groupColor = group === 'master' ? '#007bff' : '#28a745';
        const groupLabel = group === 'master' ? '主' : '明';
        return `<span class="badge me-1 mb-1" style="background-color: ${groupColor}; color: white; font-size: 0.8rem;" data-field="${fieldCode}">
            <small>${groupLabel}</small> ${fieldName} 
            <i class="fas fa-times ms-1" style="cursor: pointer;" onclick="window.approvalConfig.removeFieldBadge('${fieldCode}')"></i>
        </span>`;
    }

    /**
     * 创建编辑字段徽章HTML
     */
    createEditFieldBadge(fieldCode, fieldName, group = 'master') {
        const groupColor = group === 'master' ? '#007bff' : '#28a745';
        const groupLabel = group === 'master' ? '主' : '明';
        return `<span class="badge me-1 mb-1" style="background-color: ${groupColor}; color: white; font-size: 0.8rem;" data-field="${fieldCode}">
            <small>${groupLabel}</small> ${fieldName} 
            <i class="fas fa-times ms-1" style="cursor: pointer;" onclick="window.approvalConfig.removeEditFieldBadge('${fieldCode}')"></i>
        </span>`;
    }

    /**
     * 添加字段徽章（添加步骤）
     */
    addFieldBadge() {
        // 🔍 [对比调试] 添加模式 - 字段徽章添加开始
        console.log('🔍 [对比调试] 添加模式字段徽章添加:', {
            函数: 'addFieldBadge()',
            模式: '添加步骤',
            时间: new Date().toISOString()
        });
        
        // 支持新版组件化模态框的ID
        const selector = document.getElementById('editable_fields_select') || document.getElementById('field_selector');
        const container = document.getElementById('selected_fields') || document.getElementById('selected_fields_container');
        const hiddenInput = document.getElementById('editable_fields_input');
        
        // 🔍 [对比调试] 添加模式 - DOM元素状态
        console.log('🔍 [对比调试] 添加模式DOM检查:', {
            选择器存在: !!selector,
            选择器ID: selector ? selector.id : null,
            选择器选项数量: selector ? selector.options.length : 0,
            容器存在: !!container,
            隐藏输入存在: !!hiddenInput,
            选择器当前值: selector ? selector.value : null
        });
        
        if (!selector || !selector.value) return;
        
        const fieldCode = selector.value;
        const selectedOption = selector.options[selector.selectedIndex];
        const fieldName = selectedOption.textContent;
        const group = selectedOption.getAttribute('data-group') || 'master';
        
        // 检查是否已选择
        if (this.selectedFields.includes(fieldCode)) {
            showConfirmDialog({
                title: '字段重复',
                message: '该字段已经选择，请选择其他字段',
                type: 'warning',
                dialogId: 'branchWarningDialog',
                confirmText: '确定',
                showCancel: false
            });
            selector.value = '';
            return;
        }
        
        // 添加到数组
        this.selectedFields.push(fieldCode);
        
        // 移除提示文本
        const placeholder = container.querySelector('.text-muted');
        if (placeholder) {
            placeholder.remove();
        }
        
        // 添加徽章
        container.insertAdjacentHTML('beforeend', this.createFieldBadge(fieldCode, fieldName, group));
        
        // 更新隐藏字段
        if (hiddenInput) {
            hiddenInput.value = JSON.stringify(this.selectedFields);
            
            // 🔍 调试：记录字段添加操作
            console.log('🔍 [添加字段] 已添加字段:', {
                fieldCode: fieldCode,
                fieldName: fieldName,
                currentFields: [...this.selectedFields],
                hiddenInputValue: hiddenInput.value
            });
        }
        
        // 重置选择器
        selector.value = '';
    }

    /**
     * 移除字段徽章（添加步骤）
     */
    removeFieldBadge(fieldCode) {
        // 支持新版组件化模态框的ID
        const container = document.getElementById('selected_fields') || document.getElementById('selected_fields_container');
        const hiddenInput = document.getElementById('editable_fields_input');
        
        // 从数组中移除
        this.selectedFields = this.selectedFields.filter(code => code !== fieldCode);
        
        // 移除对应的徽章
        const badge = container.querySelector(`[data-field="${fieldCode}"]`);
        if (badge) {
            badge.remove();
        }
        
        // 如果没有选中字段了，显示提示文本
        if (this.selectedFields.length === 0) {
            container.innerHTML = '<small class="text-muted">使用下拉框选择字段后会在此显示</small>';
        }
        
        // 更新隐藏字段
        if (hiddenInput) {
            hiddenInput.value = JSON.stringify(this.selectedFields);
        }
    }

    /**
     * 添加字段徽章（编辑步骤）
     */
    addEditFieldBadge() {
        // 🔍 [对比调试] 编辑模式 - 字段徽章添加开始
        console.log('🔍 [对比调试] 编辑模式字段徽章添加:', {
            函数: 'addEditFieldBadge()',
            模式: '编辑步骤',
            时间: new Date().toISOString()
        });
        
        // 支持新版组件化模态框的ID
        const selector = document.getElementById('edit_editable_fields_select') || document.getElementById('edit_field_selector');
        const container = document.getElementById('edit_selected_fields') || document.getElementById('edit_selected_fields_container');
        const hiddenInput = document.getElementById('edit_editable_fields_input');
        
        // 🔍 [对比调试] 编辑模式 - DOM元素状态
        const allOptions = selector ? Array.from(selector.options || []) : [];
        console.log('🔍 [对比调试] 编辑模式DOM检查:', {
            选择器存在: !!selector,
            选择器ID: selector ? selector.id : null,
            选择器选项数量: selector ? selector.options.length : 0,
            所有选项详情: allOptions.map(opt => ({
                value: opt.value,
                text: opt.textContent,
                group: opt.getAttribute('data-group')
            })),
            容器存在: !!container,
            隐藏输入存在: !!hiddenInput,
            选择器当前值: selector ? selector.value : null,
            当前已选字段: [...(this.editSelectedFields || [])]
        });
        
        if (!selector || !selector.value) return;
        
        const fieldCode = selector.value;
        const selectedOption = selector.options[selector.selectedIndex];
        const fieldName = selectedOption.textContent;
        const group = selectedOption.getAttribute('data-group') || 'master';
        
        // 检查是否已选择
        if (this.editSelectedFields.includes(fieldCode)) {
            showConfirmDialog({
                title: '字段重复',
                message: '该字段已经选择，请选择其他字段',
                type: 'warning',
                dialogId: 'branchWarningDialog',
                confirmText: '确定',
                showCancel: false
            });
            selector.value = '';
            return;
        }
        
        // 添加到数组
        this.editSelectedFields.push(fieldCode);
        
        // 移除提示文本
        const placeholder = container.querySelector('.text-muted');
        if (placeholder) {
            placeholder.remove();
        }
        
        // 添加徽章
        container.insertAdjacentHTML('beforeend', this.createEditFieldBadge(fieldCode, fieldName, group));
        
        // 更新隐藏字段
        if (hiddenInput) {
            hiddenInput.value = JSON.stringify(this.editSelectedFields);
            
            // 🔍 调试：记录编辑字段添加操作
            console.log('🔍 [编辑-添加字段] 已添加字段:', {
                fieldCode: fieldCode,
                fieldName: fieldName,
                currentFields: [...this.editSelectedFields],
                hiddenInputValue: hiddenInput.value
            });
        }
        
        // 重置选择器
        selector.value = '';
    }

    /**
     * 移除编辑字段徽章
     */
    removeEditFieldBadge(fieldCode) {
        // 支持新版组件化模态框的ID
        const container = document.getElementById('edit_selected_fields') || document.getElementById('edit_selected_fields_container');
        const hiddenInput = document.getElementById('edit_editable_fields_input');
        
        // 从数组中移除
        this.editSelectedFields = this.editSelectedFields.filter(code => code !== fieldCode);
        
        // 移除对应的徽章
        const badge = container.querySelector(`[data-field="${fieldCode}"]`);
        if (badge) {
            badge.remove();
        }
        
        // 如果没有选中字段了，显示提示文本
        if (this.editSelectedFields.length === 0) {
            container.innerHTML = '<small class="text-muted">使用下拉框选择字段后会在此显示</small>';
        }
        
        // 更新隐藏字段
        if (hiddenInput) {
            hiddenInput.value = JSON.stringify(this.editSelectedFields);
        }
    }

    /**
     * 填充可编辑字段徽章（编辑模式数据加载）
     */
    populateEditableFields(fieldCodes, isEdit = false) {
        const selector = document.getElementById(isEdit ? 'edit_editable_fields_select' : 'editable_fields_select');
        const container = document.getElementById(isEdit ? 'edit_selected_fields' : 'selected_fields');
        let hiddenInput = document.getElementById(isEdit ? 'edit_editable_fields_input' : 'editable_fields_input');
        
        // 🔍 [DOM调试] 检查DOM元素状态和模态框完整性
        const modalElement = document.getElementById('editStepModal');
        const allHiddenInputsInModal = modalElement ? modalElement.querySelectorAll('input[type="hidden"]') : [];
        const debugComment = modalElement ? modalElement.innerHTML.includes('DEBUG: is_edit=') : false;
        
        console.log('🔍 [DOM调试] populateEditableFields DOM元素检查:', {
            isEdit: isEdit,
            selectorId: isEdit ? 'edit_editable_fields_select' : 'editable_fields_select',
            containerId: isEdit ? 'edit_selected_fields' : 'selected_fields',
            hiddenInputId: isEdit ? 'edit_editable_fields_input' : 'editable_fields_input',
            hasSelector: !!selector,
            hasContainer: !!container,
            hasHiddenInput: !!hiddenInput,
            // 🔍 新增：模态框完整性检查
            modalExists: !!modalElement,
            modalVisible: modalElement ? modalElement.offsetParent !== null : false,
            modalDisplay: modalElement ? modalElement.style.display : 'unknown',
            modalClasses: modalElement ? modalElement.className : 'unknown',
            allHiddenInputsCount: allHiddenInputsInModal.length,
            allHiddenInputsIds: Array.from(allHiddenInputsInModal).map(input => input.id),
            // 🔍 详细查找特定ID
            directQueryResult: !!document.querySelector('#edit_editable_fields_input'),
            querySelectorAllResult: document.querySelectorAll('input[id="edit_editable_fields_input"]').length
        });
        
        if (!selector || !container || !hiddenInput) {
            console.error('❌ populateEditableFields: 缺少必要的DOM元素，详细检查:', {
                selector_exists: !!selector,
                selector_value: selector,
                container_exists: !!container, 
                container_value: container,
                hiddenInput_exists: !!hiddenInput,
                hiddenInput_value: hiddenInput,
                isEdit: isEdit,
                查找的ID: {
                    selectorId: isEdit ? 'edit_editable_fields_select' : 'editable_fields_select',
                    containerId: isEdit ? 'edit_selected_fields' : 'selected_fields', 
                    hiddenInputId: isEdit ? 'edit_editable_fields_input' : 'editable_fields_input'
                }
            });
            
            // 🛠️ [应急修复] 如果只是隐藏输入字段缺失，尝试动态创建
            if (selector && container && !hiddenInput && isEdit) {
                console.warn('⚠️ [应急修复] 编辑模式隐藏输入字段缺失，尝试动态创建...');
                
                const form = document.getElementById('editStepForm');
                if (form) {
                    const newHiddenInput = document.createElement('input');
                    newHiddenInput.type = 'hidden';
                    newHiddenInput.id = 'edit_editable_fields_input';
                    newHiddenInput.name = 'editable_fields';
                    newHiddenInput.value = '';
                    
                    form.appendChild(newHiddenInput);
                    
                    console.log('✅ [应急修复] 已动态创建隐藏输入字段:', {
                        id: newHiddenInput.id,
                        name: newHiddenInput.name,
                        parentForm: form.id
                    });
                    
                    // 重新获取隐藏输入字段并继续执行
                    const dynamicHiddenInput = document.getElementById('edit_editable_fields_input');
                    if (dynamicHiddenInput) {
                        // 继续执行函数的其余部分，使用动态创建的字段
                        hiddenInput = dynamicHiddenInput;
                        console.log('🔧 [应急修复] 使用动态创建的隐藏字段继续执行');
                        
                        // 验证修复后的DOM结构
                        setTimeout(() => {
                            validateModalDOMStructure(isEdit);
                            console.log('✅ [应急修复] 验证完成，隐藏字段现在存在:', !!document.getElementById('edit_editable_fields_input'));
                        }, 100);
                    } else {
                        console.error('❌ [应急修复] 动态创建隐藏字段失败，DOM查找失败');
                        // 再次尝试查找，可能有延迟
                        setTimeout(() => {
                            const retryHiddenInput = document.getElementById('edit_editable_fields_input');
                            if (retryHiddenInput) {
                                hiddenInput = retryHiddenInput;
                                console.log('✅ [应急修复] 延迟查找成功，继续执行');
                            } else {
                                console.error('❌ [应急修复] 最终失败，无法找到或创建隐藏字段');
                                return;
                            }
                        }, 200);
                    }
                } else {
                    console.error('❌ [应急修复] 找不到editStepForm表单，无法创建隐藏字段');
                    return;
                }
            } else {
                // 其他情况下直接返回
                return;
            }
        }
        
        // 🔍 [DOM调试] 记录下拉框中所有可用的选项
        const allOptions = Array.from(selector.options || []);
        console.log('🔍 [DOM调试] 下拉框中所有可用选项:', {
            totalOptions: allOptions.length,
            options: allOptions.map(option => ({
                value: option.value,
                text: option.textContent,
                group: option.getAttribute('data-group'),
                parentLabel: option.parentElement.label || 'no-group'
            }))
        });
        
        // 数据验证和清理
        let cleanFieldCodes = [];
        if (Array.isArray(fieldCodes)) {
            cleanFieldCodes = fieldCodes.filter(code => typeof code === 'string' && code.trim() !== '');
        } else if (typeof fieldCodes === 'string') {
            // 尝试解析字符串格式的数据
            try {
                const parsed = JSON.parse(fieldCodes);
                if (Array.isArray(parsed)) {
                    cleanFieldCodes = parsed.filter(code => typeof code === 'string' && code.trim() !== '');
                } else {
                    console.error('❌ 解析后不是数组格式:', parsed);
                    return;
                }
            } catch (e) {
                console.error('❌ 无法解析字段代码:', fieldCodes, e);
                return;
            }
        } else {
            console.error('❌ 无效的字段代码格式:', fieldCodes);
            return;
        }
        
        console.log('🔍 [调试] populateEditableFields 处理字段:', {
            original: fieldCodes,
            cleaned: cleanFieldCodes,
            isEdit: isEdit
        });
        
        // 清空容器并重置数组
        container.innerHTML = '';
        if (isEdit) {
            this.editSelectedFields = [];
        } else {
            this.selectedFields = [];
        }
        
        // 为每个字段代码创建徽章
        cleanFieldCodes.forEach((fieldCode, index) => {
            // 🔍 [字段调试] 开始处理单个字段代码
            console.log(`🔍 [字段调试] 处理字段 ${index + 1}/${cleanFieldCodes.length}:`, {
                fieldCode: fieldCode,
                type: typeof fieldCode,
                length: fieldCode.length
            });
            
            // 使用更安全的选择器查询方式
            try {
                // 转义特殊字符以防止CSS选择器错误
                const escapedFieldCode = CSS.escape(fieldCode);
                const selectorString = `option[value="${escapedFieldCode}"]`;
                
                // 🔍 [字段调试] 记录查找过程
                console.log(`🔍 [字段调试] 查找选项元素:`, {
                    原始字段代码: fieldCode,
                    转义后字段代码: escapedFieldCode,
                    CSS选择器: selectorString,
                    下拉框元素: !!selector
                });
                
                const option = selector.querySelector(selectorString);
                
                // 🔍 [字段调试] 记录查找结果
                console.log(`🔍 [字段调试] 选项查找结果:`, {
                    fieldCode: fieldCode,
                    找到选项: !!option,
                    选项文本: option ? option.textContent : null,
                    选项值: option ? option.value : null,
                    选项分组: option ? option.getAttribute('data-group') : null
                });
                
                if (option) {
                    const fieldName = option.textContent;
                    const group = option.getAttribute('data-group') || 'master';
                    
                    // 🔍 [字段调试] 成功找到字段选项
                    console.log(`🔍 [字段调试] 成功创建字段徽章:`, {
                        fieldCode: fieldCode,
                        fieldName: fieldName,
                        group: group,
                        isEdit: isEdit
                    });
                    
                    // 添加到数组
                    if (isEdit) {
                        this.editSelectedFields.push(fieldCode);
                        container.insertAdjacentHTML('beforeend', this.createEditFieldBadge(fieldCode, fieldName, group));
                    } else {
                        this.selectedFields.push(fieldCode);
                        container.insertAdjacentHTML('beforeend', this.createFieldBadge(fieldCode, fieldName, group));
                    }
                } else {
                    // 🔍 [字段调试] 找不到选项的详细调试
                    console.warn('⚠️ [字段调试] 找不到字段选项，进行详细分析:', {
                        fieldCode: fieldCode,
                        escapedFieldCode: escapedFieldCode,
                        selectorString: selectorString,
                        所有可用选项值: allOptions.map(opt => opt.value),
                        可能匹配的选项: allOptions.filter(opt => 
                            opt.value.includes(fieldCode) || fieldCode.includes(opt.value)
                        ).map(opt => ({
                            value: opt.value,
                            text: opt.textContent
                        }))
                    });
                }
            } catch (e) {
                console.error('❌ 处理字段代码时出错:', fieldCode, e);
            }
        });
        
        // 🔍 [字段调试] 最终结果汇总
        const finalSelectedFields = isEdit ? this.editSelectedFields : this.selectedFields;
        console.log('🔍 [字段调试] 字段填充完成汇总:', {
            isEdit: isEdit,
            原始字段: fieldCodes,
            清理后字段: cleanFieldCodes,
            成功加载字段: finalSelectedFields,
            成功率: `${finalSelectedFields.length}/${cleanFieldCodes.length}`,
            隐藏字段值: JSON.stringify(finalSelectedFields)
        });
        
        // 更新隐藏字段
        hiddenInput.value = JSON.stringify(finalSelectedFields);
        
        // 🔍 [字段调试] 验证隐藏输入字段值设置
        console.log('🔍 [字段调试] 隐藏输入字段验证:', {
            hiddenInput_element: hiddenInput,
            hiddenInput_id: hiddenInput.id,
            hiddenInput_name: hiddenInput.name,
            设置前的值: hiddenInput.getAttribute('value'),
            设置后的值: hiddenInput.value,
            设置后的getAttribute: hiddenInput.getAttribute('value'),
            DOM中实际值: document.getElementById(hiddenInput.id)?.value,
            字段数组长度: finalSelectedFields.length
        });
    }

    /**
     * 在模态框显示后填充可编辑字段（修复DOM时机问题）
     */
    populateEditableFieldsAfterModalShown(stepData) {
        console.log('🔧 [模态框后调试] 开始在模态框显示后填充可编辑字段');
        
        if (stepData.editable_fields && Array.isArray(stepData.editable_fields) && stepData.editable_fields.length > 0) {
            // 🔍 [DOM调试] 模态框显示后的状态检查
            console.log('🔍 [模态框后调试] 模态框显示后的DOM状态:', {
                字段数据: stepData.editable_fields,
                字段数量: stepData.editable_fields.length,
                模态框完全显示: true,
                DOM状态: {
                    字段选择器存在: !!document.getElementById('edit_editable_fields_select'),
                    字段容器存在: !!document.getElementById('edit_selected_fields'),
                    隐藏输入存在: !!document.getElementById('edit_editable_fields_input')
                },
                当前时间: new Date().toISOString()
            });
            
            // 在模态框完全显示后调用
            this.populateEditableFields(stepData.editable_fields, true);
            console.log('✅ [模态框后调试] 模态框显示后字段填充完成');
        } else {
            console.log('❌ [模态框后调试] 无可编辑字段数据，跳过填充');
        }
    }

    /**
     * 为步骤列表渲染字段徽章（复用模态框逻辑）
     * @param {Array} fieldCodes - 字段代码数组
     * @param {string} containerId - 容器元素ID
     * @param {string} templateId - 模板ID（用于获取字段选项）
     */
    renderFieldBadgesFromCodes(fieldCodes, containerId, templateId) {
        const container = document.getElementById(containerId);
        if (!container) {
            return;
        }

        // 如果没有字段代码，显示空状态
        if (!fieldCodes || fieldCodes.length === 0) {
            container.innerHTML = '<small class="text-muted">暂无可编辑字段</small>';
            return;
        }

        // 获取字段选项数据（复用现有API）
        this.getFieldOptionsForDisplay(templateId)
            .then(fieldOptions => {
                // 清空容器
                container.innerHTML = '';
                
                // 为每个字段代码创建徽章
                fieldCodes.forEach(fieldCode => {
                    const fieldInfo = this.getFieldInfoFromOptions(fieldCode, fieldOptions);
                    if (fieldInfo) {
                        const badgeHtml = this.createDisplayFieldBadge(fieldCode, fieldInfo.name, fieldInfo.group);
                        container.insertAdjacentHTML('beforeend', badgeHtml);
                    } else {
                        // 使用字段代码作为显示名称的后备方案
                        const badgeHtml = this.createDisplayFieldBadge(fieldCode, fieldCode, 'master');
                        container.insertAdjacentHTML('beforeend', badgeHtml);
                    }
                });
            })
            .catch(error => {
                console.error('字段徽章渲染失败:', error);
                // 降级到简单显示
                container.innerHTML = '';
                fieldCodes.forEach(fieldCode => {
                    const badgeHtml = this.createDisplayFieldBadge(fieldCode, fieldCode, 'master');
                    container.insertAdjacentHTML('beforeend', badgeHtml);
                });
            });
    }

    /**
     * 获取字段选项数据用于显示
     * @param {string} templateId - 模板ID
     * @returns {Promise} 字段选项数据
     */
    async getFieldOptionsForDisplay(templateId) {
        try {
            const response = await fetch(`/admin/approval/template/${templateId}/field-options`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            if (data.success) {
                return data.field_options;
            } else {
                throw new Error(data.message || '获取字段选项失败');
            }
        } catch (error) {
            console.error('字段选项API请求失败:', error);
            throw error;
        }
    }

    /**
     * 从字段选项中获取字段信息
     * @param {string} fieldCode - 字段代码
     * @param {Object} fieldOptions - 字段选项数据
     * @returns {Object|null} 字段信息 {name, group}
     */
    getFieldInfoFromOptions(fieldCode, fieldOptions) {
        if (!fieldOptions) return null;

        // 支持新格式：{master: [...], detail: [...]}
        if (fieldOptions.master && Array.isArray(fieldOptions.master)) {
            const masterField = fieldOptions.master.find(item => 
                Array.isArray(item) && item.length >= 2 && item[0] === fieldCode
            );
            if (masterField) {
                return { name: masterField[1], group: 'master' };
            }
        }

        if (fieldOptions.detail && Array.isArray(fieldOptions.detail)) {
            const detailField = fieldOptions.detail.find(item => 
                Array.isArray(item) && item.length >= 2 && item[0] === fieldCode
            );
            if (detailField) {
                return { name: detailField[1], group: 'detail' };
            }
        }

        // 支持旧格式：直接数组
        if (Array.isArray(fieldOptions)) {
            const field = fieldOptions.find(item => 
                Array.isArray(item) && item.length >= 2 && item[0] === fieldCode
            );
            if (field) {
                return { name: field[1], group: 'master' };
            }
        }

        return null;
    }

    /**
     * 创建显示专用的字段徽章HTML（无删除按钮）
     * @param {string} fieldCode - 字段代码
     * @param {string} fieldName - 字段显示名称
     * @param {string} group - 字段分组 ('master' 或 'detail')
     * @returns {string} 徽章HTML
     */
    createDisplayFieldBadge(fieldCode, fieldName, group = 'master') {
        const groupColor = group === 'master' ? '#007bff' : '#28a745';
        const groupLabel = group === 'master' ? '主' : '明';
        return `<span class="badge me-1 mb-1" style="background-color: ${groupColor}; color: white; font-size: 0.8rem;" data-field="${fieldCode}">
            <small>${groupLabel}</small> ${fieldName}
        </span>`;
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

            // 如果关闭抄送，清空所有选中的用户
            if (!checkbox.checked) {
                const checkboxes = ccSection.querySelectorAll('.cc-user-checkbox');
                checkboxes.forEach(cb => cb.checked = false);
                this.updateCcUserBadges(prefix);
            }
        }
    }

    /**
     * 更新抄送用户徽章显示
     */
    updateCcUserBadges(prefix = '') {
        const badgesContainer = document.querySelector(`#${prefix}selectedCcUsersBadges`);
        const checkboxes = document.querySelectorAll(`#${prefix}ccUsersList .cc-user-checkbox:checked`);

        if (!badgesContainer) return;

        // 清空现有徽章
        badgesContainer.innerHTML = '';

        if (checkboxes.length === 0) {
            badgesContainer.innerHTML = '<small class="text-muted">未选择任何用户</small>';
            return;
        }

        // 添加每个选中用户的徽章
        checkboxes.forEach(checkbox => {
            const username = checkbox.getAttribute('data-username');
            const userId = checkbox.value;

            const badge = document.createElement('span');
            badge.className = 'badge bg-info text-white me-2 mb-1';
            badge.style.fontSize = '0.875rem';
            badge.innerHTML = `
                ${username}
                <i class="fas fa-times ms-1"
                   style="cursor: pointer;"
                   onclick="window.approvalConfig.removeCcUser('${prefix}', '${userId}')"></i>
            `;

            badgesContainer.appendChild(badge);
        });
    }

    /**
     * 移除抄送用户
     */
    removeCcUser(prefix, userId) {
        const checkbox = document.querySelector(`#${prefix}cc_user_${userId}`);
        if (checkbox) {
            checkbox.checked = false;
            this.updateCcUserBadges(prefix);
        }
    }

    /**
     * 过滤抄送用户列表
     */
    filterCcUsers(prefix = '') {
        const searchInput = document.querySelector(`#${prefix}ccUserSearch`);
        const userItems = document.querySelectorAll(`#${prefix}ccUsersList .cc-user-item`);

        if (!searchInput || !userItems.length) return;

        const searchText = searchInput.value.toLowerCase();

        userItems.forEach(item => {
            const userName = item.getAttribute('data-user-name');
            if (!searchText || userName.includes(searchText)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
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

        // 调试信息：记录映射过程
        console.log('🔍 [调试] updateHiddenApproverFields 开始:', {
            value: value,
            isEditMode: isEditMode,
            prefix: prefix,
            container: container,
            containerId: container ? container.id : 'no container',
            approverTypeField: approverTypeField,
            approverIdField: approverIdField,
            approverTypeFieldFound: !!approverTypeField,
            approverIdFieldFound: !!approverIdField
        });

        // 详细调试：查找字段的过程
        console.log('🔍 [调试] 字段查找详情:');
        console.log('  查找ID:', `#${prefix}approver_type`, '结果:', container.querySelector(`#${prefix}approver_type`));
        console.log('  查找name:', '[name="approver_type"]', '结果:', container.querySelector('[name="approver_type"]'));
        console.log('  查找ID:', `#${prefix}approver_id`, '结果:', container.querySelector(`#${prefix}approver_id`));
        console.log('  查找name:', '[name="approver_id"]', '结果:', container.querySelector('[name="approver_id"]'));
        
        // 检查容器内所有input元素
        const allInputs = container.querySelectorAll('input');
        console.log('🔍 [调试] 容器内所有input元素:', Array.from(allInputs).map(input => ({
            id: input.id,
            name: input.name,
            type: input.type,
            value: input.value
        })));

        if (value === 'next_level') {
            if (approverTypeField) {
                approverTypeField.value = 'next_level';
                console.log('🔍 [调试] 设置 approver_type = next_level');
            }
            if (approverIdField) {
                approverIdField.value = '';
                console.log('🔍 [调试] 设置 approver_id = ""');
            }
        } else if (value.startsWith('user_')) {
            const userId = value.replace('user_', '');
            console.log('🔍 [调试] 解析用户ID:', userId);
            
            if (approverTypeField) {
                approverTypeField.value = 'user';
                console.log('🔍 [调试] 设置 approver_type = user');
            }
            if (approverIdField) {
                approverIdField.value = userId;
                console.log('🔍 [调试] 设置 approver_id =', userId);
            }
        }

        // 调试信息：记录映射结果
        console.log('🔍 [调试] updateHiddenApproverFields 完成:', {
            approver_type_final: approverTypeField ? approverTypeField.value : 'field not found',
            approver_id_final: approverIdField ? approverIdField.value : 'field not found'
        });
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

    /**
     * 重置添加步骤模态框
     */
    resetAddStepModal() {
        console.log('🔍 [调试] 重置添加步骤模态框 - 开始');
        
        const modal = document.getElementById('addStepModal');
        if (!modal) {
            console.warn('⚠️ 找不到添加步骤模态框');
            return;
        }

        console.log('🔍 [调试] 重置前模态框状态:', {
            exists: !!modal,
            display: modal.style.display,
            classes: modal.className,
            formElementsCount: modal.querySelectorAll('input, select, textarea').length,
            selectedFieldsArrayLength: this.selectedFields.length,
            branchConfigVisible: modal.querySelector('#branchConfigSection')?.style.display,
            ccSectionVisible: modal.querySelector('#ccUsersSection')?.style.display
        });

        // 重置基本表单字段
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
            console.log('✅ 表单已重置');
        }

        // 清空字段徽章和重置状态
        this.selectedFields = [];
        const selectedFieldsContainer = modal.querySelector('#selected_fields');
        if (selectedFieldsContainer) {
            selectedFieldsContainer.innerHTML = '<small class="text-muted">使用下拉框选择字段后会在此显示</small>';
        }

        // 重置隐藏字段
        const hiddenInput = modal.querySelector('#editable_fields_input');
        if (hiddenInput) {
            hiddenInput.value = '';
        }

        // 重置审批人相关隐藏字段
        const approverTypeField = modal.querySelector('#approver_type');
        if (approverTypeField) {
            approverTypeField.value = 'user';
        }
        const approverIdField = modal.querySelector('#approver_id');
        if (approverIdField) {
            approverIdField.value = '';
        }

        // 重置步骤类型为默认值（normal）
        const stepTypeSelect = modal.querySelector('#step_type');
        if (stepTypeSelect) {
            stepTypeSelect.value = 'normal';
        }

        // 隐藏分支条件配置区域
        const branchConfigSection = modal.querySelector('#branchConfigSection');
        if (branchConfigSection) {
            branchConfigSection.style.display = 'none';
        }

        // 隐藏上级领导说明区域
        const nextLevelInfoSection = modal.querySelector('#next_level_info_section');
        if (nextLevelInfoSection) {
            nextLevelInfoSection.style.display = 'none';
        }

        // 隐藏并重置抄送区域
        const ccUsersSection = modal.querySelector('#ccUsersSection');
        if (ccUsersSection) {
            ccUsersSection.style.display = 'none';
        }
        
        // 重置抄送启用开关
        const ccEnabledCheckbox = modal.querySelector('#cc_enabled');
        if (ccEnabledCheckbox) {
            ccEnabledCheckbox.checked = false;
        }

        // 重置分支条件相关字段
        const branchValueContainer = modal.querySelector('#branchValueContainer');
        if (branchValueContainer) {
            branchValueContainer.innerHTML = '<input type="text" class="form-control" id="branch_value" name="branch_value" placeholder="请输入比较值">';
        }

        // 重置分支条件选择框
        const branchFieldSelect = modal.querySelector('#branch_field');
        if (branchFieldSelect) {
            branchFieldSelect.selectedIndex = 0;
        }
        const branchOperatorSelect = modal.querySelector('#branch_operator');
        if (branchOperatorSelect) {
            branchOperatorSelect.selectedIndex = 0;
        }

        // 重置邮件通知开关为默认状态（开启）
        const sendEmailCheckbox = modal.querySelector('#send_email');
        if (sendEmailCheckbox) {
            sendEmailCheckbox.checked = true;
        }

        // 清除抄送用户多选框的选择
        const ccUsersSelect = modal.querySelector('#cc_users');
        if (ccUsersSelect) {
            ccUsersSelect.selectedIndex = -1; // 清空所有选择
        }

        console.log('🔍 [调试] 重置后模态框状态:', {
            display: modal.style.display,
            classes: modal.className,
            selectedFieldsArrayLength: this.selectedFields.length,
            branchConfigVisible: modal.querySelector('#branchConfigSection')?.style.display,
            ccSectionVisible: modal.querySelector('#ccUsersSection')?.style.display,
            stepTypeValue: modal.querySelector('#step_type')?.value,
            approverSelectionValue: modal.querySelector('#approver_selection')?.value
        });

        console.log('🔍 [调试] 重置添加步骤模态框 - 完成');
    }

    /**
     * 重置编辑步骤模态框（增强调试版）
     */
    resetEditStepModal() {
        console.log('🔧 [编辑调试] 重置编辑步骤模态框 - 开始完善重置逻辑');
        
        const modal = document.getElementById('editStepModal');
        if (!modal) {
            console.warn('⚠️ [编辑调试] 找不到编辑步骤模态框');
            return;
        }

        // 详细记录重置前状态
        const editableFieldsInput = modal.querySelector('#edit_editable_fields_input');
        console.log('🔍 [编辑调试] 重置前编辑模态框状态:', {
            exists: !!modal,
            display: modal.style.display,
            classes: modal.className,
            formElementsCount: modal.querySelectorAll('input, select, textarea').length,
            editSelectedFieldsArrayLength: this.editSelectedFields?.length || 0,
            editSelectedFieldsArray: [...(this.editSelectedFields || [])],
            hiddenInputValue: editableFieldsInput?.value || '',
            branchConfigVisible: modal.querySelector('#edit_branchConfigSection')?.style.display,
            ccSectionVisible: modal.querySelector('#edit_ccUsersSection')?.style.display
        });

        // 重置基本表单字段
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
            console.log('✅ 表单已重置');
        }

        // 清空编辑字段徽章和重置状态
        this.editSelectedFields = [];
        const editSelectedFieldsContainer = modal.querySelector('#edit_selected_fields');
        if (editSelectedFieldsContainer) {
            editSelectedFieldsContainer.innerHTML = '<small class="text-muted">使用下拉框选择字段后会在此显示</small>';
        }

        // 重置隐藏字段
        const editHiddenInput = modal.querySelector('#edit_editable_fields_input');
        if (editHiddenInput) {
            editHiddenInput.value = '';
        }

        // 重置审批人相关隐藏字段
        const editApproverTypeField = modal.querySelector('#edit_approver_type');
        if (editApproverTypeField) {
            editApproverTypeField.value = 'user';
        }
        const editApproverIdField = modal.querySelector('#edit_approver_id');
        if (editApproverIdField) {
            editApproverIdField.value = '';
        }

        // 重置步骤类型为默认值（normal）
        const editStepTypeSelect = modal.querySelector('#edit_step_type');
        if (editStepTypeSelect) {
            editStepTypeSelect.value = 'normal';
        }

        // 隐藏分支条件配置区域
        const editBranchConfigSection = modal.querySelector('#edit_branchConfigSection');
        if (editBranchConfigSection) {
            editBranchConfigSection.style.display = 'none';
        }

        // 隐藏上级领导说明区域
        const editNextLevelInfoSection = modal.querySelector('#edit_next_level_info_section');
        if (editNextLevelInfoSection) {
            editNextLevelInfoSection.style.display = 'none';
        }

        // 隐藏并重置抄送区域
        const editCcUsersSection = modal.querySelector('#edit_ccUsersSection');
        if (editCcUsersSection) {
            editCcUsersSection.style.display = 'none';
        }
        
        // 重置抄送启用开关
        const editCcEnabledCheckbox = modal.querySelector('#edit_cc_enabled');
        if (editCcEnabledCheckbox) {
            editCcEnabledCheckbox.checked = false;
        }

        // 重置分支条件相关字段（复用resetAddStepModal的完善逻辑）
        const editBranchValueContainer = modal.querySelector('#edit_branchValueContainer');
        if (editBranchValueContainer) {
            editBranchValueContainer.innerHTML = '<input type="text" class="form-control" id="edit_branch_value" name="branch_value" placeholder="请输入比较值">';
        }

        // 重置分支条件选择框（复用完善的重置逻辑）
        const editBranchFieldSelect = modal.querySelector('#edit_branch_field');
        if (editBranchFieldSelect) {
            editBranchFieldSelect.selectedIndex = 0;
        }
        const editBranchOperatorSelect = modal.querySelector('#edit_branch_operator');
        if (editBranchOperatorSelect) {
            editBranchOperatorSelect.selectedIndex = 0;
        }

        // 重置字段值容器（重要：清理动态生成的复选框）
        const editFieldValuesContainer = modal.querySelector('#edit_field_values_container');
        if (editFieldValuesContainer) {
            editFieldValuesContainer.innerHTML = '<div class="text-center text-muted">请先选择字段和操作符</div>';
        }

        // 重置邮件通知开关为默认状态（开启）
        const editSendEmailCheckbox = modal.querySelector('#edit_send_email');
        if (editSendEmailCheckbox) {
            editSendEmailCheckbox.checked = true;
        }

        // 清除抄送用户多选框的选择
        const editCcUsersSelect = modal.querySelector('#edit_cc_users');
        if (editCcUsersSelect) {
            editCcUsersSelect.selectedIndex = -1; // 清空所有选择
        }

        // 移除动态添加的隐藏字段（保留永久字段）
        if (form) {
            const dynamicFields = form.querySelectorAll('input[type="hidden"]:not([name="csrf_token"]):not([data-permanent])');
            dynamicFields.forEach(field => {
                if (!field.hasAttribute('data-permanent')) {
                    field.remove();
                }
            });
        }

        console.log('✅ 编辑步骤模态框已完全重置（复用完善的重置逻辑）');
        
        console.log('🔍 [调试] 重置后编辑模态框状态:', {
            display: modal.style.display,
            classes: modal.className,
            editSelectedFieldsArrayLength: this.editSelectedFields.length,
            branchConfigVisible: modal.querySelector('#edit_branchConfigSection')?.style.display,
            ccSectionVisible: modal.querySelector('#edit_ccUsersSection')?.style.display,
            fieldValuesContent: modal.querySelector('#edit_field_values_container')?.innerHTML.substring(0, 50) + '...'
        });
    }

    /**
     * 验证分支条件是否存在冲突
     * @param {number} stepId - 步骤ID
     * @param {Object} conditionData - 条件数据
     */
    async validateBranchCondition(stepId, conditionData) {
        try {
            const response = await fetch(`/admin/approval/step/${stepId}/validate-condition`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
                },
                body: JSON.stringify(conditionData)
            });
            
            if (!response.ok) {
                throw new Error('网络请求失败');
            }
            
            const data = await response.json();
            
            console.log('🔍 [调试] 条件验证结果:', data);
            return data;
            
        } catch (error) {
            console.error('验证分支条件失败:', error);
            throw error;
        }
    }

    /**
     * 显示冲突提示对话框 - 使用通用对话框组件
     * @param {Object} conflictInfo - 冲突信息
     */
    showConflictDialog(conflictInfo) {
        const existingCondition = conflictInfo.existing_condition || {};
        const conditionText = existingCondition.field_value || '未知条件';
        const approverText = existingCondition.approver_name ? `\n审批人：${existingCondition.approver_name}` : '';
        
        const message = `发现冲突的条件："${conditionText}"${approverText}\n\n请修改条件值以避免冲突，或取消操作返回编辑。`;
        
        if (typeof window.showConfirmDialog === 'function') {
            window.showConfirmDialog({
                title: '条件冲突',
                message: message,
                type: 'warning',
                confirmText: '修改条件',
                cancelText: '取消操作',
                dialogId: 'branchConflictDialog',
                onConfirm: () => {
                    // 返回表单让用户修改条件
                    if (typeof window.warning === 'function') {
                        window.warning('请修改条件值以避免与现有条件冲突');
                    } else {
                        this.showErrorMessage('请修改条件值以避免与现有条件冲突');
                    }
                },
                onCancel: () => {
                    // 关闭编辑模态框
                    const editModal = document.getElementById('editStepModal');
                    if (editModal) {
                        const bootstrapModal = bootstrap.Modal.getInstance(editModal);
                        if (bootstrapModal) {
                            bootstrapModal.hide();
                        }
                    }
                    if (typeof window.info === 'function') {
                        window.info('操作已取消');
                    }
                }
            });
        } else {
            // 降级到普通alert
            const shouldContinue = confirm(`条件冲突\n\n${message}\n\n点击"确定"修改条件，点击"取消"退出操作。`);
            if (!shouldContinue) {
                const editModal = document.getElementById('editStepModal');
                if (editModal) {
                    const bootstrapModal = bootstrap.Modal.getInstance(editModal);
                    if (bootstrapModal) {
                        bootstrapModal.hide();
                    }
                }
            }
        }
    }


    /**
     * 预提交验证 - 检查表单数据是否存在冲突
     * @param {HTMLFormElement} form - 表单元素
     */
    async preSubmitValidation(form) {
        console.log('🔍 [调试] 开始预提交验证');
        
        // 检查是否是分支条件相关的表单
        const isBranchForm = form.querySelector('#edit_is_branch_condition')?.value === 'true' ||
                           form.querySelector('#edit_step_type')?.value === 'branch';
        
        if (!isBranchForm) {
            console.log('✅ [调试] 非分支条件表单，跳过冲突验证');
            return { hasConflict: false };
        }
        
        // 提取表单数据
        const formData = this.extractBranchConditionData(form);
        if (!formData) {
            console.log('⚠️ [调试] 无法提取分支条件数据');
            return { hasConflict: false };
        }
        
        // 获取步骤ID
        const stepId = this.extractStepId(form);
        if (!stepId) {
            console.log('⚠️ [调试] 无法获取步骤ID');
            return { hasConflict: false };
        }
        
        try {
            // 调用验证API
            const validationResult = await this.validateBranchCondition(stepId, formData);
            
            if (validationResult.success) {
                console.log('✅ [调试] 验证通过，无冲突');
                return { hasConflict: false };
            } else if (validationResult.conflict?.has_conflict) {
                console.log('⚠️ [调试] 检测到条件冲突');
                return { 
                    hasConflict: true, 
                    conflictInfo: validationResult.conflict 
                };
            } else {
                console.log('❌ [调试] 验证失败:', validationResult.message);
                return { hasConflict: false };
            }
        } catch (error) {
            console.error('预提交验证失败:', error);
            return { hasConflict: false };
        }
    }

    /**
     * 从表单中提取分支条件数据
     * @param {HTMLFormElement} form - 表单元素
     */
    extractBranchConditionData(form) {
        const branchField = form.querySelector('#edit_branch_field')?.value;
        const branchOperator = form.querySelector('#edit_branch_operator')?.value;
        const branchValue = form.querySelector('#edit_branch_value')?.value;
        const approverId = form.querySelector('#edit_approver_user_id')?.value;
        
        if (!branchField || !branchOperator || !branchValue) {
            console.log('⚠️ [调试] 分支条件数据不完整:', { branchField, branchOperator, branchValue });
            return null;
        }
        
        return {
            field: branchField,
            operator: branchOperator,
            value: branchValue,
            approver_id: approverId || null
        };
    }

    /**
     * 从表单中提取步骤ID
     * @param {HTMLFormElement} form - 表单元素
     */
    extractStepId(form) {
        // 从表单action URL中提取
        if (form.action) {
            const match = form.action.match(/\/step\/(\d+)\//);
            if (match && match[1]) {
                return parseInt(match[1]);
            }
        }
        
        // 从隐藏字段中获取
        const stepIdInput = form.querySelector('input[name="step_id"]');
        if (stepIdInput && stepIdInput.value) {
            return parseInt(stepIdInput.value);
        }
        
        return null;
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
window.addFieldBadge = function() {
    if (window.approvalConfig) {
        window.approvalConfig.addFieldBadge();
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
    console.log('🔍 [调试] 全局 updateSelectedFieldValues 调用:', {
        prefix: prefix,
        approvalConfigExists: !!window.approvalConfig,
        timestamp: new Date().toLocaleTimeString()
    });

    if (window.approvalConfig) {
        console.log('✅ [调试] 调用类实例的 updateSelectedFieldValues 方法');
        window.approvalConfig.updateSelectedFieldValues(prefix);
    } else {
        console.error('❌ [调试] window.approvalConfig 不存在，无法调用类方法');
    }
};

// 全局抄送用户徽章更新函数
window.updateCcUserBadges = function(prefix) {
    if (window.approvalConfig) {
        window.approvalConfig.updateCcUserBadges(prefix);
    }
};

// 全局抄送用户搜索过滤函数
window.filterCcUsers = function(prefix) {
    if (window.approvalConfig) {
        window.approvalConfig.filterCcUsers(prefix);
    }
};

// 全局字段徽章管理函数
window.addEditFieldBadge = function() {
    if (window.approvalConfig) {
        window.approvalConfig.addEditFieldBadge();
    }
};

window.removeFieldBadge = function(fieldCode) {
    if (window.approvalConfig) {
        window.approvalConfig.removeFieldBadge(fieldCode);
    }
};

window.removeEditFieldBadge = function(fieldCode) {
    if (window.approvalConfig) {
        window.approvalConfig.removeEditFieldBadge(fieldCode);
    }
};

/**
 * 验证模态框DOM结构完整性
 * @param {boolean} isEdit - 是否为编辑模式
 */
function validateModalDOMStructure(isEdit) {
    const modalId = isEdit ? 'editStepModal' : 'addStepModal';
    const modal = document.getElementById(modalId);
    
    if (!modal) {
        console.error(`❌ [DOM验证] 模态框 ${modalId} 不存在`);
        return false;
    }
    
    console.log(`🔍 [DOM验证] 开始验证 ${modalId} 结构完整性`);
    
    // 检查关键表单元素
    const formId = isEdit ? 'editStepForm' : 'addStepForm';
    const form = modal.querySelector(`#${formId}`);
    console.log(`  - 表单存在 (${formId}):`, !!form);
    
    // 检查关键输入字段
    const prefix = isEdit ? 'edit_' : '';
    const keyFields = [
        `${prefix}step_name`,
        `${prefix}step_type`,
        `${prefix}approver_selection`,
        `${prefix}editable_fields_select`,
        `${prefix}selected_fields`,
        `${prefix}editable_fields_input`
    ];
    
    const fieldResults = {};
    keyFields.forEach(fieldId => {
        const element = modal.querySelector(`#${fieldId}`);
        fieldResults[fieldId] = !!element;
        console.log(`  - ${fieldId}:`, !!element);
    });
    
    // 检查HTML中的调试注释
    const hasDebugComment = modal.innerHTML.includes('DEBUG: is_edit=');
    console.log(`  - 包含调试注释:`, hasDebugComment);
    
    if (hasDebugComment) {
        const debugMatch = modal.innerHTML.match(/DEBUG: is_edit=(\w+)/);
        if (debugMatch) {
            const templateIsEdit = debugMatch[1];
            console.log(`  - 模板中is_edit值:`, templateIsEdit);
            console.log(`  - JavaScript中isEdit值:`, isEdit);
            console.log(`  - 值匹配:`, templateIsEdit === String(isEdit));
        }
    }
    
    // 检查所有隐藏输入字段
    const hiddenInputs = modal.querySelectorAll('input[type="hidden"]');
    console.log(`  - 隐藏输入字段数量:`, hiddenInputs.length);
    hiddenInputs.forEach((input, index) => {
        console.log(`    [${index}] ID: ${input.id}, Name: ${input.name}, Value: "${input.value}"`);
    });
    
    // 特别检查可编辑字段的隐藏输入
    const editableFieldsInput = modal.querySelector(`#${prefix}editable_fields_input`);
    if (!editableFieldsInput && isEdit) {
        console.warn(`⚠️ [DOM验证] 关键字段缺失: ${prefix}editable_fields_input`);
        
        // 检查是否存在不带前缀的版本
        const unprefixedInput = modal.querySelector('#editable_fields_input');
        if (unprefixedInput) {
            console.log(`  - 发现无前缀版本: editable_fields_input`);
        }
        
        return false;
    }
    
    console.log(`✅ [DOM验证] ${modalId} 结构验证完成`);
    return true;
}

// 将验证函数添加到全局作用域以便调试使用
window.validateModalDOMStructure = validateModalDOMStructure;

