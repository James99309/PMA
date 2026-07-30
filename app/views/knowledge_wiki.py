# -*- coding: utf-8 -*-
"""Wiki 知识库 API（Karpathy LLM Wiki 方案）

Blueprint: knowledge_wiki_bp  url_prefix: ''  (前端页面和 /api/wiki/* 混在一起)

端点清单：
    GET    /wiki                              — Tailwind 前端主页面
    POST   /api/wiki/raw-files                — 从 file_library 选文件加入 Wiki
    GET    /api/wiki/raw-files                — 列出原始文件（可按 topic 过滤）
    POST   /api/wiki/raw-files/<id>/ingest    — 触发 Opus 编译
    DELETE /api/wiki/raw-files/<id>           — 删除原始文件登记（不删文章）
    GET    /api/wiki/articles                 — 文章列表（可按 topic 过滤）
    GET    /api/wiki/articles/<id>            — 文章详情（含 Markdown 正文）
    GET    /api/wiki/tree                     — topic → [articles] 树结构
    GET    /api/wiki/index                    — 读 wiki/index.md 原始 Markdown
    POST   /api/wiki/query                    — 基于 Wiki 问答
    POST   /api/wiki/lint                     — 触发整库质检

权限：
    - admin/ceo: 全部
    - 其他登录用户：只读 + query
"""
import html as _html
import json
import logging
import os
import re
import threading

from flask import Blueprint, jsonify, render_template, request, current_app, send_file, abort, url_for, Response, stream_with_context
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename, safe_join

from app import db
from app.models.file_manager import FileLibrary, UserFileRef
from app.models.knowledge import KnowledgeRawFile, KnowledgeWikiArticle, KnowledgePromotionRequest, KnowledgeTopic, KnowledgeShareGrant
from app.models.course import InteractiveCourse
from app.models.message import Message
from app.models.user import User
from app.services.file_manager_service import FileManagerService
from app.services.wiki import compiler, linter, querier, storage
from app.services.wiki.paths import ensure_wiki_structure, get_wiki_dir, get_wiki_root

logger = logging.getLogger(__name__)

knowledge_wiki_bp = Blueprint('knowledge_wiki', __name__)


# ══════════════════════════════════════════════════════════════════
# 权限辅助
# ══════════════════════════════════════════════════════════════════

def _is_admin() -> bool:
    return getattr(current_user, 'role', None) in ('admin', 'ceo')


def _require_admin():
    if not _is_admin():
        return jsonify({'success': False, 'message': '仅管理员可执行此操作'}), 403
    return None


def _reject_if_unsuitable_for_wiki(raw_path: str):
    """文件落盘后调用：检查是否适合入 wiki。
    若不合适：unlink 该文件，返回 (jsonify_response, status_code)；适合则返回 None。
    """
    abs_path = get_wiki_root() / raw_path
    reason = storage.validate_raw_file_for_wiki(abs_path)
    if not reason:
        return None
    try:
        abs_path.unlink(missing_ok=True)
    except Exception:
        logger.warning(f'[Wiki] 拒绝 {raw_path} 后清理文件失败')
    logger.info(f'[Wiki] 拒绝入库 {raw_path}: {reason}')
    return jsonify({'success': False, 'message': reason}), 400


def _get_allowed_topic_names() -> set[str]:
    """返回主数据表中定义的所有 topic 名称集合。

    非 admin 上传 / 加入知识库时，用来校验 topic 是否在 admin 预定义列表中。
    """
    return {t[0] for t in db.session.query(KnowledgeTopic.name).all()}


# ══════════════════════════════════════════════════════════════════
# 前端页面
# ══════════════════════════════════════════════════════════════════

@knowledge_wiki_bp.route('/wiki')
@login_required
def wiki_page():
    """Wiki 主页面 —— 侧栏目录 + 正文 + 问答区"""
    ensure_wiki_structure()
    return render_template(
        'knowledge/tw_wiki.html',
        is_admin=_is_admin(),
        is_dept_manager=getattr(current_user, 'is_department_manager', False),
        current_user_id=current_user.id,
    )


# ══════════════════════════════════════════════════════════════════
# AT 版知识库 —— 互动课程(自包含 HTML 课件)
# ──────────────────────────────────────────────────────────────────
# 第 1 步:AT 格式落地页 + 课程卡片,点击在新标签页播放自包含 HTML。
# 课件文件不入 git(15M 自包含 SPA),放在 app/course_assets/<key>.html,
# 由 play_course 路由读取下发;部署时单独投放 / 后续走 NAS WebDAV。
# 课程清单先内联(forward-compatible:加一条即多一门课),后续再 DB 化。
# ══════════════════════════════════════════════════════════════════

COURSE_ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'course_assets'
)

# 课程改为 DB 登记(interactive_courses 表);此处不再硬编码。

# 每门课的"逐页备注"缓存:{course_key: [{label, notes}, ...]}
# 备注就写在课件 HTML 里(deck 格式:每个 <section> 的 data-speaker-notes),
# 翻页时播放页据此把对应页的备注同步到下方面板。解析一次后缓存。
_COURSE_PAGES_CACHE = {}


def _parse_course_pages(abs_path):
    """从自包含课件 HTML 解析每页 {label, notes}(有序)。

    课件是 bundler 打包格式:真实 DOM 存在 <script type="__bundler/template"> 里,
    内容是一段 JSON 字符串;解码后每页是 <section data-label data-speaker-notes>。
    """
    try:
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            data = f.read()
    except OSError:
        return []
    m = re.search(r'<script type="__bundler/template"[^>]*>(.*?)</script>', data, re.S)
    if not m:
        return []
    raw = m.group(1).strip()
    try:
        tpl = json.loads(raw) if raw[:1] == '"' else raw
    except ValueError:
        tpl = raw
    labels = re.findall(r'data-label="([^"]*)"', tpl)
    notes = re.findall(r'data-speaker-notes="([^"]*)"', tpl)
    pages = []
    for i, note in enumerate(notes):
        pages.append({
            'label': _html.unescape(labels[i]) if i < len(labels) else '',
            'notes': _html.unescape(note),
        })
    return pages


def _get_course_pages(course_key, abs_path):
    if course_key not in _COURSE_PAGES_CACHE:
        _COURSE_PAGES_CACHE[course_key] = _parse_course_pages(abs_path)
    return _COURSE_PAGES_CACHE[course_key]


def _list_courses():
    """全部互动课程(dict 列表,新→旧)。"""
    rows = InteractiveCourse.query.order_by(InteractiveCourse.created_at.desc()).all()
    return [c.to_dict() for c in rows]


def _list_courses_grouped():
    """按 media_type 分三组:video / html(互动课件) / ppt。每组新→旧。"""
    rows = InteractiveCourse.query.order_by(InteractiveCourse.created_at.desc()).all()
    grouped = {'video': [], 'html': [], 'ppt': []}
    for r in rows:
        d = r.to_dict()
        grouped.get(d['media_type'], grouped['html']).append(d)
    return grouped


def _is_package(safe_key):
    """多文件离线包:存在 course_assets/<key>/index.html(目录形态)。"""
    return os.path.isfile(os.path.join(COURSE_ASSETS_DIR, safe_key, 'index.html'))


def _course_html_path(safe_key):
    """课件主 HTML 绝对路径:多文件包→<key>/index.html;单文件→<key>.html。"""
    if _is_package(safe_key):
        return os.path.join(COURSE_ASSETS_DIR, safe_key, 'index.html')
    return os.path.join(COURSE_ASSETS_DIR, safe_key + '.html')


def _find_course(course_key):
    """按 key 读 DB 课程 + 校验课件文件存在;返回 (course_dict, abs_path) 或 (None, None)。"""
    safe_key = secure_filename(course_key)
    if not safe_key:
        return None, None
    row = InteractiveCourse.query.filter_by(key=safe_key).first()
    if not row:
        return None, None
    path = _course_html_path(safe_key)
    if not os.path.isfile(path):
        logger.warning('互动课程文件缺失: %s', path)
        return None, None
    return row.to_dict(), path


@knowledge_wiki_bp.route('/wiki/at')
@login_required
def at_wiki_page():
    """AT 版知识库 —— 文章库(复用 wikiApp)+ 互动课程。"""
    ensure_wiki_structure()
    grouped = _list_courses_grouped()
    return render_template(
        'knowledge/at_wiki.html',
        courses=_list_courses(),
        courses_video=grouped['video'],
        courses_html=grouped['html'],
        courses_ppt=grouped['ppt'],
        is_admin=_is_admin(),
        is_dept_manager=getattr(current_user, 'is_department_manager', False),
        current_user_id=current_user.id,
    )


@knowledge_wiki_bp.route('/wiki/play/<course_key>')
@login_required
def play_course(course_key):
    """课程播放页 —— PMA 外壳(返回 + 逐页同步备注)+ 内嵌课件 iframe。"""
    course, path = _find_course(course_key)
    if not course:
        abort(404)
    pages = _get_course_pages(course['key'], path)
    # 多文件包:iframe 指向包内 index.html(相对资源经 /pkg/ 伺服);单文件走 /asset
    if _is_package(course['key']):
        asset_url = url_for('knowledge_wiki.course_pkg', course_key=course['key'], rel='index.html')
    else:
        asset_url = url_for('knowledge_wiki.course_asset', course_key=course['key'])
    return render_template('knowledge/at_course_player.html', course=course, pages=pages, asset_url=asset_url)


@knowledge_wiki_bp.route('/wiki/video/<course_key>')
@login_required
def play_video(course_key):
    """视频课程播放页 —— HTML5 <video> + 章节列表 + 看完记录。"""
    row = _find_media_course(course_key, 'video')
    if not row:
        abort(404)
    from app.models.video_watch import VideoWatchState
    st = VideoWatchState.query.filter_by(user_id=current_user.id, course_key=row.key).first()
    watch = st.to_dict() if st else {'last_position': 0, 'max_progress': 0, 'completed': False}
    return render_template('knowledge/at_video_player.html', course=row.to_dict(), watch=watch)


@knowledge_wiki_bp.route('/wiki/play/<course_key>/asset')
@login_required
def course_asset(course_key):
    """把自包含课件 HTML 作为 iframe 源整页下发(登录用户可见)。"""
    course, path = _find_course(course_key)
    if not course:
        abort(404)
    return send_file(path, mimetype='text/html')


def _find_media_course(course_key, media_type):
    """按 key 读 DB 课程并校验 media_type;video/ppt 无本地文件,只需 media_url。
    返回 InteractiveCourse 行或 None。"""
    safe_key = secure_filename(course_key)
    if not safe_key:
        return None
    row = InteractiveCourse.query.filter_by(key=safe_key).first()
    if not row or (row.media_type or 'html') != media_type or not row.media_url:
        return None
    return row


def _parse_range(range_header, total):
    """解析 'bytes=start-end' → (start, end)。end 可省(到文件尾)。越界夹紧。"""
    try:
        unit, _, rng = range_header.partition('=')
        if unit.strip() != 'bytes':
            return 0, total - 1
        start_s, _, end_s = rng.strip().partition('-')
        if not start_s:
            # suffix range: bytes=-N → 最后 N 字节
            n = int(end_s) if end_s else 0
            start = max(0, total - n)
            return start, total - 1
        start = int(start_s)
        end = int(end_s) if end_s else total - 1
        start = max(0, start)
        end = min(end, total - 1)
        if start > end:
            start, end = 0, total - 1
        return start, end
    except (ValueError, AttributeError):
        return 0, total - 1


