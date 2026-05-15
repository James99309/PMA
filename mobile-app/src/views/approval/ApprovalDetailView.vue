<!--
  ApprovalDetailView · 审批详情(审批人视角)
  严格对齐 design_handoff/expense-approval.jsx::ApprovalDetail (L139-232)
-->
<template>
  <div class="flex flex-col h-full" style="background: #F7F5F2;">

    <!-- Header — 项目同款 (返回 ‹ 审批 + ··· 菜单) -->
    <div class="flex items-center justify-between px-5 py-2.5 shrink-0">
      <button @click="$router.back()"
        class="flex items-center gap-1 active:opacity-60 py-1 pr-2"
        style="color: var(--color-ink-2);">
        <svg width="9" height="14" viewBox="0 0 9 14">
          <path d="M7 1L1 7l6 6" fill="none" stroke="currentColor"
            stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <span class="text-[15px]">{{ t('approval.backApproval') }}</span>
      </button>
      <!-- ··· 直接打开转交 sheet(设计稿没有中间菜单步骤);
           非当前审批人不显示 -->
      <button v-if="detail?.is_current_approver"
        @click="openSheet('forward')"
        class="text-[18px] font-bold active:opacity-60 px-2"
        style="color: var(--color-ink);">···</button>
      <div v-else style="width: 32px;" />
    </div>

    <div v-if="loading" class="flex justify-center items-center flex-1">
      <div class="w-6 h-6 border-2 border-[#D97757] border-t-transparent rounded-full animate-spin" />
    </div>

    <div
      v-else-if="detail"
      class="flex-1 overflow-y-auto no-scrollbar"
      :style="{ paddingBottom: detail.is_current_approver ? '92px' : '24px' }"
    >
      <!-- Hero — 项目同款: 30px 标题 + 44px serif tabular 金额 -->
      <div class="px-7 pt-5 pb-6">
        <!-- 状态 chip + 单号 + 转交徽章 -->
        <div class="flex items-center gap-2 mb-3.5 flex-wrap">
          <!-- 状态 chip 可点击 → 弹流程 sheet (替代之前底部一大块审批进度) -->
          <span
            v-if="currentStepName"
            class="text-[12px] font-medium active:opacity-60 cursor-pointer inline-flex items-center"
            :style="{
              color: 'var(--color-ex-warn)',
              background: 'var(--color-ex-warn-soft)',
              padding: '2px 8px', borderRadius: '4px',
              gap: '3px',
            }"
            @click="flowSheetOpen = true"
          >{{ t('approval.detYouToApprove', { step: currentStepName }) }}
            <svg width="9" height="9" viewBox="0 0 12 12" fill="none">
              <path d="M3 4.5l3 3 3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <!-- 转交徽章: 当前步骤已被代理时显示 -->
          <span
            v-if="detail.delegated_to"
            class="text-[12px] font-medium"
            :style="{
              color: 'var(--color-ex-blue)',
              background: 'var(--color-ex-blue-soft)',
              padding: '2px 8px', borderRadius: '4px',
            }"
          >{{ t('approval.detDelegatedTo', { name: detail.delegated_to.name }) }}</span>
          <span
            class="text-[11px]"
            :style="{
              color: 'var(--color-ink-3)', letterSpacing: '0.5px',
              fontFamily: 'var(--font-mono)',
            }"
          >· {{ detail.business_obj?.expense_number || detail.object_name }}</span>
        </div>

        <!-- 主题: 30px serif (项目同款) -->
        <h1 class="font-serif m-0"
          :style="{
            fontSize: '30px', fontWeight: 500,
            lineHeight: '1.2', letterSpacing: '-0.3px',
            color: 'var(--color-ink)',
          }">{{ detail.business_obj?.title || detail.object_name }}</h1>

        <!-- Sub: 申请人提交时间 -->
        <div v-if="detail.submitter" class="mt-3.5 text-[13px]" style="color: var(--color-ink-3);">
          {{ t('approval.detSubmitterAt', { name: detail.submitter.name, date: (detail.created_at || '').slice(0, 10) }) }}
        </div>

        <!-- 金额 44px serif tabular (项目同款) -->
        <div class="mt-7 flex items-baseline gap-2">
          <span class="font-serif font-medium tabular leading-none"
            :style="{ fontSize: '44px', color: 'var(--color-ink)' }">
            {{ amountStr }}
          </span>
          <span v-if="isProject" class="text-[14px]" style="color: var(--color-ink-3);">
            {{ t('approval.suffixWan') }} · {{ detail.business_obj?.stage_label || '—' }}
          </span>
          <span v-else-if="isPricingOrder" class="text-[14px]" style="color: var(--color-ink-3);">
            {{ currencyLabel(detail.business_obj?.currency) }} · 折扣 {{ ((detail.business_obj?.pricing_total_discount_rate || 1) * 100).toFixed(1) }}%
          </span>
          <span v-else-if="isQuotation" class="text-[14px]" style="color: var(--color-ink-3);">
            {{ currencyLabel(detail.business_obj?.currency) }} · {{ detail.business_obj?.project_stage || '—' }}
          </span>
          <span v-else-if="detail.business_obj" class="text-[14px]" style="color: var(--color-ink-3);">
            {{ currencyLabel(detail.business_obj.currency) }} · {{ t('approval.detailCountSuffix', { n: detail.business_obj.detail_count }) }}
          </span>
        </div>
        <div v-if="waitingHint" class="text-[12px] mt-1.5" style="color: var(--color-ink-3);">{{ waitingHint }}</div>
      </div>

      <!-- 申请人卡 -->
      <ApplicantCard
        v-if="detail.submitter"
        :submitter="detail.submitter"
        :stats="detail.submitter_stats"
      />

      <!-- 详情 def list — 报销 / 项目 字段不同 -->
      <ExSectionHeader v-if="detail.business_obj">{{ t('approval.detSection') }}</ExSectionHeader>
      <!-- 报销字段 -->
      <div v-if="detail.business_obj && isExpense" :style="{ background: 'var(--color-ex-card)' }">
        <ExDefRow :label="t('approval.fSubject')">{{ detail.business_obj.title }}</ExDefRow>
        <ExDefRow :label="t('approval.fCustomer')">{{ detail.business_obj.customer_name || '—' }}</ExDefRow>
        <ExDefRow :label="t('approval.fProject')">{{ detail.business_obj.project_name || '—' }}</ExDefRow>
        <ExDefRow :label="t('approval.fDescription')" :last="true">{{ detail.business_obj.description || '—' }}</ExDefRow>
      </div>
      <!-- 项目字段 -->
      <div v-else-if="detail.business_obj && isProject" :style="{ background: 'var(--color-ex-card)' }">
        <ExDefRow :label="t('approval.fProjectName')">{{ detail.business_obj.project_name }}</ExDefRow>
        <ExDefRow v-if="detail.business_obj.project_code" :label="t('approval.fProjectCode')">{{ detail.business_obj.project_code }}</ExDefRow>
        <ExDefRow :label="t('approval.fCustomer')">{{ detail.business_obj.customer_name || '—' }}</ExDefRow>
        <ExDefRow :label="t('approval.fOwner')">{{ detail.business_obj.owner_name || '—' }}</ExDefRow>
        <ExDefRow v-if="detail.business_obj.sales_manager_name" :label="t('approval.fSalesManager')">{{ detail.business_obj.sales_manager_name }}</ExDefRow>
        <ExDefRow :label="t('approval.fIndustry')">{{ detail.business_obj.industry_label || detail.business_obj.industry || '—' }}</ExDefRow>
        <ExDefRow :label="t('approval.fLocation')">{{ [detail.business_obj.region, detail.business_obj.city].filter(Boolean).join(' · ') || '—' }}</ExDefRow>
        <ExDefRow :label="t('approval.fCurrentStage')">{{ detail.business_obj.stage_label || detail.business_obj.current_stage || '—' }}</ExDefRow>
        <ExDefRow v-if="detail.business_obj.project_type_label || detail.business_obj.project_type" :label="t('approval.fProjectType')">
          {{ detail.business_obj.project_type_label || detail.business_obj.project_type }}
        </ExDefRow>
        <ExDefRow v-if="detail.business_obj.authorization_status_label" :label="t('approval.fAuthStatus')">
          {{ detail.business_obj.authorization_status_label }}
        </ExDefRow>
        <ExDefRow v-if="detail.business_obj.authorization_code" :label="t('approval.fAuthCode')">{{ detail.business_obj.authorization_code }}</ExDefRow>
        <ExDefRow :label="t('approval.fDescription')" :last="true">{{ detail.business_obj.description || '—' }}</ExDefRow>
      </div>
      <!-- 批价单字段 -->
      <div v-else-if="detail.business_obj && isPricingOrder" :style="{ background: 'var(--color-ex-card)' }">
        <ExDefRow :label="t('approval.fOrderNumber')">{{ detail.business_obj.order_number }}</ExDefRow>
        <ExDefRow :label="t('approval.fProject')">{{ detail.business_obj.project_name || '—' }}</ExDefRow>
        <ExDefRow :label="t('approval.fCustomer')">{{ detail.business_obj.customer_name || '—' }}</ExDefRow>
        <ExDefRow v-if="detail.business_obj.quotation_number" :label="t('approval.fLinkedQuotation')">{{ detail.business_obj.quotation_number }}</ExDefRow>
        <ExDefRow v-if="detail.business_obj.dealer_name" :label="t('approval.fDealer')">{{ detail.business_obj.dealer_name }}</ExDefRow>
        <ExDefRow v-if="detail.business_obj.distributor_name" :label="t('approval.fDistributor')">{{ detail.business_obj.distributor_name }}</ExDefRow>
        <ExDefRow v-if="detail.business_obj.is_direct_contract" :label="t('approval.fDirectContract')">{{ t('approval.yes') }}</ExDefRow>
        <ExDefRow v-if="detail.business_obj.is_factory_pickup" :label="t('approval.fFactoryPickup')">{{ t('approval.yes') }}</ExDefRow>
        <ExDefRow :label="t('approval.fPricingAmount')">
          {{ currencySymbol(detail.business_obj.currency) }}{{ formatAmount(detail.business_obj.pricing_total_amount) }}
          <span v-if="detail.business_obj.pricing_total_discount_rate"
            :style="{ color: 'var(--color-ex-ink3)', fontSize: '11px', marginLeft: '6px' }">
            {{ t('approval.discountTip', { pct: ((detail.business_obj.pricing_total_discount_rate || 1) * 100).toFixed(1) }) }}
          </span>
        </ExDefRow>
        <ExDefRow v-if="detail.business_obj.settlement_total_amount" :label="t('approval.fSettlementAmount')">
          {{ currencySymbol(detail.business_obj.currency) }}{{ formatAmount(detail.business_obj.settlement_total_amount) }}
        </ExDefRow>
        <ExDefRow :label="t('approval.fApplicant')">{{ detail.business_obj.creator_name || '—' }}</ExDefRow>
        <ExDefRow :label="t('approval.fNotes')" :last="true">{{ detail.business_obj.notes || '—' }}</ExDefRow>
      </div>
      <!-- 报价单字段 -->
      <div v-else-if="detail.business_obj && isQuotation" :style="{ background: 'var(--color-ex-card)' }">
        <ExDefRow :label="t('approval.fQuotationNumber')">{{ detail.business_obj.quotation_number }}</ExDefRow>
        <ExDefRow :label="t('approval.fProject')">{{ detail.business_obj.project_name || '—' }}</ExDefRow>
        <ExDefRow :label="t('approval.fCustomer')">{{ detail.business_obj.customer_name || '—' }}</ExDefRow>
        <ExDefRow v-if="detail.business_obj.contact_name" :label="t('approval.fContact')">{{ detail.business_obj.contact_name }}</ExDefRow>
        <ExDefRow :label="t('approval.fOwner')">{{ detail.business_obj.owner_name || '—' }}</ExDefRow>
        <ExDefRow :label="t('approval.fQuoteAmount')">
          {{ currencySymbol(detail.business_obj.currency) }}{{ formatAmount(detail.business_obj.amount) }}
        </ExDefRow>
        <ExDefRow v-if="detail.business_obj.implant_total_amount" :label="t('approval.fImplantAmount')">
          {{ currencySymbol(detail.business_obj.currency) }}{{ formatAmount(detail.business_obj.implant_total_amount) }}
        </ExDefRow>
        <ExDefRow v-if="detail.business_obj.project_stage" :label="t('approval.fProjectStage')">{{ detail.business_obj.project_stage }}</ExDefRow>
        <ExDefRow v-if="detail.business_obj.project_type" :label="t('approval.fProjectType')">{{ detail.business_obj.project_type }}</ExDefRow>
        <ExDefRow :label="t('approval.fNotes')" :last="true">{{ detail.business_obj.notes || '—' }}</ExDefRow>
      </div>

      <!-- 明细 list -->
      <ExSectionHeader v-if="detail.business_obj?.lines?.length">
        {{ t('approval.detLines', { n: detail.business_obj.lines.length }) }}
      </ExSectionHeader>
      <div v-if="detail.business_obj?.lines?.length" :style="{ background: 'var(--color-ex-card)' }">
        <div
          v-for="(d, i) in detail.business_obj.lines"
          :key="d.id"
          class="flex items-center active:opacity-60 cursor-pointer"
          :style="{
            padding: '12px 20px',
            borderBottom: i < detail.business_obj.lines.length - 1 ? '1px solid var(--color-ex-divider-soft)' : 'none',
            gap: '12px',
          }"
          @click="openLineDetail(d)"
        >
          <div
            class="flex items-center justify-center flex-shrink-0 relative overflow-hidden"
            :style="{
              width: '40px', height: '40px', borderRadius: '4px',
              background: 'var(--color-ex-divider-soft)',
              color: 'var(--color-ex-ink4)', fontSize: '9px', fontWeight: 600,
            }"
          >
            <img v-if="lineThumbUrl(d)"
              :src="lineThumbUrl(d)"
              class="w-full h-full" style="object-fit: cover;"
              @error="$event.target.style.display='none'" />
            <span v-else>{{ t('approval.detInvoice') }}</span>
            <span v-if="(d.invoice_images?.length || 0) > 1"
              :style="{
                position: 'absolute', top: '-2px', right: '-2px',
                minWidth: '14px', height: '14px',
                borderRadius: '7px', padding: '0 3px',
                background: 'var(--color-ex-ink)', color: '#fff',
                fontSize: '8px', fontWeight: 700,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                border: '1.5px solid var(--color-ex-card)',
              }">{{ d.invoice_images.length }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <div :style="{ fontSize: '13px', fontWeight: 600 }">{{ d.category_label || d.category }}</div>
            <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginTop: '2px' }">
              {{ d.description }} · {{ d.expense_date }}
            </div>
          </div>
          <div :style="{ fontSize: '14px', fontFamily: 'var(--font-serif)', fontWeight: 500 }">
            {{ currencySymbol(d.currency) }}{{ formatAmount(d.invoice_amount) }}
          </div>
          <div :style="{ fontSize: '14px', color: 'var(--color-ex-ink4)' }">›</div>
        </div>
      </div>

      <!-- 明细详情 sheet — 当前审批人在 editable_fields 内字段可内联编辑 -->
      <ExLineDetailSheet
        v-model="lineDetailOpen"
        :line="selectedLine"
        :base-currency="detail.business_obj?.currency || 'CNY'"
        :editable-fields="editableLineFields"
        @save-field="onSaveLineField" />

      <!-- 审批进度 -->
      <!-- 之前底部「审批进度」section 已迁到顶部 chip 点击弹 ExFlowSheet,
           节省屏幕空间 + 进度查看入口更显眼 -->
    </div>

    <!-- 流程 sheet (顶部 chip 点击触发) -->
    <ExFlowSheet v-model="flowSheetOpen" :nodes="detail?.flow || []" />

    <!-- 底部审批操作 -->
    <div
      v-if="detail?.is_current_approver"
      class="absolute bottom-0 left-0 right-0 flex"
      :style="{
        padding: '12px 16px 28px',
        paddingBottom: 'calc(28px + env(safe-area-inset-bottom))',
        background: 'var(--color-ex-card)',
        borderTop: '1px solid var(--color-ex-divider)',
        gap: '10px',
      }"
    >
      <!-- ↻ 设计稿是历史按钮(audit 入口); 暂复用为转交触发, 转交 sheet 在弹出 -->
      <div
        class="flex items-center justify-center"
        :style="{
          width: '46px', height: '46px', borderRadius: '23px',
          background: 'var(--color-ex-divider-soft)',
          fontSize: '18px', color: 'var(--color-ex-ink2)',
        }"
        @click="openSheet('forward')"
      >↻</div>
      <div
        class="flex-1 flex items-center justify-center"
        :style="{
          height: '46px', borderRadius: '23px',
          background: 'var(--color-ex-card)',
          border: '1.5px solid var(--color-ex-red)',
          color: 'var(--color-ex-red)',
          fontSize: '14px', fontWeight: 600,
        }"
        @click="openSheet('reject')"
      >{{ t('approval.rejectBtn') }}</div>
      <div
        class="flex items-center justify-center"
        :style="{
          flex: 2,
          height: '46px', borderRadius: '23px',
          background: 'var(--color-ex-green)',
          color: 'var(--color-ex-card)',
          fontSize: '14px', fontWeight: 600,
        }"
        @click="openSheet('approve')"
      >{{ t('approval.approveBtn') }}</div>
    </div>

    <!-- 同意/驳回/转交 sheet -->
    <ApprovalSheet
      v-model="sheetOpen"
      :action="currentAction"
      :context-line="contextLine"
      :selected-user="selectedForwardUser"
      :submitting="submitting"
      :object-type-label="objectKindLabel"
      :object-kind="detail?.object_type || ''"
      @confirm="onConfirmAction"
      @pick-user="userPickerOpen = true"
    />

    <!-- 转交目标 user picker -->
    <ExSearchPickerSheet
      v-model="userPickerOpen"
      :title="t('approval.selectForwardTarget')"
      :placeholder="t('approval.searchUser')"
      :search-fn="searchUsers"
      @pick="onPickForwardUser"
    />

    <!-- 操作成功 toast -->
    <Teleport to="body">
      <transition name="ex-toast">
        <div v-if="toastVisible"
          class="fixed left-1/2 z-[60] flex items-center justify-center"
          :style="{
            top: 'calc(env(safe-area-inset-top) + 60px)',
            transform: 'translateX(-50%)',
            background: 'var(--color-ex-ink)',
            color: '#fff',
            padding: '10px 20px',
            borderRadius: '20px',
            fontSize: '13px',
            fontWeight: 500,
            boxShadow: '0 6px 16px rgba(0,0,0,0.18)',
          }">
          ✓ {{ toastText }}
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style scoped>
.ex-toast-enter-active, .ex-toast-leave-active { transition: opacity 0.2s, transform 0.2s; }
.ex-toast-enter-from, .ex-toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-10px);
}
</style>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import client from '@/api/client'

