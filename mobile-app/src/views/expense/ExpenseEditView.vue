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

    <!-- Nav 表头: 取消(左) / 标题(中) / 保存草稿(右) — 底部 CTA 只留"提交审批" -->
    <div class="flex items-center justify-between shrink-0" style="padding: 10px 20px 8px;">
      <button @click="onCancel"
        class="active:opacity-60"
        style="font-size: 15px; color: #3A3A3A; font-weight: 500; background: none; border: none; padding: 0; min-width: 48px; text-align: left;">
        {{ t('common.cancel') }}
      </button>
      <div class="text-center flex-1">
        <div style="font-family: 'Noto Serif SC', Georgia, serif; font-size: 18px; font-weight: 500; color: #1A1A1A;">
          {{ editingId ? t('expense.editTitle') : t('expense.newTitle') }}
        </div>
        <div style="font-size: 11px; color: #7A7570; margin-top: 1px;">{{ navSub }}</div>
      </div>
      <button @click="onTopSave"
        class="active:opacity-60"
        :disabled="savingTop"
        style="font-size: 15px; color: var(--color-accent); font-weight: 500; background: none; border: none; padding: 0; min-width: 48px; text-align: right;">
        {{ savingTop ? t('expense.lineSaving') : t('expense.save') }}
      </button>
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
            {{ t('expense.fSubject') }}
            <span
              :style="{ color: titleGenerating ? 'var(--color-ex-warn)' : 'var(--color-ex-ink4)', fontWeight: 400, marginLeft: '4px' }"
            >
              {{ titleGenerating ? t('expense.fSubjectGenerating') : t('expense.fSubjectAi') }}
            </span>
          </div>
          <input
            v-model="form.title"
            :placeholder="t('expense.fSubjectPh')"
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
              {{ t('expense.settlementCurrency') }}
            </div>
            <div @click="currencyPickerOpen = true"
              :style="{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '14px',
                fontWeight: 500,
                color: 'var(--color-ex-ink)',
                lineHeight: '24px',
                cursor: 'pointer',
              }">
              {{ currencyDisplayLabel }}
              <span :style="{ color: 'var(--color-ex-ink4)', fontSize: '13px' }">›</span>
            </div>
          </div>
          <div class="flex-1">
            <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginBottom: '4px' }">{{ t('expense.fStatus') }}</div>
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
          <div :style="{ fontSize: '13px', color: 'var(--color-ex-ink2)' }">{{ t('expense.fNoLink') }}</div>
        </div>
        <div
          :style="{ padding: '0 20px 8px', fontSize: '11px', color: 'var(--color-ex-ink4)', marginLeft: '28px' }"
        >{{ form.no_link ? t('expense.fNoLinkOn') : t('expense.fNoLinkOff') }}</div>

        <!-- 关联客户 / 项目 (no_link=false 时) -->
        <template v-if="!form.no_link">
          <ExRow
            :label="t('expense.fLinkCustomer')"
            :value="form.customer_name || t('expense.fPleaseSelect')"
            :sub="form.customer_code ? t('expense.fCustomerCode', { code: form.customer_code }) : ''"
            @click="customerPickerOpen = true"
          />
          <ExRow
            :label="t('expense.fLinkProject')"
            :value="form.project_name || t('expense.fPleaseSelect')"
            @click="projectPickerOpen = true"
          />
        </template>

        <!-- 报销说明 -->
        <ExRow :label="t('expense.fDescription')" :multi="true">
          <textarea
            v-model="form.description"
            rows="3"
            :placeholder="t('expense.fDescriptionPh')"
            :style="{ background: 'transparent', border: 'none', fontSize: '14px', color: 'var(--color-ex-ink)', width: '100%', resize: 'none', outline: 'none', lineHeight: 1.55 }"
          />
        </ExRow>

        <!-- 申请人 -->
        <ExRow :label="t('expense.fApplicant')" :value="ownerName">
          <template #right>
            <span :style="{ fontSize: '10px', color: 'var(--color-ex-ink4)' }">{{ t('expense.fSystemDefault') }}</span>
          </template>
        </ExRow>

        <!-- 归属人 (默认自己; 选其他人会插入"归属人审批"节点) -->
        <ExRow :label="t('expense.fAttributedTo')"
               :value="form.attributed_to_name || t('expense.fAttributedSelf')"
               @click="attributedPickerOpen = true">
          <template #right>
            <span :style="{ fontSize: '13px', color: 'var(--color-ex-ink4)' }">›</span>
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
        >{{ t('expense.detailsHeader') }}</div>
        <div :style="{ fontSize: '12px', color: 'var(--color-ex-ink3)' }">
          {{ t('expense.itemsN', { n: lines.length }) }} ·
          <span
            :style="{ fontSize: '14px', fontWeight: 600, fontFamily: 'var(--font-serif)', color: 'var(--color-ex-ink)' }"
          >{{ currencySymbolFor(form.currency) }}{{ formatAmount(totalAmount) }}</span>
        </div>
      </div>

      <!-- 明细 · 空状态 (虚线卡 + 单 CTA 弹 4-option sheet) -->
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
          {{ t('expense.emptyHint') }}
        </div>
        <div
          class="flex items-center justify-center"
          :style="{
            height: '44px', borderRadius: '22px',
            background: 'var(--color-ex-ink)', color: 'var(--color-ex-card)',
            gap: '6px', fontSize: '13px', fontWeight: 600,
          }"
          @click="openAddOptions"
        >＋ {{ t('expense.addLineCTA') }}</div>
      </div>

      <!-- 明细 · 列表态 (左滑删除, 仅可编辑状态) -->
      <div v-else :style="{ background: 'var(--color-ex-card)' }">
        <SwipeRowAction
          v-for="(d, i) in lines"
          :key="d.id || i"
          :disabled="status !== 'draft' && status !== 'rejected'"
          :actions="[{ label: t('expense.deleteAction'), color: 'red', handler: () => d.id && onDeleteLine(d.id) }]"
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
            <span v-else>{{ d.invoice_images?.length ? t('expense.imgCount', { n: d.invoice_images.length }) : t('expense.invoiceLabel') }}</span>
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
              <span>{{ t('expense.docCountN', { n: d.document_count }) }}</span>
              <span>·</span>
              <span>{{ t('expense.rateAt', { r: (d.exchange_rate || 1).toFixed(4) }) }}</span>
            </div>
          </div>
        </div>
        </SwipeRowAction>
      </div>

      <!-- 续拍 / 添加 (有明细时显示) -->
      <div v-if="hasLines" class="flex" :style="{ padding: '14px 20px' }">
        <div
          class="flex-1 flex items-center justify-center"
          :style="{
            height: '42px', borderRadius: '21px',
            background: 'var(--color-ex-card)',
            border: '1.5px solid var(--color-ex-ink)',
            gap: '6px', fontSize: '13px', fontWeight: 600, color: 'var(--color-ex-ink)',
          }"
          @click="openAddOptions"
        >＋ {{ t('expense.addLineCTA') }}</div>
      </div>
    </div>

    <!-- 底部 CTA: 保存草稿。 提交审批移到详情页 (存草稿后 detail.control.can_submit
         才出现), 编辑态不提交流程 -->
    <ExBottomBar
      :primary="savingTop ? t('expense.lineSaving') : t('expense.save')"
      :disabled="savingTop"
      @primary="onTopSave"
    />

    <!-- 客户/项目 picker -->
    <ExSearchPickerSheet
      v-model="customerPickerOpen"
      :title="t('expense.pickCustomer')"
      :placeholder="t('expense.pickCustomerPh')"
      :search-fn="searchCustomers"
      @pick="onPickCustomer"
    />
    <ExSearchPickerSheet
      v-model="projectPickerOpen"
      :title="t('expense.pickProject')"
      :placeholder="t('expense.pickProjectPh')"
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
      :next-approver="{ user: t('expense.nextApprover'), node: t('expense.nextApproverNode') }"
      :submitting="submitting"
      @confirm="onConfirmSubmit"
    />

    <!-- 货币选择 sheet -->
    <ExPickerSheet
      v-model="currencyPickerOpen"
      :title="t('expense.settlementCurrency')"
      :options="currencyOptions"
      :selected="form.currency"
      @pick="onPickCurrency"
    />

    <!-- 添加明细 选项 sheet (拍照 / 相册 / 文件 / 手动) -->
    <Teleport to="body">
      <transition name="sheet">
        <div v-if="addOptionsSheetOpen"
          class="fixed inset-0 z-50 flex flex-col"
          :style="{ background: 'rgba(0,0,0,0.32)' }"
          @click.self="closeAddOptionsBackdrop">
          <div class="mt-auto"
            :style="{
              background: 'var(--color-ex-bg)',
              borderRadius: '20px 20px 0 0',
              paddingBottom: 'env(safe-area-inset-bottom)',
            }">
            <div :style="{ width: '36px', height: '4px', background: 'var(--color-ex-divider)', borderRadius: '2px', margin: '10px auto 6px' }" />
            <div class="px-5 pt-2 pb-3 text-center" :style="{ fontSize: '15px', fontWeight: 600 }">
              {{ t('expense.addLineCTA') }}
            </div>
            <div
              v-for="(opt, i) in addOptions"
              :key="opt.key"
              class="flex items-center"
              :style="{
                padding: '16px 20px',
                background: 'var(--color-ex-card)',
                borderTop: i === 0 ? '1px solid var(--color-ex-divider-soft)' : 'none',
                borderBottom: '1px solid var(--color-ex-divider-soft)',
                gap: '14px',
              }"
              @click="onAddOptionTap(opt.key)">
              <div :style="{ fontSize: '20px', width: '24px', textAlign: 'center' }">{{ opt.icon }}</div>
              <div class="flex-1">
                <div :style="{ fontSize: '14px', fontWeight: 600, color: 'var(--color-ex-ink)' }">{{ opt.label }}</div>
                <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginTop: '2px' }">{{ opt.sub }}</div>
              </div>
              <div :style="{ fontSize: '13px', color: 'var(--color-ex-ink4)' }">›</div>
            </div>
            <div class="text-center active:opacity-70"
              :style="{ padding: '14px 0', fontSize: '14px', color: 'var(--color-ex-ink3)' }"
              @click="addOptionsSheetOpen = false">
              {{ t('common.cancel') }}
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <!-- 隐藏 file input — 用于"从文件上传" (含 PDF) -->
    <input ref="fileInputEl"
      type="file"
      accept="image/*,application/pdf"
      multiple
      style="display: none;"
      @change="onFileInputChange" />

    <!-- 归属人 picker sheet (FilterSheet 风格的头像 chip) -->
    <Teleport to="body">
      <transition name="sheet">
        <div v-if="attributedPickerOpen"
          class="fixed inset-0 z-50 flex flex-col"
          :style="{ background: 'rgba(0,0,0,0.32)' }"
          @click.self="attributedPickerOpen = false">
          <div class="mt-auto flex flex-col"
            :style="{
              background: 'var(--color-ex-bg)',
              borderRadius: '20px 20px 0 0',
              maxHeight: '70vh',
              paddingBottom: 'env(safe-area-inset-bottom)',
            }">
            <div :style="{ width: '36px', height: '4px', background: 'var(--color-ex-divider)', borderRadius: '2px', margin: '10px auto 6px' }" />
            <div class="px-5 pt-2 pb-3 flex items-center justify-between shrink-0">
              <div :style="{ fontSize: '15px', fontWeight: 600 }">{{ t('expense.fAttributedTo') }}</div>
              <div :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)' }" @click="attributedPickerOpen = false">{{ t('common.cancel') }}</div>
            </div>
            <div class="overflow-auto" :style="{ padding: '12px 20px 20px' }">
              <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink4)', marginBottom: '12px', lineHeight: 1.5 }">
                {{ t('expense.fAttributedHint') }}
              </div>
              <div class="flex flex-wrap" :style="{ gap: '16px' }">
                <button v-for="(u, idx) in attributedCandidates"
                  :key="u.id"
                  type="button"
                  class="flex flex-col items-center gap-1 active:opacity-70"
                  @click="onPickAttributed(u)">
                  <div class="flex items-center justify-center"
                    :style="{
                      width: '44px', height: '44px', borderRadius: '22px',
                      background: (u.is_current_user && !form.attributed_to_id) || form.attributed_to_id === u.id
                        ? '#D97757' : attributedAvatarColor(idx),
                      color: '#fff', fontSize: '16px', fontWeight: 700,
                      transition: 'all 0.15s',
                    }"
                    :class="(u.is_current_user && !form.attributed_to_id) || form.attributed_to_id === u.id ? 'ring-2 ring-offset-1 ring-[#D97757]' : ''">
                    {{ (u.real_name || u.username || '?')[0] }}
                  </div>
                  <div :style="{ fontSize: '12px', color: 'var(--color-ex-ink2)', maxWidth: '56px', textAlign: 'center', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }">
                    {{ u.is_current_user ? t('expense.fAttributedSelf') : u.real_name }}
                  </div>
                  <div v-if="u.department" :style="{ fontSize: '10px', color: 'var(--color-ex-ink4)', maxWidth: '56px', textAlign: 'center', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }">
                    {{ u.department }}
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
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
import ExPickerSheet from '@/components/expense/ExPickerSheet.vue'
import SwipeRowAction from '@/components/common/SwipeRowAction.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const store = useExpenseStore()
const auth = useAuthStore()

