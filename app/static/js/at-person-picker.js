/**
 * AT 人员/部门选择器(个人配置各页公用)
 * ───────────────────────────────────────────────────────────
 * 替代各页内联的 renderMenu/toggleMenu 复制实现。下拉含搜索框 + 按部门分组的人员列表。
 * 关键:菜单外壳(搜索框 + 列表容器)只构建一次,输入时**只刷新列表容器**,
 *       搜索框 DOM 不被重建 → 原生保持焦点(修复"输入一个字符即丢焦点"老 bug)。
 *
 * 用法:
 *   const picker = AtPersonPicker.init({
 *     button: 'psPickerBtn' | el,   // 触发按钮
 *     menu:   'psUserMenu'  | el,   // 下拉容器(.cm-role-menu)
 *     getUsers: () => [{id,name,department,role_display, ...}],  // 当前可选人员
 *     activeId: () => _userId,      // 可选:当前选中 id(高亮)
 *     onSelect: id => {...},        // 选中回调
 *     rowBadge: u => '<span>…</span>',  // 可选:每行右侧徽章(方案/新手/AI 开通等,各页不同)
 *     locked:   () => bool,         // 可选:锁定不可展开(如绩效审批模式)
 *     placeholder: '搜索人员 / 部门…',
 *   });
 *   picker.refresh();  // 数据变化后刷新列表(菜单展开时)
 */
(function (g) {
  'use strict';
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

  g.AtPersonPicker = {
    init(cfg) {
      const btn = typeof cfg.button === 'string' ? document.getElementById(cfg.button) : cfg.button;
      const menu = typeof cfg.menu === 'string' ? document.getElementById(cfg.menu) : cfg.menu;
      if (!btn || !menu) return null;
      const placeholder = cfg.placeholder || '搜索人员 / 部门…';
      let built = false;

      function buildShell() {
        menu.innerHTML =
          '<input class="pp-search at-pp-search" type="text" autocomplete="off" placeholder="' + esc(placeholder) + '">' +
          '<div class="at-pp-list"></div>';
        const inp = menu.querySelector('.at-pp-search');
        inp.addEventListener('click', e => e.stopPropagation());
        inp.addEventListener('keydown', e => e.stopPropagation());
        inp.addEventListener('input', renderList);
        built = true;
      }

      function renderList() {
        const inp = menu.querySelector('.at-pp-search');
        const term = (inp ? inp.value : '').trim().toLowerCase();
        const users = (cfg.getUsers ? cfg.getUsers() : []) || [];
        const list = users.filter(u => !term ||
          ((u.name || '') + ' ' + (u.department || '') + ' ' + (u.role_display || '')).toLowerCase().includes(term));
        const activeId = cfg.activeId ? cfg.activeId() : null;
        const groups = {};
        list.forEach(u => {
          const dep = u.department || '未分组';
          (groups[dep] = groups[dep] || []).push(u);
        });
        let html = '';
        Object.keys(groups).forEach(dep => {
          html += '<div class="pp-dep">' + esc(dep) + '</div>';
          groups[dep].forEach(u => {
            const badge = cfg.rowBadge ? (cfg.rowBadge(u) || '') : '';
            html += '<div class="cm-role-item' + (u.id === activeId ? ' active' : '') + '" data-pp-id="' + u.id + '">' +
              '<span style="display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;' +
              'border-radius:50%;background:var(--accent-tint);color:var(--accent);font-size:11px;font-weight:600;flex-shrink:0;">' +
              esc((u.name || '?')[0]) + '</span>' +
              '<span style="flex:1;">' + esc(u.name || '') + '</span>' +
              badge +
              '<span class="at-dim" style="font-size:10.5px;">' + esc(u.role_display || '') + '</span>' +
              '</div>';
          });
        });
        const listEl = menu.querySelector('.at-pp-list');
        listEl.innerHTML = html || '<div class="at-dim" style="padding:18px;text-align:center;font-size:12px;">无匹配</div>';
        listEl.querySelectorAll('[data-pp-id]').forEach(el =>
          el.addEventListener('click', () => {
            close();
            cfg.onSelect && cfg.onSelect(parseInt(el.dataset.ppId));
          }));
      }

      function open() {
        if (!built) buildShell();
        menu.style.display = 'block';
        const inp = menu.querySelector('.at-pp-search');
        if (inp) inp.value = '';
        renderList();
        if (inp) inp.focus();
      }
      function close() { menu.style.display = 'none'; }
      function isOpen() { return menu.style.display && menu.style.display !== 'none'; }

      btn.addEventListener('click', e => {
        e.stopPropagation();
        if (cfg.locked && cfg.locked()) return;
        isOpen() ? close() : open();
      });
      document.addEventListener('click', close);

      return { open, close, refresh() { if (isOpen()) renderList(); } };
    }
  };
})(window);
