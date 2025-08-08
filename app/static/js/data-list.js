/**
 * =============================================================================
 * ⚠️  通用模组保护声明 ⚠️
 * =============================================================================
 * 
 * 此文件是PMA系统的通用数据列表组件JavaScript核心文件
 * 被所有使用通用列表组件的页面共同依赖
 * 
 * 🚨 修改保护协议 🚨
 * - 本文件的任何修改都会影响整个系统的列表功能
 * - 禁止随意修改此文件中的任何代码
 * - 如需修改，必须：
 *   1. 详细分析影响范围和风险  
 *   2. 获得项目负责人明确同意
 *   3. 进行充分测试验证
 *   4. 记录修改原因和影响范围
 * 
 * 📋 核心功能列表：
 * - setupDataList: 数据列表初始化
 * - updateStatsFromAjax: 统计数据更新
 * - loadInitialData: 初始数据加载
 * - setupInfiniteScroll: 无限滚动功能
 * - initializeTableEnhancements: 表格增强功能
 * 
 * 🔒 修改前请三思！
 * =============================================================================
 * 
 * 通用数据列表组件 JavaScript 功能
 * 提供标准化的列表交互功能，与筛选搜索组件集成
 */

/**
 * 检测是否为移动设备
 * @returns {boolean} 是否为移动设备
 */
function isMobileDevice() {
    // 检查URL参数（优先级最高，用于强制切换）
    const urlParams = new URLSearchParams(window.location.search);
    const mobileParam = urlParams.get('mobile');
    if (mobileParam === 'true') return true;
    if (mobileParam === 'false') return false;
    
    // 检查User-Agent（与服务器端保持一致）
    const userAgent = navigator.userAgent.toLowerCase();
    const mobileKeywords = ['mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'];
    return mobileKeywords.some(keyword => userAgent.includes(keyword));
}

/**
 * 获取移动端AJAX目标容器
 * @param {string} desktopTarget - 桌面端目标选择器
 * @returns {string} 移动端目标选择器
 */
function getMobileAjaxTarget(desktopTarget) {
    // 桌面端目标通常是表格body，移动端需要定位到卡片容器
    return '.product-list-mobile .p-3';
}

/**
 * 设置数据列表功能
 * @param {Object} config - 配置对象
 * @param {string} config.module_name - 模块名称
 * @param {Object} config.stats - 统计配置（可选）
 * @param {Object} config.filter - 筛选配置（可选）
 * @param {Object} config.table - 表格配置
 * @param {boolean} config.ajax_mode - 是否启用AJAX模式（默认false）
 * @param {string} config.ajax_endpoint - AJAX端点URL（AJAX模式必需）
 * @param {string} config.ajax_target - AJAX更新目标选择器（AJAX模式必需）
 * @param {Function} config.onStatsUpdate - 统计数据更新回调（可选）
 * @param {Function} config.onDataLoad - 数据加载完成回调（可选）
 */
