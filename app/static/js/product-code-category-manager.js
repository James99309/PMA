/**
 * 产品代码分类管理器
 * 管理产品分类的增删改查操作（模态框模式）
 */
class ProductCodeCategoryManager {
    constructor() {
        this.currentMode = null;  // 'add' or 'edit'
        this.currentCategoryId = null;
    }

    /**
     * 打开模态框（统一入口）
     * @param {string} mode - 'add' 或 'edit'
     * @param {number|null} categoryId - 分类ID（编辑时使用）
     */
    async openModal(mode, categoryId = null) {
        this.currentMode = mode;
        this.currentCategoryId = categoryId;

        // 设置标题
        const title = mode === 'add' ? '添加分类' : '编辑分类';
        const modalHeader = document.querySelector('#categoryModal .header-title');
        if (modalHeader) {
            const iconHtml = '<i class="fas fa-plus me-2"></i>';
            modalHeader.innerHTML = iconHtml + title;
        }

        try {
            if (mode === 'add') {
                this.resetForm();
            } else if (mode === 'edit') {
                await this.loadCategoryData(categoryId);
            }

            // 显示模态框
            showCustomDialog('categoryModal');
        } catch (error) {
            console.error('打开模态框失败:', error);
            this.showError('加载数据失败，请重试');
        }
    }

    /**
     * 加载分类数据（编辑模式）
     * @param {number} categoryId - 分类ID
     */
    async loadCategoryData(categoryId) {
        try {
            const response = await fetch(`/product-code/api/categories/${categoryId}`);
            const result = await response.json();

            if (!result.success) {
                throw new Error(result.message || '加载分类数据失败');
            }

            const category = result.data;

            // 填充表单
            document.getElementById('categoryId').value = category.id;
            document.getElementById('categoryName').value = category.name;
            document.getElementById('categoryCode').value = category.code_letter;
            document.getElementById('categoryDescription').value = category.description;

        } catch (error) {
            console.error('加载分类数据失败:', error);
            throw error;
        }
    }

    /**
     * 重置表单（添加模式）
     */
    resetForm() {
        document.getElementById('categoryForm').reset();
        document.getElementById('categoryId').value = '';

        // 移除验证样式
        const form = document.getElementById('categoryForm');
        form.classList.remove('was-validated');
        document.getElementById('categoryName').classList.remove('is-invalid');
        document.getElementById('categoryCode').classList.remove('is-invalid');
    }

    /**
     * 生成唯一标识符（调用后端API）
     */
    async generateCodeLetter() {
        try {
            const response = await fetch('/product-code/api/generate-category-code');
            const result = await response.json();

            if (result.success) {
                document.getElementById('categoryCode').value = result.code;
                // 移除错误样式
                document.getElementById('categoryCode').classList.remove('is-invalid');
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
        const nameInput = document.getElementById('categoryName');
        const codeInput = document.getElementById('categoryCode');
        const name = nameInput.value.trim();
        const code = codeInput.value.trim();

        let isValid = true;

        // 验证名称
        if (!name) {
            nameInput.classList.add('is-invalid');
            this.showError('请输入分类名称');
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
        } else if (!/^[A-Z]$/.test(code)) {
            codeInput.classList.add('is-invalid');
            this.showError('标识符必须是大写字母A-Z');
            isValid = false;
        } else {
            codeInput.classList.remove('is-invalid');
        }

        return isValid;
    }

    /**
     * 保存分类（统一处理创建和编辑）
     */
    async saveCategory() {
        // 验证表单
        if (!this.validateForm()) {
            return;
        }

        const name = document.getElementById('categoryName').value.trim();
        const codeLetter = document.getElementById('categoryCode').value.trim().toUpperCase();
        const description = document.getElementById('categoryDescription').value.trim();

        const data = {
            name: name,
            code_letter: codeLetter,
            description: description
        };

        try {
            let url, method;
            if (this.currentMode === 'add') {
                url = '/product-code/api/categories';
                method = 'POST';
            } else {
                url = `/product-code/api/categories/${this.currentCategoryId}`;
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
                closeCustomDialog('categoryModal');
                // 直接刷新页面，不显示提示
                location.reload();
            } else {
                this.showError(result.message);
            }

        } catch (error) {
            console.error('保存分类失败:', error);
            this.showError('保存失败，请重试');
        }
    }

    /**
     * 确认删除分类
     * @param {number} categoryId - 分类ID
     * @param {string} categoryName - 分类名称
     */
    confirmDelete(categoryId, categoryName) {
        showDeleteConfirm({
            title: '确认删除分类',
            message: `确定要删除分类"${categoryName}"吗？\n\n此操作将同时删除所有相关子分类、规格和指标，且不可恢复。`,
            dialogId: 'deleteCategoryDialog',
            onConfirm: () => {
                this.deleteCategory(categoryId);
            }
        });
    }

    /**
     * 删除分类
     * @param {number} categoryId - 分类ID
     */
    async deleteCategory(categoryId) {
        try {
            const response = await fetch(`/product-code/api/categories/${categoryId}`, {
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
            console.error('删除分类失败:', error);
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
let categoryManager;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    categoryManager = new ProductCodeCategoryManager();
    console.log('产品代码分类管理器已初始化');
});
