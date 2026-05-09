<!--
  ExPickerSheet · 通用底部 picker (chip 选项列表)
-->
<template>
  <Teleport to="body">
    <transition name="ex-picker">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex flex-col"
        :style="{ background: 'rgba(0,0,0,0.32)' }"
        @click.self="close"
      >
        <div
          class="mt-auto flex flex-col"
          :style="{
            background: 'var(--color-ex-bg)',
            borderRadius: '20px 20px 0 0',
            maxHeight: '70vh',
            paddingBottom: 'env(safe-area-inset-bottom)',
          }"
        >
          <div :style="{ width: '36px', height: '4px', background: 'var(--color-ex-divider)', borderRadius: '2px', margin: '10px auto 6px' }" />
          <div class="px-5 pt-2 pb-3 flex items-center justify-between shrink-0">
            <div :style="{ fontSize: '15px', fontWeight: 600 }">{{ title }}</div>
            <div :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)' }" @click="close">取消</div>
          </div>
          <div class="overflow-auto">
            <div
              v-for="o in options"
              :key="o.value"
              class="flex items-center justify-between"
              :style="{
                padding: '14px 20px',
                background: 'var(--color-ex-card)',
                borderBottom: '1px solid var(--color-ex-divider-soft)',
              }"
              @click="$emit('pick', o.value)"
            >
              <div :style="{ fontSize: '14px', color: 'var(--color-ex-ink)' }">{{ o.label }}</div>
              <div
                v-if="o.value === selected"
                :style="{ fontSize: '14px', color: 'var(--color-ex-accent)' }"
              >✓</div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '请选择' },
  options: { type: Array, default: () => [] },
  selected: { type: [String, Number], default: '' },
})
const emit = defineEmits(['update:modelValue', 'pick'])
function close() { emit('update:modelValue', false) }
</script>

<style scoped>
.ex-picker-enter-active, .ex-picker-leave-active { transition: opacity 0.2s; }
.ex-picker-enter-from, .ex-picker-leave-to { opacity: 0; }
</style>
