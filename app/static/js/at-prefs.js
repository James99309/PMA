/**
 * AT 设计系统 · 用户偏好(localStorage)
 *
 * 管理 4 项偏好:
 *   - at-dark           暗色模式(0/1)
 *   - at-density        信息密度(compact/standard/cozy)
 *   - at-headline-font  大标题字体(serif/sans)
 *   - at-accent         强调色(hex)
 *
 * 自动在文档加载时应用到 <html data-*>;暴露 window.ATPrefs 供脚本调用。
 */
(function (window) {
    const ACCENT_TINT_MAP = {
        '#C15F3C': { soft: '#F2DCCC', tint: '#FBF1E9' },
        '#2A5F8F': { soft: '#D5E2EF', tint: '#EDF3F9' },
        '#1F2937': { soft: '#D9DDE3', tint: '#EEEFF2' },
        '#2F7155': { soft: '#D4E5DC', tint: '#EDF4F0' }
    };

    function read() {
        return {
            dark: localStorage.getItem('at-dark') === '1',
            density: localStorage.getItem('at-density') || 'standard',
            headlineFont: localStorage.getItem('at-headline-font') || 'serif',
            accent: localStorage.getItem('at-accent') || '#C15F3C'
        };
    }

    function apply() {
        const p = read();
        const root = document.documentElement;
        root.dataset.theme = p.dark ? 'dark' : 'light';
        root.dataset.density = p.density;
        root.dataset.headlineFont = p.headlineFont;
        root.style.setProperty('--accent', p.accent);
        const m = ACCENT_TINT_MAP[p.accent] || { soft: 'var(--bg-sunk)', tint: 'var(--bg-hover)' };
        root.style.setProperty('--accent-soft', m.soft);
        root.style.setProperty('--accent-tint', m.tint);
        root.style.setProperty('--accent-2', p.accent);
        document.dispatchEvent(new CustomEvent('at-prefs-changed', { detail: p }));
    }

    window.ATPrefs = {
        get: read,
        apply,
        setDark(v)         { localStorage.setItem('at-dark', v ? '1' : '0'); apply(); },
        toggleDark()       { this.setDark(!read().dark); },
        setDensity(v)      { localStorage.setItem('at-density', v); apply(); },
        setHeadlineFont(v) { localStorage.setItem('at-headline-font', v); apply(); },
        setAccent(v)       { localStorage.setItem('at-accent', v); apply(); }
    };

    apply();
})(window);