@knowledge_wiki_bp.route('/wiki/play/<course_key>/video')
@login_required
def course_video(course_key):
    """视频课程流式代理 —— 支持 HTTP Range,分块从 NAS WebDAV 取,不整块进内存。

    浏览器 <video> 拖动进度会发 Range 请求,只拉需要那段;服务器同时只持 512KB。
    """
    row = _find_media_course(course_key, 'video')
    if not row:
        abort(404)

    from app.utils.synology_webdav_client import get_synology_webdav_client
    client = get_synology_webdav_client()
    if not client.is_configured:
        abort(503, description='存储未配置')

    info = client.get_file_info(row.media_url)
    if not info or not info.get('content_length'):
        abort(404, description='视频文件不存在')
    total = int(info['content_length'])
    CHUNK = 1024 * 512  # 512KB/块,恒定内存

    range_header = request.headers.get('Range')
    if range_header:
        start, end = _parse_range(range_header, total)
    else:
        start, end = 0, total - 1

    def generate():
        pos = start
        while pos <= end:
            n = min(CHUNK, end - pos + 1)
            chunk = client.download_file_range(row.media_url, pos, pos + n - 1)
            if not chunk:
                break
            yield chunk
            pos += n

    status = 206 if range_header else 200
    headers = {
        'Accept-Ranges': 'bytes',
        'Content-Length': str(end - start + 1),
        'Content-Type': 'video/mp4',
        'Cache-Control': 'private, max-age=3600',
    }
    if range_header:
        headers['Content-Range'] = f'bytes {start}-{end}/{total}'
    return Response(stream_with_context(generate()), status=status, headers=headers)


@knowledge_wiki_bp.route('/wiki/video/<course_key>/progress', methods=['POST'])
@login_required
def video_progress(course_key):
    """上报视频观看进度:记续播位置 + 看过最大进度,>=90% 标完成。"""
    row = _find_media_course(course_key, 'video')
    if not row:
        return jsonify({'success': False}), 404
    data = request.get_json(silent=True) or {}
    try:
        cur = max(0.0, float(data.get('position', 0)))
        dur = max(0.0, float(data.get('duration', 0)))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': '参数无效'}), 400
    pct = (cur / dur) if dur > 0 else 0.0

    from app.models.video_watch import VideoWatchState
    from datetime import datetime
    st = VideoWatchState.query.filter_by(user_id=current_user.id, course_key=row.key).first()
    if not st:
        st = VideoWatchState(user_id=current_user.id, course_key=row.key)
        db.session.add(st)
    st.last_position = cur
    if pct > (st.max_progress or 0):
        st.max_progress = pct
    if pct >= 0.9 and not st.completed:
        st.completed = True
        st.completed_at = datetime.now()
    db.session.commit()
    return jsonify({'success': True, 'completed': st.completed})


@knowledge_wiki_bp.route('/wiki/play/<course_key>/download')
@login_required
def course_download(course_key):
    """PPT/PDF 下载 —— 从 NAS WebDAV 流式下发,强制另存。"""
    row = _find_media_course(course_key, 'ppt')
    if not row:
        abort(404)
    from app.utils.synology_webdav_client import get_synology_webdav_client
    client = get_synology_webdav_client()
    if not client.is_configured:
        abort(503, description='存储未配置')
    from urllib.parse import quote
    fname = row.media_url.split('/')[-1]
    ext = os.path.splitext(fname)[1].lower()
    ctype = {'.pdf': 'application/pdf',
             '.ppt': 'application/vnd.ms-powerpoint',
             '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
             }.get(ext, 'application/octet-stream')

    def generate():
        for chunk in client.download_file_stream(row.media_url, chunk_size=1024 * 512):
            if chunk:
                yield chunk

    return Response(stream_with_context(generate()), mimetype=ctype, headers={
        'Content-Disposition': f"attachment; filename*=UTF-8''{quote(fname)}",
        'Cache-Control': 'private, max-age=3600',
    })


@knowledge_wiki_bp.route('/wiki/play/<course_key>/pkg/<path:rel>')
@login_required
def course_pkg(course_key, rel):
    """多文件离线包内的文件(index.html / assets 图片 / mp4 视频),安全伺服。

    仅登录可见;safe_join 防目录穿越;mp4 由 send_file 支持 Range(可拖动进度)。
    """
    safe = secure_filename(course_key)
    if not safe:
        abort(404)
    base = os.path.join(COURSE_ASSETS_DIR, safe)
    if not os.path.isdir(base):
        abort(404)
    full = safe_join(base, rel)
    if not full or not os.path.isfile(full):
        abort(404)
    return send_file(full, conditional=True)


@knowledge_wiki_bp.route('/wiki/play/<course_key>/thumb/<int:page>')
@login_required
def course_thumb(course_key, page):
    """逐页缩略图(用于问答答案卡片预览;默认第1页可当封面)。"""
    safe = secure_filename(course_key)
    if not safe:
        abort(404)
    path = os.path.join(COURSE_ASSETS_DIR, safe + '.thumbs', f'{page}.png')
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, mimetype='image/png')


# ── 对外公开课件(无需登录,供二维码扫码;仅标记 .public 的课程)────────────
# 只下发干净 deck 本身(无 PMA 外壳/说明/考核);其余课程/系统内容不可达。
# opt-in 方式:课程目录/单文件旁放一个空的 .public 标记文件即公开,删除即下线。

def _course_is_public(safe_key):
    return (os.path.isfile(os.path.join(COURSE_ASSETS_DIR, safe_key, '.public'))
            or os.path.isfile(os.path.join(COURSE_ASSETS_DIR, safe_key + '.public')))


@knowledge_wiki_bp.route('/wiki/pub/<course_key>/', strict_slashes=False)
def public_course(course_key):
    """公开课件入口(无登录):下发干净 deck 的 index.html。仅 .public 课程可达。"""
    safe = secure_filename(course_key)
    if not safe or not _course_is_public(safe):
        abort(404)
    path = _course_html_path(safe)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, mimetype='text/html')


@knowledge_wiki_bp.route('/wiki/pub/<course_key>/<path:rel>')
def public_course_asset(course_key, rel):
    """公开课件的同级资源(pkg-assets 图片 / mp4),无登录;safe_join 防穿越,mp4 支持 Range。"""
    safe = secure_filename(course_key)
    if not safe or not _course_is_public(safe):
        abort(404)
    if rel.startswith('.') or '/.' in rel:   # 挡掉 .public 等点文件
        abort(404)
    base = os.path.join(COURSE_ASSETS_DIR, safe)
    if not os.path.isdir(base):
        abort(404)
    full = safe_join(base, rel)
    if not full or not os.path.isfile(full):
        abort(404)
    return send_file(full, conditional=True)


# ── 课程管理(上传 / 编辑 / 生成缩略图 / 删除,仅管理员)──────────────

def _bg_generate_thumbs(app_obj, cid, key, n_pages):
    """后台线程:生成逐页缩略图并置 has_thumbs(best-effort,失败仅记日志)。"""
    with app_obj.app_context():
        try:
            from app.services import course_thumbs
            course_thumbs.generate_thumbnails(key, n_pages, COURSE_ASSETS_DIR)
            row = InteractiveCourse.query.get(cid)
            if row:
                row.has_thumbs = True
                db.session.commit()
            logger.info('[course] 后台缩略图完成: %s (%d 页)', key, n_pages)
        except Exception:
            logger.exception('[course] 后台缩略图失败(服务端可能缺 Playwright): %s', key)


def _kick_thumbs(cid, key, n_pages):
    if n_pages > 0:
        threading.Thread(
            target=_bg_generate_thumbs,
            args=(current_app._get_current_object(), cid, key, n_pages),
            daemon=True,
        ).start()


@knowledge_wiki_bp.route('/wiki/courses', methods=['POST'])
@login_required
def create_course():
    """上传 HTML 课件 → 建课程 + 析出知识(缩略图另点按钮生成)。"""
    if not _is_admin():
        return jsonify({'success': False, 'message': '仅管理员可上传课程'}), 403
    f = request.files.get('file')
    if not f or not (f.filename or '').lower().endswith('.html'):
        return jsonify({'success': False, 'message': '请上传 .html 课件文件'}), 400
    title = (request.form.get('title') or '').strip()
    if not title:
        return jsonify({'success': False, 'message': '请填写标题'}), 400
    subtitle = (request.form.get('subtitle') or '').strip()
    desc = (request.form.get('desc') or '').strip()
    topic = (request.form.get('topic') or '产品技术').strip()
    accent = (request.form.get('accent') or '#1A0E3D').strip()

    raw_key = (request.form.get('key') or '').strip() or os.path.splitext(f.filename)[0]
    base = secure_filename(raw_key) or 'course'
    key, n = base, 2
    while InteractiveCourse.query.filter_by(key=key).first():
        key, n = f'{base}-{n}', n + 1

    os.makedirs(COURSE_ASSETS_DIR, exist_ok=True)
    path = os.path.join(COURSE_ASSETS_DIR, key + '.html')
    f.save(path)
    _COURSE_PAGES_CACHE.pop(key, None)
    pages = _parse_course_pages(path)

    row = InteractiveCourse(
        key=key, title=title, subtitle=subtitle, desc=desc, topic=topic, accent=accent,
        cover_page=1, page_count=len(pages), has_thumbs=False, owner_id=current_user.id)
    db.session.add(row)
    db.session.commit()

    if pages:
        try:
            from app.services import course_knowledge
            art = course_knowledge.ingest_course_knowledge(
                row.to_dict(), pages, topic=topic, owner_id=current_user.id, scope='company')
            row.article_id = art.id
            db.session.commit()
        except Exception:
            logger.exception('[course] 知识析出失败: %s', key)

    # 上传即后台生成缩略图(不用单独点)
    _kick_thumbs(row.id, key, len(pages))

    return jsonify({'success': True, 'data': row.to_dict(), 'page_count': len(pages),
                    'message': (f'已创建,解析 {len(pages)} 页,缩略图后台生成中(稍后刷新可见)'
                                if pages else '已创建(课件无分页,无知识析出/缩略图)')})


@knowledge_wiki_bp.route('/wiki/courses/media', methods=['POST'])
@login_required
def register_media_course():
    """登记视频/PPT 课程 —— 文件已在 NAS WebDAV,这里只存元信息 + media_url。

    JSON: {media_type:'video'|'ppt', title, media_url, subtitle?, desc?, topic?,
           accent?, duration?(video 秒), file_size?(字节)}
    """
    if not _is_admin():
        return jsonify({'success': False, 'message': '仅管理员可登记'}), 403
    data = request.get_json(silent=True) or {}
    media_type = (data.get('media_type') or '').strip()
    if media_type not in ('video', 'ppt'):
        return jsonify({'success': False, 'message': 'media_type 必须为 video 或 ppt'}), 400
    title = (data.get('title') or '').strip()
    media_url = (data.get('media_url') or '').strip()
    # 视频来源:webdav(NAS 路径) / gdrive(Google Drive 文件ID)
    video_source = (data.get('video_source') or 'webdav').strip()
    if media_type == 'video' and video_source not in ('webdav', 'gdrive'):
        video_source = 'webdav'
    if not title:
        return jsonify({'success': False, 'message': '请填写标题'}), 400
    if not media_url:
        return jsonify({'success': False, 'message': '请填写文件路径或 Google Drive 文件ID'}), 400

    raw_key = (data.get('key') or '').strip() or os.path.splitext(media_url.split('/')[-1])[0]
    base = secure_filename(raw_key) or media_type
    key, n = base, 2
    while InteractiveCourse.query.filter_by(key=key).first():
        key, n = f'{base}-{n}', n + 1

    def _int(v):
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return None

    row = InteractiveCourse(
        key=key, title=title,
        subtitle=(data.get('subtitle') or '').strip(),
        desc=(data.get('desc') or '').strip(),
        topic=(data.get('topic') or '产品技术').strip(),
        accent=(data.get('accent') or '#1A0E3D').strip(),
        media_type=media_type, media_url=media_url,
        video_source=video_source if media_type == 'video' else None,
        duration=_int(data.get('duration')) if media_type == 'video' else None,
        file_size=_int(data.get('file_size')),
        cover_page=1, page_count=0, has_thumbs=False, owner_id=current_user.id)
    db.session.add(row)
    db.session.commit()
    return jsonify({'success': True, 'data': row.to_dict(),
                    'message': f'已登记{"视频" if media_type == "video" else "PPT"}课程'})


