/*!
 * 导出信息补充模态框组件
 * 支持客户选择、联系人选择、备注编辑等功能
 */

class ExportInfoModal {
    constructor(modalId, config = {}) {
        this.modalId = modalId;
        this.config = config;
        this.modal = null;
        this.customerSelector = null;
        this.contactSelector = null;
        this.selectedData = {
            customer: null,
            contact: null,
            notes: '',
            options: []
        };
        
        this.init();
    }
    
    init() {
        console.log('🚀 初始化导出信息模态框:', this.modalId);
        console.log('🔧 配置信息:', this.config);
        
        this.modal = document.getElementById(this.modalId);
        if (!this.modal) {
            console.error(`导出信息模态框未找到: ${this.modalId}`);
            return;
        }
        console.log('✅ 模态框元素找到:', this.modal);
        
        this.initSelectors();
        this.initNotesEditor();
        this.initEventListeners();
        
        console.log('✅ 导出信息模态框初始化完成');
    }
    
    initSelectors() {
        // 初始化客户选择器
        if (this.config.customer_config && this.config.customer_config.enabled !== false) {
            this.initCustomerSelector();
        }
        
        // 初始化联系人选择器
        if (this.config.contact_config && this.config.contact_config.enabled !== false) {
            this.initContactSelector();
        }
    }
    
    initCustomerSelector() {
        const containerEl = document.getElementById(`${this.modalId}CustomerSelector`);
        if (!containerEl) {
            console.error(`❌ 客户选择器容器未找到: ${this.modalId}CustomerSelector`);
            return;
        }
        console.log('✅ 客户选择器容器找到:', containerEl);
        
        if (typeof KeywordSelector === 'undefined') {
            console.error('❌ KeywordSelector 类未定义，请检查 keyword-selector.js 是否正确加载');
            return;
        }
        
        console.log('🔧 初始化客户选择器，配置:', this.config.customer_config);
        this.customerSelector = new KeywordSelector({
            container: containerEl,
            searchEndpoint: this.config.customer_config.endpoint || '/api/export-helpers/customers/search',
            placeholder: this.config.customer_config.placeholder || '输入公司名称搜索...',
            valueField: 'id',
            labelField: 'company_name',
            searchFields: ['company_name', 'company_code'],
            minChars: 2,
            maxResults: 15,
            displayRenderer: (item) => {
                // 使用徽章风格显示企业全称
                return `<span class="badge badge-user regular rounded-pill">${item.company_name}</span>`;
            },
            resultRenderer: (item) => {
                // 自定义搜索结果显示，包含拥有者信息
                const ownerBadge = item.owner ? this.renderOwnerBadge(item.owner) : '';
                return `
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="result-main-label">${item.company_name}</div>
                        ${ownerBadge}
                    </div>
                `;
            },
            onSelect: (customer) => {
                console.log('🏢 客户选择器 - 客户已选择:', customer);
                this.selectedData.customer = customer;
                this.onCustomerSelected(customer);
            },
            onClear: () => {
                this.selectedData.customer = null;
                this.onCustomerCleared();
            }
        });
    }
    
    initContactSelector() {
        const containerEl = document.getElementById(`${this.modalId}ContactSelector`);
        if (!containerEl) {
            console.error(`❌ 联系人选择器容器未找到: ${this.modalId}ContactSelector`);
            return;
        }
        console.log('✅ 联系人选择器容器找到:', containerEl);
        
        this.contactSelector = new KeywordSelector({
            container: containerEl,
            searchEndpoint: this.config.contact_config.endpoint || '/api/export-helpers/contacts/search',
            placeholder: this.config.contact_config.placeholder || '点击展开联系人列表...',
            valueField: 'id',
            labelField: 'name',
            subLabelField: 'position',
            searchFields: ['name', 'phone', 'email'],
            minChars: 0,  // 支持点击展开
            maxResults: 15,
            autoExpandOnFocus: true,  // 聚焦时自动展开
            filters: {},
            onSelect: (contact) => {
                console.log('👤 联系人选择器 - 联系人已选择:', contact);
                this.selectedData.contact = contact;
                this.onContactSelected(contact);
            },
            onClear: () => {
                this.selectedData.contact = null;
                this.onContactCleared();
            }
        });
        
        // 如果联系人依赖客户选择，初始时禁用
        if (this.config.contact_config.depends_on_customer !== false) {
            this.disableContactSelector();
        }
    }
    
