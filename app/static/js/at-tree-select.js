/*
 * at-tree-select.js — AT 通用「公司 ▸ 部门 ▸ 账户」树形多选组件
 * ─────────────────────────────────────────────────────────────
 * 任何「跨公司/部门选人(选范围)」场景复用:归属授权 / 共享 / 通知抄送 / 范围授权 等。
 * 纯 AT 设计语言、零依赖、自注入样式。
 *
 * 用法:
 *   const tsel = ATTreeSelect.init({
 *     container: 'afPanel',          // 容器 id 或元素
 *     items: [{id, name, company, department, role_display?, badgeHtml?}],
 *     selected: [1,2,3],             // 预选 id(数组或 Set)
 *     canEdit: true,                 // false=只读
 *     excludeIds: [self_id],         // 不显示的 id(如本人)
 *     searchInput: 'afSearch',       // 可选:外部搜索框 id(绑定 input 过滤)
 *     companyFirst: '和源通信…',     // 可选:置顶的公司名
 *     onChange: (set) => {...},      // 选择变化回调(参数为 Set<id>)
 *   });
 *   tsel.getSelected();  // → [id,...]
 *   tsel.setItems(items); tsel.setSelected([...]);
 */
(function (g) {
  'use strict';
  const _t = (g.t) ? g.t : (s => s);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

  if (!document.getElementById('at-tree-select-style')) {
    const st = document.createElement('style');
    st.id = 'at-tree-select-style';
    st.textContent = `
      .at-tsel { font-size:13px; color:var(--ink); }
      .at-tsel-bar { display:flex;align-items:center;gap:10px;margin-bottom:8px;
                     font-size:12px;color:var(--ink-3); }
      .at-tsel-bar a { color:var(--accent);cursor:pointer;text-decoration:none; }
      .at-tsel-empty { padding:20px;text-align:center;color:var(--ink-4);font-size:12.5px; }
      .at-tsel-node { user-select:none; }
      .at-tsel-row { display:flex;align-items:center;gap:8px;padding:5px 6px;border-radius:6px;
                     cursor:pointer;transition:background 100ms; }
      .at-tsel-row:hover { background:var(--bg-elev-2); }
      .at-tsel-chev { width:16px;height:16px;flex-shrink:0;display:inline-flex;align-items:center;
                      justify-content:center;color:var(--ink-4);transition:transform .15s; }
      .at-tsel-chev.collapsed { transform:rotate(-90deg); }
      .at-tsel-chev.leaf { visibility:hidden; }
      .at-tsel-cbx { width:16px;height:16px;flex-shrink:0;border:1.5px solid var(--line-2);
                     border-radius:4px;display:inline-flex;align-items:center;justify-content:center;
                     background:var(--bg);transition:all 100ms; }
      .at-tsel-cbx.on { background:var(--accent);border-color:var(--accent); }
      .at-tsel-cbx.partial { border-color:var(--accent); }
      .at-tsel-cbx.partial::after { content:'';width:8px;height:2px;background:var(--accent);border-radius:1px; }
      .at-tsel-cbx svg { width:11px;height:11px; }
      .at-tsel-disabled .at-tsel-row { cursor:default;opacity:.55; }
      .at-tsel-disabled .at-tsel-row:hover { background:transparent; }
      .at-tsel-co > .at-tsel-row { font-weight:600;color:var(--ink); }
      .at-tsel-dept { margin-left:18px; }
      .at-tsel-dept > .at-tsel-row { color:var(--ink-2); }
      .at-tsel-user { margin-left:36px; }
      .at-tsel-count { font-size:11px;color:var(--ink-4);font-family:var(--font-mono,monospace); }
      .at-tsel-name { flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }
      .at-tsel-role { font-size:11px;color:var(--ink-4);margin-left:4px; }
      .at-tsel-body { max-height:46vh;overflow-y:auto; }
    `;
    document.head.appendChild(st);
  }

  const CHECK = '<svg viewBox="0 0 12 12"><polyline points="1,6 5,10 11,2" stroke="#fff" stroke-width="2" fill="none"/></svg>';
  const CHEV = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>';

  function init(opts) {
    const el = typeof opts.container === 'string' ? document.getElementById(opts.container) : opts.container;
    if (!el) return null;
    const canEdit = opts.canEdit !== false;
    const onChange = typeof opts.onChange === 'function' ? opts.onChange : function () {};
    const companyFirst = opts.companyFirst || '';
    let items = [];
    let selected = new Set();
    let exclude = new Set();
    let openCo = null, openDept = null;   // 手风琴:同级只展开一个;默认全收起
    let term = '';
    let tree = [];                 // [{company, depts:[{dept, users:[item]}]}]

    function buildTree() {
      exclude = new Set((opts.excludeIds || []).map(Number));
      const byCo = new Map();
      items.forEach(u => {
        if (exclude.has(Number(u.id))) return;
        const co = u.company || _t('未归属公司');
        const dp = u.department || _t('未分组');
        if (!byCo.has(co)) byCo.set(co, new Map());
        const m = byCo.get(co);
        if (!m.has(dp)) m.set(dp, []);
        m.get(dp).push(u);
      });
      const cos = [...byCo.keys()].sort((a, b) =>
        (a === companyFirst ? -1 : b === companyFirst ? 1 : a.localeCompare(b, 'zh')));
      tree = cos.map(co => ({
        company: co,
        depts: [...byCo.get(co).entries()].sort((a, b) => a[0].localeCompare(b[0], 'zh'))
          .map(([dp, users]) => ({ dept: dp, users })),
      }));
    }

    const matches = u => !term ||
      ((u.name || '') + ' ' + (u.department || '') + ' ' + (u.company || '')).toLowerCase().includes(term);
    const visUsers = d => d.users.filter(matches);

    function cbxState(ids) {
      let total = 0, on = 0;
      ids.forEach(id => { total++; if (selected.has(id)) on++; });
      if (!total) return '';
      return on === total ? 'on' : (on > 0 ? 'partial' : '');
    }
    const cbxHtml = state => `<span class="at-tsel-cbx ${state}">${state === 'on' ? CHECK : ''}</span>`;

    function render() {
      const parts = [];
      let visTotal = 0;
      tree.forEach((co, ci) => {
        const vd = co.depts.map((d, di) => ({ d, di, vu: visUsers(d) })).filter(x => x.vu.length);
        if (!vd.length) return;
        const coIds = new Set();
        vd.forEach(x => x.vu.forEach(u => coIds.add(Number(u.id))));
        visTotal += coIds.size;
        const coOpen = term ? true : (openCo === ci);
        const coSel = [...coIds].filter(id => selected.has(id)).length;
        parts.push(`<div class="at-tsel-node at-tsel-co">
          <div class="at-tsel-row" data-ci="${ci}">
            <span class="at-tsel-chev ${coOpen ? '' : 'collapsed'}">${CHEV}</span>
            ${cbxHtml(cbxState(coIds))}
            <span class="at-tsel-name">${esc(co.company)}</span>
            <span class="at-tsel-count">${coSel}/${coIds.size}</span>
          </div>`);
        if (coOpen) {
          vd.forEach(({ d, di, vu }) => {
            const dOpen = term ? true : (openCo === ci && openDept === di);
            const dIds = new Set(vu.map(u => Number(u.id)));
            const dSel = [...dIds].filter(id => selected.has(id)).length;
            parts.push(`<div class="at-tsel-node at-tsel-dept">
              <div class="at-tsel-row" data-ci="${ci}" data-di="${di}">
                <span class="at-tsel-chev ${dOpen ? '' : 'collapsed'}">${CHEV}</span>
                ${cbxHtml(cbxState(dIds))}
                <span class="at-tsel-name">${esc(d.dept)}</span>
                <span class="at-tsel-count">${dSel}/${dIds.size}</span>
              </div>`);
            if (dOpen) {
              vu.forEach(u => {
                const id = Number(u.id);
                parts.push(`<div class="at-tsel-node at-tsel-user">
                  <div class="at-tsel-row" data-uid="${id}">
                    <span class="at-tsel-chev leaf">${CHEV}</span>
                    ${cbxHtml(selected.has(id) ? 'on' : '')}
                    <span class="at-tsel-name">${esc(u.name)}${u.badgeHtml || ''}${u.role_display ? `<span class="at-tsel-role">${esc(u.role_display)}</span>` : ''}</span>
                  </div>
                </div>`);
              });
            }
            parts.push('</div>');
          });
        }
        parts.push('</div>');
      });
      const bar = `<div class="at-tsel-bar"><span>${_t('已选')} <b style="color:var(--accent)">${selected.size}</b></span>`
        + (canEdit ? `<a data-act="all">${_t('全选')}</a><a data-act="none">${_t('清空')}</a>` : '')
        + `<span style="flex:1"></span><span>${_t('可选')} ${visTotal}</span></div>`;
      el.innerHTML = `<div class="at-tsel ${canEdit ? '' : 'at-tsel-disabled'}">${bar}<div class="at-tsel-body">${parts.join('') || `<div class="at-tsel-empty">${_t('无匹配人员')}</div>`}</div></div>`;
    }

    function toggleIds(ids, on) {
      ids.forEach(id => { if (on) selected.add(id); else selected.delete(id); });
      onChange(new Set(selected)); render();
    }

    el.addEventListener('click', function (e) {
      const act = e.target.closest('[data-act]');
      if (act && canEdit) {
        if (act.dataset.act === 'all') tree.forEach(co => co.depts.forEach(d => visUsers(d).forEach(u => selected.add(Number(u.id)))));
        else selected.clear();
        onChange(new Set(selected)); render(); return;
      }
      const row = e.target.closest('.at-tsel-row');
      if (!row) return;
      const ci = row.dataset.ci != null ? Number(row.dataset.ci) : null;
      const di = row.dataset.di != null ? Number(row.dataset.di) : null;
      const uid = row.dataset.uid;
      const onCbx = !!e.target.closest('.at-tsel-cbx');

      // 用户行:整行=勾选
      if (uid != null) {
        if (!canEdit) return;
        const id = Number(uid);
        selected.has(id) ? selected.delete(id) : selected.add(id);
        onChange(new Set(selected)); render(); return;
      }
      // 公司/部门行:点复选框=全选其下;点其它区域=手风琴展开/收起
      if (onCbx) {
        if (!canEdit) return;
        if (di != null) {
          const d = tree[ci] && tree[ci].depts[di]; if (!d) return;
          const ids = new Set(visUsers(d).map(u => Number(u.id)));
          toggleIds(ids, cbxState(ids) !== 'on');
        } else if (ci != null) {
          const co = tree[ci]; if (!co) return;
          const ids = new Set(); co.depts.forEach(d => visUsers(d).forEach(u => ids.add(Number(u.id))));
          toggleIds(ids, cbxState(ids) !== 'on');
        }
        return;
      }
      // 手风琴:同级只开一个;搜索态下全展开、不收折
      if (term) return;
      if (di != null) {
        if (openCo === ci && openDept === di) openDept = null;
        else { openCo = ci; openDept = di; }
      } else if (ci != null) {
        if (openCo === ci) { openCo = null; openDept = null; }
        else { openCo = ci; openDept = null; }
      }
      render();
    });

    if (opts.searchInput) {
      const si = typeof opts.searchInput === 'string' ? document.getElementById(opts.searchInput) : opts.searchInput;
      if (si) si.addEventListener('input', function () { term = (si.value || '').trim().toLowerCase(); render(); });
    }

    items = opts.items || [];
    const initSel = opts.selected ? (opts.selected.forEach ? [...opts.selected] : opts.selected) : [];
    selected = new Set(initSel.map(Number));
    buildTree(); render();

    return {
      getSelected: () => [...selected],
      getSelectedSet: () => new Set(selected),
      setSelected(ids) { selected = new Set((ids || []).map(Number)); render(); },
      setItems(newItems) { items = newItems || []; buildTree(); render(); },
      setExclude(ids) { opts.excludeIds = ids || []; buildTree(); render(); },
      render,
    };
  }

  g.ATTreeSelect = { init };
})(window);