const editingId = ref(parseInt(route.params.id) || null)
const isNew = computed(() => !editingId.value)
// 本次会话里因加明细/OCR 自动建出来的草稿(非从列表打开的旧草稿)
// 用于"取消即丢弃": 取消时删掉它, 不留在列表
const autoCreatedThisSession = ref(false)

// 默认货币: 用户结算货币 → 当前区域默认 (cn=CNY, sg=SGD)。
// 仅作初始值, 创建/编辑时可点头部货币行改 form.currency。
const defaultCurrency = (() => {
  const u = auth.user
  if (u?.settlement_currency) return u.settlement_currency
  return auth.regionId === 'sg' ? 'SGD' : 'CNY'
})()
const currencyDisplayLabel = computed(() => {
  const c = currencies.value?.find(x => x.code === form.value.currency)
  if (c) return `${c.label} ${c.symbol} (${c.code})`
  return form.value.currency || '—'
})
// 货币可选 (创建/编辑时点头部货币行打开选择器)
const currencyPickerOpen = ref(false)
const currencyOptions = computed(() =>
  (currencies.value || []).map(c => ({
    value: c.code,
    label: `${c.label || c.code} ${c.symbol || ''} (${c.code})`.replace(/\s+/g, ' ').trim(),
  })))
function onPickCurrency(code) {
  form.value.currency = code
  currencyPickerOpen.value = false
}

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
  attributed_to_id: null,  // null = 自己; 非空 = 归属其他人, 流程会插入"归属人审批"节点
  attributed_to_name: '',
})
// 归属人候选 (同公司所有 active 用户, 自己排最前) - onMounted 加载
const attributedCandidates = ref([])
const attributedPickerOpen = ref(false)

