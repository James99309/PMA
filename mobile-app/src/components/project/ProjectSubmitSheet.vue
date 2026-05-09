<!--
  ProjectSubmitSheet · 项目提交审批确认 sheet
  视觉对齐 ExSubmitSheet (报销),展示项目摘要而非金额明细
  字段:项目名(主体) + 项目类型徽章 + 关联客户 + 负责人 + 预计金额
-->
<template>
  <Teleport to="body">
    <transition name="proj-submit-sheet">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50"
        :style="{ background: 'rgba(26,26,26,0.42)' }"
        @click.self="close"
      >
        <div
          class="absolute left-0 right-0 bottom-0"
          :style="{
            background: 'var(--color-ex-bg)',
            borderRadius: '20px 20px 0 0',
            padding: '14px 20px 24px',
            boxShadow: 'var(--shadow-ex-sheet)',
            paddingBottom: 'calc(24px + env(safe-area-inset-bottom))',
          }"
        >
          <div :style="{
            width: '36px', height: '4px',
            background: 'var(--color-ex-divider)',
            borderRadius: '2px', margin: '0 auto 14px',
          }" />
          <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', letterSpacing: '0.6px' }">
            提交审批
          </div>
          <div :style="{
            fontSize: '22px', fontWeight: 500,
            fontFamily: 'var(--font-serif)',
            color: 'var(--color-ex-ink)',
            marginTop: '4px',
          }">确认提交?</div>

          <!-- 项目信息卡 -->
          <div :style="{
            marginTop: '16px', padding: '14px',
            background: 'var(--color-ex-card)',
            borderRadius: '10px',
            border: '1px solid var(--color-ex-divider)',
          }">
            <!-- 项目名 + 类型徽章 -->
            <div class="flex items-start justify-between" :style="{ gap: '10px' }">
              <div :style="{
                fontSize: '15px', fontWeight: 600,
                color: 'var(--color-ex-ink)', lineHeight: 1.4, flex: 1,
              }">{{ projectName || '—' }}</div>
              <span v-if="projectType" :style="typeBadgeStyle">{{ projectTypeLabel }}</span>
            </div>

            <div :style="{ height: '1px', background: 'var(--color-ex-divider-soft)', margin: '10px 0' }" />

            <div :style="{ fontSize: '12px', color: 'var(--color-ex-ink3)', lineHeight: 1.7 }">
              <div class="flex justify-between">
                <span>关联客户</span>
                <span :style="{ color: 'var(--color-ex-ink2)' }">{{ customerName || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span>负责人</span>
                <span :style="{ color: 'var(--color-ex-ink2)' }">{{ ownerName || '—' }}</span>
              </div>
              <div v-if="amount" class="flex justify-between">
                <span>预计签约金额</span>
                <span :style="{ color: 'var(--color-ex-ink2)' }">{{ amount }}</span>
              </div>
              <div v-if="stage" class="flex justify-between">
                <span>当前阶段</span>
                <span :style="{ color: 'var(--color-ex-ink2)' }">{{ stage }}</span>
              </div>
            </div>
          </div>

          <!-- 下一节点提示 -->
          <div :style="{
            marginTop: '12px', padding: '10px 12px',
            background: 'var(--color-ex-warn-soft)',
            borderRadius: '8px',
          }">
            <div :style="{ fontSize: '11px', color: 'var(--color-ex-warn)', fontWeight: 600, marginBottom: '2px' }">
              下一节点
            </div>
            <div :style="{ fontSize: '13px', color: 'var(--color-ex-ink2)' }">
              将按「{{ projectTypeLabel || '默认' }}」类型自动分配审批人
            </div>
          </div>

          <div class="flex" :style="{ gap: '10px', marginTop: '18px' }">
            <div
              class="flex-1 flex items-center justify-center"
              role="button"
              :style="{
                height: '48px', borderRadius: '24px',
                background: 'var(--color-ex-card)',
                border: '1.5px solid var(--color-ex-divider)',
                color: 'var(--color-ex-ink2)',
                fontSize: '14px', fontWeight: 600,
              }"
              @click="close"
            >取消</div>
            <div
              class="flex items-center justify-center"
              role="button"
              :style="{
                flex: 2, height: '48px', borderRadius: '24px',
                background: 'var(--color-ex-ink)', color: '#fff',
                fontSize: '14px', fontWeight: 600,
                opacity: submitting ? 0.7 : 1,
              }"
              @click="!submitting && $emit('confirm')"
            >{{ submitting ? '提交中...' : '确认提交' }}</div>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'

const TYPE_LABEL = {
  channel_follow:       '渠道',
  sales_focus:          '销售',
  business_opportunity: '服务',
}
const TYPE_COLOR = {
  channel_follow:       { bg: '#E8F1FF', fg: '#1E5DDB' },
  sales_focus:          { bg: '#FFF1E0', fg: '#C57211' },
  business_opportunity: { bg: '#E9F7EE', fg: '#1F8A4F' },
}

const props = defineProps({
  modelValue:   { type: Boolean, default: false },
  projectName:  { type: String, default: '' },
  projectType:  { type: String, default: '' }, // channel_follow / sales_focus / business_opportunity
  customerName: { type: String, default: '' },
  ownerName:    { type: String, default: '' },
  amount:       { type: String, default: '' },
  stage:        { type: String, default: '' },
  submitting:   { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'confirm'])

const projectTypeLabel = computed(() => TYPE_LABEL[props.projectType] || props.projectType || '')
const typeBadgeStyle = computed(() => {
  const c = TYPE_COLOR[props.projectType] || { bg: 'var(--color-ex-divider)', fg: 'var(--color-ex-ink2)' }
  return {
    fontSize: '11px', fontWeight: 600,
    padding: '3px 9px', borderRadius: '10px',
    background: c.bg, color: c.fg,
    whiteSpace: 'nowrap',
  }
})

function close() { emit('update:modelValue', false) }
</script>

<style scoped>
.proj-submit-sheet-enter-active { transition: opacity 0.2s; }
.proj-submit-sheet-leave-active { transition: opacity 0.2s; }
.proj-submit-sheet-enter-from, .proj-submit-sheet-leave-to { opacity: 0; }
.proj-submit-sheet-enter-active > div:last-child,
.proj-submit-sheet-leave-active > div:last-child {
  transition: transform 320ms cubic-bezier(0.32, 0.72, 0, 1);
}
.proj-submit-sheet-enter-from > div:last-child,
.proj-submit-sheet-leave-to > div:last-child {
  transform: translateY(100%);
}
</style>
