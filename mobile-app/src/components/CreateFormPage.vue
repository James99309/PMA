<script setup>
defineProps({
  title: { type: String, required: true },
  submitLabel: { type: String, default: '创建' },
  submitting: { type: Boolean, default: false },
})
const emit = defineEmits(['back', 'submit'])
</script>

<template>
  <div class="flex flex-col h-full bg-gray-50">
    <!-- 顶部导航（AppShell 已处理 safe-area-top，这里只需 44px） -->
    <div class="bg-white border-b border-gray-100 h-11 px-4 flex items-center justify-between shrink-0">
      <button @click="emit('back')" class="text-blue-500 text-sm py-1 pr-3">取消</button>
      <span class="font-semibold text-gray-900 text-sm">{{ title }}</span>
      <button @click="emit('submit')" :disabled="submitting"
        class="text-blue-500 text-sm font-medium py-1 pl-3 disabled:opacity-40">
        {{ submitting ? '提交中…' : submitLabel }}
      </button>
    </div>

    <!-- 滚动内容 -->
    <div class="flex-1 overflow-y-auto">
      <div class="bg-white mt-3 mx-3 rounded-2xl px-4 py-4 space-y-4 shadow-sm">
        <slot />
      </div>
      <div class="h-8" />
    </div>
  </div>
</template>
