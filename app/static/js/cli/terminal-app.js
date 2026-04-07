/**
 * PMA CLI Terminal App
 *
 * 阶段 2 完整终端：多标签、Markdown 渲染、斜杠命令、快捷键、会话恢复。
 * 设计文档: docs/plans/2026-04-05-pma-cli-agent-design.md
 */

class CliTerminalApp {
  constructor() {
    // DOM
    this.els = {
      tabbar:       document.getElementById('cli-tabbar'),
      tabAdd:       document.getElementById('cli-tab-add'),
      body:         document.getElementById('cli-body'),
      transcript:   document.getElementById('cli-transcript'),
      input:        document.getElementById('cli-input'),
      submit:       document.getElementById('cli-submit'),
      sessionId:    document.getElementById('cli-session-id'),
      tokenCount:   document.getElementById('cli-token-count'),
      tokenWrap:    document.getElementById('cli-token-wrap'),
      newBtn:       document.getElementById('cli-btn-new'),
      welcome:      document.querySelector('.cli-welcome'),
    };
    this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

    // 状态
    this.sessions   = new Map();  // sessionId → {title, usage, messageCount}
    this.tabs        = [];         // 有序 [{id, title}]
    this.activeId    = null;
    this.isStreaming  = false;
    this.messageCache = new Map(); // sessionId → 已渲染的 DOM 片段 HTML

    // Markdown 渲染器
    this.md = new CliMarkdownRenderer();

    // 流式累计
    this._streamingBlock = null;
    this._streamingText  = '';
    this._abortController = null;
  }

  // ═══════════════════════════════════════════════════════════════
  //  初始化
  // ═══════════════════════════════════════════════════════════════

  async init() {
    this._bindInput();
    this._bindShortcuts();
    this._autoResize();
    await this._loadSessions();
    this.els.input.focus();
  }

  async _loadSessions() {
    try {
      const r = await this._fetch('/cli/api/sessions');
      const data = await r.json();
      this.activeId = data.current_session_id;

      // 重建 tabs
      this.tabs = [];
      for (const s of (data.active || [])) {
        this.sessions.set(s.id, {
          title: s.title || '新会话',
          usage: s.usage_total || {},
          messageCount: s.message_count || 0,
        });
        this.tabs.push({ id: s.id, title: s.title || '新会话' });
      }
      this._renderTabs();

      // 加载当前 session 的消息
      if (this.activeId) {
        await this._restoreSession(this.activeId);
      }
    } catch (e) {
      console.error('[CLI] loadSessions failed', e);
    }
  }

  // ═══════════════════════════════════════════════════════════════
  //  标签管理
  // ═══════════════════════════════════════════════════════════════

  _renderTabs() {
    // 清空现有 tabs（保留 + 按钮）
    const addBtn = this.els.tabAdd;
    this.els.tabbar.innerHTML = '';

    for (const tab of this.tabs) {
      const el = document.createElement('div');
      el.className = 'cli-tab' + (tab.id === this.activeId ? ' cli-tab-active' : '');
      el.dataset.sessionId = tab.id;

      const titleSpan = document.createElement('span');
      titleSpan.className = 'cli-tab-title';
      titleSpan.textContent = this._truncate(tab.title, 8);
      titleSpan.title = tab.title;
      el.appendChild(titleSpan);

      const closeBtn = document.createElement('button');
      closeBtn.className = 'cli-tab-close';
      closeBtn.setAttribute('aria-label', 'close tab');
      closeBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px">close</span>';
      closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.closeTab(tab.id);
      });
      el.appendChild(closeBtn);