// 添加明细 4 选项 sheet
const addOptionsSheetOpen = ref(false)
const addSheetOpenedAt = ref(0)

// 打开加明细 sheet: 先收键盘(避免键盘收起重排与进场动画打架),
// nextTick 后再开 → 触发打开的那次点击事件已结束, 不会穿透到刚铺上的遮罩
async function openAddOptions() {
  try { document.activeElement?.blur?.() } catch (e) { /* noop */ }
  await nextTick()
  addSheetOpenedAt.value = Date.now()
  addOptionsSheetOpen.value = true
}

// 背景点击关闭: 刚打开 <350ms 内忽略 → 同一次手势的误触/穿透关不掉它
function closeAddOptionsBackdrop() {
  if (Date.now() - addSheetOpenedAt.value < 350) return
  addOptionsSheetOpen.value = false
}

const fileInputEl = ref(null)
const addOptions = computed(() => [
  { key: 'camera',  icon: '📷', label: t('expense.addOptCamera'),  sub: t('expense.addOptCameraSub') },
  { key: 'gallery', icon: '🖼',  label: t('expense.addOptGallery'), sub: t('expense.addOptGallerySub') },
  { key: 'file',    icon: '📄', label: t('expense.addOptFile'),    sub: t('expense.addOptFileSub') },
  { key: 'manual',  icon: '✏️', label: t('expense.addOptManual'),  sub: t('expense.addOptManualSub') },
])
const lines = ref([])
const status = ref('draft')

