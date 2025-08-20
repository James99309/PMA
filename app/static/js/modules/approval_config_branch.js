/**
 * 审批配置分支功能模块
 * 负责：分支条件编辑、添加、删除等复杂操作
 */

class ApprovalConfigBranch {
  constructor() {
    this.initialized = false;
    
    // 绑定方法上下文
    this.init = this.init.bind(this);
    this.editBranchCondition = this.editBranchCondition.bind(this);
    this.addNewBranch = this.addNewBranch.bind(this);
    this.deleteBranchCondition = this.deleteBranchCondition.bind(this);
  }
  
  /**
   * 初始化分支模块
   */
  init() {
    if (!window.ApprovalConfigMain || !window.ApprovalConfigMain.initialized) {
      console.error('❌ ApprovalConfigMain 未初始化，分支模块无法启动');
      return;
    }
    
    this.initialized = true;
    
    // 设置模态框关闭时的清理事件
    this.setupModalCleanup();
    
    console.log('✅ ApprovalConfigBranch 初始化完成');
  }
  
  /**
   * 设置模态框清理事件监听器
   */
  setupModalCleanup() {
    const addStepModal = document.getElementById('addStepModal');
    if (addStepModal) {
      addStepModal.addEventListener('hidden.bs.modal', () => {
        this.cleanupEditMode(addStepModal);
      });
      console.log('🔧 模态框清理事件监听器已设置');
    }
  }
  
  /**
   * 编辑分支条件
   */
  async editBranchCondition(stepId, conditionIndex) {
    console.log(`🔧 编辑分支条件 - 步骤ID: ${stepId}, 条件索引: ${conditionIndex}`);
    
    if (!window.ApprovalConfigMain.checkPermission()) {
      return;
    }
    
    try {
      // 获取步骤详情
      const url = `${window.ApprovalConfigMain.getUrl('stepDetails')}${stepId}/details`;
      const data = await window.ApprovalConfigMain.safeFetch(url);
      
      if (data.success && data.step.branch_condition && data.step.branch_condition.conditions) {
        const condition = data.step.branch_condition.conditions[conditionIndex];
        if (condition) {
          console.log('📊 获取到条件数据:', condition);
          
          // 这里将来会打开编辑模态框
          this.showEditModal(stepId, conditionIndex, data.step, condition);
        } else {
          alert('条件不存在');
        }
      } else {
        alert('获取条件信息失败');
      }
    } catch (error) {
      console.error('🗨️ 网络错误:', error);
      alert('网络错误，请检查连接');
    }
  }
  
  /**
   * 添加新分支条件
   */
  addNewBranch(stepId, branchType) {
    console.log(`🔀 为步骤 ${stepId} 添加分支条件`);
    
    if (!window.ApprovalConfigMain.checkPermission()) {
      return;
    }
    
    // 暂时显示提示，将来实现完整功能
    alert(`添加分支条件功能正在完善中\n步骤ID: ${stepId}\n分支类型: ${branchType}`);
  }
  
  /**
   * 删除分支条件
   */
  async deleteBranchCondition(stepId, conditionIndex) {
    console.log(`🗑️ 删除分支条件 - 步骤ID: ${stepId}, 条件索引: ${conditionIndex}`);
    
    if (!window.ApprovalConfigMain.checkPermission()) {
      return;
    }
    
    if (!confirm('确定要删除此分支条件吗？')) {
      return;
    }
    
    try {
      // 准备删除请求数据
      const formData = new FormData();
      formData.append('csrf_token', window.ApprovalConfigMain.getCsrfToken());
      formData.append('action', 'delete_branch_condition');
      formData.append('condition_index', conditionIndex);
      
      // 发送删除请求
      const response = await fetch(`/admin/approval/step/${stepId}/edit`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        console.log('✅ 删除请求成功');
        // 刷新页面以更新显示
        location.reload();
      } else {
        console.error('❌ 删除请求失败:', response.status);
        alert('删除失败，请重试');
      }
    } catch (error) {
      console.error('❌ 网络错误:', error);
      alert('网络错误，请重试');
    }
  }
  
  /**
   * 显示分支条件编辑模态框
   */
  showEditModal(stepId, conditionIndex, stepData, condition) {
    console.log('🔧 显示分支条件编辑模态框');
    console.log('参数:', { stepId, conditionIndex, stepData: stepData?.step_name, condition });
    
    try {
      this.openEditModal(stepId, conditionIndex, stepData, condition);
    } catch (error) {
      console.error('❌ 编辑模态框显示失败:', error);
      alert(`编辑分支条件失败: ${error.message}`);
    }
  }
  
