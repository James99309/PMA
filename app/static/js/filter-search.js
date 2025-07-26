/**
 * =============================================================================
 * ⚠️  通用模组保护声明 ⚠️
 * =============================================================================
 * 
 * 此文件是PMA系统的通用筛选搜索组件JavaScript核心文件
 * 被所有使用筛选搜索功能的页面共同依赖
 * 
 * 🚨 修改保护协议 🚨
 * - 本文件的任何修改都会影响整个系统的筛选搜索功能
 * - 禁止随意修改此文件中的任何代码
 * - 如需修改，必须：
 *   1. 详细分析影响范围和风险
 *   2. 获得项目负责人明确同意
 *   3. 进行充分测试验证
 *   4. 记录修改原因和影响范围
 * 
 * 📋 核心功能列表：
 * - setupFilterSearch: 筛选搜索初始化
 * - resetFilters: 重置筛选条件
 * - performAjaxSearch: AJAX搜索功能
 * - updateSearchResults: 搜索结果更新
 * 
 * 🔒 修改前请三思！
 * =============================================================================
 * 
 * 筛选搜索组件 JavaScript 功能
 * 提供标准化的筛选搜索交互功能
 */

/**
 * 检测移动设备
 * @returns {boolean} 是否为移动设备
 */
function detectMobileDevice() {
    // 优先检查URL参数
    const urlParams = new URLSearchParams(window.location.search);
    const mobileParam = urlParams.get('mobile');
    if (mobileParam === 'true') return true;
    if (mobileParam === 'false') return false;
    
    // 检查User-Agent
    const userAgent = navigator.userAgent.toLowerCase();
    const mobileKeywords = ['mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone'];
    return mobileKeywords.some(keyword => userAgent.includes(keyword));
}

/**
 * 重置筛选条件
 * @param {string} resetUrl - 重置后跳转的URL
 */
function resetFilters(resetUrl) {
    window.location.href = resetUrl;
}

/**
 * 设置筛选搜索功能
 * @param {Object} config - 配置对象
 * @param {string} config.form_id - 表单ID
 * @param {string} config.search_field_id - 搜索框ID
 * @param {boolean} config.realtime_search - 是否启用实时搜索
 * @param {string} config.search_mode - 搜索模式 ('server'|'client')
 * @param {number} config.search_delay - 搜索延迟时间(毫秒)
 * @param {boolean} config.auto_submit - 筛选器变化时是否自动提交
 * @param {Array} config.filter_fields - 筛选字段配置
 * @param {boolean} config.dynamic_reset_button - 是否启用动态重置按钮
 * @param {string} config.reset_button_id - 重置按钮ID
 * @param {boolean} config.adaptive_button_layout - 是否启用自适应按钮布局
 * @param {boolean} config.ajax_mode - 是否启用AJAX模式
 * @param {string} config.ajax_endpoint - AJAX筛选端点URL
 * @param {string} config.ajax_target - AJAX更新目标选择器
 * @param {number} config.ajax_columns - 表格列数（用于加载状态显示）
 * @param {Function} config.ajax_callback - 自定义AJAX回调函数（可选，用于复杂场景）
 * @param {Function} config.ajax_reset_callback - 自定义AJAX重置回调函数（可选）
 */
