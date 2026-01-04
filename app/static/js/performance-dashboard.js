/**
 * 绩效看板图表脚本
 *
 * 使用 ECharts 5.4.3 绘制绩效相关图表
 * - 目标达成趋势图 (折线图)
 * - 月度增长对比图 (柱状图)
 * - 预算使用趋势图 (混合图)
 * - 费用科目分布图 (饼图)
 * - 活跃度维度图 (雷达图)
 * - 活跃度趋势图 (折线图)
 * - 行业分布图 (饼图)
 * - 行业趋势图 (堆叠柱状图)
 */

const PerformanceDashboardCharts = {

    // 图表实例存储
    instances: {},

    // 通用颜色配置
    colors: {
        primary: '#3b82f6',      // 蓝色
        success: '#22c55e',      // 绿色
        warning: '#f59e0b',      // 黄色
        danger: '#ef4444',       // 红色
        info: '#06b6d4',         // 青色
        purple: '#8b5cf6',       // 紫色
        pink: '#ec4899',         // 粉色
        indigo: '#6366f1',       // 靛蓝

        // 图表系列颜色
        series: ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],

        // 渐变色
        gradientBlue: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
                { offset: 0, color: 'rgba(59, 130, 246, 0.8)' },
                { offset: 1, color: 'rgba(59, 130, 246, 0.1)' }
            ]
        },
        gradientGreen: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
                { offset: 0, color: 'rgba(34, 197, 94, 0.8)' },
                { offset: 1, color: 'rgba(34, 197, 94, 0.1)' }
            ]
        }
    },

    // 月份标签
    months: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],

    // 通用配置
    baseOption: {
        animation: true,
        animationDuration: 500,
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            top: '15%',
            containLabel: true
        },
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#e5e7eb',
            borderWidth: 1,
            textStyle: {
                color: '#374151'
            },
            axisPointer: {
                type: 'cross',
                crossStyle: {
                    color: '#999'
                }
            }
        }
    },

    /**
     * 初始化图表实例
     * @param {string} containerId - 容器ID
     * @returns {Object|null} ECharts实例
     */
    initChart(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`图表容器不存在: ${containerId}`);
            return null;
        }

        // 如果已有实例，先销毁
        if (this.instances[containerId]) {
            this.instances[containerId].dispose();
        }

        const chart = echarts.init(container);
        this.instances[containerId] = chart;

        // 响应式处理
        window.addEventListener('resize', () => {
            chart.resize();
        });

        return chart;
    },

    /**
     * 销毁所有图表实例
     */
    dispose() {
        Object.keys(this.instances).forEach(key => {
            if (this.instances[key]) {
                this.instances[key].dispose();
            }
        });
        this.instances = {};
    },

    /**
     * 目标达成趋势图 - 折线图
     * @param {string} containerId - 容器ID
     * @param {Object} data - 数据对象
     */
    renderGoalTrendChart(containerId, data) {
        const chart = this.initChart(containerId);
        if (!chart) return;

        const option = {
            ...this.baseOption,
            legend: {
                data: ['目标', '实际', '去年同期'],
                top: '5%'
            },
            xAxis: {
                type: 'category',
                data: this.months,
                axisLine: { lineStyle: { color: '#e5e7eb' } },
                axisLabel: { color: '#6b7280' }
            },
            yAxis: {
                type: 'value',
                name: '金额 (万元)',
                nameTextStyle: { color: '#6b7280' },
                axisLine: { show: false },
                axisLabel: { color: '#6b7280' },
                splitLine: { lineStyle: { color: '#f3f4f6' } }
            },
            series: [
                {
                    name: '目标',
                    type: 'line',
                    data: data.targets || [],
                    lineStyle: { color: this.colors.warning, width: 2, type: 'dashed' },
                    itemStyle: { color: this.colors.warning },
                    symbol: 'circle',
                    symbolSize: 6
                },
                {
                    name: '实际',
                    type: 'line',
                    data: data.actuals || [],
                    lineStyle: { color: this.colors.primary, width: 3 },
                    itemStyle: { color: this.colors.primary },
                    symbol: 'circle',
                    symbolSize: 8,
                    areaStyle: this.colors.gradientBlue
                },
                {
                    name: '去年同期',
                    type: 'line',
                    data: data.lastYear || [],
                    lineStyle: { color: '#9ca3af', width: 2, type: 'dotted' },
                    itemStyle: { color: '#9ca3af' },
                    symbol: 'circle',
                    symbolSize: 4
                }
            ]
        };

        chart.setOption(option);
    },

    /**
     * 月度增长对比图 - 柱状图
     * @param {string} containerId - 容器ID
     * @param {Object} data - 数据对象
     */
    renderMonthlyGrowthChart(containerId, data) {
        const chart = this.initChart(containerId);
        if (!chart) return;

        const option = {
            ...this.baseOption,
            legend: {
                data: ['植入额', '销售额', '新客户', '新项目'],
                top: '5%'
            },
            xAxis: {
                type: 'category',
                data: this.months,
                axisLine: { lineStyle: { color: '#e5e7eb' } },
                axisLabel: { color: '#6b7280' }
            },
            yAxis: {
                type: 'value',
                name: '增长率 (%)',
                nameTextStyle: { color: '#6b7280' },
                axisLine: { show: false },
                axisLabel: {
                    color: '#6b7280',
                    formatter: '{value}%'
                },
                splitLine: { lineStyle: { color: '#f3f4f6' } }
            },
            series: [
                {
                    name: '植入额',
                    type: 'bar',
                    data: data.implant_growth || [],
                    itemStyle: { color: this.colors.primary }
                },
                {
                    name: '销售额',
                    type: 'bar',
                    data: data.sales_growth || [],
                    itemStyle: { color: this.colors.success }
                },
                {
                    name: '新客户',
                    type: 'bar',
                    data: data.customer_growth || [],
                    itemStyle: { color: this.colors.warning }
                },
                {
                    name: '新项目',
                    type: 'bar',
                    data: data.project_growth || [],
                    itemStyle: { color: this.colors.purple }
                }
            ]
        };

        chart.setOption(option);
    },

    /**
     * 预算使用趋势图 - 混合图
     * @param {string} containerId - 容器ID
     * @param {Object} data - 数据对象
     */
    renderBudgetTrendChart(containerId, data) {
        const chart = this.initChart(containerId);
        if (!chart) return;

        const option = {
            ...this.baseOption,
            legend: {
                data: ['月度报销', '累计使用率'],
                top: '5%'
            },
            xAxis: {
                type: 'category',
                data: this.months,
                axisLine: { lineStyle: { color: '#e5e7eb' } },
                axisLabel: { color: '#6b7280' }
            },
            yAxis: [
                {
                    type: 'value',
                    name: '金额 (万元)',
                    nameTextStyle: { color: '#6b7280' },
                    axisLine: { show: false },
                    axisLabel: { color: '#6b7280' },
                    splitLine: { lineStyle: { color: '#f3f4f6' } }
                },
                {
                    type: 'value',
                    name: '使用率 (%)',
                    nameTextStyle: { color: '#6b7280' },
                    axisLine: { show: false },
                    axisLabel: {
                        color: '#6b7280',
                        formatter: '{value}%'
                    },
                    splitLine: { show: false },
                    max: 100
                }
            ],
            series: [
                {
                    name: '月度报销',
                    type: 'bar',
                    data: data.monthly_expense || [],
                    itemStyle: {
                        color: this.colors.primary,
                        borderRadius: [4, 4, 0, 0]
                    },
                    barWidth: '40%'
                },
                {
                    name: '累计使用率',
                    type: 'line',
                    yAxisIndex: 1,
                    data: data.cumulative_rate || [],
                    lineStyle: { color: this.colors.warning, width: 3 },
                    itemStyle: { color: this.colors.warning },
                    symbol: 'circle',
                    symbolSize: 8,
                    markLine: {
                        silent: true,
                        data: [
                            {
                                yAxis: 80,
                                lineStyle: { color: this.colors.danger, type: 'dashed' },
                                label: { show: true, formatter: '警戒线 80%' }
                            }
                        ]
                    }
                }
            ]
        };

        chart.setOption(option);
    },

    /**
     * 费用科目分布图 - 饼图
     * @param {string} containerId - 容器ID
     * @param {Object} data - 数据对象
     */
    renderExpenseCategoryChart(containerId, data) {
        const chart = this.initChart(containerId);
        if (!chart) return;

        const categoryNames = {
            'entertainment': '招待费',
            'travel': '差旅费',
            'transport': '交通费',
            'office': '办公费',
            'communication': '通讯费',
            'other': '其他'
        };

        const pieData = Object.entries(data).map(([key, value], index) => ({
            name: categoryNames[key] || key,
            value: value,
            itemStyle: { color: this.colors.series[index % this.colors.series.length] }
        })).filter(item => item.value > 0);

        const option = {
            tooltip: {
                trigger: 'item',
                formatter: '{b}: {c}万元 ({d}%)'
            },
            legend: {
                orient: 'vertical',
                right: '5%',
                top: 'center'
            },
            series: [
                {
                    type: 'pie',
                    radius: ['40%', '70%'],
                    center: ['40%', '50%'],
                    avoidLabelOverlap: false,
                    itemStyle: {
                        borderRadius: 6,
                        borderColor: '#fff',
                        borderWidth: 2
                    },
                    label: {
                        show: false,
                        position: 'center'
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: 16,
                            fontWeight: 'bold',
                            formatter: '{b}\n{d}%'
                        }
                    },
                    labelLine: {
                        show: false
                    },
                    data: pieData
                }
            ]
        };

        chart.setOption(option);
    },

    /**
     * 活跃度维度图 - 雷达图
     * @param {string} containerId - 容器ID
     * @param {Object} data - 数据对象
     */
    renderActivityRadarChart(containerId, data) {
        const chart = this.initChart(containerId);
        if (!chart) return;

        const indicators = [
            { name: '行动记录数', max: 100 },
            { name: '回复数', max: 100 },
            { name: '平均字数', max: 100 },
            { name: '客户覆盖率', max: 100 },
            { name: '项目关联率', max: 100 }
        ];

        const values = [
            data.action_count?.score || 0,
            data.reply_count?.score || 0,
            data.avg_length?.score || 0,
            data.customer_coverage?.score || 0,
            data.project_link_rate?.score || 0
        ];

        const option = {
            tooltip: {
                trigger: 'item'
            },
            radar: {
                indicator: indicators,
                shape: 'circle',
                splitNumber: 4,
                axisName: {
                    color: '#6b7280'
                },
                splitLine: {
                    lineStyle: {
                        color: ['#f3f4f6', '#e5e7eb', '#d1d5db', '#9ca3af']
                    }
                },
                splitArea: {
                    show: true,
                    areaStyle: {
                        color: ['rgba(59, 130, 246, 0.02)', 'rgba(59, 130, 246, 0.04)']
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: '#e5e7eb'
                    }
                }
            },
            series: [
                {
                    type: 'radar',
                    data: [
                        {
                            value: values,
                            name: '活跃度指标',
                            areaStyle: {
                                color: 'rgba(59, 130, 246, 0.3)'
                            },
                            lineStyle: {
                                color: this.colors.primary,
                                width: 2
                            },
                            itemStyle: {
                                color: this.colors.primary
                            },
                            symbol: 'circle',
                            symbolSize: 6
                        }
                    ]
                }
            ]
        };

        chart.setOption(option);
    },

    /**
     * 活跃度趋势图 - 双Y轴折线图
     * @param {string} containerId - 容器ID
     * @param {Array} data - 月度趋势数据
     */
    renderActivityTrendChart(containerId, data) {
        const chart = this.initChart(containerId);
        if (!chart) return;

        const actionCounts = data.map(d => d.action_count || 0);
        const scores = data.map(d => d.score || 0);

        const option = {
            ...this.baseOption,
            legend: {
                data: ['行动记录数', '活跃度评分'],
                top: '5%'
            },
            xAxis: {
                type: 'category',
                data: this.months,
                axisLine: { lineStyle: { color: '#e5e7eb' } },
                axisLabel: { color: '#6b7280' }
            },
            yAxis: [
                {
                    type: 'value',
                    name: '记录数',
                    nameTextStyle: { color: '#6b7280' },
                    axisLine: { show: false },
                    axisLabel: { color: '#6b7280' },
                    splitLine: { lineStyle: { color: '#f3f4f6' } }
                },
                {
                    type: 'value',
                    name: '评分',
                    nameTextStyle: { color: '#6b7280' },
                    axisLine: { show: false },
                    axisLabel: { color: '#6b7280' },
                    splitLine: { show: false },
                    max: 100
                }
            ],
            series: [
                {
                    name: '行动记录数',
                    type: 'bar',
                    data: actionCounts,
                    itemStyle: {
                        color: this.colors.primary,
                        borderRadius: [4, 4, 0, 0]
                    },
                    barWidth: '30%'
                },
                {
                    name: '活跃度评分',
                    type: 'line',
                    yAxisIndex: 1,
                    data: scores,
                    lineStyle: { color: this.colors.success, width: 3 },
                    itemStyle: { color: this.colors.success },
                    symbol: 'circle',
                    symbolSize: 8,
                    areaStyle: this.colors.gradientGreen
                }
            ]
        };

        chart.setOption(option);
    },

    /**
     * 行业分布图 - 饼图
     * @param {string} containerId - 容器ID
     * @param {Object} data - 行业分布数据
     */
    renderIndustryDistributionChart(containerId, data) {
        const chart = this.initChart(containerId);
        if (!chart) return;

        const pieData = Object.entries(data).map(([name, value], index) => ({
            name: name || '未分类',
            value: value,
            itemStyle: { color: this.colors.series[index % this.colors.series.length] }
        })).filter(item => item.value > 0);

        const option = {
            tooltip: {
                trigger: 'item',
                formatter: '{b}: {c}个 ({d}%)'
            },
            legend: {
                type: 'scroll',
                orient: 'vertical',
                right: '5%',
                top: 'center'
            },
            series: [
                {
                    type: 'pie',
                    radius: ['40%', '70%'],
                    center: ['40%', '50%'],
                    roseType: 'radius',
                    itemStyle: {
                        borderRadius: 6,
                        borderColor: '#fff',
                        borderWidth: 2
                    },
                    label: {
                        show: false
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: 14,
                            fontWeight: 'bold',
                            formatter: '{b}\n{d}%'
                        }
                    },
                    data: pieData
                }
            ]
        };

        chart.setOption(option);
    },

    /**
     * 行业趋势图 - 堆叠柱状图
     * @param {string} containerId - 容器ID
     * @param {Array} data - 月度行业趋势数据
     */
    renderIndustryTrendChart(containerId, data) {
        const chart = this.initChart(containerId);
        if (!chart) return;

        // 获取所有行业
        const industries = new Set();
        data.forEach(month => {
            if (month.industries) {
                Object.keys(month.industries).forEach(ind => industries.add(ind));
            }
        });

        const industryList = Array.from(industries).slice(0, 6); // 最多显示6个行业

        const series = industryList.map((industry, index) => ({
            name: industry || '未分类',
            type: 'bar',
            stack: 'total',
            emphasis: {
                focus: 'series'
            },
            data: data.map(month => month.industries?.[industry] || 0),
            itemStyle: { color: this.colors.series[index % this.colors.series.length] }
        }));

        const option = {
            ...this.baseOption,
            legend: {
                type: 'scroll',
                top: '5%'
            },
            xAxis: {
                type: 'category',
                data: this.months,
                axisLine: { lineStyle: { color: '#e5e7eb' } },
                axisLabel: { color: '#6b7280' }
            },
            yAxis: {
                type: 'value',
                name: '数量',
                nameTextStyle: { color: '#6b7280' },
                axisLine: { show: false },
                axisLabel: { color: '#6b7280' },
                splitLine: { lineStyle: { color: '#f3f4f6' } }
            },
            series: series
        };

        chart.setOption(option);
    },

    /**
     * 进度环形图 - 用于显示单个指标的完成度
     * @param {string} containerId - 容器ID
     * @param {number} value - 当前值
     * @param {number} target - 目标值
     * @param {string} label - 标签
     */
    renderProgressRing(containerId, value, target, label) {
        const chart = this.initChart(containerId);
        if (!chart) return;

        const rate = target > 0 ? Math.min((value / target) * 100, 100) : 0;
        const color = rate >= 100 ? this.colors.success :
                      rate >= 80 ? this.colors.primary :
                      rate >= 60 ? this.colors.warning : this.colors.danger;

        const option = {
            series: [
                {
                    type: 'gauge',
                    startAngle: 90,
                    endAngle: -270,
                    pointer: { show: false },
                    progress: {
                        show: true,
                        overlap: false,
                        roundCap: true,
                        clip: false,
                        itemStyle: {
                            color: color
                        }
                    },
                    axisLine: {
                        lineStyle: {
                            width: 12,
                            color: [[1, '#f3f4f6']]
                        }
                    },
                    splitLine: { show: false },
                    axisTick: { show: false },
                    axisLabel: { show: false },
                    data: [
                        {
                            value: rate,
                            name: label,
                            title: {
                                offsetCenter: ['0%', '0%'],
                                fontSize: 12,
                                color: '#6b7280'
                            },
                            detail: {
                                valueAnimation: true,
                                offsetCenter: ['0%', '30%'],
                                fontSize: 18,
                                fontWeight: 'bold',
                                color: color,
                                formatter: function(value) {
                                    return value.toFixed(0) + '%';
                                }
                            }
                        }
                    ]
                }
            ]
        };

        chart.setOption(option);
    }
};

// 暴露到全局
window.PerformanceDashboardCharts = PerformanceDashboardCharts;