  /**
   * 打开分支条件编辑模态框
   */
  openEditModal(stepId, conditionIndex, stepData, condition) {
    console.log('🔧 打开分支条件编辑模态框');
    
    // 查找添加步骤模态框
    const addStepModal = document.getElementById('addStepModal');
    if (!addStepModal) {
      alert('编辑功能不可用，请刷新页面后重试');
      return;
    }
    
    try {
      // 1. 设置模态框标题为编辑模式
      const modalTitle = addStepModal.querySelector('.modal-title');
      if (modalTitle) {
        modalTitle.textContent = `编辑分支条件 ${conditionIndex + 1} - ${stepData.step_name}`;
      }
      
      // 2. 隐藏步骤类型选择（编辑时不允许修改步骤类型）
      const stepTypeContainer = addStepModal.querySelector('#step_type')?.closest('.mb-3');
      if (stepTypeContainer) {
        stepTypeContainer.style.display = 'none';
        console.log('🔒 已隐藏步骤类型选择（编辑模式）');
      }
      
      // 3. 预填充基础信息
      const stepNameInput = addStepModal.querySelector('#step_name');
      const stepOrderInput = addStepModal.querySelector('#step_order');
      const stepTypeSelect = addStepModal.querySelector('#step_type');
      
      // 设置步骤名称为只读提示
      if (stepNameInput) {
        stepNameInput.value = `编辑: ${stepData.step_name} - 分支条件${conditionIndex + 1}`;
        stepNameInput.disabled = true;
        stepNameInput.style.backgroundColor = '#f8f9fa';
        stepNameInput.style.cursor = 'not-allowed';
      }
      
      if (stepOrderInput) stepOrderInput.value = stepData.step_order || '';
      
      // 确保步骤类型设置为分支并触发相关UI显示
      if (stepTypeSelect) {
        stepTypeSelect.value = 'branch';
        // 触发类型变化事件来显示分支配置区域
        if (typeof handleStepTypeChange === 'function') {
          handleStepTypeChange();
        }
      }
      
      // 3. 预填充分支条件数据
      setTimeout(() => {
        this.loadBranchConditionData(condition, stepData, conditionIndex);
      }, 200);
      
      // 4. 修改表单提交行为为编辑模式
      this.setupEditMode(addStepModal, stepId, conditionIndex);
      
      // 5. 显示模态框 - 尝试jQuery或Bootstrap 5
      if (typeof $ !== 'undefined' && $.fn.modal) {
        $(addStepModal).modal('show');
      } else if (typeof bootstrap !== 'undefined') {
        const modal = new bootstrap.Modal(addStepModal);
        modal.show();
      } else {
        // 最后的降级方案
        addStepModal.style.display = 'block';
        addStepModal.classList.add('show');
      }
      
      console.log('✅ 编辑模态框已显示');
      
    } catch (error) {
      console.error('❌ 备用编辑模态框失败:', error);
      alert('编辑模态框显示失败，请刷新页面后重试');
    }
  }
  
  /**
   * 加载分支条件数据到编辑表单
   */
  loadBranchConditionData(condition, stepData, conditionIndex) {
    console.log('📝 加载分支条件数据:', condition);
    console.log('📝 步骤数据:', stepData);
    
    try {
      // 1. 分支字段 - 使用步骤已配置的字段，不允许修改
      const branchFieldSelect = document.getElementById('branch_field');
      const configuredField = stepData.branch_condition && stepData.branch_condition.field;
      
      console.log('🔍 分支字段配置检测:', {
        'stepData.branch_condition?.field': configuredField,
        '使用配置的字段': configuredField
      });
      
      if (branchFieldSelect && configuredField) {
        // 等待动态字段加载完成后设置，使用重试机制
        this.setBranchFieldWithRetry(branchFieldSelect, configuredField, 0);
      } else {
        console.error('❌ 分支步骤未配置条件字段');
        alert('分支步骤配置错误：未找到条件字段配置');
        return;
      }
      
      // 2. 操作符
      const branchOperatorSelect = document.getElementById('branch_operator');
      if (branchOperatorSelect && condition.operator) {
        setTimeout(() => {
          console.log('🔧 设置操作符:', condition.operator);
          branchOperatorSelect.value = condition.operator;
          
          // 触发现有的操作符变化事件
          if (typeof handleBranchOperatorChange === 'function') {
            handleBranchOperatorChange();
          }
        }, 400);
      }
      
      // 3. 条件值 - 延迟更长时间确保UI组件准备好
      setTimeout(() => {
        this.loadConditionValue(condition);
      }, 500);
      
      // 4. 审批人信息和执行动作
      setTimeout(() => {
        const trueApproverSelect = document.getElementById('true_branch_approver');
        const falseApproverSelect = document.getElementById('false_branch_approver');
        const trueActionSelect = document.getElementById('true_branch_action');
        const falseActionSelect = document.getElementById('false_branch_action');
        
        console.log('🔍 审批人和动作元素检测:', {
          trueApproverSelect: !!trueApproverSelect,
          falseApproverSelect: !!falseApproverSelect,
          trueActionSelect: !!trueActionSelect,
          falseActionSelect: !!falseActionSelect
        });
        
        // 设置审批人
        if (condition.approver_id) {
          if (trueApproverSelect) {
            console.log('🔧 设置True分支审批人:', condition.approver_id);
            trueApproverSelect.value = condition.approver_id;
          }
        }
        
        // 设置执行动作
        if (condition.action) {
          if (trueActionSelect) {
            console.log('🔧 设置True分支动作:', condition.action);
            trueActionSelect.value = condition.action;
          }
        }
        
        // 如果有False分支的配置，也要设置
        if (stepData.branch_condition && stepData.branch_condition.conditions && stepData.branch_condition.conditions.length > 1) {
          const falseCondition = stepData.branch_condition.conditions.find((c, index) => index !== conditionIndex);
          if (falseCondition) {
            if (falseApproverSelect && falseCondition.approver_id) {
              console.log('🔧 设置False分支审批人:', falseCondition.approver_id);
              falseApproverSelect.value = falseCondition.approver_id;
            }
            if (falseActionSelect && falseCondition.action) {
              console.log('🔧 设置False分支动作:', falseCondition.action);
              falseActionSelect.value = falseCondition.action;
            }
          }
        }
      }, 600);
      
      // 5. 可编辑字段处理（新增）
      setTimeout(() => {
        this.loadEditableFields(stepData);
      }, 700);
      
      // 6. 隐藏不相关字段
      const actionTypeContainer = document.querySelector('#action_type')?.closest('.mb-3');
      if (actionTypeContainer) {
        actionTypeContainer.style.display = 'none';
      }
      
      console.log('✅ 分支条件数据加载完成');
    } catch (error) {
      console.error('❌ 数据加载失败:', error);
    }
  }
  