def _upload_to_webdav(file_storage, subdir):
    """把上传的文件存到 NAS WebDAV 的 subdir 下,返回相对路径(如 /courses/xxx.pptx)。失败返回 None。"""
    from app.utils.synology_webdav_client import get_synology_webdav_client
    client = get_synology_webdav_client()
    if not client.is_configured:
        return None, '存储未配置'
    fname = secure_filename(file_storage.filename or 'file')
    if not fname:
        return None, '文件名无效'
    # 冲突加时间戳
    from datetime import datetime
    stem, ext = os.path.splitext(fname)
    remote = f'/{subdir}/{stem}{ext}'
    content = file_storage.read()
    ok = client.upload_file(content, remote)
    if not ok:
        # 重名冲突时加时间戳重试
        remote = f'/{subdir}/{stem}_{datetime.now().strftime("%H%M%S")}{ext}'
        ok = client.upload_file(content, remote)
    return (remote, len(content)) if ok else (None, '上传失败')


@knowledge_wiki_bp.route('/wiki/courses/ppt', methods=['POST'])
@login_required
def upload_ppt_course():
    """上传 PPT/PDF 课程 —— 文件直传到 NAS WebDAV(SG nginx 无限制),可选封面图。

    multipart: file(必), title(必), cover(可选图), subtitle?, desc?, topic?, accent?
    """
    if not _is_admin():
        return jsonify({'success': False, 'message': '仅管理员可上传'}), 403
    f = request.files.get('file')
    if not f or not (f.filename or '').lower().endswith(('.ppt', '.pptx', '.pdf')):
        return jsonify({'success': False, 'message': '请上传 .ppt / .pptx / .pdf 文件'}), 400
    title = (request.form.get('title') or '').strip()
    if not title:
        return jsonify({'success': False, 'message': '请填写标题'}), 400

    remote, size_or_err = _upload_to_webdav(f, 'courses')
    if not remote:
        return jsonify({'success': False, 'message': f'文件上传失败: {size_or_err}'}), 500

    # 可选封面
    cover_url = None
    cover = request.files.get('cover')
    if cover and (cover.filename or '').lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        cover_remote, _ = _upload_to_webdav(cover, 'courses/covers')
        cover_url = cover_remote

    raw_key = (request.form.get('key') or '').strip() or os.path.splitext(secure_filename(f.filename))[0]
    base = secure_filename(raw_key) or 'ppt'
    key, n = base, 2
    while InteractiveCourse.query.filter_by(key=key).first():
        key, n = f'{base}-{n}', n + 1

    row = InteractiveCourse(
        key=key, title=title,
        subtitle=(request.form.get('subtitle') or '').strip(),
        desc=(request.form.get('desc') or '').strip(),
        topic=(request.form.get('topic') or '产品技术').strip(),
        accent=(request.form.get('accent') or '#1A0E3D').strip(),
        media_type='ppt', media_url=remote, cover_url=cover_url,
        file_size=size_or_err if isinstance(size_or_err, int) else None,
        cover_page=1, page_count=0, has_thumbs=False, owner_id=current_user.id)
    db.session.add(row)
    db.session.commit()
    return jsonify({'success': True, 'data': row.to_dict(), 'message': '已上传 PPT 课程'})


@knowledge_wiki_bp.route('/wiki/courses/<int:cid>/cover', methods=['POST'])
@login_required
def upload_course_cover(cid):
    """给已有课程(video/ppt)上传/更换封面图。multipart: cover(图)。"""
    if not _is_admin():
        return jsonify({'success': False, 'message': '仅管理员可操作'}), 403
    row = InteractiveCourse.query.get_or_404(cid)
    cover = request.files.get('cover')
    if not cover or not (cover.filename or '').lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        return jsonify({'success': False, 'message': '请上传 jpg/png/webp 图片'}), 400
    remote, err = _upload_to_webdav(cover, 'courses/covers')
    if not remote:
        return jsonify({'success': False, 'message': f'封面上传失败: {err}'}), 500
    row.cover_url = remote
    db.session.commit()
    return jsonify({'success': True, 'data': row.to_dict(), 'message': '封面已更新'})


@knowledge_wiki_bp.route('/wiki/courses/<course_key>/cover')
@login_required
def course_cover(course_key):
    """课程自定义封面图 —— 从 NAS WebDAV 流式下发。"""
    safe = secure_filename(course_key)
    row = InteractiveCourse.query.filter_by(key=safe).first()
    if not row or not row.cover_url:
        abort(404)
    from app.utils.synology_webdav_client import get_synology_webdav_client
    client = get_synology_webdav_client()
    if not client.is_configured:
        abort(503)
    from urllib.parse import quote
    ext = os.path.splitext(row.cover_url)[1].lower()
    ctype = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
             '.webp': 'image/webp'}.get(ext, 'application/octet-stream')

    def generate():
        for chunk in client.download_file_stream(row.cover_url, chunk_size=1024 * 256):
            if chunk:
                yield chunk

    return Response(stream_with_context(generate()), mimetype=ctype,
                    headers={'Cache-Control': 'private, max-age=86400'})


@knowledge_wiki_bp.route('/wiki/courses/<int:cid>', methods=['PATCH', 'POST'])
@login_required
def update_course(cid):
    """编辑课程元数据;可选替换课件 HTML(multipart 带 file → 重解析+重析出+重生成缩略图)。"""
    if not _is_admin():
        return jsonify({'success': False, 'message': '仅管理员可编辑'}), 403
    row = InteractiveCourse.query.get_or_404(cid)
    is_multipart = 'multipart' in (request.content_type or '')
    data = request.form if is_multipart else (request.get_json(silent=True) or {})
    for fld in ('title', 'subtitle', 'desc', 'topic', 'accent'):
        if fld in data:
            setattr(row, fld, (data.get(fld) or '').strip())
    if 'cover_page' in data:
        try:
            row.cover_page = max(1, int(data['cover_page']))
        except (TypeError, ValueError):
            pass

    f = request.files.get('file')
    if f and (f.filename or '').lower().endswith('.html'):
        path = os.path.join(COURSE_ASSETS_DIR, row.key + '.html')
        f.save(path)
        _COURSE_PAGES_CACHE.pop(row.key, None)
        pages = _parse_course_pages(path)
        row.page_count = len(pages)
        row.has_thumbs = False
        if pages:
            try:
                from app.services import course_knowledge
                art = course_knowledge.ingest_course_knowledge(
                    row.to_dict(), pages, topic=row.topic,
                    owner_id=row.owner_id or current_user.id, scope='company')
                row.article_id = art.id
            except Exception:
                logger.exception('[course] 替换 HTML 后知识析出失败: %s', row.key)
        db.session.commit()
        _kick_thumbs(row.id, row.key, len(pages))
        return jsonify({'success': True, 'data': row.to_dict(), 'replaced': True,
                        'message': f'已替换课件,解析 {len(pages)} 页,缩略图后台重生成中'})

    db.session.commit()
    return jsonify({'success': True, 'data': row.to_dict()})


@knowledge_wiki_bp.route('/wiki/courses/<int:cid>/thumbs', methods=['POST'])
@login_required
def gen_course_thumbs(cid):
    """生成/重生成逐页缩略图(需服务端 Playwright + Chromium)。"""
    if not _is_admin():
        return jsonify({'success': False, 'message': '仅管理员可操作'}), 403
    row = InteractiveCourse.query.get_or_404(cid)
    _, path = _find_course(row.key)
    if not path:
        return jsonify({'success': False, 'message': '课件文件缺失'}), 404
    pages = _get_course_pages(row.key, path)
    if not pages:
        return jsonify({'success': False, 'message': '课件无分页,无法生成缩略图'}), 400
    try:
        from app.services import course_thumbs
        cnt = course_thumbs.generate_thumbnails(row.key, len(pages), COURSE_ASSETS_DIR)
        row.has_thumbs = True
        row.page_count = len(pages)
        db.session.commit()
        return jsonify({'success': True, 'count': cnt})
    except Exception as e:
        logger.exception('[course] 缩略图生成失败: %s', row.key)
        return jsonify({'success': False,
                        'message': f'生成失败(服务端可能未装 Playwright/Chromium): {e}'}), 500


@knowledge_wiki_bp.route('/wiki/courses/<int:cid>', methods=['DELETE'])
@login_required
def delete_course(cid):
    """删除课程 + 连带:课件/缩略图/题库文件 + 析出的知识文章(深链会随课程失效,故一并删)。"""
    if not _is_admin():
        return jsonify({'success': False, 'message': '仅管理员可删除'}), 403
    import shutil
    row = InteractiveCourse.query.get_or_404(cid)
    key = row.key

    # 连带删除析出的知识文章(优先按 article_id,兜底按 <key>-deck slug)+ 其 .md 文件
    art = (KnowledgeWikiArticle.query.get(row.article_id) if row.article_id else None) \
        or KnowledgeWikiArticle.query.filter_by(slug=key + '-deck').first()
    if art:
        try:
            storage.delete_article(art.topic, art.slug)
        except Exception:
            logger.warning('[course] 删知识文章 .md 失败: %s', art.slug)
        db.session.delete(art)

    db.session.delete(row)
    db.session.commit()

    for p in (key + '.html', key + '.quiz.json'):
        try:
            os.remove(os.path.join(COURSE_ASSETS_DIR, p))
        except OSError:
            pass
    try:
        shutil.rmtree(os.path.join(COURSE_ASSETS_DIR, key + '.thumbs'))
    except OSError:
        pass
    _COURSE_PAGES_CACHE.pop(key, None)
    return jsonify({'success': True})


# ── 第3步:考核 + 评分 ────────────────────────────────────────────

@knowledge_wiki_bp.route('/wiki/play/<course_key>/quiz')
@login_required
def course_quiz_page(course_key):
    """考核页外壳(题目走 AJAX 拉,避免首生成阻塞页面)。"""
    course, _ = _find_course(course_key)
    if not course:
        abort(404)
    return render_template('knowledge/at_course_quiz.html', course=course)