function setupFilterSearch(config) {
    console.log('正在设置筛选搜索功能:', config);
    
    const form = document.getElementById(config.form_id);
    if (!form) {
        console.warn(`筛选搜索表单未找到: ${config.form_id}`);
        return;
    }
    
    console.log(`✅ 找到表单: ${config.form_id}`);
    
    // 初始化自适应宽度功能
    if (config.adaptive_width !== false) {
        // 立即执行一次以避免闪烁，然后用requestAnimationFrame确保DOM渲染完成后再次调整
        adjustAdaptiveWidths();
        requestAnimationFrame(() => {
            adjustAdaptiveWidths();
            setupLanguageChangeListener();
        });
    }
    
    // 初始化自适应按钮布局
    if (config.adaptive_button_layout !== false) {
        setTimeout(() => {
            initializeAdaptiveButtonLayout(config);
            setupResizeListener(config);
        }, 100);
    }
    
    // 初始化动态重置按钮（延迟执行，确保表单值已正确设置）
    if (config.dynamic_reset_button) {
        setTimeout(() => {
            initializeDynamicResetButton(config);
        }, 200); // 延迟200ms，确保表单值完全同步
    }

    // 实时搜索配置
    if (config.realtime_search && config.search_field_id) {
        const searchInput = document.getElementById(config.search_field_id);
        if (searchInput) {
            let timeout;
            searchInput.addEventListener('input', function() {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    if (config.search_mode === 'client') {
                        performClientSearch(this.value, config);
                    } else if (config.ajax_mode) {
                        // AJAX模式实时搜索
                        if (config.ajax_callback && typeof config.ajax_callback === 'function') {
                            config.ajax_callback();
                        } else if (config.ajax_endpoint && config.ajax_target) {
                            performGenericAjaxFilter(config);
                        }
                    } else {
                        // 传统模式实时搜索
                        form.submit();
                    }
                }, config.search_delay || 300);
            });
            
            // 回车键搜索
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    if (config.ajax_mode) {
                        // AJAX模式回车搜索
                        if (config.ajax_callback && typeof config.ajax_callback === 'function') {
                            config.ajax_callback();
                        } else if (config.ajax_endpoint && config.ajax_target) {
                            performGenericAjaxFilter(config);
                        }
                    } else {
                        // 传统模式回车搜索
                        form.submit();
                    }
                }
            });
        }
    }
    
    // 筛选器变化事件
    if (config.filter_fields && config.auto_submit) {
        console.log('✅ 启用自动提交功能，监听筛选器变化');
        console.log('📋 筛选字段配置详情:', config.filter_fields);
        config.filter_fields.forEach(field => {
            const element = document.getElementById(field.name);
            if (element) {
                console.log(`📋 为字段 ${field.name} 添加变化监听器`);
                element.addEventListener('change', function() {
                    console.log(`🔄 筛选器 ${field.name} 变化，执行筛选`);
                    
                    // 执行筛选操作
                    if (config.ajax_mode) {
                        // AJAX模式
                        console.log('🌐 使用AJAX模式执行筛选');
                        
                        if (config.ajax_callback && typeof config.ajax_callback === 'function') {
                            // 使用自定义AJAX回调函数（兼容旧模式）
                            config.ajax_callback();
                        } else if (config.ajax_endpoint && config.ajax_target) {
                            // 使用通用AJAX筛选功能
                            performGenericAjaxFilter(config);
                        } else {
                            console.error('❌ AJAX模式配置错误：缺少 ajax_endpoint 或 ajax_target 配置');
                        }
                    } else {
                        // 传统模式：显示重置按钮并提交表单
                        console.log('📄 使用传统模式提交表单');
                        console.log('📄 表单信息:', {
                            action: form.action,
                            method: form.method,
                            id: form.id,
                            elements: Array.from(form.elements).map(el => ({
                                name: el.name,
                                value: el.value,
                                type: el.type || el.tagName
                            }))
                        });
                        
                        if (config.dynamic_reset_button) {
                            showResetButton(config);
                        }
                        addLightLoadingState(config);
                        form.submit();
                    }
                });
            } else {
                console.warn(`⚠️ 筛选字段未找到: ${field.name}`);
            }
        });
    } else {
        console.log('❌ 自动提交功能已禁用或未配置筛选字段');
    }
    
    // 搜索按钮AJAX模式处理
    if (config.ajax_mode) {
        const searchButton = form.querySelector('.filter-search-button');
        if (searchButton) {
            searchButton.addEventListener('click', function(e) {
                e.preventDefault(); // 阻止默认的表单提交
                console.log('🔍 搜索按钮点击，使用AJAX模式');
                
                if (config.ajax_callback && typeof config.ajax_callback === 'function') {
                    config.ajax_callback();
                } else if (config.ajax_endpoint && config.ajax_target) {
                    performGenericAjaxFilter(config);
                } else {
                    console.error('❌ AJAX模式配置错误：缺少 ajax_endpoint 或 ajax_target 配置');
                }
            });
        }
    }
    
    // 搜索框变化也需要显示重置按钮
    if (config.dynamic_reset_button && config.search_field_id) {
        const searchInput = document.getElementById(config.search_field_id);
        if (searchInput) {
            console.log(`📋 为搜索框 ${config.search_field_id} 添加输入监听器`);
            searchInput.addEventListener('input', function() {
                console.log(`🔍 搜索框输入变化: "${this.value}"`);
                if (this.value.trim() !== '') {
                    showResetButton(config);
                } else {
                    // 搜索框为空时，检查其他筛选条件
                    const hasActiveFilters = checkActiveFilters(config);
                    if (!hasActiveFilters) {
                        hideResetButton(config);
                    }
                }
            });
        } else {
            console.warn(`⚠️ 搜索框未找到: ${config.search_field_id}`);
        }
    }
    
    // 初次加载数据（AJAX模式下）
    if (config.ajax_mode && config.auto_submit) {
        console.log('🚀 AJAX模式下自动触发初次数据加载');
        // 使用 requestAnimationFrame 确保DOM完全渲染后再执行，比setTimeout更高效
        requestAnimationFrame(() => {
            const targetElement = document.querySelector(config.ajax_target);
            if (targetElement && targetElement.textContent.includes('正在加载数据')) {
                console.log('📊 执行初次数据加载');
                if (config.ajax_callback && typeof config.ajax_callback === 'function') {
                    config.ajax_callback();
                } else if (config.ajax_endpoint && config.ajax_target) {
                    performGenericAjaxFilter(config);
                } else {
                    console.error('❌ 初次加载：AJAX模式配置错误');
                }
            } else {
                console.log('📊 跳过初次加载：目标元素不在加载状态');
            }
        });
    }
}

