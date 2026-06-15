/**
 * AT 订单明细表 · 可复用控制器
 *
 * 管理一张 10 列可编辑明细表(产品/型号/编码/规格/数量/单位/单价/金额/删除)+ 拖拽排序 +
 * 货币切换 + 实时合计。通过回调与调用方协作:
 *
 *   ATItemTable.init({
 *     onAddProduct:  function (replaceKey) { ... 打开产品挑选器 ... },
 *     onImportNeeds: function () { ... 打开客户需求池 ... },
 *     onChange:      function (items, total, currency) { ... 联动表单提交按钮等 ... }
 *   });
 *
 *   ATItemTable.addItem({id, name, model, code, spec, price, unit});
 *   ATItemTable.replaceItem(key, p);
 *   ATItemTable.removeItem(key);
 *   ATItemTable.getItems()   → 当前明细数组
 *   ATItemTable.getCurrency()→ CNY | USD | EUR | HKD
 *   ATItemTable.getTotal()   → 合计金额(数字)
 *   ATItemTable.clear()
 *
 * 依赖 at_item_table_section 宏注入的 DOM:
 *   #atItBody, #atItEmpty, #atItEmptyAdd, #atItAddBtn, #atItImportBtn,
 *   #atItCurrency, #atItTotal
 */
(function (window) {
    const CURRENCY_SYM = { CNY: '¥', USD: '$', EUR: '€', HKD: 'HK$',
                           SGD: 'S$', MYR: 'RM', IDR: 'Rp', THB: '฿',
                           GBP: '£', JPY: '¥', AUD: 'A$', CAD: 'C$' };

    const State = {
        items: [],
        draggingKey: null,
        // 外部强制设置的货币(setCurrency 调用),优先级高于内置 <select>
        currencyOverride: null,
        // 显示「市场价 / 折扣率」两列(SO/报价单用,PO 不用)
        // - true:price 字段变只读,由 marketPrice × discount/100 自动算
        // - false:用户直接编辑 price(默认,PO 行为)
        showMarketDiscount: false,
        // 回调
        onAddProduct:  null,
        onImportNeeds: null,
        onChange:      null,
    };

    // 折扣率(0-100)→ 实际单价
    function _calcPrice(item) {
        if (!State.showMarketDiscount) return Number(item.price) || 0;
        const mp = Number(item.marketPrice) || 0;
        const d = Number(item.discount);
        const eff = (d == null || isNaN(d)) ? 100 : d;
        return +(mp * eff / 100).toFixed(2);
    }

    function _normalizeForMarketDiscount(it) {
        if (!State.showMarketDiscount) return it;
        // 默认 marketPrice = 初次传入的 price(产品库价)
        if (it.marketPrice == null) it.marketPrice = Number(it.price) || 0;
        if (it.discount == null) it.discount = 100;
        it.price = _calcPrice(it);  // 重算 price = market * discount/100
        return it;
    }

    function el(id) { return document.getElementById(id); }
    function escapeHtml(s) {
        return String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
    }
    function currentCurrency() {
        return State.currencyOverride || el('atItCurrency')?.value || 'CNY';
    }
    function currencySym() {
        return CURRENCY_SYM[currentCurrency()] || '¥';
    }
    function fmt(n) {
        return Number(n || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    // 在 SO 模式下,在"单价"列前插入"折扣率"列(单价仍展示,但只读 = 市场价 × 折扣)
    function _maybeInjectMdHeader() {
        if (!State.showMarketDiscount) return;
        const body = el('atItBody');
        if (!body) return;
        const tr = body.closest('table')?.querySelector('thead tr');
        if (!tr || tr.dataset.mdInjected) return;
        const ths = tr.querySelectorAll('th');
        // 列序假设(原 10 列):0 handle, 1 产品, 2 型号, 3 编码, 4 规格, 5 数量, 6 单位, 7 单价, 8 金额, 9 del
        const targetUnitPriceTh = ths[7];
        if (!targetUnitPriceTh) return;
        const th = document.createElement('th');
        th.textContent = t('折扣率');
        th.style.cssText = targetUnitPriceTh.style.cssText;
        th.style.width = '74px';
        th.style.textAlign = 'right';
        tr.insertBefore(th, targetUnitPriceTh);
        tr.dataset.mdInjected = '1';
    }

    // tbody 列总数(空态 colspan 用)
    function _colCount() {
        return State.showMarketDiscount ? 11 : 10;
    }

    // ─── 公开 API ─────────────────────────────────
    function init(opts) {
        opts = opts || {};
        State.onAddProduct  = opts.onAddProduct  || State.onAddProduct;
        State.onImportNeeds = opts.onImportNeeds || State.onImportNeeds;
        State.onChange      = opts.onChange      || State.onChange;
        if (typeof opts.showMarketDiscount === 'boolean') {
            State.showMarketDiscount = opts.showMarketDiscount;
        }
        _maybeInjectMdHeader();

        // 按钮点击
        const emptyAddBtn = el('atItEmptyAdd');
        if (emptyAddBtn && !emptyAddBtn.dataset.bound) {
            emptyAddBtn.dataset.bound = '1';
            emptyAddBtn.addEventListener('click', () => State.onAddProduct && State.onAddProduct(null));
        }
        const addBtn = el('atItAddBtn');
        if (addBtn && !addBtn.dataset.bound) {
            addBtn.dataset.bound = '1';
            addBtn.addEventListener('click', () => State.onAddProduct && State.onAddProduct(null));
        }
        const importBtn = el('atItImportBtn');
        if (importBtn && !importBtn.dataset.bound) {
            importBtn.dataset.bound = '1';
            importBtn.addEventListener('click', () => State.onImportNeeds && State.onImportNeeds());
        }
        const curSel = el('atItCurrency');
        if (curSel && !curSel.dataset.bound) {
            curSel.dataset.bound = '1';
            curSel.addEventListener('change', () => render());
        }
        render();
    }

    function addItem(p) {
        if (!p) return;
        const incomingQty = Number(p.qty) || 1;
        // 合并逻辑:product_id 相同 + sales_order_detail_id 相同(null 也算)→ 累加 qty,不 push 新行
        // 自定义产品(无 product_id)不合并,各自一行
        if (p.id) {
            const sodId = p.sales_order_detail_id || null;
            const existing = State.items.find(it => it.product_id === p.id && (it.sales_order_detail_id || null) === sodId);
            if (existing) {
                existing.qty = (Number(existing.qty) || 0) + incomingQty;
                // SO 模式:qty 变动后重算行价
                if (State.showMarketDiscount) existing.price = _calcPrice(existing);
                render();
                return;
            }
        }
        const newItem = {
            key: `${p.id || 'x'}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
            product_id: p.id, name: p.name, model: p.model || '',
            code: p.code || '', spec: p.spec || '',
            qty: incomingQty, unit: p.unit || t('套'), price: Number(p.price) || 0,
            // 透传可选元数据(如客户需求池导入时携带的 SO 关联信息)
            sales_order_detail_id: p.sales_order_detail_id || null,
            sales_order_id:        p.sales_order_id || null,
            order_number:          p.order_number || '',
            customer_name:         p.customer_name || '',
        };
        // SO/报价单模式:把首次入参 price 视为 marketPrice,默认 100% 折扣
        if (State.showMarketDiscount) {
            newItem.marketPrice = (p.marketPrice != null) ? Number(p.marketPrice) : (Number(p.price) || 0);
            newItem.discount = (p.discount != null) ? Number(p.discount) : 100;
            newItem.price = _calcPrice(newItem);
        }
        State.items.push(newItem);
        render();
    }

    function replaceItem(key, p) {
        if (!key || !p) return;
        const idx = State.items.findIndex(x => x.key === key);
        if (idx >= 0) {
            const updated = {
                ...State.items[idx],
                product_id: p.id, name: p.name, model: p.model || '',
                code: p.code || '', spec: p.spec || '',
                price: Number(p.price) || 0,
            };
            // SO 模式:新产品价格视为新 marketPrice,保留原 discount,重算 price
            if (State.showMarketDiscount) {
                updated.marketPrice = (p.marketPrice != null) ? Number(p.marketPrice) : (Number(p.price) || 0);
                if (updated.discount == null) updated.discount = 100;
                updated.price = _calcPrice(updated);
            }
            State.items[idx] = updated;
            render();
        }
    }

    function removeItem(keyOrIdx) {
        const idx = (typeof keyOrIdx === 'number')
            ? keyOrIdx
            : State.items.findIndex(x => x.key === keyOrIdx);
        if (idx >= 0) {
            State.items.splice(idx, 1);
            render();
        }
    }

    function setItems(arr) {
        const list = Array.isArray(arr) ? arr.slice() : [];
        // SO 模式:批量刷新货币后,price 字段被外部填回的是"新货币市场价" → 当作 marketPrice 重新算
        if (State.showMarketDiscount) {
            list.forEach(it => {
                // 若外部明确给了 marketPrice,以 marketPrice 为准;否则把 price 视为 marketPrice
                if (it.marketPrice == null && it.price != null) {
                    it.marketPrice = Number(it.price) || 0;
                }
                if (it.discount == null) it.discount = 100;
                it.price = _calcPrice(it);
            });
        }
        State.items = list;
        render();
    }

    function getItems() {
        return State.items.map(it => ({ ...it }));
    }

    function getCurrency() {
        return currentCurrency();
    }

    function setCurrency(code) {
        // 外部强制设置(允许任意 ISO 货币码,内置 select 无对应项时不报错)
        State.currencyOverride = code ? String(code).toUpperCase() : null;
        // 若内置 <select> 有对应项,同步选中以保持 UI 一致
        const sel = el('atItCurrency');
        if (sel && State.currencyOverride) {
            const opt = Array.from(sel.options).find(o => o.value === State.currencyOverride);
            if (opt) sel.value = State.currencyOverride;
        }
        render();
    }

    function getTotal() {
        return State.items.reduce((s, it) => s + (Number(it.qty) || 0) * (Number(it.price) || 0), 0);
    }

    function isEmpty() { return State.items.length === 0; }

    function clear() { State.items = []; render(); }

    // ─── 渲染 ─────────────────────────────────────
    function render() {
        const tbody = el('atItBody');
        const totalEl = el('atItTotal');
        const sym = currencySym();

        if (!State.items.length) {
            tbody.innerHTML = `
                <tr id="atItEmpty">
                    <td colspan="${_colCount()}" style="padding:0;">
                        <button type="button" onmouseenter="this.style.background='var(--bg-hover)'"
                                onmouseleave="this.style.background='transparent'"
                                onclick="window.ATItemTable && ATItemTable._emptyClick && ATItemTable._emptyClick()"
                                style="width:100%;padding:18px 14px;display:flex;align-items:center;justify-content:flex-start;gap:10px;
                                       color:var(--ink-3);font-size:13px;border-top:1px solid var(--line-soft);
                                       background:transparent;border:0;border-top:1px solid var(--line-soft);cursor:pointer;transition:background 100ms;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"/></svg>
                            ${t('点击选择产品…')}
                        </button>
                    </td>
                </tr>`;
            if (totalEl) totalEl.textContent = sym + '0.00';
            notify();
            return;
        }

        const ellipsis = 'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;';
        let total = 0;
        tbody.innerHTML = State.items.map((it, i) => {
            const amount = (Number(it.qty) || 0) * (Number(it.price) || 0);
            total += amount;
            return `
                <tr data-row-key="${escapeHtml(it.key)}" data-row-idx="${i}" draggable="true"
                    style="border-top:1px solid var(--line-soft);transition:background 100ms;">
                    <td style="padding:12px 6px 12px 12px;vertical-align:middle;cursor:grab;color:var(--ink-4);white-space:nowrap;" title="${t('拖动排序')}">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                            <circle cx="9" cy="6" r="1.5"/><circle cx="15" cy="6" r="1.5"/>
                            <circle cx="9" cy="12" r="1.5"/><circle cx="15" cy="12" r="1.5"/>
                            <circle cx="9" cy="18" r="1.5"/><circle cx="15" cy="18" r="1.5"/>
                        </svg>
                    </td>
                    <td style="padding:12px 14px;vertical-align:middle;max-width:220px;${ellipsis}">
                        <button type="button" data-action="replace" title="${escapeHtml(it.name || '')}"
                                onmouseenter="this.style.borderBottomColor='var(--accent)';this.style.color='var(--accent)';"
                                onmouseleave="this.style.borderBottomColor='transparent';this.style.color='var(--ink)';"
                                style="text-align:left;padding:0;font-weight:500;color:var(--ink);font-size:13.5px;
                                       border:0;border-bottom:1px dashed transparent;background:transparent;cursor:pointer;
                                       max-width:100%;${ellipsis}
                                       transition:border-color 120ms, color 120ms;">${escapeHtml(it.name || '')}</button>
                    </td>
                    <td class="at-mono" style="padding:12px 14px;vertical-align:middle;color:var(--ink-2);max-width:130px;${ellipsis}" title="${escapeHtml(it.model || '')}">${escapeHtml(it.model || '')}</td>
                    <td class="at-mono at-dim" style="padding:12px 14px;vertical-align:middle;font-size:12px;max-width:120px;${ellipsis}" title="${escapeHtml(it.code || '')}">${escapeHtml(it.code || '-')}</td>
                    <td class="at-dim" style="padding:12px 14px;vertical-align:middle;max-width:260px;font-size:11.5px;${ellipsis}" title="${escapeHtml(it.spec || '')}">${escapeHtml(it.spec || '')}</td>
                    <td style="padding:12px 8px;text-align:right;vertical-align:middle;white-space:nowrap;">
                        <input data-field="qty" type="number" min="1" step="1" class="at-mono at-tab-num" value="${it.qty}"
                               style="width:64px;height:28px;padding:0 6px;text-align:right;
                                      border:1px solid var(--line-2);border-radius:4px;
                                      background:var(--bg-elev);outline:none;font-size:13px;">
                    </td>
                    <td style="padding:12px 14px;vertical-align:middle;white-space:nowrap;">
                        <span class="at-dim" style="font-size:12px;">${escapeHtml(it.unit || t('套'))}</span>
                    </td>
                    ${State.showMarketDiscount ? `
                    <td style="padding:12px 8px;text-align:right;vertical-align:middle;white-space:nowrap;">
                        <input data-field="discount" type="number" min="0" step="0.1"
                               class="at-mono at-tab-num" value="${it.discount != null ? it.discount : 100}"
                               style="width:64px;height:28px;padding:0 6px;text-align:right;
                                      border:1px solid var(--line-2);border-radius:4px;
                                      background:var(--bg-elev);outline:none;font-size:12.5px;">
                        <span class="at-dim" style="font-size:11px;margin-left:2px;">%</span>
                    </td>
                    <td class="at-mono at-tab-num" style="padding:12px 14px;text-align:right;vertical-align:middle;white-space:nowrap;font-size:12.5px;color:var(--ink);">
                        ${sym}${fmt(it.price || 0)}
                    </td>
                    ` : `
                    <td style="padding:12px 14px;text-align:right;vertical-align:middle;white-space:nowrap;">
                        <input data-field="price" class="at-mono at-tab-num" value="${it.price}"
                               style="width:84px;height:28px;padding:0 8px;text-align:right;
                                      border:1px solid var(--line-2);border-radius:4px;
                                      background:var(--bg-elev);outline:none;font-size:12.5px;">
                    </td>
                    `}
                    <td class="at-mono at-tab-num" style="padding:12px 14px;text-align:right;font-weight:500;vertical-align:middle;white-space:nowrap;">
                        ${sym}${fmt(amount)}
                    </td>
                    <td style="padding:12px 10px;text-align:right;vertical-align:middle;white-space:nowrap;">
                        <button type="button" data-action="remove" title="${t('移除')}"
                                onmouseenter="this.style.background='var(--danger-soft)';this.style.color='var(--danger)';"
                                onmouseleave="this.style.background='transparent';this.style.color='var(--ink-4)';"
                                style="width:24px;height:24px;border-radius:4px;color:var(--ink-4);
                                       display:inline-flex;align-items:center;justify-content:center;
                                       background:transparent;border:0;cursor:pointer;transition:all 120ms;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                 stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M6 6l12 12M18 6L6 18"/>
                            </svg>
                        </button>
                    </td>
                </tr>`;
        }).join('');
        if (totalEl) totalEl.textContent = sym + fmt(total);

        // 行内事件绑定(委托式,行随 render 重建,所以每次都绑)
        tbody.querySelectorAll('tr[data-row-key]').forEach(tr => {
            const key = tr.dataset.rowKey;
            const idx = parseInt(tr.dataset.rowIdx);
            // 替换 / 删除按钮
            tr.querySelector('button[data-action="replace"]')?.addEventListener('click', () => State.onAddProduct && State.onAddProduct(key));
            tr.querySelector('button[data-action="remove"]')?.addEventListener('click', () => removeItem(key));
            // qty / price 输入
            tr.querySelector('input[data-field="qty"]')?.addEventListener('input', (e) => {
                State.items[idx].qty = Math.max(1, parseInt(e.target.value) || 1);
                updateAmountCell(tr, idx);
                refreshTotal();
                notify();
            });
            tr.querySelector('input[data-field="price"]')?.addEventListener('input', (e) => {
                State.items[idx].price = Math.max(0, parseFloat(e.target.value) || 0);
                updateAmountCell(tr, idx);
                refreshTotal();
                notify();
            });
            // SO 模式:折扣率改变 → 重算 price → 重算 amount(允许 >100% 溢价场景)
            tr.querySelector('input[data-field="discount"]')?.addEventListener('input', (e) => {
                let d = parseFloat(e.target.value);
                if (isNaN(d) || d < 0) d = 0;
                State.items[idx].discount = d;
                State.items[idx].price = _calcPrice(State.items[idx]);
                _refreshSoCells(tr, idx);
                refreshTotal();
                notify();
            });
            // 拖拽
            tr.addEventListener('dragstart', (e) => {
                State.draggingKey = key;
                e.dataTransfer.effectAllowed = 'move';
                try { e.dataTransfer.setData('text/plain', key); } catch (_) {}
                tr.style.opacity = '0.4';
                tr.style.background = 'var(--bg-hover)';
            });
            tr.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                if (State.draggingKey !== key) tr.style.borderTop = '2px solid var(--accent)';
            });
            tr.addEventListener('dragleave', () => { tr.style.borderTop = '1px solid var(--line-soft)'; });
            tr.addEventListener('drop', (e) => {
                e.preventDefault();
                const from = State.draggingKey, to = key;
                if (from && to && from !== to) {
                    const fi = State.items.findIndex(x => x.key === from);
                    const ti = State.items.findIndex(x => x.key === to);
                    if (fi >= 0 && ti >= 0) {
                        const [m] = State.items.splice(fi, 1);
                        State.items.splice(ti, 0, m);
                    }
                }
                State.draggingKey = null;
                render();
            });
            tr.addEventListener('dragend', () => {
                State.draggingKey = null;
                tr.style.opacity = '1';
                tr.style.background = 'transparent';
                tr.style.borderTop = '1px solid var(--line-soft)';
            });
        });

        notify();
    }

    function updateAmountCell(tr, idx) {
        const sym = currencySym();
        const amount = (Number(State.items[idx].qty) || 0) * (Number(State.items[idx].price) || 0);
        // PO 模式列序:handle/name/model/code/spec/qty/unit/price/amount/del → amount = children[8]
        // SO 模式列序:handle/name/model/code/spec/qty/unit/discount/price/amount/del → amount = children[9]
        const amountIdx = State.showMarketDiscount ? 9 : 8;
        if (tr && tr.children[amountIdx]) tr.children[amountIdx].textContent = sym + fmt(amount);
    }

    // SO 模式专用:折扣率变化时刷新「单价」与「金额」两个只读单元格
    function _refreshSoCells(tr, idx) {
        if (!tr) return;
        const sym = currencySym();
        const it = State.items[idx];
        // children[8] = 单价(只读),children[9] = 金额
        if (tr.children[8]) tr.children[8].textContent = sym + fmt(it.price || 0);
        const amount = (Number(it.qty) || 0) * (Number(it.price) || 0);
        if (tr.children[9]) tr.children[9].textContent = sym + fmt(amount);
    }

    function refreshTotal() {
        const sym = currencySym();
        let t = 0;
        State.items.forEach(it => { t += (Number(it.qty) || 0) * (Number(it.price) || 0); });
        const el2 = el('atItTotal');
        if (el2) el2.textContent = sym + fmt(t);
    }

    function notify() {
        if (typeof State.onChange === 'function') {
            try { State.onChange(getItems(), getTotal(), getCurrency()); }
            catch (e) { console.error('[ATItemTable] onChange error:', e); }
        }
    }

    // 内部桥接:空状态按钮也走 onAddProduct
    function _emptyClick() { if (State.onAddProduct) State.onAddProduct(null); }

    window.ATItemTable = {
        init, addItem, replaceItem, removeItem,
        setItems, getItems, getCurrency, setCurrency, getTotal,
        isEmpty, clear,
        _emptyClick,
    };
})(window);
