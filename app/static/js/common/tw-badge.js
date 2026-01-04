/**
 * TwBadge - 用户徽章生成器
 *
 * 与 Jinja2 宏 render_tw_owner_badge 保持一致的 JavaScript 实现
 * 用于需要动态渲染用户徽章的场景（如 Alpine.js x-for 循环）
 *
 * 使用示例：
 *   <span :class="TwBadge.getColorClass(user.id)">{{ user.initials }}</span>
 */
const TwBadge = {
    // 浅色模式颜色（与 render_tw_owner_badge 宏的 light_colors 保持一致）
    lightColors: [
        'bg-blue-200 text-blue-600 dark:bg-blue-800 dark:text-blue-300',
        'bg-purple-200 text-purple-600 dark:bg-purple-800 dark:text-purple-300',
        'bg-teal-200 text-teal-600 dark:bg-teal-800 dark:text-teal-300',
        'bg-yellow-200 text-yellow-600 dark:bg-yellow-800 dark:text-yellow-300',
        'bg-red-200 text-red-600 dark:bg-red-800 dark:text-red-300',
        'bg-green-200 text-green-600 dark:bg-green-800 dark:text-green-300'
    ],

    // 实心颜色（与 render_tw_owner_badge 宏的 solid_colors 保持一致）
    solidColors: [
        'bg-blue-500 text-white',
        'bg-green-500 text-white',
        'bg-purple-500 text-white',
        'bg-orange-500 text-white',
        'bg-pink-500 text-white',
        'bg-teal-500 text-white'
    ],

    /**
     * 获取用户徽章颜色类
     * @param {number} userId - 用户ID
     * @param {string} variant - 颜色变体: 'light'(默认) 或 'solid'
     * @returns {string} Tailwind CSS 类名
     */
    getColorClass(userId, variant = 'light') {
        const colors = variant === 'solid' ? this.solidColors : this.lightColors;
        return colors[(userId || 0) % colors.length];
    },

    /**
     * 获取用户名首字母
     * @param {string} name - 用户名
     * @param {number} chars - 字符数，默认2
     * @returns {string} 首字母
     */
    getInitials(name, chars = 2) {
        if (!name) return '?';
        return name.substring(0, chars);
    }
};
