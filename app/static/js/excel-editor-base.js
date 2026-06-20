/**
 * excel-editor-base.js
 * Excel 风格编辑器共享逻辑：Tab 切换、审批抽屉、列显示、关闭菜单
 */
const ExcelEditorBase = (() => {

  /* ── Tab 切换 ── */
  function initTabs(tabSelector, panelSelector) {
    const tabs = document.querySelectorAll(tabSelector);
    const panels = document.querySelectorAll(panelSelector);

    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const target = tab.dataset.tab;
        tabs.forEach(t => {
          const active = t.dataset.tab === target;
          t.classList.toggle('border-blue-600', active);
          t.classList.toggle('text-blue-600', active);
          t.classList.toggle('border-transparent', !active);
          t.classList.toggle('text-slate-500', !active);
        });
        panels.forEach(p => {
          p.classList.toggle('hidden', p.dataset.panel !== target);
        });
      });
    });
  }

  /* ── 审批抽屉 ── */
  function initApprovalDrawer(btnId, drawerId, paperId) {
    const btn = document.getElementById(btnId);
    const drawer = document.getElementById(drawerId);
    const paper = document.getElementById(paperId);
    if (!btn || !drawer) return;

    btn.addEventListener('click', () => {
      const isOpen = drawer.classList.toggle('open');
      if (paper) paper.classList.toggle('drawer-open', isOpen);
      btn.textContent = isOpen ? '收起 ‹' : '审批流程 ›';
    });

    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && drawer.classList.contains('open')) {
        drawer.classList.remove('open');
        if (paper) paper.classList.remove('drawer-open');
        btn.textContent = '审批流程 ›';
      }
    });
  }

  /* ── 显示列 切换 ── */
  function toggleCol(tableId, colClass, visible) {
    const table = document.getElementById(tableId);
    if (!table) return;
    table.querySelectorAll('.' + colClass).forEach(cell => {
      cell.classList.toggle('hidden-col', !visible);
    });
  }

  /* ── 点击外部关闭浮层菜单 ── */
  function initOutsideClose(...menuIds) {
    document.addEventListener('click', e => {
      menuIds.forEach(id => {
        const el = document.getElementById(id);
        if (el && !el.classList.contains('hidden') && !el.contains(e.target)) {
          el.classList.add('hidden');
        }
      });
    });
  }

  /* ── 金额自动计算 ── */
  function calcRowAmounts(row, opts = {}) {
    const {
      marketSel  = '.cell-market',
      discSel    = '.cell-discount',
      priceSel   = '.cell-price',
      qtySel     = '.cell-qty',
      subtotalSel= '.cell-subtotal',
    } = opts;

    const getVal = sel => {
      const el = row.querySelector(sel);
      return el ? parseFloat(el.value) || 0 : 0;
    };
    const setVal = (sel, v) => {
      const el = row.querySelector(sel);
      if (el) el.value = v.toFixed(2);
    };

    const market   = getVal(marketSel);
    const disc     = getVal(discSel);      // 0-100 的百分比
    const qty      = getVal(qtySel);
    const price    = market * (disc / 100);
    const subtotal = price * qty;

    setVal(priceSel, price);
    setVal(subtotalSel, subtotal);
    return { price, subtotal };
  }

  /* ── 行拖拽排序（简单版：mousedown→mousemove→mouseup）── */
  function initRowDragSort(tbodyId, handleSel, onSorted) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;

    let dragging = null, placeholder = null;

    tbody.addEventListener('mousedown', e => {
      const handle = e.target.closest(handleSel);
      if (!handle) return;
      const row = handle.closest('tr');
      if (!row) return;

      e.preventDefault();
      dragging = row;
      row.classList.add('dragging');

      placeholder = document.createElement('tr');
      placeholder.style.height = row.offsetHeight + 'px';
      placeholder.style.opacity = '0';
      row.parentNode.insertBefore(placeholder, row.nextSibling);
    });

    document.addEventListener('mousemove', e => {
      if (!dragging) return;
      const rows = [...tbody.querySelectorAll('tr:not(.dragging)')];
      const after = rows.find(r => {
        const box = r.getBoundingClientRect();
        return e.clientY < box.top + box.height / 2;
      });
      tbody.insertBefore(dragging, after || null);
    });

    document.addEventListener('mouseup', () => {
      if (!dragging) return;
      dragging.classList.remove('dragging');
      placeholder && placeholder.remove();
      dragging = null;
      placeholder = null;
      if (onSorted) onSorted();
    });
  }

  /* ── 公开接口 ── */
  return { initTabs, initApprovalDrawer, toggleCol, initOutsideClose, calcRowAmounts, initRowDragSort };
})();
