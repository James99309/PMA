/**
 * AT 目标表格组件(Excel 式 · 角色绩效目标 / 个人目标覆盖 共用)
 * ─────────────────────────────────────────────────────────────
 * 渲染整张目标表(thead+tbody)到容器,封装:
 *   - 两级表头:全部行为季考时仅一行(1-4季度);任一行月考才出现 1-12 月行
 *   - 季/月粒度切换(数量金额:精确切割换算;比率%:水平复制)
 *   - 年度自动均分(季优先+末位吃余数)、周期调剂封顶不超年度、未分配完年度置灰
 *   - ↑/↓ 步进 1、Enter 提交;权重编辑(可选)带 ≤100% 余量封顶
 *   - dirty 跟踪(变更行首黄条);个人模式行尾「↺ 继承」(已覆盖/有变更时出现)
 *
 * 用法:
 *   const sheet = ATTargetSheet({
 *     container: 'elId' | el,
 *     canEdit: true,
 *     mode: 'role' | 'person',        // person: 行尾继承按钮 + overridden 语义
 *     weightEditable: true|false,     // role 页可改权重(余量制);person 页只读
 *     showDesc: true|false,           // 名称下灰字考核方法(role 页用)
 *     nameLabel: '考核项目',          // 名称列表头文字(预算页传'预算项目')
 *     granYear: true|false,           // 启用「年」粒度:无分摊的行=年,数据区合并为一格
 *     weightBaseCode: 'total',        // 权重驱动金额:行金额 = 基数行年度 × 权重%;
 *                                     //   改基数行年度→全部权重行重算;手改行金额→反算权重
 *     onChange()                      // 任意变更后回调(刷新余量/dirty 指示)
 *     onRevert(item)                  // person:点「↺ 继承」(确认逻辑由调用方做)
 *     showActuals: true|false,        // 数据格显示「实际 / 目标」双值(实际值只读,经 setActuals 注入)
 *     manualCodes: ['pm_dev_rate'],   // 手工采集指标:周期格点击弹录入(不可直接打字),年度格仍编辑目标
 *     inverseCodes: ['fail_rate'],    // 反向指标:实际 ≤ 目标 = 达标(失败率类)
 *     onManualEdit(item, {kind,idx})  // 手工指标周期格点击(kind:'m'|'q'|'y';弹录入框由调用方做)
 *   });
 *   sheet.setActuals(map);            // {item_code:{m:{1..12},q:{1..4},y}} 后重渲;null 期不显示
 *   sheet.setItems(items);            // [{item_code,item_name,unit,locked,weight,annual_target,
 *                                     //   q1..q4_target,enable_quarterly,enable_monthly,
 *                                     //   monthly_targets{},overridden?,description?,
 *                                     //   strong?,indent?}]
 *                                     // strong: 主行突出(加粗+灰底,如预算总额行)
 *                                     // indent: 细分行缩进(└ 前缀,如预算科目行)
 *                                     // locked: 锁定行(不渲染启用勾选;无徽章,锁定语义由页面说明)
 *   sheet.getItems() / sheet.getDirty() / sheet.weightSum() / sheet.render()
 */
