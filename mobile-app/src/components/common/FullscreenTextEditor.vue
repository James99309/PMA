<!--
  FullscreenTextEditor - generic "expand to full-screen" long-text editor.
  For notes / descriptions that need more room: one tap blows the small box
  up to full screen. props.value = current text; emits save(text) on save,
  discards on cancel. Full-screen flex layout, textarea fills the area above
  the keyboard, autofocus, 16px to avoid iOS zoom. UI text via t() (i18n).
-->
<template>
  <Teleport to="body">
    <transition name="fte">
      <div v-if="open" class="fixed inset-0 z-50"
        :style="{ background: '#F7F5F2', display: 'flex', flexDirection: 'column' }">
        <div class="status-pad" />
        <div :style="{ height: '52px', display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', padding: '0 16px',
          borderBottom: '1px solid #EBE6DD', flexShrink: 0 }">
          <span @click="cancel" class="active:opacity-60"
            :style="{ fontSize: '14px', color: '#7A7570' }">{{ t('common.cancel') }}</span>
          <span :style="{ fontSize: '15px', fontWeight: 600, color: '#1A1A1A' }">
            {{ title }}</span>
          <span @click="save" class="active:opacity-60"
            :style="{ fontSize: '14px', fontWeight: 600, color: '#D97757' }">
            {{ t('common.save') }}</span>
        </div>
        <textarea ref="ta" v-model="draft" :placeholder="placeholder"
          :style="{ flex: 1, width: '100%', boxSizing: 'border-box', padding: '18px 18px',
            background: '#F7F5F2', border: 'none', outline: 'none', resize: 'none',
            fontSize: '16px', lineHeight: 1.7, color: '#1A1A1A',
            paddingBottom: 'calc(18px + env(safe-area-inset-bottom))' }" />
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  value: { type: String, default: '' },
  title: { type: String, default: '' },
  placeholder: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'save'])

const open = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v),
})
const draft = ref('')
const ta = ref(null)

watch(() => props.modelValue, async v => {
  if (v) {
    draft.value = props.value || ''
    await nextTick()
    ta.value?.focus()
  }
})
function save() {
  emit('save', draft.value)
  open.value = false
}
function cancel() { open.value = false }
</script>

<style scoped>
.fte-enter-active, .fte-leave-active { transition: opacity .15s; }
.fte-enter-from, .fte-leave-to { opacity: 0; }
</style>
