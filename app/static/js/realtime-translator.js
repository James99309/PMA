/**
 * 实时翻译轨道 - Realtime Translator
 *
 * 独立于会议录音的"翻译轨道"：
 * - 每 ~3s 切片上传到 /meeting/api/recordings/{id}/realtime-translate
 * - 后端 Whisper 转写 + GPT 翻译，返回 JSON
 * - 通过回调把消息推到浮窗的翻译流
 *
 * 设计理由：
 * - 跟录音的 30s chunk 完全独立（双轨道架构）
 * - 录音继续上传到 NAS 存档，翻译只走内存+API，不存盘
 * - 单人模式（场景 B）：只翻译给当前用户看，不推送给别人
 *
 * 用法：
 * const translator = new RealtimeTranslator({
 *     recordingId: 15,
 *     stream: micStream,            // 必填，已经 getUserMedia 的 MediaStream
 *     speaker: 'me',                // 'me' (麦克风) | 'peer' (系统音频)
 *     sourceLang: 'zh-CN',
 *     targetLang: 'en',
 *     chunkMs: 3000,                // chunk 大小 (毫秒)，3s 平衡延迟和准确度
 *     onMessage: (msg) => {...},    // 收到翻译消息
 *     onError: (err) => {...}
 * });
 *
 * await translator.start();
 * translator.pause();
 * translator.resume();
 * translator.stop();
 */

class RealtimeTranslator {
    constructor(options = {}) {
        this.recordingId = options.recordingId;
        this.stream = options.stream;
        this.speaker = options.speaker || 'me';
        this.nativeLang = options.nativeLang || 'zh-CN';
        this.chunkMs = options.chunkMs || 5000;
        this.uploadUrl = options.uploadUrl
            || `/meeting/api/recordings/${this.recordingId}/realtime-translate`;

        this.onMessage = options.onMessage || (() => {});
        this.onError = options.onError || console.error;
        this.onLevel = options.onLevel || (() => {});  // 实时音量回调（0-1 RMS），每 50ms 触发一次
        this.onStatus = options.onStatus || (() => {});

        // 内部状态
        this.state = 'idle';        // idle / running / paused / stopped
        this._mediaRecorder = null;
        this._buffer = [];          // 累积当前 chunk 的 Blob 片段
        this._cycleTimer = null;
        this._inflight = 0;         // 正在上传中的请求数
    }

    async start() {
        if (this.state === 'running') return;
        if (!this.stream) {
            throw new Error('RealtimeTranslator: missing stream');
        }
        if (!this.recordingId) {
            throw new Error('RealtimeTranslator: missing recordingId');
        }

        this._mimeType = this._getSupportedMimeType();
        this.state = 'running';
        this.onStatus('running');

        // 录音真正开始时间（用于算每个 chunk 在 audio 里的偏移秒数）
        this._recordingStartedAt = Date.now();
        // 暂停累计：暂停期间不算 audio 时间
        this._pausedAccumulatedMs = 0;
        this._pausedAt = null;

        // VAD-based 智能切片参数：
        // - rmsThreshold: 单次 RMS 视为"有声音"的阈值（0.020 = 略大于环境噪音）
        // - silenceMs: 连续静音超过此毫秒数 → 触发切片（自然句号停顿）
        // - minChunkMs: 最小 chunk 长度（防超短碎片）
        // - maxChunkMs: 最大 chunk 长度（防有人讲不停一直不切）
        // - minPeak: chunk 上传前要求的最大音量峰值（过滤纯噪音 chunk）
        this._vadRmsThreshold = this._vadRmsThreshold || 0.020;
        this._vadSilenceMs = this._vadSilenceMs || 600;       // 600ms 停顿 = 一句话结束
        this._vadMinChunkMs = this._vadMinChunkMs || 2500;    // 至少 2.5s 才切
        this._vadMaxChunkMs = this._vadMaxChunkMs || 15000;   // 最多 15s 强制切
        this._vadMinPeak = this._vadMinPeak || 0.025;
        this._vadSampleIntervalMs = 50;

        // 状态机：
        //   'idle'      初始/刚切完
        //   'speaking'  正在说话
        //   'silence'   说话中遇到停顿（累计 silence 时间）
        this._vadState = 'idle';
        this._chunkStartTs = null;       // 当前 chunk 起始时间
        this._silenceStartTs = null;     // 进入 silence 状态的起始时间
        this._vadMaxRms = 0;             // 当前 chunk 的最大 RMS（用于上传判断）
        this._vadVoicedCount = 0;        // 当前 chunk 有声音的采样次数
        this._vadSampleCount = 0;        // 当前 chunk 总采样次数
        this._cyclingRotation = false;   // 防止并发触发 rotation

        try {
            this._audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this._source = this._audioContext.createMediaStreamSource(this.stream);
            this._analyser = this._audioContext.createAnalyser();
            this._analyser.fftSize = 512;
            this._source.connect(this._analyser);
            this._timeData = new Uint8Array(this._analyser.fftSize);
            this._vadTimer = setInterval(() => this._vadTick(), this._vadSampleIntervalMs);
        } catch (e) {
            console.warn('[translator] VAD 初始化失败，将退化为固定 8s 切片:', e.message);
            // VAD 不可用时回退到固定切片（兜底）
            this._cycleTimer = setInterval(() => this._rotateRecorder(), 8000);
        }

        this._startNewRecorderCycle();
        this._chunkStartTs = Date.now();
    }

