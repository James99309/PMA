/**
 * 标准化审批流程图组件
 * 支持多种对象类型的审批流程显示和交互
 */
class ApprovalFlow {
    constructor(objectType, objectId, options = {}) {
        this.objectType = objectType;
        this.objectId = objectId;
        this.options = {
            containerId: 'approvalFlowSection',
            containerSelector: '#approvalFlowContainer',
            enableInteraction: true,
            showSubmitButton: true,
            autoLoad: false,
            apiBasePath: '/inventory/api/approval',
            customActions: [], // 自定义审批操作
            ...options
        };
        
        this.approvalData = null;
        this.container = null;
        this.flowDiv = null;
    }
    
    // 初始化流程图
    async init() {
        this.container = document.querySelector(this.options.containerSelector);
        if (!this.container) {
            console.error('Approval flow container not found:', this.options.containerSelector);
            return;
        }
        
        if (this.options.autoLoad) {
            await this.loadFlow();
        }
    }
    
    // 获取CSRF令牌
    getCSRFToken() {
        // 从meta标签获取
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            return metaToken.getAttribute('content');
        }
        
        // 从隐藏表单字段获取
        const hiddenToken = document.querySelector('input[name="csrf_token"]');
        if (hiddenToken) {
            return hiddenToken.value;
        }
        
        // 从全局变量获取（如果模板中设置了）
        if (window.csrf_token) {
            return window.csrf_token;
        }
        
