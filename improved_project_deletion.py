
# 改进后的项目删除函数 - 添加到 app/views/project.py 的 delete_project 函数中

@project.route('/delete/<int:project_id>', methods=['POST'])
@permission_required('project', 'delete')
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    # 检查删除权限
    if not can_edit_data(project, current_user):
        logger.warning(f"用户 {current_user.username} (ID: {current_user.id}, 角色: {current_user.role}) 尝试删除无权限的项目: {project_id} (所有者: {project.owner_id})")
        
        # 检查是否是AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': '您没有权限删除此项目'
            }), 403
            
        flash('您没有权限删除此项目', 'danger')
        return redirect(url_for('project.list_projects'))
    
    try:
        # === 关联数据清理开始 ===
        
        # 1. 先删除项目关联的所有报价单
        from app.models.quotation import Quotation
        quotations = Quotation.query.filter_by(project_id=project_id).all()
        quotation_ids = [q.id for q in quotations]  # 保存报价单ID用于后续删除审批
        
        if quotations:
            for quotation in quotations:
                db.session.delete(quotation)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(quotations)} 个报价单")
        
        # 2. 删除项目关联的所有阶段历史记录
        from app.models.projectpm_stage_history import ProjectStageHistory
        stage_histories = ProjectStageHistory.query.filter_by(project_id=project_id).all()
        if stage_histories:
            for history in stage_histories:
                db.session.delete(history)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(stage_histories)} 个阶段历史记录")
        
        # 3. 删除项目跟进记录和回复 (新增)
        from app.models.action import Action, ActionReply
        project_actions = Action.query.filter_by(project_id=project_id).all()
        if project_actions:
            action_reply_count = 0
            for action in project_actions:
                # 统计回复数量
                replies = ActionReply.query.filter_by(action_id=action.id).all()
                action_reply_count += len(replies)
                # ActionReply已通过cascade='all, delete-orphan'自动删除
                db.session.delete(action)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(project_actions)} 个跟进记录和 {action_reply_count} 个回复")
        
        # 4. 删除项目审批实例和记录 (新增)
        from app.models.approval import ApprovalInstance, ApprovalRecord
        project_approvals = ApprovalInstance.query.filter_by(
            object_type='project', 
            object_id=project_id
        ).all()
        if project_approvals:
            approval_record_count = 0
            for approval in project_approvals:
                # 统计审批记录数量
                records = ApprovalRecord.query.filter_by(instance_id=approval.id).all()
                approval_record_count += len(records)
                # ApprovalRecord已通过cascade="all, delete-orphan"自动删除
                db.session.delete(approval)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(project_approvals)} 个项目审批实例和 {approval_record_count} 个审批记录")
        
        # 5. 删除关联报价单的审批实例 (新增)
        if quotation_ids:
            quotation_approvals = ApprovalInstance.query.filter(
                ApprovalInstance.object_type == 'quotation',
                ApprovalInstance.object_id.in_(quotation_ids)
            ).all()
            if quotation_approvals:
                quotation_approval_record_count = 0
                for approval in quotation_approvals:
                    # 统计审批记录数量
                    records = ApprovalRecord.query.filter_by(instance_id=approval.id).all()
                    quotation_approval_record_count += len(records)
                    db.session.delete(approval)
                logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(quotation_approvals)} 个报价单审批实例和 {quotation_approval_record_count} 个审批记录")
        
        # 6. 删除项目评分记录
        try:
            from app.models.project_scoring import ProjectScoringRecord, ProjectTotalScore
            
            # 删除评分记录
            scoring_records = ProjectScoringRecord.query.filter_by(project_id=project_id).all()
            if scoring_records:
                for record in scoring_records:
                    db.session.delete(record)
                logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(scoring_records)} 个项目评分记录")
            
            # 删除总评分记录
            total_scores = ProjectTotalScore.query.filter_by(project_id=project_id).all()
            if total_scores:
                for score in total_scores:
                    db.session.delete(score)
                logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(total_scores)} 个项目总分记录")
                    
        except ImportError:
            # 如果新评分系统模块不存在，跳过
            logger.info("项目评分系统模块不存在，跳过评分记录清理")
        
        # 7. 删除旧的评分记录
        try:
            if ProjectRatingRecord:
                old_rating_records = ProjectRatingRecord.query.filter_by(project_id=project_id).all()
                if old_rating_records:
                    for record in old_rating_records:
                        db.session.delete(record)
                    logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(old_rating_records)} 个旧版评分记录")
        except Exception:
            # 如果评分系统模块处理失败，跳过
            logger.info("旧版评分系统模块处理失败，跳过")
        
        # === 关联数据清理结束 ===
        
        # 8. 最后删除项目
        # 记录删除历史（在实际删除前记录）
        try:
            ChangeTracker.log_delete(project)
        except Exception as track_err:
            logger.warning(f"记录项目删除历史失败: {str(track_err)}")
        
        db.session.delete(project)
        db.session.commit()
        
        logger.info(f"项目 {project_id} ({project.project_name}) 及其所有关联数据删除成功")
        
        # 检查是否是AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': '项目删除成功！'
            })
        flash('项目删除成功！', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除项目 {project_id} 失败: {str(e)}")
        
        # 检查是否是AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': f'删除失败：{str(e)}'
            }), 500
            
        flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('project.list_projects'))