    // VAD 状态机：每 50ms 跑一次，决定是否触发切片
    _vadTick() {
        if (!this._analyser || this.state !== 'running') return;
        this._analyser.getByteTimeDomainData(this._timeData);
        let sum = 0;
        for (let i = 0; i < this._timeData.length; i++) {
            const v = (this._timeData[i] - 128) / 128;
            sum += v * v;
        }
        const rms = Math.sqrt(sum / this._timeData.length);
        try { this.onLevel(rms); } catch (_) {}
        const now = Date.now();
        const chunkAge = this._chunkStartTs ? now - this._chunkStartTs : 0;
        const isVoiced = rms >= this._vadRmsThreshold;

        // 累积当前 chunk 的 VAD 统计（用于上传时过滤纯噪音）
        this._vadSampleCount++;
        if (isVoiced) this._vadVoicedCount++;
        if (rms > this._vadMaxRms) this._vadMaxRms = rms;

        // 状态转移
        if (isVoiced) {
            // 有声音 → speaking
            this._vadState = 'speaking';
            this._silenceStartTs = null;
        } else {
            // 没声音 → 进入 silence 状态（如果之前在 speaking）
            if (this._vadState === 'speaking') {
                this._vadState = 'silence';
                this._silenceStartTs = now;
            }
        }

        // 触发切片的两个条件：
        // 1. 处在 silence 状态 + 静音持续 ≥ silenceMs + chunk 已够 minChunkMs → 自然停顿切
        // 2. chunk 时长 ≥ maxChunkMs → 强制切（防有人讲不停）
        let shouldCut = false;
        let reason = '';
        if (this._vadState === 'silence' &&
            this._silenceStartTs &&
            (now - this._silenceStartTs) >= this._vadSilenceMs &&
            chunkAge >= this._vadMinChunkMs) {
            shouldCut = true;
            reason = `自然停顿 ${now - this._silenceStartTs}ms`;
        } else if (chunkAge >= this._vadMaxChunkMs) {
            shouldCut = true;
            reason = `达到最大长度 ${chunkAge}ms`;
        }

        if (shouldCut && !this._cyclingRotation) {
            this._cyclingRotation = true;
            console.log(`[VAD ${this.speaker}] cut: ${reason}, chunkAge=${chunkAge}ms, voiced=${this._vadVoicedCount}/${this._vadSampleCount}, peak=${this._vadMaxRms.toFixed(3)}`);
            this._rotateRecorder().finally(() => {
                this._cyclingRotation = false;
            });
        }
    }