/**
 * 客户端搜索功能（用于不刷新页面的搜索）
 * @param {string} searchText - 搜索文本
 * @param {Object} config - 配置对象
 */
function performClientSearch(searchText, config) {
    // 这里可以实现客户端筛选逻辑
    // 具体实现依赖于页面结构和需求
    console.log('执行客户端搜索:', searchText);
    
    if (config.client_search_callback && typeof config.client_search_callback === 'function') {
        config.client_search_callback(searchText);
    }
}

/**
 * 获取当前筛选参数
 * @param {string} formId - 表单ID
 * @returns {Object} 筛选参数对象
 */
function getCurrentFilters(formId) {
    const form = document.getElementById(formId);
    if (!form) return {};
    
    const formData = new FormData(form);
    const filters = {};
    
    for (let [key, value] of formData.entries()) {
        if (value.trim() !== '') {
            filters[key] = value;
        }
    }
    
    return filters;
}

/**
 * 设置筛选参数
 * @param {string} formId - 表单ID
 * @param {Object} filters - 筛选参数对象
 */
function setFilters(formId, filters) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    Object.keys(filters).forEach(key => {
        const element = form.querySelector(`[name="${key}"]`);
        if (element) {
            element.value = filters[key] || '';
        }
    });
}

/**
 * 清除特定筛选字段
 * @param {string} formId - 表单ID
 * @param {Array} fieldNames - 要清除的字段名数组
 */
function clearSpecificFilters(formId, fieldNames) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    fieldNames.forEach(fieldName => {
        const element = form.querySelector(`[name="${fieldName}"]`);
        if (element) {
            element.value = '';
        }
    });
}

/**
 * 初始化动态重置按钮功能
 * @param {Object} config - 配置对象
 */
function initializeDynamicResetButton(config) {
    console.log('🔧 初始化动态重置按钮功能');
    
    const resetButton = document.querySelector('.filter-reset-button');
    if (!resetButton) {
        console.warn('⚠️ 重置按钮未找到');
        return;
    }
    
    // 检查当前是否有筛选条件
    const hasActiveFilters = checkActiveFilters(config);
    
    if (hasActiveFilters) {
        showResetButton(config);
    } else {
        hideResetButton(config);
    }
}

/**
 * 检查是否有激活的筛选条件
 * @param {Object} config - 配置对象
 * @returns {boolean} 是否有激活的筛选条件
 */
