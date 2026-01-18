/**
 * 规格字典管理器
 *
 * 提供规格字典的完整CRUD功能，包括：
 * - 规格列表管理（搜索、添加、编辑、删除、状态切换）
 * - 指标管理（添加、编辑、删除、状态切换）
 * - 智能编码预览
 *
 * 使用方式：
 *   SpecDictionaryManager.show();  // 打开模态框
 *   SpecDictionaryManager.hide();  // 关闭模态框
 *
 * API端点：
 *   GET    /api/spec-dictionary              - 获取规格列表
 *   POST   /api/spec-dictionary              - 创建规格
 *   PUT    /api/spec-dictionary/:id          - 更新规格
 *   DELETE /api/spec-dictionary/:id          - 删除规格
 *   PUT    /api/spec-dictionary/:id/toggle   - 切换规格状态
 *   GET    /api/spec-dictionary/:id/options  - 获取指标列表
 *   POST   /api/spec-dictionary/:id/options  - 创建指标
 *   POST   /api/spec-dictionary/:id/preview-code - 预览编码
 *   PUT    /api/spec-dictionary/options/:id  - 更新指标
 *   DELETE /api/spec-dictionary/options/:id  - 删除指标
 *   PUT    /api/spec-dictionary/options/:id/toggle - 切换指标状态
 */

