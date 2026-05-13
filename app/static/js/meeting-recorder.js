/**
 * 会议录音工具 - Meeting Recorder Utility
 *
 * 功能：
 * - 浏览器音频录制（麦克风/系统音频）
 * - 分块上传（30秒间隔）
 * - 暂停/恢复录音
 * - 离线支持（本地存储后上传）
 * - 录音时长控制（最长3小时）
 *
 * 使用示例：
 * const recorder = new MeetingRecorder({
 *     recordingId: 123,
 *     mode: 'microphone', // 'microphone' | 'microphone_system'
 *     onTimeUpdate: (seconds) => console.log('Time:', seconds),
 *     onStateChange: (state) => console.log('State:', state),
 *     onError: (error) => console.error(error)
 * });
 *
 * await recorder.start();
 * recorder.pause();
 * recorder.resume();
 * await recorder.stop();
 */

class MeetingRecorder {
    constructor(options = {}) {
        // 配置
        this.recordingId = options.recordingId;
        this.mode = options.mode || 'microphone';
        this.externalStream = options.externalStream || null;  // 用于 mode='external_stream'
        this.chunkDuration = options.chunkDuration || 30; // 秒
        this.maxDuration = options.maxDuration || 3 * 60 * 60; // 3小时
        this.uploadUrl = options.uploadUrl || '/meeting/api/recordings/chunk';
        this.completeUrl = options.completeUrl || `/meeting/api/recordings/${this.recordingId}/complete`;
        this.track = options.track || 'mixed';  // 双轨录音：'mixed' / 'system'

        // 回调
        this.onTimeUpdate = options.onTimeUpdate || (() => {});
        this.onStateChange = options.onStateChange || (() => {});
        this.onError = options.onError || console.error;
        this.onDurationWarning = options.onDurationWarning || (() => {});
        this.onUploadProgress = options.onUploadProgress || (() => {});

        // 状态
        this.state = 'idle'; // idle | recording | paused | stopped
        this.elapsedTime = options.initialTime || 0;
        this.isOnline = navigator.onLine;

        // MediaRecorder
        this.mediaRecorder = null;
        this.audioStream = null;
        this.audioContext = null;
        this.audioChunks = [];

        // 定时器
        this.timerInterval = null;
        this.chunkInterval = null;

        // 上传队列
        this.pendingChunks = [];
        this.isUploading = false;

        // 时长警告标记
        this.hourWarningShown = false;
        this.twoHourWarningShown = false;

        // 绑定网络事件
        this._bindNetworkEvents();
    }

    /**
     * 开始录音
     */
    async start() {
        if (this.state === 'recording') {
            console.warn('Already recording');
            return;
        }

        try {
            await this._initMediaRecorder();
            // 传入 timeslice (1000ms) 让 MediaRecorder 自动每秒触发一次 ondataavailable
            // 这样 audioChunks 始终有最新数据，停止录音时不会丢失
            this.mediaRecorder.start(1000);
            this._startTimer();
            this._startChunkUpload();
            this._setState('recording');
        } catch (error) {
            this.onError(this._getPermissionErrorMessage(error));
            throw error;
        }
    }

