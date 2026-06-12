/**
 * AT 权限矩阵组件(角色默认权限 / 个人权限覆盖 共用)
 * ─────────────────────────────────────────────────────────────
 * 渲染整张权限矩阵到容器,封装:
 *   - 模块分组行 + 查看/新建/编辑/删除联动(去查看清动作;勾动作带查看)
 *   - 数据范围分段开关(.at-seg);只读/操作型模块不渲染动作勾选
 *   - 扩展区:内容筛选(标签|不限|纯文字选项)/ 功能页签(role)/ 更多权限 / 折扣(需新建+编辑)
 *   - person 模式:行级「继承/覆盖」语义 —— 行尾「↺ 继承」(覆盖或有变更时出现),
 *     dirty 行首黄条;来源不单列(继承按钮出现即代表已自定义)
 *
 * 用法:
 *   const sheet = ATPermSheet({ container, canEdit, mode:'role'|'person',
 *                               onChange(), onRevert(moduleId) });
 *   sheet.setData({ modules, permissions, featurePermissions, filterOptions,
 *                   overridden });          // overridden: {module_id:true}(person)
 *   sheet.getPermissions() / getFeaturePermissions() / getDirty() / isOverridden(mid)
 */
(function (g) {
  'use strict';

  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

  const LEVELS = [['personal', '个人'], ['department', '部门'], ['company', '公司'], ['system', '系统']];
  // 天然只读模块(报表/操作型):不渲染动作勾选,保存强制 false
  const VIEW_ONLY_MODULES = ['product_analysis', 'change_history', 'approval', 'notification', 'cli_agent', 'backup'];

  // 组件样式随 JS 注入(一次),使用页零样式重复
  function injectCSS() {
    if (document.getElementById('atPermSheetCSS')) return;
    const st = document.createElement('style');
    st.id = 'atPermSheetCSS';
    st.textContent = `
  .pm-sheet td, .pm-sheet th { padding:4px 8px; }
  .pm-sheet td.cm-name { font-size:12.5px; }
  .pm-group td { background:var(--bg-sunk); text-align:left; font-size:10.5px; font-weight:500;
                 color:var(--ink-3); letter-spacing:0.08em; padding:5px 10px; }
  .pm-chk { width:14px; height:14px; accent-color:var(--accent); cursor:pointer; }
  .pm-chk:disabled { cursor:default; }
  .pm-sheet .at-seg { padding:2px; gap:1px; }
  body.at-page .pm-sheet .at-seg > button { padding:2px 9px; font-size:11px; }
  .pm-filter-row td { background:var(--bg-sunk); text-align:left; padding:8px 14px 10px; }
  .pm-flt-grid { display:grid; grid-template-columns:76px 40px 1fr; row-gap:5px; column-gap:10px;
                 align-items:start; }
  .pm-flt-label { font-size:11px; color:var(--ink-3); padding-top:1px; text-align:left; }
  .pm-flt-chips { display:flex; flex-wrap:wrap; gap:2px 14px; }
  body.at-page .pm-opt { font:inherit; font-size:11px; padding:0; border:0; background:transparent;
            color:var(--ink-4); cursor:pointer; white-space:nowrap; transition:color 100ms; }
  body.at-page .pm-opt:hover { color:var(--ink); }
  body.at-page .pm-opt.on { color:var(--accent); font-weight:600; }
  body.at-page .pm-opt:disabled { cursor:default; }
  .pm-num { display:inline-block; min-width:46px; padding:1px 6px; text-align:right;
            background:var(--bg-page); border:1px solid var(--line-2); border-radius:5px;
            font-size:11px; color:var(--ink); cursor:cell; }
  .pm-num:focus { outline:2px solid var(--accent); outline-offset:-2px; background:var(--bg-elev); }`;
    document.head.appendChild(st);
  }

  g.ATPermSheet = function (cfg) {
    injectCSS();
    const el = typeof cfg.container === 'string' ? document.getElementById(cfg.container) : cfg.container;
    const canEdit = !!cfg.canEdit;
    const person = cfg.mode === 'person';
    let modules = [], perms = {}, featPerms = {}, filterOptions = {}, overridden = {}, dirty = {};

    function permOf(mid) {
      if (!perms[mid]) perms[mid] = { module: mid, can_view: false, can_create: false,
        can_edit: false, can_delete: false, can_change_owner: false, can_export_email: false,
        permission_level: 'personal' };
      return perms[mid];
    }
    const markDirty = mid => { dirty[mid] = true; };
    const fire = () => cfg.onChange && cfg.onChange();

    // ── 交互 ──
    function setField(mid, field, value) {
      const p = permOf(mid);
      p[field] = value;
      if (field === 'can_view' && !value) { p.can_create = p.can_edit = p.can_delete = false; }
      if (field !== 'can_view' && field !== 'permission_level' && value === true && !p.can_view) p.can_view = true;
      markDirty(mid); render(); fire();
    }
    function filterAll(mid, fk) {
      const p = permOf(mid);
      if (p.content_filter) { delete p.content_filter[fk];
        if (!Object.keys(p.content_filter).length) p.content_filter = null; }
      markDirty(mid); render(); fire();
    }
    function filterToggle(mid, fk, key) {
      const p = permOf(mid);
      let list = (p.content_filter && Array.isArray(p.content_filter[fk])) ? [...p.content_filter[fk]] : [];
      const idx = list.indexOf(key);
      if (idx >= 0) list.splice(idx, 1); else list.push(key);
      if (!p.content_filter) p.content_filter = {};
      if (!list.length) delete p.content_filter[fk];
      else p.content_filter[fk] = list;
      if (!Object.keys(p.content_filter).length) p.content_filter = null;
      markDirty(mid); render(); fire();
    }
    function featOn(mid, fid) {
      const mp = featPerms[mid];
      return !mp || mp[fid] === undefined ? true : !!mp[fid];
    }
    function featToggle(mid, fid) {
      if (!featPerms[mid]) featPerms[mid] = {};
      featPerms[mid][fid] = !featOn(mid, fid);
      markDirty(mid); render(); fire();
    }
    function numSet(span, storeMid, field, mid) {
      const raw = (span.textContent || '').replace(/[%\s,]/g, '');
      permOf(storeMid)[field] = raw === '' ? null : (parseFloat(raw) || 0);
      markDirty(mid); if (storeMid !== mid) markDirty(storeMid);
      render(); fire();
    }

    // ── 渲染 ──
    function render() {
      if (!modules.length) {
        el.innerHTML = '<div class="at-dim" style="padding:26px;text-align:center;font-size:12.5px;">无模块数据</div>';
        return;
      }
      const dis = canEdit ? '' : 'disabled';
      let tbody = '', lastGroup = null;
      modules.forEach(m => {
        const p = permOf(m.id);
        const group = m.group || '其他';
        const cols = person ? 7 : 6;
        if (group !== lastGroup) {
          tbody += `<tr class="pm-group"><td colspan="${cols}">${esc(group)}</td></tr>`;
          lastGroup = group;
        }
        const viewOnly = VIEW_ONLY_MODULES.includes(m.id);
        const chk = field => (viewOnly && field !== 'can_view')
          ? `<td class="at-dim" title="该模块为只读/操作型,无此动作">—</td>`
          : `<td><input type="checkbox" class="pm-chk" ${p[field] ? 'checked' : ''} ${dis}
                 data-mid="${m.id}" data-field="${field}"></td>`;

        const fOpts = filterOptions[m.id];
        const supportsFilter = !!fOpts;
        const features = (!person && Array.isArray(m.features)) ? m.features : [];
        const hasExtra = m.supports_owner_change || m.supports_export_email;
        const hasDiscount = (m.id === 'pricing_order' && m.supports_discount) || m.id === 'settlement';

        const isOver = !!overridden[m.id];
        const isDirty = !!dirty[m.id];
        const dirtyBar = isDirty ? 'box-shadow:inset 2px 0 0 var(--warn);' : '';
        const revertCell = person
          ? `<td>${(canEdit && (isOver || isDirty))
              ? `<button type="button" class="at-revert-btn" data-revert="${m.id}" title="恢复继承:删除该模块的个人覆盖,恢复角色默认"><span class="material-symbols-outlined" style="font-size:16px;">history</span></button>` : ''}</td>`
          : '';

        tbody += `
        <tr class="${p.can_view ? '' : 'cm-disabled'}">
          <td class="cm-name" style="${dirtyBar}" title="${esc(m.description || '')}">${esc(m.name)}</td>
          ${chk('can_view')}${chk('can_create')}${chk('can_edit')}${chk('can_delete')}
          <td>
            <span class="at-seg${(!p.can_view || !canEdit) ? ' at-seg-off' : ''}">
              ${LEVELS.map(([v, l]) => `<button type="button" class="${p.permission_level === v ? 'on' : ''}"
                  data-mid="${m.id}" data-level="${v}">${l}</button>`).join('')}
            </span>
          </td>
          ${revertCell}
        </tr>`;

        // 扩展区
        if (supportsFilter || features.length || hasExtra || hasDiscount) {
          const cf = p.content_filter || {};
          let groupsHtml = '';
          if (supportsFilter) Object.keys(fOpts).forEach(fk => {
            const def = fOpts[fk];
            if (!def || !Array.isArray(def.options)) return;
            const selected = Array.isArray(cf[fk]) ? cf[fk] : null;
            groupsHtml += `
              <span class="pm-flt-label">${esc(def.label)}</span>
              <button type="button" class="pm-opt${selected === null ? ' on' : ''}" ${dis}
                      style="justify-self:start;" data-fltall="${m.id}|${fk}">不限</button>
              <span class="pm-flt-chips">
                ${def.options.map(([k, l]) => `
                  <button type="button" class="pm-opt${selected && selected.includes(k) ? ' on' : ''}" ${dis}
                          data-flt="${m.id}|${fk}|${k}">${esc(l)}</button>`).join('')}
              </span>`;
          });
          if (features.length) {
            groupsHtml += `
              <span class="pm-flt-label">功能页签</span><span></span>
              <span class="pm-flt-chips">
                ${features.map(f => `
                  <button type="button" class="pm-opt${featOn(m.id, f.feature_id) ? ' on' : ''}" ${dis}
                          title="点亮=该页签可见" data-feat="${m.id}|${f.feature_id}">${esc(f.name)}</button>`).join('')}
              </span>`;
          }
          if (hasExtra) {
            groupsHtml += `
              <span class="pm-flt-label">更多权限</span><span></span>
              <span class="pm-flt-chips">
                ${m.supports_owner_change ? `<button type="button" class="pm-opt${p.can_change_owner ? ' on' : ''}" ${dis}
                    data-bool="${m.id}|can_change_owner">改归属人</button>` : ''}
                ${m.supports_export_email ? `<button type="button" class="pm-opt${p.can_export_email ? ' on' : ''}" ${dis}
                    data-bool="${m.id}|can_export_email">邮件导出</button>` : ''}
              </span>`;
          }
          if (hasDiscount) {
            const isSettle = m.id === 'settlement';
            const storeMid = isSettle ? 'settlement_order' : 'pricing_order';
            const dField = isSettle ? 'settlement_discount_limit' : 'pricing_discount_limit';
            const dVal = permOf(storeMid)[dField];
            const canSet = canEdit && p.can_create && p.can_edit;
            groupsHtml += `
              <span class="pm-flt-label">折扣权限</span><span></span>
              <span class="pm-flt-chips" style="align-items:center;gap:6px;${canSet ? '' : 'opacity:0.45;'}"
                    ${canSet ? '' : 'title="需先勾选该模块的「新建」和「编辑」权限,折扣下限才有效"'}>
                <span class="at-dim" style="font-size:11px;">${isSettle ? '结算折扣下限' : '批价折扣下限'}</span>
                <span class="pm-num" ${canSet ? 'contenteditable spellcheck="false"' : 'style="cursor:not-allowed;"'}
                      data-num="${m.id}|${storeMid}|${dField}">${dVal != null ? dVal : ''}</span>
                <span class="at-dim" style="font-size:11px;">%(留空=不限)</span>
              </span>`;
          }
          if (groupsHtml) {
            tbody += `<tr class="pm-filter-row${p.can_view ? '' : ' cm-disabled'}"><td colspan="${cols}">
                        <div class="pm-flt-grid">${groupsHtml}</div>
                      </td></tr>`;
          }
        }
      });

      el.innerHTML = `
      <table class="cm-sheet pm-sheet" style="min-width:${person ? 760 : 680}px;">
        <thead><tr>
          <th style="width:220px;text-align:left;">模块</th>
          <th style="width:56px;">查看</th><th style="width:56px;">新建</th>
          <th style="width:56px;">编辑</th><th style="width:56px;">删除</th>
          <th style="width:178px;">数据范围</th>
          ${person ? '<th style="width:40px;"></th>' : ''}
        </tr></thead>
        <tbody>${tbody}</tbody>
      </table>`;

      // 事件绑定
      el.querySelectorAll('input.pm-chk[data-mid]').forEach(c =>
        c.addEventListener('change', () => setField(c.dataset.mid, c.dataset.field, c.checked)));
      el.querySelectorAll('.at-seg button[data-mid]').forEach(b =>
        b.addEventListener('click', () => setField(b.dataset.mid, 'permission_level', b.dataset.level)));
      el.querySelectorAll('[data-fltall]').forEach(b =>
        b.addEventListener('click', () => { const [mid, fk] = b.dataset.fltall.split('|'); filterAll(mid, fk); }));
      el.querySelectorAll('[data-flt]').forEach(b =>
        b.addEventListener('click', () => { const [mid, fk, k] = b.dataset.flt.split('|'); filterToggle(mid, fk, k); }));
      el.querySelectorAll('[data-feat]').forEach(b =>
        b.addEventListener('click', () => { const [mid, fid] = b.dataset.feat.split('|'); featToggle(mid, fid); }));
      el.querySelectorAll('[data-bool]').forEach(b =>
        b.addEventListener('click', () => { const [mid, f] = b.dataset.bool.split('|'); setField(mid, f, !permOf(mid)[f]); }));
      el.querySelectorAll('[data-num]').forEach(s =>
        s.addEventListener('blur', () => { const [mid, storeMid, f] = s.dataset.num.split('|'); numSet(s, storeMid, f, mid); }));
      el.querySelectorAll('[data-revert]').forEach(b =>
        b.addEventListener('click', () => cfg.onRevert && cfg.onRevert(b.dataset.revert)));
    }

    return {
      setData(d) {
        modules = d.modules || [];
        perms = d.permissions || {};
        featPerms = d.featurePermissions || {};
        filterOptions = d.filterOptions || {};
        overridden = d.overridden || {};
        dirty = {};
        render();
      },
      getPermissions() {
        // 只读/操作型模块动作强制 false(清理脏数据)
        VIEW_ONLY_MODULES.forEach(mid => {
          const p = perms[mid];
          if (p) { p.can_create = false; p.can_edit = false; p.can_delete = false; }
        });
        return perms;
      },
      getFeaturePermissions: () => featPerms,
      getDirty: () => Object.keys(dirty),
      isOverridden: mid => !!overridden[mid],
      countGranted: () => modules.filter(m => permOf(m.id).can_view).length,
      moduleCount: () => modules.length,
      render,
    };
  };
})(window);