const categories = computed(() => store.categories)
const currencies = computed(() => store.currencies)

const hasLines = computed(() => lines.value.length > 0)
const navSub = computed(() => {
  if (editingId.value) {
    // 编辑模式: 显示单号 + 明细数
    const num = store.detailCache[editingId.value]?.expense_number || ''
    return `${num}${num ? ' · ' : ''}${t('expense.formLines', { n: lines.value.length })}`
  }
  // 新建模式: 用 step 引导
  return hasLines.value
    ? t('expense.subTitleStep2', { n: lines.value.length })
    : t('expense.subTitleStep1')
})
const contextLine = computed(() => {
  const parts = []
  if (form.value.customer_name) parts.push(form.value.customer_name)
  if (form.value.project_name) parts.push(form.value.project_name)
  return parts.join(' · ') || t('expense.noLinkedCustomer')
})
const statusLabel = computed(() => {
  const m = store.statuses.find(s => s.key === status.value)
  return m?.label || t('expense.defaultStatusDraft')
})
const ownerName = computed(() => auth.user?.real_name || auth.user?.username || '—')
const totalAmount = computed(() =>
  lines.value.reduce((s, l) => s + (Number(l.invoice_amount) || 0) * (Number(l.exchange_rate) || 1), 0))

function categoryLabel(key) { return store.categoryLabel(key) }
function currencySymbolFor(code) { return store.currencySymbol(code) }
function formatAmount(n) {
  return (n || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// canSubmit: 底部"提交审批"按钮启用条件 — 必须有明细 + 说明 + (关联客户/项目 或 不关联模式)
const canSubmit = computed(() => {
  if (!hasLines.value) return false
  if (!form.value.description.trim()) return false
  if (!form.value.no_link && (!form.value.customer_id || !form.value.project_id)) return false
  return true
})

// ── 加载已有报销单(编辑模式) ────────────────────
async function loadExisting() {
  if (!editingId.value) return
  const d = await store.fetchDetail(editingId.value, true)
  if (!d) return
  // 当 d.attributed_to.id 等于 owner_id 时, 视为"归属自己"(UI 不显示具体名字), 置 null
  const myId = auth.user?.id
  const attrId = d.attributed_to?.id
  const isSelfAttr = !attrId || attrId === myId || attrId === d.owner_id
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
    attributed_to_id: isSelfAttr ? null : attrId,
    attributed_to_name: isSelfAttr ? '' : (d.attributed_to?.name || ''),
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
    sub: c.primary_contact_name ? `${t('expense.mainContactPrefix')}: ${c.primary_contact_name}` : (c.industry || ''),
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
    attributed_to_id: form.value.attributed_to_id || null,
  })
  if (r.data?.success) {
    editingId.value = r.data.data.id
    autoCreatedThisSession.value = true  // 取消时该删
    // 草稿建好即把当前表单暂存到新 id, 之后走 OCR 跳页返回不丢手输内容
    store.stashCompose(editingId.value, form.value)
    triggerAutoTitle()  // fire-and-forget AI 生成标题
    return editingId.value
  }
  throw new Error(r.data?.message || t('expense.createFail'))
}

