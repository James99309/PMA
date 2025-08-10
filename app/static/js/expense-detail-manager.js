/**
 * 通用报销明细管理组件
 * 参考产品明细组件设计，专门为报销业务优化
 * 
 * @author Claude AI
 * @version 1.0.0
 */

class ExpenseDetailManager {
    constructor(config) {
        this.config = this.mergeConfig(config);
        this.rows = [];
        this.eventHandlers = new Map();
        
        this.init();
    }
    
    /**
     * 合并默认配置和用户配置
     */
    mergeConfig(config) {
        const defaultConfig = {
            // 基础配置
            table_id: 'expenseTable',
            tableSelector: '#expenseTable',
            addButtonSelector: '#addExpense',
            grandTotalId: 'expenseGrandTotal',
            expenseCountId: 'expenseCount',
            documentCountId: 'documentCount',
            
            // 报销科目配置
            categories: [
                {value: 'entertainment', label: '招待费', color: '#ff6b6b'},
                {value: 'local_transport', label: '市内交通', color: '#4ecdc4'},
                {value: 'travel_accommodation', label: '差旅住宿', color: '#45b7d1'},
                {value: 'office_supplies', label: '办公用品', color: '#96ceb4'},
                {value: 'communication', label: '通讯费', color: '#ffeaa7'},
                {value: 'fuel', label: '油费', color: '#dda0dd'},
                {value: 'parking', label: '停车费', color: '#98d8c8'},
                {value: 'meals', label: '餐费', color: '#f7dc6f'},
                {value: 'other', label: '其他', color: '#aab7b8'}
            ],
            
            // 字段映射配置
            fieldMapping: {
                expense_category: 'expense_category',
                expense_date: 'expense_date',
                description: 'description',
                document_count: 'document_count',
                amount: 'amount'
            },
            
            // 验证规则
            validators: {
                expense_category: (val) => val && val.trim() !== '',
                expense_date: (val) => val && val.trim() !== '',
                description: (val) => val && val.trim() !== '',
                document_count: (val) => parseInt(val) > 0,
                amount: (val) => parseFloat(val) > 0
            },
            
            // 列配置
            columns: [
                {
                    key: 'expense_category',
                    label: '报销科目',
                    type: 'select',
                    required: true,
                    width: '120px'
                },
                {
                    key: 'expense_date',
                    label: '发生日期',
                    type: 'date',
                    required: true,
                    width: '130px'
                },
                {
                    key: 'description',
                    label: '费用描述',
                    type: 'text',
                    required: true,
                    width: '300px'
                },
                {
                    key: 'document_count',
                    label: '数量',
                    type: 'number',
                    required: false,
                    width: '80px'
                },
                {
                    key: 'amount',
                    label: '金额(元)',
                    type: 'text-currency',
                    required: true,
                    width: '120px'
                },
                {
                    key: 'actions',
                    label: '操作',
                    type: 'actions',
                    width: '80px'
                }
            ]
        };
        
        const mergedConfig = Object.assign({}, defaultConfig, config);
        
        // 🔥 处理字符串引用的全局变量
        this.resolveStringReferences(mergedConfig);
        
        return mergedConfig;
    }
    
    /**
     * 解析配置中的字符串引用为实际的JavaScript变量
     */
    resolveStringReferences(config) {
        try {
            // 处理 currency_options 字符串引用
            if (config.currency_options && typeof config.currency_options === 'string') {
                const variableName = config.currency_options;
                if (window[variableName]) {
                    config.currency_options = window[variableName];
                    console.log(`✅ 解析货币选项引用: ${variableName}`, config.currency_options);
                } else {
                    console.warn(`⚠️ 未找到全局变量: ${variableName}`);
                }
            }
            
            // 处理列配置中的 options 字符串引用
            if (config.columns && Array.isArray(config.columns)) {
                config.columns.forEach(column => {
                    if (column.options && typeof column.options === 'string') {
                        const variableName = column.options;
                        if (window[variableName]) {
                            column.options = window[variableName];
                            console.log(`✅ 解析列选项引用: ${column.key}.options = ${variableName}`, column.options);
                        } else {
                            console.warn(`⚠️ 未找到全局变量: ${variableName}`);
                        }
                    }
                });
            }
            
        } catch (error) {
            console.error('解析字符串引用失败:', error);
        }
    }
    
    /**
     * 初始化组件
     */
    init() {
        // 清理任何残留的模态框
        this.cleanupModalBackdrops();
        
        this.tableElement = document.querySelector(this.config.tableSelector);
        this.addButton = document.querySelector(this.config.addButtonSelector);
        this.grandTotalElement = document.getElementById(this.config.grandTotalId);
        
        if (!this.tableElement) {
            console.error('报销明细表格元素未找到:', this.config.tableSelector);
            return;
        }
        
        this.bindEvents();
        this.addRow(); // 默认添加一行
        
        // 初始化货币符号
        this.updateCurrencySymbol();
        
        // 添加页面卸载时的清理
        this.setupPageUnloadCleanup();
        
        // 监听窗口大小变化，切换显示模式
        this.setupResponsiveListener();
        
        // 初始渲染 - 确保移动端和桌面端都正确显示
        this.renderTable();
        
        console.log('报销明细管理器初始化完成');
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        if (this.addButton) {
            this.addButton.addEventListener('click', () => this.addRow());
        }
        
        // 绑定表格事件代理
        this.tableElement.addEventListener('change', (e) => this.handleFieldChange(e));
        this.tableElement.addEventListener('input', (e) => this.handleFieldInput(e));
        this.tableElement.addEventListener('click', (e) => this.handleButtonClick(e));
    }
    
    /**
     * 添加一行
     */
    addRow(data = null) {
        const rowIndex = this.rows.length;
        const rowId = `expense-row-${rowIndex}`;
        
        const rowData = data || {
            expense_category: '',
            expense_date: new Date().toISOString().split('T')[0], // 默认今天
            description: '',
            document_count: 0, // 默认0个单据
            currency: '', // 货币类型，会在创建元素时设为默认值
            invoice_amount: 0, // 发票金额
            current_amount: 0, // 当前金额（转换后）
            amount: 0, // 向后兼容
            exchange_rate: 1.0000, // 汇率，默认1:1
            invoice_images: [] // 初始化发票图片数组
        };
        
        this.rows.push(rowData);
        
        const row = this.createRowElement(rowData, rowIndex, rowId);
        this.tableElement.querySelector('tbody').appendChild(row);
        
        this.updateSummary();
        
        // 更新移动端显示
        if (this.isMobileView()) {
            this.renderMobileCards();
        }
        
        return row;
    }
    
    /**
     * 创建行元素
     */
    createRowElement(data, rowIndex, rowId) {
        const row = document.createElement('tr');
        row.id = rowId;
        row.dataset.rowIndex = rowIndex;
        
        this.config.columns.forEach(column => {
            const cell = document.createElement('td');
            
            // 为发票显示列添加特殊类名
            if (column.type === 'invoice_display') {
                cell.className = 'invoice-display-column-cell';
            }
            
            cell.appendChild(this.createFieldElement(column, data, rowIndex));
            row.appendChild(cell);
        });
        
        return row;
    }
    
    /**
     * 创建字段元素
     */
    createFieldElement(column, data, rowIndex) {
        const fieldName = `details[${rowIndex}][${column.key}]`;
        const fieldId = `${column.key}_${rowIndex}`;
        
        switch (column.type) {
            case 'select':
                return this.createSelectElement(column, data, fieldName, fieldId, rowIndex);
            case 'date':
                return this.createDateElement(column, data, fieldName, fieldId, rowIndex);
            case 'number':
                return this.createNumberElement(column, data, fieldName, fieldId, rowIndex);
            case 'text-currency':
                return this.createTextCurrencyElement(column, data, fieldName, fieldId, rowIndex);
            case 'currency_display':
                return this.createCurrencyDisplayElement(column, data, fieldName, fieldId, rowIndex);
            case 'exchange_rate_input':
                return this.createExchangeRateInputElement(column, data, fieldName, fieldId, rowIndex);
            case 'invoice_upload':
                return this.createInvoiceUploadElement(column, data, rowIndex);
            case 'invoice_display':
                return this.createInvoiceDisplayElement(column, data, rowIndex);
            case 'actions':
                return this.createActionsElement(rowIndex);
            case 'actions_with_invoice':
                return this.createActionsWithInvoiceElement(rowIndex);
            default:
                return this.createTextElement(column, data, fieldName, fieldId, rowIndex);
        }
    }
    
    /**
     * 创建发票上传元素
     */
    createInvoiceUploadElement(column, data, rowIndex) {
        const container = document.createElement('div');
        container.innerHTML = this.renderInvoiceUploadCell(rowIndex, data.invoice_images || []);
        
        // 绑定事件
        setTimeout(() => {
            this.bindInvoiceEvents(rowIndex);
        }, 0);
        
        return container.firstElementChild;
    }
    
