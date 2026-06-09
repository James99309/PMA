/* ─────────────────────────────────────────────────────────────
   PMA · 采购订单模块 · App 主入口
   ───────────────────────────────────────────────────────────── */

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "#C15F3C",
  "headlineFont": "serif",
  "density": "standard",
  "timelinePos": "top",
  "dark": false
}/*EDITMODE-END*/;

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [route, setRoute] = useState({ name: "list", orderId: null });
  const [modal, setModal] = useState(null);
  const [collapsed, setCollapsed] = useState(true);

  // Apply tweaks to <html>
  useEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = t.dark ? "dark" : "light";
    root.dataset.density = t.density;
    root.dataset.headlineFont = t.headlineFont;
    root.style.setProperty("--accent", t.accent);
    // recompute accent-soft / tint from accent
    const tintMap = {
      "#C15F3C": { soft: "#F2DCCC", tint: "#FBF1E9" },
      "#2A5F8F": { soft: "#D5E2EF", tint: "#EDF3F9" },
      "#1F2937": { soft: "#D9DDE3", tint: "#EEEFF2" },
      "#2F7155": { soft: "#D4E5DC", tint: "#EDF4F0" },
    };
    const m = tintMap[t.accent] || { soft: "var(--bg-sunk)", tint: "var(--bg-hover)" };
    root.style.setProperty("--accent-soft", m.soft);
    root.style.setProperty("--accent-tint", m.tint);
    root.style.setProperty("--accent-2", t.accent);
  }, [t]);

  // Routing helpers
  const openOrder = (id) => setRoute({ name: "detail", orderId: id });
  const goBack    = () => setRoute({ name: "list", orderId: null });

  // Modal helpers
  const openModal  = (kind) => setModal(kind);
  const closeModal = ()     => setModal(null);

  const currentOrder = route.orderId
    ? window.PMA_DATA.ORDERS.find(o => o.id === route.orderId)
    : null;

  // Build breadcrumbs
  const breadcrumbs = route.name === "list"
    ? [{ label: "采购管理" }, { label: "采购订单" }]
    : [
        { label: "采购管理", onClick: goBack },
        { label: "采购订单", onClick: goBack },
        { label: route.orderId },
      ];

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg-page)" }}>
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />

      <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
        <Topbar breadcrumbs={breadcrumbs} />

        <main style={{ flex: 1, minHeight: 0 }}>
          {route.name === "list" ? (
            <ListScreen onOpenOrder={openOrder} headlineFont={t.headlineFont} onNewOrder={() => openModal("create")} />
          ) : (
            <DetailScreen
              orderId={route.orderId}
              onBack={goBack}
              onOpenModal={openModal}
              timelinePos={t.timelinePos}
            />
          )}
        </main>
      </div>

      {/* Modals */}
      <SupplierConfirmModal open={modal === "supplier-confirm"} order={currentOrder} onClose={closeModal} />
      <UploadTestModal      open={modal === "upload-test"}      order={currentOrder} onClose={closeModal} />
      <CreateShipmentModal  open={modal === "ship"}             order={currentOrder} onClose={closeModal} />
      <CreateOrderModal     open={modal === "create"}                                onClose={closeModal} />

      {/* Tweaks panel */}
      <TweaksPanel>
        <TweakSection label="主题" />
        <TweakColor
          label="强调色" value={t.accent}
          options={["#C15F3C", "#2A5F8F", "#1F2937", "#2F7155"]}
          onChange={v => setTweak("accent", v)}
        />
        <TweakToggle
          label="深色模式" value={t.dark}
          onChange={v => setTweak("dark", v)}
        />

        <TweakSection label="排版" />
        <TweakRadio
          label="大标题字体" value={t.headlineFont}
          options={[
            { value: "serif", label: "衬线" },
            { value: "sans",  label: "黑体" },
          ]}
          onChange={v => setTweak("headlineFont", v)}
        />
        <TweakRadio
          label="信息密度" value={t.density}
          options={[
            { value: "compact",  label: "紧凑" },
            { value: "standard", label: "标准" },
            { value: "cozy",     label: "宽松" },
          ]}
          onChange={v => setTweak("density", v)}
        />

        <TweakSection label="详情页布局" />
        <TweakRadio
          label="阶段时间线位置" value={t.timelinePos}
          options={[
            { value: "top",  label: "顶部" },
            { value: "side", label: "右侧" },
          ]}
          onChange={v => setTweak("timelinePos", v)}
        />

        <TweakSection label="演示捷径" />
        <TweakButton onClick={() => { setRoute({ name: "list" }); }}>列表页</TweakButton>
        <TweakButton onClick={() => { setRoute({ name: "detail", orderId: "CG-2601-001" }); }}>
          详情页 · 测试中(CG-2601-001)
        </TweakButton>
        <TweakButton onClick={() => { setRoute({ name: "detail", orderId: "CG-2605-002" }); }}>
          详情页 · 已入库(CG-2605-002)
        </TweakButton>
        <TweakButton onClick={() => { setRoute({ name: "detail", orderId: "PUO202507-004" }); openModal && setModal(null); }}>
          详情页 · 待审批(PUO…-004)
        </TweakButton>
        <TweakButton onClick={() => { setRoute({ name: "detail", orderId: "CG-2604-001" }); }}>
          详情页 · 待发货(CG-2604-001)
        </TweakButton>
        <div style={{ height: 4 }} />
        <TweakButton onClick={() => setModal("supplier-confirm")}>弹窗 · 供应商确认</TweakButton>
        <TweakButton onClick={() => setModal("upload-test")}>弹窗 · 上传测试报告</TweakButton>
        <TweakButton onClick={() => setModal("ship")}>弹窗 · 创建发货单</TweakButton>
        <TweakButton onClick={() => setModal("create")}>弹窗 · 新建采购订单</TweakButton>
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <ToastProvider><App /></ToastProvider>
);