  /**
   * 设置分支字段，带重试机制
   */
  setBranchFieldWithRetry(branchFieldSelect, configuredField, retryCount) {
    const maxRetries = 10;
    const retryDelay = 500;
    
    console.log(`🔄 尝试设置分支字段 (第${retryCount + 1}次):`, configuredField);
    
    // 检查字段选项是否已加载
    const optionsCount = branchFieldSelect.options.length;
    const hasTargetOption = Array.from(branchFieldSelect.options).some(option => option.value === configuredField);
    
    console.log(`📋 字段选项状态: 总数=${optionsCount}, 包含目标=${hasTargetOption}`);
    console.log(`📋 当前可用选项:`, Array.from(branchFieldSelect.options).map(opt => `${opt.value}="${opt.textContent}"`));
    
    if (hasTargetOption) {
      // 选项已加载，设置字段值
      console.log('✅ 字段选项已加载，设置字段值');
      branchFieldSelect.value = configuredField;
      branchFieldSelect.disabled = true;
      
      // 添加编辑模式的视觉样式
      branchFieldSelect.style.backgroundColor = '#f8f9fa';
      branchFieldSelect.style.cursor = 'not-allowed';
      branchFieldSelect.style.border = '1px solid #dee2e6';
      
      // 添加字段说明
      const fieldContainer = branchFieldSelect.parentElement;
      if (fieldContainer && !fieldContainer.querySelector('.field-edit-hint')) {
        const hint = document.createElement('small');
        hint.className = 'field-edit-hint text-muted d-block mt-1';
        hint.innerHTML = '<i class="fas fa-info-circle"></i> 条件字段继承自分支步骤配置，不可修改';
        fieldContainer.appendChild(hint);
      }
      
      // 验证设置是否成功
      setTimeout(() => {
        if (branchFieldSelect.value === configuredField) {
          console.log('✅ 分支字段设置成功:', branchFieldSelect.value);
          
          // 触发字段变化事件加载相关UI
          if (typeof handleBranchFieldChange === 'function') {
            handleBranchFieldChange();
          }
        } else {
          console.warn('⚠️ 分支字段设置后值不匹配:', branchFieldSelect.value, '期望:', configuredField);
        }
      }, 100);
      
    } else if (retryCount < maxRetries) {
      // 选项未加载，重试
      console.log(`⏳ 字段选项未加载完成，${retryDelay}ms后重试...`);
      setTimeout(() => {
        this.setBranchFieldWithRetry(branchFieldSelect, configuredField, retryCount + 1);
      }, retryDelay);
    } else {
      // 重试次数超限，手动添加缺失的字段选项
      console.error('❌ 分支字段设置失败，重试次数超限');
      console.error('当前可用选项:', Array.from(branchFieldSelect.options).map(opt => `${opt.value}="${opt.textContent}"`));
      console.log('🔧 手动添加缺失的字段选项...');
      
      // 手动添加缺失的字段选项（带中文名称映射）
      const chineseFieldName = this.getFieldChineseName(configuredField);
      console.log('📝 添加字段选项:', configuredField, '→', chineseFieldName);
      
      const option = document.createElement('option');
      option.value = configuredField;
      option.textContent = chineseFieldName;
      branchFieldSelect.appendChild(option);
      
      // 再次尝试设置
      branchFieldSelect.value = configuredField;
      branchFieldSelect.disabled = true;
      
      // 添加编辑模式视觉样式
      branchFieldSelect.style.backgroundColor = '#f8f9fa';
      branchFieldSelect.style.cursor = 'not-allowed';
      branchFieldSelect.style.border = '1px solid #dee2e6';
      
      // 添加字段说明
      const fieldContainer = branchFieldSelect.parentElement;
      if (fieldContainer && !fieldContainer.querySelector('.field-edit-hint')) {
        const hint = document.createElement('small');
        hint.className = 'field-edit-hint text-muted d-block mt-1';
        hint.innerHTML = '<i class="fas fa-info-circle"></i> 条件字段继承自分支步骤配置，不可修改';
        fieldContainer.appendChild(hint);
      }
      
      console.log('✅ 已手动添加并设置分支字段');
    }
  }
  
