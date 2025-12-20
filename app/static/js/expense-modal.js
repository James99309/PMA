/**
 * 报销单模态框管理器
 * 支持创建和编辑两种模式，共享所有前端逻辑
 *
 * 使用方式:
 * 1. 在页面中引入此文件
 * 2. 调用 ExpenseModal.init(config) 初始化
 * 3. 调用 ExpenseModal.openCreate() 或 ExpenseModal.openEdit(data) 打开模态框
 */
(function(window) {
    'use strict';

    // 默认配置
    const defaultConfig = {
        modalId: 'expenseFormModal',
        defaultCurrency: 'CNY',
        currencySymbols: {
            'CNY': '¥', 'USD': '$', 'HKD': 'HK$', 'TWD': 'NT$', 'SGD': 'S$',
            'MYR': 'RM', 'IDR': 'Rp', 'THB': '฿', 'VND': '₫'
        },
        i18n: {
            loading: '加载中...',
            selectCustomerFirst: '请先选择关联客户',
            selectContact: '请选择联系人',
            noContacts: '该客户暂无联系人',
            noResults: '无匹配结果',
            createSuccess: '报销单创建成功',
            saveSuccess: '保存成功',
            createError: '创建失败',
            saveError: '保存失败',
            requiredField: '请填写必填项',
            atLeastOneDetail: '请至少添加一条报销明细',
            createTitle: '新建报销单',
            editTitle: '编辑报销单',
            createBtn: '创建',
            saveBtn: '保存'
        },
        api: {
            customerSearch: '/api/export-helpers/customers/search',
            projectSearch: '/api/v1/search/projects/for-expense',
            contacts: '/api/customers/{id}/contacts',
            exchangeRate: '/api/exchange-rate',
            create: '/expense/create',
            edit: '/expense/{id}/edit'
        },
        csrfToken: ''
    };

    let config = {};
    let detailRowId = 0;
    let searchTimeout = null;
    let currentMode = 'create'; // 'create' or 'edit'
    let editExpenseId = null;
    let existingDetails = [];

    const ExpenseModal = {
        /**
         * 初始化模态框
         * @param {Object} options - 配置选项
         */
        init: function(options) {
            config = Object.assign({}, defaultConfig, options);
            config.i18n = Object.assign({}, defaultConfig.i18n, options?.i18n || {});
            config.api = Object.assign({}, defaultConfig.api, options?.api || {});
            config.currencySymbols = Object.assign({}, defaultConfig.currencySymbols, options?.currencySymbols || {});

            this.bindEvents();
        },

        /**
         * 绑定事件监听
         */
        bindEvents: function() {
            const doBindEvents = () => {
                // 客户搜索
                const customerSearch = document.getElementById('expense_customer_search');
                if (customerSearch) {
                    customerSearch.addEventListener('input', (e) => this.searchCustomers(e.target.value));
                    customerSearch.addEventListener('focus', (e) => {
                        if (e.target.value.length >= 2) this.searchCustomers(e.target.value);
                    });
                }

                // 清除客户按钮
                const clearCustomerBtn = document.getElementById('expense_clear_customer');
                if (clearCustomerBtn) {
                    clearCustomerBtn.addEventListener('click', () => this.clearCustomer());
                }

                // 项目搜索
                const projectSearch = document.getElementById('expense_project_search');
                if (projectSearch) {
                    projectSearch.addEventListener('input', (e) => this.searchProjects(e.target.value));
                    projectSearch.addEventListener('focus', (e) => {
                        if (e.target.value.length >= 2) this.searchProjects(e.target.value);
                    });
                }

                // 清除项目按钮
                const clearProjectBtn = document.getElementById('expense_clear_project');
                if (clearProjectBtn) {
                    clearProjectBtn.addEventListener('click', () => this.clearProject());
                }

                // 不关联客户模式切换
                const noCustomerCheckbox = document.getElementById('expense_no_customer_mode');
                if (noCustomerCheckbox) {
                    noCustomerCheckbox.addEventListener('change', (e) => this.toggleNoCustomerMode(e.target.checked));
                }

                // 货币变化时更新总额符号
                const currencySelect = document.getElementById('expense_currency');
                if (currencySelect) {
                    currencySelect.addEventListener('change', () => this.updateDetailStats());
                }

                // 点击下拉框外部关闭
                document.addEventListener('click', (e) => {
                    const customerDropdown = document.getElementById('expense_customer_dropdown');
                    const customerSearchEl = document.getElementById('expense_customer_search');
                    if (customerDropdown && !customerDropdown.contains(e.target) && e.target !== customerSearchEl) {
                        customerDropdown.classList.add('hidden');
                    }

                    const projectDropdown = document.getElementById('expense_project_dropdown');
                    const projectSearchEl = document.getElementById('expense_project_search');
                    if (projectDropdown && !projectDropdown.contains(e.target) && e.target !== projectSearchEl) {
                        projectDropdown.classList.add('hidden');
                    }
                });

                // 同步表头和表体的水平滚动
                const tableScroll = document.getElementById('expenseModalTableScroll');
                const headerEl = document.getElementById('expenseModalTableHeader');
                if (tableScroll && headerEl) {
                    tableScroll.addEventListener('scroll', function() {
                        headerEl.scrollLeft = tableScroll.scrollLeft;
                    });
                }

                // 检查URL参数，自动打开创建模态框
                const urlParams = new URLSearchParams(window.location.search);
                if (urlParams.get('action') === 'create') {
                    urlParams.delete('action');
                    const newUrl = window.location.pathname + (urlParams.toString() ? '?' + urlParams.toString() : '');
                    window.history.replaceState({}, '', newUrl);
                    setTimeout(() => this.openCreate(), 100);
                }
            };

            // 如果 DOM 已加载完成则直接执行，否则等待 DOMContentLoaded
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', doBindEvents);
            } else {
                doBindEvents();
            }
        },

        /**
         * 打开创建模态框
         */
        openCreate: function() {
            currentMode = 'create';
            editExpenseId = null;
            existingDetails = [];
            this.reset();

            if (typeof openFormModal === 'function') {
                openFormModal(config.modalId, {
                    title: config.i18n.createTitle,
                    submitText: config.i18n.createBtn,
                    onSubmit: () => this.submit()
                });
            }
        },

        /**
         * 打开编辑模态框
         * @param {Object} data - 报销单数据
         * @param {Object} options - 可选参数
         * @param {boolean} options.approvalEditMode - 是否为审批编辑模式
         * @param {Array} options.editableFields - 可编辑的字段列表
         * @param {string} options.stepName - 当前审批步骤名称
         */
        openEdit: function(data, options = {}) {
            currentMode = 'edit';
            editExpenseId = data.id;
            existingDetails = data.details || [];

            // 保存审批编辑模式配置
            this.approvalEditMode = options.approvalEditMode || false;
            this.editableFields = options.editableFields || [];
            this.stepName = options.stepName || '';

            this.reset();
            this.fillFormData(data);

            // 如果是审批编辑模式，禁用不可编辑的字段
            if (this.approvalEditMode) {
                this.applyApprovalEditRestrictions();
            }

            if (typeof openFormModal === 'function') {
                const title = this.approvalEditMode
                    ? (config.i18n.approvalEditTitle || '审批编辑 - ' + this.stepName)
                    : config.i18n.editTitle;
                openFormModal(config.modalId, {
                    title: title,
                    submitText: config.i18n.saveBtn,
                    onSubmit: () => this.submit()
                });
            }
        },

        /**
         * 应用审批编辑模式的字段限制
         * 使用通用工具 ApprovalFieldControl 处理字段控制
         */
        applyApprovalEditRestrictions: function() {
            // 使用通用工具处理主表字段控制
            const form = document.getElementById(config.modalId + '-form');
            if (form && typeof ApprovalFieldControl !== 'undefined') {
                ApprovalFieldControl.apply(form, this.editableFields);
            }

            // 保存明细可编辑字段供后续使用
            const detailFieldCodes = [
                'expense_date', 'expense_category', 'description', 'document_count',
                'currency', 'invoice_amount', 'exchange_rate', 'amount', 'invoice_images'
            ];
            this.detailEditableFields = this.editableFields.filter(f => detailFieldCodes.includes(f));
        },


        /**
         * 重置表单
         */
        reset: function() {
            const form = document.getElementById(config.modalId + '-form');
            if (form) form.reset();

            // 重置所有字段的禁用状态和样式
            const allInputs = form ? form.querySelectorAll('input, select, textarea') : [];
            allInputs.forEach(el => {
                el.classList.remove('bg-slate-100', 'dark:bg-slate-700', 'cursor-not-allowed');
                el.classList.remove('bg-amber-50', 'dark:bg-amber-900/20');
            });

            // 重置添加行按钮
            const addRowBtn = document.getElementById('expenseAddDetailRow');
            if (addRowBtn) {
                addRowBtn.disabled = false;
                addRowBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            }

            // 重置隐藏字段
            const customerId = document.getElementById('expense_customer_id');
            const projectId = document.getElementById('expense_project_id');
            if (customerId) customerId.value = '';
            if (projectId) projectId.value = '';

            // 重置搜索框
            const customerSearch = document.getElementById('expense_customer_search');
            const projectSearch = document.getElementById('expense_project_search');
            if (customerSearch) customerSearch.value = '';
            if (projectSearch) projectSearch.value = '';

            // 隐藏清除按钮
            const clearCustomer = document.getElementById('expense_clear_customer');
            const clearProject = document.getElementById('expense_clear_project');
            if (clearCustomer) clearCustomer.classList.add('hidden');
            if (clearProject) clearProject.classList.add('hidden');

            // 重置联系人下拉框
            const contactSelect = document.getElementById('expense_contact_id');
            if (contactSelect) {
                contactSelect.disabled = true;
                contactSelect.innerHTML = '<option value="">' + config.i18n.selectCustomerFirst + '</option>';
            }

            // 显示客户相关字段（包括客户、联系人、项目）
            const customerFields = document.getElementById('expenseCustomerFields');
            if (customerFields) customerFields.style.display = '';

            // 重置不关联客户模式
            const noCustomerCheckbox = document.getElementById('expense_no_customer_mode');
            if (noCustomerCheckbox) {
                noCustomerCheckbox.checked = false;
                noCustomerCheckbox.disabled = false;
            }

            // 隐藏说明必填标记
            const descRequired = document.querySelector('.expense-desc-required');
            if (descRequired) descRequired.classList.add('hidden');

            // 显示客户必填标记
            document.querySelectorAll('.expense-customer-required').forEach(el => el.classList.remove('hidden'));

            // 清空明细表格
            const tbody = document.getElementById('expenseModalTableBody');
            if (tbody) tbody.innerHTML = '';

            detailRowId = 0;
            this.updateDetailStats();
        },

        /**
         * 填充表单数据（编辑模式）
         * @param {Object} data - 报销单数据
         */
        fillFormData: function(data) {
            // 基本信息
            const titleEl = document.getElementById('expense_title');
            const currencyEl = document.getElementById('expense_currency');
            const descriptionEl = document.getElementById('expense_description');

            if (titleEl) titleEl.value = data.title || '';
            if (currencyEl) currencyEl.value = data.currency || config.defaultCurrency;
            if (descriptionEl) descriptionEl.value = data.description || '';

            if (data.customer_id) {
                // 关联客户模式
                const customerId = document.getElementById('expense_customer_id');
                const customerSearch = document.getElementById('expense_customer_search');
                const clearCustomer = document.getElementById('expense_clear_customer');
                const contactSelect = document.getElementById('expense_contact_id');

                if (customerId) customerId.value = data.customer_id;
                if (customerSearch) customerSearch.value = data.customer_name || '';
                if (clearCustomer) clearCustomer.classList.remove('hidden');

                if (contactSelect && data.contact_id) {
                    contactSelect.innerHTML = `<option value="${data.contact_id}" selected>${data.contact_name || ''}</option>`;
                    contactSelect.disabled = false;
                }

                if (data.project_id) {
                    const projectId = document.getElementById('expense_project_id');
                    const projectSearch = document.getElementById('expense_project_search');
                    const clearProject = document.getElementById('expense_clear_project');

                    if (projectId) projectId.value = data.project_id;
                    if (projectSearch) projectSearch.value = data.project_name || '';
                    if (clearProject) clearProject.classList.remove('hidden');
                }
            } else {
                // 不关联客户模式
                const noCustomerCheckbox = document.getElementById('expense_no_customer_mode');
                const customerFields = document.getElementById('expenseCustomerFields');
                const descRequired = document.querySelector('.expense-desc-required');

                if (noCustomerCheckbox) {
                    noCustomerCheckbox.checked = true;
                    noCustomerCheckbox.disabled = true;
                }
                // 隐藏客户相关字段（包括客户、联系人、项目）
                if (customerFields) customerFields.style.display = 'none';
                if (descRequired) descRequired.classList.remove('hidden');
                document.querySelectorAll('.expense-customer-required').forEach(el => el.classList.add('hidden'));
            }

            // 加载明细行
            if (existingDetails && existingDetails.length > 0) {
                existingDetails.forEach((detail) => {
                    this.addDetailRow(detail);
                });
            }

            this.updateDetailStats();
        },

        /**
         * 添加明细行
         * @param {Object} data - 明细数据（可选）
         */
        addDetailRow: function(data) {
            const template = document.getElementById('expenseModalRowTemplate');
            const tbody = document.getElementById('expenseModalTableBody');

            if (!template || !tbody) {
                return;
            }

            const row = template.content.cloneNode(true).querySelector('tr');

            if (!row) {
                return;
            }

            detailRowId++;
            row.dataset.rowId = detailRowId;
            if (data && data.id) {
                row.dataset.detailId = data.id;
            }

            // 填充默认值
            const today = new Date().toISOString().split('T')[0];
            const currencyEl = document.getElementById('expense_currency');
            const defaultCurrency = currencyEl ? currencyEl.value : config.defaultCurrency;

            row.querySelector('[name="expense_date"]').value = data?.expense_date || today;
            row.querySelector('[name="detail_currency"]').value = data?.currency || defaultCurrency;

            if (data) {
                row.querySelector('[name="expense_category"]').value = data.expense_category || '';
                row.querySelector('[name="detail_description"]').value = data.description || '';
                row.querySelector('[name="document_count"]').value = data.document_count || 1;
                row.querySelector('[name="invoice_amount"]').value = data.invoice_amount || '';
                row.querySelector('[name="exchange_rate"]').value = data.exchange_rate || 1;

                const currentAmount = (data.invoice_amount || 0) * (data.exchange_rate || 1);
                row.querySelector('.expense-current-amount').textContent = currentAmount.toFixed(2);

                // 显示现有发票
                if (data.invoice_images && data.invoice_images.length > 0) {
                    const container = row.querySelector('.expense-invoice-container');
                    const input = row.querySelector('.expense-invoice-input');
                    const self = this;

                    data.invoice_images.forEach((img, imgIndex) => {
                        const url = img.url || img;
                        const filename = img.filename || 'invoice';
                        const isImage = !filename.toLowerCase().endsWith('.pdf');

                        const preview = document.createElement('div');
                        preview.className = 'relative group flex-shrink-0';
                        preview.dataset.existingInvoice = JSON.stringify(img);

                        preview.innerHTML = `
                            <div class="w-7 h-7 rounded border border-slate-200 dark:border-slate-700 overflow-hidden bg-slate-100 dark:bg-slate-800 flex items-center justify-center cursor-pointer invoice-preview-trigger"
                                 data-url="${url}" data-type="${isImage ? 'image' : 'file'}" data-name="${filename}">
                                ${isImage
                                    ? `<img src="${url}" class="w-full h-full object-cover" onerror="this.outerHTML='<span class=\\'material-symbols-outlined text-green-500\\' style=\\'font-size:14px\\'>check_circle</span>'">`
                                    : `<span class="material-symbols-outlined text-slate-500" style="font-size: 14px;">description</span>`
                                }
                            </div>
                            <button type="button" class="absolute -top-1 -right-1 w-3.5 h-3.5 bg-red-500 text-white rounded-full hidden group-hover:flex items-center justify-center" style="font-size: 10px; line-height: 1;">×</button>
                        `;

                        // 点击预览
                        preview.querySelector('.invoice-preview-trigger').addEventListener('click', function() {
                            const triggers = container.querySelectorAll('.invoice-preview-trigger');
                            const index = Array.from(triggers).indexOf(this);
                            self.showInvoicePreview(this.dataset.url, this.dataset.type, this.dataset.name, row, index);
                        });

                        // 删除按钮
                        preview.querySelector('button').addEventListener('click', function(e) {
                            e.stopPropagation();
                            preview.remove();
                            self.updateDocumentCount(row);
                        });

                        container.insertBefore(preview, input.parentElement);
                    });

                    // 更新单据数量显示
                    this.updateDocumentCount(row);
                }
            }

            this.bindRowEvents(row);
            tbody.appendChild(row);

            // 审批编辑模式：禁用不可编辑的明细字段
            if (this.approvalEditMode) {
                this.applyDetailRowRestrictions(row);
            }

            this.updateDetailStats();
        },

        /**
         * 应用明细行字段限制（审批编辑模式）
         * 使用通用工具 ApprovalFieldControl 处理字段控制
         * @param {HTMLElement} row - 明细行元素
         */
        applyDetailRowRestrictions: function(row) {
            // 使用通用工具处理明细行字段控制
            if (typeof ApprovalFieldControl !== 'undefined') {
                ApprovalFieldControl.applyToRow(row, this.editableFields);
            }
        },

        /**
         * 绑定行事件
         * @param {HTMLElement} row - 行元素
         */
        bindRowEvents: function(row) {
            // 货币变化时获取汇率
            row.querySelector('[name="detail_currency"]').addEventListener('change', () => this.fetchExchangeRate(row));

            // 金额/汇率变化时计算报销额
            row.querySelector('[name="invoice_amount"]').addEventListener('input', () => this.calculateCurrentAmount(row));
            row.querySelector('[name="exchange_rate"]').addEventListener('input', () => this.calculateCurrentAmount(row));

            // 发票上传
            row.querySelector('.expense-invoice-input').addEventListener('change', (e) => this.handleInvoiceUpload(row, e.target.files));
        },

        /**
         * 删除明细行
         * @param {HTMLElement} btn - 删除按钮
         */
        removeDetailRow: function(btn) {
            const row = btn.closest('tr');
            if (row) {
                row.remove();
                this.updateDetailStats();
            }
        },

        /**
         * 获取汇率
         * @param {HTMLElement} row - 行元素
         */
        fetchExchangeRate: function(row) {
            const fromCurrency = row.querySelector('[name="detail_currency"]').value;
            const currencyEl = document.getElementById('expense_currency');
            const toCurrency = currencyEl ? currencyEl.value : config.defaultCurrency;

            if (fromCurrency === toCurrency) {
                row.querySelector('[name="exchange_rate"]').value = 1;
                this.calculateCurrentAmount(row);
                return;
            }

            fetch(`${config.api.exchangeRate}?from=${fromCurrency}&to=${toCurrency}`)
                .then(r => r.json())
                .then(data => {
                    if (data.success && data.rate) {
                        row.querySelector('[name="exchange_rate"]').value = data.rate;
                        this.calculateCurrentAmount(row);
                    }
                })
                .catch(err => console.error('获取汇率失败:', err));
        },

        /**
         * 计算报销额
         * @param {HTMLElement} row - 行元素
         */
        calculateCurrentAmount: function(row) {
            const invoiceAmount = parseFloat(row.querySelector('[name="invoice_amount"]').value) || 0;
            const exchangeRate = parseFloat(row.querySelector('[name="exchange_rate"]').value) || 1;
            row.querySelector('.expense-current-amount').textContent = (invoiceAmount * exchangeRate).toFixed(2);
            this.updateDetailStats();
        },

        /**
         * 处理发票上传
         * @param {HTMLElement} row - 行元素
         * @param {FileList} files - 文件列表
         */
        handleInvoiceUpload: function(row, files) {
            const container = row.querySelector('.expense-invoice-container');
            const input = row.querySelector('.expense-invoice-input');
            const self = this;

            for (const file of files) {
                const preview = document.createElement('div');
                preview.className = 'relative group flex-shrink-0 invoice-file-preview';

                // 存储 File 对象用于提交
                preview.fileData = file;

                // 创建预览URL
                const objectUrl = URL.createObjectURL(file);
                const isImage = file.type.startsWith('image/');

                preview.innerHTML = `
                    <div class="w-7 h-7 rounded border border-slate-200 dark:border-slate-700 overflow-hidden bg-slate-100 dark:bg-slate-800 flex items-center justify-center cursor-pointer invoice-preview-trigger"
                         data-url="${objectUrl}" data-type="${isImage ? 'image' : 'file'}" data-name="${file.name}">
                        ${isImage
                            ? `<img src="${objectUrl}" class="w-full h-full object-cover">`
                            : `<span class="material-symbols-outlined text-slate-500" style="font-size: 14px;">description</span>`
                        }
                    </div>
                    <button type="button" class="absolute -top-1 -right-1 w-3.5 h-3.5 bg-red-500 text-white rounded-full hidden group-hover:flex items-center justify-center" style="font-size: 10px; line-height: 1;">×</button>
                `;

                // 点击预览 - 传递行和索引以支持切换
                preview.querySelector('.invoice-preview-trigger').addEventListener('click', function() {
                    const triggers = container.querySelectorAll('.invoice-preview-trigger');
                    const index = Array.from(triggers).indexOf(this);
                    self.showInvoicePreview(this.dataset.url, this.dataset.type, this.dataset.name, row, index);
                });

                // 删除按钮
                preview.querySelector('button').addEventListener('click', function(e) {
                    e.stopPropagation();
                    preview.remove();
                    self.updateDocumentCount(row);
                });

                container.insertBefore(preview, input.parentElement);
            }

            // 更新单据数量
            this.updateDocumentCount(row);
        },

        /**
         * 更新单据数量
         */
        updateDocumentCount: function(row) {
            const container = row.querySelector('.expense-invoice-container');
            const count = container.querySelectorAll('.invoice-preview-trigger').length;
            const countDisplay = row.querySelector('.expense-document-count');
            const countInput = row.querySelector('[name="document_count"]');

            if (countDisplay) countDisplay.textContent = count;
            if (countInput) countInput.value = count;
        },

        // 当前预览状态
        currentPreviewRow: null,
        currentPreviewIndex: 0,
        currentPreviewList: [],

        /**
         * 显示发票预览
         */
        showInvoicePreview: function(url, type, name, row, index) {
            // 收集当前行所有发票
            if (row) {
                this.currentPreviewRow = row;
                this.currentPreviewList = [];
                const triggers = row.querySelectorAll('.invoice-preview-trigger');
                triggers.forEach((t, i) => {
                    this.currentPreviewList.push({
                        url: t.dataset.url,
                        type: t.dataset.type,
                        name: t.dataset.name
                    });
                });
                this.currentPreviewIndex = index || 0;
            }

            // 更新预览内容
            const content = document.getElementById('invoicePreviewContent');
            const filenameEl = document.getElementById('invoiceFilename');
            const counterEl = document.getElementById('invoiceCounter');
            const prevBtn = document.getElementById('prevInvoiceBtn');
            const nextBtn = document.getElementById('nextInvoiceBtn');

            if (!content) {
                // 如果没有预览模态框，新窗口打开
                window.open(url, '_blank');
                return;
            }

            filenameEl.textContent = name || 'invoice';

            // 更新计数器
            if (counterEl && this.currentPreviewList.length > 0) {
                counterEl.textContent = `${this.currentPreviewIndex + 1}/${this.currentPreviewList.length}`;
            }

            // 更新按钮状态
            if (prevBtn) prevBtn.disabled = this.currentPreviewIndex <= 0;
            if (nextBtn) nextBtn.disabled = this.currentPreviewIndex >= this.currentPreviewList.length - 1;

            // 判断文件类型显示内容
            const isPdf = name && name.toLowerCase().endsWith('.pdf');
            const isImage = type === 'image' || (!isPdf && !name);

            if (isPdf) {
                content.innerHTML = `<iframe src="${url}" class="w-full h-[500px] rounded-lg" frameborder="0"></iframe>`;
            } else if (isImage) {
                content.innerHTML = `<img src="${url}" alt="${name}" class="max-w-full max-h-[500px] object-contain rounded-lg" onerror="this.parentElement.innerHTML='<span class=\\'text-red-500\\'>图片加载失败</span>'">`;
            } else {
                content.innerHTML = `
                    <div class="flex flex-col items-center justify-center py-12">
                        <span class="material-symbols-outlined text-6xl text-slate-400">description</span>
                        <p class="mt-4 text-slate-600 dark:text-slate-400">${name}</p>
                    </div>
                `;
            }

            // 打开模态框
            if (typeof openCustomModal === 'function') {
                openCustomModal('invoicePreviewModal');
            }
        },

        /**
         * 上一张发票
         */
        prevInvoice: function() {
            if (this.currentPreviewIndex > 0) {
                this.currentPreviewIndex--;
                const inv = this.currentPreviewList[this.currentPreviewIndex];
                this.showInvoicePreview(inv.url, inv.type, inv.name);
            }
        },

        /**
         * 下一张发票
         */
        nextInvoice: function() {
            if (this.currentPreviewIndex < this.currentPreviewList.length - 1) {
                this.currentPreviewIndex++;
                const inv = this.currentPreviewList[this.currentPreviewIndex];
                this.showInvoicePreview(inv.url, inv.type, inv.name);
            }
        },

        /**
         * 下载当前发票
         */
        downloadCurrentInvoice: function() {
            const inv = this.currentPreviewList[this.currentPreviewIndex];
            if (!inv) return;

            const link = document.createElement('a');
            link.href = inv.url;
            link.download = inv.name || 'invoice';
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },

        /**
         * 更新明细统计
         */
        updateDetailStats: function() {
            const rows = document.querySelectorAll('#expenseModalTableBody tr');
            const count = rows.length;
            const hasDetails = count > 0;

            const countEl = document.getElementById('expenseModalCount');
            const emptyEl = document.getElementById('expenseModalEmpty');
            const headerEl = document.getElementById('expenseModalTableHeader');
            const footerEl = document.getElementById('expenseModalFooter');

            if (countEl) countEl.textContent = count;
            if (emptyEl) emptyEl.style.display = hasDetails ? 'none' : '';
            // 有明细时显示表头和底部
            if (headerEl) headerEl.classList.toggle('hidden', !hasDetails);
            if (footerEl) footerEl.classList.toggle('hidden', !hasDetails);

            // 计算总额
            let total = 0;
            rows.forEach(row => {
                total += parseFloat(row.querySelector('.expense-current-amount').textContent) || 0;
            });

            const currencyEl = document.getElementById('expense_currency');
            const currency = currencyEl ? currencyEl.value : config.defaultCurrency;
            const symbol = config.currencySymbols[currency] || currency;

            const totalEl = document.getElementById('expenseModalTotal');
            if (totalEl) totalEl.textContent = symbol + total.toFixed(2);
        },

        /**
         * 搜索客户
         * @param {string} query - 搜索关键词
         */
        searchCustomers: function(query) {
            if (query.length < 2) {
                document.getElementById('expense_customer_dropdown')?.classList.add('hidden');
                return;
            }

            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                fetch(`${config.api.customerSearch}?search=${encodeURIComponent(query)}`)
                    .then(r => r.json())
                    .then(data => {
                        const dropdown = document.getElementById('expense_customer_dropdown');
                        const results = document.getElementById('expense_customer_results');

                        if (data.success && data.results && data.results.length > 0) {
                            results.innerHTML = data.results.map(c => `
                                <div class="px-3 py-2 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700 text-sm text-slate-900 dark:text-slate-100"
                                     onclick="ExpenseModal.selectCustomer(${c.id}, '${c.company_name.replace(/'/g, "\\'")}')">
                                    ${c.company_name}
                                </div>
                            `).join('');
                        } else {
                            results.innerHTML = `<div class="px-3 py-2 text-sm text-slate-500">${config.i18n.noResults}</div>`;
                        }
                        dropdown?.classList.remove('hidden');
                    });
            }, 300);
        },

        /**
         * 选择客户
         * @param {number} id - 客户ID
         * @param {string} name - 客户名称
         */
        selectCustomer: function(id, name) {
            document.getElementById('expense_customer_id').value = id;
            document.getElementById('expense_customer_search').value = name;
            document.getElementById('expense_customer_dropdown')?.classList.add('hidden');
            document.getElementById('expense_clear_customer')?.classList.remove('hidden');
            this.loadContacts(id);
        },

        /**
         * 清除客户
         */
        clearCustomer: function() {
            document.getElementById('expense_customer_id').value = '';
            document.getElementById('expense_customer_search').value = '';
            document.getElementById('expense_clear_customer')?.classList.add('hidden');

            const contactSelect = document.getElementById('expense_contact_id');
            if (contactSelect) {
                contactSelect.disabled = true;
                contactSelect.innerHTML = '<option value="">' + config.i18n.selectCustomerFirst + '</option>';
            }
        },

        /**
         * 加载联系人
         * @param {number} customerId - 客户ID
         */
        loadContacts: function(customerId) {
            const contactSelect = document.getElementById('expense_contact_id');
            if (!contactSelect) return;

            contactSelect.disabled = true;
            contactSelect.innerHTML = '<option value="">' + config.i18n.loading + '</option>';

            fetch(config.api.contacts.replace('{id}', customerId))
                .then(r => r.json())
                .then(data => {
                    if (data.success && data.contacts && data.contacts.length > 0) {
                        contactSelect.innerHTML = '<option value="">' + config.i18n.selectContact + '</option>' +
                            data.contacts.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
                        contactSelect.disabled = false;
                    } else {
                        contactSelect.innerHTML = '<option value="">' + config.i18n.noContacts + '</option>';
                    }
                });
        },

        /**
         * 搜索项目
         * @param {string} query - 搜索关键词
         */
        searchProjects: function(query) {
            if (query.length < 2) {
                document.getElementById('expense_project_dropdown')?.classList.add('hidden');
                return;
            }

            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                fetch(`${config.api.projectSearch}?q=${encodeURIComponent(query)}`)
                    .then(r => r.json())
                    .then(data => {
                        const dropdown = document.getElementById('expense_project_dropdown');
                        const results = document.getElementById('expense_project_results');

                        if (data.success && data.data && data.data.length > 0) {
                            results.innerHTML = data.data.map(p => `
                                <div class="px-3 py-2 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700 text-sm text-slate-900 dark:text-slate-100"
                                     onclick="ExpenseModal.selectProject(${p.id}, '${p.project_name.replace(/'/g, "\\'")}')">
                                    ${p.project_name}
                                </div>
                            `).join('');
                        } else {
                            results.innerHTML = `<div class="px-3 py-2 text-sm text-slate-500">${config.i18n.noResults}</div>`;
                        }
                        dropdown?.classList.remove('hidden');
                    });
            }, 300);
        },

        /**
         * 选择项目
         * @param {number} id - 项目ID
         * @param {string} name - 项目名称
         */
        selectProject: function(id, name) {
            document.getElementById('expense_project_id').value = id;
            document.getElementById('expense_project_search').value = name;
            document.getElementById('expense_project_dropdown')?.classList.add('hidden');
            document.getElementById('expense_clear_project')?.classList.remove('hidden');
        },

        /**
         * 清除项目
         */
        clearProject: function() {
            document.getElementById('expense_project_id').value = '';
            document.getElementById('expense_project_search').value = '';
            document.getElementById('expense_clear_project')?.classList.add('hidden');
        },

        /**
         * 切换不关联客户模式
         * @param {boolean} checked - 是否选中
         */
        toggleNoCustomerMode: function(checked) {
            const customerFields = document.getElementById('expenseCustomerFields');
            const descRequired = document.querySelector('.expense-desc-required');
            const customerRequired = document.querySelectorAll('.expense-customer-required');

            if (checked) {
                // 隐藏客户相关字段（包括客户、联系人、项目）
                if (customerFields) customerFields.style.display = 'none';
                if (descRequired) descRequired.classList.remove('hidden');
                customerRequired.forEach(el => el.classList.add('hidden'));
                this.clearCustomer();
                this.clearProject();
            } else {
                // 显示客户相关字段
                if (customerFields) customerFields.style.display = '';
                if (descRequired) descRequired.classList.add('hidden');
                customerRequired.forEach(el => el.classList.remove('hidden'));
            }
        },

        /**
         * 验证表单
         * @returns {boolean} - 是否验证通过
         */
        validate: function() {
            const noCustomerMode = document.getElementById('expense_no_customer_mode')?.checked;
            const rows = document.querySelectorAll('#expenseModalTableBody tr');

            if (rows.length === 0) {
                alert(config.i18n.atLeastOneDetail);
                return false;
            }

            if (noCustomerMode) {
                const desc = document.getElementById('expense_description')?.value.trim();
                if (!desc) {
                    alert(config.i18n.requiredField);
                    document.getElementById('expense_description')?.focus();
                    return false;
                }
            } else {
                const customerId = document.getElementById('expense_customer_id')?.value;
                const contactId = document.getElementById('expense_contact_id')?.value;
                if (!customerId || !contactId) {
                    alert(config.i18n.requiredField);
                    return false;
                }
            }

            return true;
        },

        /**
         * 收集表单数据
         * @returns {FormData} - 表单数据
         */
        collectFormData: function() {
            const formData = new FormData();

            formData.append('title', document.getElementById('expense_title')?.value || '');
            formData.append('currency', document.getElementById('expense_currency')?.value || config.defaultCurrency);
            formData.append('description', document.getElementById('expense_description')?.value || '');

            const noCustomerMode = document.getElementById('expense_no_customer_mode')?.checked;
            formData.append('no_customer_mode', noCustomerMode ? '1' : '');

            if (!noCustomerMode) {
                formData.append('customer_id', document.getElementById('expense_customer_id')?.value || '');
                formData.append('project_id', document.getElementById('expense_project_id')?.value || '');
                formData.append('contact_id', document.getElementById('expense_contact_id')?.value || '');
            }

            const rows = document.querySelectorAll('#expenseModalTableBody tr');
            rows.forEach((row, index) => {
                // 编辑模式保留明细ID
                if (row.dataset.detailId) {
                    formData.append(`details[${index}][id]`, row.dataset.detailId);
                }

                formData.append(`details[${index}][expense_category]`, row.querySelector('[name="expense_category"]').value);
                formData.append(`details[${index}][expense_date]`, row.querySelector('[name="expense_date"]').value);
                formData.append(`details[${index}][description]`, row.querySelector('[name="detail_description"]').value);
                formData.append(`details[${index}][document_count]`, row.querySelector('[name="document_count"]').value);
                formData.append(`details[${index}][currency]`, row.querySelector('[name="detail_currency"]').value);
                formData.append(`details[${index}][invoice_amount]`, row.querySelector('[name="invoice_amount"]').value);
                formData.append(`details[${index}][exchange_rate]`, row.querySelector('[name="exchange_rate"]').value);

                // 保留现有发票 - 按后端期望格式发送
                const existingInvoices = row.querySelectorAll('[data-existing-invoice]');
                let existingIndex = 0;
                existingInvoices.forEach(el => {
                    try {
                        const imgData = JSON.parse(el.dataset.existingInvoice);
                        formData.append(`details[${index}][existing_invoices][${existingIndex}][url]`, imgData.url || '');
                        formData.append(`details[${index}][existing_invoices][${existingIndex}][filename]`, imgData.filename || '');
                        formData.append(`details[${index}][existing_invoices][${existingIndex}][size]`, imgData.size || 0);
                        existingIndex++;
                    } catch (e) {
                        // 兼容旧格式（直接是URL字符串）
                        formData.append(`details[${index}][existing_invoices][${existingIndex}][url]`, el.dataset.existingInvoice);
                        existingIndex++;
                    }
                });

                // 新上传的发票 - 从预览元素收集 File 对象
                const filePreviews = row.querySelectorAll('.invoice-file-preview');
                let fileIndex = 0;
                filePreviews.forEach(preview => {
                    if (preview.fileData) {
                        formData.append(`details[${index}][invoice_files][${fileIndex}]`, preview.fileData);
                        fileIndex++;
                    }
                });
            });

            return formData;
        },

        /**
         * 提交表单
         */
        submit: function() {
            if (!this.validate()) return;

            const formData = this.collectFormData();
            const submitBtn = document.getElementById(config.modalId + '-submit-btn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = config.i18n.loading;
            }

            let url = currentMode === 'edit'
                ? config.api.edit.replace('{id}', editExpenseId)
                : config.api.create;

            // 审批编辑模式添加参数
            if (this.approvalEditMode) {
                url += (url.includes('?') ? '&' : '?') + 'approval_edit=1';
            }

            const successMsg = currentMode === 'edit' ? config.i18n.saveSuccess : config.i18n.createSuccess;
            const errorMsg = currentMode === 'edit' ? config.i18n.saveError : config.i18n.createError;
            const btnText = currentMode === 'edit' ? config.i18n.saveBtn : config.i18n.createBtn;

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': config.csrfToken
                }
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    if (typeof closeFormModal === 'function') {
                        closeFormModal(config.modalId);
                    }

                    if (typeof showMessage === 'function') {
                        showMessage(successMsg, 'success');
                    }

                    // 跳转或刷新（缩短延迟时间）
                    setTimeout(() => {
                        if (data.redirect_url) {
                            window.location.href = data.redirect_url;
                        } else if (data.expense_id) {
                            window.location.href = `/expense/${data.expense_id}?tw=1`;
                        } else {
                            window.location.reload();
                        }
                    }, 300);
                } else {
                    alert(data.message || errorMsg);
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.textContent = btnText;
                    }
                }
            })
            .catch(err => {
                console.error('提交失败:', err);
                alert(errorMsg);
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = btnText;
                }
            });
        }
    };

    // 暴露到全局
    window.ExpenseModal = ExpenseModal;

})(window);