const { t } = useI18n()
import * as approvalApi from '@/api/approval'
import { lineThumbUrl } from '@/api/expense'
import ExLineDetailSheet from '@/components/expense/ExLineDetailSheet.vue'
import ExNav from '@/components/expense/ExNav.vue'
import ExSectionHeader from '@/components/expense/ExSectionHeader.vue'
import ExDefRow from '@/components/expense/ExDefRow.vue'
import ExFlowNode from '@/components/expense/ExFlowNode.vue'
import ExFlowSheet from '@/components/expense/ExFlowSheet.vue'
import ApprovalSheet from '@/components/expense/ApprovalSheet.vue'
import ExSearchPickerSheet from '@/components/expense/ExSearchPickerSheet.vue'
import ApplicantCard from '@/components/approval/ApplicantCard.vue'

const route = useRoute()
const router = useRouter()
const instanceId = computed(() => parseInt(route.params.instanceId))

const detail = ref(null)
const lineDetailOpen = ref(false)
const selectedLine = ref({})

function openLineDetail(d) {
  selectedLine.value = d
  lineDetailOpen.value = true
}
const loading = ref(false)
const sheetOpen = ref(false)
const flowSheetOpen = ref(false)
const currentAction = ref('approve')
const submitting = ref(false)
const userPickerOpen = ref(false)
const selectedForwardUser = ref(null)