  /**
   * 获取字段的中文名称映射
   */
  getFieldChineseName(fieldCode) {
    // 项目表字段的中文名称映射
    const fieldChineseNames = {
      // 基础字段
      'project_type': '项目类型',
      'total_amount': '总金额', 
      'status': '状态',
      'priority': '优先级',
      'department': '部门',
      'description': '描述',
      'remarks': '备注',
      
      // 项目相关字段
      'project_name': '项目名称',
      'client_name': '客户名称',
      'start_date': '开始日期',
      'end_date': '结束日期',
      'budget': '预算',
      'progress': '进度',
      
      // 财务相关字段
      'contract_amount': '合同金额',
      'paid_amount': '已付金额',
      'remaining_amount': '剩余金额',
      'payment_terms': '付款条件',
      
      // 人员相关字段
      'project_manager': '项目经理',
      'team_members': '团队成员',
      'owner': '负责人',
      'approver': '审批人',
      
      // 时间相关字段
      'created_at': '创建时间',
      'updated_at': '更新时间',
      'deadline': '截止日期',
      'approval_date': '审批日期',
      
      // 分类标识
      'category': '分类',
      'tags': '标签',
      'risk_level': '风险等级',
      'completion_rate': '完成率'
    };
    
    // 返回中文名称，如果没有映射就返回原始字段名
    const chineseName = fieldChineseNames[fieldCode];
    if (chineseName) {
      console.log(`🔤 字段名称映射: ${fieldCode} → ${chineseName}`);
      return chineseName;
    } else {
      console.warn(`⚠️ 未找到字段 ${fieldCode} 的中文映射，使用原始名称`);
      return fieldCode;
    }
  }
  
  /**
   * 加载条件值到表单
   */
  loadConditionValue(condition) {
    const branchValueInput = document.getElementById('branch_value');
    const branchValueFinal = document.getElementById('branch_value_final');
    
    if (condition.value && branchValueInput) {
      // 显示原始值或中文映射值
      this.getValueChineseMapping(condition.field || '', condition.value).then(displayValue => {
        branchValueInput.value = displayValue;
      });
      
      // 设置最终值
      if (branchValueFinal) {
        branchValueFinal.value = condition.value;
      }
      
      console.log('✅ 条件值已加载:', displayValue, '(原值:', condition.value, ')');
    }
  }
  
  /**
   * 预填充分支条件数据
   */
  prefillBranchCondition(condition) {
    console.log('📝 预填充分支条件数据:', condition);
    
    // 1. 分支字段 - 加载当前配置的字段并设为只读
    const branchFieldSelect = document.getElementById('branch_field');
    if (branchFieldSelect && condition.field) {
      branchFieldSelect.value = condition.field;
      branchFieldSelect.disabled = true; // 设为不可编辑
      
      // 触发字段变化事件
      if (window.ApprovalConfigForm && window.ApprovalConfigForm.handleBranchFieldChange) {
        window.ApprovalConfigForm.handleBranchFieldChange();
      }
    }
    
    // 2. 操作符
    const branchOperatorSelect = document.getElementById('branch_operator');
    if (branchOperatorSelect && condition.operator) {
      branchOperatorSelect.value = condition.operator;
      // 触发操作符变化事件
      if (window.ApprovalConfigForm && window.ApprovalConfigForm.handleBranchOperatorChange) {
        window.ApprovalConfigForm.handleBranchOperatorChange();
      }
    }
    
    // 3. 条件值 - 需要加载中文映射值
    this.loadConditionValue(condition);
    
    // 4. 审批人信息 - 加载当前分支步骤配置的审批人
    const approverSelect = document.getElementById('approver_selection');
    if (approverSelect && condition.approver_id) {
      approverSelect.value = condition.approver_id;
    }
    
    // 5. 隐藏动作类型字段 - 分支步骤不需要
    const actionTypeContainer = document.querySelector('#action_type').closest('.mb-3');
    if (actionTypeContainer) {
      actionTypeContainer.style.display = 'none';
    }
    
    // 6. 加载可编辑字段配置
    this.loadEditableFields(condition);
    
    console.log('✅ 分支条件数据预填充完成');
  }
  