const SpecDictionaryManager = (function() {
    'use strict';

    // ==================== 私有状态 ====================
    let state = {
        specs: [],              // 规格列表
        filteredSpecs: [],      // 过滤后的规格列表
        currentSpec: null,      // 当前选中的规格
        currentOptions: [],     // 当前规格的指标列表
        deleteTarget: null,     // 待删除的目标 { type: 'spec'|'option', id: number }
        isLoading: false,       // 加载状态
        searchKeyword: ''       // 搜索关键词
    };

    // API基础路径
    const API_BASE = '/api/spec-dictionary';

    // ==================== DOM 元素引用 ====================
    const getElements = () => ({
        // 主模态框
        modal: document.getElementById('specDictModal'),

        // 规格列表
        specList: document.getElementById('specList'),
        specListLoading: document.getElementById('specListLoading'),
        specListEmpty: document.getElementById('specListEmpty'),
        specTotalCount: document.getElementById('specTotalCount'),
        specSearchInput: document.getElementById('specSearchInput'),

        // 规格详情
        specDetailEmpty: document.getElementById('specDetailEmpty'),
        specDetailContent: document.getElementById('specDetailContent'),
        specDetailTitle: document.getElementById('specDetailTitle'),
        specInfoName: document.getElementById('specInfoName'),
        specInfoUnit: document.getElementById('specInfoUnit'),
        specInfoStatus: document.getElementById('specInfoStatus'),
        specInfoCreatedAt: document.getElementById('specInfoCreatedAt'),
        specOptionsTitle: document.getElementById('specOptionsTitle'),

        // 指标表格
        optionTableBody: document.getElementById('optionTableBody'),
        optionTableLoading: document.getElementById('optionTableLoading'),
        optionTableEmpty: document.getElementById('optionTableEmpty'),
        optionTotalCount: document.getElementById('optionTotalCount'),

        // 规格表单模态框 (tw_sub_modal 使用 modal_id-title 格式)
        specFormModal: document.getElementById('specFormModal'),
        specForm: document.getElementById('specForm'),
        specFormTitle: document.getElementById('specFormModal-title'),
        specFormId: document.getElementById('specFormId'),
        specFormName: document.getElementById('specFormName'),
        specFormUnit: document.getElementById('specFormUnit'),
        specFormActive: document.getElementById('specFormActive'),

        // 指标表单模态框 (tw_sub_modal 使用 modal_id-title 格式)
        optionFormModal: document.getElementById('optionFormModal'),
        optionForm: document.getElementById('optionForm'),
        optionFormTitle: document.getElementById('optionFormModal-title'),
        optionFormId: document.getElementById('optionFormId'),
        optionFormValue: document.getElementById('optionFormValue'),
        optionFormCode: document.getElementById('optionFormCode'),
        optionFormDesc: document.getElementById('optionFormDesc'),
        optionCodePreview: document.getElementById('optionCodePreview'),
        optionCodeHint: document.getElementById('optionCodeHint'),

        // 删除确认模态框 (tw_sub_modal 使用 modal_id-title 格式)
        deleteModal: document.getElementById('specDeleteModal'),
        deleteMessage: document.getElementById('specDeleteMessage')
    });

    // ==================== 工具函数 ====================

    /**
     * 发送API请求
     */
    async function apiRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        };

        const response = await fetch(url, { ...defaultOptions, ...options });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || '请求失败');
        }

        return data;
    }

    /**
     * 获取CSRF Token
     */
    function getCSRFToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    /**
     * 显示Toast消息
     */
    function showToast(message, type = 'success') {
        // 尝试使用全局Toast函数
        if (typeof window.showToast === 'function') {
            window.showToast(message, type);
            return;
        }

        // 备用：控制台输出
        console.log(`[${type.toUpperCase()}] ${message}`);

        // 简单的原生提示
        if (type === 'error') {
            alert(message);
        }
    }

    /**
     * 格式化日期
     */
    function formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }).replace(/\//g, '/');
    }

    /**
     * 渲染状态徽章
     */
    function renderStatusBadge(isActive) {
        if (isActive) {
            return `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
                启用
            </span>`;
        } else {
            return `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
                停用
            </span>`;
        }
    }

    // ==================== 规格列表管理 ====================

    /**
     * 加载规格列表
     */
    async function loadSpecs() {
        const els = getElements();

        // 显示加载状态
        els.specListLoading.classList.remove('hidden');
        els.specListEmpty.classList.add('hidden');
        els.specList.innerHTML = '';

        try {
            const response = await apiRequest(API_BASE);
            state.specs = response.data || [];
            state.filteredSpecs = [...state.specs];

            renderSpecList();
        } catch (error) {
            console.error('加载规格列表失败:', error);
            showToast('加载规格列表失败: ' + error.message, 'error');
        } finally {
            els.specListLoading.classList.add('hidden');
        }
    }

    /**
     * 渲染规格列表
     */
    function renderSpecList() {
        const els = getElements();
        const specs = state.filteredSpecs;

        // 更新总数
        els.specTotalCount.textContent = specs.length;

        // 空状态
        if (specs.length === 0) {
            els.specListEmpty.classList.remove('hidden');
            els.specList.innerHTML = '';
            return;
        }

        els.specListEmpty.classList.add('hidden');

        // 渲染列表
        els.specList.innerHTML = specs.map(spec => {
            const isSelected = state.currentSpec && state.currentSpec.id === spec.id;
            const isInactive = !spec.is_active;

            return `
                <li class="group flex items-center gap-3 px-3 py-3 cursor-pointer transition-colors
                           ${isSelected ? 'bg-primary/10 dark:bg-primary/20' : 'hover:bg-slate-100 dark:hover:bg-slate-800'}
                           ${isInactive ? 'opacity-60' : ''}"
                    onclick="SpecDictionaryManager.selectSpec(${spec.id})"
                    data-spec-id="${spec.id}">
                    <span class="material-symbols-outlined text-xl ${isSelected ? 'text-primary' : 'text-slate-400 dark:text-slate-500'}">
                        ${isInactive ? 'block' : 'tune'}
                    </span>
                    <div class="flex-1 min-w-0">
                        <div class="font-medium text-sm ${isSelected ? 'text-primary' : 'text-slate-900 dark:text-white'} truncate">
                            ${escapeHtml(spec.name)}
                        </div>
                        <div class="text-xs text-slate-400 dark:text-slate-500">
                            ${spec.option_count || 0} 个指标
                        </div>
                    </div>
                    ${isInactive ? '<span class="w-2 h-2 rounded-full bg-slate-400"></span>' : ''}
                </li>
            `;
        }).join('');
    }

    /**
     * 过滤规格列表
     */
    function filterSpecs(keyword) {
        state.searchKeyword = keyword.toLowerCase().trim();

        if (!state.searchKeyword) {
            state.filteredSpecs = [...state.specs];
        } else {
            state.filteredSpecs = state.specs.filter(spec =>
                spec.name.toLowerCase().includes(state.searchKeyword)
            );
        }

        renderSpecList();
    }

    /**
     * 选择规格
     */
    async function selectSpec(specId) {
        const spec = state.specs.find(s => s.id === specId);
        if (!spec) return;

        state.currentSpec = spec;

        // 更新列表选中状态
        renderSpecList();

        // 显示详情
        showSpecDetail(spec);

        // 加载指标
        await loadOptions(specId);
    }

    /**
     * 显示规格详情
     */
    function showSpecDetail(spec) {
        const els = getElements();

        // 隐藏空状态，显示详情
        els.specDetailEmpty.classList.add('hidden');
        els.specDetailContent.classList.remove('hidden');

        // 填充数据
        els.specDetailTitle.textContent = spec.name + ' 详情';
        els.specInfoName.textContent = spec.name;
        els.specInfoUnit.textContent = spec.unit || '-';
        els.specInfoStatus.innerHTML = renderStatusBadge(spec.is_active);
        els.specInfoCreatedAt.textContent = formatDate(spec.created_at);
        els.specOptionsTitle.textContent = spec.name;
    }

    // ==================== 指标管理 ====================

    /**
     * 加载指标列表
     */
    async function loadOptions(specId) {
        const els = getElements();

        // 显示加载状态
        els.optionTableLoading.classList.remove('hidden');
        els.optionTableEmpty.classList.add('hidden');

        // 清空现有指标行（保留加载和空状态行）
        const rows = els.optionTableBody.querySelectorAll('tr:not(#optionTableLoading):not(#optionTableEmpty)');
        rows.forEach(row => row.remove());

        try {
            const response = await apiRequest(`${API_BASE}/${specId}/options`);
            state.currentOptions = response.data || [];

            renderOptionTable();
        } catch (error) {
            console.error('加载指标列表失败:', error);
            showToast('加载指标列表失败: ' + error.message, 'error');
        } finally {
            els.optionTableLoading.classList.add('hidden');
        }
    }

    /**
     * 渲染指标表格
     */
    function renderOptionTable() {
        const els = getElements();
        const options = state.currentOptions;

        // 更新总数
        els.optionTotalCount.textContent = options.length;

        // 清空现有指标行
        const rows = els.optionTableBody.querySelectorAll('tr:not(#optionTableLoading):not(#optionTableEmpty)');
        rows.forEach(row => row.remove());

        // 空状态
        if (options.length === 0) {
            els.optionTableEmpty.classList.remove('hidden');
            return;
        }

        els.optionTableEmpty.classList.add('hidden');

        // 渲染行
        const html = options.map(opt => `
            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors ${!opt.is_active ? 'opacity-60' : ''}"
                data-option-id="${opt.id}">
                <td class="px-4 py-3">
                    ${opt.is_used === true ? `
                        <button type="button" onclick="SpecDictionaryManager.showProductUsage(${opt.id}, '${escapeHtml(opt.value)}')"
                                class="font-medium text-blue-600 dark:text-blue-400 hover:underline cursor-pointer">
                            ${escapeHtml(opt.value)}
                        </button>
                    ` : `
                        <span class="font-medium text-slate-900 dark:text-white">${escapeHtml(opt.value)}</span>
                    `}
                    ${opt.description ? `<p class="text-xs text-slate-400 mt-0.5">${escapeHtml(opt.description)}</p>` : ''}
                    ${opt.is_used === true ? '<span class="ml-2 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded inline-flex items-center gap-1"><span class="material-symbols-outlined text-xs">link</span>已引用</span>' : ''}
                </td>
                <td class="px-4 py-3">
                    <span class="font-mono text-primary font-medium">${escapeHtml(opt.code)}</span>
                </td>
                <td class="px-4 py-3">
                    ${renderStatusBadge(opt.is_active)}
                </td>
                <td class="px-4 py-3">
                    <div class="flex items-center justify-end gap-1">
                        ${opt.is_used === true ? `
                            <span class="p-2 text-slate-300 dark:text-slate-600 cursor-not-allowed" title="已被产品使用，无法编辑">
                                <span class="material-symbols-outlined text-lg">lock</span>
                            </span>
                        ` : `
                            <button type="button" onclick="SpecDictionaryManager.showEditOptionForm(${opt.id})"
                                    class="p-2 text-primary hover:bg-primary/10 rounded-lg transition-colors" title="编辑">
                                <span class="material-symbols-outlined text-lg">edit</span>
                            </button>
                        `}
                        <button type="button" onclick="SpecDictionaryManager.toggleOptionStatus(${opt.id})"
                                class="p-2 ${opt.is_active ? 'text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-900/20' : 'text-green-500 hover:bg-green-50 dark:hover:bg-green-900/20'} rounded-lg transition-colors"
                                title="${opt.is_active ? '停用' : '启用'}">
                            <span class="material-symbols-outlined text-lg">${opt.is_active ? 'block' : 'check_circle'}</span>
                        </button>
                        ${opt.is_used !== true ? `
                            <button type="button" onclick="SpecDictionaryManager.confirmDeleteOption(${opt.id})"
                                    class="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors" title="删除">
                                <span class="material-symbols-outlined text-lg">delete</span>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `).join('');

        els.optionTableBody.insertAdjacentHTML('beforeend', html);
    }

    // ==================== 规格表单操作 ====================

    /**
     * 显示添加规格表单
     */
    function showAddSpecForm() {
        const els = getElements();

        els.specFormTitle.textContent = '添加规格';
        els.specFormId.value = '';
        els.specFormName.value = '';
        els.specFormUnit.value = '';
        els.specFormActive.checked = true;

        els.specFormModal.classList.remove('hidden');
        els.specFormName.focus();
    }

    /**
     * 显示编辑规格表单
     */
    function showEditSpecForm() {
        if (!state.currentSpec) return;

        const els = getElements();
        const spec = state.currentSpec;

        els.specFormTitle.textContent = '编辑规格';
        els.specFormId.value = spec.id;
        els.specFormName.value = spec.name;
        els.specFormUnit.value = spec.unit || '';
        els.specFormActive.checked = spec.is_active;

        els.specFormModal.classList.remove('hidden');
        els.specFormName.focus();
    }

    /**
     * 隐藏规格表单
     */
    function hideSpecForm() {
        const els = getElements();
        els.specFormModal.classList.add('hidden');
        els.specForm.reset();
    }

    /**
     * 提交规格表单
     */
    async function submitSpecForm(event) {
        event.preventDefault();

        const els = getElements();
        const specId = els.specFormId.value;
        const isEdit = !!specId;

        const data = {
            name: els.specFormName.value.trim(),
            unit: els.specFormUnit.value.trim() || null,
            is_active: els.specFormActive.checked
        };

        if (!data.name) {
            showToast('请输入规格名称', 'error');
            return false;
        }

        try {
            if (isEdit) {
                await apiRequest(`${API_BASE}/${specId}`, {
                    method: 'PUT',
                    body: JSON.stringify(data)
                });
                showToast('规格更新成功');
            } else {
                await apiRequest(API_BASE, {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
                showToast('规格创建成功');
            }

            hideSpecForm();
            await loadSpecs();

            // 如果是编辑当前规格，刷新详情
            if (isEdit && state.currentSpec && state.currentSpec.id === parseInt(specId)) {
                const updatedSpec = state.specs.find(s => s.id === parseInt(specId));
                if (updatedSpec) {
                    state.currentSpec = updatedSpec;
                    showSpecDetail(updatedSpec);
                }
            }
        } catch (error) {
            showToast(error.message, 'error');
        }

        return false;
    }

    // ==================== 指标表单操作 ====================

    /**
     * 显示添加指标表单
     */
    function showAddOptionForm() {
        if (!state.currentSpec) {
            showToast('请先选择一个规格', 'error');
            return;
        }

        const els = getElements();

        els.optionFormTitle.textContent = '添加指标';
        els.optionFormId.value = '';
        els.optionFormValue.value = '';
        els.optionFormCode.value = '';
        els.optionFormDesc.value = '';
        els.optionCodePreview.classList.add('hidden');
        els.optionCodeHint.textContent = '';

        els.optionFormModal.classList.remove('hidden');
        els.optionFormValue.focus();
    }

    /**
     * 显示编辑指标表单
     */
    function showEditOptionForm(optionId) {
        const option = state.currentOptions.find(o => o.id === optionId);
        if (!option) return;

        const els = getElements();

        els.optionFormTitle.textContent = '编辑指标';
        els.optionFormId.value = option.id;
        els.optionFormValue.value = option.value;
        els.optionFormCode.value = option.code;
        els.optionFormDesc.value = option.description || '';
        els.optionCodePreview.classList.add('hidden');
        els.optionCodeHint.textContent = '编辑模式下编码不可自动更新';

        els.optionFormModal.classList.remove('hidden');
        els.optionFormValue.focus();
    }

    /**
     * 隐藏指标表单
     */
    function hideOptionForm() {
        const els = getElements();
        els.optionFormModal.classList.add('hidden');
        els.optionForm.reset();
    }

    /**
     * 预览编码
     */
    async function previewCode(value) {
        const els = getElements();

        // 编辑模式不预览
        if (els.optionFormId.value) return;

        if (!value.trim() || !state.currentSpec) {
            els.optionCodePreview.classList.add('hidden');
            els.optionCodeHint.textContent = '';
            return;
        }

        try {
            const response = await apiRequest(`${API_BASE}/${state.currentSpec.id}/preview-code`, {
                method: 'POST',
                body: JSON.stringify({ value: value.trim() })
            });

            if (response.success) {
                els.optionFormCode.value = response.code;
                els.optionCodeHint.textContent = response.message;
                els.optionCodeHint.className = 'mt-1 text-xs text-green-600 dark:text-green-400';
            } else if (response.exists) {
                els.optionCodeHint.textContent = response.message;
                els.optionCodeHint.className = 'mt-1 text-xs text-amber-600 dark:text-amber-400';
            } else {
                els.optionCodeHint.textContent = response.message;
                els.optionCodeHint.className = 'mt-1 text-xs text-red-600 dark:text-red-400';
            }
        } catch (error) {
            console.error('预览编码失败:', error);
        }
    }

    /**
     * 提交指标表单
     */
    async function submitOptionForm(event) {
        event.preventDefault();

        if (!state.currentSpec) {
            showToast('请先选择一个规格', 'error');
            return false;
        }

        const els = getElements();
        const optionId = els.optionFormId.value;
        const isEdit = !!optionId;

        const data = {
            value: els.optionFormValue.value.trim(),
            code: els.optionFormCode.value.trim() || undefined,
            description: els.optionFormDesc.value.trim() || undefined
        };

        if (!data.value) {
            showToast('请输入指标值', 'error');
            return false;
        }

        try {
            if (isEdit) {
                await apiRequest(`${API_BASE}/options/${optionId}`, {
                    method: 'PUT',
                    body: JSON.stringify(data)
                });
                showToast('指标更新成功');
            } else {
                await apiRequest(`${API_BASE}/${state.currentSpec.id}/options`, {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
                showToast('指标创建成功');
            }

            hideOptionForm();
            await loadOptions(state.currentSpec.id);
        } catch (error) {
            showToast(error.message, 'error');
        }

        return false;
    }

    /**
     * 切换指标状态
     */
    async function toggleOptionStatus(optionId) {
        try {
            const response = await apiRequest(`${API_BASE}/options/${optionId}/toggle`, {
                method: 'PUT'
            });
            showToast(response.message);
            await loadOptions(state.currentSpec.id);
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    // ==================== 删除操作 ====================

    /**
     * 确认删除规格
     */
    function confirmDeleteSpec() {
        if (!state.currentSpec) return;

        const els = getElements();
        state.deleteTarget = { type: 'spec', id: state.currentSpec.id };
        els.deleteMessage.textContent = `确定要删除规格"${state.currentSpec.name}"吗？此操作无法撤销。`;
        els.deleteModal.classList.remove('hidden');
    }

    /**
     * 确认删除指标
     */
    function confirmDeleteOption(optionId) {
        const option = state.currentOptions.find(o => o.id === optionId);
        if (!option) return;

        const els = getElements();
        state.deleteTarget = { type: 'option', id: optionId };
        els.deleteMessage.textContent = `确定要删除指标"${option.value}"吗？此操作无法撤销。`;
        els.deleteModal.classList.remove('hidden');
    }

    /**
     * 隐藏删除确认框
     */
    function hideDeleteModal() {
        const els = getElements();
        els.deleteModal.classList.add('hidden');
        state.deleteTarget = null;
    }

    /**
     * 执行删除
     */
    async function executeDelete() {
        if (!state.deleteTarget) return;

        const { type, id } = state.deleteTarget;

        try {
            if (type === 'spec') {
                await apiRequest(`${API_BASE}/${id}`, { method: 'DELETE' });
                showToast('规格已删除');

                // 清空当前选中
                state.currentSpec = null;
                state.currentOptions = [];

                // 隐藏详情
                const els = getElements();
                els.specDetailContent.classList.add('hidden');
                els.specDetailEmpty.classList.remove('hidden');

                // 刷新列表
                await loadSpecs();
            } else if (type === 'option') {
                await apiRequest(`${API_BASE}/options/${id}`, { method: 'DELETE' });
                showToast('指标已删除');
                await loadOptions(state.currentSpec.id);
            }
        } catch (error) {
            showToast(error.message, 'error');
        } finally {
            hideDeleteModal();
        }
    }

    // ==================== 模态框控制 ====================

    /**
     * 显示主模态框
     */
    function show() {
        const els = getElements();

        // [LegacySpecSystem] 检查模态框是否存在（被禁用时会隐藏）
        if (!els.modal) {
            console.warn('[LegacySpec] Spec dictionary modal does not exist - legacy spec system may be disabled');
            alert('规格系统已禁用，请使用新规格模板系统');
            return;
        }

        els.modal.classList.remove('hidden');

        // 重置状态
        state.currentSpec = null;
        state.currentOptions = [];
        state.searchKeyword = '';

        // 重置UI
        els.specSearchInput.value = '';
        els.specDetailContent.classList.add('hidden');
        els.specDetailEmpty.classList.remove('hidden');

        // 加载数据
        loadSpecs();
    }

    /**
     * 隐藏主模态框
     */
    function hide() {
        const els = getElements();
        els.modal.classList.add('hidden');
    }

    // ==================== 产品使用情况 ====================

    /**
     * 显示产品使用情况模态框
     * @param {number} optionId - 指标ID
     * @param {string} optionValue - 指标值
     */
    async function showProductUsage(optionId, optionValue) {
        const modal = document.getElementById('specProductUsageModal');
        const title = modal.querySelector('[data-modal-title]');
        const content = document.getElementById('specProductUsageContent');

        // 更新标题
        if (title) {
            title.textContent = `"${optionValue}" 引用情况`;
        }

        // 显示加载状态
        content.innerHTML = `
            <div class="flex items-center justify-center py-12">
                <div class="flex items-center gap-2 text-slate-400">
                    <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span class="text-sm">加载中...</span>
                </div>
            </div>
        `;
        modal.classList.remove('hidden');

        try {
            const response = await fetch(`/api/spec-dictionary/options/${optionId}/products`);
            const result = await response.json();

            if (result.success && result.data && result.data.length > 0) {
                content.innerHTML = result.data.map(s => `
                    <div class="p-4 border-b border-slate-200 dark:border-slate-700 last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                        <div class="flex items-center justify-between">
                            <div class="font-medium text-slate-900 dark:text-white">${escapeHtml(s.name)}</div>
                            <span class="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded">
                                ${s.product_count} 个产品
                            </span>
                        </div>
                        <div class="mt-1 text-sm text-slate-500 dark:text-slate-400">
                            分类: ${escapeHtml(s.category_name || '-')}
                        </div>
                    </div>
                `).join('');
            } else {
                content.innerHTML = `
                    <div class="flex flex-col items-center justify-center py-8 text-slate-400">
                        <span class="material-symbols-outlined text-4xl mb-2">inbox</span>
                        <span class="text-sm">暂无子分类使用此指标</span>
                    </div>
                `;
            }
        } catch (error) {
            console.error('获取产品使用列表失败:', error);
            content.innerHTML = `
                <div class="flex flex-col items-center justify-center py-8 text-red-500">
                    <span class="material-symbols-outlined text-4xl mb-2">error</span>
                    <span class="text-sm">加载失败</span>
                </div>
            `;
        }
    }

    /**
     * 隐藏产品使用情况模态框
     */
    function hideProductUsage() {
        const modal = document.getElementById('specProductUsageModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    // ==================== 辅助函数 ====================

    /**
     * HTML转义
     */
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ==================== 公开API ====================
    return {
        show,
        hide,
        selectSpec,
        filterSpecs,
        showAddSpecForm,
        showEditSpecForm,
        hideSpecForm,
        submitSpecForm,
        showAddOptionForm,
        showEditOptionForm,
        hideOptionForm,
        submitOptionForm,
        previewCode,
        toggleOptionStatus,
        confirmDeleteSpec,
        confirmDeleteOption,
        hideDeleteModal,
        executeDelete,
        // 产品使用情况
        showProductUsage,
        hideProductUsage
    };
})();
