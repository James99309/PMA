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
        this.mainStages = [
            { id: 0, name: '发现', value: '发现' },
            { id: 1, name: '品牌植入', value: '品牌植入' },
            { id: 2, name: '招标前', value: '招标前' },
            { id: 3, name: '招标中', value: '招标中' },
            { id: 4, name: '中标', value: '中标' },
            { id: 5, name: '签约', value: '签约' }
        ];
        this.branchStages = [
            { id: 6, name: '失败', value: '失败' },
            { id: 7, name: '搁置', value: '搁置' }
        ];
        this.stages = [...this.mainStages, ...this.branchStages];
        this.lastMainStage = this.mainStages.find(s => s.value === this.currentStage) ? this.currentStage : this.mainStages[0].value;

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
            // 无历史记录，所有阶段天数显示为"未知"
            this.stageDurations = this.stages.map(stage => {
                return {
                    stageName: stage.value,
                    days: '未知'
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

        // 创建主线进度条
        const progressBar = document.createElement('div');
        progressBar.className = 'stage-progress-bar';

        // 创建主线灰色贯穿线
        const mainLine = document.createElement('div');
        mainLine.className = 'stage-main-line';
        progressBar.appendChild(mainLine);

        // 渲染主线阶段
        this.mainStages.forEach((stage, index) => {
            const stageMarker = document.createElement('div');
            stageMarker.className = 'stage-marker';
            stageMarker.dataset.stage = stage.value;

            // 状态样式
            if (this.currentStage === '失败' || this.currentStage === '搁置') {
                stageMarker.classList.add('stage-disabled');
            } else if (index < this.getStageIndex(this.currentStage)) {
                stageMarker.classList.add('stage-completed');
            } else if (index === this.getStageIndex(this.currentStage)) {
                stageMarker.classList.add('stage-current');
            } else if (index === this.getStageIndex(this.currentStage) + 1 && this.canEdit) {
                // 下一个阶段可点击
                stageMarker.classList.add('stage-actionable');
                stageMarker.style.cursor = 'pointer';
                // 悬停动画和点击图标
                const stageDot = document.createElement('div');
                stageDot.className = 'stage-dot';
                stageDot.innerHTML = '<i class="fas fa-arrow-right"></i>';
                stageMarker.appendChild(stageDot);
                // 名称
                const stageName = document.createElement('div');
                stageName.className = 'stage-name';
                stageName.textContent = stage.name;
                stageMarker.appendChild(stageName);
                // 推进信息
                const durationItem = this.stageDurations.find(item => item.stageName === stage.value);
                const days = durationItem ? durationItem.days : '未知';
                let stageExtra = '';
                if (this.stageHistory && Array.isArray(this.stageHistory)) {
                    const historyItem = this.stageHistory.find(item => item.stage === stage.value);
                    if (historyItem && historyItem.startDate && typeof days === 'number' && days > 0) {
                        stageExtra = `${historyItem.startDate.split(' ')[0]}｜${days}天`;
                    } else if (historyItem && historyItem.startDate) {
                        stageExtra = `${historyItem.startDate.split(' ')[0]}`;
                    } else if (typeof days === 'number' && days > 0) {
                        stageExtra = `${days}天`;
                    }
                }
                if (stageExtra) {
                    const stageInfo = document.createElement('div');
                    stageInfo.className = 'stage-extra stage-days';
                    stageInfo.textContent = stageExtra;
                    stageMarker.appendChild(stageInfo);
                }
                // 悬停动画
                stageMarker.addEventListener('mouseenter', () => {
                    stageMarker.classList.add('stage-current');
                });
                stageMarker.addEventListener('mouseleave', () => {
                    stageMarker.classList.remove('stage-current');
                });
                // 点击推进
                stageMarker.addEventListener('click', () => {
                    this.currentStage = stage.value;
                    this.currentStageIndex = this.getStageIndex(this.currentStage);
                    this.init();
                });
                progressBar.appendChild(stageMarker);
                return;
            }

            // 圆点
            const stageDot = document.createElement('div');
            stageDot.className = 'stage-dot';
            if (this.currentStage === '失败' || this.currentStage === '搁置') {
                stageDot.classList.add('dot-disabled');
            }
            if (index < this.getStageIndex(this.currentStage) && this.currentStage !== '失败' && this.currentStage !== '搁置') {
                const icon = document.createElement('i');
                icon.className = 'fas fa-check';
                stageDot.appendChild(icon);
            } else if (index === this.getStageIndex(this.currentStage) && this.currentStage !== '失败' && this.currentStage !== '搁置') {
                const icon = document.createElement('i');
                icon.className = 'fas fa-circle';
                stageDot.appendChild(icon);
            }
            stageMarker.appendChild(stageDot);

            // 名称
            const stageName = document.createElement('div');
            stageName.className = 'stage-name';
            stageName.textContent = stage.name;
            stageMarker.appendChild(stageName);

            // 推进信息
            const durationItem = this.stageDurations.find(item => item.stageName === stage.value);
            const days = durationItem ? durationItem.days : '未知';
            let stageExtra = '';
            if (this.stageHistory && Array.isArray(this.stageHistory)) {
                const historyItem = this.stageHistory.find(item => item.stage === stage.value);
                if (historyItem && historyItem.startDate && typeof days === 'number' && days > 0) {
                    stageExtra = `${historyItem.startDate.split(' ')[0]}｜${days}天`;
                } else if (historyItem && historyItem.startDate) {
                    stageExtra = `${historyItem.startDate.split(' ')[0]}`;
                } else if (typeof days === 'number' && days > 0) {
                    stageExtra = `${days}天`;
                }
            }
            if (stageExtra) {
                const stageInfo = document.createElement('div');
                stageInfo.className = 'stage-extra stage-days';
                stageInfo.textContent = stageExtra;
                stageMarker.appendChild(stageInfo);
            }

            progressBar.appendChild(stageMarker);
        });

        // 渲染分支节点（失败、搁置）在主线下方居中分布
        const branchContainer = document.createElement('div');
        branchContainer.className = 'stage-branch-container';
        this.branchStages.forEach(branch => {
            const branchMarker = document.createElement('div');
            branchMarker.className = 'stage-marker stage-branch';
            branchMarker.dataset.stage = branch.value;

            // 状态样式
            if (this.currentStage === branch.value) {
                branchMarker.classList.add('stage-current');
                if (branch.value === '失败') {
                    branchMarker.classList.add('stage-failed');
                } else if (branch.value === '搁置') {
                    branchMarker.classList.add('stage-pending');
                }
            } else if (this.currentStage === '失败' || this.currentStage === '搁置') {
                branchMarker.classList.add('stage-disabled');
            }

            // 圆点
            const branchDot = document.createElement('div');
            branchDot.className = 'stage-dot';
            if (this.currentStage === branch.value) {
                if (branch.value === '失败') {
                    branchDot.style.backgroundColor = '#e74c3c';
                    branchDot.style.borderColor = '#e74c3c';
                } else if (branch.value === '搁置') {
                    branchDot.style.backgroundColor = '#555';
                    branchDot.style.borderColor = '#555';
                }
            }
            // 点击圆点弹窗确认
            branchDot.addEventListener('click', (e) => {
                e.stopPropagation();
                let msg = this.currentStage === branch.value
                    ? `确定要恢复到主线阶段吗？`
                    : `确定要将项目阶段切换为"${branch.value}"吗？`;
                if (window.confirm(msg)) {
                    if (this.currentStage === branch.value) {
                        // 恢复到上次主线阶段
                        this.currentStage = this.lastMainStage;
                        this.currentStageIndex = this.getStageIndex(this.currentStage);
                    } else {
                        // 进入分支，记住主线阶段
                        if (this.mainStages.find(s => s.value === this.currentStage)) {
                            this.lastMainStage = this.currentStage;
                        }
                        this.currentStage = branch.value;
                        this.currentStageIndex = this.getStageIndex(this.currentStage);
                    }
                    this.init();
                }
            });
            branchMarker.appendChild(branchDot);

            // 名称
            const branchName = document.createElement('div');
            branchName.className = 'stage-name';
            branchName.textContent = branch.name;
            branchMarker.appendChild(branchName);

            // 推进信息
            const durationItem = this.stageDurations.find(item => item.stageName === branch.value);
            const days = durationItem ? durationItem.days : '未知';
            let stageExtra = '';
            if (this.stageHistory && Array.isArray(this.stageHistory)) {
                const historyItem = this.stageHistory.find(item => item.stage === branch.value);
                if (historyItem && historyItem.startDate && typeof days === 'number' && days > 0) {
                    stageExtra = `${historyItem.startDate.split(' ')[0]}｜${days}天`;
                } else if (historyItem && historyItem.startDate) {
                    stageExtra = `${historyItem.startDate.split(' ')[0]}`;
                } else if (typeof days === 'number' && days > 0) {
                    stageExtra = `${days}天`;
                }
            }
            if (stageExtra) {
                const stageInfo = document.createElement('div');
                stageInfo.className = 'stage-extra stage-days';
                stageInfo.textContent = stageExtra;
                branchMarker.appendChild(stageInfo);
            }

            branchContainer.appendChild(branchMarker);
        });
        // 居中分布到主线下方
        progressContainer.appendChild(progressBar);
        progressContainer.appendChild(branchContainer);

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