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
        
        return Object.assign({}, defaultConfig, config);
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
            defaultOption.textContent = '请选择货币';
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
            defaultOption.textContent = '请选择科目';
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
            if (invoiceAmount <= 0) {
                console.log('发票金额为0，设置当前金额为0');
                // 获取报销单的基准货币
                const expenseCurrencyElement = document.getElementById('currency');
                const expenseCurrency = expenseCurrencyElement ? expenseCurrencyElement.value : 'CNY';
                // 如果没有发票金额，清空当前金额显示
                this.updateCurrentAmountDisplay(currentAmountElement, 0, expenseCurrency);
                this.calculateTotal();
                return;
            }
            
            // 获取报销单的基准货币
            const expenseCurrencyElement = document.getElementById('currency');
            const expenseCurrency = expenseCurrencyElement ? expenseCurrencyElement.value : 'CNY';
            
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
        const exchangeRateElement = document.querySelector(`input[data-row-index="${rowIndex}"][data-field="exchange_rate"]`);
        if (exchangeRateElement) {
            exchangeRateElement.value = exchangeRate.toFixed(4);
            // 更新行数据
            this.updateRowData(rowIndex, 'exchange_rate', exchangeRate);
            console.log(`✅ 汇率输入框已更新: ${exchangeRate.toFixed(4)}`);
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
            'USD': 0.14,
            'SGD': 0.19,
            'MYR': 0.65,
            'IDR': 2100.0,
            'THB': 5.0
        };
        
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
        fileInput.accept = 'image/*';
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
     * 删除行
     */
    deleteRow(rowIndex) {
        if (this.rows.length <= 1) {
            // 使用标准通知提示
            if (window.showTopNotification) {
                window.showTopNotification('至少需要保留一条报销明细', 'warning');
            } else {
                alert('至少需要保留一条报销明细');
            }
            return;
        }
        
        // 获取明细信息用于确认提示
        const detail = this.rows[rowIndex];
        const detailInfo = detail ? `${detail.description || '明细项目'}` : '此明细项目';
        
        // 使用标准确认对话框
        if (window.showDeleteConfirm) {
            window.showDeleteConfirm({
                title: '确认删除报销明细',
                message: `确定要删除这条报销明细吗？\n\n明细信息：${detailInfo}\n\n此操作不可恢复。`,
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
                        window.showTopNotification('报销明细删除成功', 'success');
                    }
                }
            });
        } else {
            // 降级到原生确认对话框（向后兼容）
            if (confirm('确定要删除这条报销明细吗？')) {
                this.rows.splice(rowIndex, 1);
                this.renderTable();
                this.updateSummary();
                this.updateHiddenField();
            }
        }
    }
    
    /**
     * 重新渲染表格
     */
    renderTable() {
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
                       accept="image/*" 
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
                
                if (isCreatePage && !row.id) {
                    // 创建页面的新行：暂时存储文件信息，等保存时再上传
                    if (!row.invoice_images) {
                        row.invoice_images = [];
                    }
                    
                    row.invoice_images.push({
                        file: file,
                        pending: true,
                        filename: file.name,
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
                        pending: false  // 明确标记为非pending状态
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
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            this.showNotification('只支持图片格式：JPG、PNG、GIF、WEBP', 'error');
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
                this.showInvoicePreview(images);
            });
        }
    }
    
    /**
     * 显示发票预览
     */
    showInvoicePreview(imageUrl, title, deleteInfo = null) {
        if (!imageUrl) {
            console.warn('发票URL为空，无法预览');
            return;
        }
        
        console.log('预览发票:', imageUrl, title, deleteInfo);
        
        // 创建简单的模态预览
        this.createInvoiceModal(imageUrl, title, deleteInfo);
    }
    
    /**
     * 创建发票预览模态框
     */
    createInvoiceModal(imageUrl, title, deleteInfo = null) {
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
            // 创建摄像头模态框
            const cameraModal = document.createElement('div');
            cameraModal.className = 'modal fade';
            cameraModal.id = 'cameraModal';
            cameraModal.innerHTML = `
                <div class="modal-dialog modal-lg modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">拍照上传发票</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body text-center">
                            <video id="cameraVideo" class="w-100 mb-3" style="max-height: 400px;" autoplay></video>
                            <canvas id="cameraCanvas" style="display: none;"></canvas>
                            <div class="d-flex justify-content-center gap-3">
                                ${this.generateStandardButton("拍照", "primary", "md", "fas fa-camera", null, "button")}
                                ${this.generateStandardButton("取消", "secondary", "md", "fas fa-times", null, "button")}
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(cameraModal);
            
            // 获取摄像头权限
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            const video = cameraModal.querySelector('#cameraVideo');
            video.srcObject = stream;
            
            // 绑定拍照按钮事件 - 通过文本内容找到按钮
            const captureBtn = Array.from(cameraModal.querySelectorAll('button')).find(btn => 
                btn.textContent.includes('拍照')
            );
            if (captureBtn) {
                captureBtn.addEventListener('click', () => {
                    this.capturePhoto(video, stream, cameraModal, rowIndex);
                });
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
        // 隐藏摄像头视频
        const video = originalModal.querySelector('#cameraVideo');
        const captureBtn = originalModal.querySelector('#captureBtn');
        if (video) video.style.display = 'none';
        if (captureBtn) captureBtn.style.display = 'none';
        
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
                // 恢复摄像头界面
                const video = modal.querySelector('#cameraVideo');
                const captureBtn = Array.from(modal.querySelectorAll('button')).find(btn => 
                    btn.textContent.includes('拍照')
                );
                const cropContainer = container;
                
                if (video) video.style.display = 'block';
                if (captureBtn) captureBtn.style.display = 'block';
                cropContainer.remove();
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
        const textHtml = icon ? 
            `<span class="d-none d-md-inline">${text}</span>` : 
            text;
        
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
                const video = modal.querySelector('#cameraVideo');
                if (video && video.srcObject) {
                    const stream = video.srcObject;
                    stream.getTracks().forEach(track => {
                        track.stop();
                        console.log('停止媒体轨道:', track.kind);
                    });
                    video.srcObject = null;
                }
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
        
        // 尝试多种可能的选择器
        let container = document.querySelector(`[data-row-index="${rowIndex}"] .invoice-display-column`);
        if (!container) {
            // 备选选择器
            container = document.querySelector(`#expenseTable tbody tr:nth-child(${rowIndex + 1}) .invoice-display-column`);
        }
        if (!container) {
            // 另一种备选选择器
            const allRows = document.querySelectorAll('#expenseTable tbody tr');
            if (allRows[rowIndex]) {
                container = allRows[rowIndex].querySelector('.invoice-display-column');
            }
        }
        
        if (!container) {
            console.warn('未找到发票显示容器:', rowIndex);
            console.log('可用的行:', document.querySelectorAll('#expenseTable tbody tr'));
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
                console.log('创建本地预览URL:', imageUrl);
            } else {
                // 已上传的文件：使用服务器URL
                imageUrl = invoice.url || invoice.image_url || invoice.path || invoice.file_url;
                console.log('使用服务器URL:', imageUrl);
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
            
            if (isPending) {
                // 创建页面的待上传文件：黄色
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
                    ? `发票${index + 1}: ${invoice.filename} (本地预览)`
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
            
            // 获取所有明细行
            const tbody = document.querySelector(`${this.config.tableSelector} tbody`);
            const rows = tbody.querySelectorAll('tr');
            
            console.log(`📋 需要更新 ${rows.length} 行明细的转换金额`);
            
            for (let i = 0; i < rows.length; i++) {
                const row = rows[i];
                const rowIndex = i;
                
                // 获取当前行的货币和发票金额
                const currencyElement = row.querySelector(`select[data-field="currency"]`);
                const invoiceAmountElement = row.querySelector(`input[data-field="invoice_amount"]`);
                
                if (currencyElement && invoiceAmountElement) {
                    const detailCurrency = currencyElement.value;
                    const invoiceAmount = parseFloat(invoiceAmountElement.value) || 0;
                    
                    if (detailCurrency && invoiceAmount > 0) {
                        console.log(`🔄 重新计算第 ${rowIndex + 1} 行: ${invoiceAmount} ${detailCurrency} -> ${newExpenseCurrency}`);
                        
                        // 重新计算转换金额
                        await this.handleCurrencyChange(rowIndex, detailCurrency);
                    }
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