<!--
  ExLineDetailSheet · 报销明细详情 sheet (只读查看)
  在 ExpenseDetail / ApprovalDetail 中点 明细行 → 弹出此 sheet
  显示: 完整字段 + 发票照片网格(点击放大全屏 + 左右切换)
-->
<template>
  <Teleport to="body">
    <transition name="ex-sheet">
      <div v-if="modelValue"
        class="fixed inset-0 z-50 flex flex-col"
        style="background: rgba(0,0,0,0.32);"
        @click.self="close">
        <div class="mt-auto flex flex-col"
          :style="{
            background: 'var(--color-ex-bg)',
            borderRadius: '20px 20px 0 0',
            maxHeight: '92vh',
            paddingBottom: 'env(safe-area-inset-bottom)',
          }">
          <!-- drag indicator -->
          <div :style="{ width: '36px', height: '4px', background: 'var(--color-ex-divider)', borderRadius: '2px', margin: '10px auto 6px' }" />

          <!-- 标题栏 -->
          <div class="px-5 pt-2 pb-3 flex items-center justify-between shrink-0">
            <div :style="{ fontSize: '15px', fontWeight: 600 }">{{ t('expense.lineSheetTitle') }}</div>
            <div :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)' }" @click="close">{{ t('expense.lineSheetClose') }}</div>
          </div>

          <!-- 内容滚动 -->
          <div class="overflow-auto" style="padding-bottom: 20px;">
            <!-- hero: 科目 + 金额 -->
            <div :style="{ padding: '12px 20px 18px' }">
              <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', letterSpacing: '0.4px' }">
                {{ categoryLabel }}
              </div>
              <div :style="{
                fontSize: '32px', fontWeight: 500,
                fontFamily: 'var(--font-serif)',
                color: 'var(--color-ex-ink)', lineHeight: 1, marginTop: '6px',
              }">{{ currencySymbol }} {{ formatAmount(line.invoice_amount) }}</div>
              <div :style="{ fontSize: '12px', color: 'var(--color-ex-ink3)', marginTop: '6px' }">
                {{ line.expense_date }}
                <template v-if="(line.document_count || 0) > 1">{{ t('expense.lineSheetMergedSuffix', { n: line.document_count }) }}</template>
              </div>
            </div>

            <!-- 字段表 -->
            <ExSectionHeader>{{ t('expense.lineSecFields') }}</ExSectionHeader>
            <div :style="{ background: 'var(--color-ex-card)' }">
              <ExDefRow :label="t('expense.lineFCategory')">{{ categoryLabel }}</ExDefRow>
              <ExDefRow :label="t('expense.lineFDate')">{{ line.expense_date }}</ExDefRow>
              <ExDefRow :label="t('expense.lineFDesc')">{{ line.description || '—' }}</ExDefRow>
              <ExDefRow :label="t('expense.lineFInvoiceAmt')">
                <span v-if="editingField !== 'invoice_amount'">
                  {{ currencySymbol }}{{ formatAmount(line.invoice_amount) }}
                  <span v-if="isEditable('invoice_amount')" role="button" class="active:opacity-60"
                    :style="{ marginLeft: '8px', fontSize: '12px', color: 'var(--color-ex-warn)', fontWeight: 600 }"
                    @click="startEdit('invoice_amount', line.invoice_amount)">{{ t('expense.lineEdit') }}</span>
                </span>
                <span v-else class="flex items-center" :style="{ gap: '6px' }">
                  <input v-model="editingValue" type="number" inputmode="decimal" step="0.01"
                    :style="{ fontSize: '13px', padding: '4px 8px', border: '1px solid var(--color-ex-divider)', borderRadius: '4px', width: '100px' }" />
                  <span role="button" class="active:opacity-60" :style="{ fontSize: '12px', color: 'var(--color-ex-warn)', fontWeight: 600 }" @click="commitEdit">{{ saving ? t('expense.lineSaving') : t('expense.lineSaveBtn') }}</span>
                  <span role="button" class="active:opacity-60" :style="{ fontSize: '12px', color: 'var(--color-ex-ink3)' }" @click="cancelEdit">{{ t('common.cancel') }}</span>
                </span>
              </ExDefRow>
              <ExDefRow :label="t('expense.lineFCurrency')">{{ currencyLabel }} ({{ line.currency }})</ExDefRow>
              <ExDefRow :label="t('expense.lineFRate')">
                <span v-if="editingField !== 'exchange_rate'">
                  {{ formatRate(line.exchange_rate) }}
                  <span v-if="isEditable('exchange_rate')" role="button" class="active:opacity-60"
                    :style="{ marginLeft: '8px', fontSize: '12px', color: 'var(--color-ex-warn)', fontWeight: 600 }"
                    @click="startEdit('exchange_rate', formatRate(line.exchange_rate))">{{ t('expense.lineEdit') }}</span>
                </span>
                <span v-else class="flex items-center" :style="{ gap: '6px' }">
                  <input v-model="editingValue" type="number" inputmode="decimal" step="0.0001"
                    :style="{ fontSize: '13px', padding: '4px 8px', border: '1px solid var(--color-ex-divider)', borderRadius: '4px', width: '100px' }" />
                  <span role="button" class="active:opacity-60" :style="{ fontSize: '12px', color: 'var(--color-ex-warn)', fontWeight: 600 }" @click="commitEdit">{{ saving ? t('expense.lineSaving') : t('expense.lineSaveBtn') }}</span>
                  <span role="button" class="active:opacity-60" :style="{ fontSize: '12px', color: 'var(--color-ex-ink3)' }" @click="cancelEdit">{{ t('common.cancel') }}</span>
                </span>
              </ExDefRow>
              <ExDefRow :label="t('expense.lineFAmount')">
                {{ baseSymbol }}{{ formatAmount(line.current_amount || line.invoice_amount) }}
              </ExDefRow>
              <ExDefRow :label="t('expense.lineFDocCount')" :last="!photos.length">{{ line.document_count || 1 }}</ExDefRow>
            </div>

            <!-- 发票照片网格 -->
            <ExSectionHeader v-if="photos.length">
              {{ t('expense.linePhotosHeader', { n: photos.length }) }}
            </ExSectionHeader>
            <div v-if="photos.length"
              class="grid"
              :style="{
                background: 'var(--color-ex-card)',
                padding: '12px 16px 16px',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '8px',
              }">
              <div v-for="(p, i) in photos" :key="i"
                @click="openPhotoViewer(i)"
                class="relative cursor-pointer overflow-hidden flex items-center justify-center"
                :style="{
                  aspectRatio: '1 / 1',
                  borderRadius: '6px',
                  background: 'var(--color-ex-divider-soft)',
                }">
                <img v-if="!p.isPdf"
                  :src="p.thumb || p.url"
                  class="w-full h-full"
                  style="object-fit: cover;"
                  @error="$event.target.style.display='none'" />
                <!-- PDF: 占位 + 角标 -->
                <div v-else class="flex flex-col items-center justify-center"
                  :style="{ color: '#7A7570', gap: '4px' }">
                  <span :style="{ fontSize: '24px' }">📄</span>
                  <span :style="{ fontSize: '10px', fontWeight: 600, letterSpacing: '0.5px' }">PDF</span>
                </div>
                <div v-if="p.isPdf"
                  :style="{
                    position: 'absolute', top: '4px', left: '4px',
                    padding: '1px 4px', borderRadius: '3px',
                    background: 'rgba(217,119,87,0.95)', color: '#fff',
                    fontSize: '9px', fontWeight: 600, letterSpacing: '0.5px',
                  }">PDF</div>
              </div>
            </div>

            <!-- 无照片提示 -->
            <div v-else :style="{
              padding: '16px 20px',
              textAlign: 'center',
              fontSize: '12px',
              color: 'var(--color-ex-ink4)',
            }">
              {{ t('expense.lineNoPhotos') }}
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 全屏图片查看器 (PDF 走 Capacitor Browser, 不进这层) -->
    <div v-if="viewerOpen"
      class="fixed inset-0 z-[60] flex flex-col"
      style="background: rgba(0,0,0,0.95);">
      <div class="flex items-center justify-between px-4 shrink-0"
        :style="{ paddingTop: 'calc(env(safe-area-inset-top) + 8px)', paddingBottom: '8px' }">
        <button @click="viewerOpen = false"
          class="flex items-center justify-center rounded-full active:opacity-70"
          style="width: 36px; height: 36px; background: rgba(255,255,255,0.16); color: #fff; font-size: 18px;">×</button>
        <span class="text-white text-[13px] opacity-80">{{ viewerIdx + 1 }} / {{ photos.length }}</span>
        <span style="width: 36px;" />
      </div>
      <div class="flex-1 flex items-center justify-center overflow-auto"
        @click="viewerOpen = false">
        <img :src="photos[viewerIdx].url"
          class="block"
          style="max-width: 100%; max-height: 100%; object-fit: contain;"
          @click.stop />
      </div>
      <div v-if="photos.length > 1"
        class="flex items-center justify-between px-6 shrink-0"
        :style="{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 16px)', paddingTop: '12px' }">
        <button @click="viewerIdx = (viewerIdx - 1 + photos.length) % photos.length"
          class="flex items-center justify-center rounded-full active:opacity-70"
          style="width: 44px; height: 44px; background: rgba(255,255,255,0.16); color: #fff; font-size: 20px;">‹</button>
        <span class="text-white text-[12px] opacity-60">{{ t('expense.lineTapBlankClose') }}</span>
        <button @click="viewerIdx = (viewerIdx + 1) % photos.length"
          class="flex items-center justify-center rounded-full active:opacity-70"
          style="width: 44px; height: 44px; background: rgba(255,255,255,0.16); color: #fff; font-size: 20px;">›</button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useExpenseStore } from '@/stores/expense'

