/**
 * project-form.js
 * 项目表单公共逻辑模块
 *
 * 用于 tw_project_detail.html（编辑项目）和 tw_list.html（新建项目）
 *
 * 使用方式：
 * 1. 在页面中引入: <script src="{{ url_for('static', filename='js/project-form.js') }}"></script>
 * 2. 初始化表单: await ProjectForm.init(config)
 * 3. 提交表单: await ProjectForm.submit(formId, mode, projectId, callbacks)
 */
window.ProjectForm = (function () {
    'use strict';

    // 缓存数据
    let optionsData = null;
    let isInitialized = false;

    // 默认配置
    const defaultConfig = {
        projectTypeId: 'project_type',
        industryId: 'industry',
        reportSourceId: 'report_source',
        productSituationId: 'product_situation',
        placeholders: {
            projectType: '请选择项目类型',
            industry: '请选择行业',
            reportSource: '请选择报备源',
            productSituation: '请选择产品情况'
        }
    };

    // API 端点
    const API = {
        options: '/project/api/options',
        create: '/project/api/create',
        update: function (id) { return '/project/api/' + id + '/update'; },
        get: function (id) { return '/project/api/' + id; },
        searchProject: '/project/api/search'
    };

    // 名称查重相关状态
    let nameCheckDebounceTimer = null;
    let matchedProjects = [];
    let currentEditingProjectId = null;  // 编辑模式时的当前项目ID

    /**
     * 加载表单选项（项目类型、行业、报备源、产品情况、用户列表）
     */
    async function loadOptions() {
        if (optionsData) return optionsData;

        try {
            const response = await fetch(API.options);
            const result = await response.json();
            if (result.success) {
                optionsData = result.data;
                return optionsData;
            }
            return null;
        } catch (error) {
            console.error('加载表单选项失败:', error);
            return null;
        }
    }

    /**
     * 填充通用下拉框
     * @param {string} selectId - select元素ID
     * @param {Array} options - 选项数组 [{value, label}]
     * @param {string} selectedValue - 选中的值
     * @param {string} placeholder - 占位文本
     */
    function populateSelect(selectId, options, selectedValue, placeholder) {
        const select = document.getElementById(selectId);
        if (!select || !options) return;

        select.innerHTML = '<option value="">' + (placeholder || '') + '</option>';

        options.forEach(function (opt) {
            const option = document.createElement('option');
            option.value = opt.value;
            option.textContent = opt.label;
            if (opt.value === selectedValue) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    }

    /**
     * 初始化表单
     * @param {Object} config - 配置对象
     * @returns {Promise<boolean>} 初始化是否成功
     */
    async function initForm(config) {
        config = Object.assign({}, defaultConfig, config);

        try {
            // 加载选项数据
            const options = await loadOptions();
            if (!options) {
                return false;
            }

            // 填充下拉框
            populateSelect(config.projectTypeId, options.project_types, '', config.placeholders.projectType);
            populateSelect(config.industryId, options.industries, '', config.placeholders.industry);
            populateSelect(config.reportSourceId, options.report_sources, '', config.placeholders.reportSource);
            populateSelect(config.productSituationId, options.product_situations, '', config.placeholders.productSituation);

            isInitialized = true;
            return true;

        } catch (error) {
            console.error('初始化表单失败:', error);
            return false;
        }
    }

    /**
     * 加载项目数据
     * @param {number} projectId - 项目ID
     * @returns {Promise<Object|null>} 项目数据
     */
    async function loadProjectData(projectId) {
        try {
            const response = await fetch(API.get(projectId));
            const result = await response.json();
            if (result.success) {
                return result.data;
            }
            return null;
        } catch (error) {
            console.error('加载项目数据失败:', error);
            return null;
        }
    }

    /**
     * 填充表单数据
     * @param {Object} projectData - 项目数据
     * @param {Object} config - 配置对象
     */
    function populateFormData(projectData, config) {
        config = config || defaultConfig;

        // 填充基础字段（非select）
        const basicFields = ['project_name', 'report_time', 'delivery_forecast',
            'authorization_code', 'stage_description'];

        basicFields.forEach(function (fieldName) {
            const field = document.getElementById(fieldName);
            if (field && projectData[fieldName] !== undefined) {
                field.value = projectData[fieldName] || '';
            }
        });

        // 填充select字段（需要重新调用populateSelect以设置选中值）
        if (optionsData) {
            populateSelect('project_type', optionsData.project_types, projectData.project_type, config.placeholders?.projectType);
            populateSelect('industry', optionsData.industries, projectData.industry, config.placeholders?.industry);
            populateSelect('report_source', optionsData.report_sources, projectData.report_source, config.placeholders?.reportSource);
            populateSelect(config.productSituationId, optionsData.product_situations, projectData.product_situation, config.placeholders?.productSituation);
        }
    }

    /**
     * 重置表单
     * @param {string} formId - 表单ID
     * @param {Object} config - 配置对象
     */
    function resetForm(formId, config) {
        config = config || defaultConfig;
        const form = document.getElementById(formId);
        if (form) {
            form.reset();
        }

        // 清空错误提示
        const errorEl = document.getElementById('projectNameError');
        if (errorEl) {
            errorEl.classList.add('hidden');
        }

        // 清空建议列表
        const suggestionsEl = document.getElementById('projectSuggestions');
        if (suggestionsEl) {
            suggestionsEl.classList.add('hidden');
        }

        // 重新填充下拉框
        populateSelect(config.projectTypeId, optionsData?.project_types, '', config.placeholders.projectType);
        populateSelect(config.industryId, optionsData?.industries, '', config.placeholders.industry);
        populateSelect(config.reportSourceId, optionsData?.report_sources, '', config.placeholders.reportSource);
        populateSelect(config.productSituationId, optionsData?.product_situations, '', config.placeholders.productSituation);
    }

    /**
     * 初始化项目名称查重功能
     * @param {Object} config - 配置对象
     * @param {string} config.inputId - 输入框ID
     * @param {number} config.excludeId - 排除的项目ID（编辑模式）
     * @param {Object} config.i18n - 国际化文本
     * @param {Function} config.onValidChange - 验证状态变化回调
     */
    function initNameCheck(config) {
        const inputId = config.inputId || 'project_name';
        const excludeId = config.excludeId || null;
        const i18n = config.i18n || {};
        const onValidChange = config.onValidChange || function () { };

        currentEditingProjectId = excludeId;

        const projectNameInput = document.getElementById(inputId);
        if (!projectNameInput) return;

        projectNameInput.addEventListener('input', function (e) {
            const value = e.target.value.trim();

            // 清除之前的定时器
            clearTimeout(nameCheckDebounceTimer);

            if (value.length === 0) {
                hideNameSuggestions();
                hideNameError();
                onValidChange(true);
                return;
            }

            // 防抖搜索
            nameCheckDebounceTimer = setTimeout(function () {
                searchProjects(value, excludeId, i18n, onValidChange);
            }, 300);
        });
    }

    /**
     * 搜索项目
     */
    async function searchProjects(keyword, excludeId, i18n, onValidChange) {
        try {
            const url = API.searchProject + '?keyword=' + encodeURIComponent(keyword);
            const response = await fetch(url);
            const result = await response.json();

            if (result.results && result.results.length > 0) {
                // 过滤掉当前编辑的项目
                matchedProjects = result.results.filter(function (p) {
                    return !excludeId || p.id !== parseInt(excludeId);
                });

                // 检查是否有完全匹配
                const exactMatch = matchedProjects.find(function (p) {
                    return p.project_name.toLowerCase() === keyword.toLowerCase();
                });

                if (exactMatch) {
                    showNameError(i18n.projectNameExists || '该项目名称已存在');
                    hideNameSuggestions();
                    onValidChange(false);
                } else {
                    showNameSuggestions(matchedProjects, i18n);
                    hideNameError();
                    onValidChange(true);
                }
            } else {
                hideNameSuggestions();
                hideNameError();
                onValidChange(true);
            }
        } catch (error) {
            console.error('搜索项目失败:', error);
        }
    }

    /**
     * 显示名称建议
     */
    function showNameSuggestions(projects, i18n) {
        const suggestionsContainer = document.getElementById('projectSuggestions');
        if (!suggestionsContainer) return;

        if (projects.length === 0) {
            hideNameSuggestions();
            return;
        }

        let html = '<div class="p-3">';
        html += '<div class="text-xs font-medium text-slate-600 dark:text-slate-400 mb-2">';
        html += i18n.similarProjects || '相似项目';
        html += '</div>';
        html += '<ul class="space-y-1">';

        projects.forEach(function (project) {
            html += '<li class="text-sm text-slate-700 dark:text-slate-300 p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-700">';
            html += '<div class="font-medium">' + escapeHtml(project.project_name) + '</div>';
            if (project.authorization_code) {
                html += '<div class="text-xs text-slate-500">授权码: ' + escapeHtml(project.authorization_code) + '</div>';
            }
            html += '</li>';
        });

        html += '</ul>';
        html += '<div class="text-xs text-slate-500 dark:text-slate-400 mt-2">';
        html += i18n.referenceNotice || '以上项目名称仅供参考，请确保输入的名称不与已有项目重复';
        html += '</div>';
        html += '</div>';

        suggestionsContainer.innerHTML = html;
        suggestionsContainer.classList.remove('hidden');
    }

    /**
     * 隐藏名称建议
     */
    function hideNameSuggestions() {
        const suggestionsContainer = document.getElementById('projectSuggestions');
        if (suggestionsContainer) {
            suggestionsContainer.classList.add('hidden');
        }
    }

    /**
     * 显示名称错误
     */
    function showNameError(message) {
        const errorEl = document.getElementById('projectNameError');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.classList.remove('hidden');
        }
    }

    /**
     * 隐藏名称错误
     */
    function hideNameError() {
        const errorEl = document.getElementById('projectNameError');
        if (errorEl) {
            errorEl.classList.add('hidden');
        }
    }

    /**
     * HTML转义
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 提交表单
     * @param {string} formId - 表单ID
     * @param {string} mode - 模式：'create' 或 'edit'
     * @param {number} projectId - 项目ID（编辑模式必需）
     * @param {Object} callbacks - 回调函数
     * @param {Function} callbacks.onSuccess - 成功回调
     * @param {Function} callbacks.onError - 错误回调
     * @param {Object} callbacks.i18n - 国际化文本
     * @returns {Promise<void>}
     */
    async function submitForm(formId, mode, projectId, callbacks) {
        callbacks = callbacks || {};
        const i18n = callbacks.i18n || {};

        const form = document.getElementById(formId);
        if (!form) {
            console.error('表单不存在:', formId);
            return;
        }

        // 收集表单数据
        const formData = new FormData(form);
        const data = {};
        formData.forEach(function (value, key) {
            data[key] = value;
        });

        // 确定API URL
        let url = mode === 'edit' ? API.update(projectId) : API.create;

        // 显示加载状态
        const submitBtn = document.getElementById(formId.replace('-form', '') + '-submit-btn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = i18n.saving || '保存中...';
        }

        // 获取CSRF Token
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                if (typeof callbacks.onSuccess === 'function') {
                    callbacks.onSuccess(result);
                }
            } else {
                if (typeof callbacks.onError === 'function') {
                    callbacks.onError(result.message || i18n.saveError || '保存失败');
                }
            }
        } catch (error) {
            console.error('提交表单失败:', error);
            if (typeof callbacks.onError === 'function') {
                callbacks.onError(i18n.saveError || '保存失败，请重试');
            }
        } finally {
            // 恢复按钮状态
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = i18n.save || '保存';
            }
        }
    }

    // 公开API
    return {
        init: initForm,
        submit: submitForm,
        reset: resetForm,
        loadProjectData: loadProjectData,
        populateFormData: populateFormData,
        initNameCheck: initNameCheck
    };
})();
