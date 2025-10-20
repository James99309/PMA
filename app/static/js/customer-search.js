/**
 * 通用客户搜索组件
 * 支持关键词搜索，权限过滤，显示公司名称、联系人等信息
 * 
 * @author Claude AI
 * @version 1.0.0
 */

class CustomerSearchComponent {
    constructor(config, container) {
        this.config = this.mergeConfig(config);
        this.container = container;
        this.selectedCustomer = null;
        this.searchTimeout = null;
        this.isLoading = false;
        
        this.init();
    }
    
    /**
     * 合并默认配置和用户配置
     */
    mergeConfig(config) {
        const defaultConfig = {
            // 基础配置
            input_id: 'customerSearch',
            input_name: 'customer_search',
            dropdown_id: 'customerDropdown',
            clear_button_id: 'clearCustomer',
            customer_id_field: 'customerId',
            customer_id_name: 'customer_id',
            data_element_id: 'customerSearchConfig',

            // 标签和占位符
            label: '选择客户',
            placeholder: '输入公司名称进行搜索...',

            // API配置
            api_endpoints: {
                search: '/api/export-helpers/customers/search'
            },

            // 搜索配置
            search_config: {
                min_length: 1,
                delay: 300,
                limit: 10,
                company_type: '',  // 可选的公司类型过滤，如 'dealer', 'user', 'designer', 'integrator' 等
                has_inventory: false  // 可选的库存过滤，true表示只显示有库存的公司
            },

            // 显示配置
            display_config: {
                show_contact: true,
                show_industry: true,
                show_owner: true
            },

            // 验证配置
            validation: {
                required: true,
                validate_on_submit: true
            }
        };
        
        return Object.assign({}, defaultConfig, config);
    }
    
    /**
     * 初始化组件
     */
    init() {
        // 获取DOM元素
        this.searchInput = this.container.querySelector(`#${this.config.input_id}`);
        this.dropdown = this.container.querySelector(`#${this.config.dropdown_id}`);
        this.clearBtn = this.container.querySelector(`#${this.config.clear_button_id}`);
        this.hiddenInput = this.container.querySelector(`#${this.config.customer_id_field}`);
        this.customerList = this.dropdown.querySelector('.customer-list');
        this.loadingElement = this.dropdown.querySelector('.dropdown-loading');
        this.noResultsElement = this.dropdown.querySelector('.no-results');
        
        if (!this.searchInput || !this.dropdown) {
            console.error('客户搜索组件关键元素未找到');
            return;
        }
        
        this.bindEvents();
        
        console.log('客户搜索组件初始化完成');
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 搜索输入事件
        this.searchInput.addEventListener('input', (e) => this.handleSearchInput(e));
        this.searchInput.addEventListener('focus', (e) => this.handleInputFocus(e));
        this.searchInput.addEventListener('blur', (e) => this.handleInputBlur(e));
        this.searchInput.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        // 清除按钮事件
        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', () => this.clearSelection());
        }
        
