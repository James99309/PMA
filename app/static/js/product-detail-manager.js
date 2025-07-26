/**
 * 通用产品明细管理组件
 * 支持报价单、采购单、销售单等多种业务场景的产品明细管理
 * 
 * @author Claude AI
 * @version 1.0.0
 */

class ProductDetailManager {
    constructor(config) {
        this.config = this.mergeConfig(config);
        this.rows = [];
        this.eventHandlers = new Map();
        
        // 货币相关属性
        this.currentCurrency = this.config.calculationRules.currency;
        this.exchangeRates = {};
        this.currencySymbols = {};
        
        this.init();
    }
    
    /**
     * 合并默认配置和用户配置
     */
    mergeConfig(config) {
        const defaultConfig = {
            // 基础配置
            tableSelector: '#productTable',
            addButtonSelector: '#addProduct',
            currencySelectorId: 'currencySelector',
            currencySymbolId: 'currencySymbol',
            
            // API端点配置
            apiEndpoints: {
                categories: '/api/products/categories',
                productsByCategory: '/api/products/by-category',
                productModels: '/api/products/models',
                productSpecs: '/api/products/specs',
                productSearch: '/api/products/search',
                tempProducts: '/quotation/products/temp',
                tempProductsByCategory: '/quotation/products/temp/by_category_product',
                saveTempProduct: '/quotation/products/temp/save'
            },
            
            // 计算规则
            calculationRules: {
                discountType: 'percentage', // percentage | fixed
                taxRate: 0,
                currency: 'CNY',
                decimalPlaces: 2,
                allowNegativeDiscount: false,
                autoCalculate: true
            },
            
            // 货币配置
            currencyConfig: {
                supportedCurrencies: [
                    {code: "USD", name: "美元", symbol: "$"},
                    {code: "CNY", name: "人民币", symbol: "¥"},
                    {code: "SGD", name: "新加坡元", symbol: "S$"},
                    {code: "MYR", name: "马来西亚林吉特", symbol: "RM"},
                    {code: "IDR", name: "印尼盾", symbol: "Rp"},
                    {code: "THB", name: "泰铢", symbol: "฿"}
                ],
                baseCurrency: "CNY",
                defaultRates: {
                    "CNY": 1.0,
                    "USD": 0.14,
                    "SGD": 0.19,
                    "MYR": 0.65,
                    "IDR": 2100.0,
                    "THB": 5.0
                }
            },
            
            // 字段映射配置
            fieldMapping: {
                product_name: 'product_name',
                product_model: 'product_model',
                product_desc: 'product_desc',
                brand: 'brand',
                unit: 'unit',
                quantity: 'quantity',
                market_price: 'market_price',
                discount: 'discount',
                unit_price: 'unit_price',
                total_price: 'total_price',
                product_mn: 'product_mn',
                currency: 'currency'
            },
            
            // 验证规则
            validators: {
                quantity: (val) => val > 0,
                market_price: (val) => val >= 0,
                discount: (val) => val >= 0 && val <= 200,
                unit_price: (val) => val >= 0
            },
            
            // 格式化配置
            formatters: {
                currency: true,
                number: true,
                percentage: true
            },
            
            // 表格列配置
            columns: [
                { key: 'product_name', label: '产品名称', type: 'product-selector', required: true, width: '200px' },
                { key: 'product_model', label: '产品型号', type: 'text', readonly: true, width: '150px' },
                { key: 'product_desc', label: '规格', type: 'text', readonly: true, width: '120px' },
                { key: 'brand', label: '品牌', type: 'text', readonly: true, width: '100px' },
                { key: 'unit', label: '单位', type: 'text', readonly: true, width: '80px' },
                { key: 'quantity', label: '数量', type: 'number', required: true, width: '80px' },
                { key: 'market_price', label: '市场价', type: 'currency', width: '100px' },
                { key: 'discount', label: '折扣率(%)', type: 'percentage', width: '100px' },
                { key: 'unit_price', label: '单价', type: 'currency', readonly: false, width: '100px' },
                { key: 'total_price', label: '小计', type: 'currency', readonly: true, width: '100px' },
                { key: 'actions', label: '操作', type: 'actions', width: '80px' }
            ],
            
            // 事件回调
            callbacks: {
                onRowAdd: null,
                onRowRemove: null,
                onRowUpdate: null,
                onProductSelect: null,
                onCalculate: null,
                onValidate: null,
                onError: null
            }
        };
        
        return this.deepMerge(defaultConfig, config || {});
    }
    
    /**
     * 深度合并配置对象
     */
    deepMerge(target, source) {
        const result = { ...target };
        
        for (const key in source) {
            if (source.hasOwnProperty(key)) {
                if (typeof source[key] === 'object' && source[key] !== null && !Array.isArray(source[key])) {
                    result[key] = this.deepMerge(target[key] || {}, source[key]);
                } else {
                    result[key] = source[key];
                }
            }
        }
        
        return result;
    }
    
    /**
     * 初始化组件
     */
    init() {
        this.validateConfig();
        this.initializeTable();
        this.bindEvents();
        this.initProductSelector();
        this.initializeCurrency(); // 初始化货币功能
        this.loadExistingData();
        
        this.trigger('ready');
    }
    
    /**
     * 验证配置
     */
    validateConfig() {
        const required = ['tableSelector'];
        
        required.forEach(key => {
            if (!this.config[key]) {
                throw new Error(`ProductDetailManager: Missing required config: ${key}`);
            }
        });
        
        // 验证表格元素是否存在
        if (!document.querySelector(this.config.tableSelector)) {
            throw new Error(`ProductDetailManager: Table element not found: ${this.config.tableSelector}`);
        }
    }
    
    /**
     * 初始化表格结构
     */
    initializeTable() {
        const table = document.querySelector(this.config.tableSelector);
        
        // 确保表格有必要的结构
        if (!table.querySelector('thead')) {
            const thead = document.createElement('thead');
            const headerRow = this.createHeaderRow();
            thead.appendChild(headerRow);
            table.insertBefore(thead, table.firstChild);
        }
        
        if (!table.querySelector('tbody')) {
            const tbody = document.createElement('tbody');
            table.appendChild(tbody);
        }
    }
    
    /**
     * 创建表头行
     */
    createHeaderRow() {
        const row = document.createElement('tr');
        
        this.config.columns.forEach(column => {
            const th = document.createElement('th');
            th.textContent = column.label;
            if (column.width) {
                th.style.width = column.width;
            }
            if (column.required) {
                th.innerHTML += ' <span class="text-danger">*</span>';
            }
            row.appendChild(th);
        });
        
        return row;
    }
    
