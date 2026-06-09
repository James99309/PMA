/**
 * AT 客户需求池 · 可复用控制器
 *
 * 用法:
 *   ATCustomerNeeds.open({
 *     onImport: function (demands) {
 *       // demands = 选中的 SO 明细数组,每条:
 *       // { sales_order_detail_id, sales_order_id, order_number, customer_name,
 *       //   product_id, product_name, product_model, product_desc,
 *       //   remaining_to_procure, unit, ... }
 *     }
 *   });
 *   ATCustomerNeeds.close();
 *
 * 依赖 at_customer_needs_modal 宏注入的 DOM:
 *   #atCustomerNeedsModal · #atCnSearchInput · #atCnBody · #atCnImportBtn · #atCnImportCount
 *
 * 后端 API:GET /purchase-order/api/procurement-demands?search=
 */
(function (window) {
    const State = {
        modalId: 'atCustomerNeedsModal',
        onImport: null,
        existingPicks: {},   // {sales_order_detail_id: qty 已加入未保存的明细} — 用于扣减剩余可采购
        demands: [],
        picked: new Set(),   // sales_order_detail_id 集合
        searchTimer: null,
    };

    function el(id) { return document.getElementById(id); }
    function escapeHtml(s) {
        return String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
    }

    function open(opts) {
        opts = opts || {};
        State.onImport = (typeof opts.onImport === 'function') ? opts.onImport : null;
        State.existingPicks = opts.existingPicks || {};
        State.picked = new Set();
        const searchInput = el('atCnSearchInput');
        if (searchInput) searchInput.value = '';
        el(State.modalId).style.display = 'flex';
        updateImportBtn();
        loadDemands('');
        setTimeout(() => searchInput?.focus(), 50);
    }

    function close() {
        el(State.modalId).style.display = 'none';
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && el(State.modalId)?.style.display === 'flex') close();
    });

    function bindSearchOnce() {
        const input = el('atCnSearchInput');
        if (!input || input.dataset.bound) return;
        input.dataset.bound = '1';
        input.addEventListener('input', () => {
            clearTimeout(State.searchTimer);
            State.searchTimer = setTimeout(() => loadDemands(input.value.trim()), 280);
        });
    }

    function bindImportBtnOnce() {
        const btn = el('atCnImportBtn');
        if (!btn || btn.dataset.bound) return;
        btn.dataset.bound = '1';
        btn.addEventListener('click', () => {
            if (!State.picked.size) return;
            // 用 effective(扣减已选未保存后的剩余),让加入 ItemTable 的 qty 不超量
            const picks = (State.demands_view || []).filter(d => State.picked.has(String(d.sales_order_detail_id)))
                .map(d => ({ ...d, remaining_to_procure: d._effective_remaining }));
            close();
            if (State.onImport) {
                try { State.onImport(picks); } catch (e) { console.error('[ATCustomerNeeds] onImport error:', e); }
            }
        });
    }

    function loadDemands(search) {
        bindSearchOnce();
        bindImportBtnOnce();
        const body = el('atCnBody');
        body.innerHTML = `<tr><td colspan="6" style="padding:44px 12px;text-align:center;color:var(--ink-3);font-size:12.5px;border-top:1px solid var(--line-soft);">加载中…</td></tr>`;
        const q = search ? ('?search=' + encodeURIComponent(search)) : '';
        fetch('/purchase-order/api/procurement-demands' + q)
            .then(r => r.json())
            .then(res => {
                State.demands = (res && res.success && Array.isArray(res.demands)) ? res.demands : [];
                renderBody();
            })
            .catch(() => {
                body.innerHTML = `<tr><td colspan="6" style="padding:44px 12px;text-align:center;color:var(--danger);font-size:12.5px;border-top:1px solid var(--line-soft);">加载失败</td></tr>`;
            });
    }

    // 扣减 demand 中"当前 ItemTable 已选未保存"的数量,过滤掉 ≤ 0 的
    function _effectiveDemands() {
        return State.demands.map(d => {
            const reserved = Number(State.existingPicks[d.sales_order_detail_id] || 0);
            const eff = Math.max(0, (d.remaining_to_procure || 0) - reserved);
            return { ...d, _effective_remaining: eff };
        }).filter(d => d._effective_remaining > 0);
    }
    function renderBody() {
        const body = el('atCnBody');
        State.demands_view = _effectiveDemands();
        if (!State.demands_view.length) {
            body.innerHTML = `
                <tr><td colspan="6" style="padding:44px 12px;text-align:center;color:var(--ink-3);font-size:12.5px;border-top:1px solid var(--line-soft);">
                    <div style="margin-bottom:8px;">
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="color:var(--ink-4);">
                            <circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M3 4h2l3 12h11l2-8H7"/>
                        </svg>
                    </div>
                    暂无待采购需求
                </td></tr>`;
            return;
        }
        body.innerHTML = State.demands_view.map(d => {
            const key = String(d.sales_order_detail_id);
            const checked = State.picked.has(key);
            return `
                <tr data-cn-key="${escapeHtml(key)}" style="border-top:1px solid var(--line-soft);cursor:pointer;transition:background 100ms;"
                    onmouseenter="this.style.background='var(--bg-hover)'"
                    onmouseleave="this.style.background='transparent'">
                    <td style="padding:12px 14px;vertical-align:middle;text-align:center;">
                        <input type="checkbox" data-cn-check ${checked ? 'checked' : ''}
                               style="width:14px;height:14px;accent-color:var(--accent);cursor:pointer;">
                    </td>
                    <td class="at-mono" style="padding:12px 14px;vertical-align:middle;color:var(--accent);font-size:12.5px;white-space:nowrap;">${escapeHtml(d.order_number || '')}</td>
                    <td style="padding:12px 14px;vertical-align:middle;color:var(--ink);font-size:13px;">
                        <div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:140px;" title="${escapeHtml(d.customer_name || '')}">${escapeHtml(d.customer_name || '-')}</div>
                    </td>
                    <td style="padding:12px 14px;vertical-align:middle;color:var(--ink);font-size:13px;">
                        <div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:180px;" title="${escapeHtml(d.product_name || '')}">${escapeHtml(d.product_name || '')}</div>
                    </td>
                    <td class="at-mono" style="padding:12px 14px;vertical-align:middle;color:var(--ink-2);font-size:12.5px;">${escapeHtml(d.product_model || '-')}</td>
                    <td class="at-mono at-tab-num" style="padding:12px 14px;text-align:right;vertical-align:middle;font-weight:500;">
                        ${d._effective_remaining} <span class="at-dim" style="font-size:11px;font-weight:400;">${escapeHtml(d.unit || '')}</span>
                    </td>
                </tr>`;
        }).join('');

        body.querySelectorAll('tr[data-cn-key]').forEach(tr => {
            const key = tr.dataset.cnKey;
            const cb = tr.querySelector('input[data-cn-check]');
            const toggle = () => {
                if (State.picked.has(key)) State.picked.delete(key);
                else State.picked.add(key);
                if (cb) cb.checked = State.picked.has(key);
                updateImportBtn();
            };
            tr.addEventListener('click', (e) => {
                if (e.target.tagName === 'INPUT') return;  // checkbox 自己处理
                toggle();
            });
            cb?.addEventListener('change', () => {
                if (cb.checked) State.picked.add(key);
                else State.picked.delete(key);
                updateImportBtn();
            });
        });
    }

    function updateImportBtn() {
        const btn = el('atCnImportBtn');
        const badge = el('atCnImportCount');
        const n = State.picked.size;
        if (btn) {
            btn.disabled = n === 0;
            btn.style.opacity = n === 0 ? '0.5' : '1';
            btn.style.cursor = n === 0 ? 'not-allowed' : 'pointer';
        }
        if (badge) badge.textContent = n > 0 ? ` · ${n}` : '';
    }

    window.ATCustomerNeeds = { open, close };
})(window);
