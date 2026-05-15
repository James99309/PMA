"""系统图视图 — 工程系统图绘制与管理"""
import copy
import os
import secrets
import uuid
from flask import Blueprint, render_template, request, jsonify, url_for, redirect, current_app, send_from_directory, session as flask_session
from flask_login import login_required, current_user
from flask_babel import gettext as _
from app.decorators import permission_required
from app.models.product import Product
from app.models.product_code import ProductCategory, ProductSubcategory
from app.models.system_diagram import SystemDiagram, DiagramShareToken, DiagramExternalSession
from app.models.user import User
from app.models.project import Project
from app.extensions import db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

system_diagram = Blueprint('system_diagram', __name__, url_prefix='/system-diagram')


def _can_edit_diagram(diagram):
    """检查当前用户是否有权编辑系统图（基于数据归属和项目权限）"""
    from app.utils.access_control import can_edit_data, can_view_project
    # admin 和 owner 在 can_edit_data 内部处理
    # SystemDiagram 不在 can_edit_data 的已知模型中，手动实现等效逻辑
    if current_user.role == 'admin':
        return True
    if diagram.owner_id == current_user.id:
        return True
    # 如果系统图关联了项目，继承项目的查看权限（能看项目即可编辑其系统图）
    if diagram.project_id:
        project = Project.query.get(diagram.project_id)
        if project and can_view_project(current_user, project):
            return True
    return False


# ── 页面路由 ──────────────────────────────────────────────

@system_diagram.route('/')
@login_required
@permission_required('system_diagram', 'view')
def list_view():
    """系统图列表页"""
    diagrams = SystemDiagram.query.filter(
        SystemDiagram.is_deleted == False,
        SystemDiagram.owner_id == current_user.id,
        SystemDiagram.project_id == None,
        SystemDiagram.is_template == False
    ).order_by(SystemDiagram.updated_at.desc()).all()
    my_templates = SystemDiagram.query.filter(
        SystemDiagram.is_deleted == False,
        SystemDiagram.owner_id == current_user.id,
        SystemDiagram.is_template == True
    ).order_by(SystemDiagram.updated_at.desc()).all()
    return render_template('system_diagram/tw_list.html',
                           diagrams=diagrams,
                           my_templates=my_templates,
                           active_page='system_diagram')


@system_diagram.route('/new')
@login_required
@permission_required('system_diagram', 'create')
def new_editor():
    """新建系统图编辑器"""
    project_id = request.args.get('project_id', 0, type=int)
    project_name = ''
    if project_id:
        project = Project.query.get(project_id)
        if project:
            project_name = project.project_name
    return render_template('system_diagram/tw_editor.html',
                           diagram_id=0,
                           diagram_name=_('未命名系统图'),
                           project_id=project_id,
                           project_name=project_name,
                           active_page='system_diagram')


@system_diagram.route('/<int:diagram_id>')
@login_required
@permission_required('system_diagram', 'view')
def edit_editor(diagram_id):
    """编辑已有系统图"""
    diagram = SystemDiagram.query.get_or_404(diagram_id)
    if diagram.is_deleted:
        return render_template('errors/404.html'), 404
    project_name = ''
    if diagram.project_id:
        project = Project.query.get(diagram.project_id)
        if project:
            project_name = project.project_name
    preview_mode = request.args.get('preview') == '1'
    return render_template('system_diagram/tw_editor.html',
                           diagram_id=diagram.id,
                           diagram_name=diagram.name,
                           project_id=diagram.project_id or 0,
                           project_name=project_name,
                           read_only=preview_mode,
                           preview_mode=preview_mode,
                           active_page='system_diagram')


@system_diagram.route('/templates')
@login_required
@permission_required('system_diagram', 'view')
def template_gallery():
    """模板选择页 — 从项目详情页创建系统图时先选模板"""
    project_id = request.args.get('project_id', 0, type=int)
    if not project_id:
        return redirect(url_for('system_diagram.new_editor'))
    project = Project.query.get_or_404(project_id)
    templates = SystemDiagram.query.filter(
        SystemDiagram.is_deleted == False,
        SystemDiagram.is_template == True
    ).order_by(SystemDiagram.updated_at.desc()).all()
    return render_template('system_diagram/tw_template_gallery.html',
                           templates=templates, project=project,
                           project_id=project_id, active_page='system_diagram')


# ── API 路由 ──────────────────────────────────────────────

@system_diagram.route('/api/create-from-template', methods=['POST'])
@login_required
@permission_required('system_diagram', 'create')
def api_create_from_template():
    """从模板创建新系统图（克隆模板数据）"""
    data = request.get_json()
    template_id = data.get('templateId')
    project_id = data.get('projectId')
    if not project_id:
        return jsonify({'success': False, 'message': _('缺少项目ID')}), 400

    if template_id:
        template = SystemDiagram.query.get(template_id)
        if not template or template.is_deleted or not template.is_template:
            return jsonify({'success': False, 'message': _('模版不存在')}), 404
        diagram = SystemDiagram(
            name=template.name,
            description=template.description,
            project_id=project_id,
            diagram_data=copy.deepcopy(template.diagram_data) if template.diagram_data else None,
            owner_id=current_user.id
        )
    else:
        diagram = SystemDiagram(
            name=_('未命名系统图'),
            project_id=project_id,
            owner_id=current_user.id
        )
    db.session.add(diagram)
    db.session.commit()
    return jsonify({
        'success': True,
        'id': diagram.id,
        'redirectUrl': url_for('system_diagram.edit_editor', diagram_id=diagram.id)
    })


