# -*- coding: utf-8 -*-
"""
export_to_word 工具：把 Markdown 内容转为精美 Word 文档。

流程：
    1. 接收 Markdown 文本（通常是上一条 AI 回复）
    2. 用 pandoc + PMA 样式参考文档 → .docx
    3. 存到 NAS WebDAV / 本地 storage
    4. 返回下载链接

依赖：
    - pandoc CLI（系统已安装）
    - pma_reference.docx（样式参考文档）
"""
from __future__ import annotations

import logging
import os
import subprocess
import tempfile
import uuid
from datetime import datetime
from typing import Any

from app.services.cli_agent.tools import BaseTool

logger = logging.getLogger(__name__)

# 参考文档路径
_REFERENCE_DOC = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', '..', 'templates', 'word', 'pma_reference.docx'
)


class ExportToWordTool(BaseTool):
    name = 'export_to_word'
    description = (
        '将 Markdown 内容导出为精美 Word 文档。'
        '当用户说"导出Word"、"生成文档"、"下载报告"时使用。\n'
        '传入 markdown 参数（完整的 Markdown 文本），自动转为 .docx。\n'
        '返回结果包含 download_url 和 message（已含 Markdown 链接），直接输出 message 即可。'
    )
    input_schema = {
        'type': 'object',
        'properties': {
            'markdown': {
                'type': 'string',
                'description': '要导出的 Markdown 内容（完整文本，包含标题、表格等）',
            },
            'title': {
                'type': 'string',
                'description': '文档标题（可选，会作为 YAML front matter 的 title）',
            },
        },
        'required': ['markdown'],
    }

    def execute(self, tool_input: dict, context: dict) -> Any:
        markdown = (tool_input or {}).get('markdown', '').strip()
        title = (tool_input or {}).get('title', '').strip()
        filename = (tool_input or {}).get('filename', '').strip()
        user = context.get('user')

        if not markdown:
            return {'error': 'markdown 参数不能为空'}

        # 检查 pandoc
        try:
            subprocess.run(['pandoc', '--version'], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            return {'error': 'pandoc 未安装，无法生成 Word 文档'}

        # 检查参考文档
        ref_doc = os.path.normpath(_REFERENCE_DOC)
        if not os.path.exists(ref_doc):
            logger.warning(f'[CLI Agent] 参考文档不存在: {ref_doc}，使用 pandoc 默认样式')
            ref_doc = None

        # 添加 YAML front matter（标题）
        if title:
            front_matter = f'---\ntitle: "{title}"\n---\n\n'
            markdown = front_matter + markdown

        # 文件名始终用英文+UUID，避免 URL 编码问题
        short_id = uuid.uuid4().hex[:8]
        date_str = datetime.now().strftime('%Y%m%d_%H%M')
        output_filename = f'report_{date_str}_{short_id}.docx'

        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                f.write(markdown)
                md_path = f.name

            output_path = os.path.join(tempfile.gettempdir(), output_filename)

            # pandoc 转换
            cmd = ['pandoc', '-f', 'markdown', '-t', 'docx', '-o', output_path]
            if ref_doc:
                cmd.extend(['--reference-doc', ref_doc])
            cmd.append(md_path)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            os.unlink(md_path)  # 清理临时 md 文件

            if result.returncode != 0:
                logger.error(f'[CLI Agent] pandoc 失败: {result.stderr}')
                return {'error': f'文档生成失败: {result.stderr[:200]}'}

            # 尝试存到 NAS WebDAV
            download_url = self._upload_to_storage(output_path, output_filename, user)

            # 存到本地 storage（始终可用）
            storage_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..', '..', '..', '..', 'storage', 'exports'
            )
            os.makedirs(storage_dir, exist_ok=True)
            final_path = os.path.join(storage_dir, output_filename)
            os.rename(output_path, final_path)

            download_url = f'/cli/api/exports/{output_filename}'

            return {
                'success': True,
                'filename': output_filename,
                'download_url': download_url,
                'note': '下载按钮已显示在终端中，无需在回复里再输出链接。只需简短确认"文档已生成"即可。',
            }

        except subprocess.TimeoutExpired:
            return {'error': '文档生成超时（30秒）'}
        except Exception as e:
            logger.exception('[CLI Agent] export_to_word 异常')
            return {'error': f'文档生成失败: {e}'}

    def _upload_to_storage(self, file_path: str, filename: str, user) -> str | None:
        """尝试上传到 NAS WebDAV，返回下载 URL 或 None"""
        try:
            from flask import current_app, url_for
            from app.utils.synology_webdav_client import get_synology_webdav_client, is_nas_available

            if not is_nas_available():
                return None

            client = get_synology_webdav_client()
            remote_dir = f'/exports/cli/{datetime.now().strftime("%Y/%m")}'
            remote_path = f'{remote_dir}/{filename}'

            with open(file_path, 'rb') as f:
                file_bytes = f.read()

            # 确保目录存在
            client.ensure_directory(remote_dir)
            client.upload(remote_path, file_bytes)

            # 返回下载链接（通过 PMA 文件下载路由）
            user_id = user.id if user else 0
            return f'/cli/api/exports/{filename}'

        except Exception as e:
            logger.warning(f'[CLI Agent] NAS 上传失败，使用本地存储: {e}')
            return None
