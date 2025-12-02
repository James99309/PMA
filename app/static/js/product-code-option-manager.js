/**
 * 产品代码指标管理器
 * 管理产品规格指标的增删改查操作（模态框模式）
 */
class ProductCodeOptionManager {
    constructor(fieldId, fieldName, fieldUnit, allowQuotationConfig = false, isLocked = false) {
        this.fieldId = fieldId;
        this.fieldName = fieldName;
        this.fieldUnit = fieldUnit;  // 规格单位
        this.allowQuotationConfig = allowQuotationConfig;  // 是否允许报价配置（控制价格增量字段显示）
        this.isLocked = isLocked;  // 是否锁定指标值（已被产品使用）
        this.currentMode = null;  // 'add' or 'edit'
        this.currentOptionId = null;
        this.currentPriceAdjustment = 0;  // 当前价格增量（分）
    }

    /**
     * 打开模态框（统一入口）
     * @param {string} mode - 'add' 或 'edit'
     * @param {number|null} optionId - 指标ID（编辑时使用）
     * @param {number} priceAdjustment - 价格增量（分，编辑时使用）
     */
    async openModal(mode = 'add', optionId = null, priceAdjustment = 0) {
        this.currentMode = mode;
        this.currentOptionId = optionId;
        this.currentPriceAdjustment = priceAdjustment || 0;

        // 设置标题
        const title = mode === 'add' ? '添加指标' : '编辑指标';
        const modalHeader = document.querySelector('#optionModal .header-title');
        if (modalHeader) {
            const iconHtml = '<i class="fas fa-list-ul me-2"></i>';
            modalHeader.innerHTML = iconHtml + title;
        }

        // 更新单位提示
        const unitHint = document.getElementById('unitHint');
        if (this.fieldUnit) {
            unitHint.innerHTML = `<i class="fas fa-info-circle me-1"></i>单位会自动添加：<strong>${this.fieldUnit}</strong>`;
        } else {
            unitHint.textContent = '';
        }

        // 控制价格增量字段的显示
        const priceAdjustmentGroup = document.getElementById('priceAdjustmentGroup');
        if (priceAdjustmentGroup) {
            priceAdjustmentGroup.style.display = this.allowQuotationConfig ? 'block' : 'none';
        }

        // 控制指标名称输入框的锁定状态
        const optionValueInput = document.getElementById('optionValue');
        if (optionValueInput) {
            optionValueInput.disabled = this.isLocked;
            if (this.isLocked) {
                optionValueInput.title = '此指标已被产品使用，无法修改';
                optionValueInput.style.cursor = 'not-allowed';
            } else {
                optionValueInput.title = '';
                optionValueInput.style.cursor = '';
            }
        }

        try {
            if (mode === 'add') {
                this.resetForm();
            } else if (mode === 'edit') {
                await this.loadOptionData(optionId);
            }

            // 显示模态框
            showCustomDialog('optionModal');
        } catch (error) {
            console.error('打开模态框失败:', error);
            this.showError('加载数据失败，请重试');
        }
    }

    /**
     * 加载指标数据（编辑模式）
     * @param {number} optionId - 指标ID
     */
    async loadOptionData(optionId) {
        try {
            const response = await fetch(`/product-code/api/options/${optionId}`);
            const result = await response.json();

            if (!result.success) {
                throw new Error(result.message || '加载指标数据失败');
            }

            const option = result.data;

            // 填充表单
            document.getElementById('optionId').value = option.id;
            document.getElementById('optionValue').value = option.value;

            // 填充价格增量（如果允许报价配置）
            if (this.allowQuotationConfig) {
                const priceAdjustmentInput = document.getElementById('optionPriceAdjustment');
                if (priceAdjustmentInput) {
                    // 从API获取的是分，转换为元显示
                    const priceAdjustmentYuan = (option.price_adjustment || this.currentPriceAdjustment || 0) / 100;
                    priceAdjustmentInput.value = priceAdjustmentYuan.toFixed(2);
                }
            }

        } catch (error) {
            console.error('加载指标数据失败:', error);
            throw error;
        }
    }

    /**
     * 重置表单（添加模式）
     */
    resetForm() {
        document.getElementById('optionForm').reset();
        document.getElementById('optionId').value = '';

        // 移除验证样式
        const form = document.getElementById('optionForm');
        form.classList.remove('was-validated');
        document.getElementById('optionValue').classList.remove('is-invalid');

        // 重置价格增量
        const priceAdjustmentInput = document.getElementById('optionPriceAdjustment');
        if (priceAdjustmentInput) {
            priceAdjustmentInput.value = '0.00';
        }
    }

