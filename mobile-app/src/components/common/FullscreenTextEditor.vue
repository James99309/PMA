<!--
  FullscreenTextEditor - 全屏长文编辑器(便签/描述/日报正文/评论)。
  两种模式:
    · 默认(plain):纯文本 textarea(原行为,所有旧调用方不变)。
    · rich=true:contenteditable 富文本,支持内联图片(相册/拍照,即时显示+后台上传),
      内容以 HTML 存(旧纯文本/Markdown 兼容);"保存"按钮显示为「缩小」(仅收起,
      内容留在表单,随业务对象创建/提交时一起保存)。
  对外:v-model=open / value / title / placeholder / saveLabel / rich;emit save(text|html)。
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
            {{ saveLabel || (rich ? t('common.minimize') : t('common.save')) }}</span>
        </div>
        <!-- 富文本工具条:插入图片 -->
        <div v-if="rich" :style="{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px',
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
        <!-- rich: contenteditable -->
        <div v-if="rich" ref="ed" contenteditable="true" class="fte-editor" :data-ph="placeholder"
          @keyup="saveSel" @mouseup="saveSel"
          :style="{ flex: 1, width: '100%', boxSizing: 'border-box', padding: '18px 18px',
            background: '#F7F5F2', border: 'none', outline: 'none', overflowY: 'auto',
            fontSize: '16px', lineHeight: 1.7, color: '#1A1A1A',
            paddingBottom: 'calc(18px + env(safe-area-inset-bottom))' }" />
        <!-- plain: textarea(原行为) -->
        <textarea v-else ref="ta" v-model="draft" :placeholder="placeholder"
          :style="{ flex: 1, width: '100%', boxSizing: 'border-box', padding: '18px 18px',
            background: '#F7F5F2', border: 'none', outline: 'none', resize: 'none',
            fontSize: '16px', lineHeight: 1.7, color: '#1A1A1A',
            paddingBottom: 'calc(18px + env(safe-area-inset-bottom))' }" />
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
  rich: { type: Boolean, default: false },   // true=富文本(图片);false=纯文本
})
const emit = defineEmits(['update:modelValue', 'save'])

const open = computed({ get: () => props.modelValue, set: v => emit('update:modelValue', v) })
const draft = ref('')
const ta = ref(null)
const ed = ref(null)
const fileInput = ref(null)
const uploading = ref(false)
let savedRange = null
let pending = []   // 后台上传 promise

watch(() => props.modelValue, async v => {
  if (v) {
    pending = []
    await nextTick()
    if (props.rich) { if (ed.value) { ed.value.innerHTML = renderRich(props.value); ed.value.focus() } }
    else { draft.value = props.value || ''; ta.value?.focus() }
  }
})

function saveSel() {
  const sel = window.getSelection()
  if (sel && sel.rangeCount && ed.value && ed.value.contains(sel.anchorNode)) {
    savedRange = sel.getRangeAt(0).cloneRange()
  }
}

// 即时把(本地)图片插到光标处,后台上传后再把 src 换成服务器地址
function insertLocalThenUpload(localUrl, file) {
  const uid = 'u' + Date.now() + Math.floor((performance.now() % 1000))
  // 默认中等尺寸(不占满),宽度写进 HTML 以便各端一致显示
  const html = `<span class="arn-img" contenteditable="false" style="width:62%"><img data-uid="${uid}" src="${localUrl}"></span>&nbsp;`
  ed.value && ed.value.focus()
  const sel = window.getSelection()
  if (savedRange && sel) { sel.removeAllRanges(); sel.addRange(savedRange) }
  let ok = false
  try { ok = document.execCommand('insertHTML', false, html) } catch (e) { ok = false }
  if (!ok && ed.value) ed.value.insertAdjacentHTML('beforeend', html)
  saveSel()
  const p = uploadWorklogImage(file).then(res => {
    const url = res?.data?.data?.url
    const img = ed.value && ed.value.querySelector(`img[data-uid="${uid}"]`)
    if (url && img) { img.setAttribute('src', url); img.removeAttribute('data-uid') }
    else if (img) { const sp = img.closest('.arn-img'); (sp || img).remove() }
    if (localUrl.startsWith('blob:')) { try { URL.revokeObjectURL(localUrl) } catch (e) {} }
  }).catch(() => {
    const img = ed.value && ed.value.querySelector(`img[data-uid="${uid}"]`)
    if (img) { const sp = img.closest('.arn-img'); (sp || img).remove() }
  })
  pending.push(p)
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
      // 即时显示(capacitor 本地 URI),同时拿 blob 供后台上传
      const local = Capacitor.convertFileSrc ? Capacitor.convertFileSrc(photo.path || photo.webPath) : photo.webPath
      const r = await fetch(photo.webPath)
      const blob = await r.blob()
      const ext = (photo.format || 'jpeg').replace('jpg', 'jpeg')
      const file = new File([blob], `img_${Date.now()}.${ext === 'jpeg' ? 'jpg' : ext}`,
        { type: blob.type || `image/${ext}` })
      insertLocalThenUpload(local || photo.webPath, file)
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
  if (f) insertLocalThenUpload(URL.createObjectURL(f), f)
}

async function save() {
  if (props.rich) {
    if (pending.length) { uploading.value = true; await Promise.allSettled(pending); uploading.value = false; pending = [] }
    const html = ed.value ? ed.value.innerHTML : ''
    emit('save', isRichEmpty(html) ? '' : html)
  } else {
    emit('save', draft.value)
  }
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