const { t } = useI18n()
import { imageUrl } from '@/api/expense'
import ExSectionHeader from './ExSectionHeader.vue'
import ExDefRow from './ExDefRow.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  line: { type: Object, default: () => ({}) },
  baseCurrency: { type: String, default: 'CNY' },
  // 当前可编辑字段(由审批步骤 editable_fields 决定); 包含哪个字段就显示 ✏ chip
  editableFields: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue', 'save-field'])

// 内联编辑状态
const editingField = ref(null)   // 'exchange_rate' | 'invoice_amount' | null
const editingValue = ref('')
const saving = ref(false)
function isEditable(f) { return props.editableFields?.includes(f) }
function startEdit(field, current) {
  editingField.value = field
  editingValue.value = String(current ?? '')
}
function cancelEdit() {
  editingField.value = null
  editingValue.value = ''
}
async function commitEdit() {
  if (!editingField.value || saving.value) return
  saving.value = true
  try {
    await new Promise((resolve, reject) =>
      emit('save-field', {
        field: editingField.value,
        value: editingValue.value,
        line: props.line,
        done: (err) => err ? reject(err) : resolve(),
      })
    )
    cancelEdit()
  } catch (e) {
    alert(e?.message || t('expense.lineSaveFail'))
  } finally {
    saving.value = false
  }
}