@knowledge_wiki_bp.route('/wiki/play/<course_key>/quiz/questions')
@login_required
def course_quiz_questions(course_key):
    """返回去掉答案的题目(首次会触发 AI 出题并落盘缓存)。"""
    from app.services import course_quiz
    course, path = _find_course(course_key)
    if not course:
        abort(404)
    pages = _get_course_pages(course['key'], path)
    if not pages:
        return jsonify({'success': False, 'message': '课件无讲解内容,无法出题'}), 400
    force = request.args.get('regenerate') == '1' and _is_admin()
    try:
        questions = course_quiz.load_or_generate(course['key'], pages, COURSE_ASSETS_DIR, force=force)
    except Exception as e:
        logger.exception('出题失败: %s', course['key'])
        return jsonify({'success': False, 'message': f'AI 出题失败: {e}'}), 502
    return jsonify({'success': True, 'questions': course_quiz.public_questions(questions),
                    'pass_score': course_quiz.PASS_SCORE})


@knowledge_wiki_bp.route('/wiki/play/<course_key>/quiz/submit', methods=['POST'])
@login_required
def course_quiz_submit(course_key):
    """收答案 → 判分 → 写 training_* 表 → 返回成绩与逐题对错。"""
    from datetime import datetime
    from app.services import course_quiz
    from app.models.training import TrainingQuizAttempt, TrainingModuleState, get_local_time

    course, path = _find_course(course_key)
    if not course:
        abort(404)
    pages = _get_course_pages(course['key'], path)
    try:
        questions = course_quiz.load_or_generate(course['key'], pages, COURSE_ASSETS_DIR)
    except Exception as e:
        return jsonify({'success': False, 'message': f'题目加载失败: {e}'}), 502

    answers = (request.get_json(silent=True) or {}).get('answers') or {}
    result = course_quiz.grade(questions, answers)

    now = get_local_time()
    module_slug = 'main'
    # 逐题留痕
    for d in result['details']:
        db.session.add(TrainingQuizAttempt(
            user_id=current_user.id,
            course_slug=course['key'], module_slug=module_slug, chapter=1,
            question_id=d['id'], question_text=d['question'],
            question_type=d['type'],
            user_answer=json.dumps(d['user_answer'], ensure_ascii=False),
            correct_answer=json.dumps(d['correct_answer'], ensure_ascii=False),
            is_correct=d['is_correct'], attempted_at=now,
        ))
    # 模块成绩(upsert)
    state = TrainingModuleState.query.filter_by(
        user_id=current_user.id, course_slug=course['key'], module_slug=module_slug).first()
    if not state:
        state = TrainingModuleState(
            user_id=current_user.id, course_slug=course['key'], module_slug=module_slug)
        db.session.add(state)
    state.final_exam_score = result['score']
    state.status = 'passed' if result['passed'] else 'failed'
    if result['passed'] and not state.final_exam_passed_at:
        state.final_exam_passed_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, **result})


# ══════════════════════════════════════════════════════════════════
# 原始文件管理
# ══════════════════════════════════════════════════════════════════

@knowledge_wiki_bp.route('/api/wiki/raw-files', methods=['GET'])
@login_required
def list_raw_files():
    from app.services.wiki.scope import visible_raw_files_query
    topic = (request.args.get('topic') or '').strip()
    q = visible_raw_files_query(current_user)
    if topic:
        q = q.filter_by(topic=topic)
    items = q.order_by(KnowledgeRawFile.created_at.desc()).all()
    return jsonify({'success': True, 'data': [r.to_dict() for r in items]})


@knowledge_wiki_bp.route('/api/wiki/raw-files', methods=['POST'])
@login_required
def add_raw_file():
    """把 file_library 中的文件登记为 Wiki 原始资料

    Body JSON:
        file_library_id: int (必填)
        topic: str (必填)
        title: str (可选，默认用 file_library.original_filename)
        scope: str (可选，默认 'personal')
    """
    # 不再要求 admin — scope 权限由 can_write_scope 控制
    data = request.get_json(silent=True) or {}
    fl_id = data.get('file_library_id')
    topic = (data.get('topic') or '').strip()
    title = (data.get('title') or '').strip()

    if not fl_id or not topic:
        return jsonify({'success': False, 'message': 'file_library_id 和 topic 必填'}), 400

    # 前置校验 topic 合法性，避免把非法输入交给 storage 层
    try:
        storage.validate_topic(topic)
    except storage.WikiPathError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    # 非管理员只能选 admin 预定义的 topic
    if current_user.role not in ('admin', 'ceo'):
        if topic not in _get_allowed_topic_names():
            return jsonify({'success': False, 'message': '只能选择已有的分类目录'}), 403

    fl = FileLibrary.query.get(fl_id)
    if not fl:
        return jsonify({'success': False, 'message': '文件不存在于 file_library'}), 404

    # 从 file_library 读原始字节
    content = FileManagerService.read_file_content_auto_decompress(fl)
    if content is None:
        return jsonify({'success': False, 'message': '无法读取 file_library 中的文件内容'}), 500

    ensure_wiki_structure()

    # 保存到 raw/<topic>/<safe-dated-name>
    safe_name = storage.dated_filename(fl.original_filename)
    raw_path = storage.save_raw_file(topic, safe_name, content)
    rejected = _reject_if_unsuitable_for_wiki(raw_path)
    if rejected is not None:
        return rejected

    # scope 参数（默认 personal）
    scope = (data.get('scope') or 'personal').strip()
    if scope not in ('personal', 'department', 'company', 'system'):
        scope = 'personal'
    from app.services.wiki.scope import can_write_scope
    if not can_write_scope(current_user, scope):
        return jsonify({'success': False, 'message': f'无权限写入 {scope} 级别'}), 403

    raw = KnowledgeRawFile(
        file_library_id=fl.id,
        topic=topic,
        raw_path=raw_path,
        title=title or fl.original_filename,
        added_by=current_user.id,
        scope=scope,
        owner_id=current_user.id,
        owner_department=current_user.department,
    )
    db.session.add(raw)
    db.session.commit()
    logger.info(f'[Wiki] user={current_user.id} 新增 raw_file id={raw.id} topic={topic} scope={scope}')
    return jsonify({'success': True, 'data': raw.to_dict()})


@knowledge_wiki_bp.route('/api/wiki/upload-and-add', methods=['POST'])
@login_required
def upload_and_add():
    """直接上传文件 → file_library + raw_file 一步完成

    Form fields:
        file: 上传的文件 (必填)
        topic: str (必填)
        title: str (可选，默认用文件名)
        scope: str (可选，默认 'personal')
    """
    # 不再要求 admin — scope 权限由 can_write_scope 控制
    file_obj = request.files.get('file')
    topic = (request.form.get('topic') or '').strip()
    title = (request.form.get('title') or '').strip()

    if not file_obj or not file_obj.filename:
        return jsonify({'success': False, 'message': '请选择文件'}), 400
    if not topic:
        return jsonify({'success': False, 'message': 'topic 必填'}), 400

    try:
        storage.validate_topic(topic)
    except storage.WikiPathError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    # 非管理员只能选 admin 预定义的 topic
    if current_user.role not in ('admin', 'ceo'):
        if topic not in _get_allowed_topic_names():
            return jsonify({'success': False, 'message': '只能选择已有的分类目录'}), 403

    # 1. 上传到 file_library（SHA256 去重）
    success, result = FileManagerService.upload_file(current_user, file_obj)
    if not success:
        return jsonify({'success': False, 'message': result}), 400

    # result 是 UserFileRef.to_dict()，取 file_library_id
    fl_id = result.get('file_library_id')
    fl = FileLibrary.query.get(fl_id)
    if not fl:
        return jsonify({'success': False, 'message': '文件存储异常'}), 500

    # 2. 读取文件内容并保存到 raw 目录
    content = FileManagerService.read_file_content_auto_decompress(fl)
    if content is None:
        return jsonify({'success': False, 'message': '无法读取上传的文件内容'}), 500

    ensure_wiki_structure()

    safe_name = storage.dated_filename(fl.original_filename)
    raw_path = storage.save_raw_file(topic, safe_name, content)
    rejected = _reject_if_unsuitable_for_wiki(raw_path)
    if rejected is not None:
        return rejected

    # scope 参数
    scope = (request.form.get('scope') or 'personal').strip()
    if scope not in ('personal', 'department', 'company', 'system'):
        scope = 'personal'
    from app.services.wiki.scope import can_write_scope
    if not can_write_scope(current_user, scope):
        return jsonify({'success': False, 'message': f'无权限写入 {scope} 级别'}), 403

    raw = KnowledgeRawFile(
        file_library_id=fl.id,
        topic=topic,
        raw_path=raw_path,
        title=title or fl.original_filename,
        added_by=current_user.id,
        scope=scope,
        owner_id=current_user.id,
        owner_department=current_user.department,
    )
    db.session.add(raw)
    db.session.commit()

    logger.info(f'[Wiki] upload-and-add user={current_user.id} raw_id={raw.id} topic={topic} scope={scope}')
    return jsonify({'success': True, 'data': raw.to_dict()})


@knowledge_wiki_bp.route('/api/wiki/raw-files/from-file-ref', methods=['POST'])
@login_required
def add_raw_from_file_ref():
    """从文件管理器的 UserFileRef 添加原始资料（文件管理器右键菜单用）

    Body JSON:
        user_file_ref_id: int (必填) — 文件管理器中的文件引用 ID
        topic: str (必填)
        title: str (可选)

    内部解析 file_ref → file_library_id，复用 add_raw_file 逻辑。
    权限由 scope + can_write_scope 控制，不再限制仅 admin。
    """
    data = request.get_json(silent=True) or {}
    ref_id = data.get('user_file_ref_id')
    topic = (data.get('topic') or '').strip()
    title = (data.get('title') or '').strip()

    if not ref_id or not topic:
        return jsonify({'success': False, 'message': 'user_file_ref_id 和 topic 必填'}), 400

    try:
        storage.validate_topic(topic)
    except storage.WikiPathError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    # 非管理员只能选 admin 预定义的 topic
    if current_user.role not in ('admin', 'ceo'):
        if topic not in _get_allowed_topic_names():
            return jsonify({'success': False, 'message': '只能选择已有的分类目录'}), 403

    from app.models.file_manager import UserFileRef
    ref = UserFileRef.query.get(ref_id)
    if not ref:
        return jsonify({'success': False, 'message': f'文件引用 ID {ref_id} 不存在'}), 404

    fl = FileLibrary.query.get(ref.file_library_id)
    if not fl:
        return jsonify({'success': False, 'message': '关联的 file_library 记录不存在'}), 404

    content = FileManagerService.read_file_content_auto_decompress(fl)
    if content is None:
        return jsonify({'success': False, 'message': '无法读取文件内容'}), 500

    ensure_wiki_structure()

    safe_name = storage.dated_filename(fl.original_filename)
    raw_path = storage.save_raw_file(topic, safe_name, content)
    rejected = _reject_if_unsuitable_for_wiki(raw_path)
    if rejected is not None:
        return rejected

    # scope 参数
    scope = (data.get('scope') or 'personal').strip()
    if scope not in ('personal', 'department', 'company', 'system'):
        scope = 'personal'
    from app.services.wiki.scope import can_write_scope
    if not can_write_scope(current_user, scope):
        return jsonify({'success': False, 'message': f'无权限写入 {scope} 级别'}), 403

    raw = KnowledgeRawFile(
        file_library_id=fl.id,
        topic=topic,
        raw_path=raw_path,
        title=title or ref.display_name or fl.original_filename,
        added_by=current_user.id,
        scope=scope,
        owner_id=current_user.id,
        owner_department=current_user.department,
    )
    db.session.add(raw)
    db.session.commit()

    logger.info(f'[Wiki] from-file-ref user={current_user.id} ref={ref_id} → raw_id={raw.id} topic={topic} scope={scope}')

    # 异步触发 Ingest —— 不阻塞前端，编译完成后通过 Message 通知用户
    user_id = current_user.id
    app = current_app._get_current_object()
    threading.Thread(
        target=_async_ingest_and_notify,
        args=(raw.id, user_id, app),
        daemon=True,
    ).start()

    return jsonify({
        'success': True,
        'data': raw.to_dict(),
        'message': '已提交编译，完成后会收到系统通知',
    })


