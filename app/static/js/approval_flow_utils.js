/**
 * 审批流程标准化工具函数
 * 提供简单易用的接口来初始化和管理审批流程
 */

// 全局审批流程实例存储
window.approvalFlowInstances = new Map();

/**
 * 初始化标准化审批流程
 * @param {string} objectType - 对象类型（如 'order', 'project', 'quotation'）
 * @param {number} objectId - 对象ID
 * @param {string} containerId - 容器ID
 * @param {object} options - 配置选项
 */
function initStandardApprovalFlow(objectType, objectId, containerId = 'approvalFlowSection', options = {}) {
    const defaultOptions = {
        containerId: containerId,
        containerSelector: `#${containerId}Container`,
        enableInteraction: true,
        autoLoad: false, // 默认不自动加载，由页面状态决定
        apiBasePath: '/inventory/api/approval'
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    const flow = new ApprovalFlow(objectType, objectId, finalOptions);
    flow.init();
    
    // 存储实例以便后续访问
    const instanceKey = `${objectType}_${objectId}`;
    window.approvalFlowInstances.set(instanceKey, flow);
    
    return flow;
}

/**
 * 获取审批流程实例
 * @param {string} objectType - 对象类型
 * @param {number} objectId - 对象ID
 * @returns {ApprovalFlow|null} 审批流程实例
 */
function getApprovalFlowInstance(objectType, objectId) {
    const instanceKey = `${objectType}_${objectId}`;
    return window.approvalFlowInstances.get(instanceKey) || null;
}

/**
 * 提交标准化审批
 * @param {string} objectType - 对象类型
 * @param {number} objectId - 对象ID
 * @param {object} options - 配置选项
 */
async function submitStandardApproval(objectType, objectId, options = {}) {
    if (confirm('确定要提交审批吗？提交后无法直接修改内容。')) {
        try {
            // 获取或创建审批流程实例
            let flow = getApprovalFlowInstance(objectType, objectId);
            if (!flow) {
                flow = initStandardApprovalFlow(objectType, objectId, 'approvalFlowSection', options);
            }
            
            // 提交审批
            await flow.submitForApproval();
            
        } catch (error) {
            console.error('提交审批失败:', error);
            alert('提交失败：网络错误');
        }
    }
}

/**
 * 手动加载审批流程图
 * @param {string} objectType - 对象类型
 * @param {number} objectId - 对象ID
 */
async function loadApprovalFlow(objectType, objectId) {
    const flow = getApprovalFlowInstance(objectType, objectId);
    if (flow) {
        await flow.loadFlow();
    } else {
        console.error('审批流程实例不存在，请先初始化');
    }
}

/**
 * 检查对象状态并自动显示相应的审批UI
 * @param {string} objectType - 对象类型
 * @param {number} objectId - 对象ID
 * @param {string} objectStatus - 对象状态
 */
function autoShowApprovalUI(objectType, objectId, objectStatus) {
    console.log(`autoShowApprovalUI: ${objectType}#${objectId} status=${objectStatus}`);
    
    let flow = getApprovalFlowInstance(objectType, objectId);
    if (!flow) {
        flow = initStandardApprovalFlow(objectType, objectId);
    }
    
    // 新的操作区域将在模板中根据状态自动显示正确内容
    // 这里主要处理流程图的显示/隐藏和操作区域的权限显示
    
    if (['pending', 'approved', 'rejected', 'recalled'].includes(objectStatus)) {
        // 有审批流程的状态：尝试显示流程图
        flow.loadFlow().then(() => {
            // 如果是pending状态但没有找到审批流程，显示提示信息
            if (objectStatus === 'pending' && (!flow.approvalData || flow.approvalData.status === 'unknown')) {
                console.warn('订单状态为审批中，但未找到审批流程，可能存在数据问题');
            }
            // 检查操作区域权限
            updateOperationSectionVisibility();
        });
    } else {
        // 草稿或其他状态，隐藏流程图，但仍需加载数据用于权限判断
        flow.hideContainer();
        flow.loadFlow().then(() => {
            // 检查操作区域权限
            updateOperationSectionVisibility();
        });
    }
}

/**
 * 获取CSRF令牌的通用函数
 * @returns {string|null} CSRF令牌
 */
function getCSRFToken() {
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
    
    // 从全局变量获取
    if (window.csrf_token) {
        return window.csrf_token;
    }
    
    // 从模板变量获取（需要在模板中设置）
    if (typeof csrf_token !== 'undefined') {
        return csrf_token;
    }
    
    console.warn('CSRF token not found');
    return null;
}

/**
 * 设置全局CSRF令牌
 * @param {string} token - CSRF令牌
 */
function setGlobalCSRFToken(token) {
    window.csrf_token = token;
    
    // 同时设置到meta标签
    let metaToken = document.querySelector('meta[name="csrf-token"]');
    if (!metaToken) {
        metaToken = document.createElement('meta');
        metaToken.name = 'csrf-token';
        document.head.appendChild(metaToken);
    }
    metaToken.content = token;
}

/**
 * 事件监听器：审批提交成功
 */
document.addEventListener('approval_submitted', function(event) {
    console.log('审批提交成功:', event.detail);
    
    // 可以在这里添加全局的成功处理逻辑
    // 比如刷新页面状态、显示通知等
});

/**
 * 事件监听器：审批处理成功
 */
document.addEventListener('approval_approved', function(event) {
    console.log('审批处理成功:', event.detail);
    
    // 可以在这里添加全局的审批成功处理逻辑
});

/**
 * 显示召回确认模态框
 */
function showRecallConfirmModal() {
    const modal = new bootstrap.Modal(document.getElementById('recallConfirmModal'));
    modal.show();
}

/**
 * 执行召回操作
 */
async function executeRecallApproval() {
    const reasonInput = document.getElementById('recallReason');
    const reason = reasonInput ? reasonInput.value.trim() : '';
    const flow = window.approvalFlowInstance;
    
    if (flow) {
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('recallConfirmModal'));
        if (modal) {
            modal.hide();
        }
        
        try {
            await flow.recallApproval(reason);
            // 清空输入框
            if (reasonInput) {
                reasonInput.value = '';
            }
            // 召回成功后动态更新操作区域，然后刷新页面
            updateOperationSection('draft');
            // 稍后刷新页面以确保所有状态同步
            setTimeout(() => location.reload(), 500);
        } catch (error) {
            console.error('召回失败:', error);
            alert('召回失败，请重试');
        }
    } else {
        alert('无法找到审批流程实例');
    }
}

