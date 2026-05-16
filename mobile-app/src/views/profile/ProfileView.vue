<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { CapacitorUpdater } from '@capgo/capacitor-updater'
import { REGIONS } from '@/api/client'
import client from '@/api/client'
import { setLocale } from '@/locales'
import { getPendingApprovals } from '@/api/approval'
import { getTasks } from '@/api/tasks'

// 待审批数(显示在审批中心圆形图标里)
const pendingCount = ref(0)
async function loadPendingCount() {
  try {
    const r = await getPendingApprovals()
    pendingCount.value = r.data?.data?.total || 0
  } catch {}
}

// Overview counts for the Task Center entry card
const taskCounts = ref({ mine: 0, created: 0, review: 0, overdue: 0 })
async function loadTaskCounts() {
  try {
    const r = await getTasks({ tab: 'mine', per: 1 })
    if (r.data?.data?.counts) taskCounts.value = r.data.data.counts
  } catch {}
}

const router = useRouter()
const auth = useAuthStore()
const { t, locale } = useI18n()

// Bundle 版本（Capgo 当前激活的）
const bundleId = ref('builtin')
const bundleVer = ref('-')
const bundleStatus = ref('')

// 区域信息 (Federation Lite)
const homeRegion = computed(() => REGIONS[auth.homeRegionId] || REGIONS.cn)
const otherRegion = computed(() => {
  const otherId = auth.regionId === 'cn' ? 'sg' : 'cn'
  return REGIONS[otherId]
})
const currentRegion = computed(() => REGIONS[auth.regionId] || REGIONS.cn)
const regions = computed(() => {
  // 数据区域两行: home 在前, peer 在后
  const home = REGIONS[auth.homeRegionId] || REGIONS.cn
  const otherId = auth.homeRegionId === 'cn' ? 'sg' : 'cn'
  return [home, REGIONS[otherId]]
})

// 切换 sheet 状态
const showSwitchSheet = ref(false)
const targetRegion = ref(null)
const switching = ref(false)
const switchError = ref('')

function tapRegionRow(r) {
  // 当前在用的区域: 没动作
  if (r.id === auth.regionId) return
  // 没有对区 token (单区用户): 不应进 sheet (UI 已经隐藏)
  if (!auth.tokens[r.id]) {
    switchError.value = t('profile.switchUnauthorized', { label: r.label })
    return
  }
  switchError.value = ''
  targetRegion.value = r
  showSwitchSheet.value = true
}

function cancelSwitch() {
  showSwitchSheet.value = false
  targetRegion.value = null
}

async function confirmSwitch() {
  if (!targetRegion.value || switching.value) return
  switching.value = true
  // 简短动画: 先关 sheet, 显示 toast 450ms, 再 reload
  showSwitchSheet.value = false
  await new Promise(r => setTimeout(r, 100))  // 给 sheet 关闭动画一点时间
  if (auth.switchRegion(targetRegion.value.id)) {
    await new Promise(r => setTimeout(r, 350))  // toast 显示窗口
    // Capacitor WebView 下 router.go(0) 是 no-op, 必须用 location.reload 真刷新
    window.location.reload()
  } else {
    switching.value = false
    switchError.value = t('profile.switchUnauthorizedShort', { label: targetRegion.value.label })
  }
}

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}

async function checkUpdate() {
  bundleStatus.value = t('profile.bundleChecking')
  try {
    const latest = await CapacitorUpdater.getLatest()
    if (latest?.version && latest.version !== bundleVer.value) {
      bundleStatus.value = t('profile.bundleNewFound', { ver: latest.version })
      const dl = await CapacitorUpdater.download({ url: latest.url, version: latest.version })
      bundleStatus.value = t('profile.bundleDownloaded')
      await CapacitorUpdater.set({ id: dl.id })
    } else {
      bundleStatus.value = t('profile.bundleLatest')
    }
  } catch (e) {
    const msg = e?.message || String(e || '')
    const benign = ['no_new_version_available', 'no_channel', 'already_set']
    if (benign.some(k => msg.includes(k))) {
      bundleStatus.value = t('profile.bundleLatest')
    } else {
      bundleStatus.value = t('profile.bundleCheckFail', { msg })
    }
  }
}

