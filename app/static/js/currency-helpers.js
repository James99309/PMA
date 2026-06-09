/**
 * 货币辅助工具模块
 * 提供货币符号、单位、除数的映射及转换功能
 *
 * @file app/static/js/currency-helpers.js
 * @description 统一的货币转换工具，用于前端显示用户结算货币
 *
 * 使用场景:
 * - 配置管理页面的费用预算和薪资分配
 * - 用户详情页的薪资明细
 * - 仪表盘的金额显示
 * - 报销单详情页
 *
 * @example
 * // 获取货币符号
 * CurrencyHelpers.getSymbol('HKD')  // 返回 'HK$'
 *
 * // 获取金额单位
 * CurrencyHelpers.getUnit('CNY')    // 返回 '万元'
 *
 * // 格式化金额
 * CurrencyHelpers.formatAmount(10000, 'HKD')  // 返回 'HK$10,000.00'
 */
window.CurrencyHelpers = (function() {
    'use strict';

    // 货币符号映射
    const SYMBOLS = {
        'CNY': '¥',
        'USD': '$',
        'HKD': 'HK$',
        'TWD': 'NT$',
        'SGD': 'S$',
        'MYR': 'RM',
        'IDR': 'Rp',
        'THB': '฿',
        'VND': '₫'
    };

    // 货币中文名映射
    const NAMES = {
        'CNY': '人民币',
        'USD': '美元',
        'SGD': '新加坡元',
        'MYR': '马来西亚林吉特',
        'HKD': '港币',
        'IDR': '印尼盾',
        'THB': '泰铢',
        'TWD': '新台币',
        'VND': '越南盾'
    };

    // 产品地区面价支持的货币（排除系统内部用货币）
    const REGION_PRICE_CURRENCIES = ['CNY', 'USD', 'SGD', 'MYR', 'HKD', 'IDR', 'THB'];

    // 货币单位映射（用于大金额显示）
    const UNITS = {
        'CNY': '万元',
        'USD': 'K',
        'HKD': 'K',
        'TWD': 'K',
        'SGD': 'K',
        'MYR': 'K',
        'IDR': 'M',  // 印尼盾用百万
        'THB': 'K',
        'VND': 'M'   // 越南盾用百万
    };

    // 货币除数映射（用于将原始金额转换为显示单位）
    const DIVISORS = {
        'CNY': 10000,    // 万
        'USD': 1000,     // K (千)
        'HKD': 1000,
        'TWD': 1000,
        'SGD': 1000,
        'MYR': 1000,
        'IDR': 1000000,  // M (百万)
        'THB': 1000,
        'VND': 1000000
    };

    // 默认值（可通过 setDefaults 由模板配置覆盖）
    const defaults = {
        currency: 'CNY',
        symbol: '¥',
        unit: '万元',
        divisor: 10000
    };

    // 汇率存储（CNY → 其他货币）
    let exchangeRate = 1;

    return {
        /**
         * 获取货币中文名
         */
        getName(currency) {
            return NAMES[currency] || currency;
        },

        /**
         * 获取货币列表（用于下拉选择器）
         * @param {string[]} [codes] - 限定返回的货币代码，默认返回地区面价支持的全部货币
         * @returns {{code:string, name:string, symbol:string, label:string}[]}
         */
        getCurrencyList(codes) {
            return (codes || REGION_PRICE_CURRENCIES).map(function(code) {
                return {
                    code:   code,
                    name:   NAMES[code]   || code,
                    symbol: SYMBOLS[code] || code,
                    label:  code + ' ' + (NAMES[code] || code)
                };
            });
        },

        /**
         * 获取货币符号
         * @param {string} currency - 货币代码 (如 'CNY', 'USD', 'HKD')
         * @returns {string} 货币符号
         */
        getSymbol(currency) {
            return SYMBOLS[currency] || defaults.symbol;
        },

        /**
         * 获取金额单位（用于大金额显示）
         * @param {string} currency - 货币代码
         * @returns {string} 金额单位 (如 '万元', 'K', 'M')
         */
        getUnit(currency) {
            return UNITS[currency] || 'K';
        },

        /**
         * 获取金额除数
         * @param {string} currency - 货币代码
         * @returns {number} 除数
         */
        getDivisor(currency) {
            return DIVISORS[currency] || 1000;
        },

        /**
         * 格式化大金额（已除以除数的值）
         * @param {number} amount - 金额数值
         * @param {string} currency - 货币代码
         * @param {Object} options - 选项
         * @param {boolean} [options.withSymbol=true] - 是否包含货币符号
         * @param {boolean} [options.withUnit=true] - 是否包含单位
         * @param {number} [options.decimals=2] - 小数位数
         * @returns {string} 格式化后的金额字符串
         */
        formatLargeAmount(amount, currency, options = {}) {
            const symbol = options.withSymbol !== false ? this.getSymbol(currency) : '';
            const unit = options.withUnit !== false ? this.getUnit(currency) : '';
            const decimals = options.decimals ?? 2;

            const formatted = Number(amount || 0).toLocaleString('en-US', {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            });

            return `${symbol}${formatted}${unit ? ' ' + unit : ''}`;
        },

        /**
         * 格式化普通金额
         * @param {number} amount - 金额数值
         * @param {string} currency - 货币代码
         * @param {Object} options - 选项
         * @param {boolean} [options.withSymbol=true] - 是否包含货币符号
         * @param {number} [options.decimals=2] - 小数位数
         * @returns {string} 格式化后的金额字符串
         */
        formatAmount(amount, currency, options = {}) {
            const symbol = options.withSymbol !== false ? this.getSymbol(currency) : '';
            const decimals = options.decimals ?? 2;

            const formatted = Number(amount || 0).toLocaleString('en-US', {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            });

            return `${symbol}${formatted}`;
        },

        /**
         * 设置默认值（用于 Jinja 模板传入系统配置）
         * @param {Object} config - 配置对象
         * @param {string} [config.currency] - 默认货币代码
         * @param {string} [config.symbol] - 默认货币符号
         * @param {string} [config.unit] - 默认金额单位
         * @param {number} [config.divisor] - 默认除数
         */
        setDefaults(config) {
            if (config.currency) defaults.currency = config.currency;
            if (config.symbol) defaults.symbol = config.symbol;
            if (config.unit) defaults.unit = config.unit;
            if (config.divisor) defaults.divisor = config.divisor;
        },

        /**
         * 获取当前默认配置
         * @returns {Object} 默认配置对象
         */
        getDefaults() {
            return { ...defaults };
        },

        /**
         * 获取所有支持的货币代码
         * @returns {string[]} 货币代码数组
         */
        getSupportedCurrencies() {
            return Object.keys(SYMBOLS);
        },

        /**
         * 检查是否支持指定货币
         * @param {string} currency - 货币代码
         * @returns {boolean} 是否支持
         */
        isSupported(currency) {
            return currency in SYMBOLS;
        },

        /**
         * 智能格式化大金额（自动选择 K 或 M 单位）
         * - CNY: 固定使用万元
         * - 其他货币: >= 1000K 自动转为 M
         *
         * @param {number} amount - 已转换为显示单位的金额（如 3885 表示 3885K）
         * @param {string} currency - 货币代码
         * @param {Object} options - 选项
         * @param {boolean} [options.withSymbol=false] - 是否包含货币符号
         * @returns {string} 格式化后的金额字符串（如 "3.89M"）
         *
         * @example
         * formatWithSmartUnit(3885, 'HKD')  // 返回 '3.89M'
         * formatWithSmartUnit(500, 'HKD')   // 返回 '500K'
         * formatWithSmartUnit(388, 'CNY')   // 返回 '388万元'
         */
        formatWithSmartUnit(amount, currency, options = {}) {
            if (!amount) {
                const symbol = options.withSymbol ? this.getSymbol(currency) : '';
                return symbol + '0';
            }

            const symbol = options.withSymbol ? this.getSymbol(currency) : '';
            const baseUnit = UNITS[currency] || 'K';

            // CNY 固定用万元
            if (currency === 'CNY') {
                return symbol + amount + '万元';
            }

            // IDR/VND 已经是 M 单位，直接返回
            if (baseUnit === 'M') {
                return symbol + amount + 'M';
            }

            // 其他货币（K单位）：>= 1000 用 M，否则用 K
            if (amount >= 1000) {
                const mValue = (amount / 1000).toFixed(2).replace(/\.?0+$/, '');
                return symbol + mValue + 'M';
            }
            return symbol + amount + 'K';
        },

        // ========== 汇率转换功能 ==========

        /**
         * 设置汇率（CNY → 用户货币）
         * @param {number} rate - 汇率值（如 1.11 表示 1 CNY = 1.11 HKD）
         */
        setExchangeRate(rate) {
            exchangeRate = rate || 1;
        },

        /**
         * 获取当前汇率
         * @returns {number} 汇率值
         */
        getExchangeRate() {
            return exchangeRate;
        },

        /**
         * CNY 元 → 用户货币显示单位
         * 用于显示时将系统存储的 CNY 元转换为用户货币的显示单位（K/M/万元）
         *
         * @param {number} amountInYuan - CNY 元金额
         * @param {string} userCurrency - 用户货币代码
         * @returns {number} 用户货币显示单位的数值
         *
         * @example
         * // 汇率 1.11，4000000 CNY元 → HKD
         * convertFromCNYYuan(4000000, 'HKD')  // 返回 4440 (即 4440K HKD)
         */
        convertFromCNYYuan(amountInYuan, userCurrency) {
            if (!amountInYuan) return 0;
            const userDivisor = DIVISORS[userCurrency] || 1000;
            // CNY元 × 汇率 ÷ 用户货币除数 = 用户货币显示单位
            return amountInYuan * exchangeRate / userDivisor;
        },

        /**
         * 用户货币显示单位 → CNY 元
         * 用于保存时将用户输入的金额转换回系统存储的 CNY 元
         *
         * @param {number} amountInUserUnit - 用户货币显示单位的金额
         * @param {string} userCurrency - 用户货币代码
         * @returns {number} CNY 元金额
         *
         * @example
         * // 汇率 1.11，4440K HKD → CNY元
         * convertToCNYYuan(4440, 'HKD')  // 返回 4000000 (即 400万 CNY元)
         */
        convertToCNYYuan(amountInUserUnit, userCurrency) {
            if (!amountInUserUnit || exchangeRate === 0) return 0;
            const userDivisor = DIVISORS[userCurrency] || 1000;
            // 用户货币显示单位 × 用户货币除数 ÷ 汇率 = CNY元
            return amountInUserUnit * userDivisor / exchangeRate;
        },

        /**
         * 从 CNY 元格式化为用户货币显示
         * 一站式函数：CNY元 → 汇率转换 → 用户货币单位 → 智能格式化
         *
         * @param {number} amountInYuan - CNY 元金额
         * @param {string} userCurrency - 用户货币代码
         * @param {Object} options - 选项
         * @param {boolean} [options.withSymbol=true] - 是否包含货币符号
         * @param {boolean} [options.smartUnit=true] - 是否使用智能单位（K/M自动切换）
         * @returns {string} 格式化后的金额字符串
         *
         * @example
         * // 汇率 1.11
         * formatFromCNYYuan(4000000, 'HKD')  // 返回 'HK$4.44M'
         * formatFromCNYYuan(400000, 'HKD')   // 返回 'HK$444K'
         */
        formatFromCNYYuan(amountInYuan, userCurrency, options = {}) {
            const converted = this.convertFromCNYYuan(amountInYuan, userCurrency);
            const withSymbol = options.withSymbol !== false;
            const smartUnit = options.smartUnit !== false;

            if (smartUnit) {
                return this.formatWithSmartUnit(converted, userCurrency, { withSymbol });
            } else {
                return this.formatLargeAmount(converted, userCurrency, { withSymbol });
            }
        },

        /**
         * CNY 万元 → 用户货币显示单位
         * 便捷函数：将 CNY 万元（系统常用存储单位）转换为用户货币显示单位
         *
         * @param {number} amountInWan - CNY 万元金额
         * @param {string} userCurrency - 用户货币代码
         * @returns {number} 用户货币显示单位的数值
         *
         * @example
         * // 汇率 1.11，400万元 CNY → HKD
         * convertFromCNYWan(400, 'HKD')  // 返回 4440 (即 4440K HKD)
         */
        convertFromCNYWan(amountInWan, userCurrency) {
            // 万元 × 10000 = 元
            return this.convertFromCNYYuan(amountInWan * 10000, userCurrency);
        },

        /**
         * 用户货币显示单位 → CNY 万元
         * 便捷函数：将用户货币转换为 CNY 万元（系统常用存储单位）
         *
         * @param {number} amountInUserUnit - 用户货币显示单位的金额
         * @param {string} userCurrency - 用户货币代码
         * @returns {number} CNY 万元金额
         *
         * @example
         * // 汇率 1.11，4440K HKD → CNY万元
         * convertToCNYWan(4440, 'HKD')  // 返回 400 (即 400万元)
         */
        convertToCNYWan(amountInUserUnit, userCurrency) {
            // 元 ÷ 10000 = 万元
            return this.convertToCNYYuan(amountInUserUnit, userCurrency) / 10000;
        },

        /**
         * 从 CNY 万元格式化为用户货币显示
         *
         * @param {number} amountInWan - CNY 万元金额
         * @param {string} userCurrency - 用户货币代码
         * @param {Object} options - 选项
         * @returns {string} 格式化后的金额字符串
         *
         * @example
         * // 汇率 1.11
         * formatFromCNYWan(400, 'HKD')  // 返回 'HK$4.44M'
         */
        formatFromCNYWan(amountInWan, userCurrency, options = {}) {
            return this.formatFromCNYYuan(amountInWan * 10000, userCurrency, options);
        }
    };
})();
