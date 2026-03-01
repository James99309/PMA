#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""销售评估报告生成器

后台线程入口，负责：
1. 权限检查
2. 调用 SalesReviewDataService 收集数据
3. 生成报告1（详细工作数据整理 - 模板渲染）
4. 生成报告2（客户画像分析 - AI 分析）
5. 上传两份 .md 文件到聊天对话
6. 发送进度/完成消息
"""

import io
import json
import logging
import os
import uuid
from datetime import datetime, timezone

from app import db
from app.models.chat import ChatConversation, ChatMessage, ChatParticipant
from app.models.user import User, Affiliation

logger = logging.getLogger(__name__)


class SalesReviewGenerator:
    """销售评估报告生成器"""

    @classmethod
    def generate_review(cls, app, target_user_id, requesting_user_id, conversation_id):
        """后台线程入口"""
        with app.app_context():
            target_user = User.query.get(target_user_id)
            target_name = target_user.real_name or target_user.username if target_user else f'ID:{target_user_id}'

            try:
                # 1. 权限检查
                if not cls._check_permission(requesting_user_id, target_user_id):
                    cls._post_message(conversation_id,
                                      f'抱歉，您没有权限评估 {target_name} 的销售表现。'
                                      f'只有管理员、CEO、部门经理或直属上级可以执行此操作。')
                    return

                # 2. 进度消息：开始收集数据
                cls._post_message(conversation_id,
                                  f'正在收集 {target_name} 的业务数据...')

                # 3. 收集数据
                from app.services.sales_review_service import SalesReviewDataService
                data = SalesReviewDataService.collect_review_data(target_user_id)

                # 4. 进度消息：数据收集完成
                stats = data.get('statistics', {})
                cls._post_message(
                    conversation_id,
                    f'数据收集完成（客户 {stats.get("customer_count", 0)} 家、'
                    f'联系人 {stats.get("contact_count", 0)} 个、'
                    f'项目 {stats.get("project_count", 0)} 个、'
                    f'报价 {stats.get("own_quotation_count", 0)} 份），'
                    f'正在生成分析报告...'
                )

                # 5. 生成报告1：详细工作数据整理（纯模板渲染，不需要 AI）
                report1_content = cls._render_work_data_report(data)

                # 6. 生成报告2：客户画像分析（AI 分析）
                report2_content = cls._generate_profile_report(data)

                # 7. 上传两份文件
                today = datetime.now().strftime('%Y%m%d')
                report1_name = f'{target_name}_详细工作数据整理_{today}.md'
                report2_name = f'{target_name}_客户画像分析报告_{today}.md'

                cls._upload_text_file(conversation_id, requesting_user_id,
                                      report1_name, report1_content)
                cls._upload_text_file(conversation_id, requesting_user_id,
                                      report2_name, report2_content)

                # 8. 完成消息
                cls._post_message(
                    conversation_id,
                    f'{target_name} 的销售评估报告已生成完毕，请查看上方两份文件：\n'
                    f'1. **{report1_name}** - 详细工作数据整理\n'
                    f'2. **{report2_name}** - 客户画像分析报告'
                )

            except Exception as e:
                logger.error(f'销售评估报告生成失败: {e}', exc_info=True)
                try:
                    cls._post_message(
                        conversation_id,
                        f'生成 {target_name} 的评估报告时出错：{str(e)[:200]}'
                    )
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # 权限检查
    # ------------------------------------------------------------------
    @classmethod
    def _check_permission(cls, requesting_user_id, target_user_id):
        """检查请求者是否有权评估目标用户"""
        # 可以评估自己
        if requesting_user_id == target_user_id:
            return True

        requester = User.query.get(requesting_user_id)
        if not requester:
            return False

        # admin / ceo 可评估任何人
        if requester.role in ('admin', 'ceo'):
            return True

        target = User.query.get(target_user_id)
        if not target:
            return False

        # 部门经理可评估同部门成员
        if (requester.is_department_manager
                and requester.department
                and requester.department == target.department
                and requester.company_name == target.company_name):
            return True

        # 有 Affiliation 关系的上级（viewer 可以看 owner 的数据，即 viewer 是上级）
        aff = Affiliation.query.filter_by(
            viewer_id=requesting_user_id,
            owner_id=target_user_id,
        ).first()
        if aff:
            return True

        return False

    # ------------------------------------------------------------------
    # 进度消息
    # ------------------------------------------------------------------
    @classmethod
    def _post_message(cls, conversation_id, content):
        """向聊天对话发送进度消息（AI 消息）"""
        try:
            msg = ChatMessage(
                conversation_id=conversation_id,
                sender_id=None,
                content=content,
                message_type='text',
                is_ai_response=True,
                source_language='zh',
            )
            db.session.add(msg)
            conv = ChatConversation.query.get(conversation_id)
            if conv:
                conv.updated_at = datetime.now(timezone.utc)
            db.session.commit()
        except Exception as e:
            logger.error(f'发送进度消息失败: {e}')
            db.session.rollback()

    # ------------------------------------------------------------------
    # 文件上传
    # ------------------------------------------------------------------
    @classmethod
    def _upload_text_file(cls, conversation_id, user_id, filename, content):
        """将文本内容作为 .md 文件上传到聊天对话"""
        try:
            file_bytes = content.encode('utf-8')
            file_size = len(file_bytes)
            unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"

            # 直接保存到本地存储
            local_dir = os.path.join('.', 'storage', 'chat_files', str(conversation_id))
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(local_dir, unique_name)
            with open(local_path, 'wb') as f:
                f.write(file_bytes)
            file_url = f"chat_files/{conversation_id}/{unique_name}"

            # 尝试上传到 NAS（如果可用）
            try:
                from app.utils.smart_storage_manager import get_smart_storage
                smart_storage = get_smart_storage()
                file_obj = io.BytesIO(file_bytes)
                file_obj.name = unique_name
                result = smart_storage.upload_file(
                    object_id=conversation_id,
                    file=file_obj,
                    filename=unique_name,
                    file_type='attachment',
                    bucket_type='chat',
                    business_type='chat',
                )
                if result:
                    file_url = result.get('storage_path', file_url)
            except Exception as ue:
                logger.warning(f'NAS 上传失败，使用本地文件: {ue}')

            # 创建文件消息
            msg = ChatMessage(
                conversation_id=conversation_id,
                sender_id=None,
                content=None,
                message_type='file',
                file_url=file_url,
                file_name=filename,
                file_size=file_size,
                is_ai_response=True,
                source_language='zh',
            )
            db.session.add(msg)
            conv = ChatConversation.query.get(conversation_id)
            if conv:
                conv.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            logger.info(f'评估报告文件上传成功: {filename}')

        except Exception as e:
            logger.error(f'上传评估报告文件失败: {e}', exc_info=True)
            db.session.rollback()

    # ------------------------------------------------------------------
    # 报告1：详细工作数据整理（模板渲染）
    # ------------------------------------------------------------------
    @classmethod
    def _render_work_data_report(cls, data):
        """渲染详细工作数据整理报告（纯模板，不需要 AI）"""
        profile = data['user_profile']
        stats = data['statistics']
        customers = data['customers']
        contacts = data['contacts']
        projects = data['projects']
        quotations = data['quotations']
        worklogs = data['worklogs']

        today = datetime.now().strftime('%Y-%m-%d')
        lines = []

        # 标题
        lines.append(f'{profile["real_name"]}（{profile["role"]}）详细工作数据整理')
        lines.append(f'数据来源：PMA 系统自动生成')
        lines.append(f'整理日期：{today}')
        lines.append(f'评估期间：{profile["created_at"]}（入职）~ {today}（当前）'
                      f'约{profile["tenure_days"]}天 / 约{profile["tenure_months"]}个月')
        lines.append(f'用户ID：{profile["id"]} ({profile["username"]}) | '
                     f'真实姓名：{profile["real_name"]} | 角色：{profile["role"]}')
        lines.append('')

        # 一、客户情况
        lines.append('一、客户情况')
        lines.append(f'1.1 系统录入客户（{stats["customer_count"]}家）')
        if customers:
            lines.append('| # | 客户名称 | 类型 | 行业 | 地区 | 创建时期 |')
            lines.append('|---|---------|------|------|------|---------|')
            for i, c in enumerate(customers, 1):
                region = c.get('region') or c.get('city') or c.get('country') or ''
                lines.append(
                    f'| {i} | {c["name"]} | {c.get("type", "")} | '
                    f'{c.get("industry", "")} | {region} | {c.get("created_at", "")} |'
                )
        lines.append('')

        # 客户类型分布
        type_dist = stats.get('customer_type_distribution', {})
        if type_dist:
            total = stats['customer_count']
            dist_parts = [f'{t} {n}家（{n/total*100:.1f}%）' for t, n in
                          sorted(type_dist.items(), key=lambda x: -x[1])]
            lines.append(f'客户类型分布：{"、".join(dist_parts)}')
            lines.append('')

        # 地区分布
        region_dist = stats.get('customer_region_distribution', {})
        if region_dist:
            total = stats['customer_count']
            dist_parts = [f'{r} {n}家（{n/total*100:.1f}%）' for r, n in
                          sorted(region_dist.items(), key=lambda x: -x[1])]
            lines.append(f'地区分布：{"、".join(dist_parts)}')
            lines.append('')

        # 1.2 联系人
        lines.append(f'1.2 联系人（{stats["contact_count"]}个）')
        if contacts:
            lines.append('| # | 姓名 | 公司 | 职位/角色 | 创建日期 |')
            lines.append('|---|------|------|----------|---------|')
            for i, ct in enumerate(contacts, 1):
                lines.append(
                    f'| {i} | {ct["name"]} | {ct.get("company_name", "")} | '
                    f'{ct.get("position", "")} | {ct.get("created_at", "")} |'
                )
        lines.append('')

        # 每家公司联系人数量
        cpc = stats.get('contacts_per_company', {})
        if cpc:
            lines.append('多联系人深度覆盖公司：')
            for company, count in cpc.items():
                if count >= 2:
                    lines.append(f'- {company}：{count}个联系人')
            lines.append('')

        # 二、项目情况
        lines.append('二、项目情况')
        lines.append(f'2.1 项目总览（{stats["project_count"]}个项目，'
                     f'其中自创建 {stats["self_created_project_count"]}个）')
        if projects:
            lines.append('| # | 项目名称 | 行业 | 阶段 | 报价金额 | 币种 | 创建人 | 创建日期 |')
            lines.append('|---|---------|------|------|---------|------|--------|---------|')
            for i, p in enumerate(projects, 1):
                amount_str = f'{p["quotation_amount"]:,.0f}' if p.get('quotation_amount') else '-'
                creator = '自己' if p.get('is_self_created') else p.get('created_by_name', '')
                lines.append(
                    f'| {i} | {p["name"]} | {p.get("industry", "")} | '
                    f'{p.get("stage", "")} | {amount_str} | '
                    f'{p.get("quotation_currency", "")} | {creator} | '
                    f'{p.get("created_at", "")} |'
                )
        lines.append('')

        # 项目阶段分布
        stage_dist = stats.get('project_stage_distribution', {})
        if stage_dist:
            dist_parts = [f'{s} {n}个' for s, n in
                          sorted(stage_dist.items(), key=lambda x: -x[1])]
            lines.append(f'阶段分布：{"、".join(dist_parts)}')

        # 活跃 pipeline
        pipeline_amount = stats.get('active_pipeline_amount', {})
        if pipeline_amount:
            parts = [f'{currency} {amount:,.0f}' for currency, amount in pipeline_amount.items()]
            lines.append(f'活跃 Pipeline：{stats.get("active_pipeline_count", 0)}个项目，'
                        f'金额 {" + ".join(parts)}')
        lines.append('')

        # 三、报价情况
        lines.append('三、报价情况')
        own_q = quotations['own_quotations']
        cross_q = quotations['cross_team_quotations']
        lines.append(f'3.1 自有报价（{len(own_q)}份）')
        if own_q:
            lines.append('| # | 报价编号 | 关联项目 | 客户 | 金额 | 币种 | 阶段 | 创建日期 |')
            lines.append('|---|---------|---------|------|------|------|------|---------|')
            for i, q in enumerate(own_q, 1):
                amount_str = f'{q["amount"]:,.0f}' if q.get('amount') else '-'
                lines.append(
                    f'| {i} | {q.get("quotation_number", "")} | '
                    f'{q.get("project_name", "")} | {q.get("customer_name", "")} | '
                    f'{amount_str} | {q.get("currency", "")} | '
                    f'{q.get("project_stage", "")} | {q.get("created_at", "")} |'
                )
        lines.append('')

        if cross_q:
            lines.append(f'3.2 跨团队报价（由其他人为其项目出的报价，{len(cross_q)}份）')
            lines.append('| # | 报价编号 | 关联项目 | 金额 | 币种 | 报价人 | 创建日期 |')
            lines.append('|---|---------|---------|------|------|--------|---------|')
            for i, q in enumerate(cross_q, 1):
                amount_str = f'{q["amount"]:,.0f}' if q.get('amount') else '-'
                lines.append(
                    f'| {i} | {q.get("quotation_number", "")} | '
                    f'{q.get("project_name", "")} | {amount_str} | '
                    f'{q.get("currency", "")} | {q.get("owner_name", "")} | '
                    f'{q.get("created_at", "")} |'
                )
            lines.append('')

        # 四、工作日志
        lines.append('四、工作日志')
        wl_list = worklogs['worklogs']
        wi_list = worklogs['work_items']
        lines.append(f'4.1 日志提交情况（共{stats["worklog_count"]}条，'
                     f'已提交 {stats["worklog_submitted_count"]}条，'
                     f'草稿 {stats["worklog_draft_count"]}条，'
                     f'提交率 {stats["worklog_submit_rate"]}）')
        lines.append('')

        lines.append(f'4.2 工作项明细（{stats["work_item_count"]}条）')
        if wi_list:
            lines.append('| # | 标题 | 工作类型 | 日期 | 时长(h) | 关联项目 | 关联客户 | 状态 |')
            lines.append('|---|------|---------|------|--------|---------|---------|------|')
            for i, wi in enumerate(wi_list, 1):
                hours = wi.get('actual_hours') or wi.get('estimated_hours') or ''
                lines.append(
                    f'| {i} | {wi.get("title", "")} | {wi.get("work_type", "")} | '
                    f'{wi.get("planned_date", "")} | {hours} | '
                    f'{wi.get("project_name", "")} | {wi.get("customer_name", "")} | '
                    f'{wi.get("status", "")} |'
                )
        lines.append('')

        # 工作类型分布
        wt_dist = stats.get('work_type_distribution', {})
        if wt_dist:
            dist_parts = [f'{t} {n}条' for t, n in
                          sorted(wt_dist.items(), key=lambda x: -x[1])]
            lines.append(f'工作类型分布：{"、".join(dist_parts)}')
            lines.append('')

        # 五、系统操作活跃度
        lines.append('五、系统操作活跃度')
        lines.append(f'变更记录总数：{stats["change_log_count"]}条')
        module_dist = stats.get('change_log_module_distribution', {})
        if module_dist:
            dist_parts = [f'{m} {n}条' for m, n in
                          sorted(module_dist.items(), key=lambda x: -x[1])]
            lines.append(f'模块分布：{"、".join(dist_parts)}')
        op_dist = stats.get('change_log_operation_distribution', {})
        if op_dist:
            dist_parts = [f'{o} {n}条' for o, n in
                          sorted(op_dist.items(), key=lambda x: -x[1])]
            lines.append(f'操作类型分布：{"、".join(dist_parts)}')
        lines.append('')

        # 六、数据概览表
        lines.append('六、数据概览表')
        lines.append('| 指标 | 数据 |')
        lines.append('|------|------|')
        lines.append(f'| 在职天数 | 约{profile["tenure_months"]}个月（{profile["created_at"]} ~ 今） |')
        lines.append(f'| 提交日志 | {stats["worklog_submitted_count"]}天（{stats["worklog_submit_rate"]}提交率） |')
        lines.append(f'| 系统录入客户 | {stats["customer_count"]}家 |')
        lines.append(f'| 系统录入联系人 | {stats["contact_count"]}个 |')
        lines.append(f'| 项目数 | {stats["project_count"]}个（自创建{stats["self_created_project_count"]}个） |')
        lines.append(f'| 自有报价 | {stats["own_quotation_count"]}份 |')
        lines.append(f'| 跨团队报价 | {stats["cross_team_quotation_count"]}份 |')
        lines.append(f'| 工作项条目 | {stats["work_item_count"]}条 |')
        lines.append(f'| 变更记录 | {stats["change_log_count"]}条 |')
        lines.append('')

        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # 报告2：客户画像分析（AI 生成）
    # ------------------------------------------------------------------
    @classmethod
    def _generate_profile_report(cls, data):
        """使用 AI 生成 8 维度客户画像分析报告"""
        profile = data['user_profile']
        stats = data['statistics']

        # 构建给 AI 的数据摘要（控制 token 用量，不传完整明细）
        data_summary = cls._build_ai_data_summary(data)

        prompt = f"""你是PMA系统的销售绩效分析师。请根据以下销售人员的业务数据，生成一份完整的工作表现与行业客户画像分析报告。

