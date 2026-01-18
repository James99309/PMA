/**
 * Tailwind 产品分类管理器
 * 管理产品分类、子分类和规格字段的 CRUD 操作
 */
const CategoryManager = {
    // [LegacySpecSystem] 功能标志
    legacySpecSystemEnabled: window.config && window.config.LEGACY_SPEC_SYSTEM_ENABLED !== undefined
        ? window.config.LEGACY_SPEC_SYSTEM_ENABLED
        : true,  // 默认启用

    // 状态
    state: {
        selectedCategoryId: null,
        selectedSubcategoryId: null,
        categories: [],
        subcategories: [],
        fields: [],
        categoryFields: [],  // 分类级规格字段列表
        deleteType: null,  // 'category', 'subcategory', 'field'
        deleteId: null,
        fieldFormMode: 'subcategory'  // 'category' 或 'subcategory'
    },

    // 通用字段拖拽排序实例
    fieldsSortable: null,

    // API 端点
    API: {
        categories: '/product-code/api/categories',
        subcategories: '/product-code/api/subcategories',
        fields: '/product-code/api/fields',
        generateCategoryCode: '/product-code/api/generate-category-code',
        categorySubcategories: (id) => `/product-code/api/category/${id}/subcategories`,
        subcategoryFields: (id) => `/product-code/api/subcategory/${id}/fields`,
        availableSpecs: (id) => `/product-code/api/fields/available-specs/${id}`,
        // 分类级字段相关
        categoryFields: (id) => `/product-code/api/category/${id}/fields`,
        categoryAvailableSpecs: (id) => `/product-code/api/category-fields/available-specs/${id}`,
        // 排序 API（复用后端已有 API）
        updateCategoryFieldsOrder: (id) => `/product-code/api/category/${id}/update-fields-order`,
        updateSubcategoryFieldsOrder: (id) => `/product-code/api/subcategory/${id}/update-fields-order`
    },

    /**
     * 初始化
     */
    init() {
        // [LegacySpecSystem] 日志输出初始化状态
        console.log('[LegacySpec] CategoryManager initialized', {
            legacySpecSystemEnabled: this.legacySpecSystemEnabled,
            timestamp: new Date().toISOString()
        });

        this.loadCategories();
    },

    // ========== 分类管理 ==========

    /**
     * 加载分类列表
     */
    async loadCategories() {
        const loading = document.getElementById('categoryLoading');
        const empty = document.getElementById('categoryEmpty');
        const list = document.getElementById('categoryList');
        const count = document.getElementById('categoryCount');

        loading.classList.remove('hidden');
        empty.classList.add('hidden');
        list.innerHTML = '';

        try {
            const response = await fetch(this.API.categories);
            const result = await response.json();

            loading.classList.add('hidden');

            if (result.success && result.data) {
                this.state.categories = result.data.map(cat => ({
                    id: cat.id,
                    name: cat.name,
                    codeLetter: cat.code_letter,
                    description: cat.description || '',
                    isUsed: cat.is_used,
                    subcategoryCount: cat.subcategory_count || 0
                }));

                count.textContent = this.state.categories.length;

                if (this.state.categories.length === 0) {
                    empty.classList.remove('hidden');
                } else {
                    this.renderCategoryList();
                }
            } else {
                empty.classList.remove('hidden');
                this.showToast(result.message || '加载失败', 'error');
            }

        } catch (error) {
            console.error('加载分类失败:', error);
            loading.classList.add('hidden');
            empty.classList.remove('hidden');
        }
    },

    /**
     * 渲染分类列表
     * @param {Array} categories - 可选，要渲染的分类列表（用于搜索过滤）
     */
    renderCategoryList(categories = null) {
        const list = document.getElementById('categoryList');
        const dataToRender = categories || this.state.categories;

        list.innerHTML = dataToRender.map(cat => `
            <li class="category-item cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-800 ${this.state.selectedCategoryId === cat.id ? 'item-selected' : ''}"
                data-id="${cat.id}"
                onclick="CategoryManager.selectCategory(${cat.id})">
                <div class="px-4 py-2.5 flex items-center justify-between">
                    <div class="flex items-center gap-2 flex-1 min-w-0">
                        <span class="font-mono text-xs px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300">${cat.codeLetter}</span>
                        <span class="text-sm font-medium text-slate-900 dark:text-white truncate">${cat.name}</span>
                    </div>
                    <div class="flex items-center gap-1 ml-2 flex-shrink-0">
                        ${!cat.isUsed ? `
                            <button type="button" onclick="event.stopPropagation(); CategoryManager.showEditCategoryModal(${cat.id})"
                                    class="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded transition-colors"
                                    title="编辑">
                                <span class="material-symbols-outlined text-lg">edit</span>
                            </button>
                            <button type="button" onclick="event.stopPropagation(); CategoryManager.confirmDeleteCategory(${cat.id}, '${cat.name}')"
                                    class="p-1.5 text-slate-400 hover:text-red-500 rounded transition-colors"
                                    title="删除">
                                <span class="material-symbols-outlined text-lg">delete</span>
                            </button>
                        ` : `
                            <button type="button" onclick="event.stopPropagation(); CategoryManager.showPartialEditCategoryModal(${cat.id})"
                                    class="p-1.5 text-slate-400 hover:text-blue-500 rounded transition-colors"
                                    title="编辑英文名称">
                                <span class="material-symbols-outlined text-lg">edit_note</span>
                            </button>
                            <span class="p-1.5 text-slate-300 dark:text-slate-600" title="已使用">
                                <span class="material-symbols-outlined text-lg">lock</span>
                            </span>
                        `}
                    </div>
                </div>
            </li>
        `).join('');
    },

    /**
     * 搜索过滤分类
     * @param {string} searchValue - 搜索关键词
     */
    filterCategories(searchValue) {
        const keyword = searchValue.trim().toLowerCase();
        const empty = document.getElementById('categoryEmpty');

        if (!keyword) {
            // 清空搜索时显示全部
            empty.classList.add('hidden');
            if (this.state.categories.length === 0) {
                empty.classList.remove('hidden');
            } else {
                this.renderCategoryList();
            }
            return;
        }

        // 按名称或标识符过滤
        const filtered = this.state.categories.filter(cat =>
            cat.name.toLowerCase().includes(keyword) ||
            cat.codeLetter.toLowerCase().includes(keyword)
        );

        if (filtered.length === 0) {
            document.getElementById('categoryList').innerHTML = '';
            empty.classList.remove('hidden');
        } else {
            empty.classList.add('hidden');
            this.renderCategoryList(filtered);
        }
    },

    /**
     * 选择分类
     */
    selectCategory(categoryId) {
        this.state.selectedCategoryId = categoryId;
        this.state.selectedSubcategoryId = null;

        // 更新选中状态
        document.querySelectorAll('.category-item').forEach(item => {
            item.classList.toggle('item-selected', parseInt(item.dataset.id) === categoryId);
        });

        // 更新标题
        const category = this.state.categories.find(c => c.id === categoryId);
        document.getElementById('subcategoryTitle').textContent = category ? `${category.name} - 子分类` : '子分类';

        // 启用添加子分类按钮
        document.getElementById('addSubcategoryBtn').disabled = false;

        // 启用编辑分类规格按钮
        const editCategoryFieldsBtn = document.getElementById('editCategoryFieldsBtn');
        if (editCategoryFieldsBtn) {
            editCategoryFieldsBtn.disabled = false;
        }

        // 加载子分类
        this.loadSubcategories(categoryId);

        // 重置规格字段区域
        this.resetFieldArea();
    },

    /**
     * 显示添加分类模态框
     */
    showAddCategoryModal() {
        document.getElementById('categoryFormId').value = '';
        document.getElementById('categoryFormName').value = '';
        document.getElementById('categoryFormNameEn').value = '';
        document.getElementById('categoryFormCode').value = '';
        document.getElementById('categoryFormDesc').value = '';
        document.getElementById('categoryFormModal-title').textContent = '添加分类';
        document.getElementById('categoryFormModal').classList.remove('hidden');
    },

    /**
     * 显示编辑分类模态框
     */
    async showEditCategoryModal(categoryId) {
        try {
            const response = await fetch(`${this.API.categories}/${categoryId}`);
            const result = await response.json();

            if (result.success) {
                const data = result.data;
                document.getElementById('categoryFormId').value = data.id;
                document.getElementById('categoryFormName').value = data.name;
                document.getElementById('categoryFormNameEn').value = data.name_en || '';
                document.getElementById('categoryFormCode').value = data.code_letter;
                document.getElementById('categoryFormDesc').value = data.description || '';
                document.getElementById('categoryFormModal-title').textContent = '编辑分类';
                document.getElementById('categoryFormModal').classList.remove('hidden');
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('加载分类详情失败:', error);
            this.showToast('加载失败', 'error');
        }
    },

    /**
     * 隐藏分类表单
     */
    hideCategoryForm() {
        document.getElementById('categoryFormModal').classList.add('hidden');
    },

    /**
     * 生成分类标识符
     */
    async generateCategoryCode() {
        try {
            const response = await fetch(this.API.generateCategoryCode);
            const result = await response.json();

            if (result.success) {
                document.getElementById('categoryFormCode').value = result.code;
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('生成标识符失败:', error);
            this.showToast('生成失败', 'error');
        }
    },

    /**
     * 自动生成分类标识符（输入名称时触发）
     * 仅在新增模式且标识符为空时自动生成
     */
    async autoGenerateCategoryCode() {
        const codeInput = document.getElementById('categoryFormCode');
        const formId = document.getElementById('categoryFormId').value;
        const nameInput = document.getElementById('categoryFormName');

        // 编辑模式不自动生成
        if (formId) return;

        // 名称为空时不生成
        if (!nameInput.value.trim()) return;

        // 标识符已有值时不覆盖
        if (codeInput.value.trim()) return;

        try {
            const response = await fetch(this.API.generateCategoryCode);
            const result = await response.json();

            if (result.success) {
                codeInput.value = result.code;
            }
        } catch (error) {
            console.error('自动生成标识符失败:', error);
        }
    },

    /**
     * 提交分类表单
     */
    async submitCategoryForm(event) {
        event.preventDefault();

        const id = document.getElementById('categoryFormId').value;
        const data = {
            name: document.getElementById('categoryFormName').value.trim(),
            name_en: document.getElementById('categoryFormNameEn').value.trim(),
            code_letter: document.getElementById('categoryFormCode').value.trim().toUpperCase(),
            description: document.getElementById('categoryFormDesc').value.trim()
        };

        try {
            const url = id ? `${this.API.categories}/${id}` : this.API.categories;
            const method = id ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                this.hideCategoryForm();
                this.loadCategories();
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('保存分类失败:', error);
            this.showToast('保存失败', 'error');
        }

        return false;
    },

    /**
     * 确认删除分类
     */
    confirmDeleteCategory(categoryId, name) {
        this.state.deleteType = 'category';
        this.state.deleteId = categoryId;
        document.getElementById('deleteConfirmMessage').textContent = `确定要删除分类「${name}」吗？此操作无法撤销。`;
        document.getElementById('deleteConfirmModal').classList.remove('hidden');
    },

    // ========== 子分类管理 ==========

    /**
     * 加载子分类列表
     */
    async loadSubcategories(categoryId) {
        const placeholder = document.getElementById('subcategoryPlaceholder');
        const loading = document.getElementById('subcategoryLoading');
        const empty = document.getElementById('subcategoryEmpty');
        const table = document.getElementById('subcategoryTable');
        const tbody = document.getElementById('subcategoryTableBody');
        const count = document.getElementById('subcategoryCount');

        placeholder.classList.add('hidden');
        loading.classList.remove('hidden');
        empty.classList.add('hidden');
        table.classList.add('hidden');

        try {
            const response = await fetch(this.API.categorySubcategories(categoryId));
            const result = await response.json();

            loading.classList.add('hidden');

            if (result.success && result.data) {
                this.state.subcategories = result.data;
            } else {
                this.state.subcategories = [];
            }
            count.textContent = this.state.subcategories.length;

            if (this.state.subcategories.length === 0) {
                empty.classList.remove('hidden');
            } else {
                this.renderSubcategoryTable();
                table.classList.remove('hidden');
            }

        } catch (error) {
            console.error('加载子分类失败:', error);
            loading.classList.add('hidden');
            empty.classList.remove('hidden');
        }
    },

    /**
     * 渲染子分类表格
     */
    renderSubcategoryTable() {
        const tbody = document.getElementById('subcategoryTableBody');
        tbody.innerHTML = this.state.subcategories.map((sub, index) => `
            <tr class="cursor-pointer transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50 ${this.state.selectedSubcategoryId === sub.id ? 'bg-primary/5' : ''}"
                onclick="CategoryManager.selectSubcategory(${sub.id})">
                <td class="p-3 text-slate-500 dark:text-slate-400">${index + 1}</td>
                <td class="p-3">
                    <span class="font-medium text-slate-900 dark:text-white">${sub.name}</span>
                </td>
                <td class="p-3">
                    <span class="text-slate-600 dark:text-slate-400">${sub.name_en || '-'}</span>
                </td>
                <td class="p-3">
                    <span class="font-mono text-xs px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">${sub.code_letter}</span>
                </td>
                <td class="p-3">
                    ${sub.is_used ?
                        '<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400">已使用</span>' :
                        '<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">可编辑</span>'
                    }
                </td>
                <td class="p-3 text-right">
                    <div class="flex items-center justify-end gap-1">
                        ${!sub.is_used ? `
                            <button type="button" onclick="event.stopPropagation(); CategoryManager.showEditSubcategoryModal(${sub.id})"
                                    class="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded transition-colors" title="编辑">
                                <span class="material-symbols-outlined text-lg">edit</span>
                            </button>
                            <button type="button" onclick="event.stopPropagation(); CategoryManager.confirmDeleteSubcategory(${sub.id}, '${sub.name}')"
                                    class="p-1.5 text-slate-400 hover:text-red-500 rounded transition-colors" title="删除">
                                <span class="material-symbols-outlined text-lg">delete</span>
                            </button>
                        ` : `
                            <button type="button" onclick="event.stopPropagation(); CategoryManager.showPartialEditSubcategoryModal(${sub.id})"
                                    class="p-1.5 text-slate-400 hover:text-blue-500 rounded transition-colors" title="编辑英文名称">
                                <span class="material-symbols-outlined text-lg">edit_note</span>
                            </button>
                            <span class="p-1.5 text-slate-300 dark:text-slate-600" title="已使用">
                                <span class="material-symbols-outlined text-lg">lock</span>
                            </span>
                        `}
                    </div>
                </td>
            </tr>
        `).join('');
    },

    /**
     * 选择子分类
     */
    selectSubcategory(subcategoryId) {
        this.state.selectedSubcategoryId = subcategoryId;

        // 更新选中状态
        this.renderSubcategoryTable();

        // 更新标题
        const subcategory = this.state.subcategories.find(s => s.id === subcategoryId);
        document.getElementById('fieldTitle').textContent = subcategory ? `${subcategory.name} - 规格字段` : '规格字段';

        // 启用添加字段按钮
        document.getElementById('addFieldBtn').disabled = false;

        // 加载规格字段
        this.loadFields(subcategoryId);
    },

    /**
     * 显示添加子分类模态框
     */
    showAddSubcategoryModal() {
        if (!this.state.selectedCategoryId) {
            this.showToast('请先选择一个分类', 'warning');
            return;
        }
        document.getElementById('subcategoryFormId').value = '';
        document.getElementById('subcategoryFormName').value = '';
        document.getElementById('subcategoryFormNameEn').value = '';
        document.getElementById('subcategoryFormCode').value = '';
        document.getElementById('subcategoryFormModal-title').textContent = '添加子分类';
        document.getElementById('subcategoryFormModal').classList.remove('hidden');
    },

    /**
     * 显示编辑子分类模态框
     */
    async showEditSubcategoryModal(subcategoryId) {
        try {
            const response = await fetch(`${this.API.subcategories}/${subcategoryId}`);
            const result = await response.json();

            if (result.success) {
                const data = result.data;
                document.getElementById('subcategoryFormId').value = data.id;
                document.getElementById('subcategoryFormName').value = data.name;
                document.getElementById('subcategoryFormNameEn').value = data.name_en || '';
                document.getElementById('subcategoryFormCode').value = data.code_letter;
                document.getElementById('subcategoryFormModal-title').textContent = '编辑子分类';
                document.getElementById('subcategoryFormModal').classList.remove('hidden');
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('加载子分类详情失败:', error);
            this.showToast('加载失败', 'error');
        }
    },

    /**
     * 隐藏子分类表单
     */
    hideSubcategoryForm() {
        document.getElementById('subcategoryFormModal').classList.add('hidden');
    },

    /**
     * 自动生成子分类标识符（输入名称时触发）
     * 仅在新增模式且标识符为空时自动生成
     */
    autoGenerateSubcategoryCode() {
        const codeInput = document.getElementById('subcategoryFormCode');
        const formId = document.getElementById('subcategoryFormId').value;
        const nameInput = document.getElementById('subcategoryFormName');

        // 编辑模式不自动生成
        if (formId) return;

        // 名称为空时不生成
        if (!nameInput.value.trim()) return;

        // 标识符已有值时不覆盖
        if (codeInput.value.trim()) return;

        // 获取当前分类下已使用的标识符
        const used = this.state.subcategories.map(s => s.code_letter);
        const all = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789'.split('');
        const available = all.filter(c => !used.includes(c));

        if (available.length > 0) {
            codeInput.value = available[0];
        }
    },

    /**
     * 提交子分类表单
     */
    async submitSubcategoryForm(event) {
        event.preventDefault();

        const id = document.getElementById('subcategoryFormId').value;
        const data = {
            category_id: this.state.selectedCategoryId,
            name: document.getElementById('subcategoryFormName').value.trim(),
            name_en: document.getElementById('subcategoryFormNameEn').value.trim(),
            code_letter: document.getElementById('subcategoryFormCode').value.trim().toUpperCase()
        };

        try {
            const url = id ? `${this.API.subcategories}/${id}` : this.API.subcategories;
            const method = id ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                this.hideSubcategoryForm();
                this.loadSubcategories(this.state.selectedCategoryId);
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('保存子分类失败:', error);
            this.showToast('保存失败', 'error');
        }

        return false;
    },

    /**
     * 确认删除子分类
     */
    confirmDeleteSubcategory(subcategoryId, name) {
        this.state.deleteType = 'subcategory';
        this.state.deleteId = subcategoryId;
        document.getElementById('deleteConfirmMessage').textContent = `确定要删除子分类「${name}」吗？此操作无法撤销。`;
        document.getElementById('deleteConfirmModal').classList.remove('hidden');
    },

    // ========== 规格字段管理 ==========

    /**
     * 重置规格字段区域
     */
    resetFieldArea() {
        document.getElementById('fieldPlaceholder').classList.remove('hidden');
        document.getElementById('fieldLoading').classList.add('hidden');
        document.getElementById('fieldEmpty').classList.add('hidden');
        document.getElementById('fieldTable').classList.add('hidden');
        document.getElementById('fieldTitle').textContent = '规格字段';
        document.getElementById('fieldCount').textContent = '0';
        document.getElementById('addFieldBtn').disabled = true;
    },

    /**
     * 加载规格字段列表
     */
    async loadFields(subcategoryId) {
        const placeholder = document.getElementById('fieldPlaceholder');
        const loading = document.getElementById('fieldLoading');
        const empty = document.getElementById('fieldEmpty');
        const table = document.getElementById('fieldTable');
        const tbody = document.getElementById('fieldTableBody');
        const count = document.getElementById('fieldCount');

        placeholder.classList.add('hidden');
        loading.classList.remove('hidden');
        empty.classList.add('hidden');
        table.classList.add('hidden');

        try {
            const response = await fetch(this.API.subcategoryFields(subcategoryId));
            const result = await response.json();

            loading.classList.add('hidden');

            // [LegacySpecSystem] 检查是否是旧系统被禁用的错误
            if (response.status === 503 || (result.source === 'legacy_spec_system' && !result.success)) {
                console.warn('[LegacySpec] Legacy spec system is disabled, field loading skipped');
                empty.classList.remove('hidden');
                this.state.fields = [];
                count.textContent = '0';
                return;
            }

            if (result.success && result.data) {
                this.state.fields = result.data;
            } else {
                this.state.fields = [];
            }
            count.textContent = this.state.fields.length;

            if (this.state.fields.length === 0) {
                empty.classList.remove('hidden');
            } else {
                this.renderFieldTable();
                table.classList.remove('hidden');
            }

        } catch (error) {
            console.error('[LegacySpec] Error loading spec fields:', error);
            loading.classList.add('hidden');
            empty.classList.remove('hidden');
        }
    },

    /**
     * 通用规格字段表格渲染
     * @param {Object} config - 配置对象
     * @param {string} config.type - 'category' 或 'subcategory'
     * @param {string} config.tbodyId - tbody 元素 ID
     * @param {Array} config.fields - 字段数据
     * @param {boolean} config.showSourceColumn - 是否显示来源列
     * @param {boolean} config.showStatusColumn - 是否显示状态列
     * @param {boolean} config.showOptionsButton - 是否显示管理指标按钮
     * @param {boolean} config.showEditButton - 是否显示编辑按钮
     */
    renderFieldsTable(config) {
        const { type, tbodyId, fields, showSourceColumn, showStatusColumn, showOptionsButton, showEditButton } = config;
        const tbody = document.getElementById(tbodyId);

        if (!fields || fields.length === 0) {
            // 基础列：拖拽手柄 + 位置 + 名称 + 编码 + 操作 = 5列
            const colSpan = 5 + (showSourceColumn ? 1 : 0) + (showStatusColumn ? 1 : 0);
            tbody.innerHTML = `<tr><td colspan="${colSpan}" class="text-center py-8 text-slate-500 dark:text-slate-400">暂无规格字段</td></tr>`;
            return;
        }

        tbody.innerHTML = fields.map(field => {
            // 锁定行：is_used 或 (子分类且is_inherited)
            const isLocked = field.is_used || (type === 'subcategory' && field.is_inherited);

            return `
            <tr class="transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50" data-id="${field.id}" ${isLocked ? 'data-locked="true"' : ''}>
                <!-- 拖拽手柄：锁定行不显示 -->
                <td class="p-3">
                    ${!isLocked ?
                        '<span class="drag-handle cursor-move text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"><span class="material-symbols-outlined text-lg">drag_indicator</span></span>' :
                        '<span class="text-slate-300 dark:text-slate-600">—</span>'}
                </td>

                <!-- 位置 -->
                <td class="p-3 font-mono text-slate-500 dark:text-slate-400">${field.position || '-'}</td>

                <!-- 规格名称 -->
                <td class="p-3">
                    <span class="font-medium text-slate-900 dark:text-white">${field.name}</span>
                </td>

                <!-- 编码 -->
                <td class="p-3">
                    ${field.use_in_code ?
                        '<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">是</span>' :
                        '<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400">否</span>'
                    }
                </td>

                <!-- 来源列（仅子分类显示） -->
                ${showSourceColumn ? `
                    <td class="p-3">
                        ${field.is_inherited ?
                            '<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">继承</span>' :
                            '<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">自有</span>'
                        }
                    </td>
                ` : ''}

                <!-- 状态列（仅子分类显示） -->
                ${showStatusColumn ? `
                    <td class="p-3">
                        ${field.is_used ?
                            '<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400">已使用</span>' :
                            '<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">可编辑</span>'
                        }
                    </td>
                ` : ''}

                <!-- 操作列 -->
                <td class="p-3 text-right">
                    <div class="flex items-center justify-end gap-1">
                        <!-- 管理指标按钮（仅子分类显示） -->
                        ${showOptionsButton ? `
                            <button type="button" onclick="SpecOptionsModal.open('${field.name}', { mode: 'subcategory', subcategoryId: ${this.state.selectedSubcategoryId}, fieldId: ${field.id} })"
                                    class="p-1.5 text-cyan-500 hover:text-cyan-600 dark:hover:text-cyan-400 hover:bg-cyan-50 dark:hover:bg-cyan-900/20 rounded transition-colors" title="管理指标">
                                <span class="material-symbols-outlined text-lg">data_array</span>
                            </button>
                        ` : ''}

                        <!-- 编辑和删除按钮 -->
                        ${!isLocked ? `
                            ${showEditButton ? `
                                <button type="button" onclick="CategoryManager.showEditFieldModal(${field.id}, '${type}')"
                                        class="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded transition-colors" title="编辑">
                                    <span class="material-symbols-outlined text-lg">edit</span>
                                </button>
                            ` : ''}
                            <button type="button" onclick="CategoryManager.confirmDeleteField(${field.id}, '${field.name}', '${type}')"
                                    class="p-1.5 text-slate-400 hover:text-red-500 rounded transition-colors" title="删除">
                                <span class="material-symbols-outlined text-lg">delete</span>
                            </button>
                        ` : `
                            <span class="p-1.5 text-slate-300 dark:text-slate-600" title="${field.is_inherited ? '继承自分类' : '已使用'}">
                                <span class="material-symbols-outlined text-lg">lock</span>
                            </span>
                        `}
                    </div>
                </td>
            </tr>
            `;
        }).join('');
    },

    /**
     * 渲染子分类规格字段表格（调用通用函数）
     */
    renderFieldTable() {
        // 调用通用渲染函数
        this.renderFieldsTable({
            type: 'subcategory',
            tbodyId: 'fieldTableBody',
            fields: this.state.fields,
            showSourceColumn: true,
            showStatusColumn: true,
            showOptionsButton: true,
            showEditButton: true
        });

        // 初始化拖拽排序
        this.initFieldsSortable({
            tbodyId: 'fieldTableBody',
            type: 'subcategory',
            targetId: this.state.selectedSubcategoryId,
            onSuccess: () => this.loadFields(this.state.selectedSubcategoryId)
        });
    },

    /**
     * 显示添加规格字段模态框（子分类级）
     */
    async showAddFieldModal() {
        // [LegacySpecSystem] 检查旧系统是否启用
        if (!this.legacySpecSystemEnabled) {
            console.warn('[LegacySpec] Attempt to add field when legacy system is disabled');
            this.showToast('规格系统已禁用，请使用新规格模板系统', 'warning');
            return;
        }

        if (!this.state.selectedSubcategoryId) {
            this.showToast('请先选择一个子分类', 'warning');
            return;
        }

        this.state.fieldFormMode = 'subcategory';
        document.getElementById('fieldFormId').value = '';
        document.getElementById('fieldFormUseInCode').checked = true;
        document.getElementById('fieldFormRequired').checked = true;
        document.getElementById('fieldFormModal-title').textContent = '添加规格字段';

        // 加载可用规格
        await this.loadAvailableSpecs();

        document.getElementById('fieldFormModal').classList.remove('hidden');
    },

    // ========== 分类级规格管理 ==========

    /**
     * 显示分类规格管理模态框
     */
    async showCategoryFieldsModal() {
        // [LegacySpecSystem] 检查旧系统是否启用
        if (!this.legacySpecSystemEnabled) {
            console.warn('[LegacySpec] Attempt to open category fields when legacy system is disabled');
            this.showToast('规格系统已禁用，请使用新规格模板系统', 'warning');
            return;
        }

        if (!this.state.selectedCategoryId) {
            this.showToast('请先选择一个分类', 'warning');
            return;
        }

        // 更新模态框标题
        const category = this.state.categories.find(c => c.id === this.state.selectedCategoryId);
        const titleEl = document.querySelector('#categoryFieldsModal-title');
        if (titleEl) {
            titleEl.textContent = `编辑分类规格 - ${category ? category.name : ''}`;
        }

        // 显示模态框
        document.getElementById('categoryFieldsModal').classList.remove('hidden');

        // 加载分类级字段（排序在 renderCategoryFieldsTable 中初始化）
        await this.loadCategoryFields();
    },

    /**
     * 隐藏分类规格管理模态框
     */
    hideCategoryFieldsModal() {
        document.getElementById('categoryFieldsModal').classList.add('hidden');
        // 销毁拖拽实例
        if (this.fieldsSortable) {
            this.fieldsSortable.destroy();
            this.fieldsSortable = null;
        }
    },

    /**
     * 加载分类级字段列表
     */
    async loadCategoryFields() {
        const loading = document.getElementById('categoryFieldsLoading');
        const empty = document.getElementById('categoryFieldsEmpty');
        const table = document.getElementById('categoryFieldsTable');
        const count = document.getElementById('categoryFieldCount');

        loading.classList.remove('hidden');
        empty.classList.add('hidden');
        table.classList.add('hidden');

        try {
            const response = await fetch(this.API.categoryFields(this.state.selectedCategoryId));
            const result = await response.json();

            loading.classList.add('hidden');

            if (result.success && result.data) {
                this.state.categoryFields = result.data;
                count.textContent = this.state.categoryFields.length;

                if (this.state.categoryFields.length === 0) {
                    empty.classList.remove('hidden');
                } else {
                    this.renderCategoryFieldsTable();
                    table.classList.remove('hidden');
                }
            } else {
                this.state.categoryFields = [];
                count.textContent = '0';
                empty.classList.remove('hidden');
            }
        } catch (error) {
            console.error('加载分类级字段失败:', error);
            loading.classList.add('hidden');
            empty.classList.remove('hidden');
        }
    },

    /**
     * 渲染分类规格表格（调用通用函数）
     */
    renderCategoryFieldsTable() {
        // 调用通用渲染函数
        this.renderFieldsTable({
            type: 'category',
            tbodyId: 'categoryFieldsTableBody',
            fields: this.state.categoryFields,
            showSourceColumn: false,
            showStatusColumn: false,
            showOptionsButton: false,
            showEditButton: true
        });

        // 初始化拖拽排序
        this.initFieldsSortable({
            tbodyId: 'categoryFieldsTableBody',
            type: 'category',
            targetId: this.state.selectedCategoryId,
            onSuccess: () => this.loadCategoryFields()
        });
    },

    /**
     * 通用拖拽排序初始化
     * @param {Object} config - 配置对象
     * @param {string} config.tbodyId - tbody 元素 ID
     * @param {string} config.type - 'category' 或 'subcategory'
     * @param {number} config.targetId - 分类或子分类 ID
     * @param {Function} config.onSuccess - 排序成功后的回调
     */
    initFieldsSortable(config) {
        const { tbodyId, type, targetId, onSuccess } = config;
        const tbody = document.getElementById(tbodyId);
        if (!tbody) return;

        // 先销毁已有实例
        if (this.fieldsSortable) {
            this.fieldsSortable.destroy();
            this.fieldsSortable = null;
        }

        // 检查是否有 Sortable 库
        if (typeof Sortable === 'undefined') {
            console.warn('Sortable 库未加载，拖拽排序不可用');
            return;
        }

        this.fieldsSortable = new Sortable(tbody, {
            animation: 150,
            handle: '.drag-handle',
            ghostClass: 'sortable-ghost',
            chosenClass: 'sortable-chosen',
            filter: '[data-locked="true"]',  // 锁定行禁止拖拽
            onMove: (evt) => {
                // 禁止拖到锁定行的位置
                return !evt.related.hasAttribute('data-locked');
            },
            onEnd: async (evt) => {
                // 收集新顺序
                const items = Array.from(tbody.querySelectorAll('tr[data-id]')).map((row, index) => ({
                    id: parseInt(row.dataset.id),
                    order: index + 1
                }));

                // 发送更新请求
                await this.updateFieldsOrder(type, targetId, items);
                if (onSuccess) onSuccess();
            }
        });
    },

    /**
     * 通用排序更新函数
     * @param {string} type - 'category' 或 'subcategory'
     * @param {number} targetId - 分类或子分类 ID
     * @param {Array} items - 排序项 [{id, order}]
     */
    async updateFieldsOrder(type, targetId, items) {
        // 根据类型选择 API
        const url = type === 'category'
            ? this.API.updateCategoryFieldsOrder(targetId)
            : this.API.updateSubcategoryFieldsOrder(targetId);

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ items })
            });

            const result = await response.json();

            if (!result.success) {
                this.showToast(result.message || '保存排序失败', 'error');
            }
        } catch (error) {
            console.error('更新排序失败:', error);
            this.showToast('保存排序失败', 'error');
        }
    },

    /**
     * 显示添加分类规格表单（复用 fieldFormModal）
     */
    async showAddCategoryFieldForm() {
        // [LegacySpecSystem] 检查旧系统是否启用
        if (!this.legacySpecSystemEnabled) {
            console.warn('[LegacySpec] Attempt to add category field when legacy system is disabled');
            this.showToast('规格系统已禁用，请使用新规格模板系统', 'warning');
            return;
        }

        this.state.fieldFormMode = 'category';
        document.getElementById('fieldFormId').value = '';
        document.getElementById('fieldFormUseInCode').checked = true;
        document.getElementById('fieldFormRequired').checked = true;
        document.getElementById('fieldFormModal-title').textContent = '添加分类规格';

        // 加载分类级可用规格
        await this.loadAvailableSpecs();

        document.getElementById('fieldFormModal').classList.remove('hidden');
    },

    /**
     * 删除分类规格
     */
    async deleteCategoryField(fieldId, name) {
        if (!confirm(`确定要删除规格「${name}」吗？删除后该分类下所有子分类将不再继承此规格。`)) {
            return;
        }

        try {
            const response = await fetch(`${this.API.fields}/${fieldId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                this.showToast('删除成功', 'success');
                await this.loadCategoryFields();
            } else {
                this.showToast(result.message || '删除失败', 'error');
            }
        } catch (error) {
            console.error('删除分类规格失败:', error);
            this.showToast('删除失败', 'error');
        }
    },

    /**
     * 加载可用规格列表（支持分类级和子分类级）
     */
    async loadAvailableSpecs() {
        const select = document.getElementById('fieldFormName');
        select.innerHTML = '<option value="">请选择规格...</option>';

        try {
            // 根据模式选择不同的 API
            let apiUrl;
            if (this.state.fieldFormMode === 'category') {
                apiUrl = this.API.categoryAvailableSpecs(this.state.selectedCategoryId);
            } else {
                apiUrl = this.API.availableSpecs(this.state.selectedSubcategoryId);
            }

            const response = await fetch(apiUrl);
            const result = await response.json();

            if (result.success && result.data) {
                result.data.forEach(spec => {
                    const option = document.createElement('option');
                    option.value = spec.name;
                    option.textContent = spec.unit ? `${spec.name} (${spec.unit})` : spec.name;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('加载可用规格失败:', error);
        }
    },

    /**
     * 显示编辑规格字段模态框
     * @param {number} fieldId - 字段ID
     * @param {string} fieldType - 字段类型 ('category' 或 'subcategory')
     */
    async showEditFieldModal(fieldId, fieldType = 'subcategory') {
        // [LegacySpecSystem] 检查旧系统是否启用
        if (!this.legacySpecSystemEnabled) {
            console.warn('[LegacySpec] Attempt to edit field when legacy system is disabled');
            this.showToast('规格系统已禁用，请使用新规格模板系统', 'warning');
            return;
        }

        try {
            // 设置表单模式，用于提交后刷新正确的列表
            this.state.fieldFormMode = fieldType;

            const response = await fetch(`${this.API.fields}/${fieldId}`);
            const result = await response.json();

            if (result.success) {
                const data = result.data;

                // 加载可用规格（排除当前字段）
                await this.loadAvailableSpecs();

                // 添加当前字段的规格名称选项
                const select = document.getElementById('fieldFormName');
                const option = document.createElement('option');
                option.value = data.name;
                option.textContent = data.name;
                option.selected = true;
                select.appendChild(option);

                document.getElementById('fieldFormId').value = data.id;
                document.getElementById('fieldFormUseInCode').checked = data.use_in_code;
                document.getElementById('fieldFormRequired').checked = data.is_required;
                document.getElementById('fieldFormModal-title').textContent = '编辑规格字段';
                document.getElementById('fieldFormModal').classList.remove('hidden');
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('[LegacySpec] Error loading field details:', error);
            this.showToast('加载失败', 'error');
        }
    },

    /**
     * 隐藏规格字段表单
     */
    hideFieldForm() {
        document.getElementById('fieldFormModal').classList.add('hidden');
    },

    /**
     * 提交规格字段表单（支持分类级和子分类级）
     */
    async submitFieldForm(event) {
        event.preventDefault();

        const id = document.getElementById('fieldFormId').value;
        const data = {
            name: document.getElementById('fieldFormName').value,
            use_in_code: document.getElementById('fieldFormUseInCode').checked,
            is_required: document.getElementById('fieldFormRequired').checked
        };

        // 根据模式设置不同的 ID 参数
        if (this.state.fieldFormMode === 'category') {
            data.category_id = this.state.selectedCategoryId;
        } else {
            data.subcategory_id = this.state.selectedSubcategoryId;
        }

        try {
            const url = id ? `${this.API.fields}/${id}` : this.API.fields;
            const method = id ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                this.hideFieldForm();
                this.showToast(result.message, 'success');

                // 根据模式刷新不同的数据
                if (this.state.fieldFormMode === 'category') {
                    // 分类级规格添加成功后，刷新分类规格模态框
                    await this.loadCategoryFields();
                    // 同时如果当前有选中子分类，也刷新其字段列表（因为会继承）
                    if (this.state.selectedSubcategoryId) {
                        this.loadFields(this.state.selectedSubcategoryId);
                    }
                } else {
                    this.loadFields(this.state.selectedSubcategoryId);
                }
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('保存规格字段失败:', error);
            this.showToast('保存失败', 'error');
        }

        return false;
    },

    /**
     * 确认删除规格字段
     * @param {number} fieldId - 字段ID
     * @param {string} name - 字段名称
     * @param {string} fieldType - 字段类型 ('category' 或 'subcategory')
     */
    confirmDeleteField(fieldId, name, fieldType = 'subcategory') {
        // 区分分类字段和子分类字段的删除类型
        this.state.deleteType = fieldType === 'category' ? 'categoryField' : 'field';
        this.state.deleteId = fieldId;
        document.getElementById('deleteConfirmMessage').textContent = `确定要删除规格字段「${name}」吗？此操作无法撤销。`;
        document.getElementById('deleteConfirmModal').classList.remove('hidden');
    },

    // ========== 删除确认 ==========

    /**
     * 隐藏删除确认
     */
    hideDeleteConfirm() {
        document.getElementById('deleteConfirmModal').classList.add('hidden');
        this.state.deleteType = null;
        this.state.deleteId = null;
    },

    /**
     * 执行删除
     */
    async executeDelete() {
        const { deleteType, deleteId } = this.state;
        if (!deleteType || !deleteId) return;

        let url;
        switch (deleteType) {
            case 'category':
                url = `${this.API.categories}/${deleteId}`;
                break;
            case 'subcategory':
                url = `${this.API.subcategories}/${deleteId}`;
                break;
            case 'field':
            case 'categoryField':  // 分类字段和子分类字段使用相同的 API
                url = `${this.API.fields}/${deleteId}`;
                break;
        }

        try {
            const response = await fetch(url, { method: 'DELETE' });
            const result = await response.json();

            this.hideDeleteConfirm();

            if (result.success) {
                // 刷新对应列表
                switch (deleteType) {
                    case 'category':
                        this.loadCategories();
                        // 重置右侧区域
                        this.state.selectedCategoryId = null;
                        this.state.selectedSubcategoryId = null;
                        document.getElementById('subcategoryPlaceholder').classList.remove('hidden');
                        document.getElementById('subcategoryTable').classList.add('hidden');
                        document.getElementById('addSubcategoryBtn').disabled = true;
                        this.resetFieldArea();
                        break;
                    case 'subcategory':
                        this.loadSubcategories(this.state.selectedCategoryId);
                        this.resetFieldArea();
                        break;
                    case 'field':
                        this.loadFields(this.state.selectedSubcategoryId);
                        break;
                    case 'categoryField':
                        this.loadCategoryFields();  // 刷新分类级字段列表
                        break;
                }
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('删除失败:', error);
            this.showToast('删除失败', 'error');
            this.hideDeleteConfirm();
        }
    },

    // ========== 规格字典 ==========

    /**
     * 显示规格字典模态框
     */
    showSpecDictModal() {
        // [LegacySpecSystem] 检查旧规格系统是否启用
        if (!this.legacySpecSystemEnabled) {
            console.warn('[LegacySpec] Spec dictionary is disabled');
            this.showToast('规格系统已禁用，请使用新规格模板系统', 'warning');
            return;
        }

        if (typeof SpecDictionaryManager !== 'undefined') {
            SpecDictionaryManager.show();
        } else {
            this.showToast('规格字典组件未加载', 'error');
        }
    },

    // ========== 部分编辑模式（已锁定分类的英文字段编辑） ==========

    /**
     * 显示分类部分编辑模态框（仅编辑 name_en）
     */
    async showPartialEditCategoryModal(categoryId) {
        try {
            const response = await fetch(`${this.API.categories}/${categoryId}`);
            const result = await response.json();

            if (result.success) {
                const data = result.data;
                document.getElementById('categoryPartialEditId').value = data.id;
                document.getElementById('categoryPartialEditNameDisplay').textContent = data.name;
                document.getElementById('categoryPartialEditCodeDisplay').textContent = data.code_letter;
                document.getElementById('categoryPartialEditNameEn').value = data.name_en || '';
                document.getElementById('categoryPartialEditModal').classList.remove('hidden');
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('加载分类详情失败:', error);
            this.showToast('加载失败', 'error');
        }
    },

    /**
     * 隐藏分类部分编辑表单
     */
    hidePartialEditCategoryForm() {
        document.getElementById('categoryPartialEditModal').classList.add('hidden');
    },

    /**
     * 保存分类部分编辑（仅 name_en）
     */
    async savePartialCategoryForm(event) {
        event.preventDefault();

        const id = document.getElementById('categoryPartialEditId').value;
        const data = {
            name_en: document.getElementById('categoryPartialEditNameEn').value.trim()
        };

        try {
            const response = await fetch(`${this.API.categories}/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                this.hidePartialEditCategoryForm();
                this.loadCategories();
                this.showToast('英文名称保存成功', 'success');
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('保存分类失败:', error);
            this.showToast('保存失败', 'error');
        }

        return false;
    },

    /**
     * 显示子分类部分编辑模态框（仅编辑 name_en）
     */
    async showPartialEditSubcategoryModal(subcategoryId) {
        try {
            const response = await fetch(`${this.API.subcategories}/${subcategoryId}`);
            const result = await response.json();

            if (result.success) {
                const data = result.data;
                document.getElementById('subcategoryPartialEditId').value = data.id;
                document.getElementById('subcategoryPartialEditNameDisplay').textContent = data.name;
                document.getElementById('subcategoryPartialEditCodeDisplay').textContent = data.code_letter;
                document.getElementById('subcategoryPartialEditNameEn').value = data.name_en || '';
                document.getElementById('subcategoryPartialEditModal').classList.remove('hidden');
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('加载子分类详情失败:', error);
            this.showToast('加载失败', 'error');
        }
    },

    /**
     * 隐藏子分类部分编辑表单
     */
    hidePartialEditSubcategoryForm() {
        document.getElementById('subcategoryPartialEditModal').classList.add('hidden');
    },

    /**
     * 保存子分类部分编辑（仅 name_en）
     */
    async savePartialSubcategoryForm(event) {
        event.preventDefault();

        const id = document.getElementById('subcategoryPartialEditId').value;
        const data = {
            name_en: document.getElementById('subcategoryPartialEditNameEn').value.trim()
        };

        try {
            const response = await fetch(`${this.API.subcategories}/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                this.hidePartialEditSubcategoryForm();
                this.loadSubcategories(this.state.selectedCategoryId);
                this.showToast('英文名称保存成功', 'success');
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('保存子分类失败:', error);
            this.showToast('保存失败', 'error');
        }

        return false;
    },

    // ========== 工具函数 ==========

    /**
     * 显示提示消息
     */
    showToast(message, type = 'info') {
        // 使用项目中已有的 toast 系统，或创建简单提示
        if (typeof showToast === 'function') {
            showToast(message, type);
        } else if (typeof toastr !== 'undefined') {
            toastr[type](message);
        } else {
            alert(message);
        }
    }
};
