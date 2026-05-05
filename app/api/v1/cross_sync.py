# -*- coding: utf-8 -*-
"""
跨系统同步 API

接收来自对等 PMA 实例的推送消息和数据同步请求。
使用 X-API-Key 认证。
"""
import logging
from flask import request, jsonify

from app import db
from app.api.v1 import api_v1_bp
from app.api.v1.configurations import require_api_key_or_jwt

logger = logging.getLogger(__name__)


@api_v1_bp.route('/cross-sync/push', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_push():
    """接收跨系统推送消息"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400

    if data.get('reply_mode'):
        for field in ['sender_email', 'recipient_email', 'content']:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        from app.services.cross_sync_service import receive_private_reply_from_peer
        result = receive_private_reply_from_peer(data)
    else:
        required_fields = ['recipient_email', 'content']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        from app.services.cross_sync_service import receive_message_from_peer
        result = receive_message_from_peer(data)

    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code


@api_v1_bp.route('/cross-sync/push-group', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_push_group():
    """接收跨系统群聊消息或群聊回复"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400

    if data.get('reply_mode'):
        for field in ['sg_group_id', 'sender_email', 'content']:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        from app.services.cross_sync_service import receive_group_reply_from_peer
        result = receive_group_reply_from_peer(data)
    else:
        for field in ['sg_group_id', 'content', 'recipient_emails']:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        from app.services.cross_sync_service import receive_group_message_from_peer
        result = receive_group_message_from_peer(data)

    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code


@api_v1_bp.route('/cross-sync/refresh-cache', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_refresh_cache():
    """刷新本地物化视图缓存（CN 分类变更时调用）"""
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT refresh_cn_cache()'))
        db.session.commit()
        logger.info('物化视图缓存刷新成功（由对等系统触发）')
        return jsonify({'success': True, 'message': '缓存刷新成功'})
    except Exception as e:
        logger.warning(f'物化视图缓存刷新失败: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500


@api_v1_bp.route('/cross-sync/sync-product-specs', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_product_specs():
    """接收跨系统产品规格同步请求

    由 CN NAS 在关联 SG 产品到配置后调用，
    更新 SG 产品的规格值、编码、排序并重建快照。

    Request body:
    {
        "product_id": 25,
        "specs": [
            {"field_name": "工作频率", "field_name_en": "Operating Frequency",
             "field_value": "400-470", "field_code": "4", "unit": "MHz", "display_order": 1},
            ...
        ],
        "config_mn": "SGAN2OFD2TE2"  # 可选：配置的 MN 编码
    }
    """
    data = request.get_json()
    if not data or not data.get('product_id'):
        return jsonify({'success': False, 'message': '缺少 product_id'}), 400

    product_id = data['product_id']
    specs_data = data.get('specs', [])

    try:
        from app.models.product import Product
        from app.models.product_spec import ProductSpec
        from app.utils.product_helpers import generate_product_snapshot

        product = Product.query.get(product_id)
        if not product or product.is_deleted:
            return jsonify({'success': False, 'message': f'产品 {product_id} 不存在'}), 404

        # 删除现有规格
        ProductSpec.query.filter_by(product_id=product_id).delete()

        # 写入新规格
        for spec in specs_data:
            ps = ProductSpec(
                product_id=product_id,
                field_name=spec.get('field_name', ''),
                field_name_en=spec.get('field_name_en', ''),
                field_value=spec.get('field_value', ''),
                field_value_en=spec.get('field_value_en', ''),
                field_code=spec.get('field_code', ''),
                use_in_code=spec.get('use_in_code', False),
                unit=spec.get('unit', ''),
                display_order=spec.get('display_order', 0),
                include_in_description=spec.get('include_in_description', True)
            )
            db.session.add(ps)

        db.session.commit()

        # 重建快照 + 更新描述
        from app.services.spec_service import SpecService
        snap = generate_product_snapshot(product, source='cross_sync')
        if snap:
            product.code_definition_snapshot = snap
        product.specification = SpecService.generate_description(SpecService.TYPE_PRODUCT, product_id)
        db.session.commit()

        logger.info(f'跨系统规格同步成功: 产品 {product_id}, {len(specs_data)} 条规格')
        return jsonify({
            'success': True,
            'message': f'已同步 {len(specs_data)} 条规格并重建快照',
            'product_id': product_id
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f'跨系统规格同步失败: 产品 {product_id}, {e}')
        return jsonify({'success': False, 'message': str(e)}), 500


@api_v1_bp.route('/cross-sync/lock-config', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_lock_config():
    """SG 导入产品后通知 CN 锁定对应配置

    Request body:
    {
        "config_id": 31,           # CN 配置 ID
        "product_mn": "SOMWCER8T3J" # SG 产品的 MN 编码
    }
    """
    data = request.get_json()
    config_id = data.get('config_id')
    product_mn = data.get('product_mn')

    if not config_id or not product_mn:
        return jsonify({'success': False, 'message': '缺少 config_id 或 product_mn'}), 400

    try:
        from app.models.spec_template import ProductConfiguration
        from app.views.spec_template import generate_mn_code, generate_code_rule_snapshot

        config = ProductConfiguration.query.get(config_id)
        if not config or config.deleted_at:
            return jsonify({'success': False, 'message': f'配置 {config_id} 不存在'}), 404

        old_mn = config.mn_code
        config.mn_code = product_mn
        config.status = 'production'

        # 重建 code_rule_snapshot（使用当前 MN，不重新生成）
        from app.views.spec_template import get_code_from_dictionary, generate_safe_code_char
        code_items = sorted(
            [item for item in config.template.items if item.use_in_code],
            key=lambda x: x.display_order
        )
        code_items_data = []
        for item in code_items:
            value = None
            for cv in config.config_values:
                if cv.template_item_id == item.id:
                    value = cv.value
                    break
            if not value:
                value = item.general_value
            code_char = get_code_from_dictionary(item.spec_dict_id, value) if item.spec_dict_id else None
            if not code_char:
                code_char = generate_safe_code_char(value, item.options or {})
            code_items_data.append({
                "item_id": item.id,
                "definition_name": item.spec_dict.name if item.spec_dict else None,
                "display_order": item.display_order,
                "code_length": item.code_length,
                "options": item.options or {},
                "value": value,
                "code_char": (code_char or 'X')[:1]
            })
        config.code_rule_snapshot = generate_code_rule_snapshot(config, product_mn, code_items_data)

        db.session.commit()
        logger.info(f'跨系统锁定配置: config_id={config_id}, old_mn={old_mn}, new_mn={product_mn}')
        return jsonify({
            'success': True,
            'message': f'配置 {config_id} 已锁定，MN 更新为 {product_mn}'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f'跨系统锁定配置失败: config_id={config_id}, {e}')
        return jsonify({'success': False, 'message': str(e)}), 500


@api_v1_bp.route('/cross-sync/unlock-config', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_unlock_config():
    """SG 删除产品后通知 CN 解锁对应配置

    仅在该配置没有其他关联产品时解锁。

    Request body:
    {
        "product_mn": "SOMWCER8T3J"  # 被删除的 SG 产品 MN
    }
    """
    data = request.get_json()
    product_mn = data.get('product_mn')

    if not product_mn:
        return jsonify({'success': False, 'message': '缺少 product_mn'}), 400

    try:
        from app.models.spec_template import ProductConfiguration
        from app.models.product import Product

        # 找到 MN 匹配的配置
        config = ProductConfiguration.query.filter_by(mn_code=product_mn).first()
        if not config:
            return jsonify({'success': True, 'message': f'未找到 MN={product_mn} 的配置，无需操作'})

        # 检查是否还有 CN 关联产品
        cn_count = Product.query.filter_by(
            source_configuration_id=config.id,
            is_deleted=False
        ).count()

        # 检查是否还有 SG 关联产品（排除刚删除的那个）
        sg_count = db.session.execute(db.text(
            "SELECT COUNT(*) FROM sg_products WHERE product_mn = :mn"
        ), {'mn': product_mn}).scalar() or 0

        if cn_count > 0 or sg_count > 0:
            logger.info(f'配置 {config.id} 仍有关联产品 (CN={cn_count}, SG={sg_count})，保持锁定')
            return jsonify({
                'success': True,
                'message': f'配置仍有 {cn_count + sg_count} 个关联产品，保持锁定'
            })

        # 无关联产品，解锁并重新生成 MN
        old_status = config.status
        config.status = 'development'

        from app.views.spec_template import generate_mn_code
        new_mn = generate_mn_code(config)
        if new_mn:
            config.mn_code = new_mn

        db.session.commit()
        logger.info(f'跨系统解锁配置: config_id={config.id}, {old_status} → development, MN={new_mn}')
        return jsonify({
            'success': True,
            'message': f'配置 {config.id} 已解锁，新 MN={new_mn}'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f'跨系统解锁配置失败: product_mn={product_mn}, {e}')
        return jsonify({'success': False, 'message': str(e)}), 500


@api_v1_bp.route('/cross-sync/sync-display-order', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_display_order():
    """接收产品排序数据同步（CN → SG）

    Request body:
    {
        "category_code": "O",
        "subcategory_code": "F",
        "items": [
            {"category_code": "O", "category_order": 3, "subcategory_code": "F",
             "subcategory_order": 1, "model": "PNR2100", "model_order": 1},
            ...
        ]
    }
    """
    data = request.get_json()
    category_code = data.get('category_code')
    subcategory_code = data.get('subcategory_code')
    items = data.get('items', [])

    if not category_code or not subcategory_code:
        return jsonify({'success': False, 'message': '缺少 category_code 或 subcategory_code'}), 400

    try:
        from app.models.product_display_order import ProductDisplayOrder

        # 删除该子分类的现有排序数据
        ProductDisplayOrder.query.filter_by(
            category_code=category_code,
            subcategory_code=subcategory_code
        ).delete()

        # 批量插入新数据
        for item in items:
            row = ProductDisplayOrder(
                category_code=item['category_code'],
                category_order=item['category_order'],
                subcategory_code=item['subcategory_code'],
                subcategory_order=item['subcategory_order'],
                model=item['model'],
                model_order=item['model_order'],
            )
            db.session.add(row)

        db.session.commit()
        logger.info(f'产品排序同步接收成功: {category_code}{subcategory_code}, {len(items)} 条')
        return jsonify({'success': True, 'message': f'已同步 {len(items)} 条排序数据'})

    except Exception as e:
        db.session.rollback()
        logger.error(f'产品排序同步接收失败: {category_code}{subcategory_code}, {e}')
        return jsonify({'success': False, 'message': str(e)}), 500


# ═══ 用户镜像（Federation Lite Phase 1）═══════════════════════════════════
# CN admin 把用户标为「海外支持」→ 后端调本族 SG NAS 的下面 3 个端点：
#   POST /cross-sync/mirror-user      创建/更新镜像用户
#   POST /cross-sync/sync-password    密码同步
#   POST /cross-sync/disable-mirror   取消镜像 (设 is_active=false, 历史保留)


@api_v1_bp.route('/cross-sync/mirror-user', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_mirror_user():
    """接收对等系统推送的用户镜像
    payload:
      {source_system: 'sp8d', source_user_id: 123,
       username, real_name, email, password_hash, is_active,
       cross_team_label}
    upsert by (source_system, source_user_id)
    """
    import time
    from app.models.user import User

    data = request.get_json() or {}
    required = ['source_system', 'source_user_id', 'username', 'password_hash']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'success': False, 'message': f'缺少字段: {missing}'}), 400

    src_sys = data['source_system']
    src_id = int(data['source_user_id'])

    # upsert
    user = User.query.filter_by(
        source_system=src_sys, source_user_id=src_id, is_mirror=True
    ).first()

    is_new = False
    if not user:
        # 检查 username/email 在本地是否已存在（伪镜像 / 同名冲突）
        # email 为 None 时不能参与 OR (会匹配到所有 NULL email 行误判)
        from sqlalchemy import or_
        clauses = [User.username == data['username']]
        if data.get('email'):
            clauses.append(User.email == data['email'])
        existing = User.query.filter(or_(*clauses)).first()
        if existing:
            return jsonify({
                'success': False,
                'code': 'CONFLICT',
                'message': f'本地已存在 username={existing.username} / email={existing.email}, '
                           f'需先用 /cross-sync/promote-to-mirror 把伪镜像转换',
                'existing_id': existing.id,
            }), 409
        user = User()
        user.is_mirror = True
        user.source_system = src_sys
        user.source_user_id = src_id
        user._is_active = bool(data.get('is_active', True))
        user.is_profile_complete = True   # mirror 用户跳过本地 onboarding 流程
        is_new = True
        db.session.add(user)

    # 同步身份字段（角色 / 权限不同步, SG admin 自己设）
    user.username = data['username']
    user.real_name = data.get('real_name') or user.username
    user.email = data.get('email')
    user.password_hash = data['password_hash']
    user.cross_team_label = data.get('cross_team_label')
    user.mirrored_at = time.time()
    if 'is_active' in data:
        user._is_active = bool(data['is_active'])

    try:
        db.session.commit()
        logger.info(f'cross_sync mirror_user {"created" if is_new else "updated"}: '
                    f'src={src_sys}#{src_id} → local#{user.id}')
        return jsonify({
            'success': True,
            'data': {'id': user.id, 'is_new': is_new},
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f'cross_sync mirror_user 失败: {e}', exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@api_v1_bp.route('/cross-sync/sync-password', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_sync_password():
    """对等系统推送密码变更"""
    import time
    from app.models.user import User
    data = request.get_json() or {}
    src_sys = data.get('source_system')
    src_id = data.get('source_user_id')
    pw_hash = data.get('password_hash')
    if not (src_sys and src_id and pw_hash):
        return jsonify({'success': False, 'message': '缺少字段'}), 400
    user = User.query.filter_by(
        source_system=src_sys, source_user_id=int(src_id), is_mirror=True
    ).first()
    if not user:
        return jsonify({'success': False, 'message': '镜像用户不存在'}), 404
    user.password_hash = pw_hash
    user.mirrored_at = time.time()
    try:
        db.session.commit()
        logger.info(f'cross_sync sync_password: src={src_sys}#{src_id} → local#{user.id}')
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@api_v1_bp.route('/cross-sync/disable-mirror', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_disable_mirror():
    """对等系统通知取消镜像 (用户 is_active=false, 不删除以保留历史)"""
    import time
    from app.models.user import User
    data = request.get_json() or {}
    src_sys = data.get('source_system')
    src_id = data.get('source_user_id')
    if not (src_sys and src_id):
        return jsonify({'success': False, 'message': '缺少字段'}), 400
    user = User.query.filter_by(
        source_system=src_sys, source_user_id=int(src_id), is_mirror=True
    ).first()
    if not user:
        return jsonify({'success': True, 'message': '镜像不存在 (已是 disabled)'})
    user._is_active = False
    user.mirrored_at = time.time()
    try:
        db.session.commit()
        logger.info(f'cross_sync disable_mirror: src={src_sys}#{src_id} → local#{user.id}')
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@api_v1_bp.route('/cross-sync/promote-to-mirror', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_promote_to_mirror():
    """把已有的本地"伪镜像"账号转为正式 mirror。
    用于迁移：CN 端有 jing@evertac.cn, SG 端 admin 早就手工建过 jing@evertac.cn,
    现在把 SG 那行加上 source_system + source_user_id + is_mirror=true,
    并用 CN 推过来的 password_hash 覆盖。
    payload:
      {source_system, source_user_id, local_user_id,
       username, password_hash, real_name, email, cross_team_label}
    校验：local_user_id 这行的 username AND email 必须与 payload 一致 (双重确认避免误转)
    """
    import time
    from app.models.user import User
    data = request.get_json() or {}
    src_sys = data.get('source_system')
    src_id = data.get('source_user_id')
    local_id = data.get('local_user_id')
    if not (src_sys and src_id and local_id):
        return jsonify({'success': False, 'message': '缺少字段'}), 400
    user = User.query.get(int(local_id))
    if not user:
        return jsonify({'success': False, 'message': '本地用户不存在'}), 404
    if user.is_mirror:
        return jsonify({'success': False, 'message': '已是镜像，请用 mirror_user 端点'}), 400
    # 双重确认：username + email 必须都匹配
    if user.username != data.get('username') or (user.email or '') != (data.get('email') or ''):
        return jsonify({
            'success': False,
            'message': f'用户名/邮箱不匹配，本地({user.username}/{user.email}) vs 推送({data.get("username")}/{data.get("email")})',
        }), 400
    user.is_mirror = True
    user.source_system = src_sys
    user.source_user_id = int(src_id)
    user.password_hash = data['password_hash']
    user.cross_team_label = data.get('cross_team_label')
    if data.get('real_name'):
        user.real_name = data['real_name']
    user.mirrored_at = time.time()
    try:
        db.session.commit()
        logger.info(f'cross_sync promote_to_mirror: local#{user.id} → mirror of {src_sys}#{src_id}')
        return jsonify({'success': True, 'data': {'id': user.id}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
