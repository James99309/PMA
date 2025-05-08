/**
 * 项目阶段可视化进度条组件
 */
class ProjectStageProgress {
    constructor(options) {
        this.containerId = options.containerId;
        this.projectId = options.projectId;
        this.currentStage = options.currentStage;
        this.csrfToken = options.csrfToken;
        this.updateUrl = options.updateUrl;
        this.stageHistory = options.stageHistory || null;
        this.canEdit = options.canEdit || false;

        // 项目阶段定义
        this.stages = [
            { id: 0, name: '发现', value: '发现' },
            { id: 1, name: '品牌植入', value: '品牌植入' },
            { id: 2, name: '招标前', value: '招标前' },
            { id: 3, name: '招标中', value: '招标中' },
            { id: 4, name: '中标', value: '中标' },
            { id: 5, name: '失败', value: '失败' }
        ];

        // 初始化
        this.init();
    }

    /**
     * 初始化组件
     */
    init() {
        // 计算当前阶段索引
        this.currentStageIndex = this.getStageIndex(this.currentStage);
        
        // 阶段历史记录计算
        this.calculateStageDurations();
        
        // 渲染进度条
        this.render();
        
        // 绑定事件
        this.bindEvents();
    }

    /**
     * 获取阶段索引
     */
    getStageIndex(stageName) {
        const stageIndex = this.stages.findIndex(stage => stage.value === stageName);
        return stageIndex >= 0 ? stageIndex : 0;
    }

    /**
     * 获取下一个阶段
     */
    getNextStage() {
        // 如果当前是失败阶段，无下一阶段
        if (this.currentStage === '失败') {
            return null;
        }
        
        // 如果当前是最后一个正常阶段，无下一阶段
        if (this.currentStageIndex === 4) {
            return null;
        }

        return this.stages[this.currentStageIndex + 1];
    }

    /**
     * 计算各阶段持续时间
     */
    calculateStageDurations() {
        // 如果有阶段历史，使用历史计算持续时间
        if (this.stageHistory && Array.isArray(this.stageHistory)) {
            this.stageDurations = this.stageHistory.map(stage => {
                return {
                    stageName: stage.stage,
                    days: this.calculateDaysBetween(stage.startDate, stage.endDate || new Date())
                };
            });
        } else {
            // 无历史记录，使用默认值
            this.stageDurations = this.stages.map(stage => {
                return {
                    stageName: stage.value,
                    days: stage.value === this.currentStage ? 
                        this.getRandomDuration() : 
                        (this.getStageIndex(stage.value) < this.currentStageIndex ? this.getRandomDuration() : 0)
                };
            });
        }
    }

    /**
     * 计算两个日期之间的天数
     */
    calculateDaysBetween(startDate, endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        const diffTime = Math.abs(end - start);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays;
    }

    /**
     * 生成随机持续时间（用于演示）
     */
    getRandomDuration() {
        return Math.floor(Math.random() * 20) + 5; // 5-25天
    }

    /**
     * 渲染进度条
     */
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        // 创建进度条容器
        const progressContainer = document.createElement('div');
        progressContainer.className = 'stage-progress-container';

        // 创建进度条
        const progressBar = document.createElement('div');
        progressBar.className = 'stage-progress-bar';

        // 创建进度线
        const progressLine = document.createElement('div');
        progressLine.className = 'stage-progress-line';

        // 计算进度线宽度（根据当前阶段位置）
        const validStages = this.stages.filter(stage => stage.value !== '失败');
        const progressPercentage = this.currentStage === '失败' ? 0 : 
            (this.currentStageIndex / (validStages.length - 1)) * 100;
        progressLine.style.width = `${progressPercentage}%`;

        progressContainer.appendChild(progressLine);
        progressContainer.appendChild(progressBar);

