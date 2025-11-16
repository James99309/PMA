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
        this.init();
    }

    /**
     * 初始化模态框
     */
    init() {
        // 绑定确认按钮事件
        const confirmBtn = document.getElementById('confirmProductSelection');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => {
                this.confirmSelection();
            });
        }

        // 绑定返回按钮事件
        const backBtn = document.getElementById('backToConfigSelection');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                this.backToConfigSelection();
            });
        }

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
        // 🆕 添加调试日志
        console.log('🔍 parseSnapshot 调试:');
        console.log('  - 原始数据类型:', typeof rawSnapshot);
        console.log('  - 原始数据值:', rawSnapshot);
        console.log('  - 是否为null:', rawSnapshot === null);
        console.log('  - 是否为undefined:', rawSnapshot === undefined);

        if (!rawSnapshot) {
            console.warn('  ⚠️ 快照为空或未定义，返回空数组');
            return [];
        }

        try {
            // 如果是字符串，先解析
            let parsed = rawSnapshot;
            if (typeof rawSnapshot === 'string') {
                console.log('  → 检测到字符串类型，尝试JSON.parse');
                parsed = JSON.parse(rawSnapshot);
                console.log('  → 解析成功，解析后类型:', typeof parsed);
            }

            // 新格式：从code_parts提取
            if (parsed && parsed.code_parts && Array.isArray(parsed.code_parts)) {
                console.log(`  ✅ 成功: 从code_parts提取${parsed.code_parts.length}个规格字段`);
                return parsed.code_parts;
            }

            // 旧格式：直接是数组
            if (Array.isArray(parsed)) {
                console.log(`  ✅ 成功: 直接使用数组格式 (${parsed.length}个元素)`);
                return parsed;
            }

            console.error('  ❌ 快照格式不匹配，parsed内容:', parsed);
            return [];
        } catch (e) {
            console.error('  ❌ 解析错误:', e);
            console.error('  原始数据:', rawSnapshot);
            return [];
        }
    }

    /**
     * 分析编码差异并显示编码选择器
     * @param {Array} products - 产品列表
     * @param {boolean} isInitial - 是否为初始调用（首次打开）
     */
    analyzeAndShowCodeSelection(products, isInitial = true) {
        try {
            // 初始调用：初始化剩余产品列表
            if (isInitial) {
                this.remainingProducts = [...products];
                this.userSelections = {};
                console.log(`🎯 初始分析: ${products.length} 个产品`);
            } else {
                console.log(`🔄 重新分析: ${products.length} 个剩余产品`);
            }

            // 🆕 添加产品数据调试日志
            console.log('📦 分析产品编码 - 调试信息:');
            console.log('  - 产品数量:', products.length);
            console.log('  - 第一个产品完整对象:', products[0]);
            console.log('  - 第一个产品关键字段:', {
                id: products[0].id,
                model: products[0].model,
                product_mn: products[0].product_mn,
                product_name: products[0].product_name
            });
            console.log('  - code_definition_snapshot字段:', {
                exists: 'code_definition_snapshot' in products[0],
                type: typeof products[0].code_definition_snapshot,
                value: products[0].code_definition_snapshot
            });

            // 获取第一个产品的编码快照作为基准
            const baseSnapshot = this.parseSnapshot(products[0].code_definition_snapshot);
            console.log('  - 解析后快照长度:', baseSnapshot.length);
            console.log('  - 解析后快照内容:', baseSnapshot);

            if (baseSnapshot.length === 0) {
                console.error('❌ 产品编码快照为空 - 详细信息已在上方日志中');
                this.showError('产品编码数据缺失');
                return;
            }

            // 分析每个编码位置的差异
            const codeAnalysis = [];

            baseSnapshot.forEach((field, index) => {
                const position = index;
                const fieldName = field.field_name || field.name;  // 适配新旧字段名

                // 检查该字段是否已被用户选择
                if (this.userSelections.hasOwnProperty(position)) {
                    // 已选择的字段标记为"用户选择"（显示为已确定）
                    codeAnalysis.push({
                        position: position,
                        fieldName: fieldName,
                        isDifferent: false,  // 标记为固定
                        status: 'user_selected',  // 状态标记
                        fixedValue: {
                            code: this.userSelections[position].code,
                            value: this.userSelections[position].value,
                            unit: this.userSelections[position].unit || null  // 添加单位
                        },
                        options: [],
                        selectedCode: this.userSelections[position].code
                    });
                    return;  // 跳过分析，已确定
                }

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

                // 判断是否有差异
                const isDifferent = codeOptions.size > 1;

                codeAnalysis.push({
                    position: position,
                    fieldName: fieldName,
                    isDifferent: isDifferent,
                    status: isDifferent ? 'selectable' : 'auto_fixed',  // 状态标记
                    options: Array.from(codeOptions.values()),
                    selectedCode: null,  // 默认未选择
                    // 如果所有产品相同，记录该确定的值
                    fixedValue: !isDifferent ? codeOptions.values().next().value : null
                });
            });

            // 分离两类字段：固定字段（确定的值）和可选字段（需要选择）
            this.fixedFields = codeAnalysis.filter(field => !field.isDifferent);
            this.selectableFields = codeAnalysis.filter(field => field.isDifferent);

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
     * 增强：区分用户选择、自动确定、可选择三种状态
     */
    renderFields() {
        const container = document.getElementById('codeFieldsContainer');
        if (!container) return;

        container.innerHTML = '';

        // 动态设置标题：根据是否有可选字段
        const titleElement = document.getElementById('codeSelectionTitle');
        if (titleElement) {
            if (this.selectableFields && this.selectableFields.length > 0) {
                // 有可选字段 → "请选择产品规格"
                titleElement.innerHTML = '<i class="fas fa-sliders-h"></i> 请选择产品规格';
            } else {
                // 无可选字段（单产品或全部确定） → "产品规格"
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

                // 添加单位显示
                const unitText = field.fixedValue.unit ? ` ${field.fixedValue.unit}` : '';

                fieldDiv.innerHTML = `
                    <div class="spec-field-label">${field.fieldName}:</div>
                    <div class="spec-field-value">${field.fixedValue.value}${unitText}</div>
                `;

                gridContainer.appendChild(fieldDiv);
            });

            container.appendChild(gridContainer);
        }

        // 2. 再渲染可选字段（需要选择）
        this.selectableFields.forEach((field, index) => {
            const fieldDiv = document.createElement('div');
            fieldDiv.className = 'spec-field-selectable';
            fieldDiv.dataset.position = field.position;

            // 字段标签
            const label = document.createElement('label');
            label.className = 'form-label';
            label.innerHTML = `
                ${field.fieldName}
                <span class="text-danger">*</span>
            `;
            fieldDiv.appendChild(label);

            // 选项列表容器
            const optionsContainer = document.createElement('div');
            optionsContainer.className = 'spec-options-list';

            field.options.forEach((option, optIndex) => {
                // 每个选项的容器（使用Bootstrap的form-check）
                const optionDiv = document.createElement('div');
                optionDiv.className = 'form-check';

                // Radio input
                const input = document.createElement('input');
                input.type = 'radio';
                input.className = 'form-check-input';
                input.name = `code-${field.position}`;
                input.id = `code-${field.position}-${optIndex}`;
                input.value = option.code;

                // ⚠️ 关键修改：绑定新的事件处理器
                input.addEventListener('change', () => {
                    this.onFieldSelect(field.position, option.code, option.value, option.unit);
                });

                // Label
                const optionLabel = document.createElement('label');
                optionLabel.className = 'form-check-label';
                optionLabel.setAttribute('for', input.id);

                // 添加单位显示
                const unitText = option.unit ? ` ${option.unit}` : '';
                optionLabel.textContent = `${option.value}${unitText}`;

                optionDiv.appendChild(input);
                optionDiv.appendChild(optionLabel);
                optionsContainer.appendChild(optionDiv);
            });

            fieldDiv.appendChild(optionsContainer);
            container.appendChild(fieldDiv);
        });
    }

    /**
     * 处理用户选择字段事件（核心新逻辑）
     * @param {number} position - 字段位置
     * @param {string} code - 选择的编码
     * @param {string} value - 选择的值
     * @param {string|null} unit - 单位
     */
    onFieldSelect(position, code, value, unit = null) {
        console.log(`👉 用户选择字段 [${position}]: ${value} (${code})`);

        // 1. 记录用户选择
        this.userSelections[position] = { code, value, unit };

        // 2. 过滤产品列表
        this.filterProductsBySelections();

        console.log(`  → 剩余产品: ${this.remainingProducts.length} 个`);

        // 3. 检查结果并决定下一步
        if (this.remainingProducts.length === 0) {
            // 没有匹配的产品 → 错误
            console.error('❌ 没有匹配的产品！');
            this.showError('未找到匹配的产品，请检查规格选择');
            this.updateMNDisplay();

        } else if (this.remainingProducts.length === 1) {
            // 只剩一个产品 → 完成确定
            console.log('✅ 产品已完全确定！');
            this.checkAndFinalize();

        } else {
            // 还有多个产品 → 重新分析并渲染
            console.log(`🔄 继续筛选 (剩余 ${this.remainingProducts.length} 个产品)`);
            this.analyzeAndShowCodeSelection(this.remainingProducts, false);  // 非初始调用
        }
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

            // 构建产品额外信息（两栏网格布局）
            let productExtraInfo = '';

            // 第一行：品牌、单位
            const row1_col1 = product.brand ?
                `<div class="spec-field-fixed"><div class="spec-field-label">品牌:</div><div class="spec-field-value">${product.brand}</div></div>` : '';
            const row1_col2 = product.unit ?
                `<div class="spec-field-fixed"><div class="spec-field-label">单位:</div><div class="spec-field-value">${product.unit}</div></div>` : '';

            // 第二行：价格、规格说明
            const price = product.retail_price || product.market_price;
            const row2_col1 = price ?
                `<div class="spec-field-fixed"><div class="spec-field-label">价格:</div><div class="spec-field-value">¥${price}</div></div>` : '';
            const row2_col2 = product.specification ?
                `<div class="spec-field-fixed"><div class="spec-field-label">规格说明:</div><div class="spec-field-value">${product.specification}</div></div>` : '';

            // 使用两栏网格布局
            if (row1_col1 || row1_col2 || row2_col1 || row2_col2) {
                productExtraInfo = `<div class="product-extra-info-grid mt-3">
                    ${row1_col1}${row1_col2}${row2_col1}${row2_col2}
                </div>`;
            }

            mnElement.innerHTML = `
                <span class="mn-badge confirmed">
                    <i class="fas fa-check-circle"></i> MN号：${product.product_mn || '无'}
                </span>
                ${productExtraInfo}
            `;
            this.selectedProduct = product;
            this.pendingSpecs = [];

        } else if (this.remainingProducts && this.remainingProducts.length > 1) {
            // 选择中（还有多个候选产品）
            mnElement.innerHTML = `
                <span class="mn-badge partial">
                    <i class="fas fa-filter"></i> 筛选中... (剩余 ${this.remainingProducts.length} 个)
                </span>
            `;
            this.selectedProduct = null;
            this.pendingSpecs = [];

        } else if (selectionCount === 0) {
            // 完全未选择
            mnElement.innerHTML = `
                <span class="mn-badge pending">
                    <i class="fas fa-clock"></i> MN号：待确定
                </span>
            `;
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
            imgElement.src = product.image_path || '/static/images/no-image.png';
            imgElement.alt = product.product_name || '产品图片';
        }

        // 产品名称
        const nameElement = document.getElementById('configProductName');
        if (nameElement) {
            nameElement.textContent = product.product_name || '产品名称';
        }

        // 产品型号
        const modelElement = document.getElementById('configProductModel');
        if (modelElement) {
            modelElement.textContent = `型号：${product.product_model || product.model || '未知'}`;
        }

        // MN号
        const mnElement = document.getElementById('configProductMn');
        if (mnElement) {
            mnElement.innerHTML = `
                <span class="mn-badge confirmed">
                    <i class="fas fa-barcode"></i> MN号：${product.product_mn || '无'}
                </span>
            `;
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

        // 标记配置已确认
        this.configConfirmed = true;

        console.log('📋 配置已确认，切换到展示模式');
    }

    /**
     * 展示已选配置
     * @param {Array} configurations - 配置列表
     */
    showSelectedConfigurations(configurations) {
        const container = document.getElementById('selectedConfigsList');
        if (!container) return;

        container.innerHTML = '';

        if (configurations.length === 0) {
            container.innerHTML = '<div class="text-muted text-center py-2">未选择任何配置</div>';
            return;
        }

        configurations.forEach(config => {
            const item = document.createElement('div');
            item.className = 'config-item-simple';

            // 根据 relation_type 确定徽章类型
            const badgeMap = {
                'required_accessory': { type: 'relation-type-required', text: '必选' },
                'recommended': { type: 'relation-type-recommended', text: '推荐' },
                'optional_accessory': { type: 'relation-type-optional-mutual', text: '可选互斥' }
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
            container.appendChild(item);
        });

        console.log(`📦 已展示 ${configurations.length} 个配置`);
    }

    /**
     * 返回到配置选择界面
     */
    backToConfigSelection() {
        // 切换视图：显示配置选择区域，隐藏已选配置区域
        const configArea = document.getElementById('productConfigArea');
        const selectedArea = document.getElementById('selectedConfigsArea');
        const backBtn = document.getElementById('backToConfigSelection');

        if (configArea) configArea.style.display = 'block';
        if (selectedArea) selectedArea.style.display = 'none';
        if (backBtn) backBtn.style.display = 'none';

        // 重置确认状态
        this.configConfirmed = false;
        this.selectedConfigurations = [];

        console.log('🔙 返回到配置选择界面');
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
        // ⭐ 修改：准备产品数据，包含配置信息
        const productData = {
            mainProduct: {
                ...this.selectedProduct,
                pending_specs: this.pendingSpecs || []  // 传递待定规格数据
            },
            configurations: configurations  // ⭐ 新增：配置列表
        };

        // 日志输出
        if (this.pendingSpecs && this.pendingSpecs.length > 0) {
            console.log('📋 产品包含待定规格:', this.pendingSpecs);
            console.log('  - 这些规格使用了默认值（第一个选项）');
            console.log('  - pending_specs 数据已附加到产品对象中');
        }

        if (configurations.length > 0) {
            console.log(`📦 产品包含 ${configurations.length} 个配置:`, configurations);
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

        try {
            const response = await fetch(`/product-management/api/product/${productId}/relations`);
            const result = await response.json();

            if (loadingSpinner) loadingSpinner.style.display = 'none';

            if (result.success && (result.data.length > 0 || Object.keys(result.groups || {}).length > 0)) {
                console.log(`  ✓ 配置加载成功: ${result.total} 个配置`);
                this.renderConfigurations(result);
            } else {
                console.log('  ℹ️ 该产品无配置选项');
                if (noConfigMessage) noConfigMessage.style.display = 'block';
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
        const fragment = document.createDocumentFragment();
        const price = config.retail_price || 0;

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
            priceDiv.textContent = `¥${price.toFixed(2)}`;

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

        // 左侧：型号+MN
        const leftSpan = document.createElement('span');
        leftSpan.className = 'text-muted';
        leftSpan.style.fontSize = '0.9rem';
        leftSpan.textContent = modelMn;

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
            rightSpan.textContent = `¥${price.toFixed(2)}`;
        }

        row2.appendChild(leftSpan);
        row2.appendChild(rightSpan);

        // 第三行：规格说明
        const row3 = document.createElement('div');
        row3.className = 'text-muted';
        row3.style.fontSize = '0.9rem';
        row3.style.marginTop = '0.25rem';
        row3.textContent = config.specification || '-';

        fragment.appendChild(row1);
        fragment.appendChild(row2);
        fragment.appendChild(row3);

        return fragment;
    }

    /**
     * 渲染必选配置
     * @param {Array} configs - 必选配置列表
     */
    renderRequiredConfigs(configs) {
        console.log(`  📌 渲染必选配置: ${configs.length} 个`);

        const area = document.getElementById('requiredConfigArea');
        const container = document.getElementById('requiredConfigList');
        if (!area || !container) return;

        container.innerHTML = '';

        configs.forEach((config, idx) => {
            const item = document.createElement('div');
            item.className = 'config-item-simple';
            item.dataset.productId = config.related_product_id;
            item.dataset.quantity = config.default_quantity || 1;
            item.dataset.configType = 'required';

            // 存储完整的产品数据（JSON字符串）
            // API 返回的数据是扁平结构，产品字段直接在 config 对象中
            item.dataset.productData = JSON.stringify(config);

            // 使用通用模板，传递必选徽章
            // API 返回的 config 对象已经包含所有产品字段
            item.appendChild(this.createConfigItemContent(config, {
                badgeType: 'relation-type-required',
                badgeText: '必选'
            }));
            container.appendChild(item);
        });

        area.style.display = 'block';
    }

    /**
     * 渲染必选互斥组
     * @param {Object} groups - 必选互斥组对象
     */
    renderRequiredMutualGroups(groups) {
        console.log(`  ⚠️ 渲染必选互斥组: ${Object.keys(groups).length} 组`);

        const area = document.getElementById('requiredMutualConfigArea');
        const container = document.getElementById('requiredMutualConfigList');
        if (!area || !container) return;

        container.innerHTML = '';

        Object.values(groups).forEach(group => {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'mutual-group';
            groupDiv.dataset.groupId = group.group_id;
            groupDiv.dataset.isRequired = 'true';

            const groupTitle = document.createElement('div');
            groupTitle.className = 'group-title';
            groupTitle.textContent = group.group_name || `必选互斥组 ${group.group_id}`;
            groupDiv.appendChild(groupTitle);

            group.products.forEach((product, index) => {
                const price = product.retail_price || 0;

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
                radio.dataset.quantity = product.default_quantity || 1;
                radio.dataset.configType = 'required_mutual';
                radio.dataset.groupId = group.group_id;

                // 存储完整的产品数据（JSON字符串）
                // API 返回的数据是扁平结构
                radio.dataset.productData = JSON.stringify(product);

                // 设置默认选项
                if (product.is_default || index === 0) {
                    radio.checked = true;
                }

                const label = document.createElement('label');
                label.className = 'form-check-label';
                label.setAttribute('for', radio.id);

                // 使用通用模板（显示必选互斥徽章）
                // API 返回的 product 对象已经包含所有产品字段
                label.appendChild(this.createConfigItemContent(product, {
                    badgeType: 'relation-type-required-mutual',
                    badgeText: '必选互斥'
                }));

                optionDiv.appendChild(radio);
                optionDiv.appendChild(label);
                groupDiv.appendChild(optionDiv);
            });

            container.appendChild(groupDiv);
        });

        area.style.display = 'block';
    }

    /**
     * 渲染推荐配置
     * @param {Array} configs - 推荐配置列表
     */
    renderRecommendedConfigs(configs) {
        console.log(`  ✨ 渲染推荐配置: ${configs.length} 个`);

        const area = document.getElementById('recommendedConfigArea');
        const container = document.getElementById('recommendedConfigList');
        if (!area || !container) return;

        container.innerHTML = '';

        // 创建分组容器（使用与互斥组相同的样式）
        const groupDiv = document.createElement('div');
        groupDiv.className = 'mutual-group';

        configs.forEach((config, idx) => {
            const optionDiv = document.createElement('div');
            optionDiv.className = 'form-check config-option-simple';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'form-check-input';
            checkbox.id = `config-rec-${config.related_product_id}`;
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

            // 使用通用模板，传递推荐徽章
            // API 返回的 config 对象已经包含所有产品字段
            label.appendChild(this.createConfigItemContent(config, {
                badgeType: 'relation-type-recommended',
                badgeText: '推荐'
            }));

            optionDiv.appendChild(checkbox);
            optionDiv.appendChild(label);
            groupDiv.appendChild(optionDiv);
        });

        container.appendChild(groupDiv);
        area.style.display = 'block';
    }

    /**
     * 渲染推荐互斥组（可选互斥）
     * @param {Object} groups - 推荐互斥组对象
     */
    renderOptionalMutualGroups(groups) {
        console.log(`  💡 渲染可选互斥组: ${Object.keys(groups).length} 组`);

        const area = document.getElementById('optionalMutualConfigArea');
        const container = document.getElementById('optionalMutualConfigList');
        if (!area || !container) return;

        container.innerHTML = '';

        Object.values(groups).forEach(group => {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'mutual-group';
            groupDiv.dataset.groupId = group.group_id;
            groupDiv.dataset.isRequired = 'false';

            const groupTitle = document.createElement('div');
            groupTitle.className = 'group-title';
            groupTitle.textContent = group.group_name || `可选互斥组 ${group.group_id}`;
            groupDiv.appendChild(groupTitle);

            // 添加具体选项（移除"不选择"选项）
            group.products.forEach((product, index) => {
                const price = product.retail_price || 0;

                const optionDiv = document.createElement('div');
                optionDiv.className = 'form-check config-option-simple';

                const radio = document.createElement('input');
                radio.type = 'radio';
                radio.className = 'form-check-input';
                radio.name = `optional-mutual-${group.group_id}`;
                radio.id = `config-om-${group.group_id}-${product.related_product_id}`;
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

                // 使用通用模板（显示可选互斥徽章）
                // API 返回的 product 对象已经包含所有产品字段
                label.appendChild(this.createConfigItemContent(product, {
                    badgeType: 'relation-type-optional-mutual',
                    badgeText: '可选互斥'
                }));

                optionDiv.appendChild(radio);
                optionDiv.appendChild(label);
                groupDiv.appendChild(optionDiv);
            });

            container.appendChild(groupDiv);
        });

        area.style.display = 'block';
    }

    /**
     * 收集配置选择
     * @returns {Array} 配置列表
     */
    collectConfigurations() {
        const configurations = [];

        // 1. 收集必选配置（全部自动添加）
        document.querySelectorAll('#requiredConfigList .config-item-simple').forEach(item => {
            const productId = item.dataset.productId;
            const quantity = parseInt(item.dataset.quantity) || 1;

            // 从dataset读取完整的产品数据
            let productData = {};
            if (item.dataset.productData) {
                try {
                    productData = JSON.parse(item.dataset.productData);
                } catch (e) {
                    console.error('❌ 解析产品数据失败:', e);
                }
            }

            configurations.push({
                ...productData,  // 展开完整的产品数据
                product_id: parseInt(productId),
                default_quantity: quantity,
                relation_type: 'required_accessory',
                is_selected: true
            });
        });

        // 2. 收集必选互斥配置（选中的）
        document.querySelectorAll('#requiredMutualConfigList input[type="radio"]:checked').forEach(radio => {
            if (radio.value) {
                const productId = radio.dataset.productId;
                const quantity = parseInt(radio.dataset.quantity) || 1;

                // 从dataset读取完整的产品数据
                let productData = {};
                if (radio.dataset.productData) {
                    try {
                        productData = JSON.parse(radio.dataset.productData);
                    } catch (e) {
                        console.error('解析产品数据失败:', e);
                    }
                }

                configurations.push({
                    ...productData,  // 展开完整的产品数据
                    product_id: parseInt(productId),
                    default_quantity: quantity,
                    relation_type: 'required_accessory',
                    is_selected: true,
                    group_id: radio.dataset.groupId
                });
            }
        });

        // 3. 收集推荐配置（选中的复选框）
        document.querySelectorAll('#recommendedConfigList input[type="checkbox"]:checked').forEach(checkbox => {
            const productId = checkbox.dataset.productId;
            const quantity = parseInt(checkbox.dataset.quantity) || 1;

            // 从dataset读取完整的产品数据
            let productData = {};
            if (checkbox.dataset.productData) {
                try {
                    productData = JSON.parse(checkbox.dataset.productData);
                } catch (e) {
                    console.error('解析产品数据失败:', e);
                }
            }

            configurations.push({
                ...productData,  // 展开完整的产品数据
                product_id: parseInt(productId),
                default_quantity: quantity,
                relation_type: 'recommended',
                is_selected: true
            });
        });

        // 4. 收集可选互斥配置（选中的，排除"不选择"）
        document.querySelectorAll('#optionalMutualConfigList input[type="radio"]:checked').forEach(radio => {
            if (radio.value) {  // 排除value为空的"不选择"选项
                const productId = radio.dataset.productId;
                const quantity = parseInt(radio.dataset.quantity) || 1;

                // 从dataset读取完整的产品数据
                let productData = {};
                if (radio.dataset.productData) {
                    try {
                        productData = JSON.parse(radio.dataset.productData);
                    } catch (e) {
                        console.error('解析产品数据失败:', e);
                    }
                }

                configurations.push({
                    ...productData,  // 展开完整的产品数据
                    product_id: parseInt(productId),
                    default_quantity: quantity,
                    relation_type: 'optional_accessory',
                    is_selected: true,
                    group_id: radio.dataset.groupId
                });
            }
        });

        console.log(`📦 收集到 ${configurations.length} 个配置`);
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
     * 重置状态
     */
    reset() {
        this.currentProducts = [];
        this.remainingProducts = [];
        this.selectedProduct = null;
        this.userSelections = {};
        this.fixedFields = [];
        this.selectableFields = [];
        this.pendingSpecs = [];
        this.configConfirmed = false;
        this.selectedConfigurations = [];

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
            if (elem) elem.innerHTML = '';
        });

        // 重置显示状态
        const codeSelectionArea = document.getElementById('codeSelectionArea');
        const specsArea = document.getElementById('productSpecsArea');
        const configArea = document.getElementById('productConfigArea');
        const selectedArea = document.getElementById('selectedConfigsArea');
        const backBtn = document.getElementById('backToConfigSelection');

        if (codeSelectionArea) codeSelectionArea.style.display = 'none';
        if (specsArea) specsArea.style.display = 'none';
        if (configArea) configArea.style.display = 'none';
        if (selectedArea) selectedArea.style.display = 'none';
        if (backBtn) backBtn.style.display = 'none';
    }
}

// 全局实例变量
window.ProductConfigModal = ProductConfigModal;
