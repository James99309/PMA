/**
 * CLI Terminal Markdown Renderer
 *
 * 基于 marked.js v15+（vendor/marked/marked.min.js）。
 * 不覆盖默认 renderer，用 CSS 样式化标准 HTML 输出，避免 API 兼容问题。
 *
 * 用法:
 *   const renderer = new CliMarkdownRenderer();
 *   container.innerHTML = renderer.render(markdownText);
 */

class CliMarkdownRenderer {
  constructor() {
    // marked v15 默认输出即可，通过 CSS 样式化
  }

  /**
   * 渲染 Markdown 文本为 HTML
   */
  render(text) {
    if (!text) return '';
    if (typeof marked === 'undefined') return this._escapeHtml(text);
    try {
      const html = marked.parse(text, { breaks: true, gfm: true });
      return this._postProcess(html);
    } catch {
      return this._escapeHtml(text);
    }
  }

  /**
   * 流式渲染（不完整 markdown 安全处理）
   */
  renderStreaming(text) {
    if (!text) return '';
    if (typeof marked === 'undefined') return this._escapeHtml(text);
    try {
      let safeText = text;
      const codeBlockCount = (safeText.match(/```/g) || []).length;
      if (codeBlockCount % 2 !== 0) {
        safeText += '\n```';
      }
      const html = marked.parse(safeText, { breaks: true, gfm: true });
      return this._postProcess(html);
    } catch {
      return this._escapeHtml(text);
    }
  }

  /**
   * 后处理：添加 CSS 类、链接新窗口打开、业务实体高亮
   */
  _postProcess(html) {
    // 表格加 wrapper
    html = html.replace(/<table>/g, '<div class="cli-md-table-wrap"><table class="cli-md-table">');
    html = html.replace(/<\/table>/g, '</table></div>');

    // 链接新窗口打开
    html = html.replace(/<a\s+href="/g, '<a target="_blank" rel="noopener" class="cli-md-link" href="');

    // 代码块加 CSS 类
    html = html.replace(/<pre><code/g, '<div class="cli-code-block"><pre><code');
    html = html.replace(/<\/code><\/pre>/g, '</code></pre></div>');

    // 行内代码加 CSS 类
    html = html.replace(/<code>/g, '<code class="cli-md-code">');

    // 但不给代码块里的 code 重复加类（修正上面的替换）
    html = html.replace(/cli-code-block"><pre><code class="cli-md-code">/g,
                         'cli-code-block"><pre><code>');

    // 业务实体高亮
    html = html.replace(/(¥[\d,]+\.?\d*(?:万)?)/g, '<span class="cli-hl-cny">$1</span>');
    html = html.replace(/(\$[\d,]+\.?\d*[MKk]?)/g, '<span class="cli-hl-usd">$1</span>');
    html = html.replace(/([\d.]+%)/g, '<span class="cli-hl-pct">$1</span>');

    return html;
  }

  _escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

window.CliMarkdownRenderer = CliMarkdownRenderer;