function setupDataList(config) {
    console.log('🚀 正在设置数据列表功能:', config);
    
    // 保存当前配置到全局变量，供其他函数使用
    window.currentDataListConfig = config;
    
    // 验证必需的配置
    if (!config.module_name) {
        console.error('❌ 数据列表配置错误：缺少 module_name');
        return;
    }
    
    if (config.ajax_mode && (!config.ajax_endpoint || !config.ajax_target)) {
        console.error('❌ AJAX模式配置错误：缺少 ajax_endpoint 或 ajax_target');
        return;
    }
    
    // 统计卡片初始化（仅显示功能，无交互）
    if (config.stats && config.stats.cards) {
        console.log('📊 统计卡片已初始化（仅显示模式）');
    }
    
    // 初始化筛选搜索功能（如果配置了）
    if (config.filter) {
        // 如果是AJAX模式，需要配置筛选搜索的AJAX参数
        if (config.ajax_mode) {
            config.filter.ajax_mode = true;
            config.filter.ajax_endpoint = config.ajax_endpoint;
            config.filter.ajax_target = config.ajax_target;
            config.filter.ajax_columns = config.table.columns ? config.table.columns.length : 5;
            
            // 移动端支持：添加设备检测参数
            config.filter.ajax_params = config.filter.ajax_params || {};
            config.filter.ajax_params.mobile = isMobileDevice() ? 'true' : 'false';
            
            // 传递无限滚动配置给筛选搜索组件
            const infiniteScrollConfig = config.table && config.table.infinite_scroll ? config.table.infinite_scroll : config.infinite_scroll;
            if (infiniteScrollConfig) {
                config.filter.infinite_scroll = infiniteScrollConfig;
            }
            
            // 添加数据列表的成功回调
            const originalOnSuccess = config.filter.onSuccess;
            config.filter.onSuccess = function(data) {
                // 调用原有的成功回调
                if (originalOnSuccess && typeof originalOnSuccess === 'function') {
                    originalOnSuccess(data);
                }
                
                // 更新统计数据
                if (config.stats && data.statistics) {
                    updateStatsFromAjax(config, data.statistics);
                }
                
                // 更新列表项计数
                const isFiltered = isCurrentlyFiltered();
                console.log('🔢 列表项计数更新:', {
                    loaded_count: data.loaded_count,
                    total_count: data.total_count,
                    isFiltered: isFiltered
                });
                // 显示筛选条件下的总项目数，而不是已加载数
                updateListItemCount(data.total_count || 0, data.total_count || 0, isFiltered);
                
                // 更新无限滚动状态
                const infiniteScrollConfig = config.table && config.table.infinite_scroll ? config.table.infinite_scroll : config.infinite_scroll;
                if (infiniteScrollConfig && infiniteScrollConfig.enabled) {
                    // 筛选时重置状态
                    resetInfiniteScrollState();
                    // 设置正确的当前偏移量（筛选后重新开始，使用实际加载的数据量）
                    infiniteScrollState.currentOffset = data.loaded_count || 0;
                    // 更新hasMore状态
                    infiniteScrollState.hasMore = data.has_more !== false; // 默认为true，除非明确为false
                    infiniteScrollState.initialLoadComplete = true; // 筛选完成后也要设置初始加载完成
                    console.log('🔄 更新无限滚动状态:', {
                        currentOffset: infiniteScrollState.currentOffset,
                        hasMore: infiniteScrollState.hasMore,
                        totalCount: data.total_count,
                        initialLoadComplete: infiniteScrollState.initialLoadComplete
                    });
                }
                
                // 调用数据列表的加载完成回调
                if (config.onDataLoad && typeof config.onDataLoad === 'function') {
                    config.onDataLoad(data);
                }
            };
        }
        
        // 初始化筛选搜索功能
        if (typeof setupFilterSearch === 'function') {
            setupFilterSearch(config.filter);
        } else {
            console.warn('⚠️ setupFilterSearch 函数未找到，请确保引入了 filter-search.js');
        }
    }
    
    // 自动初始化无限滚动功能（如果启用）
    const infiniteScrollConfig = config.table && config.table.infinite_scroll ? config.table.infinite_scroll : config.infinite_scroll;
    console.log('🔍 检查无限滚动配置:', {
        ajax_mode: config.ajax_mode,
        infinite_scroll: infiniteScrollConfig,
        enabled: infiniteScrollConfig && infiniteScrollConfig.enabled
    });
    
    if (config.ajax_mode && infiniteScrollConfig && infiniteScrollConfig.enabled) {
        console.log('🔄 自动初始化无限滚动功能');
        // 将无限滚动配置传递给setupInfiniteScroll函数
        const configWithInfiniteScroll = { ...config, infinite_scroll: infiniteScrollConfig };
        setupInfiniteScroll(configWithInfiniteScroll);
    } else {
        console.log('⚠️ 无限滚动未启用或配置不完整');
    }
    
    // 初始化列表项计数显示
    if (config.ajax_mode) {
        // 确保列表项计数元素可见
        const countElement = document.getElementById('listItemCount');
        if (countElement) {
            countElement.style.display = 'inline-block';
            // 如果当前没有显示数据（即显示的是默认内容），则设置为加载状态
            if (countElement.textContent.includes('加载中')) {
                setListItemCountLoading();
            }
        }
        
        // 只在没有配置筛选或筛选未启用自动提交时，才手动触发数据加载
        if (!config.filter || !config.filter.auto_submit) {
            // 检查是否已有初始数据
            const targetElement = document.querySelector(config.ajax_target);
            const noDataText = (config.i18n && config.i18n.noData) || '暂无数据';
            const loadingText = (config.i18n && config.i18n.loading) || '加载中';
            const hasInitialData = targetElement && targetElement.children.length > 0 && 
                                 !targetElement.textContent.includes(noDataText) &&
                                 !targetElement.textContent.includes(loadingText);
            
            if (!hasInitialData) {
                console.log('🔄 手动触发初始数据加载（筛选未配置或未启用自动提交）');
                setTimeout(() => {
                    loadInitialData(config);
                }, 500);
            }
        } else {
            console.log('✅ 筛选组件将自动处理初始数据加载（auto_submit已启用）');
        }
    }
    
    // 初始化表格增强功能
    initializeTableEnhancements(config);
    
    console.log('✅ 数据列表功能设置完成');
}



