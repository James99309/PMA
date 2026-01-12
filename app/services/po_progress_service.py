# -*- coding: utf-8 -*-
"""
采购订单进度管理服务

提供阶段推进、超期检查、交期管理等功能。

权限规则：
- 供应链：可设定/调整交期，不能更新进度
- 工厂/供应商：只能更新进度，不能调整交期
- 管理员：全部权限
"""
from datetime import datetime, date
from app import db
from app.models.inventory import PurchaseOrder, PurchaseOrderStageHistory, PurchaseOrderDeliveryChange
import logging

logger = logging.getLogger(__name__)


# 阶段配置
PRODUCTION_STAGES = {
    'not_started': {
        'order': 0,
        'label_zh': '未开始',
        'label_en': 'Not Started',
        'progress_range': (0, 0),
        'can_manual_advance': True,
        'conditions': [],
        'next_stage': 'preparing'
    },
    'preparing': {
        'order': 1,
        'label_zh': '备料',
        'label_en': 'Preparing',
        'progress_range': (1, 20),
        'can_manual_advance': True,
        'conditions': [],
        'next_stage': 'producing'
    },
    'producing': {
        'order': 2,
        'label_zh': '生产',
        'label_en': 'Producing',
        'progress_range': (21, 60),
        'can_manual_advance': True,
        'conditions': [],
        'next_stage': 'testing'
    },
    'testing': {
        'order': 3,
        'label_zh': '测试',
        'label_en': 'Testing',
        'progress_range': (61, 80),
        'can_manual_advance': False,  # 不能手动推进，必须满足条件
        'conditions': [
            'factory_test_passed',
            'test_report_uploaded',
            'test_signed',
            'fat_completed_if_required'
        ],
        'next_stage': 'packaging'
    },
    'packaging': {
        'order': 4,
        'label_zh': '包装',
        'label_en': 'Packaging',
        'progress_range': (81, 95),
        'can_manual_advance': True,
        'conditions': [],
        'next_stage': 'ready'
    },
    'ready': {
        'order': 5,
        'label_zh': '待发货',
        'label_en': 'Ready to Ship',
        'progress_range': (91, 95),
        'can_manual_advance': True,
        'conditions': [],
        'next_stage': 'delivered'
    },
    'delivered': {
        'order': 6,
        'label_zh': '到货',
        'label_en': 'Delivered',
        'progress_range': (96, 100),
        'can_manual_advance': True,
        'conditions': [],
        'next_stage': None
    }
}


