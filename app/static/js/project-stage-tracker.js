/**
 * 项目阶段跟踪器
 * 继承自通用阶段跟踪器，处理项目特定的业务逻辑
 */

class ProjectStageTracker extends StageTracker {
    constructor(options) {
        // 设置项目特定的默认值
        const projectOptions = {
            ...options,
            objectType: 'project'
        };
        
        super(projectOptions);
        
        // 项目特有属性
        this.projectId = options.projectId || options.objectId;
    }

    /**
     * 显示阶段推进确认对话框（项目特定逻辑）
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
            title: this.i18nTexts?.confirmAdvanceTitle || '确认阶段推进',
            message: this.i18nTexts?.confirmAdvanceMessage?.replace('{current}', currentStageName).replace('{next}', nextStageName) || 
                     `您确定要将项目从「${currentStageName}」阶段推进到「${nextStageName}」阶段吗？`,
            detail: this.i18nTexts?.operationNote || '此操作将更新项目的当前阶段状态，推进后将无法直接回退。',
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
     * 更新阶段（项目特定的API调用）
     */
    updateStage(targetStage) {
        // 显示加载指示器
        const loadingOverlay = this.createLoadingOverlay();
        document.body.appendChild(loadingOverlay);
        
        // 发送请求到项目专用的阶段更新API
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
            this.removeLoadingOverlay(loadingOverlay);
            
            if (data.success) {
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
                if (typeof window.showTopNotification === 'function') {
                    window.showTopNotification('更新阶段失败: ' + errorMsg, 'error', 5000);
                } else {
                    alert('更新阶段失败: ' + errorMsg);
                }
            }
        })
        .catch(error => {
            this.removeLoadingOverlay(loadingOverlay);
            
            if (error instanceof BlockedProgressError) {
                // 处理阻塞的进度推进（批价流程检查失败）
                console.log('处理阻塞的进度推进，错误数据:', error.data);
                
                if (error.data.pricing_flow) {
                    // 显示批价流程相关的提示
                    this.handlePricingFlowPrompt(error.data.pricing_flow);
                } else {
                    // 显示一般性的阻塞信息
                    if (typeof window.showTopNotification === 'function') {
                        window.showTopNotification(error.data.message || '阶段推进被阻止', 'warning', 4000);
                    } else {
                        alert(error.data.message || '阶段推进被阻止');
                    }
                }
            } else {
                console.error('更新阶段错误:', error);
                if (typeof window.showTopNotification === 'function') {
                    window.showTopNotification('更新阶段时发生错误: ' + error.message, 'error', 5000);
                } else {
                    alert('更新阶段时发生错误: ' + error.message);
                }
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
            this.showPricingFlowDialog({
                type: 'success',
                title: '签约流程 - 批价单创建',
                message: `项目已成功推进到签约阶段！\n\n发现已审核报价单：${pricingFlow.quotation_number}\n${pricingFlow.message}`,
                confirmText: '创建批价单',
                cancelText: '稍后处理',
                onConfirm: () => {
                    this.createPricingOrder(pricingFlow.quotation_id);
                }
            });
        } else if (pricingFlow.action_required === 'view_pricing_order') {
            this.showPricingFlowDialog({
                type: 'info',
                title: '签约流程 - 批价单状态',
                message: `项目已成功推进到签约阶段！\n\n已存在批价单：${pricingFlow.pricing_order_number}\n状态：${this.getPricingOrderStatusLabel(pricingFlow.pricing_order_status)}`,
                confirmText: '查看批价单',
                cancelText: '关闭',
                onConfirm: () => {
                    window.location.href = `/pricing_order/${pricingFlow.pricing_order_id}`;
                }
            });
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
        // 保留原有的复杂模态框实现作为降级选项
        // 这里可以保留原有的复杂实现代码
        if (typeof window.showTopNotification === 'function') {
            window.showTopNotification(pricingFlow.message || '批价流程处理', 'info', 4000);
        } else {
            alert(pricingFlow.message || '批价流程处理');
        }
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
                if (typeof window.showTopNotification === 'function') {
                    window.showTopNotification('创建批价单失败：' + (data.message || '未知错误'), 'error', 5000);
                } else {
                    alert('创建批价单失败：' + (data.message || '未知错误'));
                }
                this.refreshPage();
            }
        })
        .catch(error => {
            // 移除加载指示器
            const loading = document.getElementById('createPricingOrderLoading');
            if (loading) loading.remove();

            console.error('创建批价单错误:', error);
            if (typeof window.showTopNotification === 'function') {
                window.showTopNotification('创建批价单时发生错误：' + error.message, 'error', 5000);
            } else {
                alert('创建批价单时发生错误：' + error.message);
            }
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
}

// 向后兼容：保持原有的ProjectStageProgress类名
class ProjectStageProgress extends ProjectStageTracker {
    constructor(options) {
        super(options);
    }
}