<!--
  FullscreenTextEditor - 全屏富文本编辑器(便签/描述/日报正文)。
  contenteditable 富文本:支持内联图片(相册/拍照插入,上传后内联显示)。
  内容以 HTML 存储(props.value 进/出均为 HTML;旧纯文本/Markdown 自动兼容)。
  对外接口不变:v-model=open / value / title / placeholder / saveLabel;emit save(html)。
-->
<template>
  <Teleport to="body">
    <transition name="fte">
      <div v-if="open" class="fixed inset-0 z-50"
        :style="{ background: '#F7F5F2', display: 'flex', flexDirection: 'column' }">
        <div class="status-pad" />
        <div :style="{ height: '52px', display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', padding: '0 16px',
          borderBottom: '1px solid #EBE6DD', flexShrink: 0 }">
          <span @click="cancel" class="active:opacity-60"
            :style="{ fontSize: '14px', color: '#7A7570' }">{{ t('common.cancel') }}</span>
          <span :style="{ fontSize: '15px', fontWeight: 600, color: '#1A1A1A' }">{{ title }}</span>
          <span @click="save" class="active:opacity-60"
            :style="{ fontSize: '14px', fontWeight: 600, color: '#D97757' }">
            {{ saveLabel || t('common.save') }}</span>
        </div>
        <!-- 工具条:插入图片 -->
        <div :style="{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px',
          borderBottom: '1px solid #F0ECE4', flexShrink: 0 }">
          <button type="button" @click="insertImage" :disabled="uploading"
            :style="{ display: 'inline-flex', alignItems: 'center', gap: '5px', height: '32px',
              padding: '0 12px', borderRadius: '8px', border: '1px solid #E3DDD2',
              background: '#fff', color: uploading ? '#B8B2A8' : '#5A554E', fontSize: '13px' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
            <span>{{ uploading ? t('common.uploading') : t('common.insertImage') }}</span>
          </button>
        </div>
        <div ref="ed" contenteditable="true" class="fte-editor" :data-ph="placeholder"
          @keyup="saveSel" @mouseup="saveSel"
          :style="{ flex: 1, width: '100%', boxSizing: 'border-box', padding: '18px 18px',
            background: '#F7F5F2', border: 'none', outline: 'none', overflowY: 'auto',
            fontSize: '16px', lineHeight: 1.7, color: '#1A1A1A',
            paddingBottom: 'calc(18px + env(safe-area-inset-bottom))' }" />
        <!-- web 回退:文件选择 -->
        <input ref="fileInput" type="file" accept="image/*" class="fte-hidden" @change="onFilePick" />
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { Capacitor } from '@capacitor/core'
import { renderRich, isRichEmpty } from '@/utils/richNote'
import { uploadWorklogImage } from '@/api/worklog'

const { t } = useI18n()
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  value: { type: String, default: '' },
  title: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  saveLabel: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'save'])

const open = computed({ get: () => props.modelValue, set: v => emit('update:modelValue', v) })
const ed = ref(null)
const fileInput = ref(null)
const uploading = ref(false)
let savedRange = null

watch(() => props.modelValue, async v => {
  if (v) {
    await nextTick()
    if (ed.value) { ed.value.innerHTML = renderRich(props.value); ed.value.focus() }
  }
})

function saveSel() {
  const sel = window.getSelection()
  if (sel && sel.rangeCount && ed.value && ed.value.contains(sel.anchorNode)) {
    savedRange = sel.getRangeAt(0).cloneRange()
  }
}

function insertImgHtml(url) {
  const html = `<span class="arn-img" contenteditable="false"><img src="${url}"></span>&nbsp;`
  ed.value && ed.value.focus()
  const sel = window.getSelection()
  if (savedRange && sel) { sel.removeAllRanges(); sel.addRange(savedRange) }
  let ok = false
  try { ok = document.execCommand('insertHTML', false, html) } catch (e) { ok = false }
  if (!ok && ed.value) ed.value.insertAdjacentHTML('beforeend', html)
  saveSel()
}

async function doUpload(file) {
  if (!file) return
  uploading.value = true
  try {
    const res = await uploadWorklogImage(file)
    const url = res?.data?.data?.url
    if (url) insertImgHtml(url)
  } catch (e) { /* 静默:网络错误 */ }
  finally { uploading.value = false }
}

async function insertImage() {
  saveSel()
  if (Capacitor.isNativePlatform?.()) {
    try {
      const { Camera, CameraResultType, CameraSource } = await import('@capacitor/camera')
      const photo = await Camera.getPhoto({
        quality: 85, allowEditing: false, resultType: CameraResultType.Uri,
        source: CameraSource.Prompt,
        promptLabelHeader: t('common.insertImage'),
        promptLabelPhoto: t('common.fromGallery'),
        promptLabelPicture: t('common.takePhoto'),
      })
      const r = await fetch(photo.webPath)
      const blob = await r.blob()
      const ext = (photo.format || 'jpeg').replace('jpg', 'jpeg')
      const file = new File([blob], `img_${Date.now()}.${ext === 'jpeg' ? 'jpg' : ext}`,
        { type: blob.type || `image/${ext}` })
      await doUpload(file)
    } catch (e) {
      if (e?.message?.includes('cancel')) return
      fileInput.value?.click()
    }
  } else {
    fileInput.value?.click()
  }
}

function onFilePick(e) {
  const f = e.target.files?.[0]
  e.target.value = ''
  if (f) doUpload(f)
}

function save() {
  const html = ed.value ? ed.value.innerHTML : ''
  emit('save', isRichEmpty(html) ? '' : html)
  open.value = false
}
function cancel() { open.value = false }
</script>

<style scoped>
.fte-enter-active, .fte-leave-active { transition: opacity .15s; }
.fte-enter-from, .fte-leave-to { opacity: 0; }
.fte-editor:empty:before { content: attr(data-ph); color: #B8B2A8; }
.fte-editor :deep(.arn-img) { display: inline-block; max-width: 100%; line-height: 0; vertical-align: top; border-radius: 8px; margin: 4px 0; }
.fte-editor :deep(.arn-img > img), .fte-editor :deep(img) { max-width: 100%; height: auto; display: block; border-radius: 8px; }
.fte-hidden { display: none; }
</style>
