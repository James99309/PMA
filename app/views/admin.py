from app.extensions import db
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort, jsonify
from flask_login import login_required, current_user
from app.decorators import admin_required
from app.models.settings import SystemSettings, DEFAULT_SETTINGS
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def system_settings():
    """系统参数设置页面"""
    if request.method == 'POST':
        # 处理表单提交
        try:
            # 导入历史记录跟踪器
            from app.utils.change_tracker import ChangeTracker

            # 遍历表单数据，更新系统设置
            for key in DEFAULT_SETTINGS.keys():
                if key in request.form:
                    try:
                        # 尝试将值转换为整数
                        value = int(request.form.get(key))
                        # 确保值有效
                        if value <= 0:
                            flash(f'参数 {key} 必须大于0', 'danger')
                            continue
                    except (ValueError, TypeError):
                        flash(f'参数 {key} 必须是有效的数字', 'danger')
                        continue

                    # 获取旧值用于历史记录
                    old_value = SystemSettings.get(key, DEFAULT_SETTINGS[key]['value'])

                    # 更新设置，直接存储为int
                    SystemSettings.set(key, value)

                    # 记录变更历史
                    try:
                        # 创建一个虚拟对象来记录系统设置变更
                        class SystemSettingsRecord:
                            def __init__(self):
                                self.id = 0
                                self.__tablename__ = 'system_settings'

                        settings_obj = SystemSettingsRecord()
                        ChangeTracker.track_change(
                            obj=settings_obj,
                            action='update',
                            user_id=current_user.id,
                            changes={
                                key: {'old': old_value, 'new': value}
                            },
                            description=f'系统设置更新：{DEFAULT_SETTINGS[key]["label"]}'
                        )
                    except Exception as e:
                        logger.error(f"记录系统设置变更历史失败: {str(e)}")

            db.session.commit()
            flash('系统设置已更新', 'success')
            return redirect(url_for('admin.system_settings'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"更新系统设置失败: {str(e)}")
            flash(f'更新失败: {str(e)}', 'danger')

    # GET请求，显示设置页面
    settings = {}
    for key, config in DEFAULT_SETTINGS.items():
        settings[key] = {
            'label': config['label'],
            'description': config['description'],
            'value': SystemSettings.get(key, config['value']),
            'unit': config.get('unit', ''),
            'default': config['value']
        }

    return render_template('admin/system_settings.html', settings=settings)

@admin_bp.route('/refresh_project_activity', methods=['POST'])
@login_required
@admin_required
def refresh_project_activity():
    """手动刷新所有项目的活跃状态"""
    try:
        from app.models.project import Project
        from app.utils.project_activity import update_project_activity

        success_count = 0
        error_count = 0

        # 分批处理，避免一次性加载全部项目到内存
        batch_size = 100
        offset = 0
        while True:
            projects = Project.query.filter(Project.is_deleted == False).limit(batch_size).offset(offset).all()
            if not projects:
                break
            for project in projects:
                try:
                    update_project_activity(project)
                    success_count += 1
                except Exception as e:
                    logger.error(f"更新项目 {project.id} 活跃状态失败: {str(e)}")
                    error_count += 1
            db.session.commit()
            offset += batch_size

        message = f'项目活跃状态刷新完成：成功 {success_count} 个'
        if error_count > 0:
            message += f'，失败 {error_count} 个'

        flash(message, 'success' if error_count == 0 else 'warning')

    except Exception as e:
        db.session.rollback()
        logger.error(f"批量刷新项目活跃状态失败: {str(e)}")
        flash(f'刷新失败: {str(e)}', 'danger')

    return redirect(url_for('admin.system_settings'))

@admin_bp.route('/ai-usage')
@login_required
@admin_required
def ai_usage_dashboard():
    """AI 使用量监控仪表板"""
    from app.models.user import User
    users = User.query.filter(User._is_active == True).order_by(User.real_name).all()
    now = datetime.now()
    return render_template('admin/tw_ai_usage.html', users=users,
                           current_year=now.year, current_month=now.month)


@admin_bp.route('/api/ai-usage-stats')
@login_required
@admin_required
def ai_usage_stats_api():
    """AI 使用量统计数据 API"""
    from app.services.ai_usage_stats_service import get_ai_usage_stats
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    user_id = request.args.get('user_id', type=int)
    source = request.args.get('source') or None
    result = get_ai_usage_stats(year, month, user_id, source)
    return jsonify(result)


@admin_bp.route('/')
@admin_required
def index():
    """管理员首页"""
    return redirect(url_for('admin.system_settings'))


# ─── Skill 管理 ──────────────────────────────────────────────────────────────

@admin_bp.route('/skills')
@admin_required
def skill_list():
    from app.models.cli_skill import CliSkill
    skills = CliSkill.query.order_by(CliSkill.skill_type, CliSkill.title).all()
    return render_template('admin/skills/tw_list.html', skills=skills)


@admin_bp.route('/skills/<int:skill_id>')
@admin_required
def skill_detail(skill_id):
    from app.models.cli_skill import CliSkill, CliSkillVersion
    skill = CliSkill.query.get_or_404(skill_id)
    versions = CliSkillVersion.query.filter_by(skill_id=skill_id).order_by(
        CliSkillVersion.version.desc()).all()
    return render_template('admin/skills/tw_detail.html', skill=skill, versions=versions)


@admin_bp.route('/skills/<int:skill_id>/edit', methods=['GET', 'POST'])
@admin_required
def skill_edit(skill_id):
    from app.models.cli_skill import CliSkill, CliSkillVersion
    from app import db
    skill = CliSkill.query.get_or_404(skill_id)

    if request.method == 'POST':
        import json as _json
        change_note = request.form.get('change_note', '').strip() or '管理员更新'
        skill.is_active = bool(request.form.get('is_active'))
        new_title = request.form.get('title', '').strip()
        if new_title:
            skill.title = new_title
        new_desc = request.form.get('description', '').strip()
        if new_desc:
            skill.description = new_desc

        if skill.skill_type == 'docx':
            new_body = request.form.get('skill_body', '').strip()
            if new_body:
                last = CliSkillVersion.query.filter_by(skill_id=skill_id).order_by(
                    CliSkillVersion.version.desc()).first()
                next_ver = (last.version + 1) if last else 1
                db.session.add(CliSkillVersion(
                    skill_id=skill_id, version=next_ver,
                    skill_body=new_body, change_note=change_note,
                    created_by=current_user.id,
                ))
                skill.skill_body = new_body
                flash(f'Skill 已更新（版本 v{next_ver}）', 'success')
            else:
                flash('Skill 基本信息已更新', 'success')

        elif skill.skill_type == 'sql':
            # 重建 queries 列表：每步 SQL 单独 textarea
            existing = skill.queries or []
            new_queries = []
            for i, step in enumerate(existing):
                sql_val = request.form.get(f'query_sql_{i}', '').strip()
                as_name = request.form.get(f'query_as_name_{i}', step.get('as_name', '')).strip()
                step_desc = request.form.get(f'query_desc_{i}', step.get('description', '')).strip()
                new_queries.append({
                    'sql': sql_val or step.get('sql', ''),
                    'as_name': as_name,
                    'description': step_desc,
                })
            skill.queries = new_queries

            params_raw = request.form.get('parameters_json', '').strip()
            if params_raw:
                try:
                    skill.parameters = _json.loads(params_raw)
                except ValueError:
                    flash('参数 JSON 格式错误，已保留原值', 'warning')

            output_fmt = request.form.get('output_format', '').strip()
            skill.output_format = output_fmt or skill.output_format
            flash('Skill 已更新', 'success')

        db.session.commit()
        return redirect(url_for('admin.skill_detail', skill_id=skill_id))

    return render_template('admin/skills/tw_edit.html', skill=skill)


@admin_bp.route('/skills/<int:skill_id>/versions/<int:version_id>/restore', methods=['POST'])
@admin_required
def skill_version_restore(skill_id, version_id):
    from app.models.cli_skill import CliSkill, CliSkillVersion
    from app import db
    skill = CliSkill.query.get_or_404(skill_id)
    ver = CliSkillVersion.query.get_or_404(version_id)

    last = CliSkillVersion.query.filter_by(skill_id=skill_id).order_by(
        CliSkillVersion.version.desc()).first()
    next_ver = (last.version + 1) if last else 1

    snap = CliSkillVersion(
        skill_id=skill_id,
        version=next_ver,
        skill_body=ver.skill_body,
        change_note=f'从 v{ver.version} 回滚',
        created_by=current_user.id,
    )
    db.session.add(snap)
    skill.skill_body = ver.skill_body
    db.session.commit()
    flash(f'已从 v{ver.version} 回滚（新版本 v{next_ver}）', 'success')
    return redirect(url_for('admin.skill_detail', skill_id=skill_id))
