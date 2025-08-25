/**
 * 标准化审批流程图组件
 * 支持多种对象类型的审批流程显示和交互
 */
class ApprovalFlow {
    constructor(objectType, objectId, options = {}) {
        console.log('🔍 ApprovalFlow 初始化');
        console.log('🔍 objectType:', objectType);
        console.log('🔍 objectId:', objectId);
        
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
            
            const response = await fetch(`${this.options.apiBasePath}/${this.objectId}/flow`);
            
            console.log('审批流程API响应状态:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            console.log('审批流程API数据:', data);
            
            if (data.success && data.approval_flow) {
                this.approvalData = data.approval_flow;
                console.log('获取到审批实例ID:', this.approvalData.instance_id);
                
                // 🔍 调试：检查审批步骤数据
                if (this.approvalData.stages && this.approvalData.stages.length > 0) {
                    const firstStage = this.approvalData.stages[0];
                    console.log('🔍 第一步审批数据:', firstStage);
                    console.log('🔍 第一步审批人ID:', firstStage.approver_id);
                    console.log('🔍 第一步审批人姓名:', firstStage.approver_name);
                }
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
        const isRecalled = this.approvalData.status === 'recalled';
        
        console.log('🔍 审批流程关键参数:');
        console.log('🔍 currentStage:', currentStage);
        console.log('🔍 canApprove:', canApprove);
        console.log('🔍 isRecalled:', isRecalled);
        console.log('🔍 status:', this.approvalData.status);
        
        // 召回状态不显示横幅提示
        
        stages.forEach((stage, index) => {
            const stageElement = this.createStageElement(stage, currentStage, canApprove, isRecalled);
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
    createStageElement(stage, currentStage, canApprove, isRecalled = false) {
        // 创建阶段容器
        const stageDiv = document.createElement('div');
        stageDiv.className = 'approval-stage';
        stageDiv.setAttribute('data-stage-id', stage.id);
        
        // 召回状态下不允许审批和交互
        if (!isRecalled && stage.stage_order === currentStage && canApprove) {
            stageDiv.classList.add('current');
        }
        
        // 召回状态下添加特殊样式
        if (isRecalled) {
            stageDiv.classList.add('recalled');
        }
        
        // 设置点击事件（召回状态下禁用）
        if (!isRecalled && canApprove && stage.stage_order === currentStage) {
            console.log(`🔍 步骤 ${stage.stage_order} 可以审批，绑定点击事件`);
            stageDiv.classList.add('can-approve');
            stageDiv.onclick = () => this.openApprovalModal(stage);
        } else {
            console.log(`🔍 步骤 ${stage.stage_order} 不可审批，条件: isRecalled=${isRecalled}, canApprove=${canApprove}, stage.stage_order=${stage.stage_order}, currentStage=${currentStage}`);
        }
        
        // 创建圆圈
        const circleDiv = this.createCircleElement(stage, currentStage, canApprove, isRecalled);
        stageDiv.appendChild(circleDiv);
        
        // 创建信息区域
        const infoDiv = this.createInfoElement(stage, isRecalled);
        stageDiv.appendChild(infoDiv);
        
        // 只在有评语且状态为已审批时显示气泡图标（召回状态下不显示）
        if (!isRecalled && stage.comment && stage.comment.trim() !== '' && 
            (stage.status === 'approved' || stage.status === 'rejected')) {
            this.showCommentBubble(stageDiv, stage.comment, stage.status);
        }
        
        return stageDiv;
    }
    
    // 创建圆圈元素
    createCircleElement(stage, currentStage, canApprove, isRecalled = false) {
        const circleDiv = document.createElement('div');
        circleDiv.className = 'stage-circle';
        
        // 调试信息：输出步骤状态
        console.log(`步骤 ${stage.stage_order} (${stage.stage_name}): status="${stage.status}", currentStage=${currentStage}, isRecalled=${isRecalled}`);
        
        if (isRecalled) {
            // 召回状态下，检查是否是召回发生的节点
            if (stage.stage_order === currentStage) {
                // 召回发生的节点显示为橘色召回图标
                circleDiv.classList.add('recalled-node');
                circleDiv.innerHTML = '<i class="fas fa-undo"></i>';
            } else {
                // 其他节点显示为灰色
                circleDiv.classList.add('recalled-inactive');
                // 根据原来的状态显示对应图标但是灰色
                if (stage.status === 'approved') {
                    circleDiv.innerHTML = '<i class="fas fa-check"></i>';
                } else if (stage.status === 'rejected') {
                    circleDiv.innerHTML = '<i class="fas fa-times"></i>';
                } else {
                    circleDiv.innerHTML = stage.stage_order;
                }
            }
        } else if (stage.status === 'current') {
            circleDiv.classList.add('current');
            if (canApprove) {
                // 根据步骤类型选择不同图标
                if (this.isPaymentStep(stage)) {
                    circleDiv.innerHTML = '<i class="fas fa-credit-card"></i>';
                    circleDiv.classList.add('can-approve', 'payment-step');
                } else {
                    circleDiv.innerHTML = '<i class="fas fa-user-check"></i>';
                    circleDiv.classList.add('can-approve');
                }
            } else {
                // 当前阶段但无审批权限 - 观察模式，显示阶段序号
                circleDiv.innerHTML = stage.stage_order;
            }
        } else if (stage.status === 'approved') {
            circleDiv.classList.add('completed');
            // 根据步骤类型选择不同的完成图标
            if (this.isPaymentStep(stage)) {
                circleDiv.innerHTML = '<i class="fas fa-money-check"></i>';
                circleDiv.classList.add('payment-completed');
            } else {
                circleDiv.innerHTML = '<i class="fas fa-check"></i>';
            }
            console.log(`✅ 步骤 ${stage.stage_order} 标记为已审批通过，添加completed类`);
        } else if (stage.status === 'rejected') {
            circleDiv.classList.add('rejected');
            // 支付步骤被拒绝显示为暂缓
            if (this.isPaymentStep(stage)) {
                circleDiv.innerHTML = '<i class="fas fa-pause-circle"></i>';
                circleDiv.classList.add('payment-paused');
            } else {
                circleDiv.innerHTML = '<i class="fas fa-times"></i>';
            }
        } else if (stage.status === 'waiting' || stage.status === 'pending') {
            circleDiv.classList.add('pending');
            // 等待状态下，支付步骤和普通步骤都显示相同的灰色样式
            if (this.isPaymentStep(stage)) {
                circleDiv.innerHTML = '<i class="fas fa-wallet"></i>';
                // 不添加payment-pending类，保持和其他步骤一样的灰色
            } else {
                circleDiv.innerHTML = '<i class="fas fa-clock"></i>';
            }
        } else {
            // 其他未知状态，显示为pending状态
            circleDiv.classList.add('pending');
            circleDiv.innerHTML = stage.stage_order;
            console.log(`⚠️ 步骤 ${stage.stage_order} 状态未识别，添加pending类。状态值: "${stage.status}"`);
        }
        
        return circleDiv;
    }
    
    // 判断是否为支付步骤
    isPaymentStep(stage) {
        // 根据步骤名称或action_type判断是否为支付步骤
        if (stage.action_type === 'payment_processing') {
            return true;
        }
        // 也可以根据步骤名称判断（支持中英文）
        const paymentKeywords = ['支付', '付款', 'payment', 'pay'];
        const stageName = (stage.stage_name || '').toLowerCase();
        return paymentKeywords.some(keyword => stageName.includes(keyword));
    }
    
    // 创建信息元素
    createInfoElement(stage, isRecalled = false) {
        const infoDiv = document.createElement('div');
        infoDiv.className = 'stage-info';
        
        const titleDiv = document.createElement('div');
        titleDiv.className = 'stage-title';
        titleDiv.textContent = stage.stage_name;
        
        const approverDiv = document.createElement('div');
        approverDiv.className = 'stage-approver';
        approverDiv.textContent = stage.approver_name || (window.approvalFlowI18n?.pending || '待分配');
        
        const datesDiv = document.createElement('div');
        datesDiv.className = 'stage-dates';
        
        if (stage.status === 'approved' || stage.status === 'rejected') {
            // 已处理的节点：显示处理时间和处理耗时
            if (stage.processed_at) {
                const processedDate = new Date(stage.processed_at);
                datesDiv.innerHTML = `${window.approvalFlowI18n?.processed || '处理：'}${processedDate.toLocaleDateString()}`;
                
                // 如果有到达时间，计算处理耗时
                if (stage.arrived_at) {
                    const arrivedDate = new Date(stage.arrived_at);
                    const processingHours = Math.max(0, Math.floor((processedDate - arrivedDate) / (1000 * 60 * 60)));
                    if (processingHours < 24) {
                        datesDiv.innerHTML += `<br>${window.approvalFlowI18n?.duration || '耗时：'}${processingHours}${window.approvalFlowI18n?.hours || '小时'}`;
                    } else {
                        const processingDays = Math.floor(processingHours / 24);
                        const remainingHours = processingHours % 24;
                        if (remainingHours > 0) {
                            datesDiv.innerHTML += `<br>${window.approvalFlowI18n?.duration || '耗时：'}${processingDays}${window.approvalFlowI18n?.days || '天'}${remainingHours}${window.approvalFlowI18n?.hours || '小时'}`;
                        } else {
                            datesDiv.innerHTML += `<br>${window.approvalFlowI18n?.duration || '耗时：'}${processingDays}${window.approvalFlowI18n?.days || '天'}`;
                        }
                    }
                }
            }
        } else if (stage.arrived_at) {
            // 当前或等待中的节点：显示到达时间和停留天数
            const arrivedDate = new Date(stage.arrived_at);
            const daysDiff = Math.max(0, Math.floor((new Date() - arrivedDate) / (1000 * 60 * 60 * 24)));
            datesDiv.innerHTML = `
                ${window.approvalFlowI18n?.arrived || '到达：'}${arrivedDate.toLocaleDateString()}<br>
                ${window.approvalFlowI18n?.staying || '停留：'}${daysDiff}${window.approvalFlowI18n?.days || '天'}
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
            { value: 'approve', label: window.approvalFlowI18n?.approve || '同意', color: 'success' },
            { value: 'reject', label: window.approvalFlowI18n?.reject || '拒绝', color: 'danger' }
        ];
        
        // 合并自定义操作
        return [...defaultActions, ...this.options.customActions];
    }
    
    // 显示审批对话框
    async showApprovalDialog(stage, actions) {
        // 设置对话框数据
        this.currentStage = stage;
        await this.setDialogData(stage);
        
        // 显示对话框
        this.showApprovalConfirmDialog();
    }
    
    // 设置对话框数据
    async setDialogData(stage) {
        document.getElementById('approvalStageTitle').textContent = stage.stage_name;
        document.getElementById('approvalApproverName').textContent = stage.approver_name || (window.approvalFlowI18n?.pending || '待分配');
        
        // 格式化到达时间
        if (stage.arrived_at) {
            const arrivedDate = new Date(stage.arrived_at);
            const daysDiff = Math.max(0, Math.floor((new Date() - arrivedDate) / (1000 * 60 * 60 * 24)));
            document.getElementById('approvalArrivedTime').textContent = 
                `${arrivedDate.toLocaleDateString()} (${daysDiff}${window.approvalFlowI18n?.days || '天'}${window.approvalFlowI18n?.ago || '前'})`;
        } else {
            document.getElementById('approvalArrivedTime').textContent = window.approvalFlowI18n?.justArrived || '刚刚到达';
        }
        
        // 清空评语输入
        document.getElementById('approvalComment').value = '';
        
        // 如果是项目审批，获取并显示授权预览
        await this.loadAuthorizationPreview();
    }
    
    // 加载授权预览信息
    async loadAuthorizationPreview() {
        const authSection = document.getElementById('authorizationPreviewSection');
        const authText = document.getElementById('authorizationPreviewText');
        
        if (!authSection || !authText) return;
        
        // 默认隐藏授权预览区域
        authSection.style.display = 'none';
        
        // 只有项目审批才显示授权预览
        if (this.objectType === 'project') {
            console.log('🔍 正在加载项目授权预览...');
            
            try {
                const authPreview = await this.getAuthorizationPreview();
                if (authPreview && authPreview.authorization_code) {
                    console.log('🔍 显示授权预览:', authPreview.authorization_code);
                    authText.textContent = authPreview.message || `通过审批后将授予授权编码：${authPreview.authorization_code}`;
                    authSection.style.display = 'flex';
                    
                    // 保存授权预览数据供后续使用
                    this.currentAuthPreview = authPreview;
                } else {
                    console.log('🔍 未获取到授权预览信息');
                }
            } catch (error) {
                console.log('🔍 获取授权预览失败:', error);
            }
        }
    }
    
    // 显示审批确认对话框
    showApprovalConfirmDialog() {
        const dialog = document.getElementById('approvalConfirmDialog');
        if (dialog) {
            // 绑定按钮事件
            this.bindDialogEvents();
            
            // 显示对话框
            dialog.style.display = 'flex';
            setTimeout(() => {
                dialog.classList.add('show');
            }, 10);
        }
    }
    
    // 隐藏审批确认对话框
    hideApprovalConfirmDialog() {
        const dialog = document.getElementById('approvalConfirmDialog');
        if (dialog) {
            dialog.classList.remove('show');
            setTimeout(() => {
                dialog.style.display = 'none';
            }, 300);
        }
    }
    
    // 绑定对话框事件
    bindDialogEvents() {
        const dialog = document.getElementById('approvalConfirmDialog');
        if (!dialog) return;
        
        // 取消按钮
        const cancelBtn = dialog.querySelector('.dialog-cancel-btn');
        if (cancelBtn) {
            cancelBtn.onclick = () => this.hideApprovalConfirmDialog();
        }
        
        // 拒绝按钮
        const rejectBtn = dialog.querySelector('.dialog-reject-btn');
        if (rejectBtn) {
            rejectBtn.onclick = () => this.handleApprovalAction('reject');
        }
        
        // 通过按钮
        const approveBtn = dialog.querySelector('.dialog-approve-btn');
        if (approveBtn) {
            console.log('🔍 绑定通过按钮点击事件');
            approveBtn.onclick = () => {
                console.log('🔍 通过按钮被点击');
                
                // 如果已经显示过警告，则直接确认继续
                if (approveBtn.dataset.warningShown === 'true') {
                    console.log('🔍 用户确认继续审批（忽略权限违规）');
                    this.proceedWithApproval('approve');
                } else {
                    this.handleApprovalAction('approve');
                }
            };
        } else {
            console.log('🔍 未找到通过按钮 (.dialog-approve-btn)');
        }
        
        // 点击遮罩层关闭
        const overlay = dialog.querySelector('.dialog-overlay');
        if (overlay) {
            overlay.onclick = () => this.hideApprovalConfirmDialog();
        }
    }
    
    // 处理审批操作
    async handleApprovalAction(action) {
        console.log('🔍 handleApprovalAction 被调用');
        console.log('🔍 action 参数:', action);
        
        const comment = document.getElementById('approvalComment').value.trim();
        
        try {
            // 如果是通过操作且为批价单/结算单类型，先进行权限检查
            if (action === 'approve' && this.needsPricingApprovalCheck()) {
                const checkResult = await this.checkPricingApprovalLimits();
                if (checkResult && checkResult.has_violations) {
                    // 显示权限违规警告
                    this.showPricingViolationWarning(checkResult.violations);
                    return; // 不关闭对话框，等待用户确认
                }
            }
            
            // 隐藏对话框
            this.hideApprovalConfirmDialog();
            
            // 调用审批处理
            await this.processApproval(this.currentStage.id, action, comment);
            
        } catch (error) {
            console.error('审批操作失败:', error);
            // 可以显示错误提示
        }
    }
    
    // 检查是否需要批价审批权限检查
    needsPricingApprovalCheck() {
        // 检查对象类型是否为批价单或结算单
        return this.objectType === 'pricing_order' || this.objectType === 'settlement_order';
    }
    
    // 检查批价审批权限下限
    async checkPricingApprovalLimits() {
        try {
            console.log('🔍 开始权限下限检查');
            
            const response = await fetch('/approval/api/check-pricing-approval-limits', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    object_type: this.objectType,
                    object_id: this.objectId
                })
            });
            
            if (!response.ok) {
                console.error('权限检查请求失败:', response.status);
                return null;
            }
            
            const result = await response.json();
            console.log('🔍 权限检查结果:', result);
            
            return result.success ? result : null;
            
        } catch (error) {
            console.error('权限检查失败:', error);
            return null;
        }
    }
    
    // 显示权限违规警告
    showPricingViolationWarning(violations) {
        console.log('🔍 显示权限违规警告:', violations);
        
        const violationSection = document.getElementById('pricingViolationSection');
        const violationList = document.getElementById('pricingViolationList');
        
        if (!violationSection || !violationList) {
            console.error('找不到权限违规警告区域');
            return;
        }
        
        // 构建违规列表HTML
        let listHtml = '';
        violations.forEach(violation => {
            listHtml += `
                <div class="violation-item">
                    <i class="fas fa-exclamation-circle violation-icon"></i>
                    ${violation.message}
                </div>
            `;
        });
        
        violationList.innerHTML = listHtml;
        
        // 显示警告区域
        violationSection.style.display = 'block';
        
        // 更新按钮文本和样式，提示用户确认继续
        const approveBtn = document.querySelector('.dialog-approve-btn');
        if (approveBtn) {
            approveBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>确认通过';
            approveBtn.classList.add('btn-warning');
            approveBtn.classList.remove('btn-success');
            
            // 标记已经显示过警告
            approveBtn.dataset.warningShown = 'true';
        }
    }
    
    // 直接继续审批流程（跳过权限检查）
    async proceedWithApproval(action) {
        console.log('🔍 proceedWithApproval 被调用');
        console.log('🔍 action 参数:', action);
        
        const comment = document.getElementById('approvalComment').value.trim();
        
        try {
            // 隐藏对话框
            this.hideApprovalConfirmDialog();
            
            // 调用审批处理
            await this.processApproval(this.currentStage.id, action, comment);
            
        } catch (error) {
            console.error('审批操作失败:', error);
            // 可以显示错误提示
        }
    }
    
    // 获取审批实例ID
    getApprovalInstanceId() {
        // 从审批数据中获取实例ID
        if (this.approvalData && this.approvalData.instance_id) {
            return this.approvalData.instance_id;
        }
        
        // 如果没有实例ID，尝试从其他地方获取
        console.warn('未找到审批实例ID，审批操作可能失败');
        console.log('当前审批数据:', this.approvalData);
        return null;
    }
    
    // 处理审批
    async processApproval(stageId, action, comment = '') {
        try {
            // 获取审批实例ID（需要从当前审批流程数据中获取）
            const instanceId = this.getApprovalInstanceId();
            if (!instanceId) {
                throw new Error('未找到审批实例ID');
            }
            
            // 使用表单数据格式，因为通用审批端点期望表单数据
            const formData = new FormData();
            formData.append('action', action);
            formData.append('comment', comment);
            
            // 如果是项目审批，添加项目类型参数以启用授权功能
            if (this.objectType === 'project') {
                console.log('🔍 添加项目类型参数以启用授权功能');
                // 尝试从当前审批数据中获取项目类型
                const projectType = this.getProjectType();
                if (projectType) {
                    console.log('🔍 项目类型:', projectType);
                    formData.append('project_type', projectType);
                }
            }
            
            const response = await fetch(`/approval/approve/${instanceId}`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: formData
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
                alert((window.approvalFlowI18n?.approvalFailed || '审批处理失败：') + data.message);
            }
        } catch (error) {
            alert((window.approvalFlowI18n?.approvalFailed || '审批处理失败：') + (window.approvalFlowI18n?.networkError || '网络错误'));
            console.error('处理审批失败:', error);
        }
    }
    
    // 提交审批申请
    async submitForApproval() {
        try {
            console.log('🔍 [DEBUG] submitForApproval 开始执行');
            console.log('🔍 [DEBUG] this.objectType:', this.objectType);
            console.log('🔍 [DEBUG] this.objectId:', this.objectId);
            console.log('🔍 [DEBUG] this.options.apiBasePath:', this.options.apiBasePath);
            
            let apiEndpoint, requestBody = {};
            
            // 批价单特殊处理：需要先保存数据再提交审批
            if (this.objectType === 'pricing_order') {
                console.log('🔍 [DEBUG] ✅ 检测到批价单类型，使用 save_and_submit');
                apiEndpoint = `${this.options.apiBasePath}/${this.objectId}/save_and_submit`;
                console.log('🔍 [DEBUG] apiEndpoint 设置为:', apiEndpoint);
                
                // 收集批价单页面数据
                if (typeof window.pricingOrderDataCollection === 'function') {
                    requestBody = window.pricingOrderDataCollection();
                    console.log('🔍 [DEBUG] 批价单提交审批，收集的数据:', requestBody);
                } else {
                    // 后备方案：收集基本缓存数据
                    requestBody = {
                        basic_info: window.pricingOrderCache || {},
                        pricing_details: typeof collectPricingDetails === 'function' ? collectPricingDetails() : [],
                        settlement_details: typeof collectSettlementDetails === 'function' ? collectSettlementDetails() : []
                    };
                    console.log('🔍 [DEBUG] 批价单提交审批，使用后备数据收集:', requestBody);
                }
            } else {
                // 其他对象类型：使用原来的提交方式
                console.log('🔍 [DEBUG] ❌ 非批价单类型，使用普通 submit');
                apiEndpoint = `${this.options.apiBasePath}/${this.objectId}/submit`;
            }
            
            console.log('🔍 [DEBUG] 最终请求URL:', apiEndpoint);
            console.log('🔍 [DEBUG] 请求方法: POST');
            
            const response = await fetch(apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: Object.keys(requestBody).length > 0 ? JSON.stringify(requestBody) : undefined
            });
            
            const data = await response.json();
            
            if (data.success) {
                // 显示审批流程图
                this.showContainer();
                await this.loadFlow();
                
                // 触发自定义事件
                this.dispatchEvent('submitted', { object_type: this.objectType, object_id: this.objectId });
            } else {
                alert((window.approvalFlowI18n?.submitFailed || '提交失败：') + data.message);
            }
        } catch (error) {
            alert((window.approvalFlowI18n?.submitFailed || '提交失败：') + (window.approvalFlowI18n?.networkError || '网络错误'));
            console.error('提交审批失败:', error);
        }
    }
    
    // 召回审批流程
    async recallApproval(reason = '') {
        try {
            const response = await fetch(`${this.options.apiBasePath}/${this.objectId}/recall`, {
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
                alert((window.approvalFlowI18n?.recallFailed || '召回失败：') + data.message);
            }
        } catch (error) {
            alert((window.approvalFlowI18n?.recallFailed || '召回失败：') + (window.approvalFlowI18n?.networkError || '网络错误'));
            console.error('召回审批失败:', error);
        }
    }
    
    // 重新提交审批
    async resubmitApproval() {
        try {
            console.log('🔍 [DEBUG] resubmitApproval 开始执行');
            console.log('🔍 [DEBUG] this.objectType:', this.objectType);
            console.log('🔍 [DEBUG] this.objectId:', this.objectId);
            console.log('🔍 [DEBUG] this.options.apiBasePath:', this.options.apiBasePath);
            
            let apiEndpoint, requestBody = {};
            
            // 批价单特殊处理：没有专门的 resubmit 路由，使用 save_and_submit
            if (this.objectType === 'pricing_order') {
                console.log('🔍 [DEBUG] ✅ 检测到批价单类型，重新提交使用 save_and_submit');
                apiEndpoint = `${this.options.apiBasePath}/${this.objectId}/save_and_submit`;
                console.log('🔍 [DEBUG] resubmit apiEndpoint 设置为:', apiEndpoint);
                
                // 收集批价单页面数据
                if (typeof window.pricingOrderDataCollection === 'function') {
                    requestBody = window.pricingOrderDataCollection();
                    console.log('🔍 [DEBUG] 批价单重新提交，收集的数据:', requestBody);
                } else {
                    // 后备方案：收集基本缓存数据
                    requestBody = {
                        basic_info: window.pricingOrderCache || {},
                        pricing_details: typeof collectPricingDetails === 'function' ? collectPricingDetails() : [],
                        settlement_details: typeof collectSettlementDetails === 'function' ? collectSettlementDetails() : []
                    };
                    console.log('🔍 [DEBUG] 批价单重新提交，使用后备数据收集:', requestBody);
                }
            } else {
                // 其他对象类型：使用原来的重新提交方式
                console.log('🔍 [DEBUG] ❌ 非批价单类型，使用普通 resubmit');
                apiEndpoint = `${this.options.apiBasePath}/${this.objectId}/resubmit`;
            }
            
            console.log('🔍 [DEBUG] 重新提交最终请求URL:', apiEndpoint);
            console.log('🔍 [DEBUG] 重新提交请求方法: POST');
            
            const response = await fetch(apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: Object.keys(requestBody).length > 0 ? JSON.stringify(requestBody) : undefined
            });
            
            const data = await response.json();
            
            if (data.success) {
                await this.loadFlow();
                // 触发自定义事件
                this.dispatchEvent('resubmitted', { object_type: this.objectType, object_id: this.objectId });
            } else {
                alert((window.approvalFlowI18n?.resubmitFailed || '重新提交失败：') + data.message);
            }
        } catch (error) {
            alert((window.approvalFlowI18n?.resubmitFailed || '重新提交失败：') + (window.approvalFlowI18n?.networkError || '网络错误'));
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
        const message = (window.approvalFlowI18n?.noPermissionMessage || '当前阶段"{stage}"需要由 {approver} 进行审批。您暂无权限审批此阶段。')
            .replace('{stage}', stage.stage_name)
            .replace('{approver}', stage.approver_name);
        alert(message);
    }
    
    // 显示阶段信息
    showStageInfo(stage) {
        let message = `${window.approvalFlowI18n?.stageInfo || '阶段信息：'}${stage.stage_name}\n`;
        message += `${window.approvalFlowI18n?.approver || '审批人：'}${stage.approver_name}\n`;
        
        if (stage.status === 'approved') {
            message += `${window.approvalFlowI18n?.status || '状态：'}${window.approvalFlowI18n?.approved || '已通过'}\n`;
            if (stage.processed_at) {
                const processedDate = new Date(stage.processed_at);
                message += `${window.approvalFlowI18n?.processedTime || '处理时间：'}${processedDate.toLocaleString()}`;
            }
        } else if (stage.status === 'rejected') {
            message += `${window.approvalFlowI18n?.status || '状态：'}${window.approvalFlowI18n?.rejected || '已拒绝'}\n`;
            if (stage.processed_at) {
                const processedDate = new Date(stage.processed_at);
                message += `${window.approvalFlowI18n?.processedTime || '处理时间：'}${processedDate.toLocaleString()}`;
            }
        } else if (stage.status === 'pending') {
            message += `${window.approvalFlowI18n?.status || '状态：'}${window.approvalFlowI18n?.pending || '待处理'}\n`;
            if (stage.arrived_at) {
                const arrivedDate = new Date(stage.arrived_at);
                message += `${window.approvalFlowI18n?.arrivedTime || '到达时间：'}${arrivedDate.toLocaleString()}`;
            }
        } else {
            message += `${window.approvalFlowI18n?.status || '状态：'}${window.approvalFlowI18n?.waiting || '等待中'}`;
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
        icon.title = window.approvalFlowI18n?.clickToView || '点击查看审批意见';
        
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
    
    // 获取授权编码预览
    async getAuthorizationPreview() {
        console.log('🔍 getAuthorizationPreview 方法被调用');
        console.log('🔍 this.objectType:', this.objectType);
        console.log('🔍 this.objectId:', this.objectId);
        
        try {
            const url = `/${this.objectType}/api/approval/${this.objectId}/preview-authorization`;
            console.log('调用授权预览API:', url);
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({})
            });
            
            console.log('预览API响应状态:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.log('预览授权编码API响应非200，状态:', response.status, '错误信息:', errorText);
                return null;
            }
            
            const data = await response.json();
            console.log('预览API响应数据:', data);
            
            if (data.success) {
                console.log('成功获取授权预览:', data.authorization_code);
                return data;
            } else {
                console.log('预览授权编码返回不成功，原因:', data.message);
                return null;
            }
        } catch (error) {
            console.log('获取授权编码预览失败（可能不是授权步骤）:', error);
            return null;
        }
    }
    
    // 获取项目类型  
    getProjectType() {
        // 如果之前获取授权预览时保存了项目类型，直接使用
        if (this.cachedProjectType) {
            console.log('🔍 使用缓存的项目类型:', this.cachedProjectType);
            return this.cachedProjectType;
        }
        
        // 从当前授权预览数据中获取（如果可用）
        if (this.currentAuthPreview && this.currentAuthPreview.project_type) {
            this.cachedProjectType = this.currentAuthPreview.project_type;
            console.log('🔍 从授权预览数据获取项目类型:', this.cachedProjectType);
            return this.cachedProjectType;
        }
        
        // 从页面数据获取
        if (window.projectData && window.projectData.project_type) {
            this.cachedProjectType = window.projectData.project_type;
            console.log('🔍 从页面数据获取项目类型:', this.cachedProjectType);
            return this.cachedProjectType;
        }
        
        // 最后手段：根据当前审批数据推断
        // 从授权预览API的响应中，我们看到项目类型是channel_follow
        // 这是临时方案，应该从更可靠的来源获取
        console.log('⚠️ 使用默认项目类型推断: channel_follow');
        this.cachedProjectType = 'channel_follow';
        return this.cachedProjectType;
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
        alert(window.approvalFlowI18n?.noCurrentStage || '无法找到当前审批阶段信息');
    }
};