/**
 * 规格分析工具 - 用于分析产品规格差异并高亮显示
 *
 * 支持两种数据格式：
 * 1. 字符串格式：ProductConfigModal 中的 specification/product_desc
 * 2. JSON快照格式：报价单产品选择中的 code_definition_snapshot
 *
 * @author Claude AI
 * @version 1.0.0
 * @date 2025-11-28
 */
class SpecAnalyzer {

    // ========== 字符串格式解析 ==========

    /**
     * 解析规格描述字符串为 key-value 对象
     * 支持两种格式：
     * 1. 逗号分隔: "频率范围: 120 MHz, 接口类型: N"
     * 2. 空格分隔: "频率范围: 400-430MHz 信道端口数: 2 最大输入功率: 50W"
     * @param {string} specStr - 规格字符串
     * @returns {Object} - { "频率范围": "120 MHz", "接口类型": "N" }
     */
    static parseSpecString(specStr) {
        if (!specStr) return {};
        const result = {};

        // 检查是否包含逗号分隔符
        if (/[,，]/.test(specStr)) {
            // 逗号分隔格式
            specStr.split(/[,，]\s*/).forEach(pair => {
                const match = pair.match(/^(.+?)[：:]\s*(.+)$/);
                if (match) {
                    result[match[1].trim()] = match[2].trim();
                }
            });
        } else {
            // 空格分隔格式：在"中文词:"前面的空格处分割
            // 正向前瞻：空格后面跟着中文字符+冒号的模式
            const parts = specStr.split(/\s+(?=[\u4e00-\u9fa5a-zA-Z]+[：:])/);
            parts.forEach(part => {
                const match = part.match(/^(.+?)[：:]\s*(.+)$/);
                if (match) {
                    result[match[1].trim()] = match[2].trim();
                }
            });
        }

        return result;
    }

    // ========== JSON快照格式解析 ==========

    /**
     * 解析编码定义快照
     * 支持两种格式：
     * 1. 数组格式: [{field_name, value, code}, ...]
     * 2. 对象格式: {code_parts: [{field_name, value, code}, ...], ...}
     * @param {string|Object} rawSnapshot - JSON字符串或对象
     * @returns {Array} - [{field_name, value, code}, ...]
     */
    static parseSnapshot(rawSnapshot) {
        if (!rawSnapshot) return [];
        try {
            const data = typeof rawSnapshot === 'string'
                ? JSON.parse(rawSnapshot) : rawSnapshot;

            // 如果是数组，直接返回
            if (Array.isArray(data)) return data;

            // 如果是对象，尝试提取 code_parts 字段
            if (data && typeof data === 'object' && Array.isArray(data.code_parts)) {
                return data.code_parts;
            }

            return [];
        } catch (e) {
            console.warn('SpecAnalyzer: 解析快照失败', e);
            return [];
        }
    }

    // ========== 通用分组 ==========

    /**
     * 按名称分组产品
     * @param {Array} items - 产品/配置列表
     * @param {string} nameKey - 名称字段名
     * @returns {Object} - { "产品名称": [item1, item2, ...], ... }
     */
    static groupByName(items, nameKey = 'product_name') {
        const groups = {};
        items.forEach(item => {
            const name = item[nameKey] || item.name || '未命名';
            if (!groups[name]) groups[name] = [];
            groups[name].push(item);
        });
        return groups;
    }

    // ========== 字符串格式差异分析 ==========

    /**
     * 分析同组产品的规格差异（字符串格式）
     * @param {Array} items - 同名产品列表
     * @param {string} specKey - 规格字段名 ('specification' 或 'product_desc')
     * @returns {Set} - 有差异的规格key集合
     */
    static findDiffKeys(items, specKey = 'specification') {
        if (!items || items.length < 2) return new Set();

        const allSpecs = items.map(item =>
            this.parseSpecString(item[specKey] || item.product_desc || item.specification)
        );

        // 收集所有规格key
        const allKeys = new Set();
        allSpecs.forEach(spec =>
            Object.keys(spec).forEach(k => allKeys.add(k))
        );

        // 检查每个key的值是否一致
        const diffKeys = new Set();
        allKeys.forEach(key => {
            const values = allSpecs.map(spec => spec[key] || '');
            // 如果值集合大小 > 1，说明有差异
            if (new Set(values).size > 1) {
                diffKeys.add(key);
            }
        });

        return diffKeys;
    }

