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

        provider = os.environ.get('AI_PROVIDER', 'openai')  # 会议纪要默认用 OpenAI
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
                          chunk_index: int, is_final: bool = False) -> Dict:
        """
        上传音频分块到存储（支持群晖WebDAV、Supabase、本地存储）

        Args:
            recording_id: 录音记录ID
            chunk_data: 音频分块数据
            chunk_index: 分块索引
            is_final: 是否为最后一个分块

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

            # 生成分块文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            chunk_filename = f"chunk_{chunk_index:04d}_{timestamp}.webm"

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
            if not recording.audio_chunks:
                recording.audio_chunks = []
            recording.audio_chunks.append({
                'index': chunk_index,
                'path': chunk_url,
                'storage_type': storage_type,
                'size': len(chunk_data),
                'uploaded_at': datetime.utcnow().isoformat()
            })

            if is_final:
                recording.status = 'uploaded'
                recording.upload_completed_at = datetime.utcnow()

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
    def merge_audio_chunks(cls, recording_id: int) -> Dict:
        """
        合并音频分块为完整文件（支持群晖WebDAV、Supabase、本地存储）

        Args:
            recording_id: 录音记录ID

        Returns:
            dict: {success: bool, audio_url: str, duration: int}
        """
        try:
            from app.models.meeting import MeetingRecording
            from app import db

            recording = MeetingRecording.query.get(recording_id)
            if not recording:
                return {'success': False, 'error': '录音记录不存在'}

            if not recording.audio_chunks:
                return {'success': False, 'error': '没有音频分块数据'}

            # 按索引排序分块
            sorted_chunks = sorted(recording.audio_chunks, key=lambda x: x['index'])
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
            merged_filename = f"recording_{recording_id}_{timestamp}.webm"

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

            # 更新录音记录
            recording.audio_url = audio_url
            recording.storage_type = storage_type
            recording.file_size = len(merged_data)
            recording.status = 'merged'
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

            if not recording.audio_url:
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
                audio_data = webdav.download_file(recording.audio_url)
                if not audio_data:
                    return {'success': False, 'error': '无法从群晖下载音频文件'}
                logger.info(f"从群晖下载音频文件: {recording.audio_url}")

            elif storage_type == 'local':
                # 本地文件
                from flask import current_app
                local_storage_root = current_app.config.get('LOCAL_STORAGE_ROOT', './storage')
                local_path = recording.audio_url.replace('/storage/', local_storage_root + '/')
                with open(local_path, 'rb') as audio_file:
                    audio_data = audio_file.read()
                logger.info(f"读取本地音频文件: {local_path}")

            else:
                # Supabase/云端文件
                from app.utils.supabase_client import get_supabase_client
                client = get_supabase_client()

                if client.use_local_storage:
                    local_path = recording.audio_url.replace('/storage/', client.local_storage_root + '/')
                    with open(local_path, 'rb') as audio_file:
                        audio_data = audio_file.read()
                else:
                    import requests
                    response = requests.get(recording.audio_url)
                    if response.status_code != 200:
                        return {'success': False, 'error': '无法下载音频文件'}
                    audio_data = response.content
                logger.info(f"从Supabase下载音频文件: {recording.audio_url}")

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
                for seg in transcript_response.segments:
                    segments.append({
                        'start': seg.start,
                        'end': seg.end,
                        'text': seg.text,
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
            recording.transcription_completed_at = datetime.utcnow()

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
                # Anthropic Claude
                import anthropic
                client = anthropic.Anthropic(api_key=config['api_key'])
                response = client.messages.create(
                    model=config['model'],
                    max_tokens=1000,
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
                        style: str = 'standard') -> Dict:
        """
        使用 AI 生成会议纪要

        Args:
            recording_id: 录音记录ID
            style: 纪要风格 ('standard', 'detailed', 'brief')

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

            # 构建纪要生成提示
            full_text = transcript.full_text or ''

            prompt = cls._build_minutes_prompt(full_text, style, recording)

            # 调用 AI 生成纪要
            logger.info(f"开始生成纪要: recording_id={recording_id}, style={style}")

            try:
                minutes_content = cls._call_ai_for_minutes(prompt, config)
            except Exception as e:
                logger.error(f"AI 调用失败: {e}")
                return {'success': False, 'error': f'AI 生成失败: {str(e)}'}

            # 创建纪要记录
            minutes = MeetingMinutes(
                recording_id=recording_id,
                title=minutes_content.get('title', recording.title or '会议纪要'),
                summary=minutes_content.get('summary', ''),
                key_points=minutes_content.get('key_points', []),
                decisions=minutes_content.get('decisions', []),
                content=minutes_content,
                ai_model=config['model'],
                generation_style=style,
                status='draft',
                version=1,
                generated_at=datetime.utcnow()
            )
            db.session.add(minutes)
            db.session.flush()  # 获取 minutes.id

            # 创建行动项
            action_items = minutes_content.get('action_items', [])
            for item in action_items:
                action = MeetingActionItem(
                    minutes_id=minutes.id,
                    title=item.get('title', ''),
                    description=item.get('description', ''),
                    assignee_name=item.get('assignee', ''),
                    due_date_text=item.get('due_date', ''),
                    priority=item.get('priority', 'medium')
                )
                db.session.add(action)

            # 更新录音状态
            recording.status = 'minutes_generated'

            db.session.commit()

            logger.info(f"纪要生成完成: recording_id={recording_id}, minutes_id={minutes.id}")

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
- 录音时长：{recording.duration or 0} 秒

**转录内容**：
{transcript[:15000]}
{' [内容已截断...]' if len(transcript) > 15000 else ''}

**过滤规则**（请在生成纪要时应用）：
1. 删除口语填充词（嗯、啊、那个、就是说等）
2. 合并重复表达的内容
3. 过滤无效对话（如"听得到吗"、"网络卡了"等）
4. 过滤与会议主题无关的闲聊
5. 提炼冗长描述为简洁要点

**请以 JSON 格式返回**：
{{
    "title": "会议标题（如原标题不明确请根据内容生成）",
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
    "discussion_topics": [
        {{
            "topic": "讨论主题",
            "summary": "讨论摘要",
            "conclusion": "结论"
        }}
    ]
}}"""

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
            # Anthropic Claude
            import anthropic
            client = anthropic.Anthropic(api_key=config['api_key'])
            response = client.messages.create(
                model=config['model'],
                max_tokens=4000,
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
                    'duration': recording.duration,
                    'has_audio': bool(recording.audio_url)
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
