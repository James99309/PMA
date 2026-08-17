# -*- coding: utf-8 -*-
"""报备审批验证脚本的公共骨架:环境钉死 + 真正的自清理。

为什么不能靠 db.session.rollback():
  发起审批链路里有多处内部 commit(get_or_create_report_template 的模板落库、
  ApprovalMessageService 建站内消息、process_approval 的推进落库),脚本末尾的
  rollback 收不回已经提交的审批实例/项目锁。必须显式硬删 + 还原字段并 commit。
"""
import os
import sys

PROJ_FIELDS = ('status', 'authorization_code', 'vendor_sales_manager_id',
               'is_locked', 'locked_reason', 'locked_by', 'locked_at')


def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")


def make_app(db_type='sp8d'):
    """本机 pma_local(CN 数据副本)上建 app。禁用 run.py 路径:.env.*.local 里
    废弃的 Supabase 生产串会 override 掉本地库。"""
    root = get_project_root()
    sys.path.insert(0, root)
    os.chdir(root)
    from dotenv import load_dotenv
    load_dotenv(os.path.join(root, '.env.nas'), override=True)
    os.environ['DATABASE_URL'] = 'postgresql://nijie@localhost:5432/pma_local'
    os.environ['PMA_DB_TYPE'] = db_type
    os.environ['FORCE_LOCAL_STORAGE'] = 'true'
    from config import LocalConfig
    from app import create_app
    return create_app(LocalConfig)


class Sandbox:
    """记录基线 → 结束时硬删新建审批实例并还原被动过的项目字段。

    用法:
        sb = Sandbox()
        sb.watch(project)          # 每个将被发起审批的项目都先 watch
        ...
        sb.teardown()              # 必须在 finally 里调
    """

    def __init__(self):
        from sqlalchemy import func
        from app import db
        from app.models.approval import ApprovalInstance
        self._db = db
        self._max_instance_id = (db.session.query(func.max(ApprovalInstance.id)).scalar() or 0)
        self._projects = {}

    def watch(self, project):
        if project is not None and project.id not in self._projects:
            self._projects[project.id] = {f: getattr(project, f) for f in PROJ_FIELDS}
        return project

    def teardown(self):
        from app.models.approval import ApprovalInstance, ApprovalRecord
        from app.models.project import Project
        db = self._db
        db.session.rollback()          # 先丢掉未提交的脏状态
        new_ids = [i.id for i in ApprovalInstance.query.filter(
            ApprovalInstance.id > self._max_instance_id).all()]
        if new_ids:
            ApprovalRecord.query.filter(ApprovalRecord.instance_id.in_(new_ids)).delete(
                synchronize_session=False)
            ApprovalInstance.query.filter(ApprovalInstance.id.in_(new_ids)).delete(
                synchronize_session=False)
        for pid, snap in self._projects.items():
            p = Project.query.get(pid)
            if p:
                for f, v in snap.items():
                    setattr(p, f, v)
        db.session.commit()
        print(f"  [teardown] 删除审批实例 {len(new_ids)} 个, 还原项目 {len(self._projects)} 个")
