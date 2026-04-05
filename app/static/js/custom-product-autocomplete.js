/**
 * 自建产品 Autocomplete 模块
 *
 * 为报价单中"添加自建产品"新建的行提供产品名称 autocomplete 能力。
 * 从历史 quotation_details 中聚合检索（排除产品库产品），
 * 选中后回填整行所有字段。
 *
 * 使用方式：
 *   CustomProductAutocomplete.attach(inputElement, tableId, rowId);
 *
 * 创建日期: 2026-04-05
 */
(function() {
    'use strict';

    const SEARCH_DEBOUNCE = 300;  // ms
    const SEARCH_URL = '/quotation/api/product-suggestions';

    let searchTimeout = null;
    let currentDropdown = null;

    /**
     * 为 input 元素附加 autocomplete 能力
     * @param {HTMLInputElement} input - 产品名称输入框
     * @param {string} tableId - 表格ID
     * @param {string} rowId - 行ID
     */
    function attach(input, tableId, rowId) {
        if (!input) return;
        if (input.dataset.autocompleteAttached === 'true') return;

        input.dataset.autocompleteAttached = 'true';
        input.dataset.tableId = tableId;
        input.dataset.rowId = rowId;

        input.addEventListener('input', handleInput);
        input.addEventListener('focus', handleFocus);
        input.addEventListener('blur', handleBlur);
        input.addEventListener('keydown', handleKeydown);
    }

    function handleInput(e) {
        const input = e.target;
        const keyword = (input.value || '').trim();

        clearTimeout(searchTimeout);

        if (keyword.length < 1) {
            hideDropdown();
            return;
        }

        searchTimeout = setTimeout(function() {
            performSearch(keyword, input);
        }, SEARCH_DEBOUNCE);
    }

    function handleFocus(e) {
        const input = e.target;
        if ((input.value || '').trim()) {
            performSearch(input.value.trim(), input);
        }
    }

    function handleBlur() {
        // 延迟关闭，让 mousedown 事件先触发
        setTimeout(hideDropdown, 200);
    }

    function handleKeydown(e) {
        if (e.key === 'Escape') {
            hideDropdown();
        }
    }

    async function performSearch(keyword, input) {
        try {
            const url = SEARCH_URL + '?q=' + encodeURIComponent(keyword) + '&limit=10';
            const response = await fetch(url, {
                credentials: 'same-origin',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });

            if (!response.ok) {
                console.warn('[CustomProductAutocomplete] 搜索失败:', response.status);
                hideDropdown();
                return;
            }

            const data = await response.json();
            showDropdown(input, data.results || []);
        } catch (err) {
            console.error('[CustomProductAutocomplete] 搜索异常:', err);
            hideDropdown();
        }
    }

    function showDropdown(input, results) {
        hideDropdown();

        const dropdown = document.createElement('div');
        dropdown.className = 'custom-product-autocomplete-dropdown';
        applyDropdownStyle(dropdown);

        if (results.length === 0) {
            dropdown.innerHTML = '<div class="cpa-empty">无匹配记录，请继续手动填写</div>';
        } else {
            dropdown.innerHTML = results.map(function(r, i) {
                return renderItem(r, i);
            }).join('');

            // 绑定点击事件
            dropdown.querySelectorAll('.cpa-item').forEach(function(el, i) {
                el.addEventListener('mousedown', function(e) {
                    e.preventDefault();  // 阻止 blur
                    selectItem(results[i], input);
                });
            });
        }

        positionDropdown(dropdown, input);
        document.body.appendChild(dropdown);
        currentDropdown = dropdown;
    }

    function renderItem(item, index) {
        const name = escapeHtml(item.product_name || '');
        const model = escapeHtml(item.product_model || '');
        const brand = escapeHtml(item.brand || '');
        const price = item.market_price != null ? formatMoney(item.market_price) : '-';
        const currency = escapeHtml(item.currency || 'CNY');
        const usage = item.usage_count || 0;

        return [
            '<div class="cpa-item" data-index="' + index + '">',
            '  <div class="cpa-item-head">',
            '    <span class="cpa-name">' + name + '</span>',
            '    <span class="cpa-usage">' + usage + ' 次</span>',
            '  </div>',
            '  <div class="cpa-item-meta">',
            '    <span class="cpa-model">' + model + '</span>',
            (brand ? ' · <span class="cpa-brand">' + brand + '</span>' : ''),
            ' · <span class="cpa-price">' + currency + ' ' + price + '</span>',
            '  </div>',
            '</div>'
        ].join('');
    }

    function selectItem(item, input) {
        const tableId = input.dataset.tableId;
        const rowId = input.dataset.rowId;

        if (!tableId || !rowId || !window.EditableTable) {
            hideDropdown();
            return;
        }

        // 回填整行数据
        const instance = window.EditableTable.instances[tableId];
        if (!instance) {
            hideDropdown();
            return;
        }

        const rowData = instance.rows.find(function(r) { return r.rowId === rowId; });
        if (!rowData) {
            hideDropdown();
            return;
        }

        // 更新内存数据
        Object.assign(rowData.data, {
            product_name: item.product_name || '',
            product_model: item.product_model || '',
            product_desc: item.product_desc || '',
            brand: item.brand || '',
            unit: item.unit || '个',
            product_mn: item.product_mn || '',
            market_price: item.market_price || 0,
            currency: item.currency || 'CNY'
        });

        // 同步更新 DOM
        const row = document.getElementById(rowId);
        if (row) {
            const fieldMap = {
                product_name: item.product_name || '',
                product_model: item.product_model || '',
                product_desc: item.product_desc || '',
                brand: item.brand || '',
                unit: item.unit || '',
                product_mn: item.product_mn || '',
                market_price: item.market_price || 0
            };

            Object.keys(fieldMap).forEach(function(key) {
                const value = fieldMap[key];
                // 优先找 input
                const inputEl = row.querySelector('input[data-col-key="' + key + '"]');
                if (inputEl) {
                    inputEl.value = key === 'market_price'
                        ? window.EditableTable.formatNumber(value)
                        : value;
                    return;
                }
                // 再找只读 span
                const spanEl = row.querySelector('span[data-col-key="' + key + '"]');
                if (spanEl) {
                    spanEl.textContent = key === 'market_price'
                        ? window.EditableTable.formatNumber(value)
                        : value;
                    // 如果是 product_mn，去掉占位样式
                    if (key === 'product_mn' && value) {
                        spanEl.classList.remove('cpa-placeholder');
                    }
                    return;
                }
            });
        }

        // 重新计算 unit_price / total_price
        if (window.EditableTable.calculateUnitPrice) {
            window.EditableTable.calculateUnitPrice(tableId, rowId);
        }
        if (window.EditableTable.calculateTotalPrice) {
            window.EditableTable.calculateTotalPrice(tableId, rowId);
        }

        // 更新隐藏数据
        if (window.EditableTable.updateHiddenData) {
            window.EditableTable.updateHiddenData(tableId);
        }

        hideDropdown();
    }

    function hideDropdown() {
        if (currentDropdown) {
            currentDropdown.remove();
            currentDropdown = null;
        }
    }

    function positionDropdown(dropdown, input) {
        const rect = input.getBoundingClientRect();
        dropdown.style.position = 'fixed';
        dropdown.style.top = (rect.bottom + 2) + 'px';
        dropdown.style.left = rect.left + 'px';
        dropdown.style.minWidth = Math.max(rect.width, 320) + 'px';
        dropdown.style.zIndex = '10000';
    }

    function applyDropdownStyle(dropdown) {
        Object.assign(dropdown.style, {
            backgroundColor: 'white',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
            maxHeight: '320px',
            overflowY: 'auto',
            fontSize: '13px'
        });
    }

    function formatMoney(value) {
        const num = parseFloat(value) || 0;
        return num.toLocaleString('zh-CN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str == null ? '' : String(str);
        return div.innerHTML;
    }

    // 暴露全局对象
    window.CustomProductAutocomplete = {
        attach: attach,
        hideDropdown: hideDropdown
    };

    // 注入基础样式
    if (!document.getElementById('custom-product-autocomplete-styles')) {
        const style = document.createElement('style');
        style.id = 'custom-product-autocomplete-styles';
        style.textContent = [
            '.custom-product-autocomplete-dropdown .cpa-item {',
            '  padding: 8px 12px;',
            '  cursor: pointer;',
            '  border-bottom: 1px solid #f1f5f9;',
            '}',
            '.custom-product-autocomplete-dropdown .cpa-item:last-child {',
            '  border-bottom: none;',
            '}',
            '.custom-product-autocomplete-dropdown .cpa-item:hover {',
            '  background-color: #f8fafc;',
            '}',
            '.custom-product-autocomplete-dropdown .cpa-item-head {',
            '  display: flex;',
            '  align-items: center;',
            '  justify-content: space-between;',
            '  gap: 8px;',
            '}',
            '.custom-product-autocomplete-dropdown .cpa-name {',
            '  font-weight: 500;',
            '  color: #0f172a;',
            '}',
            '.custom-product-autocomplete-dropdown .cpa-usage {',
            '  font-size: 11px;',
            '  color: #94a3b8;',
            '  flex-shrink: 0;',
            '}',
            '.custom-product-autocomplete-dropdown .cpa-item-meta {',
            '  font-size: 11px;',
            '  color: #64748b;',
            '  margin-top: 2px;',
            '}',
            '.custom-product-autocomplete-dropdown .cpa-empty {',
            '  padding: 12px;',
            '  text-align: center;',
            '  color: #94a3b8;',
            '  font-size: 12px;',
            '}',
            '.cpa-placeholder {',
            '  color: #cbd5e1 !important;',
            '  font-style: italic;',
            '}',
            '@media (prefers-color-scheme: dark) {',
            '  .custom-product-autocomplete-dropdown {',
            '    background-color: #1e293b !important;',
            '    border-color: #334155 !important;',
            '    color: #e2e8f0 !important;',
            '  }',
            '  .custom-product-autocomplete-dropdown .cpa-item {',
            '    border-bottom-color: #334155 !important;',
            '  }',
            '  .custom-product-autocomplete-dropdown .cpa-item:hover {',
            '    background-color: #334155 !important;',
            '  }',
            '  .custom-product-autocomplete-dropdown .cpa-name {',
            '    color: #f1f5f9 !important;',
            '  }',
            '}'
        ].join('\n');
        document.head.appendChild(style);
    }
})();