@knowledge_wiki_bp.route('/api/wiki/raw-files/<int:raw_id>/ingest', methods=['POST'])
@login_required
def trigger_ingest(raw_id):
    """触发 Claude Opus 编译一个原始文件。**同步**阻塞约 30-60 秒。
    权限：admin/ceo 或文件所有者可触发。
    """
    raw = KnowledgeRawFile.query.get(raw_id)
    if not raw:
        return jsonify({'success': False, 'message': '记录不存在'}), 404
    if not _is_admin() and raw.owner_id != current_user.id:
        return jsonify({'success': False, 'message': '只有文件所有者或管理员可以触发编译'}), 403

    try:
        result = compiler.ingest_raw_file(raw_id)
    except compiler.IngestError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception:
        logger.exception(f'[Wiki] ingest 失败 raw_id={raw_id}')
        return jsonify({'success': False, 'message': '编译失败，请查看服务器日志'}), 500

    return jsonify({'success': True, 'data': result})


def _can_access_raw_file(user, raw_id):
    """raw_file 内容访问权限 = 严格 scope 可见

    设计取舍：
    - 「查看来源」入口只展示元数据（标题/owner/topic/scope），不放行内容下载
    - 拿到内容必须直接 scope 可见；否则需线下联系 owner
    """
    from app.services.wiki.scope import visible_raw_files_query
    return visible_raw_files_query(user).filter(KnowledgeRawFile.id == raw_id).first()


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>/sources', methods=['GET'])
@login_required
def list_article_sources(article_id):
    """列出文章的所有源文件（按文章可见性鉴权 - 能看到文章就能看到源头）"""
    from app.services.wiki.scope import visible_articles_query

    art = visible_articles_query(current_user).filter(KnowledgeWikiArticle.id == article_id).first()
    if not art:
        return jsonify({'success': False, 'message': '无权访问或文章不存在'}), 403

    source_ids = art.source_raw_ids or []
    if not source_ids:
        return jsonify({'success': True, 'data': []})

    raws = KnowledgeRawFile.query.filter(KnowledgeRawFile.id.in_(source_ids)).all()
    # 保持 source_raw_ids 顺序
    raws_by_id = {r.id: r for r in raws}
    ordered = [raws_by_id[i].to_dict() for i in source_ids if i in raws_by_id]
    return jsonify({'success': True, 'data': ordered})


@knowledge_wiki_bp.route('/api/wiki/raw-files/<int:raw_id>/preview', methods=['GET'])
@login_required
def preview_raw_file(raw_id):
    """预览 Wiki 原始文件（直接 scope 可见 OR 被某篇可见文章引用 均放行）"""
    from flask import Response
    from urllib.parse import quote

    raw = _can_access_raw_file(current_user, raw_id)
    if not raw:
        return jsonify({'success': False, 'message': '无权访问或文件不存在'}), 403

    fl = FileLibrary.query.get(raw.file_library_id)
    if not fl:
        return jsonify({'success': False, 'message': '原始文件已删除'}), 404

    try:
        content = FileManagerService.read_file_content_auto_decompress(fl)
        if content:
            encoded_name = quote(raw.title or fl.original_filename or 'file')
            return Response(
                content,
                mimetype=fl.mime_type or 'application/octet-stream',
                headers={
                    'Content-Disposition': f"inline; filename*=UTF-8''{encoded_name}",
                }
            )
    except Exception as e:
        logger.error(f'[Wiki] 预览原始文件失败: {e}')

    return jsonify({'success': False, 'message': '读取文件失败'}), 500


@knowledge_wiki_bp.route('/api/wiki/raw-files/<int:raw_id>/download', methods=['GET'])
@login_required
def download_raw_file(raw_id):
    """下载 Wiki 原始文件（直接 scope 可见 OR 被某篇可见文章引用 均放行）"""
    from flask import Response
    from urllib.parse import quote

    raw = _can_access_raw_file(current_user, raw_id)
    if not raw:
        return jsonify({'success': False, 'message': '无权访问或文件不存在'}), 403

    fl = FileLibrary.query.get(raw.file_library_id)
    if not fl:
        return jsonify({'success': False, 'message': '原始文件已删除'}), 404

    try:
        content = FileManagerService.read_file_content_auto_decompress(fl)
        if content:
            encoded_name = quote(raw.title or fl.original_filename or 'file')
            return Response(
                content,
                mimetype=fl.mime_type or 'application/octet-stream',
                headers={
                    'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_name}",
                    'Content-Length': str(len(content)),
                }
            )
    except Exception as e:
        logger.error(f'[Wiki] 下载原始文件失败: {e}')

    return jsonify({'success': False, 'message': '读取文件失败'}), 500


@knowledge_wiki_bp.route('/api/wiki/raw-files/<int:raw_id>', methods=['DELETE'])
@login_required
def delete_raw_file(raw_id):
    """删除原始文件登记 + 磁盘文件。**不会删除已生成的文章**。
    权限：admin/ceo 或文件所有者可删除。
    """
    raw = KnowledgeRawFile.query.get(raw_id)
    if not raw:
        return jsonify({'success': False, 'message': '记录不存在'}), 404
    if not _is_admin() and raw.owner_id != current_user.id:
        return jsonify({'success': False, 'message': '只有文件所有者或管理员可以删除'}), 403

    try:
        storage.delete_raw_file(raw.raw_path)
    except Exception as e:
        logger.warning(f'[Wiki] 删除磁盘文件失败（继续删 DB 记录）: {e}')

    db.session.delete(raw)
    db.session.commit()
    return jsonify({'success': True, 'message': '已删除'})


# ══════════════════════════════════════════════════════════════════
# 文章浏览
# ══════════════════════════════════════════════════════════════════

