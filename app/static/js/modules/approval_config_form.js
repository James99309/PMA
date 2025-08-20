/**
 * 审批配置表单功能模块
 * 负责：添加步骤表单、字段选择、分支配置等功能
 */

class ApprovalConfigForm {
  constructor() {
    this.initialized = false;
    this.selectedFields = [];
    this.editSelectedFields = [];
    
    // 绑定方法上下文
    this.init = this.init.bind(this);
    this.createFieldBadge = this.createFieldBadge.bind(this);
    this.addFieldBadge = this.addFieldBadge.bind(this);
    this.removeFieldBadge = this.removeFieldBadge.bind(this);
    this.handleStepTypeChange = this.handleStepTypeChange.bind(this);
    this.handleBranchFieldChange = this.handleBranchFieldChange.bind(this);
    this.handleBranchOperatorChange = this.handleBranchOperatorChange.bind(this);
  }
  
  /**
   * 初始化表单功能
   */
  init() {
    if (!window.ApprovalConfigMain || !window.ApprovalConfigMain.initialized) {
      console.error('❌ ApprovalConfigMain 未初始化，表单模块无法启动');
      return;
    }
    
    this.initialized = true;
    console.log('✅ ApprovalConfigForm 初始化完成');
  }
  
  /**
   * 创建字段徽章HTML
   */
  createFieldBadge(fieldCode, fieldName, group) {
    const groupColor = group === 'master' ? '#007bff' : '#28a745';
    const groupLabel = group === 'master' ? '主' : '明';
    return `<span class="badge me-1 mb-1" style="background-color: ${groupColor}; color: white; font-size: 0.8rem;" data-field="${fieldCode}">
      <small>${groupLabel}</small> ${fieldName} 
      <i class="fas fa-times ms-1" style="cursor: pointer;" onclick="window.ApprovalConfigForm.removeFieldBadge('${fieldCode}')"></i>
    </span>`;
  }
  
