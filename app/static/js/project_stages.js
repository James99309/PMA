/**
 * 项目阶段可视化进度条组件
 */

/**
 * 阻塞进度推进错误类
 */
class BlockedProgressError extends Error {
    constructor(data) {
        super(data.message || '阶段推进被阻止');
        this.name = 'BlockedProgressError';
        this.data = data;
    }
}

class ProjectStageProgress {
    constructor(options) {
        this.containerId = options.containerId;
        this.projectId = options.projectId;
        this.currentStage = options.currentStage;
        this.csrfToken = options.csrfToken;
        this.updateUrl = options.updateUrl;
        this.stageHistory = options.stageHistory || null;
        this.canEdit = options.canEdit || false;
        this.isLocked = options.isLocked || false;
        this.userRole = options.userRole || '';

        // 项目阶段定义（由后端传递标准结构，避免硬编码）
        if (options && options.stageDefs) {
            // 后端传递的标准结构，支持key和label
            this.mainStages = options.stageDefs.mainStages;
            this.branchStages = options.stageDefs.branchStages;
        } else {
            // 兼容旧写法，手动插入批价阶段
        this.mainStages = [
                { id: 0, key: 'discover', name: '发现' },
                { id: 1, key: 'embed', name: '植入' },
                { id: 2, key: 'pre_tender', name: '招标前' },
                { id: 3, key: 'tendering', name: '招标中' },
                { id: 4, key: 'awarded', name: '中标' },
                { id: 5, key: 'quoted', name: '批价' },
                { id: 6, key: 'signed', name: '签约' }
        ];
        this.branchStages = [
                { id: 7, key: 'lost', name: '失败' },
                { id: 8, key: 'paused', name: '搁置' }
        ];
        }
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
        const stageIndex = this.stages.findIndex(stage => stage.key === stageName);
        return stageIndex >= 0 ? stageIndex : 0;
    }

