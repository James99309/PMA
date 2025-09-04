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
    console.log('审批提交成功，将重新加载页面以更新状态');
    
    // 显示成功消息
    if (typeof showSuccessMessage === 'function') {
        showSuccessMessage('审批提交成功');
    }
    
    // 延迟刷新页面，让用户看到成功提示
    setTimeout(() => {
        window.location.reload();
    }, 1500);
});

/**
 * 事件监听器：审批处理成功
 */
document.addEventListener('approval_approved', function(event) {
    console.log('审批处理成功，将重新加载页面以更新状态');
    
    // 显示成功消息
    const message = event.detail.action === 'approve' ? '审批已通过' : '审批已拒绝';
    if (typeof showSuccessMessage === 'function') {
        showSuccessMessage(message);
    }
    
    // 延迟刷新页面，让用户看到成功提示
    setTimeout(() => {
        window.location.reload();
    }, 1500);
});

/**
 * 审批成功后更新页面状态信息
 */
async function updatePageStatusAfterApproval(eventDetail, retryCount = 0) {
    const maxRetries = 2; // 最多重试2次
    console.log(`开始更新页面状态信息... (尝试 ${retryCount + 1}/${maxRetries + 1})`);
    
    try {
        // 直接从事件详情获取对象信息，无需URL解析
        const objectType = eventDetail.objectType;
        const objectId = eventDetail.objectId;
        
        if (!objectType || !objectId) {
            console.log('事件详情中缺少对象类型或ID，跳过状态更新');
            return;
        }
        
        console.log(`从事件获取对象信息 - 类型: ${objectType}, ID: ${objectId}`);
        
        // 动态构建API路径，支持所有对象类型
        let apiPath;
        if (objectType === 'pricing_order') {
            apiPath = `/pricing_order/api/${objectId}/status`;
        } else {
            // 通用路径格式，适用于其他对象类型
            apiPath = `/${objectType}/api/${objectId}/status`;
        }
        
        // 调用API获取最新的对象状态
        const response = await fetch(apiPath);
        
        if (!response.ok) {
            console.warn('获取最新状态失败，尝试页面刷新方案');
            // 如果API不存在，使用页面刷新作为备选方案
            if (confirm('审批已完成，是否刷新页面以显示最新状态？')) {
                window.location.reload();
            }
            return;
        }
        
        const data = await response.json();
        console.log('获取到最新状态:', data);
        
        if (data.success) {
            // 更新状态徽章
            updateStatusBadge(data.status);
            // 更新锁定状态徽章
            updateLockStatusBadge(data.is_locked);
            // 更新操作按钮可见性
            updateActionButtonsVisibility(data);
            
            // 审批完成后将通过页面刷新来更新状态，无需前端权限同步
            
            console.log(`页面状态更新完成 - 类型: ${objectType}, 状态: ${data.status}, 锁定: ${data.is_locked}`);
            
            // 🔥 特殊处理：如果是支付完成，显示特殊提示
            if (data.status === 'paid') {
                console.log('检测到支付完成，报销单已支付');
                if (typeof showSuccessMessage === 'function') {
                    showSuccessMessage('支付完成！报销单已成功支付。');
                }
            }
        } else {
            console.warn('状态API返回失败:', data.message);
            // 🔥 新增：如果API返回失败且还有重试机会，尝试重试
            if (retryCount < maxRetries) {
                console.log(`状态更新失败，将在1.5秒后重试 (${retryCount + 1}/${maxRetries})`);
                setTimeout(() => {
                    updatePageStatusAfterApproval(eventDetail, retryCount + 1);
                }, 1500);
            } else {
                console.error('状态更新失败，已达到最大重试次数');
                if (confirm('审批已完成，但状态更新失败。是否刷新页面以显示最新状态？')) {
                    window.location.reload();
                }
            }
        }
        
    } catch (error) {
        console.error('更新页面状态时出错:', error);
        // 发生错误时，如果还有重试机会就重试，否则提供页面刷新选项
        if (retryCount < maxRetries) {
            console.log(`发生错误，将在1.5秒后重试 (${retryCount + 1}/${maxRetries})`);
            setTimeout(() => {
                updatePageStatusAfterApproval(eventDetail, retryCount + 1);
            }, 1500);
        } else {
            console.error('状态更新失败，已达到最大重试次数');
            if (confirm('审批已完成，但状态更新失败。是否刷新页面以显示最新状态？')) {
                window.location.reload();
            }
        }
    }
}

/**
 * 更新状态徽章
 */
function updateStatusBadge(status) {
    // 状态映射
    const statusMap = {
        'draft': { text: '草稿', class: 'bg-secondary' },
        'pending': { text: '审批中', class: 'bg-warning' },
        'approved': { text: '已通过', class: 'bg-success' },
        'rejected': { text: '已拒绝', class: 'bg-danger' },
        'recalled': { text: '已召回', class: 'bg-info' },
        'paid': { text: '已支付', class: 'bg-primary' }
    };
    
    const statusInfo = statusMap[status] || { text: status, class: 'bg-secondary' };
    
    // 查找状态徽章元素并更新
    const statusBadges = document.querySelectorAll('[class*="badge"][class*="bg-"]');
    statusBadges.forEach(badge => {
        const parent = badge.closest('tr');
        if (parent && parent.textContent.includes('状态')) {
            badge.className = `badge ${statusInfo.class}`;
            badge.textContent = statusInfo.text;
            console.log(`状态徽章已更新为: ${statusInfo.text}`);
        }
    });
}

/**
 * 更新锁定状态徽章
 */
