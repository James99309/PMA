<!--
  ReceiptCaptureView · 拍发票连拍模式
  严格对齐 design_handoff/expense-receipt.jsx::ExReceiptCapture (L4-113)
  - 深色全屏 #0E1116
  - 顶部 chrome 44 高: × 关闭 / 拍发票·连拍模式 14/600 / ?帮助
  - 中部模拟发票卡 (78%宽 1.42:1, 旋转 -1.5deg, 红棕色 7B2F22 山东增值税)
  - 4 角白色取景框 3px
  - 已对齐发票边缘 toast
  - 底部黑半透明 panel:
    - 已拍 N 张 + 缩略 chip 条 + 完成 (N) 圆角 chip
    - 单张/连拍/从相册 模式切换 (连拍 active 带 accent 下划线)
    - 闪光 / 70x70 白色快门 / 反转
-->
<template>
  <div
    class="relative h-full overflow-hidden"
    :style="{ background: '#0E1116', color: '#fff', fontFamily: 'var(--font-sans)' }"
  >
    <div class="status-pad" :style="{ background: 'transparent' }" />

    <!-- 顶部 chrome -->
    <div
      class="absolute left-0 right-0 z-[5] flex items-center justify-between"
      :style="{ top: '54px', height: '44px', padding: '0 16px' }"
    >
      <div
        class="flex items-center justify-center"
        :style="{
          width: '28px', height: '28px', borderRadius: '14px',
          background: 'rgba(255,255,255,.16)', fontSize: '16px',
        }"
        @click="onClose"
      >×</div>
      <div :style="{ fontSize: '14px', fontWeight: 600 }">拍发票 · 连拍模式</div>
      <div
        class="flex items-center justify-center"
        :style="{
          width: '28px', height: '28px', borderRadius: '14px',
          background: 'rgba(255,255,255,.16)', fontSize: '14px',
        }"
      >?</div>
    </div>

    <!-- 取景区:已拍照片预览 OR 模拟发票 -->
    <div
      class="absolute flex items-center justify-center"
      :style="{ top: '100px', left: 0, right: 0, bottom: '230px' }"
    >
      <!-- 最近一张拍到的实际照片 -->
      <div
        v-if="lastShotPreview"
        :style="{
          width: '78%', aspectRatio: '1.42 / 1',
          backgroundImage: `url(${lastShotPreview})`,
          backgroundSize: 'cover', backgroundPosition: 'center',
          transform: 'rotate(-1.5deg)',
          boxShadow: 'var(--shadow-ex-receipt)',
        }"
      />
      <!-- 默认: 模拟发票卡(取景器装饰) -->
      <div
        v-else
        :style="{
          width: '78%', aspectRatio: '1.42 / 1',
          background: '#F5EFE3', position: 'relative', overflow: 'hidden',
          transform: 'rotate(-1.5deg)',
          boxShadow: 'var(--shadow-ex-receipt)',
        }"
      >
        <div
          :style="{
            position: 'absolute', top: '8px', left: 0, right: 0, textAlign: 'center',
            color: '#7B2F22', fontSize: '8px', letterSpacing: '1.5px',
            fontFamily: 'var(--font-serif)',
          }"
        >山东增值税普通发票</div>
        <div
          :style="{
            position: 'absolute', top: '22px', left: '8px', right: '8px',
            color: '#7B2F22', fontSize: '6px',
          }"
        >发票代码 044126 &nbsp;&nbsp; 发票号码 17362245</div>
        <div
          v-for="t in [40, 50, 60, 70, 80, 90, 100, 110]"
          :key="t"
          :style="{
            position: 'absolute', top: `${t}px`, left: '12px', right: '12px',
            height: '1px', background: '#C7B79C',
          }"
        />
        <div
          :style="{
            position: 'absolute', bottom: '8px', right: '10px', color: '#7B2F22',
            fontSize: '7px', fontFamily: 'var(--font-serif)',
          }"
        >¥224.00</div>
      </div>

      <!-- 4 角取景边框 -->
      <div
        class="absolute pointer-events-none"
        :style="{ top: '28px', left: '8%', right: '8%', bottom: '28px' }"
      >
        <div :style="{ position: 'absolute', top: 0, left: 0, width: '20px', height: '20px', borderTop: '3px solid #fff', borderLeft: '3px solid #fff' }" />
        <div :style="{ position: 'absolute', top: 0, right: 0, width: '20px', height: '20px', borderTop: '3px solid #fff', borderRight: '3px solid #fff' }" />
        <div :style="{ position: 'absolute', bottom: 0, left: 0, width: '20px', height: '20px', borderBottom: '3px solid #fff', borderLeft: '3px solid #fff' }" />
        <div :style="{ position: 'absolute', bottom: 0, right: 0, width: '20px', height: '20px', borderBottom: '3px solid #fff', borderRight: '3px solid #fff' }" />
      </div>

      <!-- toast -->
      <div
        :style="{
          position: 'absolute', bottom: '-22px', fontSize: '11px', color: '#fff',
          background: 'rgba(0,0,0,.5)', padding: '4px 10px', borderRadius: '12px',
        }"
      >{{ receipts.length === 0 ? '请将发票放在取景框内' : `已拍 ${receipts.length} 张` }}</div>
    </div>

    <!-- 底部 panel -->
    <div
      class="absolute left-0 right-0 bottom-0"
      :style="{ padding: '20px 16px 28px', background: 'rgba(0,0,0,.35)', paddingBottom: 'calc(28px + env(safe-area-inset-bottom))' }"
    >
      <!-- 已拍 chips -->
      <div
        class="flex items-center"
        :style="{ marginBottom: '18px', gap: '8px' }"
      >
        <div
          :style="{ fontSize: '11px', color: 'rgba(255,255,255,.7)', flexShrink: 0 }"
        >已拍 {{ receipts.length }} 张</div>
        <div class="flex-1 flex overflow-x-auto no-scrollbar" :style="{ gap: '6px' }">
          <div
            v-for="(r, i) in receipts"
            :key="i"
            :style="{
              width: '38px', height: '26px', borderRadius: '3px',
              backgroundImage: `url(${r.dataUrl})`, backgroundSize: 'cover', backgroundPosition: 'center',
              backgroundColor: '#F5EFE3',
              position: 'relative', flexShrink: 0,
            }"
          >
            <div
              class="flex items-center justify-center"
              :style="{
                position: 'absolute', top: '-5px', right: '-5px',
                width: '12px', height: '12px', borderRadius: '6px',
                background: 'var(--color-ex-green)', color: '#fff',
                fontSize: '9px', fontWeight: 700,
              }"
            >✓</div>
          </div>
        </div>
        <div
          :style="{
            fontSize: '13px', color: '#fff',
            background: receipts.length > 0 ? 'var(--color-ex-accent)' : 'rgba(255,255,255,.16)',
            padding: '6px 12px', borderRadius: '14px',
            fontWeight: 600, flexShrink: 0,
            opacity: receipts.length > 0 ? 1 : 0.5,
          }"
          @click="receipts.length > 0 && onFinish()"
        >完成 ({{ receipts.length }})</div>
      </div>

      <!-- 模式 chip -->
      <div class="flex justify-center" :style="{ gap: '16px', marginBottom: '14px' }">
        <span
          :style="{
            fontSize: '13px',
            color: mode === 'single' ? '#fff' : 'rgba(255,255,255,.5)',
            fontWeight: mode === 'single' ? 600 : 400,
            borderBottom: mode === 'single' ? '2px solid var(--color-ex-accent)' : 'none',
            paddingBottom: '4px',
          }"
          @click="mode = 'single'"
        >单张</span>
        <span
          :style="{
            fontSize: '13px',
            color: mode === 'continuous' ? '#fff' : 'rgba(255,255,255,.5)',
            fontWeight: mode === 'continuous' ? 600 : 400,
            borderBottom: mode === 'continuous' ? '2px solid var(--color-ex-accent)' : 'none',
            paddingBottom: '4px',
          }"
          @click="mode = 'continuous'"
        >连拍</span>
        <span
          :style="{
            fontSize: '13px',
            color: mode === 'gallery' ? '#fff' : 'rgba(255,255,255,.5)',
            fontWeight: mode === 'gallery' ? 600 : 400,
            borderBottom: mode === 'gallery' ? '2px solid var(--color-ex-accent)' : 'none',
            paddingBottom: '4px',
          }"
          @click="onPickGallery"
        >从相册</span>
      </div>

      <!-- 快门 -->
      <div class="flex items-center justify-between">
        <div
          class="flex items-center justify-center"
          :style="{
            width: '40px', height: '40px', borderRadius: '20px',
            background: 'rgba(255,255,255,.16)', fontSize: '14px',
          }"
        >⚡</div>
        <div
          class="flex items-center justify-center"
          :style="{ width: '70px', height: '70px', borderRadius: '35px', background: '#fff', position: 'relative' }"
          @click="onShutter"
        >
          <div
            :style="{
              width: '56px', height: '56px', borderRadius: '28px',
              background: '#fff', border: '3px solid #0E1116',
              transition: 'transform 90ms',
              transform: shutterPressed ? 'scale(0.92)' : 'scale(1)',
            }"
          />
        </div>
        <div
          class="flex items-center justify-center"
          :style="{
            width: '40px', height: '40px', borderRadius: '20px',
            background: 'rgba(255,255,255,.16)', fontSize: '16px',
          }"
        >↺</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera'