const navTitle = computed(() => detail.value
  ? t('approval.detTitleWith', { name: detail.value.business_obj?.title || detail.value.object_name })
  : t('approval.detTitle'))
const navSub = computed(() => detail.value?.submitter
  ? t('approval.detSubmitterAt', { name: detail.value.submitter.name, date: (detail.value.created_at || '').slice(0, 10) })
  : '')

const currentStepName = computed(() => detail.value?.flow?.find(n => n.state === 'current')?.node || '')

// 业务对象 sheet 标题
const objectKindLabel = computed(() => {
  const ot = detail.value?.object_type
  if (ot === 'project') return t('approval.objProject')
  if (ot === 'expense') return t('approval.objExpense')
  if (ot === 'pricing_order') return t('approval.objPricing')
  if (ot === 'quotation') return t('approval.objQuotation')
  if (ot === 'purchase_order') return t('approval.objPurchase')
  return detail.value?.object_type_label || t('approval.objApproval')
})

// 区分业务对象类型
const isProject = computed(() => detail.value?.object_type === 'project')
const isExpense = computed(() => detail.value?.object_type === 'expense')
const isPricingOrder = computed(() => detail.value?.object_type === 'pricing_order')
const isQuotation = computed(() => detail.value?.object_type === 'quotation')

const amountStr = computed(() => {
  const b = detail.value?.business_obj
  if (!b) return '—'
  if (isProject.value) {
    return `¥ ${formatAmount(b.amount || b.total_amount || 0)}`
  }
  if (isPricingOrder.value) {
    return `${currencySymbol(b.currency)} ${formatAmount(b.pricing_total_amount || 0)}`
  }
  if (isQuotation.value) {
    return `${currencySymbol(b.currency)} ${formatAmount(b.amount || 0)}`
  }
  return `${currencySymbol(b.currency)} ${formatAmount(b.total_amount)}`
})

