/* ─────────────────────────────────────────────────────────────
   PMA · 新建采购订单
   - CreateOrderModal       主弹窗(表单 + 产品表)
   - ProductPicker          产品级联选择器(基站→数字信道机→具体 SKU)
   - CustomerNeedsModal     从客户需求池导入
   ───────────────────────────────────────────────────────────── */

const _SUPPLIERS = window.PMA_DATA.SUPPLIERS;

const PRODUCT_TREE = [
  {
    cat: "基站", icon: "factory", families: [
      { name: "数字信道机", products: [
        { id: "M1MAX-A", name: "数字智能信道机", model: "Mark1000 MAX", spec: "频率范围: 400-470 MHz, 输出功率: 25 W, 尺寸: 220×210×90 mm, 重量: 8.9 kg, 电源类型: 220V欧标", price: 13580 },
        { id: "M1MAX-B", name: "数字智能信道机", model: "Mark1000 MAX", spec: "输出功率: 2W, 尺寸: 220×210×90", price: 14583 },
      ]},
      { name: "广播多频点调频处理器", products: [
        { id: "BMF-100", name: "广播多频点调频处理器", model: "BMF-100", spec: "8 频点, 1U 机架式", price: 9800 },
      ]},
      { name: "数字基站", products: [
        { id: "M3K-BS", name: "常规数字基站", model: "Mark3000BS", spec: "400-470 MHz, 25W", price: 12000 },
        { id: "M3K-PRO", name: "数字基站 Pro", model: "Mark3000Pro", spec: "400-470 MHz, 50W, 双频段", price: 18900 },
        { id: "M3K-LITE", name: "数字基站 Lite", model: "Mark3000Lite", spec: "400-470 MHz, 10W", price: 7600 },
      ]},
      { name: "数字远端基站", products: [
        { id: "M3K-REM", name: "数字远端基站", model: "Mark3000RM", spec: "光纤接入, 400-470 MHz", price: 21500 },
      ]},
    ],
  },
  {
    cat: "合路平台", icon: "factory", families: [
      { name: "多信道分合路器", products: [
        { id: "FHJ400-2", name: "多信道分合路器", model: "FHJ400-2", spec: "2 路, 400 MHz", price: 3200 },
      ]},
    ],
  },
  {
    cat: "直放站", icon: "factory", families: [
      { name: "射频直放站", products: [
        { id: "BDA400", name: "射频直放站", model: "E-BDA400B LT", spec: "403-405/413-415 MHz 带宽 ≤4M 输出 2W", price: 8500 },
      ]},
    ],
  },
  {
    cat: "对讲机", icon: "factory", families: [
      { name: "数字对讲机", products: [
        { id: "PNR2000", name: "数字对讲机", model: "PNR2000", spec: "400-470 MHz 锂电池 3700mAh", price: 980 },
        { id: "DMR2600", name: "数字对讲机", model: "DMR-2600", spec: "400-470 MHz, IP67", price: 1280 },
      ]},
    ],
  },
  {
    cat: "功率 / 耦合器", icon: "factory", families: [] },
];

const CUSTOMER_NEEDS = [
  // { customerOrderId, customer, product, model, qty }
];

/* ─── Create order modal ───────────────────────────────────── */

