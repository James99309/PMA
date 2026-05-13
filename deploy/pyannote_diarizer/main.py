"""
PMA pyannote 声纹分离服务

部署在 Mac mini 上，被 PMA (CN/SG NAS) 通过 Tailscale 调用。

工作流程：
1. PMA 录音结束 → POST /diarize { audio_url, recording_id }
2. 本服务从 audio_url（NAS WebDAV）下载音频
3. ffmpeg 转码 → wav 16kHz mono
4. pyannote.audio 推理 → 返回 [{start, end, speaker}]

启动：
    PYANNOTE_AUTH_TOKEN=hf_xxx uvicorn main:app --host 100.110.41.83 --port 8080

环境变量：
    PYANNOTE_AUTH_TOKEN  HuggingFace token（必填，要 accept pyannote/speaker-diarization-3.1 license）
    PYANNOTE_MODEL       默认 'pyannote/speaker-diarization-3.1'
    LOG_LEVEL            默认 INFO
"""
import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
import time
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

# ============================================================================
# 新版 torchaudio (2.4+) / torch (2.6+) 兼容 shim
# pyannote 3.3.2 跟它们都不兼容，必须打补丁。
# ============================================================================
import torchaudio  # noqa: E402
import torch  # noqa: E402

# torch.load: 2.6+ 默认 weights_only=True，pyannote checkpoint 加载会失败
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

# torchaudio.AudioMetaData
if not hasattr(torchaudio, 'AudioMetaData'):
    class _AudioMetaDataShim:
        def __init__(self, sample_rate=16000, num_frames=0, num_channels=1,
                     bits_per_sample=16, encoding='PCM_S'):
            self.sample_rate = sample_rate
            self.num_frames = num_frames
            self.num_channels = num_channels
            self.bits_per_sample = bits_per_sample
            self.encoding = encoding
    torchaudio.AudioMetaData = _AudioMetaDataShim

# torchaudio.list_audio_backends
if not hasattr(torchaudio, 'list_audio_backends'):
    torchaudio.list_audio_backends = lambda: ['soundfile']

# torchaudio.get_audio_backend / set_audio_backend
if not hasattr(torchaudio, 'get_audio_backend'):
    torchaudio.get_audio_backend = lambda: 'soundfile'
if not hasattr(torchaudio, 'set_audio_backend'):
    torchaudio.set_audio_backend = lambda backend: None

# torchaudio.info — 用 soundfile 替代
if not hasattr(torchaudio, 'info'):
    import soundfile as _sf  # noqa
    def _info_shim(path, *args, **kwargs):
        try:
            info = _sf.info(str(path))
            return torchaudio.AudioMetaData(
                sample_rate=int(info.samplerate),
                num_frames=int(info.frames),
                num_channels=int(info.channels),
                bits_per_sample=info.subtype_info.split()[0].lstrip('PCM_').rstrip() if hasattr(info, 'subtype_info') else 16,
                encoding='PCM_S',
            )
        except Exception:
            return torchaudio.AudioMetaData()
    torchaudio.info = _info_shim

# torchaudio.load — 用 soundfile 替代（如果 load 也被移除）
if not hasattr(torchaudio, 'load') or 'load_with_torchcodec' in str(getattr(torchaudio, 'load', None)):
    import soundfile as _sf2  # noqa
    import numpy as _np  # noqa
    def _load_shim(path, *args, **kwargs):
        data, sr = _sf2.read(str(path), dtype='float32')
        if data.ndim == 1:
            tensor = torch.from_numpy(data).unsqueeze(0)
        else:
            tensor = torch.from_numpy(data.T)
        return tensor, sr
    torchaudio.load = _load_shim

# 配置
PYANNOTE_AUTH_TOKEN = os.environ.get('PYANNOTE_AUTH_TOKEN', '')
PYANNOTE_MODEL = os.environ.get('PYANNOTE_MODEL', 'pyannote/speaker-diarization-3.1')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