function checkActiveFilters(config) {
    const form = document.getElementById(config.form_id);
    if (!form) {
        console.log('❌ 表单未找到:', config.form_id);
        return false;
    }
    
    // 首先检查URL参数作为后备
    const urlParams = new URLSearchParams(window.location.search);
    console.log('🔍 当前URL参数:', Object.fromEntries(urlParams.entries()));
    
    // 检查搜索框
    if (config.search_field_id) {
        const searchInput = document.getElementById(config.search_field_id);
        const searchValue = searchInput ? searchInput.value.trim() : '';
        const urlSearchValue = urlParams.get('search') || '';
        
        console.log(`🔍 搜索框检查: 表单="${searchValue}", URL="${urlSearchValue}"`);
        
        if (searchValue !== '' || urlSearchValue !== '') {
            console.log(`🔍 发现搜索条件: 表单="${searchValue}", URL="${urlSearchValue}"`);
            return true;
        }
    }
    
    // 检查筛选字段
    if (config.filter_fields) {
        console.log('🎯 检查筛选字段:', config.filter_fields);
        
        for (const field of config.filter_fields) {
            const element = document.getElementById(field.name);
            const formValue = element ? element.value : '';
            const urlValue = urlParams.get(field.name) || '';
            
            console.log(`🎯 字段 ${field.name}: 表单="${formValue}", URL="${urlValue}", 元素存在=${!!element}`);
            
            if (element) {
                console.log(`   - 元素类型: ${element.tagName}, 选中值: ${element.value}, selectedIndex: ${element.selectedIndex}`);
                if (element.tagName === 'SELECT') {
                    const selectedOption = element.options[element.selectedIndex];
                    console.log(`   - 选中选项: value="${selectedOption ? selectedOption.value : 'none'}", text="${selectedOption ? selectedOption.text : 'none'}"`);
                }
            }
            
            if (formValue !== '' || urlValue !== '') {
                console.log(`🎯 发现筛选条件: ${field.name}="${formValue || urlValue}"`);
                return true;
            }
        }
    }
    
    console.log('❌ 未发现活跃筛选条件');
    return false;
}

/**
 * 显示重置按钮
 * @param {Object} config - 配置对象
 */
function showResetButton(config) {
    const resetButton = document.querySelector('.filter-reset-button');
    if (resetButton) {
        resetButton.style.display = 'inline-block';
        console.log('👁️ 显示重置按钮');
    }
}

/**
 * 隐藏重置按钮
 * @param {Object} config - 配置对象
 */
function hideResetButton(config) {
    const resetButton = document.querySelector('.filter-reset-button');
    if (resetButton) {
        resetButton.style.display = 'none';
        console.log('🫥 隐藏重置按钮');
    }
}

/**
 * 增强版重置筛选条件函数
 * @param {string} resetUrl - 重置后跳转的URL
 * @param {Object} config - 配置对象（可选）
 */
function resetFiltersEnhanced(resetUrl, config = null) {
    console.log('🔄 执行重置筛选条件');
    
    if (config && config.ajax_mode) {
        // AJAX模式重置
        console.log('🌐 使用AJAX模式重置筛选');
        
        if (config.ajax_reset_callback && typeof config.ajax_reset_callback === 'function') {
            // 使用自定义AJAX重置回调函数（兼容旧模式）
            config.ajax_reset_callback();
        } else if (config.ajax_endpoint && config.ajax_target) {
            // 使用通用AJAX重置功能
            performGenericAjaxReset(config);
        } else {
            console.error('❌ AJAX重置模式配置错误：缺少 ajax_endpoint 或 ajax_target 配置');
        }
        return;
    }
    
    // 传统模式：隐藏重置按钮并跳转
    if (config) {
        hideResetButton(config);
        addLoadingState(config);
    }
    
    // 跳转到重置URL
    window.location.href = resetUrl;
}

/**
 * 添加加载状态
 * @param {Object} config - 配置对象
 */
function addLoadingState(config) {
    const container = document.querySelector('.filter-search-container');
    if (container) {
        container.classList.add('loading');
        console.log('⏳ 添加加载状态');
    }
}

/**
 * 添加轻量级加载状态（不影响布局）
 * @param {Object} config - 配置对象
 */