    /**
     * 暂停录音
     */
    pause() {
        if (this.state !== 'recording') return;

        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.pause();
        }
        this._setState('paused');
    }

    /**
     * 恢复录音
     */
    resume() {
        if (this.state !== 'paused') return;

        if (this.mediaRecorder && this.mediaRecorder.state === 'paused') {
            this.mediaRecorder.resume();
        }
        this._setState('recording');
    }

    /**
     * 停止录音
     */
    async stop() {
        if (this.state === 'stopped' || this.state === 'idle') return;

        this._setState('stopped');
        this._stopTimer();

        // 停止 MediaRecorder（异步：等 onstop 触发后才能保证最后一次 ondataavailable 已完成）
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            await new Promise((resolve) => {
                this.mediaRecorder.onstop = () => resolve();
                this.mediaRecorder.stop();
            });
        }

        // 停止音轨
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
        }

        // 关闭 AudioContext
        if (this.audioContext) {
            this.audioContext.close();
        }

        // 上传剩余数据（此时 audioChunks 包含完整音频）
        await this._uploadRemainingChunks();

        // 通知服务器录音完成
        await this._notifyComplete();
    }

    /**
     * 取消录音（不保存）
     */
    cancel() {
        this._setState('stopped');
        this._stopTimer();

        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }

        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
        }

        if (this.audioContext) {
            this.audioContext.close();
        }

        // 清空缓存数据
        this.audioChunks = [];
        this.pendingChunks = [];
    }

    /**
     * 获取格式化的时间字符串
     */
    getFormattedTime() {
        return this._formatTime(this.elapsedTime);
    }

    /**
     * 获取当前状态
     */
    getState() {
        return this.state;
    }

    /**
     * 获取待上传块数
     */
    getPendingChunksCount() {
        return this.pendingChunks.length;
    }

    // ============ 私有方法 ============

    /**
     * 初始化 MediaRecorder
     */
    async _initMediaRecorder() {
        let stream;

        if (this.mode === 'external_stream' && this.externalStream) {
            // 外部传入的混合 stream（避免重复 getDisplayMedia / getUserMedia）
            stream = this.externalStream;
        } else if (this.mode === 'microphone_system') {
            stream = await this._getMixedStream();
        } else {
            stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
        }

        this.audioStream = stream;

        // 检测支持的 MIME 类型
        const mimeType = this._getSupportedMimeType();

        this.mediaRecorder = new MediaRecorder(stream, { mimeType });

        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.audioChunks.push(event.data);
            }
        };

        this.mediaRecorder.onstop = () => {
            // 录音停止时的处理
        };

        this.mediaRecorder.onerror = (event) => {
            this.onError('录音出错: ' + event.error);
        };
    }

    /**
     * 获取混合音频流（麦克风 + 系统音频）
     */
    async _getMixedStream() {
        // 获取屏幕共享（包含系统音频）
        const displayStream = await navigator.mediaDevices.getDisplayMedia({
            video: true, // 必须有视频才能获取音频
            audio: true
        });

        // 获取麦克风
        const micStream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        // 创建 AudioContext 合并音轨
        this.audioContext = new AudioContext();
        const destination = this.audioContext.createMediaStreamDestination();

        // 添加系统音频
        const displayAudio = displayStream.getAudioTracks()[0];
        if (displayAudio) {
            const displaySource = this.audioContext.createMediaStreamSource(
                new MediaStream([displayAudio])
            );
            displaySource.connect(destination);
        }

        // 添加麦克风音频
        const micSource = this.audioContext.createMediaStreamSource(micStream);
        micSource.connect(destination);

        // 停止视频轨道（我们只需要音频）
        displayStream.getVideoTracks().forEach(track => track.stop());

        return destination.stream;
    }

    /**
     * 获取支持的 MIME 类型
     */
    _getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/mp4',
            'audio/ogg;codecs=opus'
        ];

        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }

        return 'audio/webm';
    }

    /**
     * 开始计时器
     */
    _startTimer() {
        this.timerInterval = setInterval(() => {
            if (this.state === 'recording') {
                this.elapsedTime++;
                this.onTimeUpdate(this.elapsedTime);

                // 时长警告
                if (this.elapsedTime === 60 * 60 && !this.hourWarningShown) {
                    this.hourWarningShown = true;
                    this.onDurationWarning('1hour');
                } else if (this.elapsedTime === 2 * 60 * 60 && !this.twoHourWarningShown) {
                    this.twoHourWarningShown = true;
                    this.onDurationWarning('2hours');
                }

                // 最大时长
                if (this.elapsedTime >= this.maxDuration) {
                    this.onDurationWarning('max');
                    this.stop();
                }
            }
        }, 1000);
    }

    /**
     * 停止计时器
     */
    _stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        if (this.chunkInterval) {
            clearInterval(this.chunkInterval);
            this.chunkInterval = null;
        }
    }

    /**
     * 开始分块上传
     */
    _startChunkUpload() {
        this.chunkInterval = setInterval(() => {
            if (this.state === 'recording' && this.audioChunks.length > 0) {
                this._uploadChunk();
            }
        }, this.chunkDuration * 1000);
    }

    /**
     * 上传当前块
     */
    async _uploadChunk() {
        if (this.audioChunks.length === 0) return;

        // 请求当前数据
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.requestData();
        }

        // 等待数据
        await new Promise(resolve => setTimeout(resolve, 100));

        if (this.audioChunks.length === 0) return;

        const chunk = new Blob(this.audioChunks, { type: 'audio/webm' });
        this.audioChunks = [];

        if (!this.isOnline) {
            this.pendingChunks.push(chunk);
            this.onUploadProgress(this.pendingChunks.length);
            return;
        }

        try {
            await this._uploadBlob(chunk, false);
        } catch (error) {
            console.error('上传分块失败:', error);
            this.pendingChunks.push(chunk);
            this.onUploadProgress(this.pendingChunks.length);
        }
    }

    /**
     * 上传剩余块
     */
    async _uploadRemainingChunks() {
        // 上传最后的数据
        if (this.audioChunks.length > 0) {
            const chunk = new Blob(this.audioChunks, { type: 'audio/webm' });
            this.audioChunks = [];

            try {
                await this._uploadBlob(chunk, true);
            } catch (error) {
                console.error('上传最后分块失败:', error);
                this.pendingChunks.push(chunk);
            }
        }

        // 上传离线时积累的块
        await this._uploadPendingChunks();
    }

    /**
     * 上传待处理的块
     */
    async _uploadPendingChunks() {
        if (!this.isOnline || this.isUploading) return;

        this.isUploading = true;

        while (this.pendingChunks.length > 0 && this.isOnline) {
            const chunk = this.pendingChunks.shift();
            try {
                await this._uploadBlob(chunk, this.pendingChunks.length === 0);
                this.onUploadProgress(this.pendingChunks.length);
            } catch (error) {
                // 上传失败，放回队列
                this.pendingChunks.unshift(chunk);
                break;
            }
        }

        this.isUploading = false;
    }

    /**
     * 上传 Blob 数据
     */
    async _uploadBlob(blob, isFinal) {
        const formData = new FormData();
        formData.append('chunk', blob, 'audio.webm');
        formData.append('recording_id', this.recordingId);
        formData.append('duration', this.elapsedTime);
        formData.append('track', this.track);
        if (isFinal) {
            formData.append('is_final', 'true');
        }

        const response = await fetch(this.uploadUrl, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * 通知服务器录音完成
     */
    async _notifyComplete() {
        try {
            const response = await fetch(this.completeUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ duration: this.elapsedTime })
            });

            return response.json();
        } catch (error) {
            console.error('通知录音完成失败:', error);
            throw error;
        }
    }

    /**
     * 设置状态
     */
    _setState(state) {
        this.state = state;
        this.onStateChange(state);
    }

    /**
     * 绑定网络事件
     */
    _bindNetworkEvents() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            // 恢复上传
            this._uploadPendingChunks();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
        });
    }

    /**
     * 格式化时间
     */
    _formatTime(seconds) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }

    /**
     * 获取权限错误信息
     */
    _getPermissionErrorMessage(error) {
        if (error.name === 'NotAllowedError') {
            return '麦克风权限被拒绝，请在浏览器设置中允许访问麦克风';
        } else if (error.name === 'NotFoundError') {
            return '未找到麦克风设备，请检查设备连接';
        }
        return '无法启动录音：' + error.message;
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MeetingRecorder;
}
