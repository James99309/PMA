/**
 * AT 产品挑选器 · 可复用控制器(4 级级联)
 *
 * 用法:
 *   ATProductPicker.open({
 *     replaceMode: false,
 *     onPick: function (product) { ... }
 *   });
 *   ATProductPicker.close();
 *
 * product 形态:{ id, name, model, code, spec, price, unit }
 *
 * 依赖外部 DOM(由 at_product_picker_modal 宏注入):
 *   #atProductPickerModal · #atPpCategoryList · #atPpSubcatList ·
 *   #atPpNameList · #atPpSpecList · #atPpCol4Title
 *
 * 后端 API(product blueprint):
 *   GET /api/products/categories                          → array of category 字符串
 *   GET /api/products/subcategories?category=             → {success, subcategories:[{name, display_name, count}]}
 *   GET /api/products/by-subcategory?category=&subcategory= → 详细产品列表(含 product_name/model/specification/price)
 */
(function (window) {
    const State = {
        modalId: 'atProductPickerModal',
        replaceMode: false,
        onPick: null,
        categories: [],
        catIdx: null,
        subcats: [],
        subIdx: null,
        bySubcatProducts: [], // 缓存当前子分类下的全部产品(按 product_name 分组用)
        names: [],            // [{name, count, items: []}]
        nameIdx: null,
        // 购物车模式(统一):所有业务方点 model = toggle 加入/移出,
        // 配套自动跟随,数量可调,底部 [+ 添加到明细] 一次性 emit
        // cart = Map<productId, {product, quantity, configData, configPicks, configQuantities}>
        cart: new Map(),
    };

    function el(id) { return document.getElementById(id); }
    function escapeHtml(s) {
        return String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
    }
    function loading(text) {
        return `<div class="at-dim" style="padding:16px 10px;font-size:12px;">${text || t('加载中…')}</div>`;
    }
    function errorMsg(text) {
        return `<div style="padding:16px 10px;font-size:12px;color:var(--danger);">${text || t('加载失败')}</div>`;
    }
    function emptyMsg(text) {
        return `<div class="at-dim" style="padding:16px 10px;font-size:12px;">${text || t('暂无数据')}</div>`;
    }

    function open(opts) {
        opts = opts || {};
        State.replaceMode = !!opts.replaceMode;
        State.onPick = (typeof opts.onPick === 'function') ? opts.onPick : null;
        State.currency = opts.currency || '';   // 目标货币(可选,影响价格显示+禁选)
        State.cart = new Map();
        State.catIdx = null;
        State.subIdx = null;
        State.nameIdx = null;
        // 列 4 容器永远 flex column,底部固定 confirm bar
        _setupCol4Layout();
        _renderConfirmBar();
        el('atPpCol4Title').textContent = State.replaceMode ? t('替换为') : t('具体产品');
        el('atPpSubcatList').innerHTML = emptyMsg(t('请先选择类目'));
        el('atPpNameList').innerHTML = emptyMsg(t('请先选择子分类'));
        el('atPpSpecList').innerHTML = emptyMsg(t('请先选择产品族'));
        el(State.modalId).style.display = 'flex';
        loadCategories();
    }

    function close() {
        el(State.modalId).style.display = 'none';
        // 清理底部 confirm bar(下次打开重建)
        document.getElementById('atPpConfirmBar')?.remove();
    }

    // 列 4 容器:flex column,spec list 占满剩余空间,confirm bar 居底
    function _setupCol4Layout() {
        const specList = el('atPpSpecList');
        const col4 = specList && specList.parentNode;
        if (!col4) return;
        col4.style.display = 'flex';
        col4.style.flexDirection = 'column';
        specList.style.flex = '1';
        specList.style.minHeight = '0';
        specList.style.overflowY = 'auto';
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && el(State.modalId)?.style.display === 'flex') close();
    });

    // 类目可能返回字符串 或 {name, display_name} 对象 — 归一化
    function catName(c)    { return (c && typeof c === 'object') ? (c.name || '') : String(c || ''); }
    function catDisplay(c) { return (c && typeof c === 'object') ? (c.display_name || c.name || '') : String(c || ''); }

    // ─── Col 1 · 类目 ─────────────────────────────
    function loadCategories() {
        const list = el('atPpCategoryList');
        list.innerHTML = loading();
        fetch('/api/products/categories')
            .then(r => r.json())
            .then(cats => {
                if (!Array.isArray(cats) || cats.length === 0) {
                    list.innerHTML = emptyMsg(t('无类目数据'));
                    return;
                }
                State.categories = cats;
                renderCategoryList();
            })
            .catch(() => { list.innerHTML = errorMsg(); });
    }

    function renderCategoryList() {
        const list = el('atPpCategoryList');
        list.innerHTML = State.categories.map((c, i) => {
            const active = i === State.catIdx;
            return `
                <button type="button" data-cat-idx="${i}"
                        onmouseenter="if(!this.dataset.active){this.style.background='var(--bg-hover)'}"
                        onmouseleave="if(!this.dataset.active){this.style.background='transparent'}"
                        ${active ? 'data-active="1"' : ''}
                        style="display:flex;align-items:center;gap:10px;width:100%;padding:9px 10px;
                               border-radius:6px;margin-bottom:2px;border:0;cursor:pointer;
                               background:${active ? 'var(--accent)' : 'transparent'};
                               color:${active ? '#fff' : 'var(--ink-2)'};
                               font-size:13px;font-weight:${active ? '500' : '400'};
                               text-align:left;transition:background 100ms, color 100ms;">
                    <span style="opacity:${active ? '1' : '0.6'};">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 4 7v10l8 4 8-4V7zM4 7l8 4 8-4M12 11v10"/></svg>
                    </span>
                    <span style="flex:1;">${escapeHtml(catDisplay(c))}</span>
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
                </button>`;
        }).join('');
        list.querySelectorAll('button[data-cat-idx]').forEach(btn => {
            btn.addEventListener('click', () => selectCategory(parseInt(btn.dataset.catIdx)));
        });
    }

    function selectCategory(idx) {
        State.catIdx = idx;
        State.subIdx = null;
        State.nameIdx = null;
        renderCategoryList();
        const cat = catName(State.categories[idx]);
        const subList = el('atPpSubcatList');
        subList.innerHTML = loading();
        el('atPpNameList').innerHTML = emptyMsg(t('请先选择子分类'));
        el('atPpSpecList').innerHTML = emptyMsg(t('请先选择产品族'));
        fetch(`/api/products/subcategories?category=${encodeURIComponent(cat)}`)
            .then(r => r.json())
            .then(res => {
                const subs = (res && res.subcategories) || [];
                if (!subs.length) {
                    subList.innerHTML = emptyMsg(t('该类目下暂无子分类'));
                    State.subcats = [];
                    return;
                }
                State.subcats = subs;
                renderSubcatList();
            })
            .catch(() => { subList.innerHTML = errorMsg(); });
    }

    // ─── Col 2 · 子分类 ───────────────────────────
    function renderSubcatList() {
        const list = el('atPpSubcatList');
        list.innerHTML = State.subcats.map((s, i) => {
            const active = i === State.subIdx;
            const display = s.display_name || s.name;
            return `
                <button type="button" data-sub-idx="${i}"
                        onmouseenter="if(!this.dataset.active){this.style.background='var(--bg-hover)'}"
                        onmouseleave="if(!this.dataset.active){this.style.background='transparent'}"
                        ${active ? 'data-active="1"' : ''}
                        style="display:flex;align-items:center;gap:10px;width:100%;padding:9px 10px;
                               border-radius:6px;margin-bottom:2px;border:0;cursor:pointer;text-align:left;
                               background:${active ? 'var(--bg-active)' : 'transparent'};
                               color:var(--ink-2);font-size:13px;font-weight:${active ? '500' : '400'};
                               transition:background 100ms;">
                    <div style="flex:1;min-width:0;">
                        <div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${escapeHtml(display)}</div>
                        ${s.count != null ? `<div class="at-dim" style="font-size:11px;margin-top:1px;">${s.count}${t(' 个产品')}</div>` : ''}
                    </div>
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
                </button>`;
        }).join('');
        list.querySelectorAll('button[data-sub-idx]').forEach(btn => {
            btn.addEventListener('click', () => selectSubcat(parseInt(btn.dataset.subIdx)));
        });
    }

    function selectSubcat(idx) {
        State.subIdx = idx;
        State.nameIdx = null;
        renderSubcatList();
        const cat = catName(State.categories[State.catIdx]);
        const sub = State.subcats[idx].name;
        const nameList = el('atPpNameList');
        nameList.innerHTML = loading();
        el('atPpSpecList').innerHTML = emptyMsg(t('请先选择产品族'));
        const curQs = State.currency ? `&currency=${encodeURIComponent(State.currency)}` : '';
        fetch(`/api/products/by-subcategory?category=${encodeURIComponent(cat)}&subcategory=${encodeURIComponent(sub)}${curQs}`)
            .then(r => r.json())
            .then(res => {
                // 后端返回 {success, model_groups:[{product_name, model, count, products:[...]}]}
                const groups = (res && Array.isArray(res.model_groups)) ? res.model_groups : [];
                if (!groups.length) {
                    nameList.innerHTML = emptyMsg(t('该子分类下暂无产品'));
                    State.names = [];
                    return;
                }
                // 第 3 栏「产品族 = 同 product_name 合并」,旗下放全部 model 候选
                //   原始 groups: 每条 = (product_name, model) 单一组合 → 同名多型号会有多条
                //   合并后: 每条产品族包含若干 modelOptions = [{model, products:[...]}, ...]
                const familyMap = new Map();
                groups.forEach(g => {
                    const familyName = g.product_name || g.model || '';
                    if (!familyMap.has(familyName)) {
                        familyMap.set(familyName, { name: familyName, modelOptions: [], totalCount: 0 });
                    }
                    const fam = familyMap.get(familyName);
                    fam.modelOptions.push({
                        model: g.model || '',
                        products: g.products || [],
                    });
                    fam.totalCount += (g.count || (g.products || []).length);
                });
                State.names = Array.from(familyMap.values());
                renderNameList();
            })
            .catch(() => { nameList.innerHTML = errorMsg(); });
    }

    // ─── Col 3 · 产品族 ───────────────────────────
    function renderNameList() {
        const list = el('atPpNameList');
        if (!State.names.length) {
            list.innerHTML = emptyMsg(t('该子分类下暂无产品'));
            return;
        }
        list.innerHTML = State.names.map((n, i) => {
            const active = i === State.nameIdx;
            return `
                <button type="button" data-name-idx="${i}"
                        onmouseenter="if(!this.dataset.active){this.style.background='var(--bg-hover)'}"
                        onmouseleave="if(!this.dataset.active){this.style.background='transparent'}"
                        ${active ? 'data-active="1"' : ''}
                        style="display:flex;align-items:center;gap:10px;width:100%;padding:9px 10px;
                               border-radius:6px;margin-bottom:2px;cursor:pointer;text-align:left;
                               background:${active ? 'var(--bg-active)' : 'transparent'};
                               color:var(--ink-2);font-size:13px;font-weight:${active ? '500' : '400'};
                               border:1px solid ${active ? 'var(--line-2)' : 'transparent'};
                               transition:background 100ms;">
                    <div style="flex:1;min-width:0;">
                        <div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${escapeHtml(n.name)}</div>
                        <div class="at-dim at-mono" style="font-size:11px;margin-top:1px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${(n.modelOptions || []).length}${t(' 型号 · ')}${n.totalCount || 0}${t(' 个')}</div>
                    </div>
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
                </button>`;
        }).join('');
        list.querySelectorAll('button[data-name-idx]').forEach(btn => {
            btn.addEventListener('click', () => selectName(parseInt(btn.dataset.nameIdx)));
        });
    }

    // 货币符号映射
    const _CUR_SYMBOL = { CNY:'¥', USD:'$', SGD:'S$', MYR:'RM', IDR:'Rp', THB:'฿', EUR:'€', GBP:'£', JPY:'¥', HKD:'HK$' };
    function _currencySym(code) { return _CUR_SYMBOL[(code||'').toUpperCase()] || (code ? code + ' ' : '¥'); }

    // ─── 规格差异高亮 ─────────────────────────────────
    //   把 spec 按 ", " 切 segment(每段形如 "label: value")
    //   收集所有产品的 label→value 集合,值多于 1 个的 label = 差异 label
    function _calcSpecDiffLabels(specsArr) {
        const labelValues = {};
        specsArr.forEach(spec => {
            (spec || '').split(/,\s*/).forEach(seg => {
                const idx = seg.indexOf(':');
                if (idx < 0) return;
                const label = seg.slice(0, idx).trim();
                const value = seg.slice(idx + 1).trim();
                if (!label) return;
                if (!labelValues[label]) labelValues[label] = new Set();
                labelValues[label].add(value);
            });
        });
        const diff = new Set();
        Object.entries(labelValues).forEach(([label, values]) => {
            if (values.size > 1) diff.add(label);
        });
        return diff;
    }
    // 渲染 spec,差异 segment 用反色高亮
    function _renderSpecWithDiff(spec, diffLabels) {
        if (!spec) return '';
        return (spec || '').split(/,\s*/).map(seg => {
            const idx = seg.indexOf(':');
            if (idx < 0) return escapeHtml(seg);
            const label = seg.slice(0, idx).trim();
            if (diffLabels && diffLabels.has(label)) {
                return `<mark style="background:rgba(229,156,75,0.20);color:var(--ink);padding:0 3px;border-radius:3px;font-weight:500;">${escapeHtml(seg)}</mark>`;
            }
            return escapeHtml(seg);
        }).join(', ');
    }

    function selectName(idx) {
        State.nameIdx = idx;
        renderNameList();
        // 把所有 modelOptions 下的 products 平铺,作为列 4 候选(每个 product = 一张卡片)
        const family = State.names[idx] || {};
        const items = [];
        (family.modelOptions || []).forEach(mo => {
            (mo.products || []).forEach(p => {
                items.push({ ...p, _modelGroupName: mo.model });
            });
        });
        const list = el('atPpSpecList');
        if (!items.length) {
            list.innerHTML = emptyMsg(t('暂无产品'));
            return;
        }
        const targetCur = State.currency || '';
        const curSym = _currencySym(targetCur || items[0].currency || 'CNY');
        // 同产品族下规格差异 — 用于高亮卡片 spec 中字段值不同的段
        const diffLabels = _calcSpecDiffLabels(items.map(p => p.specification || p.product_spec || ''));

        list.innerHTML = items.map((p, i) => {
            const _name  = p.product_name || p.name || '';
            const _model = p.model || p.product_model || '';
            const _spec  = p.specification || p.product_spec || '';
            const _code  = p.product_mn || p.code || '';

            // 价格逻辑:
            //  - 若 API 返回 price_for_currency != null → 用它(targetCur 下的实际价)
            //  - 若 price_for_currency === null → 此货币下无价,显示"—",禁选
            //  - 若没有 target currency → 用 retail_price(向后兼容)
            let _price = null, _disabled = false, _priceSource = 'native';
            if (targetCur) {
                _price = p.price_for_currency;
                _priceSource = p.price_source || 'none';
                if (_price === null || _price === undefined) {
                    _disabled = true;
                }
            } else {
                _price = Number(p.retail_price || p.market_price || p.price || 0);
            }

            const priceHtml = _disabled
                ? `<div class="at-mono at-dim" style="font-size:13px;white-space:nowrap;">—<div style="font-size:10px;font-weight:400;margin-top:1px;">${t('无 ')}${escapeHtml(targetCur)}${t(' 价')}</div></div>`
                : `<div class="at-mono at-tab-num" style="font-size:13.5px;font-weight:500;color:var(--accent);white-space:nowrap;">${curSym}${(_price || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}${_priceSource === 'region' ? `<span class="at-dim" style="font-size:9.5px;margin-left:4px;font-weight:400;">${t('区域价')}</span>` : ''}</div>`;

            return `
                <button type="button" data-spec-idx="${i}" data-spec-id="${p.id}" data-disabled="${_disabled ? '1' : ''}"
                        ${_disabled ? 'disabled' : ''}
                        ${_disabled ? '' : `onmouseenter="if(!this.dataset.inCart){this.style.background='var(--accent-tint)';this.style.borderColor='var(--accent-soft)';}" onmouseleave="if(!this.dataset.inCart){this.style.background='var(--bg-elev)';this.style.borderColor='var(--line-soft)';}"`}
                        style="width:100%;padding:12px 12px;border-radius:8px;margin-bottom:4px;
                               border:1px solid var(--line-soft);background:var(--bg-elev);
                               text-align:left;transition:background 100ms, border-color 100ms;
                               ${_disabled ? 'opacity:0.55;cursor:not-allowed;' : 'cursor:pointer;'}">
                    <div style="display:flex;align-items:baseline;justify-content:space-between;gap:12px;">
                        <div style="min-width:0;flex:1;">
                            <div style="font-size:13.5px;font-weight:500;color:var(--ink);">${escapeHtml(_name)}</div>
                            <div class="at-mono" style="font-size:12px;color:var(--ink-3);margin-top:2px;">${escapeHtml(_model || '-')}${_code ? ' · ' + escapeHtml(_code) : ''}</div>
                        </div>
                        <div style="display:flex;align-items:center;gap:8px;flex-shrink:0;">
                            <div data-main-qty-wrap style="display:none;align-items:center;gap:5px;">
                                <input type="number" min="1" value="1" data-main-qty-input
                                       onclick="event.stopPropagation();"
                                       style="width:54px;height:26px;padding:0 4px;text-align:center;
                                              border:1px solid var(--line-2);border-radius:5px;background:var(--bg-elev);
                                              font-family:var(--font-mono);font-weight:500;font-size:12.5px;
                                              color:var(--ink);outline:none;">
                                <span class="at-dim" style="font-size:11px;">${escapeHtml(p.unit || t('套'))}</span>
                            </div>
                            ${priceHtml}
                        </div>
                    </div>
                    ${_spec ? `<div class="at-dim" style="font-size:11.5px;margin-top:6px;line-height:1.45;">${_renderSpecWithDiff(_spec, diffLabels)}</div>` : ''}
                </button>`;
        }).join('');
        list.querySelectorAll('button[data-spec-idx]').forEach(btn => {
            if (btn.dataset.disabled) return;  // 无价产品禁选
            btn.addEventListener('click', () => pickSpec(items[parseInt(btn.dataset.specIdx)], State.names[idx].name));
        });
        // 切换 family 后:已选卡片重新 highlight + 渲染底部 confirm bar
        _rehydrateCartHighlights();
        _renderConfirmBar();
    }

    // ─── 选中 model 卡片 — 统一购物车模式 ─────────────────────
    //   toggle 加入/移出购物车,不关闭;必选配套自动跟随;
    //   底部 [+ 添加到明细] 一次性 emit { items:[{product, configurations, quantity}] }
    function pickSpec(p, fallbackName) {
        // 价格选取:有 target_currency 时优先用 price_for_currency,否则 retail_price
        let pickedPrice = null;
        if (State.currency && p.price_for_currency != null) {
            pickedPrice = Number(p.price_for_currency);
        } else if (!State.currency) {
            pickedPrice = Number(p.retail_price || p.market_price || p.price || 0);
        } else {
            pickedPrice = 0;  // target currency 下无价(理论上禁选,这里只是兜底)
        }
        const product = {
            id:    p.id,
            name:  p.product_name || p.name || fallbackName,
            model: p.model || p.product_model || '',
            code:  p.product_mn || p.code || '',
            spec:  p.specification || p.product_spec || '',
            brand: p.brand || p.product_brand || '',
            price: pickedPrice,
            unit:  p.unit || t('套'),
            _raw:  p,
        };
        // toggle cart:已存在 → 移出 + 收 panel;否则 → 加入 + 展开 panel(loading,异步 fetch 配套)
        if (State.cart.has(p.id)) {
            State.cart.delete(p.id);
            _markCartCard(p.id, false);
            document.getElementById(`atPpConfigPanel-${p.id}`)?.remove();
            _updateConfirmBar();
        } else {
            const entry = {
                product,
                quantity: 1,
                configData: null,
                configPicks: { required: new Set(), recommended: new Set(), mutualPicks: {} },
                configQuantities: {},  // {configId: qty} 每个配套独立数量
            };
            State.cart.set(p.id, entry);
            _markCartCard(p.id, true);
            _renderCartPanel(p.id);
            _updateConfirmBar();
            _loadRelatedForCart(p.id);
        }
    }

    function _markCartCard(productId, inCart) {
        document.querySelectorAll(`#atPpSpecList button[data-spec-id="${productId}"]`).forEach(btn => {
            btn.dataset.inCart = inCart ? '1' : '';
            btn.style.background  = inCart ? 'var(--accent-tint)' : 'var(--bg-elev)';
            btn.style.borderColor = inCart ? 'var(--accent)' : 'var(--line-soft)';
            btn.style.borderWidth = inCart ? '2px' : '1px';
            // 切换主产品数量控件显示
            const qtyWrap = btn.querySelector('[data-main-qty-wrap]');
            if (qtyWrap) qtyWrap.style.display = inCart ? 'inline-flex' : 'none';
            // 绑定 qty input(只绑一次)
            const qtyInput = btn.querySelector('[data-main-qty-input]');
            if (inCart && qtyInput && !qtyInput.dataset.bound) {
                qtyInput.dataset.bound = '1';
                const entry = State.cart.get(productId);
                if (entry) qtyInput.value = entry.quantity || 1;
                qtyInput.addEventListener('input', () => {
                    const n = Math.max(1, parseInt(qtyInput.value) || 1);
                    const e2 = State.cart.get(productId);
                    if (e2) { e2.quantity = n; _updateConfirmBar(); }
                });
            }
        });
    }
    // 切换 family / subcat 重渲染列 4 后,把 cart 中卡片重新标 highlight + panel
    function _rehydrateCartHighlights() {
        State.cart.forEach((entry, pid) => {
            _markCartCard(pid, true);
            // 该 cart 产品的卡片若在当前列表 → 重新展开它的配套面板
            const card = document.querySelector(`#atPpSpecList button[data-spec-id="${pid}"]`);
            if (card) _renderCartPanel(pid);
        });
    }

    // fetch 配套 → 默认勾必选 → 重渲染该 cart 项 panel
    function _loadRelatedForCart(productId) {
        fetch(`/api/product/${productId}/relations`)
            .then(r => r.json())
            .then(res => {
                const entry = State.cart.get(productId);
                if (!entry) return;
                const required = [], recommended = [];
                const requiredMutualGroups = {}, optionalMutualGroups = {};
                if (res && res.success) {
                    (res.data || []).forEach(it => {
                        if (it.relation_type === 'required_accessory') required.push(it);
                        else if (it.relation_type === 'recommended') recommended.push(it);
                    });
                    Object.values(res.groups || {}).forEach(g => {
                        if (g.is_required) requiredMutualGroups[g.group_id] = g;
                        else optionalMutualGroups[g.group_id] = g;
                    });
                }
                entry.configData = { required, recommended, requiredMutualGroups, optionalMutualGroups };
                // 默认勾选所有必选配套
                required.forEach(it => entry.configPicks.required.add(it.id));
                _renderCartPanel(productId);
                _updateConfirmBar();
            })
            .catch(() => {
                const entry = State.cart.get(productId);
                if (!entry) return;
                entry.configData = { required: [], recommended: [], requiredMutualGroups: {}, optionalMutualGroups: {} };
                _renderCartPanel(productId);
            });
    }

    // 渲染某 cart entry 的配套面板,插到对应 model 卡片下方;复用 _renderConfigItem/_renderMutualGroup
    function _renderCartPanel(productId) {
        document.getElementById(`atPpConfigPanel-${productId}`)?.remove();
        const card = document.querySelector(`#atPpSpecList button[data-spec-id="${productId}"]`);
        const entry = State.cart.get(productId);
        if (!card || !entry) return;
        const panel = document.createElement('div');
        panel.id = `atPpConfigPanel-${productId}`;
        panel.style.cssText = 'margin:6px 4px 12px;padding:10px 12px;border-left:2px solid var(--accent);background:var(--bg-page);border-radius:0 6px 6px 0;';
        card.insertAdjacentElement('afterend', panel);

        const data = entry.configData;
        if (!data) { panel.innerHTML = loading(t('加载配套中…')); return; }
        const blocks = [];
        if (data.required && data.required.length) {
            blocks.push(`<div style="margin-bottom:12px;">
                <div style="font-size:11px;font-weight:500;letter-spacing:0.06em;text-transform:uppercase;color:var(--ink-3);margin-bottom:6px;">${t('必选配套 · ')}${data.required.length}</div>
                ${data.required.map(it => _renderConfigItem(it, 'required', { picksSet: entry.configPicks.required, cfgQuantities: entry.configQuantities })).join('')}
            </div>`);
        }
        Object.values(data.requiredMutualGroups || {}).forEach(g => {
            blocks.push(_renderMutualGroup(g, true, entry.configPicks.mutualPicks, entry.configQuantities));
        });
        if (data.recommended && data.recommended.length) {
            blocks.push(`<div style="margin-bottom:12px;">
                <div style="font-size:11px;font-weight:500;letter-spacing:0.06em;text-transform:uppercase;color:var(--ink-3);margin-bottom:6px;">${t('推荐配套 · ')}${data.recommended.length}</div>
                ${data.recommended.map(it => _renderConfigItem(it, 'recommended', { picksSet: entry.configPicks.recommended, cfgQuantities: entry.configQuantities })).join('')}
            </div>`);
        }
        Object.values(data.optionalMutualGroups || {}).forEach(g => {
            blocks.push(_renderMutualGroup(g, false, entry.configPicks.mutualPicks, entry.configQuantities));
        });
        // 无配套不显示 panel
        if (!blocks.length) { panel.remove(); return; }
        panel.innerHTML = blocks.join('');
        _bindConfigInteractions(panel, entry);
    }

    // 把选中的 model 卡片 highlight,其他卡片回常态
    function _markSelectedCard(productId) {
        const list = el('atPpSpecList');
        list.querySelectorAll('button[data-spec-id]').forEach(btn => {
            const isSelected = parseInt(btn.dataset.specId) === productId;
            btn.dataset.selected = isSelected ? '1' : '';
            btn.style.background   = isSelected ? 'var(--accent-tint)' : 'var(--bg-elev)';
            btn.style.borderColor  = isSelected ? 'var(--accent)' : 'var(--line-soft)';
        });
    }

    // ─── M5 · 配套面板(必选/推荐/互斥)— 已转购物车模式不再使用 — 保留供 future 复用 ──
    function _renderConfigPanel_unused() {
        // 移除可能的旧 panel(切卡片时位置变,需重新插入);bar 保留在 col4 底部不动
        document.getElementById('atPpConfigPanel')?.remove();
        const selectedId = State.selectedSpec && State.selectedSpec.id;
        const selectedCard = selectedId != null
            ? document.querySelector(`button[data-spec-id="${selectedId}"]`)
            : null;
        if (!selectedCard) return;
        const panel = document.createElement('div');
        panel.id = 'atPpConfigPanel';
        panel.style.cssText = 'margin:6px 4px 12px;padding:10px 12px;border-left:2px solid var(--accent);background:var(--bg-page);border-radius:0 6px 6px 0;';
        selectedCard.insertAdjacentElement('afterend', panel);
        const data = State.configData;
        if (State.configLoading) { panel.innerHTML = loading(t('加载配套中…')); return; }
        if (!data) {
            panel.innerHTML = `<div class="at-dim" style="padding:6px 10px;font-size:11.5px;">${t('已选中 「')}${escapeHtml(State.selectedSpec.name)}${t('」')}</div>`;
            _renderConfirmBar();
            return;
        }
        const blocks = [];
        // 必选配套
        if (data.required && data.required.length) {
            blocks.push(`<div style="margin-bottom:12px;">
                <div style="font-size:11px;font-weight:500;letter-spacing:0.06em;text-transform:uppercase;color:var(--ink-3);margin-bottom:6px;">${t('必选配套 · ')}${data.required.length}</div>
                ${data.required.map(it => _renderConfigItem(it, 'required')).join('')}
            </div>`);
        }
        // 必选互斥组(每组 N 选 1,必须选)
        const reqGroups = data.requiredMutualGroups || {};
        Object.values(reqGroups).forEach(g => {
            blocks.push(_renderMutualGroup(g, true));
        });
        // 推荐配套
        if (data.recommended && data.recommended.length) {
            blocks.push(`<div style="margin-bottom:12px;">
                <div style="font-size:11px;font-weight:500;letter-spacing:0.06em;text-transform:uppercase;color:var(--ink-3);margin-bottom:6px;">${t('推荐配套 · ')}${data.recommended.length}</div>
                ${data.recommended.map(it => _renderConfigItem(it, 'recommended')).join('')}
            </div>`);
        }
        // 可选互斥组
        Object.values(data.optionalMutualGroups || {}).forEach(g => {
            blocks.push(_renderMutualGroup(g, false));
        });
        if (!blocks.length) {
            panel.innerHTML = `<div class="at-dim" style="padding:6px 10px;font-size:11.5px;">${t('该产品无配套')}</div>`;
        } else {
            panel.innerHTML = blocks.join('');
        }
        _bindConfigInteractions();
        _renderConfirmBar();
    }

    // 配套卡片(必选 / 推荐 / 互斥)— 跟主产品 model 卡片同样详细
    //   opts.picksSet         · 普通 checkbox 用此 Set 判断是否勾选
    //   opts.radio            · 互斥组用 radio
    //   opts.radioName        · radio 同名分组
    //   opts.mutualGroupId, opts.mutualPicks · 互斥组判断 picked
    //   opts.cfgQuantities    · 配套数量 map(每个配套独立 qty)
    //   opts.cfgUnit          · 配套单位(显示用)
    function _renderConfigItem(it, kind, opts) {
        opts = opts || {};
        const checked = opts.radio
            ? (opts.mutualPicks && opts.mutualPicks[opts.mutualGroupId] === it.id)
            : (opts.picksSet ? opts.picksSet.has(it.id) : false);
        const isRadio = !!opts.radio;
        const radioName = opts.radioName || '';
        const cfgQty = (opts.cfgQuantities && opts.cfgQuantities[it.id]) || 1;
        const cfgUnit = it.unit || t('套');
        const price = Number(it.retail_price || it.market_price || it.price || 0);
        const curSym = _currencySym(State.currency || it.currency || 'CNY');
        const _spec  = it.specification || it.product_spec || it.spec || '';
        const _code  = it.product_mn || it.code || '';
        return `
            <label data-config-id="${it.id}" ${kind ? `data-config-kind="${kind}"` : ''} ${isRadio ? `data-mutual-gid="${opts.mutualGroupId}"` : ''}
                   style="display:block;width:100%;padding:12px 12px;border-radius:8px;
                          border:1px solid ${checked ? 'var(--accent)' : 'var(--line-soft)'};
                          background:${checked ? 'var(--accent-tint)' : 'var(--bg-elev)'};
                          margin-bottom:4px;cursor:pointer;transition:background 100ms, border-color 100ms;">
                <div style="display:flex;align-items:flex-start;gap:10px;">
                    <input type="${isRadio ? 'radio' : 'checkbox'}" ${isRadio ? `name="${radioName}"` : ''} ${checked ? 'checked' : ''}
                           style="width:14px;height:14px;accent-color:var(--accent);flex-shrink:0;margin-top:2px;">
                    <div style="flex:1;min-width:0;">
                        <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;">
                            <div style="min-width:0;flex:1;">
                                <div style="font-size:13.5px;font-weight:500;color:var(--ink);">${escapeHtml(it.name || it.product_name || '')}</div>
                                <div class="at-mono" style="font-size:12px;color:var(--ink-3);margin-top:2px;">${escapeHtml(it.model || it.product_model || '-')}${_code ? ' · ' + escapeHtml(_code) : ''}</div>
                            </div>
                            <div style="display:flex;align-items:center;gap:8px;flex-shrink:0;">
                                <div data-cfg-qty-wrap style="display:${checked ? 'inline-flex' : 'none'};align-items:center;gap:5px;">
                                    <input type="number" min="1" value="${cfgQty}" data-cfg-qty-input
                                           onclick="event.stopPropagation();"
                                           style="width:50px;height:24px;padding:0 4px;text-align:center;
                                                  border:1px solid var(--line-2);border-radius:5px;background:var(--bg-elev);
                                                  font-family:var(--font-mono);font-weight:500;font-size:12px;
                                                  color:var(--ink);outline:none;">
                                    <span class="at-dim" style="font-size:11px;">${escapeHtml(cfgUnit)}</span>
                                </div>
                                <div class="at-mono at-tab-num" style="font-size:13px;font-weight:500;color:var(--accent);white-space:nowrap;">${curSym}${price.toLocaleString('en-US', {minimumFractionDigits: 2})}</div>
                            </div>
                        </div>
                        ${_spec ? `<div class="at-dim" style="font-size:11.5px;margin-top:6px;line-height:1.45;">${escapeHtml(_spec)}</div>` : ''}
                    </div>
                </div>
            </label>`;
    }

    function _renderMutualGroup(group, isRequired, mutualPicks, cfgQuantities) {
        const gid = group.group_id;
        const items = group.items || group.products || [];
        return `<div style="margin-bottom:12px;">
            <div style="font-size:11px;font-weight:500;letter-spacing:0.06em;text-transform:uppercase;color:var(--ink-3);margin-bottom:6px;">
                ${isRequired ? t('必选互斥') : t('可选互斥')} · ${escapeHtml(group.group_name || gid)}${t(' · N 选 1')}
            </div>
            ${items.map(it => _renderConfigItem(it, null, {
                radio: true,
                radioName: 'atPpMutual_' + gid,
                mutualGroupId: gid,
                mutualPicks: mutualPicks,
                cfgQuantities: cfgQuantities,
            })).join('')}
        </div>`;
    }

    // change 事件 + 局部样式更新(整 panel 不重渲染,避免点击中断 / scroll 跳)
    function _bindConfigInteractions(panel, entry) {
        panel.querySelectorAll('label[data-config-id]').forEach(lab => {
            const input = lab.querySelector('input:not([data-cfg-qty-input])');
            const qtyWrap = lab.querySelector('[data-cfg-qty-wrap]');
            input.addEventListener('change', () => {
                const id = parseInt(lab.dataset.configId);
                if (lab.dataset.mutualGid) {
                    const gid = lab.dataset.mutualGid;
                    entry.configPicks.mutualPicks[gid] = id;
                    panel.querySelectorAll(`label[data-mutual-gid="${gid}"]`).forEach(l => {
                        const on = (l === lab);
                        _restyleConfigCard(l, on);
                        const qw = l.querySelector('[data-cfg-qty-wrap]');
                        if (qw) qw.style.display = on ? 'inline-flex' : 'none';
                    });
                } else {
                    const kind = lab.dataset.configKind;
                    const set  = entry.configPicks[kind];
                    if (input.checked) set.add(id); else set.delete(id);
                    _restyleConfigCard(lab, input.checked);
                    if (qtyWrap) qtyWrap.style.display = input.checked ? 'inline-flex' : 'none';
                }
                _updateConfirmBar();
            });
            // 配套 qty input(仅 number input,无 +/- 按钮,用浏览器原生上下 spinner)
            const qtyInput = lab.querySelector('input[data-cfg-qty-input]');
            if (!qtyInput) return;
            const cfgId = parseInt(lab.dataset.configId);
            qtyInput.addEventListener('input', () => {
                const n = Math.max(1, parseInt(qtyInput.value) || 1);
                entry.configQuantities[cfgId] = n;
                _updateConfirmBar();
            });
        });
    }

    function _restyleConfigCard(lab, on) {
        lab.style.borderColor = on ? 'var(--accent)' : 'var(--line-soft)';
        lab.style.background  = on ? 'var(--accent-tint)' : 'var(--bg-elev)';
    }

    // confirm bar 挂到 col4 容器底部(spec list 的 sibling) — 显示购物车汇总
    function _renderConfirmBar() {
        let bar = document.getElementById('atPpConfirmBar');
        const col4 = el('atPpSpecList').parentNode;
        if (!bar) {
            bar = document.createElement('div');
            bar.id = 'atPpConfirmBar';
            bar.style.cssText = 'flex-shrink:0;display:flex;align-items:center;gap:8px;padding:10px 0 0;border-top:1px solid var(--line);margin-top:8px;';
            bar.innerHTML = `
                <div id="atPpCartSummary" style="flex:1;font-size:12px;color:var(--ink-3);">${t('未选产品')}</div>
                <button type="button" id="atPpCancelBtn"
                        style="height:32px;padding:0 12px;border-radius:6px;border:1px solid var(--line-2);
                               background:var(--bg-elev);color:var(--ink);font-size:12.5px;cursor:pointer;">${t('取消')}</button>
                <button type="button" id="atPpConfirmBtn"
                        style="height:32px;padding:0 14px;border-radius:6px;border:0;
                               background:var(--accent);color:#fff;font-size:12.5px;font-weight:500;cursor:pointer;">${t('+ 添加到明细')}</button>`;
            col4.appendChild(bar);
            bar.querySelector('#atPpCancelBtn').addEventListener('click', close);
            bar.querySelector('#atPpConfirmBtn').addEventListener('click', _emitCart);
        }
        _updateConfirmBar();
    }
    function _updateConfirmBar() {
        const btn = document.getElementById('atPpConfirmBtn');
        const summary = document.getElementById('atPpCartSummary');
        if (!btn || !summary) return;
        const n = State.cart.size;
        let totalItems = 0, totalAmount = 0, allRequiredMutualPicked = true;
        State.cart.forEach(entry => {
            const qty = entry.quantity || 1;
            totalItems += 1;
            totalAmount += (entry.product.price || 0) * qty;
            const cfg = entry.configData || {};
            const findById = (arr, id) => (arr || []).find(x => x.id === id);
            // 配套各自数量(独立于主产品 qty)
            const cfgQ = (cfgId) => entry.configQuantities[cfgId] || 1;
            entry.configPicks.required.forEach(id => {
                const it = findById(cfg.required, id);
                if (it) { totalItems++; totalAmount += Number(it.retail_price || 0) * cfgQ(id); }
            });
            entry.configPicks.recommended.forEach(id => {
                const it = findById(cfg.recommended, id);
                if (it) { totalItems++; totalAmount += Number(it.retail_price || 0) * cfgQ(id); }
            });
            Object.entries(entry.configPicks.mutualPicks || {}).forEach(([gid, id]) => {
                const grp = (cfg.requiredMutualGroups || {})[gid] || (cfg.optionalMutualGroups || {})[gid];
                if (!grp) return;
                const it = (grp.items || grp.products || []).find(x => x.id === id);
                if (it) { totalItems++; totalAmount += Number(it.retail_price || 0) * cfgQ(id); }
            });
            // 必选互斥组校验:每组都必须有 pick
            Object.keys(cfg.requiredMutualGroups || {}).forEach(gid => {
                if (!entry.configPicks.mutualPicks[gid]) allRequiredMutualPicked = false;
            });
        });
        const curSym = _currencySym(State.currency || 'CNY');
        summary.innerHTML = n > 0
            ? `${t('已选 ')}<span class="at-mono at-tab-num" style="font-weight:500;color:var(--ink);">${n}</span>${t(' 个主产品 · 共 ')}<span class="at-mono at-tab-num">${totalItems}</span>${t(' 条 · ')}<span class="at-mono at-tab-num" style="color:var(--accent);font-weight:500;">${curSym}${totalAmount.toLocaleString('en-US', {minimumFractionDigits:2})}</span>`
            : t('未选产品');
        const canConfirm = n > 0 && allRequiredMutualPicked;
        btn.disabled = !canConfirm;
        btn.style.opacity = canConfirm ? '1' : '0.5';
        btn.style.cursor  = canConfirm ? 'pointer' : 'not-allowed';
        btn.title = (n > 0 && !allRequiredMutualPicked) ? t('部分必选互斥组未选择') : '';
    }

    function _emitCart() {
        const items = [];
        State.cart.forEach(entry => {
            const qty = entry.quantity || 1;
            const configs = [];
            const cfg = entry.configData || {};
            const findById = (arr, id) => (arr || []).find(x => x.id === id);
            // 配套各自数量(独立)
            const pushCfg = (it) => {
                if (!it) return;
                const cfgQ = entry.configQuantities[it.id] || 1;
                configs.push({ ..._toCfgPayload(it), quantity: cfgQ });
            };
            entry.configPicks.required.forEach(id => pushCfg(findById(cfg.required, id)));
            entry.configPicks.recommended.forEach(id => pushCfg(findById(cfg.recommended, id)));
            Object.entries(entry.configPicks.mutualPicks || {}).forEach(([gid, pickedId]) => {
                const grp = (cfg.requiredMutualGroups || {})[gid] || (cfg.optionalMutualGroups || {})[gid];
                if (!grp) return;
                pushCfg((grp.items || grp.products || []).find(x => x.id === pickedId));
            });
            items.push({
                product: { ...entry.product, quantity: qty },
                configurations: configs,
            });
        });
        if (State.onPick) {
            try { State.onPick({ items }); }
            catch (e) { console.error('[ATProductPicker] onPick error:', e); }
        }
        close();
    }

    function _loadRelatedProducts(productId) {
        State.configLoading = true;
        _renderConfigPanel();
        fetch(`/api/product/${productId}/relations`)
            .then(r => r.json())
            .then(res => {
                State.configLoading = false;
                const required = [], recommended = [];
                const requiredMutualGroups = {}, optionalMutualGroups = {};
                if (res && res.success) {
                    (res.data || []).forEach(it => {
                        if (it.relation_type === 'required_accessory') required.push(it);
                        else if (it.relation_type === 'recommended') recommended.push(it);
                    });
                    Object.values(res.groups || {}).forEach(g => {
                        if (g.is_required) requiredMutualGroups[g.group_id] = g;
                        else optionalMutualGroups[g.group_id] = g;
                    });
                }
                State.configData = { required, recommended, requiredMutualGroups, optionalMutualGroups };
                // 默认勾选所有"必选配套"
                required.forEach(it => State.configPicks.required.add(it.id));
                _renderConfigPanel();
            })
            .catch(() => {
                State.configLoading = false;
                State.configData = { required: [], recommended: [], requiredMutualGroups: {}, optionalMutualGroups: {} };
                _renderConfigPanel();
            });
    }

    // 收集所有选中配套 + 主产品,emit onPick({product, configurations})
    function _emitWithConfigurations() {
        const product = State.selectedSpec;
        const cfg = State.configData || {};
        const picks = State.configPicks;
        const configurations = [];
        const findItem = (id) => {
            for (const arr of [cfg.required, cfg.recommended]) {
                if (!arr) continue;
                const f = arr.find(x => x.id === id);
                if (f) return f;
            }
            for (const g of [...Object.values(cfg.requiredMutualGroups || {}),
                             ...Object.values(cfg.optionalMutualGroups || {})]) {
                const f = (g.items || g.products || []).find(x => x.id === id);
                if (f) return f;
            }
            return null;
        };
        picks.required.forEach(id => { const it = findItem(id); if (it) configurations.push(_toCfgPayload(it)); });
        picks.recommended.forEach(id => { const it = findItem(id); if (it) configurations.push(_toCfgPayload(it)); });
        Object.values(picks.mutualPicks).forEach(id => { const it = findItem(id); if (it) configurations.push(_toCfgPayload(it)); });

        if (State.onPick) {
            try { State.onPick({ product, configurations }); }
            catch (e) { console.error('[ATProductPicker] onPick error:', e); }
        }
        close();
    }

    function _toCfgPayload(it) {
        return {
            id:    it.id,
            name:  it.name || it.product_name || '',
            model: it.model || it.product_model || '',
            code:  it.product_mn || '',
            spec:  it.specification || it.product_spec || '',
            brand: it.brand || it.product_brand || '',
            price: Number(it.retail_price || it.market_price || it.price || 0),
            unit:  it.unit || t('套'),
        };
    }

    window.ATProductPicker = { open, close };
})(window);