function updateLockStatusBadge(isLocked) {
    const lockInfo = isLocked ? 
        { text: '已锁定', class: 'bg-danger' } : 
        { text: '未锁定', class: 'bg-success' };
    
    // 查找锁定状态徽章元素并更新
    const statusBadges = document.querySelectorAll('[class*="badge"][class*="bg-"]');
    statusBadges.forEach(badge => {
        const parent = badge.closest('tr');
        if (parent && parent.textContent.includes('锁定状态')) {
            badge.className = `badge ${lockInfo.class}`;
            badge.textContent = lockInfo.text;
            console.log(`锁定状态徽章已更新为: ${lockInfo.text}`);
        }
    });
}

/**
 * 更新操作按钮可见性
 */
function updateActionButtonsVisibility(statusData) {
    // 根据新状态和锁定状态显示/隐藏相应的操作按钮
    // 这部分逻辑可以根据具体需求进一步完善
    console.log('更新操作按钮可见性 (待完善)');
}

// updatePricingOrderPermissions 相关函数已移除
// 改为使用页面刷新机制来更新状态，更加简洁可靠

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
        // 检查是否有召回的审批历史
        const flow = window.approvalFlowInstance;
        const hasRecalledHistory = flow && flow.approvalData && flow.approvalData.status === 'recalled';
        
        if (hasRecalledHistory) {
            // 有召回历史的情况
            infoHtml = `
                <div class="alert alert-warning border-warning">
                    <i class="fas fa-undo me-2"></i>
                    <strong>审批流程已召回</strong>
                    <p class="mb-1 mt-2">上次提交的审批流程已被召回，您可以重新提交审批。</p>
                    <small class="text-muted">重新提交后将开始新的审批流程。</small>
                </div>
            `;
            buttonsHtml = `
                <button type="button" class="btn btn-success operation-btn-submit" onclick="submitStandardApproval('expense', ${window.currentExpenseId || 'null'})">
                    <i class="fas fa-redo me-1"></i>重新提交审批
                </button>
            `;
        } else {
            // 普通草稿状态
            infoHtml = `
                <p class="text-muted mb-2">创建完成，可以提交审批流程。</p>
                <small class="text-muted">提交后将进入审批流程，无法直接修改。</small>
            `;
            buttonsHtml = `
                <button type="button" class="btn btn-success operation-btn-submit" onclick="submitStandardApproval('expense', ${window.currentExpenseId || 'null'})">
                    <i class="fas fa-paper-plane me-1"></i>提交审批
                </button>
            `;
        }
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
 * V2审批系统使用模态框，不需要页面操作区域
 */
function updateOperationSectionVisibility() {
    // V2审批系统检测：通过审批流程容器或特定标识判断
    const isV2System = document.querySelector('.approval-flow-container') || 
                      document.querySelector('[data-approval-version="v2"]') ||
                      (window.approvalFlowInstance && window.approvalFlowInstance.version === 'v2');
    
    if (isV2System) {
        console.log('V2审批系统：使用模态框审批，跳过操作区域查找');
        return;
    }
    
    const operationSection = document.getElementById('approvalOperationSection');
    if (!operationSection) {
        console.log('V1审批系统未找到操作区域，可能页面不需要此区域');
        return;
    }
    
    const flow = window.approvalFlowInstance;
    
    // 获取对象状态（从页面中或流程数据中）
    let objectStatus = 'unknown';
    if (flow && flow.approvalData && flow.approvalData.status) {
        objectStatus = flow.approvalData.status;
    }
    
    // 如果没有审批流程数据，检查页面中的状态信息
    if (!flow || !flow.approvalData || objectStatus === 'unknown') {
        // 尝试从页面元素获取状态信息
        const statusElements = document.querySelectorAll('[class*="badge"]');
        for (const element of statusElements) {
            const text = element.textContent.trim();
            if (text === '草稿') {
                objectStatus = 'draft';
                break;
            } else if (text === '审批中') {
                objectStatus = 'pending';
                break;
            } else if (text === '已通过') {
                objectStatus = 'approved';
                break;
            } else if (text === '已拒绝') {
                objectStatus = 'rejected';
                break;
            } else if (text === '已召回') {
                objectStatus = 'recalled';
                break;
            }
        }
        console.log('从页面元素获取状态:', objectStatus);
    }
    
    // 检查用户是否为创建人（从模板中获取的信息）
    const creatorCheckElements = document.querySelectorAll('[data-is-creator]');
    let isCreatorFromTemplate = false;
    if (creatorCheckElements.length > 0) {
        isCreatorFromTemplate = creatorCheckElements[0].getAttribute('data-is-creator') === 'true';
    }
    
    // 权限判断逻辑
    let shouldShow = false;
    
    if (flow && flow.approvalData) {
        // 有审批数据时，使用API返回的权限信息
        const data = flow.approvalData;
        const hasAnyPermission = data.can_submit || data.can_recall || data.can_resubmit;
        const isCreator = data.is_creator;
        shouldShow = isCreator && hasAnyPermission;
        console.log('使用API权限数据:', { isCreator, hasAnyPermission, shouldShow });
    } else {
        // 没有审批数据时，对于草稿状态默认显示给创建人
        if (objectStatus === 'draft') {
            shouldShow = isCreatorFromTemplate;
            console.log('草稿状态，使用模板权限信息:', { isCreatorFromTemplate, shouldShow });
        } else {
            shouldShow = false;
            console.log('非草稿状态且无API数据，隐藏操作区域');
        }
    }
    
    if (shouldShow) {
        operationSection.style.display = 'block';
        console.log('显示操作区域');
    } else {
        operationSection.style.display = 'none';
        console.log('隐藏操作区域');
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