/**
 * 从AJAX响应更新统计数据（支持语言感知的货币单位）
 * @param {Object} config - 配置对象
 * @param {Object} statistics - 统计数据
 */
function updateStatsFromAjax(config, statistics) {
    console.log('📊 更新统计数据:', statistics);
    
    if (!config.stats || !config.stats.cards) return;
    
    config.stats.cards.forEach(card => {
        // 支持两种键名格式：直接键名（total）和键名_count格式（total_count）
        const countKey = statistics[card.data_key] !== undefined ? card.data_key : card.data_key + '_count';
        // 特殊处理total的amount键名
        const amountKey = card.data_key === 'total' ? 'total_amount' : card.data_key + '_amount';
        
        if (statistics[countKey] !== undefined) {
            const countElement = document.getElementById(`${card.id}Count`);
            const amountElement = document.getElementById(`${card.id}Amount`);
            
            if (countElement) {
                const countValue = statistics[countKey];
                countElement.textContent = formatNumber(countValue);
                console.log(`📊 更新卡片 ${card.id} 数量: ${countValue}`);
            }
            
            if (amountElement && statistics[amountKey] !== undefined) {
                const value = statistics[amountKey];
                // 确保value是数字类型，如果不是则转换为0
                const numericValue = (typeof value === 'number' && !isNaN(value)) ? value : 
                                   (typeof value === 'string' && !isNaN(parseFloat(value))) ? parseFloat(value) : 0;
                
                // 获取单位配置（优先从AJAX数据获取，支持动态语言切换）
                let unitConfig = card.unit_config;
                
                // 从AJAX数据中获取单位配置
                if (statistics.unit_configs && statistics.unit_configs[card.data_key]) {
                    unitConfig = statistics.unit_configs[card.data_key];
                    console.log(`📊 使用AJAX单位配置 ${card.data_key}:`, unitConfig);
                } else {
                    // 从元素的data属性获取
                    const unitElement = document.getElementById(`${card.id}Unit`);
                    if (unitElement && unitElement.dataset.unitConfig) {
                        try {
                            unitConfig = JSON.parse(unitElement.dataset.unitConfig);
                        } catch (e) {
                            console.warn('解析unit_config失败:', e);
                        }
                    }
                }
                
                // 使用单位配置进行格式化
                let formattedValue, displayUnit;
                if (unitConfig) {
                    const convertedValue = numericValue / (unitConfig.divisor || 1);
                    formattedValue = convertedValue.toFixed(unitConfig.decimal_places || 2);
                    displayUnit = unitConfig.unit || '万元';
                } else {
                    // 向后兼容：使用原有的格式化逻辑
                    formattedValue = card.amount_format === 'wan' ? 
                        (numericValue / 10000).toFixed(2) : 
                        numericValue.toFixed(2);
                    displayUnit = card.amount_unit || '万元';
                }
                
                // 添加千位分隔符
                const parts = formattedValue.split('.');
                parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
                const formattedWithCommas = parts.join('.');
                
                // 添加货币符号 - 优先从配置中获取，然后从单位配置中获取，最后使用默认值
                let currencySymbol = config.currency_symbol;
                if (!currencySymbol && unitConfig && unitConfig.currency_symbol) {
                    currencySymbol = unitConfig.currency_symbol;
                }
                if (!currencySymbol) {
                    currencySymbol = '¥';  // 默认货币符号
                }
                amountElement.textContent = currencySymbol + formattedWithCommas;
                
                // 更新单位显示
                const unitElement = document.getElementById(`${card.id}Unit`);
                if (unitElement && displayUnit) {
                    unitElement.textContent = displayUnit;
                    console.log(`📊 更新单位显示 ${card.id}: ${displayUnit}`);
                }
                
                console.log(`📊 更新卡片 ${card.id} 金额: ${currencySymbol}${formattedWithCommas}${displayUnit}`);
            }
        }
    });
    
    // 调用自定义统计更新回调
    if (config.onStatsUpdate && typeof config.onStatsUpdate === 'function') {
        config.onStatsUpdate(statistics);
    }
}

