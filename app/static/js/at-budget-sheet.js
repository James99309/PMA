/**
 * AT 预算表组件(部门预算 / 个人预算覆盖 共用;ATTargetSheet 的预算包装)
 * ─────────────────────────────────────────────────────────────
 * 封装:总额行 + 报销科目细分(chips 增删)、权重%驱动金额、年/季/月粒度、
 *       余量/上限计算、保存 payload 映射。依赖 at-target-sheet.js。
 *
 * 用法:
 *   const bs = ATBudgetSheet({
 *     container, chipsContainer,        // 表格容器 / 科目 chips 容器(id 或元素)
 *     canEdit, currencySymbol,
 *     categories: [{code,name}],        // 报销科目全集(细分键域)
 *     mode: 'dept' | 'person',
 *     onChange(stats)                   // 任意变更回调,stats 见 stats()
 *   });
 *   bs.setData({ items, context });
 *     items: [{item_code:'total'|cat, item_name, unit, annual_target,
 *              q1..q4_target, enable_quarterly, enable_monthly, monthly_targets}]
 *     context(person 模式): {
 *       dept_name, no_dept_budget,
 *       dept_total, dept_used_others,                  // 部门总额 / 其他成员已分配
 *       forced: [codes],                               // 部门已配明细 → 个人强制保留
 *       cat_caps: {code: {dept_amount, used_others}},  // 各科目部门额度与他人已用
 *     }
 *   bs.getPayloadItems()  // POST 用 items
 *   bs.stats()            // {total, catSum, room, deptLeft, overTotal, overCaps:[{code,name,left}]}
 *   bs.validate()         // {ok, msg}
 */
