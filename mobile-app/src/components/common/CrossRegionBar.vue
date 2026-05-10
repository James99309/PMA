<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
defineProps({
  regionFlag: { type: String, required: true },
  regionLabel: { type: String, required: true },
})
defineEmits(['back'])
</script>

<template>
  <div class="flex items-center gap-2 px-4 py-2"
    style="background: #FBF1DF; border-bottom: 1px solid #F6E4BE;">
    <span style="font-size: 13px;">{{ regionFlag }}</span>
    <span style="font-size: 12.5px; color: #6E4814; font-weight: 500;">
      {{ t('common.browsing') }} · <strong style="font-weight: 700;">{{ t('common.regionDb', { region: regionLabel }) }}</strong>
    </span>
    <button @click="$emit('back')" class="ml-auto active:opacity-70"
      style="font-size: 12px; color: #B8762A; font-weight: 600;">
      {{ t('common.switchBack') }} ›
    </button>
  </div>
</template>