/**
 * 更新列表项计数显示
 * @param {number} currentCount - 当前筛选条件下的项数
 * @param {number} unused - 未使用参数（保持兼容性）
 * @param {boolean} isFiltered - 是否为筛选状态
 */
function updateListItemCount(currentCount, unused, isFiltered = false) {
    const countElement = document.getElementById('listItemCount');
    if (!countElement) return;
    
    console.log(`🔢 更新列表计数: 当前条件下共 ${currentCount} 项，筛选状态: ${isFiltered}`);
    
    // 移除所有状态类，然后根据状态添加对应的类
    countElement.classList.remove('count-loading', 'count-total', 'count-filtered', 'count-empty');
    
    // 显示当前筛选条件下的项目总数
    if (currentCount === 0) {
        countElement.classList.add('count-empty');
        const noDataText = (window.currentDataListConfig && window.currentDataListConfig.i18n && window.currentDataListConfig.i18n.noData) || '暂无数据';
        countElement.innerHTML = `<i class="fas fa-inbox me-1"></i>${noDataText}`;
    } else {
        // 根据是否有筛选条件显示不同颜色
        countElement.classList.add(isFiltered ? 'count-filtered' : 'count-total');
        const itemsText = (window.currentDataListConfig && window.currentDataListConfig.i18n && window.currentDataListConfig.i18n.items) || '项';
        countElement.innerHTML = `<i class="fas fa-list me-1"></i>${formatNumber(currentCount)} ${itemsText}`;
    }
}

/**
 * 设置列表计数为加载状态
 */
function setListItemCountLoading() {
    const countElement = document.getElementById('listItemCount');
    if (!countElement) return;
    
    console.log('⏳ 设置列表计数为加载状态');
    
    // 移除其他状态类，添加加载状态类
    countElement.classList.remove('count-total', 'count-filtered', 'count-empty');
    countElement.classList.add('count-loading');
    const loadingText = (window.currentDataListConfig && window.currentDataListConfig.i18n && window.currentDataListConfig.i18n.loading) || '加载中';
    countElement.innerHTML = loadingText;
}

/**
 * 加载初始数据（仅AJAX模式）
 * @param {Object} config - 配置对象
 */