(function (g) {
  'use strict';

  // i18n: 复用 window.t(中→英,_js_i18n 注入);未注入时回退原文,确保任何页不报错
  const _t = (g.t) ? g.t : (s => s);

  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const r2 = v => Math.round(v * 100) / 100;
  const fmt = v => (v == null || v === '') ? '' : (Math.round(v * 100) / 100);
  // 目标查看态:0 等同未设(null)→ 显示「—」,直观表达"该期不设目标=不参加考核"(编辑态仍用 fmt 可填)
  const fmtTgt = v => (v == null || v === '' || parseFloat(v) === 0) ? '—' : fmt(v);
  const isRate = it => (it.unit === '%');
  // 积分制:单项得分(水平值)× 实际累计,封顶权重;无目标拆分,锁定为「单项」
  const isCumulative = it => (it.scoring_mode === 'cumulative');
  // 固定档位制(植入品质):阈值写死,无目标输入,实际(均值)按及格/良好两线换算
  const isTiered = it => (it.scoring_mode === 'tiered');
  const TIERED_PASS = 3, TIERED_GOOD = 5;   // 及格→50% / 良好→100%(优秀7仅展示)
  const tieredAch = v => {            // 返回 0~1 达成率
    v = parseFloat(v) || 0;
    if (v >= TIERED_GOOD) return 1;
    if (v >= TIERED_PASS) return 0.5 + (v - TIERED_PASS) / (TIERED_GOOD - TIERED_PASS) * 0.5;
    return TIERED_PASS > 0 ? (v / TIERED_PASS) * 0.5 : 0;
  };

  function splitEven(total, n) {
    const base = Math.floor(total / n * 100) / 100;
    const arr = Array(n).fill(base);
    arr[n - 1] = r2(total - base * (n - 1));
    return arr;
  }

  // 「实际 / 目标」双值样式(组件自带,注入一次)
  if (!document.getElementById('at-ts-act-style')) {
    const st = document.createElement('style');
    st.id = 'at-ts-act-style';
    st.textContent = `
      .cm-sheet td[data-act] { vertical-align: middle; }
      .cm-sheet td[data-act]::before { content: attr(data-act); display: block; font-size: 11px;
                                       line-height: 1.5; }
      .cm-sheet td[data-act-frac]::before { border-bottom: 1px solid var(--line-2);
                                            margin-bottom: 2px; padding-bottom: 1px; }
      .cm-sheet td[data-act-impl]::after { content: attr(data-act-impl); display: block;
                                           color: var(--ink-4); font-style: italic; }
      .cm-sheet td[data-act-impl]:focus::after { content: none; }
      .cm-sheet td[data-act-cls="act-ok"]::before { color: var(--success); font-weight: 600; }
      .cm-sheet td[data-act-cls="act-no"]::before { color: var(--warn); font-weight: 600; }
      .cm-sheet td[data-act-cls="act-na"]::before { color: var(--ink-3); }
      /* 可下钻的实际值 —— 用「淡色底」标记,**不能用下划线**:
         每个「实际/目标」格本来就有一条 data-act-frac 分隔线,虚线下划紧贴其上会糊成一条,
         用户完全分辨不出哪些格能点(实测踩过)。底色是这张表里唯一没被占用的视觉通道 ——
         数字颜色已被达标/未达标占用,横线已被实际/目标分隔占用。 */
      .cm-sheet td[data-kpidetail] { cursor: pointer; background: var(--accent-tint); }
      .cm-sheet td[data-kpidetail]:hover { background: var(--bg-hover); }
      .cm-sheet td[data-kpidetail]:hover::before { text-decoration: underline;
                                                   text-underline-offset: 2px; }
      .cm-sheet td[data-mecell]:hover { background: var(--bg-hover); }
      .cm-sheet .me-act { display: block; font-size: 11px; line-height: 1.5; min-height: 17px;
                          cursor: pointer; border-radius: 4px; color: var(--ink-3); }
      .cm-sheet .me-act:hover { background: var(--bg-hover); }
      .cm-sheet .me-act.me-frac { border-bottom: 1px solid var(--line-2); border-radius: 4px 4px 0 0;
                                  margin-bottom: 2px; padding-bottom: 1px; }
      .cm-sheet .me-act.act-ok { color: var(--success); font-weight: 600; }
      .cm-sheet .me-act.act-no { color: var(--warn); font-weight: 600; }
      .cm-sheet .me-tgt { display: block; min-height: 17px; cursor: cell; }
      .cm-sheet .me-tgt:focus { outline: 2px solid var(--accent); outline-offset: -1px;
                                background: var(--bg-elev); }
      .cm-sheet .me-tgt:empty::before { content: attr(data-impl); color: var(--ink-4); font-style: italic; }
      .cm-sheet .me-tgt:focus::before { content: none; }
      .cm-sheet .ts-locked { background: var(--bg-sunk); color: var(--ink-3); cursor: not-allowed; }
    `;
    document.head.appendChild(st);
  }

  g.ATTargetSheet = function (cfg) {
    const el = typeof cfg.container === 'string' ? document.getElementById(cfg.container) : cfg.container;
    const canEdit = !!cfg.canEdit;
    let editing = false;   // 当前是否处于编辑态(由 AtEditMode onEnter/onExit 驱动);
                           // 只读态下目标 0/空显示「—」,编辑态下用 fmt 可填
    const mode = cfg.mode || 'role';
    const weightEditable = !!cfg.weightEditable && canEdit;
    const granYear = !!cfg.granYear;
    const showActuals = !!cfg.showActuals;
    const manualCodes = cfg.manualCodes || [];
    const inverseCodes = cfg.inverseCodes || [];
    // 水平/对齐型目标:率类(%) + 显式登记的水平型计数(levelCodes,如销售配合广度)——
    // 年度目标=每期(季/月)目标,不做均分;与后端 scoring_modes.LEVEL_TARGET_CODES 一致。
    const levelCodes = cfg.levelCodes || [];
    const isLevel = it => isRate(it) || levelCodes.includes(it.item_code);
    let items = [];
    let actuals = {};   // {item_code:{m:{},q:{},y}}
    let lockedQ = new Set();   // 已结算锁定的季度(1..4):该季目标格只读、手工实际不可录
    const fieldLocked = (field) => {
      if (!field) return false;
      if (field[0] === 'q') return lockedQ.has(parseInt(field.slice(1)));
      if (field[0] === 'm') return lockedQ.has(Math.ceil(parseInt(field.slice(1)) / 3));
      return false;   // 年度/权重不按季锁定
    };
    const showScore = !!cfg.showScore;   // 表格底部季度加权得分行(基于实际/目标/权重自算)

    // 某期(kind:'y'|'q', idx)的加权得分:Σ(达成率×权重)/Σ(计入权重)×100;
    // 无目标的项不计入(剔除其权重),避免目标=0 凭空满分。口径与表格「实际/目标」完全一致。
    function periodScore(kind, idx) {
      let wsum = 0, sc = 0;
      items.forEach(it => {
        if (it.enabled === false) return;
        if (cfg.weightBaseCode && it.item_code === cfg.weightBaseCode) return;
        const w = parseFloat(it.weight) || 0;
        if (!w) return;
        const a = actuals[it.item_code];
        if (!a) return;
        const actual = kind === 'y' ? a.y : (a.q || {})[idx];
        if (actual == null) return;   // 未开始期间不计入(任何计分方式通用)
        const sm = it.scoring_mode || 'target';
        // 固定档位制:阈值写死,实际(均值)按及格/良好换算;无目标,权重恒计入
        if (sm === 'tiered') {
          sc += tieredAch(actual) * w; wsum += w;
          return;
        }
        // 积分制:单项得分(annual_target 视为水平值)× 实际累计,封顶权重;权重恒计入(不做=0分,不归一)
        if (sm === 'cumulative') {
          const perUnit = parseFloat(it.annual_target) || 1;
          sc += Math.min(actual * perUnit, w); wsum += w;
          return;
        }
        // 目标制/反向:季度无显式目标时按年度推导(率类水平/数量均分)
        let t = kind === 'y' ? parseFloat(it.annual_target) : parseFloat(it['q' + idx + '_target']);
        if (isNaN(t) && kind === 'q') {
          const ann = parseFloat(it.annual_target);
          if (!isNaN(ann) && ann > 0) t = isLevel(it) ? ann : r2(ann / 4);
        }
        if (isNaN(t) || t <= 0) return;   // 目标制无目标 → 不计入(剔除归一)
        const rate = (sm === 'inverse' || inverseCodes.includes(it.item_code))
          ? (actual <= t + 0.0001 ? 1 : t / actual)
          : Math.min(actual / t, 1);
        sc += rate * w; wsum += w;
      });
      return wsum > 0 ? Math.round(sc / wsum * 1000) / 10 : null;
    }

    // 数据格的「实际值」前缀:有实际值时返回 data-act 属性(含分隔符)+ 达成着色 class
    function actInfo(it, kind, idx, target) {
      if (!showActuals) return null;
      const a = actuals[it.item_code];
      if (!a) return null;
      const v = kind === 'y' ? a.y : (a[kind] || {})[idx];
      let t = parseFloat(target);
      // 周期目标未分摊时,按年度推导虚拟分母(率类=水平复制,数量金额=均分),灰显且聚焦即隐藏
      let implied = null;
      if (isNaN(t) && kind !== 'y') {
        const annual = parseFloat(it.annual_target);
        if (!isNaN(annual) && annual > 0) {
          implied = isLevel(it) ? annual : r2(annual / (kind === 'q' ? 4 : 12));
          t = implied;
        }
      }
      let cls = 'act-na';
      if (v != null && !isNaN(t) && t > 0) {
        const ok = inverseCodes.includes(it.item_code) ? v <= t + 0.0001 : v >= t - 0.0001;
        cls = ok ? 'act-ok' : 'act-no';
      }
      return { v, implied, cls, hasT: !isNaN(t) };
    }

    // 该 KPI 是否支持下钻明细。清单由后端注册表(kpi_actual_service._KPI_DETAIL_FNS)下发,
    // 前端不硬编码 code —— 后端加 provider 即自动出现入口,不用改这里。
    function drillAttr(it, kind, idx) {
      // 季/月/年都支持 —— 考核粒度是每人可配的(如李华伟植入额按月考),
      // 只做季会让月考行点不开。粒度随属性带给宿主,由后端换算窗口。
      if (canEdit && editing) return '';                 // 编辑态单元格要可 contenteditable,不抢点击
      const codes = window.ATKpiDetailCodes || [];
      if (!codes.includes(it.item_code)) return '';
      return ` data-kpidetail="${it.item_code}|${kind}|${idx}"`;
    }

    function actAttr(it, kind, idx, target) {
      const f = actInfo(it, kind, idx, target);
      if (!f || f.v == null) return '';
      return drillAttr(it, kind, idx) +
             ` data-act="${Math.round(f.v)}" data-act-cls="${f.cls}"` +
             (f.hasT ? ' data-act-frac="1"' : '') +
             (f.implied != null ? ` data-act-impl="${fmt(f.implied)}" title="${_t('目标未分摊到{p},按年度{m}推导;点击可填写显式目标').replace('{p}', kind === 'q' ? _t('季') : _t('月')).replace('{m}', isLevel(it) ? _t('水平') : _t('均分'))}"` : '');
    }

    const baseItem = () => cfg.weightBaseCode ? items.find(x => x.item_code === cfg.weightBaseCode) : null;
    const baseAnnual = () => { const b = baseItem(); return b ? (parseFloat(b.annual_target) || 0) : 0; };

    function resetSpread(it) {
      for (let q = 1; q <= 4; q++) it['q' + q + '_target'] = null;
      it.monthly_targets = {};
    }

    // 行年度上限(外部约束,如个人预算受部门明细可分配封顶);null = 不限
    function annualCapOf(it) {
      return cfg.annualCap ? cfg.annualCap(it) : null;
    }

    // 权重 → 金额(基数行年度 × 权重%),超外部上限则截断并反算权重
    function applyWeight(it) {
      const base = baseAnnual();
      let v = r2(base * (parseFloat(it.weight) || 0) / 100);
      const cap = annualCapOf(it);
      if (cap != null && v > cap + 0.0001) {
        v = r2(cap);
        it.weight = base > 0 ? r2(v / base * 100) : it.weight;
        g.ATToast && ATToast.error(_t('已按可分配上限截断为 {v}').replace('{v}', v));
      }
      it.annual_target = v;
      resetSpread(it);
      if (it.gran !== 'Y') prefill(it);
      markDirty(it);
    }

    // ── 行工具 ──
    const qSum = it => [1, 2, 3, 4].reduce((s, q) => s + (parseFloat(it['q' + q + '_target']) || 0), 0);
    const mSum = it => { let s = 0; for (let m = 1; m <= 12; m++) s += parseFloat(it.monthly_targets[String(m)]) || 0; return s; };
    const hasQ = it => [1, 2, 3, 4].some(q => it['q' + q + '_target'] != null && it['q' + q + '_target'] !== '');
    const hasM = it => { for (let m = 1; m <= 12; m++) { const v = it.monthly_targets[String(m)]; if (v != null && v !== '') return true; } return false; };
    // 基数行(weightBaseCode)代表 100% 盘子本身,不计入分配合计
    const weightSum = () => items.reduce((s, it) =>
      s + ((it.enabled !== false && !(cfg.weightBaseCode && it.item_code === cfg.weightBaseCode))
        ? (parseFloat(it.weight) || 0) : 0), 0);

    function prefill(it) {
      const annual = parseFloat(it.annual_target);
      if (isNaN(annual) || annual <= 0) return;
      if (isLevel(it)) {
        if (it.gran === 'M') { if (!hasM(it)) for (let m = 1; m <= 12; m++) it.monthly_targets[String(m)] = annual; }
        else { if (!hasQ(it)) for (let q = 1; q <= 4; q++) it['q' + q + '_target'] = annual; }
        return;
      }
      const quarters = splitEven(annual, 4);
      if (it.gran === 'M') {
        if (hasM(it)) return;
        quarters.forEach((qv, qi) => splitEven(qv, 3).forEach((mv, k) => { it.monthly_targets[String(qi * 3 + k + 1)] = mv; }));
      } else {
        if (hasQ(it)) return;
        quarters.forEach((qv, qi) => { it['q' + (qi + 1) + '_target'] = qv; });
      }
    }

    function periodCap(it, field) {
      if (isRate(it)) return 100;
      const annual = parseFloat(it.annual_target);
      if (isNaN(annual) || annual <= 0) return Infinity;
      let others = 0;
      if (field[0] === 'q') { for (let q = 1; q <= 4; q++) if ('q' + q !== field) others += parseFloat(it['q' + q + '_target']) || 0; }
      else { const cur = field.slice(1); for (let m = 1; m <= 12; m++) if (String(m) !== cur) others += parseFloat(it.monthly_targets[String(m)]) || 0; }
      return Math.max(0, r2(annual - others));
    }

    function markDirty(it) { it._dirty = true; }

    // ── 交互 ──
    function granToggle(i) {
      const it = items[i];
      if (isCumulative(it)) {
        // 积分制:仅切换展示/计分粒度(年/季/月),单项得分为常量,不拆分目标
        it.gran = granYear
          ? (it.gran === 'Y' ? 'Q' : (it.gran === 'Q' ? 'M' : 'Y'))
          : (it.gran === 'Q' ? 'M' : 'Q');
        markDirty(it); render(); fire();
        return;
      }
      // granYear:年→季→月→年;否则 季↔月
      const gNew = granYear
        ? (it.gran === 'Y' ? 'Q' : (it.gran === 'Q' ? 'M' : 'Y'))
        : (it.gran === 'Q' ? 'M' : 'Q');
      if (gNew === 'Y') {       // 回到年粒度 = 不管控节奏,清掉分摊
        resetSpread(it);
        it.gran = 'Y';
        markDirty(it);
        render(); fire();
        return;
      }
      const rate = isLevel(it);
      if (gNew === 'M' && hasQ(it)) {
        for (let q = 1; q <= 4; q++) {
          const v = parseFloat(it['q' + q + '_target']);
          if (!isNaN(v)) {
            if (rate) { for (let k = 0; k < 3; k++) it.monthly_targets[String((q - 1) * 3 + k + 1)] = v; }
            else splitEven(v, 3).forEach((mv, k) => { it.monthly_targets[String((q - 1) * 3 + k + 1)] = mv; });
          }
        }
      }
      if (gNew === 'Q' && hasM(it)) {
        for (let q = 1; q <= 4; q++) {
          let s = 0, n = 0;
          for (let k = 0; k < 3; k++) {
            const v = parseFloat(it.monthly_targets[String((q - 1) * 3 + k + 1)]);
            if (!isNaN(v)) { s += v; n++; }
          }
          it['q' + q + '_target'] = n ? r2(rate ? s / n : s) : null;
        }
      }
      it.gran = gNew;
      markDirty(it);
      prefill(it);
      render(); fire();
    }

    function commitCell(td, i, field) {
      const raw = (td.textContent || '').replace(/[,%\s]/g, '');
      const v = raw === '' ? null : (parseFloat(raw) || 0);
      const it = items[i];
      if (field === 'annual') {
        const cap = annualCapOf(it);
        if (v != null && cap != null && v > cap + 0.0001) {
          g.ATToast && ATToast.error(_t('超出可分配上限,已截为 {v}').replace('{v}', r2(cap)));
          v = r2(cap);
        }
        it.annual_target = v;
        // 改年度 → 按新值重新平铺到各季/月(清掉旧分摊,避免残留导致合计≠年度而置灰);
        // 预算(weightBaseCode)由权重驱动分摊,不在此重置
        if (!cfg.weightBaseCode && it.gran !== 'Y') resetSpread(it);
        prefill(it); markDirty(it);
        if (cfg.weightBaseCode) {
          if (it.item_code === cfg.weightBaseCode) {
            // 基数行变化 → 所有权重行金额重算
            items.forEach(x => { if (x !== it && x.weight != null) applyWeight(x); });
          } else {
            // 手改细分金额 → 反算权重(可能 Σ>100,由页面余量校验拦截)
            const base = baseAnnual();
            it.weight = base > 0 ? r2((v || 0) / base * 100) : it.weight;
          }
        }
      }
      else if (field === 'weight') {
        const others = weightSum() - (parseFloat(it.weight) || 0);
        const room = r2(100 - others);
        if (v != null && v > room + 0.0001) {
          g.ATToast && ATToast.error(_t('权重余量不足:仅剩 {n}% 可分配').replace('{n}', room));
          render(); return;
        }
        it.weight = v; markDirty(it);
        if (cfg.weightBaseCode && it.item_code !== cfg.weightBaseCode) applyWeight(it);
      } else {
        let nv = v;
        if (nv != null) {
          const cap = periodCap(it, field);
          if (nv > cap + 0.0001) {
            g.ATToast && ATToast.error(isRate(it) ? _t('比率目标不能超过 100%') : _t('超出年度余量,已截为 {v}').replace('{v}', cap));
            nv = cap;
          }
        }
        if (field[0] === 'q') it[field + '_target'] = nv;
        else it.monthly_targets[field.slice(1)] = nv;
        markDirty(it);
      }
      render(); fire();
    }

    function keyHandler(e, i, field) {
      if (e.key === 'Enter') { e.preventDefault(); e.target.blur(); return; }
      if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
      e.preventDefault();
      const it = items[i];
      const raw = (e.target.textContent || '').replace(/[,%\s]/g, '');
      let v = (raw === '' ? 0 : (parseFloat(raw) || 0)) + (e.key === 'ArrowUp' ? 1 : -1);
      if (v < 0) v = 0;
      if (field === 'weight') {
        const others = weightSum() - (parseFloat(it.weight) || 0);
        const cap = r2(100 - others);
        if (v > cap) v = cap;
        it.weight = v; markDirty(it);
        // 权重驱动:步进时就地刷新该行金额格(不整表重渲,保住焦点)
        if (cfg.weightBaseCode && it.item_code !== cfg.weightBaseCode) {
          applyWeight(it);
          el.querySelectorAll(`td[data-i="${i}"]`).forEach(td => {
            const f = td.dataset.f;
            if (f === 'annual') td.textContent = fmt(it.annual_target);
            else if (f && f[0] === 'q') td.textContent = fmt(it[f + '_target']);
            else if (f && f[0] === 'm') td.textContent = fmt(it.monthly_targets[f.slice(1)]);
          });
          const yc = el.querySelector(`td[data-y="${i}"]`);
          if (yc) yc.textContent = fmt(it.annual_target);
        }
        fire();
        e.target.textContent = v + '%';
        return;
      }
      if (field === 'annual') {
        const cap = annualCapOf(it);
        if (cap != null && v > cap) v = cap;
      } else if (field !== 'weight') {
        const cap = periodCap(it, field);
        if (v > cap) v = cap;
      }
      e.target.textContent = r2(v);
    }

    function fire() { cfg.onChange && cfg.onChange(); }

    // ── 渲染 ──
    function render() {
      const monthMode = items.some(it => it.gran === 'M');   // 任一行月考才显示月份表头
      const personCol = mode === 'person';
      // contenteditable 必须与 editing 同步:非编辑态显示的是 fmtTgt()(未设目标为「—」),
      // 往里打字本就无意义,却一直可写 —— 既有的不一致。且它会与「实际值下钻」抢点击焦点。
      const ceAttr = (canEdit && editing) ? 'contenteditable spellcheck="false"' : '';
      const periodCols = monthMode ? 12 : 4;
      const totalCols = 5 + periodCols + (personCol ? 1 : 0);

      let thead = `<tr>
        <th rowspan="${monthMode ? 2 : 1}" style="width:190px;text-align:left;">${esc(cfg.nameLabel || _t('考核项目'))}</th>
        <th rowspan="${monthMode ? 2 : 1}" style="width:50px;">${_t('单位')}</th>
        <th rowspan="${monthMode ? 2 : 1}" style="width:52px;">${_t('权重')}</th>
        <th rowspan="${monthMode ? 2 : 1}" style="width:48px;">${granYear ? _t('粒度') : _t('季/月')}</th>
        <th rowspan="${monthMode ? 2 : 1}" style="width:84px;">${_t('年度')}</th>
        ${[1, 2, 3, 4].map(q => `<th ${monthMode ? 'colspan="3"' : ''}>${_t('{q}季度').replace('{q}', q)}</th>`).join('')}
        ${personCol ? `<th rowspan="${monthMode ? 2 : 1}" style="width:40px;"></th>` : ''}
      </tr>`;
      if (monthMode) {
        thead += `<tr>${Array.from({ length: 12 }, (_, k) => `<th>${_t('{m}月').replace('{m}', k + 1)}</th>`).join('')}</tr>`;
      }

      let tbody = '';
      if (!items.length) {
        tbody = `<tr><td colspan="${totalCols}" class="at-dim" style="padding:26px;text-align:center;">${_t('暂无考核项目')}</td></tr>`;
      }
      items.forEach((it, i) => {
        const annual = parseFloat(it.annual_target) || 0;
        const isM = it.gran === 'M';
        const rate = isLevel(it);
        const sum = isM ? mSum(it) : qSum(it);
        const filled = isM ? hasM(it) : hasQ(it);
        const _cum = isCumulative(it);
        const _tier = isTiered(it);
        const _noSplit = _cum || _tier;   // 积分制/固定档位:无目标拆分
        const bad = !_noSplit && it.gran !== 'Y' && !rate && filled && annual && sum - annual > 0.01;
        const underAlloc = !_noSplit && it.gran !== 'Y' && !rate && annual > 0 && (annual - sum) > 0.01;
        const badCls = bad ? 'cm-bad' : '';
        const dirtyBar = it._dirty ? 'box-shadow:inset 2px 0 0 var(--warn);' : '';

        // 手工采集行:格子拆两区——上=实际值(点击弹录入),下=目标(直接编辑;空时灰显推导值)
        const isManual = showActuals && manualCodes.includes(it.item_code);
        const meCell = (kind, idx, field, target) => {
          const inf = actInfo(it, kind, idx, target) || { cls: 'act-na', hasT: false, implied: null, v: null };
          const frac = inf.v != null && inf.hasT;
          const lk = fieldLocked(field);
          return `<td ${kind === 'q' && monthMode ? 'colspan="3"' : ''} class="${badCls}">
            <span class="me-act ${inf.cls}${frac ? ' me-frac' : ''}${lk ? ' ts-locked' : ''}" data-mecell="${i}|${kind}|${idx}"
                  title="${lk ? _t('该季度已结算锁定,不可修改') : _t('手工指标:点击录入{p}实际值').replace('{p}', kind === 'm' ? _t('{m}月').replace('{m}', idx) : _t('{q}季度').replace('{q}', idx))}">${inf.v != null ? Math.round(inf.v) : ''}</span>
            <span class="me-tgt${lk ? ' ts-locked' : ''}" ${lk ? '' : ceAttr} data-i="${i}" data-f="${field}"${inf.implied != null ? ` data-impl="${fmt(inf.implied)}"` : ''}>${fmt(target)}</span>
          </td>`;
        };
        let cells = '';
        if (_tier) {
          // 固定档位制(植入品质):阈值写死,各期只读回显「实际均值」;得分按及格3/良好5换算。
          const _av = (k, idx) => {
            const a = actuals[it.item_code] || {};
            const v = k === 'y' ? a.y : ((a[k] || {})[idx]);
            return v != null ? (Math.round(v * 10) / 10) : '—';
          };
          const _ttl = _t('本期确认报价的植入品质均值(只读)·及格3→50% / 良好5→100% / 优秀7');
          // 档位/积分两种行型的格子是自绘只读格,不走 actAttr() —— 下钻属性必须单独补,
          // 否则这两类指标的实际值看得见却点不开(产品经理的质量处理/新品上市/上市支持
          // 全是积分制,曾整体缺失下钻入口)。只补 drillAttr、不补 data-act:数字的
          // 呈现方式保持原样,只多出可点态。
          if (it.gran === 'Y') {
            cells = `<td colspan="${periodCols}" class="at-dim"${drillAttr(it, 'y', 0)} style="text-align:center;" title="${_ttl}">${_av('y', 0)}</td>`;
          } else if (isM) {
            for (let m = 1; m <= 12; m++) cells += `<td class="at-dim"${drillAttr(it, 'm', m)} style="text-align:center;" title="${_ttl}">${_av('m', m)}</td>`;
          } else {
            for (let q = 1; q <= 4; q++) cells += `<td ${monthMode ? 'colspan="3"' : ''} class="at-dim"${drillAttr(it, 'q', q)} style="text-align:center;" title="${_ttl}">${_av('q', q)}</td>`;
          }
        } else if (isCumulative(it)) {
          // 积分制:按当前粒度(年/季/月)显示该期实际完成数(只读);得分=min(实际×单项得分, 权重)。年度列填单项得分。
          const _av = (k, idx) => {
            const a = actuals[it.item_code] || {};
            const v = k === 'y' ? a.y : ((a[k] || {})[idx]);
            return v != null ? Math.round(v) : '—';
          };
          const _ttl = _t('该期完成数(自动累计)·得分=min(实际×单项得分, 权重)');
          if (it.gran === 'Y') {
            cells = `<td colspan="${periodCols}" class="at-dim"${drillAttr(it, 'y', 0)} style="text-align:center;" title="${_ttl}">${_av('y', 0)}</td>`;
          } else if (isM) {
            for (let m = 1; m <= 12; m++) cells += `<td class="at-dim"${drillAttr(it, 'm', m)} style="text-align:center;" title="${_ttl}">${_av('m', m)}</td>`;
          } else {
            for (let q = 1; q <= 4; q++) cells += `<td ${monthMode ? 'colspan="3"' : ''} class="at-dim"${drillAttr(it, 'q', q)} style="text-align:center;" title="${_ttl}">${_av('q', q)}</td>`;
          }
        } else if (it.gran === 'Y') {
          // 年粒度:数据区合并一格,只回显年度数(年度列编辑);手工行点击弹录入
          cells = `<td colspan="${periodCols}" class="at-dim" data-y="${i}"${actAttr(it, 'y', 0, it.annual_target)}${isManual ? ` data-mecell="${i}|y|0"` : ''}
                       style="text-align:center;${isManual ? 'cursor:pointer;' : ''}"
                       title="${isManual ? _t('手工指标:点击录入实际值') : _t('年粒度:不按季/月管控节奏')}">${(canEdit && editing) ? fmt(it.annual_target) : fmtTgt(it.annual_target)}</td>`;
        } else if (isM) {
          for (let m = 1; m <= 12; m++) {
            const lk = fieldLocked('m' + m);
            cells += isManual ? meCell('m', m, 'm' + m, it.monthly_targets[String(m)])
              : `<td ${lk ? '' : ceAttr} class="${badCls}${lk ? ' ts-locked' : ''}"${lk ? ' title="' + _t('该季度已结算锁定,不可修改') + '"' : ''} data-i="${i}" data-f="m${m}"${actAttr(it, 'm', m, it.monthly_targets[String(m)])}>${(canEdit && editing) ? fmt(it.monthly_targets[String(m)]) : fmtTgt(it.monthly_targets[String(m)])}</td>`;
          }
        } else {
          // 月表头模式下季考行跨 3 列;纯季模式一格一列
          for (let q = 1; q <= 4; q++) {
            const lk = fieldLocked('q' + q);
            cells += isManual ? meCell('q', q, 'q' + q, it['q' + q + '_target'])
              : `<td ${monthMode ? 'colspan="3"' : ''} ${lk ? '' : ceAttr} class="${badCls}${lk ? ' ts-locked' : ''}"${lk ? ' title="' + _t('该季度已结算锁定,不可修改') + '"' : ''} data-i="${i}" data-f="q${q}"${actAttr(it, 'q', q, it['q' + q + '_target'])}>${(canEdit && editing) ? fmt(it['q' + q + '_target']) : fmtTgt(it['q' + q + '_target'])}</td>`;
          }
        }

        const isBase = cfg.weightBaseCode && it.item_code === cfg.weightBaseCode;
        const weightCell = isBase
          ? `<td title="${_t('年度盘子基准,固定 100%')}"><span style="font-weight:600;color:var(--ink);">100%</span></td>`
          : weightEditable
          ? `<td contenteditable spellcheck="false" style="color:var(--accent);font-weight:600;" data-i="${i}" data-f="weight">${it.weight != null ? it.weight + '%' : ''}</td>`
          : `<td>${it.weight != null ? `<span style="color:var(--accent);font-weight:600;">${it.weight}%</span>` : '<span class="at-dim">—</span>'}</td>`;

        // person:已覆盖或有未保存变更 → 行尾恢复继承图标(出现即表示该项已自定义)
        const revertCell = personCol
          ? `<td>${(canEdit && (it.overridden || it._dirty))
              ? `<button type="button" class="at-revert-btn" data-revert="${i}" title="${_t('恢复继承:删除个人覆盖,恢复角色默认')}"><span class="material-symbols-outlined" style="font-size:16px;">history</span></button>` : ''}</td>`
          : '';

        // 非方案角色(role 模式且未锁定):保留启用勾选,决定该角色考核哪些项
        const chk = (mode === 'role' && !it.locked)
          ? `<input type="checkbox" ${it.enabled !== false ? 'checked' : ''} ${canEdit ? '' : 'disabled'}
               data-enable="${i}" style="width:14px;height:14px;flex-shrink:0;">`
          : '';

        const trStyle = (it.enabled === false ? 'opacity:0.45;' : '') + (it.strong ? 'background:var(--bg-sunk);' : '');
        tbody += `
        <tr${trStyle ? ` style="${trStyle}"` : ''}>
          <td class="cm-name" style="${dirtyBar}">
            <div style="display:flex;align-items:center;gap:6px;${it.indent ? 'padding-left:18px;' : ''}">
              ${it.indent ? '<span style="color:var(--ink-4);flex-shrink:0;">└</span>' : ''}
              ${chk}
              <span style="font-weight:${it.strong ? 600 : 500};${it.strong ? 'font-size:13px;' : ''}color:var(--ink);overflow:hidden;text-overflow:ellipsis;" title="${esc(it.item_name)}">${esc(it.item_name)}</span>
              ${isManual ? `<span class="material-symbols-outlined" title="${_t('手工采集指标:点击数据格上半部录入实际值')}"
                  style="font-size:13px;color:var(--ink-4);flex-shrink:0;cursor:help;">stylus_note</span>` : ''}
              ${isCumulative(it) ? `<span style="flex-shrink:0;font-size:10px;padding:1px 5px;border-radius:6px;background:var(--bg-sunk,#eef);color:var(--ink-3,#667);" title="${_t('积分制:年度列填「单项得分」,每完成1个累计计分,封顶权重')}">${_t('单项得分')}</span>` : ''}
              ${_tier ? `<span style="flex-shrink:0;font-size:10px;padding:1px 5px;border-radius:6px;background:var(--bg-sunk,#eef);color:var(--ink-3,#667);" title="${_t('固定档位:阈值写死不可配——及格3→50% / 良好5→100% / 优秀7;取当期确认报价的植入品质均值换算')}">${_t('固定档位')}</span>` : ''}
            </div>
            ${(cfg.showDesc && it.description) ? `<div class="at-dim" style="font-size:10.5px;margin-top:2px;line-height:1.4;white-space:normal;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;" title="${esc(it.description)}">${esc(it.description)}</div>` : ''}
          </td>
          <td class="at-dim" style="font-size:11.5px;">${esc(it.unit || '—')}</td>
          ${weightCell}
          <td>${canEdit
            ? `<button type="button" class="cm-gran-btn" data-gran="${i}" title="${isCumulative(it) ? _t('积分制:切换展示/计分粒度(年/季/月),单项得分不变') : _t('点击切换粒度') + (granYear ? _t('(年→季→月)') : '')}">${it.gran === 'Y' ? _t('年') : (isM ? _t('月') : _t('季'))}</button>`
            : `<span class="at-dim" style="font-size:11.5px;">${it.gran === 'Y' ? _t('年') : (isM ? _t('月') : _t('季'))}</span>`}</td>
          ${_tier
            ? `<td class="at-dim" style="text-align:center;font-size:11px;" title="${_t('固定档位:阈值写死不可配,无需设目标(及格3/良好5/优秀7)')}">${_t('固定 3/5/7')}</td>`
            : `<td ${ceAttr} data-i="${i}" data-f="annual"${(it.gran === 'Y' || isCumulative(it)) ? '' : actAttr(it, 'y', 0, it.annual_target)}
              style="font-weight:500;${underAlloc ? 'color:var(--ink-4);' : ''}"
              title="${isCumulative(it) ? _t('单项得分:每完成1个(按评价加权)得该分值,逐季累计封顶到权重;不做=0分') : (underAlloc ? _t('尚有 {n} 未分配到{p}度').replace('{n}', r2(annual - sum)).replace('{p}', isM ? _t('月') : _t('季')) : '')}">${fmt(it.annual_target)}</td>`}
          ${cells}
          ${revertCell}
        </tr>`;
      });

      // 底部行:权重合计(权重列,动态) + 各期加权得分(showScore 时)
      let tfoot = '';
      if (showScore || weightEditable) {
        const _sc = v => {
          if (v == null) return '<span class="at-dim">—</span>';
          const c = v >= 80 ? 'var(--success)' : (v >= 60 ? 'var(--warn)' : 'var(--danger)');
          return `<span style="font-weight:600;color:${c};">${fmt(v)}</span><span class="at-dim" style="font-size:10px;"> ${_t('分')}</span>`;
        };
        // 权重合计:应为 100%,偏离标橙
        const wsTotal = weightSum();
        const wsColor = Math.abs(wsTotal - 100) < 0.01 ? 'var(--success)' : 'var(--warn)';
        const wsCell = weightEditable
          ? `<td style="text-align:center;font-weight:600;color:${wsColor};" title="${_t('权重合计(应为 100%)')}">${fmt(wsTotal)}%</td>`
          : '<td></td>';
        let qCells = '';
        for (let q = 1; q <= 4; q++) {
          qCells += `<td ${monthMode ? 'colspan="3"' : ''} style="text-align:center;">${showScore ? _sc(periodScore('q', q)) : ''}</td>`;
        }
        const label = showScore ? _t('绩效得分 · 加权(达成率×权重,未设目标项不计入)') : _t('权重合计');
        tfoot = `<tfoot><tr style="background:var(--bg-sunk);border-top:2px solid var(--line);">
          <td colspan="2" class="cm-name" style="font-weight:600;">${label}</td>
          ${wsCell}
          <td></td>
          <td style="text-align:center;">${showScore ? _sc(periodScore('y', 0)) : ''}</td>
          ${qCells}
          ${personCol ? '<td></td>' : ''}
        </tr></tfoot>`;
      }
      el.innerHTML = `<table class="cm-sheet"><thead>${thead}</thead><tbody>${tbody}</tbody>${tfoot}</table>`;

      // 事件绑定(每次渲染重绑,表格规模小)
      el.querySelectorAll('[data-f]').forEach(td => {
        const i = parseInt(td.dataset.i), f = td.dataset.f;
        td.addEventListener('blur', () => commitCell(td, i, f));
        td.addEventListener('keydown', e => keyHandler(e, i, f));
      });
      el.querySelectorAll('[data-gran]').forEach(b =>
        b.addEventListener('click', () => granToggle(parseInt(b.dataset.gran))));
      el.querySelectorAll('[data-revert]').forEach(b =>
        b.addEventListener('click', () => cfg.onRevert && cfg.onRevert(items[parseInt(b.dataset.revert)])));
      el.querySelectorAll('[data-mecell]').forEach(td =>
        td.addEventListener('click', () => {
          const [i, kind, idx] = td.dataset.mecell.split('|');
          const lk = kind === 'm' ? lockedQ.has(Math.ceil(parseInt(idx) / 3))
                   : kind === 'q' ? lockedQ.has(parseInt(idx)) : false;
          if (lk) { g.ATToast && ATToast.error(_t('该季度已结算锁定,不可修改')); return; }
          cfg.onManualEdit && cfg.onManualEdit(items[parseInt(i)], { kind, idx: parseInt(idx) });
        }));
      // 实际值下钻:回答「这个数字是怎么来的」。onKpiDetail 由宿主页面传入(需知道 userId/year)。
      el.querySelectorAll('[data-kpidetail]').forEach(td =>
        td.addEventListener('click', () => {
          const [code, gran, idx] = td.dataset.kpidetail.split('|');
          cfg.onKpiDetail && cfg.onKpiDetail({
            code, gran, idx: parseInt(idx), cellText: td.getAttribute('data-act')
          });
        }));
      el.querySelectorAll('[data-enable]').forEach(c =>
        c.addEventListener('change', () => {
          const it = items[parseInt(c.dataset.enable)];
          it.enabled = c.checked; markDirty(it); render(); fire();
        }));
    }

    return {
      setItems(list) {
        items = (list || []).map(it => {
          it.monthly_targets = it.monthly_targets || {};
          // 积分制与普通项一致:可切 年/季/月(单项得分为常量,切换不拆目标);默认季考核
          if (isCumulative(it)) {
            it.gran = it.enable_monthly ? 'M' : (it.enable_quarterly ? 'Q' : 'Q');
          } else {
            // granYear 模式:无任何分摊的行 = 年粒度
            it.gran = it.enable_monthly ? 'M'
              : (granYear ? ((it.enable_quarterly || hasQ(it)) ? 'Q' : 'Y') : 'Q');
          }
          it._dirty = false;
          return it;
        });
        render();
      },
      setActuals(map) { actuals = map || {}; render(); },
      setLocks(quarters) { lockedQ = new Set((quarters || []).map(Number)); render(); },
      // 由 AtEditMode onEnter/onExit 调用:切换编辑态并重渲(只读态目标 0/空显示「—」)
      setEditing(v) { editing = !!v; render(); },
      getActuals: () => actuals,
      // 各期加权得分(供季度结算发起取数):{year, quarters:[Q1..Q4]}
      getScores: () => ({ year: periodScore('y', 0), quarters: [1, 2, 3, 4].map(q => periodScore('q', q)) }),
      getItems: () => items,
      getDirty: () => items.filter(x => x._dirty),
      weightSum,
      render,
    };
  };
})(window);
