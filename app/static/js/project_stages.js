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
        this.lastMainStage = this.getLastMainStageBeforeBranch();

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
                // 点击推进 - 修复：不再直接更新this.currentStage，而是直接调用API
                stageMarker.addEventListener('click', () => {
                    // 不再本地更新状态，直接调用API
                    this.updateStage(stage.value);
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
            }

            // 圆点
            const branchDot = document.createElement('div');
            branchDot.className = 'stage-dot';
            if (branch.value === '失败') {
                // 添加X图标
                branchDot.innerHTML = '<i class="fas fa-times"></i>';
            } else if (branch.value === '搁置') {
                // 添加感叹号图标
                branchDot.innerHTML = '<i class="fas fa-exclamation"></i>';
            }
            if (this.currentStage === branch.value) {
                if (branch.value === '失败') {
                    branchDot.style.backgroundColor = '#e74c3c';
                    branchDot.style.borderColor = '#e74c3c';
                } else if (branch.value === '搁置') {
                    branchDot.style.backgroundColor = '#555';
                    branchDot.style.borderColor = '#555';
                }
            }
            // 只有canEdit为true时才允许点击
            if (this.canEdit) {
                branchDot.style.cursor = 'pointer';
                branchDot.addEventListener('click', (e) => {
                    e.stopPropagation();
                    let msg = this.currentStage === branch.value
                        ? `确定要恢复到主线阶段吗？`
                        : `确定要将项目阶段切换为"${branch.value}"吗？`;
                    if (window.confirm(msg)) {
                        // 统一通过API切换，无论是分支还是恢复主线
                        let targetStage = (this.currentStage === branch.value) ? this.lastMainStage : branch.value;
                        this.updateStage(targetStage);
                    }
                });
            } else {
                branchDot.classList.add('dot-disabled');
                branchDot.style.cursor = 'not-allowed';
            }
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
     * 通用阶段切换方法，调用后端API
     */
    updateStage(targetStage) {
        // 显示加载指示器
        const loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'stageUpdateLoadingOverlay';
        loadingOverlay.style.position = 'fixed';
        loadingOverlay.style.top = '0';
        loadingOverlay.style.left = '0';
        loadingOverlay.style.width = '100%';
        loadingOverlay.style.height = '100%';
        loadingOverlay.style.backgroundColor = 'rgba(0,0,0,0.3)';
        loadingOverlay.style.zIndex = '9999';
        loadingOverlay.style.display = 'flex';
        loadingOverlay.style.alignItems = 'center';
        loadingOverlay.style.justifyContent = 'center';
        const loadingIndicator = document.createElement('div');
        loadingIndicator.style.backgroundColor = 'white';
        loadingIndicator.style.padding = '20px';
        loadingIndicator.style.borderRadius = '5px';
        loadingIndicator.style.boxShadow = '0 0 10px rgba(0,0,0,0.2)';
        loadingIndicator.innerHTML = '<div>阶段更新中，请稍候...</div>';
        loadingOverlay.appendChild(loadingIndicator);
        document.body.appendChild(loadingOverlay);
        
        // 发送请求到服务器更新阶段
        fetch(this.updateUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken,
                'Cache-Control': 'no-cache, no-store'
            },
            body: JSON.stringify({
                project_id: this.projectId,
                current_stage: targetStage
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`网络请求失败: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log('项目阶段已成功更新为: ' + targetStage);
                
                // 强制完全刷新页面（不使用缓存）
                // 使用 location.reload(true) 强制浏览器不使用缓存
                // 并添加时间戳参数确保是全新请求
                window.location.href = window.location.href.split('?')[0] + 
                    '?_nocache=' + new Date().getTime();
            } else {
                const errorMsg = data.message || '未知错误';
                console.error('更新阶段失败: ' + errorMsg);
                alert('更新阶段失败: ' + errorMsg);
                // 移除加载指示器
                document.body.removeChild(loadingOverlay);
            }
        })
        .catch(error => {
            console.error('更新阶段错误:', error);
            alert('更新阶段时发生错误: ' + error.message);
            // 移除加载指示器
            document.body.removeChild(loadingOverlay);
        });
    }

    /**
     * 推进到下一阶段
     */
    advanceStage() {
        const nextStage = this.getNextStage();
        if (!nextStage) return;
        this.updateStage(nextStage.value);
    }

    /**
     * 获取分支前的主线阶段
     * 如果当前为分支阶段，则返回分支前的主线阶段，否则返回当前主线阶段
     */
    getLastMainStageBeforeBranch() {
        // 如果没有历史，默认返回"发现"
        if (!this.stageHistory || !Array.isArray(this.stageHistory) || this.stageHistory.length === 0) {
            return this.mainStages[0].value;
        }
        // 倒序查找最后一个主线阶段
        for (let i = this.stageHistory.length - 1; i >= 0; i--) {
            const s = this.stageHistory[i];
            if (this.mainStages.some(m => m.value === s.stage)) {
                return s.stage;
            }
        }
        // 找不到则返回"发现"
        return this.mainStages[0].value;
    }
}

// 文档加载完成后运行
document.addEventListener('DOMContentLoaded', function() {
    // 页面加载时自动移除残留的阶段推进loading遮罩层
    const removeStageLoading = () => {
        const oldLoading = document.getElementById('stageUpdateLoadingOverlay');
        if (oldLoading) {
            oldLoading.parentNode.removeChild(oldLoading);
        }
    };
    removeStageLoading();
    // 监听页面跳转和刷新，自动移除loading遮罩层
    window.addEventListener('popstate', removeStageLoading);
    window.addEventListener('hashchange', removeStageLoading);
    window.addEventListener('beforeunload', removeStageLoading);
    // 项目阶段进度条初始化由页面调用
}); 