class PurchaseOrderProgressService:
    """采购订单进度管理服务"""

    @staticmethod
    def get_stage_config(stage_name):
        """获取阶段配置"""
        return PRODUCTION_STAGES.get(stage_name)

    @staticmethod
    def get_stage_label(stage_name, language='zh'):
        """获取阶段标签"""
        config = PRODUCTION_STAGES.get(stage_name)
        if not config:
            return stage_name
        return config.get(f'label_{language}', config.get('label_zh', stage_name))

    @staticmethod
    def advance_stage(order_id, new_stage, operator_info, force=False):
        """
        推进生产阶段

        Args:
            order_id: 订单ID
            new_stage: 目标阶段
            operator_info: 操作人信息 {
                'user_id': 内部用户ID,
                'external_name': 外部人员姓名,
                'external_token': 外部令牌,
                'reason': 变更原因
            }
            force: 是否强制推进（管理员可用）

        Returns:
            (success: bool, message: str)
        """
        order = PurchaseOrder.query.get(order_id)
        if not order:
            return False, '订单不存在'

        current_stage = order.production_status or 'not_started'
        current_config = PRODUCTION_STAGES.get(current_stage)
        target_config = PRODUCTION_STAGES.get(new_stage)

        if not target_config:
            return False, f'无效的目标阶段: {new_stage}'

        if not current_config:
            current_config = PRODUCTION_STAGES.get('not_started')

        # 检查阶段顺序（只能向前推进）
        if target_config['order'] <= current_config['order']:
            return False, '只能向前推进阶段，不能后退'

        # 检查推进条件（测试阶段特殊处理）
        if not force and not current_config.get('can_manual_advance', True):
            conditions_met, failed_conditions = PurchaseOrderProgressService.check_stage_conditions(
                order, current_config['conditions']
            )
            if not conditions_met:
                return False, f"推进条件未满足: {', '.join(failed_conditions)}"

        # 记录历史
        old_stage = order.production_status
        old_progress = order.production_progress or 0

        # 更新阶段
        order.production_status = new_stage
        order.production_progress = target_config['progress_range'][0]
        order.current_stage_started_at = datetime.now()
        order.last_stage_change_at = datetime.now()

        if operator_info.get('user_id'):
            order.last_stage_change_by_id = operator_info['user_id']

        # 自动更新订单状态（如果从 confirmed 开始生产）
        if order.status in ['draft', 'confirmed'] and new_stage != 'not_started':
            order.status = 'producing'

        # 创建历史记录
        change_type = 'force' if force else 'manual'
        if not current_config.get('can_manual_advance', True):
            change_type = 'condition_triggered'

        history = PurchaseOrderStageHistory(
            order_id=order.id,
            from_stage=old_stage,
            to_stage=new_stage,
            from_progress=old_progress,
            to_progress=order.production_progress,
            changed_by_user_id=operator_info.get('user_id'),
            changed_by_external_name=operator_info.get('external_name'),
            changed_by_external_token=operator_info.get('external_token'),
            change_type=change_type,
            change_reason=operator_info.get('reason', ''),
            change_notes=operator_info.get('notes', '')
        )
        db.session.add(history)

        # 检查是否超期
        PurchaseOrderProgressService.check_and_update_overdue_status(order)

        try:
            db.session.commit()

            # 如果超期，发送通知
            if order.is_overdue:
                PurchaseOrderProgressService.send_overdue_notification(order)

            return True, '阶段推进成功'
        except Exception as e:
            db.session.rollback()
            logger.error(f"阶段推进失败: {str(e)}")
            return False, f'操作失败: {str(e)}'

    @staticmethod
    def check_stage_conditions(order, conditions):
        """
        检查阶段推进条件

        Args:
            order: PurchaseOrder 实例
            conditions: 条件列表

        Returns:
            (all_met: bool, failed_conditions: list)
        """
        failed = []

        for condition in conditions:
            if condition == 'factory_test_passed':
                if order.factory_test_status != 'passed':
                    failed.append('工厂测试未通过')

            elif condition == 'test_report_uploaded':
                if not order.factory_test_report_url:
                    failed.append('测试报告未上传')

            elif condition == 'test_signed':
                if not order.factory_test_signed_at:
                    failed.append('测试报告未签证确认')

            elif condition == 'fat_completed_if_required':
                # 只有配置了 site_fat 才需要检查
                if order.verification_test_type == 'site_fat' and not order.fat_completed:
                    failed.append('现场FAT未完成')

        return len(failed) == 0, failed

    @staticmethod
    def update_progress(order_id, progress, notes=None, operator_info=None):
        """
        更新进度百分比（不改变阶段）

        Args:
            order_id: 订单ID
            progress: 进度百分比 0-100
            notes: 备注
            operator_info: 操作人信息

        Returns:
            (success: bool, message: str)
        """
        order = PurchaseOrder.query.get(order_id)
        if not order:
            return False, '订单不存在'

        # 验证进度范围
        current_config = PRODUCTION_STAGES.get(order.production_status)
        if current_config:
            min_progress, max_progress = current_config['progress_range']
            if progress < min_progress or progress > max_progress:
                return False, f'当前阶段进度范围为 {min_progress}%-{max_progress}%'

        order.production_progress = progress
        if notes:
            order.production_notes = notes

        try:
            db.session.commit()
            return True, '进度更新成功'
        except Exception as e:
            db.session.rollback()
            logger.error(f"进度更新失败: {str(e)}")
            return False, f'操作失败: {str(e)}'

    @staticmethod
    def check_and_update_overdue_status(order):
        """
        检查并更新超期状态

        Args:
            order: PurchaseOrder 实例
        """
        today = date.today()
        is_overdue = False
        overdue_days = 0
        overdue_milestone = None

        # 按优先级检查各个里程碑
        milestones = [
            ('test_complete', order.milestone_test_complete_date, 'testing'),
            ('ship', order.milestone_ship_date, 'ready'),
            ('delivery', order.confirmed_date, None)
        ]

        current_stage_order = PRODUCTION_STAGES.get(order.production_status, {}).get('order', 0)

        for milestone_name, target_date, related_stage in milestones:
            if not target_date:
                continue

            target_date_only = target_date.date() if isinstance(target_date, datetime) else target_date

            if today > target_date_only:
                # 检查是否已经过了相关阶段
                if related_stage:
                    related_stage_order = PRODUCTION_STAGES.get(related_stage, {}).get('order', 0)
                    if current_stage_order >= related_stage_order:
                        continue  # 已过该阶段，不算超期

                days = (today - target_date_only).days
                if days > overdue_days:
                    overdue_days = days
                    overdue_milestone = milestone_name
                    is_overdue = True

        order.is_overdue = is_overdue
        order.overdue_days = overdue_days
        order.overdue_milestone = overdue_milestone

    @staticmethod
    def send_overdue_notification(order):
        """
        发送超期通知

        Args:
            order: PurchaseOrder 实例
        """
        try:
            from app.services.event_dispatcher import trigger_event_notification

            milestone_labels = {
                'test_complete': '测试完成',
                'ship': '发货',
                'delivery': '交付'
            }

            context = {
                'order': order,
                'order_number': order.order_number,
                'supplier_name': order.company.company_name if order.company else '',
                'overdue_days': order.overdue_days,
                'overdue_milestone': milestone_labels.get(order.overdue_milestone, order.overdue_milestone),
                'current_stage': PurchaseOrderProgressService.get_stage_label(order.production_status)
            }

            # 通知订单创建人
            if order.created_by_id:
                trigger_event_notification(
                    event_key='purchase_order_overdue',
                    target_user_id=order.created_by_id,
                    context=context
                )

            logger.info(f"发送采购订单超期通知: {order.order_number}")

        except Exception as e:
            logger.error(f"发送超期通知失败: {str(e)}")

    @staticmethod
    def update_delivery_schedule(order_id, user_id, updates, change_reason=None):
        """
        更新交期计划（仅供应链可用）

        Args:
            order_id: 订单ID
            user_id: 操作人用户ID
            updates: 更新字段 {
                'confirmed_date': datetime,
                'milestone_test_complete_date': datetime,
                'milestone_ship_date': datetime
            }
            change_reason: 变更原因

        Returns:
            (success: bool, message: str)
        """
        order = PurchaseOrder.query.get(order_id)
        if not order:
            return False, '订单不存在'

        # 记录变更历史
        field_labels = {
            'confirmed_date': '总交期',
            'milestone_test_complete_date': '测试完成日期',
            'milestone_ship_date': '发货日期'
        }

        changes_made = []

        for field, new_value in updates.items():
            if field not in field_labels:
                continue

            old_value = getattr(order, field)

            # 格式化日期值
            old_str = old_value.strftime('%Y-%m-%d') if old_value else None
            new_str = new_value.strftime('%Y-%m-%d') if new_value else None

            if old_str != new_str:
                # 更新字段
                setattr(order, field, new_value)

                # 记录变更
                change_record = PurchaseOrderDeliveryChange(
                    order_id=order.id,
                    field_name=field,
                    old_value=old_str,
                    new_value=new_str,
                    change_reason=change_reason,
                    changed_by_id=user_id
                )
                db.session.add(change_record)
                changes_made.append(field_labels[field])

        if not changes_made:
            return True, '无变更'

        # 更新超期状态
        PurchaseOrderProgressService.check_and_update_overdue_status(order)

        try:
            db.session.commit()
            return True, f"已更新: {', '.join(changes_made)}"
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新交期失败: {str(e)}")
            return False, f'操作失败: {str(e)}'

    @staticmethod
    def lock_delivery_schedule(order_id):
        """
        锁定交期（供应商确认后调用）

        Args:
            order_id: 订单ID

        Returns:
            (success: bool, message: str)
        """
        order = PurchaseOrder.query.get(order_id)
        if not order:
            return False, '订单不存在'

        order.delivery_schedule_locked = True
        order.delivery_schedule_locked_at = datetime.now()

        try:
            db.session.commit()
            return True, '交期已锁定'
        except Exception as e:
            db.session.rollback()
            logger.error(f"锁定交期失败: {str(e)}")
            return False, f'操作失败: {str(e)}'

    @staticmethod
    def mark_test_signed(order_id, user_id=None, external_name=None):
        """
        标记测试报告已签证

        Args:
            order_id: 订单ID
            user_id: 内部用户ID
            external_name: 外部签署人姓名

        Returns:
            (success: bool, message: str)
        """
        order = PurchaseOrder.query.get(order_id)
        if not order:
            return False, '订单不存在'

        if not order.factory_test_report_url:
            return False, '请先上传测试报告'

        order.factory_test_signed_at = datetime.now()

        try:
            db.session.commit()
            return True, '测试报告签证成功'
        except Exception as e:
            db.session.rollback()
            logger.error(f"测试签证失败: {str(e)}")
            return False, f'操作失败: {str(e)}'

    @staticmethod
    def mark_fat_completed(order_id, completed_by):
        """
        标记FAT完成

        Args:
            order_id: 订单ID
            completed_by: 完成确认人姓名

        Returns:
            (success: bool, message: str)
        """
        order = PurchaseOrder.query.get(order_id)
        if not order:
            return False, '订单不存在'

        if order.verification_test_type != 'site_fat':
            return False, '该订单不需要FAT'

        order.fat_completed = True
        order.fat_completed_at = datetime.now()
        order.fat_completed_by = completed_by

        try:
            db.session.commit()
            return True, 'FAT标记完成'
        except Exception as e:
            db.session.rollback()
            logger.error(f"标记FAT完成失败: {str(e)}")
            return False, f'操作失败: {str(e)}'

    @staticmethod
    def get_stage_history(order_id):
        """
        获取阶段推进历史

        Args:
            order_id: 订单ID

        Returns:
            list of PurchaseOrderStageHistory
        """
        return PurchaseOrderStageHistory.query.filter_by(
            order_id=order_id
        ).order_by(
            PurchaseOrderStageHistory.created_at.desc()
        ).all()

    @staticmethod
    def get_delivery_changes(order_id):
        """
        获取交期变更历史

        Args:
            order_id: 订单ID

        Returns:
            list of PurchaseOrderDeliveryChange
        """
        return PurchaseOrderDeliveryChange.query.filter_by(
            order_id=order_id
        ).order_by(
            PurchaseOrderDeliveryChange.created_at.desc()
        ).all()

    @staticmethod
    def check_overdue_orders():
        """
        定时任务：检查所有进行中的订单是否超期

        Returns:
            int: 新发现的超期订单数量
        """
        orders = PurchaseOrder.query.filter(
            PurchaseOrder.status.in_(['confirmed', 'producing']),
            PurchaseOrder.is_overdue == False
        ).all()

        new_overdue_count = 0

        for order in orders:
            old_status = order.is_overdue
            PurchaseOrderProgressService.check_and_update_overdue_status(order)

            if order.is_overdue and not old_status:
                new_overdue_count += 1
                PurchaseOrderProgressService.send_overdue_notification(order)

        try:
            db.session.commit()
            logger.info(f"超期检查完成，新发现 {new_overdue_count} 个超期订单")
            return new_overdue_count
        except Exception as e:
            db.session.rollback()
            logger.error(f"超期检查失败: {str(e)}")
            return 0
