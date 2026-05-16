<script setup>
// 编辑/新建表单顶部 — 严格对齐设计稿 edit-project.jsx
// 左：取消（默认 router.back）
// 中：标题（serif 18px）+ 副标题（11px ink3，必填进度提示）
// 右：保存胶囊按钮（dirty + 全填齐 → accent 橙；否则 ink4 灰）
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
const { t } = useI18n()

const props = defineProps({
  title: { type: String, required: true },
  saving: { type: Boolean, default: false },
  dirty: { type: Boolean, default: true },          // 是否有未保存改动
  missingCount: { type: Number, default: 0 },       // 必填未完成数量
  cancelLabel: { type: String, default: '' },       // 空 → 用 i18n common.cancel
  saveLabel: { type: String, default: '' },         // 空 → 用 i18n common.save
})
defineEmits(['cancel', 'save'])

const subtitle = computed(() =>
  props.missingCount > 0
    ? t('common.requiredMissing', { n: props.missingCount })
    : t('common.allRequiredDone')
)
const canSave = computed(() => props.dirty && props.missingCount === 0 && !props.saving)
</script>

<template>
  <div class="flex items-center justify-between"
    style="padding: 10px 20px 8px;">
    <button @click="$emit('cancel')" type="button"
      class="active:opacity-60 shrink-0"
      style="font-size: 15px; color: var(--color-ink-2); font-weight: 500;">
      {{ cancelLabel || t('common.cancel') }}
    </button>

    <div class="text-center flex-1 min-w-0">
      <div class="font-serif"
        style="font-size: 18px; font-weight: 500; color: var(--color-ink);">{{ title }}</div>
      <div style="font-size: 11px; color: var(--color-ink-3); margin-top: 1px;">
        {{ saving ? t('common.saving2') : subtitle }}
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
      {{ saveLabel || t('common.save') }}
    </button>
  </div>
</template>