  /**
   * 加载条件值 - 显示中文映射
   */
  loadConditionValue(condition) {
    const branchValueInput = document.getElementById('branch_value');
    const branchValueSelect = document.getElementById('branch_value_select');
    
    if (condition.value) {
      console.log('🔧 加载条件值:', condition.value, '操作符:', condition.operator, '字段:', condition.field);
      
      // 根据操作符类型决定显示方式
      if (condition.operator === 'equals_from_list' || condition.operator === 'in_from_list') {
        // 下拉选择或多选模式 - 加载数据库中的值选项
        if (branchValueSelect) {
          console.log('📋 使用下拉选择模式加载字段值选项');
          this.loadFieldValueOptions(condition.field, condition.value);
        }
      } else {
        // 文本输入模式 - 尝试显示中文映射
        if (branchValueInput) {
          this.getValueChineseMapping(condition.field, condition.value).then(chineseValue => {
            branchValueInput.value = chineseValue;
            console.log('📝 文本输入模式，显示值:', chineseValue, '(原值:', condition.value, ')');
          });
        }
      }
    } else {
      console.log('⚠️ 条件值为空，跳过加载');
    }
  }
  
  /**
   * 获取字段值的中文映射
   * 调用后端通用映射API而不是硬编码映射
   */
  async getValueChineseMapping(field, value) {
    try {
      // 处理多值情况（如 "channel_follow,sales_focus"）
      if (value && value.includes(',')) {
        const values = value.split(',');
        const mappedValues = await Promise.all(values.map(async (v) => {
          const trimmedValue = v.trim();
          return await this.getSingleValueMapping(field, trimmedValue);
        }));
        console.log(`🔤 多值映射: ${field}.${value} → ${mappedValues.join(', ')}`);
        return mappedValues.join(', ');
      }
      
      // 单值映射
      return await this.getSingleValueMapping(field, value);
    } catch (error) {
      console.error('❌ 获取值映射失败:', error);
      return value; // 错误时返回原值
    }
  }
  
