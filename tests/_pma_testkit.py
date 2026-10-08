# -*- coding: utf-8 -*-
"""tests/ 下脚本共用的最小骨架:定位项目根 + 在本机 pma_local 上建 app。

复制自 scripts/temp/_report_flow_testkit.make_app,避免 tests/ 依赖临时脚本目录。
禁用 run.py 路径:.env.*.local 里废弃的 Supabase 生产串会 override 掉本地库。
"""
import os
import sys


def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")


def make_app(db_type='sp8d'):
    root = get_project_root()
    if root not in sys.path:
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


# ───────────── 浏览器 e2e 共用:临时实例 / 临时账号 / 临时题库 ─────────────

MAIN_ASSETS = os.path.normpath(os.path.join(get_project_root(), '..', '..', 'app', 'course_assets'))

_SERVER_CODE = r'''
import os, sys
sys.path.insert(0, os.path.join(os.getcwd(), 'tests'))
from _pma_testkit import make_app
flask_app = make_app()
import app.views.knowledge_wiki as KW
main_assets = sys.argv[2]
if not os.path.isfile(KW._course_html_path(sys.argv[3])) and os.path.isdir(main_assets):
    KW.COURSE_ASSETS_DIR = main_assets      # worktree 没有课件(gitignored),只读借用主仓
flask_app.run(host='127.0.0.1', port=int(sys.argv[1]), use_reloader=False, threaded=True)
'''


def start_server(port, log_path, probe_course_key, assets_dir=None):
    """后台起一个本机 pma_local 实例(PORT 派生独立 cookie 名);返回 Popen,须配 stop_server。
    assets_dir:课件目录(默认借主仓 course_assets;临时课程用 make_temp_course 建的目录)。"""
    import subprocess
    import time
    import urllib.request
    env = dict(os.environ)
    env.update({'PORT': str(port), 'DYLD_FALLBACK_LIBRARY_PATH': '/opt/homebrew/lib',
                'DATABASE_URL': 'postgresql://nijie@localhost:5432/pma_local',
                'PMA_DB_TYPE': 'sp8d', 'FORCE_LOCAL_STORAGE': 'true'})
    log = open(log_path, 'w')
    proc = subprocess.Popen([sys.executable, '-c', _SERVER_CODE, str(port), assets_dir or MAIN_ASSETS, probe_course_key],
                            cwd=get_project_root(), env=env, stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True)
    deadline = time.time() + 120
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError('服务进程提前退出,见 ' + log_path)
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}/auth/login', timeout=3)
            return proc
        except Exception:
            time.sleep(1)
    stop_server(proc)
    raise RuntimeError('服务启动超时')


def stop_server(proc):
    import signal
    if proc and proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=15)
        except Exception:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass


def create_temp_user(app, username, password, role='sales_manager'):
    from app import db
    from app.models.user import User
    from sqlalchemy import text
    with app.app_context():
        company = db.session.execute(text(
            "SELECT company_name FROM users WHERE company_name IS NOT NULL AND company_name<>'' "
            "GROUP BY company_name ORDER BY count(*) DESC LIMIT 1")).scalar() or 'ZZ'
        u = User(username=username, real_name='ZZ ' + username, company_name=company,
                 email=username + '@example.invalid', role=role)
        u.set_password(password)
        u._is_active = True
        db.session.add(u)
        db.session.commit()
        return u.id


