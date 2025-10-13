/*!
 * 关键词查询选择组件 (Keyword Selector Component)
 * 支持搜索、过滤、字段配置的通用选择器
 */

class KeywordSelector {
    constructor(config) {
        this.config = {
            // 基础配置
            container: null,                    // 容器元素选择器
            placeholder: '请输入关键词搜索...',   // 搜索框占位文本
            minChars: 1,                       // 最小搜索字符数
            debounceDelay: 300,                // 搜索防抖延迟(ms)
            maxResults: 20,                    // 最大结果数量
            
            // API配置
            searchEndpoint: '',                // 搜索API端点
            searchMethod: 'GET',               // 请求方法
            searchParam: 'search',             // 搜索参数名
            
            // 字段配置
            valueField: 'id',                  // 值字段名
            labelField: 'name',                // 显示标签字段名
            subLabelField: null,               // 副标签字段名（可选）
            searchFields: ['name'],            // 可搜索字段列表
            
            // 过滤配置
            filters: {},                       // 额外过滤参数
            filterFunction: null,              // 自定义过滤函数
            
            // 显示配置
            showClearButton: true,             // 显示清除按钮
            allowEmpty: true,                  // 允许空选择
            multiSelect: false,                // 多选模式
            autoExpandOnFocus: false,          // 聚焦时自动展开
            displayRenderer: null,             // 自定义显示渲染器
            resultRenderer: null,              // 自定义结果项渲染器
            
            // 回调函数
            onSelect: null,                    // 选择回调
            onClear: null,                     // 清除回调
            onError: null,                     // 错误回调
            onDataLoad: null,                  // 数据加载回调
            
            // 样式配置
            cssClass: 'keyword-selector',      // 主容器CSS类
            dropdownClass: 'keyword-dropdown', // 下拉框CSS类
            ...config
        };
        
        this.selectedItems = this.config.multiSelect ? [] : null;
        this.isOpen = false;
        this.searchTimeout = null;
        this.currentRequest = null;
        
        this.init();
    }
    
    init() {
        if (!this.config.container) {
            throw new Error('KeywordSelector: container is required');
        }
        
        if (!this.config.searchEndpoint) {
            throw new Error('KeywordSelector: searchEndpoint is required');
        }
        
        this.container = typeof this.config.container === 'string' 
            ? document.querySelector(this.config.container)
            : this.config.container;
            
        if (!this.container) {
            throw new Error('KeywordSelector: container element not found');
        }
        
        this.render();
        this.bindEvents();
    }
    
    render() {
        const html = `
            <div class="${this.config.cssClass}">
                <div class="keyword-input-wrapper">
                    <input type="text" 
                           class="keyword-input form-control" 
                           placeholder="${this.config.placeholder}"
                           autocomplete="off">
                    ${this.config.showClearButton ? '<button type="button" class="keyword-clear-btn" title="清除">&times;</button>' : ''}
                </div>
                <div class="${this.config.dropdownClass}" style="display: none;">
                    <div class="keyword-loading" style="display: none;">
                        <i class="fas fa-spinner fa-spin"></i> 搜索中...
                    </div>
                    <div class="keyword-results"></div>
                    <div class="keyword-no-results" style="display: none;">
                        未找到匹配结果
                    </div>
                </div>
                ${this.config.multiSelect ? '<div class="keyword-selected-items"></div>' : ''}
            </div>
        `;
        
        this.container.innerHTML = html;
        
        // 获取关键元素引用
        this.input = this.container.querySelector('.keyword-input');
        this.dropdown = this.container.querySelector(`.${this.config.dropdownClass}`);
        this.loadingEl = this.container.querySelector('.keyword-loading');
        this.resultsEl = this.container.querySelector('.keyword-results');
        this.noResultsEl = this.container.querySelector('.keyword-no-results');
        this.clearBtn = this.container.querySelector('.keyword-clear-btn');
        this.selectedItemsEl = this.container.querySelector('.keyword-selected-items');
    }
    
