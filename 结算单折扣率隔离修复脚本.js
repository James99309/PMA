// 🔥 结算单折扣率隔离修复脚本
// 解决：调整结算单明细折扣率时错误触发批价单计算的问题

(function() {
    console.log('🔥 开始修复结算单折扣率隔离问题...');
    
    // 保存原始的 updateTableTotals 函数
    const originalUpdateTableTotals = window.updateTableTotals;
    
    // 重写 updateTableTotals 函数，添加表格类型判断
    window.updateTableTotals = function(forceUpdate = false) {
        try {
            console.log('updateTableTotals 被调用，forceUpdate:', forceUpdate);
            
            // 🔥 关键修复：检查当前活跃的表格/标签页
            const activeTab = $('.nav-tabs .nav-link.active').attr('id');
            const isOnPricingTab = activeTab === 'pricing-tab';
            const isOnSettlementTab = activeTab === 'settlement-tab';
            
            console.log('当前活跃标签页:', activeTab, '批价单标签页:', isOnPricingTab, '结算单标签页:', isOnSettlementTab);
            
            // 🔥 方案1：根据当前活跃标签页，只更新对应的表格
            if (isOnPricingTab) {
                console.log('✅ 当前在批价单标签页，只更新批价单总额');
                updatePricingTableTotal();
            } else if (isOnSettlementTab) {
                console.log('✅ 当前在结算单标签页，只更新结算单总额');
                updateSettlementTableTotal();
            } else {
                console.log('⚠️ 无法确定当前标签页，使用原始函数');
                originalUpdateTableTotals(forceUpdate);
            }
            
            // 总是更新分销利润（这个不影响表格独立性）
            if (typeof updateDistributionProfit === 'function') {
                updateDistributionProfit();
            }
            
        } catch (e) {
            console.error('updateTableTotals 修复版出错，回退到原始函数:', e);
            originalUpdateTableTotals(forceUpdate);
        }
    };
    
    // 重写明细折扣率变化的事件处理函数
    function patchDiscountRateEvents() {
        // 移除现有的事件监听器
        $('#pricingTable, #settlementTable').off('input.isolation', '.discount-rate');
        
        // 重新绑定事件监听器，带隔离逻辑
        $('#pricingTable, #settlementTable').on('input.isolation', '.discount-rate', function() {
            const $row = $(this).closest('tr');
            const $table = $row.closest('table');
            const tableId = $table.attr('id');
            const tabType = tableId === 'pricingTable' ? 'pricing' : 'settlement';
            
            console.log(`🔥 明细折扣率变化 - 表格: ${tableId}, 类型: ${tabType}`);
            
            const marketPrice = parseFloat($row.find('.product-price').data('raw-value')) || 0;
            const discountRate = parseFloat($(this).val());
            
            // 如果市场价格为0，尝试从显示值获取
            if (marketPrice === 0) {
                const displayPrice = $row.find('.product-price').val();
                if (displayPrice) {
                    const cleanPrice = displayPrice.replace(/[^\d.]/g, '');
                    const parsedMarketPrice = parseFloat(cleanPrice) || 0;
                    if (parsedMarketPrice > 0) {
                        $row.find('.product-price').data('raw-value', parsedMarketPrice);
                    }
                }
            }
            
            // 验证并计算
            if (!isNaN(discountRate) && discountRate >= 0 && marketPrice > 0) {
                const discountedPrice = marketPrice * (discountRate / 100);
                
                // 更新单价显示
                $row.find('.discounted-price')
                    .data('raw-value', discountedPrice)
                    .val(formatNumber(discountedPrice));
                
                // 重新计算小计
                calculateSubtotal($row);
                
                // 🔥 关键修复：只更新当前表格的总额
                if (tabType === 'pricing') {
                    console.log('✅ 只更新批价单总额');
                    updatePricingTableTotal();
                } else if (tabType === 'settlement') {
                    console.log('✅ 只更新结算单总额');
                    updateSettlementTableTotal();
                }
                
                // 重新计算总折扣率
                calculateAndUpdateTotalDiscountRate(tabType, true);
                
                console.log(`✅ ${tabType}明细折扣率更新完成，未影响其他表格`);
            }
        });
        
        console.log('✅ 明细折扣率事件监听器已重新绑定');
    }
    
    // 重写单价变化的事件处理函数
    function patchUnitPriceEvents() {
        // 移除现有的事件监听器
        $('#pricingTable, #settlementTable').off('input.isolation', '.discounted-price');
        
        // 重新绑定事件监听器，带隔离逻辑
        $('#pricingTable, #settlementTable').on('input.isolation', '.discounted-price', function() {
            const $row = $(this).closest('tr');
            const $table = $row.closest('table');
            const tableId = $table.attr('id');
            const tabType = tableId === 'pricingTable' ? 'pricing' : 'settlement';
            
            console.log(`🔥 明细单价变化 - 表格: ${tableId}, 类型: ${tabType}`);
            
            const rawValue = $(this).val().replace(/[^\d.]/g, '');
            
            if (rawValue) {
                // 处理可能的多个小数点
                let parts = rawValue.split('.');
                if (parts.length > 2) {
                    rawValue = parts[0] + '.' + parts.slice(1).join('');
                }
                
                const discountedPrice = parseFloat(rawValue);
                if (!isNaN(discountedPrice) && discountedPrice >= 0) {
                    // 保存原始值
                    $(this).data('raw-value', discountedPrice);
                    
                    // 反算折扣率
                    const marketPrice = parseFloat($row.find('.product-price').data('raw-value')) || 0;
                    if (marketPrice > 0) {
                        const discountRate = (discountedPrice / marketPrice) * 100;
                        const clampedDiscountRate = Math.max(0, Math.min(1000, discountRate));
                        $row.find('.discount-rate').val(clampedDiscountRate.toFixed(1));
                    }
                    
                    // 重新计算小计
                    calculateSubtotal($row);
                    
                    // 🔥 关键修复：只更新当前表格的总额
                    if (tabType === 'pricing') {
                        console.log('✅ 只更新批价单总额');
                        updatePricingTableTotal();
                    } else if (tabType === 'settlement') {
                        console.log('✅ 只更新结算单总额');
                        updateSettlementTableTotal();
                    }
                    
                    // 重新计算总折扣率
                    calculateAndUpdateTotalDiscountRate(tabType, true);
                    
                    console.log(`✅ ${tabType}明细单价更新完成，未影响其他表格`);
                }
            }
        });
        
        console.log('✅ 明细单价事件监听器已重新绑定');
    }
    
    // 重写数量变化的事件处理函数
    function patchQuantityEvents() {
        // 移除现有的事件监听器
        $('#pricingTable, #settlementTable').off('input.isolation change.isolation', '.quantity');
        
        // 重新绑定事件监听器，带隔离逻辑
        $('#pricingTable, #settlementTable').on('input.isolation change.isolation', '.quantity', function() {
            const $row = $(this).closest('tr');
            const $table = $row.closest('table');
            const tableId = $table.attr('id');
            const tabType = tableId === 'pricingTable' ? 'pricing' : 'settlement';
            
            console.log(`🔥 明细数量变化 - 表格: ${tableId}, 类型: ${tabType}`);
            
            const $input = $(this);
            const inputValue = $input.val().trim();
            let quantity = parseInt(inputValue, 10);
            
            // 验证数量
            if (isNaN(quantity) || quantity < 1) {
                quantity = 1;
            }
            
            // 同步data-raw-value和显示值
            $input.data('raw-value', quantity);
            $input.val(quantity);
            
            // 重新计算小计
            calculateSubtotal($row);
            
            // 🔥 关键修复：只更新当前表格的总额
            if (tabType === 'pricing') {
                console.log('✅ 只更新批价单总额');
                updatePricingTableTotal();
            } else if (tabType === 'settlement') {
                console.log('✅ 只更新结算单总额');
                updateSettlementTableTotal();
            }
            
            console.log(`✅ ${tabType}明细数量更新完成，未影响其他表格`);
        });
        
        console.log('✅ 明细数量事件监听器已重新绑定');
    }
    
    // 应用所有补丁
    patchDiscountRateEvents();
    patchUnitPriceEvents();
    patchQuantityEvents();
    
    // 测试函数：验证修复效果
    window.testIsolation = function() {
        console.log('🧪 开始测试结算单折扣率隔离效果...');
        
        // 切换到结算单标签页
        $('#settlement-tab').click();
        
        setTimeout(() => {
            const $firstRow = $('#settlementTable tbody tr:first');
            if ($firstRow.length > 0) {
                const $discountInput = $firstRow.find('.discount-rate');
                if ($discountInput.length > 0) {
                    console.log('🧪 触发结算单第一行折扣率变化...');
                    
                    const oldPricingTotal = $('#pricingTotalAmount').text();
                    const oldSettlementTotal = $('#settlementTotalAmount').text();
                    
                    console.log('变化前 - 批价单总额:', oldPricingTotal, '结算单总额:', oldSettlementTotal);
                    
                    // 触发折扣率变化
                    $discountInput.val('85.0').trigger('input');
                    
                    setTimeout(() => {
                        const newPricingTotal = $('#pricingTotalAmount').text();
                        const newSettlementTotal = $('#settlementTotalAmount').text();
                        
                        console.log('变化后 - 批价单总额:', newPricingTotal, '结算单总额:', newSettlementTotal);
                        
                        if (oldPricingTotal === newPricingTotal) {
                            console.log('✅ 测试通过！批价单总额未被影响');
                        } else {
                            console.log('❌ 测试失败！批价单总额被错误更新');
                        }
                        
                        if (oldSettlementTotal !== newSettlementTotal) {
                            console.log('✅ 测试通过！结算单总额正确更新');
                        } else {
                            console.log('⚠️ 结算单总额未更新，可能需要检查');
                        }
                    }, 500);
                } else {
                    console.log('❌ 测试失败：找不到结算单折扣率输入框');
                }
            } else {
                console.log('❌ 测试失败：找不到结算单行');
            }
        }, 500);
    };
    
    console.log('🔥 结算单折扣率隔离修复完成！');
    console.log('💡 使用 testIsolation() 函数测试修复效果');
    
})(); 