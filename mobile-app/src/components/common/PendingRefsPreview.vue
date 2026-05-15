<script setup>
// composer 上方的待发引用卡预览（# / $ / §），每张卡右上角有 × 移除按钮
import { REF_COMPONENT } from '@/utils/mentionRender'

defineProps({
  refs: { type: Array, default: () => [] },
})
defineEmits(['remove'])
</script>

<template>
  <div v-if="refs?.length" class="space-y-1.5">
    <div v-for="(r, i) in refs" :key="i" class="relative">
      <component :is="REF_COMPONENT[r.type]" v-bind="r.item" />
      <button @click="$emit('remove', i)"
        class="absolute -top-1 -right-1 w-5 h-5 rounded-full inline-flex items-center justify-center text-[11px] text-white shadow-md"
        style="background: var(--color-ink);">×</button>
    </div>
  </div>
</template>
