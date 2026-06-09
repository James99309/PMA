/**
 * AT 通用确认对话框 · 替代原生 confirm()
 *
 * 用法:
 *   ATConfirm.show({
 *     title: '提交审批',
 *     message: '确定要提交此订单进行审批吗?',
 *     confirmText: '提交',         // 默认「确定」
 *     cancelText: '取消',          // 默认「取消」
 *     variant: 'accent',           // accent(默认) / danger / warn / info
 *     icon: 'send',                // 可选,头部图标
 *     onConfirm: (input) => { ... }, // 点击确定时回调; 若启用了 input,会收到输入值
 *     onCancel: () => { ... },     // 可选
 *
 *     // ─── 可选输入区(让 ATConfirm 兼具"确认 + 收原因/备注"功能) ──
 *     input: {                      // 不提供 = 无输入区
 *       label:       '驳回原因',    // 字段标签
 *       placeholder: '请填写原因…',
 *       required:    true,          // true = 空值时拦截 + 红边提示
 *       multiline:   true,          // true → textarea(默认),false → input
 *       defaultValue:'',
 *       maxLength:   500,
 *       rows:        3              // multiline 时的行数
 *     }
 *   });
 *
 *   ATConfirm.close();
 */
(function (window) {
    let modalEl = null;
    const State = { onConfirm: null, onCancel: null };

    const VARIANTS = {
        accent: { iconBg: 'var(--accent-tint)', iconFg: 'var(--accent)', btnBg: 'var(--accent)', btnFg: '#fff', btnBd: 'var(--accent)' },
        danger: { iconBg: 'var(--danger-soft)', iconFg: 'var(--danger)', btnBg: 'var(--danger)', btnFg: '#fff', btnBd: 'var(--danger)' },
        warn:   { iconBg: 'var(--warn-soft)',   iconFg: 'var(--warn)',   btnBg: 'var(--warn)',   btnFg: '#fff', btnBd: 'var(--warn)' },
        info:   { iconBg: 'var(--info-soft)',   iconFg: 'var(--info)',   btnBg: 'var(--info)',   btnFg: '#fff', btnBd: 'var(--info)' }
    };
    const ICONS = {
        send:   '<path d="M5 12h14M12 5l7 7-7 7"/>',
        check:  '<path d="M5 13l4 4L19 7"/>',
        edit:   '<path d="M16 3l5 5L8 21H3v-5z"/>',
        info:   '<circle cx="12" cy="12" r="9"/><path d="M12 8v0M12 11v5"/>',
        warn:   '<path d="M12 4 2 20h20zM12 10v4M12 17v0"/>',
        cancel: '<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6M15 9l-6 6"/>'
    };

    function escapeHtml(s) {
        return String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
    }

    function ensureStyles() {
        if (document.getElementById('at-confirm-styles')) return;
        const s = document.createElement('style');
        s.id = 'at-confirm-styles';
        s.textContent = `
            @keyframes at-cfm-fade-in  { from { opacity: 0; } to { opacity: 1; } }
            @keyframes at-cfm-scale-in { from { transform: scale(0.96); opacity: 0; } to { transform: scale(1); opacity: 1; } }
        `;
        document.head.appendChild(s);
    }

    function ensureModal() {
        if (modalEl) return modalEl;
        ensureStyles();
        modalEl = document.createElement('div');
        modalEl.id = 'at-confirm-modal';
        Object.assign(modalEl.style, {
            position: 'fixed', inset: '0', zIndex: '10000', display: 'none',
            background: 'rgba(31,30,27,0.32)', backdropFilter: 'blur(2px)',
            alignItems: 'center', justifyContent: 'center', padding: '20px',
            animation: 'at-cfm-fade-in 180ms ease'
        });
        modalEl.addEventListener('click', (e) => { if (e.target === modalEl) close(); });
        document.body.appendChild(modalEl);
        return modalEl;
    }

    function close() {
        if (modalEl) modalEl.style.display = 'none';
    }

    function show(opts) {
        opts = opts || {};
        const title = opts.title || '确认';
        const message = opts.message || '';
        const confirmText = opts.confirmText || '确定';
        const cancelText = opts.cancelText || '取消';
        const variant = VARIANTS[opts.variant] || VARIANTS.accent;
        const iconPath = ICONS[opts.icon] || ICONS.check;
        State.onConfirm = (typeof opts.onConfirm === 'function') ? opts.onConfirm : null;
        State.onCancel  = (typeof opts.onCancel  === 'function') ? opts.onCancel  : null;

        // 输入区配置(可选)
        const inp = opts.input || null;
        const inputHtml = inp ? renderInput(inp) : '';

        const el = ensureModal();
        el.innerHTML = `
            <div style="width:100%;max-width:440px;background:var(--bg-elev);
                        border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,0.15), 0 0 0 1px var(--line);
                        overflow:hidden;animation:at-cfm-scale-in 200ms cubic-bezier(.2,.7,.2,1);">
                <header style="padding:18px 22px 12px;display:flex;align-items:center;gap:10px;">
                    <span style="width:30px;height:30px;border-radius:7px;
                                 background:${variant.iconBg};color:${variant.iconFg};
                                 display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                             stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${iconPath}</svg>
                    </span>
                    <h3 class="at-serif" style="margin:0;font-size:17px;font-weight:500;letter-spacing:0.01em;flex:1;">${escapeHtml(title)}</h3>
                    <button type="button" data-act="close"
                            style="color:var(--ink-3);padding:4px;border-radius:6px;background:transparent;border:0;cursor:pointer;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                             stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
                    </button>
                </header>
                <div style="padding:4px 22px ${inputHtml ? '12px' : '18px'};font-size:13.5px;color:var(--ink-2);line-height:1.55;">
                    ${escapeHtml(message)}
                </div>
                ${inputHtml}
                <footer style="padding:10px 22px 18px;display:flex;justify-content:flex-end;gap:8px;">
                    <button type="button" data-act="cancel"
                            style="height:34px;padding:0 14px;background:transparent;color:var(--ink);
                                   border:1px solid var(--line-2);border-radius:6px;font-size:13px;font-weight:500;cursor:pointer;">
                        ${escapeHtml(cancelText)}
                    </button>
                    <button type="button" data-act="confirm"
                            style="height:34px;padding:0 14px;background:${variant.btnBg};color:${variant.btnFg};
                                   border:1px solid ${variant.btnBd};border-radius:6px;font-size:13px;font-weight:500;cursor:pointer;">
                        ${escapeHtml(confirmText)}
                    </button>
                </footer>
            </div>`;
        el.style.display = 'flex';

        const inputEl = inp ? el.querySelector('[data-cfm-input]') : null;
        const errEl   = inp ? el.querySelector('[data-cfm-err]')   : null;

        // 输入区自动聚焦
        if (inputEl) setTimeout(() => inputEl.focus(), 50);

        function attemptConfirm() {
            let value = inputEl ? inputEl.value.trim() : undefined;
            if (inp && inp.required && !value) {
                inputEl.style.borderColor = 'var(--danger)';
                if (errEl) errEl.style.display = 'block';
                inputEl.focus();
                return;
            }
            const cb = State.onConfirm;
            close();
            if (cb) try { cb(value); } catch (e) { console.error('[ATConfirm] onConfirm error:', e); }
        }

        el.querySelector('[data-act="close"]').addEventListener('click', () => { if (State.onCancel) State.onCancel(); close(); });
        el.querySelector('[data-act="cancel"]').addEventListener('click', () => { if (State.onCancel) State.onCancel(); close(); });
        el.querySelector('[data-act="confirm"]').addEventListener('click', attemptConfirm);

        // 输入时清掉报错态;非 multiline 时回车直接确认
        if (inputEl) {
            inputEl.addEventListener('input', () => {
                inputEl.style.borderColor = 'var(--line-2)';
                if (errEl) errEl.style.display = 'none';
            });
            if (!inp.multiline) {
                inputEl.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') { e.preventDefault(); attemptConfirm(); }
                });
            }
        }
    }

    function renderInput(inp) {
        const label = inp.label ? `<label style="display:block;margin-bottom:6px;font-size:12px;color:var(--ink-3);font-weight:500;">${escapeHtml(inp.label)}${inp.required ? ' <span style="color:var(--danger);">*</span>' : ''}</label>` : '';
        const placeholder = inp.placeholder || '';
        const defaultValue = inp.defaultValue || '';
        const maxLength = inp.maxLength ? `maxlength="${inp.maxLength}"` : '';
        const multiline = inp.multiline !== false;  // 默认 textarea
        const rows = inp.rows || 3;
        const baseStyle = `width:100%;box-sizing:border-box;padding:8px 10px;background:var(--bg-elev);
                           border:1px solid var(--line-2);border-radius:6px;color:var(--ink);
                           font:inherit;font-size:13px;outline:none;resize:${multiline ? 'vertical' : 'none'};
                           transition:border-color 120ms;`;
        const field = multiline
            ? `<textarea data-cfm-input rows="${rows}" placeholder="${escapeHtml(placeholder)}" ${maxLength}
                         style="${baseStyle}min-height:${rows * 22}px;">${escapeHtml(defaultValue)}</textarea>`
            : `<input type="text" data-cfm-input value="${escapeHtml(defaultValue)}" placeholder="${escapeHtml(placeholder)}" ${maxLength}
                      style="${baseStyle}height:34px;">`;
        const errMsg = inp.required ? `<div data-cfm-err style="display:none;margin-top:6px;font-size:12px;color:var(--danger);">该字段为必填项</div>` : '';
        return `
            <div style="padding:0 22px 16px;">
                ${label}
                ${field}
                ${errMsg}
            </div>`;
    }

    // Esc 关闭
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modalEl && modalEl.style.display !== 'none') {
            if (State.onCancel) State.onCancel();
            close();
        }
    });

    window.ATConfirm = { show, close };
})(window);