onMounted(async () => {
  loadPendingCount()
  loadTaskCounts()
  try {
    const info = await CapacitorUpdater.current()
    bundleId.value = info?.bundle?.id || 'builtin'
    bundleVer.value = info?.bundle?.version || 'builtin'
  } catch {
    // Web/dev 环境忽略
  }
})

// Eyebrow 文案: away 时双语提示
const eyebrow = computed(() => auth.isAway ? `${t('profile.eyebrowAway')} · ${auth.regionId.toUpperCase()}` : t('profile.eyebrow'))
const title = computed(() => auth.isAway ? `${t('profile.title')} · Profile` : t('profile.title'))

// 语言切换 — 同步到 i18n + localStorage + 后端 user.language_preference
const showLangPicker = ref(false)
const LANG_OPTIONS = computed(() => [
  { code: 'zh', label: t('profile.langZh') },
  { code: 'en', label: t('profile.langEn') },
])
const currentLangLabel = computed(() =>
  LANG_OPTIONS.value.find(o => o.code === locale.value)?.label || t('profile.langZh')
)
async function selectLang(code) {
  setLocale(code)              // 立即生效 + 本地缓存 + axios header 下次自动用新 lang
  showLangPicker.value = false
  // 同步到后端 user.language_preference (失败不阻塞 UI)
  try {
    await client.put('/user/profile', { language_preference: code })
    if (auth.user) {
      auth.user.language_preference = code
      const key = `user_${auth.regionId}`
      localStorage.setItem(key, JSON.stringify(auth.user))
    }
  } catch {}
}

// 结算货币 — 只读展示, 修改入口在 Web 端
// 切换会影响报销/绩效/薪酬的统计口径, mobile 不开放避免来回切造成混乱
const CURRENCY_LABEL = computed(() => ({
  CNY: t('profile.currCNY'), USD: t('profile.currUSD'), HKD: t('profile.currHKD'),
  TWD: t('profile.currTWD'), SGD: t('profile.currSGD'), MYR: t('profile.currMYR'),
  IDR: t('profile.currIDR'), THB: t('profile.currTHB'), VND: t('profile.currVND'),
}))
const currentCurrency = computed(() => {
  const code = auth.user?.settlement_currency
  if (!code) return auth.regionId === 'sg' ? t('profile.regionDefaultUSD') : t('profile.regionDefaultCNY')
  return CURRENCY_LABEL.value[code] || code
})
</script>

