/**
 * 通用阶段统计组件
 * 提供标准化的阶段分布图表功能，支持筛选联动和多种显示模式
 */

class StageAnalyticsComponent {
    constructor(config) {
        this.config = {
            containerId: config.containerId,                    // 容器ID
            chartId: config.chartId,                           // 图表容器ID  
            apiEndpoint: config.apiEndpoint,                   // API端点
            title: config.title || '阶段分布统计',             // 标题
            icon: config.icon || 'fas fa-chart-bar',          // 图标
            chartType: config.chartType || 'bar',             // 图表类型: bar, pie, doughnut
            switchable: config.switchable !== false,          // 是否支持指标切换
            responsive: config.responsive !== false,          // 响应式
            showLegend: config.showLegend !== false,          // 显示图例
            height: config.height || '350px',                 // 图表高度
            
            // 筛选器集成配置
            filterIntegration: config.filterIntegration || false,
            
            // 图表选项
            chartOptions: config.chartOptions || {},
            
            // 自定义样式
            customStyles: config.customStyles || {},
            
            ...config
        };
        
        this.chartInstance = null;
        this.currentData = null;
        this.currentMetric = 'quantity'; // quantity | amount
        this.isLoading = false;
        
        // 事件回调
        this.onDataLoaded = config.onDataLoaded || null;
        this.onMetricChanged = config.onMetricChanged || null;
        this.onChartClicked = config.onChartClicked || null;
    }
    
    /**
     * 初始化组件
     */
    async init() {
        try {
            console.log('🚀 开始初始化阶段统计组件');
            console.log('🔧 检查ECharts可用性:', typeof echarts !== 'undefined' ? '✅ 可用' : '❌ 不可用');
            
            this.renderContainer();
            this.bindEvents();
            await this.loadData();
        } catch (error) {
            console.error('阶段统计组件初始化失败:', error);
            this.showError('组件初始化失败');
        }
    }
    
