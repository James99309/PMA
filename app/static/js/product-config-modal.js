/**
 * 产品配置模态框管理类
 * 用于报价单产品明细中处理单/多产品的配置选择
 *
 * @author Claude AI
 * @version 2.0.0 (重构为使用自定义对话框API)
 * @date 2025-11-03
 */

class ProductConfigModal {
    constructor(productSelector) {
        this.productSelector = productSelector;
        this.modalId = 'productConfigModal';
        this.currentProducts = [];
        this.remainingProducts = [];  // 剩余候选产品列表（渐进式过滤）
        this.selectedProduct = null;
        this.userSelections = {};  // 用户选择的字段 {position: {code, value}}
        this.fixedFields = [];  // 固定字段（值相同的字段）
        this.selectableFields = [];  // 可选字段（值不同的字段）
        this.pendingSpecs = [];  // 待定规格列表（使用默认值的字段）
        this.configConfirmed = false;  // 配置是否已确认展示
        this.selectedConfigurations = [];  // 已选择的配置列表
        this.step2Skipped = false;  // 步骤2是否被跳过（产品无配置时）

        // 动态规格配置相关属性
        this.configurableSpecs = [];  // 可配置的规格字段列表
        this.specConfig = {};  // 用户选择的规格配置 {field_name: value}
        this.configuredMnResult = null;  // MN计算结果
        this.hasSpecChanges = false;  // 是否有规格变更

        this.init();
    }

