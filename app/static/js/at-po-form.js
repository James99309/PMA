/**
 * AT 采购订单表单控制器(创建 / 编辑 双模式共享)
 *
 * 依赖:ATItemTable / ATToast / ATConfirm 已先注入
 *
 * 页面需要的入口函数:
 *   atOpenOrderForm(mode='create', options={})  打开模态(create:清空,edit:预填明细)
 *   atSubmitOrderForm(mode, orderId)            提交(create→POST /api/create,edit→PUT /api/<id>/update)
 *   atUpdateOrderSubmitBtn()                    校验按钮可点性
 *
 * options.items: edit 模式下预填的明细数组(ATItemTable 格式)
 * options.modalId: 自定义模态 id,默认按 mode 推断
 *   create → atOrderCreateModal
 *   edit   → atOrderEditModal
 */
(function () {
    const MODAL_ID = { create: 'atOrderCreateModal', edit: 'atOrderEditModal' };

    function modalIdFor(mode, options) {
        return (options && options.modalId) || MODAL_ID[mode] || MODAL_ID.create;
    }

    // ─── 校验按钮可点性 ───
    // create:需要供应商 + 至少 1 条明细
    // edit:已有完整数据,只要不空就行(明细可空,后端不强制?这里保持 create 同等校验)
    function atUpdateOrderSubmitBtn() {
        const btn = document.getElementById('atOrderSubmitBtn');
        if (!btn) return;
        const supplierSel = document.getElementById('atOrderSupplier'); // edit 模式下不存在
        const hasSupplier = supplierSel ? !!supplierSel.value : true;   // edit 模式视为已选
        const ok = hasSupplier && !ATItemTable.isEmpty();
        btn.disabled = !ok;
        btn.style.opacity = ok ? '1' : '0.5';
        btn.style.cursor = ok ? 'pointer' : 'not-allowed';
    }
    window.atUpdateOrderSubmitBtn = atUpdateOrderSubmitBtn;

    // ─── 打开模态 ───
    function atOpenOrderForm(mode, options) {
        mode = mode || 'create';
        options = options || {};
        const mid = modalIdFor(mode, options);

        if (mode === 'create') {
            // 重置基本信息
            ['atOrderSupplier','atOrderCategory','atOrderIncoterm','atOrderShipping',
             'atOrderFreight','atOrderVerifyTest'].forEach(id => {
                const el = document.getElementById(id); if (el) el.selectedIndex = 0;
            });
            ['atOrderShipTo','atOrderPayment','atOrderNote'].forEach(id => {
                const el = document.getElementById(id); if (el) el.value = '';
            });
            const d = new Date(); d.setDate(d.getDate() + 30);
            const needBy = document.getElementById('atOrderNeedBy');
            if (needBy) needBy.value = d.toISOString().slice(0, 10);
            const cat = document.getElementById('atOrderCategory');
            if (cat) cat.value = 'channel';
            const fr = document.getElementById('atOrderFreight');
            if (fr) fr.value = 'buyer';
            ATItemTable.clear();
        } else {
            // edit:基本信息由 Jinja 已预填(value 属性);仅预填明细
            if (options.items && Array.isArray(options.items)) {
                // 为每条明细补 key(ATItemTable 内部 render 依赖)
                const items = options.items.map(it => ({
                    ...it,
                    key: it.key || `edit-${it.id || 'x'}-${Math.random().toString(36).slice(2, 8)}`,
                }));
                ATItemTable.setItems(items);
            }
            if (options.currency) {
                // ATItemTable 内部 setCurrency 通过 setItems 时的 item.currency 推断;
                // 这里如果有显式 currency 字段,可在每个 item 上塞 currency
                // (当前 ATItemTable 实现以单一 currency 控制,无单独 API,故略)
            }
        }
        atUpdateOrderSubmitBtn();
        const modal = document.getElementById(mid);
        if (modal) modal.style.display = 'flex';
    }
    window.atOpenOrderForm = atOpenOrderForm;

    // ─── 提交 ───
    function atSubmitOrderForm(mode, orderId) {
        mode = mode || 'create';
        const isEdit = (mode === 'edit');
        const mid = modalIdFor(mode);
        const get = id => { const el = document.getElementById(id); return el ? el.value : ''; };

        // create 模式校验
        if (!isEdit) {
            const supplierId = get('atOrderSupplier');
            if (!supplierId) { ATToast.warn('无法创建订单', '请选择供应商'); return; }
        }
        if (ATItemTable.isEmpty()) {
            ATToast.warn(isEdit ? '无法保存' : '无法创建订单', '请至少保留一个产品');
            return;
        }

        const items = ATItemTable.getItems();
        const body = {
            order_category:           get('atOrderCategory'),
            required_date:            get('atOrderNeedBy'),
            incoterms:                get('atOrderIncoterm'),
            shipping_method:          get('atOrderShipping'),
            freight_terms:            get('atOrderFreight'),
            verification_test_type:   get('atOrderVerifyTest'),
            ship_to:                  get('atOrderShipTo'),
            payment_terms:            get('atOrderPayment'),
            notes:                    get('atOrderNote'),
            currency:                 ATItemTable.getCurrency(),
            details:                  items.map(it => {
                const row = {
                    product_id:    it.product_id,
                    product_name:  it.name,
                    product_model: it.model,
                    quantity:      parseInt(it.qty) || 0,
                    unit_price:    parseFloat(it.price) || 0,
                    unit:          it.unit || '套',
                };
                if (it.sales_order_detail_id) row.sales_order_detail_id = it.sales_order_detail_id;
                // edit 模式:已有明细可携带 id,后端识别为更新而非新增
                if (isEdit && it.id) row.id = it.id;
                return row;
            }),
        };

        if (!isEdit) {
            // create 模式额外字段
            body.supplier_id = parseInt(get('atOrderSupplier'));
        } else {
            // edit 模式:交期计划(若 schedule 未锁定才渲染)
            if (document.getElementById('atOrderConfirmedDate')) {
                body.confirmed_date               = get('atOrderConfirmedDate');
                body.milestone_test_complete_date = get('atOrderTestDate');
                body.milestone_ship_date          = get('atOrderShipDate');
            }
        }

        const btn = document.getElementById('atOrderSubmitBtn');
        btn.disabled = true; btn.style.opacity = '0.5'; btn.style.cursor = 'wait';
        const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';

        const url    = isEdit ? `/purchase-order/api/${orderId}/update` : '/purchase-order/api/create';
        const method = isEdit ? 'PUT' : 'POST';

        fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
            body: JSON.stringify(body),
        })
            .then(r => r.json())
            .then(res => {
                if (res.success) {
                    const modal = document.getElementById(mid);
                    if (modal) modal.style.display = 'none';
                    ATToast.success(isEdit ? '已保存修改' : '采购订单已创建', res.order_number || '');
                    setTimeout(() => location.reload(), 700);
                } else {
                    ATToast.error(isEdit ? '保存失败' : '创建失败', res.message || '');
                    btn.disabled = false; btn.style.opacity = '1'; btn.style.cursor = 'pointer';
                }
            })
            .catch(err => {
                ATToast.error(isEdit ? '保存失败' : '创建失败', String(err));
                btn.disabled = false; btn.style.opacity = '1'; btn.style.cursor = 'pointer';
            });
    }
    window.atSubmitOrderForm = atSubmitOrderForm;
})();
