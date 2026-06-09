/**
 * AT 序号查询(扫码 / 手输)
 *
 * 行为:
 *   - 防抖 300ms 调 /product-sn/api/search
 *   - 精确匹配 → 直接跳详情(snDetailUrlPrefix + id)
 *   - 模糊匹配 → 列出最多 20 条结果(可点击行跳详情)
 *   - 空输入 → 显示 empty state
 */
(function () {
  'use strict';

  const $input  = document.getElementById('snSearchInput');
  const $clear  = document.getElementById('snClearBtn');
  const $results = document.getElementById('snResults');
  if (!$input || !$results) return;

  const META  = window.SN_STATUS_META || {};
  const URL_P = window.SN_DETAIL_URL_PREFIX || '/product-sn/';
  const csrf  = document.querySelector('meta[name="csrf-token"]')?.content || '';

  const STORAGE_KEY = 'at-sn-last-query';
  let timer = null;
  let lastQuery = '';

  function detailUrl(id) { return URL_P + id; }

  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, c =>
      ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  }

  function renderEmpty(msg, iconHint) {
    $results.innerHTML = `
      <div style="text-align:center;padding:48px 12px;color:var(--ink-4);">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
          ${iconHint || '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>'}
        </svg>
        <div style="margin-top:12px;font-size:13px;">${escapeHtml(msg)}</div>
      </div>`;
  }

  function renderLoading() {
    $results.innerHTML = `
      <div style="text-align:center;padding:36px 12px;color:var(--ink-4);font-size:13px;">
        查询中…
      </div>`;
  }

  function renderPill(status) {
    const m = META[status] || {label: status, bg: 'var(--bg-page)', fg: 'var(--ink-3)'};
    return `<span style="display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;
                         background:${m.bg};color:${m.fg};font-size:11px;font-weight:500;">${escapeHtml(m.label)}</span>`;
  }

  function renderFuzzy(results, total, q) {
    if (!results.length) {
      renderEmpty(`未找到包含 "${q}" 的序号`);
      return;
    }
    const moreHint = total > results.length
      ? `<div class="at-dim" style="text-align:center;padding:10px 0;font-size:11.5px;">
           还有 ${total - results.length} 条结果未显示,请输入更完整的关键词
         </div>`
      : '';
    const rows = results.map(sn => `
      <div class="at-sn-row" data-sn-id="${sn.id}" data-expanded="0">
        <button type="button" class="at-sn-row-toggle"
                style="display:flex;align-items:center;gap:14px;width:100%;padding:12px 16px;
                       border:0;border-bottom:1px solid var(--line);background:transparent;
                       color:inherit;cursor:pointer;text-align:left;transition:background 120ms;font:inherit;"
                onmouseover="this.style.background='var(--bg-page)'"
                onmouseout="if(this.parentElement.dataset.expanded!=='1')this.style.background='transparent'">
          <span class="at-mono at-tab-num" style="font-size:13px;color:var(--ink);min-width:160px;">
            ${escapeHtml(sn.serial_number)}
          </span>
          <span style="flex:1;min-width:0;font-size:13px;color:var(--ink-2);
                       overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
            ${escapeHtml(sn.product_name || '')}
            ${sn.product_model ? `<span class="at-dim" style="margin-left:6px;">${escapeHtml(sn.product_model)}</span>` : ''}
          </span>
          ${renderPill(sn.status)}
          <span class="at-sn-row-chev" style="color:var(--ink-4);transition:transform 180ms;
                                              display:inline-flex;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m6 9 6 6 6-6"/>
            </svg>
          </span>
        </button>
        <div class="at-sn-row-body" style="display:none;background:var(--bg-page);
                                            border-bottom:1px solid var(--line);"></div>
      </div>
    `).join('');

    $results.innerHTML = `
      <div style="background:var(--bg-elev);border:1px solid var(--line);border-radius:10px;overflow:hidden;">
        <div style="padding:10px 16px;font-size:11.5px;color:var(--ink-3);letter-spacing:0.04em;
                    border-bottom:1px solid var(--line);background:var(--bg-page);">
          找到 <span class="at-mono at-tab-num" style="color:var(--ink-2);">${total}</span> 条结果 · 点击行展开预览
        </div>
        ${rows}
        ${moreHint}
      </div>`;

    // 绑定展开
    $results.querySelectorAll('.at-sn-row').forEach(row => {
      const btn  = row.querySelector('.at-sn-row-toggle');
      const body = row.querySelector('.at-sn-row-body');
      const chev = row.querySelector('.at-sn-row-chev');
      btn.addEventListener('click', () => toggleExpand(row, btn, body, chev));
    });
  }

  function toggleExpand(row, btn, body, chev) {
    const isOpen = row.dataset.expanded === '1';
    if (isOpen) {
      body.style.display = 'none';
      row.dataset.expanded = '0';
      chev.style.transform = 'rotate(0)';
      btn.style.background = 'transparent';
      return;
    }
    // 关闭其它已展开行(保持一次只开一个)
    $results.querySelectorAll('.at-sn-row[data-expanded="1"]').forEach(r => {
      r.dataset.expanded = '0';
      r.querySelector('.at-sn-row-body').style.display = 'none';
      r.querySelector('.at-sn-row-chev').style.transform = 'rotate(0)';
      r.querySelector('.at-sn-row-toggle').style.background = 'transparent';
    });

    row.dataset.expanded = '1';
    chev.style.transform = 'rotate(180deg)';
    btn.style.background = 'var(--bg-page)';

    // 已有 body 内容则直接显示
    if (body.dataset.loaded === '1') {
      body.style.display = 'block';
      return;
    }
    body.innerHTML = `<div class="at-dim" style="padding:16px;text-align:center;font-size:12px;">加载中…</div>`;
    body.style.display = 'block';

    const snId = row.dataset.snId;
    fetch(`/product-sn/api/${snId}`, { headers: { 'X-CSRFToken': csrf } })
      .then(r => r.json())
      .then(res => {
        if (!res.success) {
          body.innerHTML = `<div class="at-dim" style="padding:16px;text-align:center;color:var(--danger);">加载失败</div>`;
          return;
        }
        body.innerHTML = renderPreview(res.sn);
        body.dataset.loaded = '1';
      })
      .catch(err => {
        body.innerHTML = `<div class="at-dim" style="padding:16px;text-align:center;color:var(--danger);">${escapeHtml(String(err))}</div>`;
      });
  }

  function renderPreview(sn) {
    const fields = [
      ['采购订单', sn.purchase_order_number],
      ['供应商',  sn.supplier_name],
      ['入库位置', sn.warehouse_location],
      ['入库日期', sn.warehouse_in_date],
      ['所属库存', sn.inventory_company],
      ['客户订单', sn.sales_order_number],
      ['发货单',   sn.shipment_number],
      ['客户',     sn.customer_name],
    ].filter(([, v]) => v);  // 隐藏空字段

    const grid = fields.map(([k, v]) => `
      <div style="display:flex;gap:8px;font-size:12.5px;line-height:1.6;">
        <span class="at-dim" style="min-width:64px;">${k}</span>
        <span style="color:var(--ink);flex:1;">${escapeHtml(String(v))}</span>
      </div>
    `).join('');

    return `
      <div style="padding:16px 20px;">
        ${fields.length ? `<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px 24px;margin-bottom:14px;">${grid}</div>`
                        : `<div class="at-dim" style="text-align:center;padding:8px 0 14px;font-size:12px;">该 SN 暂无更多关联信息</div>`}
        <div style="display:flex;justify-content:flex-end;">
          <a href="${detailUrl(sn.id)}"
             style="display:inline-flex;align-items:center;gap:6px;height:30px;padding:0 14px;
                    background:var(--accent);color:#fff;font-size:12.5px;border-radius:6px;
                    text-decoration:none;">
            查看完整详情
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m9 18 6-6-6-6"/>
            </svg>
          </a>
        </div>
      </div>`;
  }

  function doSearch(q) {
    if (!q) {
      $results.innerHTML = `
        <div style="text-align:center;padding:48px 12px;color:var(--ink-4);">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>
          </svg>
          <div style="margin-top:12px;font-size:13px;">输入 SN 开始查询</div>
        </div>`;
      return;
    }

    renderLoading();
    fetch(`/product-sn/api/search?q=${encodeURIComponent(q)}`, {
      headers: { 'X-CSRFToken': csrf }
    })
      .then(r => r.json())
      .then(res => {
        if (q !== lastQuery) return;   // 过时响应丢弃
        if (!res.success) {
          renderEmpty(res.message || '查询失败');
          return;
        }
        if (res.mode === 'exact' && res.results.length === 1) {
          // 精确命中 → 跳详情
          window.location.href = detailUrl(res.results[0].id);
        } else {
          renderFuzzy(res.results || [], res.total || 0, q);
        }
      })
      .catch(err => {
        if (q !== lastQuery) return;
        renderEmpty('查询失败:' + err);
      });
  }

  $input.addEventListener('input', () => {
    const q = $input.value.trim();
    lastQuery = q;
    $clear.style.display = q ? 'inline-flex' : 'none';
    // 记住搜索词;详情页返回时自动恢复
    if (q) sessionStorage.setItem(STORAGE_KEY, q);
    else sessionStorage.removeItem(STORAGE_KEY);
    clearTimeout(timer);
    timer = setTimeout(() => doSearch(q), 300);
  });

  $input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      clearTimeout(timer);
      doSearch($input.value.trim());
    } else if (e.key === 'Escape' && $input.value) {
      $input.value = '';
      lastQuery = '';
      $clear.style.display = 'none';
      doSearch('');
    }
  });

  $input.addEventListener('focus', () => {
    $input.style.borderColor = 'var(--accent)';
    $input.style.boxShadow = '0 0 0 3px var(--accent-tint)';
  });
  $input.addEventListener('blur', () => {
    $input.style.borderColor = 'var(--line-2)';
    $input.style.boxShadow = 'none';
  });

  $clear.addEventListener('click', () => {
    $input.value = '';
    lastQuery = '';
    $clear.style.display = 'none';
    sessionStorage.removeItem(STORAGE_KEY);
    doSearch('');
    $input.focus();
  });

  // ─── 启动时从 sessionStorage 恢复上次搜索 ───
  // 场景:从详情页点"返回"回到列表,自动重放上次查询
  const restored = sessionStorage.getItem(STORAGE_KEY);
  if (restored) {
    $input.value = restored;
    lastQuery = restored;
    $clear.style.display = 'inline-flex';
    doSearch(restored);
  }
})();

