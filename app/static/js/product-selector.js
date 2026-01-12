/**
 * 通用产品选择器组件
 * 支持四级联动选择：类别 → 产品名称 → 型号 → 规格
 * 
 * @author Claude AI
 * @version 1.0.0
 */

class ProductSelector {
    constructor(config) {
        // 默认API端点
        const defaultApiEndpoints = {
            categories: '/api/products/categories',
            productsByCategory: '/api/products/by-category',
            subcategories: '/api/products/subcategories',           // 新增：子分类查询
            productsBySubcategory: '/api/products/by-subcategory',  // 新增：按子分类查询产品
            productModels: '/api/products/models',
            productSpecs: '/api/products/specs',
            productSearch: '/api/products/search'
        };
        
        // 合并API端点配置
        const mergedApiEndpoints = config && config.apiEndpoints 
            ? { ...defaultApiEndpoints, ...config.apiEndpoints }
            : defaultApiEndpoints;
        
        this.config = {
            apiEndpoints: mergedApiEndpoints,
            onSelect: (config && config.onSelect) || null,
            onError: (config && config.onError) || null,
            cache: config ? (config.cache !== false) : true, // 默认启用缓存
            cacheTimeout: (config && config.cacheTimeout) || 300000, // 5分钟缓存
            searchMinLength: (config && config.searchMinLength) || 2,
            searchDelay: (config && config.searchDelay) || 300,
            // 手动输入配置
            manual_input: config && config.manual_input ? config.manual_input : {
                enabled: false,
                option_text: '手动输入',
                temp_indicator: {
                    show: true,
                    text: '临时',
                    position: 'after_price',
                    style: 'temp-product-indicator'
                }
            },
            // 临时产品配置
            temp_products: config && config.temp_products ? config.temp_products : {
                auto_save: true,
                category_association: true,
                merge_with_regular: true
            },
            // 跳过配置模态框（采购订单等场景使用）
            skipConfigModal: config && config.skipConfigModal === true
        };
        
        this.cache = new Map();
        this.activeMenus = new Map();
        this.searchTimeout = null;
        this.configModal = null;  // 产品配置模态框实例
        this.currentInput = null;  // 当前正在操作的输入框

        this.init();
    }

    /**
     * 初始化组件
     */
    init() {
        this.addStyles();
        this.bindGlobalEvents();
        this.initConfigModal();  // 初始化产品配置模态框
    }

    /**
     * 初始化产品配置模态框（增强版 - 支持自动重试）
     */
    initConfigModal() {
        console.log('🔍 Checking ProductConfigModal initialization...');
        console.log('  - ProductConfigModal class defined:', typeof ProductConfigModal !== 'undefined');
        console.log('  - Modal DOM element exists:', !!document.getElementById('productConfigModal'));

        // 如果 ProductConfigModal 未定义，启动自动重试机制（防御性编程）
        if (typeof ProductConfigModal === 'undefined') {
            console.warn('⚠️ ProductConfigModal not yet loaded, setting up retry mechanism...');

            let retryCount = 0;
            const maxRetries = 10;  // 最多重试10次

            const retryInterval = setInterval(() => {
                retryCount++;
                console.log(`  🔄 Retry #${retryCount}...`);

                if (typeof ProductConfigModal !== 'undefined' && document.getElementById('productConfigModal')) {
                    clearInterval(retryInterval);
                    this.configModal = new ProductConfigModal(this);
                    console.log(`✅ Product config modal initialized successfully (after ${retryCount} retry)`);
                } else if (retryCount >= maxRetries) {
                    clearInterval(retryInterval);
                    console.error(`❌ ProductConfigModal initialization failed after ${maxRetries} retries`);
                    console.error('   - ProductConfigModal:', typeof ProductConfigModal);
                    console.error('   - Modal element:', document.getElementById('productConfigModal'));
                }
            }, 100);  // 每100ms重试一次
            return;
        }

        // 正常初始化路径
        if (document.getElementById('productConfigModal')) {
            this.configModal = new ProductConfigModal(this);
            console.log('✅ Product config modal initialized successfully');
        } else {
            console.error('❌ ProductConfigModal class exists but DOM element not found');
            console.error('   Please ensure render_product_config_modal() is called in the template');
        }
    }

    /**
     * 打开产品配置模态框
     * 优先使用新版 ProductSpecModal（Tailwind 风格三步流程）
     * 如果不可用，回退到旧版 ProductConfigModal
     */
    openProductConfigModal(config) {
        console.log('🔍 ========== ProductSelector.openProductConfigModal() ==========');
        console.log('  传入的config:');
        console.log('    - category:', config.category);
        console.log('    - subcategory:', config.subcategory);
        console.log('    - model:', config.model);
        console.log('    - products数量:', config.products ? config.products.length : 0);
        if (config.products && config.products.length > 0) {
            console.log('    - 产品列表:');
            config.products.forEach((p, i) => {
                console.log(`      [${i}] id=${p.id}, name=${p.product_name || p.name}`);
            });
        }

        // 优先尝试使用新版 ProductSpecModal (tw_product_spec_modal.html)
        if (typeof ProductSpecModal !== 'undefined') {
            console.log('🎨 Using new ProductSpecModal (Tailwind version)');
            const self = this;
            ProductSpecModal.open({
                products: config.products || [],
                category: config.category || '',
                subcategory: config.subcategory || '',
                model: config.model || '',
                onConfirm: function(result) {
                    console.log('✅ ProductSpecModal confirmed:', result);
                    // 将选择结果传递给原有的 onSelect 回调
                    if (self.config.onSelect && self.currentInput && result.product) {
                        const selectedProduct = {
                            product_name: result.product.product_name || result.product.name,
                            product_model: result.product.model || result.product.product_model,
                            product_desc: result.product.specification || result.product.product_spec || '',
                            product_spec: result.product.specification || result.product.product_spec || '',
                            brand: result.product.brand || '',
                            unit: result.product.unit || '个',
                            market_price: result.product.retail_price || result.product.market_price || 0,
                            product_mn: result.product.product_mn || '',
                            currency: result.product.currency || 'CNY',
                            status: result.product.status || 'active',
                            configurations: result.configurations || []
                        };
                        self.config.onSelect(selectedProduct, self.currentInput);
                    }
                    self.hideMenu();
                }
            });
            return;
        }

        // 回退到旧版 ProductConfigModal
        console.log('📦 Falling back to old ProductConfigModal');
        if (!this.configModal) {
            console.log('🔄 Attempting lazy initialization of ProductConfigModal...');
            this.initConfigModal();
        }

        if (this.configModal) {
            this.configModal.open(config);
        } else {
            console.error('❌ Product config modal not initialized and lazy initialization failed');
            alert('产品配置功能初始化失败，请刷新页面重试');
        }
    }
    
