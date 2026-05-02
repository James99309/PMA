<script setup>
// 公司广播详情 —— 设计稿无此屏，按 Plan A 风格新建
// 顶部 Hero：广播频道名 + 订阅者数；下方按时间倒序的公告列表
import { useRouter } from 'vue-router'
import NavBar from '@/components/common/NavBar.vue'
import Section from '@/components/common/Section.vue'

const router = useRouter()

// Mock 公告列表（实际由后端 announcement 表提供）
const announcements = [
  {
    id: 1, time: '09:21 · 今天', author: '管理员',
    title: 'Q2 全员目标已发布',
    body: '各位同事：Q2 全员业绩目标已在 OA 发布，请项目经理本周前与团队对齐 KPI。\n\n重点指标：\n  · 新签客户 +20%\n  · 已签项目准时回款 ≥ 85%\n  · NPS 提升 5 个点\n\n如有疑问请联系 HR 王芳。',
    pinned: true,
  },
  {
    id: 2, time: '昨天 14:00', author: '行政',
    title: '5月 1-3 日劳动节放假通知',
    body: '5月 1 日至 3 日（周五至周日）放假调休。4 日（周一）正常上班。请提前安排好客户对接。',
  },
  {
    id: 3, time: '上周 周一', author: '产品部',
    title: 'PMA 系统 v1.4 上线公告',
    body: '本周一 PMA 系统升级到 v1.4，新增移动端 AI 助手「源助手」、客户讨论卡功能。详情见内部文档。',
  },
  {
    id: 4, time: '上周 周三', author: '销售总监',
    title: '4 月销冠表彰',
    body: '恭喜张伟（132%）、陈刚（118%）、李明（105%）超额完成 4 月业绩。详细排名见 OA。',
  },
]
</script>

<template>
  <div class="flex flex-col h-full overflow-y-auto" style="background: var(--color-bg);">

    <NavBar back-label="消息" title="公司广播" @back="router.back()" />

    <!-- Hero：广播频道介绍 -->
    <div class="px-7 pt-5 pb-4 flex items-center gap-3">
      <div class="w-14 h-14 rounded-2xl inline-flex items-center justify-center text-white font-serif font-semibold"
        style="background: var(--color-ink); font-size: 24px;">广</div>
      <div class="flex-1 min-w-0">
        <div class="font-serif" style="font-size: 18px; font-weight: 500; color: var(--color-ink);">公司广播</div>
        <div class="text-[12px] mt-0.5" style="color: var(--color-ink-3);">系统频道 · 全员订阅 · 仅管理员可发</div>
      </div>
    </div>

    <!-- 公告列表 -->
    <Section title="最近公告">
      <div class="rounded-2xl"
        style="background: var(--color-card); border: 1px solid var(--color-divider);">
        <div v-for="(a, i) in announcements" :key="a.id"
          class="px-4 py-4"
          :style="i < announcements.length - 1 ? 'border-bottom: 1px solid var(--color-divider);' : ''">
          <!-- 标题行 -->
          <div class="flex items-baseline gap-2 mb-1">
            <span v-if="a.pinned" class="text-[11px]" style="color: var(--color-accent);">★</span>
            <h3 class="font-serif flex-1"
              style="font-size: 15px; font-weight: 600; color: var(--color-ink); line-height: 1.3;">
              {{ a.title }}
            </h3>
          </div>
          <!-- 元信息 -->
          <div class="text-[11px] mb-2" style="color: var(--color-ink-3);">
            {{ a.author }} · {{ a.time }}
          </div>
          <!-- 正文 -->
          <div class="font-serif whitespace-pre-line"
            style="font-size: 14px; line-height: 1.6; color: var(--color-ink-2);">
            {{ a.body }}
          </div>
        </div>
      </div>
    </Section>

    <div class="h-8" />
  </div>
</template>
