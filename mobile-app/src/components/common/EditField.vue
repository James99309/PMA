<script setup>
// 字段行 — 严格对齐设计稿 edit-project.jsx FieldRow
// 双层结构：小标签 11px + 大值 16px
// required: 标签后红 *；highlight: 必填未填，标签变橙
import { computed, ref } from 'vue'
import FullscreenTextEditor from '@/components/common/FullscreenTextEditor.vue'

const props = defineProps({
  label:    { type: String, required: true },
  modelValue: { type: [String, Number, null], default: '' },
  placeholder: { type: String, default: '' },
  focused:  { type: Boolean, default: false },
  arrow:    { type: Boolean, default: false },
  readonly: { type: Boolean, default: false },
  type:     { type: String, default: 'text' },
  required: { type: Boolean, default: false },
  highlight:{ type: Boolean, default: false },  // 必填未填高亮
  multiline:{ type: Boolean, default: false },
  // editor: editable long text → tap opens the shared full-screen editor
  // (keyboard never covers it; reusable for any multi-line field)
  editor:   { type: Boolean, default: false },
  last:     { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'click'])

const empty = computed(() => !props.modelValue)
const labelColor = computed(() => props.highlight ? 'var(--color-accent)' : 'var(--color-ink-3)')

const editorOpen = ref(false)
const isEditor = computed(() => props.editor && !props.readonly)
function onEditorSave(v) { emit('update:modelValue', v) }
</script>

<template>
  <div class="flex items-center gap-2.5"
    :style="{
      padding: '12px 16px',
      borderBottom: last ? 'none' : '1px solid var(--color-divider)',
    }"
    @click="$emit('click')">
    <div class="flex-1 min-w-0">
      <div :style="{
        fontSize: '11px',
        color: labelColor,
        fontWeight: 500,
        marginBottom: '4px',
        letterSpacing: '0.3px',
      }">
        {{ label }}<span v-if="required && !highlight"
          style="color: var(--color-accent); margin-left: 3px;">*</span>
      </div>
      <input v-if="!readonly && !arrow && !editor"
        :value="modelValue"
        :type="type"
        :placeholder="placeholder"
        @input="$emit('update:modelValue', $event.target.value)"
        class="w-full bg-transparent outline-none"
        :style="{
          fontSize: '16px',
          color: 'var(--color-ink)',
          fontWeight: 500,
          fontFamily: 'var(--font-sans)',
          lineHeight: '1.3',
        }" />
      <div v-else-if="isEditor"
        @click.stop="editorOpen = true"
        :style="{
          fontSize: '14px',
          color: empty ? 'var(--color-ink-3)' : 'var(--color-ink)',
          fontWeight: empty ? 400 : 500,
          fontStyle: empty ? 'italic' : 'normal',
          fontFamily: empty ? 'var(--font-serif)' : 'var(--font-sans)',
          lineHeight: '1.55',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          maxHeight: '7.7em',
          overflow: 'hidden',
        }">
        {{ modelValue || placeholder || '—' }}
      </div>
      <div v-else
        :style="{
          fontSize: multiline ? '14px' : '16px',
          color: empty ? 'var(--color-ink-3)' : 'var(--color-ink)',
          fontWeight: empty ? 400 : 500,
          fontStyle: empty ? 'italic' : 'normal',
          fontFamily: empty ? 'var(--font-serif)' : 'var(--font-sans)',
          lineHeight: multiline ? '1.55' : '1.3',
          overflow: multiline ? 'visible' : 'hidden',
          textOverflow: multiline ? 'clip' : 'ellipsis',
          whiteSpace: multiline ? 'normal' : 'nowrap',
        }">
        {{ modelValue || placeholder || '—' }}
      </div>
    </div>
    <svg v-if="arrow || isEditor" width="8" height="12" viewBox="0 0 8 12" fill="none" class="shrink-0">
      <path d="M2 2l4 4-4 4" stroke="var(--color-ink-3)" stroke-width="1.4" stroke-linecap="round" />
    </svg>
    <FullscreenTextEditor v-if="isEditor" v-model="editorOpen"
      :value="String(modelValue == null ? '' : modelValue)"
      :title="label" :placeholder="placeholder" @save="onEditorSave" />
  </div>
</template>