const waitingHint = computed(() => {
  if (!detail.value?.created_at) return ''
  const submitted = new Date(detail.value.created_at)
  const ms = Date.now() - submitted.getTime()
  const hours = Math.floor(ms / 3600000)
  if (hours < 1) return t('approval.waitJustNow')
  if (hours < 24) return t('approval.waitHours', { n: hours })
  const days = Math.floor(hours / 24)
  return t('approval.waitDays', { n: days })
})

const contextLine = computed(() => detail.value
  ? `${detail.value.business_obj?.expense_number || detail.value.object_name} · ${detail.value.business_obj?.title || ''} · ${amountStr.value}`
  : '')

function formatAmount(n) {
  return (Number(n) || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function currencySymbol(code) {
  const m = { CNY: '¥', USD: '$', HKD: 'HK$', TWD: 'NT$', SGD: 'S$', MYR: 'RM', IDR: 'Rp', THB: '฿', VND: '₫' }
  return m[code] || code
}
function currencyLabel(code) {
  const m = { CNY: '人民币', USD: '美元', HKD: '港币', TWD: '台币', SGD: '新加坡元', MYR: '马来西亚林吉特', IDR: '印尼盾', THB: '泰铢', VND: '越南盾' }
  return m[code] || code
}

async function load() {
  loading.value = true
  try {
    const r = await approvalApi.getApprovalDetail(instanceId.value)
    if (r.data?.success) detail.value = r.data.data
  } finally {
    loading.value = false
  }
}

// 当前审批人 + 报销审批 + step.editable_fields 决定明细可编辑字段
const editableLineFields = computed(() => {
  if (!detail.value?.is_current_approver) return []
  if (detail.value?.object_type !== 'expense') return []
  return detail.value?.editable_fields || []
})

// 内联编辑明细字段保存
async function onSaveLineField({ field, value, line, done }) {
  try {
    const payload = {}
    payload[field] = value
    const r = await client.patch(
      `/mobile/approval/${instanceId.value}/edit-line/${line.id}`,
      payload
    )
    if (r.data?.success) {
      // 同步更新本地 line + total
      const d = r.data.data
      Object.assign(line, {
        invoice_amount: d.invoice_amount,
        current_amount: d.current_amount,
        exchange_rate: d.exchange_rate,
      })
      if (detail.value?.business_obj) {
        detail.value.business_obj.total_amount = d.expense_total
      }
      done?.(null)
    } else {
      done?.(new Error(r.data?.message || t('approval.saveFailed')))
    }
  } catch (e) {
    done?.(new Error(e.response?.data?.message || e.message))
  }
}

function openSheet(action) {
  currentAction.value = action
  selectedForwardUser.value = null
  sheetOpen.value = true
}

async function onConfirmAction({ comment, targetUserId }) {
  submitting.value = true
  try {
    let resp
    if (currentAction.value === 'forward') {
      resp = await approvalApi.forwardApproval(instanceId.value, targetUserId, comment)
    } else {
      resp = await approvalApi.doApprovalAction(instanceId.value, currentAction.value, comment)
    }
    sheetOpen.value = false
    // 标记列表需要刷新(列表页 onActivated/onMounted 会重新拉)
    sessionStorage.setItem('approval-list-needs-refresh', '1')
    // 顶部 toast 浮现操作结果
    const msg = resp?.data?.message || (
      currentAction.value === 'approve' ? t('approval.actionApproved') :
      currentAction.value === 'reject'  ? t('approval.actionRejected') :
      currentAction.value === 'forward' ? t('approval.actionForwarded') : t('approval.actionDone')
    )
    showToast(msg)
    // 处理完后用户已无操作权(已驳回/已转交/已同意 → 当前步骤不再属于此用户)
    // 800ms 后自动返回审批列表(让用户看到 toast)
    setTimeout(() => router.back(), 800)
  } catch (e) {
    alert(t('approval.actionFailed') + ': ' + (e.response?.data?.message || e.message))
  } finally {
    submitting.value = false
  }
}

// 简易 toast (页面顶部短暂浮现)
const toastText = ref('')
const toastVisible = ref(false)
function showToast(text) {
  toastText.value = text
  toastVisible.value = true
  setTimeout(() => { toastVisible.value = false }, 2000)
}

async function searchUsers(q) {
  try {
    // 用专用端点(任何 jwt 用户都可调, 不查 user.view 权限)
    const r = await client.get('/mobile/approval/forward-targets', { params: { q: q || '' } })
    const items = r.data?.data?.items || []
    return items.map(u => ({
      id: u.id,
      label: u.name,
      sub: [u.department, u.company_name].filter(Boolean).join(' · ') || u.role,
      role_label: u.role || u.department,
    }))
  } catch (e) {
    console.warn('searchUsers failed:', e)
    return []
  }
}

function onPickForwardUser(it) {
  selectedForwardUser.value = {
    id: it.id,
    name: it.label,
    role_label: it.role_label || it.sub,
  }
}

onMounted(load)
</script>