function CreateOrderModal({ open, onClose }) {
  const [form, setForm] = useState({
    supplier: "", category: "渠道订单", needBy: "2026-05-23",
    incoterm: "", transport: "", freight: "采购方", verify: "到货测试",
    location: "", payment: "", note: "",
  });
  const [items, setItems] = useState([]);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickerReplaceKey, setPickerReplaceKey] = useState(null); // when re-editing existing row
  const [needsOpen, setNeedsOpen]   = useState(false);
  const [currency, setCurrency]     = useState("人民币");
  const [draggingKey, setDraggingKey] = useState(null);
  const [overKey, setOverKey] = useState(null);

  const setF = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const total = items.reduce((s, it) => s + (it.qty || 0) * (it.price || 0), 0);

  const addProduct = (p) => {
    if (pickerReplaceKey) {
      // replace mode
      setItems(arr => arr.map(it => it.key === pickerReplaceKey
        ? { ...it, productId: p.id, name: p.name, model: p.model, spec: p.spec, price: p.price }
        : it
      ));
    } else {
      setItems(arr => [...arr, {
        key: `${p.id}-${Date.now()}`,
        productId: p.id,
        name: p.name, model: p.model, spec: p.spec,
        qty: 1, unit: "套", price: p.price,
      }]);
    }
    setPickerOpen(false);
    setPickerReplaceKey(null);
  };

  const updateItem = (key, patch) => setItems(arr => arr.map(it => it.key === key ? { ...it, ...patch } : it));
  const removeItem = (key) => setItems(arr => arr.filter(it => it.key !== key));

  const reorder = (fromKey, toKey) => {
    if (!fromKey || !toKey || fromKey === toKey) return;
    setItems(arr => {
      const fromIdx = arr.findIndex(it => it.key === fromKey);
      const toIdx   = arr.findIndex(it => it.key === toKey);
      if (fromIdx < 0 || toIdx < 0) return arr;
      const next = arr.slice();
      const [moved] = next.splice(fromIdx, 1);
      next.splice(toIdx, 0, moved);
      return next;
    });
  };

  const openPicker = (replaceKey = null) => {
    setPickerReplaceKey(replaceKey);
    setPickerOpen(true);
  };

  return (
    <ModalShell
      open={open} onClose={onClose}
      title="新建采购订单"
      icon="cart"
      width={1080}
      footer={<>
        <Btn variant="ghost" onClick={onClose}>取消</Btn>
        <Btn variant="accent" iconL="check"
          disabled={!form.supplier || items.length === 0}
        >创建采购订单</Btn>
      </>}
    >
      {/* Form grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
        columnGap: 16, rowGap: 14,
        marginBottom: 4,
      }}>
        <FormField label="供应商" required colSpan={2}>
          <Select
            value={form.supplier} onChange={v => setF("supplier", v)}
            options={[..._SUPPLIERS]}
            placeholder="请选择供应商"
            style={{ width: "100%" }}
          />
        </FormField>
        <FormField label="订单类别">
          <Select
            value={form.category} onChange={v => setF("category", v)}
            options={["渠道订单", "备货订单", "样品订单"]}
            style={{ width: "100%" }}
          />
        </FormField>
        <FormField label="需求日期" required>
          <DateInput value={form.needBy} onChange={v => setF("needBy", v)} />
        </FormField>

        <FormField label="贸易术语">
          <Select
            value={form.incoterm} onChange={v => setF("incoterm", v)}
            options={["EXW", "FOB", "CIF", "DDP"]}
            placeholder="请选择"
            style={{ width: "100%" }}
          />
        </FormField>
        <FormField label="运输方式">
          <Select
            value={form.transport} onChange={v => setF("transport", v)}
            options={["汽运", "空运", "海运", "铁路", "快递"]}
            placeholder="请选择"
            style={{ width: "100%" }}
          />
        </FormField>
        <FormField label="运费承担">
          <Select
            value={form.freight} onChange={v => setF("freight", v)}
            options={["采购方", "供应商", "客户"]}
            style={{ width: "100%" }}
          />
        </FormField>
        <FormField label="验证测试">
          <Select
            value={form.verify} onChange={v => setF("verify", v)}
            options={["到货测试", "出厂测试", "不测试"]}
            style={{ width: "100%" }}
          />
        </FormField>

        <FormField label="交货地点" colSpan={2}>
          <Input
            placeholder="请输入交货地址" style={{ width: "100%" }}
            value={form.location} onChange={e => setF("location", e.target.value)}
          />
        </FormField>
        <FormField label="付款条件" colSpan={2}>
          <Input
            placeholder="例:50% 预付, 发货后 45 天付清" style={{ width: "100%" }}
            value={form.payment} onChange={e => setF("payment", e.target.value)}
          />
        </FormField>

        <FormField label="备注" colSpan={4}>
          <textarea
            placeholder="订单备注信息"
            value={form.note} onChange={e => setF("note", e.target.value)}
            style={{
              width: "100%", minHeight: 56, padding: "9px 12px",
              border: "1px solid var(--line-2)", borderRadius: 6,
              background: "var(--bg-elev)", fontSize: 13, resize: "vertical",
              outline: "none", fontFamily: "inherit", color: "var(--ink)",
            }}
          />
        </FormField>
      </div>

      {/* Items section */}
      <div style={{
        marginTop: 22,
        background: "var(--bg-page)",
        border: "1px solid var(--line)",
        borderRadius: 10, overflow: "hidden",
      }}>
        <table style={{ width: "100%", fontSize: 13, borderCollapse: "separate", borderSpacing: 0 }}>
          <thead>
            <tr>
              {[
                { l: "", w: 30 },
                { l: <>产品名称 <span style={{color:"var(--danger)"}}>*</span></>, w: "auto" },
                { l: "型号", w: 130 },
                { l: "规格描述", w: 260 },
                { l: "数量", w: 76, right: true },
                { l: "单位", w: 64 },
                { l: "单价", w: 110, right: true },
                { l: "金额", w: 120, right: true },
                { l: "", w: 36 },
              ].map((h, i) => (
                <th key={i} style={{
                  textAlign: h.right ? "right" : "left",
                  padding: "10px 12px 12px",
                  fontSize: 10.5, fontWeight: 500,
                  color: "var(--ink-4)",
                  letterSpacing: "0.06em", textTransform: "uppercase",
                  width: h.w, whiteSpace: "nowrap",
                }}>{h.l}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={9}>
                  <button
                    onClick={() => openPicker()}
                    style={{
                      width: "100%", padding: "18px 14px",
                      display: "flex", alignItems: "center", justifyContent: "flex-start", gap: 10,
                      color: "var(--ink-3)", fontSize: 13,
                      borderTop: "1px solid var(--line-soft)", background: "transparent",
                      cursor: "pointer", transition: "background 100ms",
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"}
                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                  >
                    <Icon name="plus" size={14} />
                    点击选择产品…
                  </button>
                </td>
              </tr>
            ) : items.map((it, i) => {
              const isDragging = draggingKey === it.key;
              const isOver     = overKey === it.key && draggingKey !== it.key;
              return (
                <tr
                  key={it.key}
                  draggable
                  onDragStart={(e) => {
                    setDraggingKey(it.key);
                    e.dataTransfer.effectAllowed = "move";
                    try { e.dataTransfer.setData("text/plain", it.key); } catch(_) {}
                  }}
                  onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = "move"; setOverKey(it.key); }}
                  onDragLeave={() => { if (overKey === it.key) setOverKey(null); }}
                  onDrop={(e) => { e.preventDefault(); reorder(draggingKey, it.key); setDraggingKey(null); setOverKey(null); }}
                  onDragEnd={() => { setDraggingKey(null); setOverKey(null); }}
                  style={{
                    borderTop: isOver ? "2px solid var(--accent)" : "1px solid var(--line-soft)",
                    opacity: isDragging ? 0.4 : 1,
                    background: isDragging ? "var(--bg-hover)" : "transparent",
                    transition: "background 100ms",
                  }}
                >
                  <td style={{ padding: "12px 6px 12px 12px", verticalAlign: "top", cursor: "grab", color: "var(--ink-4)" }} title="拖动排序">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                      <circle cx="9" cy="6" r="1.5"/><circle cx="15" cy="6" r="1.5"/>
                      <circle cx="9" cy="12" r="1.5"/><circle cx="15" cy="12" r="1.5"/>
                      <circle cx="9" cy="18" r="1.5"/><circle cx="15" cy="18" r="1.5"/>
                    </svg>
                  </td>
                  <td style={{ padding: "12px 14px", verticalAlign: "top" }}>
                    <button
                      onClick={() => openPicker(it.key)}
                      title="点击替换产品"
                      style={{
                        textAlign: "left", padding: 0,
                        fontWeight: 500, color: "var(--ink)", fontSize: 13.5,
                        borderBottom: "1px dashed transparent",
                        transition: "border-color 120ms, color 120ms",
                      }}
                      onMouseEnter={e => { e.currentTarget.style.borderBottomColor = "var(--accent)"; e.currentTarget.style.color = "var(--accent)"; }}
                      onMouseLeave={e => { e.currentTarget.style.borderBottomColor = "transparent"; e.currentTarget.style.color = "var(--ink)"; }}
                    >{it.name}</button>
                  </td>
                  <td style={{ padding: "12px 14px", verticalAlign: "top" }} className="mono">{it.model}</td>
                  <td style={{ padding: "12px 14px", verticalAlign: "top" }} className="dim">
                    <div style={{ fontSize: 11.5, lineHeight: 1.4, maxWidth: 260 }}>{it.spec}</div>
                  </td>
                  <td style={{ padding: "12px 8px", textAlign: "right", verticalAlign: "top" }}>
                    <input
                      value={it.qty}
                      onChange={e => updateItem(it.key, { qty: Math.max(1, Number(e.target.value) || 1) })}
                      className="mono tab-num"
                      style={{
                        width: 56, height: 28, padding: "0 8px", textAlign: "right",
                        border: "1px solid var(--line-2)", borderRadius: 4,
                        background: "var(--bg-elev)", outline: "none", fontSize: 13,
                      }}/>
                  </td>
                  <td style={{ padding: "12px 14px", verticalAlign: "top" }}>
                    <span className="dim" style={{ fontSize: 12 }}>{it.unit}</span>
                  </td>
                  <td style={{ padding: "12px 14px", textAlign: "right", verticalAlign: "top" }}>
                    <input value={it.price} onChange={e => updateItem(it.key, { price: Number(e.target.value) || 0 })}
                      className="mono tab-num" style={{
                        width: 84, height: 28, padding: "0 8px", textAlign: "right",
                        border: "1px solid var(--line-2)", borderRadius: 4,
                        background: "var(--bg-elev)", outline: "none", fontSize: 12.5,
                      }}/>
                  </td>
                  <td style={{ padding: "12px 14px", textAlign: "right", fontWeight: 500, verticalAlign: "top" }} className="mono tab-num">
                    {fmtCNY(it.qty * it.price)}
                  </td>
                  <td style={{ padding: "12px 10px", textAlign: "right", verticalAlign: "top" }}>
                    <button onClick={() => removeItem(it.key)} style={{
                      width: 24, height: 24, borderRadius: 4,
                      color: "var(--ink-4)",
                      display: "inline-flex", alignItems: "center", justifyContent: "center",
                    }}
                    onMouseEnter={e => { e.currentTarget.style.background = "var(--danger-soft)"; e.currentTarget.style.color = "var(--danger)"; }}
                    onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "var(--ink-4)"; }}
                    >
                      <Icon name="close" size={14} />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {/* Footer of items table */}
        <div style={{
          padding: "10px 14px",
          borderTop: "1px solid var(--line)",
          display: "flex", alignItems: "center", gap: 8,
        }}>
          <Btn variant="ghost" size="sm" iconL="plus" onClick={() => openPicker()}>
            添加产品
          </Btn>
          <Btn variant="ghost" size="sm" iconL="cart" onClick={() => setNeedsOpen(true)}>
            从客户需求导入
          </Btn>

          <div style={{ flex: 1 }} />

          <span className="dim" style={{ fontSize: 12 }}>货币</span>
          <Select
            value={currency} onChange={setCurrency}
            options={["人民币", "美元", "欧元", "港币"]}
            style={{ minWidth: 100 }}
          />
          <span className="dim" style={{ fontSize: 12, marginLeft: 14 }}>合计金额</span>
          <span className="mono tab-num" style={{
            fontSize: 18, fontWeight: 600, color: "var(--ink)",
            fontFamily: "var(--font-mono)",
          }}>
            {fmtCNY(total)}
          </span>
        </div>
      </div>

      {/* Product picker popover */}
      {pickerOpen && (
        <ProductPicker
          onClose={() => { setPickerOpen(false); setPickerReplaceKey(null); }}
          onPick={addProduct}
          replaceMode={!!pickerReplaceKey}
        />
      )}

      {/* Customer needs modal */}
      <CustomerNeedsModal
        open={needsOpen} onClose={() => setNeedsOpen(false)}
        onImport={(picks) => {
          // not yet wired to real data — just close.
          setNeedsOpen(false);
        }}
      />
    </ModalShell>
  );
}

/* ─── Form field wrapper ───────────────────────────────────── */

function FormField({ label, required, hint, children, colSpan = 1 }) {
  return (
    <div style={{ gridColumn: `span ${colSpan}`, minWidth: 0 }}>
      <label style={{
        display: "flex", alignItems: "baseline", gap: 4,
        fontSize: 12.5, fontWeight: 500, color: "var(--ink-2)",
        marginBottom: 6,
      }}>
        <span>{label}</span>
        {required && <span style={{ color: "var(--danger)" }}>*</span>}
        {hint && <span className="dim" style={{ fontSize: 11, fontWeight: 400, marginLeft: "auto" }}>{hint}</span>}
      </label>
      {children}
    </div>
  );
}

/* ─── Date input ───────────────────────────────────────────── */

function DateInput({ value, onChange }) {
  return (
    <input
      type="date" value={value}
      onChange={e => onChange?.(e.target.value)}
      style={{
        width: "100%", height: 34, padding: "0 12px",
        background: "var(--bg-elev)", border: "1px solid var(--line-2)",
        borderRadius: 6, fontSize: 13, color: "var(--ink)",
        outline: "none", fontFamily: "var(--font-mono)",
        fontVariantNumeric: "tabular-nums",
      }}
    />
  );
}

/* ─── Product picker (cascading panels) ────────────────────── */

function ProductPicker({ onClose, onPick, replaceMode }) {
  const [catIdx, setCatIdx]       = useState(0);
  const [familyIdx, setFamilyIdx] = useState(0);

  const cats     = PRODUCT_TREE;
  const families = cats[catIdx]?.families || [];
  const products = families[familyIdx]?.products || [];

  // close on Esc
  useEffect(() => {
    const onKey = e => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      style={{
        position: "fixed", inset: 0, zIndex: 110,
        background: "rgba(31,30,27,0.18)",
        display: "flex", alignItems: "center", justifyContent: "center",
        animation: "fade-in 140ms ease",
      }}
    >
      <div style={{
        width: "min(880px, 92vw)", height: "min(460px, 70vh)",
        background: "var(--bg-elev)",
        border: "1px solid var(--line)",
        borderRadius: 10, overflow: "hidden",
        boxShadow: "0 20px 60px rgba(0,0,0,0.15)",
        display: "grid",
        gridTemplateColumns: "180px 220px 1fr",
        animation: "scale-in 200ms cubic-bezier(.2,.7,.2,1)",
      }}>
        {/* Category column */}
        <div style={{
          background: "var(--bg-page)",
          borderRight: "1px solid var(--line)",
          padding: 10, overflowY: "auto",
        }}>
          <div className="mono dim" style={{
            fontSize: 10.5, letterSpacing: "0.1em", padding: "6px 8px 8px",
          }}>类目</div>
          {cats.map((c, i) => {
            const active = i === catIdx;
            return (
              <button
                key={c.cat}
                onClick={() => { setCatIdx(i); setFamilyIdx(0); }}
                style={{
                  display: "flex", alignItems: "center", gap: 10,
                  width: "100%", padding: "9px 10px",
                  borderRadius: 6, marginBottom: 2,
                  background: active ? "var(--accent)" : "transparent",
                  color: active ? "#fff" : "var(--ink-2)",
                  fontSize: 13, fontWeight: active ? 500 : 400,
                  textAlign: "left",
                  transition: "background 100ms, color 100ms",
                }}
                onMouseEnter={e => { if (!active) e.currentTarget.style.background = "var(--bg-hover)"; }}
                onMouseLeave={e => { if (!active) e.currentTarget.style.background = "transparent"; }}
              >
                <span style={{ opacity: active ? 1 : 0.6 }}>
                  <Icon name="cube" size={14} />
                </span>
                <span style={{ flex: 1 }}>{c.cat}</span>
                <Icon name="chev" size={11} />
              </button>
            );
          })}
        </div>

        {/* Family column */}
        <div style={{
          background: "var(--bg-elev)",
          borderRight: "1px solid var(--line)",
          padding: 10, overflowY: "auto",
        }}>
          <div className="mono dim" style={{
            fontSize: 10.5, letterSpacing: "0.1em", padding: "6px 8px 8px",
          }}>产品族</div>
          {families.length === 0 && (
            <div className="dim" style={{ padding: "16px 10px", fontSize: 12 }}>
              该类目下暂无产品
            </div>
          )}
          {families.map((f, i) => {
            const active = i === familyIdx;
            return (
              <button
                key={f.name}
                onClick={() => setFamilyIdx(i)}
                style={{
                  display: "flex", alignItems: "center", gap: 10,
                  width: "100%", padding: "9px 10px",
                  borderRadius: 6, marginBottom: 2,
                  background: active ? "var(--bg-active)" : "transparent",
                  color: "var(--ink-2)",
                  fontSize: 13, fontWeight: active ? 500 : 400,
                  textAlign: "left",
                  border: active ? "1px solid var(--line-2)" : "1px solid transparent",
                  transition: "background 100ms",
                }}
                onMouseEnter={e => { if (!active) e.currentTarget.style.background = "var(--bg-hover)"; }}
                onMouseLeave={e => { if (!active) e.currentTarget.style.background = "transparent"; }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{f.name}</div>
                  <div className="dim" style={{ fontSize: 11, marginTop: 1 }}>{f.products.length} 个产品</div>
                </div>
                <Icon name="chev" size={11} />
              </button>
            );
          })}
        </div>

        {/* Products column */}
        <div style={{ padding: 10, overflowY: "auto" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 4px 8px" }}>
            <div className="mono dim" style={{ fontSize: 10.5, letterSpacing: "0.1em" }}>
              {replaceMode ? "替换为" : "具体产品"}
            </div>
            <button onClick={onClose} style={{
              color: "var(--ink-3)", padding: 4, borderRadius: 4,
            }} title="关闭"><Icon name="close" size={14} /></button>
          </div>
          {products.length === 0 && (
            <div className="dim" style={{ padding: "16px 10px", fontSize: 12 }}>
              暂无产品
            </div>
          )}
          {products.map((p) => (
            <button
              key={p.id}
              onClick={() => onPick(p)}
              style={{
                width: "100%", padding: "12px 12px",
                borderRadius: 8, marginBottom: 4,
                border: "1px solid var(--line-soft)",
                background: "var(--bg-elev)",
                textAlign: "left",
                transition: "background 100ms, border-color 100ms",
                cursor: "pointer",
              }}
              onMouseEnter={e => { e.currentTarget.style.background = "var(--accent-tint)"; e.currentTarget.style.borderColor = "var(--accent-soft)"; }}
              onMouseLeave={e => { e.currentTarget.style.background = "var(--bg-elev)"; e.currentTarget.style.borderColor = "var(--line-soft)"; }}
            >
              <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 12 }}>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ fontSize: 13.5, fontWeight: 500, color: "var(--ink)" }}>{p.name}</div>
                  <div className="mono" style={{ fontSize: 12, color: "var(--ink-3)", marginTop: 2 }}>{p.model}</div>
                </div>
                <div className="mono tab-num" style={{
                  fontSize: 13.5, fontWeight: 500, color: "var(--accent)",
                  whiteSpace: "nowrap",
                }}>{fmtCNY(p.price)}</div>
              </div>
              {p.spec && (
                <div className="dim" style={{ fontSize: 11.5, marginTop: 6, lineHeight: 1.45 }}>{p.spec}</div>
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─── Customer needs pool modal ────────────────────────────── */

function CustomerNeedsModal({ open, onClose, onImport }) {
  const [query, setQuery] = useState("");
  const [picked, setPicked] = useState(new Set());

  return (
    <ModalShell
      open={open} onClose={onClose}
      title="客户需求池"
      icon="cart"
      width={720}
      footer={<>
        <Btn variant="ghost" onClick={onClose}>取消</Btn>
        <Btn variant="accent" iconL="check"
          onClick={() => onImport(Array.from(picked))}
          disabled={picked.size === 0}
        >导入选中 {picked.size > 0 && `· ${picked.size}`}</Btn>
      </>}
    >
      <Input
        iconL="search" placeholder="搜索产品名称 / 订单号…"
        value={query} onChange={e => setQuery(e.target.value)}
        style={{ width: "100%", marginBottom: 14 }}
      />

      <div style={{
        border: "1px solid var(--line)", borderRadius: 8,
        background: "var(--bg-elev)", overflow: "hidden",
      }}>
        <table style={{ width: "100%", fontSize: 13, borderCollapse: "separate", borderSpacing: 0 }}>
          <thead>
            <tr>
              {["", "订单号", "客户", "产品", "型号", "待采购"].map((h, i) => (
                <th key={i} style={{
                  textAlign: i === 5 ? "right" : "left",
                  padding: "10px 14px 12px",
                  fontSize: 10.5, fontWeight: 500,
                  color: "var(--ink-4)",
                  letterSpacing: "0.08em", textTransform: "uppercase",
                  width: i === 0 ? 36 : undefined,
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {CUSTOMER_NEEDS.length === 0 ? (
              <tr><td colSpan={6} style={{
                padding: "44px 12px", textAlign: "center", color: "var(--ink-3)",
                borderTop: "1px solid var(--line-soft)",
              }}>
                <div style={{ marginBottom: 8 }}>
                  <Icon name="cart" size={28} />
                </div>
                暂无待采购需求
              </td></tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </ModalShell>
  );
}

Object.assign(window, {
  CreateOrderModal, ProductPicker, CustomerNeedsModal,
});
