/**
 * 规格字典管理器
 * 管理规格字典的增删改查操作
 */
class SpecDictManager {
    constructor() {
        this.currentEditId = null;
        this.specList = [];
        this.currentSearchKeyword = ''; // 当前搜索关键词
        this.sortableInitialized = false; // 拖拽排序是否已初始化
        this.expandedSpecs = new Set(); // 已展开的规格ID集合
        this.optionsCache = {}; // 指标缓存
        this.currentEditOptionId = null; // 当前编辑的指标ID
        this.currentOptionSpecId = null; // 当前操作的规格ID

        // 初始化时加载数据
        this.loadSpecList();
        // 初始化搜索框
        this.initSearchBox();
    }

    /**
     * 加载规格列表
     */
    async loadSpecList() {
        try {
            const response = await fetch('/api/spec-dictionary');
            const result = await response.json();

            if (result.success) {
                this.specList = result.data;
                this.renderTable();
                this.updateCount();
            } else {
                this.showError(result.message || '加载规格列表失败');
            }
        } catch (error) {
            console.error('加载规格列表错误:', error);
            this.showError('加载规格列表失败，请刷新页面重试');
        }
    }

    /**
     * 初始化搜索框事件
     */
    initSearchBox() {
        const searchInput = document.getElementById('specDictSearch');
        const clearBtn = document.getElementById('specDictSearchClear');

        if (!searchInput) return;

        // 实时搜索
        searchInput.addEventListener('input', (e) => {
            const keyword = e.target.value.trim();
            this.currentSearchKeyword = keyword;

            // 显示/隐藏清除按钮
            if (clearBtn) {
                clearBtn.style.display = keyword ? 'block' : 'none';
            }

            this.renderTable();
        });

        // 清除按钮
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                searchInput.value = '';
                this.currentSearchKeyword = '';
                clearBtn.style.display = 'none';
                this.renderTable();
                searchInput.focus();
            });
        }
    }

    /**
     * 渲染表格
     */
    renderTable() {
        const tbody = document.getElementById('specDictList');

        // 过滤数据
        let filteredList = this.specList;
        if (this.currentSearchKeyword) {
            const keyword = this.currentSearchKeyword.toLowerCase();
            filteredList = this.specList.filter(spec => {
                const matchName = spec.name.toLowerCase().includes(keyword);
                const matchUnit = spec.unit && spec.unit.toLowerCase().includes(keyword);
                return matchName || matchUnit;
            });
        }

        // 如果没有数据显示
        if (filteredList.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted">
                        <i class="fas fa-search me-2"></i>
                        ${this.currentSearchKeyword ? '未找到匹配的规格' : '暂无规格数据'}
                    </td>
                </tr>
            `;
            this.updateCount(0);
            return;
        }

        let html = '';
        filteredList.forEach((spec, index) => {
            const rowClass = spec.is_active ? '' : 'spec-disabled-row table-secondary';
            const statusBadge = spec.is_active
                ? '<span class="badge bg-success">● 启用</span>'
                : '<span class="badge bg-secondary">○ 停用</span>';

            const createdAt = spec.created_at
                ? new Date(spec.created_at).toLocaleString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                })
                : '-';

            // 指标数量和展开按钮
            const optionCount = spec.option_count || 0;
            const isExpanded = this.expandedSpecs.has(spec.id);
            const expandIcon = isExpanded ? 'fa-chevron-down' : 'fa-chevron-right';
            const expandTitle = isExpanded ? '收起指标' : '展开指标';

            html += `
                <tr class="${rowClass}" data-id="${spec.id}">
                    <td>
                        <i class="fas fa-grip-vertical drag-handle text-muted me-2"
                           title="拖拽排序"
                           style="cursor: move;"></i>
                        ${index + 1}
                    </td>
                    <td><strong>${this.escapeHtml(spec.name)}</strong></td>
                    <td class="text-muted">${spec.unit ? this.escapeHtml(spec.unit) : '-'}</td>
                    <td>${statusBadge}</td>
                    <td class="text-center">
                        <button class="btn btn-sm ${optionCount > 0 ? 'btn-outline-info' : 'btn-outline-secondary'}"
                                onclick="specDictManager.toggleOptions(${spec.id})"
                                title="${expandTitle}"
                                id="toggleBtn-${spec.id}">
                            <i class="fas ${expandIcon} me-1" id="expandIcon-${spec.id}"></i>
                            <span class="badge ${optionCount > 0 ? 'bg-info' : 'bg-secondary'}">${optionCount}</span>
                        </button>
                    </td>
                    <td class="small text-muted">${createdAt}</td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-outline-primary me-1"
                                onclick="specDictManager.showEditForm(${spec.id})"
                                title="编辑">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger"
                                onclick="specDictManager.confirmDelete(${spec.id}, '${this.escapeHtml(spec.name)}')"
                                title="删除">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;

            // 如果已展开，添加指标子表格行
            if (isExpanded) {
                html += this.renderOptionsRow(spec.id);
            }
        });

        tbody.innerHTML = html;
        this.updateCount(filteredList.length);

        // 初始化拖拽排序（仅首次）
        this.initSortable();
    }

    /**
     * 更新统计数量
     */
    updateCount(filteredCount = null) {
        const countElement = document.getElementById('specCount');
        if (!countElement) return;

        const totalCount = this.specList.length;
        const displayCount = filteredCount !== null ? filteredCount : totalCount;

        if (this.currentSearchKeyword && filteredCount !== null && filteredCount < totalCount) {
            // 有搜索关键词且结果少于总数，显示筛选信息
            countElement.textContent = displayCount;
            countElement.parentElement.innerHTML = `共 <span id="specCount">${displayCount}</span> 条记录（已筛选，总计 ${totalCount} 条）`;
        } else {
            // 无搜索或显示全部
            countElement.textContent = totalCount;
        }
    }

    /**
     * 显示添加表单
     */
    showAddForm() {
        this.currentEditId = null;
        document.getElementById('formTitle').textContent = '添加规格';
        document.getElementById('specForm').reset();
        document.getElementById('specId').value = '';
        document.getElementById('specActive').checked = true;
        document.getElementById('specFormCard').style.display = 'block';

        // 移除验证样式
        const form = document.getElementById('specForm');
        form.classList.remove('was-validated');
        document.getElementById('specName').classList.remove('is-invalid');
    }

    /**
     * 显示编辑表单
     */
    showEditForm(specId) {
        const spec = this.specList.find(s => s.id === specId);
        if (!spec) {
            this.showError('规格不存在');
            return;
        }

        this.currentEditId = specId;
        document.getElementById('formTitle').textContent = '编辑规格';
        document.getElementById('specId').value = spec.id;
        document.getElementById('specName').value = spec.name;
        document.getElementById('specUnit').value = spec.unit || '';
        document.getElementById('specActive').checked = spec.is_active;
        document.getElementById('specFormCard').style.display = 'block';

        // 移除验证样式
        const form = document.getElementById('specForm');
        form.classList.remove('was-validated');
        document.getElementById('specName').classList.remove('is-invalid');

        // 滚动到表单
        document.getElementById('specFormCard').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    /**
     * 隐藏表单
     */
    hideForm() {
        document.getElementById('specFormCard').style.display = 'none';
        this.currentEditId = null;
        document.getElementById('specForm').reset();
    }

    /**
     * 验证表单
     */
    validateForm() {
        const nameInput = document.getElementById('specName');
        const name = nameInput.value.trim();

        if (!name) {
            nameInput.classList.add('is-invalid');
            return false;
        }

        // 检查名称唯一性（排除当前编辑的规格）
        const duplicate = this.specList.find(s =>
            s.name === name && s.id !== this.currentEditId
        );

        if (duplicate) {
            nameInput.classList.add('is-invalid');
            const feedback = nameInput.nextElementSibling.nextElementSibling; // .invalid-feedback
            feedback.textContent = `规格名称"${name}"已存在`;
            return false;
        }

        nameInput.classList.remove('is-invalid');
        return true;
    }

    /**
     * 保存规格
     */
    async saveSpec() {
        // 验证表单
        if (!this.validateForm()) {
            return;
        }

        const name = document.getElementById('specName').value.trim();
        const unit = document.getElementById('specUnit').value.trim();
        const isActive = document.getElementById('specActive').checked;

        const data = {
            name: name,
            unit: unit || null,
            is_active: isActive
        };

        try {
            let url, method;
            if (this.currentEditId) {
                // 编辑模式
                url = `/api/spec-dictionary/${this.currentEditId}`;
                method = 'PUT';
            } else {
                // 新增模式
                url = '/api/spec-dictionary';
                method = 'POST';
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
                this.showSuccess(result.message);
                this.hideForm();
                await this.loadSpecList(); // 重新加载列表
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            console.error('保存规格错误:', error);
            this.showError('保存失败，请重试');
        }
    }

    /**
     * 确认删除
     */
    confirmDelete(specId, specName) {
        const spec = this.specList.find(s => s.id === specId);
        if (!spec) {
            this.showError('规格不存在');
            return;
        }

        showDeleteConfirm({
            title: '确认删除规格',
            message: `确定要删除规格"${specName}"吗？\n\n此操作不可恢复。`,
            dialogId: 'deleteSpecDialog',
            onConfirm: () => {
                this.deleteSpec(specId);
            }
        });
    }

    /**
     * 删除规格
     */
    async deleteSpec(specId) {
        try {
            const response = await fetch(`/api/spec-dictionary/${specId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message);
                await this.loadSpecList(); // 重新加载列表
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            console.error('删除规格错误:', error);
            this.showError('删除失败，请重试');
        }
    }

    /**
     * 切换启用/停用状态
     */
    async toggleSpec(specId) {
        try {
            const response = await fetch(`/api/spec-dictionary/${specId}/toggle`, {
                method: 'PUT'
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message);
                await this.loadSpecList(); // 重新加载列表
            } else {
                this.showError(result.message);
            }
        } catch (error) {
            console.error('切换状态错误:', error);
            this.showError('操作失败，请重试');
        }
    }

    /**
     * 显示成功提示
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
     */
    showError(message) {
        if (typeof showTopNotification === 'function') {
            showTopNotification(message, 'error', 5000);
        } else {
            alert(message);
        }
    }

    /**
     * 初始化拖拽排序功能
     */
    initSortable() {
        // 检查是否已经初始化
        if (this.sortableInitialized) return;

        // 检查sortable-list.js是否已加载
        if (typeof initSortableList !== 'function') {
            console.warn('sortable-list.js 未加载，无法启用拖拽排序');
            return;
        }

        // 初始化拖拽排序
        initSortableList('specDictList', '/api/spec-dictionary/update-order', {
            handle: '.drag-handle',
            animation: 150,
            onSuccess: () => {
                console.log('规格字典排序已保存');
                // 重新加载数据以确保顺序正确
                this.loadSpecList();
            },
            onError: (error) => {
                console.error('保存排序失败:', error);
                this.showError('保存排序失败，页面将自动刷新');
            }
        });

        this.sortableInitialized = true;
    }

    /**
     * 转义HTML特殊字符
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ============================================================================
    // 指标管理方法
    // ============================================================================

    /**
     * 展开/收起指标列表
     */
    async toggleOptions(specId) {
        if (this.expandedSpecs.has(specId)) {
            // 收起
            this.expandedSpecs.delete(specId);
            this.renderTable();
        } else {
            // 展开 - 先加载数据
            await this.loadOptions(specId);
            this.expandedSpecs.add(specId);
            this.renderTable();
        }
    }

    /**
     * 加载指标列表
     */
    async loadOptions(specId) {
        try {
            const response = await fetch(`/api/spec-dictionary/${specId}/options`);
            const result = await response.json();

            if (result.success) {
                this.optionsCache[specId] = result.data;
            } else {
                this.showError(result.message || '加载指标失败');
            }
        } catch (error) {
            console.error('加载指标错误:', error);
            this.showError('加载指标失败');
        }
    }

    /**
     * 渲染指标子表格行
     */
    renderOptionsRow(specId) {
        const options = this.optionsCache[specId] || [];
        const spec = this.specList.find(s => s.id === specId);

        let optionsHtml = '';
        if (options.length === 0) {
            optionsHtml = `
                <tr class="text-center text-muted">
                    <td colspan="4">暂无指标，点击下方添加</td>
                </tr>
            `;
        } else {
            options.forEach(opt => {
                const statusBadge = opt.is_active
                    ? '<span class="badge bg-success">启用</span>'
                    : '<span class="badge bg-secondary">停用</span>';

                optionsHtml += `
                    <tr data-option-id="${opt.id}">
                        <td>
                            <strong>${this.escapeHtml(opt.value)}</strong>
                            ${opt.value_en ? `<br><small class="text-muted">${this.escapeHtml(opt.value_en)}</small>` : ''}
                        </td>
                        <td class="text-center"><code class="fs-6">${this.escapeHtml(opt.code)}</code></td>
                        <td class="text-center">${statusBadge}</td>
                        <td class="text-center">
                            <button class="btn btn-sm btn-outline-primary me-1"
                                    onclick="specDictManager.showEditOptionForm(${specId}, ${opt.id})"
                                    title="编辑">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-warning me-1"
                                    onclick="specDictManager.toggleOption(${opt.id}, ${specId})"
                                    title="${opt.is_active ? '停用' : '启用'}">
                                <i class="fas ${opt.is_active ? 'fa-ban' : 'fa-check'}"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger"
                                    onclick="specDictManager.confirmDeleteOption(${opt.id}, '${this.escapeHtml(opt.value)}', ${specId})"
                                    title="删除">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `;
            });
        }

        return `
            <tr class="options-row" data-parent-id="${specId}">
                <td colspan="7" class="p-0">
                    <div class="bg-light border-top border-bottom p-3">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <strong class="text-muted">
                                <i class="fas fa-list me-1"></i>
                                ${spec ? this.escapeHtml(spec.name) : ''} 的指标列表
                            </strong>
                            <button class="btn btn-sm btn-success"
                                    onclick="specDictManager.showAddOptionForm(${specId})">
                                <i class="fas fa-plus me-1"></i>添加指标
                            </button>
                        </div>
                        <table class="table table-sm table-bordered mb-0 bg-white">
                            <thead class="table-light">
                                <tr>
                                    <th style="width: 40%">指标值</th>
                                    <th style="width: 15%" class="text-center">编码</th>
                                    <th style="width: 15%" class="text-center">状态</th>
                                    <th style="width: 30%" class="text-center">操作</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${optionsHtml}
                            </tbody>
                        </table>
                        <!-- 添加指标表单（默认隐藏）-->
                        <div id="addOptionForm-${specId}" class="mt-3" style="display: none;">
                            <div class="card">
                                <div class="card-body py-2">
                                    <div class="row g-2 align-items-end">
                                        <div class="col-md-5">
                                            <label class="form-label small">指标值</label>
                                            <input type="text" class="form-control form-control-sm"
                                                   id="newOptionValue-${specId}"
                                                   placeholder="输入指标值（编码自动生成）">
                                        </div>
                                        <div class="col-md-4">
                                            <label class="form-label small">描述（可选）</label>
                                            <input type="text" class="form-control form-control-sm"
                                                   id="newOptionDesc-${specId}"
                                                   placeholder="可选描述">
                                        </div>
                                        <div class="col-md-3">
                                            <button class="btn btn-sm btn-primary me-1"
                                                    onclick="specDictManager.saveOption(${specId})">
                                                <i class="fas fa-check me-1"></i>保存
                                            </button>
                                            <button class="btn btn-sm btn-secondary"
                                                    onclick="specDictManager.hideAddOptionForm(${specId})">
                                                取消
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <!-- 编辑指标表单（默认隐藏）-->
                        <div id="editOptionForm-${specId}" class="mt-3" style="display: none;">
                            <div class="card">
                                <div class="card-body py-2">
                                    <input type="hidden" id="editOptionId-${specId}">
                                    <div class="row g-2 align-items-end">
                                        <div class="col-md-3">
                                            <label class="form-label small">指标值</label>
                                            <input type="text" class="form-control form-control-sm"
                                                   id="editOptionValue-${specId}">
                                        </div>
                                        <div class="col-md-3">
                                            <label class="form-label small">英文值</label>
                                            <input type="text" class="form-control form-control-sm"
                                                   id="editOptionValueEn-${specId}"
                                                   placeholder="English">
                                        </div>
                                        <div class="col-md-1">
                                            <label class="form-label small">编码</label>
                                            <input type="text" class="form-control form-control-sm"
                                                   id="editOptionCode-${specId}"
                                                   maxlength="1">
                                        </div>
                                        <div class="col-md-2">
                                            <label class="form-label small">描述</label>
                                            <input type="text" class="form-control form-control-sm"
                                                   id="editOptionDesc-${specId}">
                                        </div>
                                        <div class="col-md-3">
                                            <button class="btn btn-sm btn-primary me-1"
                                                    onclick="specDictManager.updateOption(${specId})">
                                                <i class="fas fa-check me-1"></i>保存
                                            </button>
                                            <button class="btn btn-sm btn-secondary"
                                                    onclick="specDictManager.hideEditOptionForm(${specId})">
                                                取消
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
        `;
    }

    /**
     * 显示添加指标表单
     */
    showAddOptionForm(specId) {
        this.hideEditOptionForm(specId);
        document.getElementById(`addOptionForm-${specId}`).style.display = 'block';
        document.getElementById(`newOptionValue-${specId}`).focus();
    }

    /**
     * 隐藏添加指标表单
     */
    hideAddOptionForm(specId) {
        const form = document.getElementById(`addOptionForm-${specId}`);
        if (form) {
            form.style.display = 'none';
            document.getElementById(`newOptionValue-${specId}`).value = '';
            document.getElementById(`newOptionDesc-${specId}`).value = '';
        }
    }

    /**
     * 显示编辑指标表单
     */
    showEditOptionForm(specId, optionId) {
        this.hideAddOptionForm(specId);
        const options = this.optionsCache[specId] || [];
        const option = options.find(o => o.id === optionId);
        if (!option) return;

        document.getElementById(`editOptionId-${specId}`).value = optionId;
        document.getElementById(`editOptionValue-${specId}`).value = option.value;
        document.getElementById(`editOptionValueEn-${specId}`).value = option.value_en || '';
        document.getElementById(`editOptionCode-${specId}`).value = option.code;
        document.getElementById(`editOptionDesc-${specId}`).value = option.description || '';
        document.getElementById(`editOptionForm-${specId}`).style.display = 'block';
    }

    /**
     * 隐藏编辑指标表单
     */
    hideEditOptionForm(specId) {
        const form = document.getElementById(`editOptionForm-${specId}`);
        if (form) {
            form.style.display = 'none';
        }
    }

    /**
     * 保存新指标
     */
    async saveOption(specId) {
        const value = document.getElementById(`newOptionValue-${specId}`).value.trim();
        const description = document.getElementById(`newOptionDesc-${specId}`).value.trim();

        if (!value) {
            this.showError('请输入指标值');
            return;
        }

        try {
            const response = await fetch(`/api/spec-dictionary/${specId}/options`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ value, description })
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message || '指标添加成功');
                this.hideAddOptionForm(specId);
                // 刷新指标列表和规格列表
                await this.loadOptions(specId);
                await this.loadSpecList();
            } else {
                this.showError(result.message || '添加失败');
            }
        } catch (error) {
            console.error('添加指标错误:', error);
            this.showError('添加失败');
        }
    }

    /**
     * 更新指标
     */
    async updateOption(specId) {
        const optionId = document.getElementById(`editOptionId-${specId}`).value;
        const value = document.getElementById(`editOptionValue-${specId}`).value.trim();
        const value_en = document.getElementById(`editOptionValueEn-${specId}`).value.trim();
        const code = document.getElementById(`editOptionCode-${specId}`).value.trim();
        const description = document.getElementById(`editOptionDesc-${specId}`).value.trim();

        if (!value) {
            this.showError('请输入指标值');
            return;
        }

        if (!code) {
            this.showError('请输入编码');
            return;
        }

        try {
            const response = await fetch(`/api/spec-dictionary/options/${optionId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ value, value_en, code, description })
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message || '指标更新成功');
                this.hideEditOptionForm(specId);
                await this.loadOptions(specId);
                this.renderTable();
            } else {
                this.showError(result.message || '更新失败');
            }
        } catch (error) {
            console.error('更新指标错误:', error);
            this.showError('更新失败');
        }
    }

    /**
     * 切换指标状态
     */
    async toggleOption(optionId, specId) {
        try {
            const response = await fetch(`/api/spec-dictionary/options/${optionId}/toggle`, {
                method: 'PUT'
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message || '状态已更新');
                await this.loadOptions(specId);
                this.renderTable();
            } else {
                this.showError(result.message || '操作失败');
            }
        } catch (error) {
            console.error('切换状态错误:', error);
            this.showError('操作失败');
        }
    }

    /**
     * 确认删除指标
     */
    confirmDeleteOption(optionId, optionValue, specId) {
        showDeleteConfirm({
            title: '确认删除指标',
            message: `确定要删除指标"${optionValue}"吗？\n\n此操作不可恢复。`,
            dialogId: 'deleteOptionDialog',
            onConfirm: () => {
                this.deleteOption(optionId, specId);
            }
        });
    }

    /**
     * 删除指标
     */
    async deleteOption(optionId, specId) {
        try {
            const response = await fetch(`/api/spec-dictionary/options/${optionId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message || '指标已删除');
                await this.loadOptions(specId);
                await this.loadSpecList();
            } else {
                this.showError(result.message || '删除失败');
            }
        } catch (error) {
            console.error('删除指标错误:', error);
            this.showError('删除失败');
        }
    }
}
