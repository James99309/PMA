<!--
  ExpenseListView · 报销单列表(我的)
  严格对齐 design_handoff/expense-list-form.jsx::ExpenseList (L46-130)
  - 顶部状态栏 54px + 标题栏 48px(报销 22 serif + 筛选/搜索 13 ink3)
  - hero summary: 11 ink3 eyebrow / 38 serif amount / 12 ink3 meta(pending warn)
  - section: 11/600 ink3 uppercase + accent 全部›
  - 列表行: 14/20 padding + 1px dividerSoft
    左: title 15/600 + status chip(10/600 colored), subtitle ink3 12,
        meta ink4 11(id · n 项明细 · 当前 warn)
    右: amount 17/600 serif, applyAt 10 ink4
  - FAB: 54x54 ink 圆形, ¥+ 文字, 阴影; 位置 right 20 bottom 100 (Tab 78 + 22)
-->
<template>
  <div
    class="relative h-full overflow-hidden"
    :style="{ background: 'var(--color-ex-bg)', color: 'var(--color-ex-ink)', fontFamily: 'var(--font-sans)' }"
  >
    <!-- 状态栏占位 54 -->
    <div class="status-pad" />

    <!-- 顶部标题栏 (绝对定位 top=54 height=48) -->
    <div
      class="absolute left-0 right-0 z-[5] flex items-center justify-between"
      :style="{ top: '54px', height: '48px', padding: '0 16px', background: 'var(--color-ex-bg)' }"
    >
      <div :style="{ fontSize: '22px', fontWeight: 600, fontFamily: 'var(--font-serif)' }">报销</div>
      <div class="flex items-center" :style="{ gap: '12px' }">
        <div :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)' }">筛选</div>
        <div :style="{ fontSize: '13px', color: 'var(--color-ex-ink3)' }">搜索</div>
      </div>
    </div>

    <!-- 滚动内容区 -->
    <div
      class="overflow-auto h-full no-scrollbar"
      :style="{ paddingTop: '102px', paddingBottom: '24px' }"
    >
      <!-- hero summary -->
      <div :style="{ padding: '14px 20px 18px' }">
        <div :style="{ fontSize: '11px', color: 'var(--color-ex-ink3)', letterSpacing: '0.4px' }">
          本月已申报 · {{ summary.currency || 'CNY' }}
        </div>
        <div
          :style="{
            fontSize: '38px',
            fontWeight: 500,
            fontFamily: 'var(--font-serif)',
            color: 'var(--color-ex-ink)',
            lineHeight: 1.1,
            marginTop: '4px',
          }"
        >¥ {{ formatAmount(summary.month_total) }}</div>
        <div :style="{ fontSize: '12px', color: 'var(--color-ex-ink3)', marginTop: '6px' }">
          <span :style="{ color: 'var(--color-ex-warn)', fontWeight: 600 }">{{ summary.pending_count }}</span>
          笔审批中 ·
          <span :style="{ marginLeft: '4px' }">共 {{ summary.total_count }} 笔</span>
        </div>
      </div>

      <!-- Section header -->
      <div
        class="flex items-center justify-between"
        :style="{ padding: '0 20px 8px' }"
      >
        <div
          :style="{
            fontSize: '11px',
            fontWeight: 600,
            color: 'var(--color-ex-ink3)',
            letterSpacing: '0.6px',
            textTransform: 'uppercase',
          }"
        >最近 30 天</div>
        <div :style="{ fontSize: '11px', color: 'var(--color-ex-accent)', fontWeight: 600 }">
          全部 ›
        </div>
      </div>

      <!-- 列表 -->
      <div v-if="loading && items.length === 0" :style="{ padding: '40px 20px', textAlign: 'center', color: 'var(--color-ex-ink3)', fontSize: '13px' }">
        加载中...
      </div>
      <div v-else-if="items.length === 0" :style="{ padding: '40px 20px', textAlign: 'center', color: 'var(--color-ex-ink3)', fontSize: '13px' }">
        还没有任何报销单
      </div>
      <div v-else>
        <div
          v-for="it in items"
          :key="it.id"
          class="flex"
          :style="{
            background: 'var(--color-ex-card)',
            padding: '14px 20px',
            borderBottom: '1px solid var(--color-ex-divider-soft)',
            gap: '12px',
          }"
          @click="$router.push(`/expense/${it.id}`)"
        >
          <div class="flex-1 min-w-0">
            <div class="flex items-center" :style="{ gap: '8px' }">
              <div
                class="truncate"
                :style="{ fontSize: '15px', fontWeight: 600, color: 'var(--color-ex-ink)' }"
              >{{ it.title }}</div>
              <div
                :style="{
                  fontSize: '10px',
                  fontWeight: 600,
                  color: it.status_meta.color,
                  background: it.status_meta.bg,
                  padding: '2px 7px',
                  borderRadius: '4px',
                  flexShrink: 0,
                }"
              >{{ it.status_meta.label }}</div>
            </div>
            <div
              class="truncate"
              :style="{ fontSize: '12px', color: 'var(--color-ex-ink3)', marginTop: '3px' }"
            >{{ it.subtitle || '—' }}</div>
            <div
              class="flex"
              :style="{ fontSize: '11px', color: 'var(--color-ex-ink4)', marginTop: '6px', gap: '8px' }"
            >
              <span>{{ it.expense_number }}</span>
              <span>·</span>
              <span>{{ it.detail_count }} 项明细</span>
              <template v-if="it.current_node">
                <span>·</span>
                <span :style="{ color: 'var(--color-ex-warn)' }">当前: {{ it.current_node }}</span>
              </template>
            </div>
          </div>
          <div :style="{ textAlign: 'right' }">
            <div
              :style="{
                fontSize: '17px',
                fontWeight: 600,
                fontFamily: 'var(--font-serif)',
                color: 'var(--color-ex-ink)',
              }"
            >{{ currencySymbol(it.currency) }}{{ formatAmount(it.amount) }}</div>
            <div :style="{ fontSize: '10px', color: 'var(--color-ex-ink4)', marginTop: '4px' }">
              {{ it.apply_at }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- FAB -->
    <div
      class="absolute flex items-center justify-center"
      :style="{
        right: '20px',
        bottom: '20px',
        width: '54px',
        height: '54px',
        borderRadius: '27px',
        background: 'var(--color-ex-ink)',
        color: 'var(--color-ex-card)',
        fontSize: '28px',
        fontWeight: 300,
        boxShadow: 'var(--shadow-ex-fab)',
      }"
      @click="$router.push('/expense/new')"
    >+</div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useExpenseStore } from '@/stores/expense'

const store = useExpenseStore()
const items = computed(() => store.items)
const summary = computed(() => store.summary)
const loading = computed(() => store.loading)

function formatAmount(n) {
  return (n || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function currencySymbol(code) {
  const map = { CNY: '¥', USD: '$', HKD: 'HK$', TWD: 'NT$', SGD: 'S$', MYR: 'RM', IDR: 'Rp', THB: '฿', VND: '₫' }
  return map[code] || code
}

onMounted(() => {
  store.loadReference()
  store.fetchList()
})
</script>
