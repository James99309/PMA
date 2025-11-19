/**
 * 产品代码字段管理器
 * 管理产品规格字段的增删改查操作（模态框模式）
 */
class ProductCodeFieldManager {
    constructor(subcategoryId) {
        this.subcategoryId = subcategoryId;
        this.currentMode = null;  // 'add' or 'edit'
        this.currentFieldId = null;
        this.currentSearchKeyword = '';  // 当前搜索关键词
        this.allAvailableSpecs = [];     // 所有可用规格（未过滤）
        this.searchBoxInitialized = false; // 搜索框是否已初始化

        // 初始化事件监听
        this.initEventListeners();
    }

    /**
     * 初始化事件监听器
     */
    initEventListeners() {
        // 纳入编码复选框变化时，自动勾选必填项
        const useInCodeCheckbox = document.getElementById('fieldUseInCode');
        const requiredCheckbox = document.getElementById('fieldRequired');

        if (useInCodeCheckbox && requiredCheckbox) {
            useInCodeCheckbox.addEventListener('change', function() {
                if (this.checked) {
                    requiredCheckbox.checked = true;
                }
            });
        }
    }

    /**
     * 初始化搜索框（仅初始化一次）
     */
    initSearchBox() {
        if (this.searchBoxInitialized) return;

        const searchInput = document.getElementById('fieldSpecSearch');
        const clearBtn = document.getElementById('fieldSpecSearchClear');

        if (!searchInput) return;

        // 实时搜索 - input事件监听
        searchInput.addEventListener('input', (e) => {
            const keyword = e.target.value.trim();
            this.currentSearchKeyword = keyword;

            // 显示/隐藏清除按钮
            if (clearBtn) {
                clearBtn.style.display = keyword ? 'block' : 'none';
            }

            // 过滤并渲染选项
            this.filterAndRenderSpecs();
        });

        // 清除按钮点击事件
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                searchInput.value = '';
                this.currentSearchKeyword = '';
                clearBtn.style.display = 'none';
                this.filterAndRenderSpecs();
                searchInput.focus();
            });
        }

        this.searchBoxInitialized = true;
    }

    /**
     * 过滤并渲染规格选项
     */
    filterAndRenderSpecs() {
        const selectElement = document.getElementById('fieldName');
        if (!selectElement) return;

        // 过滤规格列表
        let filteredSpecs = this.allAvailableSpecs;
        if (this.currentSearchKeyword) {
            const keyword = this.currentSearchKeyword.toLowerCase();
            filteredSpecs = this.allAvailableSpecs.filter(spec =>
                spec.name.toLowerCase().includes(keyword)
            );
        }

        // 清空并重新填充选项
        selectElement.innerHTML = '<option value="">-- 请选择规格 --</option>';
        filteredSpecs.forEach(spec => {
            const option = document.createElement('option');
            option.value = spec.name;
            option.textContent = spec.unit
                ? `${spec.name} (${spec.unit})`
                : spec.name;
            selectElement.appendChild(option);
        });

        // 更新搜索提示
        const hint = document.getElementById('fieldSpecSearchHint');
        const count = document.getElementById('fieldSpecMatchCount');
        if (hint && count && this.currentSearchKeyword) {
            count.textContent = filteredSpecs.length;
            hint.style.display = 'block';
        } else if (hint) {
            hint.style.display = 'none';
        }

        // 如果没有匹配结果
        if (filteredSpecs.length === 0 && this.currentSearchKeyword) {
            selectElement.innerHTML = '<option value="">未找到匹配的规格</option>';
        }
    }

    /**
     * 打开模态框（统一入口）
     * @param {string} mode - 'add' 或 'edit'
     * @param {number|null} fieldId - 字段ID（编辑时使用）
     */
    async openModal(mode, fieldId = null) {
        this.currentMode = mode;
        this.currentFieldId = fieldId;

        // 重置搜索状态
        this.resetSearchBox();

        // 设置标题（更新模态框头部的标题文本）
        const title = mode === 'add' ? '添加规格' : '编辑规格';
        const modalHeader = document.querySelector('#fieldModal .header-title');
        if (modalHeader) {
            const iconHtml = '<i class="fas fa-plus me-2"></i>';
            modalHeader.innerHTML = iconHtml + title;
        }

        try {
            // 加载可用规格列表
            await this.loadAvailableSpecs(fieldId);

            if (mode === 'add') {
                this.resetForm();
            } else if (mode === 'edit') {
                await this.loadFieldData(fieldId);
            }

            // 显示模态框
            showCustomDialog('fieldModal');
        } catch (error) {
            console.error('打开模态框失败:', error);
            this.showError('加载数据失败，请重试');
        }
    }

    /**
     * 重置搜索框状态
     */
    resetSearchBox() {
        const searchInput = document.getElementById('fieldSpecSearch');
        const clearBtn = document.getElementById('fieldSpecSearchClear');
        const hint = document.getElementById('fieldSpecSearchHint');

        if (searchInput) {
            searchInput.value = '';
        }
        if (clearBtn) {
            clearBtn.style.display = 'none';
        }
        if (hint) {
            hint.style.display = 'none';
        }

        this.currentSearchKeyword = '';
    }

    /**
     * 加载可用规格列表（从字典过滤重复）
     * @param {number|null} excludeFieldId - 排除的字段ID（编辑时使用）
     */
    async loadAvailableSpecs(excludeFieldId = null) {
        try {
            const url = `/product-code/api/fields/available-specs/${this.subcategoryId}` +
                (excludeFieldId ? `?exclude_field_id=${excludeFieldId}` : '');

            const response = await fetch(url);
            const result = await response.json();

            if (!result.success) {
                throw new Error(result.message || '加载规格列表失败');
            }

            // 保存完整的规格列表
            this.allAvailableSpecs = result.data;

            // 初始化搜索框（仅首次）
            this.initSearchBox();

            // 过滤并渲染选项
            this.filterAndRenderSpecs();

        } catch (error) {
            console.error('加载可用规格失败:', error);
            throw error;
        }
    }

    /**
     * 加载字段数据（编辑模式）
     * @param {number} fieldId - 字段ID
     */
    async loadFieldData(fieldId) {
        try {
            const response = await fetch(`/product-code/api/fields/${fieldId}`);
            const result = await response.json();

            if (!result.success) {
                throw new Error(result.message || '加载字段数据失败');
            }

            const field = result.data;

            // 填充表单
            document.getElementById('fieldId').value = field.id;
            document.getElementById('fieldName').value = field.name;
            document.getElementById('fieldRequired').checked = field.is_required;
            document.getElementById('fieldUseInCode').checked = field.use_in_code;

        } catch (error) {
            console.error('加载字段数据失败:', error);
            throw error;
        }
    }

    /**
     * 重置表单（添加模式）
     */
    resetForm() {
        document.getElementById('fieldForm').reset();
        document.getElementById('fieldId').value = '';

        // 移除验证样式
        const form = document.getElementById('fieldForm');
        form.classList.remove('was-validated');
        document.getElementById('fieldName').classList.remove('is-invalid');
    }

    /**
     * 验证表单
     * @returns {boolean} 验证是否通过
     */
    validateForm() {
        const nameSelect = document.getElementById('fieldName');
        const name = nameSelect.value.trim();

        if (!name) {
            nameSelect.classList.add('is-invalid');
            this.showError('请选择规格名称');
            return false;
        }

        nameSelect.classList.remove('is-invalid');
        return true;
    }

    /**
     * 保存字段（统一处理创建和编辑）
     */
    async saveField() {
        // 验证表单
        if (!this.validateForm()) {
            return;
        }

        const name = document.getElementById('fieldName').value.trim();
        const isRequired = document.getElementById('fieldRequired').checked;
        const useInCode = document.getElementById('fieldUseInCode').checked;

        const data = {
            subcategory_id: this.subcategoryId,
            name: name,
            is_required: isRequired,
            use_in_code: useInCode
        };

        try {
            let url, method;
            if (this.currentMode === 'add') {
                url = '/product-code/api/fields';
                method = 'POST';
            } else {
                url = `/product-code/api/fields/${this.currentFieldId}`;
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
                closeCustomDialog('fieldModal');
                // 直接刷新页面，不显示提示
                location.reload();
            } else {
                this.showError(result.message);
            }

        } catch (error) {
            console.error('保存字段失败:', error);
            this.showError('保存失败，请重试');
        }
    }

    /**
     * 确认删除字段
     * @param {number} fieldId - 字段ID
     * @param {string} fieldName - 字段名称
     */
    confirmDelete(fieldId, fieldName) {
        showDeleteConfirm({
            title: '确认删除规格',
            message: `确定要删除规格"${fieldName}"吗？\n\n此操作将同时删除所有相关指标，且不可恢复。`,
            dialogId: 'deleteFieldDialog',
            onConfirm: () => {
                this.deleteField(fieldId);
            }
        });
    }

    /**
     * 删除字段
     * @param {number} fieldId - 字段ID
     */
    async deleteField(fieldId) {
        try {
            const response = await fetch(`/product-code/api/fields/${fieldId}`, {
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
            console.error('删除字段失败:', error);
            this.showError('删除失败，请重试');
        }
    }

    /**
     * 显示成功提示
     * @param {string} message - 提示信息
     */
    showSuccess(message) {
        if (typeof showTopNotification === 'function') {
            showTopNotification(message, 'success', 3000);
        } else {
            alert(message);
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
let fieldManager;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    const subcategoryIdInput = document.getElementById('subcategory_id');
    if (subcategoryIdInput) {
        const subcategoryId = parseInt(subcategoryIdInput.value);
        fieldManager = new ProductCodeFieldManager(subcategoryId);
        console.log('产品代码字段管理器已初始化，子分类ID:', subcategoryId);
    }
});