    /**
     * 渲染容器结构
     */
    renderContainer() {
        console.log('🏗️ 渲染容器结构，容器ID:', this.config.containerId);
        const container = document.getElementById(this.config.containerId);
        if (!container) {
            console.error('❌ 未找到容器:', this.config.containerId);
            throw new Error(`未找到容器: ${this.config.containerId}`);
        }
        
        console.log('✅ 找到容器:', container);
        
        container.innerHTML = `
            <div class="stage-analytics-wrapper">
                <div class="analytics-header d-flex justify-content-between align-items-center mb-3">
                    <h6 class="analytics-title mb-0">
                        <i class="${this.config.icon} me-2"></i>
                        ${this.config.title}
                    </h6>
                    ${this.config.switchable ? this.renderMetricSwitches() : ''}
                </div>
                
                <div class="analytics-chart-container position-relative" style="height: ${this.config.height};">
                    <div class="chart-wrapper" id="${this.config.chartId}" style="width: 100%; height: 100%;"></div>
                    <div class="loading-overlay position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center bg-light bg-opacity-75" style="display: none !important;">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">加载中...</span>
                        </div>
                    </div>
                    <div class="error-message position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center text-muted" style="display: none !important;">
                        <div class="text-center">
                            <i class="fas fa-exclamation-circle fa-2x mb-2"></i>
                            <div class="error-text">加载失败</div>
                        </div>
                    </div>
                    <div class="no-data-message position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center text-muted" style="display: none !important;">
                        <div class="text-center">
                            <i class="fas fa-chart-bar fa-2x mb-2 opacity-50"></i>
                            <div>暂无数据</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * 渲染指标切换按钮
     */
    renderMetricSwitches() {
        return `
            <div class="analytics-switches">
                <div class="btn-group btn-group-sm" role="group">
                    <button type="button" class="btn btn-outline-primary metric-switch active" data-metric="quantity">
                        数量
                    </button>
                    <button type="button" class="btn btn-outline-primary metric-switch" data-metric="amount">
                        金额
                    </button>
                </div>
            </div>
        `;
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        const container = document.getElementById(this.config.containerId);
        
        // 移除已有的事件监听器，防止重复绑定
        if (this.clickHandler) {
            container.removeEventListener('click', this.clickHandler);
        }
        
        // 指标切换事件
        if (this.config.switchable) {
            this.clickHandler = (e) => {
                if (e.target.classList.contains('metric-switch')) {
                    const newMetric = e.target.dataset.metric;
                    console.log('🔘 点击切换按钮:', newMetric, '当前指标:', this.currentMetric);
                    if (newMetric !== this.currentMetric && !this.isLoading) {
                        console.log('🔄 执行指标切换');
                        this.switchMetric(newMetric);
                    } else {
                        console.log('⏭️ 跳过切换 - 相同指标或正在加载中');
                    }
                }
            };
            container.addEventListener('click', this.clickHandler);
        }
        
        // 与筛选器集成
        if (this.config.filterIntegration) {
            this.setupFilterIntegration();
        }
    }
    
    /**
     * 设置筛选器集成
     */
    setupFilterIntegration() {
        // 监听全局筛选器变化事件
        document.addEventListener('filterChanged', (event) => {
            if (event.detail && event.detail.filters) {
                this.updateFilters(event.detail.filters);
            }
        });
        
        // 注册到全局筛选器组件
        if (window.filterSearchConfig) {
            window.filterSearchConfig.stageAnalyticsComponents = 
                window.filterSearchConfig.stageAnalyticsComponents || [];
            window.filterSearchConfig.stageAnalyticsComponents.push(this);
        }
    }
    
    /**
     * 加载数据
     */
    async loadData(filters = {}) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading(true);
        
        try {
            // 构建请求URL
            const url = new URL(this.config.apiEndpoint, window.location.origin);
            
            // 添加筛选参数
            Object.keys(filters).forEach(key => {
                if (filters[key]) {
                    url.searchParams.append(key, filters[key]);
                }
            });
            
            console.log('🌐 请求URL:', url.toString());
            const response = await fetch(url);
            const data = await response.json();
            
            console.log('📡 API响应:', data);
            
            if (data.success) {
                console.log('✅ 数据加载成功，准备渲染图表');
                this.currentData = data;
                this.renderChart();
                
                // 触发数据加载回调
                if (this.onDataLoaded) {
                    this.onDataLoaded(data);
                }
            } else {
                console.error('❌ API返回失败:', data.message);
                throw new Error(data.message || '数据加载失败');
            }
            
        } catch (error) {
            console.error('加载阶段统计数据失败:', error);
            this.showError(error.message);
        } finally {
            this.isLoading = false;
            this.showLoading(false);
        }
    }
    
    /**
     * 渲染图表
     */
    renderChart() {
        const chartContainer = document.getElementById(this.config.chartId);
        if (!chartContainer || !this.currentData || !this.currentData.data) {
            this.showNoData();
            return;
        }
        
        const data = this.currentData.data;
        if (!data.length) {
            this.showNoData();
            return;
        }
        
        // 过滤有效数据
        console.log('🔍 原始数据:', data);
        console.log('🔍 当前指标:', this.currentMetric);
        
        const validData = data.filter(item => {
            const isValid = (this.currentMetric === 'quantity' && item.quantity > 0) || 
                           (this.currentMetric === 'amount' && item.amount > 0);
            console.log(`🔍 检查项目 ${item.stage} (${item.name}): quantity=${item.quantity}, amount=${item.amount}, isValid=${isValid}`);
            return isValid;
        });
        
        console.log('🔍 过滤后的有效数据:', validData);
        
        if (!validData.length) {
            console.log('⚠️ 没有有效数据，显示无数据提示');
            this.showNoData();
            return;
        }
        
        // 隐藏错误和无数据提示
        console.log('🧹 隐藏错误和无数据提示');
        this.hideMessages();
        console.log('🧹 消息隐藏完成');
        
        // 初始化或更新图表
        console.log('📊 图表容器:', chartContainer);
        if (!this.chartInstance) {
            console.log('🆕 初始化新的ECharts实例');
            this.chartInstance = echarts.init(chartContainer);
        } else {
            console.log('♻️ 复用现有ECharts实例');
        }
        
        // 构建图表配置
        console.log('⚙️ 构建图表配置');
        const chartOption = this.buildChartOption(validData);
        console.log('⚙️ 图表配置:', chartOption);
        
        // 设置图表配置
        console.log('🎨 设置图表配置');
        this.chartInstance.setOption(chartOption, true);
        
        // 确保图表正确调整大小
        setTimeout(() => {
            if (this.chartInstance) {
                console.log('📐 手动调整图表大小');
                this.chartInstance.resize();
            }
        }, 100);
        
        console.log('✅ 图表渲染完成');
        
        // 绑定点击事件
        this.chartInstance.off('click');
        this.chartInstance.on('click', (params) => {
            if (this.onChartClicked) {
                this.onChartClicked(params, this.currentMetric);
            }
        });
        
        // 响应式调整
        if (this.config.responsive) {
            window.addEventListener('resize', () => {
                if (this.chartInstance) {
                    this.chartInstance.resize();
                }
            });
        }
    }
    
    /**
     * 构建图表配置
     */
    buildChartOption(data) {
        const isAmountMetric = this.currentMetric === 'amount';
        const colorKey = isAmountMetric ? 'color_amount' : 'color_quantity';
        
        if (this.config.chartType === 'bar') {
            return {
                tooltip: {
                    trigger: 'axis',
                    axisPointer: { type: 'shadow' },
                    formatter: (params) => {
                        const data = params[0];
                        const value = data.value;
                        const unit = isAmountMetric ? '万元' : '个';
                        const formattedValue = isAmountMetric ? 
                            (value / 10000).toFixed(2) : value.toLocaleString();
                        return `${data.axisValue}<br/>${data.seriesName}: ${formattedValue} ${unit}`;
                    }
                },
                xAxis: {
                    type: 'category',
                    data: data.map(item => item.name),
                    axisLine: { lineStyle: { color: '#e0e0e0' } },
                    axisTick: { lineStyle: { color: '#e0e0e0' } },
                    axisLabel: { 
                        color: '#666',
                        interval: 0,
                        rotate: data.length > 6 ? 45 : 0
                    }
                },
                yAxis: {
                    type: 'value',
                    axisLine: { show: false },
                    axisTick: { show: false },
                    axisLabel: { 
                        color: '#666',
                        formatter: (value) => {
                            return isAmountMetric ? 
                                `${(value / 10000).toFixed(1)}万` : value.toLocaleString();
                        }
                    },
                    splitLine: { lineStyle: { color: '#f0f0f0' } }
                },
                series: [{
                    name: isAmountMetric ? '金额分布' : '数量分布',
                    type: 'bar',
                    data: data.map(item => ({
                        value: isAmountMetric ? item.amount : item.quantity,
                        itemStyle: { color: item[colorKey] }
                    })),
                    barMaxWidth: 50,
                    label: {
                        show: data.length <= 8,
                        position: 'top',
                        color: '#666',
                        fontSize: 11,
                        formatter: (params) => {
                            const value = params.value;
                            return isAmountMetric ? 
                                `${(value / 10000).toFixed(1)}万` : value.toLocaleString();
                        }
                    }
                }],
                grid: {
                    left: '50px',
                    right: '30px',
                    bottom: data.length > 6 ? '80px' : '50px',
                    top: '30px'
                },
                ...this.config.chartOptions
            };
        } else if (this.config.chartType === 'pie' || this.config.chartType === 'doughnut') {
            return {
                tooltip: {
                    trigger: 'item',
                    formatter: (params) => {
                        const value = params.value;
                        const unit = isAmountMetric ? '万元' : '个';
                        const formattedValue = isAmountMetric ? 
                            (value / 10000).toFixed(2) : value.toLocaleString();
                        return `${params.name}<br/>${formattedValue} ${unit} (${params.percent}%)`;
                    }
                },
                legend: {
                    show: this.config.showLegend && data.length <= 10,
                    orient: 'horizontal',
                    bottom: 0,
                    left: 'center'
                },
                series: [{
                    name: isAmountMetric ? '金额分布' : '数量分布',
                    type: 'pie',
                    radius: this.config.chartType === 'doughnut' ? ['35%', '70%'] : '70%',
                    center: ['50%', '45%'],
                    data: data.map(item => ({
                        name: item.name,
                        value: isAmountMetric ? item.amount : item.quantity,
                        itemStyle: { color: item[colorKey] }
                    })),
                    label: {
                        formatter: '{b}\n{c}' + (isAmountMetric ? '万元' : '个')
                    },
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }],
                ...this.config.chartOptions
            };
        }
        
        return {};
    }
    
    /**
     * 切换显示指标
     */
    switchMetric(metric) {
        if (this.currentMetric === metric || this.isLoading) {
            console.log('⏭️ switchMetric: 跳过切换，currentMetric:', this.currentMetric, 'newMetric:', metric, 'isLoading:', this.isLoading);
            return;
        }
        
        console.log('🔄 switchMetric: 开始切换指标从', this.currentMetric, '到', metric);
        this.currentMetric = metric;
        
        // 更新按钮状态
        const container = document.getElementById(this.config.containerId);
        const buttons = container.querySelectorAll('.metric-switch');
        buttons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.metric === metric);
        });
        
        // 重新渲染图表
        console.log('🎨 switchMetric: 重新渲染图表');
        this.renderChart();
        
        // 触发指标变化回调（但不在回调中执行其他操作）
        if (this.onMetricChanged) {
            console.log('📞 switchMetric: 触发回调');
            this.onMetricChanged(metric);
        }
        
        console.log('✅ switchMetric: 指标切换完成');
    }
    
    /**
     * 更新筛选条件
     */
    async updateFilters(filters) {
        await this.loadData(filters);
    }
    
    /**
     * 显示加载状态
     */
    showLoading(show) {
        const container = document.getElementById(this.config.containerId);
        const loadingOverlay = container.querySelector('.loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = show ? 'flex' : 'none';
        }
    }
    
    /**
     * 显示错误信息
     */
    showError(message) {
        const container = document.getElementById(this.config.containerId);
        const errorMessage = container.querySelector('.error-message');
        if (errorMessage) {
            errorMessage.querySelector('.error-text').textContent = message;
            errorMessage.style.display = 'flex';
        }
        
        this.hideMessages(['loading', 'nodata']);
        
        if (this.chartInstance) {
            this.chartInstance.clear();
        }
    }
    
    /**
     * 显示无数据提示
     */
    showNoData() {
        const container = document.getElementById(this.config.containerId);
        const noDataMessage = container.querySelector('.no-data-message');
        if (noDataMessage) {
            noDataMessage.style.display = 'flex';
        }
        
        this.hideMessages(['loading', 'error']);
        
        if (this.chartInstance) {
            this.chartInstance.clear();
        }
    }
    
    /**
     * 隐藏消息提示
     */
    hideMessages(types = ['loading', 'error', 'nodata']) {
        console.log('🫥 hideMessages 被调用，隐藏类型:', types);
        const container = document.getElementById(this.config.containerId);
        
        types.forEach(type => {
            let selector;
            switch(type) {
                case 'loading': selector = '.loading-overlay'; break;
                case 'error': selector = '.error-message'; break;
                case 'nodata': selector = '.no-data-message'; break;
            }
            
            if (selector) {
                const element = container.querySelector(selector);
                if (element) {
                    console.log(`🫥 隐藏元素 ${selector}, 当前显示状态:`, element.style.display);
                    element.style.display = 'none';
                    console.log(`🫥 隐藏完成，新状态:`, element.style.display);
                } else {
                    console.log(`⚠️ 未找到元素:`, selector);
                }
            }
        });
    }
    
    /**
     * 销毁组件
     */
    destroy() {
        if (this.chartInstance) {
            this.chartInstance.dispose();
            this.chartInstance = null;
        }
        
        // 移除点击事件监听器
        if (this.clickHandler) {
            const container = document.getElementById(this.config.containerId);
            if (container) {
                container.removeEventListener('click', this.clickHandler);
            }
            this.clickHandler = null;
        }
        
        // 移除resize事件监听器
        if (this.resizeHandler) {
            window.removeEventListener('resize', this.resizeHandler);
            this.resizeHandler = null;
        }
        
        // 从全局筛选器中移除
        if (window.filterSearchConfig && window.filterSearchConfig.stageAnalyticsComponents) {
            const index = window.filterSearchConfig.stageAnalyticsComponents.indexOf(this);
            if (index > -1) {
                window.filterSearchConfig.stageAnalyticsComponents.splice(index, 1);
            }
        }
    }
}

// 全局导出
window.StageAnalyticsComponent = StageAnalyticsComponent;