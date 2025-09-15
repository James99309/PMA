/**
 * 通用阶段跟踪可视化进度条组件
 * 从项目阶段跟踪功能提取的通用组件，支持多种对象类型的阶段管理
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

/**
 * 通用阶段跟踪器
 * 支持项目、研发产品等多种对象类型的阶段管理
 */
class StageTracker {
    constructor(options) {
        // 基本配置
        this.containerId = options.containerId;
        this.objectType = options.objectType;  // 'project', 'rd_product', etc.
        this.objectId = options.objectId;
        this.currentStage = options.currentStage;
        this.csrfToken = options.csrfToken;
        this.updateUrl = options.updateUrl;
        this.stageHistory = options.stageHistory || null;
        this.canEdit = options.canEdit || false;
        this.isLocked = options.isLocked || false;
        this.userRole = options.userRole || '';
        this.i18nTexts = options.i18nTexts || {};

        // 阶段定义（从配置传入）
        if (options && options.stageDefs) {
            this.mainStages = options.stageDefs.mainStages || [];
            this.branchStages = options.stageDefs.branchStages || [];
        } else {
            this.mainStages = [];
            this.branchStages = [];
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
        // 如果当前是分支阶段，无下一阶段
        if (this.branchStages.some(branch => branch.key === this.currentStage)) {
            return null;
        }
        
        // 如果当前是最后一个主线阶段，无下一阶段
        if (this.currentStageIndex >= this.mainStages.length - 1) {
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
                    days: this.i18nTexts?.unknown || '未知'
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
        this.renderMainStages(progressBar);

        // 渲染分支阶段（如果存在）
        if (this.branchStages.length > 0) {
            const branchContainer = this.renderBranchStages();
            progressContainer.appendChild(progressBar);
            progressContainer.appendChild(branchContainer);
        } else {
            progressContainer.appendChild(progressBar);
        }

        // 添加到容器
        container.innerHTML = '';
        container.appendChild(progressContainer);
    }

    /**
     * 渲染主线阶段
     */
    renderMainStages(progressBar) {
        this.mainStages.forEach((stage, index) => {
            const stageMarker = document.createElement('div');
            stageMarker.className = 'stage-marker';
            stageMarker.dataset.stage = stage.key;

            // 状态样式
            this.applyStageMarkerStyle(stageMarker, stage, index);

            // 创建阶段内容
            this.createStageContent(stageMarker, stage, index);

            progressBar.appendChild(stageMarker);
        });
    }

    /**
     * 渲染分支阶段
     */
    renderBranchStages() {
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
                } else if (branch.key === 'cancelled') {
                    branchMarker.classList.add('stage-failed'); // 已取消使用失败样式
                } else if (branch.key === 'suspended') {
                    branchMarker.classList.add('stage-pending'); // 暂停使用待处理样式
                }
            }

            // 创建分支阶段内容
            this.createBranchStageContent(branchMarker, branch);

            branchContainer.appendChild(branchMarker);
        });

        return branchContainer;
    }

    /**
     * 应用阶段标记样式
     */
    applyStageMarkerStyle(stageMarker, stage, index) {
        // 判断是否为分支阶段状态
        const isInBranchState = this.branchStages.some(branch => branch.key === this.currentStage);
        
        if (isInBranchState) {
            stageMarker.classList.add('stage-disabled');
        } else if (index < this.getStageIndex(this.currentStage)) {
            stageMarker.classList.add('stage-completed');
        } else if (index === this.getStageIndex(this.currentStage)) {
            stageMarker.classList.add('stage-current');
        } else if (index === this.getStageIndex(this.currentStage) + 1 && this.canEdit && (!this.isLocked || this.userRole === 'admin')) {
            // 下一个阶段可点击
            stageMarker.classList.add('stage-actionable');
            stageMarker.style.cursor = 'pointer';
            this.bindStageAdvanceEvent(stageMarker, stage);
        }
    }

    /**
     * 创建阶段内容（圆点、名称、推进信息）
     */
    createStageContent(stageMarker, stage, index) {
        // 判断是否为分支阶段状态
        const isInBranchState = this.branchStages.some(branch => branch.key === this.currentStage);
        
        // 圆点
        const stageDot = document.createElement('div');
        stageDot.className = 'stage-dot';
        
        if (isInBranchState) {
            stageDot.classList.add('dot-disabled');
        } else if (index < this.getStageIndex(this.currentStage)) {
            const icon = document.createElement('i');
            icon.className = 'fas fa-check';
            stageDot.appendChild(icon);
        } else if (index === this.getStageIndex(this.currentStage)) {
            const icon = document.createElement('i');
            icon.className = 'fas fa-circle';
            stageDot.appendChild(icon);
        } else if (index === this.getStageIndex(this.currentStage) + 1 && this.canEdit && (!this.isLocked || this.userRole === 'admin')) {
            const icon = document.createElement('i');
            icon.className = 'fas fa-arrow-right';
            stageDot.appendChild(icon);
        }
        
        stageMarker.appendChild(stageDot);

        // 名称
        const stageName = document.createElement('div');
        stageName.className = 'stage-name';
        stageName.textContent = stage.name;
        stageMarker.appendChild(stageName);

        // 推进信息
        this.createStageExtraInfo(stageMarker, stage);
    }

    /**
     * 创建分支阶段内容
     */
    createBranchStageContent(branchMarker, branch) {
        // 圆点
        const branchDot = document.createElement('div');
        branchDot.className = 'stage-dot';
        
        if (branch.key === 'lost') {
            branchDot.innerHTML = '<i class="fas fa-times"></i>';
        } else if (branch.key === 'paused') {
            branchDot.innerHTML = '<i class="fas fa-exclamation"></i>';
        } else if (branch.key === 'cancelled') {
            branchDot.innerHTML = '<i class="fas fa-ban"></i>';
        } else if (branch.key === 'suspended') {
            branchDot.innerHTML = '<i class="fas fa-pause"></i>';
        }
        
        if (this.currentStage === branch.key) {
            if (branch.key === 'lost') {
                branchDot.style.backgroundColor = '#e74c3c';
                branchDot.style.borderColor = '#e74c3c';
            } else if (branch.key === 'paused') {
                branchDot.style.backgroundColor = '#555';
                branchDot.style.borderColor = '#555';
            } else if (branch.key === 'cancelled') {
                branchDot.style.backgroundColor = '#e74c3c'; // 已取消使用红色
                branchDot.style.borderColor = '#e74c3c';
            } else if (branch.key === 'suspended') {
                branchDot.style.backgroundColor = '#ffc107'; // 暂停使用黄色
                branchDot.style.borderColor = '#ffc107';
            }
        }
        
        // 绑定分支阶段点击事件
        if (this.canEdit) {
            branchDot.style.cursor = 'pointer';
            this.bindBranchStageEvent(branchDot, branch);
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
        this.createStageExtraInfo(branchMarker, branch);
    }

    /**
     * 创建阶段额外信息（推进日期、持续天数）
     */
    createStageExtraInfo(stageMarker, stage) {
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
                const stageDate = historyItem.startDate.split(' ')[0];
                if (typeof days === 'number' && days > 0) {
                    stageExtra = `${stageDate}｜${days}${this.i18nTexts?.days || '天'}`;
                } else {
                    stageExtra = stageDate;
                }
            } else if (typeof days === 'number' && days > 0) {
                stageExtra = `${days}${this.i18nTexts?.days || '天'}`;
            }
        }
        
        if (stageExtra) {
            const stageInfo = document.createElement('div');
            stageInfo.className = 'stage-extra stage-days';
            stageInfo.textContent = stageExtra;
            stageMarker.appendChild(stageInfo);
        }
    }

    /**
     * 绑定阶段推进事件
     */
    bindStageAdvanceEvent(stageMarker, stage) {
        // 悬停效果
        stageMarker.addEventListener('mouseenter', () => {
            stageMarker.classList.add('stage-current');
        });
        stageMarker.addEventListener('mouseleave', () => {
            stageMarker.classList.remove('stage-current');
        });
        
        // 点击推进
        stageMarker.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.showStageProgressConfirmation(stage);
        });
    }

    /**
     * 绑定分支阶段事件
     */
    bindBranchStageEvent(branchDot, branch) {
        branchDot.addEventListener('click', (e) => {
            e.stopPropagation();
            let targetStage = (this.currentStage === branch.key) ? this.lastMainStage : branch.key;
            let isRestore = (this.currentStage === branch.key);
            this.showBranchStageConfirmation(branch, targetStage, isRestore);
        });
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 事件绑定已在 render 方法中完成
    }

    /**
     * 显示阶段推进确认对话框
     */
    showStageProgressConfirmation(nextStage) {
        const currentStageName = this.getStageDisplayName(this.currentStage);
        const nextStageName = nextStage.name;
        
        this.showConfirmDialog({
            title: this.i18nTexts?.confirmAdvanceTitle || '确认阶段推进',
            message: this.i18nTexts?.confirmAdvanceMessage?.replace('{current}', currentStageName).replace('{next}', nextStageName) || 
                     `您确定要将${this.getObjectTypeName()}从「${currentStageName}」阶段推进到「${nextStageName}」阶段吗？`,
            detail: this.i18nTexts?.operationNote || '此操作将更新当前阶段状态，推进后将无法直接回退。',
            confirmText: this.i18nTexts?.confirmAdvance || '确认推进',
            cancelText: this.i18nTexts?.cancel || '取消',
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
            title = this.i18nTexts?.confirmRestore || '确认恢复到主线';
            message = this.i18nTexts?.confirmRestoreMessage?.replace('{branch}', branch.name).replace('{main}', lastMainStageName) ||
                     `您确定要将${this.getObjectTypeName()}从「${branch.name}」状态恢复到主线「${lastMainStageName}」阶段吗？`;
            detail = this.i18nTexts?.restoreNote || '将重新进入正常的阶段流程中。';
            confirmText = this.i18nTexts?.confirmRestoreBtn || '确认恢复';
        } else {
            const currentStageName = this.getStageDisplayName(this.currentStage);
            title = this.i18nTexts?.confirmSwitchTitle || '确认切换到分支状态';
            message = this.i18nTexts?.confirmSwitchMessage?.replace('{current}', currentStageName).replace('{branch}', branch.name) ||
                     `您确定要将${this.getObjectTypeName()}从「${currentStageName}」阶段切换为「${branch.name}」状态吗？`;
            detail = branch.key === 'lost' ? (this.i18nTexts?.lostNote || '将被标记为失败状态。') : (this.i18nTexts?.pausedNote || '将被暂时搁置。');
            confirmText = this.i18nTexts?.confirmSwitch || '确认切换';
        }

        this.showConfirmDialog({
            title: title,
            message: message,
            detail: detail,
            confirmText: confirmText,
            cancelText: this.i18nTexts?.cancel || '取消',
            type: branch.key === 'lost' ? 'danger' : 'warning',
            icon: branch.key === 'lost' ? 'fas fa-times-circle' : 'fas fa-pause-circle',
            onConfirm: () => {
                this.updateStage(targetStage);
            }
        });
    }

    /**
     * 通用确认对话框显示方法
     */
    showConfirmDialog(options) {
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

        // 设置确认按钮
        if (confirmBtn) {
            confirmBtn.textContent = options.confirmText;
            confirmBtn.className = confirmBtn.className.replace(/btn-\w+/g, '');
            confirmBtn.classList.add('btn', 'btn-' + this.getButtonColorByType(options.type), 'dialog-confirm-btn');
        }

        // 设置取消按钮
        if (cancelBtn) {
            cancelBtn.textContent = options.cancelText;
        }

        // 绑定事件
        this.bindDialogEvents(dialog, options);

        // 显示对话框
        this.showDialog(options.dialogId);
    }

    /**
     * 绑定对话框事件
     */
    bindDialogEvents(dialog, options) {
        const confirmHandler = () => {
            this.hideDialog(options.dialogId);
            if (options.onConfirm) {
                options.onConfirm();
            }
        };

        const cancelHandler = () => {
            this.hideDialog(options.dialogId);
        };

        // 移除旧的事件监听器并添加新的
        const confirmBtn = dialog.querySelector('.dialog-confirm-btn');
        const cancelBtn = dialog.querySelector('.dialog-cancel-btn');
        const overlay = dialog.querySelector('.dialog-overlay');

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

        if (overlay) {
            overlay.replaceWith(overlay.cloneNode(true));
            const newOverlay = dialog.querySelector('.dialog-overlay');
            newOverlay.addEventListener('click', cancelHandler);
        }
    }

    /**
     * 显示对话框
     */
    showDialog(dialogId) {
        const dialog = document.getElementById(dialogId);
        if (!dialog) return;

        dialog.style.display = 'flex';
        setTimeout(() => {
            dialog.classList.add('show');
        }, 10);

        // ESC键关闭
        const handleEsc = (e) => {
            if (e.key === 'Escape') {
                this.hideDialog(dialogId);
                document.removeEventListener('keydown', handleEsc);
            }
        };
        document.addEventListener('keydown', handleEsc);
    }

    /**
     * 隐藏对话框
     */
    hideDialog(dialogId) {
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
     * 获取阶段显示名称
     */
    getStageDisplayName(stageKey) {
        const stage = this.stages.find(s => s.key === stageKey);
        return stage ? stage.name : stageKey;
    }

    /**
     * 获取对象类型名称（用于提示文本）
     */
    getObjectTypeName() {
        const typeNames = {
            'project': '项目',
            'rd_product': '研发产品',
            'product': '产品'
        };
        return typeNames[this.objectType] || '对象';
    }

    /**
     * 通用阶段更新方法，调用后端API
     */
    updateStage(targetStage) {
        // 显示加载指示器
        const loadingOverlay = this.createLoadingOverlay();
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
                object_type: this.objectType,
                object_id: this.objectId,
                current_stage: targetStage
            })
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else if (response.status === 400) {
                return response.json().then(data => {
                    throw new BlockedProgressError(data);
                });
            } else {
                throw new Error(`网络请求失败: ${response.status} ${response.statusText}`);
            }
        })
        .then(data => {
            this.removeLoadingOverlay(loadingOverlay);
            
            if (data.success) {
                // 处理特定对象类型的后续流程
                this.handleUpdateSuccess(data);
            } else {
                const errorMsg = data.message || '未知错误';
                console.error('更新阶段失败: ' + errorMsg);
                alert('更新阶段失败: ' + errorMsg);
            }
        })
        .catch(error => {
            this.removeLoadingOverlay(loadingOverlay);
            
            if (error instanceof BlockedProgressError) {
                this.handleBlockedProgress(error);
            } else {
                console.error('更新阶段错误:', error);
                alert('更新阶段时发生错误: ' + error.message);
            }
        });
    }

    /**
     * 创建加载指示器
     */
    createLoadingOverlay() {
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
        loadingIndicator.innerHTML = `<div>${this.i18nTexts?.stageUpdating || '阶段更新中，请稍候...'}</div>`;
        
        loadingOverlay.appendChild(loadingIndicator);
        return loadingOverlay;
    }

    /**
     * 移除加载指示器
     */
    removeLoadingOverlay(loadingOverlay) {
        if (loadingOverlay && loadingOverlay.parentNode) {
            document.body.removeChild(loadingOverlay);
        }
    }

    /**
     * 处理更新成功
     * 子类可以覆盖此方法来处理特定的后续流程
     */
    handleUpdateSuccess(data) {
        this.refreshPage();
    }

    /**
     * 处理阻塞的进度推进
     * 子类可以覆盖此方法来处理特定的阻塞逻辑
     */
    handleBlockedProgress(error) {
        alert(error.data.message || '阶段推进被阻止');
    }

    /**
     * 刷新页面
     */
    refreshPage() {
        window.location.href = window.location.href.split('?')[0] + 
            '?_nocache=' + new Date().getTime();
    }

    /**
     * 获取分支前的主线阶段
     */
    getLastMainStageBeforeBranch() {
        if (!this.stageHistory || !Array.isArray(this.stageHistory) || this.stageHistory.length === 0) {
            return this.mainStages.length > 0 ? this.mainStages[0].key : null;
        }
        
        // 倒序查找最后一个主线阶段
        for (let i = this.stageHistory.length - 1; i >= 0; i--) {
            const s = this.stageHistory[i];
            if (this.mainStages.some(m => m.key === s.stage)) {
                return s.stage;
            }
        }
        
        return this.mainStages.length > 0 ? this.mainStages[0].key : null;
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
});