    /**
     * 创建总计容器
     */
    createGrandTotalContainer() {
        const table = document.querySelector(this.config.tableSelector);
        const existingContainer = document.querySelector('.grand-total-container');
        
        if (!existingContainer) {
            const container = document.createElement('div');
            container.className = 'grand-total-container mt-3 text-end';
            container.innerHTML = `
                <div class="row justify-content-end">
                    <div class="col-md-3">
                        <div class="input-group">
                            <span class="input-group-text">总计金额</span>
                            <input type="text" class="form-control" id="grandTotal" readonly>
                        </div>
                    </div>
                </div>
            `;
            
            table.parentNode.insertBefore(container, table.nextSibling);
        }
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        const table = document.querySelector(this.config.tableSelector);
        const tbody = table.querySelector('tbody');
        
        // 添加产品按钮事件
        const addButtonContainer = document.querySelector(this.config.addButtonSelector);
        if (addButtonContainer) {
            // 查找容器内的实际按钮元素
            const addButton = addButtonContainer.querySelector('button, a.btn');
            if (addButton) {
                addButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.addRow();
                });
            }
        }
        
        // 表格内事件委托
        tbody.addEventListener('click', (e) => {
            const target = e.target;
            
            // 删除行按钮
            if (target.classList.contains('remove-row')) {
                e.preventDefault();
                const row = target.closest('tr');
                this.removeRow(row);
            }
        });
        
        // 输入字段变化事件
        tbody.addEventListener('input', (e) => {
            const target = e.target;
            const row = target.closest('tr');
            
            // 避免在更新时触发事件
            if (row && this.config.calculationRules.autoCalculate && !target.dataset.updating) {
                this.handleFieldChange(row, target);
            }
        });
        
        tbody.addEventListener('change', (e) => {
            const target = e.target;
            const row = target.closest('tr');
            
            // 避免在更新时触发事件
            if (row && this.config.calculationRules.autoCalculate && !target.dataset.updating) {
                this.handleFieldChange(row, target);
            }
        });
        
        // 焦点事件处理格式化
        tbody.addEventListener('focus', (e) => {
            if (e.target.classList.contains('currency-input') || e.target.classList.contains('number-input')) {
                this.showRawValue(e.target);
            }
        });
        
        tbody.addEventListener('blur', (e) => {
            if (e.target.classList.contains('currency-input') || e.target.classList.contains('number-input')) {
                this.showFormattedValue(e.target);
                // 失焦时也触发计算，但避免在更新时触发
                const row = e.target.closest('tr');
                if (row && this.config.calculationRules.autoCalculate && !e.target.dataset.updating) {
                    this.handleFieldChange(row, e.target);
                }
            }
        });
    }
    
    /**
     * 处理字段变化
     */
    handleFieldChange(row, field) {
        console.log('字段变化:', field.className, field.value);
        
        // 从类名中提取字段名，如 'quantity-input' -> 'quantity'
        const fieldName = field.className.split(' ').find(cls => cls.endsWith('-input'))?.replace('-input', '');
        console.log('提取的字段名:', fieldName);
        
        // 更新输入框的rawValue，货币字段需要移除千位分隔符
        if (field.value !== '') {
            if (field.classList.contains('currency-input')) {
                // 货币字段：移除千位分隔符后存储原始值
                field.dataset.rawValue = field.value.replace(/,/g, '');
            } else {
                // 普通字段：直接存储
                field.dataset.rawValue = field.value;
            }
        }
        
        // 根据不同字段类型选择计算方式
        if (fieldName === 'unit_price') {
            // 单价变化时，反向计算折扣率
            console.log('单价变化，反向计算折扣率...');
            this.calculateDiscountFromUnitPrice(row);
        } else {
            // 其他字段变化时，正向计算单价
            console.log('其他字段变化，重新计算单价...');
            this.calculateRow(row);
        }
        
        this.updateGrandTotal();
    }
    
    /**
     * 初始化产品选择器
     */
    initProductSelector() {
        const selectorConfig = {
            apiEndpoints: this.config.apiEndpoints,
            onSelect: (product, inputElement) => {
                this.handleProductSelect(product, inputElement);
            },
            onError: (error) => {
                this.trigger('error', { type: 'product-selector', error });
            }
        };
        
        // 传递手动输入配置
        if (this.config.manual_input) {
            selectorConfig.manual_input = this.config.manual_input;
        }
        
        // 传递临时产品配置
        if (this.config.temp_products) {
            selectorConfig.temp_products = this.config.temp_products;
        }
        
        console.log('🔧 产品选择器配置:', selectorConfig);
        this.productSelector = new ProductSelector(selectorConfig);
    }
    
    /**
     * 处理产品选择
     */
    handleProductSelect(product, inputElement) {
        console.log('🔄 处理产品选择:', product.product_name);
        const row = inputElement.closest('tr');
        
        // 填充产品数据
        this.fillProductData(row, product);
        
        // 处理手动输入模式的字段状态
        if (product.is_temp || product.status === 'temp') {
            this.enableManualInputMode(row, product);
        } else {
            this.disableManualInputMode(row);
        }
        
        // 重新计算
        this.calculateRow(row);
        this.updateGrandTotal();
        
        // 确保产品选择器菜单被关闭
        if (this.productSelector) {
            this.productSelector.hideMenu();
            console.log('🔧 手动关闭产品选择器菜单');
        }
        
        // 触发回调
        this.trigger('productSelect', { product, row });
        
        console.log('🔄 产品选择处理完成');
    }
    
    /**
     * 填充产品数据到行
     */
    fillProductData(row, product) {
        console.log('✅ 填充产品数据:', product);
        console.log('市场价格数据:', {
            market_price: product.market_price,
            retail_price: product.retail_price,
            '使用值': product.market_price || product.retail_price || 0
        });
        
        // 根据实际HTML结构设置字段值
        // 产品名称使用特殊的类名
        const productNameInput = row.querySelector('.product-name');
        if (productNameInput) {
            productNameInput.value = product.product_name || '';
            console.log('✅ 设置产品名称:', product.product_name);
        }
        
        // 检查是否为停产产品 - 更全面的检测
        const isDiscontinued = product.status === 'discontinued' || 
                              product.status === '停产' || 
                              product.status === 'inactive' ||
                              product.product_status === 'discontinued' ||
                              product.product_status === '停产' ||
                              (product.status && product.status.toLowerCase().includes('discontin'));
        
        // 其他字段使用标准的key-input格式
        // 产品型号字段 - 简单设置，不做特殊处理
        const productModel = product.product_model || product.model || '';
        this.setFieldValueByKey(row, 'product_model', productModel);
        
        this.setFieldValueByKey(row, 'product_desc', product.product_desc || product.specification || '');
        this.setFieldValueByKey(row, 'brand', product.brand || '');
        this.setFieldValueByKey(row, 'unit', product.unit || '');
        this.setFieldValueByKey(row, 'market_price', product.retail_price || product.market_price || 0);
        this.setFieldValueByKey(row, 'product_mn', product.product_mn || '');
        
        // 设置默认值
        this.setFieldValueByKey(row, 'quantity', 1);
        this.setFieldValueByKey(row, 'discount', 100);
        
        // 初始化单价为市场价（100%折扣）
        const initialUnitPrice = product.retail_price || product.market_price || 0;
        this.setFieldValueByKey(row, 'unit_price', initialUnitPrice);
        
        // 如果是临时产品，设置临时产品ID和类别信息
        if (product.is_temp || product.status === 'temp') {
            row.dataset.tempProductId = product.id || product.temp_product_id;
            row.dataset.isTemp = 'true';
            
            // 保存类别信息到DOM中，供后续保存报价单时使用
            if (product.category) {
                row.dataset.category = product.category;
                console.log('✅ 保存类别信息到DOM:', product.category);
            }
            if (product.category_path) {
                row.dataset.categoryPath = product.category_path;
                console.log('✅ 保存类别路径到DOM:', product.category_path);
            }
            
            console.log('✅ 设置临时产品ID:', row.dataset.tempProductId);
        }
        
        // 如果是停产产品，给价格字段添加停产样式
        if (isDiscontinued) {
            const marketPriceInput = row.querySelector('.market_price-input');
            const unitPriceInput = row.querySelector('.unit_price-input');
            
            if (marketPriceInput) {
                marketPriceInput.classList.add('discontinued-price');
                marketPriceInput.setAttribute('title', '该产品已停产');
            }
            if (unitPriceInput) {
                unitPriceInput.classList.add('discontinued-price');
                unitPriceInput.setAttribute('title', '该产品已停产');
            }
        }
        
        console.log('✅ 产品数据填充完成');
    }
    
    /**
     * 根据列配置key设置字段值 (推荐使用)
     */
    setFieldValueByKey(row, columnKey, value, allowHtml = false) {
        // 产品名称字段使用特殊的类名
        if (columnKey === 'product_name') {
            const input = row.querySelector('.product-name');
            if (input) {
                input.value = String(value);
                input.dataset.rawValue = String(value);
                console.log(`✅ 设置产品名称: ${value}`);
                return;
            } else {
                console.warn(`❌ 未找到产品名称字段，尝试的选择器: .product-name`);
                return;
            }
        }
        
        // 直接使用columnKey作为类名前缀
        const className = `${columnKey}-input`;
        
        // 查找输入框
        let input = row.querySelector(`.${className}`);
        
        if (input) {
            console.log(`✅ 设置字段 ${columnKey} = ${value}`);
            
            // 更新原始值
            input.dataset.rawValue = String(value);
            
            if (input.classList.contains('currency-input') && columnKey === 'market_price') {
                // 只有市场单价字段使用货币格式化
                const numValue = parseFloat(value) || 0;
                input.value = this.formatCurrency(numValue);
                console.log(`💰 设置市场单价: ${numValue} -> ${input.value}`);
            } else if (input.classList.contains('currency-input')) {
                // 其他货币类型字段（单价、小计）
                const numValue = parseFloat(value) || 0;
                input.value = this.formatCurrency(numValue);
                console.log(`💰 设置货币值: ${columnKey} = ${numValue} -> ${input.value}`);
            } else {
                // 普通字段直接设置值
                input.value = String(value);
                console.log(`ℹ️ 设置普通值: ${columnKey} = ${value}`);
            }
        } else {
            console.warn(`❌ 未找到字段 ${columnKey} 的输入框，尝试的选择器: .${className}`);
        }
    }

    /**
     * 设置字段值 (向后兼容)
     */
    setFieldValue(row, fieldName, value) {
        // 尝试多种选择器查找输入框
        let input = row.querySelector(`[name="${fieldName}"]`);
        if (!input) {
            input = row.querySelector(`.${fieldName}-input`);
        }
        if (!input) {
            input = row.querySelector(`input[class*="${fieldName}"]`);
        }
        if (!input) {
            input = row.querySelector(`select[class*="${fieldName}"]`);
        }
        
        if (input) {
            input.value = value;
            if (input.dataset) {
                input.dataset.rawValue = value;
            }
        }
    }
    
    /**
     * 获取字段值
     */
    getFieldValue(row, fieldName) {
        // 产品名称字段使用特殊的类名
        if (fieldName === 'product_name') {
            const input = row.querySelector('.product-name');
            if (input) {
                return input.dataset.rawValue || input.value || '';
            }
            console.warn(`❌ 未找到产品名称字段，尝试的选择器: .product-name`);
            return '';
        }
        
        // 尝试多种选择器查找输入框
        let input = row.querySelector(`.${fieldName}-input`);
        if (!input) {
            input = row.querySelector(`[name="${fieldName}[]"]`);
        }
        if (!input) {
            input = row.querySelector(`[name*="${fieldName}"]`);
        }
        
        
        if (input) {
            // 优先使用原始值，避免千位分隔符问题
            let value = input.dataset.rawValue || input.value || '';
            
            // 如果是货币类型字段且没有原始值，需要移除千位分隔符
            if (!input.dataset.rawValue && input.classList.contains('currency-input')) {
                value = String(value).replace(/,/g, '');
                console.log(`💰 移除千位分隔符: ${input.value} -> ${value}`);
            }
            
            console.log(`获取字段 ${fieldName} 的值:`, value);
            return value;
        }
        
        console.warn(`未找到字段 ${fieldName} 的输入框`);
        return null;
    }
    
    /**
     * 添加新行
     */
    addRow(data = null) {
        const tbody = document.querySelector(`${this.config.tableSelector} tbody`);
        const row = this.createRow(data);
        
        tbody.appendChild(row);
        
        // 初始化行的产品选择器
        this.productSelector.initializeRow(row);
        
        // 如果有数据则填充
        if (data) {
            this.fillRowData(row, data);
            // 只有在数据不包含单价信息时才重新计算（新添加的行）
            // 编辑模式下加载现有数据时，保持原有价格
            const hasExistingPrice = data.unit_price !== undefined && data.unit_price !== null;
            if (!hasExistingPrice) {
                this.calculateRow(row);
            } else {
                console.log('🔧 编辑模式：保持现有价格，不重新计算');
            }
        }
        
        this.updateGrandTotal();
        
        // 触发回调
        this.trigger('rowAdd', { row, data });
        
        return row;
    }
    
    /**
     * 创建表格行
     */
    createRow(data = null) {
        const row = document.createElement('tr');
        
        this.config.columns.forEach(column => {
            const td = document.createElement('td');
            const input = this.createField(column, data);
            
            if (input) {
                td.appendChild(input);
            }
            row.appendChild(td);
        });
        
        return row;
    }
    
    /**
     * 创建字段元素
     */
    createField(column, data = null) {
        const value = data ? data[column.key] : '';
        
        switch (column.type) {
            case 'product-selector':
                return this.createProductSelectorField(column, value);
            case 'text':
                return this.createTextInput(column, value);
            case 'number':
                return this.createNumberInput(column, value);
            case 'currency':
                return this.createCurrencyInput(column, value);
            case 'percentage':
                return this.createPercentageInput(column, value);
            case 'actions':
                return this.createActionsField();
            default:
                return this.createTextInput(column, value);
        }
    }
    
    /**
     * 创建产品选择器字段
     */
    createProductSelectorField(column, value) {
        const container = document.createElement('div');
        container.className = 'product-name-container';
        
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control product-name';
        input.name = this.config.fieldMapping[column.key] + '[]';
        input.placeholder = '点击选择产品...';
        input.required = column.required || false;
        input.value = value || '';
        input.dataset.rawValue = value || '';  // 添加rawValue属性
        
        if (column.readonly) {
            input.readOnly = true;
        }
        
        container.appendChild(input);
        return container;
    }
    
    /**
     * 创建文本输入框
     */
    createTextInput(column, value) {
        const input = document.createElement('input');
        input.type = 'text';
        input.className = `form-control ${column.key}-input`;
        input.name = this.config.fieldMapping[column.key] + '[]';
        input.value = value || '';
        input.required = column.required || false;
        
        if (column.readonly) {
            input.readOnly = true;
        }
        
        return input;
    }
    
    /**
     * 创建数字输入框
     */
    createNumberInput(column, value) {
        const input = document.createElement('input');
        input.type = 'number';
        input.className = `form-control ${column.key}-input number-input`;
        input.name = this.config.fieldMapping[column.key] + '[]';
        input.value = value || '';
        input.required = column.required || false;
        input.min = 0;
        input.step = column.key === 'quantity' ? '1' : '0.01';
        
        if (column.readonly) {
            input.readOnly = true;
        }
        
        return input;
    }
    
    /**
     * 创建货币输入框
     */
    createCurrencyInput(column, value) {
        const input = document.createElement('input');
        input.type = 'text';
        input.className = `form-control ${column.key}-input currency-input`;
        input.name = this.config.fieldMapping[column.key] + '[]';
        input.style.textAlign = 'right';
        
        if (column.readonly) {
            input.readOnly = true;
        }
        
        if (value !== null && value !== undefined) {
            input.dataset.rawValue = value;
            input.value = this.formatCurrency(value);
        }
        
        return input;
    }
    
    /**
     * 创建百分比输入框
     */
    createPercentageInput(column, value) {
        const input = document.createElement('input');
        input.type = 'number';
        input.className = `form-control ${column.key}-input percentage-input`;
        input.name = this.config.fieldMapping[column.key] + '[]';
        input.value = value || '100';
        input.min = 0;
        input.max = 200;
        input.step = '0.1';
        input.style.textAlign = 'right';
        
        return input;
    }
    
    /**
     * 创建操作按钮字段
     */
    createActionsField() {
        const container = document.createElement('div');
        container.className = 'text-center';
        
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-sm btn-outline-danger remove-row';
        removeBtn.innerHTML = '<i class="fas fa-trash"></i>';
        removeBtn.title = '删除行';
        
        container.appendChild(removeBtn);
        return container;
    }
    
    /**
     * 删除行
     */
    removeRow(row) {
        const tbody = row.parentNode;
        
        // 至少保留一行
        if (tbody.children.length <= 1) {
            this.showError('至少需要保留一行产品明细');
            return;
        }
        
        tbody.removeChild(row);
        this.updateGrandTotal();
        
        // 触发回调
        this.trigger('rowRemove', { row });
    }
    
    /**
     * 计算行小计
     */
    calculateRow(row) {
        const mapping = this.config.fieldMapping;
        const rules = this.config.calculationRules;
        
        console.log('计算行小计, 字段映射:', mapping);
        
        // 检查是否为临时产品
        const isTempProduct = row.dataset.isTemp === 'true' || row.dataset.manualInputMode === 'true';
        
        if (isTempProduct) {
            console.log('🟠 计算临时产品行小计');
            return this.calculateTempProductRow(row);
        }
        
        console.log('计算普通产品行小计');
        console.log('行中所有输入框:', row.querySelectorAll('input'));
        
        // 获取计算所需的值 - 尝试多种选择器
        let marketPriceInput = row.querySelector('.market_price-input');
        let discountInput = row.querySelector('.discount-input');
        let quantityInput = row.querySelector('.quantity-input');
        
        // 如果找不到，尝试其他可能的选择器
        if (!marketPriceInput) {
            marketPriceInput = row.querySelector('input[class*="market"]') || row.querySelector('input[name*="market"]');
        }
        if (!discountInput) {
            discountInput = row.querySelector('input[class*="discount"]') || row.querySelector('input[name*="discount"]');
        }
        if (!quantityInput) {
            quantityInput = row.querySelector('input[class*="quantity"]') || row.querySelector('input[name*="quantity"]');
        }
        
        console.log('输入框查找结果:', {
            marketPriceInput: marketPriceInput,
            discountInput: discountInput,
            quantityInput: quantityInput,
            marketPriceClass: marketPriceInput?.className,
            discountClass: discountInput?.className,
            quantityClass: quantityInput?.className
        });
        
        // 使用原始值或当前值
        const marketPrice = parseFloat(marketPriceInput?.dataset.rawValue || marketPriceInput?.value?.replace(/,/g, '') || 0);
        const discount = parseFloat(discountInput?.dataset.rawValue || discountInput?.value || 100);
        const quantity = parseInt(quantityInput?.dataset.rawValue || quantityInput?.value || 1);
        
        console.log('获取的原始值:', {
            marketPriceValue: marketPriceInput?.value,
            marketPriceRaw: marketPriceInput?.dataset.rawValue,
            discountValue: discountInput?.value,
            discountRaw: discountInput?.dataset.rawValue,
            quantityValue: quantityInput?.value,
            quantityRaw: quantityInput?.dataset.rawValue
        });
        
        console.log('计算参数:', { 
            marketPrice: marketPrice, 
            discount: discount, 
            quantity: quantity,
            discountType: rules.discountType,
            '数据类型': {
                marketPrice: typeof marketPrice,
                discount: typeof discount,
                quantity: typeof quantity
            }
        });
        
        // 计算单价
        let unitPrice = 0;
        if (!isNaN(marketPrice) && !isNaN(discount)) {
            if (rules.discountType === 'percentage') {
                unitPrice = marketPrice * (discount / 100);
            } else {
                unitPrice = marketPrice - discount;
            }
        }
        
        // 计算小计
        let totalPrice = 0;
        if (!isNaN(unitPrice) && !isNaN(quantity)) {
            totalPrice = unitPrice * quantity;
        }
        
        console.log('计算结果:', { 
            unitPrice: unitPrice, 
            totalPrice: totalPrice,
            '公式': rules.discountType === 'percentage' ? 
                `${marketPrice} * (${discount}/100) * ${quantity} = ${totalPrice}` :
                `(${marketPrice} - ${discount}) * ${quantity} = ${totalPrice}`
        });
        
        // 更新界面 - 使用setFieldValueByKey方法
        this.setFieldValueByKey(row, 'unit_price', unitPrice);
        this.setFieldValueByKey(row, 'total_price', totalPrice);
        
        return { unitPrice, totalPrice };
    }
    
    /**
     * 临时产品行计算
     */
    calculateTempProductRow(row) {
        // 获取输入框
        const unitPriceInput = row.querySelector('.unit_price-input');
        const quantityInput = row.querySelector('.quantity-input');
        
        // 获取当前值
        const unitPrice = parseFloat(unitPriceInput?.value?.replace(/,/g, '') || 0);
        const quantity = parseInt(quantityInput?.value || 1);
        
        // 临时产品的计算逻辑：单价 * 数量 = 小计
        // 不依赖市场价格和折扣率
        const totalPrice = unitPrice * quantity;
        
        console.log('🟠 临时产品计算:', {
            unitPrice: unitPrice,
            quantity: quantity,
            totalPrice: totalPrice,
            公式: `${unitPrice} * ${quantity} = ${totalPrice}`
        });
        
        // 只更新小计，不更新单价
        this.setFieldValueByKey(row, 'total_price', totalPrice);
        
        return { unitPrice, totalPrice };
    }
    
    /**
     * 根据单价反向计算折扣率
     */
    calculateDiscountFromUnitPrice(row) {
        const mapping = this.config.fieldMapping;
        const rules = this.config.calculationRules;
        
        console.log('反向计算折扣率...');
        
        // 获取输入框
        const marketPriceInput = row.querySelector('.market_price-input');
        const unitPriceInput = row.querySelector('.unit_price-input');
        const discountInput = row.querySelector('.discount-input');
        const quantityInput = row.querySelector('.quantity-input');
        
        // 获取值
        const marketPrice = parseFloat(marketPriceInput?.dataset.rawValue || marketPriceInput?.value?.replace(/,/g, '') || 0);
        const unitPrice = parseFloat(unitPriceInput?.dataset.rawValue || unitPriceInput?.value?.replace(/,/g, '') || 0);
        const quantity = parseInt(quantityInput?.dataset.rawValue || quantityInput?.value || 1);
        
        console.log('反向计算参数:', { marketPrice, unitPrice, quantity });
        
        // 计算折扣率
        let discount = 100; // 默认100%
        if (marketPrice > 0) {
            if (rules.discountType === 'percentage') {
                discount = (unitPrice / marketPrice) * 100;
            } else {
                discount = marketPrice - unitPrice;
            }
            // 限制折扣率范围
            discount = Math.max(0, Math.min(200, discount));
        }
        
        // 计算小计
        const totalPrice = unitPrice * quantity;
        
        console.log('反向计算结果:', { 
            discount: discount, 
            totalPrice: totalPrice,
            '公式': rules.discountType === 'percentage' ? 
                `(${unitPrice} / ${marketPrice}) * 100 = ${discount.toFixed(2)}%` :
                `${marketPrice} - ${unitPrice} = ${discount}`
        });
        
        // 更新折扣率和小计
        this.setFieldValueByKey(row, 'discount', discount.toFixed(1));
        this.setFieldValueByKey(row, 'total_price', totalPrice);
        
        return { discount, totalPrice };
    }
    
    /**
     * 更新总计
     */
    updateGrandTotal() {
        const tbody = document.querySelector(`${this.config.tableSelector} tbody`);
        const rows = tbody.querySelectorAll('tr');
        let grandTotal = 0;
        
        rows.forEach(row => {
            const totalPriceInput = row.querySelector(`.${this.config.fieldMapping.total_price}-input`);
            if (totalPriceInput) {
                const value = parseFloat(totalPriceInput.dataset.rawValue) || 0;
                grandTotal += value;
            }
        });
        
        // 更新总计显示
        const grandTotalId = this.config.grand_total_id || 'grandTotal';
        const grandTotalInput = document.querySelector(`#${grandTotalId}`);
        if (grandTotalInput) {
            grandTotalInput.value = this.formatCurrency(grandTotal);
            grandTotalInput.dataset.rawValue = grandTotal;
            console.log(`✅ 更新总计显示: ${grandTotal} -> ${grandTotalInput.value}`);
        } else {
            console.warn(`❌ 找不到总计输入框: #${grandTotalId}`);
        }
        
        // 触发回调
        this.trigger('grandTotalUpdate', { grandTotal, currency: this.currentCurrency });
        
        return grandTotal;
    }
    
    /**
     * 初始化货币功能
     */
    async initializeCurrency() {
        console.log('💱 初始化货币功能...');
        
        try {
            // 从模板配置中更新货币配置
            if (this.config.currency_config) {
                this.config.currencyConfig = {
                    supportedCurrencies: this.config.currency_config.supported_currencies || this.config.currencyConfig.supportedCurrencies,
                    defaultRates: this.config.currency_config.default_rates || this.config.currencyConfig.defaultRates,
                    baseCurrency: this.config.currency_config.base_currency || this.config.currencyConfig.baseCurrency
                };
            }
            
            // 更新ID配置
            if (this.config.currency_selector_id) {
                this.config.currencySelectorId = this.config.currency_selector_id;
            }
            if (this.config.currency_symbol_id) {
                this.config.currencySymbolId = this.config.currency_symbol_id;
            }
            
            // 加载货币符号映射
            if (this.config.currencyConfig && this.config.currencyConfig.supportedCurrencies) {
                this.config.currencyConfig.supportedCurrencies.forEach(currency => {
                    this.currencySymbols[currency.code] = currency.symbol;
                });
            }
            
            // 加载汇率数据
            await this.loadExchangeRates();
            
            // 创建货币选择器
            this.createCurrencySelector();
            
            // 绑定货币变化事件
            this.bindCurrencyEvents();
            
            // 设置初始货币符号
            this.updateCurrencySymbol(this.currentCurrency);
            
            console.log('✅ 货币功能初始化完成');
            
        } catch (error) {
            console.error('❌ 货币功能初始化失败:', error);
            // 使用默认设置
            this.exchangeRates = (this.config.currencyConfig && this.config.currencyConfig.defaultRates) || {
                'CNY': 1.0,
                'USD': 0.14,
                'SGD': 0.19,
                'MYR': 0.65,
                'IDR': 2100.0,
                'THB': 5.0
            };
        }
    }
    
    /**
     * 加载汇率数据
     */
    async loadExchangeRates() {
        try {
            const response = await fetch('/api/v1/exchange-rate/rates');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.exchangeRates = result.data.rates;
                console.log('💱 汇率数据加载成功:', this.exchangeRates);
            } else {
                throw new Error(result.message || '获取汇率失败');
            }
        } catch (error) {
            console.warn('汇率加载失败，使用默认汇率:', error);
            this.exchangeRates = this.config.currencyConfig.defaultRates;
        }
    }
    
    /**
     * 创建货币选择器
     */
    createCurrencySelector() {
        const currencySelect = document.getElementById(this.config.currencySelectorId);
        if (!currencySelect) {
            console.warn('未找到货币选择器元素:', this.config.currencySelectorId);
            return;
        }
        
        // 清空现有选项
        currencySelect.innerHTML = '';
        
        // 添加货币选项
        this.config.currencyConfig.supportedCurrencies.forEach(currency => {
            const option = document.createElement('option');
            option.value = currency.code;
            option.textContent = `${currency.name} (${currency.code})`;
            
            if (currency.code === this.currentCurrency) {
                option.selected = true;
            }
            
            currencySelect.appendChild(option);
        });
        
        console.log('💱 货币选择器创建完成');
    }
    
    /**
     * 绑定货币变化事件
     */
    bindCurrencyEvents() {
        const currencySelect = document.getElementById(this.config.currencySelectorId);
        if (!currencySelect) return;
        
        currencySelect.addEventListener('change', (e) => {
            const newCurrency = e.target.value;
            this.handleCurrencyChange(newCurrency);
        });
    }
    
    /**
     * 处理货币变化
     */
    async handleCurrencyChange(newCurrency) {
        console.log(`🔄 货币变化: ${this.currentCurrency} -> ${newCurrency}`);
        
        if (newCurrency === this.currentCurrency) {
            return;
        }
        
        const oldCurrency = this.currentCurrency;
        this.currentCurrency = newCurrency;
        
        // 更新货币符号
        this.updateCurrencySymbol(newCurrency);
        
        // 转换所有金额字段
        await this.convertAllAmounts(oldCurrency, newCurrency);
        
        // 更新总计
        this.updateGrandTotal();
        
        // 触发事件
        this.trigger('currencyChanged', { oldCurrency, newCurrency });
        
        console.log('✅ 货币变化完成');
    }
    
    /**
     * 更新货币符号
     */
    updateCurrencySymbol(currency) {
        const symbolElement = document.getElementById(this.config.currencySymbolId);
        if (symbolElement) {
            symbolElement.textContent = this.currencySymbols[currency] || currency;
        }
    }
    
    /**
     * 转换所有金额字段
     */
    async convertAllAmounts(fromCurrency, toCurrency) {
        const tbody = document.querySelector(`${this.config.tableSelector} tbody`);
        const rows = tbody.querySelectorAll('tr');
        
        console.log(`🔄 开始转换所有金额: ${fromCurrency} -> ${toCurrency}`);
        
        for (const row of rows) {
            await this.convertRowAmounts(row, fromCurrency, toCurrency);
        }
    }
    
    /**
     * 转换单行金额
     */
    async convertRowAmounts(row, fromCurrency, toCurrency) {
        const currencyFields = ['market_price', 'unit_price', 'total_price'];
        
        for (const fieldName of currencyFields) {
            const input = row.querySelector(`.${fieldName}-input`);
            if (!input) continue;
            
            const rawValue = parseFloat(input.dataset.rawValue || 0);
            if (rawValue === 0) continue;
            
            try {
                const convertedValue = await this.convertAmount(rawValue, fromCurrency, toCurrency);
                
                // 更新原始值和显示值
                input.dataset.rawValue = convertedValue.toString();
                input.value = this.formatCurrency(convertedValue);
                
                console.log(`💱 ${fieldName}: ${rawValue} ${fromCurrency} -> ${convertedValue} ${toCurrency}`);
                
            } catch (error) {
                console.error(`转换 ${fieldName} 失败:`, error);
            }
        }
    }
    
    /**
     * 货币转换
     */
    async convertAmount(amount, fromCurrency, toCurrency) {
        if (fromCurrency === toCurrency) {
            return parseFloat(amount);
        }
        
        try {
            // 尝试使用API转换
            const response = await fetch('/api/v1/exchange-rate/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
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
                    return result.data.converted_amount;
                }
            }
            
            throw new Error('API转换失败');
            
        } catch (error) {
            console.warn('API转换失败，使用本地转换:', error);
            return this.convertAmountLocally(amount, fromCurrency, toCurrency);
        }
    }
    
    /**
     * 本地货币转换
     */
    convertAmountLocally(amount, fromCurrency, toCurrency) {
        if (fromCurrency === toCurrency) {
            return parseFloat(amount);
        }
        
        const rates = this.exchangeRates;
        let convertedAmount = parseFloat(amount);
        
        // 先转换到基础货币（CNY）
        if (fromCurrency !== this.config.currencyConfig.baseCurrency) {
            const fromRate = rates[fromCurrency];
            if (!fromRate) {
                throw new Error(`不支持的源货币: ${fromCurrency}`);
            }
            convertedAmount = convertedAmount / fromRate;
        }
        
        // 再转换到目标货币
        if (toCurrency !== this.config.currencyConfig.baseCurrency) {
            const toRate = rates[toCurrency];
            if (!toRate) {
                throw new Error(`不支持的目标货币: ${toCurrency}`);
            }
            convertedAmount = convertedAmount * toRate;
        }
        
        return convertedAmount;
    }
    
    /**
     * 获取当前货币
     */
    getCurrentCurrency() {
        return this.currentCurrency;
    }
    
    /**
     * 设置货币（外部调用）
     */
    async setCurrency(currency) {
        const currencySelect = document.getElementById(this.config.currencySelectorId);
        if (currencySelect) {
            currencySelect.value = currency;
            await this.handleCurrencyChange(currency);
        }
    }
    
    /**
     * 获取行数据
     */
    getRowData(row) {
        const data = {};
        const mapping = this.config.fieldMapping;
        
        Object.keys(mapping).forEach(key => {
            data[key] = this.getFieldValue(row, mapping[key]);
        });
        
        // 检查是否为临时产品行
        if (row.dataset.isTemp === 'true' || row.dataset.manualInputMode === 'true') {
            data.is_temp = true;
            data.status = 'temp';
            data.temp_product_id = row.dataset.tempProductId || 'MANUAL';
            
            // 获取保存在DOM中的类别信息
            if (row.dataset.category) {
                data.category = row.dataset.category;
                console.log('🔧 从DOM获取类别信息:', data.category);
            }
            if (row.dataset.categoryPath) {
                data.category_path = row.dataset.categoryPath;
                console.log('🔧 从DOM获取类别路径:', data.category_path);
            }
            
            console.log('🔧 获取临时产品行数据:', data);
        }
        
        return data;
    }
    
    /**
     * 填充行数据
     */
    fillRowData(row, data) {
        console.log('🔧 填充行数据:', data);
        
        // 直接使用列键设置值，不使用字段映射
        Object.keys(data).forEach(key => {
            console.log(`🔧 设置字段 ${key} = ${data[key]}`);
            this.setFieldValueByKey(row, key, data[key]);
        });
        
        // 检查是否为临时产品并启用相应模式
        if (data.is_temp || data.temp_product_id || data.status === 'temp') {
            console.log('🔧 检测到临时产品，启用手动输入模式');
            
            // 创建临时产品对象
            const tempProduct = {
                is_temp: true,
                status: 'temp',
                product_name: data.product_name,
                product_model: data.product_model,
                product_desc: data.product_desc,
                brand: data.brand,
                unit: data.unit
            };
            
            // 启用手动输入模式
            this.enableManualInputMode(row, tempProduct);
            
            // 确保单价和小计正确显示
            if (data.unit_price) {
                this.setFieldValueByKey(row, 'unit_price', data.unit_price);
            }
            if (data.total_price) {
                this.setFieldValueByKey(row, 'total_price', data.total_price);
            }
            
            console.log('✅ 临时产品模式启用完成');
        }
        
        console.log('✅ 行数据填充完成');
    }
    
    /**
     * 获取所有行数据
     */
    getAllData() {
        const tbody = document.querySelector(`${this.config.tableSelector} tbody`);
        const rows = tbody.querySelectorAll('tr');
        const data = [];
        
        rows.forEach(row => {
            data.push(this.getRowData(row));
        });
        
        return data;
    }
    
    /**
     * 设置所有数据
     */
    setAllData(dataArray) {
        const tbody = document.querySelector(`${this.config.tableSelector} tbody`);
        
        // 清空现有行
        tbody.innerHTML = '';
        
        // 添加数据行
        if (dataArray && dataArray.length > 0) {
            dataArray.forEach(data => {
                this.addRow(data);
            });
        } else {
            // 添加空行
            this.addRow();
        }
        
        this.updateGrandTotal();
    }
    
    /**
     * 加载已有数据
     */
    loadExistingData() {
        // 从隐藏字段或data属性中加载数据
        const dataElement = document.querySelector('[data-product-details]');
        if (dataElement) {
            try {
                const data = JSON.parse(dataElement.dataset.productDetails);
                this.setAllData(data);
            } catch (e) {
                console.warn('Failed to load existing product details:', e);
                this.addRow(); // 添加空行
            }
        } else {
            this.addRow(); // 添加空行
        }
    }
    
    /**
     * 验证字段
     */
    validateField(fieldName, value) {
        const validator = this.config.validators[fieldName];
        if (validator && typeof validator === 'function') {
            const isValid = validator(parseFloat(value) || 0);
            console.log(`验证字段 ${fieldName} = ${value}, 结果:`, isValid);
            return isValid;
        }
        return true;
    }
    
    /**
     * 验证所有数据
     */
    validateAll() {
        const tbody = document.querySelector(`${this.config.tableSelector} tbody`);
        const rows = tbody.querySelectorAll('tr');
        const errors = [];
        
        rows.forEach((row, index) => {
            const rowData = this.getRowData(row);
            const rowErrors = this.validateRow(rowData, index);
            if (rowErrors.length > 0) {
                errors.push(...rowErrors);
            }
        });
        
        return errors;
    }
    
    /**
     * 验证单行数据
     */
    validateRow(rowData, rowIndex) {
        const errors = [];
        const tbody = document.querySelector(`${this.config.tableSelector} tbody`);
        const rows = tbody.querySelectorAll('tr');
        const row = rows[rowIndex];
        
        // 检查必填字段
        const required = this.config.columns.filter(col => col.required).map(col => col.key);
        required.forEach(field => {
            if (!rowData[field] || rowData[field].toString().trim() === '') {
                errors.push({
                    row: rowIndex,
                    field: field,
                    message: `第${rowIndex + 1}行的${this.getColumnLabel(field)}不能为空`
                });
            }
        });
        
        // 手动输入字段验证
        if (row) {
            const manualInputErrors = this.validateManualInputFields(row);
            manualInputErrors.forEach(error => {
                errors.push({
                    row: rowIndex,
                    field: error.field,
                    message: `第${rowIndex + 1}行：${error.message}`
                });
            });
        }
        
        // 自定义验证
        Object.keys(this.config.validators).forEach(field => {
            if (rowData[field] && !this.validateField(field, rowData[field])) {
                errors.push({
                    row: rowIndex,
                    field: field,
                    message: `第${rowIndex + 1}行的${this.getColumnLabel(field)}格式不正确`
                });
            }
        });
        
        return errors;
    }
    
    /**
     * 获取列标签
     */
    getColumnLabel(key) {
        const column = this.config.columns.find(col => col.key === key);
        return column ? column.label : key;
    }
    
    /**
     * 显示字段错误
     */
    showFieldError(field, message) {
        field.classList.add('is-invalid');
        
        // 移除已有错误提示
        const existingError = field.parentNode.querySelector('.invalid-feedback');
        if (existingError) {
            existingError.remove();
        }
        
        // 添加错误提示
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }
    
    /**
     * 清除字段错误
     */
    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
    
    /**
     * 显示原始值（编辑时）
     */
    showRawValue(input) {
        const rawValue = input.dataset.rawValue;
        if (rawValue !== undefined && rawValue !== '') {
            input.value = rawValue;
        }
    }
    
    /**
     * 显示格式化值（失焦时）
     */
    showFormattedValue(input) {
        // 更新原始值，货币字段需要移除千位分隔符
        if (input.value !== '') {
            if (input.classList.contains('currency-input')) {
                // 货币字段：移除千位分隔符后存储原始值
                input.dataset.rawValue = input.value.replace(/,/g, '');
            } else {
                // 普通字段：直接存储
                input.dataset.rawValue = input.value;
            }
        }
        
        const rawValue = input.dataset.rawValue;
        if (rawValue !== undefined && rawValue !== '') {
            if (input.classList.contains('currency-input')) {
                input.value = this.formatCurrency(rawValue);
            } else if (input.classList.contains('number-input')) {
                input.value = this.formatNumber(rawValue);
            }
        }
    }
    
    /**
     * 格式化货币
     */
    formatCurrency(amount) {
        const num = parseFloat(amount) || 0;
        return num.toLocaleString('zh-CN', {
            minimumFractionDigits: this.config.calculationRules.decimalPlaces,
            maximumFractionDigits: this.config.calculationRules.decimalPlaces
        });
    }
    
    /**
     * 格式化数字
     */
    formatNumber(number) {
        const num = parseFloat(number) || 0;
        return num.toLocaleString('zh-CN', {
            minimumFractionDigits: this.config.calculationRules.decimalPlaces,
            maximumFractionDigits: this.config.calculationRules.decimalPlaces
        });
    }
    
    /**
     * 显示错误
     */
    showError(message) {
        console.error('ProductDetailManager Error:', message);
        
        // 触发错误回调
        this.trigger('error', { message });
        
        // 可以在这里添加UI错误提示
        if (typeof window.showToast === 'function') {
            window.showToast('error', message);
        } else {
            alert(message);
        }
    }
    
    /**
     * 事件系统
     */
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }
    
    off(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }
    
    trigger(event, data = null) {
        // 执行配置中的回调
        const callback = this.config.callbacks[`on${event.charAt(0).toUpperCase()}${event.slice(1)}`];
        if (callback && typeof callback === 'function') {
            callback(data);
        }
        
        // 执行注册的事件处理器
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (e) {
                    console.error(`Error in event handler for ${event}:`, e);
                }
            });
        }
    }
    
    /**
     * 启用手动输入模式
     */
    enableManualInputMode(row, product) {
        console.log('🔧 启用手动输入模式:', product.product_model);
        
        // 获取手动输入配置
        const manualConfig = this.config.manual_input || {};
        const requiredFields = manualConfig.validation?.required_fields || [
            'product_model', 'product_desc', 'brand', 'unit'
        ];
        
        // 启用可编辑字段
        requiredFields.forEach(fieldKey => {
            const input = row.querySelector(`.${fieldKey}-input`);
            if (input) {
                input.readOnly = false;
                input.classList.add('manual-input-field');
                input.setAttribute('title', '手动输入字段，可以修改');
                console.log(`✅ 启用字段编辑: ${fieldKey}`);
            }
        });
        
        // 禁用市场价和折扣率
        const disabledFields = ['market_price', 'discount'];
        disabledFields.forEach(fieldKey => {
            const input = row.querySelector(`.${fieldKey}-input`);
            if (input) {
                input.readOnly = true;
                input.style.backgroundColor = '#f8f9fa';
                input.style.color = '#6c757d';
                input.setAttribute('title', '临时产品无市场价和折扣');
                console.log(`🔒 禁用字段: ${fieldKey}`);
            }
        });
        
        // 添加临时产品标识
        this.addTempProductIndicator(row, product);
        
        // 标记行为手动输入模式
        row.dataset.manualInputMode = 'true';
        row.dataset.isTemp = 'true';
        
        console.log('✅ 手动输入模式已启用');
    }
    
    /**
     * 禁用手动输入模式
     */
    disableManualInputMode(row) {
        console.log('🔧 禁用手动输入模式');
        
        // 恢复所有字段为只读状态（除了可编辑字段）
        const editableFields = ['quantity', 'unit_price'];
        
        row.querySelectorAll('input').forEach(input => {
            const fieldClass = input.className.split(' ').find(cls => cls.endsWith('-input'));
            const fieldKey = fieldClass ? fieldClass.replace('-input', '') : '';
            
            if (!editableFields.includes(fieldKey)) {
                input.readOnly = true;
                input.classList.remove('manual-input-field');
                input.style.backgroundColor = '';
                input.style.color = '';
                input.removeAttribute('title');
            }
        });
        
        // 恢复市场价和折扣率的正常状态
        const normalFields = ['market_price', 'discount'];
        normalFields.forEach(fieldKey => {
            const input = row.querySelector(`.${fieldKey}-input`);
            if (input) {
                // 根据列配置确定是否只读
                const columnConfig = this.config.columns.find(col => col.key === fieldKey);
                input.readOnly = columnConfig ? columnConfig.readonly : true;
                input.style.backgroundColor = '';
                input.style.color = '';
                input.removeAttribute('title');
            }
        });
        
        // 移除临时产品标识
        this.removeTempProductIndicator(row);
        
        // 清除手动输入模式标记
        row.removeAttribute('data-manual-input-mode');
        row.removeAttribute('data-is-temp');
        
        console.log('✅ 手动输入模式已禁用');
    }
    
    /**
     * 添加临时产品标识
     */
    addTempProductIndicator(row, product) {
        // 临时产品不显示标识，而是通过样式来区分
        // 为临时产品的可编辑字段添加橙色样式
        this.applyTempProductStyles(row);
        
        console.log('✅ 应用临时产品样式');
    }
    
    /**
     * 为临时产品应用橙色样式
     */
    applyTempProductStyles(row) {
        // 为临时产品的所有可编辑字段添加橙色样式
        const editableFields = ['product_model', 'product_desc', 'brand', 'unit', 'unit_price', 'quantity', 'discount'];
        
        editableFields.forEach(fieldKey => {
            const input = row.querySelector(`.${fieldKey}-input`);
            if (input && !input.readOnly) {
                input.classList.add('temp-product-editable');
                
                // 为单价字段添加变化监听器，自动保存价格更新
                if (fieldKey === 'unit_price') {
                    input.addEventListener('blur', () => {
                        this.handleTempProductPriceUpdate(row, input.value);
                    });
                }
                console.log(`🎨 为临时产品字段 ${fieldKey} 添加橙色样式`);
            }
        });
        
        // 移除任何行级别的临时产品样式
        row.classList.remove('temp-product-row');
        
        console.log('✅ 临时产品橙色样式应用完成');
    }
    
    /**
     * 处理临时产品价格更新
     */
    async handleTempProductPriceUpdate(row, newPrice) {
        if (!row.dataset.isTemp || !row.dataset.tempProductId) {
            return;
        }
        
        try {
            const tempProductId = row.dataset.tempProductId;
            
            // 首先获取现有的临时产品数据以保留类别信息
            const existingData = await this.getTempProductById(tempProductId);
            if (existingData) {
                console.log('🔧 获取到现有临时产品数据:', existingData);
                
                // 获取当前行的数据（可能包含用户的修改）
                const rowData = this.getRowData(row);
                
                // 合并数据：保留类别信息，更新其他字段
                const productData = {
                    product_name: rowData.productName || existingData.product_name,
                    product_model: rowData.productModel || existingData.product_model,
                    product_desc: rowData.productDesc || existingData.product_desc,
                    brand: rowData.brand || existingData.brand,
                    unit: rowData.unit || existingData.unit,
                    // 保留类别信息
                    category: existingData.category || '',
                    category_path: existingData.category_path || '',
                    // 添加价格信息
                    unit_price: parseFloat(newPrice) || 0,
                    reference_price: parseFloat(newPrice) || 0
                };
                
                console.log('🔧 准备保存的合并数据:', productData);
                
                // 调用产品选择器的保存方法
                if (this.productSelector && this.productSelector.saveTempProduct) {
                    await this.productSelector.saveTempProduct(productData);
                    console.log('✅ 临时产品价格已更新，类别已保留:', tempProductId, newPrice, productData.category);
                }
            } else {
                console.warn('🔥 无法获取现有临时产品数据，使用基础方法更新');
                
                // 降级处理：使用原来的方法
                const productData = this.getRowData(row);
                productData.unit_price = parseFloat(newPrice) || 0;
                productData.reference_price = parseFloat(newPrice) || 0;
                
                if (this.productSelector && this.productSelector.saveTempProduct) {
                    await this.productSelector.saveTempProduct(productData);
                    console.log('✅ 临时产品价格已更新（基础模式）:', tempProductId, newPrice);
                }
            }
        } catch (error) {
            console.warn('更新临时产品价格失败:', error);
        }
    }

    /**
     * 根据ID获取临时产品数据
     * @param {string} tempProductId - 临时产品ID
     * @returns {Promise<Object|null>} 临时产品数据
     */
    async getTempProductById(tempProductId) {
        try {
            const response = await fetch(`/api/v1/temp-products/${tempProductId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                console.warn(`获取临时产品数据失败: HTTP ${response.status}`);
                return null;
            }

            const result = await response.json();
            
            if (result.success && result.data) {
                return result.data;
            } else {
                console.warn('获取临时产品数据失败:', result.message);
                return null;
            }

        } catch (error) {
            console.error('获取临时产品数据出错:', error);
            return null;
        }
    }
    
    /**
     * 移除临时产品标识
     */
    removeTempProductIndicator(row) {
        // 移除临时产品的橙色样式
        const editableInputs = row.querySelectorAll('.temp-product-editable');
        editableInputs.forEach(input => {
            input.classList.remove('temp-product-editable');
        });
        
        // 移除旧的标识元素（如果存在）
        const indicators = row.querySelectorAll('.temp-product-indicator');
        indicators.forEach(indicator => {
            indicator.remove();
        });
    }
    
    /**
     * 检查行是否为手动输入模式
     */
    isManualInputMode(row) {
        return row.dataset.manualInputMode === 'true';
    }
    
    /**
     * 检查行是否为临时产品
     */
    isTempProduct(row) {
        return row.dataset.isTemp === 'true';
    }
    
    /**
     * 验证手动输入字段
     */
    validateManualInputFields(row) {
        if (!this.isManualInputMode(row)) {
            return [];
        }
        
        const errors = [];
        const manualConfig = this.config.manual_input || {};
        const requiredFields = manualConfig.validation?.required_fields || [
            'product_model', 'product_desc', 'brand', 'unit'
        ];
        
        requiredFields.forEach(fieldKey => {
            const input = row.querySelector(`.${fieldKey}-input`);
            if (input) {
                const value = input.value ? input.value.trim() : '';
                if (!value) {
                    const columnConfig = this.config.columns.find(col => col.key === fieldKey);
                    const fieldLabel = columnConfig ? columnConfig.label : fieldKey;
                    errors.push({
                        field: fieldKey,
                        message: `${fieldLabel}不能为空（手动输入字段）`
                    });
                }
            }
        });
        
        return errors;
    }
    
    /**
     * 处理临时产品的计算逻辑
     */
    calculateTempProductRow(row) {
        console.log('🔧 计算临时产品行');
        
        // 临时产品的计算逻辑
        const quantityInput = row.querySelector('.quantity-input');
        const unitPriceInput = row.querySelector('.unit_price-input');
        const totalPriceInput = row.querySelector('.total_price-input');
        
        const quantity = parseInt(quantityInput?.value || 1);
        const unitPrice = parseFloat(unitPriceInput?.dataset.rawValue || unitPriceInput?.value?.replace(/,/g, '') || 0);
        
        // 临时产品只计算：单价 × 数量 = 小计
        const totalPrice = unitPrice * quantity;
        
        // 更新小计
        if (totalPriceInput) {
            totalPriceInput.dataset.rawValue = totalPrice.toString();
            totalPriceInput.value = this.formatCurrency(totalPrice);
        }
        
        console.log(`🔧 临时产品计算: ${unitPrice} × ${quantity} = ${totalPrice}`);
        
        return { unitPrice, totalPrice };
    }
    
    /**
     * 扩展现有的calculateRow方法以支持临时产品
     */
    calculateRowExtended(row) {
        // 如果是临时产品，使用特殊计算逻辑
        if (this.isTempProduct(row)) {
            return this.calculateTempProductRow(row);
        }
        
        // 否则使用原有计算逻辑
        return this.calculateRow(row);
    }
    
    /**
     * 销毁组件
     */
    destroy() {
        this.eventHandlers.clear();
        if (this.productSelector) {
            this.productSelector.destroy();
        }
    }
}

// 导出到全局命名空间
window.ProductDetailManager = ProductDetailManager;