logging.basicConfig(level=getattr(logging, LOG_LEVEL), format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('diarizer')

# 全局 pipeline（启动时加载一次）
_pipeline = None
# 推理串行锁（避免并发把内存打爆）
_inference_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时预加载 pyannote pipeline（~3-10s）"""
    global _pipeline
    if not PYANNOTE_AUTH_TOKEN:
        logger.error('PYANNOTE_AUTH_TOKEN 未配置，服务不可用')
        yield
        return

    try:
        from pyannote.audio import Pipeline
        import torch

        logger.info(f'加载 pipeline: {PYANNOTE_MODEL}')
        t0 = time.time()
        _pipeline = Pipeline.from_pretrained(PYANNOTE_MODEL, use_auth_token=PYANNOTE_AUTH_TOKEN)

        # Apple Silicon MPS 加速（如果可用）
        if torch.backends.mps.is_available():
            device = torch.device('mps')
            _pipeline.to(device)
            logger.info(f'pipeline 加载完毕 ({time.time() - t0:.1f}s)，使用 MPS 加速')
        else:
            logger.info(f'pipeline 加载完毕 ({time.time() - t0:.1f}s)，CPU 推理')
    except Exception as e:
        logger.error(f'pipeline 加载失败: {e}', exc_info=True)
        _pipeline = None

    yield

    # 关闭时清理
    _pipeline = None


app = FastAPI(title='PMA Diarizer', lifespan=lifespan)


class DiarizeRequest(BaseModel):
    audio_url: str = Field(..., description='音频文件 URL（NAS WebDAV 或 http）')
    recording_id: Optional[int] = Field(None, description='录音 ID，仅用于日志追踪')
    num_speakers: Optional[int] = Field(None, description='已知说话人数（可选，提高准确率）')
    min_speakers: Optional[int] = Field(None, description='最少说话人数')
    max_speakers: Optional[int] = Field(None, description='最多说话人数')
    auth_basic: Optional[str] = Field(None, description='NAS WebDAV Basic auth: user:pass')


class Segment(BaseModel):
    start: float
    end: float
    speaker: str  # SPEAKER_00, SPEAKER_01, ...


class DiarizeResponse(BaseModel):
    success: bool
    recording_id: Optional[int]
    speaker_count: int
    segments: list[Segment]
    duration_ms: int
    error: Optional[str] = None


@app.get('/health')
def health():
    return {
        'ok': _pipeline is not None,
        'model': PYANNOTE_MODEL,
        'has_token': bool(PYANNOTE_AUTH_TOKEN),
    }


@app.post('/diarize-upload', response_model=DiarizeResponse)
async def diarize_upload(
    audio: UploadFile = File(...),
    recording_id: Optional[int] = Form(None),
    num_speakers: Optional[int] = Form(None),
    min_speakers: Optional[int] = Form(None),
    max_speakers: Optional[int] = Form(None),
):
    """multipart 直接上传音频文件（适合 PMA 实例直接发本地文件，无需 audio_url）"""
    if _pipeline is None:
        raise HTTPException(503, 'pipeline 未加载')

    t_total = time.time()
    rec_id = recording_id

    async with _inference_lock:
        with tempfile.TemporaryDirectory(prefix='diarize_up_') as tmpdir:
            in_path = os.path.join(tmpdir, 'in_' + (audio.filename or 'audio.webm'))
            wav_path = os.path.join(tmpdir, 'in.wav')

            # 1. 保存上传文件
            t0 = time.time()
            with open(in_path, 'wb') as f:
                while True:
                    chunk = await audio.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
            size = os.path.getsize(in_path)
            logger.info(f'[{rec_id}] upload 完成 {size} bytes ({time.time() - t0:.1f}s)')

            # 2. ffmpeg 转码
            t0 = time.time()
            result = subprocess.run(
                ['ffmpeg', '-y', '-i', in_path, '-f', 'wav', '-ar', '16000', '-ac', '1', wav_path],
                capture_output=True, timeout=180
            )
            if result.returncode != 0:
                err = result.stderr.decode(errors='ignore')[-500:]
                raise HTTPException(500, f'ffmpeg 转码失败: {err}')
            logger.info(f'[{rec_id}] 转码完成 ({time.time() - t0:.1f}s)')

            # 3. pyannote 推理
            t0 = time.time()
            kwargs = {}
            if num_speakers: kwargs['num_speakers'] = num_speakers
            if min_speakers: kwargs['min_speakers'] = min_speakers
            if max_speakers: kwargs['max_speakers'] = max_speakers

            loop = asyncio.get_running_loop()
            try:
                diarization = await loop.run_in_executor(
                    None, lambda: _pipeline(wav_path, **kwargs)
                )
            except Exception as e:
                logger.error(f'[{rec_id}] 推理失败: {e}', exc_info=True)
                raise HTTPException(500, f'推理失败: {e}')
            logger.info(f'[{rec_id}] 推理完成 ({time.time() - t0:.1f}s)')

            segments = []
            speakers_set = set()
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append(Segment(start=round(turn.start, 3), end=round(turn.end, 3), speaker=speaker))
                speakers_set.add(speaker)

    duration_ms = int((time.time() - t_total) * 1000)
    logger.info(f'[{rec_id}] 完成 segments={len(segments)} speakers={len(speakers_set)} 总耗时={duration_ms}ms')
    return DiarizeResponse(
        success=True,
        recording_id=rec_id,
        speaker_count=len(speakers_set),
        segments=segments,
        duration_ms=duration_ms,
    )


@app.post('/diarize', response_model=DiarizeResponse)
async def diarize(req: DiarizeRequest):
    if _pipeline is None:
        raise HTTPException(503, 'pipeline 未加载（检查 HF token 和 license）')

    t_total = time.time()
    rec_id = req.recording_id

    # 串行锁：避免多请求并发把 Mac 内存爆掉
    async with _inference_lock:
        with tempfile.TemporaryDirectory(prefix='diarize_') as tmpdir:
            webm_path = os.path.join(tmpdir, 'in.webm')
            wav_path = os.path.join(tmpdir, 'in.wav')

            # 1. 下载音频（支持 NAS WebDAV basic auth）
            try:
                t0 = time.time()
                auth = None
                if req.auth_basic and ':' in req.auth_basic:
                    user, pw = req.auth_basic.split(':', 1)
                    auth = (user, pw)
                async with httpx.AsyncClient(timeout=120.0, auth=auth) as client:
                    async with client.stream('GET', req.audio_url) as r:
                        if r.status_code >= 400:
                            raise HTTPException(400, f'下载音频失败 HTTP {r.status_code}')
                        with open(webm_path, 'wb') as f:
                            async for chunk in r.aiter_bytes():
                                f.write(chunk)
                size = os.path.getsize(webm_path)
                logger.info(f'[{rec_id}] 下载完成 {size} bytes ({time.time() - t0:.1f}s)')
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(500, f'下载音频异常: {e}')

            # 2. ffmpeg 转码为 16kHz mono wav（pyannote 要求）
            try:
                t0 = time.time()
                result = subprocess.run(
                    ['ffmpeg', '-y', '-i', webm_path, '-f', 'wav', '-ar', '16000', '-ac', '1', wav_path],
                    capture_output=True, timeout=120
                )
                if result.returncode != 0:
                    err = result.stderr.decode(errors='ignore')[-500:]
                    raise HTTPException(500, f'ffmpeg 转码失败: {err}')
                logger.info(f'[{rec_id}] 转码完成 {os.path.getsize(wav_path)} bytes ({time.time() - t0:.1f}s)')
            except subprocess.TimeoutExpired:
                raise HTTPException(500, 'ffmpeg 转码超时')

            # 3. pyannote 推理
            try:
                t0 = time.time()
                kwargs = {}
                if req.num_speakers:
                    kwargs['num_speakers'] = req.num_speakers
                if req.min_speakers:
                    kwargs['min_speakers'] = req.min_speakers
                if req.max_speakers:
                    kwargs['max_speakers'] = req.max_speakers

                # 把同步推理放到 thread pool，避免阻塞事件循环
                loop = asyncio.get_running_loop()
                diarization = await loop.run_in_executor(
                    None,
                    lambda: _pipeline(wav_path, **kwargs)
                )
                logger.info(f'[{rec_id}] 推理完成 ({time.time() - t0:.1f}s)')
            except Exception as e:
                logger.error(f'[{rec_id}] 推理失败: {e}', exc_info=True)
                raise HTTPException(500, f'推理失败: {e}')

            # 4. 整理输出
            segments = []
            speakers_set = set()
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append(Segment(
                    start=round(turn.start, 3),
                    end=round(turn.end, 3),
                    speaker=speaker,
                ))
                speakers_set.add(speaker)

    duration_ms = int((time.time() - t_total) * 1000)
    logger.info(f'[{rec_id}] 完成 segments={len(segments)} speakers={len(speakers_set)} 总耗时={duration_ms}ms')
    return DiarizeResponse(
        success=True,
        recording_id=rec_id,
        speaker_count=len(speakers_set),
        segments=segments,
        duration_ms=duration_ms,
    )