    /**
     * 获取下一个阶段
     */
    getNextStage() {
        // 如果当前是失败阶段，无下一阶段
        if (this.currentStage === 'lost') {
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
                // 对于当前阶段，确保天数计算是从推进日到今天
                const endDate = stage.endDate || new Date();
                return {
                    stageName: stage.stage,
                    days: this.calculateDaysBetween(stage.startDate, endDate)
                };
            });
        } else {
            // 无历史记录，所有阶段天数显示为"未知"
            this.stageDurations = this.stages.map(stage => {
                return {
                    stageName: stage.key,
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
        console.log('ProjectStageProgress 渲染开始:');
        console.log('- 当前阶段:', this.currentStage);
        console.log('- 主线阶段:', this.mainStages);
        console.log('- 分支阶段:', this.branchStages);
        
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error('找不到容器元素:', this.containerId);
            return;
        }

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
            stageMarker.dataset.stage = stage.key;

            // 状态样式
            if (this.currentStage === 'lost' || this.currentStage === 'paused') {
                stageMarker.classList.add('stage-disabled');
            } else if (index < this.getStageIndex(this.currentStage)) {
                stageMarker.classList.add('stage-completed');
            } else if (index === this.getStageIndex(this.currentStage)) {
                stageMarker.classList.add('stage-current');
            } else if (index === this.getStageIndex(this.currentStage) + 1 && this.canEdit && (!this.isLocked || this.userRole === 'admin')) {
                // 下一个阶段可点击 (考虑锁定状态，管理员可跳过锁定检查)
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
                // 推进信息 - 对于当前阶段，显示推进到这个阶段的日期和从推进日到今天的天数
                const durationItem = this.stageDurations.find(item => item.stageName === stage.key);
                const days = durationItem ? durationItem.days : '未知';
                let stageExtra = '';
                if (this.stageHistory && Array.isArray(this.stageHistory)) {
                    const historyItem = this.stageHistory.find(item => item.stage === stage.key);
                    if (historyItem && historyItem.startDate) {
                        // 显示推进到这个阶段的日期
                        const stageDate = historyItem.startDate.split(' ')[0];
                        if (typeof days === 'number' && days > 0) {
                            // 显示推进日期和从推进日到今天的天数
                            stageExtra = `${stageDate}｜${days}天`;
                        } else {
                            // 只显示推进日期
                            stageExtra = stageDate;
                        }
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
                    this.updateStage(stage.key);
                });
                progressBar.appendChild(stageMarker);
                return;
            }

            // 圆点
            const stageDot = document.createElement('div');
            stageDot.className = 'stage-dot';
            if (this.currentStage === 'lost' || this.currentStage === 'paused') {
                stageDot.classList.add('dot-disabled');
            }
            if (index < this.getStageIndex(this.currentStage) && this.currentStage !== 'lost' && this.currentStage !== 'paused') {
                const icon = document.createElement('i');
                icon.className = 'fas fa-check';
                stageDot.appendChild(icon);
            } else if (index === this.getStageIndex(this.currentStage) && this.currentStage !== 'lost' && this.currentStage !== 'paused') {
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

            // 推进信息 - 显示推进到这个阶段的日期和从推进日到今天的天数
            const durationItem = this.stageDurations.find(item => item.stageName === stage.key);
            const days = durationItem ? durationItem.days : '未知';
            let stageExtra = '';
            if (this.stageHistory && Array.isArray(this.stageHistory)) {
                const historyItem = this.stageHistory.find(item => item.stage === stage.key);
                if (historyItem && historyItem.startDate) {
                    // 显示推进到这个阶段的日期
                    const stageDate = historyItem.startDate.split(' ')[0];
                    if (typeof days === 'number' && days > 0) {
                        // 显示推进日期和从推进日到今天的天数
                        stageExtra = `${stageDate}｜${days}天`;
                    } else {
                        // 只显示推进日期
                        stageExtra = stageDate;
                    }
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
            branchMarker.dataset.stage = branch.key;

            // 状态样式
            if (this.currentStage === branch.key) {
                branchMarker.classList.add('stage-current');
                if (branch.key === 'lost') {
                    branchMarker.classList.add('stage-failed');
                } else if (branch.key === 'paused') {
                    branchMarker.classList.add('stage-pending');
                }
            }

            // 圆点
            const branchDot = document.createElement('div');
            branchDot.className = 'stage-dot';
            if (branch.key === 'lost') {
                // 添加X图标
                branchDot.innerHTML = '<i class="fas fa-times"></i>';
            } else if (branch.key === 'paused') {
                // 添加感叹号图标
                branchDot.innerHTML = '<i class="fas fa-exclamation"></i>';
            }
            if (this.currentStage === branch.key) {
                if (branch.key === 'lost') {
                    branchDot.style.backgroundColor = '#e74c3c';
                    branchDot.style.borderColor = '#e74c3c';
                } else if (branch.key === 'paused') {
                    branchDot.style.backgroundColor = '#555';
                    branchDot.style.borderColor = '#555';
                }
            }
            // 只有canEdit为true时才允许点击
            if (this.canEdit) {
                branchDot.style.cursor = 'pointer';
                branchDot.addEventListener('click', (e) => {
                    e.stopPropagation();
                    let msg = this.currentStage === branch.key
                        ? `确定要恢复到主线阶段吗？`
                        : `确定要将项目阶段切换为"${branch.key}"吗？`;
                    if (window.confirm(msg)) {
                        // 统一通过API切换，无论是分支还是恢复主线
                        let targetStage = (this.currentStage === branch.key) ? this.lastMainStage : branch.key;
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

            // 推进信息 - 显示推进到这个阶段的日期和从推进日到今天的天数
            const durationItem = this.stageDurations.find(item => item.stageName === branch.key);
            const days = durationItem ? durationItem.days : '未知';
            let stageExtra = '';
            if (this.stageHistory && Array.isArray(this.stageHistory)) {
                const historyItem = this.stageHistory.find(item => item.stage === branch.key);
                if (historyItem && historyItem.startDate) {
                    // 显示推进到这个阶段的日期
                    const stageDate = historyItem.startDate.split(' ')[0];
                    if (typeof days === 'number' && days > 0) {
                        // 显示推进日期和从推进日到今天的天数
                        stageExtra = `${stageDate}｜${days}天`;
                    } else {
                        // 只显示推进日期
                        stageExtra = stageDate;
                    }
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
            if (response.ok) {
                return response.json();
            } else if (response.status === 400) {
                // 处理阻塞响应（批价流程检查失败）
                return response.json().then(data => {
                    throw new BlockedProgressError(data);
                });
            } else {
                throw new Error(`网络请求失败: ${response.status} ${response.statusText}`);
            }
        })
        .then(data => {
            if (data.success) {
                console.log('项目阶段已成功更新为: ' + targetStage);
                
                // 移除加载指示器
                document.body.removeChild(loadingOverlay);
                
                // **新增: 处理批价流程信息**
                if (data.pricing_flow) {
                    this.handlePricingFlowPrompt(data.pricing_flow);
                } else {
                    // 没有批价流程信息，直接刷新页面
                    this.refreshPage();
                }
            } else {
                const errorMsg = data.message || '未知错误';
                console.error('更新阶段失败: ' + errorMsg);
                alert('更新阶段失败: ' + errorMsg);
                // 移除加载指示器
                document.body.removeChild(loadingOverlay);
            }
        })
        .catch(error => {
            // 移除加载指示器
            document.body.removeChild(loadingOverlay);
            
            if (error instanceof BlockedProgressError) {
                // 处理阻塞的进度推进（批价流程检查失败）
                console.log('阶段推进被阻止:', error.data.message);
                
                if (error.data.pricing_flow) {
                    // 显示批价流程相关的提示
                    this.handlePricingFlowPrompt(error.data.pricing_flow);
                } else {
                    // 显示一般性的阻塞信息
                    alert(error.data.message || '阶段推进被阻止');
                }
            } else {
                console.error('更新阶段错误:', error);
                alert('更新阶段时发生错误: ' + error.message);
            }
        });
    }
    
    /**
     * 处理批价流程提示
     */
    handlePricingFlowPrompt(pricingFlow) {
        const modalId = 'pricingFlowModal';
        let modalHtml = '';
        
        if (pricingFlow.action_required === 'create_pricing_order') {
            // 需要创建批价单
            modalHtml = `
                <div class="modal fade" id="${modalId}" tabindex="-1" aria-labelledby="pricingFlowModalLabel" aria-hidden="true">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header bg-success text-white">
                                <h5 class="modal-title" id="pricingFlowModalLabel">
                                    <i class="fas fa-file-invoice-dollar me-2"></i>签约流程 - 批价单创建
                                </h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="alert alert-success mb-3">
                                    <i class="fas fa-check-circle me-2"></i>
                                    项目已成功推进到签约阶段！
                                </div>
                                
                                <div class="d-flex align-items-start mb-3">
                                    <i class="fas fa-file-alt text-success me-3 mt-1" style="font-size: 1.2em;"></i>
                                    <div>
                                        <h6 class="mb-1">发现已审核报价单</h6>
                                        <p class="mb-0 text-muted">报价单号：<strong>${pricingFlow.quotation_number}</strong></p>
                                        <p class="mb-0 text-success"><i class="fas fa-check me-1"></i>审核状态：已通过审核</p>
                                    </div>
                                </div>
                                
                                <div class="alert alert-info mb-3">
                                    <i class="fas fa-info-circle me-2"></i>
                                    ${pricingFlow.message}
                                </div>
                                
                                <p class="mb-0">您可以选择以下操作：</p>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                    <i class="fas fa-times me-1"></i>稍后处理
                                </button>
                                <button type="button" class="btn btn-success" id="createPricingOrderBtn">
                                    <i class="fas fa-plus me-1"></i>创建批价单
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else if (pricingFlow.action_required === 'view_pricing_order') {
            // 已存在批价单
            modalHtml = `
                <div class="modal fade" id="${modalId}" tabindex="-1" aria-labelledby="pricingFlowModalLabel" aria-hidden="true">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header bg-success text-white">
                                <h5 class="modal-title" id="pricingFlowModalLabel">
                                    <i class="fas fa-check-circle me-2"></i>签约流程 - 批价单状态
                                </h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="alert alert-success mb-3">
                                    <i class="fas fa-check-circle me-2"></i>
                                    项目已成功推进到签约阶段！
                                </div>
                                
                                <div class="d-flex align-items-start mb-3">
                                    <i class="fas fa-file-invoice-dollar text-primary me-3 mt-1" style="font-size: 1.2em;"></i>
                                    <div>
                                        <h6 class="mb-1">已存在批价单</h6>
                                        <p class="mb-1 text-muted">
                                            批价单号：<strong>${pricingFlow.pricing_order_number}</strong>
                                        </p>
                                        <p class="mb-0 text-muted">
                                            状态：<span class="badge bg-info">${this.getPricingOrderStatusLabel(pricingFlow.pricing_order_status)}</span>
                                        </p>
                                    </div>
                                </div>
                                
                                <div class="alert alert-info mb-3">
                                    <i class="fas fa-info-circle me-2"></i>
                                    ${pricingFlow.message}
                                </div>
                                
                                <p class="mb-0">您可以选择以下操作：</p>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                    <i class="fas fa-times me-1"></i>关闭
                                </button>
                                <button type="button" class="btn btn-primary" id="viewPricingOrderBtn">
                                    <i class="fas fa-eye me-1"></i>查看批价单
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else if (pricingFlow.action_required === 'complete_quotation_approval') {
            // 需要完成报价单审核
            modalHtml = `
                <div class="modal fade" id="${modalId}" tabindex="-1" aria-labelledby="pricingFlowModalLabel" aria-hidden="true">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header bg-warning text-dark">
                                <h5 class="modal-title" id="pricingFlowModalLabel">
                                    <i class="fas fa-exclamation-triangle me-2"></i>签约流程 - 审核缺失
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="alert alert-warning mb-3">
                                    <i class="fas fa-exclamation-triangle me-2"></i>
                                    无法推进到签约阶段！
                                </div>
                                
                                <div class="d-flex align-items-start mb-3">
                                    <i class="fas fa-file-alt text-warning me-3 mt-1" style="font-size: 1.2em;"></i>
                                    <div>
                                        <h6 class="mb-1">发现报价单但缺少审核</h6>
                                        <p class="mb-0 text-muted">报价单号：<strong>${pricingFlow.quotation_number}</strong></p>
                                        <p class="mb-0 text-warning"><i class="fas fa-times me-1"></i>审核状态：未审核或审核未通过</p>
                                    </div>
                                </div>
                                
                                <div class="alert alert-danger mb-3">
                                    <i class="fas fa-times-circle me-2"></i>
                                    ${pricingFlow.message}
                                </div>
                                
                                <p class="mb-0">请先完成以下操作再重新推进：</p>
                                <ul class="mt-2">
                                    <li>确保报价单内容完整</li>
                                    <li>提交报价单审批流程</li>
                                    <li>等待审批通过</li>
                                    <li>然后再推进到签约阶段</li>
                                </ul>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                    <i class="fas fa-times me-1"></i>知道了
                                </button>
                                <button type="button" class="btn btn-warning" id="viewQuotationBtn">
                                    <i class="fas fa-eye me-1"></i>查看报价单
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else if (pricingFlow.action_required === 'create_quotation') {
            // 需要创建报价单
            modalHtml = `
                <div class="modal fade" id="${modalId}" tabindex="-1" aria-labelledby="pricingFlowModalLabel" aria-hidden="true">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header bg-danger text-white">
                                <h5 class="modal-title" id="pricingFlowModalLabel">
                                    <i class="fas fa-exclamation-triangle me-2"></i>签约流程 - 报价单缺失
                                </h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="alert alert-danger mb-3">
                                    <i class="fas fa-times-circle me-2"></i>
                                    无法推进到签约阶段！
                                </div>
                                
                                <div class="alert alert-warning mb-3">
                                    <i class="fas fa-exclamation-triangle me-2"></i>
                                    ${pricingFlow.message}
                                </div>
                                
                                <p class="mb-0">建议您先完成以下操作：</p>
                                <ul class="mt-2">
                                    <li>为项目创建报价单</li>
                                    <li>完善报价单产品明细</li>
                                    <li>完成报价单审批流程</li>
                                    <li>然后再发起签约流程</li>
                                </ul>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                    <i class="fas fa-times me-1"></i>知道了
                                </button>
                                <button type="button" class="btn btn-danger" id="createQuotationBtn">
                                    <i class="fas fa-plus me-1"></i>创建报价单
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // 移除已存在的模态框
        const existingModal = document.getElementById(modalId);
        if (existingModal) {
            existingModal.remove();
        }
        
        // 添加新模态框到DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById(modalId));
        modal.show();
        
        // 绑定按钮事件
        this.bindPricingFlowModalEvents(pricingFlow, modal);
    }
    
    /**
     * 绑定批价流程模态框按钮事件
     */
    bindPricingFlowModalEvents(pricingFlow, modal) {
        const createPricingOrderBtn = document.getElementById('createPricingOrderBtn');
        const viewPricingOrderBtn = document.getElementById('viewPricingOrderBtn');
        const createQuotationBtn = document.getElementById('createQuotationBtn');
        const viewQuotationBtn = document.getElementById('viewQuotationBtn');
        
        if (createPricingOrderBtn) {
            createPricingOrderBtn.addEventListener('click', () => {
                modal.hide();
                // 发起创建批价单流程
                this.createPricingOrder(pricingFlow.quotation_id);
            });
        }
        
        if (viewPricingOrderBtn) {
            viewPricingOrderBtn.addEventListener('click', () => {
                modal.hide();
                // 跳转到批价单详情页面
                window.location.href = `/pricing_order/${pricingFlow.pricing_order_id}`;
            });
        }
        
        if (createQuotationBtn) {
            createQuotationBtn.addEventListener('click', () => {
                modal.hide();
                // 跳转到创建报价单页面
                window.open(`/quotation/add?project_id=${this.projectId}`, '_blank');
                this.refreshPage();
            });
        }
        
        if (viewQuotationBtn) {
            viewQuotationBtn.addEventListener('click', () => {
                modal.hide();
                // 跳转到报价单详情页面
                window.open(`/quotation/${pricingFlow.quotation_id}/detail`, '_blank');
                this.refreshPage();
            });
        }
        
        // 模态框关闭后刷新页面
        modal._element.addEventListener('hidden.bs.modal', () => {
            this.refreshPage();
        });
    }
    
    /**
     * 创建批价单
     */
    createPricingOrder(quotationId) {
        // 显示加载指示器
        const loadingHtml = `
            <div id="createPricingOrderLoading" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                 background-color: rgba(0,0,0,0.5); z-index: 10000; display: flex; align-items: center; justify-content: center;">
                <div style="background: white; padding: 20px; border-radius: 8px; text-align: center;">
                    <div class="spinner-border text-primary mb-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <div>正在创建批价单...</div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', loadingHtml);
        
        // 调用创建批价单API
        fetch(`/pricing_order/project/${this.projectId}/start_pricing_process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            },
            body: JSON.stringify({
                quotation_id: quotationId
            })
        })
        .then(response => response.json())
        .then(data => {
            // 移除加载指示器
            const loading = document.getElementById('createPricingOrderLoading');
            if (loading) loading.remove();
            
            if (data.success) {
                // 成功创建，直接跳转到批价单编辑页面
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    // 如果没有返回redirect_url，刷新页面
                    this.refreshPage();
                }
            } else {
                alert('创建批价单失败：' + (data.message || '未知错误'));
                this.refreshPage();
            }
        })
        .catch(error => {
            // 移除加载指示器
            const loading = document.getElementById('createPricingOrderLoading');
            if (loading) loading.remove();
            
            console.error('创建批价单错误:', error);
            alert('创建批价单时发生错误：' + error.message);
            this.refreshPage();
        });
    }
    
    /**
     * 获取批价单状态标签
     */
    getPricingOrderStatusLabel(status) {
        const statusLabels = {
            'draft': '草稿',
            'pending': '审批中',
            'approved': '已批准',
            'rejected': '已拒绝'
        };
        return statusLabels[status] || status;
    }
    
    /**
     * 刷新页面
     */
    refreshPage() {
        // 强制完全刷新页面（不使用缓存）
        window.location.href = window.location.href.split('?')[0] + 
            '?_nocache=' + new Date().getTime();
    }

    /**
     * 推进到下一阶段
     */
    advanceStage() {
        const nextStage = this.getNextStage();
        if (!nextStage) return;
        this.updateStage(nextStage.key);
    }

    /**
     * 获取分支前的主线阶段
     * 如果当前为分支阶段，则返回分支前的主线阶段，否则返回当前主线阶段
     */
    getLastMainStageBeforeBranch() {
        // 如果没有历史，默认返回"发现"
        if (!this.stageHistory || !Array.isArray(this.stageHistory) || this.stageHistory.length === 0) {
            return this.mainStages[0].key;
        }
        // 倒序查找最后一个主线阶段
        for (let i = this.stageHistory.length - 1; i >= 0; i--) {
            const s = this.stageHistory[i];
            if (this.mainStages.some(m => m.key === s.stage)) {
                return s.stage;
            }
        }
        // 找不到则返回"发现"
        return this.mainStages[0].key;
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