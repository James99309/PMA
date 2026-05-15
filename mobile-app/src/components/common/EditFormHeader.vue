<script setup>
// 编辑/新建表单顶部 — 严格对齐设计稿 edit-project.jsx
// 左：取消（默认 router.back）
// 中：标题（serif 18px）+ 副标题（11px ink3，必填进度提示）
// 右：保存胶囊按钮（dirty + 全填齐 → accent 橙；否则 ink4 灰）
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  saving: { type: Boolean, default: false },
  dirty: { type: Boolean, default: true },          // 是否有未保存改动
  missingCount: { type: Number, default: 0 },       // 必填未完成数量
  cancelLabel: { type: String, default: '取消' },
  saveLabel: { type: String, default: '保存' },
})
defineEmits(['cancel', 'save'])

const subtitle = computed(() =>
  props.missingCount > 0 ? `${props.missingCount} 项必填未完成` : '所有必填已完成'
)
const canSave = computed(() => props.dirty && props.missingCount === 0 && !props.saving)
</script>

<template>
  <div class="flex items-center justify-between"
    style="padding: 10px 20px 8px;">
    <button @click="$emit('cancel')" type="button"
      class="active:opacity-60 shrink-0"
      style="font-size: 15px; color: var(--color-ink-2); font-weight: 500;">
      {{ cancelLabel }}
    </button>

    <div class="text-center flex-1 min-w-0">
      <div class="font-serif"
        style="font-size: 18px; font-weight: 500; color: var(--color-ink);">{{ title }}</div>
      <div style="font-size: 11px; color: var(--color-ink-3); margin-top: 1px;">
        {{ saving ? '保存中…' : subtitle }}
      </div>
    </div>

    <button @click="canSave && $emit('save')" type="button"
      class="active:opacity-80 shrink-0"
      :disabled="!canSave"
      :style="{
        fontSize: '13px',
        fontWeight: 600,
        color: '#fff',
        background: canSave ? 'var(--color-accent)' : 'var(--color-ink-4)',
        padding: '6px 14px',
        borderRadius: '999px',
        border: 'none',
      }">
      {{ saveLabel }}
    </button>
  </div>
</template>