        // 点击外部关闭下拉框
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.hideDropdown();
            }
        });
        
        // 下拉框点击事件代理
        this.customerList.addEventListener('click', (e) => this.handleCustomerSelect(e));
    }
    
    /**
     * 处理搜索输入
     */
    handleSearchInput(e) {
        const query = e.target.value.trim();
        
        // 清除之前的搜索超时
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // 如果输入为空，隐藏下拉框
        if (!query) {
            this.hideDropdown();
            this.updateClearButton();
            return;
        }
        
        // 检查最小搜索长度
        if (query.length < this.config.search_config.min_length) {
            return;
        }
        
        // 延时搜索
        this.searchTimeout = setTimeout(() => {
            this.performSearch(query);
        }, this.config.search_config.delay);
    }
    
    /**
     * 处理输入框获得焦点
     */
    handleInputFocus(e) {
        const query = e.target.value.trim();

        // 所有选择器点击时都自动展开，提供一致的用户体验
        if (!query) {
            // 输入为空时，自动触发搜索显示结果
            // 实现"点击展开，输入过滤"的用户体验
            this.performSearch('');
        } else if (query.length >= this.config.search_config.min_length) {
            // 有输入内容且符合最小长度要求，显示之前的搜索结果
            this.showDropdown();
        }
    }
    
    /**
     * 处理输入框失去焦点
     */
    handleInputBlur(e) {
        // 延时隐藏，允许点击下拉框项目
        setTimeout(() => {
            if (!this.container.contains(document.activeElement)) {
                this.hideDropdown();
            }
        }, 150);
    }
    
    /**
     * 处理键盘事件
     */
    handleKeydown(e) {
        const items = this.customerList.querySelectorAll('.customer-item');
        const activeItem = this.customerList.querySelector('.customer-item.active');
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.navigateItems(items, activeItem, 1);
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.navigateItems(items, activeItem, -1);
                break;
            case 'Enter':
                e.preventDefault();
                if (activeItem) {
                    this.selectCustomerFromElement(activeItem);
                }
                break;
            case 'Escape':
                this.hideDropdown();
                break;
        }
    }
    
    /**
     * 导航项目（键盘上下箭头）
     */
    navigateItems(items, activeItem, direction) {
        if (items.length === 0) return;
        
        let newIndex = 0;
        
        if (activeItem) {
            const currentIndex = Array.from(items).indexOf(activeItem);
            newIndex = currentIndex + direction;
            
            // 循环导航
            if (newIndex < 0) newIndex = items.length - 1;
            if (newIndex >= items.length) newIndex = 0;
            
            activeItem.classList.remove('active');
        }
        
        items[newIndex].classList.add('active');
        items[newIndex].scrollIntoView({ block: 'nearest' });
    }
    
    /**
     * 执行搜索
     */
    async performSearch(query) {
        if (this.isLoading) return;

        this.isLoading = true;
        this.showDropdown();
        this.showLoading();

        try {
            const url = new URL(this.config.api_endpoints.search, window.location.origin);

            // 只在有查询词的情况下才添加search参数
            // 这样可以支持空搜索（当有过滤条件时）
            if (query) {
                url.searchParams.append('search', query);
            }

            url.searchParams.append('limit', this.config.search_config.limit);

            // 添加company_type过滤参数（如果配置了）
            if (this.config.search_config.company_type) {
                url.searchParams.append('company_type', this.config.search_config.company_type);
            }

            // 添加has_inventory过滤参数（如果配置了）
            if (this.config.search_config.has_inventory) {
                url.searchParams.append('has_inventory', 'true');
            }

            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`搜索请求失败: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.renderResults(data.results);
            } else {
                console.error('客户搜索失败:', data.error);
                this.showNoResults();
            }

        } catch (error) {
            console.error('客户搜索请求失败:', error);
            this.showNoResults();
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }
    
    /**
     * 渲染搜索结果
     */
    renderResults(customers) {
        this.customerList.innerHTML = '';
        
        if (!customers || customers.length === 0) {
            this.showNoResults();
            return;
        }
        
        customers.forEach(customer => {
            const item = this.createCustomerItem(customer);
            this.customerList.appendChild(item);
        });
        
        this.hideNoResults();
    }
    
    /**
     * 创建客户项目元素
     */
    createCustomerItem(customer) {
        const item = document.createElement('div');
        item.className = 'customer-item';
        item.dataset.customerId = customer.id;
        item.dataset.customerData = JSON.stringify(customer);

        // 构建显示内容
        const metaItems = [];

        // 公司类型徽章 - 使用API返回的徽章信息（复用通用系统）
        let companyTypeBadge = '';
        if (customer.company_type && customer.company_type_label && customer.company_type_color) {
            // 使用与 render_company_type_badge() 相同的徽章样式
            companyTypeBadge = `<span class="badge rounded-pill me-2" style="background-color: ${customer.company_type_color}; color: #fff; font-size: 0.75rem; padding: 0.35em 0.65em;">${customer.company_type_label}</span>`;
        }

        // 联系人信息
        if (this.config.display_config.show_contact && customer.contact_person) {
            metaItems.push(`<span class="meta-item"><span class="meta-label">联系人:</span><span class="meta-value">${customer.contact_person}</span></span>`);
        }

        // 行业信息
        if (this.config.display_config.show_industry && customer.industry) {
            metaItems.push(`<span class="meta-item"><span class="meta-label">行业:</span><span class="meta-value">${customer.industry}</span></span>`);
        }

        // 拥有者信息
        let ownerInfo = '';
        if (this.config.display_config.show_owner && customer.owner) {
            const ownerClass = customer.owner.is_vendor_user ? 'badge-user vendor' : 'badge-user regular';
            const ownerName = customer.owner.real_name || customer.owner.username;
            ownerInfo = `<div class="owner-info"><span class="badge ${ownerClass}">${ownerName}</span></div>`;
        }

        item.innerHTML = `
            <div class="customer-single-line">
                <div class="customer-main-section">
                    <div class="customer-name">${companyTypeBadge}${customer.company_name || '未知公司'}</div>
                    <div class="customer-meta-info">
                        ${metaItems.join('<span class="meta-divider"></span>')}
                    </div>
                </div>
                ${ownerInfo}
            </div>
        `;

        return item;
    }
    
    /**
     * 处理客户选择
     */
    handleCustomerSelect(e) {
        const customerItem = e.target.closest('.customer-item');
        if (!customerItem) return;
        
        this.selectCustomerFromElement(customerItem);
    }
    
    /**
     * 从元素选择客户
     */
    selectCustomerFromElement(element) {
        try {
            const customerData = JSON.parse(element.dataset.customerData);
            this.setSelectedCustomer(customerData);
            this.hideDropdown();
        } catch (error) {
            console.error('解析客户数据失败:', error);
        }
    }
    
    /**
     * 设置选中的客户
     */
    setSelectedCustomer(customer) {
        this.selectedCustomer = customer;
        
        // 更新显示
        this.searchInput.value = customer.company_name || '';
        this.hiddenInput.value = customer.id || '';
        
        // 更新清除按钮显示
        this.updateClearButton();
        
        // 触发自定义事件
        this.container.dispatchEvent(new CustomEvent('customerSelected', {
            detail: { customer: customer }
        }));
        
        console.log('已选择客户:', customer);
    }
    
    /**
     * 清除选择
     */
    clearSelection() {
        this.selectedCustomer = null;
        this.searchInput.value = '';
        this.hiddenInput.value = '';
        
        // 更新清除按钮显示
        this.updateClearButton();
        
        // 隐藏下拉框
        this.hideDropdown();
        
        // 触发自定义事件
        this.container.dispatchEvent(new CustomEvent('customerCleared'));
        
        // 聚焦到搜索框
        this.searchInput.focus();
        
        console.log('已清除客户选择');
    }
    
    /**
     * 更新清除按钮显示状态
     */
    updateClearButton() {
        if (!this.clearBtn) return;
        
        const hasValue = this.searchInput.value.trim() !== '';
        this.clearBtn.style.display = hasValue ? 'block' : 'none';
    }
    
    /**
     * 显示下拉框
     */
    showDropdown() {
        this.dropdown.style.display = 'block';
    }
    
    /**
     * 隐藏下拉框
     */
    hideDropdown() {
        this.dropdown.style.display = 'none';
        
        // 清除活动状态
        const activeItems = this.customerList.querySelectorAll('.customer-item.active');
        activeItems.forEach(item => item.classList.remove('active'));
    }
    
    /**
     * 显示加载状态
     */
    showLoading() {
        this.loadingElement.style.display = 'block';
        this.customerList.style.display = 'none';
        this.noResultsElement.style.display = 'none';
    }
    
    /**
     * 隐藏加载状态
     */
    hideLoading() {
        this.loadingElement.style.display = 'none';
        this.customerList.style.display = 'block';
    }
    
    /**
     * 显示无结果提示
     */
    showNoResults() {
        this.customerList.style.display = 'none';
        this.noResultsElement.style.display = 'block';
    }
    
    /**
     * 隐藏无结果提示
     */
    hideNoResults() {
        this.noResultsElement.style.display = 'none';
    }
    
    /**
     * 获取选中的客户
     */
    getSelectedCustomer() {
        return this.selectedCustomer;
    }
    
    /**
     * 验证选择
     */
    validate() {
        if (this.config.validation.required && !this.selectedCustomer) {
            this.searchInput.classList.add('is-invalid');
            return false;
        }
        
        this.searchInput.classList.remove('is-invalid');
        return true;
    }
    
    /**
     * 重置组件
     */
    reset() {
        this.clearSelection();
        this.searchInput.classList.remove('is-invalid');
    }
}

// 全局工具函数
window.CustomerSearchComponent = CustomerSearchComponent;