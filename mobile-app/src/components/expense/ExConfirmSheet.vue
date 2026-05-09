<!--
  ExConfirmSheet · 通用二次确认 sheet (召回/删除等单选确认)
  对齐 ExSubmitSheet 视觉风格 (drag + eyebrow + serif title + sub + 取消/确认 按钮)
  - color: 'red' (危险动作如删除) / 'ink' (普通确认)
-->
<template>
  <Teleport to="body">
    <transition name="ex-confirm-sheet">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50"
        :style="{ background: 'rgba(26,26,26,0.42)' }"
        @click.self="close"
      >
        <div
          class="absolute left-0 right-0 bottom-0"
          :style="{
            background: 'var(--color-ex-bg)',
            borderRadius: '20px 20px 0 0',
            padding: '14px 20px 26px',
            paddingBottom: 'calc(26px + env(safe-area-inset-bottom))',
            boxShadow: 'var(--shadow-ex-sheet)',
          }"
        >
          <div :style="{ width: '36px', height: '4px', background: 'var(--color-ex-divider)', borderRadius: '2px', margin: '0 auto 14px' }" />
          <div :style="{ fontSize: '11px', color: cfgColor, letterSpacing: '0.6px', fontWeight: 600 }">
            {{ eyebrow }}
          </div>
          <div
            :style="{
              fontSize: '22px', fontWeight: 500, fontFamily: 'var(--font-serif)',
              color: 'var(--color-ex-ink)', marginTop: '4px',
            }"
          >{{ title }}</div>
          <div
            v-if="sub"
            :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)', marginTop: '4px' }"
          >{{ sub }}</div>

          <!-- CTA -->
          <div class="flex" :style="{ gap: '10px', marginTop: '20px' }">
            <div
              class="flex-1 flex items-center justify-center"
              role="button"
              :style="{
                height: '48px', borderRadius: '24px',
                background: 'var(--color-ex-card)',
                border: '1.5px solid var(--color-ex-divider)',
                color: 'var(--color-ex-ink2)',
                fontSize: '14px', fontWeight: 600,
              }"
              @click="close"
            >取消</div>
            <div
              class="flex items-center justify-center"
              role="button"
              :style="{
                flex: 2,
                height: '48px',
                borderRadius: '24px',
                background: cfgColor,
                color: '#fff',
                fontSize: '14px',
                fontWeight: 600,
              }"
              @click="onConfirm"
            >{{ submitting ? '处理中...' : confirmLabel }}</div>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  eyebrow:    { type: String, default: '操作' },
  title:      { type: String, default: '确认?' },
  sub:        { type: String, default: '' },
  confirmLabel: { type: String, default: '确认' },
  color:      { type: String, default: 'ink' },  // ink / red / warn / blue / green
  submitting: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'confirm'])

const cfgColor = computed(() => {
  const map = {
    ink: 'var(--color-ex-ink)',
    red: 'var(--color-ex-red)',
    warn: 'var(--color-ex-warn)',
    blue: 'var(--color-ex-blue)',
    green: 'var(--color-ex-green)',
  }
  return map[props.color] || map.ink
})

function close() { emit('update:modelValue', false) }
function onConfirm() { if (!props.submitting) emit('confirm') }
</script>

<style scoped>
.ex-confirm-sheet-enter-active, .ex-confirm-sheet-leave-active { transition: opacity 0.2s; }
.ex-confirm-sheet-enter-from, .ex-confirm-sheet-leave-to { opacity: 0; }
</style>
