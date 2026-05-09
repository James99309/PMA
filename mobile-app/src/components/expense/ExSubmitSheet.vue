<!--
  ExSubmitSheet · 提交确认 sheet
  严格对齐 design_handoff/expense-list-form.jsx::ExpenseSubmitSheet (L361-425)
  - drag indicator 36x4 divider
  - eyebrow 11 ink3 letterSpacing 0.6 "提交审批"
  - title 22/500 serif "确认提交?"
  - 信息卡: 14 padding, card bg, 1px divider 边
      行: 报销总金额(13 ink3) + 数额(20 serif 600)
      分隔 1px dividerSoft
      def-list 12 ink3 -> ink2(关联客户/项目/明细数)
  - 下一节点 callout: warnSoft 背景, padding 10/12, radius 8
      eyebrow 11/600 warn "下一节点"
      正文 13 ink2: <name 600> · <node> · 通常 1 个工作日内
  - 按钮: 取消(flex 1, 48 高, 24 圆, divider 边) + 确认提交(flex 2, ink 黑底)
-->
<template>
  <Teleport to="body">
    <transition name="ex-submit-sheet">
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
          <!-- drag -->
          <div
            :style="{
              width: '36px',
              height: '4px',
              background: 'var(--color-ex-divider)',
              borderRadius: '2px',
              margin: '0 auto 14px',
            }"
          />
          <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', letterSpacing: '0.6px' }">
            提交审批
          </div>
          <div
            :style="{
              fontSize: '22px',
              fontWeight: 500,
              fontFamily: 'var(--font-serif)',
              color: 'var(--color-ex-ink)',
              marginTop: '4px',
            }"
          >确认提交?</div>

          <!-- 信息卡 -->
          <div
            :style="{
              marginTop: '16px',
              padding: '14px',
              background: 'var(--color-ex-card)',
              borderRadius: '10px',
              border: '1px solid var(--color-ex-divider)',
            }"
          >
            <div class="flex items-baseline justify-between">
              <div :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)' }">报销总金额</div>
              <div
                :style="{
                  fontSize: '20px',
                  fontFamily: 'var(--font-serif)',
                  fontWeight: 600,
                }"
              >{{ currencySymbol }}{{ formatAmount(totalAmount) }}</div>
            </div>
            <div :style="{ height: '1px', background: 'var(--color-ex-divider-soft)', margin: '10px 0' }" />
            <div :style="{ fontSize: '12px', color: 'var(--color-ex-ink3)', lineHeight: 1.7 }">
              <div class="flex justify-between">
                <span>关联客户</span>
                <span :style="{ color: 'var(--color-ex-ink2)' }">{{ customerName || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span>关联项目</span>
                <span :style="{ color: 'var(--color-ex-ink2)' }">{{ projectName || '—' }}</span>
              </div>
              <div class="flex justify-between">
                <span>明细数</span>
                <span :style="{ color: 'var(--color-ex-ink2)' }">{{ lineCount }} 项</span>
              </div>
            </div>
          </div>

          <!-- 下一节点预告 -->
          <div
            v-if="nextApprover"
            :style="{
              marginTop: '12px',
              padding: '10px 12px',
              background: 'var(--color-ex-warn-soft)',
              borderRadius: '8px',
            }"
          >
            <div :style="{ fontSize: '11px', color: 'var(--color-ex-warn)', fontWeight: 600, marginBottom: '2px' }">
              下一节点
            </div>
            <div :style="{ fontSize: '13px', color: 'var(--color-ex-ink2)' }">
              <span :style="{ fontWeight: 600 }">{{ nextApprover.user }}</span>
              · {{ nextApprover.node }} · 通常 1 个工作日内
            </div>
          </div>

          <!-- 按钮组 -->
          <div class="flex" :style="{ gap: '10px', marginTop: '18px' }">
            <div
              class="flex-1 flex items-center justify-center"
              :style="{
                height: '48px',
                borderRadius: '24px',
                background: 'var(--color-ex-card)',
                border: '1.5px solid var(--color-ex-divider)',
                color: 'var(--color-ex-ink2)',
                fontSize: '14px',
                fontWeight: 600,
              }"
              @click="close"
            >取消</div>
            <div
              class="flex items-center justify-center"
              :style="{
                flex: 2,
                height: '48px',
                borderRadius: '24px',
                background: submitting ? 'var(--color-ex-divider)' : 'var(--color-ex-ink)',
                color: submitting ? 'var(--color-ex-ink4)' : 'var(--color-ex-card)',
                fontSize: '14px',
                fontWeight: 600,
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
defineProps({
  modelValue: { type: Boolean, default: false },
  totalAmount: { type: Number, default: 0 },
  currencySymbol: { type: String, default: '¥' },
  customerName: { type: String, default: '' },
  projectName: { type: String, default: '' },
  lineCount: { type: Number, default: 0 },
  nextApprover: { type: Object, default: null }, // {user, node}
  submitting: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'confirm'])

function formatAmount(n) {
  return (n || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function close() { emit('update:modelValue', false) }
</script>

<style scoped>
.ex-submit-sheet-enter-active { transition: opacity 0.2s; }
.ex-submit-sheet-leave-active { transition: opacity 0.2s; }
.ex-submit-sheet-enter-from, .ex-submit-sheet-leave-to { opacity: 0; }
.ex-submit-sheet-enter-active > div:last-child,
.ex-submit-sheet-leave-active > div:last-child {
  transition: transform 320ms cubic-bezier(0.32, 0.72, 0, 1);
}
.ex-submit-sheet-enter-from > div:last-child,
.ex-submit-sheet-leave-to > div:last-child {
  transform: translateY(100%);
}
</style>