// AI 生成标题: 不阻塞用户(不 await 调用方), 但拿回结果原地写回 +
// 期间显示"生成标题中…", 完成自动替换, 用户无需手动刷新
const titleGenerating = ref(false)
async function triggerAutoTitle() {
  if (!editingId.value) return
  if (form.value.title.trim()) return  // 用户已手填, 不覆盖
  if (!form.value.description.trim()) return  // 没说明, AI 也无从生成
  titleGenerating.value = true
  try {
    const r = await expApi.autoTitle(editingId.value)
    const tt = r?.data?.data?.title
    if (tt && !form.value.title.trim()) form.value.title = tt
  } catch (e) {
    // 静默失败, 标题保持空, 不打扰用户
  } finally {
    titleGenerating.value = false
  }
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
    alert(t('expense.saveLineFail') + ': ' + (e.response?.data?.message || e.message))
  }
}

async function onDeleteLine(lineId) {
  if (!editingId.value) return
  try {
    await expApi.deleteLine(editingId.value, lineId)
    lines.value = lines.value.filter(l => l.id !== lineId)
  } catch (e) {
    alert(t('expense.deleteFailed') + ': ' + (e.response?.data?.message || e.message))
  }
}

// ── 拍发票 ───────────────────────────────────
async function onCapture() {
  const id = await ensureExpenseExists().catch(() => null)
  if (id) router.push(`/expense/${id}/capture`)
}

