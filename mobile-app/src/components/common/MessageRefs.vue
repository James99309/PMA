<script setup>
// 消息附挂的引用卡列表（# 项目 / $ 客户）
// 点击 → 跳转对应详情页
import { useRouter } from 'vue-router'
import { REF_COMPONENT } from '@/utils/mentionRender'

defineProps({
  refs: { type: Array, default: () => [] },  // [{ type, item }]
  maxWidth: { type: String, default: '300px' },
})

const router = useRouter()

function onCardClick(r) {
  const id = r?.item?.id
  if (!id) return
  if (r.type === '#') {
    router.push(`/projects/${id}`)
  } else if (r.type === '$') {
    router.push(`/customers/${id}`)
  }
}
</script>

<template>
  <div v-if="refs?.length" class="space-y-1.5"
    :style="{ maxWidth: maxWidth }">
    <component v-for="(r, i) in refs" :key="i"
      :is="REF_COMPONENT[r.type]" v-bind="r.item"
      @click="onCardClick(r)" />
  </div>
</template>
