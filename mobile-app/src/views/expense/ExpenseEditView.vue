<!--
  ExpenseEditView · 新建/编辑报销单
  合并 design_handoff:
    - ExpenseNewForm (L132-216) — ① 主表 · 单号系统自动生成 (无明细)
    - ExpenseLines (L218-289) — ② 明细 · 已添加 N 项

  根据 lines.length 切换 sub-title 和明细区域(空态卡 / 列表态)
-->
<template>
  <div
    class="relative h-full overflow-hidden"
    :style="{ background: 'var(--color-ex-bg)', color: 'var(--color-ex-ink)', fontFamily: 'var(--font-sans)' }"
  >
    <div class="status-pad" />

    <ExNav
      title="新建报销单"
      :sub="navSub"
      @back="$router.back()"
    >
      <template #right>
        <div :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)' }" @click="$router.back()">取消</div>
      </template>
    </ExNav>

    <div
      class="overflow-auto h-full no-scrollbar"
      :style="{ paddingTop: '102px', paddingBottom: '100px' }"
    >
      <!-- 已有明细时:压缩头部到 context block -->
      <div v-if="hasLines" :style="{ padding: '14px 20px 4px' }">
        <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', letterSpacing: '0.4px' }">
          {{ form.title || '未命名' }}
        </div>
        <div :style="{ fontSize: '14px', color: 'var(--color-ex-ink2)', marginTop: '2px' }">
          {{ contextLine }}
        </div>
      </div>

      <!-- 主表区域 (无明细时大字标题, 有明细时折叠/可点回到主表编辑) -->
      <template v-if="!hasLines">
        <!-- 报销主题 -->
        <div :style="{ padding: '0 20px 16px' }">
          <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginBottom: '4px' }">报销主题 *</div>
          <input
            v-model="form.title"
            placeholder="例: 苏州客户拜访"
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
            <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginBottom: '4px' }">货币类型 *</div>
            <select
              v-model="form.currency"
              :style="{
                fontSize: '14px',
                fontWeight: 500,
                color: 'var(--color-ex-ink)',
                background: 'transparent',
                border: 'none',
                width: '100%',
                outline: 'none',
              }"
            >
              <option v-for="c in currencies" :key="c.code" :value="c.code">
                {{ c.label }} {{ c.symbol }} ({{ c.code }})
              </option>
            </select>
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
      </template>

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

      <!-- 明细 · 列表态 -->
      <div v-else :style="{ background: 'var(--color-ex-card)' }">
        <div
          v-for="(d, i) in lines"
          :key="d.id || i"
          class="flex"
          :style="{
            padding: '14px 20px',
            borderBottom: i < lines.length - 1 ? '1px solid var(--color-ex-divider-soft)' : 'none',
            gap: '12px',
          }"
          @click="openLineForm(d)"
        >
          <div
            class="flex items-center justify-center flex-shrink-0"
            :style="{
              width: '44px', height: '44px', borderRadius: '6px',
              background: 'var(--color-ex-divider-soft)',
              color: 'var(--color-ex-ink3)', fontSize: '10px', fontWeight: 600,
            }"
          >{{ d.invoice_images?.length ? `图${d.invoice_images.length}` : '发票' }}</div>
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
import { useExpenseStore } from '@/stores/expense'
import { useAuthStore } from '@/stores/auth'
import ExNav from '@/components/expense/ExNav.vue'
import ExRow from '@/components/expense/ExRow.vue'
import ExBottomBar from '@/components/expense/ExBottomBar.vue'
import ExSearchPickerSheet from '@/components/expense/ExSearchPickerSheet.vue'
import ExLineFormSheet from '@/components/expense/ExLineFormSheet.vue'
import ExSubmitSheet from '@/components/expense/ExSubmitSheet.vue'

const route = useRoute()
const router = useRouter()
const store = useExpenseStore()
const auth = useAuthStore()

const editingId = ref(parseInt(route.params.id) || null)
const isNew = computed(() => !editingId.value)

const form = ref({
  title: '',
  description: '',
  currency: 'CNY',
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
const navSub = computed(() => hasLines.value
  ? `② 明细 · 已添加 ${lines.value.length} 项`
  : '① 主表 · 单号系统自动生成')
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
const canPrimary = computed(() => {
  if (!form.value.title.trim()) return false
  if (!form.value.no_link && (!form.value.customer_id || !form.value.project_id)) return false
  if (hasLines.value && !canSubmit.value) return false
  return true
})
const canSubmit = computed(() => hasLines.value && form.value.title.trim() && form.value.description.trim())

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
  const r = await client.get('/mobile/customers', { params: { q: q || '', per_page: 20 } })
  return (r.data?.data?.items || []).map(c => ({
    id: c.id,
    label: c.name || c.company_name,
    sub: c.code || c.company_code || '',
    code: c.code || c.company_code || '',
  }))
}

async function searchProjects(q) {
  const r = await client.get('/mobile/projects', { params: { search: q || '', per_page: 20 } })
  return (r.data?.data?.items || []).map(p => ({
    id: p.id,
    label: p.project_name,
    sub: p.customer_name || '',
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
  // 必须先创建草稿才能加明细
  const r = await expApi.createExpense({
    title: form.value.title.trim() || '未命名报销',
    description: form.value.description.trim(),
    currency: form.value.currency,
    customer_id: form.value.no_link ? null : form.value.customer_id,
    project_id: form.value.no_link ? null : form.value.project_id,
  })
  if (r.data?.success) {
    editingId.value = r.data.data.id
    return editingId.value
  }
  throw new Error(r.data?.message || '创建失败')
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
