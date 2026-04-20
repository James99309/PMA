# -*- coding: utf-8 -*-
"""
export_to_word 工具：生成精美 Word 文档。

两种路径：
    1. python_code 参数（主路径）：Claude 使用 PMA docx 样式库写的完整代码，
       PMA 在临时目录执行，输出 .docx。效果等同 claude.ai 原生文档质量。
    2. markdown 参数（兜底）：pandoc 转换，样式较基础。

存储：本地 storage/exports/，可选 NAS WebDAV 备份。
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.services.cli_agent.tools import BaseTool

logger = logging.getLogger(__name__)

_REFERENCE_DOC = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', '..', 'templates', 'word', 'pma_reference.docx'
))

_STORAGE_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', '..', '..', 'storage', 'exports'
))


class ExportToWordTool(BaseTool):
    name = 'export_to_word'
    description = (
        '生成 Word 文档（.docx）。\n'
        '当用户说"生成报告"、"导出Word"、"生成文档"、"下载报告"时使用。\n\n'
        '参数选择：\n'
        '- python_code（推荐）：使用 [PMA Word 样式库] 中的函数写完整 python-docx 代码。'
        '代码必须调用 init_doc(db_type=DB_TYPE) 初始化，最后 doc.save(OUTPUT_PATH) 保存。'
        'OUTPUT_PATH 写占位符字符串 "__OUTPUT__"，工具会自动替换为实际路径。'
        'DB_TYPE 从系统 [运行环境] 获取（SP8D 或 OVS）。\n'
        '- markdown（兜底）：传入 Markdown 文本，用 pandoc 转换，样式较基础。\n\n'
        '返回结果包含 download_url，直接输出"文档已生成"即可，无需在回复中重复链接。'
    )
    input_schema = {
        'type': 'object',
        'properties': {
            'python_code': {
                'type': 'string',
                'description': '完整 python-docx 代码，使用 PMA 样式库函数，doc.save("__OUTPUT__") 结尾',
            },
            'markdown': {
                'type': 'string',
                'description': '兜底：Markdown 文本，pandoc 转换',
            },
            'title': {
                'type': 'string',
                'description': '文档标题（必填，用于文件命名，应概括文档内容，如"范敬_失败项目说明"、"李华伟_上周工作总结"）',
            },
        },
    }

    def execute(self, tool_input: dict, context: dict) -> Any:
        tool_input = tool_input or {}
        python_code = tool_input.get('python_code', '').strip()
        markdown = tool_input.get('markdown', '').strip()
        title = tool_input.get('title', '').strip()
        user = context.get('user')

        if python_code:
            return self._execute_python_code(python_code, title, user)
        elif markdown:
            return self._execute_pandoc(markdown, title, user)
        else:
            return {'error': 'python_code 或 markdown 参数不能同时为空'}

    # ── python-docx 路径 ────────────────────────────────────────────

    def _execute_python_code(self, code: str, title: str, user) -> dict:
        output_filename = self._make_filename(title)
        os.makedirs(_STORAGE_DIR, exist_ok=True)
        final_path = os.path.join(_STORAGE_DIR, output_filename)

        with tempfile.TemporaryDirectory() as tmpdir:
            # 将样式库保存为 pma_docx_style.py，使 Claude 的 import 语句生效
            try:
                from app.models.cli_skill import CliSkill
                skill = CliSkill.query.filter_by(name='pma_docx_style', skill_type='docx', is_active=True).first()
                if skill and skill.skill_body:
                    Path(os.path.join(tmpdir, 'pma_docx_style.py')).write_text(skill.skill_body, encoding='utf-8')
            except Exception as e:
                logger.warning(f'[export_to_word] 无法加载 skill_body: {e}')

            tmp_out = os.path.join(tmpdir, 'output.docx')
            # 替换 __OUTPUT__ 占位符，或兜底替换 doc.save(...)
            if '__OUTPUT__' in code:
                code = code.replace('__OUTPUT__', tmp_out)
            else:
                code = re.sub(
                    r'doc\.save\(["\'].*?["\']\)',
                    f'doc.save("{tmp_out}")',
                    code
                )
            script_path = os.path.join(tmpdir, 'gen.py')
            Path(script_path).write_text(code, encoding='utf-8')

            try:
                result = subprocess.run(
                    ['python3', script_path],
                    capture_output=True, text=True, timeout=60
                )
            except subprocess.TimeoutExpired:
                return {'error': '文档生成超时（60秒）'}

            if result.returncode != 0:
                logger.error(f'[export_to_word] python-docx 执行失败:\n{result.stderr}')
                return {'error': f'文档生成失败: {result.stderr[:300]}'}

            if not os.path.exists(tmp_out):
                return {'error': '代码执行成功但未找到输出文件，请确认代码中有 doc.save("__OUTPUT__")'}

            shutil.copy(tmp_out, final_path)

        self._try_upload_nas(final_path, output_filename, user)
        logger.info(f'[export_to_word] python-docx 生成: {output_filename}')
        return {
            'success': True,
            'filename': output_filename,
            'download_url': f'/cli/api/exports/{output_filename}',
            'note': '下载按钮已显示在终端中，只需简短回复"文档已生成"即可。',
        }

    # ── pandoc 兜底路径 ─────────────────────────────────────────────

    def _execute_pandoc(self, markdown: str, title: str, user) -> dict:
        if not shutil.which('pandoc'):
            return {'error': 'pandoc 未安装，请改用 python_code 参数'}

        output_filename = self._make_filename(title)
        os.makedirs(_STORAGE_DIR, exist_ok=True)
        final_path = os.path.join(_STORAGE_DIR, output_filename)

        if title:
            markdown = f'---\ntitle: "{title}"\n---\n\n' + markdown

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False,
                                         encoding='utf-8') as f:
            f.write(markdown)
            md_path = f.name

        tmp_out = os.path.join(tempfile.gettempdir(), output_filename)
        try:
            cmd = ['pandoc', '-f', 'markdown', '-t', 'docx', '-o', tmp_out]
            if os.path.exists(_REFERENCE_DOC):
                cmd.extend(['--reference-doc', _REFERENCE_DOC])
            cmd.append(md_path)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            os.unlink(md_path)
            if result.returncode != 0:
                return {'error': f'pandoc 转换失败: {result.stderr[:200]}'}
            shutil.move(tmp_out, final_path)
        except subprocess.TimeoutExpired:
            return {'error': '文档生成超时'}
        except Exception as e:
            logger.exception('[export_to_word] pandoc 异常')
            return {'error': f'文档生成失败: {e}'}

        self._try_upload_nas(final_path, output_filename, user)
        return {
            'success': True,
            'filename': output_filename,
            'download_url': f'/cli/api/exports/{output_filename}',
            'note': '下载按钮已显示在终端中，只需简短回复"文档已生成"即可。',
        }

    # ── 工具函数 ────────────────────────────────────────────────────

    @staticmethod
    def _make_filename(title: str) -> str:
        date_str = datetime.now().strftime('%Y%m%d_%H%M')
        if title:
            # 只保留中文、英文、数字、下划线，其余替换为下划线
            safe = re.sub(r'[^\w\u4e00-\u9fff]+', '_', title).strip('_')
            # 截断过长标题
            if len(safe) > 60:
                safe = safe[:60].rstrip('_')
            return f'{safe}_{date_str}.docx'
        short_id = uuid.uuid4().hex[:8]
        return f'report_{date_str}_{short_id}.docx'

    @staticmethod
    def _try_upload_nas(file_path: str, filename: str, user) -> None:
        try:
            from app.utils.synology_webdav_client import get_synology_webdav_client, is_nas_available
            if not is_nas_available():
                return
            client = get_synology_webdav_client()
            remote_dir = f'/exports/cli/{datetime.now().strftime("%Y/%m")}'
            client.ensure_directory(remote_dir)
            with open(file_path, 'rb') as f:
                client.upload(f'{remote_dir}/{filename}', f.read())
        except Exception as e:
            logger.debug(f'[export_to_word] NAS 上传跳过: {e}')
