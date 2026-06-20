"""Office 文档预览：调用 LibreOffice headless 将 doc/docx/ppt/pptx 转 PDF 并按 sha256 缓存。"""
from __future__ import annotations

import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
import threading

logger = logging.getLogger(__name__)

OFFICE_MIME_PREFIXES = (
    'application/msword',
    'application/vnd.ms-word',
    'application/vnd.openxmlformats-officedocument.wordprocessingml',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml',
)
OFFICE_EXTS = ('.doc', '.docx', '.ppt', '.pptx')

CACHE_DIR = os.environ.get('OFFICE_PREVIEW_CACHE_DIR') or os.path.join(
    tempfile.gettempdir(), 'pma_office_preview'
)
SOFFICE_TIMEOUT_SEC = int(os.environ.get('OFFICE_PREVIEW_TIMEOUT', '60'))

_convert_lock = threading.Lock()


def is_office_file(*, mime_type: str | None = None, filename: str | None = None) -> bool:
    if mime_type:
        m = mime_type.lower()
        if any(m.startswith(p) for p in OFFICE_MIME_PREFIXES):
            return True
    if filename:
        n = filename.lower()
        if n.endswith(OFFICE_EXTS):
            return True
    return False


def _soffice_binary() -> str | None:
    return (
        shutil.which('soffice')
        or shutil.which('libreoffice')
        or os.environ.get('SOFFICE_BIN')
    )


def _cache_path(sha256: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f'{sha256}.pdf')


def get_or_convert_pdf(*, content: bytes, sha256: str, filename: str) -> tuple[bool, str]:
    """返回 (success, path_or_error_message)。命中缓存则直接返回路径。

    路由：优先调 Mac mini office-convert 服务（PMA_OFFICE_CONVERT_URL）；
    未配置则回退到本地 soffice subprocess（开发机 / 老部署兼容）。
    """
    cached = _cache_path(sha256)
    if os.path.exists(cached) and os.path.getsize(cached) > 0:
        return True, cached

    service_url = os.environ.get('PMA_OFFICE_CONVERT_URL', '').rstrip('/')

    if service_url:
        # ── 远程路径：HTTP POST 给 Mac mini office_convert.py ──
        import requests as _http
        try:
            resp = _http.post(
                f"{service_url}/convert",
                files={'file': (filename, content, 'application/octet-stream')},
                data={'target': 'pdf'},
                timeout=120,
            )
        except _http.exceptions.RequestException as e:
            logger.error('office-convert service unreachable: %s', e)
            return False, f'文档转换服务不可达: {e}'

        if resp.status_code != 200:
            logger.error('office-convert service error %s: %s', resp.status_code, resp.text[:300])
            return False, f'文档转换失败 HTTP {resp.status_code}'

        # 并发保护：拿到 PDF 再写缓存（写入用临时文件 + rename 避免半成品）
        tmp_out = cached + '.tmp'
        with open(tmp_out, 'wb') as f:
            f.write(resp.content)
        os.replace(tmp_out, cached)
        return True, cached

    # ── 本地 fallback 路径：subprocess soffice ──
    soffice = _soffice_binary()
    if not soffice:
        return False, 'LibreOffice (soffice) 未安装；请在 Docker 镜像内安装 libreoffice 或配置 PMA_OFFICE_CONVERT_URL'

    # 串行执行避免 LibreOffice 并发实例冲突
    with _convert_lock:
        if os.path.exists(cached) and os.path.getsize(cached) > 0:
            return True, cached

        with tempfile.TemporaryDirectory(prefix='pma_office_') as workdir:
            ext = os.path.splitext(filename)[1].lower() or '.bin'
            src = os.path.join(workdir, f'src{ext}')
            with open(src, 'wb') as f:
                f.write(content)

            try:
                proc = subprocess.run(
                    [
                        soffice, '--headless', '--norestore', '--nologo',
                        '--convert-to', 'pdf',
                        '--outdir', workdir,
                        src,
                    ],
                    capture_output=True,
                    timeout=SOFFICE_TIMEOUT_SEC,
                )
            except subprocess.TimeoutExpired:
                return False, f'LibreOffice 转换超时（>{SOFFICE_TIMEOUT_SEC}s）'
            except FileNotFoundError:
                return False, 'LibreOffice 启动失败'

            if proc.returncode != 0:
                stderr = (proc.stderr or b'').decode('utf-8', errors='replace')[:500]
                logger.error('LibreOffice 转换失败: rc=%s stderr=%s', proc.returncode, stderr)
                return False, f'LibreOffice 转换失败 (rc={proc.returncode})'

            pdf_src = os.path.join(workdir, f'src.pdf')
            if not os.path.exists(pdf_src):
                # LibreOffice 输出名称可能跟随源文件主名
                candidates = [p for p in os.listdir(workdir) if p.lower().endswith('.pdf')]
                if not candidates:
                    return False, '转换后未找到 PDF 输出'
                pdf_src = os.path.join(workdir, candidates[0])

            shutil.move(pdf_src, cached)

    return True, cached


def hash_content(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
