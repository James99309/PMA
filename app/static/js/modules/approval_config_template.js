/**
 * 审批配置模板相关功能
 * 负责：模板删除、启用/禁用、步骤排序等功能
 */

class ApprovalConfigTemplate {
  constructor() {
    this.initialized = false;
    
    // 绑定方法上下文
    this.init = this.init.bind(this);
    this.initSortable = this.initSortable.bind(this);
    this.confirmDeleteTemplate = this.confirmDeleteTemplate.bind(this);
    this.confirmToggleTemplate = this.confirmToggleTemplate.bind(this);
  }
  
  /**
   * 初始化模板功能
   */
  init() {
    if (!window.ApprovalConfigMain || !window.ApprovalConfigMain.initialized) {
      console.error('❌ ApprovalConfigMain 未初始化，模板模块无法启动');
      return;
    }
    
    // 初始化拖拽排序功能
    this.initSortable();
    
    this.initialized = true;
    console.log('✅ ApprovalConfigTemplate 初始化完成');
  }
  
  /**
   * 初始化步骤拖拽排序
   */
  initSortable() {
    // 检查是否有修改权限和Sortable库
    if (!window.ApprovalConfigMain.config.canModify || typeof Sortable === 'undefined') {
      return;
    }
    
    const stepList = document.getElementById('stepList');
    if (!stepList) return;
    
    new Sortable(stepList, {
      handle: '.handle',
      animation: 150,
      onEnd: (evt) => {
        this.handleStepReorder(stepList);
      }
    });
    
    console.log('✅ 步骤拖拽排序已初始化');
  }
  
  /**
   * 处理步骤重新排序
   */
  async handleStepReorder(stepList) {
    try {
      // 获取新的步骤顺序
      const stepIds = Array.from(stepList.querySelectorAll('li')).map(li => li.getAttribute('data-step-id'));
      
      // 获取模板ID（从URL或数据属性获取）
      const templateId = this.getCurrentTemplateId();
      if (!templateId) {
        throw new Error('无法获取模板ID');
      }
      
      // 发送AJAX请求
      const response = await fetch(`/admin/approval/template/${templateId}/reorder-steps`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': window.ApprovalConfigMain.getCsrfToken()
        },
        body: JSON.stringify({ steps: stepIds })
      });
      
      const data = await response.json();
      
      if (data.success) {
        console.log('✅ 步骤重排序成功');
        // 刷新页面显示新的顺序
        window.location.reload();
      } else {
        throw new Error(data.message || '重新排序失败');
      }
    } catch (error) {
      console.error('❌ 步骤重排序失败:', error);
      alert('操作失败，请重试');
    }
  }
  
  /**
   * 获取当前模板ID
   */
  getCurrentTemplateId() {
    // 尝试从URL路径获取
    const pathMatch = window.location.pathname.match(/\/template\/(\d+)/);
    if (pathMatch) {
      return pathMatch[1];
    }
    
    // 尝试从数据属性获取
    const templateElement = document.querySelector('[data-template-id]');
    if (templateElement) {
      return templateElement.getAttribute('data-template-id');
    }
    
    return null;
  }
  
  /**
   * 确认删除模板
   */
  confirmDeleteTemplate(templateId, templateName) {
    console.log(`🗑️ 确认删除模板: ${templateId} - ${templateName}`);
    
    if (!window.ApprovalConfigMain.checkPermission()) {
      return;
    }
    
    try {
      // 更新模态框内容
      document.getElementById('templateNameToDelete').textContent = templateName;
      document.getElementById('deleteTemplateForm').action = `/admin/approval/template/${templateId}/delete`;
      
      // 显示模态框
      const deleteModal = new bootstrap.Modal(document.getElementById('deleteTemplateModal'));
      deleteModal.show();
    } catch (error) {
      console.error('❌ 显示删除模态框失败:', error);
      alert('操作失败，请重试');
    }
  }
  
  /**
   * 确认启用/禁用模板
   */
  confirmToggleTemplate(templateId, templateName, isActive) {
    console.log(`🔄 切换模板状态: ${templateId} - ${templateName} - ${isActive ? '禁用' : '启用'}`);
    
    if (!window.ApprovalConfigMain.checkPermission()) {
      return;
    }
    
    try {
      // 更新模态框内容
      document.getElementById('templateNameToToggle').textContent = templateName;
      
      if (isActive) {
        document.getElementById('toggleActionText').textContent = '禁用';
        document.getElementById('toggleWarningText').textContent = '禁用后该模板将不能用于新的审批实例，但不会影响现有的审批流程。';
        document.getElementById('toggleIsActive').value = 'false';
        document.getElementById('toggleConfirmBtn').className = 'btn btn-warning';
      } else {
        document.getElementById('toggleActionText').textContent = '启用';
        document.getElementById('toggleWarningText').textContent = '启用后该模板将可以用于创建新的审批实例。';
        document.getElementById('toggleIsActive').value = 'true';
        document.getElementById('toggleConfirmBtn').className = 'btn btn-success';
      }
      
      document.getElementById('toggleTemplateForm').action = `/admin/approval/template/${templateId}/toggle`;
      
      // 显示模态框
      const toggleModal = new bootstrap.Modal(document.getElementById('toggleTemplateModal'));
      toggleModal.show();
    } catch (error) {
      console.error('❌ 显示切换模态框失败:', error);
      alert('操作失败，请重试');
    }
  }
}