        // 添加各阶段标记
        this.stages.forEach((stage, index) => {
            // 跳过失败阶段，它是特殊状态
            if (stage.value === '失败' && this.currentStage !== '失败') {
                return;
            }

            const stageMarker = document.createElement('div');
            stageMarker.className = 'stage-marker';
            stageMarker.dataset.stage = stage.value;

            // 设置阶段状态样式
            if (index < this.currentStageIndex) {
                stageMarker.classList.add('stage-completed');
            } else if (index === this.currentStageIndex) {
                stageMarker.classList.add('stage-current');
                // 如果用户有编辑权限且不处于最后阶段或失败阶段，添加可操作类
                if (this.canEdit && index < 4 && stage.value !== '失败') {
                    stageMarker.classList.add('stage-actionable');
                }
            }

            // 创建阶段圆点
            const stageDot = document.createElement('div');
            stageDot.className = 'stage-dot';
            
            // 添加阶段图标
            if (index < this.currentStageIndex || index === this.currentStageIndex) {
                const icon = document.createElement('i');
                icon.className = index < this.currentStageIndex ? 'fas fa-check' : 'fas fa-circle';
                stageDot.appendChild(icon);
            }

            // 创建阶段名称
            const stageName = document.createElement('div');
            stageName.className = 'stage-name';
            stageName.textContent = stage.name;

            // 创建阶段天数
            const stageDays = document.createElement('div');
            stageDays.className = 'stage-days';
            
            // 获取当前阶段持续时间
            const durationItem = this.stageDurations.find(item => item.stageName === stage.value);
            const days = durationItem ? durationItem.days : 0;
            
            stageDays.textContent = days > 0 ? `${days} 天` : '';

            // 组装阶段标记
            stageMarker.appendChild(stageDot);
            stageMarker.appendChild(stageName);
            stageMarker.appendChild(stageDays);

            // 添加推进按钮（仅当前阶段且有权限时显示）
            if (index === this.currentStageIndex && this.canEdit && index < 4) {
                const advanceBtn = document.createElement('button');
                advanceBtn.className = 'btn btn-sm btn-outline-success stage-advance-btn';
                advanceBtn.innerHTML = '<i class="fas fa-arrow-right"></i> 推进';
                advanceBtn.dataset.toggle = 'modal';
                advanceBtn.dataset.target = '#advanceStageModal';
                stageMarker.appendChild(advanceBtn);
            }

            progressBar.appendChild(stageMarker);
        });

        // 添加到容器
        container.innerHTML = '';
        container.appendChild(progressContainer);

        // 添加确认推进模态框
        this.renderAdvanceModal(container);
    }

    /**
     * 渲染确认推进模态框
     */
    renderAdvanceModal(container) {
        const nextStage = this.getNextStage();
        if (!nextStage) return;

        const modalHtml = `
            <div class="modal fade advance-modal" id="advanceStageModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">确认推进项目阶段</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p>您确定要将项目从 <strong>${this.currentStage}</strong> 阶段推进到 <strong class="next-stage">${nextStage.name}</strong> 阶段吗？</p>
                            <p>此操作将更新项目的当前阶段状态，不可回退。</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-success" id="confirmAdvanceBtn">确认推进</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 添加模态框到DOM
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        container.appendChild(modalContainer);
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        // 当前阶段点击事件（推进阶段）
        const currentStage = container.querySelector('.stage-current.stage-actionable');
        if (currentStage) {
            currentStage.addEventListener('click', (e) => {
                // 处理点击确认弹窗
                const modal = new bootstrap.Modal(document.getElementById('advanceStageModal'));
                modal.show();
            });
        }

        // 确认推进按钮点击事件
        const confirmBtn = container.querySelector('#confirmAdvanceBtn');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => {
                this.advanceStage();
            });
        }
    }

    /**
     * 推进到下一阶段
     */
    advanceStage() {
        const nextStage = this.getNextStage();
        if (!nextStage) return;

        // 发送请求到服务器更新阶段
        fetch(this.updateUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            },
            body: JSON.stringify({
                project_id: this.projectId,
                current_stage: nextStage.value
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('网络请求失败');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // 更新成功，刷新页面
                window.location.reload();
            } else {
                alert('更新阶段失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('更新阶段错误:', error);
            alert('更新阶段时发生错误，请重试');
        });
    }
}

// 文档加载完成后运行
document.addEventListener('DOMContentLoaded', function() {
    // 项目阶段进度条初始化由页面调用
}); 