    initNotesEditor() {
        const notesEl = document.getElementById(`${this.modalId}Notes`);
        const countEl = document.getElementById(`${this.modalId}NotesCount`);
        
        if (!notesEl) return;
        
        // 字符计数
        notesEl.addEventListener('input', () => {
            if (countEl) {
                countEl.textContent = notesEl.value.length;
            }
            this.selectedData.notes = notesEl.value;
        });
        
        // 初始化默认内容
        if (this.config.notes_config && this.config.notes_config.default_content) {
            notesEl.value = this.config.notes_config.default_content;
            this.selectedData.notes = notesEl.value;
        }
    }
    
    initEventListeners() {
        // 模态框显示时的初始化
        this.modal.addEventListener('shown.bs.modal', () => {
            this.onModalShown();
        });
        
        // 模态框隐藏时的清理
        this.modal.addEventListener('hidden.bs.modal', () => {
            this.onModalHidden();
        });
        
        // 选项变化监听
        const optionInputs = this.modal.querySelectorAll('input[name="export_options"]');
        optionInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.updateSelectedOptions();
            });
        });
        
        // 初始化时收集已选中的选项
        this.updateSelectedOptions();
    }
    
    onCustomerSelected(customer) {
        console.log('客户已选择:', customer);
        
        // 如果联系人依赖客户，启用联系人选择器并更新过滤条件
        if (this.contactSelector && this.config.contact_config.depends_on_customer !== false) {
            this.enableContactSelector();
            this.contactSelector.config.filters = {
                customer_id: customer.id
            };
            this.contactSelector.clear(); // 清除之前的联系人选择
        }
        
        // 更新预览
        this.updatePreview();
    }
    
    onCustomerCleared() {
        console.log('客户选择已清除');
        
        // 如果联系人依赖客户，禁用联系人选择器
        if (this.contactSelector && this.config.contact_config.depends_on_customer !== false) {
            this.disableContactSelector();
            this.contactSelector.clear();
        }
        
        // 更新预览
        this.updatePreview();
    }
    
    onContactSelected(contact) {
        console.log('联系人已选择:', contact);
        
        // 更新预览
        this.updatePreview();
    }
    
    onContactCleared() {
        console.log('联系人选择已清除');
        
        // 更新预览
        this.updatePreview();
    }
    
    enableContactSelector() {
        if (this.contactSelector) {
            const container = this.contactSelector.container;
            container.classList.remove('disabled');
            const input = container.querySelector('.keyword-input');
            if (input) {
                input.disabled = false;
                input.placeholder = this.config.contact_config.placeholder || '输入联系人姓名搜索...';
            }
        }
    }
    
    disableContactSelector() {
        if (this.contactSelector) {
            const container = this.contactSelector.container;
            container.classList.add('disabled');
            const input = container.querySelector('.keyword-input');
            if (input) {
                input.disabled = true;
                input.placeholder = '请先选择客户';
            }
        }
    }
    
    renderOwnerBadge(owner) {
        // 根据是否为厂商用户渲染不同样式的徽章
        if (owner.is_vendor_user) {
            return `<span class="badge badge-user vendor rounded-pill">${owner.real_name || owner.username}</span>`;
        } else {
            return `<span class="badge badge-user regular">${owner.real_name || owner.username}</span>`;
        }
    }
    
    updateSelectedOptions() {
        const optionInputs = this.modal.querySelectorAll('input[name="export_options"]:checked');
        this.selectedData.options = Array.from(optionInputs).map(input => input.value);
        console.log('🔄 更新选择的选项:', this.selectedData.options);
    }
    
    updatePreview() {
        if (!this.config.previewEnabled) return;
        
        const previewEl = document.getElementById(`${this.modalId}Preview`);
        if (!previewEl) return;
        
        const { customer, contact } = this.selectedData;
        
        if (!customer && !contact) {
            previewEl.innerHTML = `
                <div class="preview-loading text-center text-muted">
                    <i class="fas fa-info-circle me-1"></i>请选择客户和联系人
                </div>
            `;
            return;
        }
        
        let previewHtml = '<div class="preview-content">';
        
        if (customer) {
            previewHtml += `
                <div class="preview-section mb-2">
                    <strong class="text-primary">客户信息：</strong>
                    <div class="ms-3">
                        <div><strong>${this.escapeHtml(customer.company_name)}</strong></div>
                        ${customer.address ? `<div class="text-muted small">${this.escapeHtml(customer.address)}</div>` : ''}
                    </div>
                </div>
            `;
        }
        
        if (contact) {
            previewHtml += `
                <div class="preview-section">
                    <strong class="text-success">联系人信息：</strong>
                    <div class="ms-3">
                        <div><strong>${this.escapeHtml(contact.name)}</strong></div>
                        ${contact.position ? `<div class="text-muted small">${this.escapeHtml(contact.position)}</div>` : ''}
                        ${contact.phone ? `<div class="text-muted small"><i class="fas fa-phone me-1"></i>${this.escapeHtml(contact.phone)}</div>` : ''}
                        ${contact.email ? `<div class="text-muted small"><i class="fas fa-envelope me-1"></i>${this.escapeHtml(contact.email)}</div>` : ''}
                    </div>
                </div>
            `;
        }
        
        previewHtml += '</div>';
        previewEl.innerHTML = previewHtml;
    }
    
    onModalShown() {
        // 聚焦到第一个可用的输入框
        if (this.customerSelector) {
            this.customerSelector.input.focus();
        } else if (this.contactSelector && !this.contactSelector.container.classList.contains('disabled')) {
            this.contactSelector.input.focus();
        } else {
            const notesEl = document.getElementById(`${this.modalId}Notes`);
            if (notesEl) {
                notesEl.focus();
            }
        }
    }
    
    onModalHidden() {
        // 清理选择状态（可选）
        // this.reset();
    }
    
    reset() {
        // 重置所有选择
        this.selectedData = {
            customer: null,
            contact: null,
            notes: '',
            options: []
        };
        
        if (this.customerSelector) {
            this.customerSelector.clear();
        }
        
        if (this.contactSelector) {
            this.contactSelector.clear();
        }
        
        const notesEl = document.getElementById(`${this.modalId}Notes`);
        if (notesEl) {
            notesEl.value = this.config.notes_config?.default_content || '';
            this.selectedData.notes = notesEl.value;
        }
        
        // 重置选项
        const optionInputs = this.modal.querySelectorAll('input[name="export_options"]');
        optionInputs.forEach(input => {
            input.checked = false;
        });
        
        this.updatePreview();
    }
    
    validate() {
        const errors = [];
        
        // 验证客户选择
        if (this.config.customer_config?.required && !this.selectedData.customer) {
            errors.push('请选择客户');
        }
        
        // 验证联系人选择
        if (this.config.contact_config?.required && !this.selectedData.contact) {
            errors.push('请选择联系人');
        }
        
        // 验证备注长度
        if (this.config.notes_config?.enabled && this.selectedData.notes) {
            const maxLength = this.config.notes_config.max_length || 1000;
            if (this.selectedData.notes.length > maxLength) {
                errors.push(`备注信息不能超过${maxLength}个字符`);
            }
        }
        
        return errors;
    }
    
    getExportData() {
        return {
            customer: this.selectedData.customer,
            contact: this.selectedData.contact,
            notes: this.selectedData.notes,
            options: this.selectedData.options
        };
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    show() {
        const modalInstance = new bootstrap.Modal(this.modal);
        modalInstance.show();
    }
    
    hide() {
        const modalInstance = bootstrap.Modal.getInstance(this.modal);
        if (modalInstance) {
            modalInstance.hide();
        }
    }
    
    confirmExport() {
        console.log('🎯 confirmExport 被调用');
        console.log('🔍 当前selectedData状态:', this.selectedData);
        
        // 验证输入
        const errors = this.validate();
        if (errors.length > 0) {
            console.error('❌ 验证失败:', errors);
            alert(`请修正以下错误：\n${errors.join('\n')}`);
            return;
        }
        
        // 获取导出数据
        const exportData = this.getExportData();
        console.log('📦 获取的导出数据:', exportData);
        console.log('📊 selectedData详情:', JSON.stringify(this.selectedData, null, 2));
        
        // 调用确认回调
        if (this.config.onConfirm) {
            console.log('📞 调用确认回调函数');
            this.config.onConfirm(exportData);
        } else {
            console.error('❌ 没有配置确认回调函数');
        }
        
        // 隐藏模态框
        this.hide();
    }
    
    validate() {
        const errors = [];
        
        // 检查必填字段
        if (this.config.customer_config && this.config.customer_config.required && !this.selectedData.customer) {
            errors.push('请选择客户');
        }
        
        if (this.config.contact_config && this.config.contact_config.required && !this.selectedData.contact) {
            errors.push('请选择联系人');
        }
        
        return errors;
    }
    
    getExportData() {
        return {
            customer: this.selectedData.customer,
            contact: this.selectedData.contact,
            notes: this.selectedData.notes || '',
            options: this.selectedData.options || []
        };
    }
    
    destroy() {
        if (this.customerSelector) {
            this.customerSelector.destroy();
        }
        
        if (this.contactSelector) {
            this.contactSelector.destroy();
        }
    }
}

