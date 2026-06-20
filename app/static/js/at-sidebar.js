/**
 * AT 侧边栏控制器
 *
 * 状态:
 *   collapsed(默认 64px,仅图标)
 *   pinned   (固定展开 232px,持久化到 localStorage `at-sidebar-pinned`)
 *   hovered  (悬停时浮层展开,absolute 覆盖,不挤压主内容)
 *
 * DOM 约定(由 at_sidebar 宏注入):
 *   .at-sidebar             外层 aside,宽度过渡(64 ↔ 232)
 *   .at-sidebar-panel       内层面板,absolute 定位,实际可见宽度
 *   .at-sb-text             展开态才显示的文字/子菜单/操作
 *   #{id}Toggle             右上角圆形 pin 按钮
 *
 * 用法:页面只要 include at_sidebar 宏并加载本 JS,自动绑定。
 */
(function (window) {
    const STORAGE_KEY = 'at-sidebar-pinned';
    const GROUP_KEY = (key) => 'at-sb-open-' + key;

    function isGroupOpen(groupEl) {
        const key = groupEl.dataset.groupKey;
        const saved = localStorage.getItem(GROUP_KEY(key));
        if (saved === '1') return true;
        if (saved === '0') return false;
        // 未保存过 → 看 data-default-open(active 分组)
        return groupEl.dataset.defaultOpen === '1';
    }

    function applyGroupState(groupEl, expanded, open) {
        const sub = groupEl.querySelector('.at-sb-sub');
        const chev = groupEl.querySelector('.at-sb-chev');
        if (sub) sub.style.display = (expanded && open) ? 'flex' : 'none';
        if (chev) chev.style.transform = open ? 'rotate(180deg)' : 'rotate(0deg)';
    }

    function setVisualState(aside, panel, toggle, opts) {
        const isPinned = !!opts.pinned;
        const isHover = !!opts.hover;
        const showExpanded = isPinned || isHover;
        const isFloating = !isPinned && isHover;

        aside.style.width = isPinned ? '232px' : '64px';
        aside.style.zIndex = isFloating ? '50' : '1';

        panel.style.width = showExpanded ? '232px' : '64px';
        panel.style.boxShadow = isFloating ? '8px 0 24px rgba(31,30,27,0.08)' : 'none';
        panel.style.borderRight = isFloating ? '1px solid var(--line)' : '0';

        // 文字/子菜单/操作显隐(子菜单还要叠加分组 open 状态)
        aside.querySelectorAll('.at-sb-text').forEach(el => {
            if (el.classList.contains('at-sb-sub')) return; // 由 applyGroupState 处理
            if (el.tagName === 'BUTTON' || el.tagName === 'SPAN') {
                el.style.display = showExpanded ? 'inline-flex' : 'none';
            } else if (el.tagName === 'A') {
                el.style.display = showExpanded ? 'inline-flex' : 'none';
            } else {
                el.style.display = showExpanded ? 'flex' : 'none';
            }
        });

        // 每个分组按当前 open 状态刷新子菜单
        aside.querySelectorAll('.at-sb-group').forEach(g => {
            applyGroupState(g, showExpanded, isGroupOpen(g));
        });

        if (toggle) {
            toggle.style.transform = isPinned ? 'rotate(180deg)' : 'rotate(0deg)';
            toggle.title = isPinned ? '收起' : '固定展开';
            toggle.style.display = isFloating ? 'none' : 'flex';
        }
    }

    function bindOne(aside) {
        if (aside.dataset.atBound) return;
        aside.dataset.atBound = '1';
        const panel = aside.querySelector('.at-sidebar-panel');
        const toggle = document.getElementById(aside.id + 'Toggle');
        if (!panel) return;

        const state = {
            pinned: localStorage.getItem(STORAGE_KEY) === '1',
            hover: false,
        };
        const apply = () => setVisualState(aside, panel, toggle, state);

        aside.addEventListener('mouseenter', () => { state.hover = true; apply(); });
        aside.addEventListener('mouseleave', () => { state.hover = false; apply(); });
        if (toggle) {
            toggle.addEventListener('click', () => {
                state.pinned = !state.pinned;
                localStorage.setItem(STORAGE_KEY, state.pinned ? '1' : '0');
                apply();
            });
        }

        // 分组按钮:折叠/展开子菜单(仅展开态下生效)
        aside.querySelectorAll('.at-sb-group [data-act="toggle"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const group = e.currentTarget.closest('.at-sb-group');
                if (!group) return;
                // 收缩态点击 → 先 pin 展开
                const expanded = state.pinned || state.hover;
                if (!expanded) {
                    state.pinned = true;
                    localStorage.setItem(STORAGE_KEY, '1');
                    apply();
                    return;
                }
                const key = group.dataset.groupKey;
                const nowOpen = !isGroupOpen(group);
                localStorage.setItem(GROUP_KEY(key), nowOpen ? '1' : '0');
                applyGroupState(group, true, nowOpen);
            });
        });

        // 初始应用一次
        apply();
    }

    function init() {
        document.querySelectorAll('aside.at-sidebar').forEach(bindOne);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})(window);
