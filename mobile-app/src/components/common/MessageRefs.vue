<script setup>
// 消息附挂的引用卡列表（# 项目 / $ 客户 / § 合同）
// 放在 bubble 下方
import { REF_COMPONENT } from '@/utils/mentionRender'

defineProps({
  refs: { type: Array, default: () => [] },  // [{ type, item }]
  maxWidth: { type: String, default: '300px' },
})
</script>

<template>
  <div v-if="refs?.length" class="space-y-1.5"
    :style="{ maxWidth: maxWidth }">
    <component v-for="(r, i) in refs" :key="i"
      :is="REF_COMPONENT[r.type]" v-bind="r.item" />
  </div>
</template>