    /**
     * 初始化模态框
     */
    init() {
        // 绑定确认按钮事件（使用onclick以便后续可覆盖）
        const confirmBtn = document.getElementById('confirmProductSelection');
        if (confirmBtn) {
            confirmBtn.onclick = () => this.confirmSelection();
        }

        // 绑定返回按钮事件
        const backBtn = document.getElementById('backToConfigSelection');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                this.backToConfigSelection();
            });
        }

        // 将步骤指示器移动到header区域
        this.moveStepIndicatorToHeader();

        // 扩展自定义对话框关闭函数，添加清理逻辑
        const originalCloseCustomDialog = window.closeCustomDialog;
        window.closeCustomDialog = (dialogId) => {
            if (dialogId === this.modalId) {
                this.reset();
            }
            originalCloseCustomDialog(dialogId);
        };
    }

    /**
     * 将步骤指示器移动到对话框header区域
     */
    moveStepIndicatorToHeader() {
        const modal = document.getElementById(this.modalId);
        if (!modal) return;

        const stepIndicator = modal.querySelector('.config-step-indicator');
        const header = modal.querySelector('.custom-dialog-header');

        if (stepIndicator && header) {
            // 移动到header内部（在关闭按钮之前）
            header.insertBefore(stepIndicator, header.firstChild);
            console.log('📍 步骤指示器已移动到header区域');
        }
    }

    /**
     * 打开配置模态框
     * @param {Object} config - 配置对象
     * @param {string} config.category - 分类名称
     * @param {string} config.subcategory - 子分类名称
     * @param {string} config.model - 型号名称
     * @param {Array} config.products - 产品列表
     */
    open(config) {
        this.currentProducts = config.products || [];

        if (this.currentProducts.length === 0) {
            console.error('No products provided');
            return;
        }

        // 强制隐藏返回按钮（初始状态）
        const backBtn = document.getElementById('backToConfigSelection');
        if (backBtn) {
            backBtn.style.display = 'none';
        }

        // 重置确认状态
        this.configConfirmed = false;

        // Step 1 时隐藏配置区域和确认展示区域
        const configArea = document.getElementById('productConfigArea');
        const selectedArea = document.getElementById('selectedConfigsArea');
        if (configArea) configArea.style.display = 'none';
        if (selectedArea) selectedArea.style.display = 'none';

        // 检测产品数量
        if (this.currentProducts.length === 1) {
            // 单个产品：直接显示产品信息
            this.showSingleProduct(this.currentProducts[0]);
        } else {
            // 多个产品：分析编码差异并显示选择器
            this.analyzeAndShowCodeSelection(this.currentProducts);
        }

        // 使用自定义对话框API打开
        showCustomDialog(this.modalId);
    }

    /**
     * 显示单个产品（无需编码选择）
     * @param {Object} product - 产品对象
     */
    showSingleProduct(product) {
        this.selectedProduct = product;

        // 填充产品基本信息
        this.fillProductBasicInfo(product);

        // 解析产品快照，生成固定字段列表
        const snapshot = this.parseSnapshot(product.code_definition_snapshot);

        // 单产品场景：所有字段都是固定的，没有可选字段
        this.fixedFields = snapshot.map((field, index) => ({
            position: index,
            fieldName: field.field_name || field.name,  // 适配新旧字段名
            isDifferent: false,
            status: 'auto_fixed',
            fixedValue: {
                code: field.code,
                value: field.value,
                unit: field.unit || null
            },
            options: [],
            selectedCode: field.code
        }));
        this.selectableFields = [];
        this.userSelections = {};
        this.remainingProducts = [product];  // 设置剩余产品为当前单产品

        // 复用 renderFields() 方法显示规格（与多产品场景一致）
        this.renderFields();

        // 显示规格选择区域（实际只显示固定字段）
        const codeSelectionArea = document.getElementById('codeSelectionArea');
        const specsArea = document.getElementById('productSpecsArea');
        if (codeSelectionArea) codeSelectionArea.style.display = 'block';
        if (specsArea) specsArea.style.display = 'none';

        // 初始化MN号显示
        this.updateMNDisplay();

        // 加载产品配置
        this.loadProductConfigurations(product.id);
    }

    /**
     * 解析编码快照辅助函数（提取为实例方法，供多处复用）
     */
    parseSnapshot(rawSnapshot) {
        if (!rawSnapshot) {
            return [];
        }

        try {
            // 如果是字符串，先解析
            let parsed = rawSnapshot;
            if (typeof rawSnapshot === 'string') {
                parsed = JSON.parse(rawSnapshot);
            }

            // 定义编码规格过滤器：
            // 1. use_in_code 必须不为 false
            // 2. 必须有编码值（code 字段非空）- 真正的编码规格必须有对应编码
            const isCodeField = (part) => {
                // use_in_code 明确为 false 的排除
                if (part.use_in_code === false) return false;
                // 没有编码值的排除（非编码规格）
                if (!part.code || part.code.trim() === '') return false;
                return true;
            };

            // 新格式：从code_parts提取（仅编码规格）
            if (parsed && parsed.code_parts && Array.isArray(parsed.code_parts)) {
                return parsed.code_parts.filter(isCodeField);
            }

            // 旧格式：直接是数组
            if (Array.isArray(parsed)) {
                return parsed.filter(isCodeField);
            }

            console.error('快照格式不匹配:', parsed);
            return [];
        } catch (e) {
            console.error('解析快照错误:', e);
            return [];
        }
    }

    /**
     * 分析编码差异并显示编码选择器
     * @param {Array} products - 产品列表
     * @param {boolean} isInitial - 是否为初始调用（首次打开）
     */
    async analyzeAndShowCodeSelection(products, isInitial = true) {
        try {
            // 初始调用：初始化剩余产品列表
            if (isInitial) {
                this.remainingProducts = [...products];
                this.userSelections = {};
                this.initialSelectablePositions = new Set();  // 记录初始可选字段位置
                this.initialFieldOptions = new Map();  // 存储每个字段的初始选项
                this.specFieldMap = new Map();  // 🆕 存储规格字段映射（可配置字段信息）
                console.log(`🎯 初始分析: ${products.length} 个产品`);

                // 🆕 首先获取可配置字段信息（在分析产品之前）
                // 从产品对象或快照中获取 subcategory_id
                let subcategoryId = products[0].subcategory_id;
                if (!subcategoryId) {
                    // 尝试从快照中获取
                    const snapshot = products[0].code_definition_snapshot;
                    if (snapshot && snapshot.subcategory && snapshot.subcategory.id) {
                        subcategoryId = snapshot.subcategory.id;
                    }
                }

                if (products.length > 0 && subcategoryId) {
                    try {
                        const specFieldsData = await this.fetchSpecFieldOptions(subcategoryId);
                        if (specFieldsData && specFieldsData.spec_fields) {
                            specFieldsData.spec_fields.forEach(sf => {
                                this.specFieldMap.set(sf.field_name, sf);
                            });
                        }
                    } catch (e) {
                        console.warn('获取规格字段选项失败:', e);
                    }
                }
            } else {
                console.log(`🔄 重新分析: ${products.length} 个剩余产品`);
            }

            // 获取第一个产品的编码快照作为基准
            const baseSnapshot = this.parseSnapshot(products[0].code_definition_snapshot);

            if (baseSnapshot.length === 0) {
                console.error('产品编码快照为空');
                this.showError('产品编码数据缺失');
                return;
            }

            // 分析每个编码位置的差异
            const codeAnalysis = [];

            baseSnapshot.forEach((field, index) => {
                const position = index;
                const fieldName = field.field_name || field.name;  // 适配新旧字段名

                // 检查该字段是否已被用户手动选择（区分手动和自动选中）
                // 修复：用户已选字段保持为可选状态，允许用户修改
                const isUserManualSelection = this.userManualSelections &&
                                              this.userManualSelections.hasOwnProperty(position);
                const userSelectedCode = isUserManualSelection
                    ? this.userSelections[position].code
                    : null;

                // 收集该位置所有产品的编码值和指标值
                const codeOptions = new Map();

                products.forEach(product => {
                    try {
                        const snapshot = this.parseSnapshot(product.code_definition_snapshot);
                        if (snapshot[position]) {
                            const codeValue = snapshot[position].code;
                            const indicatorValue = snapshot[position].value;
                            const unitValue = snapshot[position].unit || null;

                            if (!codeOptions.has(codeValue)) {
                                codeOptions.set(codeValue, {
                                    code: codeValue,
                                    value: indicatorValue,
                                    unit: unitValue,
                                    count: 0
                                });
                            }
                            codeOptions.get(codeValue).count++;
                        }
                    } catch (e) {
                        console.error('Error parsing product snapshot:', e);
                    }
                });

                // 判断是否有差异（多个选项）
                const isDifferent = codeOptions.size > 1;

                // 初始分析时，记录初始可选字段位置和选项
                if (isInitial && isDifferent) {
                    this.initialSelectablePositions.add(position);
                    this.initialFieldOptions.set(position, Array.from(codeOptions.values()));
                }

                // 检查是否为初始可选字段（即使现在只剩一个选项）
                const wasInitiallySelectable = this.initialSelectablePositions &&
                                               this.initialSelectablePositions.has(position);

                // 修复：初始可选字段即使过滤后只剩一个选项，也保持可选状态
                const showAsSelectable = isDifferent || userSelectedCode !== null || wasInitiallySelectable;

                // 确定字段状态
                let fieldStatus;
                if (userSelectedCode) {
                    fieldStatus = 'user_selected';
                } else if (isDifferent) {
                    fieldStatus = 'selectable';
                } else if (wasInitiallySelectable) {
                    fieldStatus = 'auto_selected';  // 新状态：初始可选但被过滤成单选
                } else {
                    fieldStatus = 'auto_fixed';
                }

                // 对于auto_selected状态，自动选中唯一的选项并记录到userSelections
                let autoSelectedCode = null;
                if (fieldStatus === 'auto_selected' && codeOptions.size === 1) {
                    const autoOption = codeOptions.values().next().value;
                    autoSelectedCode = autoOption.code;
                    // 将auto_selected的值加入userSelections，以便后续过滤使用
                    this.userSelections[position] = {
                        code: autoOption.code,
                        value: autoOption.value,
                        unit: autoOption.unit || null
                    };
                    console.log(`  ✓ 自动选中字段 [${position}]: ${autoOption.value} (${autoOption.code})`);
                }

                // 确定要使用的选项列表：用户选中字段使用初始选项，允许切换
                let optionsToUse = Array.from(codeOptions.values());
                if (isUserManualSelection && this.initialFieldOptions && this.initialFieldOptions.has(position)) {
                    optionsToUse = this.initialFieldOptions.get(position);
                }

                codeAnalysis.push({
                    position: position,
                    fieldName: fieldName,
                    isDifferent: showAsSelectable,
                    status: fieldStatus,
                    options: optionsToUse,
                    selectedCode: userSelectedCode || autoSelectedCode,
                    // 如果是真正的固定字段（初始就单选），记录确定的值
                    fixedValue: (!showAsSelectable) ? codeOptions.values().next().value : null
                });
            });

            // 🆕 使用已加载的可配置字段信息处理 codeAnalysis
            // 对于可配置字段（产品差异或固定），用规格定义中的全部选项替换
            if (this.specFieldMap && this.specFieldMap.size > 0) {
                codeAnalysis.forEach(field => {
                    const specField = this.specFieldMap.get(field.fieldName);
                    if (specField && specField.allow_quotation_config && specField.options.length > 0) {
                        // 标记为可配置字段
                        field.isConfigurable = true;

                        // 保存原始选项（现有产品使用的值）
                        const originalCode = field.fixedValue?.code || (field.options.length > 0 ? field.options[0].code : null);

                        // 用规格定义的全部选项替换
                        // 使用字段级别的单位（specField.unit）
                        field.options = specField.options.map(opt => ({
                            code: opt.code,
                            value: opt.value,
                            unit: specField.unit || null,  // 使用字段的单位
                            price_adjustment: opt.price_adjustment,
                            hasExistingProduct: opt.code === originalCode
                        }));

                        // 可配置字段强制设为可选（即使原来是固定字段）
                        if (specField.options.length > 1) {
                            field.isDifferent = true;
                            field.status = 'configurable';
                            // 如果原来是固定字段，保留固定值作为默认选中
                            if (field.fixedValue) {
                                field.selectedCode = field.fixedValue.code;
                                field.autoLinkedCode = field.fixedValue.code;
                            }
                        }
                    }
                });
            }

            // 分离两类字段：固定字段（确定的值）和可选字段（需要选择）
            this.fixedFields = codeAnalysis.filter(field => !field.isDifferent);
            this.selectableFields = codeAnalysis.filter(field => field.isDifferent);

            // 🆕 进一步分类可选字段：产品差异字段 vs 可配置字段
            this.productDifferenceFields = this.selectableFields.filter(field => !field.isConfigurable);
            this.configurableSelectableFields = this.selectableFields.filter(field => field.isConfigurable);

            // 显示产品数量
            const productCountElem = document.getElementById('productCount');
            if (productCountElem) {
                productCountElem.textContent = products.length;
            }

            // 填充产品基本信息（型号等）
            this.fillProductBasicInfo(products[0]);

            // 渲染规格字段（智能显示）
            this.renderFields();

            // 显示规格选择区域，隐藏规格详情区域
            const codeSelectionArea = document.getElementById('codeSelectionArea');
            const specsArea = document.getElementById('productSpecsArea');
            if (codeSelectionArea) codeSelectionArea.style.display = 'block';
            if (specsArea) specsArea.style.display = 'none';

            // 初始化MN号显示（默认为"待确定"）
            this.updateMNDisplay();
        } catch (error) {
            console.error('Error in analyzeAndShowCodeSelection:', error);
            this.showError('分析产品编码时出错');
        }
    }

    /**
     * 智能渲染规格字段（固定字段+可选字段）
     * 增强：分层显示 - 先显示产品差异字段，选完后才显示可配置字段
     */
    renderFields() {
        const container = document.getElementById('codeFieldsContainer');
        if (!container) return;

        container.innerHTML = '';

        // 动态设置标题：根据是否有可选字段
        const titleElement = document.getElementById('codeSelectionTitle');
        if (titleElement) {
            if (this.selectableFields && this.selectableFields.length > 0) {
                titleElement.innerHTML = '<i class="fas fa-sliders-h"></i> 请选择产品规格';
            } else {
                titleElement.innerHTML = '<i class="fas fa-list-ul"></i> 产品规格';
            }
        }

        // 1. 先渲染固定字段（两栏网格布局）
        if (this.fixedFields.length > 0) {
            const gridContainer = document.createElement('div');
            gridContainer.className = 'spec-fields-grid';

            this.fixedFields.forEach(field => {
                const fieldDiv = document.createElement('div');
                fieldDiv.className = 'spec-field-fixed';
                const unitText = field.fixedValue.unit ? ` ${field.fixedValue.unit}` : '';
                fieldDiv.innerHTML = `
                    <div class="spec-field-label">${field.fieldName}:</div>
                    <div class="spec-field-value">${field.fixedValue.value}${unitText}</div>
                `;
                gridContainer.appendChild(fieldDiv);
            });

            container.appendChild(gridContainer);
        }

        // 2. 渲染产品差异字段（非可配置，必须先选）
        if (this.productDifferenceFields && this.productDifferenceFields.length > 0) {
            this.productDifferenceFields.forEach(field => {
                this.renderSelectableField(container, field, false);
            });
        }

        // 3. 检查产品差异字段是否都已选择
        const allDifferenceFieldsSelected = !this.productDifferenceFields ||
            this.productDifferenceFields.length === 0 ||
            this.productDifferenceFields.every(field =>
                this.userSelections && this.userSelections[field.position]
            );

        // 4. 只有产品差异字段都选完，才渲染可配置字段
        if (this.configurableSelectableFields && this.configurableSelectableFields.length > 0) {
            if (allDifferenceFieldsSelected) {
                // 计算可配置字段的自动关联值
                this.calculateAutoLinkedValues();

                // 初始化 configurableSelections（用于自动关联的默认选择）
                if (!this.configurableSelections) {
                    this.configurableSelections = {};
                }
                this.configurableSelectableFields.forEach(field => {
                    // 如果有自动关联值且尚未被用户手动选择，初始化选择
                    if (field.autoLinkedCode && !this.configurableSelections[field.position]) {
                        const autoLinkedOption = field.options?.find(opt => opt.code === field.autoLinkedCode);
                        if (autoLinkedOption) {
                            this.configurableSelections[field.position] = {
                                code: autoLinkedOption.code,
                                value: autoLinkedOption.value,
                                unit: autoLinkedOption.unit || null
                            };
                        }
                    }
                });

                // 渲染可配置字段
                this.configurableSelectableFields.forEach(field => {
                    this.renderSelectableField(container, field, true);
                });
            } else {
                // 显示提示：请先选择产品规格差异
                this.renderConfigurableFieldsPlaceholder(container);
            }
        }
    }

    /**
     * 渲染单个可选字段
     * @param {HTMLElement} container - 容器元素
     * @param {Object} field - 字段数据
     * @param {boolean} isConfigurable - 是否为可配置字段
     */
    renderSelectableField(container, field, isConfigurable) {
        const fieldDiv = document.createElement('div');
        fieldDiv.className = 'spec-field-selectable';
        fieldDiv.dataset.position = field.position;

        // 字段标签
        const label = document.createElement('label');
        label.className = 'form-label';

        // 只显示字段名称，不显示必填和可配置符号
        label.textContent = field.fieldName;
        fieldDiv.appendChild(label);

        // 选项列表容器
        const optionsContainer = document.createElement('div');
        optionsContainer.className = 'spec-options-list';

        field.options.forEach((option, optIndex) => {
            const optionDiv = document.createElement('div');
            optionDiv.className = 'form-check d-flex align-items-center';

            // Radio input
            const input = document.createElement('input');
            input.type = 'radio';
            input.className = 'form-check-input';
            input.name = `code-${field.position}`;
            input.id = `code-${field.position}-${optIndex}`;
            input.value = option.code;

            // 检查是否应该选中
            const isAutoLinked = isConfigurable && field.autoLinkedCode === option.code;
            const isUserSelected = field.selectedCode === option.code;
            if (isAutoLinked || isUserSelected) {
                input.checked = true;
            }

            // auto_selected 状态：禁用radio（因为被过滤自动确定）- 但可配置字段不禁用
            if (field.status === 'auto_selected' && !isConfigurable) {
                input.disabled = true;
            }

            // 绑定事件处理器
            if (!input.disabled) {
                input.addEventListener('change', () => {
                    this.onFieldSelect(field.position, option.code, option.value, option.unit, isConfigurable);
                });
            }

            // Label
            const optionLabel = document.createElement('label');
            optionLabel.className = 'form-check-label';
            optionLabel.setAttribute('for', input.id);

            const unitText = option.unit ? ` ${option.unit}` : '';

            // 构建标签内容
            let labelHtml = `${option.value}${unitText}`;

            // 可配置字段的自动关联选项添加蓝色圆圈标记
            if (isAutoLinked) {
                labelHtml += ` <span class="auto-linked-indicator" title="自动关联"></span>`;
            }

            // 如果有价格增量，显示价格标识（复用货币符号，蓝色靠右，与上方价格对齐）
            let priceTag = '';
            if (option.price_adjustment && option.price_adjustment !== 0) {
                const adjustmentYuan = option.price_adjustment / 100;
                const sign = adjustmentYuan > 0 ? '+' : '';
                const currencySymbol = document.getElementById('currencySymbol')?.textContent?.trim() || '¥';
                // padding-right 约等于右侧图片区域宽度(col-md-4 约33%)，使价格与上方产品价格对齐
                priceTag = `<span class="price-adjustment-tag fw-bold text-primary" style="margin-left: auto; padding-right: calc(33.33% + 15px);">${sign}${currencySymbol}${Math.abs(adjustmentYuan).toLocaleString()}</span>`;
            }

            optionLabel.innerHTML = labelHtml;

            optionDiv.appendChild(input);
            optionDiv.appendChild(optionLabel);
            // 价格标签放在最右侧
            if (priceTag) {
                const priceSpan = document.createElement('span');
                priceSpan.innerHTML = priceTag;
                optionDiv.appendChild(priceSpan.firstChild);
            }
            optionsContainer.appendChild(optionDiv);
        });

        fieldDiv.appendChild(optionsContainer);

        // 根据字段状态添加视觉标记
        if (field.status === 'user_selected') {
            fieldDiv.classList.add('user-selected');
        } else if (field.status === 'auto_selected') {
            fieldDiv.classList.add('auto-selected');
        }
        if (isConfigurable) {
            fieldDiv.classList.add('configurable-field');
        }

        container.appendChild(fieldDiv);
    }

    /**
     * 计算可配置字段的自动关联值
     * 基于当前剩余产品的规格值
     */
    calculateAutoLinkedValues() {
        if (!this.configurableSelectableFields || !this.remainingProducts || this.remainingProducts.length === 0) {
            return;
        }

        // 使用第一个剩余产品作为参考
        const referenceProduct = this.remainingProducts[0];
        const snapshot = this.parseSnapshot(referenceProduct.code_definition_snapshot);

        this.configurableSelectableFields.forEach(field => {
            const productValue = snapshot[field.position];
            if (productValue) {
                // 产品有该字段的值 → 自动关联
                field.autoLinkedCode = productValue.code;
                field.autoLinkedValue = productValue.value;
                console.log(`  🔗 自动关联 [${field.fieldName}]: ${productValue.value} (${productValue.code})`);
            } else {
                // 产品无该字段的值 → 无自动关联
                field.autoLinkedCode = null;
                field.autoLinkedValue = null;
            }
        });
    }

    /**
     * 渲染可配置字段的占位提示
     * @param {HTMLElement} container - 容器元素
     */
    renderConfigurableFieldsPlaceholder(container) {
        const placeholderDiv = document.createElement('div');
        placeholderDiv.className = 'configurable-fields-placeholder';
        placeholderDiv.innerHTML = `
            <div class="placeholder-content">
                <i class="fas fa-info-circle text-muted"></i>
                <span class="text-muted">请先选择上方产品规格，完成后将显示可配置选项</span>
            </div>
        `;
        container.appendChild(placeholderDiv);
    }

    /**
     * 处理用户选择字段事件（核心新逻辑）
     * @param {number} position - 字段位置
     * @param {string} code - 选择的编码
     * @param {string} value - 选择的值
     * @param {string|null} unit - 单位
     * @param {boolean} isConfigurable - 是否为可配置字段
     */
    onFieldSelect(position, code, value, unit = null, isConfigurable = false) {
        console.log(`👉 用户选择字段 [${position}]: ${value} (${code})${isConfigurable ? ' [可配置]' : ''}`);

        // 🆕 可配置字段的选择逻辑不同：不过滤产品，只记录选择
        if (isConfigurable) {
            this.onConfigurableFieldSelect(position, code, value, unit);
            return;
        }

        // ✅ 非可配置字段：智能清除不兼容的选择
        // 步骤1：先只用当前选择过滤产品
        const currentSelection = { code, value, unit };
        let compatibleProducts = this.currentProducts.filter(product => {
            const snapshot = this.parseSnapshot(product.code_definition_snapshot);
            return snapshot[position]?.code === code;
        });
        console.log(`  → 当前选择匹配 ${compatibleProducts.length} 个产品`);

        // 步骤2：验证其他手动选择是否兼容
        const newUserSelections = {};
        const newUserManualSelections = {};

        if (this.userManualSelections) {
            for (const [pos, sel] of Object.entries(this.userSelections)) {
                const posInt = parseInt(pos);
                if (posInt === position) continue;  // 跳过当前字段
                if (!this.userManualSelections[posInt]) continue;  // 跳过非手动选择

                // 检查该选择是否在兼容产品中存在
                const isCompatible = compatibleProducts.some(product => {
                    const snapshot = this.parseSnapshot(product.code_definition_snapshot);
                    return snapshot[posInt]?.code === sel.code;
                });

                if (isCompatible) {
                    newUserSelections[posInt] = sel;
                    newUserManualSelections[posInt] = true;
                    // 进一步过滤产品
                    compatibleProducts = compatibleProducts.filter(product => {
                        const snapshot = this.parseSnapshot(product.code_definition_snapshot);
                        return snapshot[posInt]?.code === sel.code;
                    });
                    console.log(`  ✓ 保留兼容选择 [${posInt}]: ${sel.value}`);
                } else {
                    console.log(`  ⚠️ 清除不兼容的选择 [${posInt}]: ${sel.value}`);
                }
            }
        }

        // 步骤3：添加当前选择
        newUserSelections[position] = currentSelection;
        newUserManualSelections[position] = true;

        this.userSelections = newUserSelections;
        this.userManualSelections = newUserManualSelections;
        this.remainingProducts = compatibleProducts;

        console.log(`  → 剩余产品: ${this.remainingProducts.length} 个`);

        // 3. 检查结果并决定下一步
        if (this.remainingProducts.length === 0) {
            // 没有匹配的产品 → 错误
            console.error('❌ 没有匹配的产品！');
            this.showError('未找到匹配的产品，请检查规格选择');
            this.updateMNDisplay();

        } else if (this.remainingProducts.length === 1) {
            // 只剩一个产品 → 显示关联规格选中效果，不自动跳转
            console.log('✅ 产品规格已完全确定，显示关联效果');

            // 🆕 检测产品是否变化，如果变化则重置可配置规格状态
            const newProduct = this.remainingProducts[0];
            if (this.selectedProduct && this.selectedProduct.id !== newProduct.id) {
                console.log('📦 产品已切换，重置可配置规格状态');
                this.configurableSelections = {};
                this.configurablePriceAdjustment = 0;
                this.configurablePriceDetails = [];
            }

            this.showFinalizedSpecs();

        } else {
            // 还有多个产品 → 重新分析并渲染
            console.log(`🔄 继续筛选 (剩余 ${this.remainingProducts.length} 个产品)`);

            // 🆕 多产品情况下也重置可配置规格状态（因为还未确定最终产品）
            this.configurableSelections = {};
            this.configurablePriceAdjustment = 0;
            this.configurablePriceDetails = [];

            this.analyzeAndShowCodeSelection(this.remainingProducts, false);  // 非初始调用
        }
    }

    /**
     * 处理可配置字段的选择事件
     * 可配置字段选择不影响产品过滤，只记录用户选择并更新MN号
     * @param {number} position - 字段位置
     * @param {string} code - 选择的编码
     * @param {string} value - 选择的值
     * @param {string|null} unit - 单位
     */
    onConfigurableFieldSelect(position, code, value, unit = null) {
        // 初始化可配置字段选择存储
        if (!this.configurableSelections) {
            this.configurableSelections = {};
        }

        // 记录可配置字段的选择
        this.configurableSelections[position] = { code, value, unit };

        // 更新对应字段的 autoLinkedCode（清除自动关联标记，因为用户已手动选择）
        const field = this.configurableSelectableFields?.find(f => f.position === position);
        if (field) {
            field.userSelectedCode = code;
        }

        // 计算价格增量
        this.calculateConfigurablePriceAdjustment();

        // 立即更新价格显示
        this.updatePriceDisplay();

        // 更新MN号显示
        this.updateMNDisplay();

        // 更新产品描述（Step 1 使用 configurableSelectableFields）
        this.updateSpecificationFromConfigurableFields();
    }

    /**
     * 更新产品描述（Step 1：根据 configurableSelectableFields 的选择更新描述）
     * 与 Step 2 的 updateProductSpecification 不同，这里使用 configurableSelections
     * 如果原描述中没有该字段，会追加到末尾
     */
    updateSpecificationFromConfigurableFields() {
        const specElement = document.getElementById('configProductSpec');
        if (!specElement || !this.selectedProduct) {
            return;
        }

        // 从原始描述开始
        let specification = this.selectedProduct.specification || '';
        const addedFields = [];  // 记录需要追加的字段

        if (this.configurableSelectableFields && this.configurableSelections) {
            this.configurableSelectableFields.forEach(field => {
                const selection = this.configurableSelections[field.position];
                if (!selection) return;

                const fieldName = field.fieldName;
                const newValue = selection.value;
                const unit = selection.unit || '';

                if (newValue) {
                    // 替换描述中对应字段的值（匹配 "字段名: 值" 或 "字段名: 值 单位" 格式）
                    // 支持中英文冒号和逗号/分号分隔
                    const pattern = new RegExp(`${fieldName}[:：]\\s*[^,，;；]+`, 'g');
                    const replacement = unit ? `${fieldName}: ${newValue} ${unit}` : `${fieldName}: ${newValue}`;
                    const beforeReplace = specification;
                    specification = specification.replace(pattern, replacement);

                    // 如果替换未生效（原描述中没有该字段），记录需要追加
                    if (specification === beforeReplace) {
                        addedFields.push(replacement);
                    }
                }
            });
        }

        // 追加原描述中不存在的可配置规格
        if (addedFields.length > 0) {
            const separator = specification.trim() ? ', ' : '';
            specification = specification.trim() + separator + addedFields.join(', ');
        }

        specElement.textContent = specification;
    }

    /**
     * 更新价格显示（包含可配置字段的价格增量）
     */
    updatePriceDisplay() {
        const brandPriceElement = document.getElementById('configProductBrandPrice');
        if (!brandPriceElement || !this.selectedProduct) return;

        const brand = this.selectedProduct.brand || '';
        const basePrice = this.selectedProduct.retail_price || this.selectedProduct.market_price || 0;
        const adjustmentTotal = this.configurablePriceAdjustment || 0;
        const adjustmentYuan = adjustmentTotal / 100;
        const finalPrice = parseFloat(basePrice) + adjustmentYuan;
        const currencySymbol = document.getElementById('currencySymbol')?.textContent?.trim() || '¥';

        let priceHtml = '';
        if (adjustmentTotal !== 0) {
            // 有价格增量时，只显示新价格（橘色，与可配置字段圆圈颜色一致）
            priceHtml = `<span class="fw-bold" style="color: #f0ad4e;">${currencySymbol}${finalPrice.toLocaleString()}</span>`;
        } else {
            // 无价格增量，显示原价（蓝色）
            priceHtml = `<span class="fw-bold text-primary">${currencySymbol}${basePrice ? parseFloat(basePrice).toLocaleString() : basePrice}</span>`;
        }

        if (brand && basePrice) {
            brandPriceElement.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-muted">${brand}</span>
                    <div>${priceHtml}</div>
                </div>
            `;
        } else if (brand) {
            brandPriceElement.innerHTML = `<span class="text-muted">${brand}</span>`;
        } else if (basePrice) {
            brandPriceElement.innerHTML = `<div>${priceHtml}</div>`;
        } else {
            brandPriceElement.innerHTML = '';
        }
    }

    /**
     * 计算可配置字段的价格增量总额
     * @returns {number} 价格增量总额（分）
     */
    calculateConfigurablePriceAdjustment() {
        let total = 0;
        let adjustmentDetails = [];

        if (this.configurableSelectableFields) {
            this.configurableSelectableFields.forEach(field => {
                // 获取用户选择的 code（手动选择或自动关联）
                const selectedCode = this.configurableSelections?.[field.position]?.code
                    || field.userSelectedCode
                    || field.autoLinkedCode;

                if (selectedCode) {
                    // 找到选中选项的价格增量
                    const selectedOption = field.options?.find(opt => opt.code === selectedCode);

                    if (selectedOption && selectedOption.price_adjustment) {
                        total += selectedOption.price_adjustment;
                        adjustmentDetails.push({
                            fieldName: field.fieldName,
                            value: selectedOption.value,
                            adjustment: selectedOption.price_adjustment
                        });
                    }
                }
            });
        }

        this.configurablePriceAdjustment = total;
        this.configurablePriceDetails = adjustmentDetails;

        return total;
    }

    /**
     * 根据产品的 spec_mn 和用户的可配置字段选择，生成新的规格MN
     *
     * MN 结构：地区(0) + 分类(1) + 子分类(2) + 规格编码(3+)
     * configurableSelections 的 key 是 code_parts 数组的索引（规格字段在数组中的位置）
     * 实际 MN 位置 = 数组索引 + 3（因为前3位是地区+分类+子分类）
     *
     * @returns {string|null} 生成的规格MN字符串，如果无法生成则返回null
     */
    generateSpecMn() {
        if (!this.selectedProduct) {
            return null;
        }

        // 必须使用 spec_mn 作为基础（不是 product_mn）
        const originalSpecMn = this.selectedProduct.spec_mn;
        if (!originalSpecMn) {
            return null;
        }

        // 如果没有可配置字段选择，直接返回原始 spec_mn
        if (!this.configurableSelections || Object.keys(this.configurableSelections).length === 0) {
            return originalSpecMn;
        }

        // 将 spec_mn 转换为字符数组
        let mnChars = originalSpecMn.split('');

        // MN 结构偏移量：前3位是地区+分类+子分类，规格编码从位置3开始
        const MN_SPEC_OFFSET = 3;

        // 遍历可配置字段选择
        // key (posStr) 是 code_parts 数组的索引，需要 +3 才是 MN 中的实际位置
        for (const [posStr, selection] of Object.entries(this.configurableSelections)) {
            const arrayIndex = parseInt(posStr);
            const mnPosition = arrayIndex + MN_SPEC_OFFSET;  // 转换为 MN 中的实际位置

            if (mnPosition < mnChars.length && selection.code) {
                mnChars[mnPosition] = selection.code;
            }
        }

        return mnChars.join('');
    }

    /**
     * 根据用户已选择的字段过滤产品列表
     */
    filterProductsBySelections() {
        this.remainingProducts = this.currentProducts.filter(product => {
            const snapshot = this.parseSnapshot(product.code_definition_snapshot);

            // 检查所有用户已选择的字段是否匹配
            for (const [pos, selection] of Object.entries(this.userSelections)) {
                const position = parseInt(pos);
                if (snapshot[position]?.code !== selection.code) {
                    return false;  // 不匹配，过滤掉
                }
            }

            return true;  // 所有字段匹配，保留
        });
    }

    /**
     * 显示规格确定效果（所有规格禁用+选中）
     * 用户需要手动点击确认按钮才进入配置选择
     */
    showFinalizedSpecs() {
        if (this.remainingProducts.length !== 1) {
            console.warn('⚠️ showFinalizedSpecs() 应该只在剩余1个产品时调用');
            return;
        }

        // 确定唯一产品
        this.selectedProduct = this.remainingProducts[0];

        // 自动填充未选择的字段（非可配置字段）
        const snapshot = this.parseSnapshot(this.selectedProduct.code_definition_snapshot);
        const configurablePositions = new Set(
            (this.configurableSelectableFields || []).map(f => f.position)
        );

        snapshot.forEach((field, pos) => {
            // 🆕 只自动填充非可配置字段
            if (!this.userSelections.hasOwnProperty(pos) && !configurablePositions.has(pos)) {
                this.userSelections[pos] = {
                    code: field.code,
                    value: field.value,
                    unit: field.unit || null
                };
                console.log(`  ✓ 自动关联字段 [${pos}]: ${field.value} (${field.code})`);
            }
        });

        // 🆕 重新渲染字段，确保可配置字段显示（此时产品差异字段已全部选完）
        this.renderFields();

        // 然后在现有UI上更新状态
        this.renderAllFieldsAsSelected();

        // 更新MN号显示
        this.updateMNDisplay();

        // 显示确认规格按钮
        this.showSpecConfirmButton();

        // 标记为待确认状态
        this.specsFinalized = true;
    }

    /**
     * 将所有规格字段渲染为选中状态
     * 区分用户手动选择（可修改）和自动关联选中（禁用）
     * 🆕 可配置字段始终保持可选状态
     */
    renderAllFieldsAsSelected() {
        const container = document.getElementById('codeFieldsContainer');
        if (!container) return;

        // 获取可配置字段的位置集合
        const configurablePositions = new Set(
            (this.configurableSelectableFields || []).map(f => f.position)
        );

        // 遍历所有规格字段容器
        const fieldContainers = container.querySelectorAll('.spec-field-selectable');
        fieldContainers.forEach(fieldDiv => {
            const position = parseInt(fieldDiv.dataset.position);
            const selection = this.userSelections[position];
            if (!selection) return;

            const isManual = this.userManualSelections && this.userManualSelections[position];
            const isConfigurable = configurablePositions.has(position);

            // 找到所有单选框
            const radioInputs = fieldDiv.querySelectorAll('input[type="radio"]');
            radioInputs.forEach(radio => {
                if (radio.value === selection.code) {
                    radio.checked = true;   // 选中
                }
                // 🆕 可配置字段始终保持可用，不禁用
                // 非可配置字段：只有自动关联的才禁用
                if (!isConfigurable && !isManual) {
                    radio.disabled = true;  // 自动关联的禁用
                }
            });

            // 添加视觉提示：区分手动选择和自动关联
            if (!isManual && !isConfigurable) {
                fieldDiv.classList.add('auto-selected');
            } else if (isManual) {
                fieldDiv.classList.add('user-selected');
            }
            // 可配置字段保持原有的 configurable-field 样式
        });
    }

    /**
     * 显示确认规格按钮
     */
    showSpecConfirmButton() {
        // 修改确认按钮的文本和行为
        const confirmBtn = document.getElementById('confirmProductSelection');
        if (confirmBtn) {
            confirmBtn.innerHTML = '<i class="fas fa-check"></i> 确认规格';
            confirmBtn.onclick = () => this.confirmSpecsAndLoadConfig();
        }
    }

    /**
     * 确认规格后加载配置
     */
    confirmSpecsAndLoadConfig() {
        if (!this.specsFinalized || !this.selectedProduct) {
            console.warn('⚠️ 规格未完全确定');
            return;
        }

        console.log('✅ 用户确认规格，加载产品配置');

        // 隐藏规格选择区域（产品已确定，不再需要显示）
        const container = document.getElementById('codeFieldsContainer');
        if (container) {
            container.style.display = 'none';
        }

        // 隐藏规格选择标题（步骤2不需要显示）
        const codeSelectionTitle = document.getElementById('codeSelectionTitle');
        if (codeSelectionTitle) {
            codeSelectionTitle.style.display = 'none';
        }

        // 隐藏已选配置区域（Step 2 时不应显示，只在 Step 3 显示）
        const selectedArea = document.getElementById('selectedConfigsArea');
        if (selectedArea) selectedArea.style.display = 'none';

        // 显示返回按钮（可以返回到规格选择）
        const backBtn = document.getElementById('backToConfigSelection');
        if (backBtn) backBtn.style.display = 'inline-block';

        // 设置当前步骤并更新指示器
        this.currentStep = 2;
        this.updateStepIndicator(2);

        // 显示固定编码规格（可配置规格将在loadConfigurableSpecs加载后更新）
        this.showCodeSpecsInConfirmation();

        // 加载产品配置
        this.loadProductConfigurations(this.selectedProduct.id);

        // 重置确认按钮为原来的行为
        const confirmBtn = document.getElementById('confirmProductSelection');
        if (confirmBtn) {
            confirmBtn.innerHTML = '<i class="fas fa-check"></i> 确认选择';
            confirmBtn.onclick = () => this.confirmSelection();
        }
    }

    /**
     * 检查并最终确定产品（当只剩1个产品时）
     */
    checkAndFinalize() {
        if (this.remainingProducts.length !== 1) {
            console.warn('⚠️ checkAndFinalize() 应该只在剩余1个产品时调用');
            return;
        }

        // 确定唯一产品
        this.selectedProduct = this.remainingProducts[0];

        // 自动填充未选择的字段
        const snapshot = this.parseSnapshot(this.selectedProduct.code_definition_snapshot);
        snapshot.forEach((field, pos) => {
            if (!this.userSelections.hasOwnProperty(pos)) {
                this.userSelections[pos] = {
                    code: field.code,
                    value: field.value,
                    unit: field.unit || null
                };
                console.log(`  ✓ 自动确定字段 [${pos}]: ${field.value} (${field.code})`);
            }
        });

        // 重新分析（所有字段变为"已确定"）
        this.analyzeAndShowCodeSelection([this.selectedProduct], false);

        // 更新MN号显示（显示绿色MN号）
        this.updateMNDisplay();

        // ⭐ 新增：加载产品配置
        this.loadProductConfigurations(this.selectedProduct.id);
    }

    /**
     * 动态更新MN号显示（简化版）
     * 根据剩余产品数量显示不同状态
     */
    updateMNDisplay() {
        const mnElement = document.getElementById('configProductMn');
        if (!mnElement) return;

        const selectionCount = Object.keys(this.userSelections).length;

        // 优先检查是否已确定唯一产品（单产品场景或选择完成场景）
        if (this.remainingProducts && this.remainingProducts.length === 1) {
            // 完全确定
            const product = this.remainingProducts[0];

            // 更新型号（修复：规格选择后型号未更新的问题）
            const modelElement = document.getElementById('configProductModel');
            if (modelElement) {
                modelElement.textContent = product.product_model || product.model || '未知';
            }

            const hasConfigurableAdjustment = this.configurablePriceAdjustment > 0;

            // 🔍 调试：MN显示逻辑
            console.log('🔍 updateMNDisplay 调试信息:');
            console.log('  - product_mn:', product.product_mn);
            console.log('  - spec_mn:', product.spec_mn);
            console.log('  - configurablePriceAdjustment:', this.configurablePriceAdjustment);
            console.log('  - hasConfigurableAdjustment:', hasConfigurableAdjustment);
            console.log('  - configurableSelections:', JSON.stringify(this.configurableSelections));
            console.log('  - selectedProduct:', this.selectedProduct);

            if (hasConfigurableAdjustment) {
                // 有价格增量时：生成新的规格MN，橘色徽章 + 感叹号图标
                const generatedMn = this.generateSpecMn();
                console.log('  - generateSpecMn() 返回:', generatedMn);
                const newSpecMn = generatedMn || product.spec_mn || product.product_mn || '无';
                console.log('  - 最终显示的MN:', newSpecMn);
                mnElement.innerHTML = `
                    <span class="mn-badge" style="background-color: #f0ad4e; color: white;">
                        <i class="fas fa-exclamation-circle"></i> ${newSpecMn}
                    </span>
                `;
            } else {
                // 无价格增量时：显示产品MN，绿色徽章 + 打勾图标
                const displayMn = product.product_mn || '无';
                mnElement.innerHTML = `
                    <span class="mn-badge confirmed">
                        <i class="fas fa-check-circle"></i> ${displayMn}
                    </span>
                `;
            }

            // 更新品牌 + 价格（复用 updatePriceDisplay 以支持价格增量）
            this.updatePriceDisplay();

            // 更新规格说明
            const specElement = document.getElementById('configProductSpec');
            if (specElement) {
                specElement.textContent = product.specification || '';
            }

            this.selectedProduct = product;
            this.pendingSpecs = [];

        } else if (this.remainingProducts && this.remainingProducts.length > 1) {
            // 选择中（还有多个候选产品）- 不显示筛选状态，保持空白
            mnElement.innerHTML = '';
            // 清空品牌价格和规格说明
            const brandPriceElement = document.getElementById('configProductBrandPrice');
            if (brandPriceElement) brandPriceElement.innerHTML = '';
            const specElement = document.getElementById('configProductSpec');
            if (specElement) specElement.textContent = '';

            this.selectedProduct = null;
            this.pendingSpecs = [];

        } else if (selectionCount === 0) {
            // 完全未选择
            mnElement.innerHTML = `
                <span class="mn-badge pending">
                    <i class="fas fa-clock"></i> 待确定
                </span>
            `;
            // 清空品牌价格和规格说明
            const brandPriceElement = document.getElementById('configProductBrandPrice');
            if (brandPriceElement) brandPriceElement.innerHTML = '';
            const specElement = document.getElementById('configProductSpec');
            if (specElement) specElement.textContent = '';

            this.selectedProduct = null;
            this.pendingSpecs = [];

        } else {
            // 错误：没有匹配产品
            mnElement.innerHTML = `
                <span class="mn-badge error">
                    <i class="fas fa-exclamation-triangle"></i> 未找到匹配产品
                </span>
                <small class="text-danger d-block mt-1">
                    请检查规格选择是否正确
                </small>
            `;
            // 清空品牌价格和规格说明
            const brandPriceElement = document.getElementById('configProductBrandPrice');
            if (brandPriceElement) brandPriceElement.innerHTML = '';
            const specElement = document.getElementById('configProductSpec');
            if (specElement) specElement.textContent = '';

            this.selectedProduct = null;
            this.pendingSpecs = [];
        }
    }

    /**
     * 填充产品基本信息
     * @param {Object} product - 产品对象
     */
    fillProductBasicInfo(product) {
        // 产品图片
        const imgElement = document.getElementById('configProductImage');
        if (imgElement) {
            imgElement.src = product.effective_image || product.image_path || '/static/images/no-image.png';
            imgElement.alt = product.product_name || '产品图片';
        }

        // 产品名称
        const nameElement = document.getElementById('configProductName');
        if (nameElement) {
            nameElement.textContent = product.product_name || '产品名称';
        }

        // 产品型号（显示在产品名称右侧）
        const modelElement = document.getElementById('configProductModel');
        if (modelElement) {
            modelElement.textContent = product.product_model || product.model || '未知';
        }

        // MN号（保持简洁，只显示MN徽章）
        const mnElement = document.getElementById('configProductMn');
        if (mnElement) {
            mnElement.innerHTML = `
                <span class="mn-badge confirmed">
                    <i class="fas fa-check-circle"></i> ${product.product_mn || '无'}
                </span>
            `;
        }

        // 品牌 + 价格
        const brandPriceElement = document.getElementById('configProductBrandPrice');
        if (brandPriceElement) {
            const brand = product.brand || '';
            const price = product.retail_price || product.market_price || 0;

            if (brand && price) {
                brandPriceElement.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="text-muted">${brand}</span>
                        <span class="fw-bold text-primary">${(document.getElementById('currencySymbol')?.textContent?.trim() || '¥')}${price ? parseFloat(price).toLocaleString() : price}</span>
                    </div>
                `;
            } else if (brand) {
                brandPriceElement.innerHTML = `<span class="text-muted">${brand}</span>`;
            } else if (price) {
                brandPriceElement.innerHTML = `<span class="fw-bold text-primary">${(document.getElementById('currencySymbol')?.textContent?.trim() || '¥')}${price ? parseFloat(price).toLocaleString() : price}</span>`;
            } else {
                brandPriceElement.innerHTML = '';
            }
        }

        // 规格说明
        const specElement = document.getElementById('configProductSpec');
        if (specElement) {
            specElement.textContent = product.specification || '';
        }
    }


    /**
     * 确认选择
     */
    confirmSelection() {
        if (!this.selectedProduct) {
            alert('未找到匹配的产品，请检查规格选择或稍后重试');
            return;
        }

        // 如果配置已确认展示，则执行最终添加
        if (this.configConfirmed) {
            this.executeFinalAddProduct();
            return;
        }

        // ⭐ 第一次确认：验证必选互斥组
        if (!this.validateRequiredMutualGroups()) {
            return;
        }

        // ⭐ 第一次确认：收集配置选择
        const configurations = this.collectConfigurations();
        this.selectedConfigurations = configurations;

        // 展示已选配置
        this.showSelectedConfigurations(configurations);

        // 切换视图：隐藏配置选择区域，显示已选配置区域
        const configArea = document.getElementById('productConfigArea');
        const selectedArea = document.getElementById('selectedConfigsArea');
        const backBtn = document.getElementById('backToConfigSelection');

        if (configArea) configArea.style.display = 'none';
        if (selectedArea) selectedArea.style.display = 'block';
        if (backBtn) backBtn.style.display = 'inline-block';

        // 标记配置已确认并更新步骤指示器
        this.configConfirmed = true;
        this.currentStep = 3;
        this.updateStepIndicator(3);

        // 显示编码规格（复用 renderFields 的数据）
        this.showCodeSpecsInConfirmation();

        console.log('📋 配置已确认，切换到展示模式');
    }

    /**
     * 在确认页面显示编码规格
     * 复用 Step 1 的固定字段数据，使用相同的两栏网格布局
     * 同时显示可配置规格（黑色斜体）
     */
    showCodeSpecsInConfirmation() {
        const container = document.getElementById('codeSpecsGrid');
        const wrapper = document.getElementById('configProductCodeSpecs');
        if (!container || !wrapper) return;

        container.innerHTML = '';

        // 使用已有的 fixedFields 数据（Step 1 已解析）
        if (this.fixedFields && this.fixedFields.length > 0) {
            this.fixedFields.forEach(field => {
                const fieldDiv = document.createElement('div');
                fieldDiv.className = 'spec-field-fixed';

                const unitText = field.fixedValue.unit ? ` ${field.fixedValue.unit}` : '';

                fieldDiv.innerHTML = `
                    <div class="spec-field-label">${field.fieldName}:</div>
                    <div class="spec-field-value">${field.fixedValue.value}${unitText}</div>
                `;

                container.appendChild(fieldDiv);
            });
        }

        // 添加可配置规格（黑色斜体）
        if (this.configurableSpecs && this.configurableSpecs.length > 0) {
            this.configurableSpecs.forEach(field => {
                const selectedValue = this.specConfig[field.field_name] || field.current_value;
                if (selectedValue) {
                    const fieldDiv = document.createElement('div');
                    fieldDiv.className = 'spec-field-fixed spec-field-configurable';
                    const unitText = field.field_unit || '';

                    fieldDiv.innerHTML = `
                        <div class="spec-field-label">${field.field_name}:</div>
                        <div class="spec-field-value">${selectedValue}${unitText}</div>
                    `;

                    container.appendChild(fieldDiv);
                }
            });
        }

        // 显示容器（只要有固定规格或可配置规格就显示）
        const hasSpecs = (this.fixedFields && this.fixedFields.length > 0) ||
                         (this.configurableSpecs && this.configurableSpecs.length > 0);
        wrapper.style.display = hasSpecs ? 'block' : 'none';

        console.log(`📋 编码规格已显示: 固定${this.fixedFields?.length || 0}个 + 可配置${this.configurableSpecs?.length || 0}个`);
    }

    /**
     * 展示已选配置
     * @param {Array} configurations - 配置列表
     */
    showSelectedConfigurations(configurations) {
        console.log('📋 [showSelectedConfigurations] 开始展示配置');
        console.log('  - 配置数量:', configurations.length);
        console.log('  - 配置数据:', configurations);

        const container = document.getElementById('selectedConfigsList');
        if (!container) return;

        container.innerHTML = '';

        if (configurations.length === 0) {
            // 隐藏整个已选配置区域
            const selectedArea = document.getElementById('selectedConfigsArea');
            if (selectedArea) selectedArea.style.display = 'none';
            return;
        }

        // 递归渲染配置（包含嵌套）
        configurations.forEach(config => {
            this.renderConfigWithNested(config, container, 0);
        });

        console.log(`📦 已展示配置完成`);
    }

    /**
     * 递归渲染配置项（包含嵌套配置）
     * @param {Object} config - 配置对象
     * @param {HTMLElement} container - 容器元素
     * @param {number} level - 嵌套层级
     */
    renderConfigWithNested(config, container, level = 0) {
        console.log(`%c${'  '.repeat(level)}📦 [Level ${level}] 渲染配置: ${config.product_name}`, 'color: #2196F3; font-weight: bold;');
        console.log(`${'  '.repeat(level)}   - 容器ID: ${container.id || '(无ID)'}`);
        console.log(`${'  '.repeat(level)}   - 容器类名: ${container.className}`);

        const item = document.createElement('div');
        item.className = 'config-item-simple';  // 所有层级统一使用 config-item-simple，缩进由父容器 sub-config-container 负责
        console.log(`${'  '.repeat(level)}   - 创建item, 类名: ${item.className}`);

        // 根据 relation_type 确定徽章类型（使用 i18nTexts 支持国际化）
        const badgeMap = {
            'required_accessory': { type: 'relation-type-required', text: window.i18nTexts?.required || '必选' },
            'recommended': { type: 'relation-type-recommended', text: window.i18nTexts?.recommended || '推荐' },
            'optional_accessory': { type: 'relation-type-optional-mutual', text: window.i18nTexts?.optionalMutual || '可选互斥' }
        };

        const badge = badgeMap[config.relation_type] || { type: '', text: '' };

        // 直接使用配置数据（已包含完整的产品信息）
        // 使用通用模板，传递数量和徽章参数
        const fragment = this.createConfigItemContent(config, {
            quantity: config.default_quantity || 1,
            badgeType: badge.type,
            badgeText: badge.text
        });

        item.appendChild(fragment);
        console.log(`${'  '.repeat(level)}   ✅ fragment已添加到item`);

        // ⭐ 递归渲染子配置（使用父子结构，与选择页面一致）
        if (config.nested_configs && config.nested_configs.length > 0) {
            console.log(`%c${'  '.repeat(level)}   📦 发现 ${config.nested_configs.length} 个子配置，创建嵌套容器`, 'color: #FF9800; font-weight: bold;');

            // 创建子配置容器作为item的子元素（与选择页面相同）
            const nestedContainer = document.createElement('div');
            nestedContainer.className = `sub-config-container level-${level}`;
            console.log(`${'  '.repeat(level)}   - 创建嵌套容器，类名: ${nestedContainer.className}`);

            // 递归渲染子配置到嵌套容器中
            config.nested_configs.forEach((nestedConfig, idx) => {
                console.log(`${'  '.repeat(level)}   - 递归渲染子配置 ${idx + 1}/${config.nested_configs.length}`);
                this.renderConfigWithNested(nestedConfig, nestedContainer, level + 1);
            });

            // 将嵌套容器添加到item作为子元素
            item.appendChild(nestedContainer);
            console.log(`%c${'  '.repeat(level)}   ✅ 嵌套容器已添加到item (父子结构)`, 'color: #4CAF50; font-weight: bold;');
        } else {
            console.log(`${'  '.repeat(level)}   ℹ️ 无子配置`);
        }

        // 将item添加到父容器
        container.appendChild(item);
        console.log(`${'  '.repeat(level)}   ✅ item已添加到container (container.children: ${container.children.length})`)

        console.log('');  // 空行分隔
    }

    /**
     * 返回上一步（根据当前步骤逐级返回）
     */
    backToConfigSelection() {
        const codeFieldsContainer = document.getElementById('codeFieldsContainer');
        const configArea = document.getElementById('productConfigArea');
        const selectedArea = document.getElementById('selectedConfigsArea');
        const backBtn = document.getElementById('backToConfigSelection');

        if (this.currentStep === 3) {
            // 从配置确认返回
            if (this.step2Skipped) {
                // 步骤2被跳过（无配置），直接返回步骤1
                this.step2Skipped = false;  // 重置标记
                this.configConfirmed = false;
                this.selectedConfigurations = [];

                if (codeFieldsContainer) codeFieldsContainer.style.display = '';
                if (selectedArea) selectedArea.style.display = 'none';
                if (backBtn) backBtn.style.display = 'none';
                if (configArea) configArea.style.display = 'none';

                // 🆕 隐藏编码规格显示区域（步骤1不需要显示）
                const codeSpecsWrapper = document.getElementById('configProductCodeSpecs');
                if (codeSpecsWrapper) codeSpecsWrapper.style.display = 'none';

                // 🆕 隐藏产品规格详情区域（步骤1应该只显示选择界面，不显示规格详情）
                const specsArea = document.getElementById('productSpecsArea');
                if (specsArea) specsArea.style.display = 'none';

                const codeSelectionTitle = document.getElementById('codeSelectionTitle');
                if (codeSelectionTitle) codeSelectionTitle.style.display = '';

                this.showSpecConfirmButton();

                if (codeFieldsContainer) {
                    codeFieldsContainer.querySelectorAll('input[type="radio"]').forEach(radio => {
                        radio.disabled = false;
                    });
                    codeFieldsContainer.querySelectorAll('.spec-field-selectable').forEach(fieldDiv => {
                        fieldDiv.classList.remove('auto-selected');
                    });
                }

                this.currentStep = 1;
                this.updateStepIndicator(1);
                console.log('🔙 步骤2被跳过，直接返回规格选择界面');
            } else {
                // 正常返回步骤2
                if (configArea) configArea.style.display = 'block';
                if (selectedArea) selectedArea.style.display = 'none';
                this.configConfirmed = false;
                this.selectedConfigurations = [];
                this.currentStep = 2;
                this.updateStepIndicator(2);
                console.log('🔙 返回到配置选择界面');
            }
        } else if (this.currentStep === 2) {
            // 从配置选择返回到规格选择
            if (codeFieldsContainer) codeFieldsContainer.style.display = '';
            if (selectedArea) selectedArea.style.display = 'none';
            if (backBtn) backBtn.style.display = 'none';

            // 隐藏配置区域（步骤1不显示）
            if (configArea) configArea.style.display = 'none';

            // 🆕 隐藏编码规格显示区域（步骤1不需要显示）
            const codeSpecsWrapper = document.getElementById('configProductCodeSpecs');
            if (codeSpecsWrapper) codeSpecsWrapper.style.display = 'none';

            // 🆕 隐藏产品规格详情区域（步骤1应该只显示选择界面，不显示规格详情）
            const specsArea = document.getElementById('productSpecsArea');
            if (specsArea) specsArea.style.display = 'none';

            // 恢复规格选择标题（返回步骤1时需要显示）
            const codeSelectionTitle = document.getElementById('codeSelectionTitle');
            if (codeSelectionTitle) codeSelectionTitle.style.display = '';

            // ⭐ 重置确认按钮为步骤1的行为
            this.showSpecConfirmButton();

            // ⭐ 重新启用所有规格选择radio按钮
            if (codeFieldsContainer) {
                codeFieldsContainer.querySelectorAll('input[type="radio"]').forEach(radio => {
                    radio.disabled = false;
                });
                codeFieldsContainer.querySelectorAll('.spec-field-selectable').forEach(fieldDiv => {
                    fieldDiv.classList.remove('auto-selected');
                });
            }

            this.currentStep = 1;
            this.updateStepIndicator(1);
            console.log('🔙 返回到规格选择界面');
        }
    }

    /**
     * 执行最终添加产品
     */
    executeFinalAddProduct() {
        // 检查是否有待定规格（未选择的规格使用了默认值）
        if (this.pendingSpecs && this.pendingSpecs.length > 0) {
            // 显示确认对话框
            showConfirmDialog({
                type: 'warning',
                title: '确认产品配置',
                message: `当前产品配置中有 ${this.pendingSpecs.length} 个规格未选择，系统将使用推荐的默认选项。\n\n在下单时，这个产品的最终规格还需要再次确认。\n\n是否继续添加此产品？`,
                confirmText: '确认添加',
                cancelText: '返回修改',
                onConfirm: () => {
                    // 用户确认后执行添加
                    this.executeAddProduct(this.selectedConfigurations);
                }
                // onCancel 无需处理，用户可以继续选择规格
            });
        } else {
            // 没有待定规格，直接添加
            this.executeAddProduct(this.selectedConfigurations);
        }
    }

    /**
     * 执行添加产品（内部方法）
     * @param {Array} configurations - 配置列表
     */
    executeAddProduct(configurations = []) {
        // ⭐ 获取动态规格配置数据
        const dynamicSpecConfig = this.getDynamicSpecConfigData();

        // ⭐ 计算可配置字段的价格增量（步骤1的规格选择）
        this.calculateConfigurablePriceAdjustment();

        // ⭐ 修改：准备产品数据，包含配置信息和动态规格配置
        const productData = {
            mainProduct: {
                ...this.selectedProduct,
                pending_specs: this.pendingSpecs || []  // 传递待定规格数据
            },
            configurations: configurations,  // 配置列表
            dynamicSpecConfig: dynamicSpecConfig,  // 动态规格配置（步骤2）
            // ⭐ 新增：可配置字段价格增量（步骤1）
            configurableSpecConfig: {
                price_adjustment_total: this.configurablePriceAdjustment || 0,
                price_details: this.configurablePriceDetails || [],
                configurable_selections: this.configurableSelections || {},
                spec_mn: this.generateSpecMn(),  // 生成的规格MN
                // ⭐ 传递更新后的描述（配置确认页面显示的描述）
                configured_description: document.getElementById('configProductSpec')?.textContent?.trim() || ''
            }
        };

        // 日志输出
        if (this.pendingSpecs && this.pendingSpecs.length > 0) {
            console.log('📋 产品包含待定规格:', this.pendingSpecs);
        }

        if (configurations.length > 0) {
            console.log(`📦 产品包含 ${configurations.length} 个配置:`, configurations);
        }

        // 输出动态规格配置日志
        if (dynamicSpecConfig) {
            console.log('🔧 产品包含动态规格配置:', dynamicSpecConfig);
        }

        // ⭐ 输出可配置字段价格增量
        if (this.configurablePriceAdjustment && this.configurablePriceAdjustment !== 0) {
            console.log(`💰 可配置字段价格增量: ¥${(this.configurablePriceAdjustment / 100).toFixed(2)}`);
            console.log('  - 明细:', this.configurablePriceDetails);
        }

        // 添加产品
        if (this.productSelector && this.productSelector.config.onSelect) {
            this.productSelector.config.onSelect(
                productData,
                this.productSelector.currentInput
            );
        }

        // 使用自定义对话框API关闭
        closeCustomDialog(this.modalId);

        // 重置状态会在关闭事件中自动执行
    }

    /**
     * 显示错误信息
     * @param {string} message - 错误消息
     */
    showError(message) {
        const container = document.getElementById('codeSelectionArea');
        if (container) {
            container.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    ${message}
                </div>
            `;
        }
    }

    // ============================================================================
    // 产品配置功能
    // ============================================================================

    /**
     * 加载产品配置
     * @param {number} productId - 产品ID
     */
    async loadProductConfigurations(productId) {
        console.log(`🔧 加载产品配置: product_id=${productId}`);

        // 显示加载状态
        const configArea = document.getElementById('productConfigArea');
        const loadingSpinner = document.getElementById('configLoadingSpinner');
        const noConfigMessage = document.getElementById('noConfigMessage');

        if (configArea) configArea.style.display = 'block';
        if (loadingSpinner) loadingSpinner.style.display = 'block';
        if (noConfigMessage) noConfigMessage.style.display = 'none';

        // 隐藏所有配置区域
        this.hideAllConfigAreas();

        // 同时加载可配置规格（动态规格配置功能）
        this.loadConfigurableSpecs(productId);

        try {
            const response = await fetch(`/product-management/api/product/${productId}/relations`);
            const result = await response.json();

            if (loadingSpinner) loadingSpinner.style.display = 'none';

            if (result.success && (result.data.length > 0 || Object.keys(result.groups || {}).length > 0)) {
                console.log(`  ✓ 配置加载成功: ${result.total} 个配置`);
                this.renderConfigurations(result);
            } else {
                console.log('  ℹ️ 该产品无配置选项，直接进入确认步骤');
                // 隐藏配置区域
                if (configArea) configArea.style.display = 'none';

                // ⭐ 设置空配置并跳转到步骤3
                this.selectedConfigurations = [];
                this.configConfirmed = true;
                this.step2Skipped = true;  // 标记跳过了步骤2

                // 隐藏已选配置区域（无配置时不显示）
                const selectedArea = document.getElementById('selectedConfigsArea');
                if (selectedArea) selectedArea.style.display = 'none';

                // 更新按钮为最终确认
                const confirmBtn = document.getElementById('confirmProductSelection');
                if (confirmBtn) {
                    confirmBtn.innerHTML = '<i class="fas fa-check"></i> 确认产品';
                    confirmBtn.onclick = () => this.executeFinalAddProduct();
                }

                // 显示返回按钮
                const backBtn = document.getElementById('backToConfigSelection');
                if (backBtn) backBtn.style.display = 'inline-block';

                this.currentStep = 3;
                this.updateStepIndicator(3);

                // 显示编码规格
                this.showCodeSpecsInConfirmation();
            }
        } catch (error) {
            console.error('❌ 加载配置失败:', error);
            if (loadingSpinner) loadingSpinner.style.display = 'none';
            if (noConfigMessage) {
                noConfigMessage.innerHTML = '<i class="fas fa-exclamation-triangle text-danger"></i> 加载配置失败';
                noConfigMessage.style.display = 'block';
            }
        }
    }

    /**
     * 隐藏所有配置区域
     */
    hideAllConfigAreas() {
        const areas = [
            'requiredConfigArea',
            'requiredMutualConfigArea',
            'recommendedConfigArea',
            'optionalMutualConfigArea'
        ];
        areas.forEach(id => {
            const elem = document.getElementById(id);
            if (elem) elem.style.display = 'none';
        });
    }

    /**
     * 渲染配置UI
     * @param {Object} data - API返回的配置数据
     */
    renderConfigurations(data) {
        console.log('🎨 渲染配置UI');

        // 分类处理配置数据
        const required = [];
        const requiredMutualGroups = {};
        const recommended = [];
        const optionalMutualGroups = {};

        // 处理普通关联产品
        if (data.data && Array.isArray(data.data)) {
            data.data.forEach(item => {
                if (item.relation_type === 'required_accessory') {
                    required.push(item);
                } else if (item.relation_type === 'recommended') {
                    recommended.push(item);
                }
            });
        }

        // 处理互斥组
        if (data.groups && typeof data.groups === 'object') {
            Object.values(data.groups).forEach(group => {
                if (group.is_required) {
                    requiredMutualGroups[group.group_id] = group;
                } else {
                    optionalMutualGroups[group.group_id] = group;
                }
            });
        }

        // 渲染各个区域
        if (required.length > 0) {
            this.renderRequiredConfigs(required);
        }

        if (Object.keys(requiredMutualGroups).length > 0) {
            this.renderRequiredMutualGroups(requiredMutualGroups);
        }

        if (recommended.length > 0) {
            this.renderRecommendedConfigs(recommended);
        }

        if (Object.keys(optionalMutualGroups).length > 0) {
            this.renderOptionalMutualGroups(optionalMutualGroups);
        }

        // ⭐ 新增：如果只有必选配置（无可选、无推荐、无需选择的互斥组），自动选择并跳过选择界面
        const hasOnlyRequired =
            required.length > 0 &&  // 有必选配置
            recommended.length === 0 &&  // 无推荐配置
            Object.keys(optionalMutualGroups).length === 0 &&  // 无可选互斥组
            Object.keys(requiredMutualGroups).length === 0;  // 无必选互斥组（无需选择）

        if (hasOnlyRequired) {
            console.log('  ✓ 检测到只有必选配置，自动选择并跳转到已选配置界面');

            // 自动选择所有必选配置
            this.selectedConfigurations = required.map(config => ({
                ...config,
                quantity: config.default_quantity || 1,
                source: 'required'
            }));

            // 直接显示已选配置界面
            this.showSelectedConfigurations(this.selectedConfigurations);

            // 切换视图：隐藏配置选择区域，显示已选配置区域
            const configArea = document.getElementById('productConfigArea');
            const selectedArea = document.getElementById('selectedConfigsArea');
            const backBtn = document.getElementById('backToConfigSelection');

            if (configArea) configArea.style.display = 'none';
            if (selectedArea) selectedArea.style.display = 'block';
            if (backBtn) backBtn.style.display = 'inline-block';

            // 标记配置已确认
            this.configConfirmed = true;
        }
    }

    /**
     * 创建配置项DOM元素（通用模板 - 新版简化布局）
     * @param {Object} config - 配置对象
     * @param {Object} options - 选项 {badgeType: string, badgeText: string, quantity: number}
     * @returns {DocumentFragment} 配置项内容片段
     */
    createConfigItemContent(config, options = {}) {
        console.log('🎨 [createConfigItemContent] 创建配置项内容');
        console.log('  - config对象:', config);
        console.log('  - options:', options);

        const fragment = document.createDocumentFragment();
        const price = config.retail_price || 0;
        console.log('  - 使用的价格:', price);

        // 配置类型徽章
        let typeBadge = '';
        if (options.badgeType && options.badgeText) {
            typeBadge = `<span class="badge relation-type-badge ${options.badgeType} rounded-pill ms-2">${options.badgeText}</span>`;
        }

        // 第一行：产品名称 + 徽章 (+ 价格，如果有数量参数)
        const row1 = document.createElement('div');
        if (options.quantity) {
            // 已选配置模式：名称+徽章（左），价格（右）
            row1.className = 'd-flex justify-content-between align-items-center';
            row1.style.paddingRight = '1rem';

            const nameDiv = document.createElement('div');
            nameDiv.className = 'config-product-name';
            nameDiv.innerHTML = `${config.product_name || '-'}${typeBadge}`;

            const priceDiv = document.createElement('div');
            priceDiv.className = 'config-price';
            priceDiv.style.whiteSpace = 'nowrap';
            priceDiv.textContent = `${(document.getElementById('currencySymbol')?.textContent?.trim() || '¥')}${price.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

            row1.appendChild(nameDiv);
            row1.appendChild(priceDiv);
        } else {
            // 正常配置选择模式：名称+徽章
            row1.className = 'config-product-name';
            row1.innerHTML = `${config.product_name || '-'}${typeBadge}`;
        }

        // 第二行：型号 + MN（左），价格或数量（右）
        const row2 = document.createElement('div');
        row2.className = 'd-flex justify-content-between align-items-center';
        row2.style.marginTop = '0.25rem';
        row2.style.paddingRight = '1rem';

        const modelMn = `${config.product_model || '-'}  ${config.product_mn || '-'}`;
        console.log('  - 型号:', config.product_model);
        console.log('  - MN:', config.product_mn);
        console.log('  - 拼接后:', modelMn);

        // 左侧：型号+MN
        const leftSpan = document.createElement('span');
        leftSpan.className = 'text-muted';
        leftSpan.style.fontSize = '0.9rem';
        leftSpan.textContent = modelMn;
        console.log('  - 设置左侧文本:', modelMn);

        // 右侧：数量（已选配置）或 价格（正常选择）
        const rightSpan = document.createElement('span');
        rightSpan.style.whiteSpace = 'nowrap';

        if (options.quantity) {
            // 已选配置模式：显示数量
            rightSpan.className = 'text-muted';
            rightSpan.style.fontSize = '0.9rem';
            rightSpan.textContent = `数量: ${options.quantity}`;
        } else {
            // 正常配置选择模式：显示价格
            rightSpan.className = 'config-price';
            rightSpan.textContent = `${(document.getElementById('currencySymbol')?.textContent?.trim() || '¥')}${price.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }

        row2.appendChild(leftSpan);
        row2.appendChild(rightSpan);

        // 第三行：规格说明（支持差异高亮）
        const row3 = document.createElement('div');
        row3.className = 'text-muted';
        row3.style.fontSize = '0.9rem';
        row3.style.marginTop = '0.25rem';

        // 如果有差异keys且SpecAnalyzer可用，使用高亮显示
        const specText = config.specification || config.product_desc || '-';
        if (options.diffKeys && options.diffKeys.size > 0 && window.SpecAnalyzer) {
            row3.innerHTML = window.SpecAnalyzer.highlightSpecString(specText, options.diffKeys);
        } else {
            row3.textContent = specText;
        }
        console.log('  - 规格说明:', config.specification);
        console.log('  - 第三行文本:', row3.textContent);

        fragment.appendChild(row1);
        fragment.appendChild(row2);
        fragment.appendChild(row3);

        console.log('✅ [createConfigItemContent] 配置项内容创建完成');
        return fragment;
    }

    /**
     * 渲染必选配置
     * @param {Array} configs - 必选配置列表
     */
    renderRequiredConfigs(configs, options = {}) {
        const containerId = options.containerId || 'requiredConfigList';
        const level = options.level || 0;
        const parentId = options.parentId || null;

        console.log(`  📌 渲染必选配置: ${configs.length} 个 (层级: ${level})`);

        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = '';

        configs.forEach((config, idx) => {
            const item = document.createElement('div');
            item.className = 'config-item-simple';
            item.dataset.productId = config.related_product_id;
            item.dataset.productName = config.product_name;
            item.dataset.productMn = config.product_mn;
            item.dataset.quantity = config.default_quantity || 1;
            item.dataset.configType = 'required';
            item.dataset.relationType = 'required_accessory';

            // 存储完整的产品数据（JSON字符串）
            item.dataset.productData = JSON.stringify(config);

            // 使用通用模板，传递必选徽章（使用 i18nTexts 支持国际化）
            item.appendChild(this.createConfigItemContent(config, {
                badgeType: 'relation-type-required',
                badgeText: window.i18nTexts?.required || '必选'
            }));

            // ⭐ 新增：如果有子配置且未超过最大层级，添加展开按钮和子配置容器
            if (config.has_nested_configs && level < 1) {
                console.log(`  🔧 为产品 ${config.related_product_id} 添加展开按钮 (层级: ${level})`);
                const contentWrapper = item.querySelector('.config-item-content') || item.firstChild;
                if (contentWrapper) {
                    // 添加展开按钮
                    const toggleBtn = document.createElement('button');
                    toggleBtn.className = 'btn btn-sm btn-link toggle-nested-btn';
                    toggleBtn.type = 'button';
                    toggleBtn.innerHTML = `<i class="fas fa-chevron-right" id="toggle-icon-${config.related_product_id}"></i>`;
                    toggleBtn.onclick = () => {
                        console.log('🖱️ 展开按钮被点击 - related_product_id:', config.related_product_id, 'level:', level);
                        this.toggleNestedConfig(config.related_product_id, level);
                    };
                    contentWrapper.appendChild(toggleBtn);
                    console.log(`  ✅ 展开按钮已添加到内容包装器`);


                    // 添加"已配置"徽章占位
                    const badge = document.createElement('span');
                    badge.id = `configured-badge-${config.related_product_id}`;
                    badge.className = 'badge bg-success ms-2';
                    badge.textContent = '已配置';
                    badge.style.display = 'none';
                    contentWrapper.appendChild(badge);
                }

                // 添加子配置容器
                const nestedContainer = this.createNestedConfigContainer(config, level);
                console.log(`  📦 创建嵌套容器ID: ${nestedContainer.id}`);
                item.appendChild(nestedContainer);
            }

            container.appendChild(item);
        });

        // 只在第一层显示area
        if (level === 0) {
            const area = document.getElementById('requiredConfigArea');
            if (area) area.style.display = 'block';
        }
    }

    /**
     * 渲染必选互斥组
     * @param {Object} groups - 必选互斥组对象
     */
    renderRequiredMutualGroups(groups, options = {}) {
        const containerId = options.containerId || 'requiredMutualConfigList';
        const level = options.level || 0;
        const parentId = options.parentId || null;

        console.log(`  ⚠️ 渲染必选互斥组: ${Object.keys(groups).length} 组 (层级: ${level})`);

        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = '';

        Object.values(groups).forEach(group => {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'mutual-group';
            groupDiv.dataset.groupId = group.group_id;
            groupDiv.dataset.isRequired = 'true';
            groupDiv.dataset.groupRequired = 'true';
            groupDiv.dataset.groupName = group.group_name || `必选互斥组 ${group.group_id}`;

            const groupTitle = document.createElement('div');
            groupTitle.className = 'group-title';
            groupTitle.textContent = group.group_name || `必选互斥组 ${group.group_id}`;
            groupDiv.appendChild(groupTitle);

            // ⭐ 修复：先确定应该默认选中的那一个产品
            const defaultProduct = group.products.find(p => p.is_default) || group.products[0];
            const defaultProductId = defaultProduct ? defaultProduct.related_product_id : null;
            console.log(`  🎯 [必选互斥] 组 ${group.group_id} 的默认选中产品ID: ${defaultProductId}`);

            // ⭐ 计算同名产品的规格差异（用于高亮显示）
            const diffKeys = window.SpecAnalyzer ? window.SpecAnalyzer.findDiffKeys(group.products) : new Set();
            if (diffKeys.size > 0) {
                console.log(`  🔍 [必选互斥] 组 ${group.group_id} 发现规格差异:`, [...diffKeys]);
            }

            group.products.forEach((product, index) => {
                const price = product.retail_product || 0;

                // 使用简化的选项样式
                const optionDiv = document.createElement('div');
                optionDiv.className = 'form-check config-option-simple';

                const radio = document.createElement('input');
                radio.type = 'radio';
                radio.className = 'form-check-input';
                radio.name = `required-mutual-${group.group_id}`;
                radio.id = `config-rm-${group.group_id}-${product.related_product_id}`;
                radio.value = product.related_product_id;
                radio.dataset.productId = product.related_product_id;
                radio.dataset.productName = product.product_name;
                radio.dataset.productMn = product.product_mn;
                radio.dataset.quantity = product.default_quantity || 1;
                radio.dataset.configType = 'required_mutual';
                radio.dataset.groupId = group.group_id;
                radio.dataset.required = 'true';

                // 存储完整的产品数据（JSON字符串）
                radio.dataset.productData = JSON.stringify(product);

                // ⭐ 修复：只为应该默认选中的那一个产品设置 checked
                if (product.related_product_id === defaultProductId) {
                    radio.checked = true;
                    console.log(`  ✅ [必选互斥] 设置产品 ${product.related_product_id} 为默认选中`);
                }

                const label = document.createElement('label');
                label.className = 'form-check-label';
                label.setAttribute('for', radio.id);

                // 使用通用模板（显示必选互斥徽章，传递差异keys用于高亮）
                label.appendChild(this.createConfigItemContent(product, {
                    badgeType: 'relation-type-required-mutual',
                    badgeText: '必选互斥',
                    diffKeys: diffKeys
                }));

                optionDiv.appendChild(radio);
                optionDiv.appendChild(label);

                // ⭐ 新增：如果有子配置且未超过最大层级，添加子配置容器和监听
                if (product.has_nested_configs && level < 1) {
                    console.log(`  🔧 [必选互斥] 为产品 ${product.related_product_id} 添加嵌套配置 (层级: ${level})`);

                    // 添加"已配置"徽章占位
                    const badge = document.createElement('span');
                    badge.id = `configured-badge-${product.related_product_id}`;
                    badge.className = 'badge bg-success ms-2';
                    badge.textContent = '已配置';
                    badge.style.display = 'none';
                    label.appendChild(badge);

                    // 添加子配置容器
                    const nestedContainer = this.createNestedConfigContainer(product, level);
                    console.log(`  📦 [必选互斥] 创建嵌套容器ID: ${nestedContainer.id}`);
                    optionDiv.appendChild(nestedContainer);

                    // ⭐ 监听radio选中状态变化
                    radio.addEventListener('change', (e) => {
                        console.log(`📻 [必选互斥] Radio状态变化 - 产品ID: ${product.related_product_id}, 选中: ${e.target.checked}`);

                        if (e.target.checked) {
                            // 选中时自动展开
                            this.autoExpandNestedConfig(product.related_product_id, level);
                        }
                    });

                    // 监听同组其他radio的change事件，取消选中时收起
                    const groupName = `required-mutual-${group.group_id}`;
                    document.addEventListener('change', (e) => {
                        if (e.target.name === groupName && e.target.value != product.related_product_id) {
                            // 同组其他选项被选中，收起当前产品的嵌套配置
                            console.log(`📻 [必选互斥] 其他选项被选中，收起产品 ${product.related_product_id} 的嵌套配置`);
                            this.collapseNestedConfig(product.related_product_id, level);
                        }
                    });

                    // 如果当前是默认选中，自动展开
                    if (radio.checked) {
                        console.log(`  ✅ [必选互斥] 产品 ${product.related_product_id} 是默认选中，将自动展开`);
                        // 延迟展开，确保DOM已完全渲染
                        setTimeout(() => {
                            this.autoExpandNestedConfig(product.related_product_id, level);
                        }, 100);
                    }
                }

                groupDiv.appendChild(optionDiv);
            });

            container.appendChild(groupDiv);
        });

        // 只在第一层显示area
        if (level === 0) {
            const area = document.getElementById('requiredMutualConfigArea');
            if (area) area.style.display = 'block';
        }
    }

    /**
     * 渲染推荐配置
     * @param {Array} configs - 推荐配置列表
     */
    renderRecommendedConfigs(configs, options = {}) {
        const containerId = options.containerId || 'recommendedConfigList';
        const level = options.level || 0;
        const parentId = options.parentId || null;

        console.log(`  ✨ 渲染推荐配置: ${configs.length} 个 (层级: ${level})`);

        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = '';

        // 只在第一层（level 0）创建分组容器，嵌套层级直接使用容器
        let targetContainer;
        if (level === 0) {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'mutual-group';
            container.appendChild(groupDiv);
            targetContainer = groupDiv;
        } else {
            targetContainer = container;
        }

        // ⭐ 计算同名产品的规格差异（按产品名称分组）
        const diffMap = window.SpecAnalyzer ? window.SpecAnalyzer.calculateDiffMap(configs) : new Map();
        if (diffMap.size > 0) {
            console.log(`  🔍 [推荐配置] 发现 ${diffMap.size} 个产品有规格差异`);
        }

        configs.forEach((config, idx) => {
            const optionDiv = document.createElement('div');
            optionDiv.className = 'form-check config-option-simple';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'form-check-input';
            checkbox.id = `config-rec-${config.related_product_id}-${level}`;
            checkbox.value = config.related_product_id;
            checkbox.dataset.productId = config.related_product_id;
            checkbox.dataset.quantity = config.default_quantity || 1;
            checkbox.dataset.configType = 'recommended';

            // 存储完整的产品数据（JSON字符串）
            // API 返回的数据是扁平结构
            checkbox.dataset.productData = JSON.stringify(config);

            const label = document.createElement('label');
            label.className = 'form-check-label';
            label.setAttribute('for', checkbox.id);

            // 使用通用模板，传递推荐徽章（使用 i18nTexts 支持国际化）
            // API 返回的 config 对象已经包含所有产品字段
            // 获取该配置的差异keys（基于product id）
            const configId = config.id || config.related_product_id;
            const diffKeys = diffMap.get(configId) || new Set();
            label.appendChild(this.createConfigItemContent(config, {
                badgeType: 'relation-type-recommended',
                badgeText: window.i18nTexts?.recommended || '推荐',
                diffKeys: diffKeys
            }));

            // 子配置容器变量（确保每次迭代重置）
            let nestedContainer = null;

            // ⭐ 新增：如果有子配置且为顶层配置（level 0），添加展开按钮和子配置容器
            if (config.has_nested_configs && level === 0) {
                console.log(`  🔧 为推荐配置产品 ${config.related_product_id} 添加展开按钮 (层级: ${level})`);

                // 添加展开按钮
                const toggleBtn = document.createElement('button');
                toggleBtn.className = 'btn btn-sm btn-link toggle-nested-btn';
                toggleBtn.type = 'button';
                toggleBtn.innerHTML = `<i class="fas fa-chevron-right" id="toggle-icon-${config.related_product_id}"></i>`;
                toggleBtn.onclick = () => {
                    console.log('🖱️ 推荐配置展开按钮被点击 - related_product_id:', config.related_product_id, 'level:', level);
                    this.toggleNestedConfig(config.related_product_id, level);
                };
                label.appendChild(toggleBtn);

                // 添加"已配置"徽章占位
                const badge = document.createElement('span');
                badge.id = `configured-badge-${config.related_product_id}`;
                badge.className = 'badge bg-success ms-2';
                badge.textContent = '已配置';
                badge.style.display = 'none';
                label.appendChild(badge);

                // 创建子配置容器（稍后添加到checkbox和label之后）
                nestedContainer = this.createNestedConfigContainer(config, level);
                console.log(`  📦 创建嵌套容器ID: ${nestedContainer.id}`);

                // ⭐ 监听checkbox选中状态变化
                checkbox.addEventListener('change', (e) => {
                    console.log(`☑️ [推荐配置] Checkbox状态变化 - 产品ID: ${config.related_product_id}, 选中: ${e.target.checked}`);
                    if (e.target.checked) {
                        // 选中时自动展开
                        this.autoExpandNestedConfig(config.related_product_id, level);
                    } else {
                        // 取消选中时折叠
                        this.collapseNestedConfig(config.related_product_id, level);
                    }
                });
            }

            optionDiv.appendChild(checkbox);
            optionDiv.appendChild(label);
            // 子配置容器放在checkbox和label之后（显示在下方）
            if (nestedContainer) {
                optionDiv.appendChild(nestedContainer);
            }
            targetContainer.appendChild(optionDiv);
        });

        // 只在第一层显示area
        if (level === 0) {
            const area = document.getElementById('recommendedConfigArea');
            if (area) area.style.display = 'block';
        }
    }

    /**
     * 渲染推荐互斥组（可选互斥）
     * @param {Object} groups - 推荐互斥组对象
     */
    renderOptionalMutualGroups(groups, options = {}) {
        const containerId = options.containerId || 'optionalMutualConfigList';
        const level = options.level || 0;
        const parentId = options.parentId || null;

        console.log(`  💡 渲染可选互斥组: ${Object.keys(groups).length} 组 (层级: ${level})`);

        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = '';

        Object.values(groups).forEach(group => {
            // 只在第一层（level 0）创建组容器和标题，嵌套层级直接使用容器
            let targetContainer;
            if (level === 0) {
                const groupDiv = document.createElement('div');
                groupDiv.className = 'mutual-group';
                groupDiv.dataset.groupId = group.group_id;
                groupDiv.dataset.isRequired = 'false';

                const groupTitle = document.createElement('div');
                groupTitle.className = 'group-title';
                groupTitle.textContent = group.group_name || `可选互斥组 ${group.group_id}`;
                groupDiv.appendChild(groupTitle);

                container.appendChild(groupDiv);
                targetContainer = groupDiv;
            } else {
                targetContainer = container;
            }

            // ⭐ 计算同名产品的规格差异（用于高亮显示）
            const diffKeys = window.SpecAnalyzer ? window.SpecAnalyzer.findDiffKeys(group.products) : new Set();
            if (diffKeys.size > 0) {
                console.log(`  🔍 [可选互斥] 组 ${group.group_id} 发现规格差异:`, [...diffKeys]);
            }

            // 添加具体选项（移除"不选择"选项）
            group.products.forEach((product, index) => {
                const price = product.retail_price || 0;

                const optionDiv = document.createElement('div');
                optionDiv.className = 'form-check config-option-simple';

                const radio = document.createElement('input');
                radio.type = 'radio';
                radio.className = 'form-check-input';
                radio.name = `optional-mutual-${group.group_id}-${level}`;
                radio.id = `config-om-${group.group_id}-${product.related_product_id}-${level}`;
                radio.value = product.related_product_id;
                radio.dataset.productId = product.related_product_id;
                radio.dataset.quantity = product.default_quantity || 1;
                radio.dataset.configType = 'optional_mutual';
                radio.dataset.groupId = group.group_id;

                // 存储完整的产品数据（JSON字符串）
                // API 返回的数据是扁平结构
                radio.dataset.productData = JSON.stringify(product);

                // 如果有默认选项或第一个选项，选中它
                if (product.is_default || index === 0) {
                    radio.checked = true;
                }

                const label = document.createElement('label');
                label.className = 'form-check-label';
                label.setAttribute('for', radio.id);

                // 使用通用模板（显示可选互斥徽章，传递差异keys用于高亮）
                // API 返回的 product 对象已经包含所有产品字段
                label.appendChild(this.createConfigItemContent(product, {
                    badgeType: 'relation-type-optional-mutual',
                    badgeText: '可选互斥',
                    diffKeys: diffKeys
                }));

                // 子配置容器变量（确保每次迭代重置）
                let nestedContainer = null;

                // ⭐ 新增：如果有子配置且为顶层配置（level 0），添加展开按钮和子配置容器
                if (product.has_nested_configs && level === 0) {
                    console.log(`  🔧 为可选互斥产品 ${product.related_product_id} 添加展开按钮 (层级: ${level})`);

                    // 添加展开按钮
                    const toggleBtn = document.createElement('button');
                    toggleBtn.className = 'btn btn-sm btn-link toggle-nested-btn';
                    toggleBtn.type = 'button';
                    toggleBtn.innerHTML = `<i class="fas fa-chevron-right" id="toggle-icon-${product.related_product_id}"></i>`;
                    toggleBtn.onclick = () => {
                        console.log('🖱️ 可选互斥展开按钮被点击 - related_product_id:', product.related_product_id, 'level:', level);
                        this.toggleNestedConfig(product.related_product_id, level);
                    };
                    label.appendChild(toggleBtn);

                    // 添加"已配置"徽章占位
                    const badge = document.createElement('span');
                    badge.id = `configured-badge-${product.related_product_id}`;
                    badge.className = 'badge bg-success ms-2';
                    badge.textContent = '已配置';
                    badge.style.display = 'none';
                    label.appendChild(badge);

                    // 创建子配置容器（稍后添加到radio和label之后）
                    nestedContainer = this.createNestedConfigContainer(product, level);
                    console.log(`  📦 创建嵌套容器ID: ${nestedContainer.id}`);

                    // ⭐ 监听radio选中状态变化
                    radio.addEventListener('change', (e) => {
                        console.log(`📻 [可选互斥] Radio状态变化 - 产品ID: ${product.related_product_id}, 选中: ${e.target.checked}`);
                        if (e.target.checked) {
                            // 选中时自动展开
                            this.autoExpandNestedConfig(product.related_product_id, level);
                        }
                    });

                    // 监听同组其他radio的change事件，取消选中时收起
                    const groupName = `optional-mutual-${group.group_id}-${level}`;
                    document.addEventListener('change', (e) => {
                        if (e.target.name === groupName && e.target.value != product.related_product_id) {
                            // 同组其他选项被选中，收起当前产品的嵌套配置
                            console.log(`📻 [可选互斥] 其他选项被选中，收起产品 ${product.related_product_id} 的嵌套配置`);
                            this.collapseNestedConfig(product.related_product_id, level);
                        }
                    });

                    // 如果当前是默认选中，自动展开
                    if (radio.checked) {
                        console.log(`  ✅ [可选互斥] 产品 ${product.related_product_id} 是默认选中，将自动展开`);
                        setTimeout(() => {
                            this.autoExpandNestedConfig(product.related_product_id, level);
                        }, 100);
                    }
                }

                optionDiv.appendChild(radio);
                optionDiv.appendChild(label);
                // 子配置容器放在radio和label之后（显示在下方）
                if (nestedContainer) {
                    optionDiv.appendChild(nestedContainer);
                }
                targetContainer.appendChild(optionDiv);
            });
        });

        // 只在第一层显示area
        if (level === 0) {
            const area = document.getElementById('optionalMutualConfigArea');
            if (area) area.style.display = 'block';
        }
    }

    /**
     * 收集配置选择
     * @returns {Array} 配置列表
     */
    collectConfigurations() {
        console.log('🚀 [collectConfigurations] 开始收集所有配置...');

        // ⭐ 统一收集所有配置类型（包含嵌套）
        // - 必选配置 (required_accessory)
        // - 必选互斥配置 (required_accessory with group)
        // - 推荐配置 (recommended)
        // - 可选互斥配置 (optional_mutual)
        // 注：所有配置类型统一在 collectNestedConfigs() 中收集，避免重复
        const configurations = this.collectNestedConfigs('#productConfigArea', 0);

        console.log(`✅ [collectConfigurations] 收集完成！`);
        console.log(`  📦 总计: ${configurations.length} 个配置`);
        console.log(`  📋 完整配置列表:`, configurations);

        return configurations;
    }

    /**
     * 验证必选互斥组是否已选择
     * @returns {boolean} 是否通过验证
     */
    validateRequiredMutualGroups() {
        const groups = document.querySelectorAll('#requiredMutualConfigList .mutual-group');

        for (const group of groups) {
            const groupId = group.dataset.groupId;
            const checkedRadio = group.querySelector('input[type="radio"]:checked');

            if (!checkedRadio || !checkedRadio.value) {
                const groupTitle = group.querySelector('.group-title').textContent;
                alert(`请选择 "${groupTitle}" 中的一个配置选项`);
                return false;
            }
        }

        return true;
    }


    /**
     * 更新步骤指示器
     * @param {number} step - 当前步骤 (1, 2, 或 3)
     */
    updateStepIndicator(step) {
        const indicator = document.getElementById('configStepIndicator');
        if (!indicator) return;

        const items = indicator.querySelectorAll('.step-item');
        const dividers = indicator.querySelectorAll('.step-divider');

        items.forEach((item, index) => {
            const itemStep = index + 1;
            item.classList.remove('active', 'completed');
            if (itemStep === step) {
                item.classList.add('active');
            } else if (itemStep < step) {
                item.classList.add('completed');
            }
        });

        // 更新分隔线颜色（已完成步骤之后的分隔线变绿）
        dividers.forEach((divider, index) => {
            if (index < step - 1) {
                divider.style.background = '#28a745';
            } else {
                divider.style.background = '#dee2e6';
            }
        });

        console.log(`📍 步骤指示器更新: Step ${step}`);
    }

    /**
     * 重置状态
     */
    reset() {
        this.currentProducts = [];
        this.remainingProducts = [];
        this.selectedProduct = null;
        this.userSelections = {};
        this.userManualSelections = {};  // 用户手动选择的字段标记
        this.initialSelectablePositions = null;  // 初始可选字段位置
        this.initialFieldOptions = null;  // 初始选项列表
        this.specsFinalized = false;  // 规格是否已确定（待确认状态）
        this.fixedFields = [];
        this.selectableFields = [];
        this.pendingSpecs = [];
        this.configConfirmed = false;
        this.selectedConfigurations = [];
        this.step2Skipped = false;  // 重置步骤2跳过标记
        this.currentStep = 1;  // 1=规格选择, 2=配置选择, 3=配置确认

        // 更新步骤指示器
        this.updateStepIndicator(1);

        // 清空内容
        const containers = [
            'codeFieldsContainer',
            'matchedProductInfo',
            'productSpecsList',
            // ⭐ 新增：清空配置容器
            'requiredConfigList',
            'requiredMutualConfigList',
            'recommendedConfigList',
            'optionalMutualConfigList',
            'selectedConfigsList'
        ];

        containers.forEach(id => {
            const elem = document.getElementById(id);
            if (elem) {
                elem.innerHTML = '';
                if (id === 'codeFieldsContainer') {
                    elem.style.display = '';
                }
            }
        });

        // 重置显示状态
        const codeSelectionArea = document.getElementById('codeSelectionArea');
        const specsArea = document.getElementById('productSpecsArea');
        const configArea = document.getElementById('productConfigArea');
        const selectedArea = document.getElementById('selectedConfigsArea');
        const backBtn = document.getElementById('backToConfigSelection');

        if (codeSelectionArea) codeSelectionArea.style.display = 'none';
        if (specsArea) specsArea.style.display = 'none';

        // Step 1 时隐藏配置区域，只在 Step 2 才显示
        if (configArea) configArea.style.display = 'none';
        if (selectedArea) selectedArea.style.display = 'none';

        // 隐藏编码规格区域（Step 3 时显示）
        const codeSpecsWrapper = document.getElementById('configProductCodeSpecs');
        if (codeSpecsWrapper) codeSpecsWrapper.style.display = 'none';

        // 强制隐藏返回按钮
        if (backBtn) backBtn.style.display = 'none';

        // 重置确认按钮状态
        const confirmBtn = document.getElementById('confirmProductSelection');
        if (confirmBtn) {
            confirmBtn.innerHTML = '<i class="fas fa-check"></i> 确认选择';
            confirmBtn.onclick = () => this.confirmSelection();
        }

        // 重置动态规格配置
        this.resetDynamicSpecConfig();
    }

    // ==================== 嵌套配置方法（新增）====================

    /**
     * 加载必选配置的子配置
     * @param {number} parentProductId - 父产品ID
     * @param {string} containerId - 渲染容器ID
     * @param {number} level - 嵌套层级（最多2层）
     */
    async loadNestedRequiredConfigs(parentProductId, containerId, level) {
        if (level >= 2) return; // 限制最多2层

        console.log(`📡 [loadNestedRequiredConfigs] 加载产品 ${parentProductId} 的子配置 (层级: ${level})`);

        try {
            const response = await fetch(`/product-management/api/product/${parentProductId}/relations`);
            console.log('  - API响应状态:', response.status);

            const data = await response.json();
            console.log('  - API返回数据:', data);

            if (!data.success) {
                console.error('加载子配置失败:', data.message);
                return;
            }

            // 1. 渲染必选配置
            const requiredConfigs = data.data.filter(config => config.relation_type === 'required_accessory');
            if (requiredConfigs.length > 0) {
                this.renderRequiredConfigs(requiredConfigs, {
                    containerId: `${containerId}_required`,
                    level: level + 1,
                    parentId: parentProductId
                });
            }

            // 2. 渲染必选互斥组
            const requiredGroups = {};
            for (const [groupId, groupData] of Object.entries(data.groups || {})) {
                if (groupData.is_required) {
                    requiredGroups[groupId] = groupData;
                }
            }
            if (Object.keys(requiredGroups).length > 0) {
                this.renderRequiredMutualGroups(requiredGroups, {
                    containerId: `${containerId}_mutual`,
                    level: level + 1,
                    parentId: parentProductId
                });
            }

            // 3. 渲染推荐配置
            const recommendedConfigs = data.data.filter(config => config.relation_type === 'recommended');
            if (recommendedConfigs.length > 0) {
                this.renderRecommendedConfigs(recommendedConfigs, {
                    containerId: `${containerId}_recommended`,
                    level: level + 1,
                    parentId: parentProductId
                });
            }

            // 4. 渲染可选互斥组
            const optionalGroups = {};
            for (const [groupId, groupData] of Object.entries(data.groups || {})) {
                if (!groupData.is_required) {
                    optionalGroups[groupId] = groupData;
                }
            }
            if (Object.keys(optionalGroups).length > 0) {
                this.renderOptionalMutualGroups(optionalGroups, {
                    containerId: `${containerId}_optional_mutual`,
                    level: level + 1,
                    parentId: parentProductId
                });
            }

            // 5. 所有配置渲染完成后，动态添加分割线
            this.addDividersToNestedContainer(containerId);

        } catch (error) {
            console.error('加载子配置失败:', error);
        }
    }

    /**
     * 创建嵌套配置容器
     * @param {Object} config - 配置对象
     * @param {number} level - 嵌套层级
     * @returns {HTMLElement} 子配置容器
     */
    createNestedConfigContainer(config, level) {
        // 兼容两种属性名：related_product_id (从API返回) 或 product_id
        const productId = config.related_product_id || config.product_id;
        const containerId = `nested-config-${productId}-${level}`;

        console.log(`  🏗️ [createNestedConfigContainer] 创建容器`);
        console.log(`    - config对象:`, config);
        console.log(`    - 使用的productId: ${productId}`);
        console.log(`    - level: ${level}`);
        console.log(`    - 生成的containerId: ${containerId}`);

        const container = document.createElement('div');
        container.id = containerId;
        container.className = `sub-config-container level-${level}`;
        container.style.display = 'none'; // 默认隐藏
        // 不再静态添加分割线，只创建容器，分割线将在渲染完成后动态添加
        container.innerHTML = `
            <div id="${containerId}_required"></div>
            <div id="${containerId}_mutual"></div>
            <div id="${containerId}_recommended"></div>
            <div id="${containerId}_optional_mutual"></div>
        `;

        return container;
    }

    /**
     * 动态添加分割线到嵌套配置容器
     * 只在有内容的区域之间添加分割线
     * @param {string} containerId - 嵌套容器ID
     */
    addDividersToNestedContainer(containerId) {
        console.log(`📏 [addDividersToNestedContainer] 为容器添加分割线: ${containerId}`);

        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`  ⚠️ 容器未找到: ${containerId}`);
            return;
        }

        // 获取所有子容器
        const requiredDiv = document.getElementById(`${containerId}_required`);
        const mutualDiv = document.getElementById(`${containerId}_mutual`);
        const recommendedDiv = document.getElementById(`${containerId}_recommended`);
        const optionalMutualDiv = document.getElementById(`${containerId}_optional_mutual`);

        // 收集有内容的容器（按顺序）
        const nonEmptyContainers = [
            requiredDiv,
            mutualDiv,
            recommendedDiv,
            optionalMutualDiv
        ].filter(div => div && div.children.length > 0);

        console.log(`  ✅ 找到 ${nonEmptyContainers.length} 个有内容的容器`);

        // 在有内容的容器之间插入分割线
        for (let i = 0; i < nonEmptyContainers.length - 1; i++) {
            const divider = document.createElement('hr');
            divider.className = 'nested-divider';

            // 在下一个容器之前插入分割线
            const nextContainer = nonEmptyContainers[i + 1];
            container.insertBefore(divider, nextContainer);
            console.log(`  ➕ 在第 ${i + 1} 和第 ${i + 2} 个容器之间添加分割线`);
        }

        console.log(`  ✅ 分割线添加完成`);
    }

    /**
     * 展开/折叠子配置
     * @param {number} productId - 产品ID
     * @param {number} level - 当前层级
     */
    toggleNestedConfig(productId, level) {
        console.log('🔍 [toggleNestedConfig] 被调用');
        console.log('  - productId:', productId);
        console.log('  - level:', level);
        console.log('  - 查找容器ID:', `nested-config-${productId}-${level}`);

        const container = document.getElementById(`nested-config-${productId}-${level}`);
        console.log('  - 找到容器:', container ? 'YES' : 'NO');

        const icon = document.getElementById(`toggle-icon-${productId}`);
        console.log('  - 找到图标:', icon ? 'YES' : 'NO');

        const btn = icon ? icon.closest('.toggle-nested-btn') : null;
        console.log('  - 找到按钮:', btn ? 'YES' : 'NO');

        if (!container) {
            console.error('❌ 容器未找到! 期望ID:', `nested-config-${productId}-${level}`);
            // 列出页面上所有的嵌套容器ID
            const allContainers = document.querySelectorAll('[id^="nested-config-"]');
            console.log('  页面上现有的嵌套容器:', Array.from(allContainers).map(c => c.id));
            return;
        }

        if (container.style.display === 'none') {
            // 展开
            container.style.display = 'block';
            container.classList.remove('collapsed');
            if (icon) icon.className = 'fas fa-chevron-down';
            if (btn) btn.classList.add('expanded');

            // 首次展开时加载子配置
            if (!container.dataset.loaded) {
                this.loadNestedRequiredConfigs(productId, container.id, level);
                container.dataset.loaded = 'true';
            }
        } else {
            // 折叠
            container.style.display = 'none';
            container.classList.add('collapsed');
            if (icon) icon.className = 'fas fa-chevron-right';
            if (btn) btn.classList.remove('expanded');
        }
    }

    /**
     * 自动展开嵌套配置（选中时调用）
     * @param {number} productId - 产品ID
     * @param {number} level - 当前层级
     */
    autoExpandNestedConfig(productId, level) {
        console.log(`🔓 [autoExpandNestedConfig] 自动展开产品 ${productId} 的嵌套配置 (层级: ${level})`);

        const container = document.getElementById(`nested-config-${productId}-${level}`);

        if (!container) {
            console.error('❌ 容器未找到! 期望ID:', `nested-config-${productId}-${level}`);
            return;
        }

        // 展开容器
        container.style.display = 'block';
        container.classList.remove('collapsed');

        // 首次展开时加载子配置
        if (!container.dataset.loaded) {
            console.log(`  📡 首次展开，加载子配置...`);
            this.loadNestedRequiredConfigs(productId, container.id, level);
            container.dataset.loaded = 'true';
        } else {
            console.log(`  ✅ 子配置已加载，直接展开`);
        }
    }

    /**
     * 收起嵌套配置（取消选中时调用）
     * @param {number} productId - 产品ID
     * @param {number} level - 当前层级
     */
    collapseNestedConfig(productId, level) {
        console.log(`🔒 [collapseNestedConfig] 收起产品 ${productId} 的嵌套配置 (层级: ${level})`);

        const container = document.getElementById(`nested-config-${productId}-${level}`);

        if (!container) {
            console.log('  ℹ️ 容器不存在或已移除');
            return;
        }

        // 收起容器
        container.style.display = 'none';
        container.classList.add('collapsed');

        console.log(`  ✅ 嵌套配置已收起`);
    }

    /**
     * 递归收集嵌套配置
     * @param {string} baseSelector - 容器选择器
     * @param {number} level - 层级
     * @returns {Array} 配置列表（包含子配置）
     */
    collectNestedConfigs(baseSelector, level = 0) {
        console.log(`📦 [collectNestedConfigs] 开始收集嵌套配置`);
        console.log(`  - baseSelector: ${baseSelector}`);
        console.log(`  - level: ${level}`);

        const configs = [];
        const container = document.querySelector(baseSelector);
        if (!container) {
            console.warn(`  ⚠️ 容器未找到: ${baseSelector}`);
            return configs;
        }
        console.log(`  ✅ 找到容器: ${container.id}`);

        // 收集必选配置
        // 第一层使用固定ID，嵌套层使用动态ID
        const requiredContainerId = (level === 0) ? 'requiredConfigList' : `${container.id}_required`;
        const requiredContainer = document.getElementById(requiredContainerId);
        console.log(`  🔍 查找必选配置容器: #${requiredContainerId}, 找到: ${requiredContainer ? 'YES' : 'NO'}`);

        if (requiredContainer) {
            console.log(`  📌 收集必选配置...`);
            const requiredItems = requiredContainer.querySelectorAll('[data-product-id][data-relation-type="required_accessory"]');
            console.log(`    - 找到 ${requiredItems.length} 个必选配置项`);

            requiredItems.forEach(item => {
                const productId = item.dataset.productId;
                console.log(`    - 收集必选配置: productId=${productId}`);

                // 优先使用完整的产品数据
                let config = {};
                if (item.dataset.productData) {
                    try {
                        config = JSON.parse(item.dataset.productData);
                        console.log(`      ✅ 使用完整产品数据`);
                        console.log(`      - 解析后的config:`, config);
                        console.log(`      - product_model: ${config.product_model}`);
                        console.log(`      - specification: ${config.specification}`);
                        console.log(`      - retail_price: ${config.retail_price}`);
                    } catch (e) {
                        console.error('      ❌ 解析产品数据失败:', e);
                    }
                }

                // 如果没有完整数据，使用基本字段
                if (!config.related_product_id && !config.product_id) {
                    config = {
                        product_id: parseInt(productId),
                        product_name: item.dataset.productName,
                        product_mn: item.dataset.productMn,
                        default_quantity: parseInt(item.dataset.quantity || 1),
                        relation_type: 'required_accessory'
                    };
                    console.log(`      ⚠️ 使用基本字段数据`);
                } else {
                    console.log(`      ✅ 保留完整产品数据，不覆盖`);
                }

                // 确保字段一致性（但不覆盖已有的完整数据）
                if (!config.product_id) {
                    config.product_id = config.related_product_id || parseInt(productId);
                }
                if (!config.default_quantity) {
                    config.default_quantity = parseInt(item.dataset.quantity || 1);
                }
                config.relation_type = 'required_accessory';

                // 递归收集子配置
                const subContainerId = `nested-config-${productId}-${level}`;
                console.log(`      🔍 查找子配置容器: ${subContainerId}`);
                const subContainer = document.getElementById(subContainerId);

                if (subContainer) {
                    console.log(`      ✅ 找到子配置容器, loaded=${subContainer.dataset.loaded}`);
                    if (subContainer.dataset.loaded === 'true') {
                        console.log(`      📦 递归收集子配置...`);
                        config.nested_configs = this.collectNestedConfigs(`#${subContainer.id}`, level + 1);
                        console.log(`      ✅ 收集到 ${config.nested_configs.length} 个子配置`);
                    }
                } else {
                    console.log(`      ℹ️ 没有子配置容器`);
                }

                configs.push(config);
                console.log(`      ✅ 已添加配置到列表`);
            });
        }

        // 收集必选互斥配置
        // 第一层使用固定ID，嵌套层使用动态ID
        const mutualContainerId = (level === 0) ? 'requiredMutualConfigList' : `${container.id}_mutual`;
        const mutualContainer = document.getElementById(mutualContainerId);
        console.log(`  🔍 查找必选互斥配置容器: #${mutualContainerId}, 找到: ${mutualContainer ? 'YES' : 'NO'}`);

        if (mutualContainer) {
            console.log(`  📻 收集必选互斥配置...`);
            const checkedRadios = mutualContainer.querySelectorAll('input[type="radio"]:checked');
            console.log(`    - 找到 ${checkedRadios.length} 个选中的radio`);

            checkedRadios.forEach(radio => {
                console.log(`    - 检查radio: productId=${radio.value}, required=${radio.dataset.required}`);

                if (radio.dataset.required === 'true') {
                    const productId = radio.value;
                    console.log(`      ✅ 收集产品 ${productId}`);

                    // 优先使用完整的产品数据
                    let config = {};
                    if (radio.dataset.productData) {
                        try {
                            config = JSON.parse(radio.dataset.productData);
                            console.log(`      ✅ [互斥组] 使用完整产品数据`);
                            console.log(`      - 解析后的config:`, config);
                            console.log(`      - product_model: ${config.product_model}`);
                            console.log(`      - specification: ${config.specification}`);
                            console.log(`      - retail_price: ${config.retail_price}`);
                        } catch (e) {
                            console.error('      ❌ [互斥组] 解析产品数据失败:', e);
                        }
                    }

                    // 如果没有完整数据，使用基本字段
                    if (!config.related_product_id && !config.product_id) {
                        config = {
                            product_id: parseInt(productId),
                            product_name: radio.dataset.productName,
                            product_mn: radio.dataset.productMn,
                            default_quantity: 1,
                            relation_type: 'required_accessory',
                            group_id: radio.name
                        };
                        console.log(`      ⚠️ [互斥组] 使用基本字段数据`);
                    } else {
                        console.log(`      ✅ [互斥组] 保留完整产品数据，不覆盖`);
                    }

                    // 确保字段一致性
                    if (!config.product_id) {
                        config.product_id = config.related_product_id || parseInt(productId);
                    }
                    config.default_quantity = 1;
                    config.relation_type = 'required_accessory';
                    config.group_id = radio.name;

                    // 递归收集子配置
                    const subContainerId = `nested-config-${productId}-${level}`;
                    console.log(`      🔍 查找子配置容器: ${subContainerId}`);
                    const subContainer = document.getElementById(subContainerId);

                    if (subContainer) {
                        console.log(`      ✅ 找到子配置容器, loaded=${subContainer.dataset.loaded}`);
                        if (subContainer.dataset.loaded === 'true') {
                            console.log(`      📦 递归收集子配置...`);
                            config.nested_configs = this.collectNestedConfigs(`#${subContainer.id}`, level + 1);
                            console.log(`      ✅ 收集到 ${config.nested_configs.length} 个子配置`);
                        } else {
                            console.log(`      ⚠️ 子配置容器未加载`);
                        }
                    } else {
                        console.log(`      ℹ️ 没有子配置容器`);
                    }

                    configs.push(config);
                    console.log(`      ✅ 已添加配置到列表`);
                }
            });
        } else {
            console.log(`  ℹ️ 没有必选互斥配置容器`);
        }

        // ===== 新增：收集推荐配置 =====
        const recommendedContainerId = (level === 0) ? 'recommendedConfigList' : `${container.id}_recommended`;
        const recommendedContainer = document.getElementById(recommendedContainerId);
        console.log(`  🔍 查找推荐配置容器: #${recommendedContainerId}, 找到: ${recommendedContainer ? 'YES' : 'NO'}`);

        if (recommendedContainer) {
            console.log(`  ✨ 收集推荐配置...`);
            const checkedBoxes = recommendedContainer.querySelectorAll('input[type="checkbox"]:checked');
            console.log(`    - 找到 ${checkedBoxes.length} 个选中的checkbox`);

            checkedBoxes.forEach(checkbox => {
                const productId = checkbox.dataset.productId;
                console.log(`    - 收集推荐配置: productId=${productId}`);

                // 优先使用完整的产品数据
                let config = {};
                if (checkbox.dataset.productData) {
                    try {
                        config = JSON.parse(checkbox.dataset.productData);
                        console.log(`      ✅ 使用完整产品数据`);
                    } catch (e) {
                        console.error('      ❌ 解析产品数据失败:', e);
                    }
                }

                // 确保字段一致性
                if (!config.product_id) {
                    config.product_id = config.related_product_id || parseInt(productId);
                }
                if (!config.default_quantity) {
                    config.default_quantity = parseInt(checkbox.dataset.quantity || 1);
                }
                config.relation_type = 'recommended';

                // 递归收集子配置
                const subContainerId = `nested-config-${productId}-${level}`;
                console.log(`      🔍 查找子配置容器: ${subContainerId}`);
                const subContainer = document.getElementById(subContainerId);

                if (subContainer && subContainer.dataset.loaded === 'true') {
                    console.log(`      📦 递归收集子配置...`);
                    config.nested_configs = this.collectNestedConfigs(`#${subContainer.id}`, level + 1);
                    console.log(`      ✅ 收集到 ${config.nested_configs.length} 个子配置`);
                }

                configs.push(config);
                console.log(`      ✅ 已添加配置到列表`);
            });
        }

        // ===== 新增：收集可选互斥配置 =====
        const optionalMutualContainerId = (level === 0) ? 'optionalMutualConfigList' : `${container.id}_optional_mutual`;
        const optionalMutualContainer = document.getElementById(optionalMutualContainerId);
        console.log(`  🔍 查找可选互斥配置容器: #${optionalMutualContainerId}, 找到: ${optionalMutualContainer ? 'YES' : 'NO'}`);

        if (optionalMutualContainer) {
            console.log(`  💡 收集可选互斥配置...`);
            const checkedRadios = optionalMutualContainer.querySelectorAll('input[type="radio"]:checked');
            console.log(`    - 找到 ${checkedRadios.length} 个选中的radio`);

            checkedRadios.forEach(radio => {
                const productId = radio.value;
                console.log(`    - 收集可选互斥配置: productId=${productId}`);

                // 优先使用完整的产品数据
                let config = {};
                if (radio.dataset.productData) {
                    try {
                        config = JSON.parse(radio.dataset.productData);
                        console.log(`      ✅ 使用完整产品数据`);
                    } catch (e) {
                        console.error('      ❌ 解析产品数据失败:', e);
                    }
                }

                // 确保字段一致性
                if (!config.product_id) {
                    config.product_id = config.related_product_id || parseInt(productId);
                }
                if (!config.default_quantity) {
                    config.default_quantity = parseInt(radio.dataset.quantity || 1);
                }
                config.relation_type = 'optional_mutual';
                config.group_id = radio.dataset.groupId;

                // 递归收集子配置
                const subContainerId = `nested-config-${productId}-${level}`;
                console.log(`      🔍 查找子配置容器: ${subContainerId}`);
                const subContainer = document.getElementById(subContainerId);

                if (subContainer && subContainer.dataset.loaded === 'true') {
                    console.log(`      📦 递归收集子配置...`);
                    config.nested_configs = this.collectNestedConfigs(`#${subContainer.id}`, level + 1);
                    console.log(`      ✅ 收集到 ${config.nested_configs.length} 个子配置`);
                }

                configs.push(config);
                console.log(`      ✅ 已添加配置到列表`);
            });
        }

        console.log(`📦 [collectNestedConfigs] 收集完成，共 ${configs.length} 个配置`);
        console.log(`  配置列表:`, configs);
        return configs;
    }

    /**
     * 递归验证必选配置
     * @param {string} baseSelector - 容器选择器
     * @param {number} level - 层级
     * @returns {boolean} 是否通过验证
     */
    validateNestedRequiredConfigs(baseSelector, level = 0) {
        const container = document.querySelector(baseSelector);
        if (!container) return true;

        // 验证必选互斥组
        const mutualContainer = container.querySelector(`#${container.id}_mutual`);
        if (mutualContainer) {
            const groups = mutualContainer.querySelectorAll('[data-group-required="true"]');
            for (const group of groups) {
                const groupName = group.dataset.groupName;
                const checkedInputs = group.querySelectorAll('input[type="radio"]:checked');

                if (checkedInputs.length === 0) {
                    alert(`请为"${groupName}"选择一个选项`);
                    return false;
                }

                // 递归验证选中项的子配置
                const checkedProductId = checkedInputs[0].value;
                const subContainer = document.getElementById(`nested-config-${checkedProductId}-${level}`);
                if (subContainer && subContainer.dataset.loaded === 'true') {
                    if (!this.validateNestedRequiredConfigs(`#${subContainer.id}`, level + 1)) {
                        return false;
                    }
                }
            }
        }

        return true;
    }

    // ============== 动态规格配置功能 ==============

    /**
     * 获取子分类的所有规格字段及其选项（包括继承的分类级字段）
     * @param {number} subcategoryId - 子分类ID
     * @returns {Object|null} 规格字段数据，包含 spec_fields 数组
     */
    async fetchSpecFieldOptions(subcategoryId) {
        try {
            const response = await fetch(`/quotation/api/subcategory/${subcategoryId}/spec-field-options`);
            const result = await response.json();
            if (result.success) {
                return result.data;
            }
            console.warn('获取规格字段选项失败:', result.message);
            return null;
        } catch (error) {
            console.error('获取规格字段选项请求失败:', error);
            return null;
        }
    }

    /**
     * 加载产品的可配置规格
     * @param {number} productId - 产品ID
     */
    async loadConfigurableSpecs(productId) {
        console.log(`🔧 加载可配置规格: product_id=${productId}`);

        const specArea = document.getElementById('dynamicSpecConfigArea');
        const loadingEl = document.getElementById('specConfigLoading');
        const listEl = document.getElementById('configurableSpecsList');
        const noSpecsEl = document.getElementById('noConfigurableSpecs');
        const previewEl = document.getElementById('specConfigPreview');

        // 重置状态
        this.configurableSpecs = [];
        this.specConfig = {};
        this.configuredMnResult = null;
        this.hasSpecChanges = false;

        // 显示加载状态
        if (specArea) specArea.style.display = 'block';
        if (loadingEl) loadingEl.style.display = 'block';
        if (listEl) listEl.innerHTML = '';
        if (noSpecsEl) noSpecsEl.style.display = 'none';
        if (previewEl) previewEl.style.display = 'none';

        try {
            const response = await fetch(`/quotation/api/product/${productId}/configurable-specs`);
            const result = await response.json();

            if (loadingEl) loadingEl.style.display = 'none';

            if (result.success && result.data.configurable_fields && result.data.configurable_fields.length > 0) {
                console.log(`  ✓ 可配置规格加载成功: ${result.data.configurable_fields.length} 个字段`);
                this.configurableSpecs = result.data.configurable_fields;
                this.originalMn = result.data.spec_mn;

                // 初始化specConfig为当前值
                this.configurableSpecs.forEach(field => {
                    this.specConfig[field.field_name] = field.current_value;
                });

                // 渲染可配置规格UI
                this.renderConfigurableSpecs();

                // 更新头部编码规格显示（包含可配置规格）
                this.showCodeSpecsInConfirmation();
            } else {
                console.log('  ℹ️ 该产品无可配置规格');
                if (specArea) specArea.style.display = 'none';  // 完全隐藏区域
            }
        } catch (error) {
            console.error('❌ 加载可配置规格失败:', error);
            if (loadingEl) loadingEl.style.display = 'none';
            if (specArea) specArea.style.display = 'none';  // 出错时隐藏
        }
    }

    /**
     * 渲染可配置规格UI
     */
    renderConfigurableSpecs() {
        const listEl = document.getElementById('configurableSpecsList');
        if (!listEl) return;

        listEl.innerHTML = '';

        this.configurableSpecs.forEach(field => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'configurable-spec-item';
            itemDiv.dataset.fieldName = field.field_name;

            // 标题行
            const headerDiv = document.createElement('div');
            headerDiv.className = 'spec-header';

            const nameSpan = document.createElement('span');
            nameSpan.className = 'spec-name';
            nameSpan.textContent = field.field_name + (field.field_unit ? ` (${field.field_unit})` : '');

            const currentSpan = document.createElement('span');
            currentSpan.className = 'spec-current';
            currentSpan.innerHTML = `当前: <span class="current-value">${field.current_value}${field.field_unit || ''}</span>`;

            headerDiv.appendChild(nameSpan);
            headerDiv.appendChild(currentSpan);

            // 选项区域
            const optionsDiv = document.createElement('div');
            optionsDiv.className = 'spec-options';

            field.options.forEach(option => {
                const optionBtn = document.createElement('button');
                optionBtn.type = 'button';
                optionBtn.className = 'spec-option-btn';
                if (option.is_current) {
                    optionBtn.classList.add('is-current', 'active');
                }
                optionBtn.dataset.value = option.value;
                optionBtn.dataset.code = option.code;
                optionBtn.dataset.optionId = option.option_id;

                // 选项文本
                const valueText = option.value + (field.field_unit || '');
                optionBtn.innerHTML = valueText;

                // 价格增量标签
                if (option.price_adjustment !== 0) {
                    const priceBadge = document.createElement('span');
                    const priceYuan = option.price_adjustment / 100;
                    if (priceYuan > 0) {
                        priceBadge.className = 'price-badge positive';
                        priceBadge.textContent = `+${priceYuan}`;
                    } else {
                        priceBadge.className = 'price-badge negative';
                        priceBadge.textContent = `${priceYuan}`;
                    }
                    optionBtn.appendChild(priceBadge);
                }

                // 点击事件
                optionBtn.addEventListener('click', () => {
                    this.onSpecOptionSelect(field.field_name, option.value, optionsDiv, optionBtn);
                });

                optionsDiv.appendChild(optionBtn);
            });

            itemDiv.appendChild(headerDiv);
            itemDiv.appendChild(optionsDiv);
            listEl.appendChild(itemDiv);
        });
    }

    /**
     * 处理规格选项选择
     * @param {string} fieldName - 字段名
     * @param {string} value - 选择的值
     * @param {HTMLElement} optionsContainer - 选项容器
     * @param {HTMLElement} selectedBtn - 选中的按钮
     */
    async onSpecOptionSelect(fieldName, value, optionsContainer, selectedBtn) {
        // 更新按钮状态
        optionsContainer.querySelectorAll('.spec-option-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        selectedBtn.classList.add('active');

        // 更新配置
        this.specConfig[fieldName] = value;

        // 更新头部编码规格显示（同步显示选择的可配置规格）
        this.showCodeSpecsInConfirmation();

        // 更新产品描述（跟随可配置规格选择变化）
        this.updateProductSpecification();

        // 检查是否有变更
        this.checkSpecChanges();

        // 更新UI状态
        const itemDiv = optionsContainer.closest('.configurable-spec-item');
        const field = this.configurableSpecs.find(f => f.field_name === fieldName);
        if (field) {
            if (field.current_value !== value) {
                itemDiv.classList.add('spec-changed');
            } else {
                itemDiv.classList.remove('spec-changed');
            }
        }

        // 如果有变更，计算新MN
        if (this.hasSpecChanges) {
            await this.calculateConfiguredMn();
        } else {
            // 无变更，隐藏预览
            const previewEl = document.getElementById('specConfigPreview');
            if (previewEl) previewEl.style.display = 'none';
        }
    }

    /**
     * 检查是否有规格变更
     */
    checkSpecChanges() {
        this.hasSpecChanges = false;

        for (const field of this.configurableSpecs) {
            if (this.specConfig[field.field_name] !== field.current_value) {
                this.hasSpecChanges = true;
                break;
            }
        }

    }

    /**
     * 更新产品描述（Step 2：根据可配置规格的选择更新描述文字）
     * 如果原描述中没有该字段，会追加到末尾
     */
    updateProductSpecification() {
        const specElement = document.getElementById('configProductSpec');
        if (!specElement || !this.selectedProduct) {
            return;
        }

        // 从原始描述开始，替换可配置规格的值
        let specification = this.selectedProduct.specification || '';
        const addedFields = [];  // 记录需要追加的字段

        if (this.configurableSpecs && this.specConfig) {
            this.configurableSpecs.forEach(field => {
                const fieldName = field.field_name;
                const newValue = this.specConfig[fieldName];
                const unit = field.field_unit || '';

                if (newValue) {
                    // 替换描述中对应字段的值（匹配 "字段名: 值" 格式）
                    // 支持中英文冒号和逗号/分号分隔
                    const pattern = new RegExp(`${fieldName}[:：]\\s*[^,，;；]+`, 'g');
                    const replacement = unit ? `${fieldName}: ${newValue} ${unit}` : `${fieldName}: ${newValue}`;
                    const beforeReplace = specification;
                    specification = specification.replace(pattern, replacement);

                    // 如果替换未生效（原描述中没有该字段），记录需要追加
                    if (specification === beforeReplace) {
                        addedFields.push(replacement);
                    }
                }
            });
        }

        // 追加原描述中不存在的可配置规格
        if (addedFields.length > 0) {
            const separator = specification.trim() ? ', ' : '';
            specification = specification.trim() + separator + addedFields.join(', ');
        }

        specElement.textContent = specification;
    }

    /**
     * 计算配置后的MN
     */
    async calculateConfiguredMn() {
        if (!this.selectedProduct || !this.hasSpecChanges) return;

        console.log('🔄 计算配置后的MN...');

        const previewEl = document.getElementById('specConfigPreview');
        const previewLoading = document.getElementById('specConfigLoading');

        // 显示计算中状态
        if (previewLoading) {
            previewLoading.style.display = 'block';
            previewLoading.innerHTML = `
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2 text-muted">正在计算新MN...</span>
            `;
        }

        try {
            const response = await fetch(`/quotation/api/product/${this.selectedProduct.id}/calculate-mn`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    spec_config: this.specConfig
                })
            });

            const result = await response.json();

            if (previewLoading) previewLoading.style.display = 'none';

            if (result.success) {
                console.log('  ✓ MN计算成功:', result.data);
                this.configuredMnResult = result.data;
                this.renderConfigPreview(result.data);
            } else {
                console.error('  ✗ MN计算失败:', result.message);
                this.configuredMnResult = null;
                if (previewEl) previewEl.style.display = 'none';
            }
        } catch (error) {
            console.error('❌ 计算MN请求失败:', error);
            if (previewLoading) previewLoading.style.display = 'none';
            this.configuredMnResult = null;
        }
    }

    /**
     * 渲染配置预览
     * @param {Object} data - MN计算结果
     */
    renderConfigPreview(data) {
        const previewEl = document.getElementById('specConfigPreview');
        if (!previewEl) return;

        previewEl.style.display = 'block';

        // 原MN
        const origMnEl = document.getElementById('previewOriginalMn');
        if (origMnEl) origMnEl.textContent = data.original_mn || '-';

        // 新MN
        const configMnEl = document.getElementById('previewConfiguredMn');
        if (configMnEl) configMnEl.textContent = data.configured_mn || '-';

        // 价格增量
        const priceAdjEl = document.getElementById('previewPriceAdjustment');
        if (priceAdjEl) {
            const priceYuan = data.price_adjustment_total / 100;
            if (priceYuan > 0) {
                priceAdjEl.textContent = `价格 +¥${priceYuan.toFixed(2)}`;
                priceAdjEl.className = 'badge bg-warning text-dark';
            } else if (priceYuan < 0) {
                priceAdjEl.textContent = `价格 ¥${priceYuan.toFixed(2)}`;
                priceAdjEl.className = 'badge bg-success';
            } else {
                priceAdjEl.textContent = '价格不变';
                priceAdjEl.className = 'badge bg-secondary';
            }
        }

        // 是否已存在产品
        const existingEl = document.getElementById('previewExistingProduct');
        const newEl = document.getElementById('previewNewProduct');

        if (data.is_new_product) {
            if (existingEl) existingEl.style.display = 'none';
            if (newEl) newEl.style.display = 'block';
        } else {
            if (existingEl) {
                existingEl.style.display = 'block';
                const msgEl = document.getElementById('previewExistingMessage');
                if (msgEl && data.existing_product_price) {
                    const priceYuan = data.existing_product_price / 100;
                    msgEl.textContent = `已存在相同规格产品，价格 ¥${priceYuan.toFixed(2)}`;
                }
            }
            if (newEl) newEl.style.display = 'none';
        }
    }

    /**
     * 重置动态规格配置
     */
    resetDynamicSpecConfig() {
        this.configurableSpecs = [];
        this.specConfig = {};
        this.configuredMnResult = null;
        this.hasSpecChanges = false;

        const specArea = document.getElementById('dynamicSpecConfigArea');
        const listEl = document.getElementById('configurableSpecsList');
        const previewEl = document.getElementById('specConfigPreview');

        if (specArea) specArea.style.display = 'none';
        if (listEl) listEl.innerHTML = '';
        if (previewEl) previewEl.style.display = 'none';
    }

    /**
     * 获取动态规格配置数据（供保存时使用）
     * @returns {Object|null} 配置数据或null（无变更时）
     */
    getDynamicSpecConfigData() {
        if (!this.hasSpecChanges || !this.configuredMnResult) {
            return null;
        }

        return {
            original_product_id: this.selectedProduct?.id,
            original_mn: this.configuredMnResult.original_mn,
            configured_mn: this.configuredMnResult.configured_mn,
            spec_config: this.specConfig,
            price_adjustment_total: this.configuredMnResult.price_adjustment_total,
            is_new_product: this.configuredMnResult.is_new_product,
            existing_product_id: this.configuredMnResult.existing_product_id,
            spec_details: this.configuredMnResult.spec_details
        };
    }
}

// 全局实例变量
window.ProductConfigModal = ProductConfigModal;