  /**
   * 添加字段徽章（添加步骤）
   */
  addFieldBadge() {
    const selector = document.getElementById('field_selector');
    const container = document.getElementById('selected_fields_container');
    const hiddenInput = document.getElementById('editable_fields_input');
    
    if (!selector || !selector.value) return;
    
    const fieldCode = selector.value;
    const selectedOption = selector.options[selector.selectedIndex];
    const fieldName = selectedOption.textContent.split(' ')[1]; // 移除前缀 [主] 或 [明]
    const group = selectedOption.textContent.includes('[主]') ? 'master' : 'detail';
    
    // 检查是否已选择
    if (this.selectedFields.includes(fieldCode)) {
      alert('字段已选择');
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
    hiddenInput.value = JSON.stringify(this.selectedFields);
    
    // 重置选择器
    selector.value = '';
  }
  
  /**
   * 移除字段徽章（添加步骤）
   */
  removeFieldBadge(fieldCode) {
    const container = document.getElementById('selected_fields_container');
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
    hiddenInput.value = JSON.stringify(this.selectedFields);
  }
  
  /**
   * 添加字段徽章（编辑步骤）
   */
  addEditFieldBadge() {
    const selector = document.getElementById('edit_field_selector');
    const container = document.getElementById('edit_selected_fields_container');
    const hiddenInput = document.getElementById('edit_editable_fields_input');
    
    if (!selector || !selector.value) return;
    
    const fieldCode = selector.value;
    const selectedOption = selector.options[selector.selectedIndex];
    const fieldName = selectedOption.textContent.split(' ')[1]; // 移除前缀 [主] 或 [明]
    const group = selectedOption.textContent.includes('[主]') ? 'master' : 'detail';
    
    // 检查是否已选择
    if (this.editSelectedFields.includes(fieldCode)) {
      alert('字段已选择');
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
    hiddenInput.value = JSON.stringify(this.editSelectedFields);
    
    // 重置选择器
    selector.value = '';
  }
  
  /**
   * 创建编辑字段徽章HTML
   */
  createEditFieldBadge(fieldCode, fieldName, group) {
    const groupColor = group === 'master' ? '#007bff' : '#28a745';
    const groupLabel = group === 'master' ? '主' : '明';
    return `<span class="badge me-1 mb-1" style="background-color: ${groupColor}; color: white; font-size: 0.8rem;" data-field="${fieldCode}">
      <small>${groupLabel}</small> ${fieldName} 
      <i class="fas fa-times ms-1" style="cursor: pointer;" onclick="window.ApprovalConfigForm.removeEditFieldBadge('${fieldCode}')"></i>
    </span>`;
  }
  
  /**
   * 移除编辑字段徽章
   */
  removeEditFieldBadge(fieldCode) {
    const container = document.getElementById('edit_selected_fields_container');
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
    hiddenInput.value = JSON.stringify(this.editSelectedFields);
  }
  
  /**
   * 处理步骤类型变化
   */
  handleStepTypeChange() {
    const stepType = document.getElementById('step_type').value;
    const branchConfigSection = document.getElementById('branch_config_section');
    const branchPreviewSection = document.getElementById('branch_preview_section');
    const normalApproverSection = document.getElementById('normal_approver_section');
    const actionTypeField = document.getElementById('action_type');
    const approverSelectionField = document.getElementById('approver_selection');
    const approverTypeField = document.getElementById('approver_type');
    
    if (stepType === 'branch') {
      // 分支步骤
      if (branchConfigSection) branchConfigSection.style.display = 'block';
      if (branchPreviewSection) branchPreviewSection.style.display = 'none';
      if (normalApproverSection) normalApproverSection.style.display = 'none';
      if (actionTypeField) {
        actionTypeField.value = 'branch_decision';
        actionTypeField.disabled = true;
      }
      
      // 设置分支步骤的审批人类型
      if (approverTypeField) {
        approverTypeField.value = 'branch';
      }
      
      // 移除审批人选择字段的必填验证
      if (approverSelectionField) {
        approverSelectionField.removeAttribute('required');
        approverSelectionField.value = '';
      }
      
      // 加载字段选项
      this.loadBranchFields();
    } else {
      // 常规步骤
      if (branchConfigSection) branchConfigSection.style.display = 'none';
      if (branchPreviewSection) branchPreviewSection.style.display = 'none';
      if (normalApproverSection) normalApproverSection.style.display = 'block';
      if (actionTypeField) {
        actionTypeField.value = 'approve';
        actionTypeField.disabled = false;
      }
      
      // 恢复审批人选择字段的必填验证
      if (approverSelectionField) {
        approverSelectionField.setAttribute('required', 'required');
      }
    }
  }
  
  /**
   * 处理分支字段变化
   */
  handleBranchFieldChange() {
    const fieldSelect = document.getElementById('branch_field');
    if (!fieldSelect) return;
    
    const fieldName = fieldSelect.value;
    console.log('分支字段变化:', fieldName);
    
    // 重置相关字段
    this.resetDependentFields();
    
    // 触发预览更新
    this.updateBranchPreview();
  }
  
  /**
   * 处理分支操作符变化
   */
  handleBranchOperatorChange() {
    const operatorSelect = document.getElementById('branch_operator');
    const valueInputSection = document.getElementById('branch_value_input_section');
    const valueSelectSection = document.getElementById('branch_value_select_section');
    const valueMultiselectSection = document.getElementById('branch_value_multiselect_section');
    
    if (!operatorSelect) return;
    
    const operator = operatorSelect.value;
    
    // 隐藏所有输入类型
    if (valueInputSection) valueInputSection.style.display = 'none';
    if (valueSelectSection) valueSelectSection.style.display = 'none';
    if (valueMultiselectSection) valueMultiselectSection.style.display = 'none';
    
    // 根据操作符显示相应的输入类型
    if (['equals_from_list'].includes(operator)) {
      if (valueSelectSection) valueSelectSection.style.display = 'block';
      this.loadFieldValues();
    } else if (['in_from_list'].includes(operator)) {
      if (valueMultiselectSection) valueMultiselectSection.style.display = 'block';
      this.loadFieldValues();
    } else if (['is_null', 'is_not_null', 'is_empty', 'is_not_empty'].includes(operator)) {
      // 这些操作符不需要值输入
    } else {
      if (valueInputSection) valueInputSection.style.display = 'block';
    }
    
    // 更新预览
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
    
    const fieldName = fieldSelect ? fieldSelect.options[fieldSelect.selectedIndex]?.text || '' : '';
    const operator = operatorSelect ? operatorSelect.options[operatorSelect.selectedIndex]?.text || '' : '';
    const value = valueInput ? valueInput.value : '';
    
    // 更新预览内容
    if (fieldName && operator && (value || ['为空', '非空', '为空字符串', '非空字符串'].includes(operator))) {
      previewElement.innerHTML = `
        <div class="alert alert-info">
          <strong>预览：</strong>如果 ${fieldName} ${operator} ${value || '(无需值)'}，则...
        </div>
      `;
    } else {
      previewElement.innerHTML = '<div class="text-muted">请配置完整的分支条件</div>';
    }
  }
  
  /**
   * 加载分支字段选项
   */
  async loadBranchFields() {
    const fieldSelect = document.getElementById('branch_field');
    if (!fieldSelect) return;
    
    try {
      // 从后端API获取项目表的字段选项
      console.log('🔄 开始从后端获取项目字段选项...');
      
      const response = await fetch('/admin/approval/field-options/project', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('📋 后端字段数据:', data);
        
        if (data.success && data.fields) {
          fieldSelect.innerHTML = '<option value="">请选择字段...</option>';
          
          data.fields.forEach(field => {
            const option = document.createElement('option');
            option.value = field.name;        // 字段代码
            option.textContent = field.display_name;  // 中文显示名称
            fieldSelect.appendChild(option);
            console.log(`📝 添加字段选项: ${field.name} → ${field.display_name}`);
          });
          
          console.log('✅ 字段选项加载完成，总数:', data.fields.length);
        } else {
          console.error('❌ 后端返回数据格式异常:', data);
        }
      } else {
        console.error('❌ 字段选项API请求失败:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('❌ 加载字段选项网络错误:', error);
    }
  }
  
  /**
   * 加载字段值选项
   */
  async loadFieldValues() {
    const fieldSelect = document.getElementById('branch_field');
    const valueSelect = document.getElementById('branch_value_select');
    const valueCheckboxes = document.getElementById('branch_value_checkboxes');
    
    if (!fieldSelect || !fieldSelect.value) return;
    
    const fieldName = fieldSelect.value;
    console.log('🔄 开始加载字段值选项:', fieldName);
    
    try {
      // 调用后端API获取字段的去重值
      const response = await fetch(`/admin/approval/api/get-field-values?object_type=project&field_name=${encodeURIComponent(fieldName)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('📋 字段值数据:', data);
        
        if (data.success && data.values) {
          // 更新单选下拉框
          if (valueSelect) {
            valueSelect.innerHTML = '<option value="">请选择...</option>';
            data.values.forEach(valueItem => {
              const option = document.createElement('option');
              option.value = valueItem.value;        // 实际值
              option.textContent = valueItem.display; // 显示值（可能是映射后的中文）
              option.title = `使用次数: ${valueItem.count}`;  // 显示使用频次
              valueSelect.appendChild(option);
              console.log(`📝 添加选项: ${valueItem.value} → ${valueItem.display} (${valueItem.count}次)`);
            });
          }
          
          // 更新多选复选框
          if (valueCheckboxes) {
            valueCheckboxes.innerHTML = '';
            data.values.forEach((valueItem, index) => {
              const checkboxWrapper = document.createElement('div');
              checkboxWrapper.className = 'form-check';
              
              const checkbox = document.createElement('input');
              checkbox.type = 'checkbox';
              checkbox.className = 'form-check-input';
              checkbox.id = `branch_value_check_${index}`;
              checkbox.value = valueItem.value;
              
              const label = document.createElement('label');
              label.className = 'form-check-label';
              label.setAttribute('for', checkbox.id);
              label.textContent = `${valueItem.display} (${valueItem.count})`;
              
              checkboxWrapper.appendChild(checkbox);
              checkboxWrapper.appendChild(label);
              valueCheckboxes.appendChild(checkboxWrapper);
              
              console.log(`☑️ 添加复选框: ${valueItem.value} → ${valueItem.display}`);
            });
          }
          
          console.log(`✅ 字段值选项加载完成，共 ${data.values.length} 个选项`);
        } else {
          console.error('❌ 后端返回数据格式异常:', data);
        }
      } else {
        console.error('❌ 字段值API请求失败:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('❌ 加载字段值网络错误:', error);
    }
  }
}

// 创建全局实例
window.ApprovalConfigForm = new ApprovalConfigForm();

// 向后兼容：保留原有的全局函数 - 立即暴露
window.addFieldBadge = function() {
  if (!window.ApprovalConfigForm) {
    console.warn('⚠️ ApprovalConfigForm 模块未加载');
    return;
  }
  return window.ApprovalConfigForm.addFieldBadge();
};

window.removeFieldBadge = function(fieldCode) {
  if (!window.ApprovalConfigForm) {
    console.warn('⚠️ ApprovalConfigForm 模块未加载');
    return;
  }
  return window.ApprovalConfigForm.removeFieldBadge(fieldCode);
};

window.addEditFieldBadge = function() {
  if (!window.ApprovalConfigForm) {
    console.warn('⚠️ ApprovalConfigForm 模块未加载');
    return;
  }
  return window.ApprovalConfigForm.addEditFieldBadge();
};

window.removeEditFieldBadge = function(fieldCode) {
  if (!window.ApprovalConfigForm) {
    console.warn('⚠️ ApprovalConfigForm 模块未加载');
    return;
  }
  return window.ApprovalConfigForm.removeEditFieldBadge(fieldCode);
};

window.handleStepTypeChange = function() {
  if (!window.ApprovalConfigForm) {
    console.warn('⚠️ ApprovalConfigForm 模块未加载');
    return;
  }
  return window.ApprovalConfigForm.handleStepTypeChange();
};

window.handleBranchFieldChange = function() {
  if (!window.ApprovalConfigForm) {
    console.warn('⚠️ ApprovalConfigForm 模块未加载');
    return;
  }
  return window.ApprovalConfigForm.handleBranchFieldChange();
};

window.handleBranchOperatorChange = function() {
  if (!window.ApprovalConfigForm) {
    console.warn('⚠️ ApprovalConfigForm 模块未加载');
    return;
  }
  return window.ApprovalConfigForm.handleBranchOperatorChange();
};

// DOM就绪时初始化
document.addEventListener('DOMContentLoaded', function() {
  // 延迟初始化，确保主模块先加载
  setTimeout(() => {
    window.ApprovalConfigForm.init();
  }, 200);
});

console.log('📦 approval_config_form.js 已加载');