    _startNewRecorderCycle() {
        // 先检查 stream 状态，给出有用错误信息
        const tracks = this.stream && this.stream.getAudioTracks ? this.stream.getAudioTracks() : [];
        if (tracks.length === 0) {
            this.onError(`stream 没有音轨 (speaker=${this.speaker})`);
            return;
        }
        const liveCount = tracks.filter(t => t.readyState === 'live').length;
        if (liveCount === 0) {
            const info = tracks.map(t => `${t.kind}:${t.readyState}:enabled=${t.enabled}`).join(', ');
            this.onError(`stream 音轨已结束 (speaker=${this.speaker}, tracks=${info})`);
            return;
        }

        // 构造 MediaRecorder：先尝试 opus 编码，失败降级到默认
        try {
            try {
                this._mediaRecorder = new MediaRecorder(this.stream, { mimeType: this._mimeType });
            } catch (mimeErr) {
                console.warn(`[translator ${this.speaker}] mimeType ${this._mimeType} 不支持，降级 default:`, mimeErr.message);
                this._mediaRecorder = new MediaRecorder(this.stream);
            }
            this._buffer = [];

            this._mediaRecorder.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) {
                    this._buffer.push(e.data);
                }
            };

            this._mediaRecorder.onerror = (e) => {
                this.onError('MediaRecorder error: ' + (e.error || 'unknown'));
            };