    /**
     * 验证表单
     * @returns {boolean} 验证是否通过
     */
    validateForm() {
        const valueInput = document.getElementById('optionValue');
        const value = valueInput.value.trim();

        if (!value) {
            valueInput.classList.add('is-invalid');
            this.showError('请输入指标名称');
            return false;
        }

        valueInput.classList.remove('is-invalid');
        return true;
    }

    /**
     * 保存指标（统一处理创建和编辑）
     */
    async saveOption() {
        // 验证表单
        if (!this.validateForm()) {
            return;
        }

        const value = document.getElementById('optionValue').value.trim();

        const data = {
            value: value
        };

        // 如果允许报价配置，添加价格增量（元转换为分）
        if (this.allowQuotationConfig) {
            const priceAdjustmentInput = document.getElementById('optionPriceAdjustment');
            if (priceAdjustmentInput) {
                const priceYuan = parseFloat(priceAdjustmentInput.value) || 0;
                data.price_adjustment = Math.round(priceYuan * 100);  // 转换为分
            }
        }

        try {
            let url, method;
            if (this.currentMode === 'add') {
                url = `/product-code/api/fields/${this.fieldId}/options`;
                method = 'POST';
            } else {
                url = `/product-code/api/options/${this.currentOptionId}`;
                method = 'PUT';
            }

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                closeCustomDialog('optionModal');
                // 直接刷新页面显示新指标，不显示提示
                location.reload();
            } else {
                this.showError(result.message);
            }

        } catch (error) {
            console.error('保存指标失败:', error);
            this.showError('保存失败，请重试');
        }
    }

    /**
     * 确认删除指标
     * @param {number} optionId - 指标ID
     * @param {string} optionValue - 指标名称
     */
    confirmDelete(optionId, optionValue) {
        showDeleteConfirm({
            title: '确认删除指标',
            message: `确定要删除指标"${optionValue}"吗？\n\n此操作不可恢复。`,
            dialogId: 'deleteOptionDialog',
            onConfirm: () => {
                this.deleteOption(optionId);
            }
        });
    }

    /**
     * 删除指标
     * @param {number} optionId - 指标ID
     */
    async deleteOption(optionId) {
        try {
            const response = await fetch(`/product-code/api/options/${optionId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                // 直接刷新页面，不显示提示
                location.reload();
            } else {
                this.showError(result.message);
            }

        } catch (error) {
            console.error('删除指标失败:', error);
            this.showError('删除失败，请重试');
        }
    }

    /**
     * 显示错误提示
     * @param {string} message - 错误信息
     */
    showError(message) {
        if (typeof showTopNotification === 'function') {
            showTopNotification(message, 'error', 5000);
        } else {
            alert(message);
        }
    }

    /**
     * 转义HTML特殊字符
     * @param {string} text - 需要转义的文本
     * @returns {string} 转义后的文本
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 全局变量，用于在页面中调用
let optionManager;

/**
 * 打开指标管理模态框的全局函数
 * @param {number} fieldId - 规格字段ID
 * @param {string} fieldName - 规格名称
 * @param {string} fieldUnit - 规格单位
 * @param {string} mode - 模式：'add' 或 'edit'（默认 'add'）
 * @param {number|null} optionId - 指标ID（编辑模式时使用）
 * @param {boolean} allowQuotationConfig - 是否允许报价配置（控制价格增量字段显示）
 * @param {number} priceAdjustment - 当前价格增量（分，编辑模式时使用）
 * @param {boolean} isLocked - 是否锁定指标值（已被产品使用，只允许修改价格）
 */
window.openOptionModal = function(fieldId, fieldName, fieldUnit, mode = 'add', optionId = null, allowQuotationConfig = false, priceAdjustment = 0, isLocked = false) {
    // 初始化管理器
    optionManager = new ProductCodeOptionManager(fieldId, fieldName, fieldUnit || '', allowQuotationConfig, isLocked);

    // 打开模态框（支持添加和编辑模式）
    optionManager.openModal(mode, optionId, priceAdjustment);
};

/**
 * 删除指标的全局函数
 * @param {number} fieldId - 规格字段ID
 * @param {string} fieldName - 规格名称
 * @param {string} fieldUnit - 规格单位
 * @param {number} optionId - 指标ID
 * @param {string} optionValue - 指标名称
 */
window.deleteOption = function(fieldId, fieldName, fieldUnit, optionId, optionValue) {
    // 如果 optionManager 不存在或属于不同的字段，重新初始化
    if (!optionManager || optionManager.fieldId !== fieldId) {
        optionManager = new ProductCodeOptionManager(fieldId, fieldName, fieldUnit || '');
    }

    // 调用确认删除
    optionManager.confirmDelete(optionId, optionValue);
};