def delete_temp_user(app, username):
    """硬删临时账号及其所有外键关联行 + 作答留痕(无外键)。返回是否已删干净。"""
    from app import db
    from sqlalchemy import text
    with app.app_context():
        uid = db.session.execute(text('SELECT id FROM users WHERE username=:u'), {'u': username}).scalar()
        if uid:
            fks = db.session.execute(text("""
                SELECT tc.table_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name = 'users'
                  AND ccu.column_name = 'id' AND tc.table_schema = 'public'""")).fetchall()
            db.session.execute(text("DELETE FROM training_quiz_attempt WHERE user_id=:u"), {'u': uid})
            for _ in range(3):           # 关联表之间可能互相引用,多轮删到干净
                for table, col in fks:
                    if table == 'users':
                        continue
                    try:
                        with db.session.begin_nested():
                            db.session.execute(text(f'DELETE FROM "{table}" WHERE "{col}" = :u'), {'u': uid})
                    except Exception:
                        pass
            db.session.execute(text('DELETE FROM users WHERE id=:u'), {'u': uid})
        db.session.commit()
        return not db.session.execute(text('SELECT count(*) FROM users WHERE username=:u'),
                                      {'u': username}).scalar()


def add_temp_bank(app, course_key, prefix):
    """给课程插 34 道难题(3 分,共 102 分 → 题库健康):30 单选 + 2 多选 + 2 判断。题干带 prefix 便于清理。"""
    from app import db
    from app.models.course_exam import CourseQuizQuestion
    with app.app_context():
        for i in range(30):
            db.session.add(CourseQuizQuestion(course_key=course_key, qtype='single', difficulty=3,
                                              question=f'{prefix}single {i}', options=['A1', 'B2', 'C3', 'D4'],
                                              answer=0, explain='ZZ explain', source_page=2, status='active'))
        for i in range(2):
            db.session.add(CourseQuizQuestion(course_key=course_key, qtype='multi', difficulty=3,
                                              question=f'{prefix}multi {i}', options=['M1', 'M2', 'M3', 'M4'],
                                              answer=[0, 2], explain='ZZ explain', status='active'))
            db.session.add(CourseQuizQuestion(course_key=course_key, qtype='judge', difficulty=3,
                                              question=f'{prefix}judge {i}', options=None,
                                              answer=True, explain='ZZ explain', status='active'))
        db.session.commit()


def delete_temp_bank(app, prefix):
    from app import db
    from sqlalchemy import text
    with app.app_context():
        db.session.execute(text("DELETE FROM course_quiz_questions WHERE question LIKE :p"), {'p': prefix + '%'})
        db.session.commit()
        return not db.session.execute(text("SELECT count(*) FROM course_quiz_questions WHERE question LIKE :p"),
                                      {'p': prefix + '%'}).scalar()


# ───────────── 种子题库:首访自动导入的清理 ─────────────
# 小源面板 / 题库页 / 考核接口会把 app/course_exam_seeds/ 下的种子题库导入「题库为空」的课。
# 浏览器 e2e 跑完要把本次导入的种子题删掉,pma_local 保持干净。

def empty_seed_keys(app):
    """有种子文件且当前题库为空的课(= 本次测试可能触发自动导入的课)。启动服务前调用。"""
    from app import db
    from app.models.course_exam import CourseQuizQuestion
    from app.services.course_exam import service as S
    if not os.path.isdir(S.SEED_DIR):
        return []
    keys = [f[:-5] for f in sorted(os.listdir(S.SEED_DIR)) if f.endswith('.json')]
    with app.app_context():
        have = {k for (k,) in db.session.query(CourseQuizQuestion.course_key)
                .filter(CourseQuizQuestion.course_key.in_(keys)).distinct().all()} if keys else set()
        db.session.rollback()
    return [k for k in keys if k not in have]


def delete_seed_imports(app, keys):
    """硬删 keys(测试前为空的课)本次被自动导入的题;返回是否已清空。"""
    from app import db
    from app.models.course_exam import CourseQuizQuestion
    if not keys:
        return True
    with app.app_context():
        CourseQuizQuestion.query.filter(CourseQuizQuestion.course_key.in_(keys)).delete(synchronize_session=False)
        db.session.commit()
        return not CourseQuizQuestion.query.filter(CourseQuizQuestion.course_key.in_(keys)).count()


