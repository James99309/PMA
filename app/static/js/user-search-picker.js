/**
 * 通用用户搜索选择器 — Alpine.js 组件
 *
 * 支持单选和多选模式，带搜索过滤、标签展示、键盘导航。
 *
 * 用法：
 *   <div x-data="userSearchPicker({
 *       users: allUsersArray,            // [{id, real_name, username, company_name?}]
 *       multiple: false,                 // true=多选  false=单选
 *       selected: initialValue,          // 单选: userId (Number)  多选: [{id,real_name,username}]
 *       tagColor: 'primary',             // 标签色: primary / amber / blue
 *       placeholder: '搜索用户',
 *       onChange(val) { ... }            // 回调: 单选传 userId，多选传 [{id,...}]
 *   })">
 *       <template x-html="$el.__picker_html"></template>   ← 不需要，自带 DOM
 *   </div>
 */
function userSearchPicker(opts = {}) {
    const colorMap = {
        primary: {
            tag: 'bg-primary/10 text-primary dark:bg-primary/20 dark:text-primary-light',
            ring: 'focus-within:ring-primary/50 focus-within:border-primary',
        },
        amber: {
            tag: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
            ring: 'focus-within:ring-amber-400/50 focus-within:border-amber-400',
        },
        blue: {
            tag: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
            ring: 'focus-within:ring-blue-400/50 focus-within:border-blue-400',
        },
    };
    const color = colorMap[opts.tagColor] || colorMap.primary;

    return {
        allUsers: opts.users || [],
        multiple: opts.multiple !== undefined ? opts.multiple : false,
        search: '',
        showDrop: false,
        filtered: [],
        // 多选: 已选用户对象数组;  单选: 已选用户对象或 null
        selected: [],
        _onChange: opts.onChange || null,
        _tagCls: color.tag,
        _ringCls: color.ring,
        _placeholder: opts.placeholder || '搜索用户',

        init() {
            // 初始化 selected
            if (this.multiple) {
                this.selected = Array.isArray(opts.selected) ? [...opts.selected] : [];
            } else {
                // 单选: 传入 userId → 找到用户对象
                if (opts.selected) {
                    const uid = typeof opts.selected === 'object' ? opts.selected.id : Number(opts.selected);
                    const u = this.allUsers.find(u => u.id === uid);
                    this.selected = u ? [u] : [];
                } else {
                    this.selected = [];
                }
            }
            this.filtered = this.allUsers.slice(0, 20);

            // 使用 capture 阶段监听点击，确保在 @click.stop 的模态框内也能关闭下拉
            const el = this.$el;
            const self = this;
            document.addEventListener('click', (e) => {
                if (self.showDrop && !el.contains(e.target)) {
                    self.showDrop = false;
                }
            }, true);
        },

        get displayName() {
            if (this.selected.length === 0) return '';
            const u = this.selected[0];
            return u.real_name || u.username || '';
        },

        filter() {
            const q = this.search.toLowerCase();
            const src = this.allUsers;
            if (!q) {
                this.filtered = src.slice(0, 20);
            } else {
                this.filtered = src.filter(u =>
                    (u.real_name || '').toLowerCase().includes(q) ||
                    (u.username || '').toLowerCase().includes(q) ||
                    (u.company_name || '').toLowerCase().includes(q)
                ).slice(0, 20);
            }
        },

        isSelected(uid) {
            return this.selected.some(u => u.id === uid);
        },

        pick(user) {
            if (this.multiple) {
                if (!this.isSelected(user.id)) {
                    this.selected.push(user);
                }
            } else {
                // 单选：替换
                this.selected = [user];
                this.showDrop = false;
            }
            this.search = '';
            this.filter();
            this._notify();
        },

        remove(uid) {
            this.selected = this.selected.filter(u => u.id !== uid);
            this._notify();
        },

        _notify() {
            if (!this._onChange) return;
            if (this.multiple) {
                this._onChange([...this.selected]);
            } else {
                this._onChange(this.selected.length ? this.selected[0].id : null);
            }
        },

        /** 外部重设用户列表（如异步加载后） */
        setUsers(users) {
            this.allUsers = users;
            this.filter();
        },

        /** 外部重设已选值 */
        setSelected(val) {
            if (this.multiple) {
                this.selected = Array.isArray(val) ? [...val] : [];
            } else {
                if (val) {
                    const uid = typeof val === 'object' ? val.id : Number(val);
                    const u = this.allUsers.find(u => u.id === uid);
                    this.selected = u ? [u] : [];
                } else {
                    this.selected = [];
                }
            }
        },
    };
}
