// 客户端渲染 PDF 第 1 页 → JPEG dataUrl (供 thumbnail / 全屏 view 用)
// pdfjs-dist 是动态 import (~500KB), 首次选 PDF 时才加载
//
// 用法:
//   const dataUrl = await renderPdfFirstPage(file, 800)
//   const blobUrl = makePdfBlobUrl(file)  // 给 iframe 全屏看

let _pdfjsPromise = null

async function loadPdfjs() {
  if (_pdfjsPromise) return _pdfjsPromise
  _pdfjsPromise = (async () => {
    const pdfjs = await import('pdfjs-dist/build/pdf.mjs')
    // worker: vite ?url 后缀 → 自动拷到 dist, 返回最终 URL
    const workerModule = await import('pdfjs-dist/build/pdf.worker.mjs?url')
    pdfjs.GlobalWorkerOptions.workerSrc = workerModule.default
    return pdfjs
  })()
  return _pdfjsPromise
}

export async function renderPdfFirstPage(blobOrFile, maxWidth = 800) {
  const pdfjs = await loadPdfjs()
  const arrayBuffer = await blobOrFile.arrayBuffer()
  const pdf = await pdfjs.getDocument({ data: arrayBuffer }).promise
  try {
    const page = await pdf.getPage(1)
    const viewport = page.getViewport({ scale: 1 })
    const scale = Math.min(maxWidth / viewport.width, 2)
    const scaledViewport = page.getViewport({ scale })
    const canvas = document.createElement('canvas')
    canvas.width = scaledViewport.width
    canvas.height = scaledViewport.height
    const ctx = canvas.getContext('2d')
    // 白底, 避免透明 PDF 在深色背景上看不清
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    await page.render({ canvasContext: ctx, viewport: scaledViewport }).promise
    return canvas.toDataURL('image/jpeg', 0.85)
  } finally {
    pdf.destroy()
  }
}

export function makePdfBlobUrl(blob) {
  return URL.createObjectURL(blob)
}