        console.warn('CSRF token not found');
        return null;
    }
    
    // 加载审批流程数据
    async loadFlow() {
        try {
            console.log(`开始加载审批流程，对象类型: ${this.objectType}, ID: ${this.objectId}`);
            
            const response = await fetch(`${this.options.apiBasePath}/${this.objectType}/${this.objectId}/flow`);
            
            console.log('审批流程API响应状态:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            console.log('审批流程API数据:', data);
            
            if (data.success && data.approval_flow) {
                this.approvalData = data.approval_flow;
                this.renderFlow();
                this.showContainer();
                console.log('审批流程图已显示');
                
                // 触发审批控制按钮更新和操作区域可见性更新
                if (typeof updateApprovalControlButtons === 'function') {
                    setTimeout(updateApprovalControlButtons, 100);
                }
                if (typeof updateOperationSectionVisibility === 'function') {
                    setTimeout(updateOperationSectionVisibility, 150);
                }
            } else {
                // 如果没有审批流程，使用API返回的控制信息
                console.log('未找到审批流程:', data.message);
                
                if (data.control_info) {
                    // 使用API返回的控制信息
                    this.approvalData = {
                        status: data.control_info.status,
                        can_submit: data.control_info.can_submit,
                        can_recall: data.control_info.can_recall,
                        can_resubmit: data.control_info.can_resubmit,
                        is_creator: data.control_info.is_creator
                    };
                    console.log('获取控制信息:', this.approvalData);
                } else {
                    // 降级处理：设置默认的控制信息
                    this.approvalData = {
                        status: 'unknown',
                        can_submit: false,
                        can_recall: false,
                        can_resubmit: false,
                        is_creator: false
                    };
                    console.log('使用默认控制信息');
                }
                
                this.hideContainer();
                
                // 触发审批控制按钮更新和操作区域可见性更新
                if (typeof updateApprovalControlButtons === 'function') {
                    setTimeout(updateApprovalControlButtons, 100);
                }
                if (typeof updateOperationSectionVisibility === 'function') {
                    setTimeout(updateOperationSectionVisibility, 150);
                }
            }
        } catch (error) {
            console.error('加载审批流程失败:', error);
            this.hideContainer();
        }
    }
    
    // 显示容器
    showContainer() {
        const section = document.getElementById(this.options.containerId);
        if (section) {
            section.style.display = 'block';
            console.log(`显示审批流程容器: ${this.options.containerId}`);
        } else {
            console.error(`找不到审批流程容器: ${this.options.containerId}`);
        }
    }
    
    // 隐藏容器
    hideContainer() {
        const section = document.getElementById(this.options.containerId);
        if (section) {
            section.style.display = 'none';
            console.log(`隐藏审批流程容器: ${this.options.containerId}`);
        } else {
            console.error(`找不到要隐藏的容器: ${this.options.containerId}`);
        }
    }
    
    // 渲染流程图
    renderFlow() {
        if (!this.approvalData) return;
        
        // 清空容器
        this.container.innerHTML = '';
        
        // 创建流程图容器
        this.flowDiv = document.createElement('div');
        this.flowDiv.className = 'approval-flow';
        
        const stages = this.approvalData.stages || [];
        const currentStage = this.approvalData.current_stage;
        const canApprove = this.approvalData.can_approve;
        
        stages.forEach((stage, index) => {
            const stageElement = this.createStageElement(stage, currentStage, canApprove);
            this.flowDiv.appendChild(stageElement);
        });
        
        this.container.appendChild(this.flowDiv);
        
        // 创建连接线
        this.createProgressLine(stages, currentStage);
        
        // 监听窗口大小变化
        window.addEventListener('resize', () => {
            setTimeout(() => {
                this.createProgressLine(stages, currentStage);
            }, 100);
        });
    }
    
    // 创建阶段元素
    createStageElement(stage, currentStage, canApprove) {
        // 创建阶段容器
        const stageDiv = document.createElement('div');
        stageDiv.className = 'approval-stage';
        stageDiv.setAttribute('data-stage-id', stage.id);
        
        if (stage.stage_order === currentStage && canApprove) {
            stageDiv.classList.add('current');
        }
        
        // 设置点击事件
        if (canApprove && stage.stage_order === currentStage) {
            stageDiv.classList.add('can-approve');
            stageDiv.onclick = () => this.openApprovalModal(stage);
        }
        
        // 创建圆圈
        const circleDiv = this.createCircleElement(stage, currentStage, canApprove);
        stageDiv.appendChild(circleDiv);
        
        // 创建信息区域
        const infoDiv = this.createInfoElement(stage);
        stageDiv.appendChild(infoDiv);
        
        // 只在有评语且状态为已审批时显示气泡图标
        if (stage.comment && stage.comment.trim() !== '' && 
            (stage.status === 'approved' || stage.status === 'rejected')) {
            this.showCommentBubble(stageDiv, stage.comment, stage.status);
        }
        
        return stageDiv;
    }
    
    // 创建圆圈元素
    createCircleElement(stage, currentStage, canApprove) {
        const circleDiv = document.createElement('div');
        circleDiv.className = 'stage-circle';
        
        if (stage.stage_order === currentStage && stage.status === 'pending') {
            circleDiv.classList.add('current');
            if (canApprove) {
                circleDiv.innerHTML = '<i class="fas fa-user-check"></i>';
                circleDiv.classList.add('can-approve');
            } else {
                // 当前阶段但无审批权限 - 观察模式，显示阶段序号
                circleDiv.innerHTML = stage.stage_order;
            }
        } else if (stage.status === 'approved') {
            circleDiv.classList.add('completed');
            circleDiv.innerHTML = '<i class="fas fa-check"></i>';
        } else if (stage.status === 'rejected') {
            circleDiv.classList.add('rejected');
            circleDiv.innerHTML = '<i class="fas fa-times"></i>';
        } else if (stage.status === 'waiting' || (stage.status === 'pending' && stage.stage_order !== currentStage)) {
            circleDiv.classList.add('pending');
            circleDiv.innerHTML = '<i class="fas fa-clock"></i>';
        } else {
            circleDiv.classList.add('pending');
            circleDiv.innerHTML = stage.stage_order;
        }
        
        return circleDiv;
    }
    
    // 创建信息元素
    createInfoElement(stage) {
        const infoDiv = document.createElement('div');
        infoDiv.className = 'stage-info';
        
        const titleDiv = document.createElement('div');
        titleDiv.className = 'stage-title';
        titleDiv.textContent = stage.stage_name;
        
        const approverDiv = document.createElement('div');
        approverDiv.className = 'stage-approver';
        approverDiv.textContent = stage.approver_name || '待分配';
        
        const datesDiv = document.createElement('div');
        datesDiv.className = 'stage-dates';
        
        if (stage.arrived_at) {
            const arrivedDate = new Date(stage.arrived_at);
            const daysDiff = Math.max(0, Math.floor((new Date() - arrivedDate) / (1000 * 60 * 60 * 24)));
            datesDiv.innerHTML = `
                到达：${arrivedDate.toLocaleDateString()}<br>
                停留：${daysDiff}天
            `;
        }
        
        infoDiv.appendChild(titleDiv);
        infoDiv.appendChild(approverDiv);
        infoDiv.appendChild(datesDiv);
        
        return infoDiv;
    }
    
    // 创建进度连接线
    createProgressLine(stages, currentStage) {
        if (stages.length <= 1) return;
        
        // 清除之前的连接线
        const existingSegments = this.flowDiv.querySelectorAll('.progress-segment');
        existingSegments.forEach(segment => segment.remove());
        
        setTimeout(() => {
            const stageElements = this.flowDiv.querySelectorAll('.approval-stage');
            if (stageElements.length < 2) return;
            
            // 计算当前阶段索引
            let currentStageIndex = -1;
            stages.forEach((stage, index) => {
                if (stage.stage_order === currentStage) {
                    currentStageIndex = index;
                }
            });
            
            // 获取每个阶段圆圈的中心位置
            const circlePositions = [];
            stageElements.forEach((stageEl) => {
                const circle = stageEl.querySelector('.stage-circle');
                const rect = circle.getBoundingClientRect();
                const flowRect = this.flowDiv.getBoundingClientRect();
                const centerX = rect.left + rect.width/2 - flowRect.left;
                circlePositions.push(centerX);
            });
            
            // 创建连接线段
            for (let i = 0; i < circlePositions.length - 1; i++) {
                const segmentDiv = document.createElement('div');
                segmentDiv.className = 'progress-segment';
                
                const startX = circlePositions[i];
                const endX = circlePositions[i + 1];
                const width = endX - startX;
                
                segmentDiv.style.left = startX + 'px';
                segmentDiv.style.width = width + 'px';
                
                // 根据进度设置颜色
                if (i < currentStageIndex) {
                    segmentDiv.style.backgroundColor = '#198754'; // 已完成 - 绿色
                } else if (i === currentStageIndex - 1 && currentStageIndex > 0) {
                    segmentDiv.style.background = 'linear-gradient(to right, #198754 70%, #dee2e6 30%)'; // 当前进行中 - 渐变
                } else {
                    segmentDiv.style.backgroundColor = '#dee2e6'; // 未开始 - 灰色
                }
                
                this.flowDiv.appendChild(segmentDiv);
            }
        }, 50);
    }
    
    // 打开审批模态框
    openApprovalModal(stage) {
        // 获取可审批的圆圈元素
        const targetCircle = this.flowDiv.querySelector('.stage-circle.can-approve');
        
        // 触发点击动画
        if (targetCircle) {
            this.triggerClickAnimation(targetCircle);
        }
        
        // 延迟显示确认对话框
        setTimeout(() => {
            const actions = this.getAvailableActions(stage);
            this.showApprovalDialog(stage, actions);
        }, 200);
    }
    
    // 获取可用的审批操作
    getAvailableActions(stage) {
        const defaultActions = [
            { value: 'approve', label: '同意', color: 'success' },
            { value: 'reject', label: '拒绝', color: 'danger' }
        ];
        
        // 合并自定义操作
        return [...defaultActions, ...this.options.customActions];
    }
    
    // 显示审批对话框
    showApprovalDialog(stage, actions) {
        // 设置模态框数据
        this.currentStage = stage;
        this.setModalData(stage);
        
        // 显示模态框
        const modal = new bootstrap.Modal(document.getElementById('approvalConfirmModal'));
        modal.show();
    }
    
    // 设置模态框数据
    setModalData(stage) {
        document.getElementById('modalStageTitle').textContent = stage.stage_name;
        document.getElementById('modalApproverName').textContent = stage.approver_name || '待分配';
        
        // 格式化到达时间
        if (stage.arrived_at) {
            const arrivedDate = new Date(stage.arrived_at);
            const daysDiff = Math.max(0, Math.floor((new Date() - arrivedDate) / (1000 * 60 * 60 * 24)));
            document.getElementById('modalArrivedTime').textContent = 
                `${arrivedDate.toLocaleDateString()} (${daysDiff}天前)`;
        } else {
            document.getElementById('modalArrivedTime').textContent = '刚刚到达';
        }
        
        // 清空评语输入
        document.getElementById('approvalComment').value = '';
    }
    
    // 处理审批
    async processApproval(stageId, action, comment = '') {
        try {
            const response = await fetch(`${this.options.apiBasePath}/${this.objectType}/${this.objectId}/process`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    stage_id: stageId,
                    action: action,
                    comment: comment
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // 在重新加载流程图之前显示气泡
                if (comment) {
                    this.updateStageWithComment(stageId, comment, action);
                }
                
                await this.loadFlow(); // 重新加载流程图
                
                // 重新加载后再次显示气泡（因为DOM重新创建了）
                if (comment) {
                    setTimeout(() => {
                        this.updateStageWithComment(stageId, comment, action);
                    }, 200);
                }
                
                // 触发自定义事件
                this.dispatchEvent('approved', { stage_id: stageId, action: action });
            } else {
                alert('审批处理失败：' + data.message);
            }
        } catch (error) {
            alert('审批处理失败：网络错误');
            console.error('处理审批失败:', error);
        }
    }
    
    // 提交审批申请
    async submitForApproval() {
        try {
            const response = await fetch(`${this.options.apiBasePath}/${this.objectType}/${this.objectId}/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // 显示审批流程图
                this.showContainer();
                await this.loadFlow();
                
                // 触发自定义事件
                this.dispatchEvent('submitted', { object_type: this.objectType, object_id: this.objectId });
            } else {
                alert('提交失败：' + data.message);
            }
        } catch (error) {
            alert('提交失败：网络错误');
            console.error('提交审批失败:', error);
        }
    }
    
    // 召回审批流程
    async recallApproval(reason = '') {
        try {
            const response = await fetch(`${this.options.apiBasePath}/${this.objectType}/${this.objectId}/recall`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    reason: reason
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                await this.loadFlow();
                // 触发自定义事件
                this.dispatchEvent('recalled', { object_type: this.objectType, object_id: this.objectId });
            } else {
                alert('召回失败：' + data.message);
            }
        } catch (error) {
            alert('召回失败：网络错误');
            console.error('召回审批失败:', error);
        }
    }
    
    // 重新提交审批
    async resubmitApproval() {
        try {
            const response = await fetch(`${this.options.apiBasePath}/${this.objectType}/${this.objectId}/resubmit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                await this.loadFlow();
                // 触发自定义事件
                this.dispatchEvent('resubmitted', { object_type: this.objectType, object_id: this.objectId });
            } else {
                alert('重新提交失败：' + data.message);
            }
        } catch (error) {
            alert('重新提交失败：网络错误');
            console.error('重新提交审批失败:', error);
        }
    }
    
    // 触发点击动画效果
    triggerClickAnimation(circleElement) {
        circleElement.classList.add('clicking');
        setTimeout(() => {
            circleElement.classList.remove('clicking');
        }, 600);
    }
    
    // 显示无权限消息
    showNoPermissionMessage(stage) {
        alert(`当前阶段"${stage.stage_name}"需要由 ${stage.approver_name} 进行审批。您暂无权限审批此阶段。`);
    }
    
    // 显示阶段信息
    showStageInfo(stage) {
        let message = `阶段信息：${stage.stage_name}\n`;
        message += `审批人：${stage.approver_name}\n`;
        
        if (stage.status === 'approved') {
            message += `状态：已通过\n`;
            if (stage.processed_at) {
                const processedDate = new Date(stage.processed_at);
                message += `处理时间：${processedDate.toLocaleString()}`;
            }
        } else if (stage.status === 'rejected') {
            message += `状态：已拒绝\n`;
            if (stage.processed_at) {
                const processedDate = new Date(stage.processed_at);
                message += `处理时间：${processedDate.toLocaleString()}`;
            }
        } else if (stage.status === 'pending') {
            message += `状态：待处理\n`;
            if (stage.arrived_at) {
                const arrivedDate = new Date(stage.arrived_at);
                message += `到达时间：${arrivedDate.toLocaleString()}`;
            }
        } else {
            message += `状态：等待中`;
        }
        
        alert(message);
    }
    
    // 事件分发
    dispatchEvent(eventName, detail) {
        const event = new CustomEvent(`approval_${eventName}`, { detail });
        document.dispatchEvent(event);
    }
    
    // 销毁实例
    destroy() {
        if (this.container) {
            this.container.innerHTML = '';
        }
        window.removeEventListener('resize', this.resizeHandler);
    }
    
    // 显示审批评语气泡
    showCommentBubble(stageElement, comment, action) {
        // 移除已有的气泡和图标
        const existingIcon = stageElement.querySelector('.approval-comment-icon');
        const existingBubble = stageElement.querySelector('.approval-comment-bubble');
        if (existingIcon) existingIcon.remove();
        if (existingBubble) existingBubble.remove();
        
        if (!comment || comment.trim() === '') return;
        
        // 创建气泡图标
        const icon = document.createElement('div');
        icon.className = `approval-comment-icon ${action}`;
        icon.innerHTML = '<i class="fas fa-comment"></i>';
        icon.title = '点击查看审批意见';
        
        // 创建气泡内容（隐藏）
        const bubble = document.createElement('div');
        bubble.className = `approval-comment-bubble ${action}`;
        bubble.innerHTML = `
            <div class="approval-comment-content">
                ${comment}
            </div>
        `;
        
        // 图标点击事件：显示/隐藏气泡
        icon.addEventListener('click', (e) => {
            e.stopPropagation();
            if (bubble.style.display === 'none' || bubble.style.display === '') {
                // 隐藏其他所有气泡
                document.querySelectorAll('.approval-comment-bubble').forEach(b => {
                    b.style.display = 'none';
                });
                bubble.style.display = 'block';
                bubble.classList.add('show');
            } else {
                bubble.style.display = 'none';
                bubble.classList.remove('show');
            }
        });
        
        // 气泡点击事件：隐藏气泡
        bubble.addEventListener('click', (e) => {
            e.stopPropagation();
            bubble.style.display = 'none';
            bubble.classList.remove('show');
        });
        
        // 点击其他地方隐藏气泡
        document.addEventListener('click', () => {
            bubble.style.display = 'none';
            bubble.classList.remove('show');
        });
        
        stageElement.appendChild(icon);
        stageElement.appendChild(bubble);
    }
    
    // 更新审批流程显示以包含评语气泡
    updateStageWithComment(stageId, comment, action) {
        const stageElement = this.flowDiv.querySelector(`[data-stage-id="${stageId}"]`);
        if (stageElement) {
            this.showCommentBubble(stageElement, comment, action);
        }
    }
}

// 全局便利函数
window.ApprovalFlow = ApprovalFlow;

window.initApprovalFlow = function(objectType, objectId, options = {}) {
    const flow = new ApprovalFlow(objectType, objectId, options);
    flow.init();
    return flow;
};

// 提交审批的全局函数
window.submitApprovalFlow = function(objectType, objectId, options = {}) {
    const flow = new ApprovalFlow(objectType, objectId, options);
    return flow.submitForApproval();
};

// 全局模态框确认函数
window.confirmApprovalAction = function(action) {
    const comment = document.getElementById('approvalComment').value.trim();
    
    // 获取当前活跃的审批流程实例
    const activeFlows = Array.from(window.approvalFlowInstances.values());
    const currentFlow = activeFlows.find(flow => flow.currentStage);
    
    if (currentFlow && currentFlow.currentStage) {
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('approvalConfirmModal'));
        if (modal) {
            modal.hide();
        }
        
        // 处理审批
        currentFlow.processApproval(currentFlow.currentStage.id, action, comment);
    } else {
        alert('无法找到当前审批阶段信息');
    }
};