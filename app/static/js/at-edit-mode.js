/**
 * AT 编辑模式守卫(配置管理 / 个人配置 矩阵页公用)
 * ───────────────────────────────────────────────────────────
 * 解决:切换角色/人员后矩阵默认**只读**,必须点「编辑」才能改(防误勾);保存需确认;
 *       编辑且有未保存改动时,切换角色/人员或离开页面会提醒。
 *
 * 机制:只读时给 lockEl 加 pointer-events:none + 置灰(无需改各 sheet 组件);
 *       脏标记由页面在 sheet 的 onChange 里调用 markDirty() 维护。
 *
 * 用法:
 *   const guard = AtEditMode.init({
 *     mount:  'pmEditBar',          // 放 编辑/保存/取消 按钮的容器
 *     lockEl: 'pmSheet',            // 只读时锁定(置灰+不可点)的容器
 *     canEdit: true,               // false → 永远只读,无编辑按钮
 *     onSave: async () => true,    // 保存逻辑,返回 true=成功(成功后自动退出编辑)
 *     onDiscard: () => {},         // 取消/放弃改动时恢复(通常重载当前数据)
 *     saveConfirm: { title:'保存', message:'确认保存?' },  // 可选
 *   });
 *   // 切换角色/人员务必经 guard.attempt:
 *   guard.attempt(() => { _role = r; load(); });
 *   // sheet 变更时:
 *   onChange: () => guard.markDirty()
 */
