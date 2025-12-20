/**
 * customer-form.js
 * 客户表单公共逻辑模块
 *
 * 用于 tw_view.html（编辑客户）和 tw_list.html（新建客户）
 *
 * 使用方式：
 * 1. 在页面中引入: <script src="{{ url_for('static', filename='js/customer-form.js') }}"></script>
 * 2. 初始化表单: await CustomerForm.init(config)
 * 3. 提交表单: await CustomerForm.submit(formId, mode, companyId, callbacks)
 */
window.CustomerForm = (function() {
    'use strict';

    // 缓存数据
    let countriesData = null;
    let optionsData = null;
    let isInitialized = false;

    // 默认配置
    const defaultConfig = {
        countryId: 'country',
        regionId: 'region',
        industryId: 'industry',
        companyTypeId: 'company_type',
        sourceId: 'source',
        placeholders: {
            country: '请选择国家',
            region: '请选择省/州',
            industry: '请选择行业',
            companyType: '请选择企业类型',
            source: '请选择来源'
        }
    };

    // API 端点
    const API = {
        countries: '/customer/api/countries-regions',
        options: '/customer/api/company/options',
        create: '/customer/api/company/create',
        update: function(id) { return '/customer/api/company/' + id + '/update'; },
        get: function(id) { return '/customer/api/company/' + id; },
        searchCompany: '/customer/api/company/search'
    };

    // 名称查重相关状态
    let nameCheckDebounceTimer = null;
    let matchedCompanies = [];
    let currentEditingCompanyId = null;  // 编辑模式时的当前公司ID

    /**
     * 加载国家和地区数据
     */
    async function loadCountries() {
        if (countriesData) return countriesData;

        try {
            const response = await fetch(API.countries);
            countriesData = await response.json();
            return countriesData;
        } catch (error) {
            console.error('加载国家数据失败:', error);
            return null;
        }
    }

    /**
     * 加载表单选项（行业、企业类型、来源）
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
     * 填充国家下拉框
     * @param {string} selectId - select元素ID
     * @param {string} selectedValue - 选中的值
     * @param {string} placeholder - 占位文本
     */
    function populateCountrySelect(selectId, selectedValue, placeholder) {
        const select = document.getElementById(selectId);
        if (!select) return;

        select.innerHTML = '<option value="">' + (placeholder || defaultConfig.placeholders.country) + '</option>';

        if (countriesData && countriesData.countries) {
            countriesData.countries.forEach(function(country) {
                const option = document.createElement('option');
                option.value = country.code;
                option.textContent = country.name;
                if (country.code === selectedValue) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        }
    }

    /**
     * 填充省/州下拉框
     * @param {string} selectId - select元素ID
     * @param {string} countryCode - 国家代码
     * @param {string} selectedValue - 选中的值
     * @param {string} placeholder - 占位文本
     */
    function populateRegionSelect(selectId, countryCode, selectedValue, placeholder) {
        const select = document.getElementById(selectId);
        if (!select) return;

        select.innerHTML = '<option value="">' + (placeholder || defaultConfig.placeholders.region) + '</option>';

        if (countriesData && countriesData.regions && countryCode) {
            const regions = countriesData.regions[countryCode];
            if (regions) {
                regions.forEach(function(region) {
                    const option = document.createElement('option');
                    option.value = region;
                    option.textContent = region;
                    if (region === selectedValue) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                });
            }
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

        options.forEach(function(opt) {
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
     * @param {string} config.countryId - 国家select的ID
     * @param {string} config.regionId - 地区select的ID
     * @param {string} config.industryId - 行业select的ID
     * @param {string} config.companyTypeId - 企业类型select的ID
     * @param {string} config.sourceId - 来源select的ID
     * @param {Object} config.placeholders - 各字段的占位文本
     * @returns {Promise<boolean>} 初始化是否成功
     */
    async function initForm(config) {
        config = Object.assign({}, defaultConfig, config);

        try {
            // 并行加载数据
            const [countries, options] = await Promise.all([
                loadCountries(),
                loadOptions()
            ]);

            if (!countries || !options) {
                return false;
            }

            // 填充下拉框
            populateCountrySelect(config.countryId, '', config.placeholders.country);
            populateSelect(config.industryId, options.industries, '', config.placeholders.industry);
            populateSelect(config.companyTypeId, options.company_types, '', config.placeholders.companyType);
            populateSelect(config.sourceId, options.sources, '', config.placeholders.source);

            // 绑定国家变更事件
            const countrySelect = document.getElementById(config.countryId);
            const regionSelect = document.getElementById(config.regionId);

            if (countrySelect && regionSelect) {
                countrySelect.addEventListener('change', function() {
                    populateRegionSelect(config.regionId, this.value, '', config.placeholders.region);
                });
            }

            isInitialized = true;
            return true;
        } catch (error) {
            console.error('初始化表单失败:', error);
            return false;
        }
    }

    /**
     * 填充表单数据（用于编辑模式）
     * @param {Object} data - 客户数据
     * @param {Object} config - 配置对象
     */
    function populateFormData(data, config) {
        config = Object.assign({}, defaultConfig, config);

        // 填充文本字段
        const fields = ['company_name', 'address', 'notes'];
        fields.forEach(function(field) {
            const el = document.getElementById(field);
            if (el) el.value = data[field] || '';
        });

        // 填充国家
        const countrySelect = document.getElementById(config.countryId);
        if (countrySelect) {
            countrySelect.value = data.country || '';
        }

        // 填充地区
        populateRegionSelect(config.regionId, data.country, data.region, config.placeholders.region);

        // 填充其他下拉框
        const selectFields = [
            { id: config.industryId, value: data.industry },
            { id: config.companyTypeId, value: data.company_type },
            { id: config.sourceId, value: data.source }
        ];

        selectFields.forEach(function(field) {
            const el = document.getElementById(field.id);
            if (el) el.value = field.value || '';
        });
    }

    /**
     * 提交表单
     * @param {string} formId - 表单ID
     * @param {string} mode - 模式: 'create' 或 'update'
     * @param {number|null} companyId - 公司ID（更新时需要）
     * @param {Object} callbacks - 回调函数
     * @param {Function} callbacks.onSuccess - 成功回调
     * @param {Function} callbacks.onError - 失败回调
     * @param {Object} callbacks.i18n - 国际化文本
     */
    async function submitForm(formId, mode, companyId, callbacks) {
        callbacks = callbacks || {};
        const i18n = callbacks.i18n || {
            saving: '保存中...',
            creating: '创建中...',
            save: '保存',
            create: '创建',
            saveError: '保存失败，请重试'
        };

        const form = document.getElementById(formId);
        if (!form) return;

        const formData = new FormData(form);
        const data = {};
        formData.forEach(function(value, key) {
            if (key !== 'company_id') {
                data[key] = value;
            }
        });

        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        const submitBtn = document.getElementById(formId.replace('-form', '') + '-submit-btn');

        const url = mode === 'create' ? API.create : API.update(companyId);
        const btnText = mode === 'create' ? i18n.create : i18n.save;
        const btnLoadingText = mode === 'create' ? i18n.creating : i18n.saving;

        try {
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = btnLoadingText;
            }

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken ? csrfToken.getAttribute('content') : ''
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                if (typeof callbacks.onSuccess === 'function') {
                    callbacks.onSuccess(result);
                }
            } else {
                const errorMsg = result.message || i18n.saveError;
                if (typeof callbacks.onError === 'function') {
                    callbacks.onError(errorMsg);
                } else {
                    alert(errorMsg);
                }
            }
        } catch (error) {
            console.error('提交表单失败:', error);
            if (typeof callbacks.onError === 'function') {
                callbacks.onError(i18n.saveError);
            } else {
                alert(i18n.saveError);
            }
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = btnText;
            }
        }
    }

    /**
     * 加载客户数据
     * @param {number} companyId - 公司ID
     * @returns {Promise<Object|null>} 客户数据
     */
    async function loadCompanyData(companyId) {
        try {
            const response = await fetch(API.get(companyId));
            const result = await response.json();

            if (result.success) {
                return result.data;
            }
            return null;
        } catch (error) {
            console.error('加载客户数据失败:', error);
            return null;
        }
    }

    /**
     * 重置表单
     * @param {string} formId - 表单ID
     * @param {Object} config - 配置对象
     */
    function resetForm(formId, config) {
        config = Object.assign({}, defaultConfig, config);

        const form = document.getElementById(formId);
        if (form) {
            form.reset();
        }

        // 重置地区下拉框
        populateRegionSelect(config.regionId, '', '', config.placeholders.region);

        // 重置名称查重状态
        matchedCompanies = [];
        hideSuggestions();
        clearNameError();
    }

    /**
     * 搜索相似企业
     * @param {string} keyword - 搜索关键词
     * @returns {Promise<Array>} 匹配的企业列表
     */
    async function searchCompanies(keyword) {
        if (!keyword || keyword.trim().length < 1) {
            return [];
        }

        try {
            const response = await fetch(API.searchCompany + '?keyword=' + encodeURIComponent(keyword.trim()));
            const data = await response.json();
            return data.results || [];
        } catch (error) {
            console.error('搜索企业失败:', error);
            return [];
        }
    }

    /**
     * 验证企业名称是否重复
     * @param {string} inputValue - 输入的名称
     * @param {number|null} excludeId - 排除的企业ID（编辑模式时排除当前企业）
     * @returns {boolean} 是否有效（无重复）
     */
    function validateCompanyName(inputValue, excludeId) {
        if (!inputValue || inputValue.trim() === '') {
            return true;
        }

        const normalizedInput = inputValue.trim().toLowerCase();

        // 检查是否与现有公司名称完全匹配（忽略大小写和空格）
        for (var i = 0; i < matchedCompanies.length; i++) {
            var company = matchedCompanies[i];
            var companyName = company.name.trim().toLowerCase();
            // 排除当前编辑的企业
            if (excludeId && company.id === excludeId) {
                continue;
            }
            if (normalizedInput === companyName) {
                return false;  // 名称重复
            }
        }

        return true;  // 名称有效
    }

    /**
     * 显示建议列表
     * @param {Array} companies - 企业列表
     * @param {Object} i18n - 国际化文本
     */
    function showSuggestions(companies, i18n) {
        i18n = i18n || {};
        var container = document.getElementById('companySuggestions');
        if (!container) return;

        container.innerHTML = '';

        if (companies.length === 0) {
            container.classList.add('hidden');
            return;
        }

        container.classList.remove('hidden');

        // 添加标题
        var header = document.createElement('div');
        header.className = 'px-3 py-2 text-xs font-medium text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700';
        header.textContent = i18n.similarCompanies || '相似企业';
        container.appendChild(header);

        // 添加每个建议项
        companies.forEach(function(company) {
            var item = document.createElement('div');
            item.className = 'px-3 py-2 text-sm text-slate-600 dark:text-slate-300 border-b border-slate-100 dark:border-slate-700 last:border-b-0';

            var content = document.createElement('div');
            content.className = 'flex items-center gap-2';

            // 公司名称
            var nameSpan = document.createElement('span');
            nameSpan.className = 'font-medium text-slate-800 dark:text-slate-200';
            nameSpan.textContent = company.name;
            content.appendChild(nameSpan);

            // 地区信息
            var locationText = '';
            if (company.country && company.region) {
                locationText = company.country + ' ' + company.region;
            } else if (company.country) {
                locationText = company.country;
            } else if (company.region) {
                locationText = company.region;
            }

            if (locationText) {
                var locationSpan = document.createElement('span');
                locationSpan.className = 'text-slate-400 dark:text-slate-500';
                locationSpan.textContent = '| ' + locationText;
                content.appendChild(locationSpan);
            }

            // 负责人
            if (company.owner_name) {
                var ownerSpan = document.createElement('span');
                ownerSpan.className = 'text-slate-400 dark:text-slate-500';
                ownerSpan.textContent = '| ' + company.owner_name;
                content.appendChild(ownerSpan);
            }

            item.appendChild(content);
            container.appendChild(item);
        });

        // 添加提示信息
        var notice = document.createElement('div');
        notice.className = 'px-3 py-2 text-xs text-slate-400 dark:text-slate-500 bg-slate-50 dark:bg-slate-800/50';
        notice.textContent = i18n.referenceNotice || '以上企业名称仅供参考，请确保输入的名称不与已有企业重复';
        container.appendChild(notice);
    }

    /**
     * 隐藏建议列表
     */
    function hideSuggestions() {
        var container = document.getElementById('companySuggestions');
        if (container) {
            container.classList.add('hidden');
            container.innerHTML = '';
        }
    }

    /**
     * 显示名称错误
     * @param {string} message - 错误信息
     */
    function showNameError(message) {
        var input = document.getElementById('company_name');
        var errorEl = document.getElementById('companyNameError');

        if (input) {
            input.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
            input.classList.remove('border-slate-300', 'focus:border-primary');
        }

        if (errorEl) {
            errorEl.textContent = message;
            errorEl.classList.remove('hidden');
        }
    }

    /**
     * 清除名称错误
     */
    function clearNameError() {
        var input = document.getElementById('company_name');
        var errorEl = document.getElementById('companyNameError');

        if (input) {
            input.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
            input.classList.add('border-slate-300', 'focus:border-primary');
        }

        if (errorEl) {
            errorEl.textContent = '';
            errorEl.classList.add('hidden');
        }
    }

    /**
     * 初始化名称查重功能
     * @param {Object} config - 配置对象
     * @param {string} config.inputId - 输入框ID，默认 'company_name'
     * @param {number|null} config.excludeId - 排除的企业ID（编辑模式）
     * @param {Object} config.i18n - 国际化文本
     * @param {Function} config.onValidChange - 验证状态变化回调
     */
    function initNameCheck(config) {
        config = config || {};
        var inputId = config.inputId || 'company_name';
        var excludeId = config.excludeId || null;
        var i18n = config.i18n || {};
        var onValidChange = config.onValidChange || function() {};

        currentEditingCompanyId = excludeId;

        var input = document.getElementById(inputId);
        if (!input) return;

        // 输入事件处理
        input.addEventListener('input', function() {
            clearTimeout(nameCheckDebounceTimer);
            var keyword = this.value.trim();

            // 清除之前的错误状态
            clearNameError();

            // 如果输入为空，隐藏建议
            if (keyword.length < 1) {
                hideSuggestions();
                matchedCompanies = [];
                onValidChange(true);
                return;
            }

            // 防抖 300ms
            nameCheckDebounceTimer = setTimeout(function() {
                searchCompanies(keyword).then(function(companies) {
                    matchedCompanies = companies;

                    // 显示建议列表
                    showSuggestions(companies, i18n);

                    // 验证名称
                    var isValid = validateCompanyName(keyword, excludeId);
                    if (!isValid) {
                        showNameError(i18n.companyNameExists || '该企业名称已存在');
                        onValidChange(false);
                    } else {
                        clearNameError();
                        onValidChange(true);
                    }
                });
            }, 300);
        });

        // 失焦时隐藏建议（延迟一点以便用户能看到）
        input.addEventListener('blur', function() {
            setTimeout(function() {
                hideSuggestions();
            }, 200);
        });

        // 聚焦时如果有匹配结果，显示建议
        input.addEventListener('focus', function() {
            if (matchedCompanies.length > 0 && this.value.trim().length > 0) {
                showSuggestions(matchedCompanies, i18n);
            }
        });
    }

    /**
     * 设置当前编辑的企业ID（用于排除自己）
     * @param {number|null} companyId - 企业ID
     */
    function setEditingCompanyId(companyId) {
        currentEditingCompanyId = companyId;
    }

    // 公开 API
    return {
        init: initForm,
        submit: submitForm,
        reset: resetForm,
        loadCompanyData: loadCompanyData,
        populateFormData: populateFormData,
        populateCountry: populateCountrySelect,
        populateRegion: populateRegionSelect,
        populateSelect: populateSelect,
        isInitialized: function() { return isInitialized; },
        API: API,
        // 名称查重功能
        initNameCheck: initNameCheck,
        setEditingCompanyId: setEditingCompanyId,
        validateName: validateCompanyName,
        hideSuggestions: hideSuggestions,
        clearNameError: clearNameError
    };
})();