  /**
   * 获取单个值的映射
   */
  async getSingleValueMapping(field, value) {
    try {
      // 调用后端映射API
      const response = await fetch(`/admin/approval/api/get-value-mapping?field=${encodeURIComponent(field)}&value=${encodeURIComponent(value)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.mapped_value) {
          console.log(`🔤 值映射: ${field}.${value} → ${data.mapped_value}`);
          return data.mapped_value;
        }
      }
      
      console.log(`⚠️ 未找到映射: ${field}.${value}，使用原值`);
      return value; // 如果没有映射就返回原值
    } catch (error) {
      console.error('❌ 单值映射请求失败:', error);
      return value;
    }
  }
  
  /**
   * 加载字段值选项
   */
  async loadFieldValueOptions(field, currentValue) {
    try {
      console.log('🔄 加载字段值选项:', field, '当前值:', currentValue);
      
      // 调用后端API获取字段的去重值
      const response = await fetch(`/admin/approval/api/get-field-values?object_type=project&field_name=${encodeURIComponent(field)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('📋 字段值数据:', data);
        
        if (data.success && data.values) {
          const branchValueSelect = document.getElementById('branch_value_select');
          if (branchValueSelect) {
            branchValueSelect.innerHTML = '<option value="">请选择...</option>';
            
            data.values.forEach(valueItem => {
              const optionElement = document.createElement('option');
              optionElement.value = valueItem.value;        // 实际值
              optionElement.textContent = valueItem.display; // 显示值
              optionElement.title = `使用次数: ${valueItem.count}`;
              optionElement.selected = valueItem.value === currentValue;
              branchValueSelect.appendChild(optionElement);
              console.log(`📝 添加字段值选项: ${valueItem.value} → ${valueItem.display} (选中: ${valueItem.value === currentValue})`);
            });
            
            console.log(`✅ 字段值选项加载完成，共 ${data.values.length} 个，当前值: ${currentValue}`);
          }
        } else {
          console.error('❌ 字段值API返回数据异常:', data);
        }
      } else {
        console.error('❌ 字段值API请求失败:', response.status);
      }
    } catch (error) {
      console.error('❌ 加载字段值选项失败:', error);
    }
  }
  
  /**
   * 加载可编辑字段配置
   */
  loadEditableFields(condition) {
    if (condition.editable_fields && condition.editable_fields.length > 0) {
      const selectedFieldsContainer = document.getElementById('selected_fields_container');
      
      if (selectedFieldsContainer && window.ApprovalConfigForm) {
        // 清空当前选择的字段
        window.ApprovalConfigForm.selectedFields = [...condition.editable_fields];
        
        // 清空容器并重新添加徽章
        selectedFieldsContainer.innerHTML = '';
        
        condition.editable_fields.forEach(fieldCode => {
          // 需要获取字段名称，这里暂时使用字段代码
          const fieldName = this.getFieldName(fieldCode);
          const group = 'master'; // 需要根据实际情况确定
          
          const badgeHtml = window.ApprovalConfigForm.createFieldBadge(fieldCode, fieldName, group);
          selectedFieldsContainer.insertAdjacentHTML('beforeend', badgeHtml);
        });
        
        // 更新隐藏字段
        const hiddenInput = document.getElementById('editable_fields_input');
        if (hiddenInput) {
          hiddenInput.value = JSON.stringify(condition.editable_fields);
        }
        
        console.log('✅ 可编辑字段已加载:', condition.editable_fields);
      }
    }
  }
  
  /**
   * 获取字段名称映射
   */
  getFieldName(fieldCode) {
    const fieldNames = {
      'total_amount': '总金额',
      'status': '状态',
      'priority': '优先级',
      'department': '部门',
      'description': '描述',
      'remarks': '备注'
    };
    
    return fieldNames[fieldCode] || fieldCode;
  }
  
  /**
   * 设置编辑模式
   */
  setupEditMode(modal, stepId, conditionIndex) {
    // 查找表单
    const form = modal.querySelector('form');
    if (!form) return;
    
    // 添加隐藏字段标识编辑模式
    let editModeInput = form.querySelector('#edit_mode');
    if (!editModeInput) {
      editModeInput = document.createElement('input');
      editModeInput.type = 'hidden';
      editModeInput.id = 'edit_mode';
      editModeInput.name = 'edit_mode';
      form.appendChild(editModeInput);
    }
    editModeInput.value = 'branch_condition';
    
    // 添加步骤ID
    let stepIdInput = form.querySelector('#edit_step_id');
    if (!stepIdInput) {
      stepIdInput = document.createElement('input');
      stepIdInput.type = 'hidden';
      stepIdInput.id = 'edit_step_id';
      stepIdInput.name = 'edit_step_id';
      form.appendChild(stepIdInput);
    }
    stepIdInput.value = stepId;
    
    // 添加条件索引
    let conditionIndexInput = form.querySelector('#edit_condition_index');
    if (!conditionIndexInput) {
      conditionIndexInput = document.createElement('input');
      conditionIndexInput.type = 'hidden';
      conditionIndexInput.id = 'edit_condition_index';
      conditionIndexInput.name = 'edit_condition_index';
      form.appendChild(conditionIndexInput);
    }
    conditionIndexInput.value = conditionIndex;
    
    console.log('✅ 编辑模式设置完成');
  }
  
  /**
   * 清理编辑模式设置（当模态框关闭时调用）
   */
  cleanupEditMode(modal) {
    console.log('🧹 开始清理编辑模式');
    
    // 恢复模态框标题
    const modalTitle = modal.querySelector('.modal-title');
    if (modalTitle) {
      modalTitle.textContent = '添加审批步骤';
    }
    
    // 显示步骤类型选择
    const stepTypeContainer = modal.querySelector('#step_type')?.closest('.mb-3');
    if (stepTypeContainer) {
      stepTypeContainer.style.display = 'block';
      console.log('✅ 恢复步骤类型选择显示');
    }
    
    // 恢复步骤名称输入的可编辑状态
    const stepNameInput = modal.querySelector('#step_name');
    if (stepNameInput) {
      stepNameInput.disabled = false;
      stepNameInput.style.backgroundColor = '';
      stepNameInput.style.cursor = '';
    }
    
    // 恢复分支字段的可编辑状态
    const branchFieldSelect = document.getElementById('branch_field');
    if (branchFieldSelect) {
      branchFieldSelect.disabled = false;
      branchFieldSelect.style.backgroundColor = '';
      branchFieldSelect.style.cursor = '';
      branchFieldSelect.style.border = '';
      
      // 移除字段说明
      const fieldContainer = branchFieldSelect.parentElement;
      const hint = fieldContainer?.querySelector('.field-edit-hint');
      if (hint) {
        hint.remove();
      }
    }
    
    // 显示动作类型字段
    const actionTypeContainer = document.querySelector('#action_type')?.closest('.mb-3');
    if (actionTypeContainer) {
      actionTypeContainer.style.display = 'block';
    }
    
    // 清空可编辑字段选择
    if (window.ApprovalConfigForm) {
      window.ApprovalConfigForm.selectedFields = [];
      
      const selectedFieldsContainer = document.getElementById('selected_fields_container');
      if (selectedFieldsContainer) {
        selectedFieldsContainer.innerHTML = '<small class="text-muted">使用下拉框选择字段后会在此显示</small>';
      }
      
      const hiddenInput = document.getElementById('editable_fields_input');
      if (hiddenInput) {
        hiddenInput.value = '[]';
      }
    }
    
    // 清除编辑模式相关的隐藏字段
    const form = modal.querySelector('form');
    if (form) {
      const editInputs = form.querySelectorAll('#edit_mode, #edit_step_id, #edit_condition_index');
      editInputs.forEach(input => input.remove());
      
      // 重置表单
      form.reset();
    }
    
    console.log('🧹 编辑模式清理完成');
  }
  
  /**
   * 处理分支字段变化
   */
  handleBranchFieldChange(fieldSelect) {
    if (!fieldSelect) return;
    
    const fieldName = fieldSelect.value;
    console.log('分支字段变化:', fieldName);
    
    // 重置相关字段
    this.resetDependentFields();
    
    // 触发预览更新
    this.updateBranchPreview();
  }
  
  /**
   * 重置依赖字段
   */
  resetDependentFields() {
    const operatorSelect = document.getElementById('branch_operator');
    const valueInput = document.getElementById('branch_value');
    
    if (operatorSelect) operatorSelect.value = '';
    if (valueInput) valueInput.value = '';
  }
  
  /**
   * 更新分支预览
   */
  updateBranchPreview() {
    const previewElement = document.getElementById('branch_preview');
    if (!previewElement) return;
    
    // 获取当前配置
    const fieldSelect = document.getElementById('branch_field');
    const operatorSelect = document.getElementById('branch_operator');
    const valueInput = document.getElementById('branch_value');
    
    const fieldName = fieldSelect ? fieldSelect.value : '';
    const operator = operatorSelect ? operatorSelect.value : '';
    const value = valueInput ? valueInput.value : '';
    
    // 更新预览内容
    if (fieldName && operator && value) {
      previewElement.innerHTML = `
        <div class="alert alert-info">
          <strong>预览：</strong>如果 ${fieldName} ${operator} ${value}，则...
        </div>
      `;
    } else {
      previewElement.innerHTML = '<div class="text-muted">请配置完整的分支条件</div>';
    }
  }
  
  /**
   * 加载可编辑字段到编辑表单
   */
  loadEditableFields(stepData) {
    console.log('📋 开始加载可编辑字段:', stepData.editable_fields);
    console.log('🚨 [DEBUG] loadEditableFields函数已调用 - 版本2');
    
    if (!stepData.editable_fields || !Array.isArray(stepData.editable_fields) || stepData.editable_fields.length === 0) {
      console.log('ℹ️ 没有找到可编辑字段数据');
      return;
    }
    
    // 检查是否有新格式的字段选择器（徽章界面）
    const editFieldSelector = document.querySelector('#edit_field_selector');
    const editSelectedFieldsContainer = document.querySelector('#edit_selected_fields_container');
    const editEditableFieldsInput = document.querySelector('#edit_editable_fields_input');
    
    // 调试：检查所有可能的容器
    console.log('🔍 DOM元素检测结果:', {
      editFieldSelector: !!editFieldSelector,
      editSelectedFieldsContainer: !!editSelectedFieldsContainer,
      editEditableFieldsInput: !!editEditableFieldsInput,
      containerVisible: editSelectedFieldsContainer ? window.getComputedStyle(editSelectedFieldsContainer).display !== 'none' : false
    });
    
    console.log('🔍 所有可能的可编辑字段容器:', {
      'selected_fields_container': !!document.querySelector('#selected_fields_container'),
      'edit_selected_fields_container': !!document.querySelector('#edit_selected_fields_container'),
      'editable_fields_container': !!document.querySelector('#editable_fields_container'),
      'current_modal': document.querySelector('.modal.show')?.id || 'none'
    });
    
    if (editFieldSelector && editSelectedFieldsContainer && editEditableFieldsInput) {
      // 新格式：徽章界面
      console.log('📋 使用新格式徽章界面填充可编辑字段');
      
      // 清空容器并设置数据
      editSelectedFieldsContainer.innerHTML = '';
      const editableFields = stepData.editable_fields.slice(); // 复制数组
      
      // 为每个已选字段创建徽章
      editableFields.forEach((fieldCode) => {
        // 从选择器中查找对应的选项来获取显示名称
        const option = editFieldSelector.querySelector(`option[value="${fieldCode}"]`);
        let fieldName = fieldCode; // 默认使用字段代码
        
        if (option) {
          fieldName = option.textContent;
        } else {
          // 如果选择器中没有这个选项，使用字段代码映射
          fieldName = this.getFieldDisplayName(fieldCode);
        }
        
        const badge = document.createElement('span');
        badge.className = 'badge bg-primary me-2 mb-2';
        badge.setAttribute('data-field', fieldCode);
        badge.innerHTML = `${fieldName} <button type="button" class="btn-close btn-close-white ms-1" onclick="removeEditFieldBadge('${fieldCode}')" style="font-size: 0.7em;"></button>`;
        
        // 移除调试样式，使用正常的badge样式
        
        editSelectedFieldsContainer.appendChild(badge);
        console.log(`✨ 创建字段徽章: ${fieldCode} → ${fieldName}`);
      });
      
      // 调试：输出容器最终状态
      console.log('🔧 容器最终状态:', {
        containerHTML: editSelectedFieldsContainer.innerHTML,
        childrenCount: editSelectedFieldsContainer.children.length,
        containerRect: editSelectedFieldsContainer.getBoundingClientRect()
      });
      
      // 更新隐藏输入字段
      editEditableFieldsInput.value = JSON.stringify(editableFields);
      
      // 更新全局变量（如果存在）
      if (typeof window.editSelectedFields !== 'undefined') {
        window.editSelectedFields = editableFields;
      }
      
      console.log('✅ 新格式可编辑字段徽章已填充:', editableFields);
    } else {
      // 传统格式：复选框界面
      console.log('📋 使用传统格式复选框界面填充可编辑字段');
      
      stepData.editable_fields.forEach((fieldCode) => {
        const checkbox = document.querySelector(`input[name="editable_fields"][value="${fieldCode}"]`);
        if (checkbox) {
          checkbox.checked = true;
          console.log(`✅ 勾选复选框: ${fieldCode}`);
        } else {
          console.warn(`⚠️ 未找到字段复选框: ${fieldCode}`);
        }
      });
      
      console.log('✅ 传统格式可编辑字段复选框已填充');
    }
  }
  
  /**
   * 获取字段显示名称映射
   */
  getFieldDisplayName(fieldCode) {
    const fieldNames = {
      'settlement_total_discount_rate': '结算总折扣率',
      'pricing_total_discount_rate': '批价总折扣率',
      'is_direct_contract': '是否直接合同',
      'is_factory_pickup': '是否工厂提货',
      'discount_rate': '折扣率',
      'total_amount': '总金额',
      'project_type': '项目类型',
      'project_code': '项目编号',
      'project_name': '项目名称',
      'authorization_code': '授权编号'
    };
    return fieldNames[fieldCode] || fieldCode;
  }
  
  /**
   * 注意：这些映射函数需要函数专家创建统一的前端映射接口
   * 当前使用模板层面的映射，避免在前端重复硬编码
   * 
   * TODO: 请函数专家创建：
   * 1. 统一的前端访问后端映射的接口
   * 2. 将 PROJECT_TYPE_LABELS 和 ACTION_TYPE_LABELS 暴露给前端
   * 3. 提供JavaScript访问这些映射的标准方法
   */
}

// 创建全局实例
window.ApprovalConfigBranch = new ApprovalConfigBranch();

// 向后兼容：保留原有的全局函数 - 立即暴露
window.editBranchCondition = function(stepId, conditionIndex) {
  console.log(`🔧 全局函数调用 editBranchCondition: ${stepId}, ${conditionIndex}`);
  
  if (!window.ApprovalConfigBranch) {
    console.warn('⚠️ ApprovalConfigBranch 模块未加载，使用降级处理');
    alert('分支条件编辑功能正在加载中，请稍后再试');
    return;
  }
  
  return window.ApprovalConfigBranch.editBranchCondition(stepId, conditionIndex);
};

window.addNewBranch = function(stepId, branchType) {
  console.log(`🔀 全局函数调用 addNewBranch: ${stepId}, ${branchType}`);
  
  if (!window.ApprovalConfigBranch) {
    console.warn('⚠️ ApprovalConfigBranch 模块未加载');
    alert('添加分支功能正在加载中，请稍后再试');
    return;
  }
  
  return window.ApprovalConfigBranch.addNewBranch(stepId, branchType);
};

window.deleteBranchCondition = function(stepId, conditionIndex) {
  console.log(`🗑️ 全局函数调用 deleteBranchCondition: ${stepId}, ${conditionIndex}`);
  
  if (!window.ApprovalConfigBranch) {
    console.warn('⚠️ ApprovalConfigBranch 模块未加载');
    alert('删除分支功能正在加载中，请稍后再试');
    return;
  }
  
  return window.ApprovalConfigBranch.deleteBranchCondition(stepId, conditionIndex);
};

// DOM就绪时初始化
document.addEventListener('DOMContentLoaded', function() {
  // 延迟初始化，确保主模块先加载
  setTimeout(() => {
    window.ApprovalConfigBranch.init();
  }, 100);
});

console.log('📦 approval_config_branch.js 已加载');