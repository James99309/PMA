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

        // 配置产品关系映射: {parentRowId: [configRowId1, configRowId2, ...]}
        this.rowConfigMap = new Map();
        this.rowIdCounter = 0;  // 行ID计数器

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
                currency: 'currency',
                // 配置产品字段（主次关系）
                parent_row_id: 'parent_row_id',
                is_configuration: 'is_configuration',
                config_type: 'config_type',
                config_base_quantity: 'config_base_quantity'
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

            // 取消级联按钮（波折图标点击）
            const linkIcon = target.closest('.config-link-icon');
            if (linkIcon && linkIcon.dataset.action === 'unlink') {
                e.preventDefault();
                e.stopPropagation();
                const rowId = linkIcon.dataset.rowId;
                if (rowId) {
                    this.unlinkConfiguration(rowId);
                }
                return;
            }

            // 删除行按钮（使用 closest 确保点击图标也能触发）
            const removeBtn = target.closest('.remove-row');
            if (removeBtn) {
                e.preventDefault();
                const row = removeBtn.closest('tr');
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

            // 处理数量同步复选框状态变化
            if (target.classList.contains('sync-quantity-checkbox')) {
                const quantityInput = row.querySelector('.quantity-input');
                if (!quantityInput) return;

                if (target.checked) {
                    // 勾选：同步主产品数量
                    row.dataset.quantitySynced = 'true';
                    quantityInput.readOnly = true;
                    quantityInput.style.backgroundColor = '';  // 恢复默认灰色背景

                    // 立即同步数量
                    const parentRowId = row.dataset.parentRowId;
                    if (parentRowId) {
                        const tbody = row.parentNode;
                        const parentRow = tbody.querySelector(`tr[data-row-id="${parentRowId}"]`);
                        if (parentRow) {
                            const configBaseQuantity = parseInt(row.dataset.configBaseQuantity) || 1;
                            const newQuantity = this.calculateConfigQuantity(parentRow, configBaseQuantity);
                            quantityInput.value = newQuantity;
                            quantityInput.dataset.rawValue = newQuantity;
                            this.calculateRow(row);
                            this.updateGrandTotal();
                        }
                    }
                } else {
                    // 取消勾选：允许独立编辑数量
                    row.dataset.quantitySynced = 'false';
                    quantityInput.readOnly = false;
                    quantityInput.style.backgroundColor = '#ffffff';  // 白色背景表示可编辑
                }
                return;
            }

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

        // 如果是主产品行的数量字段变化，更新其配置产品数量
        if (fieldName === 'quantity' && row.dataset.hasConfigurations === 'true') {
            console.log('🔄 主产品数量变化，更新配置产品数量');
            this.updateConfigurationQuantities(row);
        }

        // 如果是主产品行的折扣率字段变化，同步更新其配置产品折扣率
        if (fieldName === 'discount' && row.dataset.hasConfigurations === 'true') {
            console.log('🔄 主产品折扣率变化，同步配置产品折扣率');
            this.updateConfigurationDiscounts(row);
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
    handleProductSelect(productData, inputElement) {
        // 兼容性处理：支持多种数据格式
        // 格式1: { mainProduct: {...}, configurations: [...] }  - 旧版带配置格式
        // 格式2: { product_name: '...', configurations: [...] } - 新版扁平格式（product-selector.js）
        // 格式3: { product_name: '...' }                        - 单产品格式
        const hasMainProduct = productData && productData.mainProduct;
        const hasConfigurations = productData && Array.isArray(productData.configurations);
        const isProductItself = productData && productData.product_name;

        let product, configurations, dynamicSpecConfig, configurableSpecConfig;

        if (hasMainProduct) {
            // 格式1: 明确的 mainProduct 字段
            product = productData.mainProduct;
            configurations = productData.configurations || [];
            dynamicSpecConfig = productData.dynamicSpecConfig || null;
            configurableSpecConfig = productData.configurableSpecConfig || null;
        } else if (isProductItself) {
            // 格式2/3: productData 本身就是产品对象
            product = productData;
            configurations = productData.configurations || [];
            dynamicSpecConfig = productData.dynamicSpecConfig || null;
            configurableSpecConfig = productData.configurableSpecConfig || null;
        } else {
            // 未知格式，尝试直接使用
            product = productData;
            configurations = [];
            dynamicSpecConfig = null;
            configurableSpecConfig = null;
        }

        console.log('🔄 处理产品选择:', product.product_name);
        if (configurations.length > 0) {
            console.log(`📦 包含 ${configurations.length} 个配置产品`);
        }
        if (dynamicSpecConfig) {
            console.log(`🔧 包含动态规格配置: ${dynamicSpecConfig.original_mn} → ${dynamicSpecConfig.configured_mn}`);
        }
        if (configurableSpecConfig && configurableSpecConfig.price_adjustment_total) {
            console.log(`💰 可配置字段价格增量: +¥${(configurableSpecConfig.price_adjustment_total / 100).toFixed(2)}`);
        }

        const row = inputElement.closest('tr');

        // 生成行ID（用于跟踪父子关系）
        const rowId = this.generateRowId();
        row.dataset.rowId = rowId;

        // 填充主产品数据
        this.fillProductData(row, product);

        // 处理动态规格配置（如果有）
        if (dynamicSpecConfig) {
            this.applyDynamicSpecConfig(row, dynamicSpecConfig);
        }

        // 处理可配置字段价格增量（如果有配置数据或spec_mn变化）
        // 注意：即使 price_adjustment_total 为0，如果有 spec_mn 变化也需要处理
        if (configurableSpecConfig && (configurableSpecConfig.price_adjustment_total || configurableSpecConfig.spec_mn)) {
            // 补充原产品ID（用于创建研发产品时追溯）
            configurableSpecConfig.original_product_id = product.id;
            console.log('🔧 [DEBUG] 处理可配置字段配置:', configurableSpecConfig);
            this.applyConfigurableSpecPriceAdjustment(row, configurableSpecConfig);
        } else {
            console.log('🔧 [DEBUG] 无可配置字段配置或配置为空:', configurableSpecConfig);
        }

        // 处理手动输入模式的字段状态
        if (product.is_temp || product.status === 'temp') {
            this.enableManualInputMode(row, product);
        } else {
            this.disableManualInputMode(row);
        }

        // 重新计算主产品行
        this.calculateRow(row);

        // 处理配置产品
        if (configurations.length > 0) {
            const configRowIds = [];
            const tbody = row.parentNode;
            let rowIndex = Array.from(tbody.children).indexOf(row);
            let insertOffset = 0;

            // 递归添加配置（包含嵌套配置）
            const addConfigRecursively = (config) => {
                const configRow = this.addConfigurationRow(config, rowId, row);
                configRowIds.push(configRow.dataset.rowId);

                // 插入到主产品行之后
                const insertIndex = rowIndex + 1 + insertOffset;
                if (insertIndex < tbody.children.length) {
                    tbody.insertBefore(configRow, tbody.children[insertIndex]);
                } else {
                    tbody.appendChild(configRow);
                }
                insertOffset++;

                // 如果有嵌套配置，递归添加
                if (config.nested_configs && config.nested_configs.length > 0) {
                    console.log(`  📦 配置 "${config.product_name}" 包含 ${config.nested_configs.length} 个子配置`);
                    config.nested_configs.forEach(nestedConfig => {
                        addConfigRecursively(nestedConfig);
                    });
                }
            };

            configurations.forEach(config => {
                addConfigRecursively(config);
            });

            // 记录父子关系
            this.rowConfigMap.set(rowId, configRowIds);

            // 标记主产品行有配置
            row.dataset.hasConfigurations = 'true';
        }

        this.updateGrandTotal();

        // 确保产品选择器菜单被关闭
        if (this.productSelector) {
            this.productSelector.hideMenu();
            console.log('🔧 手动关闭产品选择器菜单');
        }

        // 触发回调
        this.trigger('productSelect', { product, row, configurations });

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

        // ⚠️ 货币转换：产品价格需要根据当前货币进行转换
        const productCurrency = product.currency || 'CNY'; // 产品原始货币（数据库中产品默认为CNY）
        let marketPrice = product.retail_price || product.market_price || 0;

        // 如果当前货币与产品货币不同，需要转换
        if (this.currentCurrency && this.currentCurrency !== productCurrency) {
            console.log(`💱 货币转换: ${marketPrice} ${productCurrency} -> ${this.currentCurrency}`);
            const convertedPrice = this.convertAmountLocally(marketPrice, productCurrency, this.currentCurrency);
            marketPrice = convertedPrice;
            console.log(`💱 转换后市场价: ${marketPrice}`);
        }

        this.setFieldValueByKey(row, 'market_price', marketPrice);
        this.setFieldValueByKey(row, 'product_mn', product.product_mn || '');

        // 设置默认值
        this.setFieldValueByKey(row, 'quantity', 1);
        this.setFieldValueByKey(row, 'discount', 100);

        // 初始化单价为市场价（100%折扣）- 使用转换后的价格
        const initialUnitPrice = marketPrice;
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

        // ✅ 从数据中判断是否是配置产品
        const isConfiguration = data && (
            data.is_configuration === true ||
            data.is_configuration === 'true'
        );

        const row = this.createRow(data, isConfiguration);

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
     * @param {*} data - 行数据
     * @param {boolean} isConfiguration - 是否是配置产品行
     */
    createRow(data = null, isConfiguration = false) {
        const row = document.createElement('tr');

        this.config.columns.forEach(column => {
            const td = document.createElement('td');
            const input = this.createField(column, data, isConfiguration);

            if (input) {
                td.appendChild(input);
            }
            row.appendChild(td);
        });

        return row;
    }
    
    /**
     * 创建字段元素
     * @param {Object} column - 列配置
     * @param {*} data - 数据
     * @param {boolean} isConfiguration - 是否是配置产品行
     */
    createField(column, data = null, isConfiguration = false) {
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
                return this.createActionsField(isConfiguration);
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
        input.placeholder = this.config.i18n?.clickToSelectProduct || '点击选择产品...';
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
     * @param {boolean} isConfiguration - 是否是配置产品行
     */
    createActionsField(isConfiguration = false) {
        const container = document.createElement('div');
        container.className = isConfiguration
            ? 'text-center d-flex flex-row align-items-center justify-content-center gap-2'
            : 'text-center';

        // 配置产品行添加同步数量复选框
        if (isConfiguration) {
            const syncCheckbox = document.createElement('input');
            syncCheckbox.type = 'checkbox';
            syncCheckbox.className = 'form-check-input sync-quantity-checkbox';
            syncCheckbox.checked = true;
            syncCheckbox.title = '同步主产品数量';
            syncCheckbox.style.cursor = 'pointer';
            container.appendChild(syncCheckbox);
        }

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-sm btn-outline-danger remove-row';
        removeBtn.innerHTML = '<i class="fas fa-trash"></i>';
        removeBtn.title = this.config.i18n?.deleteRow || '删除行';

        container.appendChild(removeBtn);
        return container;
    }
    
    /**
     * 生成唯一行ID
     */
    generateRowId() {
        return `row_${++this.rowIdCounter}_${Date.now()}`;
    }

    /**
     * 添加配置产品行
     * @param {Object} config - 配置产品数据
     * @param {string} parentRowId - 父产品行ID
     * @param {HTMLElement} parentRow - 父产品行元素
     * @returns {HTMLElement} 配置产品行
     */
    addConfigurationRow(config, parentRowId, parentRow) {
        console.log(`📦 添加配置产品行: ${config.product_name}`);

        // 创建新行（传入true表示这是配置产品行）
        const configRow = this.createRow(null, true);

        // 生成配置行ID
        const configRowId = this.generateRowId();
        configRow.dataset.rowId = configRowId;
        configRow.dataset.parentRowId = parentRowId;
        configRow.dataset.isConfiguration = 'true';
        configRow.dataset.configType = config.relation_type || 'required_accessory';
        configRow.dataset.configBaseQuantity = config.default_quantity || 1;
        configRow.dataset.quantitySynced = 'true';  // 默认同步数量

        // 添加波折符号 DOM 元素到第一列（可点击取消级联）
        const firstTd = configRow.querySelector('td:first-child');
        if (firstTd) {
            const linkIcon = document.createElement('span');
            linkIcon.className = 'config-link-icon';
            linkIcon.dataset.action = 'unlink';
            linkIcon.dataset.rowId = configRowId;
            linkIcon.title = '点击取消关联';
            linkIcon.innerHTML = '<span class="link-normal">└─</span><span class="link-unlink">✕─</span>';
            firstTd.insertBefore(linkIcon, firstTd.firstChild);
        }

        // 填充配置产品数据
        this.fillProductData(configRow, config);

        // 计算配置产品数量
        const quantity = this.calculateConfigQuantity(parentRow, config.default_quantity || 1);

        // 设置数量
        const quantityInput = configRow.querySelector('.quantity-input');
        if (quantityInput) {
            quantityInput.value = quantity;
            quantityInput.readOnly = true;  // 配置产品数量只读
        }

        // 重新计算
        this.calculateRow(configRow);

        console.log(`✅ 配置产品行创建完成: ${config.product_name}, 数量=${quantity}`);

        return configRow;
    }

    /**
     * 计算配置产品数量
     * @param {HTMLElement} parentRow - 父产品行
     * @param {number} configBaseQuantity - 配置基础数量
     * @returns {number} 计算后的数量
     */
    calculateConfigQuantity(parentRow, configBaseQuantity) {
        const quantityInput = parentRow.querySelector('.quantity-input');
        const parentQuantity = quantityInput ? parseInt(quantityInput.value) || 1 : 1;
        return parentQuantity * (configBaseQuantity || 1);
    }

    /**
     * 更新配置产品数量（当主产品数量改变时调用）
     * @param {HTMLElement} parentRow - 父产品行
     */
    updateConfigurationQuantities(parentRow) {
        const rowId = parentRow.dataset.rowId;
        if (!rowId) return;

        const configRowIds = this.rowConfigMap.get(rowId);
        if (!configRowIds || configRowIds.length === 0) return;

        console.log(`🔄 更新配置产品数量，主产品行ID: ${rowId}`);

        const tbody = parentRow.parentNode;

        configRowIds.forEach(configRowId => {
            const configRow = tbody.querySelector(`tr[data-row-id="${configRowId}"]`);
            if (!configRow) return;

            // 检查是否需要同步数量（复选框未勾选时跳过）
            if (configRow.dataset.quantitySynced === 'false') {
                console.log(`  - 配置产品 ${configRowId}: 跳过数量同步（用户已取消同步）`);
                return;
            }

            const configBaseQuantity = parseInt(configRow.dataset.configBaseQuantity) || 1;
            const newQuantity = this.calculateConfigQuantity(parentRow, configBaseQuantity);

            const quantityInput = configRow.querySelector('.quantity-input');
            if (quantityInput) {
                quantityInput.value = newQuantity;
                quantityInput.dataset.rawValue = newQuantity;  // 同步更新rawValue，确保数据收集时能读取到最新值
                this.calculateRow(configRow);
                console.log(`  - 配置产品 ${configRowId}: 数量更新为 ${newQuantity}`);
            }
        });

        this.updateGrandTotal();
    }

    /**
     * 更新配置产品折扣率（当主产品折扣率改变时调用）
     * @param {HTMLElement} parentRow - 父产品行
     */
    updateConfigurationDiscounts(parentRow) {
        const rowId = parentRow.dataset.rowId;
        if (!rowId) return;

        const configRowIds = this.rowConfigMap.get(rowId);
        if (!configRowIds || configRowIds.length === 0) return;

        console.log(`💰 更新配置产品折扣率，主产品行ID: ${rowId}`);

        const tbody = parentRow.parentNode;

        // 获取主产品的折扣率
        const parentDiscountInput = parentRow.querySelector('.discount-input');
        if (!parentDiscountInput) return;

        const parentDiscount = parseFloat(parentDiscountInput.dataset.rawValue || parentDiscountInput.value || 100);
        console.log(`  主产品折扣率: ${parentDiscount}%`);

        configRowIds.forEach(configRowId => {
            const configRow = tbody.querySelector(`tr[data-row-id="${configRowId}"]`);
            if (!configRow) return;

            const discountInput = configRow.querySelector('.discount-input');
            if (discountInput) {
                // 更新折扣率值
                discountInput.value = parentDiscount;
                discountInput.dataset.rawValue = parentDiscount;

                // 重新计算该行
                this.calculateRow(configRow);
                console.log(`  - 配置产品 ${configRowId}: 折扣率更新为 ${parentDiscount}%`);
            }
        });

        this.updateGrandTotal();
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

        const rowId = row.dataset.rowId;
        const isConfiguration = row.dataset.isConfiguration === 'true';
        const parentRowId = row.dataset.parentRowId;

        // 如果是主产品行，级联删除其所有配置产品行
        if (!isConfiguration && rowId) {
            const configRowIds = this.rowConfigMap.get(rowId);
            if (configRowIds && configRowIds.length > 0) {
                console.log(`🗑️ 级联删除 ${configRowIds.length} 个配置产品行`);
                configRowIds.forEach(configRowId => {
                    const configRow = tbody.querySelector(`tr[data-row-id="${configRowId}"]`);
                    if (configRow) {
                        tbody.removeChild(configRow);
                        console.log(`  - 已删除配置行: ${configRowId}`);
                    }
                });
                this.rowConfigMap.delete(rowId);
            }
        }

        // 如果是配置产品行，从父产品的配置列表中移除
        if (isConfiguration && parentRowId && rowId) {
            console.log(`🗑️ 删除配置产品行: ${rowId}，父产品: ${parentRowId}`);

            const configRowIds = this.rowConfigMap.get(parentRowId);
            if (configRowIds) {
                // 从配置列表中移除当前行ID
                const index = configRowIds.indexOf(rowId);
                if (index > -1) {
                    configRowIds.splice(index, 1);
                    console.log(`  - 已从父产品配置列表中移除`);
                }

                // 如果父产品已没有配置产品，清理映射并取消标记
                if (configRowIds.length === 0) {
                    this.rowConfigMap.delete(parentRowId);

                    // 取消父产品的 hasConfigurations 标记
                    const parentRow = tbody.querySelector(`tr[data-row-id="${parentRowId}"]`);
                    if (parentRow) {
                        parentRow.dataset.hasConfigurations = 'false';
                        console.log(`  - 父产品已无配置，取消 hasConfigurations 标记`);
                    }
                } else {
                    console.log(`  - 父产品还有 ${configRowIds.length} 个配置产品`);
                }
            }
        }

        // 删除当前行
        tbody.removeChild(row);
        this.updateGrandTotal();

        // 触发回调
        this.trigger('rowRemove', { row });
    }

    /**
     * 取消配置产品的级联关联
     * 将配置产品行转换为独立的普通产品行
     * @param {string} configRowId - 配置产品行ID
     */
    unlinkConfiguration(configRowId) {
        const tbody = document.querySelector(`${this.config.tableSelector} tbody`);
        const configRow = tbody.querySelector(`tr[data-row-id="${configRowId}"]`);

        if (!configRow) {
            console.warn(`❌ 未找到配置行: ${configRowId}`);
            return;
        }

        const parentRowId = configRow.dataset.parentRowId;
        console.log(`🔗 取消级联关联: 配置行 ${configRowId}, 父行 ${parentRowId}`);

        // 1. 找到父产品配置组的最后一个配置行，将当前行移动到其后面
        if (parentRowId) {
            let lastConfigRow = null;
            let sibling = tbody.querySelector(`tr[data-row-id="${parentRowId}"]`);

            // 遍历找到该父产品的最后一个配置行
            while (sibling) {
                sibling = sibling.nextElementSibling;
                if (sibling && sibling.dataset.parentRowId === parentRowId) {
                    lastConfigRow = sibling;
                } else if (sibling && sibling.dataset.parentRowId !== parentRowId) {
                    break;
                }
            }

            // 如果找到了最后一个配置行，且不是当前行自己，则移动
            if (lastConfigRow && lastConfigRow !== configRow) {
                lastConfigRow.insertAdjacentElement('afterend', configRow);
                console.log(`  ↪ 行已移动到配置组之后`);
            }
        }

        // 2. 从 rowConfigMap 中移除
        if (parentRowId) {
            const configRowIds = this.rowConfigMap.get(parentRowId);
            if (configRowIds) {
                const index = configRowIds.indexOf(configRowId);
                if (index > -1) {
                    configRowIds.splice(index, 1);
                    console.log(`  - 已从父产品配置列表中移除`);
                }

                // 如果父产品已没有配置产品，清理映射并取消标记
                if (configRowIds.length === 0) {
                    this.rowConfigMap.delete(parentRowId);
                    const parentRow = tbody.querySelector(`tr[data-row-id="${parentRowId}"]`);
                    if (parentRow) {
                        parentRow.dataset.hasConfigurations = 'false';
                        console.log(`  - 父产品已无配置，取消 hasConfigurations 标记`);
                    }
                }
            }
        }

        // 3. 清除配置行的父子关系属性
        delete configRow.dataset.parentRowId;
        delete configRow.dataset.isConfiguration;
        delete configRow.dataset.configType;
        delete configRow.dataset.configBaseQuantity;
        delete configRow.dataset.quantitySynced;

        // 4. 移除波折图标
        const linkIcon = configRow.querySelector('.config-link-icon');
        if (linkIcon) {
            linkIcon.remove();
        }

        // 5. 恢复数量字段的编辑状态
        const quantityInput = configRow.querySelector('.quantity-input');
        if (quantityInput) {
            quantityInput.readOnly = false;
            quantityInput.style.backgroundColor = '';
            quantityInput.style.cursor = '';
        }

        // 6. 触发回调
        this.trigger('configurationUnlinked', { rowId: configRowId, parentRowId });

        console.log(`✅ 配置行 ${configRowId} 已转换为独立行`);
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

        // 如果是主产品行，同步更新其配置产品折扣率
        if (row.dataset.hasConfigurations === 'true') {
            console.log('🔄 反向计算后，同步配置产品折扣率');
            this.updateConfigurationDiscounts(row);
        }

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
            // 使用国际化的货币名称，如果可用的话
            const i18nName = (window.CURRENCY_I18N && window.CURRENCY_I18N[currency.code]) 
                ? window.CURRENCY_I18N[currency.code] 
                : currency.name;
            option.textContent = `${i18nName} (${currency.code})`;
            
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

        // 从 dataset 中读取配置产品字段（主次关系）
        if (row.dataset.isConfiguration === 'true') {
            data.is_configuration = true;
            data.parent_row_id = row.dataset.parentRowId || null;
            data.config_type = row.dataset.configType || null;
            data.config_base_quantity = row.dataset.configBaseQuantity ? parseInt(row.dataset.configBaseQuantity) : null;

            // ✅ 收集同步状态（默认为 true）
            data.quantity_synced = row.dataset.quantitySynced !== 'false';

            console.log('📦 收集配置产品数据:', {
                is_configuration: data.is_configuration,
                parent_row_id: data.parent_row_id,
                config_type: data.config_type,
                config_base_quantity: data.config_base_quantity,
                quantity_synced: data.quantity_synced
            });
        }

        // 从 dataset 中读取行ID（用于建立父子关系）
        if (row.dataset.rowId) {
            data.row_id = row.dataset.rowId;

            // 调试日志：显示主产品的 row_id
            if (!data.is_configuration) {
                console.log('🔑 主产品 row_id:', {
                    product_name: data.product_name,
                    row_id: data.row_id
                });
            }
        }

        // 收集动态规格配置数据（如果有）
        const specConfig = this.getDynamicSpecConfig(row);
        // 🔍 调试：检查 dataset 属性
        console.log('🔍 [DEBUG] getRowData - row.dataset:', {
            configuredSpecs: row.dataset.configuredSpecs,
            configuredMn: row.dataset.configuredMn,
            pendingProductCreation: row.dataset.pendingProductCreation
        });
        console.log('🔍 [DEBUG] getRowData - specConfig:', specConfig);

        if (specConfig) {
            data.configured_specs = specConfig.configured_specs;
            data.configured_mn = specConfig.configured_mn;
            data.price_adjustment_total = specConfig.price_adjustment_total;
            data.pending_product_creation = specConfig.pending_product_creation;

            console.log('🔧 收集动态规格配置:', {
                configured_mn: data.configured_mn,
                price_adjustment: data.price_adjustment_total,
                pending_creation: data.pending_product_creation
            });
        } else {
            console.log('🔍 [DEBUG] getRowData - 没有动态规格配置');
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

        // ✅ 恢复配置产品的同步状态
        if (data.is_configuration === true || data.is_configuration === 'true') {
            // 从数据中读取同步状态，支持布尔值和字符串
            const quantitySynced = data.quantity_synced === true ||
                                   data.quantity_synced === 'true';

            // 设置 dataset
            row.dataset.quantitySynced = quantitySynced ? 'true' : 'false';

            // 更新复选框状态
            const syncCheckbox = row.querySelector('.sync-quantity-checkbox');
            if (syncCheckbox) {
                syncCheckbox.checked = quantitySynced;
                console.log(`🔧 恢复复选框状态: ${quantitySynced}`);
            }

            // 同步数量输入框的只读状态和背景色
            const quantityInput = row.querySelector('.quantity-input');
            if (quantityInput) {
                quantityInput.readOnly = quantitySynced;
                quantityInput.style.backgroundColor = quantitySynced ? '' : '#ffffff';
                console.log(`🔧 恢复数量输入框状态: readOnly=${quantitySynced}`);
            }
        }

        // ✅ 恢复动态规格配置（编辑时保持配置数据）
        // 🔍 调试：打印配置数据检查
        console.log('🔍 [DEBUG] 检查动态规格配置数据:');
        console.log('🔍 [DEBUG]   configured_specs:', data.configured_specs, typeof data.configured_specs);
        console.log('🔍 [DEBUG]   configured_mn:', data.configured_mn, typeof data.configured_mn);
        console.log('🔍 [DEBUG]   pending_product_creation:', data.pending_product_creation, typeof data.pending_product_creation);

        if (data.configured_specs && data.configured_mn) {
            console.log('🔧 恢复动态规格配置:', data.configured_mn);
            const specConfig = {
                original_product_id: data.original_product_id,
                original_mn: data.original_mn,
                configured_mn: data.configured_mn,
                spec_config: typeof data.configured_specs === 'string'
                    ? JSON.parse(data.configured_specs)
                    : data.configured_specs,
                price_adjustment_total: data.price_adjustment_total || 0,
                is_new_product: data.pending_product_creation === true || data.pending_product_creation === 'true'
            };
            this.applyDynamicSpecConfig(row, specConfig);
            console.log('✅ 动态规格配置恢复完成, specConfig:', specConfig);
        } else {
            console.log('🔍 [DEBUG] 没有动态规格配置数据需要恢复');
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

            // 重建配置产品的主次关系
            this.rebuildConfigurationRelationships(dataArray);

            // 重新排列DOM顺序，将配置产品移动到父产品后面
            this.reorderConfigurationRows();
        } else {
            // 添加空行
            this.addRow();
        }

        this.updateGrandTotal();
    }

    /**
     * 重建配置产品的主次关系（编辑页面加载时）
     * @param {Array} dataArray - 产品明细数据数组
     */
    rebuildConfigurationRelationships(dataArray) {
        const tbody = document.querySelector(`${this.config.tableSelector} tbody`);
        const rows = tbody.querySelectorAll('tr');

        if (!rows || rows.length === 0) return;

        console.log('🔄 ========== 开始重建配置产品主次关系 ==========');
        console.log(`📊 基本信息:`);
        console.log(`   - 数据数组长度: ${dataArray.length}`);
        console.log(`   - 表格行数: ${rows.length}`);
        console.log(`\n📋 原始数据详情:`);

        dataArray.forEach((data, index) => {
            console.log(`   [${index}] {
      item_id: ${data.item_id || 'undefined'},
      id: ${data.id || 'undefined'},
      product_name: "${data.product_name}",
      is_configuration: ${data.is_configuration},
      parent_item_id: ${data.parent_item_id || 'null'}
    }`);
        });

        // 第一步：为所有行设置 rowId（如果还没有）并建立映射
        const itemIdToRowMap = new Map();
        const itemIdToRowIdMap = new Map();

        console.log(`\n🔨 第一步：构建映射表`);

        dataArray.forEach((data, index) => {
            if (index < rows.length) {
                const row = rows[index];

                // 🔧 关键修复：确保每行都有 rowId
                if (!row.dataset.rowId) {
                    if (data.item_id) {
                        // 使用数据库ID生成稳定的 rowId
                        row.dataset.rowId = `row_db_${data.item_id}`;
                    } else {
                        // 如果没有item_id，生成临时ID
                        row.dataset.rowId = `row_temp_${Date.now()}_${index}`;
                    }
                    console.log(`   ✓ 为第 ${index + 1} 行设置 rowId: ${row.dataset.rowId}`);
                }

                const rowId = row.dataset.rowId;
                // 修复：统一使用字符串类型作为 Map 的键，避免类型不匹配问题
                const itemId = String(data.item_id || data.id || index);

                // 🆕 检测重复的 item_id
                if (itemIdToRowMap.has(itemId)) {
                    console.warn(`   ⚠️ 警告：item_id=${itemId} 已存在于映射表中！`);
                    const existingRow = itemIdToRowMap.get(itemId);
                    const existingIndex = Array.from(rows).indexOf(existingRow);
                    console.warn(`      已有映射: item_id=${itemId} → row[${existingIndex}]`);
                    console.warn(`      新数据: item_id=${itemId} → row[${index}] (将覆盖)`);
                    console.warn(`      这会导致配置产品关联错误！`);
                }

                itemIdToRowMap.set(itemId, row);
                itemIdToRowIdMap.set(itemId, rowId);

                console.log(`   [${index}] 映射: item_id=${itemId} → row[${index}] (rowId=${rowId})`);
            }
        });

        // 🆕 映射表完整性检查
        console.log(`\n📊 映射表构建完成:`);
        console.log(`   - itemIdToRowMap 大小: ${itemIdToRowMap.size}`);
        console.log(`   - 数据数组长度: ${dataArray.length}`);

        if (itemIdToRowMap.size < dataArray.length) {
            console.error(`   ❌ 映射表大小 < 数据数组长度，存在重复的 item_id！`);
            console.error(`      丢失的条目数: ${dataArray.length - itemIdToRowMap.size}`);
        } else {
            console.log(`   ✅ 映射表完整，无重复键`);
        }

        console.log(`\n🔍 映射表内容:`);
        itemIdToRowMap.forEach((row, itemId) => {
            const index = Array.from(rows).indexOf(row);
            const data = dataArray[index];
            console.log(`   item_id=${itemId} → row[${index}] "${data?.product_name}"`);
        });

        // 第二步：为配置产品设置 parent_row_id 并恢复主次关系
        console.log(`\n🔗 第二步：关联配置产品到父产品`);

        let successCount = 0;
        let failCount = 0;

        dataArray.forEach((data, index) => {
            // 修复：正确处理字符串类型的 is_configuration（'false' 也是 truthy 值）
            const isConfig = data.is_configuration === true || data.is_configuration === 'true';
            if (index < rows.length && isConfig && data.parent_item_id) {
                const row = rows[index];

                console.log(`   [${index}] 处理配置产品: "${data.product_name}"`);
                console.log(`      - parent_item_id: ${data.parent_item_id}`);

                // 修复：查找时也使用字符串类型，确保与 Map 键类型一致
                const parentItemIdStr = String(data.parent_item_id);
                console.log(`      - 查找映射表: itemIdToRowMap.has("${parentItemIdStr}") = ${itemIdToRowMap.has(parentItemIdStr)}`);

                const parentRow = itemIdToRowMap.get(parentItemIdStr);
                const parentRowId = itemIdToRowIdMap.get(parentItemIdStr);

                if (parentRow && parentRowId) {
                    const parentIndex = Array.from(rows).indexOf(parentRow);
                    const parentData = dataArray[parentIndex];

                    console.log(`      ✅ 找到父产品: row[${parentIndex}] "${parentData?.product_name}"`);
                    console.log(`         parent_row_id: ${parentRowId}`);

                    // 设置配置产品的 dataset 属性
                    row.dataset.isConfiguration = 'true';
                    row.dataset.parentRowId = parentRowId;
                    row.dataset.configType = data.config_type || '';
                    row.dataset.configBaseQuantity = data.config_base_quantity || 1;

                    // 标记父产品有配置
                    parentRow.dataset.hasConfigurations = 'true';

                    // 添加到 rowConfigMap
                    const parentRowIdKey = parentRowId;
                    if (!this.rowConfigMap.has(parentRowIdKey)) {
                        this.rowConfigMap.set(parentRowIdKey, []);
                    }
                    this.rowConfigMap.get(parentRowIdKey).push(row.dataset.rowId);

                    successCount++;
                } else {
                    console.error(`      ❌ 找不到父产品！`);
                    console.error(`         parent_item_id=${data.parent_item_id}`);
                    console.error(`         itemIdToRowMap 中的所有键: [${Array.from(itemIdToRowMap.keys()).join(', ')}]`);
                    failCount++;
                }
            }
        });

        console.log(`\n✅ 配置产品主次关系重建完成`);
        console.log(`   - 成功关联: ${successCount} 个`);
        console.log(`   - 关联失败: ${failCount} 个`);
        console.log(`\n📋 最终 rowConfigMap:`, this.rowConfigMap);
        console.log('========== 重建完成 ==========\n');
    }

    /**
     * 重新排列配置产品的DOM顺序
     * 将配置产品行移动到其父产品行之后
     */
    reorderConfigurationRows() {
        const tbody = document.querySelector(`${this.config.tableSelector} tbody`);
        if (!tbody) {
            console.warn('⚠️ 未找到表格tbody，无法重排DOM顺序');
            return;
        }

        console.log('🔄 ========== 开始重新排列配置产品DOM顺序 ==========');
        console.log(`📊 rowConfigMap 大小: ${this.rowConfigMap.size}`);

        let totalMoved = 0;

        // 遍历所有父产品及其配置产品
        this.rowConfigMap.forEach((configRowIds, parentRowId) => {
            const parentRow = tbody.querySelector(`tr[data-row-id="${parentRowId}"]`);
            if (!parentRow) {
                console.warn(`   ⚠️ 未找到父产品行: ${parentRowId}`);
                return;
            }

            const parentIndex = Array.from(tbody.children).indexOf(parentRow);
            console.log(`\n   处理父产品 [row ${parentIndex}] ${parentRowId}:`);
            console.log(`      配置产品数量: ${configRowIds.length}`);

            // 将每个配置产品行移动到父产品行之后
            let insertAfter = parentRow;
            configRowIds.forEach((configRowId, index) => {
                const configRow = tbody.querySelector(`tr[data-row-id="${configRowId}"]`);
                if (!configRow) {
                    console.warn(`      ⚠️ 未找到配置产品行: ${configRowId}`);
                    return;
                }

                const currentIndex = Array.from(tbody.children).indexOf(configRow);
                const expectedPosition = insertAfter.nextElementSibling;

                // 检查是否需要移动
                if (configRow !== expectedPosition) {
                    // 将配置行插入到正确位置
                    tbody.insertBefore(configRow, expectedPosition);
                    const newIndex = Array.from(tbody.children).indexOf(configRow);
                    console.log(`      ✓ [${index + 1}/${configRowIds.length}] 移动 ${configRowId}: row[${currentIndex}] → row[${newIndex}]`);
                    totalMoved++;
                } else {
                    console.log(`      ○ [${index + 1}/${configRowIds.length}] ${configRowId} 已在正确位置`);
                }

                insertAfter = configRow;
            });
        });

        console.log(`\n✅ DOM顺序重排完成`);
        console.log(`   - 总共移动: ${totalMoved} 行`);
        console.log('========== 重排完成 ==========\n');
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
                    message: `${this.config.i18n?.rowPrefix || '第'}${rowIndex + 1}${this.config.i18n?.rowSuffix || '行的'}${this.getColumnLabel(field)}${this.config.i18n?.cannotBeEmpty || '不能为空'}`
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
                    message: `${this.config.i18n?.rowPrefix || '第'}${rowIndex + 1}${this.config.i18n?.rowSuffix || '行'}：${error.message}`
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
                input.setAttribute('title', this.config.i18n?.manualInputField || '手动输入字段，可以修改');
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
                input.setAttribute('title', this.config.i18n?.tempProductNoPrice || '临时产品无市场价和折扣');
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

    // ============== 动态规格配置功能 ==============

    /**
     * 应用动态规格配置到行
     * @param {HTMLElement} row - 表格行元素
     * @param {Object} config - 动态规格配置数据
     */
    applyDynamicSpecConfig(row, config) {
        console.log('🔧 应用动态规格配置到行:', config);

        // 存储配置数据到行的dataset中（JSON字符串）
        row.dataset.configuredSpecs = JSON.stringify(config.spec_config);
        row.dataset.configuredMn = config.configured_mn;
        row.dataset.originalMn = config.original_mn;
        row.dataset.priceAdjustmentTotal = config.price_adjustment_total;
        row.dataset.pendingProductCreation = config.is_new_product ? 'true' : 'false';
        row.dataset.originalProductId = config.original_product_id;

        // 如果是新MN（需要创建新产品），更新行显示
        if (config.is_new_product) {
            // 更新MN显示为配置后的MN
            const mnInput = row.querySelector('[name*="product_mn"]');
            if (mnInput) {
                mnInput.value = config.configured_mn;
            }

            // 添加视觉标识
            row.classList.add('spec-configured');
        } else if (config.existing_product_id) {
            // 已存在相同MN的产品，更新为已存在产品
            row.dataset.existingProductId = config.existing_product_id;
        }

        // 如果有价格增量，可以选择更新价格（可选）
        if (config.price_adjustment_total !== 0) {
            console.log(`  💰 价格增量: ${config.price_adjustment_total / 100} 元`);
            // 注意：是否自动更新价格取决于业务需求
            // 这里暂不自动修改价格，保持原产品价格
        }

        console.log('  ✅ 动态规格配置已应用');
    }

    /**
     * 应用可配置字段价格增量到行
     * @param {HTMLElement} row - 表格行元素
     * @param {Object} config - 可配置字段配置数据
     */
    applyConfigurableSpecPriceAdjustment(row, config) {
        // 存储配置数据到行的dataset中
        row.dataset.configurableSpecConfig = JSON.stringify(config);

        // 如果有规格MN，更新product_mn字段
        if (config.spec_mn) {
            this.setFieldValueByKey(row, 'product_mn', config.spec_mn);
            console.log(`📝 设置规格MN: ${config.spec_mn}`);

            // ⭐ 设置配置数据用于保存（统一数据格式）
            // 将可配置字段配置转换为统一的配置数据格式
            row.dataset.configuredMn = config.spec_mn;
            row.dataset.configuredSpecs = JSON.stringify({
                source: 'configurable_spec',
                original_product_id: config.original_product_id || null,
                configurable_selections: config.configurable_selections || {},
                price_details: config.price_details || [],
                // ⭐ 新增：保存配置后的描述
                configured_description: config.configured_description || ''
            });
            row.dataset.priceAdjustmentTotal = config.price_adjustment_total || 0;
            // 标记为需要创建新产品
            row.dataset.pendingProductCreation = 'true';
            row.dataset.originalProductId = config.original_product_id || '';

            // ⭐ 如果有配置后的描述，更新产品描述字段
            if (config.configured_description) {
                this.setFieldValueByKey(row, 'product_desc', config.configured_description);
                console.log(`📝 设置配置后的描述: ${config.configured_description.substring(0, 50)}...`);
            }

            console.log('✅ 可配置字段配置已保存到 dataset:', {
                configuredMn: row.dataset.configuredMn,
                pendingProductCreation: row.dataset.pendingProductCreation,
                originalProductId: row.dataset.originalProductId,
                hasConfiguredDescription: !!config.configured_description
            });
        }

        const adjustmentTotal = config.price_adjustment_total || 0;
        if (adjustmentTotal === 0) {
            return;
        }

        row.dataset.configurablePriceAdjustment = adjustmentTotal;

        // 价格增量以分为单位，需要转换为元
        const adjustmentInYuan = adjustmentTotal / 100;

        // 更新市场价（同时更新 data-raw-value 和显示值）
        const marketPriceInput = row.querySelector('.market_price-input');
        if (marketPriceInput) {
            // 获取原始值（CNY）
            const currentRawPrice = parseFloat(marketPriceInput.dataset.rawValue || marketPriceInput.value) || 0;
            const newRawPrice = currentRawPrice + adjustmentInYuan;

            // 更新原始值
            marketPriceInput.dataset.rawValue = newRawPrice;

            // 更新显示值（考虑货币转换）
            if (this.currentCurrency && this.currentCurrency !== 'CNY') {
                const displayPrice = this.convertAmountLocally(newRawPrice, 'CNY', this.currentCurrency);
                marketPriceInput.value = parseFloat(displayPrice).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            } else {
                marketPriceInput.value = parseFloat(newRawPrice).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            }
        }
    }

    /**
     * 获取行的动态规格配置数据（用于保存）
     * @param {HTMLElement} row - 表格行元素
     * @returns {Object|null} 配置数据或null
     */
    getDynamicSpecConfig(row) {
        if (!row.dataset.configuredSpecs || !row.dataset.configuredMn) {
            return null;
        }

        return {
            configured_specs: JSON.parse(row.dataset.configuredSpecs),
            configured_mn: row.dataset.configuredMn,
            original_mn: row.dataset.originalMn,
            price_adjustment_total: parseInt(row.dataset.priceAdjustmentTotal) || 0,
            pending_product_creation: row.dataset.pendingProductCreation === 'true',
            original_product_id: parseInt(row.dataset.originalProductId) || null,
            existing_product_id: row.dataset.existingProductId ? parseInt(row.dataset.existingProductId) : null
        };
    }
}

// 导出到全局命名空间
window.ProductDetailManager = ProductDetailManager;