<template>
  <div class="flex flex-col h-full bg-[#F7F5F2]">
    <!-- PageHead -->
    <div class="bg-[#F7F5F2] px-5 pt-4 pb-3">
      <p class="text-[11px] font-semibold uppercase tracking-wider"
        style="color: var(--color-ink-3); letter-spacing: 1.2px;">{{ eyebrow }}</p>
      <h1 class="font-serif font-medium leading-none mt-1"
        style="font-size: 32px; letter-spacing: -0.4px; color: var(--color-ink);">{{ title }}</h1>
    </div>

    <div class="flex-1 overflow-y-auto px-4 pb-6 space-y-3">
      <!-- 头像卡 -->
      <div class="bg-white rounded-2xl px-4 py-3.5 flex items-center gap-3.5"
        style="border: 1px solid var(--color-divider);">
        <div class="w-12 h-12 rounded-full flex items-center justify-center font-serif font-semibold text-[20px] shrink-0"
          style="background: var(--color-accent-soft); color: var(--color-accent);">
          {{ auth.user?.real_name?.[0] || auth.user?.username?.[0] || '?' }}
        </div>
        <div class="flex-1 min-w-0">
          <p class="font-serif text-[17px] leading-tight" style="color: var(--color-ink); letter-spacing: -0.2px;">
            {{ auth.user?.real_name || auth.user?.username }}
          </p>
          <p class="text-[12px] mt-0.5 truncate" style="color: var(--color-ink-3);">
            {{ auth.user?.email || auth.user?.username || '' }}{{ auth.isAway ? t('profile.crossAccountSuffix') : '' }}
          </p>
        </div>
      </div>

      <!-- Task Center entry card (Claude Design / MeWithTaskEntry) -->
      <div class="bg-white rounded-2xl overflow-hidden" style="border: 1px solid var(--color-divider);">
        <div class="px-4 py-3.5 flex items-center gap-3 active:bg-gray-50"
          style="border-bottom: 1px solid var(--color-divider);"
          @click="router.push('/tasks')">
          <div class="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
            style="background: var(--color-accent); color: #fff;">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M5 10l3 3 7-7" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <circle cx="10" cy="10" r="9" stroke="#fff" stroke-width="1.5"/>
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-[15px] font-semibold" style="color: var(--color-ink);">{{ t('task.entryTitle') }}</div>
            <div class="text-[11.5px] mt-0.5" style="color: var(--color-ink-3);">
              {{ t('task.entrySub', { mine: taskCounts.mine, review: taskCounts.review, overdue: taskCounts.overdue }) }}
            </div>
          </div>
          <span style="color: var(--color-ink-4);">›</span>
        </div>
        <div class="px-4 py-2.5 flex gap-3">
          <div v-for="s in [
              { l: t('task.entryStatMine'),    n: taskCounts.mine,    c: 'var(--color-blue)' },
              { l: t('task.entryStatReview'),  n: taskCounts.review,  c: '#7B5BAC' },
              { l: t('task.entryStatCreated'), n: taskCounts.created, c: 'var(--color-ink-2)' },
              { l: t('task.entryStatOverdue'), n: taskCounts.overdue, c: 'var(--color-red)' },
            ]" :key="s.l" class="flex-1 text-center">
            <div class="font-serif text-[18px] font-semibold" :style="{ color: s.c }">{{ s.n }}</div>
            <div class="text-[10px] mt-0.5" style="color: var(--color-ink-3);">{{ s.l }}</div>
          </div>
        </div>
      </div>

      <!-- 数据区域 (仅多区账户) -->
      <template v-if="auth.hasOtherRegionToken">
        <div class="px-2 pt-3 pb-1">
          <div class="text-[11px] font-semibold uppercase"
            style="color: var(--color-ink-3); letter-spacing: 0.6px;">
            {{ t('profile.dataRegion') }}{{ auth.isAway ? ' · DATA REGION' : '' }}
          </div>
        </div>
        <div class="bg-white rounded-2xl overflow-hidden"
          style="border: 1px solid var(--color-divider);">
          <div v-for="(r, i) in regions" :key="r.id"
            @click="tapRegionRow(r)"
            class="px-3.5 py-3.5 flex items-center gap-3 active:bg-gray-50"
            :style="{
              borderBottom: i < regions.length - 1 ? '1px solid var(--color-divider)' : 'none',
              cursor: r.id === auth.regionId ? 'default' : 'pointer',
            }">
            <!-- 国旗块 -->
            <div class="shrink-0 inline-flex items-center justify-center"
              :style="{
                width: '36px', height: '36px', borderRadius: '10px',
                fontSize: '18px',
                background: r.id === auth.regionId
                  ? (auth.isAway ? '#FBF1DF' : 'var(--color-ink)')
                  : 'var(--color-bg)',
                border: r.id === auth.regionId ? 'none' : '1px solid var(--color-divider)',
              }">
              {{ r.flag }}
            </div>
            <!-- 名称 + 描述 -->
            <div class="flex-1 min-w-0">
              <div class="flex items-baseline gap-2">
                <span class="font-semibold" style="font-size: 14.5px; color: var(--color-ink);">{{ r.label }}</span>
                <span class="font-mono uppercase tracking-wider" style="font-size: 10px; color: var(--color-ink-3);">{{ r.id }}</span>
              </div>
              <div class="mt-0.5" style="font-size: 12px; color: var(--color-ink-3);">
                {{ r.id === 'cn' ? t('profile.cnDc') : t('profile.sgDc') }}
              </div>
            </div>
            <!-- 状态 chip / hint -->
            <span v-if="r.id === auth.regionId && r.id === auth.homeRegionId"
              class="font-semibold"
              style="font-size: 10.5px; padding: 3px 8px; border-radius: 999px; background: var(--color-ink); color: #fff; letter-spacing: 0.2px;">
              {{ t('profile.currentHome') }}
            </span>
            <span v-else-if="r.id === auth.regionId && r.id !== auth.homeRegionId"
              class="font-semibold"
              style="font-size: 10.5px; padding: 3px 8px; border-radius: 999px; background: #FBF1DF; color: #B8762A; letter-spacing: 0.2px;">
              {{ t('profile.current') }}
            </span>
            <span v-else-if="r.id === auth.homeRegionId"
              style="font-size: 11.5px; color: var(--color-ink-3);">
              {{ t('profile.canSwitchBack') }}
            </span>
            <span v-else style="font-size: 11.5px; color: var(--color-ink-3);">
              {{ t('profile.canAccess') }}
            </span>
          </div>
        </div>
        <p class="px-2 pt-1.5" style="font-size: 11.5px; color: var(--color-ink-3); line-height: 1.55;">
          {{ t('profile.switchHint') }}
        </p>
      </template>

      <!-- 工作入口 -->
      <div class="pt-2">
        <div class="px-2 pb-1">
          <div class="text-[11px] font-semibold uppercase"
            style="color: var(--color-ink-3); letter-spacing: 0.6px;">{{ t('profile.work') }}</div>
        </div>
        <div class="bg-white rounded-2xl overflow-hidden"
          style="border: 1px solid var(--color-divider);">
          <button @click="router.push('/approval')"
            class="w-full flex items-center gap-3.5 px-4 py-4 active:bg-gray-50 text-left">
            <!-- 44x44 圆形带待审批数字(对齐设计稿 expense-approval.jsx L36-37) -->
            <div class="rounded-full flex items-center justify-center shrink-0"
              style="
                width: 44px; height: 44px;
                background: var(--color-ex-warn-soft);
                color: var(--color-ex-warn);
                font-size: 18px; font-weight: 600;
              ">{{ pendingCount }}</div>
            <div class="flex-1">
              <div style="font-size: 14px; color: var(--color-ink); font-weight: 600;">{{ t('profile.myApprovals') }}</div>
              <div style="font-size: 11px; color: var(--color-ink-3); margin-top: 2px;">
                {{ pendingCount > 0 ? t('profile.pendingCount', { n: pendingCount }) : t('profile.noPending') }}
              </div>
            </div>
            <svg width="7" height="11" viewBox="0 0 7 11">
              <path d="M1 1l4 4.5L1 10" stroke="#A8A29B" stroke-width="1.4" fill="none" stroke-linecap="round" />
            </svg>
          </button>
        </div>
      </div>

      <!-- 设置 -->
      <div class="pt-2">
        <div class="px-2 pb-1">
          <div class="text-[11px] font-semibold uppercase"
            style="color: var(--color-ink-3); letter-spacing: 0.6px;">
            {{ t('profile.settings') }}{{ auth.isAway ? ' · SETTINGS' : '' }}
          </div>
        </div>
        <div class="bg-white rounded-2xl overflow-hidden"
          style="border: 1px solid var(--color-divider);">
          <div class="px-4 py-3 flex items-center justify-between"
            style="border-bottom: 1px solid var(--color-divider);">
            <span style="font-size: 14px; color: var(--color-ink); font-weight: 500;">{{ t('profile.notification') }}</span>
            <span class="inline-block relative"
              style="width: 38px; height: 22px; border-radius: 11px; background: var(--color-ink); opacity: 0.85;">
              <span class="absolute" style="top: 2px; left: 18px; width: 18px; height: 18px; border-radius: 9px; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.2);"></span>
            </span>
          </div>
          <button @click="showLangPicker = true"
            class="w-full px-4 py-3 flex items-center justify-between active:bg-gray-50 text-left"
            style="border-bottom: 1px solid var(--color-divider);">
            <span style="font-size: 14px; color: var(--color-ink); font-weight: 500;">{{ t('profile.language') }}</span>
            <span class="inline-flex items-center gap-1" style="font-size: 13px; color: var(--color-ink-3);">
              {{ currentLangLabel }}
              <span style="font-size: 16px; color: #A8A29B; font-weight: 200;">›</span>
            </span>
          </button>
          <div class="px-4 py-3 flex items-center justify-between"
            style="border-bottom: 1px solid var(--color-divider);">
            <div class="flex flex-col">
              <span style="font-size: 14px; color: var(--color-ink); font-weight: 500;">{{ t('profile.settlementCurrency') }}</span>
              <span style="font-size: 11px; color: var(--color-ink-3); margin-top: 2px;">{{ t('profile.settlementHint') }}</span>
            </div>
            <span style="font-size: 13px; color: var(--color-ink-3);">{{ currentCurrency }}</span>
          </div>
          <div class="px-4 py-3 flex items-center justify-between">
            <span style="font-size: 14px; color: var(--color-ink); font-weight: 500;">{{ t('profile.appVersion') }}</span>
            <span class="tabular" style="font-size: 12px; color: var(--color-ink-3);">{{ bundleVer }}</span>
          </div>
          <button @click="checkUpdate"
            class="w-full px-4 py-3 flex items-center justify-between active:bg-gray-50 text-left"
            style="border-top: 1px solid var(--color-divider);">
            <span style="font-size: 13px; color: var(--color-accent); font-weight: 500;">{{ t('profile.checkUpdate') }}</span>
            <span style="font-size: 11px; color: var(--color-ink-3);">{{ bundleStatus }}</span>
          </button>
        </div>
      </div>

      <!-- 退出 -->
      <div class="pt-4 pb-8">
        <button @click="handleLogout"
          class="w-full py-3.5 rounded-2xl active:opacity-80"
          style="background: white; border: 1px solid var(--color-divider-strong); font-size: 14.5px; color: var(--color-ink-2); font-weight: 500;">
          {{ t('profile.logout') }}
        </button>
      </div>
    </div>

    <!-- 切换确认 sheet -->
    <Teleport to="body">
      <Transition name="sheet">
        <div v-if="showSwitchSheet" class="fixed inset-0 z-50">
          <div class="absolute inset-0" style="background: rgba(0,0,0,0.32);"
            @click="cancelSwitch" />
          <div class="absolute left-0 right-0 bottom-0 pb-7 pt-2.5"
            style="background: var(--color-bg); border-top-left-radius: 18px; border-top-right-radius: 18px;">
            <div class="mx-auto" style="width: 36px; height: 4px; border-radius: 2px; background: rgba(0,0,0,0.10); margin-bottom: 14px;"></div>
            <div class="px-6 pb-2">
              <div class="font-serif" style="font-size: 22px; line-height: 1.25; color: var(--color-ink); letter-spacing: -0.3px;">
                {{ t('profile.switchToTitle', { flag: targetRegion?.flag, label: targetRegion?.label }) }}
              </div>
              <div class="mt-2.5" style="font-size: 13.5px; color: var(--color-ink-3); line-height: 1.55;">
                {{ t('profile.switchToBody', { label: targetRegion?.label, cur: currentRegion.label }) }}
              </div>
            </div>
            <!-- 概览对比卡 -->
            <div class="mx-4 mt-4 mb-1 p-3.5"
              style="background: white; border-radius: 14px; border: 1px solid var(--color-divider);">
              <div class="flex items-center gap-2.5">
                <div class="flex-1" style="opacity: 0.55;">
                  <div style="font-size: 11px; color: var(--color-ink-3); margin-bottom: 4px;">{{ t('profile.switchToCurrent') }}</div>
                  <div style="font-size: 14.5px; font-weight: 600; color: var(--color-ink-2);">
                    {{ currentRegion.flag }} {{ currentRegion.label }}
                  </div>
                </div>
                <span style="font-size: 18px; color: #A8A29B; font-weight: 200;">→</span>
                <div class="flex-1">
                  <div style="font-size: 11px; color: #B8762A; margin-bottom: 4px; font-weight: 600;">{{ t('profile.switchToTarget') }}</div>
                  <div style="font-size: 14.5px; font-weight: 600; color: var(--color-ink);">
                    {{ targetRegion?.flag }} {{ targetRegion?.label }}
                  </div>
                </div>
              </div>
            </div>
            <p v-if="switchError" class="px-4 mt-2 text-center" style="font-size: 12px; color: #C44;">
              {{ switchError }}
            </p>
            <div class="px-4 pt-4.5 flex gap-2.5" style="padding-top: 18px;">
              <button @click="cancelSwitch"
                class="flex-1 py-3.5 rounded-xl"
                style="background: transparent; border: 1px solid var(--color-divider-strong); font-size: 15px; color: var(--color-ink-2); font-weight: 500;">
                {{ t('common.cancel') }}
              </button>
              <button @click="confirmSwitch"
                class="rounded-xl text-white font-semibold"
                style="flex: 2; padding: 14px 0; background: var(--color-ink); border: none; font-size: 15px;">
                {{ t('profile.switchToConfirm', { label: targetRegion?.label }) }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 切换中 toast -->
    <Teleport to="body">
      <Transition name="toast">
        <div v-if="switching" class="fixed inset-0 z-[60] flex items-center justify-center pointer-events-none">
          <div class="inline-flex items-center gap-2.5 px-5 py-3.5 rounded-xl"
            style="background: rgba(26,26,26,0.92); backdrop-filter: blur(8px); color: #fff; font-size: 13.5px; font-weight: 500; box-shadow: 0 18px 48px rgba(0,0,0,0.22);">
            <span class="inline-block animate-spin"
              style="width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.25); border-top-color: #fff; border-radius: 7px;"></span>
            {{ t('profile.switchingTo', { label: targetRegion?.label }) }}
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 语言切换 picker -->
    <Teleport to="body">
      <Transition name="sheet">
        <div v-if="showLangPicker" class="fixed inset-0 z-50"
          style="background: rgba(0,0,0,0.32);"
          @click.self="showLangPicker = false">
          <div class="absolute left-0 right-0 bottom-0 bg-white"
            :style="{
              borderRadius: '20px 20px 0 0',
              paddingBottom: 'calc(20px + env(safe-area-inset-bottom))',
            }">
            <div :style="{ width: '36px', height: '4px', background: 'var(--color-divider)', borderRadius: '2px', margin: '10px auto 8px' }"></div>
            <div class="px-5 pb-3 flex items-center justify-between">
              <span class="font-serif" style="font-size: 16px; font-weight: 500;">{{ t('profile.language') }}</span>
              <button @click="showLangPicker = false" class="text-[13px]" style="color: var(--color-ink-3);">{{ t('common.cancel') }}</button>
            </div>
            <div style="border-top: 1px solid var(--color-divider);">
              <button v-for="opt in LANG_OPTIONS" :key="opt.code"
                @click="selectLang(opt.code)"
                class="w-full px-5 py-3.5 flex items-center justify-between active:bg-gray-50 text-left"
                style="border-bottom: 1px solid var(--color-divider-soft);">
                <span style="font-size: 14px; color: var(--color-ink); font-weight: 500;">{{ opt.label }}</span>
                <span v-if="locale === opt.code"
                  style="font-size: 13px; color: var(--color-accent); font-weight: 600;">✓</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<style scoped>
.sheet-enter-active, .sheet-leave-active { transition: opacity .18s ease, transform .22s ease; }
.sheet-enter-from, .sheet-leave-to { opacity: 0; }
.sheet-enter-from > div:last-child, .sheet-leave-to > div:last-child { transform: translateY(20px); }
.toast-enter-active, .toast-leave-active { transition: opacity .15s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; }
</style>
