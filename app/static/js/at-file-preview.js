/**
 * AT 文件预览模态(全局单例)
 *
 * API:
 *   ATFilePreview.open(label, files, notes)
 *     label: 顶部 pill 标签(可空,如 "供应商确认"、"快递单")
 *     files: [{name, url, size?, type?, uploaded_at?}] — 单元素或多个
 *     notes: 文件下方的备注块文本(可空)
 *   ATFilePreview.close()
 *
 * 行为:
 *   - 单文件 → 模态 580px,直接展示
 *   - 多文件 → 模态 820px,左侧文件列表 + 右侧预览面板
 *   - 图片 → <img>,PDF → <iframe>,其他 → 类型色块占位
 *   - 备注块(若 notes 非空)固定在预览下方
 *
 * 依赖 DOM(由 at_file_preview_modal() 宏渲染):
 *   #atFilePreview          模态外层
 *   #atFilePreviewShell     模态主体(JS 控制 maxWidth)
 *   #atFilePreviewTitle     标题(JS 写入 label · 附件)
 *   #atFilePreviewBody      内容容器(JS 注入 HTML)
 *
 * 向后兼容:同时暴露 window.atOpenFilePreview / atCloseFilePreview / atSelectPreviewFile
 *   旧调用 atOpenFilePreview(stageKey, stageLabel, files, notes) 仍 work
 *   stageKey 参数被忽略(没有实际用途,仅历史保留)
 */