// 全局导出信息模态框管理器
window.exportInfoModals = window.exportInfoModals || {};

// 初始化导出信息模态框
function initExportInfoModal(modalId, config) {
    if (window.exportInfoModals[modalId]) {
        window.exportInfoModals[modalId].destroy();
    }
    
    window.exportInfoModals[modalId] = new ExportInfoModal(modalId, config);
    return window.exportInfoModals[modalId];
}

// 显示导出信息模态框
function showExportInfoModal(modalId) {
    const modal = window.exportInfoModals[modalId];
    if (modal) {
        modal.show();
    } else {
        console.error(`导出信息模态框未初始化: ${modalId}`);
    }
}

// 关闭导出信息模态框
function closeExportInfoModal(modalId) {
    const modal = window.exportInfoModals[modalId];
    if (modal) {
        modal.hide();
    }
}

// 确认导出信息
function confirmExportInfo(modalId) {
    const modal = window.exportInfoModals[modalId];
    if (!modal) {
        console.error(`导出信息模态框未找到: ${modalId}`);
        return;
    }
    
    // 验证输入
    const errors = modal.validate();
    if (errors.length > 0) {
        alert(`请修正以下错误：\n${errors.join('\n')}`);
        return;
    }
    
    // 获取导出数据
    const exportData = modal.getExportData();
    
    // 调用配置的回调函数
    const callbackConfig = modal.config.callbackConfig;
    if (callbackConfig && callbackConfig.on_confirm) {
        if (typeof window[callbackConfig.on_confirm] === 'function') {
            window[callbackConfig.on_confirm](exportData);
        } else {
            console.error(`回调函数未找到: ${callbackConfig.on_confirm}`);
        }
    }
    
    // 关闭模态框
    modal.hide();
}

// 自动初始化页面上的导出信息模态框
document.addEventListener('DOMContentLoaded', function() {
    if (window.exportInfoModalConfigs) {
        Object.keys(window.exportInfoModalConfigs).forEach(modalId => {
            const config = window.exportInfoModalConfigs[modalId];
            initExportInfoModal(modalId, config);
        });
    }
});

// 导出供其他模块使用
window.ExportInfoModal = ExportInfoModal;
window.initExportInfoModal = initExportInfoModal;
window.showExportInfoModal = showExportInfoModal;
window.closeExportInfoModal = closeExportInfoModal;
window.confirmExportInfo = confirmExportInfo;