function addLightLoadingState(config) {
    const form = document.getElementById(config.form_id);
    if (form) {
        // 只禁用表单元素，不改变布局
        const inputs = form.querySelectorAll('input, select, button');
        inputs.forEach(input => {
            input.disabled = true;
            input.style.opacity = '0.6';
        });
        console.log('⏳ 添加轻量级加载状态');
    }
}

/**
 * 移除加载状态
 * @param {Object} config - 配置对象
 */
function removeLoadingState(config) {
    const container = document.querySelector('.filter-search-container');
    if (container) {
        container.classList.remove('loading');
        console.log('✅ 移除加载状态');
    }
}

/**
 * 自适应宽度调整功能
 * 根据标签文本长度和内容长度动态调整输入框宽度
 */
function adjustAdaptiveWidths() {
    // 移动端跳过自适应宽度调整，防止与CSS媒体查询冲突
    if (window.innerWidth <= 768) {
        console.log('📱 移动端模式：跳过自适应宽度调整');
        return;
    }
    
    const adaptiveControls = document.querySelectorAll('.filter-control.adaptive-width');
    
    adaptiveControls.forEach(control => {
        const label = control.querySelector('.form-label');
        const input = control.querySelector('.form-control, .form-select');
        
        if (label && input) {
            // 计算标签文本宽度
            const labelText = label.textContent || label.innerText;
            const labelWidth = getTextWidth(labelText, getComputedStyle(label).font);
            
            // 计算内容宽度（对于select元素）
            let contentWidth = 120; // 默认最小宽度
            if (input.tagName === 'SELECT') {
                const options = input.querySelectorAll('option');
                let maxOptionWidth = 0;
                options.forEach(option => {
                    const optionText = option.textContent || option.innerText;
                    const optionWidth = getTextWidth(optionText, getComputedStyle(input).font);
                    maxOptionWidth = Math.max(maxOptionWidth, optionWidth);
                });
                contentWidth = Math.max(contentWidth, maxOptionWidth + 60); // 加上下拉箭头和padding
            } else if (input.placeholder) {
                const placeholderWidth = getTextWidth(input.placeholder, getComputedStyle(input).font);
                contentWidth = Math.max(contentWidth, placeholderWidth + 40); // 加上padding
            }
            
            // 取标签宽度和内容宽度的最大值，并应用限制
            const targetWidth = Math.max(labelWidth + 20, contentWidth); // 标签额外加20px padding
            const minWidth = parseInt(getComputedStyle(control).getPropertyValue('--min-width')) || 120;
            const maxWidth = parseInt(getComputedStyle(control).getPropertyValue('--max-width')) || 300;
            
            const finalWidth = Math.min(Math.max(targetWidth, minWidth), maxWidth);
            
            // 应用计算的宽度
            control.style.flexBasis = `${finalWidth}px`;
            control.style.maxWidth = `${finalWidth}px`;
            
            console.log(`🔧 调整控件宽度: ${labelText} -> ${finalWidth}px`);
        }
    });
}

/**
 * 计算文本宽度的辅助函数
 * @param {string} text - 要测量的文本
 * @param {string} font - 字体样式
 * @returns {number} 文本宽度（像素）
 */
function getTextWidth(text, font) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    context.font = font;
    return context.measureText(text).width;
}

/**
 * 语言切换时重新调整宽度
 */
function handleLanguageChange() {
    // 延迟执行，确保DOM更新完成
    setTimeout(() => {
        adjustAdaptiveWidths();
    }, 100);
}

/**
 * 监听语言切换事件
 */
function setupLanguageChangeListener() {
    // 监听可能的语言切换按钮点击
    const languageButtons = document.querySelectorAll('[data-language], .language-switch, .lang-switch');
    languageButtons.forEach(button => {
        button.addEventListener('click', handleLanguageChange);
    });
    
    // 监听DOM变化（某些情况下语言切换会修改DOM）
    const observer = new MutationObserver((mutations) => {
        let shouldAdjust = false;
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList' || 
                (mutation.type === 'attributes' && 
                 (mutation.attributeName === 'class' || mutation.attributeName === 'lang'))) {
                shouldAdjust = true;
            }
        });
        
        if (shouldAdjust) {
            handleLanguageChange();
        }
    });
    
    // 观察文档的语言属性变化
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['lang', 'class'],
        childList: true,
        subtree: false
    });
}