const store = useExpenseStore()
const viewerOpen = ref(false)
const viewerIdx = ref(0)

const photos = computed(() => {
  const imgs = props.line?.invoice_images || []
  return imgs.map(im => {
    const fname = im.filename || ''
    const isPdf = fname.toLowerCase().endsWith('.pdf')
    return {
      url: imageUrl(im.url),
      thumb: imageUrl(im.thumb || im.url),
      filename: fname,
      isPdf,
    }
  })
})

// 用 iOS in-app Safari 打开 PDF (有完整 pinch zoom / 翻页 / 分享)
async function openInBrowser(url) {
  if (!url) return
  try {
    const { Capacitor } = await import('@capacitor/core')
    if (Capacitor.isNativePlatform?.()) {
      const { Browser } = await import('@capacitor/browser')
      await Browser.open({ url, presentationStyle: 'fullscreen' })
    } else {
      window.open(url, '_blank')
    }
  } catch (e) {
    console.warn('open in browser failed:', e?.message)
  }
}

const categoryLabel = computed(() => {
  // 兼容两种字段名(line.expense_category 来自 expense.lines, line.category 来自 approval lines)
  const key = props.line?.expense_category || props.line?.category
  if (props.line?.expense_category_label) return props.line.expense_category_label
  return store.categoryLabel(key) || key || '—'
})
const currencySymbol = computed(() => store.currencySymbol(props.line?.currency) || '¥')
const currencyLabel = computed(() => {
  const m = { CNY: '人民币', USD: '美元', HKD: '港币', TWD: '台币', SGD: '新加坡元', MYR: '马来西亚林吉特', IDR: '印尼盾', THB: '泰铢', VND: '越南盾' }
  return m[props.line?.currency] || props.line?.currency || ''
})
const baseSymbol = computed(() => store.currencySymbol(props.baseCurrency) || '¥')

function formatAmount(n) {
  return (Number(n) || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// Exchange rate display: 4-decimal precision but strip trailing zeros.
// 1 → '1', 1.2 → '1.2', 0.5795 → '0.5795', 1.2000 → '1.2'.
function formatRate(n) {
  const v = parseFloat(n)
  if (!isFinite(v) || v <= 0) return '1'
  return (Math.round(v * 10000) / 10000).toString()
}

function openPhotoViewer(i) {
  const p = photos.value[i]
  // PDF 直接调 iOS in-app Safari, 完整 pinch zoom / 翻页 / 分享
  if (p?.isPdf) {
    openInBrowser(p.url)
    return
  }
  viewerIdx.value = i
  viewerOpen.value = true
}

function close() {
  emit('update:modelValue', false)
  viewerOpen.value = false
}
</script>

<style scoped>
.ex-sheet-enter-active, .ex-sheet-leave-active { transition: opacity 0.2s; }
.ex-sheet-enter-from, .ex-sheet-leave-to { opacity: 0; }
</style>