    bindEvents() {
        // 搜索输入事件
        this.input.addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });
        
        // 获得焦点时显示下拉框
        this.input.addEventListener('focus', () => {
            if (this.input.value.length >= this.config.minChars) {
                this.showDropdown();
            } else if (this.config.autoExpandOnFocus) {
                // 自动展开模式：聚焦时直接搜索
                this.performSearch('');
            }
        });
        
        // 失去焦点时隐藏下拉框（延迟处理点击事件）
        this.input.addEventListener('blur', () => {
            setTimeout(() => this.hideDropdown(), 150);
        });
        
        // 清除按钮事件
        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', () => {
                this.clear();
            });
        }
        
        // 键盘导航事件
        this.input.addEventListener('keydown', (e) => {
            this.handleKeyNavigation(e);
        });
        
        // 点击外部关闭下拉框
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.hideDropdown();
            }
        });
    }
    
    handleSearch(query) {
        // 清除之前的搜索定时器
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // 取消之前的请求
        if (this.currentRequest) {
            this.currentRequest.abort();
        }
        
        query = query.trim();
        
        if (query.length < this.config.minChars) {
            this.hideDropdown();
            return;
        }
        
        // 防抖搜索
        this.searchTimeout = setTimeout(() => {
            this.performSearch(query);
        }, this.config.debounceDelay);
    }
    
    async performSearch(query) {
        try {
            this.showLoading();
            this.showDropdown();
            
            // 构建搜索参数
            const params = new URLSearchParams({
                [this.config.searchParam]: query,
                limit: this.config.maxResults,
                ...this.config.filters
            });
            
            // 执行搜索请求
            const controller = new AbortController();
            this.currentRequest = controller;
            
            const response = await fetch(`${this.config.searchEndpoint}?${params}`, {
                method: this.config.searchMethod,
                signal: controller.signal,
                credentials: 'same-origin',  // 包含同源cookies
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    // 包含CSRF token（如果存在）
                    ...(document.querySelector('meta[name="csrf-token"]') && {
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                    })
                }
            });
            
            if (!response.ok) {
                throw new Error(`搜索请求失败: ${response.status}`);
            }
            
            const data = await response.json();
            this.displayResults(data.results || data.items || data);
            
            // 调用数据加载回调
            if (this.config.onDataLoad) {
                this.config.onDataLoad(data);
            }
            
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('搜索错误:', error);
                this.showNoResults();
                
                if (this.config.onError) {
                    this.config.onError(error);
                }
            }
        } finally {
            this.hideLoading();
            this.currentRequest = null;
        }
    }
    
    displayResults(results) {
        this.resultsEl.innerHTML = '';
        
        if (!results || results.length === 0) {
            this.showNoResults();
            return;
        }
        
        this.hideNoResults();
        
        // 应用自定义过滤函数
        if (this.config.filterFunction) {
            results = results.filter(this.config.filterFunction);
        }
        
        results.forEach(item => {
            const resultEl = this.createResultElement(item);
            this.resultsEl.appendChild(resultEl);
        });
    }
    
    createResultElement(item) {
        const div = document.createElement('div');
        div.className = 'keyword-result-item';
        div.dataset.value = item[this.config.valueField];
        
        if (this.config.resultRenderer) {
            // 使用自定义结果渲染器
            div.innerHTML = this.config.resultRenderer(item);
        } else {
            // 默认渲染
            const label = item[this.config.labelField] || '';
            const subLabel = this.config.subLabelField ? item[this.config.subLabelField] : '';
            
            div.innerHTML = `
                <div class="result-main-label">${this.escapeHtml(label)}</div>
                ${subLabel ? `<div class="result-sub-label">${this.escapeHtml(subLabel)}</div>` : ''}
            `;
        }
        
        div.addEventListener('click', () => {
            this.selectItem(item);
        });
        
        return div;
    }
    
    selectItem(item) {
        if (this.config.multiSelect) {
            // 多选模式
            const value = item[this.config.valueField];
            const existingIndex = this.selectedItems.findIndex(selected => 
                selected[this.config.valueField] === value
            );
            
            if (existingIndex === -1) {
                this.selectedItems.push(item);
                this.renderSelectedItems();
            }
        } else {
            // 单选模式
            this.selectedItems = item;
            if (this.config.displayRenderer) {
                // 使用自定义渲染器
                this.input.style.display = 'none';
                this.showSelectedDisplay(item);
            } else {
                this.input.value = item[this.config.labelField];
            }
        }
        
        this.hideDropdown();
        
        // 调用选择回调
        if (this.config.onSelect) {
            this.config.onSelect(item, this.selectedItems);
        }
    }
    
    renderSelectedItems() {
        if (!this.config.multiSelect || !this.selectedItemsEl) return;
        
        this.selectedItemsEl.innerHTML = '';
        
        this.selectedItems.forEach((item, index) => {
            const tag = document.createElement('span');
            tag.className = 'keyword-selected-tag';
            tag.innerHTML = `
                ${this.escapeHtml(item[this.config.labelField])}
                <button type="button" class="tag-remove" data-index="${index}">&times;</button>
            `;
            
            tag.querySelector('.tag-remove').addEventListener('click', () => {
                this.removeSelectedItem(index);
            });
            
            this.selectedItemsEl.appendChild(tag);
        });
        
        // 清空输入框
        this.input.value = '';
    }
    
    removeSelectedItem(index) {
        if (this.config.multiSelect && this.selectedItems.length > index) {
            this.selectedItems.splice(index, 1);
            this.renderSelectedItems();
            
            // 调用选择回调
            if (this.config.onSelect) {
                this.config.onSelect(null, this.selectedItems);
            }
        }
    }
    
    showSelectedDisplay(item) {
        // 创建或更新自定义显示元素
        if (!this.selectedDisplayEl) {
            this.selectedDisplayEl = document.createElement('div');
            this.selectedDisplayEl.className = 'keyword-selected-display';
            this.selectedDisplayEl.style.cssText = `
                position: relative;
                min-height: 38px;
                padding: 6px 12px;
                border: 1px solid #ced4da;
                border-radius: 0.375rem;
                background-color: #fff;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: space-between;
            `;
            
            // 添加到输入框容器中
            this.input.parentNode.appendChild(this.selectedDisplayEl);
            
            // 点击显示元素时重新聚焦到输入框
            this.selectedDisplayEl.addEventListener('click', () => {
                this.clearSelectedDisplay();
                this.input.focus();
            });
        }
        
        // 渲染内容
        const content = this.config.displayRenderer(item);
        const clearButton = this.config.showClearButton ? '<button type="button" class="btn-close btn-close-sm ms-2" style="font-size: 0.75em;"></button>' : '';
        this.selectedDisplayEl.innerHTML = `<div class="flex-grow-1">${content}</div>${clearButton}`;
        
        // 绑定清除按钮事件
        if (this.config.showClearButton) {
            const clearBtn = this.selectedDisplayEl.querySelector('.btn-close');
            if (clearBtn) {
                clearBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.clear();
                });
            }
        }
    }
    
    clearSelectedDisplay() {
        if (this.selectedDisplayEl) {
            this.selectedDisplayEl.remove();
            this.selectedDisplayEl = null;
        }
        this.input.style.display = '';
        this.input.value = '';
    }
    
    clear() {
        if (this.config.multiSelect) {
            this.selectedItems = [];
            this.renderSelectedItems();
        } else {
            this.selectedItems = null;
            if (this.config.displayRenderer) {
                this.clearSelectedDisplay();
            } else {
                this.input.value = '';
            }
        }
        
        this.hideDropdown();
        
        // 调用清除回调
        if (this.config.onClear) {
            this.config.onClear();
        }
    }
    
    getValue() {
        if (this.config.multiSelect) {
            return this.selectedItems.map(item => item[this.config.valueField]);
        } else {
            return this.selectedItems ? this.selectedItems[this.config.valueField] : null;
        }
    }
    
    getSelectedItems() {
        return this.selectedItems;
    }
    
    setValue(value) {
        // 通过API或预设数据设置选中值
        // 实现时需要根据具体需求调整
        if (this.config.multiSelect) {
            this.selectedItems = Array.isArray(value) ? value : [value];
            this.renderSelectedItems();
        } else {
            this.selectedItems = value;
            if (value) {
                this.input.value = value[this.config.labelField] || '';
            }
        }
    }
    
    showDropdown() {
        this.dropdown.style.display = 'block';
        this.isOpen = true;
    }
    
    hideDropdown() {
        this.dropdown.style.display = 'none';
        this.isOpen = false;
    }
    
    showLoading() {
        this.loadingEl.style.display = 'block';
        this.resultsEl.style.display = 'none';
        this.noResultsEl.style.display = 'none';
    }
    
    hideLoading() {
        this.loadingEl.style.display = 'none';
        this.resultsEl.style.display = 'block';
    }
    
    showNoResults() {
        this.resultsEl.style.display = 'none';
        this.noResultsEl.style.display = 'block';
    }
    
    hideNoResults() {
        this.noResultsEl.style.display = 'none';
    }
    
    handleKeyNavigation(e) {
        // 实现键盘导航逻辑
        const items = this.resultsEl.querySelectorAll('.keyword-result-item');
        const activeItem = this.resultsEl.querySelector('.keyword-result-item.active');
        
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
                    activeItem.click();
                }
                break;
            case 'Escape':
                this.hideDropdown();
                break;
        }
    }
    
    navigateItems(items, activeItem, direction) {
        if (items.length === 0) return;
        
        let currentIndex = -1;
        if (activeItem) {
            currentIndex = Array.from(items).indexOf(activeItem);
            activeItem.classList.remove('active');
        }
        
        const nextIndex = currentIndex + direction;
        
        if (nextIndex >= 0 && nextIndex < items.length) {
            items[nextIndex].classList.add('active');
        } else if (direction > 0 && nextIndex >= items.length) {
            items[0].classList.add('active');
        } else if (direction < 0 && nextIndex < 0) {
            items[items.length - 1].classList.add('active');
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    destroy() {
        // 清理资源
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        if (this.currentRequest) {
            this.currentRequest.abort();
        }
        
        this.container.innerHTML = '';
    }
}

// 导出为全局变量和模块
window.KeywordSelector = KeywordSelector;

// 如果支持模块导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KeywordSelector;
}