/**
 * 确认重新提交
 */
function confirmResubmitApproval() {
    if (confirm('确定要重新提交审批吗？重新提交后将重置所有审批历史，重新开始审批流程。')) {
        executeResubmitApproval();
    }
}

/**
 * 执行重新提交操作
 */
async function executeResubmitApproval() {
    const flow = window.approvalFlowInstance;
    
    if (flow) {
        try {
            await flow.resubmitApproval();
            // 重新提交成功后动态更新操作区域，然后刷新页面
            updateOperationSection('pending');
            // 稍后刷新页面以确保所有状态同步
            setTimeout(() => location.reload(), 500);
        } catch (error) {
            console.error('重新提交失败:', error);
            alert('重新提交失败，请重试');
        }
    } else {
        alert('无法找到审批流程实例');
    }
}

/**
 * 动态更新操作区域
 * @param {string} newStatus 新的状态
 */
function updateOperationSection(newStatus) {
    const operationSection = document.getElementById('approvalOperationSection');
    const operationInfo = document.getElementById('approvalOperationInfo');
    const operationButtons = document.getElementById('approvalOperationButtons');
    
    if (!operationSection || !operationInfo || !operationButtons) {
        console.log('找不到操作区域元素');
        return;
    }
    
    // 更新信息区域
    let infoHtml = '';
    let buttonsHtml = '';
    
    if (newStatus === 'draft') {
        infoHtml = `
            <p class="text-muted mb-2">创建完成，可以提交审批流程。</p>
            <small class="text-muted">提交后将进入审批流程，无法直接修改。</small>
        `;
        buttonsHtml = `
            <button type="button" class="btn btn-success operation-btn-submit" onclick="submitStandardApproval('order', ${window.currentOrderId || 'null'})">
                <i class="fas fa-paper-plane me-1"></i>提交审批
            </button>
        `;
    } else if (newStatus === 'pending') {
        // 检查是否有召回权限
        const flow = window.approvalFlowInstance;
        const canRecall = flow && flow.approvalData && flow.approvalData.can_recall;
        
        if (canRecall) {
            infoHtml = `
                <p class="text-muted mb-2">审批流程进行中，您可以召回流程。</p>
                <small class="text-muted">召回后流程将停止，状态将回到草稿状态。</small>
            `;
            buttonsHtml = `
                <button type="button" class="btn btn-warning operation-btn-recall" onclick="showRecallConfirmModal()">
                    <i class="fas fa-undo me-1"></i>召回流程
                </button>
            `;
        } else {
            infoHtml = `
                <p class="text-muted mb-2">审批流程进行中，已有人员审批，无法召回。</p>
                <small class="text-muted">请等待审批完成或联系相关审批人员。</small>
            `;
            buttonsHtml = ''; // 不显示召回按钮
        }
    } else if (newStatus === 'rejected' || newStatus === 'recalled') {
        const statusText = newStatus === 'rejected' ? '拒绝' : '召回';
        infoHtml = `
            <p class="text-muted mb-2">审批流程被${statusText}，您可以重新提交。</p>
            <small class="text-muted">重新提交将重置审批历史，重新开始审批流程。</small>
        `;
        buttonsHtml = `
            <button type="button" class="btn btn-success operation-btn-resubmit" onclick="confirmResubmitApproval()">
                <i class="fas fa-redo me-1"></i>重新提交
            </button>
        `;
    }
    
    // 更新DOM
    operationInfo.innerHTML = infoHtml;
    operationButtons.innerHTML = buttonsHtml;
    
    console.log(`操作区域已更新为状态: ${newStatus}`);
}