(function (window) {
  'use strict';

  const FILE_ICON = {
    pdf:  { color: '#A23B3B', tint: '#F0DAD8', label: 'PDF' },
    zip:  { color: '#7A5AE0', tint: '#E2DCF5', label: 'ZIP' },
    img:  { color: '#2F7155', tint: '#DCE8E0', label: 'IMG' },
    jpg:  { color: '#2F7155', tint: '#DCE8E0', label: 'JPG' },
    jpeg: { color: '#2F7155', tint: '#DCE8E0', label: 'JPG' },
    png:  { color: '#2F7155', tint: '#DCE8E0', label: 'PNG' },
    doc:  { color: '#2A5F8F', tint: '#DDE6F1', label: 'DOC' },
    docx: { color: '#2A5F8F', tint: '#DDE6F1', label: 'DOC' },
    xls:  { color: '#2F7155', tint: '#DCE8E0', label: 'XLS' },
    xlsx: { color: '#2F7155', tint: '#DCE8E0', label: 'XLS' },
    csv:  { color: '#2F7155', tint: '#DCE8E0', label: 'CSV' },
    ppt:  { color: '#C2703B', tint: '#F2E2D6', label: 'PPT' },
    pptx: { color: '#C2703B', tint: '#F2E2D6', label: 'PPT' },
    rar:  { color: '#7A5AE0', tint: '#E2DCF5', label: 'RAR' },
    '7z': { color: '#7A5AE0', tint: '#E2DCF5', label: '7Z'  },
    dwg:  { color: '#2A6F7A', tint: '#D8E9EC', label: 'DWG' },
    txt:  { color: '#5C5A54', tint: '#E5E3DD', label: 'TXT' },
  };

  function fileMeta(f) {
    const ext = String(f.type || (f.name || '').split('.').pop() || '').toLowerCase();
    return FILE_ICON[ext] || FILE_ICON.doc;
  }

  function fmtFileSize(b) {
    if (b == null) return '';
    if (b < 1024) return b + ' B';
    if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB';
    return (b / 1024 / 1024).toFixed(1) + ' MB';
  }

  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  }

  // 内部状态(模块作用域)
  let _files = [];
  let _active = 0;
  let _notes = '';
  let _label = '';

  function open(label, files, notes) {
    _files = files || [];
    _active = 0;
    _notes = notes || '';
    _label = label || '';

    const modal = document.getElementById('atFilePreview');
    if (!modal) {
      console.error('[ATFilePreview] atFilePreview modal DOM not found. Include at_file_preview_modal() macro on the page.');
      return;
    }
    const shell = document.getElementById('atFilePreviewShell');
    shell.style.maxWidth = _files.length > 1 ? '820px' : '580px';
    document.getElementById('atFilePreviewTitle').textContent = _label ? (_label + ' · ' + t('附件')) : t('附件预览');
    renderBody();
    modal.style.display = 'flex';
  }

  function close() {
    const modal = document.getElementById('atFilePreview');
    if (modal) modal.style.display = 'none';
  }

  function selectFile(idx) {
    _active = idx;
    renderBody();
  }

  function renderBody() {
    const files = _files;
    const active = _active;
    const file = files[active];

    // 阶段标签 pill
    const pillHtml = _label ? `
      <div style="margin-bottom:14px;">
        <span style="display:inline-flex;align-items:center;gap:6px;
                     background:var(--bg-sunk);color:var(--ink-2);
                     padding:2px 8px;border-radius:999px;font-size:11px;
                     font-weight:500;line-height:1.5;white-space:nowrap;letter-spacing:0.02em;">
          ${t('阶段')} · ${escapeHtml(_label)}
        </span>
      </div>` : '';

    if (!files.length) {
      document.getElementById('atFilePreviewBody').innerHTML = pillHtml +
        `<div style="padding:40px;text-align:center;color:var(--ink-3);font-size:13px;">${t('暂无附件')}</div>`;
      return;
    }

    const multi = files.length > 1;

    // 多文件:左侧文件列表
    const listHtml = !multi ? '' : `
      <div style="border-right:1px solid var(--line);padding-right:12px;">
        <div class="at-mono at-dim" style="font-size:10.5px;letter-spacing:0.1em;margin-bottom:10px;">
          ${t('文件')} · ${files.length}
        </div>
        <div style="display:flex;flex-direction:column;gap:4px;">
          ${files.map((f, i) => {
            const m = fileMeta(f);
            const isActive = i === active;
            return `
              <button onclick="ATFilePreview._selectFile(${i})"
                      style="display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:6px;
                             text-align:left;background:${isActive ? 'var(--bg-active)' : 'transparent'};
                             border:1px solid ${isActive ? 'var(--line-2)' : 'transparent'};">
                <span style="width:26px;height:30px;border-radius:4px;
                             background:${m.tint};color:${m.color};
                             display:inline-flex;align-items:center;justify-content:center;
                             font-size:9px;font-weight:600;letter-spacing:0.04em;
                             font-family:var(--font-mono);flex-shrink:0;">${m.label}</span>
                <div style="flex:1;min-width:0;">
                  <div style="font-size:12px;font-weight:500;color:var(--ink-2);
                              overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${escapeHtml(f.name || '')}</div>
                  <div class="at-dim at-mono" style="font-size:10.5px;margin-top:1px;">${escapeHtml(fmtFileSize(f.size) || '')}</div>
                </div>
              </button>`;
          }).join('')}
        </div>
      </div>`;

    // 预览面板:PDF/图片直显,其他色块占位
    const meta = fileMeta(file);
    const ext = String(file.type || (file.name || '').split('.').pop() || '').toLowerCase();
    const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'img'].includes(ext);
    const isPdf = (ext === 'pdf');
    const hasUrl = !!(file.url && file.url !== '#');

    let previewInner;
    if (isImage && hasUrl) {
      previewInner = `
        <img src="${escapeHtml(file.url)}" alt="${escapeHtml(file.name || '')}"
             style="max-width:100%;max-height:100%;min-width:0;min-height:0;
                    width:auto;height:auto;object-fit:contain;border-radius:4px;display:block;"
             onerror="this.parentElement.innerHTML='<div class=\\'at-dim\\' style=\\'font-size:12px;\\'>${t('图片加载失败')}</div>'">`;
    } else if (isPdf && hasUrl) {
      previewInner = `
        <iframe src="${escapeHtml(file.url)}#toolbar=0&view=FitH"
                title="${escapeHtml(file.name || '')}"
                style="width:100%;height:100%;min-width:0;border:0;border-radius:4px;background:#fff;"></iframe>`;
    } else {
      previewInner = `
        <div style="width:56px;height:70px;border-radius:8px;
                    background:${meta.tint};color:${meta.color};
                    display:flex;align-items:center;justify-content:center;
                    font-family:var(--font-mono);font-weight:700;font-size:14px;letter-spacing:0.05em;">
          ${meta.label}
        </div>
        <div class="at-dim" style="font-size:12px;">${hasUrl ? t('此格式暂不支持页内预览') : t('文件预览(示意)')}</div>`;
    }

    const showFrame = isImage || isPdf;
    const paneHtml = `
      <div>
        <div style="background:${showFrame ? 'var(--bg-elev)' : 'var(--bg-page)'};
                    border:${showFrame ? '1px solid var(--line)' : '1px dashed var(--line-2)'};
                    border-radius:8px;height:320px;
                    display:flex;align-items:center;justify-content:center;
                    flex-direction:column;gap:10px;position:relative;overflow:hidden;padding:0;">
          ${previewInner}
        </div>
        <div style="margin-top:14px;padding:10px 14px;
                    background:var(--bg-page);border-radius:8px;border:1px solid var(--line);
                    display:flex;align-items:center;gap:12px;">
          <div style="flex:1;min-width:0;">
            <div style="font-size:13px;font-weight:500;color:var(--ink);
                        overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${escapeHtml(file.name || '')}</div>
            <div class="at-dim at-mono at-tab-num" style="font-size:11px;margin-top:2px;">${escapeHtml(fmtFileSize(file.size) || (file.uploaded_at || ''))}</div>
          </div>
          <a href="${file.url || '#'}" download="${escapeHtml(file.name || '')}"
             style="height:28px;padding:0 10px;display:inline-flex;align-items:center;gap:6px;
                    background:transparent;color:var(--ink);border:1px solid var(--line-2);
                    border-radius:6px;font-size:12px;font-weight:500;text-decoration:none;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 3v12M7 10l5 5 5-5M5 21h14"/>
            </svg>
            ${t('下载')}
          </a>
        </div>
      </div>`;

    // 备注块(若有)— 在文件预览下方
    const notesHtml = _notes ? `
      <div style="margin-top:14px;padding:12px 14px;background:var(--bg-page);
                  border:1px solid var(--line);border-radius:8px;">
        <div class="at-mono at-dim" style="font-size:10.5px;letter-spacing:0.1em;
                     margin-bottom:6px;text-transform:uppercase;">${t('备注')}</div>
        <div style="font-size:12.5px;color:var(--ink-2);line-height:1.55;
                    white-space:pre-wrap;word-break:break-word;">${escapeHtml(_notes)}</div>
      </div>` : '';

    document.getElementById('atFilePreviewBody').innerHTML = pillHtml + `
      <div style="display:grid;grid-template-columns:${multi ? '200px minmax(0, 1fr)' : 'minmax(0, 1fr)'};gap:16px;min-height:0;">
        ${listHtml}
        ${paneHtml}
      </div>` + notesHtml;
  }

  // 公共 API
  window.ATFilePreview = {
    open: open,
    close: close,
    _selectFile: selectFile,   // 内部用,onclick 引用
  };

  // ─── 向后兼容(老调用 atOpenFilePreview/atCloseFilePreview/atSelectPreviewFile) ───
  window.atOpenFilePreview = function (stageKey, stageLabel, files, notes) {
    // stageKey 参数已废弃,仅历史保留;实际用 stageLabel 作为 pill 标签
    open(stageLabel, files, notes);
  };
  window.atCloseFilePreview = close;
  window.atSelectPreviewFile = selectFile;

})(window);
