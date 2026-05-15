<!--
  ExLineFormSheet · 手动添加/编辑明细 sheet
  字段: 报销科目 / 发生日期 / 金额 / 币种 / 描述 / 单据数
-->
<template>
  <Teleport to="body">
    <transition name="sheet">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex flex-col"
        :style="{ background: 'rgba(0,0,0,0.32)' }"
        @click.self="close"
      >
        <div
          class="mt-auto flex flex-col"
          :style="[{
            background: 'var(--color-ex-bg)',
            borderRadius: '20px 20px 0 0',
            maxHeight: '90vh',
          }, kbStyle]"
        >
          <div :style="{ width: '36px', height: '4px', background: 'var(--color-ex-divider)', borderRadius: '2px', margin: '10px auto 6px' }" />
          <div class="px-5 pt-2 pb-3 flex items-center justify-between shrink-0">
            <div :style="{ fontSize: '15px', fontWeight: 600 }">{{ form.id ? t('expense.lineFormEditTitle') : t('expense.lineFormNewTitle') }}</div>
            <div :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)' }" @click="close">{{ t('expense.lineFormCancel') }}</div>
          </div>

          <div class="overflow-auto" :style="{ paddingBottom: '12px' }">
            <ExRow :label="t('expense.lineFormFCategory')">
              <select
                v-model="form.expense_category"
                :style="{ background: 'transparent', border: 'none', fontSize: '14px', color: 'var(--color-ex-ink)', width: '100%' }"
              >
                <option v-for="c in categories" :key="c.key" :value="c.key">{{ c.label }}</option>
              </select>
            </ExRow>

            <ExRow :label="t('expense.lineFormFDate')">
              <input
                v-model="form.expense_date"
                type="date"
                :style="{ background: 'transparent', border: 'none', fontSize: '14px', color: 'var(--color-ex-ink)', width: '100%' }"
              />
            </ExRow>

            <ExRow :label="t('expense.lineFormFAmount')">
              <input
                v-model.number="form.invoice_amount"
                type="number"
                step="0.01"
                placeholder="0.00"
                :style="{ background: 'transparent', border: 'none', fontSize: '14px', color: 'var(--color-ex-ink)', width: '100%' }"
              />
            </ExRow>

            <ExRow :label="t('expense.lineFormFCurrency')">
              <select
                v-model="form.currency"
                :style="{ background: 'transparent', border: 'none', fontSize: '14px', color: 'var(--color-ex-ink)', width: '100%' }"
              >
                <option v-for="c in currencies" :key="c.code" :value="c.code">
                  {{ c.label }} {{ c.symbol }} ({{ c.code }})
                </option>
              </select>
            </ExRow>

            <ExRow :label="t('expense.lineFormFDesc')" :multi="true">
              <textarea
                v-model="form.description"
                rows="2"
                :placeholder="t('expense.lineFormFDescPh')"
                :style="{ background: 'transparent', border: 'none', fontSize: '14px', color: 'var(--color-ex-ink)', width: '100%', resize: 'none' }"
              />
            </ExRow>

            <ExRow :label="t('expense.lineFormFDocCount')">
              <input
                v-model.number="form.document_count"
                type="number"
                min="1"
                :style="{ background: 'transparent', border: 'none', fontSize: '14px', color: 'var(--color-ex-ink)', width: '100%' }"
              />
            </ExRow>
          </div>

          <div
            class="flex"
            :style="{ padding: '12px 16px 18px', gap: '10px', borderTop: '1px solid var(--color-ex-divider)', background: 'var(--color-ex-card)' }"
          >
            <div
              v-if="form.id"
              class="flex-1 flex items-center justify-center"
              :style="{
                height: '46px', borderRadius: '23px',
                background: 'var(--color-ex-card)',
                border: '1.5px solid var(--color-ex-red)',
                color: 'var(--color-ex-red)',
                fontSize: '14px', fontWeight: 600,
              }"
              @click="$emit('delete', form.id); close()"
            >{{ t('expense.lineFormDelete') }}</div>
            <div
              class="flex items-center justify-center"
              :style="{
                flex: form.id ? 2 : 1,
                height: '46px',
                borderRadius: '23px',
                background: canSave ? 'var(--color-ex-ink)' : 'var(--color-ex-divider)',
                color: canSave ? 'var(--color-ex-card)' : 'var(--color-ex-ink4)',
                fontSize: '14px',
                fontWeight: 600,
              }"
              @click="canSave && save()"
            >{{ t('expense.lineFormSave') }}</div>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import ExRow from './ExRow.vue'
import { useKeyboardOffset } from '@/composables/useKeyboardOffset'

const { kbStyle } = useKeyboardOffset()
const { t } = useI18n()

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  initial:    { type: Object,  default: null },
  categories: { type: Array,   default: () => [] },
  currencies: { type: Array,   default: () => [] },
  defaultCurrency: { type: String, default: 'CNY' },
})
const emit = defineEmits(['update:modelValue', 'save', 'delete'])

const today = new Date().toISOString().slice(0, 10)
const form = ref(makeForm())

function makeForm(src) {
  return {
    id: src?.id || null,
    expense_category: src?.expense_category || 'other',
    expense_date: src?.expense_date || today,
    invoice_amount: src?.invoice_amount ?? 0,
    currency: src?.currency || props.defaultCurrency,
    description: src?.description || '',
    document_count: src?.document_count || 1,
  }
}

watch(() => props.modelValue, (v) => {
  if (v) form.value = makeForm(props.initial)
})

const canSave = computed(() =>
  form.value.expense_category && form.value.expense_date &&
  form.value.invoice_amount > 0 && form.value.currency,
)

function save() {
  emit('save', { ...form.value })
  close()
}
function close() { emit('update:modelValue', false) }
</script>

<style scoped>
.sheet-enter-active, .sheet-leave-active { transition: opacity 0.2s; }
.sheet-enter-from, .sheet-leave-to { opacity: 0; }
</style>
