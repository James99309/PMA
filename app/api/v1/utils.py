from functools import wraps
from flask import json, request

# Flask 2.3+ JSON兼容层
try:
    from flask.json import jsonify, loads, dumps
except (ImportError, AttributeError):
    from flask import current_app
    
    def jsonify(*args, **kwargs):
        return current_app.json.response(*args, **kwargs)
    
    def dumps(*args, **kwargs):
        return current_app.json.dumps(*args, **kwargs)
    
    def loads(*args, **kwargs):
        return current_app.json.loads(*args, **kwargs)

try:
    from flask.json.provider import JSONProvider
except ImportError:
    # 兼容低版本的Flask
    JSONProvider = None

from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_login import current_user
from app.models.user import User

def api_response(success=True, code=200, message="操作成功", data=None):
    """
    统一的API响应格式
    
    参数:
        success (bool): 操作是否成功
        code (int): HTTP状态码
        message (str): 响应消息
        data (dict/list): 响应数据
    
    返回:
        JSON响应
    """
    response = {
        "success": success,
        "code": code,
        "message": message,
        "data": data if data is not None else {}
    }
    return jsonify(response), code

def jwt_required_with_permission(module, action):
    """
    JWT认证 + 权限检查装饰器
    
    参数:
        module (str): 模块名称
        action (str): 操作类型 (view/create/edit/delete)
    
    返回:
        装饰器函数
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                # 验证JWT
                verify_jwt_in_request()
                
                # 获取当前用户
                user_id = get_jwt_identity()
                # 不再转换ID类型，保持一致性
                    
                user = User.query.get(user_id)
                
                if not user:
                    return api_response(
                        success=False, 
                        code=401, 
                        message="认证失败，用户不存在"
                    )
                
                # 验证用户是否激活
                if not user.is_active:
                    return api_response(
                        success=False, 
                        code=403, 
                        message="账号未激活，请联系管理员"
                    )
                
                # 检查权限
                if not user.has_permission(module, action):
                    return api_response(
                        success=False, 
                        code=403, 
                        message=f"无权执行此操作: {module}/{action}"
                    )
                
                return fn(*args, **kwargs)
            except Exception as e:
                return api_response(
                    success=False,
                    code=401,
                    message=f"认证失败: {str(e)}"
                )
        return wrapper
    return decorator

def flexible_auth_with_permission(module, action):
    """
    灵活认证 + 权限检查装饰器
    支持JWT认证或会话认证，同时检查权限

    参数:
        module (str): 模块名称
        action (str): 操作类型 (view/create/edit/delete)

    返回:
        装饰器函数
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = None

            # 尝试JWT认证
            try:
                verify_jwt_in_request(optional=True)
                user_id = get_jwt_identity()
                if user_id:
                    user = User.query.get(user_id)
            except Exception:
                pass

            # 如果JWT认证失败，尝试会话认证
            if not user and current_user and current_user.is_authenticated:
                user = current_user

            # 如果都未认证
            if not user:
                return api_response(
                    success=False,
                    code=401,
                    message="认证失败: 请先登录"
                )

            # 验证用户是否激活
            if not user.is_active:
                return api_response(
                    success=False,
                    code=403,
                    message="账号未激活，请联系管理员"
                )

            # 检查权限
            if not user.has_permission(module, action):
                return api_response(
                    success=False,
                    code=403,
                    message=f"无权执行此操作: {module}/{action}"
                )

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_request_lang():
    """从请求 Accept-Language header 解析 mobile 端语言偏好.

    mobile axios 拦截器在每个请求带 Accept-Language: zh-CN 或 en.
    返回 'zh' 或 'en' (字典 helper 用此参数取对应语言 label)。
    Fallback 到 'zh' (兼容老客户端不带 header 的情况)。
    """
    al = (request.headers.get('Accept-Language') or '').lower()
    if al.startswith('en'):
        return 'en'
    return 'zh'


def get_pagination_params():
    """
    获取分页参数

    返回:
        tuple: (page, limit)
    """
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)

    # 确保参数在合理范围内
    page = max(1, page)
    limit = max(1, min(100, limit))  # 限制最大查询数量为100

    return page, limit


# ─── 图片上传 + OCR 通用 helper ───────────────────────────────────────
# 名片 / 发票 等场景共用. 复用 NAS chat 桶 + 调指定 OCR 函数.

def handle_image_ocr_upload(file_storage, owner_id, business_type, ocr_fn,
                            default_filename='upload.jpg'):
    """multipart 图片 → NAS 存档(chat 桶) + 调 OCR → 返回 {file_url, fields, ocr_json}.

    Args:
        file_storage: werkzeug FileStorage (request.files.get('file'))
        owner_id: int, 上传用户 ID
        business_type: str, NAS 存档分类标签 (e.g. 'business_card', 'expense_invoice')
        ocr_fn: callable(blob: bytes) -> {'success': bool, 'data'?: dict, 'message'?: str}
        default_filename: 上传文件名兜底

    Returns:
        (success: bool, payload: dict, code: int, message: str)
        success=True  → payload={file_url, fields, ocr_json}
        success=False → message + code 用于 api_response
    """
    import logging as _logging
    import json as _json

    logger = _logging.getLogger(__name__)

    if not file_storage:
        return False, {'file_url': None}, 400, '未提供图片'

    blob = file_storage.read()
    try:
        file_storage.stream.seek(0)
    except Exception:
        pass
    if not blob:
        return False, {'file_url': None}, 400, '图片为空'

    # 1) 存到 NAS 的 chat 桶 (复用现有 attachment 通道)
    # 按 blob magic bytes 判 file_type, 否则 SupabaseStorageClient 按 image 白名单拒收 PDF
    from app.services.claude_vision_ocr import detect_image_type
    detected_mime = detect_image_type(blob)
    detected_file_type = 'pdf' if detected_mime == 'application/pdf' else 'image'

    # 合成一个一定带正确扩展名的文件名传给 storage:
    # 用户传的中文文件名经过 werkzeug.secure_filename 会被剥到只剩 'pdf'(没点),
    # 让 SupabaseStorageClient 的 file_ext 嗅探拿不到扩展名导致白名单失败
    _ext_map = {
        'application/pdf': 'pdf',
        'image/jpeg': 'jpg', 'image/png': 'png',
        'image/webp': 'webp', 'image/gif': 'gif',
    }
    safe_ext = _ext_map.get(detected_mime, 'jpg')
    safe_filename = f'invoice-{owner_id}.{safe_ext}'

    file_url = None
    try:
        from app.utils.smart_storage_manager import get_smart_storage
        from urllib.parse import quote
        storage = get_smart_storage()
        result = storage.upload_file(
            object_id=owner_id,
            file=file_storage.stream,
            filename=safe_filename,
            file_type=detected_file_type,
            bucket_type='chat',
            business_type=business_type,
        )
        if result and result.get('url'):
            nas_path = result.get('nas_path') or result.get('storage_path') or ''
            rel_path = nas_path.split('/', 1)[1] if '/' in nas_path else nas_path
            file_url = f'/api/v1/mobile/chat/file?path={quote(rel_path)}'
    except Exception as e:
        logger.warning(f'image upload to NAS failed ({business_type}): {e}')

    # 2) 调 OCR
    ocr_result = ocr_fn(blob)
    if not ocr_result.get('success'):
        return False, {'file_url': file_url}, 500, ocr_result.get('message', '识别失败')

    fields = ocr_result['data']
    return True, {
        'file_url': file_url,
        'fields': fields,
        'ocr_json': _json.dumps(fields, ensure_ascii=False),
    }, 200, '识别成功'
