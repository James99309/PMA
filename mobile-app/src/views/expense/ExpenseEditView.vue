<!--
  ExpenseEditView · 新建/编辑报销单
  合并 design_handoff:
    - ExpenseNewForm (L132-216) — ① 主表 · 单号系统自动生成 (无明细)
    - ExpenseLines (L218-289) — ② 明细 · 已添加 N 项

  根据 lines.length 切换 sub-title 和明细区域(空态卡 / 列表态)
-->
<template>
  <div class="flex flex-col h-full" :style="[{ background: '#F7F5F2', color: 'var(--color-ink)', fontFamily: 'var(--font-sans)' }, kbStyle]">

    <!-- 顶部安全区 -->
    <div style="height: env(safe-area-inset-top); background: #F7F5F2;" />

    <!-- Nav 表头 — 对齐 ProjectCreateView/CustomerCreateView 的 na-nav 标准 -->
    <div class="flex items-center justify-between shrink-0" style="padding: 10px 20px 8px;">
      <button @click="$router.back()"
        class="active:opacity-60"
        style="font-size: 15px; color: #3A3A3A; font-weight: 500; background: none; border: none; padding: 0;">
        取消
      </button>
      <div class="text-center">
        <div style="font-family: 'Noto Serif SC', Georgia, serif; font-size: 18px; font-weight: 500; color: #1A1A1A;">
          {{ editingId ? '编辑报销单' : '新建报销单' }}
        </div>
        <div style="font-size: 11px; color: #7A7570; margin-top: 1px;">{{ navSub }}</div>
      </div>
      <!-- 右侧占位让标题居中(主操作在底部 ExBottomBar) -->
      <div style="width: 32px;" />
    </div>

    <div
      class="flex-1 overflow-y-auto no-scrollbar"
      :style="{ paddingBottom: '110px' }"
    >
      <!-- 主表区域 — 始终显示, 让用户在有明细时也能改主题/客户/项目/说明 -->
      <div>
        <!-- 报销主题 -->
        <div :style="{ padding: '0 20px 16px' }">
          <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginBottom: '4px' }">
            报销主题
            <span :style="{ color: 'var(--color-ex-ink4)', fontWeight: 400, marginLeft: '4px' }">
              留空时 AI 据说明自动生成
            </span>
          </div>
          <input
            v-model="form.title"
            placeholder="例: 苏州客户拜访 (可留空 AI 生成)"
            :style="{
              fontSize: '22px',
              fontWeight: 500,
              fontFamily: 'var(--font-serif)',
              color: 'var(--color-ex-ink)',
              lineHeight: 1.3,
              border: 'none',
              background: 'transparent',
              width: '100%',
              outline: 'none',
            }"
          />
          <div :style="{ height: '1px', background: 'var(--color-ex-divider)', marginTop: '12px' }" />
        </div>

        <!-- 货币 + 状态 -->
        <div class="flex" :style="{ padding: '0 20px', gap: '16px', marginBottom: '18px' }">
          <div class="flex-1">
            <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginBottom: '4px' }">
              报销币种<span :style="{ color: 'var(--color-ex-ink4)', marginLeft: '4px' }">· 按结算偏好</span>
            </div>
            <div :style="{
                fontSize: '14px',
                fontWeight: 500,
                color: 'var(--color-ex-ink)',
                lineHeight: '24px',
              }">
              {{ currencyDisplayLabel }}
            </div>
          </div>
          <div class="flex-1">
            <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginBottom: '4px' }">状态</div>
            <div
              :style="{
                fontSize: '12px',
                color: 'var(--color-ex-ink3)',
                background: 'var(--color-ex-divider-soft)',
                padding: '3px 8px',
                borderRadius: '4px',
                display: 'inline-block',
                fontWeight: 600,
              }"
            >{{ statusLabel }}</div>
          </div>
        </div>

        <!-- 不关联客户 toggle -->
        <div
          class="flex items-center"
          :style="{ padding: '0 20px', marginBottom: '12px', gap: '10px' }"
          @click="form.no_link = !form.no_link"
        >
          <div
            class="flex items-center justify-center"
            :style="{
              width: '18px',
              height: '18px',
              borderRadius: '4px',
              border: `1.5px solid ${form.no_link ? 'var(--color-ex-ink)' : 'var(--color-ex-ink4)'}`,
              background: form.no_link ? 'var(--color-ex-ink)' : 'var(--color-ex-card)',
              color: 'var(--color-ex-card)',
              fontSize: '12px',
            }"
          >{{ form.no_link ? '✓' : '' }}</div>
          <div :style="{ fontSize: '13px', color: 'var(--color-ex-ink2)' }">不关联客户/项目模式</div>
        </div>
        <div
          :style="{ padding: '0 20px 8px', fontSize: '11px', color: 'var(--color-ex-ink4)', marginLeft: '28px' }"
        >{{ form.no_link ? '已开启 · 此报销单不归属任何客户或项目' : '默认关闭 · 必须关联客户和项目' }}</div>

        <!-- 关联客户 / 项目 (no_link=false 时) -->
        <template v-if="!form.no_link">
          <ExRow
            label="关联客户 *"
            :value="form.customer_name || '请选择'"
            :sub="form.customer_code ? `客户编号 ${form.customer_code}` : ''"
            @click="customerPickerOpen = true"
          />
          <ExRow
            label="关联项目 *"
            :value="form.project_name || '请选择'"
            @click="projectPickerOpen = true"
          />
        </template>

        <!-- 报销说明 -->
        <ExRow label="报销说明 *" :multi="true">
          <textarea
            v-model="form.description"
            rows="3"
            placeholder="请说明此次报销背景、必要性"
            :style="{ background: 'transparent', border: 'none', fontSize: '14px', color: 'var(--color-ex-ink)', width: '100%', resize: 'none', outline: 'none', lineHeight: 1.55 }"
          />
        </ExRow>

        <!-- 申请人 -->
        <ExRow label="申请人" :value="ownerName">
          <template #right>
            <span :style="{ fontSize: '10px', color: 'var(--color-ex-ink4)' }">系统默认</span>
          </template>
        </ExRow>
      </div>

      <!-- ─── 明细区域(以下与有无明细无关, 始终显示) ─── -->

      <!-- 明细 section header -->
      <div
        class="flex items-center justify-between"
        :style="{ padding: '20px 20px 6px' }"
      >
        <div
          :style="{
            fontSize: '11px',
            fontWeight: 600,
            color: 'var(--color-ex-ink3)',
            letterSpacing: '0.6px',
            textTransform: 'uppercase',
          }"
        >报销明细</div>
        <div :style="{ fontSize: '12px', color: 'var(--color-ex-ink3)' }">
          共 {{ lines.length }} 项 ·
          <span
            :style="{ fontSize: '14px', fontWeight: 600, fontFamily: 'var(--font-serif)', color: 'var(--color-ex-ink)' }"
          >{{ currencySymbolFor(form.currency) }}{{ formatAmount(totalAmount) }}</span>
        </div>
      </div>

      <!-- 明细 · 空状态 (虚线卡 + 拍发票/手动添加) -->
      <div
        v-if="!hasLines"
        :style="{
          margin: '0 20px',
          padding: '24px 18px',
          background: 'var(--color-ex-card)',
          border: '1px dashed var(--color-ex-divider)',
          borderRadius: '12px',
        }"
      >
        <div :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)', textAlign: 'center', marginBottom: '14px' }">
          还没有任何明细 · 拍发票自动识别 或 手动添加
        </div>
        <div class="flex" :style="{ gap: '10px' }">
          <div
            class="flex-1 flex items-center justify-center"
            :style="{
              height: '44px', borderRadius: '22px',
              background: 'var(--color-ex-ink)', color: 'var(--color-ex-card)',
              gap: '6px', fontSize: '13px', fontWeight: 600,
            }"
            @click="onCapture"
          >
            <span :style="{ fontSize: '14px' }">◉</span> 拍发票
          </div>
          <div
            class="flex-1 flex items-center justify-center"
            :style="{
              height: '44px', borderRadius: '22px',
              background: 'var(--color-ex-card)',
              border: '1.5px solid var(--color-ex-ink)',
              color: 'var(--color-ex-ink)',
              fontSize: '13px', fontWeight: 600,
            }"
            @click="openLineForm()"
          >+ 手动添加</div>
        </div>
      </div>

      <!-- 明细 · 列表态 (左滑删除, 仅可编辑状态) -->
      <div v-else :style="{ background: 'var(--color-ex-card)' }">
        <SwipeRowAction
          v-for="(d, i) in lines"
          :key="d.id || i"
          :disabled="status !== 'draft' && status !== 'rejected'"
          :actions="[{ label: '删除', color: 'red', handler: () => d.id && onDeleteLine(d.id) }]"
        >
        <div
          class="flex"
          :style="{
            padding: '14px 20px',
            borderBottom: i < lines.length - 1 ? '1px solid var(--color-ex-divider-soft)' : 'none',
            gap: '12px',
            background: 'var(--color-ex-card)',
          }"
          @click="openLineForm(d)"
        >
          <div
            class="flex items-center justify-center flex-shrink-0 relative overflow-hidden"
            :style="{
              width: '44px', height: '44px', borderRadius: '6px',
              background: 'var(--color-ex-divider-soft)',
              color: 'var(--color-ex-ink3)', fontSize: '10px', fontWeight: 600,
            }"
          >
            <!-- 实际发票缩略图; 加载失败 fallback 文字 -->
            <img v-if="lineThumbUrl(d)"
              :src="lineThumbUrl(d)"
              class="w-full h-full"
              style="object-fit: cover;"
              @error="$event.target.style.display='none'" />
            <span v-else>{{ d.invoice_images?.length ? `图${d.invoice_images.length}` : '发票' }}</span>
            <!-- 多张发票数量角标 -->
            <span v-if="(d.invoice_images?.length || 0) > 1"
              :style="{
                position: 'absolute', top: '-2px', right: '-2px',
                minWidth: '16px', height: '16px',
                borderRadius: '8px', padding: '0 4px',
                background: 'var(--color-ex-ink)', color: '#fff',
                fontSize: '9px', fontWeight: 700,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                border: '1.5px solid var(--color-ex-card)',
              }">{{ d.invoice_images.length }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex justify-between">
              <div :style="{ fontSize: '14px', fontWeight: 600, color: 'var(--color-ex-ink)' }">
                {{ categoryLabel(d.expense_category) }}
              </div>
              <div :style="{ fontSize: '15px', fontWeight: 600, fontFamily: 'var(--font-serif)' }">
                {{ currencySymbolFor(d.currency) }}{{ formatAmount(d.invoice_amount) }}
              </div>
            </div>
            <div :style="{ fontSize: '12px', color: 'var(--color-ex-ink3)', marginTop: '3px' }">
              {{ d.description || '—' }}
            </div>
            <div class="flex" :style="{ fontSize: '11px', color: 'var(--color-ex-ink4)', marginTop: '4px', gap: '8px' }">
              <span>{{ d.expense_date }}</span>
              <span>·</span>
              <span>{{ d.document_count }} 张</span>
              <span>·</span>
              <span>汇率 {{ (d.exchange_rate || 1).toFixed(4) }}</span>
            </div>
          </div>
        </div>
        </SwipeRowAction>
      </div>

      <!-- 续拍 / 添加 (有明细时显示) -->
      <div v-if="hasLines" class="flex" :style="{ padding: '14px 20px', gap: '10px' }">
        <div
          class="flex-1 flex items-center justify-center"
          :style="{
            height: '42px', borderRadius: '21px',
            background: 'var(--color-ex-card)',
            border: '1.5px solid var(--color-ex-ink)',
            gap: '6px', fontSize: '13px', fontWeight: 600, color: 'var(--color-ex-ink)',
          }"
          @click="onCapture"
        ><span>◉</span> 继续拍</div>
        <div
          class="flex-1 flex items-center justify-center"
          :style="{
            height: '42px', borderRadius: '21px',
            background: 'var(--color-ex-card)',
            border: '1px solid var(--color-ex-divider)',
            fontSize: '13px', color: 'var(--color-ex-ink2)',
          }"
          @click="openLineForm()"
        >+ 手动添加</div>
      </div>
    </div>

    <!-- 底部 CTA -->
    <ExBottomBar
      :primary="hasLines ? '提交审批' : '保存草稿'"
      :secondary="hasLines ? '保存草稿' : '提交审批'"
      :disabled="!canPrimary"
      @primary="onPrimary"
      @secondary="onSecondary"
    />

    <!-- 客户/项目 picker -->
    <ExSearchPickerSheet
      v-model="customerPickerOpen"
      title="选择客户"
      placeholder="搜索客户名称"
      :search-fn="searchCustomers"
      @pick="onPickCustomer"
    />
    <ExSearchPickerSheet
      v-model="projectPickerOpen"
      title="选择项目"
      placeholder="搜索项目名称"
      :search-fn="searchProjects"
      @pick="onPickProject"
    />

    <!-- 明细表单 sheet -->
    <ExLineFormSheet
      v-model="lineFormOpen"
      :initial="editingLine"
      :categories="categories"
      :currencies="currencies"
      :default-currency="form.currency"
      @save="onSaveLine"
      @delete="onDeleteLine"
    />

    <!-- 提交确认 sheet -->
    <ExSubmitSheet
      v-model="submitSheetOpen"
      :total-amount="totalAmount"
      :currency-symbol="currencySymbolFor(form.currency)"
      :customer-name="form.customer_name"
      :project-name="form.project_name"
      :line-count="lines.length"
      :next-approver="{ user: '上级', node: '上级审批' }"
      :submitting="submitting"
      @confirm="onConfirmSubmit"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import client from '@/api/client'
