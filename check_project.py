from app import create_app
from app.models.project import Project
from app.models.user import User
from app.models.projectpm_stage_history import ProjectStageHistory
from app.models.projectpm_statistics import ProjectStatistics, MAINLINE_STAGES
from app import db
from datetime import datetime
app = create_app()
with app.app_context():
    print('主线阶段定义: ', MAINLINE_STAGES)
    project = Project.query.get(69)
    print(f'Project 69: id={project.id}, name={project.project_name}, stage={project.current_stage}, auth_code={project.authorization_code}')
    today = datetime.now().date()
    start_date = today.replace(day=1)
    print(f'本月开始日期: {start_date}')
    # 查询符合条件的历史记录
    history_query = db.session.query(ProjectStageHistory.project_id).filter(
        ProjectStageHistory.change_date >= start_date,
        ProjectStageHistory.from_stage.in_(MAINLINE_STAGES),
        ProjectStageHistory.to_stage.in_(MAINLINE_STAGES),
        ProjectStageHistory.to_stage.notin_(['失败', '搁置'])
    )
    project_ids = [row.project_id for row in history_query.all()]
    print(f'历史记录查询获取的项目IDs: {project_ids}')
    print('是否包含项目69:', 69 in project_ids)
    # 查询实际统计的项目
    projects = Project.query.filter(
        Project.id.in_(project_ids),
        Project.authorization_code.isnot(None),
        db.func.length(Project.authorization_code) > 0
    ).all()
    print(f'实际统计的项目数量: {len(projects)}')
    for p in projects:
        print(f'项目: id={p.id}, name={p.project_name}, stage={p.current_stage}, auth_code={p.authorization_code}')
    # 执行完整的统计逻辑
    # 查询项目69的阶段历史记录
    histories = ProjectStageHistory.query.filter_by(project_id=69).all()
    print(f'项目69的历史记录条数: {len(histories)}')
    for h in histories:
        from_stage_in_mainline = h.from_stage in MAINLINE_STAGES
        to_stage_in_mainline = h.to_stage in MAINLINE_STAGES
        to_stage_in_excluded = h.to_stage in ['失败', '搁置']
        date_in_current_month = h.change_date.date() >= start_date
        should_be_counted = from_stage_in_mainline and to_stage_in_mainline and not to_stage_in_excluded and date_in_current_month
        print(f'历史记录: id={h.id}, from={h.from_stage}, to={h.to_stage}, date={h.change_date}, 是否符合统计条件={should_be_counted} (from_in_main={from_stage_in_mainline}, to_in_main={to_stage_in_mainline}, date_in_month={date_in_current_month})')
