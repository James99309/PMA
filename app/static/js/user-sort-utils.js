/**
 * 用户排序工具函数
 *
 * 提供通用的用户列表排序功能
 */

/**
 * 按部门和团队分组排序用户列表
 * 排序规则：
 * 0. 未激活用户排在最后
 * 1. 按部门名称分组（相同部门放在一起）
 * 2. 同部门内排序：
 *    - 部门负责人最优先
 *    - 然后按团队分组（相同团队放一起）
 *      - 团队负责人优先
 *      - 团队成员按姓名排序
 *    - 无团队的部门成员最后
 * 3. 每个分组内按姓名排序
 *
 * @param {Array} users - 用户列表，需包含以下字段：
 *   - is_active: 是否激活（可选，默认 true）
 *   - department: 部门名称
 *   - is_department_manager: 是否为部门负责人
 *   - team_name: 团队名称（可选）
 *   - is_team_leader: 是否为团队负责人
 *   - real_name: 真实姓名
 * @returns {Array} - 排序后的用户列表（新数组）
 */
function sortUsersByDepartment(users) {
    if (!users || !Array.isArray(users)) return users;

    return [...users].sort((a, b) => {
        // 0. 先按激活状态排序（激活用户优先）
        const isActiveA = a.is_active !== false ? 1 : 0;
        const isActiveB = b.is_active !== false ? 1 : 0;
        if (isActiveB !== isActiveA) return isActiveB - isActiveA;

        // 1. 再按部门名称排序（相同部门放一起）
        const deptA = a.department || '';
        const deptB = b.department || '';
        const deptCompare = deptA.localeCompare(deptB, 'zh-CN');
        if (deptCompare !== 0) return deptCompare;

        // === 同部门内排序 ===

        // 2. 部门负责人最优先
        const isDeptManagerA = a.is_department_manager ? 1 : 0;
        const isDeptManagerB = b.is_department_manager ? 1 : 0;
        if (isDeptManagerB !== isDeptManagerA) return isDeptManagerB - isDeptManagerA;

        // 3. 有团队的优先于无团队的
        const hasTeamA = a.team_name ? 1 : 0;
        const hasTeamB = b.team_name ? 1 : 0;
        if (hasTeamB !== hasTeamA) return hasTeamB - hasTeamA;

        // 4. 如果都有团队，按团队名称分组
        if (a.team_name && b.team_name) {
            const teamCompare = (a.team_name || '').localeCompare(b.team_name || '', 'zh-CN');
            if (teamCompare !== 0) return teamCompare;

            // 同团队内，团队负责人优先
            const isTeamLeaderA = a.is_team_leader ? 1 : 0;
            const isTeamLeaderB = b.is_team_leader ? 1 : 0;
            if (isTeamLeaderB !== isTeamLeaderA) return isTeamLeaderB - isTeamLeaderA;
        }

        // 5. 最后按姓名排序
        const nameA = a.real_name || a.username || '';
        const nameB = b.real_name || b.username || '';
        return nameA.localeCompare(nameB, 'zh-CN');
    });
}