(function (g) {
  'use strict';

  // 只读样式:只禁"可交互元素"的点击/编辑,容器本身仍可滚动(否则只读看不到下面内容)
  if (!document.getElementById('at-edit-mode-style')) {
    var _st = document.createElement('style');
    _st.id = 'at-edit-mode-style';
    _st.textContent =
      '.at-em-ro input,.at-em-ro select,.at-em-ro textarea,.at-em-ro button,' +
      '.at-em-ro [contenteditable],.at-em-ro .me-act,.at-em-ro .me-tgt,' +
      '.at-em-ro .cm-gran-btn,.at-em-ro .pm-opt,.at-em-ro .cyc-btn,.at-em-ro .af-chip,' +
      '.at-em-ro .ss-del,.at-em-ro [data-pp-id],.at-em-ro [data-revert],.at-em-ro [data-delp]' +
      '{pointer-events:none !important;}';
    document.head.appendChild(_st);
  }

  function el(id) { return typeof id === 'string' ? document.getElementById(id) : id; }

  g.AtEditMode = {
    init(cfg) {
      const lockEl = el(cfg.lockEl);
      const mount = el(cfg.mount);
      const canEdit = cfg.canEdit !== false;
      let editing = false, dirty = false;

      function applyLock() {
        if (!lockEl) return;
        // 仅可编辑场景才需"只读锁";view-only 用户本就不可改,不锁
        const ro = canEdit && !editing;
        // 只禁交互元素(见 .at-em-ro 样式),容器保持可滚动
        lockEl.classList.toggle('at-em-ro', ro);
        lockEl.style.pointerEvents = '';
        lockEl.style.opacity = ro ? '0.6' : '';
        lockEl.style.transition = 'opacity 120ms';
      }

      // 工具条按钮
      const bs = 'height:32px;padding:0 14px;border-radius:6px;font:inherit;font-size:13px;cursor:pointer;';
      const btnGhost = 'border:1px solid var(--line-2);background:var(--bg-elev);color:var(--ink-2);';
      const btnDark = 'border:0;background:var(--ink);color:var(--bg-page);font-weight:500;';
      let editBtn, saveBtn, cancelBtn;
      if (mount) {
        mount.innerHTML = (canEdit
          ? '<button type="button" data-em-edit style="' + bs + btnGhost + '">编辑</button>' +
            '<button type="button" data-em-cancel style="' + bs + btnGhost + 'display:none;">取消</button>' +
            '<button type="button" data-em-save style="' + bs + btnDark + 'display:none;">保存</button>'
          : '');
        mount.style.display = 'inline-flex';
        mount.style.alignItems = 'center';
        mount.style.gap = '8px';
        editBtn = mount.querySelector('[data-em-edit]');
        saveBtn = mount.querySelector('[data-em-save]');
        cancelBtn = mount.querySelector('[data-em-cancel]');
      }

      function setUI() {
        if (editBtn) editBtn.style.display = editing ? 'none' : '';
        if (saveBtn) saveBtn.style.display = editing ? '' : 'none';
        if (cancelBtn) cancelBtn.style.display = editing ? '' : 'none';
      }

      function enter() { if (!canEdit) return; editing = true; dirty = false; applyLock(); setUI(); if (cfg.onEnter) cfg.onEnter(); }
      function exit() { editing = false; dirty = false; applyLock(); setUI(); if (cfg.onExit) cfg.onExit(); }

      function confirmThen(opts, onYes, onNo) {
        if (g.ATConfirm) {
          g.ATConfirm.show(Object.assign({
            confirmText: '确定', cancelText: '取消', onConfirm: onYes, onCancel: onNo,
          }, opts));
        } else if (window.confirm((opts.title ? opts.title + '\n' : '') + (opts.message || ''))) {
          onYes();
        } else if (onNo) { onNo(); }
      }

      async function doSave() {
        if (!editing) return;
        confirmThen({
          title: (cfg.saveConfirm && cfg.saveConfirm.title) || '保存',
          message: (cfg.saveConfirm && cfg.saveConfirm.message) || '确认保存当前修改?',
          variant: 'accent', icon: 'save', confirmText: '保存',
        }, async () => {
          let ok = true;
          if (cfg.onSave) ok = await cfg.onSave();
          if (ok !== false) exit();
        });
      }

      function cancel() {
        if (dirty) {
          confirmThen({
            title: '放弃修改', message: '有未保存的修改,确定放弃?',
            variant: 'danger', icon: 'undo', confirmText: '放弃',
          }, () => { if (cfg.onDiscard) cfg.onDiscard(); exit(); });
        } else {
          exit();
        }
      }

      // 切换角色/人员等:编辑且脏 → 提醒;否则放行(顺带退出编辑)。
      // onCancel 用于 <select> 等需要在用户取消时回退控件值的场景。
      function attempt(fn, onCancel) {
        if (editing && dirty) {
          confirmThen({
            title: '有未保存的修改', message: '切换后将丢失当前未保存的修改,继续?',
            variant: 'danger', icon: 'undo', confirmText: '不保存并继续',
          }, () => { exit(); fn(); }, onCancel);
          return;
        }
        if (editing) exit();
        fn();
      }

      if (editBtn) editBtn.addEventListener('click', enter);
      if (saveBtn) saveBtn.addEventListener('click', doSave);
      if (cancelBtn) cancelBtn.addEventListener('click', cancel);

      // 站内链接(tab 切换 / 侧栏导航)→ 用 in-app 确认框,而非浏览器原生提示
      let _bypass = false;
      document.addEventListener('click', function (e) {
        if (!editing || !dirty || _bypass) return;
        const a = e.target.closest ? e.target.closest('a[href]') : null;
        if (!a) return;
        const href = a.getAttribute('href');
        if (!href || href.charAt(0) === '#' || href.indexOf('javascript:') === 0) return;
        if (a.target === '_blank') return;
        e.preventDefault();
        e.stopPropagation();
        confirmThen({
          title: '有未保存的修改', message: '离开当前页将丢失未保存的修改,确定离开?',
          variant: 'danger', icon: 'undo', confirmText: '不保存并离开',
        }, function () { _bypass = true; window.location.href = a.href; });
      }, true);

      // 兜底:仅刷新/关闭标签等真实卸载时用原生提示(站内 tab 切换已被上面拦截)
      window.addEventListener('beforeunload', function (e) {
        if (editing && dirty && !_bypass) { e.preventDefault(); e.returnValue = ''; return ''; }
      });

      exit();   // 初始只读

      return {
        enter, exit, save: doSave, attempt,
        markDirty() { dirty = true; },
        clearDirty() { dirty = false; },
        isEditing: () => editing,
        isDirty: () => dirty,
      };
    }
  };
})(window);