    /**
     * 创建选择框元素（报销科目）
     */
    createSelectElement(column, data, fieldName, fieldId, rowIndex) {
        const select = document.createElement('select');
        select.name = fieldName;
        select.id = fieldId;
        select.dataset.rowIndex = rowIndex;
        select.dataset.field = column.key;
        
        if (column.required) {
            select.required = true;
        }
        
        // 根据字段类型设置不同的样式和选项
        if (column.key === 'currency') {
            // 货币选择器
            select.className = 'form-select currency-select';
            
            // 添加默认选项
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = window.i18nTexts?.pleaseSelectCurrency || '请选择货币';
            select.appendChild(defaultOption);
            
            // 添加货币选项
            if (column.options) {
                // 获取报销单的基准货币，用作默认选择
                const expenseCurrencyElement = document.getElementById('currency');
                const expenseCurrency = expenseCurrencyElement ? expenseCurrencyElement.value : 'CNY';
                
                column.options.forEach(option => {
                    const optionElement = document.createElement('option');
                    optionElement.value = option.value;
                    optionElement.textContent = option.label;
                    
                    // 如果是新建行且没有指定货币，默认使用报销单货币
                    const shouldSelect = data[column.key] === option.value || 
                                       (!data[column.key] && option.value === expenseCurrency);
                    
                    if (shouldSelect) {
                        optionElement.selected = true;
                    }
                    
                    select.appendChild(optionElement);
                });
            }
            
            // 添加货币变更事件监听器
            select.addEventListener('change', (e) => {
                this.handleCurrencyChange(rowIndex, e.target.value);
            });
            
        } else {
            // 报销科目选择器（默认行为）
            select.className = 'form-select expense-category-select';
            
            // 添加默认选项
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = window.i18nTexts?.pleaseSelectCategory || '请选择科目';
            select.appendChild(defaultOption);
            
            // 添加科目选项
            this.config.categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.value;
                option.textContent = category.label;
                option.dataset.color = category.color;
                
                if (data[column.key] === category.value) {
                    option.selected = true;
                }
                
                select.appendChild(option);
            });
        }
        
        return select;
    }
    
    /**
     * 创建日期元素
     */
    createDateElement(column, data, fieldName, fieldId, rowIndex) {
        const input = document.createElement('input');
        input.type = 'date';
        input.className = 'form-control';
        input.name = fieldName;
        input.id = fieldId;
        input.value = data[column.key] || '';
        input.dataset.rowIndex = rowIndex;
        input.dataset.field = column.key;
        
        if (column.required) {
            input.required = true;
        }
        
        return input;
    }
    
    /**
     * 创建文本货币元素（金额输入框）
     */
    createTextCurrencyElement(column, data, fieldName, fieldId, rowIndex) {
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control text-end';
        input.name = fieldName;
        input.id = fieldId;
        input.value = data[column.key] || '';
        input.placeholder = '0.00';
        input.dataset.rowIndex = rowIndex;
        input.dataset.field = column.key;
        
        // 添加输入格式化
        input.addEventListener('input', (e) => {
            // 只允许数字和小数点
            let value = e.target.value.replace(/[^\d.]/g, '');
            // 确保只有一个小数点
            const parts = value.split('.');
            if (parts.length > 2) {
                value = parts[0] + '.' + parts.slice(1).join('');
            }
            // 限制小数点后两位
            if (parts[1] && parts[1].length > 2) {
                value = parts[0] + '.' + parts[1].substring(0, 2);
            }
            e.target.value = value;
            
            // 如果是发票金额字段，触发货币转换（延迟执行，等待用户输入完成）
            if (column.key === 'invoice_amount') {
                clearTimeout(this.convertTimeout);
                this.convertTimeout = setTimeout(() => {
                    this.handleInvoiceAmountChange(rowIndex);
                }, 500); // 500ms延迟，避免频繁转换
            }
        });
        
        if (column.required) {
            input.required = true;
        }
        
        return input;
    }
    
    /**
     * 创建货币显示元素（只读，显示转换后金额）
     */
    createCurrencyDisplayElement(column, data, fieldName, fieldId, rowIndex) {
        const container = document.createElement('div');
        container.className = 'currency-display-container';
        
        const display = document.createElement('input');
        display.type = 'text';
        display.className = 'form-control text-end currency-display';
        display.name = fieldName;
        display.id = fieldId;
        // 获取报销单的基准货币
        const expenseCurrencyElement = document.getElementById('currency');
        const expenseCurrency = expenseCurrencyElement ? expenseCurrencyElement.value : 'CNY';
        display.value = this.formatCurrency(data[column.key] || 0, expenseCurrency);
        display.readOnly = true;
        display.dataset.rowIndex = rowIndex;
        display.dataset.field = column.key;
        display.style.backgroundColor = '#f8f9fa';
        display.style.color = '#6c757d';
        
        // 隐藏的数值字段，用于表单提交
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = fieldName;
        hiddenInput.value = data[column.key] || 0;
        
        container.appendChild(display);
        container.appendChild(hiddenInput);
        
        return container;
    }
    
    /**
     * 创建汇率输入元素
     */
    createExchangeRateInputElement(column, data, fieldName, fieldId, rowIndex) {
        const container = document.createElement('div');
        container.className = 'exchange-rate-input-container';
        
        const input = document.createElement('input');
        input.type = 'number';
        input.className = 'form-control text-center exchange-rate-input';
        input.name = fieldName;
        input.id = fieldId;
        input.value = data[column.key] || 1.0000;
        input.step = '0.0001';
        input.min = '0.0001';
        input.placeholder = '1.0000';
        input.dataset.rowIndex = rowIndex;
        input.dataset.field = column.key;
        
        // 汇率变化时重新计算报销金额
        input.addEventListener('input', () => {
            this.handleExchangeRateChange(rowIndex, parseFloat(input.value) || 1.0);
        });
        
        // 失去焦点时格式化显示并重新计算
        input.addEventListener('blur', () => {
            const rate = parseFloat(input.value) || 1.0;
            input.value = rate.toFixed(4);
            // 触发重新计算
            this.handleExchangeRateChange(rowIndex, rate);
        });
        
        container.appendChild(input);
        
        return container;
    }
    
    /**
     * 处理货币变更事件
     */
    async handleCurrencyChange(rowIndex, newCurrency) {
        try {
            console.log(`🔄 处理货币变更，行索引: ${rowIndex}, 新货币: ${newCurrency}`);
            
            // 获取当前行的发票金额
            const invoiceAmountElement = document.querySelector(`input[data-row-index="${rowIndex}"][data-field="invoice_amount"]`);
            const currentAmountElement = document.querySelector(`input[data-row-index="${rowIndex}"][data-field="current_amount"]`);
            
            if (!invoiceAmountElement || !currentAmountElement) {
                console.warn('找不到金额元素');
                return;
            }
            
            const invoiceAmount = parseFloat(invoiceAmountElement.value) || 0;
            
            // 获取报销单的基准货币
            const expenseCurrencyElement = document.getElementById('currency');
            const expenseCurrency = expenseCurrencyElement ? expenseCurrencyElement.value : 'CNY';
            
            if (invoiceAmount <= 0) {
                console.log('发票金额为0，设置当前金额为0，但仍需设置正确汇率');
                // 即使发票金额为0，也要设置正确的汇率
                if (newCurrency === expenseCurrency) {
                    this.updateExchangeRateInput(rowIndex, 1.0);
                } else {
                    // 异步获取汇率但不等待，用于下次输入金额时使用
                    this.getExchangeRateAsync(newCurrency, expenseCurrency, rowIndex);
                }
                // 清空当前金额显示
                this.updateCurrentAmountDisplay(currentAmountElement, 0, expenseCurrency);
                this.calculateTotal();
                return;
            }
            
            console.log(`💱 发票金额: ${invoiceAmount} ${newCurrency}, 报销单货币: ${expenseCurrency}`);
            
            if (newCurrency === expenseCurrency) {
                // 如果货币相同，直接显示原金额
                console.log('货币相同，直接使用原金额');
                this.updateCurrentAmountDisplay(currentAmountElement, invoiceAmount, expenseCurrency);
                
                // 更新汇率为1:1
                this.updateExchangeRateInput(rowIndex, 1.0);
            } else {
                // 需要进行货币转换
                console.log('货币不同，开始转换...');
                
                // 显示转换中状态
                this.showConvertingStatus(currentAmountElement, true);
                
                try {
                    const convertedAmount = await this.convertCurrency(invoiceAmount, newCurrency, expenseCurrency);
                    console.log(`✅ 转换完成: ${invoiceAmount} ${newCurrency} -> ${convertedAmount} ${expenseCurrency}`);
                    this.updateCurrentAmountDisplay(currentAmountElement, convertedAmount, expenseCurrency);
                    
                    // 更新汇率输入框
                    const exchangeRate = convertedAmount / invoiceAmount;
                    this.updateExchangeRateInput(rowIndex, exchangeRate);
                } catch (error) {
                    console.error('货币转换失败:', error);
                    // 转换失败时显示原金额，但使用报销单货币格式
                    this.updateCurrentAmountDisplay(currentAmountElement, invoiceAmount, expenseCurrency);
                    this.showConversionError(currentAmountElement);
                } finally {
                    this.showConvertingStatus(currentAmountElement, false);
                }
            }
            
            // 重新计算总金额
            this.calculateTotal();
            
        } catch (error) {
            console.error('处理货币变更失败:', error);
        }
    }
    
    /**
     * 异步获取汇率（不阻塞界面）
     */
    async getExchangeRateAsync(fromCurrency, toCurrency, rowIndex) {
        try {
            console.log(`🔄 异步获取汇率: ${fromCurrency} -> ${toCurrency}`);
            const convertedAmount = await this.convertCurrency(1, fromCurrency, toCurrency);
            const exchangeRate = convertedAmount / 1; // 1单位fromCurrency对应的toCurrency金额
            
            console.log(`✅ 异步汇率获取完成: ${fromCurrency} -> ${toCurrency} = ${exchangeRate.toFixed(4)}`);
            this.updateExchangeRateInput(rowIndex, exchangeRate);
        } catch (error) {
            console.error('异步获取汇率失败:', error);
            // 失败时设置为1.0
            this.updateExchangeRateInput(rowIndex, 1.0);
        }
    }
    
    /**
     * 处理汇率变更事件
     */
    handleExchangeRateChange(rowIndex, newRate) {
        try {
            console.log(`🔄 处理汇率变更，行索引: ${rowIndex}, 新汇率: ${newRate}`);
            
            // 获取当前行的发票金额
            const invoiceAmountElement = document.querySelector(`input[data-row-index="${rowIndex}"][data-field="invoice_amount"]`);
            const currentAmountElement = document.querySelector(`input[data-row-index="${rowIndex}"][data-field="current_amount"]`);
            
            if (!invoiceAmountElement || !currentAmountElement) {
                console.warn('找不到金额元素');
                return;
            }
            
            // 获取报销单的基准货币
            const expenseCurrencyElement = document.getElementById('currency');
            const expenseCurrency = expenseCurrencyElement ? expenseCurrencyElement.value : 'CNY';
            
            const invoiceAmount = parseFloat(invoiceAmountElement.value) || 0;
            if (invoiceAmount <= 0) {
                console.log('发票金额为0，设置报销金额为0');
                this.updateCurrentAmountDisplay(currentAmountElement, 0, expenseCurrency);
                this.updateRowData(rowIndex, 'current_amount', 0);
                this.updateRowData(rowIndex, 'exchange_rate', newRate);
                this.calculateTotal();
                return;
            }
            
            // 根据汇率计算报销金额
            const convertedAmount = invoiceAmount * newRate;
            console.log(`💱 手动汇率计算: ${invoiceAmount} × ${newRate} = ${convertedAmount}`);
            
            // 更新报销金额显示
            this.updateCurrentAmountDisplay(currentAmountElement, convertedAmount, expenseCurrency);
            
            // 更新行数据
            this.updateRowData(rowIndex, 'current_amount', convertedAmount);
            this.updateRowData(rowIndex, 'exchange_rate', newRate);
            
            // 重新计算总金额
            this.calculateTotal();
            
        } catch (error) {
            console.error('处理汇率变更失败:', error);
        }
    }
    
    /**
     * 更新汇率输入框
     */
    updateExchangeRateInput(rowIndex, exchangeRate) {
        // 🔥 优先查找移动端汇率输入框，然后查找PC端
        let exchangeRateElement = document.querySelector(`.expense-detail-input-card input[data-row-index="${rowIndex}"][data-field="exchange_rate"]`);
        
        if (!exchangeRateElement) {
            // 如果没有找到移动端输入框，查找PC端表格中的输入框
            exchangeRateElement = document.querySelector(`table input[data-row-index="${rowIndex}"][data-field="exchange_rate"]`);
        }
        
        if (!exchangeRateElement) {
            // 兜底：使用原来的通用选择器
            exchangeRateElement = document.querySelector(`input[data-row-index="${rowIndex}"][data-field="exchange_rate"]`);
        }
        
        if (exchangeRateElement) {
            exchangeRateElement.value = exchangeRate.toFixed(4);
            // 更新行数据
            this.updateRowData(rowIndex, 'exchange_rate', exchangeRate);
            console.log(`✅ 汇率输入框已更新: ${exchangeRate.toFixed(4)} (元素类型: ${exchangeRateElement.closest('.expense-detail-input-card') ? '移动端' : 'PC端'})`);
            
            // 🔥 汇率更新后重新计算报销金额
            this.calculateCurrentAmountMobile(rowIndex);
            
            // 重新计算总金额
            this.calculateTotal();
        } else {
            console.warn(`❌ 未找到汇率输入框，rowIndex: ${rowIndex}`);
        }
    }
    
    /**
     * 显示转换中状态
     */
    showConvertingStatus(element, isConverting) {
        if (isConverting) {
            element.style.backgroundColor = '#fff3cd';
            element.style.borderColor = '#ffc107';
            if (element.classList.contains('currency-display')) {
                element.value = '转换中...';
            }
        } else {
            element.style.backgroundColor = '#f8f9fa';
            element.style.borderColor = '#ced4da';
        }
    }
    
    /**
     * 显示转换错误
     */
    showConversionError(element) {
        element.style.backgroundColor = '#f8d7da';
        element.style.borderColor = '#dc3545';
        
        // 3秒后恢复正常样式
        setTimeout(() => {
            element.style.backgroundColor = '#f8f9fa';
            element.style.borderColor = '#ced4da';
        }, 3000);
    }
    
    /**
     * 货币转换 - 参考产品明细管理器的转换方式
     */
    async convertCurrency(amount, fromCurrency, toCurrency) {
        if (fromCurrency === toCurrency) {
            return parseFloat(amount);
        }
        
        try {
            console.log(`🔄 开始货币转换: ${amount} ${fromCurrency} -> ${toCurrency}`);
            
            // 尝试使用API转换（与产品明细管理器相同的方式）
            const response = await fetch('/api/v1/exchange-rate/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
                },
                body: JSON.stringify({
                    amount: parseFloat(amount),
                    from_currency: fromCurrency,
                    to_currency: toCurrency
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    console.log(`💱 API转换成功: ${amount} ${fromCurrency} -> ${result.data.converted_amount} ${toCurrency}`);
                    return result.data.converted_amount;
                }
            }
            
            throw new Error('API转换失败');
            
        } catch (error) {
            console.warn('API转换失败，使用本地汇率转换:', error);
            
            // 回退到本地汇率转换
            if (window.currencySelector) {
                return await window.currencySelector.convertAmountLocally(amount, fromCurrency, toCurrency);
            } else {
                // 使用默认汇率
                return this.convertAmountWithDefaultRates(amount, fromCurrency, toCurrency);
            }
        }
    }
    
    /**
     * 使用默认汇率进行转换
     */
    convertAmountWithDefaultRates(amount, fromCurrency, toCurrency) {
        const defaultRates = {
            'CNY': 1.0,
            'USD': 0.14,    // 1 CNY = 0.14 USD，即 1 USD = 7.14 CNY
            'SGD': 0.19,    // 1 CNY = 0.19 SGD，即 1 SGD = 5.26 CNY  
            'EUR': 0.13,    // 1 CNY = 0.13 EUR，即 1 EUR = 7.69 CNY
            'MYR': 0.65,
            'IDR': 2100.0,
            'THB': 5.0
        };
        
        // 检查货币是否支持
        if (fromCurrency !== 'CNY' && !defaultRates[fromCurrency]) {
            console.error(`❌ 不支持的货币: ${fromCurrency}`);
            return parseFloat(amount); // 返回原金额
        }
        
        if (toCurrency !== 'CNY' && !defaultRates[toCurrency]) {
            console.error(`❌ 不支持的货币: ${toCurrency}`);
            return parseFloat(amount); // 返回原金额
        }
        
        let convertedAmount = parseFloat(amount);
        
        // 先转换为人民币
        if (fromCurrency !== 'CNY') {
            convertedAmount = convertedAmount / defaultRates[fromCurrency];
        }
        
        // 再转换为目标货币
        if (toCurrency !== 'CNY') {
            convertedAmount = convertedAmount * defaultRates[toCurrency];
        }
        
        console.log(`💱 默认汇率转换: ${amount} ${fromCurrency} -> ${convertedAmount.toFixed(2)} ${toCurrency}`);
        return Math.round(convertedAmount * 100) / 100;
    }
    
    /**
     * 更新当前金额显示
     */
    updateCurrentAmountDisplay(element, amount, currency) {
        // 更新DOM元素
        if (element.classList.contains('currency-display')) {
            // 更新显示值
            element.value = this.formatCurrency(amount, currency);
            // 更新隐藏字段值
            const hiddenInput = element.parentElement.querySelector('input[type="hidden"]');
            if (hiddenInput) {
                hiddenInput.value = amount;
            }
        } else {
            // 直接更新值
            element.value = amount;
        }
        
        // 同步更新数据数组中的值
        const rowIndex = parseInt(element.dataset.rowIndex);
        if (!isNaN(rowIndex) && this.rows[rowIndex]) {
            this.rows[rowIndex].current_amount = amount;
            // 同时更新 amount 字段以保持兼容性
            this.rows[rowIndex].amount = amount;
            console.log(`✅ 同步更新行 ${rowIndex} 的当前金额:`, amount);
        }
    }
    
    /**
     * 格式化货币显示
     */
    formatCurrency(amount, currency) {
        const symbols = {
            'CNY': '¥',
            'USD': '$',
            'SGD': 'S$',
            'MYR': 'RM',
            'IDR': 'Rp',
            'THB': '฿'
        };
        const symbol = symbols[currency] || '¥';
        return `${symbol}${parseFloat(amount).toFixed(2)}`;
    }
    
    /**
     * 更新行数据
     */
    updateRowData(rowIndex, field, value) {
        if (this.rows && this.rows[rowIndex]) {
            this.rows[rowIndex][field] = value;
            console.log(`✅ 更新行 ${rowIndex} 的 ${field}: ${value}`);
        } else {
            console.warn(`无法更新行数据: rowIndex=${rowIndex}, field=${field}, rows存在=${!!this.rows}`);
        }
    }
    
    /**
     * 处理发票金额变更事件
     */
    async handleInvoiceAmountChange(rowIndex) {
        try {
            console.log(`📝 发票金额变更，行索引: ${rowIndex}`);
            
            // 获取当前行的发票金额
            const invoiceAmountElement = document.querySelector(`input[data-row-index="${rowIndex}"][data-field="invoice_amount"]`);
            const invoiceAmount = parseFloat(invoiceAmountElement?.value || 0);
            
            // 同步更新数据数组中的发票金额
            if (this.rows[rowIndex]) {
                this.rows[rowIndex].invoice_amount = invoiceAmount;
            }
            
            if (invoiceAmount <= 0) {
                console.log('发票金额为0或无效，设置当前金额为0');
                // 获取报销单的基准货币
                const expenseCurrencyElement = document.getElementById('currency');
                const expenseCurrency = expenseCurrencyElement ? expenseCurrencyElement.value : 'CNY';
                // 清空当前金额
                const currentAmountElement = document.querySelector(`input[data-row-index="${rowIndex}"][data-field="current_amount"]`);
                if (currentAmountElement) {
                    this.updateCurrentAmountDisplay(currentAmountElement, 0, expenseCurrency);
                }
                return;
            }
            
            // 获取当前行的货币选择器
            const currencyElement = document.querySelector(`select[data-row-index="${rowIndex}"][data-field="currency"]`);
            const detailCurrency = currencyElement?.value;
            
            if (!detailCurrency) {
                console.log('明细货币未选择，跳过转换');
                return;
            }
            
            console.log(`💰 发票金额: ${invoiceAmount} ${detailCurrency}`);
            
            // 获取报销单的基准货币
            const expenseCurrencyElement = document.getElementById('currency');
            const expenseCurrency = expenseCurrencyElement ? expenseCurrencyElement.value : 'CNY';
            
            // 检查是否已有手动输入的汇率
            const exchangeRateElement = document.querySelector(`input[data-row-index="${rowIndex}"][data-field="exchange_rate"]`);
            const manualRate = parseFloat(exchangeRateElement?.value || 0);
            
            if (detailCurrency === expenseCurrency) {
                // 同货币，汇率为1:1，直接计算
                console.log('同货币，汇率1:1');
                this.handleExchangeRateChange(rowIndex, 1.0);
            } else if (manualRate > 0 && manualRate !== 1.0) {
                // 有手动汇率，直接使用手动汇率计算
                console.log(`💱 使用手动汇率: ${manualRate}`);
                this.handleExchangeRateChange(rowIndex, manualRate);
            } else {
                // 没有手动汇率，触发货币转换获取API汇率
                await this.handleCurrencyChange(rowIndex, detailCurrency);
            }
            
        } catch (error) {
            console.error('处理发票金额变更失败:', error);
        }
    }
    
    /**
     * 创建数字元素（单据数量）
     */
    createNumberElement(column, data, fieldName, fieldId, rowIndex) {
        const input = document.createElement('input');
        input.type = 'number';
        input.className = 'form-control text-center';
        input.name = fieldName;
        input.id = fieldId;
        input.value = data[column.key] || 1;
        input.min = '1';
        input.max = '9999';
        input.step = '1';
        input.style.width = '80px';
        input.dataset.rowIndex = rowIndex;
        input.dataset.field = column.key;
        
        // 为单据数量字段添加特殊处理
        if (column.key === 'document_count') {
            // 默认设置为自动计算模式（只读）
            input.readOnly = true;
            input.dataset.autoCalculate = 'true';
            input.classList.add('auto-calculate-mode');
            
            // 双击切换模式
            input.addEventListener('dblclick', (e) => {
                const isAutoMode = e.target.dataset.autoCalculate === 'true';
                
                if (isAutoMode) {
                    // 切换到手动编辑模式
                    e.target.readOnly = false;
                    e.target.dataset.autoCalculate = 'false';
                    e.target.classList.remove('auto-calculate-mode');
                    e.target.classList.add('manual-edit-mode');
                    e.target.title = '手动编辑模式 - 双击切换回自动计算';
                    e.target.focus();
                    e.target.select();
                    console.log('切换到手动编辑模式');
                } else {
                    // 切换回自动计算模式
                    e.target.readOnly = true;
                    e.target.dataset.autoCalculate = 'true';
                    e.target.classList.remove('manual-edit-mode');
                    e.target.classList.add('auto-calculate-mode');
                    e.target.title = '自动计算模式 - 根据发票数量自动更新（双击切换到手动编辑）';
                    
                    // 重新计算发票数量
                    const rowData = this.rows[rowIndex];
                    if (rowData && rowData.invoice_images) {
                        this.autoUpdateDocumentCount(rowIndex, rowData.invoice_images);
                    } else {
                        // 如果没有发票，默认为0
                        e.target.value = 0;
                    }
                    
                    console.log('切换到自动计算模式');
                }
            });
            
            // 初始状态的标题提示
            input.title = '自动计算模式 - 根据发票数量自动更新（双击切换到手动编辑）';
            
            // 允许数量为0
            input.min = '0';
        }
        
        return input;
    }
    
    
    /**
     * 创建文本元素
     */
    createTextElement(column, data, fieldName, fieldId, rowIndex) {
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control';
        input.name = fieldName;
        input.id = fieldId;
        input.value = data[column.key] || '';
        input.dataset.rowIndex = rowIndex;
        input.dataset.field = column.key;
        
        // 如果是描述字段，允许水平拉伸
        if (column.key === 'description') {
            input.style.resize = 'horizontal';
            input.style.minWidth = '200px';
            input.style.maxWidth = '500px';
        }
        
        if (column.required) {
            input.required = true;
        }
        
        return input;
    }
    
    /**
     * 创建操作按钮元素
     */
    createActionsElement(rowIndex) {
        const container = document.createElement('div');
        container.className = 'text-center';
        
        const deleteBtn = document.createElement('button');
        deleteBtn.type = 'button';
        deleteBtn.className = 'btn btn-danger btn-sm';
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
        deleteBtn.title = '删除此项';
        deleteBtn.dataset.action = 'delete';
        deleteBtn.dataset.rowIndex = rowIndex;
        
        container.appendChild(deleteBtn);
        
        return container;
    }
    
    /**
     * 创建带发票上传的操作按钮元素
     */
    createActionsWithInvoiceElement(rowIndex) {
        const container = document.createElement('div');
        container.className = 'text-center d-flex gap-1 justify-content-center align-items-center';
        container.dataset.rowIndex = rowIndex;
        
        // 发票上传按钮
        const invoiceBtn = document.createElement('button');
        invoiceBtn.type = 'button';
        invoiceBtn.className = 'btn btn-outline-primary btn-sm';
        invoiceBtn.innerHTML = '<i class="fas fa-file-invoice"></i>';
        invoiceBtn.title = '上传发票';
        invoiceBtn.dataset.action = 'upload-invoice';
        invoiceBtn.dataset.rowIndex = rowIndex;
        
        // 删除按钮
        const deleteBtn = document.createElement('button');
        deleteBtn.type = 'button';
        deleteBtn.className = 'btn btn-danger btn-sm';
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
        deleteBtn.title = '删除此项';
        deleteBtn.dataset.action = 'delete';
        deleteBtn.dataset.rowIndex = rowIndex;
        
        // 隐藏的文件上传输入框
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.className = 'invoice-upload-input';
        fileInput.id = `invoiceInput_${rowIndex}`;
        fileInput.accept = 'image/*,application/pdf,.heic,.heif';
        fileInput.multiple = true;
        fileInput.style.display = 'none';
        
        container.appendChild(invoiceBtn);
        container.appendChild(deleteBtn);
        container.appendChild(fileInput);
        
        // 绑定发票上传事件
        setTimeout(() => {
            this.bindInvoiceEvents(rowIndex);
        }, 0);
        
        return container;
    }
    
    /**
     * 创建发票显示元素
     */
    createInvoiceDisplayElement(column, data, rowIndex) {
        const container = document.createElement('div');
        container.className = 'invoice-display-column';
        container.dataset.rowIndex = rowIndex;
        
        // 强制设置内联样式确保水平布局
        container.style.cssText = `
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            min-width: 150px !important;
            max-width: 200px !important;
            width: 180px !important;
            gap: 6px !important;
            justify-content: flex-start !important;
            align-items: center !important;
            overflow-x: auto !important;
            overflow-y: hidden !important;
            padding: 8px 6px !important;
            box-sizing: border-box !important;
            background-color: transparent !important;
            border: none !important;
        `;
        
        const invoiceImages = data.invoice_images || [];
        
        // 延迟更新发票显示，确保DOM已渲染
        setTimeout(() => {
            this.updateInvoiceDisplay(rowIndex, invoiceImages);
            // 自动更新单据数量
            this.autoUpdateDocumentCount(rowIndex, invoiceImages);
        }, 10);
        
        return container;
    }
    
    /**
     * 处理字段变化事件
     */
    handleFieldChange(e) {
        const field = e.target.dataset.field;
        const rowIndex = parseInt(e.target.dataset.rowIndex);
        
        if (field && !isNaN(rowIndex)) {
            this.rows[rowIndex][field] = e.target.value;
            this.updateSummary();
            this.updateHiddenField(); // 同步数据到隐藏字段
            
            // 如果是科目选择，更新样式
            if (field === 'expense_category') {
                this.updateCategoryStyle(e.target);
            }
        }
    }
    
    /**
     * 处理字段输入事件
     */
    handleFieldInput(e) {
        const field = e.target.dataset.field;
        const rowIndex = parseInt(e.target.dataset.rowIndex);
        
        if (field && !isNaN(rowIndex)) {
            // 对于货币显示字段，需要特殊处理
            if (field === 'current_amount' && e.target.classList.contains('currency-display')) {
                // 从隐藏字段获取实际数值
                const hiddenInput = e.target.parentElement.querySelector('input[type="hidden"]');
                if (hiddenInput) {
                    this.rows[rowIndex][field] = parseFloat(hiddenInput.value) || 0;
                }
            } else {
                this.rows[rowIndex][field] = e.target.value;
            }
            
            // 如果是金额或数量字段，实时更新统计
            if (field === 'amount' || field === 'current_amount' || field === 'invoice_amount' || field === 'document_count') {
                this.updateSummary();
            }
        }
    }
    
    /**
     * 处理按钮点击事件
     */
    handleButtonClick(e) {
        const action = e.target.dataset.action || e.target.closest('[data-action]')?.dataset.action;
        const rowIndex = parseInt(e.target.dataset.rowIndex || e.target.closest('[data-row-index]')?.dataset.rowIndex);
        
        if (action === 'delete' && !isNaN(rowIndex)) {
            this.deleteRow(rowIndex);
        } else if (action === 'upload-invoice' && !isNaN(rowIndex)) {
            this.triggerInvoiceUpload(rowIndex);
        }
    }
    
    /**
     * 编辑行 - 移动端使用
     */
    editRow(rowIndex) {
        console.log('编辑明细行:', rowIndex);
        
        if (rowIndex < 0 || rowIndex >= this.rows.length) {
            console.warn('无效的行索引:', rowIndex);
            return;
        }
        
        const rowData = this.rows[rowIndex];
        console.log('编辑行数据:', rowData);
        
        // 🔥 在移动端，编辑操作切换到桌面视图进行编辑
        // 或者可以打开一个编辑模态框
        
        // 方案1：滚动到对应行并高亮显示
        console.log('🔍 查找表格行，rowIndex:', rowIndex);
        
        // 尝试多种选择器找到表格行
        const selectors = [
            `tr[data-row-index="${rowIndex}"]`,  // 表格行
            `[data-row-index="${rowIndex}"]`,    // 任何带data-row-index的元素
            `#expenseTable tr:nth-child(${rowIndex + 2})`, // 第N行（考虑表头）
            `.expense-table-row[data-row-index="${rowIndex}"]` // 带特定类的行
        ];
        
        let tableRow = null;
        for (let selector of selectors) {
            tableRow = document.querySelector(selector);
            console.log(`🔍 选择器 "${selector}" 找到元素:`, tableRow);
            if (tableRow) break;
        }
        
        if (tableRow) {
            console.log('✅ 找到表格行，开始高亮和滚动');
            
            // 🔥 更明显的高亮效果
            tableRow.style.backgroundColor = '#fff3cd';
            tableRow.style.border = '3px solid #ffc107';
            tableRow.style.boxShadow = '0 0 15px rgba(255, 193, 7, 0.5)';
            tableRow.style.transform = 'scale(1.02)';
            tableRow.style.transition = 'all 0.3s ease';
            
            // 🔥 延长高亮时间并添加闪烁效果
            let blinkCount = 0;
            const blinkInterval = setInterval(() => {
                tableRow.style.backgroundColor = tableRow.style.backgroundColor === 'rgb(255, 243, 205)' ? '#ffeb3b' : '#fff3cd';
                blinkCount++;
                if (blinkCount >= 6) { // 闪烁3次
                    clearInterval(blinkInterval);
                    tableRow.style.backgroundColor = '#fff3cd';
                }
            }, 300);
            
            // 5秒后恢复原状
            setTimeout(() => {
                tableRow.style.backgroundColor = '';
                tableRow.style.border = '';
                tableRow.style.boxShadow = '';
                tableRow.style.transform = '';
                tableRow.style.transition = '';
            }, 5000);
            
            // 滚动到该行
            tableRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // 聚焦到第一个可编辑字段
            const firstInput = tableRow.querySelector('input, select, textarea');
            console.log('🔍 找到的第一个输入字段:', firstInput);
            if (firstInput) {
                setTimeout(() => {
                    firstInput.focus();
                    firstInput.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    
                    // 🔥 让输入字段也闪烁一下
                    const originalBorder = firstInput.style.border;
                    firstInput.style.border = '2px solid #007bff';
                    firstInput.style.boxShadow = '0 0 10px rgba(0, 123, 255, 0.5)';
                    
                    setTimeout(() => {
                        firstInput.style.border = originalBorder;
                        firstInput.style.boxShadow = '';
                    }, 2000);
                }, 1000);
            }
        } else {
            console.warn('❌ 未找到对应的表格行，rowIndex:', rowIndex);
            console.log('🔍 页面中所有带data-row-index的元素:', 
                document.querySelectorAll('[data-row-index]'));
        }
        
        // 🔥 检查是否为移动端视图
        const isMobileView = window.innerWidth <= 768 || document.querySelector('.expense-detail-mobile-cards');
        
        if (isMobileView && !tableRow) {
            // 移动端且找不到表格行，说明是纯卡片视图
            console.log('🔥 移动端卡片视图，切换为内联编辑模式');
            this.enableInlineEditForMobile(rowIndex);
        } else {
            // 桌面端或混合视图，显示提示消息
            if (window.showTopNotification) {
                window.showTopNotification('请在上方表格中编辑明细信息', 'info');
            } else {
                console.log('提示：请在上方表格中编辑明细信息');
            }
        }
    }
    
    /**
     * 🔥 移动端内联编辑模式
     */
    enableInlineEditForMobile(rowIndex) {
        console.log('🔥 启用移动端内联编辑，rowIndex:', rowIndex);
        
        const rowData = this.rows[rowIndex];
        if (!rowData) {
            console.warn('行数据不存在:', rowIndex);
            return;
        }
        
        // 查找移动端卡片
        const mobileCard = document.querySelector(`[data-row-index="${rowIndex}"].expense-detail-card`);
        if (!mobileCard) {
            console.warn('未找到移动端卡片:', rowIndex);
            return;
        }
        
        console.log('✅ 找到移动端卡片，开始转换为编辑模式');
        
        // 创建编辑表单HTML
        const editFormHTML = this.createMobileEditForm(rowData, rowIndex);
        
        // 替换卡片内容
        mobileCard.innerHTML = editFormHTML;
        
        // 绑定保存和取消事件
        this.bindMobileEditEvents(mobileCard, rowIndex, rowData);
        
        // 添加移动端编辑样式（如果不存在）
        this.addMobileEditStyles();
        
        // 显示成功提示
        if (window.showTopNotification) {
            window.showTopNotification('已切换到编辑模式', 'success');
        }
    }
    
    /**
     * 🔥 创建移动端编辑表单
     */
    createMobileEditForm(rowData, rowIndex) {
        return `
            <div class="expense-detail-mobile-edit-form">
                <div class="mobile-edit-header">
                    <h6 class="mb-0">编辑报销明细</h6>
                </div>
                
                <div class="mobile-edit-fields">
                    <div class="mb-3">
                        <label class="form-label">报销科目</label>
                        <select class="form-select" name="expense_category" data-field="expense_category">
                            <option value="">请选择科目</option>
                            <option value="交通费" ${rowData.expense_category === '交通费' ? 'selected' : ''}>交通费</option>
                            <option value="餐费" ${rowData.expense_category === '餐费' ? 'selected' : ''}>餐费</option>
                            <option value="住宿费" ${rowData.expense_category === '住宿费' ? 'selected' : ''}>住宿费</option>
                            <option value="办公用品" ${rowData.expense_category === '办公用品' ? 'selected' : ''}>办公用品</option>
                            <option value="其他" ${rowData.expense_category === '其他' ? 'selected' : ''}>其他</option>
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">日期</label>
                        <input type="date" class="form-control" name="expense_date" data-field="expense_date" value="${rowData.expense_date || ''}">
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">说明描述</label>
                        <textarea class="form-control" name="description" data-field="description" rows="2" placeholder="请输入费用说明">${rowData.description || ''}</textarea>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">发票金额</label>
                        <input type="number" class="form-control" name="amount" data-field="amount" step="0.01" value="${rowData.amount || ''}">
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">币种</label>
                        <select class="form-select" name="currency" data-field="currency">
                            <option value="CNY" ${rowData.currency === 'CNY' ? 'selected' : ''}>人民币 (CNY)</option>
                            <option value="USD" ${rowData.currency === 'USD' ? 'selected' : ''}>美元 (USD)</option>
                            <option value="SGD" ${rowData.currency === 'SGD' ? 'selected' : ''}>新币 (SGD)</option>
                        </select>
                    </div>
                </div>
                
                <div class="mobile-edit-actions">
                    <button type="button" class="btn btn-outline-secondary btn-cancel">取消</button>
                    <button type="button" class="btn btn-primary btn-save">保存</button>
                </div>
            </div>
        `;
    }
    
    /**
     * 🔥 绑定移动端编辑事件
     */
    bindMobileEditEvents(mobileCard, rowIndex, originalData) {
        const saveBtn = mobileCard.querySelector('.btn-save');
        const cancelBtn = mobileCard.querySelector('.btn-cancel');
        
        // 保存按钮
        saveBtn.addEventListener('click', () => {
            console.log('🔥 移动端保存编辑');
            
            // 收集表单数据
            const formData = {};
            mobileCard.querySelectorAll('[data-field]').forEach(input => {
                formData[input.dataset.field] = input.value;
            });
            
            console.log('🔥 收集的表单数据:', formData);
            
            // 更新行数据
            Object.assign(this.rows[rowIndex], formData);
            
            // 重新渲染
            this.renderTable();
            
            // 显示成功提示
            if (window.showTopNotification) {
                window.showTopNotification('保存成功', 'success');
            }
        });
        
        // 取消按钮
        cancelBtn.addEventListener('click', () => {
            console.log('🔥 移动端取消编辑');
            
            // 重新渲染恢复原状
            this.renderTable();
            
            if (window.showTopNotification) {
                window.showTopNotification('已取消编辑', 'info');
            }
        });
    }
    
    /**
     * 🔥 添加移动端编辑样式
     */
    addMobileEditStyles() {
        if (document.getElementById('mobile-edit-styles')) {
            return; // 样式已存在
        }
        
        const style = document.createElement('style');
        style.id = 'mobile-edit-styles';
        style.textContent = `
            .expense-detail-mobile-edit-form {
                padding: 1rem;
                background: #f8f9fa;
                border-radius: 8px;
                border: 2px solid #007bff;
            }
            
            /* 🔥 移动端输入卡片样式 */
            .expense-detail-input-card {
                background: #fff;
                border: 1px solid #e9ecef;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                margin-bottom: 1rem;
            }
            
            .mobile-input-card-content {
                padding: 1rem;
            }
            
            
            .mobile-input-fields {
                display: grid;
                gap: 1rem;
            }
            
            .mobile-input-row {
                display: flex;
                flex-direction: column;
            }
            
            .mobile-input-row.full-width {
                grid-column: 1 / -1;
            }
            
            .mobile-input-label {
                font-size: 0.875rem;
                font-weight: 500;
                color: #495057;
                margin-bottom: 0.25rem;
            }
            
            .mobile-input-field {
                border-radius: 6px;
                border: 1px solid #ced4da;
                font-size: 1rem;
            }
            
            .mobile-input-field:focus {
                border-color: #007bff;
                box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
            }
            
            /* 🔥 移动端发票区域样式 */
            .mobile-invoice-container {
                padding: 12px;
                border: 1px solid #e9ecef;
                border-radius: 12px;
                background: #f8f9fa;
                min-height: 56px;
                flex: 1;
            }
            
            .mobile-invoice-display {
                min-height: 40px;
                display: flex !important;
                align-items: center;
                gap: 8px;
                position: relative;
                width: 100%;
            }
            
            .mobile-invoice-display:empty::after {
                content: "发票图标";
                color: #adb5bd;
                font-size: 0.75rem;
                opacity: 0.8;
            }
            
            /* 🔥 标准按键样式支持 */
            .min-width-sm {
                min-width: 80px;
            }
            
            .text-xs {
                font-size: 0.75rem;
            }
            
            /* 底部区域布局 */
            .mobile-bottom-section {
                display: flex;
                justify-content: space-between;
                align-items: flex-end;
                gap: 1rem;
                margin-top: 0.5rem;
            }
            
            .mobile-input-actions {
                display: flex;
                gap: 8px;
                align-items: center;
                flex-shrink: 0;
            }
            
            .mobile-input-actions .btn {
                min-width: 40px;
                height: 32px;
                font-size: 0.875rem;
                line-height: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }
            
            /* 圆形按钮样式 */
            .btn-circle {
                width: 32px !important;
                height: 32px !important;
                min-width: 32px !important;
                border-radius: 50% !important;
                padding: 0 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                background-color: transparent !important;
                border: 1px solid #dee2e6 !important;
                color: #6c757d !important;
                transition: all 0.2s ease !important;
            }
            
            .btn-circle i {
                font-size: 14px;
            }
            
            /* 悬停时显示颜色 */
            .btn-hover-primary:hover {
                background-color: #007bff !important;
                border-color: #007bff !important;
                color: white !important;
            }
            
            .btn-hover-danger:hover {
                background-color: #dc3545 !important;
                border-color: #dc3545 !important;
                color: white !important;
            }
            
            /* 🔥 移动端发票图标样式 */
            .mobile-invoice-display .individual-invoice-icon {
                position: relative;
                display: inline-flex;
                flex-shrink: 0;
                align-items: center;
                justify-content: center;
                margin: 0 4px;
                min-width: 28px;
                width: 28px;
                height: 28px;
            }
            
            .mobile-invoice-display .invoice-preview-icon {
                font-size: 20px;
                cursor: pointer;
                transition: transform 0.2s ease;
            }
            
            .mobile-invoice-display .invoice-preview-icon:hover {
                transform: scale(1.1);
            }
            
            .mobile-invoice-display .invoice-number-badge {
                position: absolute;
                bottom: -2px;
                right: -2px;
                background-color: #ffffff;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 50%;
                width: 14px;
                height: 14px;
                font-size: 8px;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: center;
                line-height: 1;
            }
            
            .mobile-edit-header {
                border-bottom: 1px solid #dee2e6;
                padding-bottom: 0.5rem;
                margin-bottom: 1rem;
            }
            
            .mobile-edit-header h6 {
                color: #007bff;
                font-weight: 600;
            }
            
            .mobile-edit-fields .form-label {
                font-weight: 500;
                color: #495057;
                margin-bottom: 0.25rem;
            }
            
            .mobile-edit-fields .form-control,
            .mobile-edit-fields .form-select {
                border-radius: 6px;
                border: 1px solid #ced4da;
            }
            
            .mobile-edit-fields .form-control:focus,
            .mobile-edit-fields .form-select:focus {
                border-color: #007bff;
                box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
            }
            
            .mobile-edit-actions {
                display: flex;
                gap: 0.5rem;
                justify-content: flex-end;
                margin-top: 1rem;
                padding-top: 1rem;
                border-top: 1px solid #dee2e6;
            }
            
            .mobile-edit-actions .btn {
                flex: 1;
                max-width: 120px;
            }
        `;
        
        document.head.appendChild(style);
        console.log('✅ 移动端编辑样式已添加');
    }
    
    
    /**
     * 🔥 绑定移动端输入事件（与PC端逻辑一致）
     */
    bindMobileInputEvents(card, index) {
        // 绑定输入字段变化事件
        card.querySelectorAll('.mobile-input-field').forEach(input => {
            input.addEventListener('change', (e) => {
                const field = e.target.dataset.field;
                const value = e.target.value;
                
                console.log(`🔥 移动端字段变化: ${field} = ${value}`);
                
                // 更新行数据
                if (this.rows[index]) {
                    this.rows[index][field] = value;
                    
                    // 🔥 支持新的字段名：invoice_amount
                    if (field === 'invoice_amount') {
                        // 同步到amount字段以保持兼容性
                        this.rows[index]['amount'] = value;
                    }
                    
                    // 🔥 与PC端相同的联动逻辑：发票金额或汇率变化时重新计算
                    if (field === 'invoice_amount' || field === 'amount' || field === 'exchange_rate') {
                        this.calculateCurrentAmountMobile(index);
                    }
                    
                    // 🔥 货币字段由专门的事件监听器处理，这里跳过避免重复处理
                    if (field === 'currency') {
                        console.log('🔥 货币字段由专门的事件监听器处理，跳过通用处理');
                        return;
                    }
                }
                
                // 更新隐藏表单字段
                this.updateHiddenField();
                
                // 触发总金额计算
                this.calculateTotal();
            });
            
            // 🔥 为汇率输入框添加实时格式化
            if (input.classList.contains('exchange-rate-input')) {
                input.addEventListener('blur', (e) => {
                    const value = parseFloat(e.target.value);
                    if (!isNaN(value)) {
                        e.target.value = value.toFixed(4);
                        this.rows[index].exchange_rate = value.toFixed(4);
                        this.calculateCurrentAmountMobile(index);
                    }
                });
            }
        });
    }
    
    /**
     * 🔥 计算当前金额（报销金额）- 移动端版本
     */
    calculateCurrentAmountMobile(index) {
        const rowData = this.rows[index];
        if (!rowData) return;
        
        // 🔥 支持新字段名：优先使用invoice_amount，fallback到amount
        const invoiceAmount = parseFloat(rowData.invoice_amount || rowData.amount) || 0;
        const exchangeRate = parseFloat(rowData.exchange_rate) || 1;
        const currentAmount = invoiceAmount * exchangeRate;
        
        // 更新数据
        rowData.current_amount = currentAmount.toFixed(2);
        
        // 更新移动端显示
        const card = document.querySelector(`[data-row-index="${index}"].expense-detail-input-card`);
        if (card) {
            const currentAmountInput = card.querySelector('.current-amount-input');
            if (currentAmountInput) {
                currentAmountInput.value = currentAmount.toFixed(2);
            }
        }
        
        console.log(`🔥 移动端计算报销金额: ${invoiceAmount} × ${exchangeRate} = ${currentAmount.toFixed(2)}`);
    }
    
    /**
     * 🔥 计算当前金额（报销金额）- 兼容旧版本
     */
    calculateCurrentAmount(index) {
        return this.calculateCurrentAmountMobile(index);
    }
    
    /**
     * 🔥 更新币种符号 - 移动端版本
     */
    updateCurrencySymbol(index) {
        const rowData = this.rows[index];
        if (!rowData) return;
        
        // 移动端不需要更新币种符号显示，因为没有顶部金额显示区域
        // 但保持函数接口一致性
        console.log(`🔥 移动端更新币种: ${rowData.currency}`);
    }
    
    /**
     * 🔥 更新移动端金额显示
     */
    updateMobileAmountDisplay(card, index) {
        const rowData = this.rows[index];
        if (!rowData) return;
        
        const currencySymbols = { 'CNY': '¥', 'USD': '$', 'SGD': 'S$', 'EUR': '€' };
        const symbol = currencySymbols[rowData.currency] || '¥';
        const amount = parseFloat(rowData.amount || 0).toFixed(2);
        
        const symbolEl = card.querySelector('.currency-symbol');
        const amountEl = card.querySelector('.amount-value');
        
        if (symbolEl) symbolEl.textContent = symbol;
        if (amountEl) amountEl.textContent = amount;
    }
    
    /**
     * 删除行
     */
    deleteRow(rowIndex) {
        if (this.rows.length <= 1) {
            // 使用标准通知提示
            if (window.showTopNotification) {
                window.showTopNotification(window.i18nTexts?.keepAtLeastOneDetail || '至少需要保留一条报销明细', 'warning');
            } else {
                alert(window.i18nTexts?.keepAtLeastOneDetail || '至少需要保留一条报销明细');
            }
            return;
        }
        
        // 获取明细信息用于确认提示
        const detail = this.rows[rowIndex];
        const detailInfo = detail ? `${detail.description || '明细项目'}` : '此明细项目';
        
        // 使用标准确认对话框
        if (window.showDeleteConfirm) {
            window.showDeleteConfirm({
                title: window.i18nTexts?.confirmDeleteDetailTitle || '确认删除报销明细',
                message: `${window.i18nTexts?.confirmDeleteDetailMessage || '确定要删除这条报销明细吗？'}\n\n${window.i18nTexts?.detailInfo || '明细信息：'}${detailInfo}\n\n${window.i18nTexts?.operationCannotBeUndone || '此操作不可恢复。'}`,
                dialogId: 'expenseDetailDeleteDialog',
                onConfirm: () => {
                    // 执行删除操作
                    this.rows.splice(rowIndex, 1);
                    
                    // 重新渲染表格
                    this.renderTable();
                    
                    this.updateSummary();
                    this.updateHiddenField();
                    
                    // 显示删除成功提示
                    if (window.showTopNotification) {
                        window.showTopNotification(window.i18nTexts?.detailDeletedSuccessfully || '报销明细删除成功', 'success');
                    }
                }
            });
        } else {
            // 降级到原生确认对话框（向后兼容）
            if (confirm(window.i18nTexts?.confirmDeleteDetailMessage || '确定要删除这条报销明细吗？')) {
                this.rows.splice(rowIndex, 1);
                this.renderTable();
                this.updateSummary();
                this.updateHiddenField();
            }
        }
    }
    
    /**
     * 检测是否为移动端
     */
    isMobileView() {
        return window.innerWidth < 992; // Bootstrap lg断点
    }

    /**
     * 重新渲染表格
     */
    renderTable() {
        if (this.isMobileView()) {
            this.renderMobileCards();
        } else {
            this.renderDesktopTable();
        }
    }

    /**
     * 渲染桌面端表格
     */
    renderDesktopTable() {
        const tbody = this.tableElement.querySelector('tbody');
        tbody.innerHTML = '';
        
        this.rows.forEach((rowData, index) => {
            const rowId = `expense-row-${index}`;
            const row = this.createRowElement(rowData, index, rowId);
            tbody.appendChild(row);
            
            // 更新科目样式
            const categorySelect = row.querySelector('.expense-category-select');
            if (categorySelect && categorySelect.value) {
                this.updateCategoryStyle(categorySelect);
            }
        });
    }

    /**
     * 渲染移动端卡片
     */
    renderMobileCards() {
        // 使用配置中的table_id，如果没有则从表格元素获取ID
        const tableId = this.config.table_id || this.tableElement.id || this.config.tableSelector.replace('#', '');
        let mobileContainer = document.querySelector(`#${tableId}_mobile`);
        
        // 尝试其他可能的移动端容器选择器
        if (!mobileContainer) {
            mobileContainer = document.querySelector('.expense-detail-cards');
        }
        if (!mobileContainer) {
            mobileContainer = document.querySelector('.expense-detail-mobile-cards');
        }
        
        if (!mobileContainer) {
            console.warn('移动端容器未找到:', `#${tableId}_mobile`);
            console.warn('配置中的table_id:', this.config.table_id);
            console.warn('表格元素ID:', this.tableElement.id);
            console.warn('当前窗口宽度:', window.innerWidth);
            console.warn('当前isMobileView():', this.isMobileView());
            console.warn('尝试查找其他移动端容器...');
            console.warn('可用的容器:', document.querySelectorAll('.expense-detail-cards, [id*="mobile"], [class*="mobile"]'));
            return;
        }
        
        console.log('✅ 找到移动端容器:', mobileContainer);
        console.log('容器可见性:', window.getComputedStyle(mobileContainer).display);

        mobileContainer.innerHTML = '';

        if (this.rows.length === 0) {
            mobileContainer.innerHTML = `
                <div class="empty-state text-center py-4">
                    <i class="fas fa-receipt text-muted mb-2" style="font-size: 2rem;"></i>
                    <p class="text-muted mb-0">${window.i18nTexts?.noExpenseDetails || '暂无报销明细'}</p>
                    <small class="text-muted">${window.i18nTexts?.clickBelowToAddExpense || '点击下方按钮添加报销项目'}</small>
                </div>
            `;
            return;
        }

        this.rows.forEach((rowData, index) => {
            const card = this.createMobileCard(rowData, index);
            mobileContainer.appendChild(card);
            
            // 🔥 卡片创建后立即更新发票图标显示
            setTimeout(() => {
                if (rowData.invoice_images && rowData.invoice_images.length > 0) {
                    console.log(`🔥 移动端渲染后更新发票显示 行${index}:`, rowData.invoice_images);
                    this.updateInvoiceDisplay(index, rowData.invoice_images);
                }
            }, 50); // 稍长的延时确保DOM已完全渲染
        });
    }

    /**
     * 创建移动端卡片元素
     */
    createMobileCard(rowData, index) {
        const card = document.createElement('div');
        card.className = 'expense-detail-card';
        card.dataset.index = index;
        card.dataset.rowIndex = index; // 添加row-index用于选择器
        
        // 🔥 检查是否为创建或编辑页面，如果是则显示输入表单
        const isCreatePage = window.location.pathname.includes('/create') || 
                            document.querySelector('form[action*="create"]');
        const isEditPage = window.location.pathname.includes('/edit') || 
                          document.querySelector('form[action*="edit"]');
        const isInputPage = isCreatePage || isEditPage;
        
        if (isInputPage) {
            return this.createMobileInputCard(rowData, index);
        }

        // 格式化金额显示
        const formatAmount = (amount, currency = 'CNY') => {
            const symbols = { 'CNY': '¥', 'USD': '$', 'EUR': '€', 'GBP': '£' };
            const symbol = symbols[currency] || currency;
            return `${symbol}${parseFloat(amount || 0).toFixed(2)}`;
        };

        // 获取科目映射
        const categoryMap = {
            'entertainment': '招待费',
            'local_transport': '市内交通',
            'travel_accommodation': '差旅住宿',
            'office_supplies': '办公用品',
            'communication': '通讯费',
            'fuel': '油费',
            'parking': '停车费',
            'meals': '餐费',
            'other': '其他'
        };

        const categoryLabel = categoryMap[rowData.expense_category] || rowData.expense_category;
        const currentAmount = formatAmount(rowData.current_amount, this.config.base_currency);
        const invoiceAmount = formatAmount(rowData.invoice_amount, rowData.currency);

        card.innerHTML = `
            <div class="expense-detail-card-header">
                <h6 class="expense-detail-card-title">${rowData.description || '报销项目'}</h6>
                <div class="expense-detail-card-amount">${currentAmount}</div>
            </div>
            
            <div class="expense-detail-card-body">
                <div class="expense-detail-card-field">
                    <div class="expense-detail-card-field-label">科目</div>
                    <div class="expense-detail-card-field-value">${categoryLabel}</div>
                </div>
                
                <div class="expense-detail-card-field">
                    <div class="expense-detail-card-field-label">日期</div>
                    <div class="expense-detail-card-field-value">${rowData.expense_date || ''}</div>
                </div>
                
                <div class="expense-detail-card-field">
                    <div class="expense-detail-card-field-label">发票金额</div>
                    <div class="expense-detail-card-field-value">${invoiceAmount}</div>
                </div>
                
                <div class="expense-detail-card-field">
                    <div class="expense-detail-card-field-label">汇率</div>
                    <div class="expense-detail-card-field-value">${parseFloat(rowData.exchange_rate || 1).toFixed(4)}</div>
                </div>
                
                <div class="expense-detail-card-field">
                    <div class="expense-detail-card-field-label">单据数量</div>
                    <div class="expense-detail-card-field-value">${rowData.document_count || 1} 张</div>
                </div>
            </div>
            
            ${this.createMobileCardInvoiceImages(rowData.invoice_images)}
            
            <div class="expense-detail-card-actions">
                <button type="button" class="btn btn-sm btn-outline-primary" onclick="window.expenseDetailManager.editRow(${index})">
                    <i class="fas fa-edit me-1"></i>编辑
                </button>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="window.expenseDetailManager.deleteRow(${index})">
                    <i class="fas fa-trash me-1"></i>删除
                </button>
            </div>
        `;

        return card;
    }
    
    /**
     * 🔥 创建移动端输入表单卡片（用于创建页面）
     */
    createMobileInputCard(rowData, index) {
        const card = document.createElement('div');
        card.className = 'expense-detail-card expense-detail-input-card';
        card.dataset.index = index;
        card.dataset.rowIndex = index;
        
        // 🔥 使用与PC端相同的科目配置
        const categoryOptions = this.config.categories ? 
            '<option value="">请选择科目</option>' + 
            this.config.categories.map(category => 
                `<option value="${category.value}" ${rowData.expense_category === category.value ? 'selected' : ''}>${category.label}</option>`
            ).join('') :
            // 备用选项（如果配置不存在）
            [
                { value: '', label: '请选择科目' },
                { value: 'entertainment', label: '招待费' },
                { value: 'local_transport', label: '市内交通' },
                { value: 'travel_accommodation', label: '差旅住宿' },
                { value: 'office_supplies', label: '办公用品' },
                { value: 'communication', label: '通讯费' },
                { value: 'fuel', label: '油费' },
                { value: 'parking', label: '停车费' },
                { value: 'meals', label: '餐费' },
                { value: 'other', label: '其他' }
            ].map(option => 
                `<option value="${option.value}" ${rowData.expense_category === option.value ? 'selected' : ''}>${option.label}</option>`
            ).join('');
        
        // 🔥 使用与PC端相同的货币配置
        const currencyColumn = this.config.columns.find(col => col.key === 'currency');
        const currencyOptions = currencyColumn && currencyColumn.options ? 
            currencyColumn.options.map(option => 
                `<option value="${option.value}" ${rowData.currency === option.value ? 'selected' : ''}>${option.label} (${option.value})</option>`
            ).join('') :
            // 备用选项（如果配置不存在）
            [
                { value: 'CNY', label: '人民币' },
                { value: 'USD', label: '美元' },
                { value: 'SGD', label: '新元' },
                { value: 'MYR', label: '林吉特' },
                { value: 'IDR', label: '印尼盾' },
                { value: 'THB', label: '泰铢' }
            ].map(option => 
                `<option value="${option.value}" ${rowData.currency === option.value ? 'selected' : ''}>${option.label} (${option.value})</option>`
            ).join('');
        
        // 🔥 按用户要求的顺序排列字段: 科目 -> 日期 -> 币种 -> 发票金额 -> 汇率 -> 报销金额 -> 单据数量 -> 说明描述 -> 发票图片
        card.innerHTML = `
            <div class="mobile-input-card-content">
                <div class="mobile-input-fields">
                    <!-- 科目 -->
                    <div class="mobile-input-row">
                        <label class="mobile-input-label">科目</label>
                        <select name="details[${index}][expense_category]" 
                                class="form-select mobile-input-field" 
                                data-field="expense_category" 
                                data-row-index="${index}"
                                required>
                            ${categoryOptions}
                        </select>
                    </div>
                    
                    <!-- 日期 -->
                    <div class="mobile-input-row">
                        <label class="mobile-input-label">日期</label>
                        <input type="date" 
                               name="details[${index}][expense_date]" 
                               class="form-control mobile-input-field" 
                               data-field="expense_date"
                               data-row-index="${index}"
                               value="${rowData.expense_date || ''}"
                               required>
                    </div>
                    
                    <!-- 币种 (发票金额前面) -->
                    <div class="mobile-input-row">
                        <label class="mobile-input-label">币种</label>
                        <select name="details[${index}][currency]" 
                                class="form-select mobile-input-field currency-select" 
                                data-field="currency"
                                data-row-index="${index}">
                            ${currencyOptions}
                        </select>
                    </div>
                    
                    <!-- 发票金额 -->
                    <div class="mobile-input-row">
                        <label class="mobile-input-label">发票金额</label>
                        <input type="number" 
                               name="details[${index}][invoice_amount]" 
                               class="form-control mobile-input-field invoice-amount-input" 
                               data-field="invoice_amount"
                               data-row-index="${index}"
                               step="0.01" 
                               min="0"
                               value="${rowData.invoice_amount || rowData.amount || ''}"
                               placeholder="0.00">
                    </div>
                    
                    <!-- 汇率 (保持4位小数精度) -->
                    <div class="mobile-input-row">
                        <label class="mobile-input-label">汇率</label>
                        <input type="number" 
                               name="details[${index}][exchange_rate]" 
                               class="form-control mobile-input-field exchange-rate-input" 
                               data-field="exchange_rate"
                               data-row-index="${index}"
                               step="0.0001" 
                               min="0"
                               value="${parseFloat(rowData.exchange_rate || 1.0000).toFixed(4)}"
                               placeholder="1.0000">
                    </div>
                    
                    <!-- 报销金额 (汇率下面) -->
                    <div class="mobile-input-row">
                        <label class="mobile-input-label">报销金额</label>
                        <input type="number" 
                               name="details[${index}][current_amount]" 
                               class="form-control mobile-input-field current-amount-input" 
                               data-field="current_amount"
                               data-row-index="${index}"
                               step="0.01" 
                               min="0"
                               value="${rowData.current_amount || ''}"
                               readonly
                               title="根据发票金额和汇率自动计算">
                    </div>
                    
                    <!-- 单据数量 -->
                    <div class="mobile-input-row">
                        <label class="mobile-input-label">单据数量</label>
                        <input type="number" 
                               name="details[${index}][document_count]" 
                               class="form-control mobile-input-field document-count-input" 
                               data-field="document_count"
                               data-row-index="${index}"
                               min="0" 
                               value="${rowData.document_count || '0'}"
                               placeholder="0">
                    </div>
                    
                    <!-- 说明描述 -->
                    <div class="mobile-input-row full-width">
                        <label class="mobile-input-label">说明描述</label>
                        <textarea name="details[${index}][description]" 
                                  class="form-control mobile-input-field" 
                                  data-field="description"
                                  data-row-index="${index}"
                                  rows="2" 
                                  placeholder="请输入费用说明">${rowData.description || ''}</textarea>
                    </div>
                    
                    <!-- 发票图片区域和操作按钮 -->
                    <div class="mobile-input-row full-width">
                        <div class="mobile-bottom-section">
                            <div class="mobile-invoice-container">
                                <div class="mobile-invoice-display" data-row-index="${index}">
                                    <!-- 发票图标在这里显示 -->
                                </div>
                            </div>
                            <!-- 操作按钮 - 圆形按钮在右下角 -->
                            <div class="mobile-input-actions">
                                <button type="button" 
                                        class="btn btn-circle btn-hover-primary"
                                        onclick="window.expenseDetailManager.triggerInvoiceUpload(${index})"
                                        title="上传发票">
                                    <i class="fas fa-plus"></i>
                                </button>
                                <button type="button" 
                                        class="btn btn-circle btn-hover-danger"
                                        onclick="window.expenseDetailManager.deleteRow(${index})"
                                        title="删除此项">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 绑定输入事件
        this.bindMobileInputEvents(card, index);
        
        // 🔥 专门为移动端货币选择器添加事件监听器（与PC端保持一致）
        const currencySelect = card.querySelector('.currency-select');
        if (currencySelect) {
            currencySelect.addEventListener('change', (e) => {
                console.log(`🔥 移动端货币变更触发: ${e.target.value}`);
                this.handleCurrencyChange(index, e.target.value);
            });
        }
        
        // 🔥 创建卡片后立即更新发票图标显示
        setTimeout(() => {
            if (rowData.invoice_images && rowData.invoice_images.length > 0) {
                console.log(`🔥 移动端卡片创建后更新发票显示:`, rowData.invoice_images);
                this.updateInvoiceDisplay(index, rowData.invoice_images);
            }
        }, 10);
        
        return card;
    }

    /**
     * 创建移动端卡片的发票图片部分
     */
    createMobileCardInvoiceImages(invoiceImages) {
        if (!invoiceImages || invoiceImages.length === 0) {
            return '';
        }

        const imagesHtml = invoiceImages.map(image => `
            <img src="${image.url || image.path}" 
                 alt="发票图片" 
                 class="expense-detail-card-invoice-thumb"
                 onclick="window.showImagePreview('${image.url || image.path}')">
        `).join('');

        return `
            <div class="expense-detail-card-field full-width">
                <div class="expense-detail-card-field-label">发票图片</div>
                <div class="expense-detail-card-invoice-images">
                    ${imagesHtml}
                </div>
            </div>
        `;
    }
    
    /**
     * 更新科目选择样式
     */
    updateCategoryStyle(selectElement) {
        const selectedOption = selectElement.selectedOptions[0];
        if (selectedOption && selectedOption.dataset.color) {
            selectElement.style.borderLeftColor = selectedOption.dataset.color;
        }
    }
    
    /**
     * 更新统计信息
     */
    updateSummary() {
        // 使用新的计算总金额方法
        const totalAmount = this.calculateTotal();
        
        // 更新货币符号
        this.updateCurrencySymbol();
        
        // 发送数据变化事件
        const changeEvent = new CustomEvent('expenseDetailChanged', {
            detail: {
                totalAmount: totalAmount,
                detailCount: this.getAllData().length,
                rowCount: this.rows.length
            }
        });
        document.dispatchEvent(changeEvent);
    }
    
    /**
     * 更新隐藏字段数据
     */
    updateHiddenField() {
        const hiddenField = document.getElementById('expenseDetailsData');
        if (hiddenField) {
            // 准备数据，过滤掉空行和无效数据
            const validRows = this.rows.filter(row => {
                return row.expense_category && 
                       row.expense_date && 
                       row.description && 
                       row.amount && 
                       parseFloat(row.amount) > 0;
            });
            
            hiddenField.value = JSON.stringify(validRows);
        }
    }
    
    /**
     * 验证所有数据
     */
    validateAll() {
        const errors = [];
        
        this.rows.forEach((row, index) => {
            this.config.columns.forEach(column => {
                if (column.required && this.config.validators[column.key]) {
                    const value = row[column.key];
                    const isValid = this.config.validators[column.key](value);
                    
                    if (!isValid) {
                        errors.push({
                            row: index + 1,
                            field: column.label,
                            message: `第${index + 1}行的"${column.label}"字段不符合要求`
                        });
                    }
                }
            });
        });
        
        return errors;
    }
    
    /**
     * 获取所有数据
     */
    getAllData() {
        return this.rows.filter(row => {
            // 过滤掉空行（至少要有科目和金额）
            return row.expense_category && parseFloat(row.amount) > 0;
        });
    }
    
    /**
     * 设置所有数据
     */
    setAllData(data) {
        this.rows = [...data];
        this.renderTable();
        this.updateSummary();
    }
    
    /**
     * 清空所有数据
     */
    clearAll() {
        this.rows = [];
        this.addRow(); // 添加一个空行
        this.updateSummary();
        // 注意：addRow() 方法已经会调用移动端渲染，所以这里不需要额外调用
    }
    
    /**
     * 获取表单数据（用于提交）
     */
    getFormData() {
        const validData = this.getAllData();
        const formData = new FormData();
        
        validData.forEach((row, index) => {
            Object.keys(this.config.fieldMapping).forEach(key => {
                const mappedKey = this.config.fieldMapping[key];
                formData.append(`details[${index}][${mappedKey}]`, row[key] || '');
            });
        });
        
        return formData;
    }
    
    /**
     * 渲染发票上传单元格
     */
    renderInvoiceUploadCell(rowIndex, invoiceImages = []) {
        const hasImages = invoiceImages && invoiceImages.length > 0;
        const imageCount = hasImages ? invoiceImages.length : 0;
        
        return `
            <div class="invoice-upload-cell" data-row-index="${rowIndex}">
                <input type="file" 
                       class="invoice-upload-input" 
                       id="invoiceInput_${rowIndex}" 
                       accept="image/*,application/pdf,.heic,.heif" 
                       multiple>
                <div class="invoice-upload-btn ${hasImages ? 'has-images' : ''}" 
                     onclick="document.getElementById('invoiceInput_${rowIndex}').click()">
                    <i class="fas fa-${hasImages ? 'file-invoice' : 'plus'}"></i>
                    <span class="ms-1">${hasImages ? '发票' : '上传'}</span>
                    ${hasImages ? `<span class="invoice-count-badge">${imageCount}</span>` : ''}
                </div>
                ${hasImages ? `<i class="fas fa-eye invoice-preview-icon" 
                                 data-row-index="${rowIndex}" 
                                 data-images='${JSON.stringify(invoiceImages)}'
                                 title="预览发票图片"></i>` : ''}
            </div>
        `;
    }
    
    /**
     * 处理发票上传
     */
    async handleInvoiceUpload(rowIndex, files) {
        if (!files || files.length === 0) return;
        
        // 在新的UI布局中，找到上传按钮
        const uploadBtn = document.querySelector(`[data-row-index="${rowIndex}"] [data-action="upload-invoice"]`);
        
        if (!uploadBtn) {
            console.error('找不到发票上传按钮:', rowIndex);
            return;
        }
        
        // 显示上传进度
        this.showUploadProgress(uploadBtn);
        
        try {
            for (let file of files) {
                // 验证文件
                if (!this.validateInvoiceFile(file)) {
                    continue;
                }
                
                const row = this.rows[rowIndex];
                
                // 检查当前页面类型（通过URL判断）
                const isCreatePage = window.location.pathname.includes('/create');
                const isEditPage = window.location.pathname.includes('/edit');
                
                if ((isCreatePage && !row.id) || (isEditPage && row.id)) {
                    // 创建/编辑页面：暂时存储文件信息，等保存时再上传
                    if (!row.invoice_images) {
                        row.invoice_images = [];
                    }
                    
                    // 获取规范化文件名（用于预览显示）
                    let displayFilename = file.name; // 默认使用原始文件名
                    console.log('🔍 开始处理文件预览:', {
                        originalFilename: file.name,
                        mimeType: file.type,
                        fileSize: file.size,
                        lastModified: new Date(file.lastModified).toLocaleString(),
                        rowIndex: rowIndex,
                        rowId: row.id,
                        hasRowId: !!row.id
                    });
                    
                    // 详细的文件信息调试
                    console.log('📁 用户选择的文件详细信息:');
                    console.log('  文件名:', file.name);
                    console.log('  MIME类型:', file.type || '无');
                    console.log('  文件大小:', file.size, '字节');
                    console.log('  最后修改:', new Date(file.lastModified).toLocaleString());
                    
                    // 从文件名判断用户期望的格式
                    const expectedExtension = file.name.split('.').pop()?.toLowerCase();
                    console.log('  从文件名推断的扩展名:', expectedExtension);
                    
                    // 检测浏览器自动转换问题（特别是iOS Safari）
                    const isTempFile = file.name.startsWith('tempImage') || file.name.startsWith('image-');
                    if (isTempFile) {
                        console.warn('🚨 检测到临时文件名格式：', file.name);
                        console.warn('🍎 这通常表示iOS/Safari浏览器自动转换了用户的原始文件');
                        console.warn('💡 用户实际选择的文件可能是不同的格式');
                    }
                    
                    if (expectedExtension && expectedExtension !== 'heic' && file.type === 'image/heic') {
                        console.warn('⚠️  警告：用户选择了', expectedExtension.toUpperCase(), '文件，但浏览器检测到MIME类型为 image/heic');
                        console.warn('⚠️  这可能是iOS设备自动转换或文件格式识别问题');
                    }
                    
                    try {
                        if (row.id) {
                            console.log('📞 调用预览API:', `/expense/api/preview_invoice_filename/${row.id}`);
                            
                            // 如果有detail_id，调用预览API获取规范化文件名
                            const previewResponse = await fetch(`/expense/api/preview_invoice_filename/${row.id}`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    filename: file.name,
                                    mimeType: file.type || ''
                                })
                            });
                            
                            console.log('🌐 预览API响应状态:', previewResponse.status);
                            
                            if (previewResponse.ok) {
                                const previewResult = await previewResponse.json();
                                console.log('📋 预览API响应内容:', previewResult);
                                
                                if (previewResult.success) {
                                    displayFilename = previewResult.preview_filename;
                                    console.log('✅ 获取到规范化文件名:', displayFilename);
                                } else {
                                    console.warn('⚠️  获取规范化文件名失败:', previewResult.message);
                                }
                            } else {
                                console.warn('⚠️  预览API请求失败:', previewResponse.status);
                                const errorText = await previewResponse.text();
                                console.warn('⚠️  错误详情:', errorText);
                            }
                        } else {
                            console.log('ℹ️  没有row.id，为创建页面生成预览文件名');
                            console.log('🚀 文件类型检测代码版本: 2.0 - 已更新');
                            // 在创建页面，没有detail_id时，生成基于当前信息的预览文件名
                            // 格式：系统标识_当前日期_明细序号_文件序号.扩展名
                            const now = new Date();
                            const dateStr = now.getFullYear().toString().slice(-2) + 
                                          String(now.getMonth() + 1).padStart(2, '0') + 
                                          String(now.getDate()).padStart(2, '0');
                            
                            // 根据文件的MIME类型确定正确的扩展名
                            let extension = 'jpg'; // 默认扩展名
                            
                            console.log('🔍 文件类型检测开始:', {
                                fileName: file.name,
                                mimeType: file.type,
                                fileSize: file.size
                            });
                            console.log('📊 检测到的MIME类型:', file.type || '无MIME类型');
                            
                            if (file.type) {
                                const mimeToExtension = {
                                    'image/png': 'png',
                                    'image/jpeg': 'jpg',
                                    'image/jpg': 'jpg',
                                    'image/gif': 'gif',
                                    'image/bmp': 'bmp',
                                    'image/webp': 'webp',
                                    'image/heic': 'heic',
                                    'image/heif': 'heif',
                                    'application/pdf': 'pdf'
                                };
                                
                                extension = mimeToExtension[file.type.toLowerCase()] || 'jpg';
                                console.log('✅ 基于MIME类型检测到扩展名:', extension);
                                
                                // 额外的调试信息和智能修正
                                if (expectedExtension && extension !== expectedExtension) {
                                    console.warn('🔄 扩展名不匹配！');
                                    console.warn('  用户文件名显示:', expectedExtension);
                                    console.warn('  MIME类型检测:', extension);
                                    
                                    // 智能修正：对于常见的图片格式，优先使用用户期望的格式
                                    const commonImageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];
                                    if (commonImageExtensions.includes(expectedExtension)) {
                                        console.log('🔧 应用智能修正：使用用户文件名的扩展名', expectedExtension);
                                        extension = expectedExtension === 'jpeg' ? 'jpg' : expectedExtension;
                                        console.log('✅ 修正后的扩展名:', extension);
                                    } else {
                                        console.warn('⚠️  保持MIME类型检测结果，因为用户文件扩展名不在常见图片格式列表中');
                                    }
                                }
                            } else {
                                // 如果没有MIME类型，尝试通过文件魔数检测
                                console.warn('⚠️  文件没有MIME类型，尝试通过文件内容检测');
                                
                                try {
                                    const buffer = await file.slice(0, 12).arrayBuffer();
                                    const bytes = new Uint8Array(buffer);
                                    
                                    // PNG: 89 50 4E 47 0D 0A 1A 0A
                                    if (bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4E && bytes[3] === 0x47) {
                                        extension = 'png';
                                        console.log('✅ 通过文件头检测到PNG格式');
                                    }
                                    // JPEG: FF D8 FF
                                    else if (bytes[0] === 0xFF && bytes[1] === 0xD8 && bytes[2] === 0xFF) {
                                        extension = 'jpg';
                                        console.log('✅ 通过文件头检测到JPEG格式');
                                    }
                                    // GIF: GIF87a or GIF89a
                                    else if (bytes[0] === 0x47 && bytes[1] === 0x49 && bytes[2] === 0x46) {
                                        extension = 'gif';
                                        console.log('✅ 通过文件头检测到GIF格式');
                                    }
                                    // BMP: BM
                                    else if (bytes[0] === 0x42 && bytes[1] === 0x4D) {
                                        extension = 'bmp';
                                        console.log('✅ 通过文件头检测到BMP格式');
                                    }
                                    // PDF: %PDF
                                    else if (bytes[0] === 0x25 && bytes[1] === 0x50 && bytes[2] === 0x44 && bytes[3] === 0x46) {
                                        extension = 'pdf';
                                        console.log('✅ 通过文件头检测到PDF格式');
                                    }
                                    else {
                                        console.warn('⚠️  无法识别文件类型，使用默认扩展名 jpg');
                                        extension = 'jpg';
                                    }
                                } catch (error) {
                                    console.warn('⚠️  文件内容检测失败，使用默认扩展名:', error);
                                    extension = 'jpg';
                                }
                            }
                            
                            console.log('📝 最终确定的扩展名:', extension);
                            
                            // 🔧 智能格式处理（解决iOS HEIC兼容性问题）
                            const isTempFile = file.name.startsWith('tempImage') || file.name.startsWith('image-');
                            
                            if (extension === 'heic' || extension === 'heif') {
                                console.log('🍎 检测到Apple HEIC/HEIF格式');
                                
                                if (isTempFile) {
                                    console.log('🔍 这是浏览器生成的临时文件');
                                    console.log('💡 用户实际选择的可能是JPG文件，被浏览器自动转换为HEIC');
                                    console.log('🎯 强制使用JPG格式以匹配用户期望');
                                } else {
                                    console.log('💡 为了更好的兼容性和通用性，自动转换为JPG格式');
                                }
                                
                                // 自动转换为JPG格式，提供更好的兼容性
                                const originalExtension = extension;
                                extension = 'jpg';
                                
                                console.log(`🔄 格式转换: ${originalExtension.toUpperCase()} → JPG`);
                                console.log('✅ 转换完成，现在使用JPG扩展名');
                                console.log('📋 说明：JPG格式具有更好的通用兼容性');
                            }
                            
                            // 明细序号 (rowIndex + 1)
                            const detailSequence = String(rowIndex + 1).padStart(2, '0');
                            
                            // 文件序号（当前明细已有的文件数 + 1）
                            const currentFileCount = (row.invoice_images ? row.invoice_images.length : 0) + 1;
                            const fileSequence = String(currentFileCount).padStart(2, '0');
                            
                            // 系统标识（本地为LOCAL-PMA）
                            const systemId = 'LOCAL-PMA';
                            
                            // 报销单编号（如果有expense对象的话，这里暂时用占位符）
                            const expenseNumber = `BX${dateStr}`;
                            
                            displayFilename = `${systemId}_${expenseNumber}_${detailSequence}_${fileSequence}.${extension}`;
                            console.log('📝 生成创建页面预览文件名:', displayFilename);
                        }
                    } catch (error) {
                        console.warn('⚠️  调用预览API时出错:', error);
                        // 继续使用原始文件名
                    }
                    
                    console.log('📝 最终使用的文件名:', displayFilename);
                    
                    row.invoice_images.push({
                        file: file,
                        pending: true,
                        filename: displayFilename, // 使用规范化文件名
                        original_filename: file.name, // 保存原始文件名
                        size: file.size
                    });
                    
                    this.hideUploadProgress(uploadBtn);
                    this.updateInvoiceDisplay(rowIndex, row.invoice_images);
                    this.autoUpdateDocumentCount(rowIndex, row.invoice_images);
                    this.updateHiddenField();
                    continue;
                }
                
                // 编辑页面（所有明细）或创建页面的已有明细：统一使用临时上传
                const uploadResult = await this.uploadInvoiceToServer(row.id, file);
                
                if (uploadResult.success) {
                    // 更新行数据
                    if (!row.invoice_images) {
                        row.invoice_images = [];
                    }
                    row.invoice_images.push({
                        filename: uploadResult.filename,
                        url: uploadResult.image_url,
                        size: uploadResult.size,
                        temp_id: uploadResult.temp_id,
                        is_temp: uploadResult.is_temp || true,  // 标记为临时文件
                        pending: true,  // 🔥 编辑页面的新上传文件应该保持pending状态
                        file: file  // 🔥 保持file对象用于blob URL预览
                    });
                    
                    this.updateInvoiceDisplay(rowIndex, row.invoice_images);
                    // 自动更新单据数量
                    this.autoUpdateDocumentCount(rowIndex, row.invoice_images);
                    // 更新隐藏字段
                    this.updateHiddenField();
                    this.showNotification('发票上传成功', 'success');
                } else {
                    this.showNotification(uploadResult.message || '发票上传失败', 'error');
                }
            }
        } catch (error) {
            console.error('发票上传异常:', error);
            this.showNotification('发票上传失败，请重试', 'error');
        } finally {
            this.hideUploadProgress(uploadBtn);
        }
    }
    
    /**
     * 验证发票文件
     */
    validateInvoiceFile(file) {
        // 检查文件类型
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/heic', 'image/heif', 'application/pdf'];
        if (!allowedTypes.includes(file.type)) {
            this.showNotification('支持格式：JPG、PNG、GIF、WEBP、HEIC、PDF', 'error');
            return false;
        }
        
        // 检查文件大小 (5MB)
        const maxSize = 5 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showNotification('文件大小不能超过5MB', 'error');
            return false;
        }
        
        return true;
    }
    
    /**
     * 上传发票到服务器
     */
    async uploadInvoiceToServer(detailId, file) {
        const formData = new FormData();
        formData.append('invoice_image', file);
        
        // 在编辑页面中，所有发票上传都使用临时上传API，确保数据一致性
        // 只有在最终提交表单时才真正保存到数据库
        const apiUrl = '/expense/api/upload_invoice_temp';
        
        const response = await fetch(apiUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        });
        
        const result = await response.json();
        
        // 统一返回数据格式
        if (result.success && result.data) {
            return {
                success: true,
                filename: result.data.filename,
                image_url: result.data.url,
                size: result.data.size,
                temp_id: result.data.temp_id,
                is_temp: true  // 标记为临时文件
            };
        }
        
        return result;
    }
    
    /**
     * 更新发票上传单元格（旧版本）
     */
    updateInvoiceUploadCell(rowIndex, images) {
        const cell = document.querySelector(`[data-row-index="${rowIndex}"] .invoice-upload-cell`);
        if (cell) {
            const newCell = this.renderInvoiceUploadCell(rowIndex, images);
            cell.outerHTML = newCell;
            
            // 重新绑定事件
            this.bindInvoiceEvents(rowIndex);
        }
    }
    
    /**
     * 绑定发票相关事件
     */
    bindInvoiceEvents(rowIndex) {
        const input = document.getElementById(`invoiceInput_${rowIndex}`);
        if (input) {
            // 移除可能存在的旧事件监听器
            const newInput = input.cloneNode(true);
            input.parentNode.replaceChild(newInput, input);
            
            // 绑定新的事件监听器
            newInput.addEventListener('change', (e) => {
                this.handleInvoiceUpload(rowIndex, e.target.files);
            });
        }
        
        const previewIcon = document.querySelector(`[data-row-index="${rowIndex}"] .invoice-preview-icon`);
        if (previewIcon) {
            previewIcon.addEventListener('click', (e) => {
                const images = JSON.parse(e.target.dataset.images || '[]');
                console.log('🔥 旧的预览逻辑被调用，传递的images:', images);
                
                if (images && images.length > 0) {
                    const firstImage = images[0];
                    console.log('🔥 第一个图片对象:', firstImage);
                    
                    // 🔥 根据图片状态决定URL - 和第3144行逻辑一致
                    let imageUrl;
                    let isPending = false;
                    
                    if (firstImage.pending === true && firstImage.file) {
                        // 待上传的文件：创建本地预览URL
                        imageUrl = URL.createObjectURL(firstImage.file);
                        isPending = true;
                        console.log('🔥 旧逻辑-创建本地预览URL（blob）:', imageUrl);
                    } else {
                        // 已上传的文件：使用服务器URL
                        imageUrl = firstImage.url || firstImage.image_url || firstImage.path || firstImage.file_url;
                        console.log('🔥 旧逻辑-使用服务器URL:', imageUrl);
                        console.log('🔥 旧逻辑-发票对象调试:', {
                            pending: firstImage.pending,
                            hasFile: !!firstImage.file,
                            url: firstImage.url,
                            image_url: firstImage.image_url,
                            path: firstImage.path,
                            file_url: firstImage.file_url
                        });
                    }
                    
                    const title = isPending 
                        ? `发票1: ${firstImage.filename}`
                        : `发票1: ${firstImage.filename}`;
                    
                    this.showInvoicePreview(imageUrl, title, {
                        rowIndex: rowIndex,
                        invoiceIndex: 0,
                        invoice: firstImage,
                        isPending: isPending
                    });
                } else {
                    console.warn('没有发票图片可预览');
                }
            });
        }
    }
    
    /**
     * 显示发票预览
     */
    showInvoicePreview(imageUrl, title, deleteInfo = null) {
        console.log('🔥🔥🔥 showInvoicePreview 被调用，参数:', {
            imageUrl: imageUrl,
            title: title,
            deleteInfo: deleteInfo,
            imageUrlType: typeof imageUrl,
            isBlob: imageUrl && imageUrl.startsWith('blob:')
        });
        console.trace('🔥 调用栈追踪:');
        
        if (!imageUrl) {
            console.warn('发票URL为空，无法预览');
            return;
        }
        
        console.log('预览发票:', imageUrl, title, deleteInfo);
        
        // 创建简单的模态预览
        this.createInvoiceModal(imageUrl, title, deleteInfo);
    }
    
    /**
     * 创建发票预览模态框 - 🔥 使用通用预览组件
     */
    createInvoiceModal(imageUrl, title, deleteInfo = null) {
        console.log('🔥 createInvoiceModal 调用通用预览组件:', imageUrl, title);
        
        // 🔥 优先使用通用预览组件
        if (typeof showInvoicePreviewDialog === 'function') {
            // 确定使用哪个对话框ID
            let dialogId = 'expenseInvoicePreview'; // 默认详情页
            
            if (document.getElementById('createExpenseInvoicePreview')) {
                dialogId = 'createExpenseInvoicePreview';
            } else if (document.getElementById('editExpenseInvoicePreview')) {
                dialogId = 'editExpenseInvoicePreview';
            }
            
            // 准备文件信息和删除信息
            const filename = title || 'invoice.jpg';
            const fileInfo = { description: '报销单发票' };
            
            console.log('使用通用预览组件:', imageUrl, filename, dialogId, deleteInfo);
            
            // 🔥 如果有删除信息，传递给通用预览组件
            if (deleteInfo) {
                showInvoicePreviewDialog(imageUrl, filename, fileInfo, dialogId, deleteInfo);
            } else {
                showInvoicePreviewDialog(imageUrl, filename, fileInfo, dialogId);
            }
            return;
        }
        
        // 备用方案：传统模态框（如果通用组件不可用）
        console.warn('通用预览组件不可用，使用备用模态框');
        
        // 移除现有模态框
        const existingModal = document.getElementById('invoicePreviewModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // 创建模态框HTML
        const modal = document.createElement('div');
        modal.id = 'invoicePreviewModal';
        modal.innerHTML = `
            <div class="modal fade" tabindex="-1" style="z-index: 9999;">
                <div class="modal-dialog modal-lg modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                        </div>
                        <div class="modal-body text-center">
                            <div class="loading-spinner mb-3">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">加载中...</span>
                                </div>
                                <div class="mt-2">正在加载图片...</div>
                            </div>
                            <img id="invoicePreviewImg" src="${imageUrl}" 
                                 class="img-fluid" style="max-height: 70vh; display: none;"
                                 alt="${title}">
                            <div id="imageError" class="text-danger" style="display: none;">
                                <i class="fas fa-exclamation-triangle"></i>
                                <div class="mt-2">图片加载失败</div>
                            </div>
                        </div>
                        <div class="modal-footer justify-content-between">
                            <button type="button" class="btn btn-danger btn-md rounded-pill py-2 px-4 text-sm d-inline-flex align-items-center min-width-md" id="deleteInvoiceBtn">
                                <i class="fas fa-trash me-2"></i>删除
                            </button>
                            <button type="button" class="btn btn-primary btn-md rounded-pill py-2 px-4 text-sm d-inline-flex align-items-center min-width-md" onclick="window.open('${imageUrl}', '_blank')">
                                <i class="fas fa-external-link-alt me-2"></i>新窗口打开
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 获取元素
        const modalElement = modal.querySelector('.modal');
        const img = modal.querySelector('#invoicePreviewImg');
        const spinner = modal.querySelector('.loading-spinner');
        const errorDiv = modal.querySelector('#imageError');
        
        // 图片加载事件
        img.onload = function() {
            spinner.style.display = 'none';
            img.style.display = 'block';
        };
        
        img.onerror = function() {
            spinner.style.display = 'none';
            errorDiv.style.display = 'block';
        };
        
        // 绑定删除按钮事件
        const deleteBtn = modal.querySelector('#deleteInvoiceBtn');
        if (deleteInfo && deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                this.deleteInvoice(deleteInfo);
                bsModal.hide();
            });
        } else if (deleteBtn) {
            // 如果没有删除信息，隐藏删除按钮
            deleteBtn.style.display = 'none';
        }
        
        // 显示模态框，允许点击背景关闭
        const bsModal = new bootstrap.Modal(modalElement, {
            backdrop: true,
            keyboard: true
        });
        bsModal.show();
        
        // 模态框关闭时移除DOM元素和清理URL
        modalElement.addEventListener('hidden.bs.modal', function() {
            // 如果是本地预览URL，需要清理以避免内存泄漏
            if (imageUrl && imageUrl.startsWith('blob:')) {
                URL.revokeObjectURL(imageUrl);
                console.log('清理本地预览URL:', imageUrl);
            }
            modal.remove();
        });
    }
    
    /**
     * 删除发票
     */
    deleteInvoice(deleteInfo) {
        const { rowIndex, invoiceIndex, invoice, isPending } = deleteInfo;
        
        console.log('删除发票:', deleteInfo);
        
        // 获取行数据
        const rowData = this.rows[rowIndex];
        if (!rowData || !rowData.invoice_images) {
            console.warn('找不到行数据或发票数据');
            return;
        }
        
        // 确保invoiceIndex有效
        if (invoiceIndex < 0 || invoiceIndex >= rowData.invoice_images.length) {
            console.warn('无效的发票索引:', invoiceIndex);
            return;
        }
        
        // 清理本地URL（如果是待上传的文件）
        if (isPending && invoice.url && invoice.url.startsWith('blob:')) {
            URL.revokeObjectURL(invoice.url);
            console.log('清理本地URL:', invoice.url);
        }
        
        // 从数组中移除发票
        rowData.invoice_images.splice(invoiceIndex, 1);
        
        // 更新显示
        this.updateInvoiceDisplay(rowIndex, rowData.invoice_images);
        
        // 自动更新单据数量
        this.autoUpdateDocumentCount(rowIndex, rowData.invoice_images);
        
        // 更新隐藏字段
        this.updateHiddenField();
        
        // 显示删除成功消息
        this.showNotification(`发票 "${invoice.filename}" 已删除`, 'success');
        
        console.log('发票删除完成，剩余发票:', rowData.invoice_images);
    }
    
    /**
     * 显示上传进度
     */
    showUploadProgress(btn) {
        btn.style.position = 'relative';
        const progress = document.createElement('div');
        progress.className = 'invoice-upload-progress';
        progress.innerHTML = `
            <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">上传中...</span>
            </div>
            上传中...
        `;
        btn.appendChild(progress);
    }
    
    /**
     * 隐藏上传进度
     */
    hideUploadProgress(btn) {
        const progress = btn.querySelector('.invoice-upload-progress');
        if (progress) {
            progress.remove();
        }
    }
    
    /**
     * 显示通知消息
     */
    showNotification(message, type = 'info') {
        // 使用现有的通知系统或创建简单的提示
        if (window.showNotification) {
            window.showNotification(message, type);
        } else {
            // 备选方案
            const alertClass = type === 'error' ? 'alert-danger' : 
                              type === 'success' ? 'alert-success' : 'alert-info';
            
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            document.body.insertBefore(alertDiv, document.body.firstChild);
            
            // 自动消失
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 3000);
        }
    }
    
    /**
     * 获取CSRF Token
     */
    getCSRFToken() {
        const tokenElement = document.querySelector('meta[name="csrf-token"]') || 
                           document.querySelector('input[name="csrf_token"]');
        return tokenElement ? tokenElement.content || tokenElement.value : '';
    }
    
    /**
     * 触发发票上传
     */
    async triggerInvoiceUpload(rowIndex) {
        // 检测设备是否有摄像头
        const hasCamera = await this.detectCamera();
        
        if (hasCamera) {
            // 有摄像头，显示选择对话框
            this.showUploadOptions(rowIndex);
        } else {
            // 没有摄像头，直接打开文件选择器
            this.openFileSelector(rowIndex);
        }
    }

    /**
     * 检测设备是否有摄像头
     */
    async detectCamera() {
        try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                return false;
            }
            
            // 尝试获取摄像头设备列表
            const devices = await navigator.mediaDevices.enumerateDevices();
            const hasVideoInput = devices.some(device => device.kind === 'videoinput');
            
            return hasVideoInput;
        } catch (error) {
            console.log('摄像头检测失败:', error);
            return false;
        }
    }

    /**
     * 获取可用摄像头列表
     */
    async getAvailableCameras() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            
            console.log('可用摄像头数量:', videoDevices.length);
            return videoDevices;
        } catch (error) {
            console.log('获取摄像头列表失败:', error);
            return [];
        }
    }

    /**
     * 启动摄像头
     */
    async startCamera(modal) {
        const video = modal.querySelector('#cameraVideo');
        const statusDiv = modal.querySelector('#cameraStatus');
        const statusText = modal.querySelector('#statusText');
        const switchBtn = modal.querySelector('#switchCameraBtn');
        
        try {
            // 显示状态提示
            statusDiv.style.display = 'block';
            statusText.textContent = '正在启动摄像头...';
            
            // 配置摄像头约束
            const constraints = {
                video: {
                    facingMode: this.currentFacingMode,
                    width: { ideal: 1280, max: 1920 },
                    height: { ideal: 720, max: 1080 },
                    frameRate: { ideal: 30, max: 60 }
                }
            };
            
            // 如果有多个摄像头，尝试使用设备ID
            if (this.availableCameras.length > 1 && this.currentCameraId) {
                constraints.video.deviceId = { exact: this.currentCameraId };
                delete constraints.video.facingMode; // 使用deviceId时移除facingMode
            }
            
            // 停止之前的流
            if (this.currentStream) {
                this.currentStream.getTracks().forEach(track => track.stop());
            }
            
            // 获取新的媒体流
            this.currentStream = await navigator.mediaDevices.getUserMedia(constraints);
            video.srcObject = this.currentStream;
            
            // 等待视频加载
            await new Promise((resolve) => {
                video.onloadedmetadata = () => {
                    video.play().then(resolve).catch(resolve);
                };
            });
            
            // 隐藏状态提示
            statusDiv.style.display = 'none';
            
            // 绑定摄像头切换事件
            if (switchBtn && this.availableCameras.length > 1) {
                switchBtn.onclick = () => this.switchCamera(modal);
            }
            
            console.log('摄像头启动成功');
            
        } catch (error) {
            console.error('摄像头启动失败:', error);
            statusText.textContent = '摄像头启动失败，请检查权限设置';
            statusDiv.className = 'alert alert-warning mb-2';
            
            // 显示重试按钮
            setTimeout(() => {
                statusDiv.innerHTML = `
                    <small><i class="fas fa-exclamation-triangle me-1"></i>
                    摄像头启动失败，请检查权限设置</small>
                    <button type="button" class="btn btn-sm btn-outline-primary ms-2" onclick="location.reload()">
                        <i class="fas fa-refresh me-1"></i>重新授权
                    </button>
                `;
            }, 2000);
        }
    }

    /**
     * 切换摄像头
     */
    async switchCamera(modal) {
        const switchBtn = modal.querySelector('#switchCameraBtn');
        const statusDiv = modal.querySelector('#cameraStatus');
        const statusText = modal.querySelector('#statusText');
        
        try {
            // 防止重复点击
            switchBtn.disabled = true;
            switchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            
            // 显示切换状态
            statusDiv.style.display = 'block';
            statusDiv.className = 'alert alert-info mb-2';
            statusText.textContent = '正在切换摄像头...';
            
            // 切换前后摄像头
            if (this.currentFacingMode === 'environment') {
                this.currentFacingMode = 'user'; // 切换到前置
            } else {
                this.currentFacingMode = 'environment'; // 切换到后置
            }
            
            // 如果有多个摄像头，循环选择
            if (this.availableCameras.length > 1) {
                const currentIndex = this.availableCameras.findIndex(camera => camera.deviceId === this.currentCameraId);
                const nextIndex = (currentIndex + 1) % this.availableCameras.length;
                this.currentCameraId = this.availableCameras[nextIndex].deviceId;
            }
            
            // 重新启动摄像头
            await this.startCamera(modal);
            
            // 恢复按钮状态
            switchBtn.disabled = false;
            switchBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
            
            console.log('摄像头切换成功:', this.currentFacingMode);
            
        } catch (error) {
            console.error('摄像头切换失败:', error);
            statusText.textContent = '摄像头切换失败';
            statusDiv.className = 'alert alert-warning mb-2';
            
            // 恢复按钮状态
            switchBtn.disabled = false;
            switchBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
        }
    }

    /**
     * 显示上传选项对话框
     */
    showUploadOptions(rowIndex) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'invoiceUploadModal';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">选择上传方式</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center">
                        <div class="row">
                            <div class="col-6">
                                <button type="button" class="btn btn-outline-primary btn-lg w-100 h-100 upload-option-btn" data-option="file">
                                    <i class="fas fa-folder-open fa-2x mb-2"></i><br>
                                    从文件选择
                                </button>
                            </div>
                            <div class="col-6">
                                <button type="button" class="btn btn-outline-success btn-lg w-100 h-100 upload-option-btn" data-option="camera">
                                    <i class="fas fa-camera fa-2x mb-2"></i><br>
                                    拍照上传
                                </button>
                            </div>
                        </div>
                        <div class="mt-3">
                            ${this.generateStandardButton("取消", "secondary", "md", "fas fa-times", null, "button")}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 绑定选项点击事件
        modal.querySelectorAll('.upload-option-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const option = e.currentTarget.dataset.option;
                
                // 使用通用关闭方法
                this.closeModal(modal, 'invoiceUploadModal');
                
                // 执行对应操作
                setTimeout(() => {
                    if (option === 'file') {
                        this.openFileSelector(rowIndex);
                    } else if (option === 'camera') {
                        this.openCamera(rowIndex);
                    }
                }, 100);
            });
        });
        
        // 绑定关闭按钮事件
        const closeBtn = modal.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.closeModal(modal, 'invoiceUploadModal');
            });
        }
        
        // 绑定取消按钮事件
        const cancelBtn = Array.from(modal.querySelectorAll('button')).find(btn => 
            btn.textContent.includes('取消')
        );
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.closeModal(modal, 'invoiceUploadModal');
            });
        }
        
        // 添加键盘事件监听（ESC键关闭）
        const keydownHandler = (e) => {
            if (e.key === 'Escape') {
                this.closeModal(modal, 'invoiceUploadModal');
                document.removeEventListener('keydown', keydownHandler);
            }
        };
        document.addEventListener('keydown', keydownHandler);
        
        // 模态框关闭时移除键盘监听器
        modal.addEventListener('hidden.bs.modal', () => {
            document.removeEventListener('keydown', keydownHandler);
        });
        
        // 显示模态框
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }

    /**
     * 打开文件选择器
     */
    openFileSelector(rowIndex) {
        const fileInput = document.getElementById(`invoiceInput_${rowIndex}`);
        if (fileInput) {
            fileInput.click();
        }
    }

    /**
     * 打开摄像头拍照
     */
    async openCamera(rowIndex) {
        try {
            // 初始化摄像头配置
            this.currentFacingMode = 'environment'; // 默认后置镜头
            this.availableCameras = await this.getAvailableCameras();
            
            // 创建摄像头模态框
            const cameraModal = document.createElement('div');
            cameraModal.className = 'modal fade';
            cameraModal.id = 'cameraModal';
            
            // 检测是否为移动设备
            const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
            const modalSize = isMobile ? 'modal-fullscreen-md-down' : 'modal-lg';
            
            cameraModal.innerHTML = `
                <div class="modal-dialog ${modalSize} modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">拍照上传发票</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body text-center p-2">
                            <!-- 摄像头状态提示 -->
                            <div id="cameraStatus" class="alert alert-info mb-2" style="display: none;">
                                <small><i class="fas fa-info-circle me-1"></i><span id="statusText">正在启动摄像头...</span></small>
                            </div>
                            
                            <!-- 视频容器 -->
                            <div class="camera-container position-relative mb-3" style="max-height: ${isMobile ? '70vh' : '400px'}; overflow: hidden; border-radius: 8px; background: #000;">
                                <video id="cameraVideo" class="w-100 h-100" autoplay playsinline muted style="object-fit: cover; min-height: 200px;"></video>
                                
                                <!-- 摄像头切换按钮 (仅多个摄像头时显示) -->
                                <button id="switchCameraBtn" type="button" class="btn btn-outline-light position-absolute" 
                                        style="top: 10px; right: 10px; border-radius: 50%; width: 50px; height: 50px; display: ${this.availableCameras.length > 1 ? 'flex' : 'none'}; align-items: center; justify-content: center;">
                                    <i class="fas fa-sync-alt"></i>
                                </button>
                                
                                <!-- 网格辅助线 -->
                                <div class="camera-grid position-absolute w-100 h-100" style="top: 0; left: 0; pointer-events: none; opacity: 0.3;">
                                    <div style="position: absolute; top: 33.33%; left: 0; right: 0; height: 1px; background: white;"></div>
                                    <div style="position: absolute; top: 66.66%; left: 0; right: 0; height: 1px; background: white;"></div>
                                    <div style="position: absolute; left: 33.33%; top: 0; bottom: 0; width: 1px; background: white;"></div>
                                    <div style="position: absolute; left: 66.66%; top: 0; bottom: 0; width: 1px; background: white;"></div>
                                </div>
                            </div>
                            
                            <canvas id="cameraCanvas" style="display: none;"></canvas>
                            
                            <!-- 控制按钮 -->
                            <div class="d-flex justify-content-center gap-3 ${isMobile ? 'flex-column' : ''}">
                                ${this.generateStandardButton("拍照", "primary", isMobile ? "lg" : "md", "fas fa-camera", null, "button")}
                                ${this.generateStandardButton("取消", "secondary", isMobile ? "lg" : "md", "fas fa-times", null, "button")}
                            </div>
                            
                            <!-- 使用提示 -->
                            <div class="mt-3">
                                <small class="text-muted">
                                    <i class="fas fa-lightbulb me-1"></i>
                                    请将发票居中对准，确保文字清晰可见
                                    ${this.availableCameras.length > 1 ? '，点击右上角按钮切换摄像头' : ''}
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(cameraModal);
            
            // 启动摄像头
            await this.startCamera(cameraModal);
            
            // 绑定拍照按钮事件 - 通过文本内容找到按钮
            const captureBtn = Array.from(cameraModal.querySelectorAll('button')).find(btn => 
                btn.textContent.includes('拍照')
            );
            console.log('拍照按钮查找结果:', captureBtn);
            if (captureBtn) {
                console.log('拍照按钮已找到，绑定点击事件');
                captureBtn.addEventListener('click', (e) => {
                    console.log('拍照按钮被点击');
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const video = cameraModal.querySelector('#cameraVideo');
                    const stream = this.currentStream;
                    console.log('视频元素:', video, '视频流:', stream);
                    
                    if (video && stream) {
                        this.capturePhoto(video, stream, cameraModal, rowIndex);
                    } else {
                        console.error('拍照失败：视频元素或流不存在');
                        alert('拍照失败，请重新启动摄像头');
                    }
                });
            } else {
                console.error('未找到拍照按钮！');
                // 调试：显示所有按钮
                const allButtons = cameraModal.querySelectorAll('button');
                console.log('所有按钮:', Array.from(allButtons).map(btn => ({
                    text: btn.textContent,
                    className: btn.className,
                    innerHTML: btn.innerHTML
                })));
            }
            
            // 绑定取消按钮事件
            const cancelBtn = Array.from(cameraModal.querySelectorAll('button')).find(btn => 
                btn.textContent.includes('取消') && !btn.classList.contains('btn-close')
            );
            if (cancelBtn) {
                cancelBtn.addEventListener('click', () => {
                    this.closeCameraModal(cameraModal);
                });
            }
            
            // 绑定模态框右上角关闭按钮事件
            const closeBtn = cameraModal.querySelector('.btn-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    this.closeCameraModal(cameraModal);
                });
            }
            
            // 显示模态框
            const bootstrapModal = new bootstrap.Modal(cameraModal);
            bootstrapModal.show();
            
            // 模态框关闭时的事件处理（仅用于日志记录）
            cameraModal.addEventListener('hidden.bs.modal', () => {
                console.log('模态框关闭事件触发');
            });
            
            // 添加键盘事件监听（ESC键关闭）
            const keydownHandler = (e) => {
                if (e.key === 'Escape') {
                    this.closeCameraModal(cameraModal);
                    document.removeEventListener('keydown', keydownHandler);
                }
            };
            document.addEventListener('keydown', keydownHandler);
            
            // 模态框关闭时移除键盘监听器
            cameraModal.addEventListener('hidden.bs.modal', () => {
                document.removeEventListener('keydown', keydownHandler);
            });
            
        } catch (error) {
            console.error('摄像头启动失败:', error);
            alert('无法启动摄像头，请检查权限设置或使用文件上传');
        }
    }

    /**
     * 拍照并处理
     */
    capturePhoto(video, stream, modal, rowIndex) {
        const canvas = modal.querySelector('#cameraCanvas');
        const context = canvas.getContext('2d');
        
        // 设置canvas尺寸，限制最大分辨率
        const maxWidth = 1024;
        const maxHeight = 768;
        
        let canvasWidth = video.videoWidth;
        let canvasHeight = video.videoHeight;
        
        // 控制分辨率，保持宽高比
        if (canvasWidth > maxWidth || canvasHeight > maxHeight) {
            const ratio = Math.min(maxWidth / canvasWidth, maxHeight / canvasHeight);
            canvasWidth = Math.floor(canvasWidth * ratio);
            canvasHeight = Math.floor(canvasHeight * ratio);
        }
        
        canvas.width = canvasWidth;
        canvas.height = canvasHeight;
        
        // 绘制当前视频帧到canvas，优化图片质量
        context.imageSmoothingEnabled = true;
        context.imageSmoothingQuality = 'high';
        context.drawImage(video, 0, 0, canvasWidth, canvasHeight);
        
        // 获取图像数据，显示预览和裁切界面
        const imageDataUrl = canvas.toDataURL('image/jpeg', 0.85);
        this.showCropPreview(imageDataUrl, modal, rowIndex);
    }
    
    /**
     * 显示图片裁切预览界面
     */
    showCropPreview(imageDataUrl, originalModal, rowIndex) {
        // 隐藏摄像头视频和控制按钮
        const video = originalModal.querySelector('#cameraVideo');
        const cameraContainer = originalModal.querySelector('.camera-container');
        const controlButtonsContainer = originalModal.querySelector('.d-flex.justify-content-center.gap-3');
        const usageHint = originalModal.querySelector('.mt-3 small.text-muted');
        
        // 调试信息
        console.log('隐藏元素调试信息:');
        console.log('- video元素:', video);
        console.log('- cameraContainer元素:', cameraContainer);
        console.log('- controlButtonsContainer元素:', controlButtonsContainer);
        console.log('- usageHint元素:', usageHint);
        
        // 查找所有可能的按钮容器
        const allButtonContainers = originalModal.querySelectorAll('.d-flex');
        console.log('- 所有.d-flex容器数量:', allButtonContainers.length);
        allButtonContainers.forEach((container, index) => {
            console.log(`  容器${index}:`, container.className, container.innerHTML.substring(0, 100));
        });
        
        if (video) {
            video.style.display = 'none';
            console.log('✓ 视频已隐藏');
        }
        if (cameraContainer) {
            cameraContainer.style.display = 'none';
            console.log('✓ 摄像头容器已隐藏');
        }
        if (controlButtonsContainer) {
            controlButtonsContainer.style.display = 'none';
            console.log('✓ 控制按钮容器已隐藏');
        } else {
            console.warn('⚠️ 未找到控制按钮容器！');
            // 尝试更具体的选择器
            const buttonContainer = originalModal.querySelector('.modal-body .d-flex.justify-content-center');
            if (buttonContainer) {
                buttonContainer.style.display = 'none';
                console.log('✓ 使用备用选择器隐藏按钮容器');
            }
        }
        if (usageHint) {
            usageHint.style.display = 'none';
            console.log('✓ 使用提示已隐藏');
        }
        
        // 强制隐藏包含"拍照"和"取消"文本的按钮
        const allButtons = originalModal.querySelectorAll('button');
        allButtons.forEach(button => {
            if (button.textContent.includes('拍照') || (button.textContent.includes('取消') && !button.classList.contains('btn-close'))) {
                button.style.display = 'none';
                console.log('✓ 强制隐藏按钮:', button.textContent.trim());
            }
        });
        
        // 创建裁切预览界面
        const modalBody = originalModal.querySelector('.modal-body');
        const cropContainer = document.createElement('div');
        cropContainer.className = 'crop-container';
        cropContainer.innerHTML = `
            <div class="crop-preview-wrapper position-relative" style="max-width: 100%; max-height: 500px; overflow: hidden; margin: 0 auto;">
                <img id="cropPreviewImage" src="${imageDataUrl}" class="img-fluid" style="max-width: 100%; height: auto; display: block;">
                <div id="cropSelection" class="crop-selection" style="
                    position: absolute;
                    border: 2px dashed #007bff;
                    background: rgba(0, 123, 255, 0.1);
                    cursor: move;
                    display: none;
                    min-width: 50px;
                    min-height: 50px;
                ">
                    <div class="resize-handle resize-nw" data-direction="nw"></div>
                    <div class="resize-handle resize-ne" data-direction="ne"></div>
                    <div class="resize-handle resize-sw" data-direction="sw"></div>
                    <div class="resize-handle resize-se" data-direction="se"></div>
                </div>
            </div>
            <div class="text-center mt-3">
                <small class="text-muted d-block mb-2">拖拽选择发票区域，然后点击确认裁切</small>
                <div class="d-flex justify-content-center gap-3">
                    ${this.generateStandardButton("确认裁切", "success", "md", "fas fa-crop", null, "button")}
                    ${this.generateStandardButton("重新拍摄", "warning", "md", "fas fa-redo", null, "button")}
                    ${this.generateStandardButton("取消", "secondary", "md", "fas fa-times", null, "button")}
                </div>
            </div>
        `;
        
        // 添加裁切句柄样式
        const style = document.createElement('style');
        style.textContent = `
            .resize-handle {
                position: absolute;
                width: 10px;
                height: 10px;
                background: #007bff;
                border: 2px solid white;
                border-radius: 50%;
            }
            .resize-nw { top: -5px; left: -5px; cursor: nw-resize; }
            .resize-ne { top: -5px; right: -5px; cursor: ne-resize; }
            .resize-sw { bottom: -5px; left: -5px; cursor: sw-resize; }
            .resize-se { bottom: -5px; right: -5px; cursor: se-resize; }
            .crop-selection:hover { border-color: #0056b3; }
        `;
        document.head.appendChild(style);
        
        modalBody.appendChild(cropContainer);
        
        // 初始化裁切功能
        this.initializeCropTool(cropContainer, imageDataUrl, originalModal, rowIndex);
    }

    /**
     * 初始化裁切工具
     */
    initializeCropTool(container, imageDataUrl, modal, rowIndex) {
        const image = container.querySelector('#cropPreviewImage');
        const selection = container.querySelector('#cropSelection');
        
        // 通过文本内容找到按钮
        const confirmBtn = Array.from(container.querySelectorAll('button')).find(btn => 
            btn.textContent.includes('确认裁切')
        );
        const retakeBtn = Array.from(container.querySelectorAll('button')).find(btn => 
            btn.textContent.includes('重新拍摄')
        );
        const cancelBtn = Array.from(container.querySelectorAll('button')).find(btn => 
            btn.textContent.includes('取消')
        );
        
        let isSelecting = false;
        let isResizing = false;
        let isDragging = false;
        let startX, startY, currentHandle;
        let selectionData = { x: 0, y: 0, width: 0, height: 0 };
        
        // 等待图片加载完成后设置默认选区
        image.onload = () => {
            const rect = image.getBoundingClientRect();
            const containerRect = container.querySelector('.crop-preview-wrapper').getBoundingClientRect();
            
            // 设置默认选区为图片中心的80%区域
            const defaultWidth = rect.width * 0.8;
            const defaultHeight = rect.height * 0.8;
            const defaultX = (rect.width - defaultWidth) / 2;
            const defaultY = (rect.height - defaultHeight) / 2;
            
            this.updateSelection(selection, defaultX, defaultY, defaultWidth, defaultHeight);
            selectionData = { x: defaultX, y: defaultY, width: defaultWidth, height: defaultHeight };
            selection.style.display = 'block';
            if (confirmBtn) {
                confirmBtn.disabled = false;
            }
        };
        
        // 图片点击开始选择
        image.addEventListener('mousedown', (e) => {
            if (isResizing || isDragging) return;
            
            const rect = image.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;
            isSelecting = true;
            
            selection.style.left = startX + 'px';
            selection.style.top = startY + 'px';
            selection.style.width = '0px';
            selection.style.height = '0px';
            selection.style.display = 'block';
        });
        
        // 鼠标移动 - 选择区域
        container.addEventListener('mousemove', (e) => {
            if (!isSelecting && !isDragging && !isResizing) return;
            
            const rect = image.getBoundingClientRect();
            const currentX = e.clientX - rect.left;
            const currentY = e.clientY - rect.top;
            
            if (isSelecting) {
                const width = Math.abs(currentX - startX);
                const height = Math.abs(currentY - startY);
                const left = Math.min(startX, currentX);
                const top = Math.min(startY, currentY);
                
                this.updateSelection(selection, left, top, width, height);
                selectionData = { x: left, y: top, width, height };
            } else if (isDragging) {
                const deltaX = currentX - startX;
                const deltaY = currentY - startY;
                
                let newX = selectionData.x + deltaX;
                let newY = selectionData.y + deltaY;
                
                // 边界检查
                newX = Math.max(0, Math.min(newX, rect.width - selectionData.width));
                newY = Math.max(0, Math.min(newY, rect.height - selectionData.height));
                
                this.updateSelection(selection, newX, newY, selectionData.width, selectionData.height);
                selectionData.x = newX;
                selectionData.y = newY;
            } else if (isResizing && currentHandle) {
                this.handleResize(currentHandle, currentX, currentY, startX, startY, selectionData, selection, image);
            }
            
            if (confirmBtn) {
                confirmBtn.disabled = selectionData.width < 20 || selectionData.height < 20;
            }
        });
        
        // 鼠标释放
        container.addEventListener('mouseup', () => {
            isSelecting = false;
            isDragging = false;
            isResizing = false;
            currentHandle = null;
        });
        
        // 选区拖拽
        selection.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('resize-handle')) {
                isResizing = true;
                currentHandle = e.target.dataset.direction;
            } else {
                isDragging = true;
            }
            
            const rect = image.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;
            e.stopPropagation();
        });
        
        // 确认裁切
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => {
                this.performCrop(imageDataUrl, selectionData, image, modal, rowIndex);
            });
        }
        
        // 重新拍摄
        if (retakeBtn) {
            retakeBtn.addEventListener('click', () => {
                // 恢复摄像头界面的所有元素
                const video = modal.querySelector('#cameraVideo');
                const cameraContainer = modal.querySelector('.camera-container');
                const controlButtonsContainer = modal.querySelector('.d-flex.justify-content-center.gap-3');
                const usageHint = modal.querySelector('.mt-3 small.text-muted');
                const cropContainer = container;
                
                // 显示之前隐藏的元素
                if (video) video.style.display = 'block';
                if (cameraContainer) cameraContainer.style.display = 'block';
                if (controlButtonsContainer) controlButtonsContainer.style.display = 'flex';
                if (usageHint) usageHint.style.display = 'block';
                
                // 恢复被强制隐藏的按钮
                const allButtons = modal.querySelectorAll('button');
                allButtons.forEach(button => {
                    if (button.textContent.includes('拍照') || (button.textContent.includes('取消') && !button.classList.contains('btn-close'))) {
                        button.style.display = 'inline-block'; // 或者原来的display值
                        console.log('✓ 恢复按钮显示:', button.textContent.trim());
                    }
                });
                
                // 移除裁切界面
                cropContainer.remove();
                
                console.log('重新拍摄：摄像头界面已恢复');
            });
        }
        
        // 取消按钮
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.closeCameraModal(modal);
            });
        }
    }

    /**
     * 更新选区位置和大小
     */
    updateSelection(selection, x, y, width, height) {
        selection.style.left = x + 'px';
        selection.style.top = y + 'px';
        selection.style.width = width + 'px';
        selection.style.height = height + 'px';
    }

    /**
     * 处理调整大小
     */
    handleResize(direction, currentX, currentY, startX, startY, selectionData, selection, image) {
        const deltaX = currentX - startX;
        const deltaY = currentY - startY;
        const rect = image.getBoundingClientRect();
        
        let newX = selectionData.x;
        let newY = selectionData.y;
        let newWidth = selectionData.width;
        let newHeight = selectionData.height;
        
        switch (direction) {
            case 'nw':
                newX = Math.max(0, selectionData.x + deltaX);
                newY = Math.max(0, selectionData.y + deltaY);
                newWidth = selectionData.width - (newX - selectionData.x);
                newHeight = selectionData.height - (newY - selectionData.y);
                break;
            case 'ne':
                newY = Math.max(0, selectionData.y + deltaY);
                newWidth = Math.min(rect.width - selectionData.x, selectionData.width + deltaX);
                newHeight = selectionData.height - (newY - selectionData.y);
                break;
            case 'sw':
                newX = Math.max(0, selectionData.x + deltaX);
                newWidth = selectionData.width - (newX - selectionData.x);
                newHeight = Math.min(rect.height - selectionData.y, selectionData.height + deltaY);
                break;
            case 'se':
                newWidth = Math.min(rect.width - selectionData.x, selectionData.width + deltaX);
                newHeight = Math.min(rect.height - selectionData.y, selectionData.height + deltaY);
                break;
        }
        
        // 最小尺寸限制
        if (newWidth >= 50 && newHeight >= 50) {
            this.updateSelection(selection, newX, newY, newWidth, newHeight);
            Object.assign(selectionData, { x: newX, y: newY, width: newWidth, height: newHeight });
        }
    }

    /**
     * 执行图片裁切
     */
    performCrop(originalImageUrl, selectionData, displayImage, modal, rowIndex) {
        const img = new Image();
        img.onload = () => {
            // 创建canvas进行裁切
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // 计算实际图片尺寸与显示尺寸的比例
            const displayRect = displayImage.getBoundingClientRect();
            const scaleX = img.naturalWidth / displayRect.width;
            const scaleY = img.naturalHeight / displayRect.height;
            
            // 计算实际裁切区域
            const cropX = Math.floor(selectionData.x * scaleX);
            const cropY = Math.floor(selectionData.y * scaleY);
            const cropWidth = Math.floor(selectionData.width * scaleX);
            const cropHeight = Math.floor(selectionData.height * scaleY);
            
            // 设置输出canvas尺寸，限制最大尺寸
            const maxOutputWidth = 800;
            const maxOutputHeight = 600;
            let outputWidth = cropWidth;
            let outputHeight = cropHeight;
            
            if (outputWidth > maxOutputWidth || outputHeight > maxOutputHeight) {
                const ratio = Math.min(maxOutputWidth / outputWidth, maxOutputHeight / outputHeight);
                outputWidth = Math.floor(outputWidth * ratio);
                outputHeight = Math.floor(outputHeight * ratio);
            }
            
            canvas.width = outputWidth;
            canvas.height = outputHeight;
            
            // 裁切图片并绘制到canvas
            ctx.imageSmoothingEnabled = true;
            ctx.imageSmoothingQuality = 'high';
            ctx.drawImage(img, cropX, cropY, cropWidth, cropHeight, 0, 0, outputWidth, outputHeight);
            
            // 转换为blob并处理上传
            canvas.toBlob(async (blob) => {
                if (blob) {
                    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                    const file = new File([blob], `invoice_cropped_${timestamp}.jpg`, { type: 'image/jpeg' });
                    
                    try {
                        // 处理上传
                        await this.handleInvoiceUpload(rowIndex, [file]);
                        
                        // 显示成功消息
                        this.showNotification('发票已成功添加', 'success');
                    } catch (error) {
                        console.error('发票上传失败:', error);
                        this.showNotification('发票上传失败，请重试', 'error');
                    }
                    
                    // 强制关闭模态框并清理
                    this.closeCameraModal(modal);
                }
            }, 'image/jpeg', 0.9);
        };
        
        img.src = originalImageUrl;
    }

    /**
     * 生成标准按钮HTML
     */
    generateStandardButton(text, color = "primary", size = "md", icon = null, onclick = null, type = "button") {
        // 根据颜色和文字自动匹配图标
        if (!icon) {
            const cleanText = text.replace(/\s/g, '');
            if (color === "primary" && (cleanText.includes("确认") || cleanText.includes("拍照"))) {
                icon = "fas fa-camera";
            } else if (color === "success" && cleanText.includes("裁切")) {
                icon = "fas fa-crop";
            } else if (color === "warning" && (cleanText.includes("重新") || cleanText.includes("重拍"))) {
                icon = "fas fa-redo";
            } else if (color === "secondary" && cleanText.includes("取消")) {
                icon = "fas fa-times";
            }
        }
        
        // 设置尺寸类
        let sizeClass, fontClass, paddingClass, minWidthClass;
        switch (size) {
            case "sm":
                sizeClass = "btn-sm";
                fontClass = "text-xs";
                paddingClass = "py-1 px-3";
                minWidthClass = "min-width-sm";
                break;
            case "lg":
                sizeClass = "btn-lg";
                fontClass = "text-sm";
                paddingClass = "py-2 px-4";
                minWidthClass = "min-width-lg";
                break;
            default:
                sizeClass = "";
                fontClass = "text-xs";
                paddingClass = "py-1 px-3";
                minWidthClass = "min-width-md";
        }
        
        // 构建CSS类
        const btnClass = `btn btn-${color} rounded-pill ${sizeClass} ${fontClass} ${paddingClass} ${minWidthClass}`;
        
        // 构建按钮HTML
        const iconHtml = icon ? `<i class="${icon} me-1"></i>` : '';
        const textHtml = text; // 移除响应式隐藏逻辑，确保文本始终显示
        
        const onclickAttr = onclick ? `onclick="${onclick}"` : '';
        
        return `<button type="${type}" class="${btnClass}" ${onclickAttr}>
            ${iconHtml}${textHtml}
        </button>`;
    }

    /**
     * 设置页面卸载时的清理
     */
    setupPageUnloadCleanup() {
        // 页面关闭前清理
        window.addEventListener('beforeunload', () => {
            this.cleanupModalBackdrops();
        });
        
        // 页面隐藏时清理（移动端兼容）
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.cleanupModalBackdrops();
            }
        });
        
        // 定期检查并清理残留的模态框
        setInterval(() => {
            const backdrops = document.querySelectorAll('.modal-backdrop');
            const hasModalOpen = document.body.classList.contains('modal-open');
            const hasActiveModals = document.querySelectorAll('.modal.show').length > 0;
            
            // 如果有背景遮罩但没有活动模态框，清理它们
            if (backdrops.length > 0 && !hasActiveModals) {
                console.log('检测到残留的模态框背景，正在清理...');
                this.cleanupModalBackdrops();
            }
            
            // 如果body标记为modal-open但没有活动模态框，恢复状态
            if (hasModalOpen && !hasActiveModals) {
                console.log('检测到body状态异常，正在恢复...');
                document.body.classList.remove('modal-open');
                document.body.style.overflow = '';
                document.body.style.paddingRight = '';
            }
        }, 5000); // 每5秒检查一次
    }

    /**
     * 设置响应式监听器
     */
    setupResponsiveListener() {
        this.resizeTimeout = null;
        
        const handleResize = () => {
            clearTimeout(this.resizeTimeout);
            this.resizeTimeout = setTimeout(() => {
                console.log('窗口大小变化，重新渲染表格');
                this.renderTable();
            }, 250);
        };
        
        window.addEventListener('resize', handleResize);
        
        // 页面卸载时清理监听器
        window.addEventListener('beforeunload', () => {
            window.removeEventListener('resize', handleResize);
            if (this.resizeTimeout) {
                clearTimeout(this.resizeTimeout);
            }
        });
    }

    /**
     * 清理任何残留的模态框背景
     */
    cleanupModalBackdrops() {
        try {
            // 清理所有残留的模态框
            const allModals = document.querySelectorAll('.modal');
            allModals.forEach(modal => {
                // 如果是我们创建的模态框，清理它们
                if (modal.id === 'cameraModal' || modal.id === 'invoiceUploadModal') {
                    // 停止媒体流（如果有）
                    if (modal.id === 'cameraModal') {
                        const video = modal.querySelector('#cameraVideo');
                        if (video && video.srcObject) {
                            const stream = video.srcObject;
                            stream.getTracks().forEach(track => track.stop());
                            video.srcObject = null;
                        }
                    }
                    
                    // 移除模态框
                    if (modal.parentNode) {
                        modal.parentNode.removeChild(modal);
                    }
                }
            });
            
            // 清理残留的模态框背景
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => {
                if (backdrop.parentNode) {
                    backdrop.parentNode.removeChild(backdrop);
                }
            });
            
            // 强制恢复body状态
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
            document.body.style.marginRight = '';
            
            console.log('已清理所有残留的模态框元素');
        } catch (error) {
            console.error('清理模态框时出错:', error);
        }
    }

    /**
     * 通用模态框关闭方法
     */
    closeModal(modal, modalId = null) {
        try {
            // 如果是摄像头模态框，需要停止媒体流
            if (modal.id === 'cameraModal') {
                // 停止当前流
                if (this.currentStream) {
                    this.currentStream.getTracks().forEach(track => {
                        track.stop();
                        console.log('停止媒体轨道:', track.kind);
                    });
                    this.currentStream = null;
                }
                
                // 清理视频元素
                const video = modal.querySelector('#cameraVideo');
                if (video && video.srcObject) {
                    video.srcObject = null;
                }
                
                // 重置摄像头配置
                this.currentFacingMode = 'environment';
                this.currentCameraId = null;
            }
            
            // 关闭Bootstrap模态框
            const bootstrapModal = bootstrap.Modal.getInstance(modal);
            if (bootstrapModal) {
                bootstrapModal.hide();
            }
            
            // 强制移除模态框元素和背景遮罩
            this.forceCleanupModal(modal, modalId);
            
        } catch (error) {
            console.error('关闭模态框时出错:', error);
            // 强制清理作为后备方案
            this.forceCleanupModal(modal, modalId);
        }
    }

    /**
     * 强制清理模态框（用于确保完全清理）
     */
    forceCleanupModal(modal = null, modalId = null) {
        setTimeout(() => {
            // 移除指定的模态框元素
            if (modal && modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }
            
            // 如果有指定ID，也清理同ID的模态框
            if (modalId) {
                const duplicateModals = document.querySelectorAll(`#${modalId}`);
                duplicateModals.forEach(m => {
                    if (m.parentNode) {
                        m.parentNode.removeChild(m);
                    }
                });
            }
            
            // 清理所有残留的模态框背景
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => {
                if (backdrop.parentNode) {
                    backdrop.parentNode.removeChild(backdrop);
                }
            });
            
            // 恢复body状态
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
            
            console.log('模态框强制清理完成');
        }, 300);
    }

    /**
     * 关闭摄像头模态框并清理资源（保持向后兼容）
     */
    closeCameraModal(modal) {
        this.closeModal(modal, 'cameraModal');
    }

    
    /**
     * 自动更新单据数量
     */
    autoUpdateDocumentCount(rowIndex, invoiceImages) {
        // 计算所有发票数量（包括pending状态的本地文件）
        const totalCount = invoiceImages ? invoiceImages.length : 0;
        
        // 查找单据数量输入框
        const documentCountInput = document.querySelector(`[data-row-index="${rowIndex}"] input[data-field="document_count"]`);
        if (!documentCountInput) {
            // 备选选择器
            const allRows = document.querySelectorAll('#expenseTable tbody tr');
            if (allRows[rowIndex]) {
                const input = allRows[rowIndex].querySelector('input[data-field="document_count"]');
                if (input) {
                    this.updateDocumentCountValue(input, totalCount);
                }
            }
            return;
        }
        
        this.updateDocumentCountValue(documentCountInput, totalCount);
    }
    
    /**
     * 更新单据数量值
     */
    updateDocumentCountValue(input, count) {
        // 只有在自动计算模式下才更新
        const isAutoMode = input.dataset.autoCalculate === 'true';
        
        if (isAutoMode) {
            // 直接显示发票数量，没有发票就显示0
            input.value = count;
            
            // 触发change事件以更新相关计算
            input.dispatchEvent(new Event('change', { bubbles: true }));
        } else {
            // 手动编辑模式，不自动更新
        }
    }

    /**
     * 更新发票显示
     */
    updateInvoiceDisplay(rowIndex, invoiceImages = []) {
        console.log('🔍 updateInvoiceDisplay调用:', {rowIndex, invoiceImages});
        
        // 根据当前视图模式选择容器
        const isMobile = this.isMobileView();
        console.log('🔍 当前视图模式:', isMobile ? '移动端' : 'PC端');
        
        let container;
        
        if (isMobile) {
            // 移动端：只查找移动端容器
            container = document.querySelector(`[data-row-index="${rowIndex}"] .mobile-invoice-display`);
            console.log('🔍 移动端容器查找:', `[data-row-index="${rowIndex}"] .mobile-invoice-display`, container);
        } else {
            // PC端：查找PC端容器
            container = document.querySelector(`[data-row-index="${rowIndex}"] .invoice-display-column`);
            console.log('🔍 PC端容器查找:', `[data-row-index="${rowIndex}"] .invoice-display-column`, container);
            
            if (!container) {
                // 备选选择器
                container = document.querySelector(`#expenseTable tbody tr:nth-child(${rowIndex + 1}) .invoice-display-column`);
                console.log('🔍 PC端备选容器:', container);
            }
            if (!container) {
                // 另一种备选选择器
                const allRows = document.querySelectorAll('#expenseTable tbody tr');
                if (allRows[rowIndex]) {
                    container = allRows[rowIndex].querySelector('.invoice-display-column');
                    console.log('🔍 PC端表格行容器:', container);
                }
            }
        }
        
        if (!container) {
            console.warn('未找到发票显示容器:', rowIndex);
            console.log('可用的行:', document.querySelectorAll('#expenseTable tbody tr'));
            console.log('所有移动端容器:', document.querySelectorAll('.mobile-invoice-display'));
            console.log('所有PC端容器:', document.querySelectorAll('.invoice-display-column'));
            return;
        }
        
        console.log('找到发票容器:', container);
        
        container.innerHTML = '';
        
        if (invoiceImages.length === 0) {
            const emptySpan = document.createElement('span');
            emptySpan.className = 'text-muted';
            emptySpan.textContent = '-';
            container.appendChild(emptySpan);
            
            // 调试：输出空容器状态
            console.log('空发票容器状态:', {
                rowIndex: rowIndex,
                containerClasses: container.className,
                containerStyle: window.getComputedStyle(container).display
            });
            return;
        }
        
        // 过滤出实际存在的发票（排除undefined或null）
        const validInvoices = invoiceImages.filter(invoice => invoice);
        
        validInvoices.forEach((invoice, index) => {
            console.log('调试发票数据:', invoice);
            
            const iconDiv = document.createElement('div');
            iconDiv.className = 'individual-invoice-icon';
            iconDiv.dataset.invoice = JSON.stringify(invoice);
            iconDiv.dataset.index = index + 1;
            
            // 根据发票状态决定URL
            let imageUrl;
            let isPending = false;
            
            if (invoice.pending === true && invoice.file) {
                // 待上传的文件：创建本地预览URL
                imageUrl = URL.createObjectURL(invoice.file);
                isPending = true;
                console.log('🔥 创建本地预览URL（blob）:', imageUrl);
            } else {
                // 已上传的文件：使用服务器URL
                imageUrl = invoice.url || invoice.image_url || invoice.path || invoice.file_url;
                console.log('🔥 使用服务器URL:', imageUrl);
                console.log('🔥 发票对象调试:', {
                    pending: invoice.pending,
                    hasFile: !!invoice.file,
                    url: invoice.url,
                    image_url: invoice.image_url,
                    path: invoice.path,
                    file_url: invoice.file_url
                });
            }
            
            if (!imageUrl) {
                console.warn('无法获取发票URL:', invoice);
                return;
            }
            
            // 强制设置发票图标的内联样式
            iconDiv.style.cssText = `
                position: relative !important;
                display: inline-flex !important;
                flex-shrink: 0 !important;
                align-items: center !important;
                justify-content: center !important;
                margin: 0 4px !important;
                min-width: 28px !important;
                width: 28px !important;
                height: 28px !important;
                box-sizing: border-box !important;
            `;
            
            const icon = document.createElement('i');
            // 根据页面类型和状态设置不同的样式
            const isCreatePage = window.location.pathname.includes('/create');
            const isEditPage = window.location.pathname.includes('/edit');
            
            if (isPending) {
                // 创建/编辑页面的待上传文件：黄色
                icon.className = 'fas fa-file-invoice text-warning invoice-preview-icon';
                icon.title = `发票${index + 1}: ${invoice.filename} (待上传)`;
            } else if (invoice.is_temp || invoice.temp_id) {
                // 编辑页面的临时上传文件：橙色，表示已上传但未最终保存
                icon.className = 'fas fa-file-invoice text-info invoice-preview-icon';
                icon.title = `发票${index + 1}: ${invoice.filename} (临时上传)`;
            } else {
                // 已保存的文件：绿色
                icon.className = 'fas fa-file-invoice text-success invoice-preview-icon';
                icon.title = `发票${index + 1}: ${invoice.filename}`;
            }
            icon.style.cursor = 'pointer';
            
            // 添加点击预览事件
            icon.addEventListener('click', (e) => {
                e.preventDefault();
                const title = isPending 
                    ? `发票${index + 1}: ${invoice.filename}`
                    : `发票${index + 1}: ${invoice.filename}`;
                this.showInvoicePreview(imageUrl, title, {
                    rowIndex: rowIndex,
                    invoiceIndex: index,
                    invoice: invoice,
                    isPending: isPending
                });
            });
            
            const badge = document.createElement('span');
            badge.className = 'invoice-number-badge';
            badge.textContent = index + 1;
            
            // 强制设置徽章的内联样式确保正确位置
            badge.style.cssText = `
                position: absolute !important;
                bottom: -2px !important;
                right: -2px !important;
                background-color: #ffffff !important;
                color: #495057 !important;
                border-radius: 3px !important;
                width: 12px !important;
                height: 12px !important;
                font-size: 0.5rem !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                z-index: 10 !important;
                font-weight: 900 !important;
                border: none !important;
                box-shadow: none !important;
                line-height: 1 !important;
                transition: all 0.2s ease !important;
            `;
            
            iconDiv.appendChild(icon);
            iconDiv.appendChild(badge);
            container.appendChild(iconDiv);
        });
        
        // 调试：输出容器状态
        const computedStyle = window.getComputedStyle(container);
        console.log('发票容器详细状态:', {
            rowIndex: rowIndex,
            invoiceCount: invoiceImages.length,
            containerClasses: container.className,
            display: computedStyle.display,
            flexDirection: computedStyle.flexDirection,
            flexWrap: computedStyle.flexWrap,
            width: computedStyle.width,
            minWidth: computedStyle.minWidth,
            maxWidth: computedStyle.maxWidth,
            overflowX: computedStyle.overflowX,
            overflowY: computedStyle.overflowY,
            children: container.children.length,
            childrenInfo: Array.from(container.children).map(child => ({
                className: child.className,
                tagName: child.tagName,
                display: window.getComputedStyle(child).display
            }))
        });
        
        // 检查是否需要滚动，并添加视觉提示
        this.checkScrollability(container);
    }
    
    /**
     * 处理报销单货币变更事件
     */
    async handleExpenseCurrencyChange(newExpenseCurrency) {
        try {
            console.log(`🔄 报销单货币变更为: ${newExpenseCurrency}`);
            
            // 🔥 优先使用内存中的行数据，而不是依赖DOM查询
            console.log(`📋 需要更新 ${this.rows.length} 行明细的转换金额`);
            
            if (this.rows.length === 0) {
                console.log('📝 当前没有报销明细行，只更新总金额货币符号');
                this.updateCurrencySymbol();
                return;
            }
            
            for (let rowIndex = 0; rowIndex < this.rows.length; rowIndex++) {
                const rowData = this.rows[rowIndex];
                
                if (rowData && rowData.currency) {
                    const invoiceAmount = parseFloat(rowData.invoice_amount) || 0;
                    console.log(`🔄 重新计算第 ${rowIndex + 1} 行: ${invoiceAmount} ${rowData.currency} -> ${newExpenseCurrency}`);
                    
                    // 即使发票金额为0，也要更新汇率以便后续输入时使用正确汇率
                    await this.handleCurrencyChange(rowIndex, rowData.currency);
                }
            }
            
            console.log('✅ 所有明细的转换金额已更新');
            
            // 更新总金额的货币符号
            this.updateCurrencySymbol();
            
        } catch (error) {
            console.error('处理报销单货币变更失败:', error);
        }
    }
    
    /**
     * 计算总金额
     */
    calculateTotal() {
        try {
            let total = 0;
            
            // 基于数据而不是DOM元素计算总金额，避免删除行后DOM不同步问题
            this.rows.forEach(rowData => {
                // 优先使用 current_amount（转换后金额），然后是 amount（兼容旧数据）
                const amount = parseFloat(rowData.current_amount) || parseFloat(rowData.amount) || 0;
                total += amount;
            });
            
            // 更新总金额显示
            if (this.grandTotalElement) {
                this.grandTotalElement.value = total.toFixed(2);
                this.grandTotalElement.dataset.rawValue = total;
            }
            
            // 只在总金额发生变化时输出日志
            const lastTotal = this.grandTotalElement?.dataset.lastLoggedTotal;
            if (!lastTotal || parseFloat(lastTotal) !== total) {
                console.log('总金额计算完成:', total, '行数:', this.rows.length);
                if (this.grandTotalElement) {
                    this.grandTotalElement.dataset.lastLoggedTotal = total;
                }
            }
            return total;
            
        } catch (error) {
            console.error('计算总金额失败:', error);
            return 0;
        }
    }
    
    /**
     * 更新总金额的货币符号
     */
    updateCurrencySymbol() {
        try {
            // 获取报销单的当前货币
            const expenseCurrencyElement = document.getElementById('currency');
            const expenseCurrency = expenseCurrencyElement ? expenseCurrencyElement.value : 'CNY';
            
            // 获取货币符号
            const currencySymbol = this.getCurrencySymbol(expenseCurrency);
            
            // 更新总金额区域的货币符号
            const currencySymbolElement = document.querySelector('.expense-total-input .currency-symbol');
            if (currencySymbolElement) {
                const oldSymbol = currencySymbolElement.textContent;
                if (oldSymbol !== currencySymbol) {
                    currencySymbolElement.textContent = currencySymbol;
                    console.log(`💱 总金额货币符号已更新为: ${currencySymbol} (${expenseCurrency})`);
                }
            }
            
        } catch (error) {
            console.error('更新货币符号失败:', error);
        }
    }
    
    /**
     * 获取货币符号
     */
    getCurrencySymbol(currency) {
        const symbols = {
            'CNY': '¥',
            'USD': '$',
            'SGD': 'S$',
            'MYR': 'RM',
            'IDR': 'Rp',
            'THB': '฿'
        };
        return symbols[currency] || '¥';
    }
    
    /**
     * 检查容器是否需要滚动，并添加相应的样式类
     */
    checkScrollability(container) {
        if (!container) return;
        
        // 延迟检查，确保DOM更新完成
        setTimeout(() => {
            const isScrollable = container.scrollWidth > container.clientWidth;
            if (isScrollable) {
                container.classList.add('scrollable');
            } else {
                container.classList.remove('scrollable');
            }
        }, 100);
    }
}

// 全局工具函数
window.ExpenseDetailManager = ExpenseDetailManager;