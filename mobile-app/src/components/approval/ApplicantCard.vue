<!--
  ApplicantCard · 审批/详情页通用申请人卡片
  - 头像(首字母 + 主题色)
  - 姓名 · 部门
  - 可选 stats.text 行(后端按业务类型组装,如"本月报销 1 笔 · 平均 ¥837.06")
  - 右侧消息按钮(可选,emit 'message')
-->
<template>
  <div class="flex items-center"
    :style="{
      margin: '0 20px 16px',
      padding: '12px 14px',
      background: 'var(--color-ex-card)',
      borderRadius: '10px',
      border: '1px solid var(--color-ex-divider)',
      gap: '12px',
    }"
  >
    <div class="flex items-center justify-center flex-shrink-0"
      :style="{
        width: '38px', height: '38px', borderRadius: '19px',
        background: submitter.avatar_color || '#3A6FB7',
        color: '#fff', fontSize: '14px', fontWeight: 600,
      }"
    >{{ initial }}</div>
    <div class="flex-1 min-w-0">
      <div :style="{ fontSize: '13px', fontWeight: 600 }">
        {{ submitter.name }}
        <span v-if="submitter.department" :style="{ color: 'var(--color-ex-ink3)' }">· {{ submitter.department }}</span>
      </div>
      <div v-if="stats?.text"
        :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', marginTop: '2px' }"
      >{{ stats.text }}</div>
    </div>
    <div v-if="showMessage"
      role="button"
      class="flex items-center justify-center active:opacity-60 flex-shrink-0"
      :style="{
        width: '28px', height: '28px', borderRadius: '14px',
        background: 'var(--color-ex-divider-soft)',
        fontSize: '12px', color: 'var(--color-ex-ink3)',
      }"
      @click="$emit('message')"
    >✉</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  submitter: { type: Object, required: true }, // {name, department?, avatar_color?}
  stats: { type: Object, default: null },      // {text: string} | null
  showMessage: { type: Boolean, default: true },
})
defineEmits(['message'])

const initial = computed(() => (props.submitter?.name || '?').slice(0, 1))
</script>
