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
                    label: '单据数量',
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
        this.tableElement = document.querySelector(this.config.tableSelector);
        this.addButton = document.querySelector(this.config.addButtonSelector);
        this.grandTotalElement = document.getElementById(this.config.grandTotalId);
        
        if (!this.tableElement) {
            console.error('报销明细表格元素未找到:', this.config.tableSelector);
            return;
        }
        
        this.bindEvents();
        this.addRow(); // 默认添加一行
        
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
            document_count: 1,
            amount: 0
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
            case 'actions':
                return this.createActionsElement(rowIndex);
            default:
                return this.createTextElement(column, data, fieldName, fieldId, rowIndex);
        }
    }
    
    /**
     * 创建选择框元素（报销科目）
     */
    createSelectElement(column, data, fieldName, fieldId, rowIndex) {
        const select = document.createElement('select');
        select.className = 'form-select expense-category-select';
        select.name = fieldName;
        select.id = fieldId;
        select.dataset.rowIndex = rowIndex;
        select.dataset.field = column.key;
        
        if (column.required) {
            select.required = true;
        }
        
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
        });
        
        if (column.required) {
            input.required = true;
        }
        
        return input;
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
     * 处理字段变化事件
     */
    handleFieldChange(e) {
        const field = e.target.dataset.field;
        const rowIndex = parseInt(e.target.dataset.rowIndex);
        
        if (field && !isNaN(rowIndex)) {
            this.rows[rowIndex][field] = e.target.value;
            this.updateSummary();
            
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
            this.rows[rowIndex][field] = e.target.value;
            
            // 如果是金额或数量字段，实时更新统计
            if (field === 'amount' || field === 'document_count') {
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
        }
    }
    
    /**
     * 删除行
     */
    deleteRow(rowIndex) {
        if (this.rows.length <= 1) {
            alert('至少需要保留一条报销明细');
            return;
        }
        
        if (confirm('确定要删除这条报销明细吗？')) {
            // 删除数据
            this.rows.splice(rowIndex, 1);
            
            // 重新渲染表格
            this.renderTable();
            
            this.updateSummary();
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
        let totalAmount = 0;
        
        this.rows.forEach(row => {
            const amount = parseFloat(row.amount) || 0;
            totalAmount += amount;
        });
        
        // 更新显示
        if (this.grandTotalElement) {
            this.grandTotalElement.value = totalAmount.toFixed(2);
            this.grandTotalElement.dataset.rawValue = totalAmount;
        }
        
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
}

// 全局工具函数
window.ExpenseDetailManager = ExpenseDetailManager;