/**
 * 初始化自适应按钮布局
 * @param {Object} config - 配置对象
 */
function initializeAdaptiveButtonLayout(config) {
    console.log('🔧 初始化自适应按钮布局');
    checkAndAdjustButtonLayout(config);
}

/**
 * 检查并调整按钮布局
 * @param {Object} config - 配置对象
 */
function checkAndAdjustButtonLayout(config) {
    const form = document.getElementById(config.form_id);
    if (!form) return;
    
    const filterRow = form.querySelector('.filter-row');
    const buttonsContainer = form.querySelector('.filter-buttons-container');
    
    if (!filterRow || !buttonsContainer) return;
    
    // 重置布局状态
    filterRow.classList.remove('buttons-wrapped');
    
    // 等待下一帧以确保样式应用完成
    requestAnimationFrame(() => {
        // 检查是否需要换行
        const containerWidth = filterRow.offsetWidth;
        const buttonsWidth = buttonsContainer.offsetWidth;
        
        // 计算所有筛选控件的总宽度
        const filterControls = filterRow.querySelectorAll('.filter-control:not(.filter-buttons-container)');
        let controlsWidth = 0;
        filterControls.forEach(control => {
            controlsWidth += control.offsetWidth;
        });
        
        // 加上一些间距的安全边距
        const safetyMargin = 60;
        const totalRequiredWidth = controlsWidth + buttonsWidth + safetyMargin;
        
        // 如果总宽度超过容器宽度，则换行
        if (totalRequiredWidth > containerWidth) {
            filterRow.classList.add('buttons-wrapped');
            console.log('🔄 按钮布局：空间不足，按钮换行到下一行');
        } else {
            console.log('✅ 按钮布局：空间充足，按钮保持在同一行右侧');
        }
    });
}

/**
 * 设置窗口大小变化监听器
 * @param {Object} config - 配置对象
 */
function setupResizeListener(config) {
    let resizeTimeout;
    
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            checkAndAdjustButtonLayout(config);
            // 同时调整自适应宽度（仅在非移动端）
            if (config.adaptive_width !== false && window.innerWidth > 768) {
                adjustAdaptiveWidths();
            }
        }, 150);
    });
    
    console.log('👂 已设置窗口大小变化监听器');
}

/**
 * 通用AJAX筛选功能
 * @param {Object} config - 配置对象
 */