import { useExpenseStore } from '@/stores/expense'

const route = useRoute()
const router = useRouter()
const store = useExpenseStore()
const expenseId = computed(() => parseInt(route.params.id))

const mode = ref('continuous')
const shutterPressed = ref(false)

const receipts = computed(() => store.pendingReceipts)
const lastShotPreview = computed(() =>
  receipts.value.length > 0 ? receipts.value[receipts.value.length - 1].dataUrl : null,
)

onMounted(() => {
  // 进入时如果不是当前 expense 的票队列, 清空
  if (store.currentReceiptExpenseId !== expenseId.value) {
    store.clearPendingReceipts()
    store.currentReceiptExpenseId = expenseId.value
  }
})

async function onShutter() {
  shutterPressed.value = true
  setTimeout(() => { shutterPressed.value = false }, 100)
  try {
    const photo = await Camera.getPhoto({
      quality: 88,
      allowEditing: false,
      resultType: CameraResultType.DataUrl,
      source: CameraSource.Camera,
      saveToGallery: false,
    })
    if (photo?.dataUrl) {
      const blob = await dataUrlToBlob(photo.dataUrl)
      store.addPendingReceipt({ dataUrl: photo.dataUrl, blob })
    }
  } catch (e) {
    if (!String(e).includes('cancel')) {
      alert('拍照失败: ' + (e.message || e))
    }
  }
}

async function onPickGallery() {
  mode.value = 'gallery'
  try {
    const photo = await Camera.getPhoto({
      quality: 88,
      allowEditing: false,
      resultType: CameraResultType.DataUrl,
      source: CameraSource.Photos,
    })
    if (photo?.dataUrl) {
      const blob = await dataUrlToBlob(photo.dataUrl)
      store.addPendingReceipt({ dataUrl: photo.dataUrl, blob })
    }
  } catch (e) {
    if (!String(e).includes('cancel')) {
      alert('选择失败: ' + (e.message || e))
    }
  }
}

async function dataUrlToBlob(dataUrl) {
  const res = await fetch(dataUrl)
  return res.blob()
}

function onClose() {
  if (receipts.value.length > 0 && !confirm('放弃已拍的发票?')) return
  store.clearPendingReceipts()
  router.back()
}

function onFinish() {
  router.replace(`/expense/${expenseId.value}/processing`)
}
</script>