// ── 添加明细 4 选项分发 ──────────────────────────
async function onAddOptionTap(key) {
  addOptionsSheetOpen.value = false
  if (key === 'camera') return onCapture()
  if (key === 'manual') return openLineForm()
  if (key === 'gallery') return pickFromGallery()
  if (key === 'file') return pickFromFile()
}

// 从相册选(可多张). 每张走 OCR 识别流, 复用 processing → confirm 链路
async function pickFromGallery() {
  const id = await ensureExpenseExists().catch(() => null)
  if (!id) return
  try {
    const { Capacitor } = await import('@capacitor/core')
    if (Capacitor.isNativePlatform?.()) {
      const { Camera } = await import('@capacitor/camera')
      // pickImages 支持相册多选 (getPhoto 仅单张); 逐张走 OCR 链路
      const result = await Camera.pickImages({ quality: 90 })
      const photos = result?.photos || []
      if (!photos.length) return
      for (const p of photos) {
        const res = await fetch(p.webPath)
        const blob = await res.blob()
        _queueReceipt(blob, p.webPath)
      }
      _gotoProcessing(id)
    } else {
      // web fallback: 走文件 input
      pickFromFile()
    }
  } catch (e) {
    const msg = e?.message || String(e || '')
    if (msg.includes('cancelled') || msg.includes('canceled')) return
    alert(t('scan.galleryFail', { msg: msg.slice(0, 80) }))
  }
}

// 从文件选(可 PDF+图片混合多张). 弹原生文件选择器
// ⚠️ iOS WKWebView: input.click() 必须在用户手势同步周期内触发, 不能先 await
// (await 会丢失 user-activation → 选择器一闪而过)。建草稿挪到选完文件之后。
function pickFromFile() {
  fileInputEl.value?.click()
}

async function onFileInputChange(e) {
  const files = Array.from(e.target.files || [])
  e.target.value = ''  // 允许同一文件再次选择
  if (!files.length) return
  // 用户已选完文件 → 此时再建草稿(同步翻译延迟不再卡选择器弹出)
  const id = await ensureExpenseExists().catch(() => null)
  if (!id) return
  for (const f of files) {
    const isPdf = f.type === 'application/pdf' || /\.pdf$/i.test(f.name)
    // PDF 不渲染首页缩略 — 让 UI 显示 "📄 PDF" 占位, 点击走 iOS Safari 看
    const dataUrl = isPdf ? '' : URL.createObjectURL(f)
    _queueReceipt(f, dataUrl, { isPdf, filename: f.name })
  }
  _gotoProcessing(id)
}

function _queueReceipt(blob, dataUrl, meta = {}) {
  if (store.currentReceiptExpenseId !== editingId.value) {
    store.clearPendingReceipts()
    store.currentReceiptExpenseId = editingId.value
  }
  store.addPendingReceipt({ blob, dataUrl, ...meta })
}