## 目标人员
- 姓名：{profile['real_name']}
- 角色：{profile['role']}
- 部门/公司：{profile.get('department', '')} / {profile.get('company_name', '')}
- 在职时间：{profile['created_at']}至今，约{profile['tenure_months']}个月

## 报告结构要求

### 第一部分：总览评级表
输出一个总览表格，包含4个维度的评级：
| 维度 | 评级 | 说明 |
- 业务能力（强/中/弱）
- 工作纪律（好/中/差）
- 业绩前景（高/中等偏上/中/低）
- 客户资产沉淀（优秀/良好/一般/薄弱）

### 第二部分：关键发现
1.1 核心数据概览（用表格呈现关键指标）
1.2 优势（列出3-6个具体优势，必须用数据支撑）
1.3 待改进（列出3-5个改进点，客观但建设性）

### 第三部分：行业客户画像分析（8维度）

评估方法论说明后，按以下框架评估：

| 层级 | 画像维度 | 包含角色 |
|------|---------|---------|
| 需求端 | ① 使用方/业主 | 运营使用人员 / 运维IT / 采购 |
| 需求端 | ② 建设方 | 新建项目方 / 已有设施扩建方 |
| 决策链 | ③ 设计院与顾问 | 方案设计 / 图纸出具 / 品牌推荐 |
| 决策链 | ④ 行业协会 | 行业交流 / 标准制定 / 资源汇聚 |
| 执行链 | ⑤ 总包/EPC | 工程总承包 / 施工管理 |
| 执行链 | ⑥ 集成商 | 系统集成 / 分包实施 |
| 合作与竞争 | ⑦ 渠道合作伙伴 | 代理商 / 资源互换方 |
| 合作与竞争 | ⑧ 竞争品牌/竞合方 | 竞品厂商 / 可合作的竞争对手 |

