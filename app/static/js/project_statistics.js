/**
 * 项目统计面板 JavaScript
 * 负责加载、展示和切换项目统计数据
 */

// 阶段常量定义（用英文key，顺序与后端一致）
const STAGE_ORDER = [
    'discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted', 'signed', 'lost', 'paused'
];

// 阶段key到中文的映射 - 初始化为空，完全依赖API拉取
let STAGE_LABELS = {};

// 从后端获取最新的阶段标签映射
function loadStageLabels() {
    fetch('/projectpm/statistics/api/stage_labels')
        .then(response => {
            if (!response.ok) {
                console.warn('获取阶段标签映射失败，使用默认值');
                return null;
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success && data.labels) {
                // 更新全局STAGE_LABELS对象
                STAGE_LABELS = data.labels;
                console.log('成功加载阶段标签映射');
            }
        })
        .catch(error => {
            console.warn('获取阶段标签失败，使用默认值:', error);
        });
}

// 阶段key转中文label的辅助函数
function project_stage_label(key) {
    if (!key) return '未设置';
    // 如果存在对应的标签则返回，否则返回key本身
    if (STAGE_LABELS[key] && STAGE_LABELS[key]['zh']) {
        return STAGE_LABELS[key]['zh'];
    }
    return STAGE_LABELS[key] || key;
}

// 阶段颜色定义 - 项目数量颜色
const STAGE_COLORS_COUNT = {
    'discover': 'rgba(2, 103, 5, 0.05)',      // 026705 透明度 5%
    'embed': 'rgba(2, 103, 5, 0.2)',   // 026705 透明度 20%
    'pre_tender': 'rgba(2, 103, 5, 0.3)',     // 026705 透明度 30%
    'tendering': 'rgba(2, 103, 5, 0.5)',     // 026705 透明度 50%
    'awarded': 'rgba(2, 103, 5, 0.7)',       // 026705 透明度 70%
    'signed': 'rgba(2, 103, 5, 1)',         // 026705 透明度 100%
    'lost': 'rgba(108, 3, 3, 1)',         // 6C0303 透明度 100%
    'paused': 'rgba(189, 194, 189, 1)'      // BDC2BD 透明度 100%
};

// 阶段颜色定义 - 项目金额颜色
const STAGE_COLORS_AMOUNT = {
    'discover': 'rgba(7, 70, 160, 0.05)',     // 0746A0 透明度 5%
    'embed': 'rgba(7, 70, 160, 0.2)',  // 0746A0 透明度 20%
    'pre_tender': 'rgba(7, 70, 160, 0.3)',    // 0746A0 透明度 30%
    'tendering': 'rgba(7, 70, 160, 0.5)',    // 0746A0 透明度 50%
    'awarded': 'rgba(7, 70, 160, 0.7)',      // 0746A0 透明度 70%
    'signed': 'rgba(7, 70, 160, 1)',        // 0746A0 透明度 100%
    'lost': 'rgba(108, 3, 3, 1)',         // 6C0303 透明度 100%
    'paused': 'rgba(189, 194, 189, 1)'      // BDC2BD 透明度 100%
};

// 原来的兼容性颜色定义
const STAGE_COLORS = {
    'discover': 'rgba(2, 103, 5, 0.05)',
    'embed': 'rgba(2, 103, 5, 0.2)',
    'pre_tender': 'rgba(2, 103, 5, 0.3)',
    'tendering': 'rgba(2, 103, 5, 0.5)',
    'awarded': 'rgba(2, 103, 5, 0.7)',
    'signed': 'rgba(2, 103, 5, 1)',
    'lost': 'rgba(108, 3, 3, 1)',
    'paused': 'rgba(189, 194, 189, 1)'
};

// 当前页面状态
let currentPeriod = 'month';            // 当前统计周期
let currentStageChartType = 'count';  // 当前阶段分布图类型: count 或 amount
let currentTrendPeriod = 'week';      // 当前趋势周期: week 或 month
let currentTrendStage = 'discover';        // 当前显示的趋势阶段
let currentAccountId = null;          // 当前选中的账户ID，null表示"全部账户"
let trendData = null;                 // 保存的趋势数据
let statisticsData = null;            // 保存的统计数据
window.autoSwitchTimer = null;           // 自动切换定时器（公开给外部访问）
let accounts = [];                    // 可用的账户列表

