/**
 * SN 摘要格式化工具
 *
 * 用途：将一组序列号格式化成简短可读的摘要文本
 *  - 连续段（同前缀 + 数字递增）→ `212 个 · XXX-001 ~ XXX-212`
 *  - 非连续 → `212 个 · XXX-001 等`
 *  - 单个 → 直接返回该 SN
 *
 * 使用场景：发货单详情模态、采购单详情发货记录里展示 SN 数量+范围,
 * 不再罗列完整列表（查询走 SN 管理器搜索）。
 */
(function (window) {
    function detectContiguous(snList) {
        if (!snList || snList.length < 2) return null;
        const parsed = snList.map(s => {
            const m = String(s).match(/^(.*?)(\d+)$/);
            return m ? { prefix: m[1], num: parseInt(m[2], 10) } : null;
        });
        if (parsed.some(p => p === null)) return null;
        const prefix = parsed[0].prefix;
        if (parsed.some(p => p.prefix !== prefix)) return null;
        for (let i = 1; i < parsed.length; i++) {
            if (parsed[i].num !== parsed[i - 1].num + 1) return null;
        }
        return { first: snList[0], last: snList[snList.length - 1] };
    }

    /**
     * 格式化 SN 列表为摘要文本
     * @param {string[]} snList - 序列号数组
     * @param {object} [opts]
     * @param {string} [opts.countSuffix=' 个'] - 数量后缀（i18n 用，英文可传 ' SNs'）
     * @param {string} [opts.etcLabel=' 等'] - 非连续时的省略标签
     * @returns {string} 摘要文本，列表为空返回空串
     */
    window.formatSnSummary = function (snList, opts) {
        opts = opts || {};
        const countSuffix = opts.countSuffix != null ? opts.countSuffix : ' 个';
        const etcLabel = opts.etcLabel != null ? opts.etcLabel : ' 等';
        if (!snList || snList.length === 0) return '';
        if (snList.length === 1) return String(snList[0]);
        const range = detectContiguous(snList);
        if (range) return `${snList.length}${countSuffix} · ${range.first} ~ ${range.last}`;
        return `${snList.length}${countSuffix} · ${snList[0]}${etcLabel}`;
    };

    /**
     * 构造跳转到 SN 管理器并预填查询的 URL
     * @param {string} sn - 用于预填搜索的 SN（通常传第一个/前缀）
     */
    window.snManagerUrl = function (sn) {
        return '/product-sn/?q=' + encodeURIComponent(sn || '');
    };
})(window);