import * as expApi from '@/api/expense'
import { lineThumbUrl } from '@/api/expense'
import { useExpenseStore } from '@/stores/expense'
import { useAuthStore } from '@/stores/auth'
import { useKeyboardOffset } from '@/composables/useKeyboardOffset'

const { kbStyle } = useKeyboardOffset()
import ExNav from '@/components/expense/ExNav.vue'
import ExRow from '@/components/expense/ExRow.vue'
import ExBottomBar from '@/components/expense/ExBottomBar.vue'
import ExSearchPickerSheet from '@/components/expense/ExSearchPickerSheet.vue'
import ExLineFormSheet from '@/components/expense/ExLineFormSheet.vue'
import ExSubmitSheet from '@/components/expense/ExSubmitSheet.vue'
import SwipeRowAction from '@/components/common/SwipeRowAction.vue'

const route = useRoute()
const router = useRouter()
const store = useExpenseStore()
const auth = useAuthStore()

const editingId = ref(parseInt(route.params.id) || null)
const isNew = computed(() => !editingId.value)

// 默认货币: 用户结算货币 → 区域默认 (cn=CNY, sg=USD)
// 创建后不允许切换 (按结算偏好), 只读展示
const defaultCurrency = (() => {
  const u = auth.user
  if (u?.settlement_currency) return u.settlement_currency
  return auth.regionId === 'sg' ? 'USD' : 'CNY'
})()
const currencyDisplayLabel = computed(() => {
  const c = currencies.value?.find(x => x.code === form.value.currency)
  if (c) return `${c.label} ${c.symbol} (${c.code})`
  return form.value.currency || '—'
})