      el.addEventListener('click', () => this.switchTab(tab.id));
      this.els.tabbar.appendChild(el);
    }

    this.els.tabbar.appendChild(addBtn);

    // session ID 显示
    if (this.activeId) {
      this.els.sessionId.textContent = this.activeId.slice(0, 8);
    }

    // + 按钮事件（重新绑定，因为 innerHTML 会清掉旧的）
    addBtn.onclick = () => this.createTab();
  }

  async createTab() {
    if (this.tabs.length >= 8) {
      this._appendSystemLine('已达到最大标签数 (8)，请关闭不需要的标签。');
      return;
    }
    try {
      const r = await this._fetch('/cli/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken },
      });
      const data = await r.json();
      if (!data.success) return;

      const s = data.session;
      this.sessions.set(s.id, { title: '新会话', usage: {}, messageCount: 0 });
      this.tabs.push({ id: s.id, title: '新会话' });
      this.activeId = s.id;
      this._renderTabs();
      this._showTranscript(s.id);
      this._updateTokenDisplay({});
      this.els.input.focus();
    } catch (e) {
      this._appendErrorLine('创建标签失败: ' + e.message);
    }
  }

  async closeTab(sessionId) {
    if (this.tabs.length <= 1) {
      // 最后一个标签不关，改为 /new 行为
      await this._resetCurrentTab();
      return;
    }
    try {
      await this._fetch(`/cli/api/sessions/${sessionId}/close`, {
        method: 'POST',
        headers: { 'X-CSRFToken': this.csrfToken },
      });

      this.tabs = this.tabs.filter(t => t.id !== sessionId);
      this.sessions.delete(sessionId);
      this.messageCache.delete(sessionId);

      if (this.activeId === sessionId) {
        this.activeId = this.tabs[this.tabs.length - 1]?.id || null;
        if (this.activeId) {
          await this._focusSession(this.activeId);
          await this._restoreSession(this.activeId);
        }
      }
      this._renderTabs();
    } catch (e) {
      this._appendErrorLine('关闭标签失败: ' + e.message);
    }
  }

  async switchTab(sessionId) {
    if (sessionId === this.activeId) return;

    // 缓存当前 transcript
    if (this.activeId) {
      this.messageCache.set(this.activeId, this.els.transcript.innerHTML);
    }

    this.activeId = sessionId;
    this._renderTabs();

    // 尝试从缓存恢复
    if (this.messageCache.has(sessionId)) {
      this.els.transcript.innerHTML = this.messageCache.get(sessionId);
      const info = this.sessions.get(sessionId);
      this._updateTokenDisplay(info?.usage || {});
      this._toggleWelcome(this.els.transcript.children.length === 0);
      this._scrollToBottom();
    } else {
      await this._restoreSession(sessionId);
    }

    await this._focusSession(sessionId);
    this.els.input.focus();
  }

  async _focusSession(sessionId) {
    try {
      await this._fetch(`/cli/api/sessions/${sessionId}/focus`, {
        method: 'POST',
        headers: { 'X-CSRFToken': this.csrfToken },
      });
    } catch { /* 非关键 */ }
  }

  async _restoreSession(sessionId) {
    try {
      const r = await this._fetch(`/cli/api/sessions/${sessionId}/messages`);
      const data = await r.json();
      if (!data.success) return;

      const info = this.sessions.get(sessionId);
      if (info && data.session) {
        info.usage = data.session.usage_total || {};
        info.title = data.session.title || info.title;
      }

      this._updateTokenDisplay(data.session?.usage_total || {});
      this._renderHistory(data.messages || []);
    } catch (e) {
      console.error('[CLI] restoreSession failed', e);
    }
  }

  // ═══════════════════════════════════════════════════════════════
  //  消息渲染
  // ═══════════════════════════════════════════════════════════════

  _renderHistory(messages) {
    this.els.transcript.innerHTML = '';
    if (messages.length > 0) this._toggleWelcome(false);

    for (const msg of messages) {
      const content = msg.content || [];
      if (msg.role === 'user') {
        for (const b of content) {
          if (b.type === 'text') this._appendUserLine(b.text);
        }
      } else if (msg.role === 'assistant') {
        for (const b of content) {
          if (b.type === 'text') this._appendAssistantBlock(b.text);
          // tool_use 在历史中不显示，只看 AI 的文字回复
        }
      }
    }
    this._scrollToBottom();
  }

  _appendUserLine(text) {
    this._toggleWelcome(false);
    const div = document.createElement('div');
    div.className = 'cli-line cli-line-user';
    div.innerHTML = '<span class="cli-user-prompt">&gt;</span> <span class="cli-user-text"></span>';
    div.querySelector('.cli-user-text').textContent = text;
    this.els.transcript.appendChild(div);
    this._scrollToBottom();
  }

  _appendAssistantBlock(text) {
    const div = document.createElement('div');
    div.className = 'cli-line cli-line-assistant';
    div.innerHTML = this.md.render(text);
    this.els.transcript.appendChild(div);
    this._scrollToBottom();
  }

  // 流式：开始新的 assistant 块
  _startStreamingBlock() {
    this._streamingText = '';
    this._streamingBlock = document.createElement('div');
    this._streamingBlock.className = 'cli-line cli-line-assistant';
    this.els.transcript.appendChild(this._streamingBlock);
  }

  // 流式：追加文本增量
  _appendStreamingDelta(text) {
    if (!this._streamingBlock) this._startStreamingBlock();
    this._streamingText += text;
    this._streamingBlock.innerHTML = this.md.renderStreaming(this._streamingText);
    this._scrollToBottom();
  }

  // 流式：结束当前块，做最终渲染
  _finishStreamingBlock() {
    if (this._streamingBlock && this._streamingText) {
      this._streamingBlock.innerHTML = this.md.render(this._streamingText);
    }
    this._streamingBlock = null;
    this._streamingText = '';
  }

  _appendToolStatus(text, spinning) {
    const div = document.createElement('div');
    div.className = 'cli-line cli-line-tool';
    const prefix = spinning
      ? '<span class="cli-tool-spinner"></span>'
      : '⚙ ';
    div.innerHTML = prefix + this._escapeHtml(text);
    this.els.transcript.appendChild(div);
    this._scrollToBottom();
    return div;
  }

  _appendErrorLine(text) {
    const div = document.createElement('div');
    div.className = 'cli-line cli-line-error';
    div.textContent = '✗ ' + text;
    this.els.transcript.appendChild(div);
    this._scrollToBottom();
  }

  _appendSystemLine(html) {
    const div = document.createElement('div');
    div.className = 'cli-line cli-line-system';
    div.innerHTML = html;
    this.els.transcript.appendChild(div);
    this._scrollToBottom();
  }

  _appendDownloadButton(filename, url) {
    const div = document.createElement('div');
    div.className = 'cli-line cli-download';
    div.innerHTML = `<a href="${this._escapeHtml(url)}" target="_blank" class="cli-download-btn">` +
      `<span class="material-symbols-outlined" style="font-size:16px;vertical-align:middle;margin-right:4px">download</span>` +
      `${this._escapeHtml(filename)}</a>`;
    this.els.transcript.appendChild(div);
    this._scrollToBottom();
  }

  _appendUsageLine() {
    const info = this.sessions.get(this.activeId);
    if (!info) return;
    const u = info.usage || {};
    const input = u.input_tokens || 0;
    const output = u.output_tokens || 0;
    const total = input + output;
    if (total <= 0) return;
    const div = document.createElement('div');
    div.className = 'cli-line cli-line-usage';
    const est = u._estimated ? ' (estimated)' : '';
    div.textContent = `tokens: ${total.toLocaleString()}${est}`;
    this.els.transcript.appendChild(div);
    this._scrollToBottom();
  }

  _showLoadingDots() {
    const div = document.createElement('div');
    div.className = 'cli-loading-dots';
    div.id = 'cli-loading-indicator';
    div.innerHTML = '<span></span><span></span><span></span>';
    this.els.transcript.appendChild(div);
    this._scrollToBottom();
    return div;
  }

  _removeLoadingDots() {
    document.getElementById('cli-loading-indicator')?.remove();
  }

  // ═══════════════════════════════════════════════════════════════
  //  发送 + SSE 流式接收
  // ═══════════════════════════════════════════════════════════════

  async sendMessage(text) {
    if (this.isStreaming) return;
    if (!text?.trim()) return;
    if (!this.activeId) {
      this._appendErrorLine('尚未加载会话，请刷新页面');
      return;
    }

    // 检查斜杠命令
    const cmd = this._parseSlashCommand(text);
    if (cmd) {
      this._clearInput();
      this._executeCommand(cmd.command, cmd.args);
      return;
    }

    this._appendUserLine(text);
    this._clearInput();
    this.isStreaming = true;
    this._abortController = new AbortController();
    this._setInputDisabled(true);
    this._finishStreamingBlock();

    // 首条消息自动设置标题
    const info = this.sessions.get(this.activeId);
    if (info && info.messageCount === 0) {
      const title = text.slice(0, 8) + (text.length > 8 ? '…' : '');
      this._updateTabTitle(this.activeId, title);
      this._patchSessionTitle(this.activeId, title);
      info.title = title;
    }
    if (info) info.messageCount++;

    const loadingDots = this._showLoadingDots();
    let toolStatusEl = null;

    try {
      const resp = await fetch('/cli/api/stream', {
        method: 'POST',
        signal: this._abortController.signal,
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.csrfToken,
        },
        body: JSON.stringify({ session_id: this.activeId, input: text }),
      });

      if (!resp.ok) {
        this._appendErrorLine('HTTP ' + resp.status + ' ' + resp.statusText);
        return;
      }

      // loading dots 在收到第一个 text_delta 时移除，不在这里移除

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (!line.startsWith('data:')) continue;
          const payload = line.slice(5).trim();
          if (!payload) continue;
          let evt;
          try { evt = JSON.parse(payload); } catch { continue; }
          toolStatusEl = this._handleStreamEvent(evt, toolStatusEl);
        }
      }
    } catch (e) {
      if (e.name === 'AbortError') {
        this._appendSystemLine('已中断');
      } else {
        this._appendErrorLine('网络错误: ' + e.message);
      }
    } finally {
      this.isStreaming = false;
      this._abortController = null;
      this._setInputDisabled(false);
      this._finishStreamingBlock();
      this._removeLoadingDots();
      this.els.input.focus();
    }
  }

  _handleStreamEvent(evt, toolStatusEl) {
    switch (evt.type) {
      case 'status':
        // 轮次状态，不显示给用户（loading dots 已覆盖）
        break;

      case 'text_delta':
        this._removeLoadingDots();
        this._appendStreamingDelta(evt.text);
        break;

      case 'tool_call':
        this._finishStreamingBlock();
        if (toolStatusEl) toolStatusEl.remove();
        // 根据工具类型显示不同状态
        const toolName = evt.name || '';
        let statusMsg = '查询中...';
        if (toolName === 'invoke_skill') {
          const skillName = evt.input?.skill_name || '';
          statusMsg = `调用技能: ${skillName}`;
        } else if (toolName === 'save_skill') {
          statusMsg = `创建技能: ${evt.input?.title || evt.input?.name || ''}`;
        } else if (toolName === 'web_search') {
          statusMsg = `搜索: ${evt.input?.query || ''}`;
        } else if (toolName === 'export_to_word') {
          statusMsg = '生成文档...';
        }
        toolStatusEl = this._appendToolStatus(statusMsg, true);
        break;

      case 'tool_result': {
        const out = evt.output || {};
        if (evt.is_error || out.error) {
          if (toolStatusEl) toolStatusEl.remove();
          toolStatusEl = null;
          this._appendToolStatus('错误: ' + (out.error || JSON.stringify(out)), false);
        } else {
          if (toolStatusEl) {
            const spinnerEl = toolStatusEl.querySelector('.cli-tool-spinner');
            if (spinnerEl) spinnerEl.remove();
            toolStatusEl = null;
          }
          // Word 导出：直接渲染下载按钮
          if (out.download_url && out.filename) {
            this._appendDownloadButton(out.filename, out.download_url);
          }
        }
        break;
      }

      case 'usage': {
        const u = evt.usage || {};
        const info = this.sessions.get(this.activeId);
        if (info) {
          info.usage.input_tokens  = (info.usage.input_tokens || 0) + (u.input_tokens || 0);
          info.usage.output_tokens = (info.usage.output_tokens || 0) + (u.output_tokens || 0);
          if (u._estimated) info.usage._estimated = true;
          this._updateTokenDisplay(info.usage);
        }
        break;
      }

      case 'done':
        this._finishStreamingBlock();
        this._appendUsageLine();
        break;

      case 'error':
        this._finishStreamingBlock();
        this._appendErrorLine(evt.message || '未知错误');
        break;
    }
    return toolStatusEl;
  }

  // ═══════════════════════════════════════════════════════════════
  //  斜杠命令
  // ═══════════════════════════════════════════════════════════════

  _parseSlashCommand(text) {
    const match = text.trim().match(/^\/(\w+)\s*(.*)/);
    if (!match) return null;
    return { command: match[1].toLowerCase(), args: match[2].trim() };
  }

  async _executeCommand(command, args) {
    this._appendUserLine('/' + command + (args ? ' ' + args : ''));

    switch (command) {
      case 'new':
        await this._resetCurrentTab();
        break;

      case 'clear':
        this.els.transcript.innerHTML = '';
        break;

      case 'tokens':
      case 'token':
        this._showTokens();
        break;

      case 'history':
        await this._showHistory();
        break;

      case 'skills':
      case 'skill':
        await this._showSkills();
        break;

      case 'memory':
      case 'memories':
        await this._showMemories(args);
        break;

      case 'help':
        this._showHelp();
        break;

      default:
        this._appendSystemLine(`未知命令: <span class="cli-sys-cmd">/${this._escapeHtml(command)}</span>，输入 <span class="cli-sys-cmd">/help</span> 查看可用命令`);
    }
  }

  async _resetCurrentTab() {
    try {
      const r = await this._fetch('/cli/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken },
      });
      const data = await r.json();
      if (!data.success) return;

      const oldId = this.activeId;
      const newSession = data.session;

      // 关掉旧的
      if (oldId) {
        await this._fetch(`/cli/api/sessions/${oldId}/close`, {
          method: 'POST',
          headers: { 'X-CSRFToken': this.csrfToken },
        }).catch(() => {});
        this.sessions.delete(oldId);
        this.messageCache.delete(oldId);
      }

      // 替换当前 tab
      this.sessions.set(newSession.id, { title: '新会话', usage: {}, messageCount: 0 });
      const tabIdx = this.tabs.findIndex(t => t.id === oldId);
      if (tabIdx >= 0) {
        this.tabs[tabIdx] = { id: newSession.id, title: '新会话' };
      } else {
        this.tabs.push({ id: newSession.id, title: '新会话' });
      }
      this.activeId = newSession.id;

      this._renderTabs();
      this.els.transcript.innerHTML = '';
      this._toggleWelcome(true);
      this._updateTokenDisplay({});
      this._appendSystemLine('会话已重置');
    } catch (e) {
      this._appendErrorLine('重置失败: ' + e.message);
    }
  }

  _showTokens() {
    const info = this.sessions.get(this.activeId);
    const u = info?.usage || {};
    const input  = (u.input_tokens || 0).toLocaleString();
    const output = (u.output_tokens || 0).toLocaleString();
    const cache_create = (u.cache_creation_input_tokens || 0).toLocaleString();
    const cache_read   = (u.cache_read_input_tokens || 0).toLocaleString();
    const total = ((u.input_tokens || 0) + (u.output_tokens || 0)).toLocaleString();
    this._appendSystemLine(
      `<span class="cli-sys-heading">Token 用量</span>\n` +
      `  输入:   ${input}\n` +
      `  输出:   ${output}\n` +
      `  缓存写: ${cache_create}\n` +
      `  缓存读: ${cache_read}\n` +
      `  ──────────\n` +
      `  合计:   ${total}`
    );
  }

  async _showHistory() {
    try {
      const r = await this._fetch('/cli/api/sessions/history');
      const data = await r.json();
      if (!data.success || !data.sessions?.length) {
        this._appendSystemLine('暂无历史会话');
        return;
      }
      let lines = '<span class="cli-sys-heading">会话历史</span>\n';
      for (const s of data.sessions) {
        const status = s.status === 'ACTIVE' ? '●' : s.status === 'CLOSED' ? '○' : '◌';
        const date = s.created_at ? new Date(s.created_at).toLocaleString('zh-CN') : '—';
        const title = s.title || '(无标题)';
        lines += `  ${status} ${s.id.slice(0, 8)}  ${title.padEnd(22)}  ${s.message_count}条  ${date}\n`;
      }
      this._appendSystemLine(lines);
    } catch (e) {
      this._appendErrorLine('获取历史失败: ' + e.message);
    }
  }

  async _showMemories(args) {
    // /memory system add ... 交给后端处理
    if (args && args.startsWith('system ') || args && args.startsWith('role ')) {
      // 系统/角色记忆通过 API 创建
      this.sendMessage('/memory ' + args);
      return;
    }
    try {
      const r = await this._fetch('/cli/api/memories');
      const data = await r.json();
      if (!data.success || !data.memories?.length) {
        this._appendSystemLine('暂无记忆');
        return;
      }
      let lines = '<span class="cli-sys-heading">记忆索引</span>\n\n';
      const system = data.memories.filter(m => m.scope === 'system');
      const role = data.memories.filter(m => m.scope.startsWith('role:'));
      const personal = data.memories.filter(m => m.scope === 'personal');

      if (system.length) {
        lines += '<span class="cli-sys-heading">系统记忆</span>\n';
        for (const m of system) {
          lines += `  <span class="cli-sys-cmd">#${m.id}</span> [${m.type}] ${m.title} — ${m.summary}\n`;
        }
      }
      if (role.length) {
        lines += '\n<span class="cli-sys-heading">角色记忆</span>\n';
        for (const m of role) {
          lines += `  <span class="cli-sys-cmd">#${m.id}</span> [${m.type}] ${m.title} — ${m.summary}\n`;
        }
      }
      if (personal.length) {
        lines += '\n<span class="cli-sys-heading">我的记忆</span>\n';
        for (const m of personal) {
          lines += `  <span class="cli-sys-cmd">#${m.id}</span> [${m.type}] ${m.title} — ${m.summary}\n`;
        }
      }
      this._appendSystemLine(lines);
    } catch (e) {
      this._appendErrorLine('获取记忆失败: ' + e.message);
    }
  }

  async _showSkills() {
    try {
      const r = await this._fetch('/cli/api/skills');
      const data = await r.json();
      if (!data.success || !data.skills?.length) {
        this._appendSystemLine('暂无可用技能');
        return;
      }
      let lines = '<span class="cli-sys-heading">可用技能</span>\n\n';
      const globalSkills = data.skills.filter(s => s.scope === 'global');
      const personalSkills = data.skills.filter(s => s.scope !== 'global');

      if (globalSkills.length) {
        lines += '<span class="cli-sys-heading">全局技能</span>\n';
        for (const s of globalSkills) {
          const params = (s.parameters || []).map(p => p.name).join(', ');
          lines += `  <span class="cli-sys-cmd">${s.name}</span>  ${s.title}${params ? '（' + params + '）' : ''}\n`;
        }
      }
      if (personalSkills.length) {
        lines += '\n<span class="cli-sys-heading">我的技能</span>\n';
        for (const s of personalSkills) {
          const params = (s.parameters || []).map(p => p.name).join(', ');
          lines += `  <span class="cli-sys-cmd">${s.name}</span>  ${s.title}${params ? '（' + params + '）' : ''}\n`;
        }
      }
      this._appendSystemLine(lines);
    } catch (e) {
      this._appendErrorLine('获取技能列表失败: ' + e.message);
    }
  }

  _showHelp() {
    this._appendSystemLine(
      `<span class="cli-sys-heading">可用命令</span>\n` +
      `  <span class="cli-sys-cmd">/new</span>      重置当前会话\n` +
      `  <span class="cli-sys-cmd">/clear</span>    清屏\n` +
      `  <span class="cli-sys-cmd">/tokens</span>   显示 token 用量\n` +
      `  <span class="cli-sys-cmd">/skills</span>   查看可用技能\n` +
      `  <span class="cli-sys-cmd">/history</span>  查看所有会话\n` +
      `  <span class="cli-sys-cmd">/help</span>     显示本帮助\n\n` +
      `<span class="cli-sys-heading">快捷键</span>\n` +
      `  <span class="cli-sys-key">Ctrl+T</span>        新标签\n` +
      `  <span class="cli-sys-key">Ctrl+W</span>        关闭标签\n` +
      `  <span class="cli-sys-key">Ctrl+1~8</span>      切换标签\n` +
      `  <span class="cli-sys-key">Ctrl+Tab</span>      下一个标签\n` +
      `  <span class="cli-sys-key">Ctrl+Shift+Tab</span> 上一个标签\n` +
      `  <span class="cli-sys-key">Ctrl+N</span>        重置会话\n` +
      `  <span class="cli-sys-key">Ctrl+L</span>        清屏\n` +
      `  <span class="cli-sys-key">Enter</span>         发送\n` +
      `  <span class="cli-sys-key">Shift+Enter</span>   换行`
    );
  }

  // ═══════════════════════════════════════════════════════════════
  //  快捷键
  // ═══════════════════════════════════════════════════════════════

  _bindShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Esc 中断流式响应
      if (e.key === 'Escape' && this.isStreaming) {
        e.preventDefault();
        this.stopStreaming();
        return;
      }

      // Ctrl/Cmd 修饰键
      const mod = e.ctrlKey || e.metaKey;
      if (!mod) return;

      // Ctrl+T → 新标签
      if (e.key === 't' && !e.shiftKey) {
        e.preventDefault();
        this.createTab();
        return;
      }

      // Ctrl+W → 关闭当前标签
      if (e.key === 'w' && !e.shiftKey) {
        e.preventDefault();
        if (this.activeId) this.closeTab(this.activeId);
        return;
      }

      // Ctrl+N → 重置当前 session
      if (e.key === 'n' && !e.shiftKey) {
        e.preventDefault();
        this._resetCurrentTab();
        return;
      }

      // Ctrl+L → 清屏
      if (e.key === 'l' && !e.shiftKey) {
        e.preventDefault();
        this.els.transcript.innerHTML = '';
        return;
      }

      // Ctrl+1~8 → 切换标签
      const num = parseInt(e.key);
      if (num >= 1 && num <= 8 && !e.shiftKey) {
        e.preventDefault();
        const tab = this.tabs[num - 1];
        if (tab) this.switchTab(tab.id);
        return;
      }

      // Ctrl+Tab → 下一个标签
      if (e.key === 'Tab' && !e.shiftKey) {
        e.preventDefault();
        this._switchTabRelative(1);
        return;
      }

      // Ctrl+Shift+Tab → 上一个标签
      if (e.key === 'Tab' && e.shiftKey) {
        e.preventDefault();
        this._switchTabRelative(-1);
        return;
      }
    });
  }

  _switchTabRelative(delta) {
    if (this.tabs.length <= 1) return;
    const idx = this.tabs.findIndex(t => t.id === this.activeId);
    const next = (idx + delta + this.tabs.length) % this.tabs.length;
    this.switchTab(this.tabs[next].id);
  }

  // ═══════════════════════════════════════════════════════════════
  //  输入处理
  // ═══════════════════════════════════════════════════════════════

  // ─── 命令建议 ───

  _COMMANDS = [
    { name: '/new',     desc: '重置当前会话' },
    { name: '/clear',   desc: '清屏' },
    { name: '/tokens',  desc: '显示 token 用量' },
    { name: '/skills',  desc: '查看可用技能' },
    { name: '/memory',  desc: '查看记忆(管理员)' },
    { name: '/history', desc: '查看所有会话' },
    { name: '/help',    desc: '显示帮助' },
  ];

  _bindInput() {
    this._suggestEl = document.getElementById('cli-cmd-suggest');
    this._suggestIdx = -1;

    this.els.input.addEventListener('keydown', (e) => {
      // 建议浮层打开时拦截方向键和 Enter
      if (this._suggestEl.style.display !== 'none') {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          this._moveSuggest(1);
          return;
        }
        if (e.key === 'ArrowUp') {
          e.preventDefault();
          this._moveSuggest(-1);
          return;
        }
        if (e.key === 'Enter') {
          e.preventDefault();
          this._selectSuggest();
          return;
        }
        if (e.key === 'Escape') {
          this._hideSuggest();
          return;
        }
      }

      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage(this.els.input.value.trim());
      }
    });

    this.els.input.addEventListener('input', () => {
      this._updateSuggest();
    });

    this.els.submit?.addEventListener('click', () => {
      this.sendMessage(this.els.input.value.trim());
    });
    this.els.newBtn?.addEventListener('click', () => this._resetCurrentTab());
  }

  _updateSuggest() {
    const text = this.els.input.value;
    // 只在输入以 / 开头时显示建议
    if (!text.startsWith('/') || text.includes(' ')) {
      this._hideSuggest();
      return;
    }
    const query = text.toLowerCase();
    const matches = this._COMMANDS.filter(c => c.name.startsWith(query));
    if (matches.length === 0 || (matches.length === 1 && matches[0].name === query)) {
      this._hideSuggest();
      return;
    }
    this._suggestIdx = 0;
    const listEl = document.getElementById('cli-cmd-list');
    listEl.innerHTML = matches.map((c, i) =>
      `<div class="cli-cmd-item${i === 0 ? ' active' : ''}" data-cmd="${c.name}">` +
      `<span class="cli-cmd-name">${c.name}</span>` +
      `<span class="cli-cmd-desc">${c.desc}</span></div>`
    ).join('');
    this._suggestEl.style.display = '';

    // 点击选择
    listEl.querySelectorAll('.cli-cmd-item').forEach(el => {
      el.addEventListener('mousedown', (e) => {
        e.preventDefault();
        this.els.input.value = el.dataset.cmd;
        this._hideSuggest();
        this.els.input.focus();
      });
    });
  }

  _moveSuggest(delta) {
    const items = this._suggestEl.querySelectorAll('.cli-cmd-item');
    if (!items.length) return;
    items[this._suggestIdx]?.classList.remove('active');
    this._suggestIdx = (this._suggestIdx + delta + items.length) % items.length;
    items[this._suggestIdx]?.classList.add('active');
  }

  _selectSuggest() {
    const items = this._suggestEl.querySelectorAll('.cli-cmd-item');
    const active = items[this._suggestIdx];
    if (active) {
      this.els.input.value = active.dataset.cmd;
    }
    this._hideSuggest();
    // 直接执行命令
    this.sendMessage(this.els.input.value.trim());
  }

  _hideSuggest() {
    this._suggestEl.style.display = 'none';
    this._suggestIdx = -1;
  }

  _autoResize() {
    this.els.input.addEventListener('input', () => {
      this.els.input.style.height = 'auto';
      this.els.input.style.height = Math.min(this.els.input.scrollHeight, 160) + 'px';
    });
  }

  _clearInput() {
    this.els.input.value = '';
    this.els.input.style.height = 'auto';
  }

  _setInputDisabled(disabled) {
    this.els.input.disabled = disabled;
    if (this.els.submit) this.els.submit.disabled = disabled;
    this.els.input.placeholder = disabled
      ? '正在思考... (按 Esc 中断)'
      : '输入问题，按 Enter 发送...';
  }

  stopStreaming() {
    if (this._abortController) {
      this._abortController.abort();
    }
  }

  // ═══════════════════════════════════════════════════════════════
  //  UI 辅助
  // ═══════════════════════════════════════════════════════════════

  _updateTokenDisplay(usage) {
    const total = (usage.input_tokens || 0) + (usage.output_tokens || 0);
    this.els.tokenCount.textContent = total.toLocaleString();

    // 阈值颜色
    const wrap = this.els.tokenWrap || this.els.tokenCount.parentElement;
    wrap.classList.remove('cli-tokens-warn', 'cli-tokens-danger');
    if (total >= 160000) {
      wrap.classList.add('cli-tokens-danger');
    } else if (total >= 120000) {
      wrap.classList.add('cli-tokens-warn');
    }
  }

  _updateTabTitle(sessionId, title) {
    const tab = this.tabs.find(t => t.id === sessionId);
    if (tab) {
      tab.title = title;
      this._renderTabs();
    }
  }

  async _patchSessionTitle(sessionId, title) {
    try {
      await this._fetch(`/cli/api/sessions/${sessionId}/title`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken },
        body: JSON.stringify({ title }),
      });
    } catch { /* 非关键 */ }
  }

  _toggleWelcome(show) {
    if (this.els.welcome) {
      this.els.welcome.style.display = show ? '' : 'none';
    }
  }

  _scrollToBottom() {
    this.els.body.scrollTop = this.els.body.scrollHeight;
  }

  _showTranscript(sessionId) {
    this.els.transcript.innerHTML = '';
    if (this.messageCache.has(sessionId)) {
      this.els.transcript.innerHTML = this.messageCache.get(sessionId);
      this._toggleWelcome(false);
    } else {
      this._toggleWelcome(true);
    }
  }

  // ═══════════════════════════════════════════════════════════════
  //  工具方法
  // ═══════════════════════════════════════════════════════════════

  _truncate(str, maxLen) {
    if (!str) return '';
    return str.length > maxLen ? str.slice(0, maxLen) + '…' : str;
  }

  _escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  async _fetch(url, opts) {
    const r = await fetch(url, opts);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r;
  }
}

// 页面加载后初始化
document.addEventListener('DOMContentLoaded', () => {
  window.cliApp = new CliTerminalApp();
  window.cliApp.init();
});
