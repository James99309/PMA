/**
 * AT 文件模块共享工具 — 资料管理(用户页) + 文件管理后台(管理员页) 共用。
 * 提供:大小/时间格式化、文件图标、预览(office→PDF / 图片 / 下载兜底)。
 */
(function (g) {
  'use strict';

  function fmtSize(n) {
    n = n || 0; if (n < 1024) return n + ' B';
    var u = ['KB', 'MB', 'GB', 'TB'], i = -1;
    do { n /= 1024; i++; } while (n >= 1024 && i < u.length - 1);
    return n.toFixed(n < 10 ? 1 : 0) + ' ' + u[i];
  }
  function fmtTime(s) { if (!s) return ''; return String(s).slice(0, 16).replace('T', ' '); }
  function icon(name) {
    var e = (name || '').split('.').pop().toLowerCase();
    var map = {
      pdf: '📕', doc: '📘', docx: '📘', xls: '📗', xlsx: '📗', csv: '📗',
      ppt: '📙', pptx: '📙', zip: '🗜️', rar: '🗜️', '7z': '🗜️',
      png: '🖼️', jpg: '🖼️', jpeg: '🖼️', gif: '🖼️', webp: '🖼️', heic: '🖼️', svg: '🖼️',
      mp4: '🎬', mov: '🎬', avi: '🎬', mp3: '🎵', wav: '🎵',
      txt: '📄', md: '📄', json: '📄'
    };
    return map[e] || '📄';
  }
  function isOffice(name, mime) {
    return /word|presentation|powerpoint|msword|officedocument/.test(mime || '') || /\.(docx?|pptx?|xlsx?)$/i.test(name || '');
  }
  function isPreviewable(name) { return /\.(pdf|png|jpe?g|gif|webp|heic)$/i.test(name || ''); }

  /**
   * 预览文件。opts: { name, mime, officeUrl, inlineUrl, downloadUrl }
   * office → officeUrl(PDF);可内联 → inlineUrl;否则下载 downloadUrl。
   */
  function preview(opts) {
    var name = opts.name || '', office = isOffice(name, opts.mime);
    if (g.ATFilePreview && (office || isPreviewable(name))) {
      ATFilePreview.open('', [{
        name: name,
        url: office ? opts.officeUrl : opts.inlineUrl,
        type: office ? 'pdf' : (name.split('.').pop() || '')
      }]);
    } else {
      g.open(opts.downloadUrl, '_blank');
    }
  }

  g.AtFileUtils = {
    fmtSize: fmtSize, fmtTime: fmtTime, icon: icon,
    isOffice: isOffice, isPreviewable: isPreviewable, preview: preview
  };
})(window);