function _gotoProcessing(id) {
  router.push(`/expense/${id}/processing`)
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
        attributed_to_id: form.value.attributed_to_id || null,
      })
      triggerAutoTitle()  // 描述更新可能影响标题, 重新触发 AI
    } else {
      await ensureExpenseExists()
    }
    autoCreatedThisSession.value = false  // 已主动保存为草稿, 取消时不再删
    return true
  } catch (e) {
    alert(t('expense.saveFail') + ': ' + (e.response?.data?.message || e.message))
    return false
  }
}

// 顶栏右上"保存": 保存草稿 + 返回. 客户/项目缺失时仅保存为不完整草稿(不提交流程)
const savingTop = ref(false)
async function onTopSave() {
  if (savingTop.value) return
  savingTop.value = true
  try {
    if (await saveDraft()) router.back()
  } finally {
    savingTop.value = false
  }
}

// 顶栏左上"取消": 若本次会话自动建了草稿且未主动保存/提交 → 删掉它,
// 不留在列表(软删 is_deleted)。从列表打开的旧草稿不受影响。
const cancelling = ref(false)
async function onCancel() {
  if (cancelling.value) return
  cancelling.value = true
  try {
    if (autoCreatedThisSession.value && editingId.value) {
      try { await expApi.deleteExpense(editingId.value) } catch (e) { /* 删失败也不挡返回 */ }
      store.clearCompose(editingId.value)
    }
  } finally {
    router.back()
  }
}

// 底部"提交审批": 保存最新数据 + 打开提交确认 sheet
async function onSubmit() {
  if (!canSubmit.value) return
  if (!await saveDraft()) return
  submitSheetOpen.value = true
}

async function onConfirmSubmit() {
  submitting.value = true
  try {
    const r = status.value === 'rejected'
      ? await expApi.resubmitExpense(editingId.value)
      : await expApi.submitExpense(editingId.value)
    if (r.data?.success) {
      autoCreatedThisSession.value = false  // 已提交, 取消时不再删
      store.clearCompose(editingId.value)  // 提交完成, 暂存作废
      submitSheetOpen.value = false
      router.replace(`/expense/${editingId.value}`)
    } else {
      alert(r.data?.message || t('expense.submitFail'))
    }
  } catch (e) {
    alert(t('expense.submitFail') + ': ' + (e.response?.data?.message || e.message))
  } finally {
    submitting.value = false
  }
}

// 本地暂存: 草稿已存在时, 表单任何改动写进 store(跨路由存活, 零服务器调用)
// hydrated 守卫: 恢复完成前不写, 避免默认值/loadExisting 覆盖已有暂存
const hydrated = ref(false)
watch(form, () => {
  if (!hydrated.value || !editingId.value) return
  store.stashCompose(editingId.value, form.value)
}, { deep: true })

onMounted(async () => {
  await store.loadReference()
  if (editingId.value) await loadExisting()
  // 返回本页时优先用本地暂存恢复手输内容(服务器值可能是建草稿那刻的旧值)
  if (editingId.value) {
    const stashed = store.getCompose(editingId.value)
    if (stashed) form.value = { ...form.value, ...stashed }
  }
  hydrated.value = true
  // 加载归属人候选(同公司用户). 失败不阻塞表单
  expApi.getAttributedCandidates()
    .then(r => { attributedCandidates.value = r.data?.data || [] })
    .catch(e => console.warn('[expense] load attributed candidates failed:', e?.message))
})

// 归属人选择
function onPickAttributed(u) {
  const myId = auth.user?.id
  if (!u || u.id === myId) {
    // 选"我自己" → 清空 attributed_to_id
    form.value.attributed_to_id = null
    form.value.attributed_to_name = ''
  } else {
    form.value.attributed_to_id = u.id
    form.value.attributed_to_name = u.real_name
  }
  attributedPickerOpen.value = false
}
function attributedAvatarColor(idx) {
  const palette = ['#3A6FB7', '#9B5DE5', '#2F7A4F', '#C77B22', '#B5453A', '#7A7570', '#1A1A1A']
  return palette[idx % palette.length]
}
</script>