            // start() 失败时打印 stream 状态便于排查
            try {
                this._mediaRecorder.start();
            } catch (startErr) {
                const info = tracks.map(t => `${t.kind}:${t.readyState}:enabled=${t.enabled}:muted=${t.muted}`).join(' / ');
                this.onError(`MediaRecorder.start 失败 (speaker=${this.speaker}, mime=${this._mimeType}, tracks=[${info}]): ${startErr.message}`);
                this._mediaRecorder = null;
                return;
            }
        } catch (e) {
            this.onError('启动新录音周期失败: ' + (e.message || e));
        }
    }

    async _rotateRecorder() {
        if (this.state !== 'running') return;
        if (!this._mediaRecorder || this._mediaRecorder.state === 'inactive') {
            this._startNewRecorderCycle();
            this._resetVadAccumulators();
            this._chunkStartTs = Date.now();
            return;
        }

        // 旧 chunk 在 recording 里的起始偏移（毫秒）—— rotation 之前抓
        const oldChunkAudioOffsetMs = this._currentChunkAudioOffsetMs();

        // stop 旧的，等 onstop 触发后拿到完整 webm
        const oldRecorder = this._mediaRecorder;
        await new Promise((resolve) => {
            oldRecorder.onstop = () => resolve();
            try { oldRecorder.stop(); } catch (_) { resolve(); }
        });

        // 抓取旧 cycle 的统计 + buffer，再启动新 cycle
        const blobToUpload = this._buffer;
        this._buffer = [];
        const samples = this._vadSampleCount;
        const voiced = this._vadVoicedCount;
        const peak = this._vadMaxRms;
        const speechRatio = samples > 0 ? voiced / samples : 0;

        // 重置 VAD 统计 + chunk 起点 + 状态
        this._resetVadAccumulators();
        this._chunkStartTs = Date.now();
        this._vadState = 'idle';
        this._silenceStartTs = null;

        if (this.state === 'running') {
            this._startNewRecorderCycle();
        }

        // 上传判断：peak + voiced 绝对值 + voiced 比例 三道闸（防止偶发噪音/低信噪比 chunk 进 Whisper hallucinate）
        if (this._analyser) {
            const voicedRatio = samples > 0 ? voiced / samples : 0;
            const isVoice = peak >= this._vadMinPeak && voiced >= 10 && voicedRatio >= 0.20;
            if (!isVoice) {
                console.log(`[VAD ${this.speaker}] SKIP: voiced=${voiced}/${samples} ratio=${voicedRatio.toFixed(2)} peak=${peak.toFixed(3)}`);
                return;
            }
        }

        // 上传旧 cycle 的完整 webm，附 chunk 在 audio 里的起始偏移
        if (blobToUpload.length > 0) {
            const blob = new Blob(blobToUpload, { type: 'audio/webm' });
            if (blob.size >= 4096) {
                this._uploadBlob(blob, oldChunkAudioOffsetMs);
            }
        }
    }

    // 当前 chunk 在录音中的开始毫秒 = 当前 chunk 起始时间 - 录音开始时间 - 暂停累计
    _currentChunkAudioOffsetMs() {
        if (!this._recordingStartedAt || !this._chunkStartTs) return 0;
        return Math.max(0, this._chunkStartTs - this._recordingStartedAt - (this._pausedAccumulatedMs || 0));
    }

    _resetVadAccumulators() {
        this._vadSampleCount = 0;
        this._vadVoicedCount = 0;
        this._vadMaxRms = 0;
    }

    pause() {
        if (this.state !== 'running') return;
        if (this._mediaRecorder && this._mediaRecorder.state === 'recording') {
            this._mediaRecorder.pause();
        }
        this.state = 'paused';
        this._pausedAt = Date.now();
        this.onStatus('paused');
    }

    resume() {
        if (this.state !== 'paused') return;
        if (this._mediaRecorder && this._mediaRecorder.state === 'paused') {
            this._mediaRecorder.resume();
        }
        // 累计暂停时长（这段不计入 audio 时间）
        if (this._pausedAt) {
            this._pausedAccumulatedMs = (this._pausedAccumulatedMs || 0) + (Date.now() - this._pausedAt);
            this._pausedAt = null;
        }
        this.state = 'running';
        // 重置 VAD 状态：暂停期间累积的 silence/chunkAge 不算
        this._resetVadAccumulators();
        this._chunkStartTs = Date.now();
        this._vadState = 'idle';
        this._silenceStartTs = null;
        this.onStatus('running');
    }

    async stop() {
        if (this.state === 'stopped' || this.state === 'idle') return;

        this.state = 'stopped';
        this.onStatus('stopped');

        if (this._cycleTimer) {
            clearInterval(this._cycleTimer);
            this._cycleTimer = null;
        }
        if (this._vadTimer) {
            clearInterval(this._vadTimer);
            this._vadTimer = null;
        }
        if (this._audioContext) {
            try { this._audioContext.close(); } catch (_) {}
            this._audioContext = null;
            this._analyser = null;
            this._source = null;
        }

        // 停止当前 recorder，等 onstop 触发拿到完整 webm
        if (this._mediaRecorder && this._mediaRecorder.state !== 'inactive') {
            await new Promise((resolve) => {
                this._mediaRecorder.onstop = () => resolve();
                try { this._mediaRecorder.stop(); } catch (_) { resolve(); }
            });
        }

        // 上传最后一块（带最后 chunk 的偏移）
        if (this._buffer.length > 0) {
            const blob = new Blob(this._buffer, { type: 'audio/webm' });
            this._buffer = [];
            if (blob.size >= 4096) {
                await this._uploadBlob(blob, this._currentChunkAudioOffsetMs());
            }
        }
    }

    updateNativeLang(nativeLang) {
        this.nativeLang = nativeLang;
    }

    // ====== 私有 ======

    _getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/mp4',
            'audio/ogg;codecs=opus'
        ];
        for (const t of types) {
            if (MediaRecorder.isTypeSupported(t)) return t;
        }
        return 'audio/webm';
    }

    async _uploadBlob(blob, chunkAudioOffsetMs = null) {
        this._inflight++;
        try {
            const formData = new FormData();
            formData.append('chunk', blob, `realtime_${Date.now()}.webm`);
            formData.append('native_lang', this.nativeLang);
            if (chunkAudioOffsetMs !== null && chunkAudioOffsetMs >= 0) {
                formData.append('chunk_audio_offset_ms', String(Math.round(chunkAudioOffsetMs)));
            }
            formData.append('speaker', this.speaker);

            const resp = await fetch(this.uploadUrl, {
                method: 'POST',
                body: formData
            });

            if (!resp.ok) {
                const err = await resp.text().catch(() => '');
                throw new Error(`HTTP ${resp.status}: ${err.substring(0, 200)}`);
            }

            const data = await resp.json();
            if (!data.success) {
                throw new Error(data.message || '翻译失败');
            }

            // 空 chunk（无人声）静默丢弃
            if (data.empty) return;

            this.onMessage({
                speaker: data.speaker,
                original: data.original,
                translation: data.translation,
                detectedLang: data.detected_lang,
                nativeLang: data.native_lang,
                wasTranslated: data.was_translated,
                durationMs: data.duration_ms,
                timestamp: new Date()
            });
        } catch (e) {
            this.onError(`翻译上传失败: ${e.message}`);
        } finally {
            this._inflight--;
        }
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RealtimeTranslator;
}
