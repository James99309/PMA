/**
 * ai-form-enrich.js
 * 通用表单查重 + AI 回填模块
 * 支持客户表单和项目表单，通过配置区分
 *
 * 用法：
 *   AiFormEnrich.init({ nameInputId, similarListId, aiBtnId, aiPanelId,
 *                        aiContentId, aiCloseId, similarApi, enrichApi,
 *                        enrichBodyKey, fieldMap })
 *
 * fieldMap 格式：
 *   [{ key, label, targetId, labelKey?, onlyIfEmpty? }, ...]
 *   - key:         AI 返回 JSON 中的字段名（如 'industry'）
 *   - label:       在面板中显示的中文标签（如 '行业'）
 *   - targetId:    表单中目标 DOM 元素 id（如 'industry'）
 *   - labelKey:    （可选）AI 返回中对应的中文 label 字段名（如 'industry_label'）
 *                  有 labelKey 时面板显示 data[labelKey]，否则显示 data[key]
 *   - onlyIfEmpty: （可选）true = 只在目标字段为空时才填入（适合 textarea）
 */
(function (global) {
    'use strict';

    function escHtml(s) {
        var d = document.createElement('div');
        d.textContent = String(s || '');
        return d.innerHTML;
    }

    function safeUrl(url) {
        return /^https?:\/\//i.test(url) ? url : '#';
    }

    function init(cfg) {
        var nameInput   = document.getElementById(cfg.nameInputId);
        var similarList = document.getElementById(cfg.similarListId);
        var aiBtn       = document.getElementById(cfg.aiBtnId);
        var aiPanel     = document.getElementById(cfg.aiPanelId);
        var aiContent   = document.getElementById(cfg.aiContentId);
        var aiClose     = document.getElementById(cfg.aiCloseId);
        var debounceTimer = null;

        var t = Object.assign({
            btnLoading:      '查询中',
            nameHintMulti:   '以下为同一工程的不同正式叫法，选一个填入',
            nameHintSingle:  '点选后自动填入',
            fieldHint:       '以下行业、地址、描述信息适用于所有候选名称',
            applyBtn:        '应用到表单',
            emptyName:       '请先输入名称',
            queryFailed:     'AI 查询失败，请稍后重试',
            networkError:    '网络错误，请稍后重试',
            similarHigh:     '高度相似',
            similarMed:      '相似',
            similarView:     '查看',
            similarOwner:    '归属：',
            similarExists:   '已存在，请勿重复创建',
        }, cfg.i18n || {});

        var AI_BTN_DEFAULT = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/></svg> AI';
        var AI_BTN_LOADING = '<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/></svg> ' + t.btnLoading;

        // ---- 内部查重 ----
        function renderSimilarList(results) {
            if (!results.length) {
                similarList && similarList.classList.add('hidden');
                return;
            }
            similarList.innerHTML = results.map(function (r) {
                var badge = r.score >= 0.9
                    ? '<span class="text-xs text-red-500 font-medium ml-1">' + t.similarHigh + '</span>'
                    : r.score >= 0.7
                        ? '<span class="text-xs text-yellow-500 font-medium ml-1">' + t.similarMed + '</span>'
                        : '';
                if (r.viewable) {
                    return '<a href="' + safeUrl(r.url) + '" target="_blank"' +
                        ' class="flex items-center justify-between px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer border-b border-slate-100 dark:border-slate-700 last:border-0">' +
                        '<span class="text-slate-800 dark:text-slate-200">' + escHtml(r.name) + badge + '</span>' +
                        '<span class="text-xs text-slate-400">' + t.similarView + '</span>' +
                        '</a>';
                } else {
                    var ownerHint = r.owner_name
                        ? '<span class="text-xs text-slate-400">' + t.similarOwner + escHtml(r.owner_name) + '，' + t.similarExists + '</span>'
                        : '<span class="text-xs text-slate-400">' + t.similarExists + '</span>';
                    return '<div class="flex items-center justify-between px-3 py-2 border-b border-slate-100 dark:border-slate-700 last:border-0">' +
                        '<span class="text-slate-500 dark:text-slate-400">' + escHtml(r.name) + badge + '</span>' +
                        ownerHint +
                        '</div>';
                }
            }).join('');
            similarList.classList.remove('hidden');
        }

        nameInput && nameInput.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            var q = this.value.trim();
            if (q.length < 2) {
                similarList && similarList.classList.add('hidden');
                return;
            }
            debounceTimer = setTimeout(function () {
                fetch(cfg.similarApi + '?q=' + encodeURIComponent(q))
                    .then(function (r) { return r.json(); })
                    .then(function (data) { renderSimilarList(data.results || []); })
                    .catch(function () {});
            }, 500);
        });

        document.addEventListener('click', function (e) {
            if (similarList && !similarList.contains(e.target) && e.target !== nameInput) {
                similarList.classList.add('hidden');
            }
        });

        // ---- AI 回填 ----
        function renderAiPanel(data) {
            var names = data.official_names || [];
            var nameOptions = names.map(function (n, i) {
                return '<label class="flex items-center gap-2 cursor-pointer">' +
                    '<input type="radio" name="ai_name_pick" value="' + escHtml(n) + '" class="text-primary"' + (i === 0 ? ' checked' : '') + '>' +
                    '<span class="text-sm text-slate-800 dark:text-slate-200">' + escHtml(n) + '</span>' +
                    '</label>';
            }).join('');

            var html = '';
            if (nameOptions) {
                var hint = names.length > 1 ? t.nameHintMulti : t.nameHintSingle;
                html += '<div class="space-y-1"><p class="text-xs text-slate-500 mb-1">' + hint + '</p>' + nameOptions + '</div>';
                if (names.length > 1) {
                    html += '<p class="text-xs text-slate-400">' + t.fieldHint + '</p>';
                }
            }
            // 同步预选第一个名称到输入框
            if (names.length > 0) nameInput.value = names[0];

            (cfg.fieldMap || []).forEach(function (f) {
                var displayVal = f.labelKey ? (data[f.labelKey] || data[f.key]) : data[f.key];
                if (displayVal) {
                    html += '<div class="text-sm"><span class="text-slate-500 text-xs">' + escHtml(f.label) + '</span>' +
                        '<p class="text-slate-800 dark:text-slate-200 mt-0.5">' + escHtml(displayVal) + '</p></div>';
                }
            });

            html += '<div class="flex gap-2 pt-1"><button type="button" id="_aiApplyBtn_' + cfg.nameInputId + '" class="flex-1 py-1.5 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-colors">' + t.applyBtn + '</button></div>';

            aiContent.innerHTML = html;

            aiContent.querySelectorAll('input[name="ai_name_pick"]').forEach(function (radio) {
                radio.addEventListener('change', function () {
                    nameInput.value = this.value;
                });
            });

            var applyBtn = document.getElementById('_aiApplyBtn_' + cfg.nameInputId);
            applyBtn && applyBtn.addEventListener('click', function () {
                var picked = aiContent.querySelector('input[name="ai_name_pick"]:checked');
                if (picked) nameInput.value = picked.value;

                (cfg.fieldMap || []).forEach(function (f) {
                    var val = data[f.key];
                    if (!val) return;
                    var el = document.getElementById(f.targetId);
                    if (!el) return;
                    if (f.onlyIfEmpty && el.value) return;
                    el.value = val;
                });

                aiPanel.classList.add('hidden');
            });

            aiPanel.classList.remove('hidden');
        }

        aiBtn && aiBtn.addEventListener('click', function () {
            var q = nameInput ? nameInput.value.trim() : '';
            if (!q) { alert(t.emptyName); return; }

            aiBtn.disabled = true;
            aiBtn.innerHTML = AI_BTN_LOADING;

            var body = {};
            body[cfg.enrichBodyKey || cfg.nameInputId] = q;

            var csrfMeta = document.querySelector('meta[name="csrf-token"]');
            var headers = { 'Content-Type': 'application/json' };
            if (csrfMeta) headers['X-CSRFToken'] = csrfMeta.getAttribute('content');

            fetch(cfg.enrichApi, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(body),
            })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.success) {
                        renderAiPanel(data);
                    } else {
                        alert(data.message || t.queryFailed);
                    }
                })
                .catch(function () { alert(t.networkError); })
                .finally(function () {
                    aiBtn.disabled = false;
                    aiBtn.innerHTML = AI_BTN_DEFAULT;
                });
        });

        aiClose && aiClose.addEventListener('click', function () {
            aiPanel.classList.add('hidden');
        });
    }

    global.AiFormEnrich = { init: init };

}(window));