function loadInitialData(config) {
    if (!config.ajax_mode) return;
    
    console.log('🔄 加载初始数据');
    
    const targetElement = document.querySelector(config.ajax_target);
    if (!targetElement) {
        console.error(`❌ 找不到目标元素: ${config.ajax_target}`);
        return;
    }
    
    // 显示加载状态
    const columns = config.table.columns ? config.table.columns.length : 5;
    targetElement.innerHTML = `
        <tr>
            <td colspan="${columns}" class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <div class="mt-2">正在加载数据...</div>
            </td>
        </tr>
    `;
    
    // 设置列表计数为加载状态
    setListItemCountLoading();
    
    // 构建请求URL
    const url = new URL(config.ajax_endpoint, window.location.origin);
    url.searchParams.set('offset', 0);
    
    // 使用无限滚动配置的分页大小，如果没有配置则使用默认20
    const infiniteScrollConfig = config.table && config.table.infinite_scroll ? config.table.infinite_scroll : config.infinite_scroll;
    const pageSize = (infiniteScrollConfig && infiniteScrollConfig.page_size) ? 
        infiniteScrollConfig.page_size : 20;
    url.searchParams.set('limit', pageSize);
    
    // 发送AJAX请求
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('✅ 初始数据加载成功:', data);
            
            // 更新表格内容
            const noDataText = (config.i18n && config.i18n.noData) || '暂无数据';
            targetElement.innerHTML = data.html || `
                <tr>
                    <td colspan="${columns}" class="text-center py-4">${noDataText}</td>
                </tr>
            `;
            
            // 设置初始加载完成标志，启用无限滚动
            infiniteScrollState.initialLoadComplete = true;
            
            // 根据实际加载的数据量更新当前偏移量
            infiniteScrollState.currentOffset = data.loaded_count || 0;
            infiniteScrollState.hasMore = data.has_more !== false;
            
            // 如果初始加载就有数据且还有更多数据，立即尝试检查滚动位置
            if (data.loaded_count > 0 && data.has_more && window.debugInfiniteScroll) {
                setTimeout(() => {
                    console.log('🔄 初始加载完成，检查是否需要自动加载更多数据...');
                    window.debugInfiniteScroll.checkScrollPosition();
                }, 100);
            }
            
            console.log('🔄 初始加载完成，设置无限滚动状态:', {
                initialLoadComplete: infiniteScrollState.initialLoadComplete,
                currentOffset: infiniteScrollState.currentOffset,
                hasMore: infiniteScrollState.hasMore
            });
            
            // 更新统计数据
            if (config.stats && data.statistics) {
                updateStatsFromAjax(config, data.statistics);
            }
            
            // 更新列表项计数
            const isFiltered = isCurrentlyFiltered();
            updateListItemCount(data.total_count || 0, data.total_count || 0, isFiltered);
            
            // 调用加载完成回调
            if (config.onDataLoad && typeof config.onDataLoad === 'function') {
                config.onDataLoad(data);
            }
        })
        .catch(error => {
            console.error('❌ 初始数据加载失败:', error);
            targetElement.innerHTML = `
                <tr>
                    <td colspan="${columns}" class="text-center text-danger py-4">
                        <i class="fas fa-exclamation-triangle"></i> 加载失败：${error.message}
                    </td>
                </tr>
            `;
        });
}

/**
 * 检查当前是否处于筛选状态
 * @returns {boolean} 是否为筛选状态
 */
function isCurrentlyFiltered() {
    // 检查搜索框是否有值
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput && searchInput.value.trim()) {
        return true;
    }
    
    // 检查所有筛选下拉框（更通用的选择器）
    const filterSelects = document.querySelectorAll('select[name]:not([name="search"])');
    for (let select of filterSelects) {
        if (select.value && select.value !== '' && select.value !== '0') {
            return true;
        }
    }
    
    // 检查其他筛选输入框
    const filterInputs = document.querySelectorAll('input[name]:not([name="search"]):not([type="hidden"]):not([type="submit"])');
    for (let input of filterInputs) {
        if (input.value && input.value.trim() !== '') {
            return true;
        }
    }
    
    return false;
}

/**
 * 格式化数字显示
 * @param {number} value - 数值
 * @returns {string} 格式化后的数字字符串
 */
function formatNumber(value) {
    // 处理各种可能的无效值
    if (value === null || value === undefined || value === '') return '0';
    
    // 转换为数字类型
    let numericValue;
    if (typeof value === 'number') {
        numericValue = value;
    } else if (typeof value === 'string') {
        numericValue = parseFloat(value);
    } else {
        numericValue = 0;
    }
    
    // 检查是否为有效数字
    if (isNaN(numericValue) || !isFinite(numericValue)) {
        return '0';
    }
    
    // 使用千分位分隔符，并确保为整数
    return Math.round(numericValue).toLocaleString();
}

/**
 * 获取当前模块的配置
 * @param {string} moduleName - 模块名称
 * @returns {Object|null} 配置对象
 */
function getDataListConfig(moduleName) {
    // 从全局变量获取配置
    const configName = `${moduleName}ListConfig`;
    return window[configName] || null;
}

/**
 * 设置全局配置（用于重置按钮等功能）
 * @param {string} moduleName - 模块名称
 * @param {Object} config - 配置对象
 */