// 创建全局实例
window.ApprovalConfigTemplate = new ApprovalConfigTemplate();

// 向后兼容：保留原有的全局函数 - 立即暴露
window.confirmDeleteTemplate = function(templateId, templateName) {
  console.log(`🗑️ 全局函数调用 confirmDeleteTemplate: ${templateId}, ${templateName}`);
  
  if (!window.ApprovalConfigTemplate) {
    console.warn('⚠️ ApprovalConfigTemplate 模块未加载，使用降级处理');
    
    if (confirm(`确定要删除模板 "${templateName}" 吗？`)) {
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = window.ApprovalConfig.urls.deleteTemplate.replace('0', templateId);
      
      const csrfToken = document.createElement('input');
      csrfToken.type = 'hidden';
      csrfToken.name = 'csrf_token';
      csrfToken.value = window.ApprovalConfig.csrfToken;
      form.appendChild(csrfToken);
      
      document.body.appendChild(form);
      form.submit();
    }
    return;
  }
  
  return window.ApprovalConfigTemplate.confirmDeleteTemplate(templateId, templateName);
};

window.confirmToggleTemplate = function(templateId, templateName, isActive) {
  console.log(`🔄 全局函数调用 confirmToggleTemplate: ${templateId}, ${templateName}, ${isActive}`);
  
  if (!window.ApprovalConfigTemplate) {
    console.warn('⚠️ ApprovalConfigTemplate 模块未加载，使用降级处理');
    
    const action = isActive ? '禁用' : '启用';
    if (confirm(`确定要${action}模板 "${templateName}" 吗？`)) {
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = window.ApprovalConfig.urls.toggleTemplate.replace('0', templateId);
      
      const csrfToken = document.createElement('input');
      csrfToken.type = 'hidden';
      csrfToken.name = 'csrf_token';
      csrfToken.value = window.ApprovalConfig.csrfToken;
      form.appendChild(csrfToken);
      
      const isActiveInput = document.createElement('input');
      isActiveInput.type = 'hidden';
      isActiveInput.name = 'is_active';
      isActiveInput.value = !isActive;
      form.appendChild(isActiveInput);
      
      document.body.appendChild(form);
      form.submit();
    }
    return;
  }
  
  return window.ApprovalConfigTemplate.confirmToggleTemplate(templateId, templateName, isActive);
};

// DOM就绪时初始化
document.addEventListener('DOMContentLoaded', function() {
  // 延迟初始化，确保主模块先加载
  setTimeout(() => {
    window.ApprovalConfigTemplate.init();
  }, 150);
});

console.log('📦 approval_config_template.js 已加载');