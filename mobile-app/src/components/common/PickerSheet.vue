<script setup>
// 通用底部 chip 选择器
// 用法：
//   <PickerSheet v-model="show" title="选择行业" :options="[{value,label},...]"
//                v-model:selected="form.industry" />
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
const { t } = useI18n()

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title:      { type: String,  default: '请选择' },
  options:    { type: Array,   default: () => [] },  // [{value,label}]
  selected:   { type: String,  default: '' },
})
const emit = defineEmits(['update:modelValue', 'update:selected'])

const open = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v),
})

function pick(v) {
  emit('update:selected', v)
  open.value = false
}
function clear() {
  emit('update:selected', '')
  open.value = false
}
</script>

<template>
  <Teleport to="body">
    <transition name="ps">
      <div v-if="open" class="fixed inset-0 z-50 flex flex-col"
        style="background: rgba(0,0,0,0.32);" @click.self="open = false">
        <div class="mt-auto rounded-t-3xl flex flex-col"
          style="background: var(--color-bg); max-height: 80vh; min-height: 40vh;">
          <div class="px-5 pt-4 pb-2 flex items-center justify-between shrink-0">
            <button @click="open = false" class="text-[13px]"
              style="color: var(--color-ink-3);">{{ t('common.cancel') }}</button>
            <span class="font-serif" style="font-size: 16px; font-weight: 500;">{{ title }}</span>
            <button @click="clear" class="text-[13px]"
              style="color: var(--color-accent);">{{ t('common.clear') }}</button>
          </div>
          <div class="flex-1 overflow-y-auto px-5 pb-6 pt-2">
            <div class="flex flex-wrap gap-2">
              <button v-for="opt in options" :key="opt.value"
                @click="pick(opt.value)" type="button"
                class="px-3.5 py-2 rounded-full text-[13px] font-medium transition-colors active:opacity-70"
                :style="selected === opt.value
                  ? { background: 'var(--color-ink)', color: '#fff', border: 'none', fontWeight: 600 }
                  : { background: 'var(--color-card)', color: 'var(--color-ink-2)', border: '1px solid var(--color-divider-strong)' }">
                {{ opt.label }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.ps-enter-active, .ps-leave-active { transition: opacity .18s; }
.ps-enter-from, .ps-leave-to { opacity: 0; }
</style>
