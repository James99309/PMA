// 🔥 结算单总折扣率调整修复脚本
(function() {
    console.log('开始修复结算单总折扣率调整问题...');
    
    // 重写结算单总折扣率更新函数
    window.updateSettlementTotalDiscount = function(newDiscountRate) {
        console.log(`更新结算单总折扣率为: ${newDiscountRate}%`);
        
        let updatedRows = 0;
        let totalRows = 0;
        
        $('#settlementTable tbody tr').each(function() {
            const $row = $(this);
            const productName = $row.find('.product-name').val() || $row.find('td:first').text().trim();
            
            if (productName && productName.trim()) {
                totalRows++;
                
                // 获取市场价格
                const $marketPriceInput = $row.find('.product-price');
                let marketPrice = parseFloat($marketPriceInput.data('raw-value')) || 0;
                
                if (marketPrice === 0) {
                    // 尝试从显示值解析市场价格
                    const displayPrice = $marketPriceInput.val() || $marketPriceInput.text();
                    if (displayPrice) {
                        const cleanPrice = displayPrice.replace(/[^\d.]/g, '');
                        marketPrice = parseFloat(cleanPrice) || 0;
                        if (marketPrice > 0) {
                            $marketPriceInput.data('raw-value', marketPrice);
                        }
                    }
                }
                
                console.log(`第${totalRows}行: 产品=${productName}, 市场价=${marketPrice}`);
                
                if (marketPrice > 0) {
                    // 计算新的单价 (市场价 * 折扣率%)
                    const newUnitPrice = marketPrice * (newDiscountRate / 100);
                    
                    // 更新折扣率显示
                    const $discountInput = $row.find('.discount-rate');
                    $discountInput.val(newDiscountRate.toFixed(1));
                    
                    // 更新单价显示
                    const $unitPriceInput = $row.find('.discounted-price');
                    $unitPriceInput.val(newUnitPrice.toFixed(2));
                    $unitPriceInput.data('raw-value', newUnitPrice);
                    
                    // 获取数量（使用修复后的函数）
                    const quantity = getQuantityValue($row);
                    
                    // 计算新的小计
                    const newSubtotal = newUnitPrice * quantity;
                    
                    // 更新小计显示
                    const $subtotalInput = $row.find('.subtotal');
                    $subtotalInput.val(newSubtotal.toFixed(2));
                    $subtotalInput.data('raw-value', newSubtotal);
                    
                    console.log(`第${totalRows}行更新: 折扣率=${newDiscountRate}%, 单价=${newUnitPrice.toFixed(2)}, 数量=${quantity}, 小计=${newSubtotal.toFixed(2)}`);
                    updatedRows++;
                } else {
                    console.warn(`第${totalRows}行市场价格无效: ${marketPrice}`);
                }
            }
        });
        
        // 重新计算总金额
        updateTableTotals(true);
        
        console.log(`✅ 结算单总折扣率更新完成！共${totalRows}行，已更新${updatedRows}行`);
        return updatedRows;
    };
    
    // 重写 updateTotalDiscount 函数，确保正确处理结算单
    const originalUpdateTotalDiscount = window.updateTotalDiscount;
    window.updateTotalDiscount = function(tabType, discountRate) {
        console.log(`updateTotalDiscount 调用: tabType=${tabType}, discountRate=${discountRate}`);
        
        if (tabType === 'settlement') {
            // 使用专门的结算单更新函数
            return updateSettlementTotalDiscount(parseFloat(discountRate));
        } else {
            // 批价单使用原有逻辑
            if (originalUpdateTotalDiscount) {
                return originalUpdateTotalDiscount(tabType, discountRate);
            }
        }
    };
    
    // 绑定结算单总折扣率输入框事件
    function bindSettlementDiscountEvents() {
        // 查找结算单总折扣率输入框
        const $settlementDiscountInput = $('#settlementTotalDiscount');
        
        if ($settlementDiscountInput.length > 0) {
            console.log('找到结算单总折扣率输入框，绑定事件...');
            
            // 移除旧的事件监听器，避免重复绑定
            $settlementDiscountInput.off('change.settlementFix input.settlementFix');
            
            // 绑定新的事件监听器
            $settlementDiscountInput.on('change.settlementFix input.settlementFix', function() {
                const newRate = parseFloat($(this).val()) || 0;
                console.log(`结算单总折扣率输入变化: ${newRate}%`);
                updateSettlementTotalDiscount(newRate);
            });
            
            console.log('✅ 结算单总折扣率事件绑定完成');
        } else {
            console.warn('未找到结算单总折扣率输入框 (#settlementTotalDiscount)');
            
            // 尝试查找其他可能的选择器
            const possibleSelectors = [
                'input[id*="settlement"][id*="discount"]',
                'input[name*="settlement"][name*="discount"]',
                '.settlement input[id*="discount"]',
                '#settlement-content input[id*="discount"]'
            ];
            
            for (const selector of possibleSelectors) {
                const $input = $(selector);
                if ($input.length > 0) {
                    console.log(`找到可能的结算单折扣率输入框: ${selector}`);
                    $input.off('change.settlementFix input.settlementFix');
                    $input.on('change.settlementFix input.settlementFix', function() {
                        const newRate = parseFloat($(this).val()) || 0;
                        console.log(`结算单总折扣率输入变化: ${newRate}%`);
                        updateSettlementTotalDiscount(newRate);
                    });
                    break;
                }
            }
        }
    }
    
    // 立即绑定事件
    bindSettlementDiscountEvents();
    
    // 测试当前结算单状态
    function testCurrentSettlementState() {
        console.log('\n=== 当前结算单状态测试 ===');
        
        let validRows = 0;
        $('#settlementTable tbody tr').each(function(index) {
            const $row = $(this);
            const productName = $row.find('.product-name').val() || $row.find('td:first').text().trim();
            
            if (productName && productName.trim()) {
                validRows++;
                const quantity = getQuantityValue($row);
                const marketPrice = parseFloat($row.find('.product-price').data('raw-value')) || 0;
                const discountRate = parseFloat($row.find('.discount-rate').val()) || 0;
                const unitPrice = parseFloat($row.find('.discounted-price').data('raw-value')) || 0;
                const subtotal = parseFloat($row.find('.subtotal').data('raw-value')) || 0;
                
                console.log(`结算单第${validRows}行状态:`);
                console.log(`  产品: ${productName}`);
                console.log(`  数量: ${quantity}`);
                console.log(`  市场价: ${marketPrice.toFixed(2)}`);
                console.log(`  折扣率: ${discountRate.toFixed(1)}%`);
                console.log(`  单价: ${unitPrice.toFixed(2)}`);
                console.log(`  小计: ${subtotal.toFixed(2)}`);
                
                // 验证计算
                const expectedUnitPrice = marketPrice * (discountRate / 100);
                const expectedSubtotal = expectedUnitPrice * quantity;
                
                console.log(`  预期单价: ${expectedUnitPrice.toFixed(2)} ${Math.abs(expectedUnitPrice - unitPrice) < 0.01 ? '✓' : '❌'}`);
                console.log(`  预期小计: ${expectedSubtotal.toFixed(2)} ${Math.abs(expectedSubtotal - subtotal) < 0.01 ? '✓' : '❌'}`);
            }
        });
        
        console.log(`结算单共有 ${validRows} 行有效数据`);
        console.log('=== 结算单状态测试完成 ===\n');
    }
    
    // 执行初始测试
    testCurrentSettlementState();
    
    console.log('✅ 结算单总折扣率修复脚本加载完成！');
    console.log('💡 现在您可以测试调整结算单总折扣率，观察计算是否正确');
    
})();

// 辅助函数：手动测试结算单总折扣率调整
function testSettlementDiscountAdjustment(testRate) {
    console.log(`\n🧪 测试结算单总折扣率调整为 ${testRate}%`);
    updateSettlementTotalDiscount(testRate);
} 