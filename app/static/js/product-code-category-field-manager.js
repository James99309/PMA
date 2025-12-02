/**
 * 分类级编码字段管理器
 * 管理分类级通用规格字段的增删改查操作（模态框模式）
 * 这些字段将被分类下的所有子分类继承
 */
class ProductCodeCategoryFieldManager {
    constructor(categoryId) {
        this.categoryId = categoryId;
        this.currentMode = null;  // 'add' or 'edit'
        this.currentFieldId = null;
        this.currentSearchKeyword = '';  // 当前搜索关键词
        this.allAvailableSpecs = [];     // 所有可用规格（未过滤）
        this.searchBoxInitialized = false; // 搜索框是否已初始化
        this.selectedSpecs = new Set();  // 已选中的规格名称

        // 初始化事件监听
        this.initEventListeners();
    }

    /**
     * 初始化事件监听器
     */
    initEventListeners() {
        // 纳入编码复选框变化时，自动勾选必填项
        // 注意：「允许报价配置」已下沉到子分类级别管理，分类级不再控制
        const useInCodeCheckbox = document.getElementById('fieldUseInCode');
        const requiredCheckbox = document.getElementById('fieldRequired');

        if (useInCodeCheckbox && requiredCheckbox) {
            useInCodeCheckbox.addEventListener('change', function() {
                if (this.checked) {
                    requiredCheckbox.checked = true;
                }
                // 「允许报价配置」已下沉到子分类级别，不再在分类级控制显示/隐藏
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
     * 过滤并渲染规格选项（复选框列表 + 徽章）
     */
    filterAndRenderSpecs() {
        const listContainer = document.getElementById('fieldNameList');
        const badgesContainer = document.getElementById('selectedSpecsBadges');
        if (!listContainer) return;

        // 渲染已选择的徽章
        this.renderSelectedBadges();

        // 过滤规格列表
        let filteredSpecs = this.allAvailableSpecs;
        if (this.currentSearchKeyword) {
            const keyword = this.currentSearchKeyword.toLowerCase();
            filteredSpecs = this.allAvailableSpecs.filter(spec =>
                spec.name.toLowerCase().includes(keyword)
            );
        }

        // 清空并重新填充复选框列表
        listContainer.innerHTML = '';

        if (filteredSpecs.length === 0) {
            listContainer.innerHTML = '<div class="text-muted text-center py-2">未找到匹配的规格</div>';
        } else {
            const self = this;
            filteredSpecs.forEach((spec, index) => {
                const div = document.createElement('div');
                div.className = 'form-check';

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'form-check-input';
                checkbox.id = `spec_${index}`;
                checkbox.value = spec.name;
                checkbox.checked = this.selectedSpecs.has(spec.name);

                // 监听复选框变化
                checkbox.addEventListener('change', function() {
                    if (this.checked) {
                        self.selectedSpecs.add(spec.name);
                    } else {
                        self.selectedSpecs.delete(spec.name);
                    }
                    self.renderSelectedBadges();
                });

                const label = document.createElement('label');
                label.className = 'form-check-label';
                label.htmlFor = `spec_${index}`;
                label.textContent = spec.unit ? `${spec.name} (${spec.unit})` : spec.name;

                div.appendChild(checkbox);
                div.appendChild(label);
                listContainer.appendChild(div);
            });
        }

        // 更新搜索提示
        const hint = document.getElementById('fieldSpecSearchHint');
        const count = document.getElementById('fieldSpecMatchCount');
        if (hint && count && this.currentSearchKeyword) {
            count.textContent = filteredSpecs.length;
            hint.style.display = 'block';
        } else if (hint) {
            hint.style.display = 'none';
        }
    }

    /**
     * 渲染已选择的规格徽章
     */
    renderSelectedBadges() {
        const badgesContainer = document.getElementById('selectedSpecsBadges');
        if (!badgesContainer) return;

        badgesContainer.innerHTML = '';

        if (this.selectedSpecs.size === 0) {
            badgesContainer.innerHTML = '<small class="text-muted">未选择任何规格</small>';
            return;
        }

        const self = this;
        this.selectedSpecs.forEach(specName => {
            const badge = document.createElement('span');
            badge.className = 'badge bg-primary me-1 mb-1';
            badge.style.cursor = 'pointer';
            badge.innerHTML = `${specName} <i class="fas fa-times ms-1"></i>`;
            badge.title = '点击移除';

            badge.addEventListener('click', function() {
                self.selectedSpecs.delete(specName);
                self.renderSelectedBadges();
                // 同步更新复选框状态
                const listContainer = document.getElementById('fieldNameList');
                if (listContainer) {
                    const checkbox = listContainer.querySelector(`input[value="${specName}"]`);
                    if (checkbox) checkbox.checked = false;
                }
            });

            badgesContainer.appendChild(badge);
        });
    }

    /**
     * 获取已选中的规格名称列表
     */
    getSelectedSpecNames() {
        return Array.from(this.selectedSpecs);
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
        const title = mode === 'add' ? '添加通用规格' : '编辑通用规格';
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
            // 使用分类级API获取可用规格
            const url = `/product-code/api/category-fields/available-specs/${this.categoryId}` +
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
            const response = await fetch(`/product-code/api/category-fields/${fieldId}`);
            const result = await response.json();

            if (!result.success) {
                throw new Error(result.message || '加载字段数据失败');
            }

            const field = result.data;

            // 填充表单
            document.getElementById('fieldId').value = field.id;
            document.getElementById('fieldRequired').checked = field.is_required;
            document.getElementById('fieldUseInCode').checked = field.use_in_code;

            // 「允许报价配置」已下沉到子分类级别管理，分类级不再显示/设置

            // 设置选中的规格（编辑时只有一个）
            this.selectedSpecs.clear();
            this.selectedSpecs.add(field.name);

            // 更新显示
            this.filterAndRenderSpecs();

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

        // 清空选中的规格
        this.selectedSpecs.clear();

        // 移除验证样式
        const form = document.getElementById('fieldForm');
        form.classList.remove('was-validated');

        // 清除复选框选中状态
        const listContainer = document.getElementById('fieldNameList');
        if (listContainer) {
            listContainer.classList.remove('is-invalid', 'border-danger');
            const checkboxes = listContainer.querySelectorAll('input[type="checkbox"]');
            checkboxes.forEach(cb => cb.checked = false);
        }

        const errorDiv = document.getElementById('fieldNameError');
        if (errorDiv) errorDiv.style.display = 'none';

        // 「允许报价配置」已下沉到子分类级别管理，分类级不再重置

        // 更新徽章显示
        this.renderSelectedBadges();
    }

    /**
     * 验证表单（复选框列表）
     * @returns {boolean} 验证是否通过
     */
    validateForm() {
        const selectedNames = this.getSelectedSpecNames();
        const listContainer = document.getElementById('fieldNameList');
        const errorDiv = document.getElementById('fieldNameError');

        if (selectedNames.length === 0) {
            if (listContainer) listContainer.classList.add('is-invalid', 'border-danger');
            if (errorDiv) errorDiv.style.display = 'block';
            this.showError('请至少选择一个规格');
            return false;
        }

        if (listContainer) listContainer.classList.remove('is-invalid', 'border-danger');
        if (errorDiv) errorDiv.style.display = 'none';
        return true;
    }

    /**
     * 保存字段（支持多选批量创建）
     */
    async saveField() {
        // 验证表单
        if (!this.validateForm()) {
            return;
        }

        const selectedNames = this.getSelectedSpecNames();
        const isRequired = document.getElementById('fieldRequired').checked;
        const useInCode = document.getElementById('fieldUseInCode').checked;
        // 「允许报价配置」已下沉到子分类级别，分类级不再发送此参数

        try {
            if (this.currentMode === 'add') {
                // 添加模式：批量创建多个字段
                let successCount = 0;
                let failedNames = [];

                for (const name of selectedNames) {
                    const data = {
                        category_id: this.categoryId,
                        name: name,
                        is_required: isRequired,
                        use_in_code: useInCode
                        // allow_quotation_config 已下沉到子分类级别
                    };

                    const response = await fetch('/product-code/api/category-fields', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(data)
                    });

                    const result = await response.json();

                    if (result.success) {
                        successCount++;
                    } else {
                        failedNames.push(name);
                    }
                }

                if (failedNames.length > 0) {
                    this.showError(`部分规格添加失败: ${failedNames.join(', ')}`);
                }

                if (successCount > 0) {
                    closeCustomDialog('fieldModal');
                    location.reload();
                }

            } else {
                // 编辑模式：只更新单个字段
                const name = selectedNames[0];  // 编辑时只取第一个
                const data = {
                    category_id: this.categoryId,
                    name: name,
                    is_required: isRequired,
                    use_in_code: useInCode
                    // allow_quotation_config 已下沉到子分类级别
                };

                const response = await fetch(`/product-code/api/category-fields/${this.currentFieldId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.success) {
                    closeCustomDialog('fieldModal');
                    location.reload();
                } else {
                    this.showError(result.message);
                }
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
            title: '确认删除通用规格',
            message: `确定要删除通用规格"${fieldName}"吗？\n\n此操作将同时删除所有相关指标，且不可恢复。\n注意：删除后，所有继承此规格的子分类将不再显示该规格。`,
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
            const response = await fetch(`/product-code/api/category-fields/${fieldId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                // 直接刷新页面
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
let categoryFieldManager;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    const categoryIdInput = document.getElementById('category_id');
    if (categoryIdInput) {
        const categoryId = parseInt(categoryIdInput.value);
        categoryFieldManager = new ProductCodeCategoryFieldManager(categoryId);
        console.log('分类级编码字段管理器已初始化，分类ID:', categoryId);
    }
});
