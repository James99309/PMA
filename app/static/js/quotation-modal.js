/**
 * 报价单模态框表单模块
 * 用于新建和编辑报价单的模态框通用逻辑
 *
 * 使用页面：
 * - quotation/tw_list.html - 报价单列表页
 * - project/tw_project_detail.html - 项目详情页
 *
 * 元素ID约定（带Modal后缀）：
 * - projectSearchModal, projectDropdownModal, projectResultsModal
 * - project_id_modal, customer_id_modal, contact_id_modal, currency_modal
 * - quotationProductTable, grandTotalModal
 *
 * 创建日期: 2025-12-12
 */
window.QuotationModal = (function() {
    'use strict';

    // 默认配置
    let config = {
        i18n: {
            loading: '加载中...',
            pleaseSelectProject: '-- 请先选择项目 --',
            pleaseSelectCustomer: '请选择客户',
            noCustomersFound: '该项目暂无关联客户',
            pleaseSelectContact: '请选择联系人',
            noContactsFound: '该客户暂无联系人',
            creating: '创建中...',
            create: '创建',
            saving: '保存中...',
            save: '保存',
            saveError: '保存失败，请重试',
            loadError: '加载数据失败，请重试',
            projectRequired: '请选择关联项目',
            customerRequired: '请选择客户',
            productRequired: '请至少添加一个产品',
            manualInput: '手动输入',
            tempIndicator: '临时',
            noProjectsFound: '未找到匹配的项目',
            newQuotation: '新建报价单',
            // 产品选择器 i18n（传给 ProductSelector 实例）
            products: '个产品',
            priceNegotiable: '价格面议',
            clickToSelectCount: '点击选择 ({count} 个型号/规格)',
            discontinued: '停产'
        },
        urls: {
            createQuotation: '/quotation/create',
            searchProjects: '/quotation/search_projects',
            getProjectCustomers: '/quotation/get_project_customers',
            getCustomerContacts: '/quotation/get_customer_contacts'
        },
        presetProjectId: null,
        presetProjectName: null,
        onSuccess: null
    };

    // 内部状态
    let currentMode = 'create';
    let currentQuotationId = null;
    let projectSearchTimeout = null;
    let initialized = false;

    /**
     * 初始化模块
     * @param {Object} options - 配置选项
     */
    function init(options) {
        if (options) {
            // 合并 i18n 配置
            if (options.i18n) {
                config.i18n = Object.assign({}, config.i18n, options.i18n);
            }
            // 合并 urls 配置
            if (options.urls) {
                config.urls = Object.assign({}, config.urls, options.urls);
            }
            // 其他配置
            if (options.presetProjectId !== undefined) {
                config.presetProjectId = options.presetProjectId;
            }
            if (options.presetProjectName !== undefined) {
                config.presetProjectName = options.presetProjectName;
            }
            if (options.onSuccess) {
                config.onSuccess = options.onSuccess;
            }
        }

        // 绑定事件
        bindEvents();
        initialized = true;
        console.log('[QuotationModal] Initialized with config:', config);
    }

    /**
     * 初始化产品表格
     */
    function initProductTable() {
        console.log('[QuotationModal] initProductTable called');
        console.log('[QuotationModal] EditableTable:', !!window.EditableTable);
        console.log('[QuotationModal] instances:', window.EditableTable ? window.EditableTable.instances : 'N/A');

        if (window.EditableTable && window.EditableTable.instances['quotationProductTable']) {
            // 清空现有数据并添加一个空行
            const instance = window.EditableTable.instances['quotationProductTable'];
            const tbody = document.getElementById('quotationProductTableBody');
            console.log('[QuotationModal] tbody found:', !!tbody);
            if (tbody) {
                tbody.innerHTML = '';
            }
            instance.rows = [];
            instance.rowCounter = 0;
            const newRow = window.EditableTable.addRow('quotationProductTable');
            console.log('[QuotationModal] Added row:', newRow);
        } else {
            console.warn('[QuotationModal] EditableTable instance not found!');
        }
    }

    /**
     * 初始化产品选择器
     */
    function initProductSelector() {
        console.log('[QuotationModal] initProductSelector called');
        console.log('[QuotationModal] ProductSelector class:', !!window.ProductSelector);

        if (window.ProductSelector) {
            window.productSelectorModal = new ProductSelector({
                manual_input: {
                    enabled: true,
                    option_text: config.i18n.manualInput,
                    temp_indicator: {
                        show: true,
                        text: config.i18n.tempIndicator,
                        position: 'after_price',
                        style: 'temp-product-indicator'
                    }
                },
                i18n: {
                    products: config.i18n.products,
                    priceNegotiable: config.i18n.priceNegotiable,
                    clickToSelectCount: config.i18n.clickToSelectCount,
                    discontinued: config.i18n.discontinued
                },
                onSelect: function(product, inputElement) {
                    console.log('[QuotationModal] Product selected:', product);
                    const rowId = inputElement.dataset.rowId;
                    if (rowId && window.EditableTable) {
                        window.EditableTable.updateRowFromProduct('quotationProductTable', rowId, product);
                    }
                }
            });
            console.log('[QuotationModal] productSelectorModal created:', !!window.productSelectorModal);
        } else {
            console.warn('[QuotationModal] ProductSelector class not found!');
        }
    }

    /**
     * 项目搜索
     * @param {string} keyword - 搜索关键词
     */
    function searchProjects(keyword) {
        clearTimeout(projectSearchTimeout);

        const dropdown = document.getElementById('projectDropdownModal');
        const results = document.getElementById('projectResultsModal');

        if (!dropdown || !results) return;

        if (!keyword || keyword.length < 2) {
            dropdown.classList.add('hidden');
            return;
        }

        projectSearchTimeout = setTimeout(async function() {
            try {
                results.innerHTML = '<div class="p-3 text-sm text-slate-500">' + config.i18n.loading + '</div>';
                dropdown.classList.remove('hidden');

                const response = await fetch(config.urls.searchProjects + '?q=' + encodeURIComponent(keyword));
                const data = await response.json();

                if (data.success && data.projects.length > 0) {
                    results.innerHTML = data.projects.map(function(p) {
                        const escapedName = (p.name || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
                        const escapedOwner = (p.owner || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
                        return '<button type="button" class="w-full px-4 py-2 text-left hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors" onclick="QuotationModal.selectProject(' + p.id + ', \'' + escapedName + '\', \'' + escapedOwner + '\', \'' + (p.type || '') + '\', \'' + (p.stage || '') + '\')">' +
                            '<div class="text-sm font-medium text-slate-900 dark:text-white">' + p.name + '</div>' +
                            '<div class="text-xs text-slate-500 dark:text-slate-400">' + (p.owner || '') + ' | ' + (p.type || '') + ' | ' + (p.stage || '') + '</div>' +
                        '</button>';
                    }).join('');
                } else {
                    results.innerHTML = '<div class="p-3 text-sm text-slate-500">' + config.i18n.noProjectsFound + '</div>';
                }
            } catch (err) {
                console.error('搜索项目失败:', err);
                results.innerHTML = '<div class="p-3 text-sm text-red-500">' + config.i18n.loadError + '</div>';
            }
        }, 300);
    }

    /**
     * 选择项目
     * @param {number} id - 项目ID
     * @param {string} name - 项目名称
     * @param {string} owner - 项目负责人
     * @param {string} type - 项目类型
     * @param {string} stage - 项目阶段
     */
    function selectProject(id, name, owner, type, stage) {
        const projectIdInput = document.getElementById('project_id_modal');
        const projectSearchInput = document.getElementById('projectSearchModal');
        const dropdown = document.getElementById('projectDropdownModal');

        if (projectIdInput) projectIdInput.value = id;
        if (projectSearchInput) projectSearchInput.value = name;
        if (dropdown) dropdown.classList.add('hidden');

        // 显示清除按钮
        const clearBtn = document.getElementById('clearProjectBtnModal');
        if (clearBtn) clearBtn.classList.remove('hidden');

        // 加载客户列表
        loadProjectCustomers(id);
    }

    /**
     * 清除项目选择
     */
    function clearProject() {
        const projectIdInput = document.getElementById('project_id_modal');
        const projectSearchInput = document.getElementById('projectSearchModal');

        if (projectIdInput) projectIdInput.value = '';
        if (projectSearchInput) {
            projectSearchInput.value = '';
            projectSearchInput.readOnly = false;
        }

        // 隐藏清除按钮
        const clearBtn = document.getElementById('clearProjectBtnModal');
        if (clearBtn) clearBtn.classList.add('hidden');

        // 重置客户下拉
        const customerSelect = document.getElementById('customer_id_modal');
        if (customerSelect) {
            customerSelect.innerHTML = '<option value="">' + config.i18n.pleaseSelectProject + '</option>';
            customerSelect.disabled = true;
        }

        // 重置联系人下拉
        const contactSelect = document.getElementById('contact_id_modal');
        if (contactSelect) {
            contactSelect.innerHTML = '<option value="">' + config.i18n.pleaseSelectContact + '</option>';
            contactSelect.disabled = true;
        }
    }

    /**
     * 加载项目客户
     * @param {number} projectId - 项目ID
     */
    async function loadProjectCustomers(projectId) {
        const customerSelect = document.getElementById('customer_id_modal');
        if (!customerSelect) return;

        customerSelect.disabled = true;
        customerSelect.innerHTML = '<option value="">' + config.i18n.loading + '</option>';

        try {
            const response = await fetch(config.urls.getProjectCustomers + '/' + projectId);
            const data = await response.json();

            if (data.success && data.customers.length > 0) {
                customerSelect.innerHTML = '<option value="">' + config.i18n.pleaseSelectCustomer + '</option>' +
                    data.customers.map(function(c) {
                        return '<option value="' + c.id + '">' + c.name + '</option>';
                    }).join('');
                customerSelect.disabled = false;
            } else {
                customerSelect.innerHTML = '<option value="">' + config.i18n.noCustomersFound + '</option>';
            }
        } catch (err) {
            console.error('加载客户列表失败:', err);
            customerSelect.innerHTML = '<option value="">' + config.i18n.loadError + '</option>';
        }

        // 重置联系人下拉
        const contactSelect = document.getElementById('contact_id_modal');
        if (contactSelect) {
            contactSelect.innerHTML = '<option value="">' + config.i18n.pleaseSelectContact + '</option>';
            contactSelect.disabled = true;
        }
    }

    /**
     * 加载客户联系人
     * @param {number} customerId - 客户ID
     */
    async function loadCustomerContacts(customerId) {
        const contactSelect = document.getElementById('contact_id_modal');
        if (!contactSelect) return;

        contactSelect.disabled = true;
        contactSelect.innerHTML = '<option value="">' + config.i18n.loading + '</option>';

        try {
            const response = await fetch(config.urls.getCustomerContacts + '/' + customerId);
            const data = await response.json();

            if (data.success && data.contacts.length > 0) {
                contactSelect.innerHTML = '<option value="">' + config.i18n.pleaseSelectContact + '</option>' +
                    data.contacts.map(function(c) {
                        return '<option value="' + c.id + '">' + c.name + (c.position ? ' (' + c.position + ')' : '') + '</option>';
                    }).join('');
                contactSelect.disabled = false;
            } else {
                contactSelect.innerHTML = '<option value="">' + config.i18n.noContactsFound + '</option>';
            }
        } catch (err) {
            console.error('加载联系人列表失败:', err);
            contactSelect.innerHTML = '<option value="">' + config.i18n.loadError + '</option>';
        }
    }

    /**
     * 重置表单
     */
    function reset() {
        const form = document.getElementById('quotationFormModal-form');
        if (form) form.reset();

        // 清除项目选择
        clearProject();

        // 清除产品表格
        initProductTable();

        // 重置总计
        const grandTotalEl = document.getElementById('grandTotalModal');
        if (grandTotalEl) grandTotalEl.textContent = '0.00';

        currentMode = 'create';
        currentQuotationId = null;
    }

    /**
     * 设置预设项目
     * @param {number} projectId - 项目ID
     * @param {string} projectName - 项目名称
     */
    function setPresetProject(projectId, projectName) {
        if (!projectId) return;

        const projectIdInput = document.getElementById('project_id_modal');
        const projectSearchInput = document.getElementById('projectSearchModal');

        if (projectIdInput) projectIdInput.value = projectId;
        if (projectSearchInput) {
            projectSearchInput.value = projectName || '';
            projectSearchInput.readOnly = true;  // 预设时禁止编辑
        }

        // 预设项目时隐藏清除按钮
        const clearBtn = document.getElementById('clearProjectBtnModal');
        if (clearBtn) clearBtn.classList.add('hidden');

        // 加载客户列表
        loadProjectCustomers(projectId);
    }

    /**
     * 收集表单数据
     * @returns {Object} 表单数据
     */
    function collectFormData() {
        const projectIdInput = document.getElementById('project_id_modal');
        const customerSelect = document.getElementById('customer_id_modal');
        const contactSelect = document.getElementById('contact_id_modal');
        const currencySelect = document.getElementById('currency_modal');
        const notesTextarea = document.querySelector('#quotationFormModal-form [name="notes"]');

        const projectId = projectIdInput ? projectIdInput.value : '';
        const customerId = customerSelect ? customerSelect.value : '';
        const contactId = contactSelect ? contactSelect.value : '';
        const currency = currencySelect ? currencySelect.value : 'CNY';
        const notes = notesTextarea ? notesTextarea.value : '';

        // 获取产品明细
        let details = [];
        if (window.EditableTable) {
            details = window.EditableTable.getData('quotationProductTable');
        }

        // 计算总金额
        let totalAmount = 0;
        details.forEach(function(d) {
            totalAmount += parseFloat(d.total_price) || 0;
        });

        return {
            project_id: projectId,
            customer_id: customerId,
            contact_id: contactId || null,
            currency: currency,
            notes: notes,
            total_amount: totalAmount,
            details: details
        };
    }

    /**
     * 验证表单
     * @returns {boolean} 是否验证通过
     */
    function validate() {
        const data = collectFormData();
        const showAlert = window.showQuotationAlert || function(title, msg) { alert(title + (msg ? '\n' + msg : '')); };

        if (!data.project_id) {
            showAlert(config.i18n.projectRequired);
            return false;
        }

        if (!data.customer_id) {
            showAlert(config.i18n.customerRequired);
            return false;
        }

        if (!data.details || data.details.length === 0) {
            showAlert(config.i18n.productRequired);
            return false;
        }

        // 检查是否有有效的产品
        const validDetails = data.details.filter(function(d) {
            return d.product_name && d.product_name.trim() !== '';
        });

        if (validDetails.length === 0) {
            showAlert(config.i18n.productRequired);
            return false;
        }

        // 校验：每行 market_price 必须有值（处理"某货币下无面价"的情况）
        const missingPriceNames = [];
        validDetails.forEach(function(d) {
            const mp = parseFloat(d.market_price || 0);
            if (!mp || isNaN(mp)) {
                missingPriceNames.push(d.product_name);
            }
        });
        if (missingPriceNames.length > 0) {
            if (typeof window.showMarketPriceMissing === 'function') {
                window.showMarketPriceMissing(missingPriceNames);
            } else {
                alert('以下产品未填写市场单价，无法保存：\n\n' + missingPriceNames.join('\n'));
            }
            return false;
        }

        return true;
    }

    /**
     * 提交表单
     */
    async function submit() {
        if (!validate()) return;

        const submitBtn = document.getElementById('quotationFormModal-submit-btn');
        if (!submitBtn) return;

        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = currentMode === 'create' ? config.i18n.creating : config.i18n.saving;

        try {
            const data = collectFormData();
            const url = currentMode === 'create'
                ? config.urls.createQuotation
                : '/quotation/' + currentQuotationId + '/edit';

            const csrfToken = document.querySelector('meta[name="csrf-token"]');
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken ? csrfToken.content : ''
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.status === 'success' || result.success) {
                if (typeof closeFormModal === 'function') {
                    closeFormModal('quotationFormModal');
                }

                // 调用自定义成功回调
                if (config.onSuccess && typeof config.onSuccess === 'function') {
                    config.onSuccess(result);
                } else {
                    // 默认行为：跳转到新建的报价单详情页
                    if (result.quotation_id) {
                        window.location.href = '/quotation/' + result.quotation_id + '/detail?tw=1';
                    } else {
                        window.location.reload();
                    }
                }
            } else {
                const showAlert = window.showQuotationAlert || function(title, msg) { alert(title + (msg ? '\n' + msg : '')); };
                showAlert(result.message || config.i18n.saveError);
            }
        } catch (err) {
            console.error('提交失败:', err);
            const showAlert = window.showQuotationAlert || function(title, msg) { alert(title + (msg ? '\n' + msg : '')); };
            showAlert(config.i18n.saveError);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    /**
     * 绑定事件
     */
    /**
     * 货币切换时批量刷新已有产品面价
     * @param {string} newCurrency - 新货币代码
     */
    function refreshMarketPricesByCurrency(newCurrency) {
        const tableId = 'quotationProductTable';
        const instance = window.EditableTable?.instances?.[tableId];
        if (!instance || !instance.rows.length) return;

        // 收集所有有 product_id 的行
        const productIds = [];
        const rowMap = {};
        instance.rows.forEach(function(r) {
            const pid = r.data.product_id || r.data.id;
            if (pid && !r.data.is_temp) {
                productIds.push(pid);
                if (!rowMap[pid]) rowMap[pid] = [];
                rowMap[pid].push(r.rowId);
            }
        });

        if (!productIds.length) return;

        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

        fetch('/api/products/region-prices/batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                product_ids: [...new Set(productIds)],
                currency: newCurrency
            })
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            const prices = data.prices || {};
            const missingProductNames = [];

            Object.keys(rowMap).forEach(function(pid) {
                const price = prices[pid];
                rowMap[pid].forEach(function(rowId) {
                    const rowData = instance.rows.find(function(r) { return r.rowId === rowId; });
                    if (!rowData) return;
                    const row = document.getElementById(rowId);

                    if (price === undefined) {
                        // 未配置该货币面价 — 清零 market_price / unit_price / total_price
                        rowData.data.market_price = 0;
                        rowData.data.unit_price = 0;
                        rowData.data.total_price = 0;
                        rowData.data._regionPriceMissing = true;
                        const name = rowData.data.product_name || ('#' + pid);
                        if (missingProductNames.indexOf(name) === -1) missingProductNames.push(name);

                        window.EditableTable.rebuildMarketPriceCell(tableId, rowId, rowData.data);
                        // 显式清零 unit_price 和 total_price 的 DOM（calculateUnitPrice 在 market_price=0 时会提前返回）
                        if (row) {
                            const unitInput = row.querySelector('input[data-col-key="unit_price"]');
                            if (unitInput) unitInput.value = '0.00';
                            const totalEl = row.querySelector('input[data-col-key="total_price"], span[data-col-key="total_price"]');
                            if (totalEl) {
                                if (totalEl.tagName === 'INPUT') totalEl.value = '0.00';
                                else totalEl.textContent = '0.00';
                            }
                        }
                    } else {
                        // 有面价 — 更新 market_price 并重算 unit_price / total_price
                        rowData.data.market_price = price;
                        rowData.data._regionPriceMissing = false;
                        window.EditableTable.rebuildMarketPriceCell(tableId, rowId, rowData.data);
                        window.EditableTable.calculateUnitPrice(tableId, rowId);
                        window.EditableTable.calculateTotalPrice(tableId, rowId);
                    }
                });
            });
            setTimeout(function() { window.EditableTable.calculateGrandTotal(tableId); }, 10);
            // 缺面价的行已通过黄色高亮 + 可编辑 input 提示用户，不主动弹窗打断
            // 保存时 validate() 会统一阻止并提示
        })
        .catch(function(err) {
            console.warn('批量获取地区面价失败:', err);
            const showAlert = window.showQuotationAlert || function(title, msg) { alert(title + (msg ? '\n' + msg : '')); };
            showAlert('获取地区面价失败，请检查网络后重试');
        });
    }

    function bindEvents() {
        document.addEventListener('DOMContentLoaded', function() {
            // 项目搜索
            const projectSearch = document.getElementById('projectSearchModal');
            if (projectSearch) {
                projectSearch.addEventListener('input', function() {
                    // 只有非只读状态才允许搜索
                    if (!this.readOnly) {
                        searchProjects(this.value);
                    }
                });
                projectSearch.addEventListener('focus', function() {
                    if (!this.readOnly && this.value.length >= 2) {
                        searchProjects(this.value);
                    }
                });
            }

            // 客户变化时加载联系人
            const customerSelect = document.getElementById('customer_id_modal');
            if (customerSelect) {
                customerSelect.addEventListener('change', function() {
                    if (this.value) {
                        loadCustomerContacts(this.value);
                    }
                });
            }

            // 货币变化 → 批量刷新已有产品面价
            const currencySelect = document.getElementById('currency_modal');
            if (currencySelect) {
                currencySelect.addEventListener('change', function() {
                    refreshMarketPricesByCurrency(this.value);
                });
            }

            // 监听总计变化
            document.addEventListener('grandTotalUpdated', function(e) {
                if (e.detail && e.detail.tableId === 'quotationProductTable') {
                    const grandTotalEl = document.getElementById('grandTotalModal');
                    if (grandTotalEl) {
                        grandTotalEl.textContent = e.detail.formatted || '0.00';
                    }
                }
            });

            // 点击下拉框外部关闭
            document.addEventListener('click', function(e) {
                const dropdown = document.getElementById('projectDropdownModal');
                const searchInput = document.getElementById('projectSearchModal');
                if (dropdown && !dropdown.contains(e.target) && e.target !== searchInput) {
                    dropdown.classList.add('hidden');
                }
            });
        });
    }

    // 公开 API
    return {
        init: init,
        initProductTable: initProductTable,
        initProductSelector: initProductSelector,
        searchProjects: searchProjects,
        selectProject: selectProject,
        clearProject: clearProject,
        loadProjectCustomers: loadProjectCustomers,
        loadCustomerContacts: loadCustomerContacts,
        reset: reset,
        setPresetProject: setPresetProject,
        collectFormData: collectFormData,
        validate: validate,
        submit: submit,
        getConfig: function() { return config; }
    };
})();

/**
 * 打开新建报价单模态框
 * @param {Object} options - 选项
 * @param {number} options.presetProjectId - 预设项目ID
 * @param {string} options.presetProjectName - 预设项目名称
 */
window.openAddQuotationModal = function(options) {
    options = options || {};

    QuotationModal.reset();
    QuotationModal.initProductTable();
    QuotationModal.initProductSelector();

    // 如果有预设项目，设置它
    // 优先使用 options 传入的，否则使用 config 中初始化时配置的
    const config = QuotationModal.getConfig();
    const presetProjectId = options.presetProjectId || config.presetProjectId;
    const presetProjectName = options.presetProjectName || config.presetProjectName;
    if (presetProjectId) {
        QuotationModal.setPresetProject(presetProjectId, presetProjectName);
    }

    // 使用全局的 openFormModal 函数打开模态框
    if (typeof openFormModal === 'function') {
        openFormModal('quotationFormModal', {
            title: config.i18n.newQuotation,
            submitText: config.i18n.create,
            onSubmit: function() {
                QuotationModal.submit();
            }
        });
    } else {
        console.error('[QuotationModal] openFormModal function not found!');
    }
};