星级标准：☆☆☆☆☆=零接触 ★☆☆☆☆=初步 ★★☆☆☆=少量 ★★★☆☆=中等 ★★★★☆=良好 ★★★★★=优秀

输出覆盖度总览表格：
| 画像维度 | 覆盖度 | 评估说明 |
对于客户数据较多的维度，增加子维度评级。

### 第四部分：改进建议
按优先级分为 P0（立即）、P1（短期）、P2（中期）给出具体可操作的改进建议。

## 业务数据
{data_summary}

## 输出要求
- 输出纯 Markdown 格式
- 标题格式：第一行为"姓名（角色）"，第二行为"工作表现与行业客户画像分析报告"
- 评估必须基于数据，不要编造不存在的信息
- 客观、专业、有建设性
- 如果某个维度数据不足，直接标注"数据不足，无法评估"
"""

        try:
            from app.services.openclaw_provider import send_openclaw_request
            response = send_openclaw_request(prompt, timeout=300)
            return response
        except Exception as e:
            logger.error(f'AI 生成画像报告失败: {e}', exc_info=True)
            # 回退：生成简易报告
            return cls._fallback_profile_report(data)

    @classmethod
    def _build_ai_data_summary(cls, data):
        """构建给 AI 的数据摘要（控制在合理 token 范围内）"""
        profile = data['user_profile']
        stats = data['statistics']
        customers = data['customers']
        contacts = data['contacts']
        projects = data['projects']

        parts = []

        # 核心统计
        parts.append('### 核心指标')
        parts.append(f'- 在职天数：约{profile["tenure_months"]}个月')
        parts.append(f'- 客户：{stats["customer_count"]}家')
        parts.append(f'- 联系人：{stats["contact_count"]}个')
        parts.append(f'- 项目：{stats["project_count"]}个（自创建{stats["self_created_project_count"]}个）')
        parts.append(f'- 自有报价：{stats["own_quotation_count"]}份')
        parts.append(f'- 跨团队报价：{stats["cross_team_quotation_count"]}份')
        parts.append(f'- 工作日志：{stats["worklog_count"]}条'
                     f'（提交{stats["worklog_submitted_count"]}条，'
                     f'草稿{stats["worklog_draft_count"]}条，'
                     f'提交率{stats["worklog_submit_rate"]}）')
        parts.append(f'- 工作项：{stats["work_item_count"]}条')
        parts.append(f'- 系统操作记录：{stats["change_log_count"]}条')

        # 客户列表
        parts.append('\n### 客户列表')
        parts.append('| 客户名称 | 类型 | 行业 | 地区 |')
        parts.append('|---------|------|------|------|')
        for c in customers:
            region = c.get('region') or c.get('city') or c.get('country') or ''
            parts.append(f'| {c["name"]} | {c.get("type", "")} | '
                        f'{c.get("industry", "")} | {region} |')

        # 客户类型分布
        parts.append(f'\n客户类型分布：{json.dumps(stats.get("customer_type_distribution", {}), ensure_ascii=False)}')

        # 联系人 - 只列每家公司的联系人数量
        parts.append('\n### 联系人深度覆盖')
        cpc = stats.get('contacts_per_company', {})
        for company, count in cpc.items():
            # 列出该公司的联系人职位
            positions = [ct.get('position', '') for ct in contacts
                        if ct.get('company_name') == company and ct.get('position')]
            pos_str = '、'.join(positions) if positions else ''
            parts.append(f'- {company}：{count}个联系人{" (" + pos_str + ")" if pos_str else ""}')

        # 项目列表
        parts.append('\n### 项目列表')
        parts.append('| 项目名称 | 行业 | 阶段 | 报价金额 | 币种 | 自创建 |')
        parts.append('|---------|------|------|---------|------|--------|')
        for p in projects:
            amount = f'{p["quotation_amount"]:,.0f}' if p.get('quotation_amount') else '-'
            self_created = '是' if p.get('is_self_created') else '否'
            parts.append(f'| {p["name"]} | {p.get("industry", "")} | '
                        f'{p.get("stage", "")} | {amount} | '
                        f'{p.get("quotation_currency", "")} | {self_created} |')

        # Pipeline
        parts.append(f'\n活跃 Pipeline：{stats.get("active_pipeline_count", 0)}个项目')
        pipeline_amount = stats.get('active_pipeline_amount', {})
        if pipeline_amount:
            for currency, amount in pipeline_amount.items():
                parts.append(f'  {currency} {amount:,.0f}')

        # 报价摘要
        parts.append(f'\n### 报价摘要')
        own_amount = stats.get('own_quotation_amount', {})
        if own_amount:
            for currency, amount in own_amount.items():
                parts.append(f'- 自有报价金额：{currency} {amount:,.0f}')
        cross_amount = stats.get('cross_team_quotation_amount', {})
        if cross_amount:
            for currency, amount in cross_amount.items():
                parts.append(f'- 跨团队报价金额：{currency} {amount:,.0f}')

        # 工作类型分布
        wt_dist = stats.get('work_type_distribution', {})
        if wt_dist:
            parts.append(f'\n### 工作类型分布')
            for wt, count in sorted(wt_dist.items(), key=lambda x: -x[1]):
                parts.append(f'- {wt}：{count}条')

        # 工作项关键内容（最多20条）
        work_items = data['worklogs']['work_items']
        if work_items:
            parts.append('\n### 工作项内容（最近）')
            for wi in work_items[:20]:
                date = wi.get('planned_date', '')
                title = wi.get('title', '')
                notes = (wi.get('execution_notes') or '')[:100]
                customer = wi.get('customer_name', '')
                parts.append(f'- [{date}] {title}'
                            f'{" | 客户:" + customer if customer else ""}'
                            f'{" | 备注:" + notes if notes else ""}')

        return '\n'.join(parts)

    @classmethod
    def _fallback_profile_report(cls, data):
        """AI 调用失败时的回退报告"""
        profile = data['user_profile']
        stats = data['statistics']
        today = datetime.now().strftime('%Y-%m-%d')

        lines = [
            f'{profile["real_name"]}（{profile["role"]}）',
            '工作表现与行业客户画像分析报告',
            '',
            f'评估期间：{profile["created_at"]}（入职）~ {today}（约{profile["tenure_months"]}个月）',
            '',
            '> 注意：AI 分析服务暂时不可用，以下为基础数据统计报告。',
            '',
            '## 核心数据概览',
            '| 指标 | 数据 |',
            '|------|------|',
            f'| 客户 | {stats["customer_count"]}家 |',
            f'| 联系人 | {stats["contact_count"]}个 |',
            f'| 项目 | {stats["project_count"]}个 |',
            f'| 自有报价 | {stats["own_quotation_count"]}份 |',
            f'| 工作日志提交率 | {stats["worklog_submit_rate"]} |',
            f'| 工作项 | {stats["work_item_count"]}条 |',
            f'| 系统操作 | {stats["change_log_count"]}条 |',
            '',
            '## 客户类型分布',
            json.dumps(stats.get('customer_type_distribution', {}), ensure_ascii=False, indent=2),
            '',
            '## 项目阶段分布',
            json.dumps(stats.get('project_stage_distribution', {}), ensure_ascii=False, indent=2),
            '',
            '*完整的8维度画像分析需要 AI 服务支持，请稍后重试。*',
        ]
        return '\n'.join(lines)