function setGlobalDataListConfig(moduleName, config) {
    const configName = `${moduleName}ListConfig`;
    window[configName] = config;
    
    // 同时设置筛选搜索的全局配置（兼容现有重置按钮）
    if (config.filter) {
        window.filterSearchConfig = config.filter;
    }
}

// 全局无限滚动状态管理
let infiniteScrollState = {
    isLoading: false,
    hasMore: true,
    currentOffset: 0,
    lastLoadTime: null  // 上次加载时间，用于控制加载间隔
};

// 重置无限滚动状态的全局函数
function resetInfiniteScrollState() {
    infiniteScrollState.isLoading = false;
    infiniteScrollState.hasMore = true;
    infiniteScrollState.currentOffset = 0;
    infiniteScrollState.lastLoadTime = null;  // 重置时间戳
    console.log('🔄 重置无限滚动状态');
}

/**
 * 设置无限滚动功能
 * @param {Object} config - 配置对象
 */
function setupInfiniteScroll(config) {
    if (!config.ajax_mode || !config.ajax_endpoint || !config.ajax_target) {
        console.log('⚠️ 无限滚动需要AJAX模式，跳过初始化');
        return;
    }
    
    // 获取无限滚动配置，使用默认值
    const scrollConfig = config.infinite_scroll || {};
    const pageSize = scrollConfig.page_size || 60;
    
    // 根据设备类型调整滚动阈值 - 移动端使用更大的阈值减少触发频率
    const isMobile = isMobileDevice();
    const baseThreshold = scrollConfig.scroll_threshold || 100;
    const scrollThreshold = isMobile ? Math.max(baseThreshold * 3, 300) : baseThreshold;
    
    const containerSelector = scrollConfig.container_selector || '.table-responsive';
    const scrollMode = scrollConfig.scroll_mode || 'window'; // 'window' 或 'container'
    
    console.log('🔄 初始化无限滚动功能', {
        pageSize,
        scrollThreshold,
        containerSelector,
        scrollMode
    });
    
    // 初始化状态 - 等待初始数据加载完成后再设置offset
    infiniteScrollState.currentOffset = 0; // 先设置为0，等初始数据加载完成后更新
    infiniteScrollState.initialLoadComplete = false; // 初始加载完成标志
    const limit = pageSize;
    
    // 找到目标容器（用于检测底部位置）
    const targetContainer = document.querySelector(containerSelector);
    if (!targetContainer) {
        console.warn(`⚠️ 未找到目标容器 ${containerSelector}，无法初始化无限滚动`);
        return;
    }
    
    // 滚动防抖定时器
    let scrollDebounceTimer = null;
    
    // 滚动监听函数（带防抖）
    function handleScroll() {
        if (infiniteScrollState.isLoading || !infiniteScrollState.hasMore) return;
        
        // 清除上一次的定时器
        if (scrollDebounceTimer) {
            clearTimeout(scrollDebounceTimer);
        }
        
        // 移动端使用更长的防抖延迟
        const debounceDelay = isMobile ? 200 : 100;
        
        // 设置新的定时器
        scrollDebounceTimer = setTimeout(() => {
            checkScrollPosition();
        }, debounceDelay);
    }
    
    // 检查滚动位置
    function checkScrollPosition() {
        
        if (scrollMode === 'window') {
            // 窗口滚动模式：监听页面滚动，检测是否接近表格底部
            const windowScrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const windowHeight = window.innerHeight;
            const tableRect = targetContainer.getBoundingClientRect();
            const tableBottom = tableRect.bottom + windowScrollTop;
            
            // 调试日志：显示滚动检测参数
            console.log(`📏 滚动检测参数:`, {
                windowScrollTop: Math.round(windowScrollTop),
                windowHeight: Math.round(windowHeight),
                tableBottom: Math.round(tableBottom),
                scrollThreshold: scrollThreshold,
                triggerPoint: Math.round(tableBottom - scrollThreshold),
                currentPosition: Math.round(windowScrollTop + windowHeight),
                shouldTrigger: windowScrollTop + windowHeight >= tableBottom - scrollThreshold,
                hasMore: infiniteScrollState.hasMore,
                isLoading: infiniteScrollState.isLoading
            });
            
            // 当滚动接近表格底部时触发加载
            if (windowScrollTop + windowHeight >= tableBottom - scrollThreshold) {
                console.log(`🔄 窗口滚动触发加载更多数据 (阈值: ${scrollThreshold}px, 设备: ${isMobile ? '移动端' : '桌面端'})`);
                loadMoreData();
            }
        } else {
            // 容器滚动模式：监听容器内部滚动
            const scrollTop = targetContainer.scrollTop;
            const scrollHeight = targetContainer.scrollHeight;
            const clientHeight = targetContainer.clientHeight;
            
            // 当滚动到容器底部附近时触发加载
            if (scrollTop + clientHeight >= scrollHeight - scrollThreshold) {
                console.log(`🔄 容器滚动触发加载更多数据 (阈值: ${scrollThreshold}px, 设备: ${isMobile ? '移动端' : '桌面端'})`);
                loadMoreData();
            }
        }
    }
    
    // 加载更多数据
    function loadMoreData() {
        if (infiniteScrollState.isLoading || !infiniteScrollState.hasMore || !infiniteScrollState.initialLoadComplete) {
            // 如果正在加载、没有更多数据，或者初始加载还没完成，则跳过
            return;
        }
        
        // 添加时间间隔控制，防止过于频繁的请求
        const now = Date.now();
        const minInterval = isMobile ? 1000 : 500; // 移动端最小间隔1秒，桌面端0.5秒
        if (infiniteScrollState.lastLoadTime && (now - infiniteScrollState.lastLoadTime) < minInterval) {
            console.log(`⏱️ 请求间隔过短，跳过加载 (距离上次: ${now - infiniteScrollState.lastLoadTime}ms)`);
            return;
        }
        
        infiniteScrollState.isLoading = true;
        infiniteScrollState.lastLoadTime = now;
        console.log(`🔄 加载更多数据: offset=${infiniteScrollState.currentOffset}, limit=${limit}`);
        
        // 显示加载提示
        showLoadingIndicator();
        
        // 获取当前筛选参数
        const formData = new FormData(document.querySelector('form'));
        const params = new URLSearchParams();
        
        // 添加筛选参数
        for (let [key, value] of formData.entries()) {
            if (value) params.append(key, value);
        }
        
        // 添加分页参数
        params.append('offset', infiniteScrollState.currentOffset);
        params.append('limit', limit);
        
        // 发送AJAX请求
        fetch(`${config.ajax_endpoint}?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.html) {
                    // 将新数据追加到表格
                    const targetElement = document.querySelector(config.ajax_target);
                    if (targetElement) {
                        targetElement.insertAdjacentHTML('beforeend', data.html);
                    }
                    
                    // 更新状态
                    infiniteScrollState.currentOffset += limit;
                    infiniteScrollState.hasMore = data.has_more;
                    
                    console.log(`✅ 加载成功: 新增数据，当前offset=${infiniteScrollState.currentOffset}，还有更多: ${infiniteScrollState.hasMore}`);
                    
                    // 更新统计数据（可选，因为滚动加载不应该改变统计）
                    if (config.stats && data.statistics) {
                        updateStatsFromAjax(config, data.statistics);
                    }
                } else {
                    console.error('❌ 加载更多数据失败:', data.message);
                    infiniteScrollState.hasMore = false;
                }
            })
            .catch(error => {
                console.error('❌ 无限滚动AJAX请求失败:', error);
                infiniteScrollState.hasMore = false;
            })
            .finally(() => {
                infiniteScrollState.isLoading = false;
                hideLoadingIndicator();
            });
    }
    
    // 显示加载提示
    function showLoadingIndicator() {
        let indicator = document.getElementById('infiniteScrollLoading');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'infiniteScrollLoading';
            indicator.className = 'text-center py-3 text-muted';
            indicator.innerHTML = '加载更多...';
            
            const tableContainer = targetContainer.querySelector('table');
            if (tableContainer) {
                tableContainer.parentNode.insertBefore(indicator, tableContainer.nextSibling);
            }
        }
        indicator.style.display = 'block';
    }
    
    // 隐藏加载提示
    function hideLoadingIndicator() {
        const indicator = document.getElementById('infiniteScrollLoading');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
    
    // 绑定滚动事件
    if (scrollMode === 'window') {
        // 窗口滚动模式：监听窗口滚动事件
        window.addEventListener('scroll', handleScroll, { passive: true });
        console.log('✅ 绑定窗口滚动事件监听器');
    } else {
        // 容器滚动模式：监听容器滚动事件
        targetContainer.addEventListener('scroll', handleScroll, { passive: true });
        console.log('✅ 绑定容器滚动事件监听器');
    }
    
    // 监听筛选重置事件（全局状态管理，不需要本地重置函数）
    document.addEventListener('filterReset', resetInfiniteScrollState);
    
    // 暴露调试方法到全局作用域
    window.debugInfiniteScroll = {
        checkScrollPosition: checkScrollPosition,
        loadMoreData: loadMoreData,
        getState: () => infiniteScrollState,
        resetState: resetInfiniteScrollState,
        getConfig: () => scrollConfig
    };
    document.addEventListener('filterSubmit', resetInfiniteScrollState);
    
    console.log('✅ 无限滚动功能初始化完成');
}

/**
 * 初始化表格增强功能
 * @param {Object} config - 配置对象
 */
function initializeTableEnhancements(config) {
    const tableContainer = document.querySelector('.table-responsive');
    if (!tableContainer) {
        console.log('⚠️ 未找到表格容器，跳过表格增强功能初始化');
        return;
    }
    
    console.log('🎨 初始化表格增强功能');
    
    // 滚动位置记忆功能
    const scrollKey = config.module_name + 'ListScrollTop';
    const scrollLeftKey = config.module_name + 'ListScrollLeft';
    
    // 恢复滚动位置
    const savedScrollTop = sessionStorage.getItem(scrollKey);
    const savedScrollLeft = sessionStorage.getItem(scrollLeftKey);
    
    if (savedScrollTop !== null) {
        tableContainer.scrollTop = parseInt(savedScrollTop);
    }
    
    if (savedScrollLeft !== null) {
        tableContainer.scrollLeft = parseInt(savedScrollLeft);
    }
    
    // 保存滚动位置
    tableContainer.addEventListener('scroll', function() {
        sessionStorage.setItem(scrollKey, this.scrollTop);
        sessionStorage.setItem(scrollLeftKey, this.scrollLeft);
    });
    
    // 键盘导航支持
    document.addEventListener('keydown', function(e) {
        // 只有当表格区域可见且在视口中时才响应键盘事件
        if (isElementInViewport(tableContainer)) {
            switch(e.key) {
                case 'Home':
                    // Home键 - 滚动到顶部
                    tableContainer.scrollTop = 0;
                    e.preventDefault();
                    break;
                case 'End':
                    // End键 - 滚动到底部
                    tableContainer.scrollTop = tableContainer.scrollHeight;
                    e.preventDefault();
                    break;
                case 'PageUp':
                    // PageUp键 - 向上翻页
                    tableContainer.scrollTop -= tableContainer.clientHeight;
                    e.preventDefault();
                    break;
                case 'PageDown':
                    // PageDown键 - 向下翻页
                    tableContainer.scrollTop += tableContainer.clientHeight;
                    e.preventDefault();
                    break;
            }
        }
    });
    
    console.log('✅ 表格增强功能初始化完成');
}

/**
 * 检查元素是否在视口中
 * @param {Element} element - 要检查的元素
 * @returns {boolean} 是否在视口中
 */
function isElementInViewport(element) {
    if (!element) return false;
    
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// 导出函数供全局使用
if (typeof window !== 'undefined') {
    window.setupDataList = setupDataList;
    window.updateStatsFromAjax = updateStatsFromAjax;
    window.updateListItemCount = updateListItemCount;
    window.setListItemCountLoading = setListItemCountLoading;
    window.isCurrentlyFiltered = isCurrentlyFiltered;
    window.getDataListConfig = getDataListConfig;
    window.setGlobalDataListConfig = setGlobalDataListConfig;
    window.setupInfiniteScroll = setupInfiniteScroll;
    window.resetInfiniteScrollState = resetInfiniteScrollState;
    window.initializeTableEnhancements = initializeTableEnhancements;
    window.isElementInViewport = isElementInViewport;
}