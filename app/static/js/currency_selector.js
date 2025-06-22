/**
 * 货币选择器组件
 * 提供货币选择和实时汇率转换功能
 */

class CurrencySelector {
    constructor() {
        this.supportedCurrencies = [
            { code: 'USD', name: '美元', symbol: '$' },
            { code: 'CNY', name: '人民币', symbol: '￥' },
            { code: 'SGD', name: '新加坡元', symbol: 'S$' },
            { code: 'MYR', name: '马来西亚林吉特', symbol: 'RM' },
            { code: 'IDR', name: '印尼盾', symbol: 'Rp' },
            { code: 'THB', name: '泰铢', symbol: '฿' }
        ];
        
        this.exchangeRates = {};
        this.baseCurrency = 'CNY';
        this.lastUpdated = null;
        
        this.init();
    }
    
    async init() {
        try {
            await this.loadExchangeRates();
        } catch (error) {
            console.error('初始化货币选择器失败:', error);
        }
    }
    
    /**
     * 加载汇率数据
     */
    async loadExchangeRates(baseCurrency = 'CNY') {
        try {
            const response = await fetch(`/api/v1/exchange-rate/rates?base=${baseCurrency}`);
            
            // 检查响应状态
            if (response.status === 302 || response.status === 401) {
                console.warn('汇率API需要认证，使用默认汇率');
                this.exchangeRates = this.getDefaultRates();
                this.baseCurrency = baseCurrency;
                this.lastUpdated = new Date();
                return;
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.exchangeRates = result.data.rates;
                this.baseCurrency = result.data.base_currency;
                this.lastUpdated = new Date();
                console.log('汇率数据加载成功:', this.exchangeRates);
            } else {
                throw new Error(result.message || '获取汇率失败');
            }
        } catch (error) {
            console.warn('加载汇率失败，使用默认汇率:', error);
            // 使用默认汇率
            this.exchangeRates = this.getDefaultRates();
            this.baseCurrency = baseCurrency;
            this.lastUpdated = new Date();
        }
    }
    
    /**
     * 获取默认汇率
     */
    getDefaultRates() {
        return {
            'CNY': 1.0,
            'USD': 0.14,
            'SGD': 0.19,
            'MYR': 0.65,
            'IDR': 2100.0,
            'THB': 5.0
        };
    }
    
    /**
     * 创建货币选择下拉框
     */
    createCurrencySelect(selectedCurrency = 'CNY', selectId = 'currency', selectName = 'currency') {
        const select = document.createElement('select');
        select.id = selectId;
        select.name = selectName;
        select.className = 'form-select';
        
        this.supportedCurrencies.forEach(currency => {
            const option = document.createElement('option');
            option.value = currency.code;
            option.textContent = `${currency.name} (${currency.code})`;
            if (currency.code === selectedCurrency) {
                option.selected = true;
            }
            select.appendChild(option);
        });
        
        return select;
    }
    
    /**
     * 初始化现有的货币选择框
     */
    initializeCurrencySelects() {
        const currencySelects = document.querySelectorAll('select[name="currency"], select[id*="currency"]');
        
        currencySelects.forEach(select => {
            // 保存当前选中的值
            const currentValue = select.value || 'CNY';
            
            // 清空现有选项
            select.innerHTML = '';
            
            // 添加货币选项
            this.supportedCurrencies.forEach(currency => {
                const option = document.createElement('option');
                option.value = currency.code;
                option.textContent = `${currency.name} (${currency.code})`;
                // 恢复之前的选中状态
                if (currency.code === currentValue) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
            
            // 确保设置正确的值
            select.value = currentValue;
        });
    }
    
    /**
     * 货币转换
     */
    async convertAmount(amount, fromCurrency, toCurrency) {
        if (fromCurrency === toCurrency) {
            return parseFloat(amount);
        }
        
        try {
            const response = await fetch('/api/v1/exchange-rate/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    amount: parseFloat(amount),
                    from_currency: fromCurrency,
                    to_currency: toCurrency
                })
            });
            
            // 检查响应状态
            if (response.status === 302 || response.status === 401) {
                console.warn('汇率转换API需要认证，使用本地转换');
                return this.convertAmountLocally(amount, fromCurrency, toCurrency);
            }
            
            const result = await response.json();
            
            if (result.success) {
                return result.data.converted_amount;
            } else {
                throw new Error(result.message || '货币转换失败');
            }
        } catch (error) {
            console.warn('货币转换API失败，使用本地转换:', error);
            // 使用本地汇率进行转换
            return this.convertAmountLocally(amount, fromCurrency, toCurrency);
        }
    }
    
    /**
     * 本地货币转换（使用缓存的汇率）
     */
    convertAmountLocally(amount, fromCurrency, toCurrency) {
        if (fromCurrency === toCurrency) {
            return parseFloat(amount);
        }
        
        const rates = this.exchangeRates;
        let convertedAmount = parseFloat(amount);
        
        // 如果源货币不是基准货币，先转换为基准货币
        if (fromCurrency !== this.baseCurrency) {
            if (rates[fromCurrency]) {
                convertedAmount = convertedAmount / rates[fromCurrency];
            }
        }
        
        // 如果目标货币不是基准货币，再转换为目标货币
        if (toCurrency !== this.baseCurrency) {
            if (rates[toCurrency]) {
                convertedAmount = convertedAmount * rates[toCurrency];
            }
        }
        
        return Math.round(convertedAmount * 100) / 100;
    }
    
    /**
     * 获取货币符号
     */
    getCurrencySymbol(currencyCode) {
        const currency = this.supportedCurrencies.find(c => c.code === currencyCode);
        return currency ? currency.symbol : currencyCode;
    }
    
    /**
     * 格式化金额显示
     */
    formatAmount(amount, currencyCode) {
        const symbol = this.getCurrencySymbol(currencyCode);
        const formattedAmount = parseFloat(amount).toLocaleString('zh-CN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        return `${symbol}${formattedAmount}`;
    }
    
    /**
     * 批量转换表格中的价格
     */
    async convertTablePrices(tableSelector, fromCurrency, toCurrency, priceColumnClass = '.price-cell') {
        const table = document.querySelector(tableSelector);
        if (!table) return;
        
        const priceCells = table.querySelectorAll(priceColumnClass);
        
        for (const cell of priceCells) {
            const originalAmount = parseFloat(cell.dataset.originalAmount || cell.textContent.replace(/[^\d.]/g, ''));
            if (!isNaN(originalAmount)) {
                try {
                    const convertedAmount = await this.convertAmount(originalAmount, fromCurrency, toCurrency);
                    cell.textContent = this.formatAmount(convertedAmount, toCurrency);
                    cell.dataset.originalAmount = originalAmount;
                    cell.dataset.currentCurrency = toCurrency;
                } catch (error) {
                    console.error('转换价格失败:', error);
                }
            }
        }
    }
    
    /**
     * 设置货币变更监听器
     */
    onCurrencyChange(callback) {
        document.addEventListener('change', (event) => {
            if (event.target.matches('select[name="currency"], select[id*="currency"]')) {
                callback(event.target.value, event.target);
            }
        });
    }
}

// 全局实例
window.currencySelector = new CurrencySelector();

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    if (window.currencySelector) {
        window.currencySelector.initializeCurrencySelects();
    }
}); 