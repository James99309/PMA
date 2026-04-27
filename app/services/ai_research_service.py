# -*- coding: utf-8 -*-
"""
AI 客户网络调研服务

通过 Claude 直接调用（默认）或 OpenClaw Gateway 调用 web_search + AI 分析，
一次请求完成搜索+结构化。

调研提供者选择（环境变量 AI_RESEARCH_PROVIDER）：
    claude（默认）  直接调用 Claude API，使用 CLI 同款 OAuth identity prefix
    openclaw        转发给 OpenClaw WebSocket 网关
模型（环境变量 AI_RESEARCH_MODEL，默认 claude-sonnet-4-6）。

支持后台自动调研：新建/改名客户自动触发，定时任务补充未调研的客户。
"""
import json
import logging
import os
import re
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

CACHE_EXPIRY_DAYS = 30


class AIResearchService:
    """AI 客户网络调研服务"""

    # ─── 公开 API ───────────────────────────────────────────

    @classmethod
    def trigger_research(cls, company_id):
        """非阻塞触发后台调研，可从任何地方调用"""
        from app.models.customer import Company
        from app import db
        from flask import current_app

        company = Company.query.get(company_id)
        if not company:
            return
        if company.ai_research_status in ('pre_searching', 'researching'):
            return  # 防重复

        company.ai_research_status = 'pre_searching'
        company.ai_research_error = None
        company.ai_research_candidates = None
        db.session.commit()

        app = current_app._get_current_object()
        thread = threading.Thread(
            target=cls._background_worker,
            args=(app, company_id),
            daemon=True
        )
        thread.start()
        logger.info(f"[AI-Research] 后台调研已触发: company_id={company_id}")

    @classmethod
    def continue_with_candidate(cls, company_id, confirmed_name):
        """用户选择候选公司后继续调研（非阻塞）"""
        from app.models.customer import Company
        from app import db
        from flask import current_app

        company = Company.query.get(company_id)
        if not company:
            return
        if company.ai_research_status in ('researching',):
            return

        company.ai_research_status = 'researching'
        company.ai_research_error = None
        db.session.commit()

        app = current_app._get_current_object()
        thread = threading.Thread(
            target=cls._do_full_research,
            args=(app, company_id, confirmed_name),
            daemon=True
        )
        thread.start()

    @classmethod
    def get_status(cls, company_id):
        """返回统一状态+数据（前端轮询用）"""
        from app.models.customer import Company

        company = Company.query.get(company_id)
        if not company:
            return None

        result = {
            'status': company.ai_research_status or 'none',
            'research_data': company.ai_research_data,
            'updated_at': company.ai_research_updated_at.isoformat() if company.ai_research_updated_at else None,
            'candidates': company.ai_research_candidates,
            'error': company.ai_research_error,
        }

        if company.ai_research_data and company.ai_research_updated_at:
            result['is_stale'] = (datetime.utcnow() - company.ai_research_updated_at) > timedelta(days=CACHE_EXPIRY_DAYS)
        else:
            result['is_stale'] = False

        return result

    @classmethod
    def batch_research_pending(cls, app=None, limit=50, interval=10):
        """定时任务用：批量处理 status=none/error 的公司"""
        import time
        from app.models.customer import Company
        from app import db

        if app is None:
            from flask import current_app
            app = current_app._get_current_object()

        with app.app_context():
            companies = Company.query.filter(
                Company.is_deleted == False,
                Company.ai_research_status.in_(['none', 'error'])
            ).order_by(Company.created_at.desc()).limit(limit).all()

            if not companies:
                logger.info("[AI-Research-Batch] 无待调研公司")
                return 0

            count = 0
            for company in companies:
                try:
                    company.ai_research_status = 'pre_searching'
                    company.ai_research_error = None
                    company.ai_research_candidates = None
                    db.session.commit()

                    cls._background_worker(app, company.id)
                    count += 1
                    logger.info(f"[AI-Research-Batch] 完成 {count}/{len(companies)}: {company.company_name}")

                    if count < len(companies):
                        time.sleep(interval)
                except Exception as e:
                    logger.error(f"[AI-Research-Batch] 失败: {company.company_name}: {e}")
                    try:
                        company.ai_research_status = 'error'
                        company.ai_research_error = str(e)[:500]
                        db.session.commit()
                    except Exception:
                        db.session.rollback()

            logger.info(f"[AI-Research-Batch] 批量调研完成: {count}/{len(companies)}")
            return count

    # ─── 后台工作线程 ──────────────────────────────────────

    @classmethod
    def _background_worker(cls, app, company_id):
        """后台线程：预搜索 → 匹配成功自动完整调研，失败则设置 needs_input"""
        from app.models.customer import Company
        from app import db

        with app.app_context():
            try:
                company = Company.query.get(company_id)
                if not company:
                    return

                company_name = company.company_name

                # 阶段一：预搜索
                try:
                    ai_result = cls._ai_pre_check(company_name)
                except Exception as e:
                    logger.error(f"[AI-Research-BG] 预搜索失败: {company_name}: {e}")
                    company.ai_research_status = 'error'
                    company.ai_research_error = f'预搜索失败: {str(e)[:400]}'
                    db.session.commit()
                    return

                if ai_result['match']:
                    # 精确匹配 → 直接进入完整调研
                    company.ai_research_status = 'researching'
                    db.session.commit()
                    cls._do_full_research(app, company_id, None)
                else:
                    candidates = ai_result.get('candidates', [])
                    if candidates:
                        # 有候选 → 需要用户确认
                        company.ai_research_status = 'needs_input'
                        company.ai_research_candidates = candidates
                        db.session.commit()
                    else:
                        # 无候选 → 仍尝试用原名调研
                        company.ai_research_status = 'researching'
                        db.session.commit()
                        cls._do_full_research(app, company_id, None)

            except Exception as e:
                logger.error(f"[AI-Research-BG] 未知错误: company_id={company_id}: {e}")
                try:
                    company = Company.query.get(company_id)
                    if company:
                        company.ai_research_status = 'error'
                        company.ai_research_error = str(e)[:500]
                        db.session.commit()
                except Exception:
                    db.session.rollback()

    @classmethod
    def _do_full_research(cls, app, company_id, confirmed_name):
        """执行完整调研并写入数据库"""
        from app.models.customer import Company
        from app import db

        with app.app_context():
            try:
                company = Company.query.get(company_id)
                if not company:
                    return

                search_name = confirmed_name or company.company_name
                core_name = cls._extract_core_name(search_name)
                search_term = core_name if core_name and len(core_name) >= 2 else search_name

                prompt = cls._build_research_prompt(search_name, search_term)
                response = cls._send_research_request(prompt, timeout=180)
                logger.info(f"[AI-Research-Full] 原始回复 ({len(response)} chars): {response[:1000]}")
                structured = cls._extract_json(response)

                now = datetime.utcnow()
                company.ai_research_data = structured
                company.ai_research_updated_at = now
                company.ai_research_status = 'completed'
                company.ai_research_error = None
                company.ai_research_candidates = None
                db.session.commit()

                logger.info(f"[AI-Research-Full] 调研完成: {search_name} (id={company_id})")

            except Exception as e:
                logger.error(f"[AI-Research-Full] 调研失败: company_id={company_id}: {e}")
                try:
                    company = Company.query.get(company_id)
                    if company:
                        company.ai_research_status = 'error'
                        company.ai_research_error = f'调研失败: {str(e)[:400]}'
                        db.session.commit()
                except Exception:
                    db.session.rollback()

    # ─── 兼容旧 API（保留供现有端点使用） ──────────────────

    @classmethod
    def get_cached_research(cls, company_id):
        """获取缓存的调研数据（兼容旧接口）"""
        status = cls.get_status(company_id)
        if not status or not status['research_data']:
            return None
        return {
            'research_data': status['research_data'],
            'updated_at': status['updated_at'],
            'is_stale': status['is_stale']
        }

    @classmethod
    def pre_search(cls, company_id):
        """阶段一：预搜索（兼容旧同步接口）"""
        from app.models.customer import Company

        company = Company.query.get(company_id)
        if not company:
            return {'success': False, 'error': '客户不存在'}

        try:
            ai_result = cls._ai_pre_check(company.company_name)
        except Exception as e:
            return {'success': False, 'error': f'AI 搜索失败: {str(e)}'}

        if ai_result['match']:
            return {'success': True, 'exact_match': True,
                    'matched_name': ai_result.get('matched_name', '')}

        candidates = ai_result.get('candidates', [])
        if not candidates:
            return {
                'success': True, 'exact_match': False, 'candidates': [],
                'message': f'未找到与"{company.company_name}"完全匹配的结果，可能是小型企业或信息较少',
                'allow_force': True
            }
        return {'success': True, 'exact_match': False, 'candidates': candidates}

    @classmethod
    def run_research(cls, company_id, confirmed_name=None):
        """阶段二：执行完整调研（兼容旧同步接口）"""
        from app.models.customer import Company
        from app import db

        company = Company.query.get(company_id)
        if not company:
            return {'success': False, 'error': '客户不存在'}

        search_name = confirmed_name or company.company_name
        core_name = cls._extract_core_name(search_name)
        search_term = core_name if core_name and len(core_name) >= 2 else search_name

        prompt = cls._build_research_prompt(search_name, search_term)

        try:
            response = cls._send_research_request(prompt, timeout=180)
            logger.info(f"[AI-Research-Full] 原始回复 ({len(response)} chars): {response[:1000]}")
            structured = cls._extract_json(response)
        except Exception as e:
            logger.error(f"AI 调研失败: {search_name}: {e}")
            return {'success': False, 'error': f'AI 调研失败: {str(e)}'}

        now = datetime.utcnow()
        company.ai_research_data = structured
        company.ai_research_updated_at = now
        company.ai_research_status = 'completed'
        company.ai_research_error = None
        company.ai_research_candidates = None
        db.session.commit()

        return {
            'success': True,
            'data': {
                'research_data': structured,
                'updated_at': now.isoformat()
            }
        }

    # ─── 调研请求分发 ─────────────────────────────────────────

    @classmethod
    def _send_research_request(cls, prompt: str, timeout: int = 180) -> str:
        """发送调研请求，使用 Claude 直接调用（与 CLI 相同的 OAuth identity prefix）。"""
        from app.services.claude_research_provider import send_claude_research_request
        return send_claude_research_request(prompt, timeout=timeout)

    # ─── 私有工具方法 ──────────────────────────────────────

    @classmethod
    def _extract_core_name(cls, company_name):
        """从完整公司名中提取核心名称，用于搜索和匹配"""
        name = company_name
        name = re.sub(r'[（(][^）)]*[）)]', '', name)
        name = re.sub(
            r'(股份有限公司|有限责任公司|有限公司|集团公司)'
            r'([\u4e00-\u9fff]{0,4}分公司)?$',
            '', name
        )
        name = re.sub(r'[\u4e00-\u9fff]{0,3}分公司$', '', name)
        stripped = re.sub(r'^(江苏|浙江|广东|北京|上海|山东|四川|湖北|湖南|河南|河北|安徽|福建|江西|陕西|云南|贵州|广西|海南|甘肃|宁夏|青海|新疆|西藏|内蒙古|黑龙江|吉林|辽宁|山西|天津|重庆)', '', name)
        if len(stripped) >= 4:
            name = stripped
        business_types = (
            '产业发展', '科技发展', '设计顾问', '信息技术', '智能科技',
            '建筑工程', '装饰工程', '机电工程', '市政工程', '园林绿化',
            '房地产', '置业', '实业', '投资', '控股', '商贸', '贸易',
        )
        for suffix in business_types:
            if name.endswith(suffix) and len(name) - len(suffix) >= 2:
                name = name[:-len(suffix)]
                break
        return name.strip()

    @classmethod
    def _extract_json(cls, content):
        """从 AI 响应中提取 JSON"""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(content[start:end + 1])
            except json.JSONDecodeError:
                pass

        raise ValueError("无法从 AI 响应中提取有效的 JSON")

    @classmethod
    def _ai_pre_check(cls, company_name):
        """搜索并判断公司是否存在"""
        core_name = cls._extract_core_name(company_name)
        search_term = core_name if core_name and len(core_name) >= 2 else company_name

        prompt = (
            f'请使用 web_search 工具搜索"{search_term}"，判断搜索结果中是否有与"{company_name}"相关的公司信息。\n\n'
            f'注意：公司可能有简称、母子公司关系、分公司等变体，这些都算匹配。\n\n'
            f'请输出 JSON（不要包含其他文字）：\n'
            f'{{"match": true/false, "matched_name": "搜索结果中该公司最常用名称", "candidates": ["候选公司1", "候选公司2"]}}\n\n'
            f'- match=true 表示搜索结果中有该公司的信息\n'
            f'- matched_name: match=true 时填写搜索结果中出现的该公司名称\n'
            f'- candidates: match=false 时填写搜索结果中可能相关的公司名列表（最多5个）'
        )

        try:
            response = cls._send_research_request(prompt, timeout=90)
            logger.info(f"[AI-Research-PreCheck] 原始回复 ({len(response)} chars): {response[:500]}")
            parsed = cls._extract_json(response)
            return {
                'match': bool(parsed.get('match', False)),
                'matched_name': parsed.get('matched_name', ''),
                'candidates': parsed.get('candidates', [])[:5]
            }
        except Exception as e:
            logger.error(f"预搜索 AI 判断失败: {company_name}: {e}")
            raise

    @classmethod
    def _build_research_prompt(cls, search_name, search_term):
        """构建完整调研的 AI 提示词 — 根据 IS_OVS 切换中/英文版本。"""
        try:
            from flask import current_app
            is_ovs = bool(current_app.config.get('IS_OVS'))
        except Exception:
            is_ovs = False

        if is_ovs:
            return cls._build_research_prompt_sg(search_name, search_term)
        return cls._build_research_prompt_cn(search_name, search_term)

    @classmethod
    def _build_research_prompt_cn(cls, search_name, search_term):
        """中国大陆企业调研 prompt — 中文。"""
        return (
            f'请对"{search_name}"（搜索关键词：{search_term}）进行全面的企业调研。\n\n'
            f'请使用 web_search 工具搜索以下维度的信息：\n'
            f'1. "{search_term}" 公司简介 主营业务\n'
            f'2. "{search_term}" 最新项目 中标 签约\n'
            f'3. "{search_term}" 高管 管理层\n'
            f'4. "{search_term}" 风险 诉讼 处罚\n\n'
            f'## 最重要的规则\n'
            f'**严禁编造任何信息！** 如果搜索结果中没有提到某项信息，该字段必须留空（空字符串""或空数组[]）。\n'
            f'- 禁止使用"张三"、"李四"等占位名称\n'
            f'- 禁止编造高管姓名、职位、项目名称、金额等任何数据\n'
            f'- 只有搜索结果中**原文包含**的真实信息才能填入\n\n'
            f'## 输出格式\n'
            f'请严格按以下 JSON 格式输出，不要包含其他文字。找不到的信息一律留空。\n\n'
            f'{{\n'
            f'    "company_profile": {{\n'
            f'        "founded": "",\n'
            f'        "headquarters": "",\n'
            f'        "positioning": "",\n'
            f'        "main_business": [],\n'
            f'        "revenue": "",\n'
            f'        "strategy": ""\n'
            f'    }},\n'
            f'    "executives": [],\n'
            f'    "active_projects": [],\n'
            f'    "partners": {{\n'
            f'        "general_contractors": [],\n'
            f'        "ecosystem": [],\n'
            f'        "key_customers": []\n'
            f'    }},\n'
            f'    "risk_alerts": [],\n'
            f'    "sales_suggestions": []\n'
            f'}}\n\n'
            f'executives 数组中每个元素格式: {{"name": "真实姓名", "title": "职位", "background": "背景", "risk_tag": null}}\n'
            f'active_projects 数组中每个元素格式: {{"name": "项目名", "amount": "金额", "type": "类型", "partner": "合作方", "status": "状态", "detail": "描述"}}\n'
            f'risk_alerts 数组中每个元素格式: {{"level": "high/medium/low", "content": "描述", "date": "日期"}}\n\n'
            f'注意：\n'
            f'- 只提取与"{search_name}"直接相关的信息\n'
            f'- risk_tag 用于标记高管的风险信息（如"被调查"、"已离职"），无风险则为 null\n'
            f'- sales_suggestions 请基于搜索结果中提到的真实业务方向给出建议\n'
            f'- **宁可留空也不要编造数据**'
        )

    @classmethod
    def _build_research_prompt_sg(cls, search_name, search_term):
        """SEA 企业调研 prompt — 英文，针对 SG/MY/ID/TH/VN 商业语境。"""
        return (
            f'Conduct a comprehensive corporate intelligence research on "{search_name}" '
            f'(search keyword: {search_term}).\n\n'
            f'Use the web_search tool to gather information across these dimensions:\n'
            f'1. "{search_term}" company profile main business activities\n'
            f'2. "{search_term}" recent projects awarded contracts\n'
            f'3. "{search_term}" leadership executives directors\n'
            f'4. "{search_term}" lawsuits litigation regulatory penalties compliance\n\n'
            f'Useful regional registries / sources:\n'
            f'- Singapore: ACRA, BCA, URA, EDB; Straits Times / Business Times\n'
            f'- Malaysia: SSM, CIDB, MITI; The Edge / The Star\n'
            f'- Indonesia: OSS / AHU, BKPM, PUPR; Bisnis.com / Kontan\n'
            f'- Thailand: BOI, DBD; Bangkok Post / Nation\n'
            f'- Vietnam: VIR / VN Express; provincial DPI portals\n'
            f'- Philippines: SEC; Inquirer / BusinessWorld\n\n'
            f'## Critical rule\n'
            f'**DO NOT fabricate any information.** If a fact is not present in search results, leave the field empty '
            f'(empty string "" or empty array []).\n'
            f'- No placeholder names (no "John Doe", no generic titles).\n'
            f'- Do not invent executive names, project names, contract values, or any data.\n'
            f'- Only fill fields with verbatim facts from the search results.\n\n'
            f'## Output format\n'
            f'Return strict JSON only. No prose. Empty fields when not found.\n\n'
            f'{{\n'
            f'    "company_profile": {{\n'
            f'        "founded": "",\n'
            f'        "headquarters": "",\n'
            f'        "positioning": "",\n'
            f'        "main_business": [],\n'
            f'        "revenue": "",\n'
            f'        "strategy": ""\n'
            f'    }},\n'
            f'    "executives": [],\n'
            f'    "active_projects": [],\n'
            f'    "partners": {{\n'
            f'        "general_contractors": [],\n'
            f'        "ecosystem": [],\n'
            f'        "key_customers": []\n'
            f'    }},\n'
            f'    "risk_alerts": [],\n'
            f'    "sales_suggestions": []\n'
            f'}}\n\n'
            f'executives item format: {{"name": "real name", "title": "title", "background": "background", "risk_tag": null}}\n'
            f'active_projects item format: {{"name": "project name", "amount": "value with currency", "type": "type", "partner": "partner", "status": "status", "detail": "description"}}\n'
            f'risk_alerts item format: {{"level": "high/medium/low", "content": "description", "date": "date"}}\n\n'
            f'Notes:\n'
            f'- Extract only facts directly tied to "{search_name}".\n'
            f'- risk_tag flags executive-level risk signals (e.g. "under investigation", "resigned"); use null when none.\n'
            f'- sales_suggestions must reference real business areas mentioned in the search results — '
            f'focus on opportunities for industrial communication systems (ELV / ICT / two-way radio / dispatch / IP intercom / PA).\n'
            f'- All free-text fields must be in English.\n'
            f'- **Prefer empty over fabricated.**'
        )

    # ═══ 项目 AI 调研 ═══════════════════════════════════════════

    @classmethod
    def trigger_project_research(cls, project_id):
        """非阻塞触发项目后台调研（预搜索 → 候选确认 → 完整调研）"""
        from app.models.project import Project
        from app import db
        from flask import current_app

        project = Project.query.get(project_id)
        if not project:
            return
        if project.ai_research_status in ('pre_searching', 'researching'):
            return  # 防重复

        project.ai_research_status = 'pre_searching'
        project.ai_research_error = None
        project.ai_research_candidates = None
        db.session.commit()

        app = current_app._get_current_object()
        thread = threading.Thread(
            target=cls._project_background_worker,
            args=(app, project_id),
            daemon=True
        )
        thread.start()
        logger.info(f"[AI-Research-Project] 后台调研已触发: project_id={project_id}")

    @classmethod
    def continue_project_with_candidate(cls, project_id, confirmed_name):
        """用户选择候选项目名后继续完整调研（非阻塞）"""
        from app.models.project import Project
        from app import db
        from flask import current_app

        project = Project.query.get(project_id)
        if not project:
            return
        if project.ai_research_status == 'researching':
            return

        project.ai_research_status = 'researching'
        project.ai_research_error = None
        db.session.commit()

        app = current_app._get_current_object()
        thread = threading.Thread(
            target=cls._project_do_full_research,
            args=(app, project_id, confirmed_name),
            daemon=True
        )
        thread.start()

    @classmethod
    def get_project_status(cls, project_id):
        """返回项目调研的统一状态+数据"""
        from app.models.project import Project

        project = Project.query.get(project_id)
        if not project:
            return None

        result = {
            'status': project.ai_research_status or 'none',
            'research_data': project.ai_research_data,
            'updated_at': project.ai_research_updated_at.isoformat() if project.ai_research_updated_at else None,
            'candidates': project.ai_research_candidates,
            'error': project.ai_research_error,
        }

        if project.ai_research_data and project.ai_research_updated_at:
            result['is_stale'] = (datetime.utcnow() - project.ai_research_updated_at) > timedelta(days=CACHE_EXPIRY_DAYS)
        else:
            result['is_stale'] = False

        return result

    @classmethod
    def batch_project_research_pending(cls, app=None, limit=50, interval=10):
        """定时任务用：批量处理项目 status=none/error"""
        import time
        from app.models.project import Project
        from app import db

        if app is None:
            from flask import current_app
            app = current_app._get_current_object()

        with app.app_context():
            projects = Project.query.filter(
                Project.ai_research_status.in_(['none', 'error'])
            ).order_by(Project.created_at.desc()).limit(limit).all()

            if not projects:
                logger.info("[AI-Research-Project-Batch] 无待调研项目")
                return 0

            count = 0
            for project in projects:
                try:
                    project.ai_research_status = 'pre_searching'
                    project.ai_research_error = None
                    project.ai_research_candidates = None
                    db.session.commit()

                    cls._project_background_worker(app, project.id)
                    count += 1
                    logger.info(f"[AI-Research-Project-Batch] 完成 {count}/{len(projects)}: {project.project_name}")

                    if count < len(projects):
                        time.sleep(interval)
                except Exception as e:
                    logger.error(f"[AI-Research-Project-Batch] 失败: {project.project_name}: {e}")
                    try:
                        project.ai_research_status = 'error'
                        project.ai_research_error = str(e)[:500]
                        db.session.commit()
                    except Exception:
                        db.session.rollback()

            logger.info(f"[AI-Research-Project-Batch] 批量调研完成: {count}/{len(projects)}")
            return count

    # ─── 项目后台工作线程 ─────────────────────────────────────

    @classmethod
    def _project_background_worker(cls, app, project_id):
        """项目后台调研：预搜索 → 有候选则等用户确认，否则直接完整调研"""
        from app.models.project import Project
        from app import db

        with app.app_context():
            try:
                project = Project.query.get(project_id)
                if not project:
                    return

                project_name = project.project_name

                try:
                    ai_result = cls._project_pre_check(project_name)
                except Exception as e:
                    logger.error(f"[AI-Research-Project-BG] 预搜索失败: {project_name}: {e}")
                    project.ai_research_status = 'error'
                    project.ai_research_error = f'预搜索失败: {str(e)[:400]}'
                    db.session.commit()
                    return

                if ai_result['match']:
                    project.ai_research_status = 'researching'
                    db.session.commit()
                    cls._project_do_full_research(app, project_id, None)
                else:
                    candidates = ai_result.get('candidates', [])
                    if candidates:
                        project.ai_research_status = 'needs_input'
                        project.ai_research_candidates = candidates
                        db.session.commit()
                    else:
                        # 无候选：用去掉城市前缀的核心名重试
                        project.ai_research_status = 'researching'
                        db.session.commit()
                        cls._project_do_full_research(app, project_id, None)

            except Exception as e:
                logger.error(f"[AI-Research-Project-BG] 未知错误: project_id={project_id}: {e}")
                try:
                    project = Project.query.get(project_id)
                    if project:
                        project.ai_research_status = 'error'
                        project.ai_research_error = str(e)[:500]
                        db.session.commit()
                except Exception:
                    db.session.rollback()

    @classmethod
    def _project_do_full_research(cls, app, project_id, confirmed_name):
        """执行项目完整调研并写入数据库"""
        from app.models.project import Project
        from app import db

        with app.app_context():
            try:
                project = Project.query.get(project_id)
                if not project:
                    return

                search_name = confirmed_name or project.project_name
                core_name = cls._extract_project_core_name(search_name)
                search_term = core_name if core_name and len(core_name) >= 2 else search_name

                prompt = cls._build_project_research_prompt(search_name, search_term)
                response = cls._send_research_request(prompt, timeout=180)
                logger.info(f"[AI-Research-Project] 原始回复 ({len(response)} chars): {response[:1000]}")
                structured = cls._extract_json(response)

                now = datetime.utcnow()
                project.ai_research_data = structured
                project.ai_research_updated_at = now
                project.ai_research_status = 'completed'
                project.ai_research_error = None
                project.ai_research_candidates = None
                db.session.commit()

                logger.info(f"[AI-Research-Project] 调研完成: {search_name} (id={project_id})")

            except Exception as e:
                logger.error(f"[AI-Research-Project] 调研失败: project_id={project_id}: {e}")
                try:
                    project = Project.query.get(project_id)
                    if project:
                        project.ai_research_status = 'error'
                        project.ai_research_error = f'调研失败: {str(e)[:400]}'
                        db.session.commit()
                except Exception:
                    db.session.rollback()

    @classmethod
    def _project_pre_check(cls, project_name):
        """预搜索：判断项目是否有公开信息，无精确匹配时返回候选列表"""
        core_name = cls._extract_project_core_name(project_name)
        search_term = core_name if core_name and len(core_name) >= 2 else project_name

        prompt = (
            f'请使用 web_search 工具搜索工程项目"{search_term}"，判断搜索结果中是否有与"{project_name}"相关的公开项目信息。\n\n'
            f'注意：项目可能有简称、分期（一期/二期）、别名等变体，这些都算匹配。\n\n'
            f'请输出 JSON（不要包含其他文字）：\n'
            f'{{"match": true/false, "candidates": ["候选项目名称1", "候选项目名称2"]}}\n\n'
            f'- match=true 表示搜索结果中有该项目的明确信息\n'
            f'- candidates: match=false 时填写搜索结果中找到的可能相关项目名称（最多5个，仅填真实搜索到的名称）'
        )

        try:
            response = cls._send_research_request(prompt, timeout=90)
            logger.info(f"[AI-Research-Project-PreCheck] 原始回复 ({len(response)} chars): {response[:500]}")
            parsed = cls._extract_json(response)
            return {
                'match': bool(parsed.get('match', False)),
                'candidates': parsed.get('candidates', [])[:5]
            }
        except Exception as e:
            logger.error(f"项目预搜索失败: {project_name}: {e}")
            raise

    @classmethod
    def _extract_project_core_name(cls, project_name):
        """从项目全名中提取核心名称，去除城市/区县前缀"""
        cities = (
            '北京', '上海', '广州', '深圳', '天津', '重庆', '成都', '武汉', '杭州', '南京',
            '西安', '苏州', '长沙', '沈阳', '哈尔滨', '济南', '郑州', '青岛', '大连', '宁波',
            '厦门', '福州', '昆明', '贵阳', '南宁', '太原', '合肥', '南昌', '兰州', '乌鲁木齐',
            '海口', '银川', '西宁', '呼和浩特', '拉萨', '石家庄', '长春', '南通', '无锡', '佛山',
            '东莞', '温州', '烟台', '徐州', '常州', '嘉兴', '中山',
        )
        name = project_name
        for city in cities:
            if name.startswith(city) and len(name) - len(city) >= 2:
                name = name[len(city):]
                break
        return name.strip()

    @classmethod
    def _build_project_research_prompt(cls, project_name, search_term=None):
        """构建项目调研的 AI 提示词 — 根据 IS_OVS 切换中/英文版本。"""
        try:
            from flask import current_app
            is_ovs = bool(current_app.config.get('IS_OVS'))
        except Exception:
            is_ovs = False

        if is_ovs:
            return cls._build_project_research_prompt_sg(project_name, search_term)
        return cls._build_project_research_prompt_cn(project_name, search_term)

    @classmethod
    def _build_project_research_prompt_cn(cls, project_name, search_term=None):
        """中国大陆项目调研 prompt — 8 个定向搜索维度（含智能化/弱电专项）"""
        current_year = datetime.utcnow().year
        kw = search_term or project_name
        return (
            f'请对工程项目「{project_name}」进行全面的公开信息调研。\n\n'
            f'请使用 web_search 工具，按以下 8 个方向分别搜索（每个方向搜一次）：\n'
            f'1. "{kw}" 总投资 建筑面积 开工 竣工\n'
            f'2. "{kw}" 建设单位 总承包 施工 设计院\n'
            f'3. "{kw}" 立项 批复 发改委 环评\n'
            f'4. "{kw}" {current_year} 招标 进展 中标\n'
            f'5. "{kw}" 弱电 智能化 通信 对讲 广播 安防 招标 中标\n'
            f'6. "{kw}" 弱电顾问 智能化顾问 系统集成商 专项分包\n'
            f'7. "{kw}" 建设方 投资方 法定代表人 联系方式 地址 邮箱\n'
            f'8. "{kw}" 运营单位 管理公司 负责人\n\n'
            f'## 最重要的规则\n'
            f'**严禁编造任何信息！** 如果搜索结果中没有提到某项信息，该字段必须留空（空字符串""或空数组[]）。\n'
            f'- 只有搜索结果中**原文包含**的真实信息才能填入\n'
            f'- **宁可留空也不要编造数据**\n\n'
            f'## 输出格式\n'
            f'请严格按以下 JSON 格式输出，不要包含其他文字。找不到的信息一律留空。\n\n'
            f'{{\n'
            f'    "project_overview": {{\n'
            f'        "description": "项目功能描述/建设内容",\n'
            f'        "total_investment": "总投资额",\n'
            f'        "total_area": "建筑面积/总面积",\n'
            f'        "land_area": "占地面积",\n'
            f'        "start_date": "开工时间",\n'
            f'        "completion_date": "预计竣工时间",\n'
            f'        "city": "所在城市",\n'
            f'        "address": "详细地址",\n'
            f'        "project_phase": "当前阶段（如：规划中/施工中/已竣工）"\n'
            f'    }},\n'
            f'    "stakeholders": {{\n'
            f'        "investor": "投资方/业主单位名称",\n'
            f'        "investor_address": "投资方地址",\n'
            f'        "investor_contact": "投资方联系方式（电话/邮箱）",\n'
            f'        "investor_legal_rep": "法定代表人姓名",\n'
            f'        "key_contacts": [\n'
            f'            {{"name": "姓名", "role": "职务", "contact": "联系方式（如有）"}}\n'
            f'        ],\n'
            f'        "general_contractor": "总承包商",\n'
            f'        "design_institute": "综合设计院",\n'
            f'        "smart_systems_consultant": "弱电顾问/智能化顾问单位（如有）",\n'
            f'        "smart_systems_integrator": "弱电/智能化系统集成商（如有）",\n'
            f'        "operator": "运营单位/物业管理方",\n'
            f'        "operator_contact": "运营单位负责人及联系方式（如有）",\n'
            f'        "subcontractors": ["其他已知分包商列表"]\n'
            f'    }},\n'
            f'    "smart_systems_procurement": {{\n'
            f'        "status": "智能化/弱电招标状态：已招标/招标中/未开始/未知",\n'
            f'        "bid_records": [\n'
            f'            {{"project": "子项目名称", "winner": "中标单位", "amount": "中标金额", "date": "招标/中标时间"}}\n'
            f'        ]\n'
            f'    }},\n'
            f'    "recent_updates": [\n'
            f'        {{"date": "YYYY-MM-DD", "content": "动态描述", "type": "招标/中标/开工/批复/公示/竣工"}}\n'
            f'    ],\n'
            f'    "sales_suggestions": ["基于搜索到的真实信息给出的销售切入建议，重点关注智能化/通信系统商机"]\n'
            f'}}\n\n'
            f'注意：\n'
            f'- recent_updates 按时间倒序排列，最新的在前\n'
            f'- sales_suggestions 必须基于搜索到的**真实信息**，不要给通用建议\n'
            f'- 如果是非公开的小型项目搜不到信息，所有字段留空即可\n'
            f'- **宁可留空也不要编造数据**'
        )

    @classmethod
    def _build_project_research_prompt_sg(cls, project_name, search_term=None):
        """SEA 项目调研 prompt — 英文，使用本地术语 ELV / M&E / IBMS / BCA / URA。"""
        current_year = datetime.utcnow().year
        kw = search_term or project_name
        return (
            f'Conduct comprehensive public-domain research on the construction project "{project_name}".\n\n'
            f'Use the web_search tool to run searches across the 8 dimensions below (one search per dimension):\n'
            f'1. "{kw}" total investment GFA groundbreaking completion date\n'
            f'2. "{kw}" developer main contractor M&E consultant\n'
            f'3. "{kw}" planning approval BCA URA OSS BOI EIA permit\n'
            f'4. "{kw}" {current_year} tender award progress milestone\n'
            f'5. "{kw}" ELV ICT IBMS smart building communication two-way radio public address security tender award\n'
            f'6. "{kw}" ELV consultant ICT specialist systems integrator specialist subcontractor\n'
            f'7. "{kw}" developer investor authorized representative contact address email\n'
            f'8. "{kw}" facility operator property management operations director\n\n'
            f'Useful regional sources:\n'
            f'- Singapore: BCA Construction Information Portal, URA, EDB, GeBIZ\n'
            f'- Malaysia: CIDB, MyEPDM, MyGovernment tenders portal\n'
            f'- Indonesia: PUPR, OSS, BKPM, LKPP\n'
            f'- Thailand: BOI, e-GP, OneStart\n'
            f'- Vietnam: National Public Procurement Network (muasamcong.mpi.gov.vn)\n'
            f'- Philippines: PhilGEPS, DPWH\n\n'
            f'## Critical rule\n'
            f'**DO NOT fabricate any information.** If a fact is not present in search results, leave the field empty '
            f'(empty string "" or empty array []).\n'
            f'- Only fill fields with verbatim facts from the search results.\n'
            f'- **Prefer empty over fabricated.**\n\n'
            f'## Output format\n'
            f'Return strict JSON only. No surrounding prose. Empty fields when not found.\n\n'
            f'{{\n'
            f'    "project_overview": {{\n'
            f'        "description": "Project scope and built-form (English)",\n'
            f'        "total_investment": "Total investment with currency (e.g. USD 800M, SGD 1.2B, RM 500M)",\n'
            f'        "total_area": "GFA / total floor area",\n'
            f'        "land_area": "Site area",\n'
            f'        "start_date": "Groundbreaking date",\n'
            f'        "completion_date": "Expected completion / TOP date",\n'
            f'        "city": "City / district",\n'
            f'        "address": "Full address",\n'
            f'        "project_phase": "Current stage (Planning / Under Construction / Completed)"\n'
            f'    }},\n'
            f'    "stakeholders": {{\n'
            f'        "investor": "Developer / owner entity",\n'
            f'        "investor_address": "Developer registered address",\n'
            f'        "investor_contact": "Developer contact (phone / email)",\n'
            f'        "investor_legal_rep": "Authorized representative / managing director",\n'
            f'        "key_contacts": [\n'
            f'            {{"name": "name", "role": "role", "contact": "contact info"}}\n'
            f'        ],\n'
            f'        "general_contractor": "Main contractor",\n'
            f'        "design_institute": "Lead M&E consultant / engineering consultancy",\n'
            f'        "smart_systems_consultant": "ELV / ICT / IBMS consultant (if any)",\n'
            f'        "smart_systems_integrator": "ELV / smart-building systems integrator (if any)",\n'
            f'        "operator": "Facility operator / property management",\n'
            f'        "operator_contact": "Operator contact and lead person (if any)",\n'
            f'        "subcontractors": ["Other known specialist subcontractors"]\n'
            f'    }},\n'
            f'    "smart_systems_procurement": {{\n'
            f'        "status": "ELV / ICT package status: Tendered / Tendering / Not Started / Unknown",\n'
            f'        "bid_records": [\n'
            f'            {{"project": "Sub-package name", "winner": "Awarded company", "amount": "Awarded value with currency", "date": "Tender / award date"}}\n'
            f'        ]\n'
            f'    }},\n'
            f'    "recent_updates": [\n'
            f'        {{"date": "YYYY-MM-DD", "content": "Update description (English)", "type": "Tender / Award / Groundbreaking / Approval / Notice / Completion"}}\n'
            f'    ],\n'
            f'    "sales_suggestions": ["Sales angle based on real search findings — focus on industrial communication systems (two-way radio, dispatch console, IP intercom, public address)"]\n'
            f'}}\n\n'
            f'Notes:\n'
            f'- Sort recent_updates by date descending (newest first).\n'
            f'- sales_suggestions must reference **real findings** from search results — no generic advice.\n'
            f'- If the project is small or non-public and nothing is found, leave all fields empty.\n'
            f'- All free-text fields must be in English.\n'
            f'- **Prefer empty over fabricated.**'
        )