@knowledge_wiki_bp.route('/api/wiki/articles', methods=['GET'])
@login_required
def list_articles():
    from app.services.wiki.scope import visible_articles_query
    topic = (request.args.get('topic') or '').strip()
    q = visible_articles_query(current_user)
    if topic:
        q = q.filter_by(topic=topic)
    items = q.order_by(KnowledgeWikiArticle.topic, KnowledgeWikiArticle.slug).all()
    return jsonify({'success': True, 'data': [a.to_dict() for a in items]})


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>', methods=['GET'])
@login_required
def get_article(article_id):
    from app.services.wiki.scope import visible_articles_query
    art = visible_articles_query(current_user).filter_by(id=article_id).first()
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404
    return jsonify({'success': True, 'data': art.to_dict(include_content=True)})


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>/asset/<path:rel>')
@login_required
def serve_article_asset(article_id, rel):
    """Serve an image from wiki/<topic>/_assets/<slug>/...

    Guards:
    - login_required (above)
    - 用户必须对该文章有可见权限（复用 visible_articles_query）
    - 路径穿越防护：rel 必须以 _assets/<slug>/ 开头，且解析后必须在 wiki/<topic>/ 目录内
    """
    from app.services.wiki.scope import visible_articles_query

    art = visible_articles_query(current_user).filter(
        KnowledgeWikiArticle.id == article_id
    ).first()
    if art is None:
        # 文章不存在或用户无权限 —— 一律 404，避免泄露存在性
        abort(404)

    expected_prefix = f'_assets/{art.slug}/'
    if '..' in rel or not rel.startswith(expected_prefix):
        abort(400)

    base = (get_wiki_dir() / art.topic).resolve()
    abs_path = (get_wiki_dir() / art.topic / rel).resolve()
    try:
        abs_path.relative_to(base)
    except ValueError:
        abort(400)

    if not abs_path.is_file():
        abort(404)

    return send_file(str(abs_path))


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>/image/<int:index>/replace', methods=['POST'])
@login_required
def replace_article_image_endpoint(article_id, index):
    """替换文章 image_manifest 中指定 index 的图片。

    旧文件备份到 _assets/<slug>/.history/，更新 manifest 条目，并将
    article.manually_edited 置为 True。
    """
    from datetime import datetime

    art = KnowledgeWikiArticle.query.get_or_404(article_id)
    # 图片替换权限严格收紧：仅文章作者 + admin/ceo
    # 不复用 can_manage_article（它放行同部门 department-scope 的部门经理，
    # 范围太宽——图片替换是不可逆的内容改动，不该让非作者的同部门同事动手）
    is_admin = current_user.role in ('admin', 'ceo')
    is_owner = art.owner_id == current_user.id
    if not (is_admin or is_owner):
        return jsonify({'success': False, 'message': '无权编辑此文章（仅作者和管理员可替换图片）'}), 403

    f = request.files.get('image')
    if not f or not (f.mimetype or '').startswith('image/'):
        return jsonify({'success': False, 'message': '请上传图片文件 (image/*)'}), 400

    manifest = list(art.image_manifest or [])
    entry = next((m for m in manifest if m.get('index') == index), None)
    if entry is None:
        return jsonify({'success': False, 'message': f'图片 index={index} 不在 manifest 中'}), 404

    data = f.read()
    MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    if len(data) == 0:
        return jsonify({'success': False, 'message': '上传文件为空'}), 400
    if len(data) > MAX_BYTES:
        return jsonify({'success': False, 'message': f'文件过大 (>{MAX_BYTES // 1024 // 1024}MB)'}), 400

    try:
        new_rel = storage.replace_article_image(art.topic, art.slug, index, data, f.mimetype)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    entry['path'] = new_rel
    entry['manually_replaced'] = True
    entry['replaced_at'] = datetime.utcnow().isoformat()
    entry['sha256'] = storage.sha256_bytes(data)
    entry['size_bytes'] = len(data)
    # 用全新 list[dict] 触发 SQLAlchemy JSON 列变更检测（直接 mutate 嵌套 dict
    # 不会被识别为 dirty）；为安全起见再显式 flag_modified
    from sqlalchemy.orm.attributes import flag_modified
    art.image_manifest = [dict(m) for m in manifest]
    flag_modified(art, 'image_manifest')
    art.manually_edited = True
    db.session.commit()

    logger.info(
        f'[Wiki] user={current_user.id} replaced image article_id={art.id} '
        f'topic={art.topic} slug={art.slug} index={index} '
        f'size={len(data)} sha256={entry["sha256"][:8]}'
    )
    return jsonify({'success': True, 'image': entry, 'manually_edited': True})


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>', methods=['DELETE'])
@login_required
def delete_article(article_id):
    """删除文章（磁盘 + DB）。

    权限：admin/ceo、文章所有者、或管理同部门的部门经理。
    """
    from app.services.wiki.scope import can_manage_article

    art = KnowledgeWikiArticle.query.get(article_id)
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404

    if not can_manage_article(current_user, art):
        return jsonify({'success': False, 'message': '没有权限删除此文章'}), 403

    # 删除磁盘文件
    try:
        storage.delete_article_file(art.file_path)
    except Exception as e:
        logger.warning(f'[Wiki] 删除文章磁盘文件失败(继续删 DB): {e}')

    db.session.delete(art)
    db.session.commit()
    logger.info(f'[Wiki] user={current_user.id} 删除文章 id={article_id} title={art.title}')
    return jsonify({'success': True, 'message': '文章已删除'})


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>/scope', methods=['PATCH'])
@login_required
def change_article_scope(article_id):
    """调整文章 scope 等级。

    权限规则：
    - admin/ceo: 可任意调整
    - 普通用户 / 部门经理: 可在 personal ↔ department 之间直接调整自己可管理的文章
    - → company / system: 需提交晋升申请，由 admin/ceo 审批
    """
    from app.services.wiki.scope import can_manage_article

    art = KnowledgeWikiArticle.query.get(article_id)
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404

    data = request.get_json(silent=True) or {}
    new_scope = data.get('scope', '').strip()
    valid_scopes = ('personal', 'department', 'company', 'system')
    if new_scope not in valid_scopes:
        return jsonify({'success': False, 'message': f'无效 scope: {new_scope}'}), 400

    if new_scope == art.scope:
        return jsonify({'success': True, 'message': '等级未变化', 'data': art.to_dict()})

    # 权限检查
    if not can_manage_article(current_user, art):
        return jsonify({'success': False, 'message': '没有权限管理此文章'}), 403

    # 非 admin/ceo：只有 company / system 需要审批，personal ↔ department 自由切换
    if current_user.role not in ('admin', 'ceo') and new_scope in ('company', 'system'):
        return jsonify({
            'success': False,
            'needs_approval': True,
            'message': '升级到公司 / 系统级别需要提交晋升申请',
        }), 403

    old_scope = art.scope
    art.scope = new_scope
    # 确保 owner 字段完整（"哪里来回哪里去"）
    if not art.owner_id:
        art.owner_id = current_user.id
    if not art.owner_department and art.owner:
        art.owner_department = art.owner.department

    # 发放积分：文章首次从私有变为共享（任意共享状态）
    if new_scope != 'personal' and old_scope == 'personal' and art.owner_id:
        try:
            from app.services.points_service import award_points
            award_points(
                user_id=art.owner_id,
                behavior_code='wiki_share',
                source_type='wiki_article',
                source_id=art.id,
                context=art.title
            )
        except Exception as pts_err:
            logger.warning(f"发放wiki_share积分失败: {pts_err}")

    db.session.commit()

    logger.info(f'[Wiki] user={current_user.id} 调整文章 id={article_id} scope: {old_scope} → {new_scope}')
    return jsonify({'success': True, 'message': f'已调整为{new_scope}级别', 'data': art.to_dict()})


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>/topic', methods=['PATCH'])
@login_required
def change_article_topic(article_id):
    """调整文章所属 topic（把文章从一个 topic 移到另一个 topic）。

    权限：文章所有者、admin/ceo、或管理同部门的部门经理。
    """
    from app.services.wiki.scope import can_manage_article

    art = KnowledgeWikiArticle.query.get(article_id)
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404

    data = request.get_json(silent=True) or {}
    new_topic = (data.get('topic') or '').strip()
    if not new_topic:
        return jsonify({'success': False, 'message': 'topic 不能为空'}), 400

    try:
        storage.validate_topic_slug(new_topic, art.slug)
    except storage.WikiPathError as e:
        return jsonify({'success': False, 'message': f'topic 格式非法: {e}'}), 400

    if new_topic == art.topic:
        return jsonify({'success': True, 'message': 'topic 未变化', 'data': art.to_dict()})

    if not can_manage_article(current_user, art):
        return jsonify({'success': False, 'message': '没有权限管理此文章'}), 403

    conflict = KnowledgeWikiArticle.query.filter_by(topic=new_topic, slug=art.slug).first()
    if conflict:
        return jsonify({
            'success': False,
            'message': f'目标 topic "{new_topic}" 下已存在同名文章，请先修改标题再切换',
        }), 400

    old_topic = art.topic
    try:
        content = storage.read_article_content(art.file_path)
        new_file_path = storage.write_article(new_topic, art.slug, content)
        storage.delete_article_file(art.file_path)
    except Exception as e:
        logger.exception(f'[Wiki] 移动文章文件失败: {e}')
        return jsonify({'success': False, 'message': f'移动文件失败: {e}'}), 500

    art.topic = new_topic
    art.file_path = new_file_path
    db.session.commit()

    try:
        storage.append_log(
            'move-topic',
            f'- article_id={art.id} title={art.title!r}\n'
            f'- {old_topic}/{art.slug} → {new_topic}/{art.slug}\n'
            f'- by user={current_user.id}'
        )
    except Exception as e:
        logger.warning(f'[Wiki] 写 log.md 失败(忽略): {e}')

    logger.info(f'[Wiki] user={current_user.id} 调整文章 id={article_id} topic: {old_topic} → {new_topic}')
    return jsonify({'success': True, 'message': f'已移到 {new_topic}', 'data': art.to_dict()})


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>/promote', methods=['POST'])
@login_required
def submit_promotion_request(article_id):
    """提交文章晋升申请。

    自动确定审核人：
    - → company: admin/ceo
    - → system: admin/ceo
    （→ department 不再需要审批，直接 PATCH scope 即可。）
    """
    try:
        from app.services.wiki.scope import visible_articles_query
        art = visible_articles_query(current_user).filter_by(id=article_id).first()
        if not art:
            return jsonify({'success': False, 'message': '文章不存在'}), 404

        data = request.get_json(silent=True) or {}
        to_scope = data.get('to_scope', '').strip()
        request_note = data.get('reason', '').strip()

        valid_scopes = ('company', 'system')
        if to_scope not in valid_scopes:
            return jsonify({'success': False, 'message': '无效的目标等级（仅 company / system 需要审批）'}), 400

        if not request_note:
            return jsonify({'success': False, 'message': '请填写申请理由'}), 400

        # 检查是否已有 pending 申请
        existing = KnowledgePromotionRequest.query.filter_by(
            article_id=article_id, status='pending'
        ).first()
        if existing:
            return jsonify({'success': False, 'message': '该文章已有待审核的晋升申请'}), 400

        # 确定审核人
        reviewer_id = _find_promotion_reviewer(to_scope, current_user)
        if not reviewer_id:
            return jsonify({'success': False, 'message': '找不到合适的审核人，请联系管理员'}), 400

        # 确保文章 owner_department 已填充
        if not art.owner_department:
            art.owner_department = current_user.department

        # 创建申请（先 flush 拿到 ID）
        req = KnowledgePromotionRequest(
            article_id=article_id,
            from_scope=art.scope,
            to_scope=to_scope,
            requested_by=current_user.id,
            request_note=request_note,
            assigned_to=reviewer_id,
        )
        db.session.add(req)
        db.session.flush()  # 分配 req.id

        # 通知审核人
        scope_labels = {'department': '部门', 'company': '公司', 'system': '系统'}
        requester_name = current_user.real_name or current_user.username
        reviewer = db.session.get(User, reviewer_id)
        reviewer_name = (reviewer.real_name or reviewer.username) if reviewer else '审核人'

        msg = Message(
            message_type='wiki_promotion_request',
            sender_id=current_user.id,
            recipient_id=reviewer_id,
            title=f'知识库晋升申请: {art.title}',
            content=f'{requester_name} 申请将「{art.title}」提升为{scope_labels.get(to_scope, to_scope)}级',
            related_object_type='wiki_promotion',
            related_object_id=article_id,
            extra_data={
                'promotion_request_id': req.id,
                'article_id': article_id,
                'article_title': art.title,
                'from_scope': art.scope,
                'to_scope': to_scope,
            },
        )
        db.session.add(msg)

        # 通知申请人（确认已提交）
        msg_self = Message(
            message_type='wiki_promotion_submitted',
            sender_id=current_user.id,
            recipient_id=current_user.id,
            title=f'晋升申请已提交',
            content=f'您的「{art.title}」晋升申请已提交给 {reviewer_name} 审核',
            related_object_type='wiki_promotion',
            related_object_id=article_id,
            extra_data={'article_id': article_id},
        )
        db.session.add(msg_self)

        db.session.commit()

        logger.info(f'[Wiki] user={current_user.id} 提交晋升申请 article={article_id} '
                    f'{art.scope}→{to_scope} reviewer={reviewer_id}')
        return jsonify({'success': True, 'message': f'申请已提交给 {reviewer_name}', 'data': req.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f'[Wiki] 提交晋升申请失败: {e}', exc_info=True)
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500


@knowledge_wiki_bp.route('/api/wiki/promotion-requests/<int:request_id>', methods=['PATCH'])
@login_required
def review_promotion_request(request_id):
    """审核晋升申请（通过/拒绝）。"""
    try:
        req = KnowledgePromotionRequest.query.get(request_id)
        if not req:
            return jsonify({'success': False, 'message': '申请不存在'}), 404

        if req.status != 'pending':
            return jsonify({'success': False, 'message': '该申请已处理'}), 400

        # 只有指定审核人或 admin/ceo 可以审核
        if req.assigned_to != current_user.id and current_user.role not in ('admin', 'ceo'):
            return jsonify({'success': False, 'message': '没有审核权限'}), 403

        data = request.get_json(silent=True) or {}
        action = data.get('action', '').strip()
        review_note = data.get('review_note', '').strip()

        if action not in ('approve', 'reject'):
            return jsonify({'success': False, 'message': '无效的审核动作'}), 400

        from datetime import datetime
        from zoneinfo import ZoneInfo

        req.status = 'approved' if action == 'approve' else 'rejected'
        req.reviewed_by = current_user.id
        req.review_note = review_note
        req.reviewed_at = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)

        # 如果通过，实际变更 scope
        art = req.article
        if action == 'approve' and art:
            old_scope = art.scope
            art.scope = req.to_scope
            # 确保 owner_department 填充（降级时自动回到原部门）
            if not art.owner_department and art.owner:
                art.owner_department = art.owner.department
            logger.info(f'[Wiki] 晋升审核通过 article={art.id} {old_scope}→{req.to_scope} by user={current_user.id}')

            # 发放积分：文章首次从私有变为共享（任意共享状态）
            if req.to_scope != 'personal' and old_scope == 'personal' and art.owner_id:
                try:
                    from app.services.points_service import award_points
                    award_points(
                        user_id=art.owner_id,
                        behavior_code='wiki_share',
                        source_type='wiki_article',
                        source_id=art.id,
                        context=art.title
                    )
                except Exception as pts_err:
                    logger.warning(f"发放wiki_share积分失败: {pts_err}")

        # 通知申请人
        scope_labels = {'personal': '个人', 'department': '部门', 'company': '公司', 'system': '系统'}
        reviewer_name = current_user.real_name or current_user.username
        action_text = '通过' if action == 'approve' else '拒绝'
        msg = Message(
            message_type='wiki_promotion_result',
            sender_id=current_user.id,
            recipient_id=req.requested_by,
            title=f'晋升申请已{action_text}',
            content=f'{reviewer_name} 已{action_text}「{art.title}」提升为{scope_labels.get(req.to_scope, req.to_scope)}级'
                    + (f'，备注：{review_note}' if review_note else ''),
            related_object_type='wiki_promotion',
            related_object_id=art.id if art else None,
            extra_data={'article_id': art.id if art else None, 'action': action},
        )
        db.session.add(msg)
        db.session.commit()

        return jsonify({'success': True, 'message': f'已{action_text}', 'data': req.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f'[Wiki] 审核晋升申请失败: {e}', exc_info=True)
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500


@knowledge_wiki_bp.route('/api/wiki/promotion-requests', methods=['GET'])
@login_required
def list_promotion_requests():
    """获取与当前用户相关的晋升申请列表。"""
    try:
        q = KnowledgePromotionRequest.query
        # 普通用户只看自己提交的和自己需要审核的
        if current_user.role not in ('admin', 'ceo'):
            q = q.filter(
                db.or_(
                    KnowledgePromotionRequest.requested_by == current_user.id,
                    KnowledgePromotionRequest.assigned_to == current_user.id,
                )
            )
        requests = q.order_by(KnowledgePromotionRequest.created_at.desc()).limit(50).all()
        return jsonify({'success': True, 'data': [r.to_dict() for r in requests]})
    except Exception as e:
        db.session.rollback()
        logger.error(f'[Wiki] 查询晋升申请失败: {e}', exc_info=True)
        return jsonify({'success': True, 'data': []})


def _find_promotion_reviewer(to_scope: str, requester) -> int | None:
    """根据目标 scope 确定审核人。

    规则：
    - department: 本部门经理（如果没有，找 admin/ceo）
    - company: admin/ceo
    - system: admin/ceo
    """
    if to_scope == 'department' and requester.department:
        # 找本部门经理
        # 注意：User.is_active 是 @property（admin 永远 True），
        # 实际列名是 _is_active（见 app/models/user.py:36），SQL 必须用 _is_active
        manager = User.query.filter_by(
            department=requester.department,
            is_department_manager=True,
        ).filter(
            User._is_active == True,
            User.id != requester.id,
        ).first()
        if manager:
            return manager.id

    # company/system 或找不到部门经理 → 找 admin/ceo
    admin = User.query.filter(
        User.role.in_(['admin', 'ceo']),
        User._is_active == True,
        User.id != requester.id,
    ).first()
    if admin:
        return admin.id

    return None


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>/recompile', methods=['POST'])
@login_required
def recompile_article(article_id):
    """重新编译文章关联的 raw file。

    权限：admin/ceo、文章所有者、或管理同部门的部门经理。
    """
    from app.services.wiki.scope import can_manage_article

    art = KnowledgeWikiArticle.query.get(article_id)
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404

    if not can_manage_article(current_user, art):
        return jsonify({'success': False, 'message': '没有权限重新编译此文章'}), 403

    raw_ids = art.source_raw_ids or []
    if not raw_ids:
        return jsonify({'success': False, 'message': '该文章没有关联的原始文件'}), 400

    # 编译第一个关联 raw file
    raw_id = raw_ids[0]
    raw = KnowledgeRawFile.query.get(raw_id)
    if not raw:
        return jsonify({'success': False, 'message': f'原始文件 raw_id={raw_id} 不存在'}), 404

    try:
        result = compiler.ingest_raw_file(raw_id)
    except compiler.IngestError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception:
        logger.exception(f'[Wiki] recompile 失败 article_id={article_id} raw_id={raw_id}')
        return jsonify({'success': False, 'message': '重新编译失败'}), 500

    return jsonify({'success': True, 'data': result})


@knowledge_wiki_bp.route('/api/wiki/tree', methods=['GET'])
@login_required
def get_tree():
    """返回 topic → [articles] 的树结构，供前端侧栏渲染。

    每篇文章带 scope/owner_name 字段，前端用于显示标签和过滤。
    """
    from app.services.wiki.scope import visible_articles_query, can_manage_article
    items = (
        visible_articles_query(current_user)
        .order_by(KnowledgeWikiArticle.topic, KnowledgeWikiArticle.slug)
        .all()
    )
    tree: dict[str, list[dict]] = {}
    for art in items:
        tree.setdefault(art.topic, []).append({
            'id': art.id,
            'slug': art.slug,
            'title': art.title,
            'summary': art.summary,
            'source_raw_ids': art.source_raw_ids or [],
            'updated_at': art.updated_at.isoformat() if art.updated_at else None,
            'scope': art.scope,
            'owner_id': art.owner_id,
            'owner_name': (art.owner.real_name or art.owner.username) if art.owner else None,
            'is_mine': art.owner_id == current_user.id,
            'can_manage': can_manage_article(current_user, art),
        })
    return jsonify({'success': True, 'data': tree})


@knowledge_wiki_bp.route('/api/wiki/topics', methods=['GET'])
@login_required
def list_topics():
    """返回 admin 预定义的 topic 列表（按 sort_order, name 排序）。

    前端上传 / 加入 Wiki 弹窗从此接口拉取可用分类。
    """
    topics = KnowledgeTopic.query.order_by(
        KnowledgeTopic.sort_order.asc(),
        KnowledgeTopic.name.asc(),
    ).all()
    # 兼容旧前端：返回纯字符串数组
    return jsonify({'success': True, 'data': [t.name for t in topics]})


@knowledge_wiki_bp.route('/api/wiki/topics/detail', methods=['GET'])
@login_required
def list_topics_detail():
    """返回 topic 详细列表（含 id / description / sort_order），供管理面板使用。"""
    topics = KnowledgeTopic.query.order_by(
        KnowledgeTopic.sort_order.asc(),
        KnowledgeTopic.name.asc(),
    ).all()
    return jsonify({'success': True, 'data': [t.to_dict() for t in topics]})


@knowledge_wiki_bp.route('/api/wiki/admin/topics', methods=['POST'])
@login_required
def create_topic():
    """管理员新建分类目录。

    Body: { name: str, description?: str, sort_order?: int }
    """
    err = _require_admin()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    description = (data.get('description') or '').strip() or None
    sort_order = int(data.get('sort_order') or 0)

    if not name:
        return jsonify({'success': False, 'message': 'name 必填'}), 400

    try:
        storage.validate_topic(name)
    except storage.WikiPathError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    if KnowledgeTopic.query.filter_by(name=name).first():
        return jsonify({'success': False, 'message': f'分类「{name}」已存在'}), 409

    try:
        topic = KnowledgeTopic(
            name=name,
            description=description,
            sort_order=sort_order,
            created_by=current_user.id,
        )
        db.session.add(topic)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception('[Wiki] create_topic failed')
        return jsonify({'success': False, 'message': f'创建失败: {e}'}), 500

    logger.info(f'[Wiki] user={current_user.id} 新建 topic={name}')
    return jsonify({'success': True, 'data': topic.to_dict()})


@knowledge_wiki_bp.route('/api/wiki/admin/topics/<int:topic_id>', methods=['PATCH'])
@login_required
def update_topic(topic_id):
    """管理员编辑分类目录（不允许改 name，只能改 description / sort_order）。

    Body: { description?: str, sort_order?: int }
    改 name 涉及物理目录和所有引用的迁移，暂不支持。
    """
    err = _require_admin()
    if err:
        return err

    topic = KnowledgeTopic.query.get(topic_id)
    if not topic:
        return jsonify({'success': False, 'message': '分类不存在'}), 404

    data = request.get_json(silent=True) or {}
    if 'description' in data:
        v = (data.get('description') or '').strip()
        topic.description = v or None
    if 'sort_order' in data:
        try:
            topic.sort_order = int(data.get('sort_order') or 0)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'sort_order 必须是整数'}), 400

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception('[Wiki] update_topic failed')
        return jsonify({'success': False, 'message': f'更新失败: {e}'}), 500

    return jsonify({'success': True, 'data': topic.to_dict()})