const form = ref({
  title: '',
  description: '',
  currency: defaultCurrency,
  no_link: false,
  customer_id: null,
  customer_name: '',
  customer_code: '',
  project_id: null,
  project_name: '',
})
const lines = ref([])
const status = ref('draft')

const categories = computed(() => store.categories)
const currencies = computed(() => store.currencies)

const hasLines = computed(() => lines.value.length > 0)
const navSub = computed(() => {
  if (editingId.value) {
    // 编辑模式: 显示单号 + 明细数
    const num = store.detailCache[editingId.value]?.expense_number || ''
    return `${num}${num ? ' · ' : ''}${lines.value.length} 项明细`
  }
  // 新建模式: 用 step 引导
  return hasLines.value
    ? `② 明细 · 已添加 ${lines.value.length} 项`
    : '① 主表 · 单号系统自动生成'
})
const contextLine = computed(() => {
  const parts = []
  if (form.value.customer_name) parts.push(form.value.customer_name)
  if (form.value.project_name) parts.push(form.value.project_name)
  return parts.join(' · ') || '未关联客户'
})
const statusLabel = computed(() => {
  const m = store.statuses.find(s => s.key === status.value)
  return m?.label || '草稿'
})
const ownerName = computed(() => auth.user?.real_name || auth.user?.username || '—')
const totalAmount = computed(() =>
  lines.value.reduce((s, l) => s + (Number(l.invoice_amount) || 0) * (Number(l.exchange_rate) || 1), 0))

