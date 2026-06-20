# -*- coding: utf-8 -*-
"""
会议录音纪要服务

集成功能：
- 音频文件上传到 Supabase Storage 或 群晖NAS (WebDAV)
- OpenAI Whisper 语音转录
- AI 会议纪要生成
- 说话人分离（使用简化方案）

存储选项（通过 MEETING_STORAGE_TYPE 环境变量配置）：
- synology: 群晖NAS WebDAV存储（推荐，无费用）
- supabase: Supabase云端存储
- local: 本地文件存储
"""
import os
import io
import json
import logging
import tempfile
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from flask import current_app

logger = logging.getLogger(__name__)


def get_storage_type() -> str:
    """获取当前配置的存储类型"""
    return os.environ.get('MEETING_STORAGE_TYPE', 'synology').lower()


def get_webdav_client():
    """获取群晖WebDAV客户端"""
    from app.utils.synology_webdav_client import get_synology_webdav_client
    return get_synology_webdav_client()


class MeetingService:
    """会议录音纪要核心服务"""

    # 支持的音频格式
    SUPPORTED_AUDIO_FORMATS = ['webm', 'mp3', 'wav', 'ogg', 'm4a', 'mp4']

    # 音频存储配置
    AUDIO_BUCKET_TYPE = 'meeting'
    MAX_AUDIO_SIZE = 500 * 1024 * 1024  # 500MB

    # Whisper 配置
    WHISPER_MODEL = 'whisper-1'
    WHISPER_LANGUAGE = 'zh'  # 中文优先

    @classmethod
    def get_openai_client(cls):
        """获取 OpenAI 客户端"""
        try:
            from openai import OpenAI
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OPENAI_API_KEY 未配置")
                return None
            return OpenAI(api_key=api_key)
        except ImportError:
            logger.error("openai 库未安装，请运行: pip install openai")
            return None
        except Exception as e:
            logger.error(f"创建 OpenAI 客户端失败: {e}")
            return None

    @classmethod
    def get_ai_provider_config(cls):
        """获取 AI 提供商配置（复用 ai_analysis_service 的模式）"""
        providers = {
            'anthropic': {
                'api_key_env': 'ANTHROPIC_API_KEY',
                'default_model': 'claude-sonnet-4-20250514',
            },
            'openai': {
                'api_key_env': 'OPENAI_API_KEY',
                'default_model': 'gpt-4o',
            }
        }

        # 会议纪要可单独 override；不设则跟随全局 AI_PROVIDER，缺省走 openai
        provider = (os.environ.get('MEETING_AI_PROVIDER')
                    or os.environ.get('AI_PROVIDER', 'openai'))
        if provider not in providers:
            provider = 'openai'

        config = providers[provider]
        api_key = os.environ.get(config['api_key_env'])

        return {
            'provider': provider,
            'api_key': api_key,
            'model': os.environ.get('MEETING_AI_MODEL', config['default_model']),
        }

    # ============ 音频上传服务 ============

    @classmethod
    def upload_audio_chunk(cls, recording_id: int, chunk_data: bytes,
                          chunk_index: int, is_final: bool = False,
                          track: str = 'mixed') -> Dict:
        """
        上传音频分块到存储（支持群晖WebDAV、Supabase、本地存储）

        Args:
            recording_id: 录音记录ID
            chunk_data: 音频分块数据
            chunk_index: 分块索引
            is_final: 是否为最后一个分块
            track: 'mixed'（mic+system 混音，用于回放）或 'system'（仅对方端，用于 pyannote）

        Returns:
            dict: {success: bool, chunk_path: str, error: str}
        """
        try:
            from app.models.meeting import MeetingRecording
            from app import db

            # 获取录音记录
            recording = MeetingRecording.query.get(recording_id)
            if not recording:
                return {'success': False, 'error': '录音记录不存在'}

            track = track if track in ('mixed', 'system') else 'mixed'
            # 生成分块文件名（track 加前缀避免冲突）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            track_prefix = '' if track == 'mixed' else 'sys_'
            chunk_filename = f"{track_prefix}chunk_{chunk_index:04d}_{timestamp}.webm"

            # 根据存储类型选择上传方式
            storage_type = get_storage_type()

            if storage_type == 'synology':
                # 群晖WebDAV存储
                webdav = get_webdav_client()
                if not webdav.is_configured:
                    return {'success': False, 'error': '群晖WebDAV未配置'}

                # 构建远程路径
                remote_path = f"/meetings/{recording_id}/{chunk_filename}"

                # 上传到群晖
                result = webdav.upload_file(
                    chunk_data,
                    remote_path,
                    content_type='audio/webm'
                )

                if result:
                    chunk_url = remote_path  # 存储相对路径，通过代理访问
                    logger.info(f"音频分块上传到群晖: {remote_path}")
                else:
                    return {'success': False, 'error': '群晖WebDAV上传失败'}

            elif storage_type == 'local':
                # 本地存储
                from flask import current_app
                local_storage_root = current_app.config.get('LOCAL_STORAGE_ROOT', './storage')
                local_dir = os.path.join(local_storage_root, 'meetings', str(recording_id))
                os.makedirs(local_dir, exist_ok=True)
                local_path = os.path.join(local_dir, chunk_filename)

                with open(local_path, 'wb') as f:
                    f.write(chunk_data)

                chunk_url = f"/storage/meetings/{recording_id}/{chunk_filename}"
                logger.info(f"音频分块保存到本地: {local_path}")

            else:
                # Supabase 云端存储
                from app.utils.supabase_client import get_supabase_client
                client = get_supabase_client()

                storage_path = f"meeting_recordings/{recording_id}/{chunk_filename}"
                bucket_name = os.environ.get('SUPABASE_BUCKET_MEETING', 'meeting-recordings')

                if client.use_local_storage:
                    # Supabase客户端的本地模式
                    local_dir = os.path.join(client.local_storage_root, 'meetings', str(recording_id))
                    os.makedirs(local_dir, exist_ok=True)
                    local_path = os.path.join(local_dir, chunk_filename)

                    with open(local_path, 'wb') as f:
                        f.write(chunk_data)

                    chunk_url = f"/storage/meetings/{recording_id}/{chunk_filename}"
                else:
                    try:
                        res = client.supabase.storage.from_(bucket_name).upload(
                            storage_path,
                            chunk_data
                        )
                        chunk_url = f"{client.supabase_url}/storage/v1/object/public/{bucket_name}/{storage_path}"
                    except Exception as e:
                        logger.error(f"Supabase 上传失败: {e}")
                        return {'success': False, 'error': f'上传失败: {str(e)}'}

                logger.info(f"音频分块上传到Supabase: {storage_path}")

            # 更新录音记录
            # SQLAlchemy JSON 字段直接 .append() 不会触发 dirty 标记，必须整体重新赋值
            target_attr = 'chunk_paths' if track == 'mixed' else 'system_chunk_paths'
            chunks = list(getattr(recording, target_attr) or [])
            chunks.append({
                'index': chunk_index,
                'path': chunk_url,
                'storage_type': storage_type,
                'size': len(chunk_data),
                'uploaded_at': datetime.utcnow().isoformat()
            })
            setattr(recording, target_attr, chunks)

            # 仅以 mixed 轨判定上传完成（system 轨可选，不影响主流程）
            if is_final and track == 'mixed':
                recording.status = 'uploaded'

            db.session.commit()

            logger.info(f"音频分块上传成功: recording_id={recording_id}, chunk={chunk_index}, storage={storage_type}")

            return {
                'success': True,
                'chunk_path': chunk_url,
                'chunk_index': chunk_index,
                'storage_type': storage_type
            }

        except Exception as e:
            logger.error(f"上传音频分块失败: {e}")
            return {'success': False, 'error': str(e)}

    @classmethod
    def merge_audio_chunks(cls, recording_id: int, track: str = 'mixed') -> Dict:
        """
        合并音频分块为完整文件（支持群晖WebDAV、Supabase、本地存储）

        Args:
            recording_id: 录音记录ID
            track: 'mixed' 合并 mic+system 混音轨（用于回放）
                   'system' 合并仅对方端轨（用于 pyannote）

        Returns:
            dict: {success: bool, audio_url: str, duration: int}
        """
        try:
            from app.models.meeting import MeetingRecording
            from app import db

            recording = MeetingRecording.query.get(recording_id)
            if not recording:
                return {'success': False, 'error': '录音记录不存在'}

            track = track if track in ('mixed', 'system') else 'mixed'
            chunks_attr = 'chunk_paths' if track == 'mixed' else 'system_chunk_paths'
            chunks_data = getattr(recording, chunks_attr) or []
            if not chunks_data:
                return {'success': False, 'error': f'没有{track}轨音频分块数据'}

            # 按索引排序分块
            sorted_chunks = sorted(chunks_data, key=lambda x: x['index'])
            merged_data = bytearray()

            # 确定存储类型（从第一个分块或当前配置获取）
            storage_type = sorted_chunks[0].get('storage_type', get_storage_type())

            # 读取并合并所有分块
            for chunk_info in sorted_chunks:
                chunk_path = chunk_info['path']
                chunk_storage = chunk_info.get('storage_type', storage_type)

                if chunk_storage == 'synology':
                    # 从群晖WebDAV下载
                    webdav = get_webdav_client()
                    chunk_data = webdav.download_file(chunk_path)
                    if chunk_data:
                        merged_data.extend(chunk_data)
                    else:
                        logger.warning(f"无法从群晖下载分块: {chunk_path}")

                elif chunk_storage == 'local':
                    # 从本地读取
                    from flask import current_app
                    local_storage_root = current_app.config.get('LOCAL_STORAGE_ROOT', './storage')
                    local_path = chunk_path.replace('/storage/', local_storage_root + '/')
                    with open(local_path, 'rb') as f:
                        merged_data.extend(f.read())

                else:
                    # 从Supabase/云端下载
                    import requests
                    response = requests.get(chunk_path)
                    if response.status_code == 200:
                        merged_data.extend(response.content)

            # 保存合并后的文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_prefix = 'recording' if track == 'mixed' else 'system'
            merged_filename = f"{file_prefix}_{recording_id}_{timestamp}.webm"

            if storage_type == 'synology':
                # 上传到群晖WebDAV
                webdav = get_webdav_client()
                remote_path = f"/meetings/{recording_id}/{merged_filename}"

                result = webdav.upload_file(
                    bytes(merged_data),
                    remote_path,
                    content_type='audio/webm'
                )

                if result:
                    audio_url = remote_path
                    logger.info(f"合并音频上传到群晖: {remote_path}")
                else:
                    return {'success': False, 'error': '合并音频上传到群晖失败'}

            elif storage_type == 'local':
                # 保存到本地
                from flask import current_app
                local_storage_root = current_app.config.get('LOCAL_STORAGE_ROOT', './storage')
                local_dir = os.path.join(local_storage_root, 'meetings', str(recording_id))
                os.makedirs(local_dir, exist_ok=True)
                merged_path = os.path.join(local_dir, merged_filename)

                with open(merged_path, 'wb') as f:
                    f.write(merged_data)

                audio_url = f"/storage/meetings/{recording_id}/{merged_filename}"
                logger.info(f"合并音频保存到本地: {merged_path}")

            else:
                # 上传到Supabase
                from app.utils.supabase_client import get_supabase_client
                client = get_supabase_client()
                bucket_name = os.environ.get('SUPABASE_BUCKET_MEETING', 'meeting-recordings')
                storage_path = f"meeting_recordings/{recording_id}/{merged_filename}"

                if client.use_local_storage:
                    local_dir = os.path.join(client.local_storage_root, 'meetings', str(recording_id))
                    os.makedirs(local_dir, exist_ok=True)
                    merged_path = os.path.join(local_dir, merged_filename)

                    with open(merged_path, 'wb') as f:
                        f.write(merged_data)

                    audio_url = f"/storage/meetings/{recording_id}/{merged_filename}"
                else:
                    client.supabase.storage.from_(bucket_name).upload(
                        storage_path,
                        bytes(merged_data)
                    )
                    audio_url = f"{client.supabase_url}/storage/v1/object/public/{bucket_name}/{storage_path}"

                logger.info(f"合并音频上传到Supabase: {storage_path}")

            # 更新录音记录（按 track 写入对应字段）
            if track == 'mixed':
                recording.storage_url = audio_url
                recording.file_size_bytes = len(merged_data)
                recording.status = 'merged'
            else:
                recording.system_storage_url = audio_url
                # system 轨完成不影响主状态机
            db.session.commit()

            logger.info(f"音频合并完成: recording_id={recording_id}, size={len(merged_data)}, storage={storage_type}")

            return {
                'success': True,
                'audio_url': audio_url,
                'file_size': len(merged_data),
                'storage_type': storage_type
            }

        except Exception as e:
            logger.error(f"合并音频分块失败: {e}")
            return {'success': False, 'error': str(e)}

    # ============ Whisper 转录服务 ============

    @classmethod
    def transcribe_audio(cls, recording_id: int) -> Dict:
        """
        使用 OpenAI Whisper 转录音频（支持群晖WebDAV、Supabase、本地存储）

        Args:
            recording_id: 录音记录ID

        Returns:
            dict: {success: bool, transcript_id: int, text: str}
        """
        try:
            from app.models.meeting import MeetingRecording, MeetingTranscript
            from app import db

            recording = MeetingRecording.query.get(recording_id)
            if not recording:
                return {'success': False, 'error': '录音记录不存在'}

            if not recording.storage_url:
                return {'success': False, 'error': '音频文件不存在'}

            # 获取 OpenAI 客户端
            openai_client = cls.get_openai_client()
            if not openai_client:
                return {'success': False, 'error': 'OpenAI API 未配置'}

            # 更新状态
            recording.status = 'transcribing'
            db.session.commit()

            # 获取音频文件（根据存储类型）
            storage_type = getattr(recording, 'storage_type', None) or get_storage_type()

            if storage_type == 'synology':
                # 从群晖WebDAV下载
                webdav = get_webdav_client()
                audio_data = webdav.download_file(recording.storage_url)
                if not audio_data:
                    return {'success': False, 'error': '无法从群晖下载音频文件'}
                logger.info(f"从群晖下载音频文件: {recording.storage_url}")

            elif storage_type == 'local':
                # 本地文件
                from flask import current_app
                local_storage_root = current_app.config.get('LOCAL_STORAGE_ROOT', './storage')
                local_path = recording.storage_url.replace('/storage/', local_storage_root + '/')
                with open(local_path, 'rb') as audio_file:
                    audio_data = audio_file.read()
                logger.info(f"读取本地音频文件: {local_path}")

            else:
                # Supabase/云端文件
                from app.utils.supabase_client import get_supabase_client
                client = get_supabase_client()

                if client.use_local_storage:
                    local_path = recording.storage_url.replace('/storage/', client.local_storage_root + '/')
                    with open(local_path, 'rb') as audio_file:
                        audio_data = audio_file.read()
                else:
                    import requests
                    response = requests.get(recording.storage_url)
                    if response.status_code != 200:
                        return {'success': False, 'error': '无法下载音频文件'}
                    audio_data = response.content
                logger.info(f"从Supabase下载音频文件: {recording.storage_url}")

            # 调用 Whisper API
            logger.info(f"开始转录: recording_id={recording_id}")

            # 创建临时文件用于 Whisper API
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_file_path = tmp_file.name

            try:
                with open(tmp_file_path, 'rb') as audio_file:
                    # 使用详细转录模式获取时间戳
                    transcript_response = openai_client.audio.transcriptions.create(
                        model=cls.WHISPER_MODEL,
                        file=audio_file,
                        language=cls.WHISPER_LANGUAGE,
                        response_format='verbose_json',
                        timestamp_granularities=['segment']
                    )
            finally:
                # 清理临时文件
                os.unlink(tmp_file_path)

            # 解析转录结果
            full_text = transcript_response.text
            segments = []

            if hasattr(transcript_response, 'segments'):
                from app.views.meeting import _is_hallucinated_segment
                for seg in transcript_response.segments:
                    text = seg.text or ''
                    if _is_hallucinated_segment(text):
                        logger.info(f"过滤 hallucination 段: {text[:50]!r}")
                        continue
                    segments.append({
                        'start': seg.start,
                        'end': seg.end,
                        'text': text,
                        'speaker': None  # 稍后通过说话人识别填充
                    })

            # 创建转录记录
            transcript = MeetingTranscript(
                recording_id=recording_id,
                full_text=full_text,
                segments=segments,
                language=cls.WHISPER_LANGUAGE,
                whisper_model=cls.WHISPER_MODEL,
                status='completed',
                transcribed_at=datetime.utcnow()
            )
            db.session.add(transcript)

            # 更新录音状态
            recording.status = 'transcribed'

            db.session.commit()

            logger.info(f"转录完成: recording_id={recording_id}, segments={len(segments)}")

            return {
                'success': True,
                'transcript_id': transcript.id,
                'text': full_text,
                'segments_count': len(segments)
            }

        except Exception as e:
            logger.error(f"转录失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

            # 更新状态为失败
            try:
                recording = MeetingRecording.query.get(recording_id)
                if recording:
                    recording.status = 'transcription_failed'
                    recording.error_message = str(e)
                    db.session.commit()
            except:
                pass

            return {'success': False, 'error': str(e)}

    # ============ 说话人分离服务（简化版） ============

    @classmethod
    def identify_speakers(cls, transcript_id: int, num_speakers: int = None) -> Dict:
        """
        识别说话人（简化版：基于语义分析）

        由于 Pyannote 需要复杂配置，这里使用基于 AI 的简化方案：
        1. 分析转录文本的说话模式
        2. 识别可能的说话人切换点
        3. 用户手动确认映射

        Args:
            transcript_id: 转录记录ID
            num_speakers: 预估说话人数量

        Returns:
            dict: {success: bool, speakers: list}
        """
        try:
            from app.models.meeting import MeetingTranscript, MeetingSpeaker
            from app import db

            transcript = MeetingTranscript.query.get(transcript_id)
            if not transcript:
                return {'success': False, 'error': '转录记录不存在'}

            segments = transcript.segments or []
            if not segments:
                return {'success': False, 'error': '没有转录片段'}

            # 使用 AI 分析说话人
            config = cls.get_ai_provider_config()
            if not config['api_key']:
                # 如果没有 AI，使用简单的启发式方法
                speakers = cls._heuristic_speaker_detection(segments)
            else:
                speakers = cls._ai_speaker_detection(segments, num_speakers, config)

            # 保存说话人信息
            for speaker_data in speakers:
                speaker = MeetingSpeaker(
                    transcript_id=transcript_id,
                    speaker_label=speaker_data['label'],
                    sample_text=speaker_data.get('sample_text', ''),
                    segments_count=speaker_data.get('segments_count', 0)
                )
                db.session.add(speaker)

            transcript.speakers_identified = True
            db.session.commit()

            return {
                'success': True,
                'speakers': speakers,
                'speakers_count': len(speakers)
            }

        except Exception as e:
            logger.error(f"说话人识别失败: {e}")
            return {'success': False, 'error': str(e)}

    @classmethod
    def _heuristic_speaker_detection(cls, segments: List[Dict]) -> List[Dict]:
        """
        启发式说话人检测
        基于停顿时间和语句模式识别可能的说话人切换
        """
        speakers = []
        current_speaker = 1
        speaker_segments = {1: []}

        prev_end = 0
        for i, seg in enumerate(segments):
            start = seg.get('start', 0)

            # 如果停顿超过2秒，可能是说话人切换
            if start - prev_end > 2.0 and i > 0:
                current_speaker = (current_speaker % 3) + 1  # 假设最多3个说话人
                if current_speaker not in speaker_segments:
                    speaker_segments[current_speaker] = []

            speaker_segments[current_speaker].append(seg)
            seg['speaker'] = f"说话人 {current_speaker}"
            prev_end = seg.get('end', start)

        # 构建说话人信息
        for speaker_id, segs in speaker_segments.items():
            if segs:
                speakers.append({
                    'label': f"说话人 {speaker_id}",
                    'sample_text': segs[0].get('text', '')[:100],
                    'segments_count': len(segs)
                })

        return speakers

    @classmethod
    def _ai_speaker_detection(cls, segments: List[Dict],
                              num_speakers: int, config: Dict) -> List[Dict]:
        """
        使用 AI 分析说话人模式
        """
        # 构建提示
        text_sample = '\n'.join([
            f"[{seg.get('start', 0):.1f}s] {seg.get('text', '')}"
            for seg in segments[:30]  # 取前30个片段
        ])

        prompt = f"""分析以下会议转录文本，识别不同的说话人。

转录片段（带时间戳）：
{text_sample}

请识别：
1. 大约有多少个不同的说话人
2. 每个说话人的典型发言特征
3. 每个说话人的代表性发言

以 JSON 格式返回：
{{
  "speakers": [
    {{"label": "说话人 1", "characteristics": "特征描述", "sample_text": "代表性发言"}}
  ]
}}"""

        try:
            if config['provider'] == 'openai':
                openai_client = cls.get_openai_client()
                response = openai_client.chat.completions.create(
                    model=config['model'],
                    messages=[
                        {"role": "system", "content": "你是一个会议分析助手，擅长识别不同说话人的发言模式。"},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                result = json.loads(response.choices[0].message.content)
                return result.get('speakers', [])
            else:
                # Anthropic Claude — 走 ANTHROPIC_BASE_URL 代理
                # ❗OAuth 代理对 Sonnet/Opus 强制要求 system[0] 是 Claude Code 身份串
                import anthropic
                client = anthropic.Anthropic(
                    api_key=config['api_key'],
                    base_url=os.environ.get('ANTHROPIC_BASE_URL') or None,
                )
                response = client.messages.create(
                    model=config['model'],
                    max_tokens=1000,
                    system=[
                        {'type': 'text', 'text': "You are Claude Code, Anthropic's official CLI for Claude."},
                        {'type': 'text', 'text': '你是说话人分析助手，基于会议转录段落判断每位说话人的身份特征。输出 JSON。'},
                    ],
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                # 解析响应
                content = response.content[0].text
                result = json.loads(content)
                return result.get('speakers', [])

        except Exception as e:
            logger.error(f"AI 说话人分析失败: {e}")
            return cls._heuristic_speaker_detection(segments)

    # ============ AI 纪要生成服务 ============

    @classmethod
    def generate_minutes(cls, recording_id: int,
                        style: str = 'standard',
                        force: bool = False) -> Dict:
        """
        使用 AI 生成会议纪要

        Args:
            recording_id: 录音记录ID
            style: 纪要风格 ('standard', 'detailed', 'brief')
            force: True 时即使已有 minutes 也覆盖；False 时已有则跳过

        Returns:
            dict: {success: bool, minutes_id: int, content: dict}
        """
        try:
            from app.models.meeting import (
                MeetingRecording, MeetingTranscript,
                MeetingMinutes, MeetingActionItem
            )
            from app import db

            recording = MeetingRecording.query.get(recording_id)
            if not recording:
                return {'success': False, 'error': '录音记录不存在'}

            # 已有 minutes：force=True 删除旧的，否则直接返回
            existing = MeetingMinutes.query.filter_by(recording_id=recording_id).first()
            if existing:
                if not force:
                    return {'success': True, 'minutes_id': existing.id, 'message': '纪要已存在'}
                # force：删旧的（cascade 自动删 action_items）
                old_version = existing.version or 1
                db.session.delete(existing)
                db.session.flush()
            else:
                old_version = 0

            # 获取转录文本
            transcript = MeetingTranscript.query.filter_by(
                recording_id=recording_id
            ).order_by(MeetingTranscript.id.desc()).first()

            if not transcript:
                return {'success': False, 'error': '转录记录不存在'}

            # 获取 AI 配置
            config = cls.get_ai_provider_config()
            if not config['api_key']:
                return {'success': False, 'error': 'AI 服务未配置'}

            # 构建纪要生成提示：用带时间戳的 transcript（每段开头 [mm:ss]）
            # 这样 AI 切 chapters 时能引用真实时间，不会偷懒按等分平均切
            full_text = cls._build_timestamped_transcript(transcript) or transcript.full_text or ''

            prompt = cls._build_minutes_prompt(full_text, style, recording)

            # 调用 AI 生成纪要
            logger.info(f"开始生成纪要: recording_id={recording_id}, style={style}")

            try:
                minutes_content = cls._call_ai_for_minutes(prompt, config)
            except Exception as e:
                logger.error(f"AI 调用失败: {e}")
                return {'success': False, 'error': f'AI 生成失败: {str(e)}'}

            # 创建纪要记录
            # ❗严格按 MeetingMinutes 模型字段：content/ai_model/generated_at 都没有这些列；
            #   generation_style 应该是 generation_mode；owner_id 是 nullable=False 必传
            minutes = MeetingMinutes(
                recording_id=recording_id,
                owner_id=recording.owner_id,
                title=minutes_content.get('title', recording.title or '会议纪要'),
                summary=minutes_content.get('summary', ''),
                key_points=minutes_content.get('key_points', []),
                decisions=minutes_content.get('decisions', []),
                chapters=minutes_content.get('chapters', []),
                key_quotes=minutes_content.get('key_quotes', []),
                highlights=minutes_content.get('highlights', []),
                generation_mode=style,
                status='draft',
                version=old_version + 1,
            )
            db.session.add(minutes)
            db.session.flush()  # 获取 minutes.id

            # 创建行动项
            # ❗model 没有 due_date_text 和 priority 字段；due_date 是 DateTime 但 AI 返回的是自然语言
            #   → 把这些信息合并到 description 里
            action_items = minutes_content.get('action_items', [])
            for item in action_items:
                desc_parts = []
                base_desc = item.get('description', '').strip()
                if base_desc:
                    desc_parts.append(base_desc)
                if item.get('due_date'):
                    desc_parts.append(f"截止：{item.get('due_date')}")
                if item.get('priority'):
                    desc_parts.append(f"优先级：{item.get('priority')}")
                action = MeetingActionItem(
                    minutes_id=minutes.id,
                    title=item.get('title', '')[:500],
                    description=' · '.join(desc_parts),
                    assignee_name=item.get('assignee', '')[:100],
                )
                db.session.add(action)

            # 更新录音状态
            recording.status = 'minutes_generated'

            # 把 AI 总结的标题同步到 recording.title（覆盖默认机械名）
            # 默认名格式：'2026-XX-XX HH:MM 会议录音' / '会议录音' / 空
            ai_title = (minutes_content.get('title') or '').strip()
            cur_title = (recording.title or '').strip()
            import re as _re
            is_default = (
                not cur_title
                or cur_title == '会议录音'
                or _re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}.*会议录音$', cur_title)
            )
            if ai_title and is_default and ai_title != cur_title:
                recording.title = ai_title[:200]
                logger.info(f"recording {recording_id} title 自动更新为: {ai_title}")

            db.session.commit()

            logger.info(f"纪要生成完成: recording_id={recording_id}, minutes_id={minutes.id}")

            # AI 文本推测说话人（基于 transcript 上下文 + 已知参会人员）
            # 不阻塞返回，失败也不影响纪要
            try:
                cls._infer_speaker_mapping(recording_id, transcript, minutes_content, config)
            except Exception as e:
                logger.warning(f"AI 推测说话人失败: {e}")

            return {
                'success': True,
                'minutes_id': minutes.id,
                'title': minutes.title,
                'summary': minutes.summary,
                'action_items_count': len(action_items)
            }

        except Exception as e:
            logger.error(f"生成纪要失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'success': False, 'error': str(e)}

    @classmethod
    def _build_timestamped_transcript(cls, transcript) -> str:
        """
        把 transcript.segments 拼成带时间戳的文本，每段：
            [mm:ss] 说话人: 原文
        让 AI 切 chapters 时引用真实时间，避免按等分平均切。
        """
        segs = transcript.segments if transcript else None
        if not segs:
            return ''

        lines = []
        for s in segs:
            text = (s.get('text') or '').strip()
            if not text:
                continue
            # 优先用 start_time（精确），fallback 用顺序
            start_sec = s.get('start_time')
            if not isinstance(start_sec, (int, float)):
                continue
            mm = int(start_sec) // 60
            ss = int(start_sec) % 60
            ts_str = f'{mm:02d}:{ss:02d}'
            speaker_label = s.get('speaker_display') or s.get('speaker') or '?'
            if speaker_label == 'me':
                speaker_label = '我'
            elif speaker_label == 'peer':
                speaker_label = '对方'
            lines.append(f'[{ts_str}] {speaker_label}: {text}')

        return '\n'.join(lines)

    @classmethod
    def _build_minutes_prompt(cls, transcript: str, style: str,
                             recording) -> str:
        """构建纪要生成的 AI 提示"""

        style_instructions = {
            'standard': '生成标准格式的会议纪要，包含摘要、关键要点、决策事项和行动项。',
            'detailed': '生成详细的会议纪要，保留更多讨论细节和背景信息。',
            'brief': '生成简洁的会议纪要，仅保留核心决策和关键行动项。'
        }

        prompt = f"""你是一个专业的会议纪要助手。请根据以下会议转录内容生成结构化的会议纪要。

{style_instructions.get(style, style_instructions['standard'])}

**会议信息**：
- 会议标题：{recording.title or '未命名会议'}
- 录音时长：{recording.duration_seconds or 0} 秒

**转录内容**：
{transcript[:80000]}
{' [内容已截断...]' if len(transcript) > 80000 else ''}

**过滤规则**（请在生成纪要时应用）：
1. 删除口语填充词（嗯、啊、那个、就是说等）
2. 合并重复表达的内容
3. 过滤无效对话（如"听得到吗"、"网络卡了"等）
4. 过滤与会议主题无关的闲聊
5. 提炼冗长描述为简洁要点

**请以 JSON 格式返回**：
{{
    "title": "8-20 字的会议主题（必须基于实际讨论内容总结，不要返回'会议纪要'/'2026-XX-XX 会议录音'/'未命名会议'这种机械名；好例子：'阳刚 4G 平台合作进展评估'/'Q3 跨语种产品路线讨论'/'供应商心跳机延期对策'）",
    "summary": "2-3句话的会议摘要",
    "key_points": [
        "关键要点1",
        "关键要点2"
    ],
    "decisions": [
        "决策事项1",
        "决策事项2"
    ],
    "action_items": [
        {{
            "title": "任务标题",
            "description": "任务描述",
            "assignee": "负责人姓名",
            "due_date": "截止日期（如：下周五）",
            "priority": "high/medium/low"
        }}
    ],
    "chapters": [
        {{
            "t": "00:00",
            "title": "章节标题（短，6-12 字）",
            "summary": "1 句话章节摘要",
            "speakers": ["发言人姓名1", "发言人姓名2"]
        }}
    ],
    "key_quotes": [
        {{
            "speaker": "发言人姓名",
            "text": "原话引用（直接抄会议中说的话，不要改写、不要总结）",
            "ts": "00:42",
            "category": "决策/愿景/判断/风险/承诺"
        }}
    ],
    "highlights": [
        "跨语种",
        "浮窗形态",
        "贴片产能",
        "Q3 灰度"
    ],
    "discussion_topics": [
        {{
            "topic": "讨论主题",
            "summary": "讨论摘要",
            "conclusion": "结论"
        }}
    ]
}}

**chapters 要求**（严格遵守）：
1. 必须根据**话题真正发生转折的位置**切——一个话题就是一段，长短不限（短的 2 分钟、长的 20 分钟都可以）
2. **t 必须从 transcript 里实际出现的 [mm:ss] 时间戳里挑**，不要自己编、不要按等分平均切
3. 不要按"15 分钟"、"半小时"这种整数间隔切——这是偷懒
4. 章节数量 3-7 个；如果会议主题集中只有 2 个话题就只切 2 个，多就最多 7 个
5. title 必须是 6-12 字的具体话题名（如"贴片产能问题"），不要写"开场介绍"、"总结"这种通用名

**key_quotes 要求**：抽 2-5 句最有价值的"原话"，必须是有判断、决策、承诺、洞察的句子；不要抽日常闲聊或废话；text 必须忠实于原文（可省略口语填充但不重写）；如果没有真正值得抽的金句，返回空数组

**highlights 要求（重要）**：抽 8-15 个**3-12 字**的"高光短语"，是会议中反复出现 / 关键决定 / 专业术语 / 人名地名等。
1. 必须是 transcript 里**实际出现的字眼**（不能改写、不能加字）
2. 长度严格控制在 3-12 字（绝不要整句话！）
3. 用于段落里黄色 mark 高亮，所以要短才能视觉清晰
4. 好例子：'跨语种'、'浮窗形态'、'贴片产能'、'阳刚 4G 平台'、'下周三前'
5. 坏例子：'我们要做的不是又一个会议总结工具'（太长，这是金句不是 highlight）/ '会议'（太通用）
"""

        return prompt

    @classmethod
    def _call_ai_for_minutes(cls, prompt: str, config: Dict) -> Dict:
        """调用 AI 生成纪要内容"""

        if config['provider'] == 'openai':
            openai_client = cls.get_openai_client()
            response = openai_client.chat.completions.create(
                model=config['model'],
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的会议纪要助手，擅长从会议录音转录中提取关键信息并生成结构化纪要。请始终返回有效的 JSON 格式。"
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=4000
            )
            return json.loads(response.choices[0].message.content)

        else:
            # Anthropic Claude — 走 ANTHROPIC_BASE_URL 代理（智能终端/聊天翻译同款配置）
            # ❗OAuth 代理对 Sonnet/Opus 强制要求 system[0] 是 Claude Code 身份串，否则伪 429
            import anthropic
            client = anthropic.Anthropic(
                api_key=config['api_key'],
                base_url=os.environ.get('ANTHROPIC_BASE_URL') or None,
            )
            response = client.messages.create(
                model=config['model'],
                max_tokens=4000,
                system=[
                    {'type': 'text', 'text': "You are Claude Code, Anthropic's official CLI for Claude."},
                    {'type': 'text', 'text': '你是一个专业的会议纪要助手，擅长从会议录音转录中提取关键信息并生成结构化纪要。请始终返回有效的 JSON 格式。'},
                ],
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.content[0].text

            # 尝试提取 JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 尝试从文本中提取 JSON
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    return json.loads(json_match.group())
                raise ValueError("无法解析 AI 响应为 JSON")

    @classmethod
    def _infer_speaker_mapping(cls, recording_id: int, transcript, minutes_content: dict, config: dict) -> None:
        """
        让 AI 看完整 transcript + 参会人员（来自 minutes_content.action_items / chapters / decisions 里
        提到的人名），输出 SPEAKER_N → 真名的推测 mapping，应用到 segments.speaker_display。

        失败、低置信度、找不到都跳过 — segments 保持原 SPEAKER_N（用户可在前端 modal 手动改）。
        """
        from app.models.meeting import MeetingTranscript
        from app import db

        # 收集 transcript 里出现的 SPEAKER_N
        segs = list(transcript.segments or [])
        speaker_keys = set()
        for s in segs:
            sp = s.get('speaker') or ''
            if sp.startswith('SPEAKER_'):
                speaker_keys.add(sp)
        if not speaker_keys:
            logger.info(f"[infer_speaker] recording={recording_id} 无 SPEAKER_N，跳过")
            return

        # 收集候选人名（从 AI 已生成内容里抽）
        candidates = set()
        for ai in minutes_content.get('action_items', []) or []:
            n = (ai.get('assignee') or '').strip()
            if n: candidates.add(n)
        for ch in minutes_content.get('chapters', []) or []:
            for n in ch.get('speakers', []) or []:
                if n: candidates.add(n.strip())
        for q in minutes_content.get('key_quotes', []) or []:
            n = (q.get('speaker') or '').strip()
            if n: candidates.add(n)

        if not candidates:
            logger.info(f"[infer_speaker] recording={recording_id} AI 内容里没提到任何人名，跳过")
            return

        # 构造 prompt：让 AI 看 transcript 的小样本（每个 SPEAKER 取前 3 段示例）
        examples = {sp: [] for sp in speaker_keys}
        for s in segs:
            sp = s.get('speaker', '')
            if sp in examples and len(examples[sp]) < 3:
                examples[sp].append(s.get('text', '')[:120])

        examples_str = '\n'.join(
            f"  {sp}: \"{' / '.join(texts)}\""
            for sp, texts in examples.items()
        )
        candidates_str = '、'.join(sorted(candidates))

        prompt = f"""根据下面的会议转录片段，推测每位 SPEAKER 对应的真实姓名。

【可能的参会人员】
{candidates_str}

【每位 SPEAKER 的发言片段】
{examples_str}

【判断依据】
- 看发言里有没有直呼对方姓名（"@张三 你来跟进"→ 下一段大概率是张三）
- 看自我介绍（"我是 X 部门的小王"）
- 看口吻、语气、专业领域是否匹配
- confidence 严格反映你的把握：0.9+ = 强证据多处指向；0.7-0.9 = 推测合理；< 0.6 别写

【返回 JSON】
{{
    "mapping": {{
        "SPEAKER_00": {{"name": "真名（必须来自上面的候选人名单）", "confidence": 0.92}},
        "SPEAKER_01": {{"name": "...", "confidence": 0.75}}
    }}
}}
若完全无法判断，返回 {{"mapping": {{}}}}。"""

        try:
            ai_resp = cls._call_ai_for_minutes(prompt, config)
            raw_mapping = (ai_resp or {}).get('mapping') or {}
            # 兼容：旧格式 {SPEAKER_00: "张三"} 或新 {SPEAKER_00: {name, confidence}}
            mapping = {}
            for k, v in raw_mapping.items():
                if not k.startswith('SPEAKER_'):
                    continue
                if isinstance(v, dict):
                    name = (v.get('name') or '').strip()
                    conf = float(v.get('confidence') or 0)
                else:
                    name = str(v).strip()
                    conf = 0.7  # 旧格式没置信度，给个中等值
                if name and name in candidates and conf >= 0.6:
                    mapping[k] = {'name': name, 'confidence': round(conf, 2)}

            if not mapping:
                logger.info(f"[infer_speaker] recording={recording_id} AI 给出空/低置信 mapping，跳过")
                return

            # ❗JSON 字段必须重新构造 list of NEW dicts（in-place mutation 不被 SQLAlchemy 追踪）
            new_segs = []
            for s in segs:
                new_s = dict(s)
                sp = new_s.get('speaker')
                if sp in mapping:
                    new_s['speaker_display'] = mapping[sp]['name']
                    new_s['speaker_display_confidence'] = mapping[sp]['confidence']
                    new_s['speaker_display_source'] = 'ai_infer'
                new_segs.append(new_s)
            transcript.segments = new_segs
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(transcript, 'segments')
            db.session.commit()
            logger.info(f"[infer_speaker] recording={recording_id} 应用 mapping: {mapping}")
        except Exception as e:
            db.session.rollback()
            logger.warning(f"[infer_speaker] recording={recording_id} 失败: {e}")

    # ============ 辅助方法 ============

    @classmethod
    def get_recording_status(cls, recording_id: int) -> Dict:
        """获取录音处理状态"""
        try:
            from app.models.meeting import MeetingRecording, MeetingTranscript, MeetingMinutes

            recording = MeetingRecording.query.get(recording_id)
            if not recording:
                return {'success': False, 'error': '录音不存在'}

            transcript = MeetingTranscript.query.filter_by(
                recording_id=recording_id
            ).first()

            minutes = MeetingMinutes.query.filter_by(
                recording_id=recording_id
            ).first()

            return {
                'success': True,
                'recording': {
                    'id': recording.id,
                    'status': recording.status,
                    'duration': recording.duration_seconds,
                    'has_audio': bool(recording.storage_url)
                },
                'transcript': {
                    'exists': transcript is not None,
                    'status': transcript.status if transcript else None,
                    'speakers_identified': transcript.speakers_identified if transcript else False
                } if transcript else None,
                'minutes': {
                    'exists': minutes is not None,
                    'status': minutes.status if minutes else None,
                    'version': minutes.version if minutes else None
                } if minutes else None
            }

        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            return {'success': False, 'error': str(e)}

    @classmethod
    def fix_transcript_with_vocab(cls, recording_id: int) -> Dict:
        """用 Claude 对完整转录段做"专有名词二次纠错"。
        典型场景：Whisper 把"倪捷"识别成"你姐"——这里拿 PMA 参会人 real_name
        作为字典，让 Claude 严格只替换同音/形近字，其他文本逐字保留。

        策略：一次最多送 80 段；超出分批跑。失败/超时 → 跳过（不阻塞纪要生成）。
        """
        from app.models.meeting import MeetingRecording, MeetingTranscript
        from app.models.user import User as _User
        from app import db
        from sqlalchemy.orm.attributes import flag_modified

        recording = MeetingRecording.query.get(recording_id)
        if not recording:
            return {'success': False, 'error': '录音不存在'}

        transcript = MeetingTranscript.query.filter_by(recording_id=recording_id).first()
        if not transcript or not transcript.segments:
            return {'success': False, 'error': '无 segments 可纠错'}

        # 收集 vocab（owner + invited）
        names = []
        if recording.owner and recording.owner.real_name:
            names.append(recording.owner.real_name)
        for uid in (recording.invited_user_ids or []):
            u = _User.query.get(uid)
            if u and u.real_name and u.real_name not in names:
                names.append(u.real_name)
        if not names:
            return {'success': True, 'fixed': 0, 'skipped': 'no_vocab'}

        vocab_str = '、'.join(names)
        segs = list(transcript.segments or [])
        total = len(segs)
        if total == 0:
            return {'success': True, 'fixed': 0}

        try:
            import anthropic
            client = anthropic.Anthropic(
                api_key=os.environ.get('ANTHROPIC_API_KEY') or 'sk-ant-placeholder',
                base_url=os.environ.get('ANTHROPIC_BASE_URL') or None,
            )
        except Exception as e:
            logger.warning(f"Claude client 初始化失败: {e}")
            return {'success': False, 'error': str(e)}

        BATCH = 80
        fixed_count = 0
        for i in range(0, total, BATCH):
            batch = segs[i:i + BATCH]
            # 只把 idx/text/translation 送上去（其他字段不需要 Claude 看）
            payload = [
                {'i': j, 'text': (s.get('text') or ''), 'translation': (s.get('translation') or '')}
                for j, s in enumerate(batch)
            ]
            sys_text = (
                "你是会议转录的专有名词校对员。严格规则：\n"
                "1. 只把与下列姓名【读音相近 / 字形相近】的同音/形近错字替换为正确姓名\n"
                "2. 不修改任何其他文字：标点、口语填充词、语序、断句、错别字（非姓名类）全部原样保留\n"
                "3. text 和 translation 都按上述规则校对\n"
                "4. 输出必须是 JSON 数组，结构与输入完全一致（含 i 字段），只修改 text/translation 内容\n"
                "5. 没有任何姓名需要校对时，原样返回输入\n"
                f"参会人姓名列表：{vocab_str}"
            )
            user_msg = (
                "输入 segments（JSON）：\n```json\n"
                + json.dumps(payload, ensure_ascii=False)
                + "\n```\n\n输出修正后的 JSON 数组，不要任何解释或 markdown 代码块包裹。"
            )
            try:
                resp = client.messages.create(
                    model='claude-haiku-4-5-20251001',
                    max_tokens=8000,
                    system=[
                        {'type': 'text', 'text': "You are Claude Code, Anthropic's official CLI for Claude."},
                        {'type': 'text', 'text': sys_text},
                    ],
                    messages=[{'role': 'user', 'content': user_msg}],
                )
                raw = (resp.content[0].text or '').strip()
                # 容错剥离 ```json ... ```
                if raw.startswith('```'):
                    raw = raw.split('```', 2)[1]
                    if raw.startswith('json'):
                        raw = raw[4:]
                    raw = raw.rsplit('```', 1)[0].strip()
                fixed = json.loads(raw)
                if not isinstance(fixed, list):
                    continue
                for item in fixed:
                    j = item.get('i')
                    if not isinstance(j, int) or j < 0 or j >= len(batch):
                        continue
                    orig_text = batch[j].get('text') or ''
                    orig_tran = batch[j].get('translation') or ''
                    new_text = item.get('text') or orig_text
                    new_tran = item.get('translation') or orig_tran
                    if new_text != orig_text or new_tran != orig_tran:
                        # 写回 segs（注意 batch 是 segs 的切片，需要回到全局 index）
                        seg_idx = i + j
                        new_seg = dict(segs[seg_idx])
                        new_seg['text'] = new_text
                        new_seg['translation'] = new_tran
                        segs[seg_idx] = new_seg
                        fixed_count += 1
            except Exception as e:
                logger.warning(f"[fix-transcript] batch i={i} 失败: {e}")
                continue

        if fixed_count > 0:
            transcript.segments = segs
            flag_modified(transcript, 'segments')
            db.session.commit()
            logger.info(f"[fix-transcript] recording={recording_id} 共修正 {fixed_count} 段")

        return {'success': True, 'fixed': fixed_count, 'total': total}

    @classmethod
    def validate_api_configuration(cls) -> Dict:
        """验证 API 配置状态"""
        # 检查群晖WebDAV配置
        synology_configured = bool(
            os.environ.get('SYNOLOGY_WEBDAV_URL') and
            os.environ.get('SYNOLOGY_WEBDAV_USER') and
            os.environ.get('SYNOLOGY_WEBDAV_PASSWORD')
        )

        result = {
            'openai': {
                'configured': bool(os.environ.get('OPENAI_API_KEY')),
                'features': ['whisper_transcription', 'gpt_minutes']
            },
            'anthropic': {
                'configured': bool(os.environ.get('ANTHROPIC_API_KEY')),
                'features': ['claude_minutes']
            },
            'supabase': {
                'configured': bool(os.environ.get('SUPABASE_URL') and os.environ.get('SUPABASE_KEY')),
                'features': ['audio_storage']
            },
            'synology': {
                'configured': synology_configured,
                'features': ['audio_storage'],
                'storage_type': 'webdav'
            }
        }

        # 当前存储类型
        storage_type = get_storage_type()
        result['current_storage'] = storage_type

        # 存储是否可用（根据当前存储类型检查）
        storage_ready = False
        if storage_type == 'synology':
            storage_ready = synology_configured
        elif storage_type == 'supabase':
            storage_ready = result['supabase']['configured']
        elif storage_type == 'local':
            storage_ready = True  # 本地存储始终可用

        result['storage_ready'] = storage_ready

        result['all_configured'] = all([
            result['openai']['configured'],  # 必需（用于 Whisper）
            storage_ready  # 存储必须可用
        ])

        result['minutes_ready'] = (
            result['openai']['configured'] or
            result['anthropic']['configured']
        )

        return result