function performGenericAjaxFilter(config) {
    console.log('🔄 执行通用AJAX筛选:', config);
    
    // 获取当前筛选参数
    const params = getGenericCurrentParams(config);
    console.log('📋 筛选参数:', params);
    
    // 显示加载状态
    const targetElement = document.querySelector(config.ajax_target);
    if (!targetElement) {
        console.error(`❌ 找不到目标元素: ${config.ajax_target}`);
        return;
    }
    
    // 显示加载状态
    const columns = config.ajax_columns || 5;
    
    // 移动端和桌面端都显示加载状态
    if (window.innerWidth <= 768) {
        // 移动端：在卡片容器中显示加载状态
        const mobileTarget = document.querySelector('.product-list-mobile .p-3, .data-list-mobile .p-3');
        if (mobileTarget) {
            mobileTarget.innerHTML = `
                <div class="loading-card">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <div class="mt-2">正在筛选数据...</div>
                </div>
            `;
        }
        // 桌面端目标也更新（虽然隐藏）
        targetElement.innerHTML = `<tr><td colspan="${columns}" class="text-center p-4">正在筛选...</td></tr>`;
    } else {
        // 桌面端：正常显示表格加载状态
        targetElement.innerHTML = `<tr><td colspan="${columns}" class="text-center p-4">正在筛选...</td></tr>`;
    }
    
    // 构造请求URL
    const url = new URL(config.ajax_endpoint, window.location.origin);
    url.searchParams.set('offset', 0);
    
    // 使用无限滚动配置的分页大小，如果没有配置则使用默认20
    const pageSize = (config.infinite_scroll && config.infinite_scroll.page_size) ? 
        config.infinite_scroll.page_size : 20;
    url.searchParams.set('limit', pageSize);
    
    // 添加筛选参数
    Object.keys(params).forEach(key => {
        if (params[key] !== '') {
            url.searchParams.set(key, params[key]);
        }
    });
    
    // 添加设备类型检测参数
    const isMobileDevice = detectMobileDevice();
    url.searchParams.set('mobile', isMobileDevice ? 'true' : 'false');
    
    // 添加额外的AJAX参数
    if (config.ajax_params) {
        Object.keys(config.ajax_params).forEach(key => {
            url.searchParams.set(key, config.ajax_params[key]);
        });
    }
    
    console.log('🌐 发送AJAX请求到:', url.toString());
    
    // 发送AJAX请求
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            // 检查是否被重定向到登录页面
            if (response.url && (response.url.includes('/auth/login') || response.url.includes('/login'))) {
                throw new Error('会话已过期，请重新登录');
            }
            
            return response.json();
        })
        .then(data => {
            // 统一更新目标元素，服务器已根据设备类型返回正确的HTML
            if (targetElement) {
                targetElement.innerHTML = data.html;
            } else {
                console.error('❌ 找不到目标元素:', config.ajax_target);
            }
            
            // 显示结果数量
            console.log(`✅ 筛选完成，加载了 ${data.loaded_count || 0} 条记录，总计 ${data.total_count || 0} 条`);
            
            // 调用成功回调函数（如果存在）
            if (config.onSuccess && typeof config.onSuccess === 'function') {
                config.onSuccess(data);
            }
            
            // 更新浏览器URL但不刷新页面
            updateBrowserUrl(params);
            
            // 检查是否有活跃的筛选条件，控制重置按钮显示
            updateResetButtonVisibility(config);
            
            // 触发自定义事件，让模块可以监听
            const event = new CustomEvent('filterComplete', {
                detail: { config, data, params }
            });
            document.dispatchEvent(event);
            
        })
        .catch(error => {
            console.error('❌ 筛选失败:', error);
            
            // 检查是否是移动端以适配错误显示格式
            const isMobile = detectMobileDevice();
            
            if (error.message.includes('会话已过期')) {
                // 会话过期错误处理
                if (isMobile) {
                    targetElement.innerHTML = `
                        <div class="alert alert-warning text-center p-4">
                            <i class="fas fa-sign-in-alt"></i> 
                            ${error.message}
                            <br><small class="text-muted">
                                <a href="javascript:window.location.reload()" class="text-primary">点击刷新页面重新登录</a>
                            </small>
                        </div>
                    `;
                } else {
                    targetElement.innerHTML = `<tr><td colspan="${columns}" class="text-center text-warning p-4">
                        <i class="fas fa-sign-in-alt"></i> 
                        ${error.message}
                        <br><small class="text-muted">
                            <a href="javascript:window.location.reload()" class="text-primary">点击刷新页面重新登录</a>
                        </small>
                    </td></tr>`;
                }
            } else {
                // 其他错误处理
                if (isMobile) {
                    targetElement.innerHTML = `
                        <div class="alert alert-danger text-center p-4">
                            <i class="fas fa-exclamation-triangle"></i> 筛选失败：${error.message}
                        </div>
                    `;
                } else {
                    targetElement.innerHTML = `<tr><td colspan="${columns}" class="text-center text-danger p-4"><i class="fas fa-exclamation-triangle"></i> 筛选失败：${error.message}</td></tr>`;
                }
            }
        });
}

/**
 * 通用重置筛选功能
 * @param {Object} config - 配置对象
 */
function performGenericAjaxReset(config) {
    console.log('🔄 执行通用AJAX重置筛选');
    
    // 清空所有筛选字段
    const form = document.getElementById(config.form_id);
    if (form) {
        const inputs = form.querySelectorAll('input, select');
        inputs.forEach(input => {
            if (input.type === 'text' || input.type === 'search') {
                input.value = '';
            } else if (input.tagName === 'SELECT') {
                input.selectedIndex = 0; // 选择第一个选项（通常是"全部"）
            }
        });
    }
    
    // 重置URL参数
    const newUrl = new URL(window.location);
    const filterParams = config.filter_fields ? config.filter_fields.map(f => f.name) : [];
    if (config.search_field_id) {
        filterParams.push(config.search_field_id);
    }
    
    filterParams.forEach(key => {
        newUrl.searchParams.delete(key);
    });
    window.history.pushState({}, '', newUrl);
    
    // 隐藏重置按钮
    hideResetButton(config);
    
    // 执行筛选（实际上是加载未筛选的数据）
    performGenericAjaxFilter(config);
}

