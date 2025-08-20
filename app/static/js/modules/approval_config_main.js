/**
 * 审批配置主要功能模块
 * 负责：基本配置、权限管理、工具函数
 */

class ApprovalConfigMain {
  constructor() {
    this.config = null;
    this.initialized = false;
    
    // 绑定方法上下文
    this.init = this.init.bind(this);
    this.checkPermission = this.checkPermission.bind(this);
  }
  
  /**
   * 初始化配置
   */
  init(config) {
    this.config = config || {
      canModify: false,
      urls: {},
      csrfToken: ''
    };
    this.initialized = true;
    console.log('✅ ApprovalConfigMain 初始化完成');
  }
  
  /**
   * 权限检查
   */
  checkPermission(action = 'modify') {
    if (!this.config.canModify) {
      alert('您没有修改权限');
      return false;
    }
    return true;
  }
  
  /**
   * 获取CSRF令牌
   */
  getCsrfToken() {
    return this.config.csrfToken;
  }
  
  /**
   * 获取URL配置
   */
  getUrl(key, params = {}) {
    let url = this.config.urls[key] || '';
    
    // 替换URL中的参数占位符
    Object.keys(params).forEach(param => {
      url = url.replace(new RegExp(`\\b${param}\\b`, 'g'), params[param]);
    });
    
    return url;
  }
  
  /**
   * 创建并提交表单（用于删除操作等）
   */
  submitForm(action, data = {}) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = action;
    
    // 添加CSRF令牌
    const csrfToken = document.createElement('input');
    csrfToken.type = 'hidden';
    csrfToken.name = 'csrf_token';
    csrfToken.value = this.getCsrfToken();
    form.appendChild(csrfToken);
    
    // 添加其他数据
    Object.keys(data).forEach(key => {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = key;
      input.value = data[key];
      form.appendChild(input);
    });
    
    document.body.appendChild(form);
    form.submit();
  }
  
  /**
   * 安全的fetch请求，自动添加CSRF
   */
  async safeFetch(url, options = {}) {
    const defaultOptions = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.getCsrfToken()
      }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
      const response = await fetch(url, finalOptions);
      return await response.json();
    } catch (error) {
      console.error('网络请求错误:', error);
      throw error;
    }
  }
}

// 创建全局实例
window.ApprovalConfigMain = new ApprovalConfigMain();

// 向后兼容：保留原有的全局函数 - 立即暴露
window.confirmDeleteStep = function(stepId) {
  console.log(`🗑️ 确认删除步骤: ${stepId}`);
  
  if (!window.ApprovalConfigMain || !window.ApprovalConfigMain.checkPermission()) {
    // 降级处理：直接删除确认
    if (confirm('确定要删除该步骤吗？')) {
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = window.ApprovalConfig.urls.deleteStep.replace('0', stepId);
      
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
  
  if (confirm('确定要删除该步骤吗？')) {
    const deleteUrl = window.ApprovalConfigMain.getUrl('deleteStep', { '0': stepId });
    window.ApprovalConfigMain.submitForm(deleteUrl);
  }
};

console.log('📦 approval_config_main.js 已加载');