    /**
     * 为配置列表计算差异信息（按产品名称分组）
     * @param {Array} configs - 配置列表
     * @param {string} specKey - 规格字段名
     * @returns {Map} - configId -> diffKeys 的映射
     */
    static calculateDiffMap(configs, specKey = 'specification') {
        const diffMap = new Map();
        const groups = this.groupByName(configs);

        Object.values(groups).forEach(groupConfigs => {
            if (groupConfigs.length >= 2) {
                // 同名产品有多个，计算差异
                const diffKeys = this.findDiffKeys(groupConfigs, specKey);
                groupConfigs.forEach(config => {
                    const id = config.id || config.related_product_id;
                    diffMap.set(id, diffKeys);
                });
            }
        });

        return diffMap;
    }

    // ========== JSON快照格式差异分析 ==========

    /**
     * 分析同组产品的规格差异（JSON快照格式）
     * 只比较有快照数据的产品，忽略无快照的产品
     * @param {Array} items - 同名产品列表
     * @returns {Array} - [{position, fieldName, isDiff, values}, ...]
     */
    static findDiffPositions(items) {
        if (!items || items.length < 2) return [];

        // 只保留有快照的产品
        const allSnapshots = items
            .map(item => this.parseSnapshot(item.code_definition_snapshot))
            .filter(snap => snap.length > 0);

        // 至少需要 2 个有快照的产品才能比较
        if (allSnapshots.length < 2) return [];

        // 收集所有唯一字段名（按第一个快照的顺序为基准）
        const fieldNames = [];
        const fieldNameSet = new Set();
        allSnapshots.forEach(snap => {
            snap.forEach(field => {
                const fn = field.field_name || field.name || '';
                if (fn && !fieldNameSet.has(fn)) {
                    fieldNameSet.add(fn);
                    fieldNames.push(fn);
                }
            });
        });

        const result = [];
        fieldNames.forEach((fieldName, pos) => {
            // 按 field_name 从每个快照中查找对应值
            const values = allSnapshots
                .map(snap => snap.find(s => (s.field_name || s.name) === fieldName))
                .filter(f => f?.value)
                .map(f => f.value);

            result.push({
                position: pos,
                fieldName,
                isDiff: new Set(values).size > 1,
                values: [...new Set(values)]
            });
        });

        return result;
    }

    // ========== HTML生成 ==========

    /**
     * 生成带差异高亮的规格HTML（字符串格式）
     * 支持逗号分隔和空格分隔两种格式
     * @param {string} specStr - 规格字符串
     * @param {Set} diffKeys - 有差异的key集合
     * @returns {string} - 带高亮标签的HTML
     */
    static highlightSpecString(specStr, diffKeys) {
        if (!specStr || !diffKeys || diffKeys.size === 0) {
            return specStr || '-';
        }

        // 检查是否包含逗号分隔符
        const hasComma = /[,，]/.test(specStr);
        let parts, joiner;

        if (hasComma) {
            // 逗号分隔格式
            parts = specStr.split(/[,，]\s*/);
            joiner = ', ';
        } else {
            // 空格分隔格式：在"中文词:"前面的空格处分割
            parts = specStr.split(/\s+(?=[\u4e00-\u9fa5a-zA-Z]+[：:])/);
            joiner = ' ';
        }

        return parts.map(pair => {
            const match = pair.match(/^(.+?)[：:]\s*(.+)$/);
            if (match && diffKeys.has(match[1].trim())) {
                // 只高亮指标值部分，规格名称保持不变
                return `${match[1].trim()}: <span class="spec-diff-highlight">${match[2].trim()}</span>`;
            }
            return pair;
        }).join(joiner);
    }

    /**
     * 生成带差异高亮的规格HTML（JSON快照格式）
     * @param {Object} snapshot - 产品的编码快照
     * @param {Array} diffPositions - findDiffPositions 的返回结果
     * @returns {string} - 带高亮标签的HTML
     */
    static highlightSnapshot(snapshot, diffPositions) {
        const parsed = this.parseSnapshot(snapshot);
        if (!parsed.length) return '-';

        return parsed.map((field, pos) => {
            const diff = diffPositions.find(d => d.fieldName === (field.field_name || field.name));
            if (diff && diff.isDiff) {
                // 只高亮指标值部分，规格名称保持不变
                return `${field.field_name}: <span class="spec-diff-highlight">${field.value}</span>`;
            }
            return `${field.field_name}: ${field.value}`;
        }).join(', ');
    }
}

// 导出供其他模块使用
window.SpecAnalyzer = SpecAnalyzer;
