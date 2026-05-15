<script setup>
// Composer + 按钮展开后的 4 操作面板：相册 / 拍照 / 位置 / 文件
// 严格对齐 chat-input-states.jsx ChatPlusPanel 设计
import { ref } from 'vue'
import { Capacitor } from '@capacitor/core'

const emit = defineEmits([
  'pick-image',  // 用户选了图片 → File[]
  'pick-camera', // 用户拍照后 → File
  'pick-file',   // 用户选了文件 → File
  'share-location', // 用户点了位置 → 由父组件打开 LocationSheet
  'close',
])

const galleryInput = ref(null)
const cameraInput = ref(null)
const fileInput = ref(null)

function onGallery(e) {
  const files = Array.from(e.target.files || [])
  if (files.length) emit('pick-image', files)
  e.target.value = ''
}
function onCamera(e) {
  const f = e.target.files?.[0]
  if (f) emit('pick-camera', f)
  e.target.value = ''
}
function onFile(e) {
  const f = e.target.files?.[0]
  if (f) emit('pick-file', f)
  e.target.value = ''
}

// 原生 iPhone 相机：完整聚焦/变焦/视频切换 UI（需要 @capacitor/camera 插件 + 原生重建）
async function openNativeCamera() {
  try {
    const { Camera, CameraResultType, CameraSource } = await import('@capacitor/camera')
    const photo = await Camera.getPhoto({
      quality: 85,
      allowEditing: false,
      resultType: CameraResultType.Uri,
      source: CameraSource.Camera,
      saveToGallery: false,
    })
    // photo.webPath 是 capacitor:// 本地 URI；fetch 后转 File
    const res = await fetch(photo.webPath)
    const blob = await res.blob()
    const ext = (photo.format || 'jpeg').replace('jpg', 'jpeg')
    const file = new File([blob], `photo_${Date.now()}.${ext === 'jpeg' ? 'jpg' : ext}`,
      { type: blob.type || `image/${ext}` })
    emit('pick-camera', file)
  } catch (e) {
    // 用户取消 / 插件未装 → 回退到 HTML capture input
    if (e?.message?.includes('cancelled') || e?.message?.includes('canceled')) return
    cameraInput.value?.click()
  }
}

const ACTIONS = [
  { key: 'gallery', label: '相册', color: 'var(--color-accent)' },
  { key: 'camera',  label: '拍照', color: '#3a8c5a' },
  { key: 'location',label: '位置', color: '#4D82E0' },
  { key: 'file',    label: '文件', color: '#7355C9' },
]

function handleAction(key) {
  if (key === 'gallery')  galleryInput.value?.click()
  else if (key === 'camera')   {
    // 原生 iOS 用 Capacitor Camera 插件; web 环境 fallback HTML capture
    if (Capacitor.isNativePlatform?.()) openNativeCamera()
    else cameraInput.value?.click()
  }
  else if (key === 'location') emit('share-location')
  else if (key === 'file')     fileInput.value?.click()
}
</script>

<template>
  <div class="px-6 pt-3 pb-5"
    style="background: var(--color-bg); border-top: 1px solid var(--color-divider);">
    <div class="grid grid-cols-4 gap-3">
      <button v-for="a in ACTIONS" :key="a.key"
        type="button"
        @click="handleAction(a.key)"
        class="flex flex-col items-center gap-2 active:opacity-70">
        <div class="w-[60px] h-[60px] rounded-[18px] inline-flex items-center justify-center"
          :style="{
            background: 'var(--color-card)',
            border: '1px solid var(--color-divider)',
            color: a.color,
            boxShadow: '0 1px 2px rgba(0,0,0,0.03)',
          }">
          <!-- 相册 -->
          <svg v-if="a.key==='gallery'" width="22" height="22" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" stroke-width="1.6"/>
            <circle cx="9" cy="10" r="1.6" fill="currentColor"/>
            <path d="M3 17l5-5 4 4 3-3 6 6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <!-- 拍照 -->
          <svg v-else-if="a.key==='camera'" width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path d="M9 6l1.5-2h3L15 6h4a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h4z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
            <circle cx="12" cy="12.5" r="3.6" stroke="currentColor" stroke-width="1.6"/>
          </svg>
          <!-- 位置 -->
          <svg v-else-if="a.key==='location'" width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path d="M12 21s7-6.5 7-12a7 7 0 10-14 0c0 5.5 7 12 7 12z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
            <circle cx="12" cy="9" r="2.4" stroke="currentColor" stroke-width="1.6"/>
          </svg>
          <!-- 文件 -->
          <svg v-else width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
            <path d="M14 3v5h5" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
          </svg>
        </div>
        <span class="text-[12px] font-medium" style="color: var(--color-ink-2);">{{ a.label }}</span>
      </button>
    </div>

    <!-- 隐藏的原生 file input；iOS WKWebView 支持 capture/accept -->
    <input ref="galleryInput" type="file" accept="image/*" multiple class="hidden" @change="onGallery" />
    <input ref="cameraInput" type="file" accept="image/*" capture="environment" class="hidden" @change="onCamera" />
    <input ref="fileInput" type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.dwg,application/*" class="hidden" @change="onFile" />
  </div>
</template>