@system_diagram.route('/api/<int:diagram_id>/toggle-template', methods=['POST'])
@login_required
@permission_required('system_diagram', 'edit')
def api_toggle_template(diagram_id):
    """切换系统图的模板标记"""
    diagram = SystemDiagram.query.get_or_404(diagram_id)
    if not _can_edit_diagram(diagram):
        return jsonify({'success': False, 'message': _('无权限')}), 403
    diagram.is_template = not diagram.is_template
    diagram.updated_at = datetime.now()
    db.session.commit()
    return jsonify({'success': True, 'is_template': diagram.is_template})


@system_diagram.route('/api/products')
@login_required
@permission_required('system_diagram', 'view')
def api_products():
    """获取产品列表，按分类→子分类→产品层级分组"""
    return jsonify({'success': True, 'categories': _get_products_data()})


@system_diagram.route('/api/save', methods=['POST'])
@login_required
@permission_required('system_diagram', 'edit')
def api_save():
    """保存或更新系统图"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': _('无效的请求数据')}), 400

    diagram_id = data.get('id', 0)
    name = data.get('name', '').strip() or _('未命名系统图')
    description = data.get('description', '')
    project_id = data.get('projectId') or None
    diagram_data = data.get('diagramData', {})
    thumbnail_svg = data.get('thumbnailSvg', '')

    if diagram_id:
        diagram = SystemDiagram.query.get(diagram_id)
        if not diagram or diagram.is_deleted:
            return jsonify({'success': False, 'message': _('系统图不存在')}), 404
        if not _can_edit_diagram(diagram):
            return jsonify({'success': False, 'message': _('无权限')}), 403
        diagram.name = name
        diagram.description = description
        diagram.project_id = project_id
        diagram.diagram_data = diagram_data
        diagram.thumbnail_svg = thumbnail_svg
        diagram.updated_at = datetime.now()
    else:
        diagram = SystemDiagram(
            name=name,
            description=description,
            project_id=project_id,
            diagram_data=diagram_data,
            thumbnail_svg=thumbnail_svg,
            owner_id=current_user.id
        )
        db.session.add(diagram)

    db.session.commit()
    return jsonify({
        'success': True,
        'id': diagram.id,
        'message': _('系统图已保存')
    })


@system_diagram.route('/api/<int:diagram_id>/data')
@login_required
@permission_required('system_diagram', 'view')
def api_load(diagram_id):
    """加载系统图数据"""
    diagram = SystemDiagram.query.get_or_404(diagram_id)
    if diagram.is_deleted:
        return jsonify({'success': False, 'message': _('系统图不存在')}), 404
    return jsonify({
        'success': True,
        'diagram': {
            'id': diagram.id,
            'name': diagram.name,
            'description': diagram.description or '',
            'projectId': diagram.project_id,
            'diagramData': diagram.diagram_data or {},
            'thumbnailSvg': diagram.thumbnail_svg or '',
            'createdAt': diagram.created_at.isoformat() if diagram.created_at else '',
            'updatedAt': diagram.updated_at.isoformat() if diagram.updated_at else '',
        }
    })


@system_diagram.route('/api/<int:diagram_id>', methods=['DELETE'])
@login_required
@permission_required('system_diagram', 'delete')
def api_delete(diagram_id):
    """软删除系统图"""
    diagram = SystemDiagram.query.get_or_404(diagram_id)
    diagram.is_deleted = True
    diagram.updated_at = datetime.now()
    db.session.commit()
    return jsonify({'success': True, 'message': _('系统图已删除')})


# ── 平面图背景 API ────────────────────────────────────────

ALLOWED_BG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'dxf', 'dwg'}
MAX_BG_SIZE = 12 * 1024 * 1024  # 12MB


def _get_bg_upload_dir():
    """获取平面图背景存储目录"""
    upload_dir = os.path.join(current_app.root_path, '..', 'storage', 'system_diagrams')
    upload_dir = os.path.abspath(upload_dir)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


@system_diagram.route('/api/<int:diagram_id>/floor-plan/upload-bg', methods=['POST'])
@login_required
@permission_required('system_diagram', 'edit')
def upload_floor_bg(diagram_id):
    """上传楼层平面图背景图片 (PNG/JPG)"""
    # 验证所有权
    diagram = SystemDiagram.query.get_or_404(diagram_id)
    if diagram.is_deleted or not _can_edit_diagram(diagram):
        return jsonify({'success': False, 'message': _('无权限')}), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': _('请选择文件')}), 400

    file = request.files['file']
    floor_id = request.form.get('floor_id', '')
    if not file.filename or not floor_id:
        return jsonify({'success': False, 'message': _('缺少参数')}), 400

    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_BG_EXTENSIONS:
        return jsonify({'success': False, 'message': _('仅支持 PNG/JPG/PDF 格式')}), 400

    # 检查文件大小
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > MAX_BG_SIZE:
        return jsonify({'success': False, 'message': _('文件大小不能超过 12MB')}), 400

    # 生成唯一文件名
    unique_name = f"{diagram_id}_{floor_id}_{uuid.uuid4().hex[:8]}.{ext}"
    upload_dir = _get_bg_upload_dir()
    save_path = os.path.join(upload_dir, unique_name)

    try:
        file.save(save_path)

        # 获取图片尺寸
        width, height = 0, 0
        try:
            from PIL import Image
            with Image.open(save_path) as img:
                width, height = img.size
        except ImportError:
            logger.warning("Pillow 未安装，无法获取图片尺寸")
        except Exception as e:
            logger.warning(f"获取图片尺寸失败: {e}")

        # 返回可访问的URL
        bg_url = url_for('system_diagram.serve_floor_bg', filename=unique_name)

        return jsonify({
            'success': True,
            'url': bg_url,
            'width': width,
            'height': height,
            'filename': unique_name
        })

    except Exception as e:
        logger.error(f"上传平面图背景失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@system_diagram.route('/api/<int:diagram_id>/floor-plan/delete-bg', methods=['POST'])
@login_required
@permission_required('system_diagram', 'edit')
def delete_floor_bg(diagram_id):
    """删除楼层背景图"""
    # 验证所有权
    diagram = SystemDiagram.query.get_or_404(diagram_id)
    if diagram.is_deleted or not _can_edit_diagram(diagram):
        return jsonify({'success': False, 'message': _('无权限')}), 403

    data = request.get_json() or {}

    # 支持多文件删除（多分辨率）和单文件删除（向后兼容）
    filenames = data.get('filenames', [])
    if not filenames:
        filename = data.get('filename', '')
        if filename:
            filenames = [filename]

    upload_dir = _get_bg_upload_dir()
    for fn in filenames:
        file_path = os.path.join(upload_dir, os.path.basename(fn))
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"删除背景文件失败: {e}")

    # 同时删除关联的 DXF 文件（如果有）
    dxf_filename = data.get('dxf_filename', '')
    if dxf_filename:
        dxf_path = os.path.join(upload_dir, os.path.basename(dxf_filename))
        if os.path.exists(dxf_path):
            try:
                os.remove(dxf_path)
            except Exception as e:
                logger.warning(f"删除 DXF 文件失败: {e}")

    return jsonify({'success': True})


@system_diagram.route('/api/<int:diagram_id>/floor-plan/analyze-pdf', methods=['POST'])
@login_required
@permission_required('system_diagram', 'edit')
def analyze_pdf_api(diagram_id):
    """分析 PDF 页面信息（缩略图 + 书签名称）"""
    diagram = SystemDiagram.query.get_or_404(diagram_id)
    if diagram.is_deleted or not _can_edit_diagram(diagram):
        return jsonify({'success': False, 'message': _('无权限')}), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': _('请选择文件')}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'message': _('缺少参数')}), 400

    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext != 'pdf':
        return jsonify({'success': False, 'message': _('仅支持 PDF 格式')}), 400

    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > MAX_BG_SIZE:
        return jsonify({'success': False, 'message': _('文件大小不能超过 12MB')}), 400

    try:
        from app.utils.pdf_converter import analyze_pdf
        import time as _time

        upload_dir = _get_bg_upload_dir()

        # 清理超过 1 小时的临时 PDF（防止孤立文件堆积）
        try:
            now = _time.time()
            for fn in os.listdir(upload_dir):
                if fn.startswith('_temp_pdf_') and fn.endswith('.pdf'):
                    fp = os.path.join(upload_dir, fn)
                    if now - os.path.getmtime(fp) > 3600:
                        os.remove(fp)
        except Exception:
            pass

        # 临时保存 PDF，使用 session_id 标识
        session_id = uuid.uuid4().hex[:12]
        temp_path = os.path.join(upload_dir, f"_temp_pdf_{session_id}.pdf")
        file.save(temp_path)

        pages = analyze_pdf(temp_path)

        return jsonify({
            'success': True,
            'page_count': len(pages),
            'pages': pages,
            'session_id': session_id
        })
    except ImportError:
        return jsonify({'success': False, 'message': 'PyMuPDF 未安装'}), 500
    except Exception as e:
        logger.error(f"分析 PDF 失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@system_diagram.route('/api/<int:diagram_id>/floor-plan/render-pdf-pages', methods=['POST'])
@login_required
@permission_required('system_diagram', 'edit')
def render_pdf_pages(diagram_id):
    """批量渲染选中的 PDF 页面为多分辨率 PNG"""
    diagram = SystemDiagram.query.get_or_404(diagram_id)
    if diagram.is_deleted or not _can_edit_diagram(diagram):
        return jsonify({'success': False, 'message': _('无权限')}), 403

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': _('无效的请求数据')}), 400

    session_id = data.get('session_id', '')
    pages = data.get('pages', [])
    if not session_id or not pages:
        return jsonify({'success': False, 'message': _('缺少参数')}), 400

    upload_dir = _get_bg_upload_dir()
    temp_path = os.path.join(upload_dir, f"_temp_pdf_{session_id}.pdf")
    if not os.path.exists(temp_path):
        return jsonify({'success': False, 'message': _('PDF 文件已过期，请重新上传')}), 404

    try:
        from app.utils.pdf_converter import convert_pdf_page_to_images

        results = []
        for page_info in pages:
            page_index = page_info.get('index', 0)
            label = page_info.get('label', f'Page-{page_index + 1}')

            # 生成安全的文件名前缀
            safe_label = ''.join(c for c in label if c.isalnum() or c in '-_ ')[:20].strip()
            base_name = f"{diagram_id}_{safe_label}_{uuid.uuid4().hex[:6]}"

            resolutions = convert_pdf_page_to_images(
                temp_path, page_index, upload_dir, base_name,
                max_dims=[1000, 2000, 4000, 8000]
            )

            # 构建 URL 映射
            res_with_urls = {}
            all_filenames = []
            for dim_key, info in resolutions.items():
                res_with_urls[dim_key] = {
                    'url': url_for('system_diagram.serve_floor_bg', filename=info['filename']),
                    'width': info['width'],
                    'height': info['height']
                }
                all_filenames.append(info['filename'])

            # 默认使用 2000px 分辨率
            default_res = res_with_urls.get('2000', list(res_with_urls.values())[0])

            results.append({
                'page_index': page_index,
                'label': label,
                'is_multi_res': True,
                'resolutions': res_with_urls,
                'width': default_res['width'],
                'height': default_res['height'],
                'filenames': all_filenames
            })

        # 删除临时 PDF
        try:
            os.remove(temp_path)
        except Exception:
            pass

        return jsonify({'success': True, 'results': results})

    except ImportError:
        return jsonify({'success': False, 'message': 'PyMuPDF 未安装'}), 500
    except Exception as e:
        logger.error(f"渲染 PDF 页面失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@system_diagram.route('/api/<int:diagram_id>/floor-plan/extract-dxf-layers', methods=['POST'])
@login_required
@permission_required('system_diagram', 'edit')
def extract_dxf_layers_api(diagram_id):
    """上传 DWG/DXF，提取图层列表（不渲染），供前端显示图层选择器"""
    diagram = SystemDiagram.query.get_or_404(diagram_id)
    if diagram.is_deleted or not _can_edit_diagram(diagram):
        return jsonify({'success': False, 'message': _('无权限')}), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': _('请选择文件')}), 400

    file = request.files['file']
    floor_id = request.form.get('floor_id', '')
    if not file.filename:
        return jsonify({'success': False, 'message': _('缺少参数')}), 400

    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in ('dxf', 'dwg'):
        return jsonify({'success': False, 'message': _('仅支持 DXF/DWG 格式')}), 400

    upload_dir = _get_bg_upload_dir()
    uid = uuid.uuid4().hex[:8]
    temp_path = os.path.join(upload_dir, f"_layers_{diagram_id}_{uid}.{ext}")

    try:
        file.save(temp_path)

        from app.utils.dxf_converter import extract_dxf_layers, convert_dwg_to_dxf

        if ext == 'dwg':
            try:
                dxf_path = convert_dwg_to_dxf(temp_path, upload_dir)
                os.remove(temp_path)
            except FileNotFoundError:
                return jsonify({
                    'success': False,
                    'message': _('服务器未安装 dwg2dxf，请先将 DWG 另存为 DXF 后上传')
                }), 500
        else:
            dxf_path = temp_path

        layers = extract_dxf_layers(dxf_path)
        temp_dxf_name = os.path.basename(dxf_path)

        return jsonify({
            'success': True,
            'layers': layers,
            'temp_dxf': temp_dxf_name,
        })

    except Exception as e:
        logger.error(f"提取 DXF 图层失败: {e}")
        for p in [temp_path, locals().get('dxf_path')]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
        return jsonify({'success': False, 'message': str(e)}), 500


@system_diagram.route('/api/<int:diagram_id>/floor-plan/find-dxf', methods=['GET'])
@login_required
@permission_required('system_diagram', 'view')
def find_dxf_api(diagram_id):
    """为丢失 dxf_filename 字段的旧图恢复 DXF 文件名。

    查找顺序：
    1. 精确匹配 {diagram_id}_{floor_id}_*.dxf （直接上传的 DXF）
    2. 匹配 _layers_{diagram_id}_*.dxf （经过图层选择流程的 DXF，按 mtime 最新的）

    请求参数: floor_id (可选)
    返回: {success, dxf_filename} 或 {success: false}
    """
    floor_id = request.args.get('floor_id', '')
    upload_dir = _get_bg_upload_dir()
    try:
        entries = os.listdir(upload_dir)
    except Exception:
        return jsonify({'success': False}), 200

    candidates = []  # list of (mtime, filename)
    for fn in entries:
        if not fn.lower().endswith('.dxf'):
            continue
        # Pattern 1: direct upload {id}_{floor}_{uid}.dxf
        if floor_id and fn.startswith(f'{diagram_id}_{floor_id}_'):
            try:
                mtime = os.path.getmtime(os.path.join(upload_dir, fn))
                candidates.append((mtime, fn, 1))  # priority 1
            except OSError:
                pass
        # Pattern 2: layer-selection flow _layers_{id}_{uid}.dxf
        elif fn.startswith(f'_layers_{diagram_id}_'):
            try:
                mtime = os.path.getmtime(os.path.join(upload_dir, fn))
                candidates.append((mtime, fn, 2))  # priority 2
            except OSError:
                pass

    if not candidates:
        return jsonify({'success': False}), 200

    # Prefer higher-priority (lower number) matches, then most recent
    candidates.sort(key=lambda x: (x[2], -x[0]))
    return jsonify({'success': True, 'dxf_filename': candidates[0][1]})


@system_diagram.route('/api/<int:diagram_id>/floor-plan/analyze-dxf', methods=['POST'])
@login_required
@permission_required('system_diagram', 'edit')
def analyze_dxf_api(diagram_id):
    """上传 DWG/DXF 文件，转换并渲染为多分辨率 PNG 底图"""
    diagram = SystemDiagram.query.get_or_404(diagram_id)
    if diagram.is_deleted or not _can_edit_diagram(diagram):
        return jsonify({'success': False, 'message': _('无权限')}), 403

    # Support two modes:
    # 1. Direct upload (file in request) — original flow
    # 2. Re-use temp DXF from extract-dxf-layers step (temp_dxf in form, no file)
    import json as _json
    floor_id = request.form.get('floor_id', '')
    temp_dxf_name = request.form.get('temp_dxf', '')
    include_layers_json = request.form.get('include_layers', '')
    include_layers = set(_json.loads(include_layers_json)) if include_layers_json else None

    upload_dir = _get_bg_upload_dir()
    uid = uuid.uuid4().hex[:8]

    if temp_dxf_name:
        # Re-use previously uploaded temp DXF (from extract-dxf-layers)
        safe_name = os.path.basename(temp_dxf_name)
        uploaded_path = None
        dxf_path = os.path.join(upload_dir, safe_name)
        if not os.path.exists(dxf_path):
            return jsonify({'success': False, 'message': _('临时文件已过期，请重新上传')}), 400
        if not floor_id:
            floor_id = 'fp'
    else:
        file = request.files.get('file')
        if not file or not file.filename or not floor_id:
            return jsonify({'success': False, 'message': _('缺少参数')}), 400

        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in ('dxf', 'dwg'):
            return jsonify({'success': False, 'message': _('仅支持 DXF/DWG 格式')}), 400

        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_BG_SIZE:
            return jsonify({'success': False, 'message': _('文件大小不能超过 12MB')}), 400

        uploaded_path = os.path.join(upload_dir, f"{diagram_id}_{floor_id}_{uid}.{ext}")
        file.save(uploaded_path)
        dxf_path = None

    try:
        from app.utils.dxf_converter import render_dxf_to_png, convert_dwg_to_dxf

        if dxf_path is None:
            ext = os.path.splitext(uploaded_path)[1].lstrip('.').lower()
            if ext == 'dwg':
                try:
                    dxf_path = convert_dwg_to_dxf(uploaded_path, upload_dir)
                    os.remove(uploaded_path)
                    uploaded_path = None
                except FileNotFoundError:
                    return jsonify({
                        'success': False,
                        'message': _('服务器未安装 dwg2dxf，请先将 DWG 另存为 DXF 后上传')
                    }), 500
            else:
                dxf_path = uploaded_path

        base_name = f"{diagram_id}_{floor_id}_{uid}"
        resolutions = render_dxf_to_png(dxf_path, upload_dir, base_name,
                                         max_dims=[1000, 2000, 4000, 8000],
                                         include_layers=include_layers)

        res_with_urls = {}
        all_png_filenames = []
        for dim_key, info in resolutions.items():
            res_with_urls[dim_key] = {
                'url': url_for('system_diagram.serve_floor_bg', filename=info['filename']),
                'width': info['width'],
                'height': info['height'],
            }
            all_png_filenames.append(info['filename'])

        default_res = res_with_urls.get('2000', list(res_with_urls.values())[0])
        dxf_filename = os.path.basename(dxf_path)

        return jsonify({
            'success': True,
            'url': default_res['url'],
            'width': default_res['width'],
            'height': default_res['height'],
            'resolutions': res_with_urls,
            'filenames': all_png_filenames,
            'dxf_filename': dxf_filename,
        })

    except ImportError:
        for p in [uploaded_path, locals().get('dxf_path')]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
        return jsonify({'success': False, 'message': 'matplotlib 未安装，无法渲染 DXF'}), 500
    except Exception as e:
        import traceback, sys
        print(f"[DXF ERROR] {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        logger.error(f"DXF 导入失败: {e}")
        for p in [uploaded_path, locals().get('dxf_path')]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
        return jsonify({'success': False, 'message': str(e)}), 500


@system_diagram.route('/bg/<string:filename>')
@login_required
@permission_required('system_diagram', 'view')
def serve_floor_bg(filename):
    """提供平面图背景图片"""
    upload_dir = _get_bg_upload_dir()
    safe_name = os.path.basename(filename)
    return send_from_directory(upload_dir, safe_name)


# ── 辅助函数 ──────────────────────────────────────────────

def _category_color(cat_name):
    """根据分类名称返回主题色"""
    color_map = {
        '基站': '#3b82f6',
        '天线': '#22c55e',
        '直放站': '#a855f7',
        '合路': '#f59e0b',
        '功率': '#ef4444',
        '耦合': '#ef4444',
        '对讲': '#06b6d4',
        '配件': '#64748b',
        '服务': '#94a3b8',
        '应用': '#8b5cf6',
    }
    for key, color in color_map.items():
        if key in (cat_name or ''):
            return color
    return '#64748b'


def _get_products_data():
    """获取产品列表（分享的内部路由和外部路由共用）

    排序规则：通过 product_display_order 表按 分类→子分类→型号 三层显示顺序排列，
    与产品列表 / 规格模板列表（spec_template.py）保持一致。
    """
    from sqlalchemy.orm import joinedload
    from sqlalchemy import func, and_
    from app.models.product_display_order import ProductDisplayOrder

    products = Product.query.filter(
        Product.status == 'active'
    ).options(
        joinedload(Product.category_obj),
        joinedload(Product.subcategory_obj)
    ).outerjoin(
        ProductCategory, Product.category_id == ProductCategory.id
    ).outerjoin(
        ProductSubcategory, Product.subcategory_id == ProductSubcategory.id
    ).outerjoin(
        ProductDisplayOrder,
        and_(
            ProductCategory.code_letter == ProductDisplayOrder.category_code,
            ProductSubcategory.code_letter == ProductDisplayOrder.subcategory_code,
            Product.model == ProductDisplayOrder.model,
        )
    ).order_by(
        func.coalesce(ProductDisplayOrder.category_order, 9999).asc(),
        func.coalesce(ProductDisplayOrder.subcategory_order, 9999).asc(),
        func.coalesce(ProductDisplayOrder.model_order, 9999).asc(),
        Product.id.asc(),
    ).all()

    categories = {}
    for p in products:
        cat_id = p.category_id or 0
        cat_obj = p.category_obj
        cat_name = cat_obj.name if cat_obj else _('未分类')
        cat_name_en = (getattr(cat_obj, 'name_en', None) or '') if cat_obj else ''
        sub_id = p.subcategory_id or 0
        sub_obj = p.subcategory_obj
        sub_name = sub_obj.name if sub_obj else _('未分类')
        sub_name_en = (getattr(sub_obj, 'name_en', None) or '') if sub_obj else ''

        if cat_id not in categories:
            categories[cat_id] = {
                'id': cat_id,
                'name': cat_name,
                'name_en': cat_name_en,
                'iconKey': getattr(cat_obj, 'icon_key', None) if cat_obj else None,
                'color': _category_color(cat_name),
                'subcategories': {}
            }

        subs = categories[cat_id]['subcategories']
        if sub_id not in subs:
            subs[sub_id] = {
                'id': sub_id,
                'name': sub_name,
                'name_en': sub_name_en,
                'iconKey': getattr(sub_obj, 'icon_key', None) if sub_obj else None,
                'products': []
            }

        subs[sub_id]['products'].append({
            'id': p.id,
            'productName': p.product_name or '',
            'mn': p.product_mn or '',
            'model': p.model or '',
            'displayLabel': p.product_mn or p.model or p.product_name or '',
            'imageUrl': p.image_path or '',
            'iconSvg': p.icon_svg,
            'specs': p.specification or '',
            'retailPrice': float(p.retail_price) if p.retail_price else 0,
        })

    result = []
    for cat in categories.values():
        cat['subcategories'] = list(cat['subcategories'].values())
        result.append(cat)
    return result


# ── BOM 提取 & 报价单生成 ──────────────────────────────────

@system_diagram.route('/api/<int:diagram_id>/create-quotation', methods=['POST'])
@login_required
@permission_required('quotation', 'create')
def api_create_quotation_from_bom(diagram_id):
    """从系统图 BOM 数据创建报价单(委托 quotation_service.create_quotation_from_bom)"""
    diagram = SystemDiagram.query.get_or_404(diagram_id)
    if diagram.is_deleted:
        return jsonify({'success': False, 'message': _('系统图不存在')}), 404
    if not diagram.project_id:
        return jsonify({'success': False, 'message': _('该系统图未关联项目')}), 400

    project = Project.query.get(diagram.project_id)
    if not project:
        return jsonify({'success': False, 'message': _('关联项目不存在')}), 404

    data = request.get_json()
    if not data or not data.get('details'):
        return jsonify({'success': False, 'message': _('无效的请求数据')}), 400

    try:
        from app.services.quotation_service import create_quotation_from_bom
        quotation = create_quotation_from_bom(
            user=current_user,
            project=project,
            items=data['details'],
            inherit_customer_from_history=True,  # 系统图原行为
        )
        return jsonify({
            'success': True,
            'status': 'success',
            'message': _('报价单创建成功'),
            'quotation_id': quotation.id,
            'redirect_url': f'/quotation/{quotation.id}'
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"从 BOM 创建报价单失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ── 分享功能 — 内部 API（需登录）──────────────────────────

@system_diagram.route('/api/share', methods=['POST'])
@login_required
@permission_required('system_diagram', 'view')
def api_create_share():
    """创建分享链接并发送邮件"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': _('无效的请求数据')}), 400

    email = (data.get('email') or '').strip().lower()
    if not email or '@' not in email:
        return jsonify({'success': False, 'message': _('请输入有效的邮箱地址')}), 400

    expires_hours = data.get('expiresHours', 72)
    if expires_hours not in (24, 48, 72, 168, 720):
        expires_hours = 72

    project_name = (data.get('projectName') or '').strip()
    source_diagram_id = data.get('sourceDiagramId') or None

    # 如果有源图，验证它存在
    if source_diagram_id:
        source = SystemDiagram.query.get(source_diagram_id)
        if not source or source.is_deleted:
            source_diagram_id = None

    permission = data.get('permission', 'edit')
    if permission not in ('view', 'edit'):
        permission = 'edit'

    token_str = secrets.token_hex(16)
    share = DiagramShareToken(
        token=token_str,
        project_name=project_name,
        designated_email=email,
        source_diagram_id=source_diagram_id,
        expires_at=datetime.now() + timedelta(hours=expires_hours),
        permission=permission,
        created_by_id=current_user.id
    )
    db.session.add(share)
    db.session.commit()

    # 生成分享链接
    share_url = url_for('system_diagram.external_entry', token=token_str, _external=True)

    # 发送邮件
    email_sent = False
    try:
        from app.utils.email import send_email
        creator_name = current_user.real_name or current_user.username
        creator_email = current_user.email or ''
        if permission == 'view':
            subject = f'{creator_name} 邀请您查看系统设计'
            invite_verb = '查看'
            invite_heading = '系统设计查看邀请'
            invite_heading_en = 'SYSTEM DESIGN VIEW INVITATION'
            invite_btn = '查看设计 →'
        else:
            subject = f'{creator_name} 邀请您参与系统设计'
            invite_verb = '参与'
            invite_heading = '系统设计邀请'
            invite_heading_en = 'SYSTEM DESIGN INVITATION'
            invite_btn = '进入设计 →'
        if project_name:
            subject += f' — {project_name}'

        expires_str = share.expires_at.strftime('%Y-%m-%d %H:%M')
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head><meta charset="utf-8"/><meta content="width=device-width, initial-scale=1.0" name="viewport"/></head>
        <body style="margin:0;padding:0;background:#fff;font-family:'Inter','Helvetica Neue',Arial,sans-serif;-webkit-font-smoothing:antialiased;">
            <div style="max-width:600px;margin:0 auto;padding:48px 24px;">
                <div style="text-align:center;padding-bottom:32px;margin-bottom:32px;border-bottom:1px solid #a0a0a0;">
                    <h1 style="font-size:24px;font-weight:300;margin:0 0 8px;color:#1a1a1a;">{invite_heading}</h1>
                    <p style="font-size:14px;color:#545454;margin:0;">{invite_heading_en}</p>
                </div>
                <div style="text-align:center;padding-bottom:32px;margin-bottom:32px;border-bottom:1px solid #e8e8e8;">
                    <p style="font-size:16px;color:#404040;margin:0 0 8px;font-weight:300;">
                        <strong>{creator_name}</strong> 邀请您{invite_verb}{('项目「' + project_name + '」的') if project_name else ''}系统设计
                    </p>
                    <p style="font-size:13px;color:#888;margin:0 0 24px;">请点击下方按钮{invite_verb}设计</p>
                    <a href="{share_url}" style="display:inline-block;padding:14px 32px;background:#1d4ed8;color:#fff;text-decoration:none;font-weight:500;font-size:14px;border-radius:8px;">
                        {invite_btn}
                    </a>
                </div>
                <div style="margin-bottom:32px;">
                    <p style="font-size:12px;color:#686868;margin:0 0 8px;">如按钮无法点击，请复制以下链接到浏览器：</p>
                    <p style="font-size:12px;color:#1d4ed8;margin:0;word-break:break-all;font-family:monospace;">{share_url}</p>
                </div>
                <div style="border:1px solid #e8e8e8;padding:16px;border-radius:8px;margin-bottom:32px;">
                    <p style="font-size:13px;color:#545454;margin:0;line-height:1.6;">
                        链接有效期至: <strong>{expires_str}</strong><br>
                        {'如有问题请联系: ' + creator_email if creator_email else ''}
                    </p>
                </div>
                <div style="text-align:center;padding-top:24px;border-top:1px solid #e8e8e8;">
                    <p style="font-size:11px;color:#a0a0a0;margin:0;">此邮件由系统自动发送，请勿直接回复</p>
                </div>
            </div>
        </body>
        </html>
        """
        email_sent = send_email(subject, email, None, html=html_content)
    except Exception as e:
        logger.error(f'发送分享邮件失败: {e}')

    return jsonify({
        'success': True,
        'shareUrl': share_url,
        'shareId': share.id,
        'emailSent': bool(email_sent),
        'expiresAt': share.expires_at.isoformat()
    })


@system_diagram.route('/api/shares')
@login_required
@permission_required('system_diagram', 'view')
def api_list_shares():
    """查看我创建的分享"""
    shares = DiagramShareToken.query.filter_by(
        created_by_id=current_user.id
    ).order_by(DiagramShareToken.created_at.desc()).limit(50).all()

    result = []
    for s in shares:
        result.append({
            'id': s.id,
            'token': s.token,
            'projectName': s.project_name or '',
            'email': s.designated_email,
            'permission': s.permission or 'edit',
            'expiresAt': s.expires_at.isoformat(),
            'isActive': s.is_active,
            'isExpired': s.is_expired,
            'createdAt': s.created_at.isoformat() if s.created_at else '',
            'sessionCount': s.sessions.count()
        })
    return jsonify({'success': True, 'shares': result})


@system_diagram.route('/api/shares/<int:share_id>', methods=['DELETE'])
@login_required
@permission_required('system_diagram', 'view')
def api_delete_share(share_id):
    """作废分享链接"""
    share = DiagramShareToken.query.get_or_404(share_id)
    if share.created_by_id != current_user.id:
        return jsonify({'success': False, 'message': _('无权限')}), 403
    share.is_active = False
    db.session.commit()
    return jsonify({'success': True})


# ── 外部路由（无需登录）──────────────────────────────────

def _validate_share_token(token):
    """验证分享令牌，返回 (share, error_response)"""
    share = DiagramShareToken.query.filter_by(token=token).first()
    if not share:
        return None, (_('链接无效'), 404)
    if not share.is_active:
        return None, (_('链接已失效'), 410)
    if share.is_expired:
        return None, (_('链接已过期'), 410)
    return share, None


@system_diagram.route('/s/<token>')
def external_entry(token):
    """外部入口 — 渲染邮箱验证页"""
    share, error = _validate_share_token(token)
    if error:
        return render_template('system_diagram/tw_external_verify.html',
                               error=error[0], token=token, share=None), error[1]
    return render_template('system_diagram/tw_external_verify.html',
                           share=share, token=token, error=None)


@system_diagram.route('/s/<token>/verify', methods=['POST'])
def external_verify(token):
    """验证邮箱"""
    share, error = _validate_share_token(token)
    if error:
        return jsonify({'success': False, 'message': error[0]}), error[1]

    data = request.get_json()
    email = (data.get('email') or '').strip().lower()
    if not email or '@' not in email:
        return jsonify({'success': False, 'message': _('请输入有效的邮箱地址')}), 400

    # 校验邮箱：必须与分享指定的收件邮箱一致
    if share.designated_email and email != share.designated_email.strip().lower():
        return jsonify({'success': False, 'message': _('邮箱地址与分享指定的收件人不匹配')}), 403

    # 设置 session
    flask_session['external_email'] = email
    flask_session['external_token'] = token

    # 查找或创建外部会话
    ext_session = DiagramExternalSession.query.filter_by(
        share_token_id=share.id, email=email
    ).first()

    if not ext_session:
        ext_session = DiagramExternalSession(
            share_token_id=share.id,
            email=email
        )
        db.session.add(ext_session)

    ext_session.access_count = (ext_session.access_count or 0) + 1
    ext_session.last_accessed_at = datetime.now()
    db.session.commit()

    return jsonify({
        'success': True,
        'hasData': ext_session.diagram_id is not None,
        'redirectUrl': url_for('system_diagram.external_editor', token=token)
    })


@system_diagram.route('/s/<token>/editor')
def external_editor(token):
    """外部编辑器页面"""
    share, error = _validate_share_token(token)
    if error:
        return redirect(url_for('system_diagram.external_entry', token=token))

    email = flask_session.get('external_email')
    session_token = flask_session.get('external_token')
    if not email or session_token != token:
        return redirect(url_for('system_diagram.external_entry', token=token))

    read_only = (share.permission == 'view')
    return render_template('system_diagram/tw_editor.html',
                           diagram_id=0,
                           diagram_name=share.project_name or _('系统设计'),
                           project_id=0,
                           project_name=share.project_name or '',
                           external_mode=True,
                           read_only=read_only,
                           share_token=token,
                           external_email=email,
                           active_page='system_diagram')


@system_diagram.route('/s/<token>/save', methods=['POST'])
def external_save(token):
    """外部用户保存设计"""
    share, error = _validate_share_token(token)
    if error:
        return jsonify({'success': False, 'message': error[0]}), error[1]

    if share.permission == 'view':
        return jsonify({'success': False, 'message': _('当前为只读权限，无法保存')}), 403

    email = flask_session.get('external_email')
    if not email or flask_session.get('external_token') != token:
        return jsonify({'success': False, 'message': _('请先验证邮箱')}), 401

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': _('无效的请求数据')}), 400

    diagram_data = data.get('diagramData', {})
    name = (data.get('name') or '').strip() or (share.project_name or '系统设计')
    thumbnail_svg = data.get('thumbnailSvg', '')

    ext_session = DiagramExternalSession.query.filter_by(
        share_token_id=share.id, email=email
    ).first()
    if not ext_session:
        return jsonify({'success': False, 'message': _('会话不存在')}), 404

    if ext_session.diagram_id:
        # 更新已有图
        diagram = SystemDiagram.query.get(ext_session.diagram_id)
        if diagram:
            diagram.name = name
            diagram.diagram_data = diagram_data
            diagram.thumbnail_svg = thumbnail_svg
            diagram.updated_at = datetime.now()
        else:
            return jsonify({'success': False, 'message': _('关联图已删除')}), 404
    else:
        # 创建新图
        diagram = SystemDiagram(
            name=name,
            diagram_data=diagram_data,
            thumbnail_svg=thumbnail_svg,
            owner_id=share.created_by_id
        )
        db.session.add(diagram)
        db.session.flush()
        ext_session.diagram_id = diagram.id

    db.session.commit()
    return jsonify({
        'success': True,
        'id': ext_session.diagram_id,
        'message': _('设计已保存')
    })


@system_diagram.route('/s/<token>/load')
def external_load(token):
    """外部用户加载设计"""
    share, error = _validate_share_token(token)
    if error:
        return jsonify({'success': False, 'message': error[0]}), error[1]

    email = flask_session.get('external_email')
    if not email or flask_session.get('external_token') != token:
        return jsonify({'success': False, 'message': _('请先验证邮箱')}), 401

    ext_session = DiagramExternalSession.query.filter_by(
        share_token_id=share.id, email=email
    ).first()
    if not ext_session or not ext_session.diagram_id:
        # 如果有源图，加载源图数据作为初始模板
        if share.source_diagram_id:
            source = SystemDiagram.query.get(share.source_diagram_id)
            if source and not source.is_deleted:
                return jsonify({
                    'success': True,
                    'diagram': {
                        'id': 0,
                        'name': share.project_name or source.name,
                        'diagramData': source.diagram_data or {},
                    }
                })
        return jsonify({'success': True, 'diagram': None})

    diagram = SystemDiagram.query.get(ext_session.diagram_id)
    if not diagram:
        return jsonify({'success': True, 'diagram': None})

    return jsonify({
        'success': True,
        'diagram': {
            'id': diagram.id,
            'name': diagram.name,
            'diagramData': diagram.diagram_data or {},
        }
    })


@system_diagram.route('/s/<token>/products')
def external_products(token):
    """外部用户获取产品列表"""
    share, error = _validate_share_token(token)
    if error:
        return jsonify({'success': False, 'message': error[0]}), error[1]

    email = flask_session.get('external_email')
    if not email or flask_session.get('external_token') != token:
        return jsonify({'success': False, 'message': _('请先验证邮箱')}), 401

    return jsonify({'success': True, 'categories': _get_products_data()})


@system_diagram.route('/api/<int:diagram_id>/export-dwg', methods=['POST'])
@login_required
@permission_required('system_diagram', 'view')
def export_dwg_api(diagram_id):
    """导出 CAD 文件：原 DXF + SYSTEM_DESIGN 图层（设备/连线/区域作为原生矢量实体）

    请求体 (JSON):
        elements: {
            bg_width_px, bg_height_px, offset_x, offset_y,
            nodes: [{id,x,y,w,h,label,model,qty,coverage}],
            routes: [{sourceNodeId,targetNodeId,waypoints,label,...}],
            areas: [{x,y,width,height,label}]
        }
        dxf_filename: fp.background.dxf_filename（服务端存储的原 DXF）
        diagram_name: 输出文件命名

    返回:
        .dxf 文件（保留原有所有实体，仅增加 SYSTEM_DESIGN* 图层）
    """
    import tempfile

    diagram = SystemDiagram.query.get_or_404(diagram_id)
    if diagram.is_deleted:
        return jsonify({'success': False, 'message': _('系统图不存在')}), 404

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': _('无效请求')}), 400

    elements = data.get('elements') or {}
    dxf_filename = data.get('dxf_filename', '')
    diagram_name = data.get('diagram_name', 'system_diagram')

    if not dxf_filename:
        return jsonify({'success': False, 'message': _('缺少 DXF 底图信息')}), 400

    upload_dir = _get_bg_upload_dir()
    dxf_path = os.path.join(upload_dir, os.path.basename(dxf_filename))
    if not os.path.exists(dxf_path):
        return jsonify({'success': False, 'message': _('DXF 源文件不存在，请重新导入底图')}), 404

    try:
        from app.utils.dxf_converter import overlay_system_design_on_dxf
        from flask import Response
        from urllib.parse import quote

        # 完整名（含中文，用于 RFC 5987）
        safe_name = ''.join(c for c in diagram_name if c.isalnum() or c in '-_ ·')[:40].strip() or 'diagram'
        # ASCII 回退名（兼容老浏览器，剥掉非 ASCII 字符）
        ascii_name = ''.join(c if c.isascii() and (c.isalnum() or c in '-_ ') else '_' for c in safe_name).strip('_').strip() or 'diagram'

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dxf_path = os.path.join(tmpdir, f"{ascii_name}.dxf")
            overlay_system_design_on_dxf(dxf_path, out_dxf_path, elements)

            with open(out_dxf_path, 'rb') as f:
                file_bytes = f.read()

        # RFC 5987：filename*=UTF-8''<percent-encoded> 让浏览器正确解码中文
        utf8_quoted = quote(f"{safe_name}.dxf")
        return Response(
            file_bytes,
            mimetype='application/dxf',
            headers={
                'Content-Disposition': f"attachment; filename=\"{ascii_name}.dxf\"; filename*=UTF-8''{utf8_quoted}",
                'Content-Length': len(file_bytes),
            }
        )

    except Exception as e:
        logger.error(f"导出 DXF 失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
