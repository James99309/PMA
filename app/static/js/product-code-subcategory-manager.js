/**
 * 产品代码子分类（产品名称）管理器
 * 管理产品名称的增删改查操作（模态框模式）
 */
class ProductCodeSubcategoryManager {
    constructor(categoryId) {
        this.categoryId = categoryId;
        this.currentMode = null;  // 'add' or 'edit'
        this.currentSubcategoryId = null;
    }

    /**
     * 打开模态框（统一入口）
     * @param {string} mode - 'add' 或 'edit'
     * @param {number|null} subcategoryId - 子分类ID（编辑时使用）
     */
    async openModal(mode, subcategoryId = null) {
        this.currentMode = mode;
        this.currentSubcategoryId = subcategoryId;

        // 设置标题
        const title = mode === 'add' ? '添加产品名称' : '编辑产品名称';
        const modalHeader = document.querySelector('#subcategoryModal .header-title');
        if (modalHeader) {
            const iconHtml = '<i class="fas fa-plus me-2"></i>';
            modalHeader.innerHTML = iconHtml + title;
        }

        try {
            if (mode === 'add') {
                this.resetForm();
            } else if (mode === 'edit') {
                await this.loadSubcategoryData(subcategoryId);
            }

            // 显示模态框
            showCustomDialog('subcategoryModal');
        } catch (error) {
            console.error('打开模态框失败:', error);
            this.showError('加载数据失败，请重试');
        }
    }

    /**
     * 加载子分类数据（编辑模式）
     * @param {number} subcategoryId - 子分类ID
     */
    async loadSubcategoryData(subcategoryId) {
        try {
            const response = await fetch(`/product-code/api/subcategories/${subcategoryId}`);
            const result = await response.json();

            if (!result.success) {
                throw new Error(result.message || '加载产品名称数据失败');
            }

            const subcategory = result.data;

            // 填充表单
            document.getElementById('subcategoryId').value = subcategory.id;
            document.getElementById('subcategoryName').value = subcategory.name;
            document.getElementById('subcategoryCode').value = subcategory.code_letter;

        } catch (error) {
            console.error('加载产品名称数据失败:', error);
            throw error;
        }
    }

    /**
     * 重置表单（添加模式）
     */
    resetForm() {
        document.getElementById('subcategoryForm').reset();
        document.getElementById('subcategoryId').value = '';

        // 移除验证样式
        const form = document.getElementById('subcategoryForm');
        form.classList.remove('was-validated');
        document.getElementById('subcategoryName').classList.remove('is-invalid');
        document.getElementById('subcategoryCode').classList.remove('is-invalid');
    }

    /**
     * 生成唯一标识符（调用后端API）
     */
    async generateCodeLetter() {
        try {
            const response = await fetch(`/product-code/api/generate-subcategory-code/${this.categoryId}`);
            const result = await response.json();

            if (result.success) {
                document.getElementById('subcategoryCode').value = result.code;
                // 移除错误样式
                document.getElementById('subcategoryCode').classList.remove('is-invalid');
            } else {
                this.showError(result.message);
            }

        } catch (error) {
            console.error('生成标识符失败:', error);
            this.showError('生成失败，请重试');
        }
    }

    /**
     * 验证表单
     * @returns {boolean} 验证是否通过
     */
    validateForm() {
        const nameInput = document.getElementById('subcategoryName');
        const codeInput = document.getElementById('subcategoryCode');
        const name = nameInput.value.trim();
        const code = codeInput.value.trim();

        let isValid = true;

        // 验证名称
        if (!name) {
            nameInput.classList.add('is-invalid');
            this.showError('请输入产品名称');
            isValid = false;
        } else {
            nameInput.classList.remove('is-invalid');
        }

        // 验证标识符
        if (!code) {
            codeInput.classList.add('is-invalid');
            this.showError('请输入或生成标识符');
            isValid = false;
        } else if (code.length !== 1) {
            codeInput.classList.add('is-invalid');
            this.showError('标识符必须是单个字符');
            isValid = false;
        } else if (!/^[A-Z1-9]$/.test(code)) {
            codeInput.classList.add('is-invalid');
            this.showError('标识符必须是大写字母A-Z或数字1-9');
            isValid = false;
        } else {
            codeInput.classList.remove('is-invalid');
        }

        return isValid;
    }

    /**
     * 保存子分类（统一处理创建和编辑）
     */
    async saveSubcategory() {
        // 验证表单
        if (!this.validateForm()) {
            return;
        }

        const name = document.getElementById('subcategoryName').value.trim();
        const codeLetter = document.getElementById('subcategoryCode').value.trim().toUpperCase();

        const data = {
            category_id: this.categoryId,
            name: name,
            code_letter: codeLetter
        };

        try {
            let url, method;
            if (this.currentMode === 'add') {
                url = '/product-code/api/subcategories';
                method = 'POST';
            } else {
                url = `/product-code/api/subcategories/${this.currentSubcategoryId}`;
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
                closeCustomDialog('subcategoryModal');
                // 直接刷新页面，不显示提示
                location.reload();
            } else {
                this.showError(result.message);
            }

        } catch (error) {
            console.error('保存产品名称失败:', error);
            this.showError('保存失败，请重试');
        }
    }

    /**
     * 确认删除子分类
     * @param {number} subcategoryId - 子分类ID
     * @param {string} subcategoryName - 子分类名称
     */
    confirmDelete(subcategoryId, subcategoryName) {
        showDeleteConfirm({
            title: '确认删除产品名称',
            message: `确定要删除产品名称"${subcategoryName}"吗？\n\n此操作将同时删除所有相关规格和指标，且不可恢复。`,
            dialogId: 'deleteSubcategoryDialog',
            onConfirm: () => {
                this.deleteSubcategory(subcategoryId);
            }
        });
    }

    /**
     * 删除子分类
     * @param {number} subcategoryId - 子分类ID
     */
    async deleteSubcategory(subcategoryId) {
        try {
            const response = await fetch(`/product-code/api/subcategories/${subcategoryId}`, {
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
            console.error('删除产品名称失败:', error);
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
let subcategoryManager;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    const categoryIdInput = document.getElementById('categoryId');
    if (categoryIdInput) {
        const categoryId = parseInt(categoryIdInput.value);
        subcategoryManager = new ProductCodeSubcategoryManager(categoryId);
        console.log('产品代码子分类管理器已初始化，分类ID:', categoryId);
    }
});
