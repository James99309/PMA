/**
 * AT Toast · 全局通知组件(可复用)
 *
 * 用法:
 *   ATToast.success('发货单已创建', '本次共发货 5 件')
 *   ATToast.info('提示', '...')
 *   ATToast.warn('无法创建发货单', '请选择目标客户订单')
 *   ATToast.error('保存失败', err)
 *
 * 视觉:
 *   - 顶部居中堆叠,高对比深色底反白文字
 *   - 左侧 4px 状态色竖条 + 30×30 状态色透明图标块
 *   - 标题 14.5px / 600 · 描述 12.5px / 白 78%
 *   - 深阴影 60px blur,3.2 秒自动消失
 *
 * 也可短调用:window.toast.success(...)
 */
(function (window) {
    const TONES = {
        info:    { bg: '#1A2632', accent: '#7CA9D8' },
        success: { bg: '#1E2E25', accent: '#6BAE8B' },
        warn:    { bg: '#2B1F12', accent: '#D89855' },
        error:   { bg: '#2A1818', accent: '#D67878' }
    };
    const ICONS = {
        info:    '<circle cx="12" cy="12" r="9"/><path d="M12 8v0M12 11v5"/>',
        success: '<path d="M5 13l4 4L19 7"/>',
        warn:    '<path d="M12 4 2 20h20zM12 10v4M12 17v0"/>',
        error:   '<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6M15 9l-6 6"/>'
    };

    let _stack = null;
    let _seq = 0;

    function ensureStack() {
        if (_stack) return _stack;
        _stack = document.createElement('div');
        _stack.id = 'at-toast-stack';
        Object.assign(_stack.style, {
            position: 'fixed', top: '20px', left: '50%',
            transform: 'translateX(-50%)',
            zIndex: '9999',
            display: 'flex', flexDirection: 'column', gap: '10px',
            pointerEvents: 'none'
        });
        // 注入动画 keyframes(一次性)
        if (!document.getElementById('at-toast-styles')) {
            const s = document.createElement('style');
            s.id = 'at-toast-styles';
            s.textContent = `
                @keyframes at-toast-in  { from { opacity: 0; transform: translateY(-12px) scale(0.97); } to { opacity: 1; transform: translateY(0) scale(1); } }
                @keyframes at-toast-out { from { opacity: 1; transform: translateY(0) scale(1); }      to { opacity: 0; transform: translateY(-8px) scale(0.97); } }
            `;
            document.head.appendChild(s);
        }
        document.body.appendChild(_stack);
        return _stack;
    }

    function escapeHtml(s) {
        return String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
    }

    function dismiss(id) {
        const el = document.getElementById('at-toast-' + id);
        if (!el) return;
        el.style.animation = 'at-toast-out 200ms ease forwards';
        setTimeout(() => el.remove(), 220);
    }

    function show(tone, title, desc, duration) {
        const meta = TONES[tone] || TONES.info;
        const id = ++_seq;
        duration = duration == null ? 3200 : duration;
        const stack = ensureStack();
        const el = document.createElement('div');
        el.id = 'at-toast-' + id;
        Object.assign(el.style, {
            position: 'relative',
            display: 'flex', alignItems: 'flex-start', gap: '12px',
            minWidth: '360px', maxWidth: '520px',
            paddingLeft: '14px', paddingRight: '18px', padding: '16px 18px 16px 14px',
            background: meta.bg, color: '#fff',
            boxShadow: '0 24px 60px rgba(31,30,27,0.30), 0 4px 12px rgba(31,30,27,0.18)',
            borderRadius: '12px',
            pointerEvents: 'auto',
            overflow: 'hidden',
            animation: 'at-toast-in 220ms cubic-bezier(.2,.7,.2,1)'
        });
        el.innerHTML = `
            <span style="position:absolute;left:0;top:0;bottom:0;width:4px;background:${meta.accent};"></span>
            <span style="width:30px;height:30px;border-radius:8px;flex-shrink:0;
                         background:${meta.accent}22;color:${meta.accent};
                         display:inline-flex;align-items:center;justify-content:center;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    ${ICONS[tone] || ICONS.info}
                </svg>
            </span>
            <div style="flex:1;min-width:0;padding-top:2px;">
                <div style="font-size:14.5px;font-weight:600;line-height:1.35;letter-spacing:0.01em;">${escapeHtml(title)}</div>
                ${desc ? `<div style="font-size:12.5px;margin-top:4px;line-height:1.5;color:rgba(255,255,255,0.78);">${escapeHtml(desc)}</div>` : ''}
            </div>
            <button data-id="${id}"
                    style="color:rgba(255,255,255,0.55);padding:4px;border-radius:4px;flex-shrink:0;background:transparent;border:0;cursor:pointer;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M6 6l12 12M18 6L6 18"/>
                </svg>
            </button>
        `;
        el.querySelector('button').addEventListener('click', () => dismiss(id));
        stack.appendChild(el);
        if (duration > 0) setTimeout(() => dismiss(id), duration);
        return id;
    }

    const ATToast = {
        show, dismiss,
        info:    (t, d, dur) => show('info',    t, d, dur),
        success: (t, d, dur) => show('success', t, d, dur),
        warn:    (t, d, dur) => show('warn',    t, d, dur),
        error:   (t, d, dur) => show('error',   t, d, dur)
    };

    window.ATToast = ATToast;
    // 短调用
    window.toast = ATToast;
})(window);