/**
 * 获取当前筛选参数（通用版本）
 * @param {Object} config - 配置对象
 * @returns {Object} 筛选参数对象
 */
function getGenericCurrentParams(config) {
    const form = document.getElementById(config.form_id);
    if (!form) {
        console.warn('⚠️ 找不到筛选表单');
        return {};
    }
    
    const params = {};
    
    // 获取搜索框值
    if (config.search_field_id) {
        const searchInput = form.querySelector(`#${config.search_field_id}`);
        if (searchInput) {
            params[config.search_field_id] = searchInput.value || '';
        }
    } else {
        // 备用逻辑：查找标准的搜索字段
        const searchInput = form.querySelector('input[name="search"]');
        if (searchInput) {
            params['search'] = searchInput.value || '';
        }
    }
    
    // 获取筛选字段值
    if (config.filter_fields) {
        config.filter_fields.forEach(field => {
            const element = form.querySelector(`#${field.name}`);
            if (element) {
                params[field.name] = element.value || '';
            }
        });
    }
    
    return params;
}

/**
 * 更新浏览器URL
 * @param {Object} params - 筛选参数
 */
function updateBrowserUrl(params) {
    const newUrl = new URL(window.location);
    Object.keys(params).forEach(key => {
        if (params[key] !== '') {
            newUrl.searchParams.set(key, params[key]);
        } else {
            newUrl.searchParams.delete(key);
        }
    });
    window.history.pushState({}, '', newUrl);
}

/**
 * 更新重置按钮显示状态
 * @param {Object} config - 配置对象
 */
function updateResetButtonVisibility(config) {
    if (!config.dynamic_reset_button) return;
    
    const params = getGenericCurrentParams(config);
    const filterParams = Object.keys(params);
    const hasFilters = filterParams.some(key => params[key] && params[key].trim() !== '');
    
    const resetButton = document.querySelector('.filter-reset-button');
    if (resetButton) {
        if (hasFilters) {
            resetButton.style.display = 'inline-block';
            console.log('👁️ 显示重置按钮（有活跃筛选条件）');
        } else {
            resetButton.style.display = 'none';
            console.log('🫥 隐藏重置按钮（无活跃筛选条件）');
        }
    }
}

/**
 * 初始化设备类型变化监听
 * 检测用户在移动端和PC端之间切换，自动刷新内容
 */
function initDeviceChangeDetection() {
    let lastDeviceType = detectMobileDevice();
    let lastWindowWidth = window.innerWidth;
    
    // 监听窗口大小变化
    window.addEventListener('resize', function() {
        const currentDeviceType = detectMobileDevice();
        const currentWindowWidth = window.innerWidth;
        
        // 检测设备类型是否发生变化（基于窗口宽度临界点）
        const wasDesktop = lastWindowWidth > 768;
        const isDesktop = currentWindowWidth > 768;
        
        if (wasDesktop !== isDesktop || lastDeviceType !== currentDeviceType) {
            console.log(`📱↔️💻 设备类型变化检测: ${wasDesktop ? 'Desktop' : 'Mobile'} → ${isDesktop ? 'Desktop' : 'Mobile'}`);
            
            // 更新URL参数以反映新的设备类型
            const newUrl = new URL(window.location);
            newUrl.searchParams.set('mobile', currentDeviceType ? 'true' : 'false');
            window.history.pushState({}, '', newUrl);
            
            // 触发页面内容刷新
            if (window.filterSearchConfig && window.filterSearchConfig.ajax_mode) {
                setTimeout(() => {
                    performGenericAjaxFilter(window.filterSearchConfig);
                }, 100); // 短暂延迟确保DOM更新完成
            }
            
            lastDeviceType = currentDeviceType;
        }
        
        lastWindowWidth = currentWindowWidth;
    });
}

// 页面加载完成后初始化设备变化检测
document.addEventListener('DOMContentLoaded', function() {
    initDeviceChangeDetection();
});