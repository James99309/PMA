"""
声纹分离服务客户端

调用 Mac mini 上部署的 pyannote.audio FastAPI 服务，
拿到 [{start, end, speaker}] 后跟现有 MeetingTranscript.segments 时间对齐，
把每条 segment.speaker 从 'me'/'peer' 重写成 SPEAKER_00/01/02。

调用：
    DiarizationService.run_for_recording(recording_id)
"""
import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class DiarizationService:
    SERVICE_URL_ENV = 'PYANNOTE_SERVICE_URL'
    NAS_AUTH_ENV = 'PYANNOTE_NAS_AUTH'
    DEFAULT_TIMEOUT = 600  # 长会议推理可能要 5+ 分钟

    @classmethod
    def is_available(cls) -> bool:
        return bool(os.environ.get(cls.SERVICE_URL_ENV))

    @classmethod
    def _resolve_audio_path(cls, recording, track: str = 'mixed') -> Optional[str]:
        """
        把 recording.{storage_url|system_storage_url} 解析成本地文件系统路径。
        track='system' 优先用对方端独立轨（不含 mic），声纹分离结果就只代表"对方说话人"。
        """
        url = (recording.system_storage_url if track == 'system' else recording.storage_url) or ''
        if not url:
            return None
        # 远程 URL 直接返回（让 service 用旧的 /diarize 端点拉）
        if url.startswith('http://') or url.startswith('https://'):
            return None
        # 本地路径：尝试从 PMA 项目根找
        from flask import current_app
        candidates = []
        if url.startswith('/storage/'):
            candidates.append(os.path.join(current_app.root_path, '..', url.lstrip('/')))
            candidates.append(os.path.join(current_app.root_path, url.lstrip('/')))
        candidates.append(url)  # 万一本身就是绝对路径
        for c in candidates:
            ap = os.path.abspath(c)
            if os.path.exists(ap):
                return ap
        return None

    @classmethod
    def run_for_recording(cls, recording_id: int) -> dict:
        """
        对指定 recording 跑声纹分离，结果写回 transcript.segments。
        返回 {success, speaker_count, segments_updated, error?}
        """
        from app.models.meeting import MeetingRecording, MeetingTranscript
        from app import db

        service_url = os.environ.get(cls.SERVICE_URL_ENV)
        if not service_url:
            return {'success': False, 'error': f'{cls.SERVICE_URL_ENV} 未配置'}

        recording = MeetingRecording.query.get(recording_id)
        if not recording:
            return {'success': False, 'error': '录音不存在'}

        # 优先用 system 轨（只含对方端语音）做声纹分离，
        # 避免 mic 被识别为额外 SPEAKER_xx 与已知的 me 段错乱
        track = 'system' if recording.system_storage_url else 'mixed'

        target_url = recording.system_storage_url if track == 'system' else recording.storage_url
        if not target_url:
            return {'success': False, 'error': '录音文件 URL 缺失（chunks 未合并？）'}

        transcript = MeetingTranscript.query.filter_by(recording_id=recording_id).first()
        if not transcript or not transcript.segments:
            return {'success': False, 'error': 'transcript 没有 segments'}

        # 解析音频本地路径
        local_path = cls._resolve_audio_path(recording, track=track)

        try:
            if local_path:
                # 本地文件 → multipart 上传到 Mac mini（避开 URL 路径问题）
                logger.info(f'[diarize] recording={recording_id} multipart 上传 {local_path} → {service_url}/diarize-upload')
                with open(local_path, 'rb') as f:
                    files = {'audio': (os.path.basename(local_path), f, 'application/octet-stream')}
                    data = {'recording_id': str(recording_id)}
                    r = requests.post(
                        f'{service_url}/diarize-upload',
                        files=files, data=data,
                        timeout=cls.DEFAULT_TIMEOUT,
                    )
            else:
                # 远程 URL → 让 service 自己拉
                payload = {
                    'audio_url': target_url,
                    'recording_id': recording_id,
                }
                nas_auth = os.environ.get(cls.NAS_AUTH_ENV)
                if nas_auth:
                    payload['auth_basic'] = nas_auth
                logger.info(f'[diarize] recording={recording_id} URL 模式 {service_url}/diarize')
                r = requests.post(
                    f'{service_url}/diarize',
                    json=payload,
                    timeout=cls.DEFAULT_TIMEOUT,
                )

            if r.status_code != 200:
                return {'success': False, 'error': f'服务返回 {r.status_code}: {r.text[:300]}'}
            data = r.json()
            if not data.get('success'):
                return {'success': False, 'error': data.get('error', '推理失败')}
        except requests.RequestException as e:
            return {'success': False, 'error': f'调用失败: {e}'}

        diar_segments = data.get('segments', [])
        if not diar_segments:
            return {'success': False, 'error': 'pyannote 没有产出 segments'}

        # 跟 transcript.segments 时间对齐：每条 transcript segment 找它时间区间内占主导的 speaker
        updated = cls._align_speakers(transcript.segments, diar_segments)

        # JSON 字段必须重新赋值 + flag_modified 才会被 SQLAlchemy 标记 dirty
        transcript.segments = updated
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(transcript, 'segments')
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'db 写入失败: {e}'}

        return {
            'success': True,
            'speaker_count': data.get('speaker_count', 0),
            'segments_updated': len(updated),
            'duration_ms': data.get('duration_ms'),
        }

    @classmethod
    def _align_speakers(cls, transcript_segments: list, diar_segments: list) -> list:
        """
        把 pyannote 的 SPEAKER_N 标签按时间区间对齐回 transcript segments。

        transcript_segments[i] 应已通过 _normalize_segment_times 有 start_time/end_time，
        或至少有 start_time。如果缺，按顺序+5s 估算。

        策略：对每条 transcript segment 找它时间区间内"占主导"的 SPEAKER_N。
        重叠时长最长的赢。如果完全没重叠（极少见），保留原 speaker 标签。
        """
        # 先确保所有 transcript segment 有数值时间
        norm = cls._ensure_segment_times(transcript_segments)

        result = []
        for s in norm:
            new_s = dict(s)
            # me 段已知是当前用户，不参与声纹映射 — 保持 speaker='me' 原样
            # （system 轨的 pyannote 结果只代表对方端，me 区间不会有覆盖）
            if (s.get('speaker') or '').lower() == 'me':
                result.append(new_s)
                continue

            seg_start = s.get('start_time', 0.0)
            seg_end = s.get('end_time', seg_start + 5.0)

            # 找重叠的 diar segments
            best_speaker = None
            best_overlap = 0.0
            for d in diar_segments:
                overlap = max(0.0, min(seg_end, d['end']) - max(seg_start, d['start']))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = d['speaker']

            # 写回
            if best_speaker:
                if 'origin_speaker' not in new_s:
                    new_s['origin_speaker'] = new_s.get('speaker')
                new_s['speaker'] = best_speaker
            result.append(new_s)

        return result

    @classmethod
    def _ensure_segment_times(cls, segments: list) -> list:
        """如果 segments 缺 start_time/end_time，按 ts 或顺序估算补齐"""
        from datetime import datetime
        out = []
        base_ms = None
        # 找首个 ts 作基准
        for s in segments:
            if isinstance(s.get('ts'), str):
                try:
                    base_ms = datetime.fromisoformat(s['ts']).timestamp()
                    break
                except Exception:
                    pass

        for i, s in enumerate(segments):
            s = dict(s)
            if not isinstance(s.get('start_time'), (int, float)):
                if isinstance(s.get('ts'), str) and base_ms is not None:
                    try:
                        s['start_time'] = max(0.0, datetime.fromisoformat(s['ts']).timestamp() - base_ms)
                    except Exception:
                        s['start_time'] = i * 5.0
                else:
                    s['start_time'] = i * 5.0
            if not isinstance(s.get('end_time'), (int, float)):
                dur = s.get('duration_ms', 5000) / 1000 if isinstance(s.get('duration_ms'), (int, float)) else 5.0
                s['end_time'] = s['start_time'] + dur
            out.append(s)
        return out

    @classmethod
    def apply_speaker_mapping(cls, recording_id: int, mapping: dict) -> dict:
        """
        用户做完 SPEAKER_00=张三、SPEAKER_01=李四 mapping 后调这个，
        把 segments 里的 SPEAKER_N 关联真人（PMA 用户 / 外部嘉宾）。

        mapping 结构（每个值支持两种格式）：
          {
              'SPEAKER_00': {'user_id': 12, 'display_name': '张三'},  # PMA 用户
              'SPEAKER_01': {'external_name': '王老板'},               # 外部嘉宾
              'SPEAKER_02': '李四',                                    # 旧格式（仅字符串名字）
          }
        """
        from app.models.meeting import MeetingTranscript
        from app.models.user import User
        from app import db

        transcript = MeetingTranscript.query.filter_by(recording_id=recording_id).first()
        if not transcript or not transcript.segments:
            return {'success': False, 'error': 'transcript 没有 segments'}

        # 规范化 mapping
        # 接受所有 speaker key（SPEAKER_xx / me / peer / 其他）
        normalized = {}
        for sp, val in (mapping or {}).items():
            if not sp:
                continue
            if isinstance(val, dict):
                uid = val.get('user_id')
                ext = (val.get('external_name') or '').strip()
                disp = (val.get('display_name') or '').strip()
                if uid:
                    user = User.query.get(uid)
                    if user:
                        normalized[sp] = {
                            'user_id': uid,
                            'display_name': disp or user.real_name or user.username,
                            'source': 'user',
                        }
                elif ext:
                    normalized[sp] = {
                        'external_name': ext,
                        'display_name': ext,
                        'source': 'external',
                    }
            elif isinstance(val, str) and val.strip():
                normalized[sp] = {
                    'display_name': val.strip(),
                    'source': 'manual',
                }

        if not normalized:
            return {'success': False, 'error': '映射为空'}

        # ❗SQLAlchemy JSON 字段 in-place mutation 不被追踪，必须重新构造 list of NEW dicts
        new_segs = []
        applied = 0
        for s in (transcript.segments or []):
            new_s = dict(s)
            sp = new_s.get('speaker')
            if sp in normalized:
                # ❗先清掉所有 mapping 相关旧字段，否则从 user 改成 external（或反向）时
                # 旧的 speaker_user_id / speaker_external_name 会残留 → 数据错乱
                for k in ('speaker_display', 'speaker_display_source',
                          'speaker_display_confidence',
                          'speaker_user_id', 'speaker_external_name'):
                    new_s.pop(k, None)
                m = normalized[sp]
                new_s['speaker_display'] = m['display_name']
                new_s['speaker_display_source'] = m['source']
                new_s['speaker_display_confidence'] = 1.0
                if 'user_id' in m:
                    new_s['speaker_user_id'] = m['user_id']
                if 'external_name' in m:
                    new_s['speaker_external_name'] = m['external_name']
                applied += 1
            new_segs.append(new_s)

        transcript.segments = new_segs
        # 双保险：显式标记 dirty
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(transcript, 'segments')

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': f'db 写入失败: {e}'}

        return {'success': True, 'segments_updated': applied, 'mapping_count': len(normalized)}
