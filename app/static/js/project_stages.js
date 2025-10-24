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
        
        if (stageIndex < 0) {
            // 如果通过key找不到，尝试通过中文名称找
            const stageIndexByName = this.stages.findIndex(stage => stage.zh_name === stageName || stage.name === stageName);
            return stageIndexByName >= 0 ? stageIndexByName : 0;
        }
        
        return stageIndex;
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
                const duration = {
                    stageName: stage.stage,
                    days: this.calculateDaysBetween(stage.startDate, endDate)
                };
                return duration;
            });
        } else {
            // 无历史记录，所有阶段天数显示为"未知"
            this.stageDurations = this.stages.map(stage => {
                return {
                    stageName: stage.key,
                    days: window.stageI18nTexts?.unknown || '未知'
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
        return Math.floor(Math.random() * 20) + 5; // 5-25 days
    }

    /**
     * 渲染进度条
     */
    render() {
        
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
                const durationItem = this.stageDurations.find(item => 
                    item.stageName === stage.key || 
                    item.stageName === stage.name || 
                    item.stageName === stage.zh_name
                );
                const days = durationItem ? durationItem.days : '未知';
                let stageExtra = '';
                if (this.stageHistory && Array.isArray(this.stageHistory)) {
                    const historyItem = this.stageHistory.find(item => 
                        item.stage === stage.key || 
                        item.stage === stage.name || 
                        item.stage === stage.zh_name
                    );
                    if (historyItem && historyItem.startDate) {
                        // 显示推进到这个阶段的日期
                        const stageDate = historyItem.startDate.split(' ')[0];
                        if (typeof days === 'number' && days > 0) {
                            // 显示推进日期和从推进日到今天的天数
                            stageExtra = `${stageDate}｜${days}${window.stageI18nTexts?.days || '天'}`;
                        } else {
                            // 只显示推进日期
                            stageExtra = stageDate;
                        }
                    } else if (typeof days === 'number' && days > 0) {
                        stageExtra = `${days}${window.stageI18nTexts?.days || '天'}`;
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
                // 点击推进 - 显示确认对话框
                stageMarker.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.showStageProgressConfirmation(stage);
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
            const durationItem = this.stageDurations.find(item => 
                item.stageName === stage.key || 
                item.stageName === stage.name || 
                item.stageName === stage.zh_name
            );
            const days = durationItem ? durationItem.days : '未知';
            let stageExtra = '';
            if (this.stageHistory && Array.isArray(this.stageHistory)) {
                const historyItem = this.stageHistory.find(item => 
                    item.stage === stage.key || 
                    item.stage === stage.name || 
                    item.stage === stage.zh_name
                );
                if (historyItem && historyItem.startDate) {
                    // 显示推进到这个阶段的日期
                    const stageDate = historyItem.startDate.split(' ')[0];
                    if (typeof days === 'number' && days > 0) {
                        // 显示推进日期和从推进日到今天的天数
                        stageExtra = `${stageDate}｜${days}${window.stageI18nTexts?.days || '天'}`;
                    } else {
                        // 只显示推进日期
                        stageExtra = stageDate;
                    }
                } else if (typeof days === 'number' && days > 0) {
                    stageExtra = `${days}${window.stageI18nTexts?.days || '天'}`;
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
                    // 显示分支阶段确认对话框
                    let targetStage = (this.currentStage === branch.key) ? this.lastMainStage : branch.key;
                    let isRestore = (this.currentStage === branch.key);
                    this.showBranchStageConfirmation(branch, targetStage, isRestore);
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
            const durationItem = this.stageDurations.find(item => 
                item.stageName === branch.key || 
                item.stageName === branch.name || 
                item.stageName === branch.zh_name
            );
            const days = durationItem ? durationItem.days : '未知';
            let stageExtra = '';
            if (this.stageHistory && Array.isArray(this.stageHistory)) {
                const historyItem = this.stageHistory.find(item => 
                    item.stage === branch.key || 
                    item.stage === branch.name || 
                    item.stage === branch.zh_name
                );
                if (historyItem && historyItem.startDate) {
                    // 显示推进到这个阶段的日期
                    const stageDate = historyItem.startDate.split(' ')[0];
                    if (typeof days === 'number' && days > 0) {
                        // 显示推进日期和从推进日到今天的天数
                        stageExtra = `${stageDate}｜${days}${window.stageI18nTexts?.days || '天'}`;
                    } else {
                        // 只显示推进日期
                        stageExtra = stageDate;
                    }
                } else if (typeof days === 'number' && days > 0) {
                    stageExtra = `${days}${window.stageI18nTexts?.days || '天'}`;
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

        // 确认推进对话框已集成到点击事件中
    }


    /**
     * 绑定事件
     */
    bindEvents() {
        // 事件绑定已在 render 方法中完成
        // 所有的点击事件都直接绑定到对应的元素上
    }

    /**
     * 显示阶段推进确认对话框
     */
    showStageProgressConfirmation(nextStage) {
        const currentStageName = this.getStageDisplayName(this.currentStage);
        const nextStageName = nextStage.name;
        
        // 特殊处理：批价到签约阶段
        if (this.currentStage === 'quoted' && nextStage.key === 'signed') {
            // 批价到签约需要检查批价流程，但不需要用户确认
            // 直接调用updateStage，让后端处理批价流程检测
            this.updateStage(nextStage.key);
            return;
        }

        // 其他阶段推进需要确认
        this.showConfirmDialog({
            title: '确认阶段推进',
            message: `您确定要将项目从「${currentStageName}」阶段推进到「${nextStageName}」阶段吗？`,
            detail: '此操作将更新项目的当前阶段状态，推进后将无法直接回退。',
            confirmText: '确认推进',
            cancelText: '取消',
            type: 'warning',
            icon: 'fas fa-arrow-right',
            onConfirm: () => {
                this.updateStage(nextStage.key);
            }
        });
    }

    /**
     * 显示分支阶段确认对话框
     */
    showBranchStageConfirmation(branch, targetStage, isRestore) {
        let title, message, detail, confirmText;
        
        if (isRestore) {
            const lastMainStageName = this.getStageDisplayName(this.lastMainStage);
            title = '确认恢复到主线';
            message = `您确定要将项目从「${branch.name}」状态恢复到主线「${lastMainStageName}」阶段吗？`;
            detail = '项目将重新进入正常的阶段流程中。';
            confirmText = '确认恢复';
        } else {
            const currentStageName = this.getStageDisplayName(this.currentStage);
            title = '确认切换到分支状态';
            message = `您确定要将项目从「${currentStageName}」阶段切换为「${branch.name}」状态吗？`;
            detail = branch.key === 'lost' ? '项目将被标记为失败状态。' : '项目将被暂时搁置。';
            confirmText = '确认切换';
        }

        this.showConfirmDialog({
            title: title,
            message: message,
            detail: detail,
            confirmText: confirmText,
            cancelText: '取消',
            type: branch.key === 'lost' ? 'danger' : 'warning',
            icon: branch.key === 'lost' ? 'fas fa-times-circle' : 'fas fa-pause-circle',
            onConfirm: () => {
                this.updateStage(targetStage);
            }
        });
    }

    /**
     * 通用确认对话框显示方法 - 使用项目标准确认对话框组件
     */
    showConfirmDialog(options) {
        // 使用项目的标准确认对话框组件
        this.showStandardConfirmDialog({
            title: options.title,
            message: options.message,
            type: options.type || 'warning',
            confirmText: options.confirmText || '确认',
            cancelText: options.cancelText || '取消',
            dialogId: 'stageProgressConfirmDialog',
            onConfirm: options.onConfirm
        });
    }

    /**
     * 显示标准确认对话框
     * 根据 CLAUDE-COMPONENTS.md 中的规范实现
     */
    showStandardConfirmDialog(options) {
        const dialog = document.getElementById(options.dialogId);
        if (!dialog) {
            console.error('找不到确认对话框容器:', options.dialogId);
            return;
        }

        // 设置对话框内容
        const titleElement = dialog.querySelector('.message-title');
        const textElement = dialog.querySelector('.message-text');
        const iconElement = dialog.querySelector('.dialog-icon');
        const confirmBtn = dialog.querySelector('.dialog-confirm-btn');
        const cancelBtn = dialog.querySelector('.dialog-cancel-btn');

        if (titleElement) titleElement.textContent = options.title;
        if (textElement) textElement.innerHTML = options.message.replace(/\n/g, '<br>');
        
        // 设置图标
        if (iconElement) {
            iconElement.className = 'dialog-icon ' + this.getIconClassByType(options.type);
        }

        // 设置确认按钮文本和样式
        if (confirmBtn) {
            confirmBtn.textContent = options.confirmText;
            // 重置按钮样式
            confirmBtn.className = confirmBtn.className.replace(/btn-\w+/g, '');
            confirmBtn.classList.add('btn', 'btn-' + this.getButtonColorByType(options.type), 'dialog-confirm-btn');
        }

        // 设置取消按钮文本
        if (cancelBtn) {
            cancelBtn.textContent = options.cancelText;
        }

        // 绑定事件
        const confirmHandler = () => {
            this.hideConfirmDialog(options.dialogId);
            if (options.onConfirm) {
                options.onConfirm();
            }
        };

        const cancelHandler = () => {
            this.hideConfirmDialog(options.dialogId);
        };

        // 移除旧的事件监听器并添加新的
        if (confirmBtn) {
            confirmBtn.replaceWith(confirmBtn.cloneNode(true));
            const newConfirmBtn = dialog.querySelector('.dialog-confirm-btn');
            newConfirmBtn.addEventListener('click', confirmHandler);
        }

        if (cancelBtn) {
            cancelBtn.replaceWith(cancelBtn.cloneNode(true));
            const newCancelBtn = dialog.querySelector('.dialog-cancel-btn');
            newCancelBtn.addEventListener('click', cancelHandler);
        }

        // 绑定遮罩层点击事件
        const overlay = dialog.querySelector('.dialog-overlay');
        if (overlay) {
            overlay.replaceWith(overlay.cloneNode(true));
            const newOverlay = dialog.querySelector('.dialog-overlay');
            newOverlay.addEventListener('click', cancelHandler);
        }

        // 显示对话框
        this.showConfirmDialog_display(options.dialogId);
    }

    /**
     * 显示确认对话框
     */
    showConfirmDialog_display(dialogId) {
        const dialog = document.getElementById(dialogId);
        if (!dialog) return;

        dialog.style.display = 'flex';
        setTimeout(() => {
            dialog.classList.add('show');
        }, 10);

        // ESC键关闭
        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                this.hideConfirmDialog(dialogId);
                document.removeEventListener('keydown', handleEsc);
            }
        };
        document.addEventListener('keydown', handleEsc);
    }

    /**
     * 隐藏确认对话框
     */
    hideConfirmDialog(dialogId) {
        const dialog = document.getElementById(dialogId);
        if (!dialog) return;

        dialog.classList.remove('show');
        setTimeout(() => {
            dialog.style.display = 'none';
        }, 300);
    }

    /**
     * 根据类型获取图标类名
     */
    getIconClassByType(type) {
        const iconMap = {
            'danger': 'fas fa-exclamation-triangle',
            'warning': 'fas fa-exclamation-triangle', 
            'info': 'fas fa-info-circle',
            'success': 'fas fa-check-circle'
        };
        return iconMap[type] || 'fas fa-exclamation-triangle';
    }

    /**
     * 根据类型获取按钮颜色
     */
    getButtonColorByType(type) {
        const colorMap = {
            'danger': 'danger',
            'warning': 'warning',
            'info': 'primary',
            'success': 'success'
        };
        return colorMap[type] || 'primary';
    }

    /**
     * 根据类型获取图标颜色
     */
    getIconColorByType(type) {
        const colorMap = {
            'danger': '#e74c3c',
            'warning': '#f39c12',
            'info': '#3498db',
            'success': '#28a745'
        };
        return colorMap[type] || '#f39c12';
    }

    /**
     * 获取阶段显示名称
     */
    getStageDisplayName(stageKey) {
        const stage = this.stages.find(s => s.key === stageKey);
        return stage ? stage.name : stageKey;
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
                
                // 安全移除加载指示器
                if (loadingOverlay && loadingOverlay.parentNode) {
                    document.body.removeChild(loadingOverlay);
                }
                
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
                // 安全移除加载指示器
                if (loadingOverlay && loadingOverlay.parentNode) {
                    document.body.removeChild(loadingOverlay);
                }
            }
        })
        .catch(error => {
            // 安全移除加载指示器
            if (loadingOverlay && loadingOverlay.parentNode) {
                document.body.removeChild(loadingOverlay);
            }
            
            if (error instanceof BlockedProgressError) {
                // 处理阻塞的进度推进（批价流程检查失败）
                console.log('处理阻塞的进度推进，错误数据:', error.data);
                
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
     * 处理批价流程提示 - 使用通用确认对话框优化版
     */
    handlePricingFlowPrompt(pricingFlow) {
        // 根据不同的操作要求，使用通用确认对话框
        if (pricingFlow.action_required === 'create_quotation') {
            this.showPricingFlowDialog({
                type: 'warning',
                title: '签约流程 - 报价单缺失',
                message: `${pricingFlow.message}\n\n建议您先创建报价单，完善产品明细并完成审批流程。`,
                confirmText: '创建报价单',
                cancelText: '稍后处理',
                onConfirm: () => {
                    window.open(`/quotation/create?project_id=${this.projectId}`, '_blank');
                    this.refreshPage();
                }
            });
        } else if (pricingFlow.action_required === 'complete_quotation_approval') {
            this.showPricingFlowDialog({
                type: 'warning',
                title: '签约流程 - 审核缺失',
                message: `${pricingFlow.message}\n\n请先完成报价单审核流程，然后重新推进到签约阶段。`,
                confirmText: '查看报价单',
                cancelText: '知道了',
                onConfirm: () => {
                    window.open(`/quotation/${pricingFlow.quotation_id}/detail`, '_blank');
                    this.refreshPage();
                }
            });
        } else if (pricingFlow.action_required === 'create_pricing_order') {
            // 🔥 已移除：不再弹出创建批价单的提示
            // 项目已成功推进到签约阶段，不做任何额外操作
            console.log('项目已推进到签约阶段，已禁用自动创建批价单流程');
        } else if (pricingFlow.action_required === 'view_pricing_order') {
            // 🔥 已移除：不再弹出批价单状态提示
            // 项目已成功推进到签约阶段，不做任何额外操作
            console.log('项目已推进到签约阶段，已禁用批价单状态提示');
        } else {
            // 降级到原有的复杂对话框实现
            this.handlePricingFlowPrompt_original(pricingFlow);
        }
    }

    /**
     * 显示批价流程对话框 - 使用通用组件
     */
    showPricingFlowDialog(options) {
        this.showConfirmDialog({
            title: options.title,
            message: options.message,
            type: options.type,
            confirmText: options.confirmText,
            cancelText: options.cancelText,
            onConfirm: options.onConfirm
        });
    }

    /**
     * 原有批价流程提示实现 - 作为降级选项保留
     */
    handlePricingFlowPrompt_original(pricingFlow) {
        const modalId = 'pricingFlowModal';
        let modalHtml = '';

        if (pricingFlow.action_required === 'create_pricing_order') {
            // 🔥 已移除：不再弹出创建批价单的提示
            console.log('项目已推进到签约阶段，已禁用自动创建批价单流程');
            return; // 直接返回，不显示任何弹窗
        } else if (pricingFlow.action_required === 'view_pricing_order') {
            // 🔥 已移除：不再弹出批价单状态提示
            console.log('项目已推进到签约阶段，已禁用批价单状态提示');
            return; // 直接返回，不显示任何弹窗
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
     * 推进到下一阶段 (已废弃，现在使用确认对话框)
     */
    advanceStage() {
        // 此方法已被 showStageProgressConfirmation 替代
        const nextStage = this.getNextStage();
        if (!nextStage) return;
        this.showStageProgressConfirmation(nextStage);
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