@knowledge_wiki_bp.route('/api/wiki/admin/topics/<int:topic_id>', methods=['DELETE'])
@login_required
def delete_topic(topic_id):
    """管理员删除分类目录。仅在该分类下没有任何原始文件和文章时允许。"""
    err = _require_admin()
    if err:
        return err

    topic = KnowledgeTopic.query.get(topic_id)
    if not topic:
        return jsonify({'success': False, 'message': '分类不存在'}), 404

    raw_count = db.session.query(KnowledgeRawFile).filter_by(topic=topic.name).count()
    art_count = db.session.query(KnowledgeWikiArticle).filter_by(topic=topic.name).count()
    if raw_count or art_count:
        return jsonify({
            'success': False,
            'message': f'分类「{topic.name}」下仍有 {raw_count} 个原始文件、{art_count} 篇文章，请先清空',
        }), 409

    try:
        db.session.delete(topic)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception('[Wiki] delete_topic failed')
        return jsonify({'success': False, 'message': f'删除失败: {e}'}), 500

    logger.info(f'[Wiki] user={current_user.id} 删除 topic={topic.name}')
    return jsonify({'success': True})


@knowledge_wiki_bp.route('/api/wiki/index', methods=['GET'])
@login_required
def get_index():
    ensure_wiki_structure()
    return jsonify({'success': True, 'content': storage.read_index()})


# ══════════════════════════════════════════════════════════════════
# 问答
# ══════════════════════════════════════════════════════════════════

@knowledge_wiki_bp.route('/api/wiki/query', methods=['POST'])
@login_required
def query_endpoint():
    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()
    topic = (data.get('topic') or '').strip() or None
    top_k = int(data.get('top_k') or 5)

    if not question:
        return jsonify({'success': False, 'message': '问题不能为空'}), 400

    try:
        result = querier.query_wiki(question, top_k=top_k, topic=topic,
                                    current_user_id=current_user.id)
    except querier.QueryError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception:
        logger.exception(f'[Wiki] query 失败: {question[:100]}')
        return jsonify({'success': False, 'message': '问答服务异常，请查看服务器日志'}), 500

    # 富化:命中的"课件知识"文章(slug 以 -deck 结尾)→ 相关页缩略图深链,
    # 让答案里能直接看到演示页、点击新标签跳到课件对应页。
    try:
        from app.services import course_knowledge
        deck_pages, seen = [], set()
        for ca in (result.get('cited_articles') or []):
            slug = ca.get('slug') or ''
            if not slug.endswith('-deck'):
                continue
            key = slug[:-5]
            if key in seen:
                continue
            course, path = _find_course(key)
            if not course:
                continue
            seen.add(key)
            pages = _get_course_pages(key, path)
            for pg, lbl in course_knowledge.relevant_pages(question, pages, top=3):
                deck_pages.append({
                    'key': key, 'page': pg, 'label': lbl,
                    'course_title': course.get('title'),
                    'thumb_url': url_for('knowledge_wiki.course_thumb', course_key=key, page=pg),
                    'play_url': url_for('knowledge_wiki.play_course', course_key=key) + '#' + str(pg),
                })
        result['deck_pages'] = deck_pages
    except Exception:
        logger.exception('[Wiki] deck_pages 富化失败(忽略)')
        result['deck_pages'] = []

    return jsonify({'success': True, 'data': result})


# ══════════════════════════════════════════════════════════════════
# 质检
# ══════════════════════════════════════════════════════════════════

@knowledge_wiki_bp.route('/api/wiki/lint', methods=['POST'])
@login_required
def lint_endpoint():
    guard = _require_admin()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    apply_fixes = bool(data.get('apply_auto_fixes'))
    topic = (data.get('topic') or '').strip() or None

    try:
        result = linter.lint_wiki(apply_auto_fixes=apply_fixes, topic=topic)
    except linter.LintError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception:
        logger.exception('[Wiki] lint 失败')
        return jsonify({'success': False, 'message': '质检服务异常，请查看服务器日志'}), 500

    return jsonify({'success': True, 'data': result})


