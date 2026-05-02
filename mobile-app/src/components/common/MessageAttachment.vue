<script setup>
// 渲染聊天消息中的附件（image / file / voice / location）
// 数据由 ChatMessage.message_type + file_url + content(JSON) 组合
import { computed, ref } from 'vue'
import { Browser } from '@capacitor/browser'
import client from '@/api/client'

const props = defineProps({
  type: { type: String, required: true },     // image / file / voice / location
  url:  { type: String, default: '' },        // file_url（可能是相对路径）
  meta: { type: Object, default: () => ({}) },// { name, size, duration?, lat?, lon? }
  inverted: { type: Boolean, default: false },
})
const emit = defineEmits(['view-location', 'view-image'])

// 把后端返回的相对 URL 拼成完整地址，并把 JWT 作为 ?token= 注入（用于 img/audio 直接访问）
const fullUrl = computed(() => {
  if (!props.url) return ''
  if (/^https?:\/\//.test(props.url)) return props.url
  // axios baseURL = `${BASE_URL}/api/v1`，但 file_url 已含 /api/v1 前缀
  const base = (client.defaults.baseURL || '').replace(/\/api\/v1\/?$/, '')
  const sep = props.url.includes('?') ? '&' : '?'
  const token = localStorage.getItem('access_token') || ''
  return `${base}${props.url}${sep}token=${encodeURIComponent(token)}`
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
      @click="openFile" />
  </div>

  <!-- ── 文件 ── -->
  <div v-else-if="type === 'file'"
    @click="openFile"
    class="rounded-xl px-3 py-2.5 flex items-center gap-3 active:opacity-80 cursor-pointer"
    :style="{
      background: inverted ? 'rgba(255,255,255,0.10)' : 'var(--color-card)',
      border: inverted ? '1px solid rgba(255,255,255,0.15)' : '1px solid var(--color-divider)',
      color: inverted ? '#fff' : 'var(--color-ink)',
      maxWidth: '260px',
    }">
    <span class="inline-flex items-center justify-center font-bold text-[10px]"
      :style="{
        width: '36px', height: '44px', borderRadius: '6px',
        background: inverted ? 'rgba(255,255,255,0.12)' : 'var(--color-bg)',
        border: inverted ? '1px solid rgba(255,255,255,0.2)' : '1px solid var(--color-divider)',
        letterSpacing: '0.5px',
      }">{{ fileExt }}</span>
    <div class="min-w-0 flex-1">
      <div class="text-[13.5px] font-medium truncate"
        style="font-family: var(--font-serif);">
        {{ meta.name || '附件' }}
      </div>
      <div class="text-[11px] mt-0.5"
        :style="{ color: inverted ? 'rgba(255,255,255,0.7)' : 'var(--color-ink-3)' }">
        {{ fmtSize(meta.size) }}
      </div>
    </div>
  </div>

  <!-- ── 语音 ── -->
  <div v-else-if="type === 'voice'"
    @click="toggleAudio"
    class="rounded-full px-4 py-2.5 inline-flex items-center gap-3 active:opacity-80 cursor-pointer"
    :style="{
      background: inverted ? 'rgba(255,255,255,0.12)' : 'var(--color-card)',
      border: inverted ? '1px solid rgba(255,255,255,0.18)' : '1px solid var(--color-divider)',
      color: inverted ? '#fff' : 'var(--color-ink)',
      minWidth: '120px',
    }">
    <span class="inline-flex items-center justify-center w-6 h-6 rounded-full"
      :style="{ background: inverted ? 'rgba(255,255,255,0.2)' : 'var(--color-accent-soft)', color: inverted ? '#fff' : 'var(--color-accent)' }">
      <svg v-if="!playing" width="10" height="12" viewBox="0 0 10 12">
        <path d="M0 1l10 5L0 11z" fill="currentColor" />
      </svg>
      <span v-else class="w-2.5 h-2.5 rounded-[1px]" style="background: currentColor;" />
    </span>
    <span class="text-[13px] tabular">{{ meta.duration || 0 }}″</span>
    <!-- 静态条 -->
    <span class="flex items-end gap-[2px] h-3">
      <span v-for="i in 5" :key="i"
        :style="{
          width: '2px',
          height: (4 + (i*3)%9) + 'px',
          background: 'currentColor',
          opacity: playing ? 1 : 0.5,
          borderRadius: '1px',
        }" />
    </span>
    <audio ref="audioRef" :src="fullUrl" @ended="onAudioEnd" preload="none" class="hidden" />
  </div>

  <!-- ── 位置 ── -->
  <div v-else-if="type === 'location'"
    @click="openMap"
    class="rounded-xl px-3 py-2.5 flex items-center gap-3 active:opacity-80 cursor-pointer"
    :style="{
      background: inverted ? 'rgba(255,255,255,0.10)' : 'var(--color-card)',
      border: inverted ? '1px solid rgba(255,255,255,0.15)' : '1px solid var(--color-divider)',
      color: inverted ? '#fff' : 'var(--color-ink)',
      maxWidth: '240px',
    }">
    <span class="inline-flex items-center justify-center w-9 h-9 rounded-full"
      :style="{ background: inverted ? 'rgba(255,255,255,0.15)' : '#E5EDFA', color: inverted ? '#fff' : '#4D82E0' }">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
        <path d="M12 21s7-6.5 7-12a7 7 0 10-14 0c0 5.5 7 12 7 12z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
        <circle cx="12" cy="9" r="2.4" stroke="currentColor" stroke-width="1.6"/>
      </svg>
    </span>
    <div class="min-w-0 flex-1">
      <div class="text-[13.5px] font-medium" style="font-family: var(--font-serif);">位置</div>
      <div class="text-[11px] tabular mt-0.5"
        :style="{ color: inverted ? 'rgba(255,255,255,0.7)' : 'var(--color-ink-3)' }">
        {{ Number(meta.lat).toFixed(5) }}, {{ Number(meta.lon).toFixed(5) }}
      </div>
    </div>
  </div>
</template>
