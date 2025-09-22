/**
 * 通用的非编码规格管理函数
 * 用于产品创建和编辑页面的规格和指标选择
 */
window.SpecManagement = {
    
    /**
     * 设置非编码规格行的交互功能
     * @param {HTMLElement} row - 规格行元素
     */
    setupNonCodeSpecRow: function(row) {
        const specSelect = row.querySelector('.spec-select');
        const indicatorSelect = row.querySelector('.indicator-select');
        const specNameHidden = row.querySelector('input[name="spec_name[]"]');
        const specFieldIdHidden = row.querySelector('input[name="spec_field_ids[]"]');
        const indicatorValueHidden = row.querySelector('input[name="spec_value[]"]');
        const indicatorCodeHidden = row.querySelector('input[name="spec_option_codes[]"]');

        // 加载可选的非编码规格
        this.loadNonCodedSpecSelect(row);

        // 规格选择事件
        specSelect.addEventListener('change', () => {
            const specName = specSelect.value;
            specNameHidden.value = specName;
            
            // 获取field_id
            const selectedOption = specSelect.options[specSelect.selectedIndex];
            if (selectedOption && selectedOption.dataset.fieldId) {
                specFieldIdHidden.value = selectedOption.dataset.fieldId;
            }
            
            if (specName) {
                // 启用指标选择框并加载指标选项
                indicatorSelect.disabled = false;
                this.loadIndicatorOptionsForSpec(row, specName, selectedOption.dataset.fieldId);
            } else {
                // 禁用指标选择框
                indicatorSelect.disabled = true;
                indicatorSelect.innerHTML = '<option value="">-- 请先选择规格 --</option>';
                indicatorValueHidden.value = '';
                indicatorCodeHidden.value = '';
                specFieldIdHidden.value = '';
            }
            
            // 更新其他行的可选规格（移除已选择的）
            this.updateAllSpecSelects();
        });

        // 指标选择事件
        indicatorSelect.addEventListener('change', () => {
            const value = indicatorSelect.value;
            const selectedOption = indicatorSelect.options[indicatorSelect.selectedIndex];
            const code = selectedOption.dataset.code || '';
            
            // 更新隐藏字段
            indicatorValueHidden.value = value;
            indicatorCodeHidden.value = code;
        });
    },

    /**
     * 加载非编码规格到下拉选择框
     * @param {HTMLElement} row - 规格行元素
     */
    loadNonCodedSpecSelect: function(row) {
        const select = row.querySelector('.spec-select');
        const subcategoryId = document.querySelector('input[name="subcategory_id"]')?.value || 
                              document.getElementById('subcategory_id')?.value;
        
        if (!subcategoryId) {
            select.innerHTML = '<option value="">-- 无可用规格 --</option>';
            select.disabled = true;
            return;
        }
        
        // 获取当前已选择的规格名称（包括现有的和新添加的）
        const selectedSpecs = new Set();
        
        // 获取所有已存在的规格名称
        document.querySelectorAll('#specs-table-body tr').forEach(tr => {
            // 检查是否是编码规格或非编码规格
            const specNameInput = tr.querySelector('input[name="spec_name[]"]');
            if (specNameInput && specNameInput.value) {
                selectedSpecs.add(specNameInput.value.trim());
            }
        });
        
        // 获取其他新添加行的选择
        document.querySelectorAll('.spec-select').forEach(sel => {
            if (sel.value && sel !== select) {
                selectedSpecs.add(sel.value);
            }
        });
        
        // 调用API获取该子类别的非编码规格
        fetch(`/product-management/api/subcategory/${subcategoryId}/spec-fields`)
            .then(response => response.json())
            .then(data => {
                select.innerHTML = '<option value="">-- 请选择规格 --</option>';
                
                if (data.spec_fields) {
                    // 只显示非编码规格且未被选择的
                    const availableSpecs = data.spec_fields.filter(field => 
                        !field.use_in_code && !selectedSpecs.has(field.name)
                    );
                    
                    availableSpecs.forEach(field => {
                        const option = document.createElement('option');
                        option.value = field.name;
                        option.textContent = field.name;
                        option.dataset.fieldId = field.id;
                        select.appendChild(option);
                    });
                    
                    // 如果没有可选规格，禁用选择框
                    if (availableSpecs.length === 0) {
                        select.disabled = true;
                        select.innerHTML = '<option value="">没有更多可用的非编码规格</option>';
                    }
                }
            })
            .catch(error => {
                console.error('加载规格选项失败:', error);
                select.innerHTML = '<option value="">加载失败</option>';
                select.disabled = true;
            });
    },

    /**
     * 更新所有规格选择框的选项
     */
    updateAllSpecSelects: function() {
        document.querySelectorAll('.spec-select').forEach(select => {
            // 保存当前选中的值
            const currentValue = select.value;
            if (currentValue) {
                // 如果有选中的值，不重新加载（避免丢失选择）
                return;
            }
            // 重新加载选项
            this.loadNonCodedSpecSelect(select.parentElement.closest('tr'));
        });
        
        // 检查是否还有可添加的规格，决定是否显示添加按钮
        this.checkCanAddMoreSpecs();
    },

    /**
     * 检查是否还能添加更多规格
     */
    checkCanAddMoreSpecs: function() {
        const subcategoryId = document.querySelector('input[name="subcategory_id"]')?.value || 
                              document.getElementById('subcategory_id')?.value;
        if (!subcategoryId) return;
        
        fetch(`/product-management/api/subcategory/${subcategoryId}/spec-fields`)
            .then(response => response.json())
            .then(data => {
                if (!data.spec_fields) return;
                
                // 获取所有已使用的规格名称
                const usedSpecs = new Set();
                document.querySelectorAll('#specs-table-body input[name="spec_name[]"]').forEach(input => {
                    if (input.value) {
                        usedSpecs.add(input.value.trim());
                    }
                });
                
                // 检查是否还有未使用的非编码规格
                const hasAvailableSpecs = data.spec_fields.some(field => 
                    !field.use_in_code && !usedSpecs.has(field.name)
                );
                
                // 控制添加按钮的显示
                const addSpecBtn = document.getElementById('add-spec-btn');
                if (addSpecBtn) {
                    const addSpecContainer = addSpecBtn.closest('div');
                    addSpecContainer.style.display = hasAvailableSpecs ? 'block' : 'none';
                }
            });
    },

    /**
     * 加载指标选项
     * @param {HTMLElement} row - 规格行元素
     * @param {string} specName - 规格名称
     * @param {string} specFieldId - 规格字段ID（可选）
     */
    loadIndicatorOptionsForSpec: function(row, specName, specFieldId = null) {
        const indicatorSelect = row.querySelector('.indicator-select');
        if (!indicatorSelect) return;
        
        const subcategoryId = document.querySelector('input[name="subcategory_id"]')?.value || 
                              document.getElementById('subcategory_id')?.value;
        
        // 重置选择框
        indicatorSelect.innerHTML = '<option value="">正在加载...</option>';
        indicatorSelect.disabled = true;
        
        // 构建API请求URL
        const url = new URL('/product-management/api/spec-field-options', window.location.origin);
        url.searchParams.append('subcategory_id', subcategoryId);
        url.searchParams.append('spec_name', specName);
        if (specFieldId) {
            url.searchParams.append('field_id', specFieldId);
        }
        
        // 获取该规格的预定义指标值
        fetch(url)
            .then(response => response.json())
            .then(data => {
                indicatorSelect.innerHTML = '<option value="">-- 请选择指标值 --</option>';
                
                if (data.options && data.options.length > 0) {
                    data.options.forEach(opt => {
                        const option = document.createElement('option');
                        option.value = opt.value;
                        option.textContent = opt.value;
                        option.dataset.code = opt.code || '';
                        option.dataset.id = opt.id;
                        indicatorSelect.appendChild(option);
                    });
                    indicatorSelect.disabled = false;
                } else {
                    indicatorSelect.innerHTML = '<option value="">该规格暂无预定义指标值</option>';
                    indicatorSelect.disabled = true;
                }
            })
            .catch(error => {
                console.error('加载指标选项失败:', error);
                indicatorSelect.innerHTML = '<option value="">加载失败</option>';
                indicatorSelect.disabled = true;
            });
    }
};