function categoryLabel(key) { return store.categoryLabel(key) }
function currencySymbolFor(code) { return store.currencySymbol(code) }
function formatAmount(n) {
  return (n || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// canPrimary: 有明细 → 主按钮是"提交"; 无明细 → 主按钮是"保存草稿"
// 主题可空(后端会用 AI 据说明生成); 但提交审批前需要有说明 + 客户/项目
const canPrimary = computed(() => {
  if (!form.value.no_link && (!form.value.customer_id || !form.value.project_id)) return false
  if (hasLines.value && !canSubmit.value) return false
  return true
})
const canSubmit = computed(() => hasLines.value && form.value.description.trim())

// ── 加载已有报销单(编辑模式) ────────────────────
async function loadExisting() {
  if (!editingId.value) return
  const d = await store.fetchDetail(editingId.value, true)
  if (!d) return
  form.value = {
    title: d.title || '',
    description: d.description || '',
    currency: d.currency || 'CNY',
    no_link: !d.customer_id && !d.project_id,
    customer_id: d.customer?.id || null,
    customer_name: d.customer?.name || '',
    customer_code: d.customer?.code || '',
    project_id: d.project?.id || null,
    project_name: d.project?.name || '',
  }
  lines.value = (d.lines || []).map(l => ({ ...l }))
  status.value = d.status
}

// ── 客户/项目搜索 ─────────────────────────────
const customerPickerOpen = ref(false)
const projectPickerOpen = ref(false)

async function searchCustomers(q) {
  // mobile_customers 接受 search/q 兼容
  const r = await client.get('/mobile/customers', { params: { q: q || '', search: q || '', per_page: 20 } })
  return (r.data?.data?.items || []).map(c => ({
    id: c.id,
    label: c.name || c.company_name,
    sub: c.primary_contact_name ? `主联系人: ${c.primary_contact_name}` : (c.industry || ''),
    code: c.code || c.company_code || '',
  }))
}

async function searchProjects(q) {
  // mobile_projects 字段名: name (不是 project_name), owner_name (不是 customer_name)
  const r = await client.get('/mobile/projects', { params: { search: q || '', per_page: 20 } })
  return (r.data?.data?.items || []).map(p => ({
    id: p.id,
    label: p.name,
    sub: [p.stage_label, p.owner_name, p.city].filter(Boolean).join(' · '),
  }))
}

function onPickCustomer(it) {
  form.value.customer_id = it.id
  form.value.customer_name = it.label
  form.value.customer_code = it.code || ''
}
function onPickProject(it) {
  form.value.project_id = it.id
  form.value.project_name = it.label
}

// ── 明细 CRUD(本地) ──────────────────────────
const lineFormOpen = ref(false)
const editingLine = ref(null)

function openLineForm(line = null) {
  editingLine.value = line
  lineFormOpen.value = true
}

async function ensureExpenseExists() {
  if (editingId.value) return editingId.value
  // 必须先创建草稿才能加明细 — title 真空就传空字符串(后端不再硬塞 fallback)
  const r = await expApi.createExpense({
    title: form.value.title.trim(),
    description: form.value.description.trim(),
    currency: form.value.currency,
    customer_id: form.value.no_link ? null : form.value.customer_id,
    project_id: form.value.no_link ? null : form.value.project_id,
  })
  if (r.data?.success) {
    editingId.value = r.data.data.id
    triggerAutoTitle()  // fire-and-forget AI 生成标题
    return editingId.value
  }
  throw new Error(r.data?.message || '创建失败')
}

// 异步触发 AI 生成标题, 不阻塞用户操作
function triggerAutoTitle() {
  if (!editingId.value) return
  if (form.value.title.trim()) return  // 用户已手填, 不覆盖
  if (!form.value.description.trim()) return  // 没说明, AI 也无从生成
  expApi.autoTitle(editingId.value).catch(() => {})  // 静默失败
}

async function onSaveLine(payload) {
  try {
    const id = await ensureExpenseExists()
    if (payload.id) {
      const r = await expApi.updateLine(id, payload.id, payload)
      if (r.data?.success) {
        const idx = lines.value.findIndex(l => l.id === payload.id)
        if (idx >= 0) lines.value[idx] = r.data.data
      }
    } else {
      const r = await expApi.addLine(id, payload)
      if (r.data?.success) lines.value.push(r.data.data)
    }
  } catch (e) {
    alert('保存明细失败: ' + (e.response?.data?.message || e.message))
  }
}

async function onDeleteLine(lineId) {
  if (!editingId.value) return
  try {
    await expApi.deleteLine(editingId.value, lineId)
    lines.value = lines.value.filter(l => l.id !== lineId)
  } catch (e) {
    alert('删除失败: ' + (e.response?.data?.message || e.message))
  }
}

// ── 拍发票 ───────────────────────────────────
async function onCapture() {
  const id = await ensureExpenseExists().catch(() => null)
  if (id) router.push(`/expense/${id}/capture`)
}

// ── 保存草稿 / 提交 ──────────────────────────
const submitSheetOpen = ref(false)
const submitting = ref(false)

async function saveDraft() {
  try {
    if (editingId.value) {
      // 已有 → 更新
      await expApi.updateExpense(editingId.value, {
        title: form.value.title.trim(),
        description: form.value.description.trim(),
        currency: form.value.currency,
        customer_id: form.value.no_link ? null : form.value.customer_id,
        project_id: form.value.no_link ? null : form.value.project_id,
      })
      triggerAutoTitle()  // 描述更新可能影响标题, 重新触发 AI
    } else {
      await ensureExpenseExists()
    }
    return true
  } catch (e) {
    alert('保存失败: ' + (e.response?.data?.message || e.message))
    return false
  }
}

async function onPrimary() {
  if (!canPrimary.value) return
  if (hasLines.value) {
    // 提交
    if (!await saveDraft()) return
    submitSheetOpen.value = true
  } else {
    // 保存草稿
    if (await saveDraft()) router.back()
  }
}

async function onSecondary() {
  if (hasLines.value) {
    if (await saveDraft()) router.back()
  } else {
    // 无明细 不能提交
    alert('请至少添加 1 条明细后再提交')
  }
}

async function onConfirmSubmit() {
  submitting.value = true
  try {
    const r = status.value === 'rejected'
      ? await expApi.resubmitExpense(editingId.value)
      : await expApi.submitExpense(editingId.value)
    if (r.data?.success) {
      submitSheetOpen.value = false
      router.replace(`/expense/${editingId.value}`)
    } else {
      alert(r.data?.message || '提交失败')
    }
  } catch (e) {
    alert('提交失败: ' + (e.response?.data?.message || e.message))
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await store.loadReference()
  if (editingId.value) await loadExisting()
})
</script>
