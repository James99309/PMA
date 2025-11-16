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
                    <td colspan="6" class="text-center text-muted">
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
}
