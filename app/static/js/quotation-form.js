/**
 * 报价单表单业务逻辑
 * 用于 Tailwind 版本的报价单创建和编辑页面
 *
 * 功能：
 * - 项目搜索和选择
 * - 客户/联系人联动加载
 * - 产品明细管理（通过 EditableTable 组件）
 * - 表单数据收集和提交
 */

window.QuotationForm = (function() {
    'use strict';

    // ============================================
    // 配置和状态
    // ============================================
    let config = {
        mode: 'create',  // 'create' | 'edit'
        quotationId: null,
        presetProjectId: null,
        presetCustomerId: null,
        apiEndpoints: {
            searchProjects: '/api/v1/search/projects/without-quotations',
            searchProjectsAll: '/api/v1/search/projects',
            projectCustomers: '/project/api/customer_associations/{projectId}/search',
            customerContacts: '/api/customers/{customerId}/contacts',
            createQuotation: '/quotation/create',
            updateQuotation: '/quotation/{id}/edit'
        },
        i18n: {
            loading: '加载中...',
            pleaseSelectProject: '-- 请先选择项目 --',
            pleaseSelectCustomer: '请选择客户',
            noCustomersFound: '该项目暂无关联客户',
            pleaseSelectContact: '请选择联系人',
            noContactsFound: '该客户暂无联系人',
            loadFailed: '加载失败',
            searchPlaceholder: '输入项目名称或授权码进行搜索...',
            submitSuccess: '提交成功',
            submitFailed: '提交失败',
            validationFailed: '请检查必填项',
            projectRequired: '请选择关联项目',
            customerRequired: '请选择客户',
            productRequired: '请至少添加一个产品'
        },
        onSubmitSuccess: null,
        onSubmitError: null
    };

    let state = {
        selectedProject: null,
        selectedCustomer: null,
        selectedContact: null,
        searchTimeout: null,
        isSearching: false
    };

    // ============================================
    // 初始化
    // ============================================

    /**
     * 初始化报价单表单
     * @param {Object} options - 配置选项
     */
    function init(options = {}) {
        // 合并配置
        config = { ...config, ...options };
        if (options.apiEndpoints) {
            config.apiEndpoints = { ...config.apiEndpoints, ...options.apiEndpoints };
        }
        if (options.i18n) {
            config.i18n = { ...config.i18n, ...options.i18n };
        }

        // 编辑模式使用不同的项目搜索API（允许搜索已有报价单的项目）
        if (config.mode === 'edit') {
            config.apiEndpoints.searchProjects = config.apiEndpoints.searchProjectsAll;
        }

        // 绑定事件
        bindEvents();

        // 如果有预设项目，加载项目关联的客户
        if (config.presetProjectId) {
            loadProjectCustomers(config.presetProjectId);
        }

        console.log('QuotationForm initialized:', config.mode);
    }

    /**
     * 绑定事件监听器
     */
    function bindEvents() {
        // 项目搜索输入
        const projectSearch = document.getElementById('projectSearch');
        if (projectSearch) {
            projectSearch.addEventListener('input', debounce(handleProjectSearch, 300));
            projectSearch.addEventListener('focus', () => {
                if (projectSearch.value.length >= 2) {
                    searchProjects(projectSearch.value);
                }
            });
            projectSearch.addEventListener('blur', () => {
                // 延迟隐藏，允许点击结果
                setTimeout(() => hideProjectDropdown(), 200);
            });
        }

        // 客户选择变化
        const customerSelect = document.getElementById('customer_id');
        if (customerSelect) {
            customerSelect.addEventListener('change', handleCustomerChange);
        }

        // 表单提交
        const form = document.getElementById('quotationForm');
        if (form) {
            form.addEventListener('submit', handleFormSubmit);
        }

        // 货币选择变化
        const currencySelect = document.getElementById('currency');
        if (currencySelect) {
            currencySelect.addEventListener('change', handleCurrencyChange);
        }

        // 点击外部关闭下拉框
        document.addEventListener('click', (e) => {
            const dropdown = document.getElementById('projectDropdown');
            const searchInput = document.getElementById('projectSearch');
            if (dropdown && searchInput && !dropdown.contains(e.target) && e.target !== searchInput) {
                hideProjectDropdown();
            }
        });
    }

    // ============================================
    // 项目搜索
    // ============================================

    /**
     * 处理项目搜索输入
     * @param {Event} e - 输入事件
     */
    function handleProjectSearch(e) {
        const keyword = e.target.value.trim();
        if (keyword.length >= 2) {
            searchProjects(keyword);
        } else {
            hideProjectDropdown();
        }
    }

    /**
     * 搜索项目
     * @param {string} keyword - 搜索关键词
     */
    async function searchProjects(keyword) {
        if (state.isSearching) return;
        state.isSearching = true;

        const dropdown = document.getElementById('projectDropdown');
        const results = document.getElementById('projectResults');

        if (!dropdown || !results) return;

        // 显示加载状态
        results.innerHTML = `
            <div class="px-4 py-3 text-sm text-slate-500 dark:text-slate-400">
                <span class="material-symbols-outlined text-sm animate-spin mr-2">progress_activity</span>
                ${config.i18n.loading}
            </div>
        `;
        dropdown.classList.remove('hidden');

        try {
            const response = await fetch(`${config.apiEndpoints.searchProjects}?q=${encodeURIComponent(keyword)}&limit=10`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            renderProjectResults(data.results || []);
        } catch (error) {
            console.error('搜索项目失败:', error);
            results.innerHTML = `
                <div class="px-4 py-3 text-sm text-red-500">
                    ${config.i18n.loadFailed}
                </div>
            `;
        } finally {
            state.isSearching = false;
        }
    }

    /**
     * 渲染项目搜索结果
     * @param {Array} projects - 项目列表
     */
    function renderProjectResults(projects) {
        const results = document.getElementById('projectResults');
        if (!results) return;

        if (projects.length === 0) {
            results.innerHTML = `
                <div class="px-4 py-3 text-sm text-slate-500 dark:text-slate-400">
                    暂无匹配的项目
                </div>
            `;
            return;
        }

        results.innerHTML = projects.map(project => `
            <div class="px-4 py-2.5 hover:bg-slate-100 dark:hover:bg-slate-700 cursor-pointer transition-colors"
                 data-project-id="${project.id}"
                 data-project='${JSON.stringify(project).replace(/'/g, "&#39;")}'>
                <p class="text-sm font-medium text-slate-900 dark:text-white">${escapeHtml(project.project_name)}</p>
                <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    ${project.owner_name || ''} ${project.project_type_label || ''} ${project.current_stage_label || ''}
                </p>
            </div>
        `).join('');

        // 绑定点击事件
        results.querySelectorAll('[data-project-id]').forEach(item => {
            item.addEventListener('click', () => {
                const project = JSON.parse(item.dataset.project.replace(/&#39;/g, "'"));
                selectProject(project);
            });
        });
    }

    /**
     * 选择项目
     * @param {Object} project - 项目对象
     */
    function selectProject(project) {
        state.selectedProject = project;

        // 更新UI
        const searchInput = document.getElementById('projectSearch');
        const projectIdInput = document.getElementById('project_id');
        const selectedInfo = document.getElementById('selectedProjectInfo');
        const selectedName = document.getElementById('selectedProjectName');
        const selectedMeta = document.getElementById('selectedProjectMeta');

        if (searchInput) searchInput.value = project.project_name;
        if (projectIdInput) projectIdInput.value = project.id;

        if (selectedInfo) {
            selectedInfo.classList.remove('hidden');
            if (selectedName) selectedName.textContent = project.project_name;
            if (selectedMeta) {
                selectedMeta.textContent = [
                    project.owner_name,
                    project.project_type_label,
                    project.current_stage_label
                ].filter(Boolean).join(' | ');
            }
        }

        hideProjectDropdown();

        // 加载项目关联的客户
        loadProjectCustomers(project.id);

        // 触发自定义事件
        document.dispatchEvent(new CustomEvent('projectSelected', { detail: { project } }));
    }

    /**
     * 清除项目选择
     */
    function clearProject() {
        state.selectedProject = null;

        // 更新UI
        const searchInput = document.getElementById('projectSearch');
        const projectIdInput = document.getElementById('project_id');
        const selectedInfo = document.getElementById('selectedProjectInfo');

        if (searchInput) {
            searchInput.value = '';
            searchInput.readOnly = false;
        }
        if (projectIdInput) projectIdInput.value = '';
        if (selectedInfo) selectedInfo.classList.add('hidden');

        // 清空客户和联系人
        clearCustomerSelector();
        clearContactSelector();

        // 触发自定义事件
        document.dispatchEvent(new CustomEvent('projectCleared'));
    }

    /**
     * 隐藏项目下拉框
     */
    function hideProjectDropdown() {
        const dropdown = document.getElementById('projectDropdown');
        if (dropdown) dropdown.classList.add('hidden');
    }

    // ============================================
    // 客户联动
    // ============================================

    /**
     * 加载项目关联的客户
     * @param {number} projectId - 项目ID
     */
    async function loadProjectCustomers(projectId) {
        const customerSelect = document.getElementById('customer_id');
        if (!customerSelect) return;

        // 显示加载状态
        customerSelect.innerHTML = `<option value="">${config.i18n.loading}</option>`;
        customerSelect.disabled = true;

        try {
            const url = config.apiEndpoints.projectCustomers.replace('{projectId}', projectId);
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            renderCustomerOptions(data.results || []);

            // 如果有预设客户，自动选中
            if (config.presetCustomerId) {
                customerSelect.value = config.presetCustomerId;
                handleCustomerChange({ target: customerSelect });
            }
        } catch (error) {
            console.error('加载客户失败:', error);
            customerSelect.innerHTML = `<option value="">${config.i18n.loadFailed}</option>`;
            customerSelect.disabled = true;
        }
    }

    /**
     * 渲染客户选项
     * @param {Array} customers - 客户列表
     */
    function renderCustomerOptions(customers) {
        const customerSelect = document.getElementById('customer_id');
        if (!customerSelect) return;

        if (customers.length === 0) {
            customerSelect.innerHTML = `<option value="">${config.i18n.noCustomersFound}</option>`;
            customerSelect.disabled = true;
            return;
        }

        customerSelect.innerHTML = `<option value="">${config.i18n.pleaseSelectCustomer}</option>`;
        customers.forEach(customer => {
            const option = document.createElement('option');
            option.value = customer.id;
            option.textContent = customer.company_name;
            if (customer.contact_person) {
                option.textContent += ` - ${customer.contact_person}`;
            }
            customerSelect.appendChild(option);
        });
        customerSelect.disabled = false;
    }

    /**
     * 清空客户选择器
     */
    function clearCustomerSelector() {
        const customerSelect = document.getElementById('customer_id');
        if (customerSelect) {
            customerSelect.innerHTML = `<option value="">${config.i18n.pleaseSelectProject}</option>`;
            customerSelect.disabled = true;
        }
        state.selectedCustomer = null;
    }

    /**
     * 处理客户选择变化
     * @param {Event} e - 事件对象
     */
    function handleCustomerChange(e) {
        const customerId = e.target.value;
        state.selectedCustomer = customerId;

        if (customerId) {
            loadCustomerContacts(customerId);
        } else {
            clearContactSelector();
        }

        // 触发自定义事件
        document.dispatchEvent(new CustomEvent('customerChanged', { detail: { customerId } }));
    }

    // ============================================
    // 联系人联动
    // ============================================

    /**
     * 加载客户联系人
     * @param {number} customerId - 客户ID
     */
    async function loadCustomerContacts(customerId) {
        const contactSelect = document.getElementById('contact_id');
        if (!contactSelect) return;

        // 显示加载状态
        contactSelect.innerHTML = `<option value="">${config.i18n.loading}</option>`;
        contactSelect.disabled = true;

        try {
            const url = config.apiEndpoints.customerContacts.replace('{customerId}', customerId);
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            renderContactOptions(data.contacts || []);
        } catch (error) {
            console.error('加载联系人失败:', error);
            contactSelect.innerHTML = `<option value="">${config.i18n.loadFailed}</option>`;
            contactSelect.disabled = true;
        }
    }

    /**
     * 渲染联系人选项
     * @param {Array} contacts - 联系人列表
     */
    function renderContactOptions(contacts) {
        const contactSelect = document.getElementById('contact_id');
        if (!contactSelect) return;

        if (contacts.length === 0) {
            contactSelect.innerHTML = `<option value="">${config.i18n.noContactsFound}</option>`;
            contactSelect.disabled = true;
            return;
        }

        contactSelect.innerHTML = `<option value="">${config.i18n.pleaseSelectContact}</option>`;
        contacts.forEach(contact => {
            const option = document.createElement('option');
            option.value = contact.id;
            option.textContent = contact.name;
            if (contact.position) {
                option.textContent += ` (${contact.position})`;
            }
            contactSelect.appendChild(option);
        });
        contactSelect.disabled = false;
    }

    /**
     * 清空联系人选择器
     */
    function clearContactSelector() {
        const contactSelect = document.getElementById('contact_id');
        if (contactSelect) {
            contactSelect.innerHTML = `<option value="">${config.i18n.pleaseSelectCustomer}</option>`;
            contactSelect.disabled = true;
        }
        state.selectedContact = null;
    }

    // ============================================
    // 货币处理
    // ============================================

    /**
     * 处理货币选择变化
     * @param {Event} e - 事件对象
     */
    function handleCurrencyChange(e) {
        const currency = e.target.value;
        const currencyLabel = document.getElementById('currencyLabel');
        if (currencyLabel) {
            currencyLabel.textContent = currency;
        }

        // 触发自定义事件，让可编辑表格更新
        document.dispatchEvent(new CustomEvent('currencyChanged', { detail: { currency } }));
    }

    // ============================================
    // 表单提交
    // ============================================

    /**
     * 处理表单提交
     * @param {Event} e - 提交事件
     */
    async function handleFormSubmit(e) {
        e.preventDefault();

        // 验证表单
        if (!validateForm()) {
            return;
        }

        // 收集数据
        const formData = collectFormData();

        // 提交
        await submitForm(formData);
    }

    /**
     * 验证表单
     * @returns {boolean} 是否有效
     */
    function validateForm() {
        const errors = [];

        // 验证项目
        const projectId = document.getElementById('project_id')?.value;
        if (!projectId) {
            errors.push(config.i18n.projectRequired);
        }

        // 验证客户
        const customerId = document.getElementById('customer_id')?.value;
        if (!customerId) {
            errors.push(config.i18n.customerRequired);
        }

        // 验证产品明细（通过 EditableTable）
        if (window.EditableTable) {
            const tableData = window.EditableTable.getData();
            if (!tableData || tableData.length === 0) {
                errors.push(config.i18n.productRequired);
            }
        }

        if (errors.length > 0) {
            showMessage(errors.join('\n'), 'error');
            return false;
        }

        return true;
    }

    /**
     * 收集表单数据
     * @returns {Object} 表单数据
     */
    function collectFormData() {
        const data = {
            project_id: document.getElementById('project_id')?.value,
            customer_id: document.getElementById('customer_id')?.value,
            contact_id: document.getElementById('contact_id')?.value || null,
            currency: document.getElementById('currency')?.value || 'CNY',
            notes: document.getElementById('notes')?.value || '',
            details: []
        };

        // 获取产品明细
        if (window.EditableTable) {
            data.details = window.EditableTable.getData();
        }

        // 计算总金额
        data.total_amount = data.details.reduce((sum, item) => {
            return sum + (parseFloat(item.total_price) || 0);
        }, 0);

        // 编辑模式添加ID
        if (config.mode === 'edit' && config.quotationId) {
            data.quotation_id = config.quotationId;
        }

        return data;
    }

    /**
     * 提交表单
     * @param {Object} data - 表单数据
     */
    async function submitForm(data) {
        // 显示加载状态
        const submitBtn = document.querySelector('[type="submit"]');
        const originalText = submitBtn?.textContent;
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <span class="material-symbols-outlined text-sm animate-spin mr-1">progress_activity</span>
                ${config.i18n.loading}
            `;
        }

        try {
            const url = config.mode === 'edit'
                ? config.apiEndpoints.updateQuotation.replace('{id}', config.quotationId)
                : config.apiEndpoints.createQuotation;

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                credentials: 'same-origin',
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                showMessage(config.i18n.submitSuccess, 'success');

                if (config.onSubmitSuccess) {
                    config.onSubmitSuccess(result);
                } else if (result.redirect_url) {
                    window.location.href = result.redirect_url;
                }
            } else {
                throw new Error(result.message || config.i18n.submitFailed);
            }
        } catch (error) {
            console.error('提交失败:', error);
            showMessage(error.message || config.i18n.submitFailed, 'error');

            if (config.onSubmitError) {
                config.onSubmitError(error);
            }
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        }
    }

    // ============================================
    // 编辑模式数据填充
    // ============================================

    /**
     * 填充表单数据（编辑模式）
     * @param {Object} quotation - 报价单数据
     */
    function populateFormData(quotation) {
        if (!quotation) return;

        // 填充项目信息
        if (quotation.project) {
            state.selectedProject = quotation.project;
            const searchInput = document.getElementById('projectSearch');
            const projectIdInput = document.getElementById('project_id');
            const selectedInfo = document.getElementById('selectedProjectInfo');
            const selectedName = document.getElementById('selectedProjectName');
            const selectedMeta = document.getElementById('selectedProjectMeta');

            if (searchInput) searchInput.value = quotation.project.project_name;
            if (projectIdInput) projectIdInput.value = quotation.project.id;

            if (selectedInfo) {
                selectedInfo.classList.remove('hidden');
                if (selectedName) selectedName.textContent = quotation.project.project_name;
                if (selectedMeta) {
                    selectedMeta.textContent = [
                        quotation.project.owner_name,
                        quotation.project.project_type_label,
                        quotation.project.current_stage_label
                    ].filter(Boolean).join(' | ');
                }
            }
        }

        // 填充客户和联系人
        if (quotation.customer_id) {
            const customerSelect = document.getElementById('customer_id');
            if (customerSelect) {
                customerSelect.value = quotation.customer_id;
            }
        }

        if (quotation.contact_id) {
            const contactSelect = document.getElementById('contact_id');
            if (contactSelect) {
                contactSelect.value = quotation.contact_id;
            }
        }

        // 填充货币
        if (quotation.currency) {
            const currencySelect = document.getElementById('currency');
            const currencyLabel = document.getElementById('currencyLabel');
            if (currencySelect) currencySelect.value = quotation.currency;
            if (currencyLabel) currencyLabel.textContent = quotation.currency;
        }

        // 填充备注
        if (quotation.notes) {
            const notesInput = document.getElementById('notes');
            if (notesInput) notesInput.value = quotation.notes;
        }

        // 填充产品明细（通过 EditableTable）
        if (quotation.details && window.EditableTable) {
            window.EditableTable.setData(quotation.details);
        }
    }

    // ============================================
    // 工具函数
    // ============================================

    /**
     * 获取CSRF Token
     */
    function getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
            || document.querySelector('input[name="csrf_token"]')?.value
            || '';
    }

    /**
     * 防抖函数
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * HTML转义
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 显示消息提示
     */
    function showMessage(message, type = 'info') {
        // 尝试使用全局消息函数
        if (typeof window.showToast === 'function') {
            window.showToast(message, type);
            return;
        }

        // 简单的alert回退
        if (type === 'error') {
            alert('错误: ' + message);
        } else {
            alert(message);
        }
    }

    /**
     * 格式化货币
     */
    function formatCurrency(value, decimals = 2) {
        const num = parseFloat(value) || 0;
        return num.toLocaleString('zh-CN', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }

    /**
     * 解析货币字符串
     */
    function parseCurrency(str) {
        if (typeof str === 'number') return str;
        return parseFloat(String(str).replace(/[,\s]/g, '')) || 0;
    }

    // ============================================
    // 公开API
    // ============================================
    return {
        init,
        clearProject,
        selectProject,
        loadProjectCustomers,
        loadCustomerContacts,
        validateForm,
        collectFormData,
        submitForm,
        populateFormData,
        formatCurrency,
        parseCurrency,
        getState: () => ({ ...state }),
        getConfig: () => ({ ...config })
    };
})();