# ══════════════════════════════════════════════════════════════════
# 文件 Wiki 状态查询（供文件管理器用）
# ══════════════════════════════════════════════════════════════════

@knowledge_wiki_bp.route('/api/wiki/file-wiki-status', methods=['POST'])
@login_required
def file_wiki_status():
    """查询一组 file_library_id 是否已在 Wiki 中（以及编译状态）。"""
    data = request.get_json(silent=True) or {}
    fl_ids = data.get('file_library_ids') or []
    if not fl_ids:
        return jsonify({'success': True, 'data': {}})

    raws = KnowledgeRawFile.query.filter(
        KnowledgeRawFile.file_library_id.in_(fl_ids)
    ).all()

    status_map = {}
    for raw in raws:
        fid = str(raw.file_library_id)
        if fid not in status_map or (raw.created_at and status_map.get(fid, {}).get('_t') and raw.created_at > status_map[fid]['_t']):
            status_map[fid] = {
                'in_wiki': raw.ingest_status == 'ingested',
                'raw_id': raw.id,
                'status': raw.ingest_status,
                'topic': raw.topic,
                '_t': raw.created_at,
            }

    for v in status_map.values():
        v.pop('_t', None)
    for fid in fl_ids:
        if str(fid) not in status_map:
            status_map[str(fid)] = {'in_wiki': False}

    return jsonify({'success': True, 'data': status_map})


# ══════════════════════════════════════════════════════════════════
# 异步编译 + 系统通知
# ══════════════════════════════════════════════════════════════════

def _async_ingest_and_notify(raw_id: int, user_id: int, app):
    """后台线程：编译 + 完成后发 PMA 系统通知。"""
    with app.app_context():
        try:
            result = compiler.ingest_raw_file(raw_id)
            ops = result.get('operations') or []
            article_count = len([o for o in ops if o.get('action') in ('create', 'update')])
            raw = db.session.get(KnowledgeRawFile, raw_id)
            title = raw.title if raw else f'raw_id={raw_id}'

            first_article_id = None
            if ops:
                art = KnowledgeWikiArticle.query.filter_by(
                    topic=ops[0].get('topic'), slug=ops[0].get('slug')
                ).first()
                if art:
                    first_article_id = art.id

            msg = Message(
                message_type='wiki_compile',
                sender_id=user_id,
                recipient_id=user_id,
                title=f'Wiki 编译完成：{title}',
                content=f'产生 {article_count} 篇文章',
                related_object_type='wiki_article',
                related_object_id=first_article_id,
                extra_data={'raw_id': raw_id, 'article_count': article_count, 'status': 'success'},
            )
            db.session.add(msg)
            db.session.commit()
            logger.info(f'[Wiki async] raw_id={raw_id} 编译成功，已通知 user_id={user_id}')

        except Exception as e:
            logger.exception(f'[Wiki async] raw_id={raw_id} 编译失败')
            try:
                raw = db.session.get(KnowledgeRawFile, raw_id)
                title = raw.title if raw else f'raw_id={raw_id}'
                msg = Message(
                    message_type='wiki_compile',
                    sender_id=user_id,
                    recipient_id=user_id,
                    title=f'Wiki 编译失败：{title}',
                    content=str(e)[:200],
                    related_object_type='wiki_raw_file',
                    related_object_id=raw_id,
                    extra_data={'raw_id': raw_id, 'status': 'error', 'error': str(e)[:500]},
                )
                db.session.add(msg)
                db.session.commit()
            except Exception:
                logger.exception(f'[Wiki async] 发送失败通知也失败了')


# ══════════════════════════════════════════════════════════════════
# 文章分享（跨部门/跨人/跨企业）
# ══════════════════════════════════════════════════════════════════

def _can_manage_shares(user, article) -> bool:
    """谁能管理分享授权：admin/ceo 或文章所有者。"""
    if user.role in ('admin', 'ceo'):
        return True
    return article.owner_id == user.id


def _serialize_grant(grant) -> dict:
    """给前端返回的授权信息，目标侧附上显示名。"""
    display_target = grant.grant_target
    if grant.grant_type == 'user':
        try:
            u = User.query.get(int(grant.grant_target))
            if u:
                display_target = u.real_name or u.username
        except (ValueError, TypeError):
            pass
    return {
        'id': grant.id,
        'grant_type': grant.grant_type,
        'grant_target': grant.grant_target,
        'display_target': display_target,
        'granted_by': grant.granted_by,
        'granter_name': (grant.granter.real_name or grant.granter.username) if grant.granter else None,
        'created_at': grant.created_at.isoformat() if grant.created_at else None,
    }


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>/shares', methods=['GET'])
@login_required
def list_article_shares(article_id):
    """列出文章当前的所有分享授权。"""
    art = KnowledgeWikiArticle.query.get(article_id)
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404
    if not _can_manage_shares(current_user, art):
        return jsonify({'success': False, 'message': '没有权限管理此文章的分享'}), 403

    grants = KnowledgeShareGrant.query.filter_by(article_id=article_id).order_by(
        KnowledgeShareGrant.created_at.desc()
    ).all()
    return jsonify({'success': True, 'data': [_serialize_grant(g) for g in grants]})


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>/shares', methods=['POST'])
@login_required
def add_article_share(article_id):
    """新增一条分享授权。

    请求体：{ grant_type: 'user'|'department'|'company', grant_target: str }
    - grant_type=user: grant_target 为 user_id 字符串
    - grant_type=department: grant_target 为部门名
    - grant_type=company: grant_target 为企业名 (users.company_name)
    """
    art = KnowledgeWikiArticle.query.get(article_id)
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404
    if not _can_manage_shares(current_user, art):
        return jsonify({'success': False, 'message': '没有权限管理此文章的分享'}), 403

    data = request.get_json(silent=True) or {}
    grant_type = (data.get('grant_type') or '').strip()
    grant_target = (data.get('grant_target') or '').strip()

    if grant_type not in ('user', 'department', 'company'):
        return jsonify({'success': False, 'message': '无效的授权类型'}), 400
    if not grant_target:
        return jsonify({'success': False, 'message': '请指定授权目标'}), 400

    # 校验目标存在
    if grant_type == 'user':
        try:
            uid = int(grant_target)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': '用户 ID 无效'}), 400
        target_user = User.query.get(uid)
        if not target_user:
            return jsonify({'success': False, 'message': '用户不存在'}), 400
        # 不允许分享给自己
        if target_user.id == art.owner_id:
            return jsonify({'success': False, 'message': '文章所有者已拥有访问权限'}), 400
    elif grant_type == 'department':
        exists = db.session.query(User.id).filter_by(department=grant_target).first()
        if not exists:
            return jsonify({'success': False, 'message': '部门不存在'}), 400
    elif grant_type == 'company':
        exists = db.session.query(User.id).filter_by(company_name=grant_target).first()
        if not exists:
            return jsonify({'success': False, 'message': '企业不存在'}), 400

    # 去重
    dup = KnowledgeShareGrant.query.filter_by(
        article_id=article_id,
        grant_type=grant_type,
        grant_target=grant_target,
    ).first()
    if dup:
        return jsonify({'success': False, 'message': '该目标已有授权'}), 400

    grant = KnowledgeShareGrant(
        article_id=article_id,
        grant_type=grant_type,
        grant_target=grant_target,
        granted_by=current_user.id,
    )
    db.session.add(grant)
    db.session.commit()

    logger.info(
        f'[Wiki] user={current_user.id} 给文章 id={article_id} 新增分享 '
        f'type={grant_type} target={grant_target}'
    )
    return jsonify({'success': True, 'message': '授权已添加', 'data': _serialize_grant(grant)})


@knowledge_wiki_bp.route(
    '/api/wiki/articles/<int:article_id>/shares/<int:grant_id>',
    methods=['DELETE'],
)
@login_required
def delete_article_share(article_id, grant_id):
    """撤销一条分享授权。"""
    art = KnowledgeWikiArticle.query.get(article_id)
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404
    if not _can_manage_shares(current_user, art):
        return jsonify({'success': False, 'message': '没有权限管理此文章的分享'}), 403

    grant = KnowledgeShareGrant.query.filter_by(id=grant_id, article_id=article_id).first()
    if not grant:
        return jsonify({'success': False, 'message': '授权记录不存在'}), 404

    db.session.delete(grant)
    db.session.commit()

    logger.info(f'[Wiki] user={current_user.id} 撤销文章 id={article_id} 的分享 grant_id={grant_id}')
    return jsonify({'success': True, 'message': '授权已撤销'})


@knowledge_wiki_bp.route('/api/wiki/share-targets', methods=['GET'])
@login_required
def search_share_targets():
    """搜索可选的分享目标（给前端下拉补全用）。

    参数：
      - type: 'user' | 'department' | 'company'
      - q: 搜索关键字（模糊匹配）
      - limit: 返回条数上限（默认 20）
    """
    target_type = (request.args.get('type') or '').strip()
    q = (request.args.get('q') or '').strip()
    try:
        limit = min(int(request.args.get('limit', 20)), 50)
    except (ValueError, TypeError):
        limit = 20

    if target_type not in ('user', 'department', 'company'):
        return jsonify({'success': False, 'message': '无效的 type'}), 400

    results = []
    if target_type == 'user':
        query = User.query.filter(User._is_active == True)  # noqa: E712
        if q:
            like = f'%{q}%'
            query = query.filter(
                db.or_(
                    User.username.ilike(like),
                    User.real_name.ilike(like),
                )
            )
        users = query.order_by(User.real_name.nullslast(), User.username).limit(limit).all()
        results = [
            {
                'value': str(u.id),
                'label': u.real_name or u.username,
                'sub': f"{u.department or ''} {u.company_name or ''}".strip(),
            }
            for u in users
        ]
    elif target_type == 'department':
        query = db.session.query(User.department).filter(User.department.isnot(None))
        if q:
            query = query.filter(User.department.ilike(f'%{q}%'))
        rows = query.distinct().order_by(User.department).limit(limit).all()
        results = [{'value': r[0], 'label': r[0], 'sub': ''} for r in rows if r[0]]
    elif target_type == 'company':
        query = db.session.query(User.company_name).filter(User.company_name.isnot(None))
        if q:
            query = query.filter(User.company_name.ilike(f'%{q}%'))
        rows = query.distinct().order_by(User.company_name).limit(limit).all()
        results = [{'value': r[0], 'label': r[0], 'sub': ''} for r in rows if r[0]]

    return jsonify({'success': True, 'data': results})


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>/citation-click', methods=['POST'])
@login_required
def wiki_citation_click(article_id):
    """记录问答引用链接被点击，向文章作者发放 wiki_link_opened 积分（不计自己点击）。"""
    from datetime import date
    from app.models.knowledge_wiki import KnowledgeWikiArticle
    article = KnowledgeWikiArticle.query.get_or_404(article_id)
    if article.owner_id and article.owner_id != current_user.id:
        try:
            from app.services.points_service import award_points
            award_points(
                user_id=article.owner_id,
                behavior_code='wiki_link_opened',
                source_type='wiki_click',
                source_id=f'{article_id}_{current_user.id}_{date.today().isoformat()}',
                context=article.title,
            )
        except Exception as _pts_err:
            logger.warning(f'wiki_link_opened积分发放失败: {_pts_err}')
    return jsonify({'success': True})