/**
 * 更新操作区域的可见性
 * 根据用户权限决定是否显示操作区域
 */
function updateOperationSectionVisibility() {
    const operationSection = document.getElementById('approvalOperationSection');
    if (!operationSection) {
        console.log('找不到操作区域');
        return;
    }
    
    const flow = window.approvalFlowInstance;
    if (!flow || !flow.approvalData) {
        console.log('没有审批流程数据，隐藏操作区域');
        operationSection.style.display = 'none';
        return;
    }
    
    const data = flow.approvalData;
    const hasAnyPermission = data.can_submit || data.can_recall || data.can_resubmit;
    const isCreator = data.is_creator;
    
    // 只有是创建人且有任何权限时才显示操作区域
    if (isCreator && hasAnyPermission) {
        operationSection.style.display = 'block';
        console.log('显示操作区域，用户有权限');
    } else {
        operationSection.style.display = 'none';
        console.log('隐藏操作区域，用户无权限或非创建人');
    }
}

// 将函数添加到全局作用域
window.initStandardApprovalFlow = initStandardApprovalFlow;
window.getApprovalFlowInstance = getApprovalFlowInstance;
window.submitStandardApproval = submitStandardApproval;
window.loadApprovalFlow = loadApprovalFlow;
window.autoShowApprovalUI = autoShowApprovalUI;
window.getCSRFToken = getCSRFToken;
window.setGlobalCSRFToken = setGlobalCSRFToken;
window.showRecallConfirmModal = showRecallConfirmModal;
window.executeRecallApproval = executeRecallApproval;
window.confirmResubmitApproval = confirmResubmitApproval;
window.executeResubmitApproval = executeResubmitApproval;
window.updateOperationSection = updateOperationSection;
window.updateOperationSectionVisibility = updateOperationSectionVisibility;

// 调试信息
console.log('approval_flow_utils.js 已加载，全局函数已定义:', {
    showRecallConfirmModal: typeof window.showRecallConfirmModal,
    confirmResubmitApproval: typeof window.confirmResubmitApproval,
    executeRecallApproval: typeof window.executeRecallApproval,
    executeResubmitApproval: typeof window.executeResubmitApproval
});