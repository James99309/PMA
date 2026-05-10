<script setup>
// 渲染聊天消息中的附件（image / file / voice / location）
// 数据由 ChatMessage.message_type + file_url + content(JSON) 组合
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Browser } from '@capacitor/browser'

const { t } = useI18n()
import client from '@/api/client'
import LocationMiniMap from './LocationMiniMap.vue'

const props = defineProps({
  type: { type: String, required: true },     // image / file / voice / location
  url:  { type: String, default: '' },        // file_url（可能是相对路径）
  meta: { type: Object, default: () => ({}) },// { name, size, duration?, lat?, lon? }
  inverted: { type: Boolean, default: false },
})
const emit = defineEmits(['view-location', 'view-image', 'media-loaded'])

// 模块级缓存 baseURL + token，避免每次渲染都读 localStorage / 改正则
const _baseHost = (client.defaults.baseURL || '').replace(/\/api\/v1\/?$/, '')
let _cachedToken = null
function _getToken() {
  if (_cachedToken == null) _cachedToken = localStorage.getItem('access_token') || ''
  return _cachedToken
}

// 把后端返回的相对 URL 拼成完整地址，并把 JWT 作为 ?token= 注入（用于 img/audio 直接访问）
const fullUrl = computed(() => {
  if (!props.url) return ''
  if (/^https?:\/\//.test(props.url)) return props.url
  const sep = props.url.includes('?') ? '&' : '?'
  return `${_baseHost}${props.url}${sep}token=${encodeURIComponent(_getToken())}`
})

function fmtSize(b) {
  if (!b) return ''
  if (b < 1024) return b + 'B'
  if (b < 1024 * 1024) return (b / 1024).toFixed(0) + 'KB'
  return (b / 1024 / 1024).toFixed(1) + 'MB'
}
const fileExt = computed(() => {
  const n = props.meta.name || ''
  const m = n.match(/\.([a-z0-9]{1,5})$/i)
  return (m?.[1] || 'FILE').toUpperCase()
})

// 波形高度 — 与 chat-screens.jsx voice msg 设计稿一致
const WAVE_HEIGHTS = [6, 11, 8, 15, 12, 18, 9, 14, 7, 11, 5, 9, 12, 8]
function formatDuration(s) {
  const sec = Math.max(0, Math.round(Number(s) || 0))
  const m = String(Math.floor(sec / 60)).padStart(2, '0')
  const ss = String(sec % 60).padStart(2, '0')
  return `${m}:${ss}`
}

const playing = ref(false)
const audioRef = ref(null)
function toggleAudio() {
  const el = audioRef.value
  if (!el) return
  if (playing.value) { el.pause(); playing.value = false }
  else { el.play(); playing.value = true }
}
function onAudioEnd() { playing.value = false }

async function openFile() {
  const u = fullUrl.value
  if (!u) return
  try { await Browser.open({ url: u }) }
  catch { window.open(u, '_blank') }
}

function openMap() {
  const { lat, lon } = props.meta || {}
  if (lat == null || lon == null) return
  emit('view-location', { lat, lon })
}
</script>

<template>
  <!-- ── 图片 ── -->
  <div v-if="type === 'image'" class="rounded-xl overflow-hidden"
    style="max-width: 220px; max-height: 280px;">
    <img :src="fullUrl" alt="" loading="lazy"
      class="block w-full h-auto"
      @click="openFile"
      @load="emit('media-loaded')" />
  </div>

  <!-- ── 文件 ── 发送方 inverted=true: 黑底白字; 接收方: 浅 card -->
  <div v-else-if="type === 'file'"
    @click="openFile"
    class="rounded-xl px-3 py-2.5 flex items-center gap-3 active:opacity-80 cursor-pointer"
    :style="{
      background: inverted ? 'var(--color-ink)' : 'var(--color-card)',
      border: inverted ? 'none' : '1px solid var(--color-divider)',
      color: inverted ? '#fff' : 'var(--color-ink)',
      maxWidth: '260px',
    }">
    <span class="inline-flex items-center justify-center font-bold text-[10px] shrink-0"
      :style="{
        width: '36px', height: '44px', borderRadius: '6px',
        background: inverted ? 'rgba(255,255,255,0.12)' : 'var(--color-bg)',
        border: inverted ? '1px solid rgba(255,255,255,0.18)' : '1px solid var(--color-divider)',
        letterSpacing: '0.5px',
      }">{{ fileExt }}</span>
    <div class="min-w-0 flex-1">
      <div class="text-[13.5px] font-medium truncate"
        style="font-family: var(--font-serif);">
        {{ meta.name || t('chat.attachFileFallback') }}
      </div>
      <div class="text-[11px] mt-0.5"
        :style="{ color: inverted ? 'rgba(255,255,255,0.7)' : 'var(--color-ink-3)' }">
        {{ fmtSize(meta.size) }}
      </div>
    </div>
  </div>

  <!-- ── 语音 ── 发送方 inverted=true: 黑底白波形; 接收方: 浅 card 底 + 黑波形 -->
  <div v-else-if="type === 'voice'"
    @click="toggleAudio"
    class="px-3.5 py-2.5 inline-flex items-center gap-2.5 active:opacity-80 cursor-pointer rounded-2xl"
    :style="{
      background: inverted ? 'var(--color-ink)' : 'var(--color-card)',
      border: inverted ? 'none' : '1px solid var(--color-divider)',
      color: inverted ? '#fff' : 'var(--color-ink)',
    }">
    <!-- 播放钮：accent orange + 白色 ▶/■ (两态都用 accent, 视觉锚点) -->
    <span class="inline-flex items-center justify-center shrink-0"
      :style="{
        width: '26px', height: '26px', borderRadius: '13px',
        background: 'var(--color-accent)', color: '#fff',
      }">
      <svg v-if="!playing" width="9" height="11" viewBox="0 0 10 12">
        <path d="M1 1l8 5-8 5z" fill="currentColor" />
      </svg>
      <span v-else class="w-2 h-2.5" style="background: currentColor; border-radius: 1px;" />
    </span>
    <!-- 14 条波形 -->
    <span class="flex items-end gap-[2px]" style="height: 20px;">
      <span v-for="(h, i) in WAVE_HEIGHTS" :key="i"
        :style="{
          width: '2px',
          height: h + 'px',
          background: inverted ? '#fff' : 'var(--color-ink-2)',
          borderRadius: '1px',
          opacity: playing ? 1 : (inverted ? 0.85 : 0.95),
        }" />
    </span>
    <!-- 时长 -->
    <span class="text-[11px] tabular shrink-0"
      :style="{ color: inverted ? 'rgba(255,255,255,0.7)' : 'var(--color-ink-3)' }">
      {{ formatDuration(meta.duration) }}
    </span>
    <audio ref="audioRef" :src="fullUrl" @ended="onAudioEnd" preload="none" class="hidden" />
  </div>

  <!-- ── 位置 ── 严格对齐 chat-location.jsx (252w 卡 + 顶部缩略图 + 下方名称/地址) -->
  <!-- 发送方 (inverted=true): ink 黑底 + 白字; 接收方: 浅 card 底 + 黑字 -->
  <div v-else-if="type === 'location'"
    @click="openMap"
    class="rounded-2xl overflow-hidden active:opacity-90 cursor-pointer"
    :style="{
      width: '252px',
      background: inverted ? 'var(--color-ink)' : 'var(--color-card)',
      border: inverted ? 'none' : '1px solid var(--color-divider)',
      color: inverted ? '#fff' : 'var(--color-ink)',
      boxShadow: inverted ? '0 1px 2px rgba(0,0,0,0.06)' : '0 1px 2px rgba(0,0,0,0.03)',
    }">
    <LocationMiniMap v-if="meta.lat != null && meta.lon != null"
      :lat="Number(meta.lat)" :lon="Number(meta.lon)" :width="252" :height="132" />
    <div class="px-3 pt-2.5 pb-3">
      <div class="text-[14px] font-semibold truncate" style="font-family: var(--font-serif);">
        {{ meta.name || t('chat.attachLocationFallback') }}
      </div>
      <div v-if="meta.address" class="text-[11.5px] mt-1 truncate"
        :style="{ color: inverted ? 'rgba(255,255,255,0.7)' : 'var(--color-ink-3)' }">
        {{ meta.address }}
      </div>
      <div v-else class="text-[11px] tabular mt-1"
        :style="{ color: inverted ? 'rgba(255,255,255,0.7)' : 'var(--color-ink-3)' }">
        {{ Number(meta.lat).toFixed(5) }}, {{ Number(meta.lon).toFixed(5) }}
      </div>
    </div>
  </div>
</template>