    /**
     * 添加样式
     */
    addStyles() {
        if (document.getElementById('product-selector-styles')) {
            return;
        }
        
        const style = document.createElement('style');
        style.id = 'product-selector-styles';
        style.textContent = `
            /* 产品选择器容器 - 参考新UI */
            .product-menu-container {
                position: absolute;
                background: white;
                border: none;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                z-index: 9999;
                display: grid;
                grid-template-columns: 200px 240px 1fr;
                border-radius: 0.5rem;
                overflow: hidden;
                min-width: 800px;
                max-width: 1000px;
            }
            .dark .product-menu-container {
                background: #1e293b;
            }

            /* 列表通用样式 */
            .menu-list {
                border-right: 1px solid #e2e8f0;
                max-height: 70vh;
                overflow-y: auto;
                overflow-x: hidden;
                background: white;
                padding: 0.5rem;
            }
            .dark .menu-list {
                border-right-color: #334155;
                background: #1e293b;
            }

            .menu-list:last-child {
                border-right: none;
            }

            .category-list {
                width: 200px;
            }

            .product-list {
                width: 240px;
                display: none;
            }

            .model-list {
                width: auto;
                min-width: 320px;
                display: none;
                padding: 0;
                background: #f8fafc;
            }
            .dark .model-list {
                background: #0f172a;
            }

            /* 菜单项样式 - 参考新UI */
            .menu-item {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0.75rem;
                cursor: pointer;
                border-radius: 0.375rem;
                font-size: 0.875rem;
                font-weight: 500;
                color: #1e293b;
                transition: all 0.15s ease;
                margin-bottom: 2px;
            }
            .dark .menu-item {
                color: #e2e8f0;
                border-bottom: none !important;
            }

            .menu-item:hover {
                background-color: #f1f5f9;
            }
            .dark .menu-item:hover {
                background-color: #334155;
            }

            .menu-item.active {
                background-color: #2563eb;
                color: white;
            }

            /* 箭头图标样式 */
            .menu-item .menu-arrow {
                font-size: 1.25rem;
                color: #94a3b8;
                flex-shrink: 0;
                margin-left: 0.5rem;
            }
            .menu-item:hover .menu-arrow {
                color: #64748b;
            }
            .dark .menu-item .menu-arrow {
                color: #64748b;
            }
            .dark .menu-item:hover .menu-arrow {
                color: #94a3b8;
            }
            .menu-item.active .menu-arrow {
                color: white;
            }

            /* 类别项带图标 */
            .menu-item .category-icon {
                margin-right: 0.75rem;
                font-size: 1.25rem;
                color: #64748b;
                flex-shrink: 0;
            }
            .menu-item:hover .category-icon {
                color: #475569;
            }
            .dark .menu-item:hover .category-icon {
                color: #94a3b8;
            }
            .menu-item.active .category-icon {
                color: white;
            }
            .menu-item .category-name {
                flex: 1;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            /* 产品项样式 - 带计数 */
            .menu-item .product-info {
                flex: 1;
                min-width: 0;
            }
            .menu-item .product-title {
                font-weight: 600;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .menu-item .product-count {
                font-size: 0.75rem;
                font-weight: 400;
                color: #64748b;
                margin-top: 2px;
            }
            .menu-item.active .product-count {
                color: rgba(255,255,255,0.8);
            }

            /* 手动输入选项样式 */
            .manual-input-option {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white !important;
                margin-top: 0.5rem;
            }
            .manual-input-option:hover {
                background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
            }
            .manual-input-option:after {
                content: "edit" !important;
                font-family: 'Material Icons' !important;
                color: white !important;
            }

            /* 加载/错误/空状态 */
            .menu-loading {
                padding: 1.5rem;
                color: #64748b;
                text-align: center;
                font-size: 0.875rem;
            }
            .menu-error {
                padding: 1.5rem;
                color: #ef4444;
                font-size: 0.875rem;
                text-align: center;
            }
            .menu-empty {
                padding: 1.5rem;
                color: #94a3b8;
                font-size: 0.875rem;
                text-align: center;
            }

            /* 搜索框 */
            .menu-search {
                padding: 0.75rem;
                border-bottom: 1px solid #e2e8f0;
                background: white;
            }
            .dark .menu-search {
                border-bottom-color: #334155;
                background: #1e293b;
            }
            .menu-search input {
                width: 100%;
                padding: 0.5rem 0.75rem;
                border: 1px solid #e2e8f0;
                border-radius: 0.375rem;
                font-size: 0.875rem;
                background: #f8fafc;
            }
            .dark .menu-search input {
                border-color: #334155;
                background: #0f172a;
                color: #e2e8f0;
            }
            .menu-search input:focus {
                outline: none;
                border-color: #2563eb;
                box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
            }

            .product-info {
                flex: 1;
                overflow: hidden;
            }

            .product-name {
                font-weight: 500;
                margin-bottom: 2px;
            }

            .product-details {
                font-size: 11px;
                color: #666;
                line-height: 1.3;
            }
            
            /* 产品详情项样式 - 第三列 */
            .product-detail-item {
                display: flex !important;
                justify-content: space-between;
                align-items: flex-start;
                padding: 1rem !important;
                border-bottom: 1px solid #e2e8f0;
                border-radius: 0 !important;
                margin-bottom: 0 !important;
                cursor: pointer;
                transition: background-color 0.15s;
            }
            .dark .product-detail-item {
                border-bottom: none;
            }
            .product-detail-item:last-child {
                border-bottom: none;
            }
            .product-detail-item:hover {
                background-color: #f1f5f9 !important;
            }
            .dark .product-detail-item:hover {
                background-color: #334155 !important;
            }
            .product-detail-item:after {
                display: none !important;
            }

            .product-detail-info {
                flex: 1;
                min-width: 0;
                padding-right: 1rem;
            }

            .product-detail-info h3,
            .product-detail-info .product-name-title {
                font-size: 0.875rem;
                font-weight: 600;
                color: #0f172a;
                margin-bottom: 0.25rem;
            }
            .dark .product-detail-info h3,
            .dark .product-detail-info .product-name-title {
                color: #f1f5f9;
            }

            .product-line-1 {
                margin-bottom: 0.25rem;
            }

            .product-model {
                font-size: 0.875rem;
                font-weight: 500;
                color: #64748b;
            }
            .dark .product-model {
                color: #94a3b8;
            }

            .product-line-2 {
                margin-top: 0.5rem;
            }

            .product-spec {
                font-size: 0.75rem;
                color: #64748b;
                line-height: 1.4;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }
            .dark .product-spec {
                color: #94a3b8;
            }

            .product-line-3 {
                display: none;
            }

            /* 价格区域 */
            .product-price-area {
                flex-shrink: 0;
                text-align: right;
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                gap: 0.25rem;
            }

            .product-price {
                font-weight: 600;
                color: #2563eb;
                font-size: 0.875rem;
                white-space: nowrap;
            }
            .dark .product-price {
                color: #60a5fa;
            }

            .product-price.discontinued {
                font-weight: 500;
                color: #94a3b8 !important;
                text-decoration: line-through;
            }

            .product-status-badge {
                font-size: 0.625rem;
                padding: 0.125rem 0.375rem;
                border-radius: 0.25rem;
                font-weight: 500;
            }
            .product-status-badge.discontinued {
                background-color: #fef2f2;
                color: #dc2626;
            }
            .dark .product-status-badge.discontinued {
                background-color: rgba(220, 38, 38, 0.2);
                color: #f87171;
            }

            /* 展开箭头和提示 */
            .expand-hint {
                color: #64748b !important;
                font-style: normal;
                font-weight: 400 !important;
                font-size: 0.75rem;
            }
            .dark .expand-hint {
                color: #94a3b8 !important;
            }

            .expand-arrow {
                font-size: 1.25rem;
                color: #94a3b8;
            }
            .product-detail-item:hover .expand-arrow {
                color: #64748b;
            }
            .dark .product-detail-item:hover .expand-arrow {
                color: #e2e8f0;
            }

            /* 多规格提示 */
            .product-variants-hint {
                font-size: 0.75rem;
                color: #64748b;
                margin-top: 0.25rem;
            }
            .dark .product-variants-hint {
                color: #94a3b8;
            }
            
            /* 滚动条样式 */
            .menu-list::-webkit-scrollbar {
                width: 6px;
            }
            
            .menu-list::-webkit-scrollbar-track {
                background: #f1f1f1;
            }
            
            .menu-list::-webkit-scrollbar-thumb {
                background: #c1c1c1;
                border-radius: 3px;
            }
            
            .menu-list::-webkit-scrollbar-thumb:hover {
                background: #a1a1a1;
            }
            
            /* 响应式调整 */
            @media (max-width: 768px) {
                .product-menu-container {
                    position: fixed !important;
                    top: 50% !important;
                    left: 50% !important;
                    transform: translate(-50%, -50%) !important;
                    max-width: 95vw;
                    max-height: 80vh;
                    min-width: auto;
                    flex-direction: column;
                }
                
                .menu-list {
                    width: 100% !important;
                    max-height: 200px;
                    border-right: none;
                    border-bottom: 1px solid #eee;
                }
                
                .menu-list:last-child {
                    border-bottom: none;
                }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    /**
     * 绑定全局事件
     */
    bindGlobalEvents() {
        // 点击外部关闭菜单
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.product-menu-container') &&
                !e.target.classList.contains('product-name') &&
                !e.target.closest('.product-selector-trigger')) {
                this.closeAllMenus();
            }
        });
        
        // ESC键关闭菜单
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllMenus();
            }
        });
        
        // 窗口大小变化时重新定位菜单
        window.addEventListener('resize', () => {
            this.repositionActiveMenus();
        });
    }
    
    /**
     * 初始化行的产品选择器
     */
    initializeRow(row) {
        const productInput = row.querySelector('.product-name');
        if (productInput) {
            this.bindInputEvents(productInput);
        }
    }
    
    /**
     * 绑定输入框事件
     */
    bindInputEvents(input) {
        // 移除旧的事件监听器
        input.removeEventListener('click', this.handleInputClick);
        input.removeEventListener('focus', this.handleInputFocus);
        input.removeEventListener('input', this.handleInputSearch);
        
        // 绑定新的事件监听器
        input.addEventListener('click', (e) => this.handleInputClick(e));
        input.addEventListener('focus', (e) => this.handleInputFocus(e));
        input.addEventListener('input', (e) => this.handleInputSearch(e));
    }
    
    /**
     * 处理输入框点击
     */
    handleInputClick(e) {
        e.stopPropagation();
        const input = e.target;
        
        // 关闭其他菜单
        this.closeAllMenus();
        
        // 显示产品选择菜单
        this.showProductMenu(input);
    }
    
    /**
     * 处理输入框获得焦点
     */
    handleInputFocus(e) {
        // 同点击处理
        this.handleInputClick(e);
    }
    
    /**
     * 处理输入框搜索
     */
    handleInputSearch(e) {
        const input = e.target;
        const searchTerm = input.value.trim();
        
        // 清除之前的搜索定时器
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // 如果搜索词太短，显示分类菜单
        if (searchTerm.length < this.config.searchMinLength) {
            this.showProductMenu(input);
            return;
        }
        
        // 延迟搜索
        this.searchTimeout = setTimeout(() => {
            this.performSearch(input, searchTerm);
        }, this.config.searchDelay);
    }
    
    /**
     * 显示产品选择菜单
     */
    showProductMenu(input) {
        // 设置当前输入框
        this.currentInput = input;
        
        // 创建菜单结构
        const menu = this.createMenuStructure();
        
        // 定位菜单
        this.positionMenu(menu, input);
        
        // 添加到页面
        document.body.appendChild(menu);
        
        // 记录活动菜单
        this.activeMenus.set(input, menu);
        
        // 加载产品类别
        this.loadCategories(menu);
    }
    
    /**
     * 创建菜单结构
     */
    createMenuStructure() {
        const menu = document.createElement('div');
        menu.className = 'product-menu-container';

        const categories = document.createElement('div');
        categories.className = 'category-list menu-list';
        categories.innerHTML = '<div class="menu-loading">加载中...</div>';

        const products = document.createElement('div');
        products.className = 'product-list menu-list';
        products.innerHTML = '<div class="menu-loading">请选择类别</div>';

        const models = document.createElement('div');
        models.className = 'model-list menu-list';
        models.innerHTML = '<div class="menu-loading">请选择产品</div>';

        menu.appendChild(categories);
        menu.appendChild(products);
        menu.appendChild(models);

        return menu;
    }
    
    /**
     * 定位菜单
     */
    positionMenu(menu, input) {
        const inputRect = input.getBoundingClientRect();
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;
        
        let top = inputRect.bottom + window.scrollY + 5;
        let left = inputRect.left + window.scrollX;
        
        // 临时添加到DOM以获取尺寸
        menu.style.visibility = 'hidden';
        document.body.appendChild(menu);
        
        const menuRect = menu.getBoundingClientRect();
        
        // 调整水平位置
        if (left + menuRect.width > windowWidth) {
            left = windowWidth - menuRect.width - 10;
        }
        if (left < 10) {
            left = 10;
        }
        
        // 调整垂直位置
        if (top + menuRect.height > windowHeight + window.scrollY - 10) {
            top = inputRect.top + window.scrollY - menuRect.height - 5;
        }
        
        menu.style.position = 'absolute';
        menu.style.top = top + 'px';
        menu.style.left = left + 'px';
        menu.style.visibility = 'visible';
    }
    
    /**
     * 重新定位活动菜单
     */
    repositionActiveMenus() {
        this.activeMenus.forEach((menu, input) => {
            this.positionMenu(menu, input);
        });
    }
    
    /**
     * 加载产品类别
     */
    async loadCategories(menu) {
        const categoriesContainer = menu.querySelector('.category-list');
        
        try {
            const categories = await this.fetchData('categories');
            
            categoriesContainer.innerHTML = '';
            
            if (!categories || categories.length === 0) {
                categoriesContainer.innerHTML = '<div class="menu-empty">暂无产品类别</div>';
                return;
            }
            
            // 类别图标映射
            const categoryIcons = {
                '基站': 'cell_tower',
                '合路平台': 'hub',
                '直放站': 'broadcast_on_personal',
                '功率/耦合器': 'power',
                '对讲机': 'perm_phone_msg',
                '配件': 'extension',
                '天线': 'settings_input_antenna',
                '应用': 'apps',
                '服务': 'support_agent'
            };

            categories.forEach(category => {
                const item = document.createElement('div');
                item.className = 'menu-item';
                const icon = categoryIcons[category] || 'category';
                item.innerHTML = `
                    <span class="material-symbols-outlined category-icon">${icon}</span>
                    <span class="category-name">${category}</span>
                    <span class="material-symbols-outlined menu-arrow">chevron_right</span>
                `;
                item.dataset.category = category;
                
                // 添加鼠标悬停和点击事件
                let hoverTimer;
                
                item.addEventListener('mouseenter', () => {
                    // 添加悬停视觉反馈
                    item.classList.add('hover-expanding');
                    
                    // 检查是否在搜索模式下
                    const input = this.currentInput || this.findInputForMenu(menu);
                    const inputValue = input ? input.value.trim() : '';
                    const hasSearchContent = inputValue.length > 0;
                    
                    // 检查是否在编辑现有产品
                    const isEditingExistingProduct = hasSearchContent && 
                        (inputValue.length > 4 && 
                         !['基站', '合路平台', '直放站', '功率/耦合器', '对讲机'].includes(inputValue));
                    
                    // 在搜索模式下（但不是编辑现有产品时）不自动展开下一级菜单
                    if (!hasSearchContent || isEditingExistingProduct) {
                        // 延迟展开，避免快速滑过时误触
                        hoverTimer = setTimeout(() => {
                            this.selectCategory(menu, category);
                        }, 200);
                    }
                });
                
                item.addEventListener('mouseleave', () => {
                    // 移除悬停视觉反馈
                    item.classList.remove('hover-expanding');
                    
                    // 清除延迟定时器
                    if (hoverTimer) {
                        clearTimeout(hoverTimer);
                    }
                });
                
                item.addEventListener('click', () => {
                    // 立即选择类别
                    if (hoverTimer) {
                        clearTimeout(hoverTimer);
                    }
                    
                    // 检查是否在搜索模式下（输入框有内容且不是完整的产品名称）
                    const input = this.currentInput || this.findInputForMenu(menu);
                    const inputValue = input ? input.value.trim() : '';
                    const hasSearchContent = inputValue.length > 0;
                    
                    // 检查输入的内容是否是一个完整的产品名称（编辑模式）
                    // 如果输入值看起来像一个完整的产品名称（不是简单的搜索关键词），
                    // 则不应该触发搜索模式的分类选择逻辑
                    const isEditingExistingProduct = hasSearchContent && 
                        (inputValue.length > 4 && inputValue !== category && 
                         !['基站', '合路平台', '直放站', '功率/耦合器', '对讲机'].includes(inputValue));
                    
                    if (hasSearchContent && !isEditingExistingProduct) {
                        // 搜索模式下直接选择分类作为产品名称
                        console.log('🔧 搜索模式下选择分类:', category);
                        const categoryProduct = {
                            product_name: category,
                            product_model: '',
                            product_desc: '',
                            brand: '',
                            unit: '',
                            market_price: 0,
                            status: 'category_selection'
                        };
                        
                        if (this.config.onSelect) {
                            this.config.onSelect(categoryProduct, input);
                        }
                        
                        // 关闭菜单
                        this.closeMenu(menu);
                    } else {
                        // 正常模式下展开产品列表
                        this.selectCategory(menu, category);
                    }
                });
                
                categoriesContainer.appendChild(item);
            });
            
        } catch (error) {
            this.handleError(categoriesContainer, '加载类别失败');
        }
    }
    
    /**
     * 选择类别 - 改造后：加载子分类列表
     */
    async selectCategory(menu, category) {
        // 高亮当前类别
        menu.querySelectorAll('.category-list .menu-item').forEach(item => {
            item.classList.remove('active');
        });
        menu.querySelector(`[data-category="${category}"]`).classList.add('active');

        // 重置后续列表
        const modelsContainer = menu.querySelector('.model-list');
        modelsContainer.innerHTML = '<div class="menu-placeholder">请选择子分类</div>';
        modelsContainer.style.display = 'none';

        // 显示并加载子分类列表
        const subcategoriesContainer = menu.querySelector('.product-list');
        subcategoriesContainer.style.display = 'block';
        subcategoriesContainer.innerHTML = '<div class="menu-loading">加载中...</div>';

        try {
            // 调用新的API接口获取子分类
            const subcategoriesData = await this.fetchData('subcategories', { category });

            subcategoriesContainer.innerHTML = '';

            if (!subcategoriesData || !subcategoriesData.subcategories || subcategoriesData.subcategories.length === 0) {
                subcategoriesContainer.innerHTML = '<div class="menu-empty">此分类下暂无子分类</div>';
                return;
            }

            const subcategories = subcategoriesData.subcategories;

            // 显示子分类列表
            subcategories.forEach(subcategory => {
                const item = document.createElement('div');
                item.className = 'menu-item';
                item.innerHTML = `
                    <div class="product-info">
                        <div class="product-title">${subcategory.name}</div>
                        <div class="product-count">${subcategory.count} 个产品</div>
                    </div>
                    <span class="material-symbols-outlined menu-arrow">chevron_right</span>
                `;
                item.dataset.subcategory = subcategory.name;
                item.dataset.category = category;

                // 添加鼠标悬停和点击事件
                let hoverTimer;

                item.addEventListener('mouseenter', () => {
                    // 添加悬停视觉反馈
                    item.classList.add('hover-expanding');

                    // 延迟展开，避免快速滑过时误触
                    hoverTimer = setTimeout(() => {
                        this.selectSubcategory(menu, category, subcategory.name);
                    }, 200);
                });

                item.addEventListener('mouseleave', () => {
                    // 移除悬停视觉反馈
                    item.classList.remove('hover-expanding');

                    // 清除延迟定时器
                    if (hoverTimer) {
                        clearTimeout(hoverTimer);
                    }
                });
                
                item.addEventListener('click', () => {
                    // 立即选择子分类
                    if (hoverTimer) {
                        clearTimeout(hoverTimer);
                    }
                    this.selectSubcategory(menu, category, subcategory.name);
                });

                subcategoriesContainer.appendChild(item);
            });

        } catch (error) {
            this.handleError(subcategoriesContainer, '加载子分类失败');
        }
    }

    /**
     * 选择子分类 - 加载产品列表
     */
    async selectSubcategory(menu, category, subcategory) {
        // 高亮当前子分类
        menu.querySelectorAll('.product-list .menu-item').forEach(item => {
            item.classList.remove('active');
        });
        const subcategoryItem = menu.querySelector(`[data-subcategory="${subcategory}"]`);
        if (subcategoryItem) {
            subcategoryItem.classList.add('active');
        }

        // 显示并加载产品列表
        const modelsContainer = menu.querySelector('.model-list');
        modelsContainer.style.display = 'block';
        modelsContainer.innerHTML = '<div class="menu-loading">加载中...</div>';

        try {
            // 调用API接口获取该子分类下的所有产品
            const productsData = await this.fetchData('productsBySubcategory', { category, subcategory });

            modelsContainer.innerHTML = '';

            if (!productsData || !productsData.model_groups || productsData.model_groups.length === 0) {
                modelsContainer.innerHTML = '<div class="menu-empty">此子分类下暂无产品</div>';
                return;
            }

            // skipConfigModal 模式：直接显示所有产品列表
            if (this.config.skipConfigModal) {
                const allProducts = productsData.model_groups.flatMap(mg => mg.products);
                this.renderProductList(modelsContainer, allProducts, category, subcategory);
                return;
            }

            // 标准模式：按型号分组显示
            const modelGroups = productsData.model_groups;

            // ⭐ 使用 JSON 快照计算同名产品的规格差异（用于高亮显示）
            // 按 product_name 分组，然后对每组使用 findDiffPositions 分析
            const allProducts = modelGroups.flatMap(mg => mg.products);
            const diffPositionsMap = new Map(); // product.id -> diffPositions

            if (window.SpecAnalyzer) {
                // 按产品名称分组
                const groups = window.SpecAnalyzer.groupByName(allProducts, 'product_name');

                // 对每组计算差异位置
                Object.values(groups).forEach(groupProducts => {
                    if (groupProducts.length >= 2) {
                        const withSnapshot = groupProducts.filter(p => p.code_definition_snapshot);
                        if (withSnapshot.length >= 2) {
                            const diffPositions = window.SpecAnalyzer.findDiffPositions(groupProducts);
                            // 将 diffPositions 关联到每个产品
                            groupProducts.forEach(product => {
                                diffPositionsMap.set(product.id, diffPositions);
                            });
                        }
                    }
                });
            }

            // 显示型号列表（去重后的）
            modelGroups.forEach(modelGroup => {
                const item = document.createElement('div');
                item.className = 'menu-item product-detail-item';

                // 根据产品数量决定显示内容
                let contentHtml = '';
                if (modelGroup.count === 1) {
                    // 只有1个产品：显示型号、规格和价格
                    const product = modelGroup.products[0];
                    const price = product.retail_price ? parseFloat(product.retail_price) : null;
                    const priceText = price ? this.formatPriceWithCurrency(price, product.currency) : '价格面议';
                    const isDiscontinued = product.status === 'discontinued' || product.status === '停产';
                    const priceClass = isDiscontinued ? 'product-price discontinued' : 'product-price';

                    // 添加 no-arrow 类隐藏箭头
                    item.classList.add('no-arrow');

                    // ⭐ 用 JSON 快照计算差异字段，然后高亮原始 specification 字符串
                    const diffPositions = diffPositionsMap.get(product.id);
                    let specHtml = product.specification || '';
                    if (diffPositions && diffPositions.length > 0 && window.SpecAnalyzer && specHtml) {
                        const diffKeys = new Set(diffPositions.filter(d => d.isDiff).map(d => d.fieldName));
                        if (diffKeys.size > 0) {
                            specHtml = window.SpecAnalyzer.highlightSpecString(specHtml, diffKeys);
                        }
                    }

                    contentHtml = `
                        <div class="product-detail-info">
                            <div class="product-line-1">
                                <h3 class="product-name-title">${modelGroup.product_name || product.product_name || ''}</h3>
                            </div>
                            ${product.model ? `<div class="product-model">${product.model}</div>` : ''}
                            ${specHtml ? `<div class="product-line-2"><div class="product-spec">${specHtml}</div></div>` : ''}
                        </div>
                        <div class="product-price-area">
                            <span class="${priceClass}">${priceText}</span>
                            ${isDiscontinued ? '<span class="product-status-badge discontinued">停产</span>' : ''}
                        </div>
                    `;
                } else {
                    // 多个产品：显示"点击选择"提示
                    const firstProduct = modelGroup.products[0];
                    contentHtml = `
                        <div class="product-detail-info">
                            <div class="product-line-1">
                                <h3 class="product-name-title">${modelGroup.product_name || firstProduct.product_name || ''}</h3>
                            </div>
                            <div class="product-count">点击选择 (${modelGroup.count} 个型号/规格)</div>
                        </div>
                        <div class="product-price-area">
                            <span class="material-symbols-outlined expand-arrow">chevron_right</span>
                        </div>
                    `;
                }

                item.innerHTML = contentHtml;
                item.dataset.model = modelGroup.model;
                item.dataset.category = category;
                item.dataset.subcategory = subcategory;

                // 点击型号时触发选择逻辑
                item.addEventListener('click', () => {
                    this.selectModel(modelGroup, category, subcategory);
                });

                modelsContainer.appendChild(item);
            });

        } catch (error) {
            console.error('加载型号列表失败:', error);
            this.handleError(modelsContainer, '加载型号失败');
        }
    }

    /**
     * 选择产品组 - 处理单/多产品逻辑（按产品名称分组）
     */
    selectModel(modelGroup, category, subcategory) {
        const products = modelGroup.products;

        if (!products || products.length === 0) {
            console.error('产品组下没有产品');
            return;
        }

        if (products.length === 1) {
            // 情况1：只有1个产品
            const product = products[0];

            // 检查产品是否有配置选项（skipConfigModal 模式下忽略配置）
            if (product.has_configurations && !this.config.skipConfigModal) {
                // 有配置 → 关闭菜单，打开配置模态框
                this.hideMenu();
                console.log('产品有配置选项，打开配置模态框:', product);
                this.openProductConfigModal({
                    category: category,
                    subcategory: subcategory,
                    product_name: modelGroup.product_name,
                    model: modelGroup.model,
                    products: products
                });
            } else {
                // 无配置 → 直接选择并关闭菜单
                console.log('产品组下只有1个产品且无配置，直接选择:', product);
                if (this.config.onSelect && this.currentInput) {
                    // 构造完整的产品信息对象 - 统一字段映射
                    const selectedProduct = {
                        product_name: modelGroup.product_name || product.product_name || product.name,
                        product_model: product.model || product.product_model || modelGroup.model,
                        product_desc: product.specification || product.product_spec || product.product_desc || product.spec || '',
                        product_spec: product.specification || product.product_spec || product.product_desc || product.spec || '',
                        brand: product.brand || '',
                        unit: product.unit || '个',
                        market_price: product.retail_price || product.market_price || 0,
                        product_mn: product.product_mn || product.mn || '',
                        currency: product.currency || 'CNY',
                        status: product.status || 'active'
                    };
                    this.config.onSelect(selectedProduct, this.currentInput);
                }
                this.hideMenu();
            }
        } else {
            // 情况2：有多个产品 → 打开配置模态框
            this.hideMenu();
            console.log('产品组下有多个产品，打开配置模态框:', products);
            this.openProductConfigModal({
                category: category,
                subcategory: subcategory,
                product_name: modelGroup.product_name,
                model: modelGroup.model,
                products: products
            });
        }
    }

    /**
     * 渲染完整产品列表（skipConfigModal 模式）
     */
    renderProductList(container, products, category, subcategory) {
        container.innerHTML = '';

        if (!products || products.length === 0) {
            container.innerHTML = '<div class="menu-empty">暂无产品</div>';
            return;
        }

        products.forEach(product => {
            const item = document.createElement('div');
            item.className = 'menu-item product-detail-item no-arrow';

            const isDiscontinued = product.status === 'discontinued' || product.status === '停产';
            const price = product.retail_price
                ? this.formatPriceWithCurrency(product.retail_price, product.currency)
                : '价格面议';
            const priceClass = isDiscontinued ? 'product-price discontinued' : 'product-price';

            item.innerHTML = `
                <div class="product-detail-info">
                    <div class="product-line-1">
                        <h3 class="product-name-title">${product.product_name || product.name || '-'}</h3>
                    </div>
                    ${product.model ? `<div class="product-model">${product.model}</div>` : ''}
                    ${product.specification ? `<div class="product-line-2"><div class="product-spec">${product.specification}</div></div>` : ''}
                </div>
                <div class="product-price-area">
                    <span class="${priceClass}">${price}</span>
                    ${isDiscontinued ? '<span class="product-status-badge discontinued">停产</span>' : ''}
                </div>
            `;

            item.addEventListener('click', () => {
                this.selectProductDirectly(product);
            });

            container.appendChild(item);
        });
    }

    /**
     * 直接选择产品（skipConfigModal 模式）
     */
    selectProductDirectly(product) {
        const selectedProduct = {
            product_id: product.id,
            product_name: product.product_name || product.name,
            product_model: product.model || '',
            product_desc: product.specification || '',
            product_spec: product.specification || '',
            brand: product.brand || '',
            unit: product.unit || '个',
            market_price: product.retail_price || product.market_price || 0,
            product_mn: product.product_mn || '',
            currency: product.currency || 'CNY',
            status: product.status || 'active'
        };

        if (this.config.onSelect && this.currentInput) {
            this.config.onSelect(selectedProduct, this.currentInput);
        }
        this.hideMenu();
    }

    /**
     * 选择产品
     */
    async selectProduct(menu, category, productName) {
        
        // 高亮当前产品
        menu.querySelectorAll('.product-list .menu-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // 查找并高亮对应的产品项
        const productItem = menu.querySelector(`[data-product-name="${productName}"]`);
        if (productItem) {
            productItem.classList.add('active');
            console.log('✅ 产品项已高亮');
        } else {
            console.warn('⚠️ 无法找到产品项:', productName);
        }
        
        // 已移除第四级菜单，不需要重置规格列表
        
        // 显示并加载型号列表
        const modelsContainer = menu.querySelector('.model-list');
        modelsContainer.style.display = 'block';
        modelsContainer.innerHTML = '<div class="menu-loading">加载中...</div>';
        
        try {
            // 同时获取常规产品和临时产品的型号
            const [regularProducts, tempProducts] = await Promise.all([
                this.fetchData('productModels', { category, product_name: productName }),
                this.config.apiEndpoints.tempProductsByCategory ? 
                    this.fetchData('tempProductsByCategory', { category, product_name: productName }) : 
                    Promise.resolve([])
            ]);
            
            console.log('📦 常规产品型号:', regularProducts);
            console.log('📦 临时产品型号:', tempProducts);
            
            modelsContainer.innerHTML = '';
            
            // 处理临时产品响应格式
            let tempProductList = tempProducts;
            if (tempProducts && typeof tempProducts === 'object' && tempProducts.data) {
                tempProductList = tempProducts.data;
            }
            
            const hasRegularProducts = regularProducts && regularProducts.length > 0;
            const hasTempProducts = tempProductList && Array.isArray(tempProductList) && tempProductList.length > 0;
            
            if (!hasRegularProducts && !hasTempProducts) {
                modelsContainer.innerHTML = '<div class="menu-empty">此产品下暂无型号</div>';
                return;
            }
            
            // 先显示常规产品的型号
            if (hasRegularProducts) {
                regularProducts.forEach(product => {
                const item = document.createElement('div');
                item.className = 'menu-item product-detail-item no-arrow';

                // 格式化价格显示，停产产品使用灰色
                const marketPrice = product.retail_price || product.market_price;
                // 更全面地检测停产状态
                const isDiscontinued = product.status === 'discontinued' ||
                                     product.status === '停产' ||
                                     product.status === 'inactive' ||
                                     product.product_status === 'discontinued' ||
                                     product.product_status === '停产' ||
                                     (product.status && product.status.toLowerCase().includes('discontin'));
                const priceText = marketPrice ? this.formatPriceWithCurrency(marketPrice, product.currency) : '价格面议';
                const priceClass = isDiscontinued ? 'product-price discontinued' : 'product-price';

                // 处理规格文本
                const specText = product.specification || product.product_spec || product.product_desc || product.spec || '';

                item.innerHTML = `
                    <div class="product-detail-info">
                        <div class="product-line-1">
                            <h3 class="product-name-title">${productName}</h3>
                        </div>
                        <div class="product-model">${product.model || product.product_model || '未知型号'}</div>
                        ${specText ? `<div class="product-line-2"><div class="product-spec">${specText}</div></div>` : ''}
                    </div>
                    <div class="product-price-area">
                        <span class="${priceClass}">${priceText}</span>
                        ${isDiscontinued ? '<span class="product-status-badge discontinued">停产</span>' : ''}
                    </div>
                `;
                
                // 点击直接选择该产品
                item.addEventListener('click', () => {
                    // 构造完整的产品信息对象 - 修复字段映射
                    const selectedProduct = {
                        product_name: productName,
                        product_model: product.model || product.product_model,
                        product_desc: product.specification || product.product_spec || product.product_desc || product.spec,
                        product_spec: product.specification || product.product_spec || product.product_desc || product.spec,
                        brand: product.brand || '未知品牌',
                        unit: product.unit || '个',
                        market_price: marketPrice || 0,
                        product_mn: product.product_mn || product.mn || '',
                        currency: product.currency || 'CNY',
                        status: product.status || 'active'
                    };
                    
                    // 如果是停产产品，显示确认对话框
                    if (isDiscontinued) {
                        const confirmed = confirm(
                            `注意：您选择的产品"${product.model || product.product_model}"已停产。\n\n` +
                            `请确认是否有供货能力，是否继续选择此产品？`
                        );
                        
                        if (!confirmed) {
                            return; // 用户取消选择
                        }
                    }
                    
                    // 选择产品，跳过第四级菜单
                    if (this.config.onSelect) {
                        this.config.onSelect(selectedProduct, this.currentInput);
                    }
                    
                    this.hideMenu();
                });
                
                modelsContainer.appendChild(item);
                });
            }
            
            // 显示临时产品的型号
            if (hasTempProducts) {
                // 如果同时有常规产品和临时产品，添加分隔线
                if (hasRegularProducts) {
                    const separator = document.createElement('div');
                    separator.className = 'temp-products-separator';
                    separator.style.cssText = `
                        border-top: 2px dashed #ff9800;
                        margin: 8px 0;
                        position: relative;
                        text-align: center;
                    `;
                    separator.innerHTML = `
                        <span style="background: white; padding: 0 8px; color: #ff9800; font-size: 11px; font-weight: 500;">
                            临时产品 (${tempProductList.length})
                        </span>
                    `;
                    modelsContainer.appendChild(separator);
                }
                
                // 显示临时产品型号
                tempProductList.forEach(product => {
                    const item = document.createElement('div');
                    item.className = 'menu-item product-detail-item temp-product-item no-arrow';
                    
                    // 临时产品专用样式
                    item.style.borderLeft = '4px solid #ff9800';
                    item.style.backgroundColor = '#fff8f0';
                    item.style.marginBottom = '4px';
                    item.style.display = 'flex';
                    item.style.alignItems = 'center';
                    
                    // 格式化参考价格
                    const referencePrice = product.reference_price || 0;
                    const priceText = referencePrice > 0 ?
                        `参考价: ${this.formatPriceWithCurrency(referencePrice, product.currency)}` :
                        '参考价: 面议';
                    
                    item.innerHTML = `
                        <div class="product-detail-info" style="flex: 1;">
                            <div class="product-line-1" style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="display: flex; align-items: center;">
                                    <strong class="product-model">${product.product_model}</strong>
                                    <span class="temp-indicator" style="
                                        background: #ff9800;
                                        color: white;
                                        padding: 1px 6px;
                                        border-radius: 10px;
                                        font-size: 10px;
                                        font-weight: 500;
                                        margin-left: 8px;
                                    ">临时</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span class="product-price" style="font-weight: bold;">${priceText}</span>
                                    <button class="temp-delete-btn"
                                            style="background: none; border: none; color: #dc3545;
                                                   font-size: 14px; cursor: pointer; padding: 2px;
                                                   opacity: 0; transition: opacity 0.3s ease, color 0.2s ease;
                                                   display: flex; align-items: center; justify-content: center;
                                                   width: 20px; height: 20px; border-radius: 3px;"
                                            onmouseover="this.style.color='#c82333'; this.style.backgroundColor='rgba(220, 53, 69, 0.1)'"
                                            onmouseout="this.style.color='#dc3545'; this.style.backgroundColor='none'"
                                            title="删除临时产品">
                                        <i class="fas fa-times"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="product-line-2">
                                <span class="product-spec">${product.product_desc || '无规格说明'}</span>
                            </div>
                            <div class="product-line-3">
                                <span class="product-mn">MN: ${product.product_mn || '无'}</span>
                                <span class="product-brand">品牌: ${product.brand || '未知'}</span>
                            </div>
                        </div>
                    `;
                    
                    // 为整个item添加鼠标悬停效果，控制删除按钮的显示/隐藏
                    const deleteBtn = item.querySelector('.temp-delete-btn');
                    
                    item.addEventListener('mouseenter', () => {
                        deleteBtn.style.opacity = '1';
                    });
                    
                    item.addEventListener('mouseleave', () => {
                        deleteBtn.style.opacity = '0';
                    });
                    
                    // 为产品信息区域添加点击事件（选择产品）
                    const productInfo = item.querySelector('.product-detail-info');
                    productInfo.addEventListener('click', (e) => {
                        // 如果点击的是删除按钮区域，不执行选择逻辑
                        if (e.target.closest('.temp-delete-btn')) {
                            return;
                        }
                        
                        // 增加使用次数
                        if (this.config.temp_products.auto_save) {
                            this.incrementTempProductUsage(product.id);
                        }
                        
                        // 构造临时产品对象
                        const selectedTempProduct = {
                            product_name: product.product_name,
                            product_model: product.product_model,
                            product_desc: product.product_desc,
                            brand: product.brand,
                            unit: product.unit,
                            market_price: product.reference_price || 0,
                            currency: 'CNY',
                            is_temp: true,
                            temp_product_id: product.id,
                            usage_count: product.usage_count
                        };
                        
                        // 选择临时产品
                        if (this.config.onSelect) {
                            this.config.onSelect(selectedTempProduct, this.currentInput);
                        }
                        
                        this.hideMenu();
                    });
                    
                    // 为删除按钮添加点击事件
                    deleteBtn.addEventListener('click', (e) => {
                        e.stopPropagation(); // 阻止事件冒泡
                        this.showDeleteConfirmDialog(product, () => {
                            // 删除确认后的回调
                            this.deleteTempProduct(product.id, item);
                        });
                    });
                    
                    modelsContainer.appendChild(item);
                });
            }
            
            // 在末尾添加手动输入选项（如果启用）
            if (this.config.manual_input.enabled) {
                const manualInputItem = document.createElement('div');
                manualInputItem.className = 'menu-item manual-input-option';
                manualInputItem.innerHTML = `
                    <div class="product-detail-info">
                        <div class="product-line-1">
                            <strong class="product-model">
                                <i class="fas fa-edit"></i> ${this.config.manual_input.option_text}
                            </strong>
                        </div>
                        <div class="product-line-2">
                            <span class="product-spec">手动输入产品信息</span>
                        </div>
                    </div>
                `;
                
                manualInputItem.addEventListener('click', () => {
                    this.showManualInputForm(category, productName);
                });
                
                modelsContainer.appendChild(manualInputItem);
            }
            
        } catch (error) {
            let errorMessage = '加载型号失败';
            if (error.message.includes('404')) {
                errorMessage = '加载型号失败 - API端点不存在';
            } else if (error.message.includes('403')) {
                errorMessage = '加载型号失败 - 权限不足';
            } else if (error.message.includes('500')) {
                errorMessage = '加载型号失败 - 服务器错误';
            }
            
            this.handleError(modelsContainer, errorMessage);
        }
    }
    /**
     * 选择规格（最终选择）
     */
    selectSpec(menu, product) {
        // 检查是否为停产产品
        const isDiscontinued = product.status === 'discontinued' || product.status === '停产';
        
        if (isDiscontinued) {
            const confirmed = confirm(
                `注意：您选择的产品"${product.specification || product.product_name || '该产品'}"已停产。\n\n` +
                `请确认是否有供货能力，是否继续选择此产品？`
            );
            
            if (!confirmed) {
                return; // 用户取消选择
            }
        }
        
        // 找到对应的输入框
        const input = this.findInputForMenu(menu);
        
        if (input && this.config.onSelect) {
            this.config.onSelect(product, input);
        }
        
        // 关闭菜单
        this.closeMenu(menu);
    }
    
    /**
     * 执行搜索
     */
    async performSearch(input, searchTerm) {
        // 关闭现有菜单
        this.closeMenuForInput(input);
        
        // 创建搜索结果菜单
        const menu = this.createSearchMenu();
        this.positionMenu(menu, input);
        document.body.appendChild(menu);
        this.activeMenus.set(input, menu);
        
        const resultsContainer = menu.querySelector('.search-results');
        resultsContainer.innerHTML = '<div class="menu-loading">搜索中...</div>';
        
        try {
            const results = await this.fetchData('productSearch', { term: searchTerm });
            
            resultsContainer.innerHTML = '';
            
            if (!results || results.length === 0) {
                resultsContainer.innerHTML = '<div class="menu-empty">未找到匹配的产品</div>';
                return;
            }
            
            // 显示搜索结果
            results.forEach(product => {
                const item = document.createElement('div');
                item.className = 'menu-item selectable no-arrow';
                
                // 检查是否为停产产品
                const isDiscontinued = product.status === 'discontinued' || product.status === '停产';
                const priceClass = isDiscontinued ? 'product-price-discontinued' : 'product-price';
                const priceText = product.retail_price ? `${this.formatPriceWithCurrency(product.retail_price, product.currency)}${isDiscontinued ? ' (停产)' : ''}` : '';
                
                item.innerHTML = `
                    <div class="product-info">
                        <div class="product-name">${product.product_name}</div>
                        <div class="product-details">
                            ${product.model ? `型号: ${product.model}` : ''}
                            ${product.specification ? ` | 规格: ${product.specification}` : ''}
                            ${product.brand ? ` | 品牌: ${product.brand}` : ''}
                        </div>
                        ${priceText ? `<div class="${priceClass}">${priceText}</div>` : ''}
                    </div>
                `;
                
                item.addEventListener('click', () => {
                    this.selectSpec(menu, product);
                });
                
                resultsContainer.appendChild(item);
            });
            
        } catch (error) {
            this.handleError(resultsContainer, '搜索失败');
        }
    }
    
    /**
     * 创建搜索菜单
     */
    createSearchMenu() {
        const menu = document.createElement('div');
        menu.className = 'product-menu-container';
        
        const results = document.createElement('div');
        results.className = 'search-results menu-list';
        results.style.width = '400px';
        results.style.display = 'block';
        
        menu.appendChild(results);
        
        return menu;
    }
    
    /**
     * 获取数据
     */
    async fetchData(endpoint, params = {}) {
        const cacheKey = `${endpoint}_${JSON.stringify(params)}`;
        
        // 检查缓存
        if (this.config.cache && this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.config.cacheTimeout) {
                return cached.data;
            }
        }
        
        // 构建URL
        const url = new URL(this.config.apiEndpoints[endpoint], window.location.origin);
        Object.keys(params).forEach(key => {
            url.searchParams.append(key, params[key]);
        });
        
        // 添加缓存破坏参数
        url.searchParams.append('_t', Date.now());
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache, no-store, must-revalidate'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // 缓存数据
        if (this.config.cache) {
            this.cache.set(cacheKey, {
                data: data,
                timestamp: Date.now()
            });
        }
        
        return data;
    }
    
    /**
     * 格式化价格
     */
    formatPrice(price) {
        const num = parseFloat(price) || 0;
        return num.toLocaleString('zh-CN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    /**
     * 获取货币符号
     */
    getCurrencySymbol(currency) {
        const symbols = {
            'CNY': '¥',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥',
            'HKD': 'HK$',
            'SGD': 'S$'
        };
        return symbols[currency] || symbols['CNY'];
    }

    /**
     * 格式化价格（带货币符号）
     */
    formatPriceWithCurrency(price, currency) {
        const symbol = this.getCurrencySymbol(currency);
        return `${symbol}${this.formatPrice(price)}`;
    }

    /**
     * 处理错误
     */
    handleError(container, message) {
        container.innerHTML = `<div class="menu-error">${message}</div>`;
        
        if (this.config.onError) {
            this.config.onError(new Error(message));
        }
    }
    
    /**
     * 查找菜单对应的输入框
     */
    findInputForMenu(menu) {
        for (const [input, menuElement] of this.activeMenus.entries()) {
            if (menuElement === menu) {
                return input;
            }
        }
        return null;
    }
    
    /**
     * 隐藏当前菜单
     */
    hideMenu() {
        if (this.currentInput) {
            this.closeMenuForInput(this.currentInput);
        }
    }
    
    /**
     * 关闭指定输入框的菜单
     */
    closeMenuForInput(input) {
        const menu = this.activeMenus.get(input);
        if (menu) {
            this.closeMenu(menu);
        }
    }
    
    /**
     * 关闭指定菜单
     */
    closeMenu(menu) {
        if (menu && menu.parentNode) {
            menu.parentNode.removeChild(menu);
        }
        
        // 从活动菜单中移除
        for (const [input, menuElement] of this.activeMenus.entries()) {
            if (menuElement === menu) {
                this.activeMenus.delete(input);
                break;
            }
        }
    }
    
    /**
     * 关闭所有菜单
     */
    closeAllMenus() {
        this.activeMenus.forEach((menu) => {
            if (menu && menu.parentNode) {
                menu.parentNode.removeChild(menu);
            }
        });
        this.activeMenus.clear();
    }
    
    /**
     * 清除缓存
     */
    clearCache() {
        this.cache.clear();
    }
    
    /**
     * 清除临时产品相关的缓存
     */
    clearTempProductCache() {
        // 遍历缓存，删除所有与临时产品相关的缓存项
        const keysToDelete = [];
        
        for (const [key, value] of this.cache.entries()) {
            // 删除临时产品相关的缓存
            if (key.includes('tempProducts') || 
                key.includes('tempProductsByCategory') || 
                key.includes('temp-products')) {
                keysToDelete.push(key);
                console.log('🗑️ 清理临时产品缓存:', key);
            }
        }
        
        keysToDelete.forEach(key => this.cache.delete(key));
        
        console.log(`✅ 已清理 ${keysToDelete.length} 个临时产品缓存项`);
    }
    
    /**
     * 选择性清理临时产品缓存（不影响菜单状态）
     */
    clearTempProductCacheSelectively(deletedProductId = null) {
        // 如果指定了删除的产品ID，则从缓存中移除该产品，而不是清空整个缓存
        if (deletedProductId) {
            console.log('🔄 从缓存中移除已删除的产品:', deletedProductId);
            
            for (const [key, value] of this.cache.entries()) {
                if (key.includes('tempProducts') || key.includes('tempProductsByCategory')) {
                    if (Array.isArray(value)) {
                        // 从数组中移除已删除的产品
                        const updatedValue = value.filter(item => item.id !== deletedProductId);
                        this.cache.set(key, updatedValue);
                        console.log('🔄 更新缓存:', key, '移除产品', deletedProductId);
                    } else if (value && value.data && Array.isArray(value.data)) {
                        // 处理包含data字段的响应格式
                        const updatedData = value.data.filter(item => item.id !== deletedProductId);
                        this.cache.set(key, { ...value, data: updatedData });
                        console.log('🔄 更新缓存:', key, '移除产品', deletedProductId);
                    }
                }
            }
            
            console.log('✅ 从缓存中移除了删除的产品，菜单结构保持不变');
        } else {
            // 原来的逻辑：清理所有临时产品缓存
            const keysToDelete = [];
            
            for (const [key, value] of this.cache.entries()) {
                if (key.includes('tempProducts') || 
                    key.includes('tempProductsByCategory')) {
                    keysToDelete.push(key);
                    console.log('🗑️ 选择性清理临时产品缓存:', key);
                }
            }
            
            keysToDelete.forEach(key => this.cache.delete(key));
            
            console.log(`✅ 选择性清理了 ${keysToDelete.length} 个临时产品缓存项，菜单结构保持不变`);
        }
    }
    
    /**
     * 从DOM中智能移除临时产品项
     */
    removeTempProductFromDOM(productId, itemElement) {
        if (!itemElement || !itemElement.parentNode) {
            console.warn('无法移除DOM元素：元素不存在或已被移除');
            return;
        }
        
        const container = itemElement.parentNode;
        console.log('🗑️ 从DOM中移除临时产品:', productId);
        
        // 移除产品项
        container.removeChild(itemElement);
        
        // 更新临时产品分隔线的计数
        this.updateTempProductSeparator(container);
        
        // 检查是否还有其他临时产品，如果没有则移除分隔线
        this.cleanupEmptyTempProductSection(container);
        
        console.log('✅ DOM更新完成，菜单位置保持不变');
    }
    
    /**
     * 更新临时产品分隔线的计数
     */
    updateTempProductSeparator(container) {
        const separator = container.querySelector('.temp-products-separator');
        if (separator) {
            // 计算当前剩余的临时产品数量
            const tempProductItems = container.querySelectorAll('.product-detail-item[style*="border-left: 4px solid #ff9800"]');
            const count = tempProductItems.length;
            
            if (count > 0) {
                const span = separator.querySelector('span');
                if (span) {
                    span.textContent = `临时产品 (${count})`;
                    console.log('🔄 更新分隔线计数:', count);
                }
            }
        }
    }
    
    /**
     * 清理空的临时产品区域
     */
    cleanupEmptyTempProductSection(container) {
        // 检查是否还有临时产品项
        const tempProductItems = container.querySelectorAll('.product-detail-item[style*="border-left: 4px solid #ff9800"]');
        
        if (tempProductItems.length === 0) {
            // 如果没有临时产品了，移除分隔线
            const separator = container.querySelector('.temp-products-separator');
            if (separator) {
                container.removeChild(separator);
                console.log('🧹 已移除空的临时产品分隔线');
            }
        }
    }
    
    /**
     * 显示手动输入表单
     */
    showManualInputForm(category, productName) {
        console.log('🔧 显示手动输入表单，接收到的参数:', {
            category: category,
            productName: productName,
            categoryIsEmpty: category === '',
            categoryIsUndefined: category === undefined,
            categoryType: typeof category
        });
        
        // 如果category为空，尝试从当前活动菜单中获取
        let finalCategory = category;
        if (!finalCategory || finalCategory === '' || finalCategory === 'undefined') {
            // 尝试从当前活动的菜单中获取选中的类别
            const activeMenus = Array.from(this.activeMenus.values());
            if (activeMenus.length > 0) {
                const currentMenu = activeMenus[0];
                const activeCategoryItem = currentMenu.querySelector('.category-list .menu-item.active');
                if (activeCategoryItem) {
                    finalCategory = activeCategoryItem.getAttribute('data-category');
                    console.log('🔧 从活动菜单中获取类别:', finalCategory);
                }
            }
            
            // 如果还是没有找到，设置默认值
            if (!finalCategory) {
                finalCategory = '基站'; // 默认类别
                console.log('🔧 使用默认类别:', finalCategory);
            }
        }
        
        console.log('🔧 最终使用的类别:', finalCategory);
        
        this.hideMenu();
        
        const form = this.createManualInputForm(finalCategory, productName);
        document.body.appendChild(form);
    }
    
    /**
     * 创建手动输入表单
     */
    createManualInputForm(category, productName) {
        console.log('🔧 创建手动输入表单，参数:', {
            category: category,
            productName: productName,
            categoryForTemplate: category || 'EMPTY_CATEGORY'
        });
        
        const overlay = document.createElement('div');
        overlay.className = 'manual-input-overlay';
        
        const formContainer = document.createElement('div');
        formContainer.className = 'manual-input-form';
        formContainer.innerHTML = `
            <div class="card" style="width: 500px;">
                <div class="card-header">
                    <h5>手动输入产品信息</h5>
                    <button type="button" class="btn-close close-manual-form"></button>
                </div>
                <div class="card-body">
                    <form id="manualProductForm">
                        <div class="mb-3">
                            <label class="form-label">产品类别</label>
                            <input type="text" class="form-control" 
                                   value="${category || '未分类'}" 
                                   readonly 
                                   style="background-color: #f8f9fa; color: #6c757d;">
                            <small class="form-text text-muted">产品将保存到此类别下</small>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">产品名称 *</label>
                            <input type="text" class="form-control" name="product_name" 
                                   value="${productName}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">产品型号 *</label>
                            <input type="text" class="form-control" name="product_model" 
                                   placeholder="请输入产品型号" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">产品描述 *</label>
                            <textarea class="form-control" name="product_desc" rows="3" 
                                      placeholder="请输入产品规格描述" required></textarea>
                        </div>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">品牌 *</label>
                                <input type="text" class="form-control" name="brand" 
                                       placeholder="产品品牌" required>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">单位 *</label>
                                <select class="form-control" name="unit" required>
                                    <option value="个">个</option>
                                    <option value="台">台</option>
                                    <option value="套">套</option>
                                    <option value="件">件</option>
                                    <option value="只">只</option>
                                    <option value="米">米</option>
                                    <option value="公斤">公斤</option>
                                </select>
                            </div>
                        </div>
                        <input type="hidden" name="category" value="${category || ''}">
                    </form>
                </div>
                <div class="card-footer text-end">
                    <button type="button" class="btn btn-secondary close-manual-form">取消</button>
                    <button type="button" class="btn btn-primary save-manual-product">保存并使用</button>
                </div>
            </div>
        `;
        
        // 绑定关闭事件
        const closeButtons = formContainer.querySelectorAll('.close-manual-form');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                document.body.removeChild(overlay);
            });
        });
        
        // 绑定保存事件
        const saveButton = formContainer.querySelector('.save-manual-product');
        saveButton.addEventListener('click', () => {
            this.handleManualProductSave(formContainer, category);
        });
        
        // ESC键关闭
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                document.body.removeChild(overlay);
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
        
        // 点击遮罩关闭
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                document.body.removeChild(overlay);
                document.removeEventListener('keydown', handleEscape);
            }
        });
        
        overlay.appendChild(formContainer);
        return overlay;
    }
    
    /**
     * 处理手动产品保存
     */
    async handleManualProductSave(formContainer, category) {
        const form = formContainer.querySelector('#manualProductForm');
        const formData = new FormData(form);
        
        // 从表单中获取category（以防参数为空）
        let categoryFromForm = formData.get('category') || category;
        
        // 进一步验证类别信息
        if (!categoryFromForm || categoryFromForm === '' || categoryFromForm === 'undefined' || categoryFromForm === 'null') {
            categoryFromForm = '基站'; // 默认类别
            console.log('🔧 类别信息无效，使用默认类别:', categoryFromForm);
        }
        
        console.log('🔧 保存临时产品，类别信息:', {
            parameterCategory: category,
            formCategory: formData.get('category'),
            finalCategory: categoryFromForm,
            isValidCategory: categoryFromForm !== '' && categoryFromForm !== 'undefined'
        });
        
        // 验证必填字段
        const requiredFields = ['product_name', 'product_model', 'product_desc', 'brand', 'unit'];
        const errors = [];
        
        for (const field of requiredFields) {
            if (!formData.get(field) || formData.get(field).trim() === '') {
                errors.push(`${this.getFieldLabel(field)}不能为空`);
            }
        }
        
        if (errors.length > 0) {
            alert('请填写完整信息：\n' + errors.join('\n'));
            return;
        }
        
        // 构造完整的分类路径
        const categoryPath = this.buildCategoryPath(categoryFromForm);
        
        // 尝试从当前输入框所在行获取单价信息
        let unitPrice = 0;
        if (this.currentInput) {
            const row = this.currentInput.closest('tr');
            if (row) {
                const unitPriceInput = row.querySelector('.unit_price-input');
                if (unitPriceInput && unitPriceInput.value) {
                    unitPrice = parseFloat(unitPriceInput.value) || 0;
                }
            }
        }
        
        // 生成临时产品MN号
        const tempMN = this.generateTempProductMN();
        
        // 构造产品对象
        const productData = {
            product_name: formData.get('product_name').trim(),
            product_model: formData.get('product_model').trim(),
            product_desc: formData.get('product_desc').trim(),
            brand: formData.get('brand').trim(),
            unit: formData.get('unit'),
            category: categoryFromForm,
            category_path: categoryPath,
            unit_price: unitPrice,
            reference_price: unitPrice,
            market_price: unitPrice,
            currency: 'CNY',
            status: 'temp',
            is_temp: true,
            product_mn: tempMN,  // 前端生成的临时MN号
            mn: tempMN          // 兼容字段
        };
        
        console.log('🔧 构造的产品数据:', productData);
        
        // 保存按钮加载状态
        const saveButton = formContainer.querySelector('.save-manual-product');
        const originalText = saveButton.textContent;
        saveButton.disabled = true;
        saveButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 保存中...';
        
        try {
            // 如果启用自动保存，先保存到后端
            if (this.config.temp_products.auto_save) {
                await this.saveTempProduct(productData);
            }
            
            // 触发产品选择回调
            if (this.config.onSelect) {
                this.config.onSelect(productData, this.currentInput);
            }
            
            // 关闭表单
            const overlay = formContainer.closest('.manual-input-overlay');
            if (overlay) {
                document.body.removeChild(overlay);
            }
            
        } catch (error) {
            console.error('保存临时产品失败:', error);
            alert('保存失败，但产品信息已填入表格。错误信息：' + error.message);
            
            // 即使保存失败，也要触发选择回调，让用户可以继续使用
            if (this.config.onSelect) {
                this.config.onSelect(productData, this.currentInput);
            }
            
            // 关闭表单
            const overlay = formContainer.closest('.manual-input-overlay');
            if (overlay) {
                document.body.removeChild(overlay);
            }
            
        } finally {
            // 恢复按钮状态
            saveButton.disabled = false;
            saveButton.textContent = originalText;
        }
    }
    
    /**
     * 保存临时产品到后端
     */
    async saveTempProduct(productData) {
        if (!this.config.apiEndpoints.saveTempProduct) {
            console.warn('未配置临时产品保存端点');
            return;
        }
        
        console.log('🔧 发送临时产品数据:', productData);
        
        // 获取CSRF令牌
        const csrfToken = document.querySelector('input[name="csrf_token"]')?.value ||
                         document.querySelector('meta[name="csrf-token"]')?.content;
        
        const headers = {
            'Content-Type': 'application/json',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        };
        
        // 添加CSRF令牌（如果存在）
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
        
        const response = await fetch(this.config.apiEndpoints.saveTempProduct, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(productData)
        });
        
        if (!response.ok) {
            let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            try {
                const errorData = await response.json();
                if (errorData.message) {
                    errorMessage += ` - ${errorData.message}`;
                }
                console.error('🔥 后端返回错误:', errorData);
            } catch (e) {
                console.error('🔥 无法解析错误响应:', e);
            }
            throw new Error(errorMessage);
        }
        
        const result = await response.json();
        console.log('✅ 临时产品保存成功:', result);
        
        if (!result.success) {
            throw new Error(result.message || '保存临时产品失败');
        }
        
        return result;
    }
    
    /**
     * 加载临时产品名称列表（显示在产品名称二级菜单中）
     * 只显示临时产品库独有的产品名称，与常规产品重复的不显示
     */
    async loadTempProductNames(container, category, menu) {
        if (!this.config.apiEndpoints.tempProducts || !this.config.apiEndpoints.productsByCategory) {
            return;
        }
        
        try {
            
            // 同时获取常规产品和临时产品
            const [regularProducts, tempProducts] = await Promise.all([
                this.fetchData('productsByCategory', { category }),
                this.fetchData('tempProducts', { category })
            ]);
            
            // 处理临时产品API响应格式
            let tempProductList = tempProducts;
            if (tempProducts && typeof tempProducts === 'object' && tempProducts.data) {
                tempProductList = tempProducts.data;
            }
            
            if (!tempProductList || !Array.isArray(tempProductList) || tempProductList.length === 0) {
                return;
            }
            
            // 获取常规产品的所有产品名称
            const regularProductNames = new Set();
            if (regularProducts && Array.isArray(regularProducts)) {
                regularProducts.forEach(product => {
                    regularProductNames.add(product.product_name);
                });
            }
            
            console.log('📋 常规产品名称列表:', Array.from(regularProductNames));
            
            // 按产品名称分组统计，只包含临时产品独有的名称
            const tempProductGroups = {};
            tempProductList.forEach(product => {
                const productName = product.product_name;
                
                // 只处理临时产品独有的产品名称
                if (!regularProductNames.has(productName)) {
                    if (!tempProductGroups[productName]) {
                        tempProductGroups[productName] = {
                            count: 0,
                            totalUsage: 0
                        };
                    }
                    tempProductGroups[productName].count++;
                    tempProductGroups[productName].totalUsage += product.usage_count || 0;
                }
            });
            
            
            // 添加分隔线（如果有临时产品）
            if (Object.keys(tempProductGroups).length > 0) {
                const separator = document.createElement('div');
                separator.className = 'temp-products-separator';
                separator.style.cssText = `
                    border-top: 2px dashed #ff9800;
                    margin: 8px 0;
                    position: relative;
                    text-align: center;
                `;
                separator.innerHTML = `
                    <span style="background: white; padding: 0 8px; color: #ff9800; font-size: 11px; font-weight: 500;">
                        临时产品 (${Object.keys(tempProductGroups).length})
                    </span>
                `;
                container.appendChild(separator);
            }
            
            // 显示临时产品名称，按使用次数排序
            Object.keys(tempProductGroups)
                .sort((a, b) => tempProductGroups[b].totalUsage - tempProductGroups[a].totalUsage)
                .forEach(productName => {
                    const group = tempProductGroups[productName];
                    const item = document.createElement('div');
                    item.className = 'menu-item temp-product-name-item';
                    
                    // 临时产品专用样式 - 橙色边框和背景
                    item.style.borderLeft = '4px solid #ff9800';
                    item.style.backgroundColor = '#fff8f0';
                    
                    item.innerHTML = `
                        <div class="product-info">
                            <div class="product-name" style="color: #e65100;">${productName}</div>
                            <div class="product-details" style="color: #ff9800;">${group.count} 个型号</div>
                        </div>
                    `;
                    item.dataset.productName = productName;
                    item.dataset.category = category;
                    item.dataset.isTempProduct = 'true';
                    
                    // 添加鼠标悬停和点击事件
                    let hoverTimer;
                    
                    item.addEventListener('mouseenter', () => {
                        item.classList.add('hover-expanding');
                        hoverTimer = setTimeout(() => {
                            this.selectProduct(menu, category, productName);
                        }, 200);
                    });
                    
                    item.addEventListener('mouseleave', () => {
                        item.classList.remove('hover-expanding');
                        if (hoverTimer) {
                            clearTimeout(hoverTimer);
                        }
                    });
                    
                    item.addEventListener('click', () => {
                        if (hoverTimer) {
                            clearTimeout(hoverTimer);
                        }
                        this.selectProduct(menu, category, productName);
                    });
                    
                    container.appendChild(item);
                });
                
            console.log(`✅ 已添加 ${Object.keys(tempProductGroups).length} 个临时产品名称`);
            
        } catch (error) {
            console.error('❌ 加载临时产品名称失败:', error);
        }
    }
    
    /**
     * 根据容器查找对应的菜单元素
     */
    findMenuForContainer(container) {
        return container.closest('.product-selector-menu');
    }
    
    /**
     * 加载临时产品（按类别）
     */
    async loadTempProducts(container, category) {
        if (!this.config.apiEndpoints.tempProducts) {
            return;
        }
        
        try {
            const tempProducts = await this.fetchData('tempProducts', { category });
            
            if (tempProducts && tempProducts.length > 0) {
                // 添加分隔线
                const separator = document.createElement('div');
                separator.className = 'temp-products-separator';
                separator.style.cssText = `
                    border-top: 2px dashed #ddd;
                    margin: 10px 0;
                    position: relative;
                    text-align: center;
                `;
                separator.innerHTML = `
                    <span style="background: white; padding: 0 10px; color: #666; font-size: 12px;">
                        临时产品 (${tempProducts.length})
                    </span>
                `;
                container.appendChild(separator);
                
                // 添加临时产品
                tempProducts.forEach(product => {
                    const item = document.createElement('div');
                    item.className = 'menu-item product-detail-item no-arrow';

                    // 临时产品样式
                    item.style.borderLeft = '4px solid #ff9800';
                    item.style.backgroundColor = '#fff3e0';
                    item.style.display = 'flex';
                    item.style.alignItems = 'center';
                    
                    item.innerHTML = `
                        <div class="product-detail-info" style="flex: 1;">
                            <div class="product-line-1" style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong class="product-model">${product.product_model}</strong>
                                    <span class="${this.config.manual_input.temp_indicator.style}">
                                        ${this.config.manual_input.temp_indicator.text}
                                    </span>
                                </div>
                                <button class="temp-delete-btn" 
                                        style="background: none; border: none; color: #dc3545; 
                                               font-size: 14px; cursor: pointer; padding: 2px; 
                                               opacity: 0; transition: opacity 0.3s ease, color 0.2s ease;
                                               display: flex; align-items: center; justify-content: center;
                                               width: 20px; height: 20px; border-radius: 3px;"
                                        onmouseover="this.style.color='#c82333'; this.style.backgroundColor='rgba(220, 53, 69, 0.1)'"
                                        onmouseout="this.style.color='#dc3545'; this.style.backgroundColor='none'"
                                        title="删除临时产品">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                            <div class="product-line-2">
                                <span class="product-spec">${product.product_desc || '无规格说明'}</span>
                            </div>
                            <div class="product-line-3">
                                <span class="product-mn">MN: ${product.product_mn || '无'}</span>
                                <span class="product-brand">品牌: ${product.brand || '未知'}</span>
                            </div>
                        </div>
                    `;
                    
                    // 为整个item添加鼠标悬停效果，控制删除按钮的显示/隐藏
                    const deleteBtn = item.querySelector('.temp-delete-btn');
                    
                    item.addEventListener('mouseenter', () => {
                        deleteBtn.style.opacity = '1';
                    });
                    
                    item.addEventListener('mouseleave', () => {
                        deleteBtn.style.opacity = '0';
                    });
                    
                    // 为产品信息区域添加点击事件（选择产品）
                    const productInfo = item.querySelector('.product-detail-info');
                    productInfo.addEventListener('click', (e) => {
                        // 如果点击的是删除按钮区域，不执行选择逻辑
                        if (e.target.closest('.temp-delete-btn')) {
                            return;
                        }
                        
                        // 增加使用次数
                        if (this.config.temp_products.auto_save) {
                            this.incrementTempProductUsage(product.id);
                        }
                        
                        // 选择临时产品
                        if (this.config.onSelect) {
                            this.config.onSelect(product, this.currentInput);
                        }
                        
                        this.hideMenu();
                    });
                    
                    // 为删除按钮添加点击事件
                    deleteBtn.addEventListener('click', (e) => {
                        e.stopPropagation(); // 阻止事件冒泡
                        this.showDeleteConfirmDialog(product, () => {
                            // 删除确认后的回调
                            this.deleteTempProduct(product.id, item);
                        });
                    });
                    
                    container.appendChild(item);
                });
            }
            
        } catch (error) {
            console.warn('加载临时产品失败:', error);
        }
    }
    
    /**
     * 加载特定产品名称下的临时产品
     */
    async loadTempProductsByProductName(container, category, productName) {
        if (!this.config.apiEndpoints.tempProductsByCategory) {
            console.warn('⚠️ tempProductsByCategory端点未配置');
            return;
        }
        
        try {
            
            const tempProducts = await this.fetchData('tempProductsByCategory', { 
                category, 
                product_name: productName 
            });
            
            console.log('📦 临时产品API响应:', tempProducts);
            
            // 处理API响应格式 - 有些API返回直接数组，有些返回包装对象
            let productList = tempProducts;
            if (tempProducts && typeof tempProducts === 'object' && tempProducts.data) {
                productList = tempProducts.data;
            }
            
            console.log('📋 解析后的产品列表:', productList);
            
            if (productList && Array.isArray(productList) && productList.length > 0) {
                // 添加分隔线，在临时产品前
                const separator = document.createElement('div');
                separator.className = 'temp-products-separator';
                separator.style.cssText = `
                    border-top: 2px dashed #ff9800;
                    margin: 8px 0;
                    position: relative;
                    text-align: center;
                `;
                separator.innerHTML = `
                    <span style="background: white; padding: 0 8px; color: #ff9800; font-size: 11px; font-weight: 500;">
                        临时产品 (${productList.length})
                    </span>
                `;
                container.appendChild(separator);
                
                // 添加临时产品，按使用次数排序
                productList.forEach(product => {
                    const item = document.createElement('div');
                    item.className = 'menu-item product-detail-item temp-product-item';
                    
                    // 临时产品专用样式
                    item.style.borderLeft = '4px solid #ff9800';
                    item.style.backgroundColor = '#fff8f0';
                    item.style.marginBottom = '4px';
                    item.style.display = 'flex';
                    item.style.alignItems = 'center';
                    
                    // 格式化参考价格
                    const referencePrice = product.reference_price || 0;
                    const priceText = referencePrice > 0 ?
                        `参考价: ${this.formatPriceWithCurrency(referencePrice, product.currency)}` :
                        '参考价: 面议';
                    
                    item.innerHTML = `
                        <div class="product-detail-info" style="flex: 1;">
                            <div class="product-line-1" style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="display: flex; align-items: center;">
                                    <strong class="product-model">${product.product_model}</strong>
                                    <span class="temp-indicator" style="
                                        background: #ff9800;
                                        color: white;
                                        padding: 1px 6px;
                                        border-radius: 10px;
                                        font-size: 10px;
                                        font-weight: 500;
                                        margin-left: 8px;
                                    ">临时</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span class="product-price" style="font-weight: bold;">${priceText}</span>
                                    <button class="temp-delete-btn"
                                            style="background: none; border: none; color: #dc3545;
                                                   font-size: 14px; cursor: pointer; padding: 2px;
                                                   opacity: 0; transition: opacity 0.3s ease, color 0.2s ease;
                                                   display: flex; align-items: center; justify-content: center;
                                                   width: 20px; height: 20px; border-radius: 3px;"
                                            onmouseover="this.style.color='#c82333'; this.style.backgroundColor='rgba(220, 53, 69, 0.1)'"
                                            onmouseout="this.style.color='#dc3545'; this.style.backgroundColor='none'"
                                            title="删除临时产品">
                                        <i class="fas fa-times"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="product-line-2">
                                <span class="product-spec">${product.product_desc || '无规格说明'}</span>
                            </div>
                            <div class="product-line-3">
                                <span class="product-mn">MN: ${product.product_mn || '无'}</span>
                                <span class="product-brand">品牌: ${product.brand || '未知'}</span>
                            </div>
                        </div>
                    `;
                    
                    // 为整个item添加鼠标悬停效果，控制删除按钮的显示/隐藏
                    const deleteBtn = item.querySelector('.temp-delete-btn');
                    
                    item.addEventListener('mouseenter', () => {
                        deleteBtn.style.opacity = '1';
                    });
                    
                    item.addEventListener('mouseleave', () => {
                        deleteBtn.style.opacity = '0';
                    });
                    
                    // 为产品信息区域添加点击事件（选择产品）
                    const productInfo = item.querySelector('.product-detail-info');
                    productInfo.addEventListener('click', (e) => {
                        // 如果点击的是删除按钮区域，不执行选择逻辑
                        if (e.target.closest('.temp-delete-btn')) {
                            return;
                        }
                        
                        // 增加使用次数
                        if (this.config.temp_products.auto_save) {
                            this.incrementTempProductUsage(product.id);
                        }
                        
                        // 构造完整的临时产品信息
                        const selectedTempProduct = {
                            product_name: product.product_name,
                            product_model: product.product_model,
                            product_desc: product.product_desc,
                            product_spec: product.product_desc,
                            brand: product.brand || '未知品牌',
                            unit: product.unit || '个',
                            market_price: product.reference_price || 0,
                            product_mn: `TEMP_${product.id}`,
                            currency: product.currency || 'CNY',
                            status: 'temp',
                            is_temp: true,
                            temp_product_id: product.id,
                            usage_count: product.usage_count
                        };
                        
                        // 选择临时产品
                        if (this.config.onSelect) {
                            this.config.onSelect(selectedTempProduct, this.currentInput);
                        }
                        
                        this.hideMenu();
                    });
                    
                    // 为删除按钮添加点击事件
                    deleteBtn.addEventListener('click', (e) => {
                        e.stopPropagation(); // 阻止事件冒泡
                        this.showDeleteConfirmDialog(product, () => {
                            // 删除确认后的回调
                            this.deleteTempProduct(product.id, item);
                        });
                    });
                    
                    container.appendChild(item);
                });
            }
            
        } catch (error) {
            console.error('❌ 加载特定产品临时产品失败:', error);
            console.error('🔍 失败的参数:', { category, productName, endpoint: this.config.apiEndpoints.tempProductsByCategory });
        }
    }
    
    /**
     * 增加临时产品使用次数
     */
    async incrementTempProductUsage(productId) {
        try {
            console.log('🔧 增加临时产品使用次数:', productId);
            
            // 获取CSRF令牌
            const csrfToken = document.querySelector('input[name="csrf_token"]')?.value ||
                             document.querySelector('meta[name="csrf-token"]')?.content;
            
            const headers = {
                'Content-Type': 'application/json'
            };
            
            // 添加CSRF令牌（如果存在）
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
            }
            
            const url = `${this.config.apiEndpoints.tempProducts}/${productId}/increment`;
            console.log('🔧 请求URL:', url);
            
            const response = await fetch(url, {
                method: 'POST',
                headers: headers
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('✅ 使用次数更新成功:', result);
            
        } catch (error) {
            console.error('❌ 更新使用次数失败:', error);
        }
    }
    
    /**
     * 获取字段标签
     */
    /**
     * 构建分类路径
     */
    buildCategoryPath(category) {
        // 基于当前分类构建完整路径
        // 这里假设category是三级分类的最后一级
        // 实际实现中可能需要查询完整的分类层级关系
        
        // 暂时返回category本身，后续可以扩展为完整路径
        return category;
    }
    
    getFieldLabel(fieldName) {
        const labels = {
            product_name: '产品名称',
            product_model: '产品型号',
            product_desc: '产品描述',
            brand: '品牌',
            unit: '单位'
        };
        return labels[fieldName] || fieldName;
    }
    
    /**
     * 显示删除确认对话框
     */
    showDeleteConfirmDialog(product, onConfirm) {
        // 创建确认对话框
        const overlay = document.createElement('div');
        overlay.className = 'delete-confirm-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        const dialog = document.createElement('div');
        dialog.className = 'delete-confirm-dialog';
        dialog.style.cssText = `
            background: white;
            border-radius: 8px;
            padding: 24px;
            max-width: 400px;
            width: 90%;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        `;
        
        dialog.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <i class="fas fa-exclamation-triangle" style="color: #f39c12; font-size: 24px; margin-right: 12px;"></i>
                <h3 style="margin: 0; color: #333;">确认删除临时产品</h3>
            </div>
            <div style="margin-bottom: 24px; color: #666; line-height: 1.5;">
                <p style="margin: 0 0 8px 0;">确定要删除以下临时产品吗？</p>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 4px; border-left: 4px solid #ff9800;">
                    <strong style="color: #333;">${product.product_model}</strong><br>
                    <span style="color: #666; font-size: 14px;">${product.product_desc || '无规格说明'}</span><br>
                    <span style="color: #666; font-size: 14px;">品牌: ${product.brand || '未知'}</span>
                </div>
                <p style="margin: 12px 0 0 0; color: #dc3545; font-size: 14px;">
                    <i class="fas fa-info-circle" style="margin-right: 4px;"></i>
                    此操作不可恢复，删除后将无法在产品选择器中找到该产品。
                </p>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 12px;">
                <button type="button" class="btn btn-secondary cancel-btn">取消</button>
                <button type="button" class="btn btn-danger confirm-btn">确认删除</button>
            </div>
        `;
        
        // 绑定事件
        const cancelBtn = dialog.querySelector('.cancel-btn');
        const confirmBtn = dialog.querySelector('.confirm-btn');
        
        cancelBtn.addEventListener('click', () => {
            document.body.removeChild(overlay);
        });
        
        confirmBtn.addEventListener('click', () => {
            document.body.removeChild(overlay);
            onConfirm();
        });
        
        // 点击遮罩关闭
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                document.body.removeChild(overlay);
            }
        });
        
        // ESC键关闭
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                document.body.removeChild(overlay);
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
        
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);
        
        // 聚焦到取消按钮
        setTimeout(() => cancelBtn.focus(), 100);
    }
    
    /**
     * 删除临时产品
     */
    async deleteTempProduct(productId, itemElement) {
        try {
            console.log('🗑️ 删除临时产品:', productId);
            
            const response = await fetch(`/api/v1/temp-products/${productId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                
                // 尝试解析错误响应
                try {
                    const errorData = await response.json();
                    if (errorData.message) {
                        errorMessage = errorData.message;
                    }
                } catch (parseError) {
                    console.warn('无法解析错误响应:', parseError);
                }
                
                // 如果是404错误，说明产品已经被删除了
                if (response.status === 404) {
                    console.warn('⚠️ 临时产品不存在，可能已被删除:', productId);
                    // 仍然从DOM中移除该项
                    this.removeTempProductFromDOM(productId, itemElement);
                    // 从缓存中移除已删除的产品，不影响菜单结构
                    this.clearTempProductCacheSelectively(productId);
                    this.showNotification('该临时产品已不存在，已从列表中移除', 'warning');
                    return;
                }
                
                throw new Error(errorMessage);
            }
            
            const result = await response.json();
            
            if (result.success) {
                // 删除成功，从DOM中移除该项
                this.removeTempProductFromDOM(productId, itemElement);
                
                // 从缓存中移除已删除的产品，不影响菜单结构
                this.clearTempProductCacheSelectively(productId);
                
                console.log('✅ 临时产品删除成功:', productId);
                
                // 显示成功提示
                this.showNotification('临时产品已删除', 'success');
                
            } else {
                throw new Error(result.message || '删除失败');
            }
            
        } catch (error) {
            console.error('❌ 删除临时产品失败:', error);
            this.showNotification('删除临时产品失败: ' + error.message, 'error');
        }
    }
    
    /**
     * 显示通知消息
     */
    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = 'temp-product-notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 16px;
            border-radius: 4px;
            color: white;
            font-size: 14px;
            z-index: 10001;
            max-width: 300px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;
        
        // 根据类型设置颜色
        switch (type) {
            case 'success':
                notification.style.backgroundColor = '#28a745';
                break;
            case 'error':
                notification.style.backgroundColor = '#dc3545';
                break;
            case 'warning':
                notification.style.backgroundColor = '#ffc107';
                notification.style.color = '#212529';
                break;
            default:
                notification.style.backgroundColor = '#17a2b8';
        }
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center;">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}" 
                   style="margin-right: 8px;"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // 动画显示
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // 3秒后自动消失
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
    
    /**
     * 生成临时产品MN号
     * 格式: TP{YYMMDDHHMM}，例如：TP2504101012
     * 如果同一分钟内有重复（极小概率），在末尾添加随机数字
     */
    generateTempProductMN() {
        const now = new Date();
        
        // 格式化时间为 YYMMDDHHMM
        const year = now.getFullYear().toString().slice(-2);  // 后两位年份
        const month = (now.getMonth() + 1).toString().padStart(2, '0');
        const day = now.getDate().toString().padStart(2, '0');
        const hour = now.getHours().toString().padStart(2, '0');
        const minute = now.getMinutes().toString().padStart(2, '0');
        
        const timeStr = `${year}${month}${day}${hour}${minute}`;
        const baseMN = `TP${timeStr}`;
        
        console.log('🏷️ 生成临时产品MN号:', baseMN);
        
        // 在极小概率下，如果需要避免重复，可以加上毫秒数的后两位
        // 但通常情况下，分钟级精度已经足够避免冲突
        return baseMN;
    }
    
    /**
     * 销毁组件
     */
    destroy() {
        this.closeAllMenus();
        this.clearCache();
        
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
    }
}

// 导出到全局命名空间
window.ProductSelector = ProductSelector;