// 获取所有阶段演示趋势数据
const getAllDemoTrends = (period) => {
    const result = {};
    
    for (const stage of STAGE_ORDER) {
        result[stage] = getDemoTrendData(stage, period);
    }
    
    return {
        trends: result,
        period: period,
        stages: STAGE_ORDER,
        colors: STAGE_COLORS_COUNT,
        total_periods: period === 'week' ? 24 : 24  // 添加总周期数
    };
};

// 万元单位转换函数 - 用于统一处理金额转换
function convertToWan(amount) {
    return Math.round(amount / 10000);
}

document.addEventListener('DOMContentLoaded', function() {
    // 加载最新的阶段标签映射
    loadStageLabels();
    
    // 初始化工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // 获取DOM元素
    const toggleBtn = document.getElementById('toggleStatisticsBtn');
    const statisticsPanel = document.getElementById('projectStatisticsPanel');
    const periodBtns = document.querySelectorAll('.period-btn');
    const trendPeriodBtns = document.querySelectorAll('.trend-period-btn');
    const chartToggleDots = document.querySelectorAll('.chart-toggle-dot');
    const accountSelectorBtn = document.getElementById('accountSelectorBtn');
    const accountSelectorMenu = document.getElementById('accountSelectorMenu');
    
    // 加载状态元素
    const loadingDiv = document.getElementById('statisticsLoading');
    const cardsDiv = document.getElementById('statisticsCards');
    const errorDiv = document.getElementById('statisticsError');
    const errorMessage = document.getElementById('errorMessage');
    
    // 检查URL参数中是否有keep_panel=true
    const urlParams = new URLSearchParams(window.location.search);
    const keepPanel = urlParams.get('keep_panel') === 'true';
    
    // 仅当显式请求保持面板展开时才展开
    if (keepPanel && statisticsPanel) {
        const dashboardWrapper = document.getElementById('dashboardWrapper');
        if (dashboardWrapper) {
            dashboardWrapper.style.display = 'block';
        }
        statisticsPanel.classList.add('show');
        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="fas fa-chart-bar me-1"></i> 📉 隐藏统计总览';
        }
    }
    
    // 调整切换圆点位置
    const toggleDotsContainer = document.querySelectorAll('.text-center .chart-toggle-dot');
    toggleDotsContainer.forEach(dot => {
        dot.style.marginTop = '-10px';
        dot.style.position = 'relative';
        dot.style.top = '-10px';
    });
    
    // 页面加载时预加载数据，以便用户点击显示时可以快速展示
    // 显示加载中状态
    if (loadingDiv) loadingDiv.classList.remove('d-none');
    if (cardsDiv) cardsDiv.classList.add('d-none');
    if (errorDiv) errorDiv.classList.add('d-none');
    
    // 清除现有图表数据
    statisticsData = null;
    trendData = null;
    
    // 加载数据
    loadStatisticsData(currentPeriod);
    
    // 加载趋势数据 (不指定阶段，加载所有阶段数据)
    loadStageTrendData(currentTrendPeriod);
    
    // 仅当统计面板显示时才启动自动切换
    if (keepPanel) {
        startAutoSwitch();
    }
    
    // 折叠/展开统计面板 - 我们不再需要这部分代码，因为现在由list.html中的脚本控制
    // 但保留此代码以支持原生Bootstrap collapse切换
    if (toggleBtn && statisticsPanel) {
        toggleBtn.addEventListener('click', function() {
            const isVisible = statisticsPanel.classList.contains('show');
            
            if (isVisible) {
                // 当面板要隐藏时，停止自动切换
                if (window.autoSwitchTimer) {
                    clearInterval(window.autoSwitchTimer);
                    window.autoSwitchTimer = null;
                }
            } else {
                // 当面板要显示时，如果没有启动自动切换，则启动它
                if (!window.autoSwitchTimer) {
                    startAutoSwitch();
                }
            }
        });
    }
    
    // 总体周期切换
    // 移除周期切换按钮逻辑，只保留本月
    
    // 趋势周期切换
    trendPeriodBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const period = this.getAttribute('data-period');
            
            // 更新激活状态
            trendPeriodBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // 更新当前趋势周期并加载数据
            currentTrendPeriod = period;
            
            // 清除当前趋势数据，强制重新加载
            trendData = null;
            
            // 加载对应周期的趋势数据
            loadStageTrendData(period);
        });
    });
    
    // 阶段分布图表类型切换
    chartToggleDots.forEach(dot => {
        dot.addEventListener('click', function() {
            const chartType = this.getAttribute('data-chart-type');
            
            // 更新激活状态
            chartToggleDots.forEach(d => d.classList.remove('active'));
            this.classList.add('active');
            
            // 更新当前图表类型并重绘
            currentStageChartType = chartType;
            updateStageDistributionChart();
        });
    });
    
    // 加载统计数据
    function loadStatisticsData(period) {
        // 显示加载状态
        loadingDiv.classList.remove('d-none');
        cardsDiv.classList.add('d-none');
        errorDiv.classList.add('d-none');
        
        // 构建URL，添加账户参数
        let url = `/projectpm/statistics/api/project_statistics?period=${period}`;
        
        // 如果AccountSelector可用，添加账户参数
        if (typeof AccountSelector !== 'undefined') {
            url = AccountSelector.appendAccountParam(url);
        }
        
        // 发起API请求
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('请求失败');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // 保存数据用于图表切换
                    statisticsData = data.data;
                    updateStatisticsUI(data.data, period);
                    
                    // 隐藏加载状态，显示数据
                    loadingDiv.classList.add('d-none');
                    cardsDiv.classList.remove('d-none');
                } else {
                    throw new Error(data.message || '加载数据失败');
                }
            })
            .catch(error => {
                console.error('加载统计数据出错:', error);
                
                // 使用演示数据作为备选
                console.log('使用演示数据作为备选');
                statisticsData = DEMO_STATISTICS_DATA;
                updateStatisticsUI(DEMO_STATISTICS_DATA, period);
                
                loadingDiv.classList.add('d-none');
                cardsDiv.classList.remove('d-none');
                
                // 显示错误信息小提示，但仍显示演示数据
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-warning p-2 mt-2 mb-2';
                alertDiv.style.fontSize = '0.8rem';
                alertDiv.innerHTML = `<i class="fas fa-exclamation-triangle me-1"></i> 数据加载失败，当前显示的是演示数据。`;
                
                // 添加到卡片最上方
                if (cardsDiv.firstChild) {
                    cardsDiv.insertBefore(alertDiv, cardsDiv.firstChild);
                }
            });
    }
    
    // 加载阶段趋势数据
    function loadStageTrendData(period, stage) {
        const trendChart = document.getElementById('stageTrendChart');
        if (!trendChart) return;
        
        // 显示加载状态
        trendChart.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2">正在加载趋势数据...</p>
            </div>
        `;
        
        // 构建URL，添加账户参数
        let url = `/projectpm/statistics/api/project_stage_trends?period=${period}`;
        if (stage) {
            url += `&stage=${encodeURIComponent(stage)}`;
        }
        
        // 如果AccountSelector可用，添加账户参数
        if (typeof AccountSelector !== 'undefined') {
            url = AccountSelector.appendAccountParam(url);
        }
        
        // 发起API请求
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('请求失败');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // 保存完整趋势数据
                    trendData = data.data;
                    
                    // 初始化阶段切换器
                    if (!stage) {
                        initStageTrendToggle(trendData);
                    }
                    
                    // 绘制趋势图表
                    if (stage) {
                        // 单个阶段数据
                        drawStageTrendChart(data.data);
                    } else if (trendData.stages && trendData.stages.length > 0) {
                        // 全部阶段数据，默认显示第一个
                        currentTrendStage = trendData.stages[0];
                        drawStageTrendChart(trendData.trends[currentTrendStage]);
                    }
                } else {
                    throw new Error(data.message || '加载趋势数据失败');
                }
            })
            .catch(error => {
                console.error('加载阶段趋势数据出错:', error);
                trendChart.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-1"></i>
                        趋势数据加载失败，请稍后重试
                    </div>
                `;
            });
    }
    
    // 绘制阶段趋势图表
    function drawStageTrendChart(trendData) {
        if (typeof echarts === 'undefined') {
            console.error('ECharts库未加载');
            const chartContainer = document.getElementById('stageTrendChart');
            if (chartContainer) {
                chartContainer.innerHTML = '<div class="alert alert-danger">图表库加载失败，请刷新页面重试</div>';
            }
            return;
        }
        
        const chartContainer = document.getElementById('stageTrendChart');
        if (!chartContainer) {
            console.error('找不到图表容器 #stageTrendChart');
            return;
        }
        
        // 检查数据有效性
        if (!trendData || !trendData.labels || !trendData.data || trendData.labels.length === 0 || trendData.data.every(val => val === 0)) {
            chartContainer.innerHTML = '<div class="alert alert-info text-center">暂无历史数据</div>';
            return;
        }
        
        if (chartContainer.offsetWidth === 0 || chartContainer.offsetHeight === 0) {
            setTimeout(() => {
                try {
                    drawStageTrendChart(trendData);
                } catch (err) {
                    console.error('延迟绘制趋势图表出错:', err);
                }
            }, 200);
            return;
        }
        
        try {
            // 处理已有图表
            if (window.stageTrendChart) {
                try {
                    if (typeof window.stageTrendChart.dispose === 'function') {
                        window.stageTrendChart.dispose();
                    }
                } catch (e) {
                    console.warn('趋势图表销毁失败:', e);
                }
            }
            
            // 初始化图表
            try {
                window.stageTrendChart = echarts.init(chartContainer);
            } catch (e) {
                console.error('趋势图表初始化失败:', e);
                chartContainer.innerHTML = '<div class="alert alert-danger">趋势图表初始化失败，请刷新页面重试</div>';
                return;
            }
            
            // 根据阶段获取颜色
            let color = STAGE_COLORS_COUNT[trendData.stage || currentTrendStage] || 'rgba(2, 103, 5, 0.7)';
            
            // 计算默认显示的数据范围 - 最多显示12个周期，优先显示最新数据
            const totalDataPoints = trendData.labels.length;
            const displayCount = Math.min(12, totalDataPoints);
            const startIndex = Math.max(0, totalDataPoints - displayCount);
            const endIndex = totalDataPoints;
            
            // 准备滚动条控制相关数据
            let dataWindow = [
                (startIndex / totalDataPoints) * 100,
                100
            ];
            
            // 图表配置
            const option = {
                animation: true,
                title: {
                    text: project_stage_label(trendData.stage) || '趋势分析', // 用中文
                    left: 'center',
                    top: 0,
                    textStyle: {
                        fontSize: 16,
                        fontWeight: 'bold',
                        color: '#333333'
                    },
                    subtext: trendData.period === 'week' ? '(可左右滚动查看更多周数据)' : '(可左右滚动查看更多月份数据)',
                    subtextStyle: {
                        fontSize: 12,
                        color: '#999999'
                    }
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'cross',
                        label: {
                            backgroundColor: '#6a7985'
                        }
                    },
                    formatter: function(params) {
                        const time = params[0].name;
                        const val = params[0].value;
                        return `<b>${time}</b><br/>${project_stage_label(trendData.stage) || '项目'}数: <b>${val}</b>个`;
                    }
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '25%', // 增加底部空间以放置滚动条
                    top: '20%',
                    containLabel: true
                },
                // 添加缩放滚动组件
                dataZoom: [
                    {
                        type: 'slider', // 使用滑块型数据区域缩放组件
                        show: true,
                        xAxisIndex: [0],
                        start: dataWindow[0], // 默认显示的起始位置
                        end: dataWindow[1], // 默认显示的结束位置
                        handleIcon: 'M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
                        handleSize: '80%',
                        handleStyle: {
                            color: '#fff',
                            shadowBlur: 3,
                            shadowColor: 'rgba(0, 0, 0, 0.6)',
                            shadowOffsetX: 2,
                            shadowOffsetY: 2
                        },
                        textStyle: {
                            color: "#999"
                        },
                        borderColor: "#ddd"
                    },
                    {
                        type: 'inside', // 内置型数据区域缩放组件
                        xAxisIndex: [0],
                        start: dataWindow[0],
                        end: dataWindow[1],
                        zoomOnMouseWheel: true, // 支持鼠标滚轮缩放
                        moveOnMouseMove: true  // 支持鼠标移动平移
                    }
                ],
                xAxis: {
                    type: 'category',
                    boundaryGap: false,
                    data: trendData.labels,
                    axisLabel: {
                        interval: 'auto',
                        rotate: 30,
                        fontSize: 11
                    }
                },
                yAxis: {
                    type: 'value',
                    name: '项目数量',
                    minInterval: 1,
                    axisLabel: {
                        formatter: '{value}个',
                        fontSize: 11
                    }
                },
                series: [
                    {
                        name: '趋势数据',
                        type: 'line',
                        data: trendData.data,
                        smooth: false,
                        showSymbol: true,
                        symbolSize: 6,
                        lineStyle: {
                            width: 3,
                            color: color
                        },
                        itemStyle: {
                            color: color
                        },
                        areaStyle: null
                    }
                ]
            };
            
            // 应用图表配置
            try {
                window.stageTrendChart.setOption(option);
                // 添加渐入动画
                chartContainer.style.transition = 'opacity 0.3s ease';
                chartContainer.style.opacity = 1;
            } catch (error) {
                console.error('趋势图表渲染失败', error);
                chartContainer.innerHTML = '<div class="text-center py-3 text-danger">趋势图表渲染失败</div>';
            }
        } catch (e) {
            console.error('绘制趋势图表时发生错误:', e);
            chartContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    趋势图表渲染失败: ${e.message}
                </div>
            `;
        }
    }
    
    // 初始化阶段趋势切换器
    function initStageTrendToggle(data) {
        const toggleContainer = document.getElementById('stageTrendToggle');
        if (!toggleContainer) {
            console.error('找不到阶段切换容器 #stageTrendToggle');
            return;
        }
        
        // 确保有有效的数据
        if (!data || !data.stages || !data.stages.length) {
            console.warn('无效的趋势数据，使用演示数据');
            data = getAllDemoTrends(currentTrendPeriod);
        }
        
        // 清空现有内容
        toggleContainer.innerHTML = '';
        
        try {
            // 创建标题提示
            const titleSpan = document.createElement('div');
            titleSpan.className = 'mb-2 text-muted small';
            titleSpan.innerHTML = '点击切换不同阶段趋势：';
            toggleContainer.appendChild(titleSpan);
            
            // 创建点容器
            const dotsContainer = document.createElement('div');
            dotsContainer.className = 'stage-toggle-container';
            toggleContainer.appendChild(dotsContainer);
            
            // 添加阶段切换点
            data.stages.forEach(stage => {
                // 为趋势图使用数量颜色
                const color = STAGE_COLORS_COUNT[stage] || 'rgba(2, 103, 5, 0.7)';
                const dot = document.createElement('span');
                dot.className = 'stage-toggle-dot';
                dot.setAttribute('data-stage', stage);
                dot.style.backgroundColor = color;
                
                // 添加阶段名称标签
                const label = document.createElement('span');
                label.className = 'stage-toggle-label';
                label.textContent = project_stage_label(stage);
                label.style.color = color;
                
                // 创建点和标签的容器
                const dotContainer = document.createElement('div');
                dotContainer.className = 'stage-toggle-item';
                dotContainer.appendChild(dot);
                dotContainer.appendChild(label);
                
                // 设置初始活跃状态
                if (stage === currentTrendStage) {
                    dot.classList.add('active');
                    label.classList.add('active');
                }
                
                // 点击事件
                dotContainer.addEventListener('click', function() {
                    const selectedStage = dot.getAttribute('data-stage');
                    if (selectedStage === currentTrendStage) return;
                    
                    // 更新活跃状态
                    document.querySelectorAll('.stage-toggle-dot').forEach(d => d.classList.remove('active'));
                    document.querySelectorAll('.stage-toggle-label').forEach(l => l.classList.remove('active'));
                    dot.classList.add('active');
                    label.classList.add('active');
                    
                    // 切换显示的阶段趋势
                    currentTrendStage = selectedStage;
                    
                    // 动画切换图表
                    const trendChart = document.getElementById('stageTrendChart');
                    if (trendChart) {
                        // 添加淡出效果
                        trendChart.style.opacity = 0;
                        setTimeout(() => {
                            // 更新图表
                            if (trendData && trendData.trends && trendData.trends[currentTrendStage]) {
                                drawStageTrendChart(trendData.trends[currentTrendStage]);
                            } else {
                                loadStageTrendData(currentTrendPeriod, currentTrendStage);
                            }
                            // 淡入效果
                            trendChart.style.opacity = 1;
                        }, 300);
                    }
                });
                
                dotsContainer.appendChild(dotContainer);
            });
            
            // 确保容器可见
            toggleContainer.style.display = 'block';
            console.log('阶段趋势切换器初始化完成，包含 ' + data.stages.length + ' 个阶段');
        } catch (e) {
            console.error('初始化阶段切换器失败:', e);
            toggleContainer.innerHTML = `<div class="alert alert-danger p-1 small">加载阶段选择器失败: ${e.message}</div>`;
        }
    }
    
    // 更新统计UI
    function updateStatisticsUI(stats, period) {
        // 格式化数字的辅助函数
        const formatNumber = (num) => {
            return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        };
        
        // 更新有效项目数据
        document.getElementById('validProjectsCount').textContent = formatNumber(stats.total_valid_projects || 0);
        document.getElementById('validProjectsAmount').textContent = formatNumber(Math.round((stats.total_valid_amount || 0) / 10000));
        
        // 更新招标中项目数据（英文key）
        if (stats.stage_counts && stats.stage_counts['tendering']) {
            document.getElementById('tenderingProjectsCount').textContent = formatNumber(stats.stage_counts['tendering'] || 0);
        } else {
            document.getElementById('tenderingProjectsCount').textContent = '0';
        }
        
        if (stats.stage_amounts && stats.stage_amounts['tendering']) {
            document.getElementById('tenderingProjectsAmount').textContent = formatNumber(Math.round((stats.stage_amounts['tendering'] || 0) / 10000));
        } else {
            document.getElementById('tenderingProjectsAmount').textContent = '0';
        }
        
        // 更新中标项目数据（英文key）
        if (stats.stage_counts && stats.stage_counts['awarded']) {
            document.getElementById('wonProjectsCount').textContent = formatNumber(stats.stage_counts['awarded'] || 0);
        } else {
            document.getElementById('wonProjectsCount').textContent = '0';
        }
        
        if (stats.stage_amounts && stats.stage_amounts['awarded']) {
            document.getElementById('wonProjectsAmount').textContent = formatNumber(Math.round((stats.stage_amounts['awarded'] || 0) / 10000));
        } else {
            document.getElementById('wonProjectsAmount').textContent = '0';
        }
        
        // 业务推进统计（本期新建+更新的项目）
        const newCount = stats.new_projects_count || 0;
        const updatedCount = stats.updated_projects_count || 0;
        const countEl = document.getElementById('updatedProjectsCount');
        if (countEl) {
            countEl.textContent = formatNumber(newCount + updatedCount);
        }
        const newAmount = stats.new_projects_amount || 0;
        const updatedAmount = stats.updated_projects_amount || 0;
        const amountEl = document.getElementById('updatedProjectsAmount');
        if (amountEl) {
            amountEl.textContent = formatNumber(Math.round((newAmount + updatedAmount) / 10000));
        }
        
        // 绘制阶段分布图表
        setTimeout(() => {
            try {
                drawStageDistributionChart();
            } catch (err) {
                statisticsData = DEMO_STATISTICS_DATA;
                drawStageDistributionChart();
            }
        }, 100);
    }

    // 根据当前状态更新阶段分布图表
    function updateStageDistributionChart() {
        if (!statisticsData) {
            statisticsData = DEMO_STATISTICS_DATA;
        }
        try {
            drawStageDistributionChart();
        } catch (err) {
            console.error('更新阶段分布图表出错:', err);
            // 错误恢复
            statisticsData = DEMO_STATISTICS_DATA;
            drawStageDistributionChart();
        }
    }
    
    // 绘制阶段分布图表
    function drawStageDistributionChart() {
        if (typeof echarts === 'undefined') {
            console.error('ECharts库未加载');
            const chartContainer = document.getElementById('stageDistributionChart');
            if (chartContainer) {
                chartContainer.innerHTML = '<div class="alert alert-danger">图表库加载失败，请刷新页面重试</div>';
            }
            return;
        }
        
        if (!statisticsData) {
            statisticsData = DEMO_STATISTICS_DATA;
        }
        
        const chartContainer = document.getElementById('stageDistributionChart');
        if (!chartContainer) {
            console.error('找不到图表容器 #stageDistributionChart');
            return;
        }
        
        if (chartContainer.offsetWidth === 0 || chartContainer.offsetHeight === 0) {
            setTimeout(() => {
                try {
                    drawStageDistributionChart();
                } catch (err) {
                    console.error('延迟绘制图表出错:', err);
                }
            }, 200);
            return;
        }
        
        try {
            const stages = STAGE_ORDER;
            
            // 根据当前显示类型选择数据和颜色
            const dataField = currentStageChartType === 'count' ? 'stage_counts' : 'stage_amounts';
            const colorsMap = currentStageChartType === 'count' ? STAGE_COLORS_COUNT : STAGE_COLORS_AMOUNT;
            
            // 处理数据 - 如果是金额，则转换为万元单位
            const dataArr = stages.map(stage => {
                if (statisticsData[dataField] && statisticsData[dataField][stage]) {
                    if (currentStageChartType === 'amount') {
                        // 将金额转换为万元并四舍五入
                        return Math.round(statisticsData[dataField][stage] / 10000);
                    } else {
                        return statisticsData[dataField][stage];
                    }
                }
                return 0;
            });
            
            // 阶段颜色
            const colors = stages.map(stage => colorsMap[stage] || '#1890ff');
            
            const hasData = dataArr.some(val => val > 0);
            if (!hasData) {
                chartContainer.innerHTML = '<div class="text-center py-5 text-muted">暂无阶段分布数据</div>';
                return;
            }
            
            // 处理已有图表
            if (window.stageDistributionChart) {
                try {
                    if (typeof window.stageDistributionChart.dispose === 'function') {
                        window.stageDistributionChart.dispose();
                    }
                } catch (e) {
                    console.warn('图表销毁失败:', e);
                }
            }
            
            // 初始化图表
            try {
                window.stageDistributionChart = echarts.init(chartContainer);
            } catch (e) {
                console.error('图表初始化失败:', e);
                chartContainer.innerHTML = '<div class="alert alert-danger">图表初始化失败，请刷新页面重试</div>';
                return;
            }
            
            // 图表标题 - 简化标题
            const chartTitle = currentStageChartType === 'count' ? '项目数量' : '项目金额(万元)';
            
            // 阶段标签映射为中文
            const stageLabels = stages.map(stage => project_stage_label(stage));
            
            // 图表配置
            const option = {
                animation: true,
                title: {
                    text: chartTitle,
                    left: 'center',
                    top: 'top',
                    textStyle: {
                        fontSize: 16,
                        fontWeight: 'bold',
                        color: '#333333'
                    }
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: { type: 'shadow' },
                    formatter: function(params) {
                        const stageName = params[0].name;
                        const val = params[0].value;
                        if (currentStageChartType === 'count') {
                            return `<b>${stageName}</b><br/>项目数: ${val}个`;
                        } else {
                            return `<b>${stageName}</b><br/>金额: ${val}万元`;
                        }
                    }
                },
                grid: { 
                    left: '5%', 
                    right: '5%', 
                    bottom: '15%', 
                    top: '20%',
                    containLabel: true 
                },
                xAxis: {
                    type: 'category',
                    data: stageLabels,
                    axisLabel: { 
                        interval: 0, 
                        rotate: 0,
                        fontSize: 11
                    }
                },
                yAxis: {
                    type: 'value',
                    name: currentStageChartType === 'count' ? '项目数量' : '金额(万元)',
                    axisLabel: { 
                        formatter: currentStageChartType === 'count' ? '{value}个' : '{value}万',
                        fontSize: 11
                    }
                },
                series: [
                    {
                        name: currentStageChartType === 'count' ? '项目数量' : '项目金额',
                        type: 'bar',
                        data: dataArr,
                        itemStyle: {
                            color: function(params) {
                                return colors[params.dataIndex];
                            }
                        },
                        barWidth: '50%',
                        barMaxWidth: 50,
                        label: {
                            show: true,
                            position: 'top',
                            fontSize: 11,
                            formatter: function(params) {
                                if (params.value === 0) return '';
                                return params.value;
                            }
                        },
                        emphasis: {
                            itemStyle: {
                                shadowBlur: 10,
                                shadowOffsetX: 0,
                                shadowColor: 'rgba(0, 0, 0, 0.5)'
                            }
                        }
                    }
                ]
            };
            
            // 应用图表配置
            try {
                window.stageDistributionChart.setOption(option);
                // 添加动画效果
                window.stageDistributionChart.setOption({
                    series: [{
                        animationDelay: function (idx) {
                            return idx * 50;
                        }
                    }]
                });
            } catch (error) {
                console.error('图表渲染失败', error);
                chartContainer.innerHTML = '<div class="text-center py-3 text-danger">图表渲染失败</div>';
            }
            
            // 窗口大小调整时重绘图表
            if (!window.chartResizeListener) {
                window.chartResizeListener = function() {
                    try {
                        if (window.stageDistributionChart) window.stageDistributionChart.resize();
                        if (window.stageTrendChart) window.stageTrendChart.resize();
                    } catch (e) {
                        console.warn('图表大小调整失败:', e);
                    }
                };
                window.addEventListener('resize', window.chartResizeListener);
            }
        } catch (e) {
            console.error('绘制阶段分布图表时发生错误:', e);
            chartContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    图表渲染失败: ${e.message}
                </div>
            `;
        }
    }
    
    // 开始自动切换
    function startAutoSwitch() {
        // 清除现有的定时器
        if (window.autoSwitchTimer) {
            clearInterval(window.autoSwitchTimer);
            window.autoSwitchTimer = null;
        }
        
        // 追踪切换次数，用于交替切换不同图表
        let switchCount = 0;
        
        // 设置每20秒切换一次
        window.autoSwitchTimer = setInterval(() => {
            // 根据计数器交替切换不同图表
            switchCount++;
            
            if (switchCount % 2 === 1) {
                // 切换阶段分布图表类型（奇数次）
                const chartToggleDots = document.querySelectorAll('.chart-toggle-dot');
                if (chartToggleDots && chartToggleDots.length > 0) {
                    let activeIndex = -1;
                    chartToggleDots.forEach((dot, index) => {
                        if (dot.classList.contains('active')) {
                            activeIndex = index;
                        }
                    });
                    
                    // 计算下一个索引
                    const nextIndex = (activeIndex + 1) % chartToggleDots.length;
                    // 模拟点击下一个点
                    chartToggleDots[nextIndex].click();
                }
            } else {
                // 切换阶段趋势图（偶数次）
                const stageToggleDots = document.querySelectorAll('.stage-toggle-dot');
                if (stageToggleDots && stageToggleDots.length > 0) {
                    let activeIndex = -1;
                    stageToggleDots.forEach((dot, index) => {
                        if (dot.classList.contains('active')) {
                            activeIndex = index;
                        }
                    });
                    
                    // 计算下一个索引
                    const nextIndex = (activeIndex + 1) % stageToggleDots.length;
                    // 模拟点击下一个点的父元素（stage-toggle-item）
                    const parent = stageToggleDots[nextIndex].closest('.stage-toggle-item');
                    if (parent) {
                        parent.click();
                    } else {
                        stageToggleDots[nextIndex].click();
                    }
                }
            }
        }, 20000);
        
        // 将定时器ID暴露为全局变量，方便外部控制
        return window.autoSwitchTimer;
    }

    // 监听账户切换事件，自动刷新统计和趋势数据
    document.addEventListener('reloadStatistics', function(e) {
        // 获取当前账户ID
        let accountId = null;
        if (typeof AccountSelector !== 'undefined') {
            accountId = AccountSelector.getCurrentAccountId();
        }
        // 重新加载统计数据和趋势数据
        loadStatisticsData(currentPeriod);
        loadStageTrendData(currentTrendPeriod);
    });
}); 