(function (g) {
  'use strict';

  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const r2 = v => Math.round(v * 100) / 100;
  const byId = x => typeof x === 'string' ? document.getElementById(x) : x;

  function injectCSS() {
    if (document.getElementById('atBudgetSheetCSS')) return;
    const st = document.createElement('style');
    st.id = 'atBudgetSheetCSS';
    st.textContent = `
  body.at-page .eb-cat { font:inherit; font-size:11.5px; padding:0; border:0; background:transparent;
            color:var(--ink-4); cursor:pointer; white-space:nowrap; transition:color 100ms; }
  body.at-page .eb-cat:hover { color:var(--ink); }
  body.at-page .eb-cat.on { color:var(--accent); font-weight:600; }
  body.at-page .eb-cat:disabled { cursor:default; }
  body.at-page .eb-cat.on:disabled { opacity:0.75; }`;
    document.head.appendChild(st);
  }

  g.ATBudgetSheet = function (cfg) {
    injectCSS();
    const chipsEl = byId(cfg.chipsContainer);
    const person = cfg.mode === 'person';
    const CATS = cfg.categories || [];
    const SYM = cfg.currencySymbol || '';
    let ctx = {};

    const sheet = g.ATTargetSheet({
      container: cfg.container,
      canEdit: !!cfg.canEdit,
      mode: 'role',
      weightEditable: true,
      weightBaseCode: 'total',
      granYear: true,
      nameLabel: '预算项目',
      showDesc: person,                 // person:科目行下灰字显示部门预算/当前可分配
      // 输入即时封顶:总额行(person)≤ 部门待分配;明细 ≤ 年度总额余量(总额−其他明细),
      // person 再与部门该明细可分配取较小
      annualCap: (it => {
        if (it.item_code === 'total') {
          if (!person || ctx.no_dept_budget || ctx.dept_total == null) return null;
          return r2((parseFloat(ctx.dept_total) || 0) - (parseFloat(ctx.dept_used_others) || 0));
        }
        const items = sheet.getItems();
        const others = catItems(items).reduce((s, i) =>
          s + (i.item_code === it.item_code ? 0 : (parseFloat(i.annual_target) || 0)), 0);
        let cap = r2(totalOf(items) - others);
        if (person) {
          const dcap = capOf(it.item_code);
          if (dcap != null) cap = Math.min(cap, dcap);
        }
        return cap;
      }),
      onChange: () => fire(),
    });

    function fire() { cfg.onChange && cfg.onChange(stats()); }

    const totalOf = items => parseFloat((items.find(i => i.item_code === 'total') || {}).annual_target) || 0;
    const catItems = items => items.filter(i => i.item_code !== 'total');

    // 行视觉:总额=主行,科目=缩进;权重按现有金额反算;person 给科目行写余额说明
    function markRows(items) {
      const total = totalOf(items);
      items.forEach(it => {
        if (it.item_code === 'total') { it.strong = true; it.weight = null; }
        else {
          it.indent = true;
          it.weight = total > 0 ? r2((parseFloat(it.annual_target) || 0) / total * 100) : 0;
          if (person) it.description = capDesc(it.item_code);
        }
      });
      return items;
    }

    // 科目的部门可用上限(部门额度 - 其他成员已用);部门未配该科目 → null(仅受个人总额约束)
    function capOf(code) {
      const c = (ctx.cat_caps || {})[code];
      if (!c) return null;
      return r2((parseFloat(c.dept_amount) || 0) - (parseFloat(c.used_others) || 0));
    }
    function capDesc(code) {
      const c = (ctx.cat_caps || {})[code];
      if (!c) return '部门未单列此明细,仅受个人总额约束';
      return `部门预算 ${SYM}${c.dept_amount} · 当前可分配 ${SYM}${capOf(code)}`;
    }

    // ── 科目 chips:点亮=加入,熄灭=移除;person 模式部门已配明细锁定(强制保留) ──
    function renderChips() {
      const active = new Set(sheet.getItems().map(i => i.item_code));
      const forced = new Set(ctx.forced || []);
      chipsEl.innerHTML = CATS.map(c => {
        const lock = person && forced.has(c.code);
        return `<button type="button" class="eb-cat${active.has(c.code) ? ' on' : ''}"
                  ${(!cfg.canEdit || lock) ? 'disabled' : ''}
                  ${lock ? 'title="部门预算已单列此明细,个人必须配置,不可移除"' : ''}
                  data-cat="${c.code}">${esc(c.name)}${lock ? ' ·锁' : ''}</button>`;
      }).join('');
      chipsEl.querySelectorAll('[data-cat]').forEach(b =>
        b.addEventListener('click', () => toggleCat(b.dataset.cat)));
    }

    function toggleCat(code) {
      const items = sheet.getItems();
      const idx = items.findIndex(i => i.item_code === code);
      if (idx >= 0) items.splice(idx, 1);
      else {
        const c = CATS.find(x => x.code === code);
        items.push({ item_code: code, item_name: c.name, unit: SYM, locked: true, indent: true,
                     weight: 0, annual_target: 0, description: person ? capDesc(code) : undefined,
                     q1_target: null, q2_target: null, q3_target: null, q4_target: null,
                     enable_quarterly: false, enable_monthly: false, monthly_targets: {}, gran: 'Y' });
        items.sort((a, b) => {
          if (a.item_code === 'total') return -1;
          if (b.item_code === 'total') return 1;
          return CATS.findIndex(x => x.code === a.item_code) - CATS.findIndex(x => x.code === b.item_code);
        });
      }
      sheet.setItems(items);
      renderChips(); fire();
    }

    // ── 余量/上限统计 ──
    function stats() {
      const items = sheet.getItems();
      const total = totalOf(items);
      const catSum = catItems(items).reduce((s, i) => s + (parseFloat(i.annual_target) || 0), 0);
      const st = { total, catSum, room: r2(total - catSum), overTotal: total - catSum < -0.005,
                   deptLeft: null, overDept: false, overCaps: [] };
      if (person && !ctx.no_dept_budget && ctx.dept_total != null) {
        const capTotal = r2((parseFloat(ctx.dept_total) || 0) - (parseFloat(ctx.dept_used_others) || 0));
        st.deptLeft = r2(capTotal - total);          // 部门待分配(扣除本人当前输入后)
        st.overDept = st.deptLeft < -0.005;          // 个人年度超部门可分
        catItems(items).forEach(it => {
          const cap = capOf(it.item_code);
          if (cap == null) return;
          const left = r2(cap - (parseFloat(it.annual_target) || 0));
          if (left < -0.005) {
            const c = CATS.find(x => x.code === it.item_code);
            st.overCaps.push({ code: it.item_code, name: c ? c.name : it.item_code, left });
          }
        });
      }
      return st;
    }

    function validate() {
      const st = stats();
      if (st.overTotal) return { ok: false, msg: `细分合计超出年度总额 ${SYM}${Math.abs(st.room)}` };
      if (st.overDept) return { ok: false, msg: `个人年度超出部门可分配额度 ${SYM}${Math.abs(st.deptLeft)}` };
      if (st.overCaps.length) {
        const f = st.overCaps[0];
        return { ok: false, msg: `「${f.name}」超出部门该明细可用上限 ${SYM}${Math.abs(f.left)}` };
      }
      return { ok: true, msg: '' };
    }

    return {
      setData(d) {
        ctx = d.context || {};
        sheet.setItems(markRows(d.items || []));
        renderChips();
        fire();
      },
      getPayloadItems() {
        return sheet.getItems().map(it => {
          const isM = it.gran === 'M';
          const monthly = {};
          if (isM) for (let m = 1; m <= 12; m++) {
            const v = it.monthly_targets[String(m)];
            if (v != null && v !== '') monthly[String(m)] = parseFloat(v) || 0;
          }
          return {
            item_code: it.item_code,
            annual_target: (it.annual_target == null || it.annual_target === '') ? 0 : parseFloat(it.annual_target),
            enable_quarterly: !isM && it.gran !== 'Y' &&
              [1, 2, 3, 4].some(q => it['q' + q + '_target'] != null && it['q' + q + '_target'] !== ''),
            q1_target: !isM ? (it.q1_target ?? null) : null,
            q2_target: !isM ? (it.q2_target ?? null) : null,
            q3_target: !isM ? (it.q3_target ?? null) : null,
            q4_target: !isM ? (it.q4_target ?? null) : null,
            enable_monthly: isM && Object.keys(monthly).length > 0,
            monthly_targets: (isM && Object.keys(monthly).length) ? monthly : null,
          };
        });
      },
      stats, validate,
      getItems: () => sheet.getItems(),
    };
  };
})(window);