# ───────────── 临时课程:不碰真实课程的题库 / 设置 ─────────────
# 题库类测试原先直接用真实课程 smart-task-intercom,一旦该课有真实题库(用户审过的)就断言失真。
# 改为建一门 ZZ 临时课程:课件经临时目录软链借用主仓同一份 HTML(页数 / 页名不变),
# 临时目录里同时软链主仓全部课件,其他真实课程照常可用。

TEMP_COURSE_PREFIX = 'zz-'


def _assert_temp_key(key):
    # 护栏:临时课程 key 必须带 zz- 前缀,任何删除前都校验,绝不误删真实课程
    if not isinstance(key, str) or not key.startswith(TEMP_COURSE_PREFIX) or len(key) <= len(TEMP_COURSE_PREFIX):
        raise ValueError(f'临时课程 key 必须以 {TEMP_COURSE_PREFIX} 开头: {key!r}')


def make_temp_course(app, key, title, src_key='smart-task-intercom'):
    """建临时课程目录 + interactive_courses 行;返回临时目录路径(配 drop_temp_course)。
    key 必须以 zz- 开头;中途失败会删掉已建的临时目录再抛出。"""
    _assert_temp_key(key)
    return _make_temp_course(app, key, title, src_key)


def _make_temp_course(app, key, title, src_key):
    import shutil
    import tempfile
    from app import db
    from app.models.course import InteractiveCourse
    d = tempfile.mkdtemp(prefix='zz-course-assets-')
    try:
        _fill_temp_course(app, d, key, title, src_key, db, InteractiveCourse)
    except Exception:
        shutil.rmtree(d, ignore_errors=True)       # 失败也清掉 mkdtemp(只删软链,不跟随进主仓)
        raise
    return d


def _fill_temp_course(app, d, key, title, src_key, db, InteractiveCourse):
    for name in os.listdir(MAIN_ASSETS) if os.path.isdir(MAIN_ASSETS) else []:
        os.symlink(os.path.join(MAIN_ASSETS, name), os.path.join(d, name))
    src = os.path.join(MAIN_ASSETS, src_key + '.html')
    if not os.path.isfile(src):
        raise RuntimeError('主仓课件不存在: ' + src)
    os.symlink(src, os.path.join(d, key + '.html'))
    if os.path.isdir(os.path.join(MAIN_ASSETS, src_key + '.thumbs')):
        os.symlink(os.path.join(MAIN_ASSETS, src_key + '.thumbs'), os.path.join(d, key + '.thumbs'))
    with app.app_context():
        import app.views.knowledge_wiki as KW
        n = len(KW._parse_course_pages(src))
        InteractiveCourse.query.filter_by(key=key).delete()
        db.session.add(InteractiveCourse(key=key, title=title, media_type='html', page_count=n,
                                         has_thumbs=os.path.isdir(os.path.join(d, key + '.thumbs')), cover_page=1))
        db.session.commit()


def drop_temp_course(app, key, assets_dir):
    """删临时课程行及其在培训 / 考核表里的所有行,删临时目录。返回是否干净。"""
    _assert_temp_key(key)
    import shutil
    from app import db
    from sqlalchemy import text
    with app.app_context():
        for sql in ("DELETE FROM course_quiz_questions WHERE course_key=:k",
                    "DELETE FROM course_learning_progress WHERE course_key=:k",
                    "DELETE FROM course_exam_settings WHERE course_key=:k",
                    "DELETE FROM course_access WHERE course_key=:k",
                    "DELETE FROM course_enrollments WHERE course_key=:k",
                    "DELETE FROM course_reviewers WHERE course_key=:k",
                    "DELETE FROM training_quiz_attempt WHERE course_slug=:k",
                    "DELETE FROM interactive_courses WHERE key=:k"):
            db.session.execute(text(sql), {'k': key})
        db.session.commit()
        left = db.session.execute(text("SELECT count(*) FROM interactive_courses WHERE key=:k"), {'k': key}).scalar()
    if assets_dir:
        shutil.rmtree(assets_dir, ignore_errors=True)
    return not left
