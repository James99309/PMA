#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AT 知识库内容发布 —— DG/TJ 08—2406—2022 阅读器 + 文章（中文 / 英文）。

一条命令跑完：构建阅读器 → 投放 course_assets → 登记 interactive_courses →
生成文章 markdown → 写 wiki 存储 + 建 DB 行。幂等，可重复跑。

为什么要有这个脚本：update.sh 只管代码。course_assets 不在 git（体积原因），
wiki 文章也没有批量导入的 UI —— 这两样以前靠手工 ssh/docker 拼命令，容易漏步骤、
没法复查。这里把输入（转换包源、译文、React UMD、封面）随包版本化，
在 NAS 上 checkout 出来就能复现同一份产物。

  cn  中文版：DG/TJ 08—2406—2022 全文阅读器 + 19 篇文章（topic：行业知识）
  en  英文版：Evertac 技术设计参考阅读器 + 29 篇文章（topic：Industry-Knowledge）
      ⚠️ 英文版是 DRAFT：73 处 [REF-CHECK] 尚未替换成本地标准，文章顶部带横幅

用法（在 PMA 仓库根目录，容器内或已配好 DATABASE_URL 的环境）：
  python3 deploy/knowledge-content/publish.py cn --dry-run     # 只构建，不写库
  python3 deploy/knowledge-content/publish.py cn --commit
  python3 deploy/knowledge-content/publish.py en --commit
  python3 deploy/knowledge-content/publish.py en --commit --scope personal

⚠️ 必须显式 DATABASE_URL，防止误写另一边的库。
"""
import sys, os, shutil, argparse, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, 'lib')
sys.path.insert(0, LIB)
import paths as P                                    # noqa: E402

COURSES = {
    'cn': {
        'key': 'dgtj08-2406-2022',
        'title': 'DG/TJ 08—2406—2022 专用数字无线对讲通信系统工程技术标准',
        'subtitle': '上海市工程建设规范 · 2023-05-01 施行',
        'desc': ('上海市地方标准全文交互阅读器：左侧 16 章 + 附录 A–N 目录，'
                 '支持条款号/关键词/表号检索（检索到条目一级），'
                 '15 张系统架构图与 50 张表格均为矢量重绘。'
                 '条文要点已同步拆成 19 篇 wiki 文章（topic：行业知识），可被知识库检索与 AI 问答引用。'),
        'accent': '#9c2b1f',
        'topic': '行业知识',
        'cover': 'dgtj08-2406-2022.png',
    },
    'en': {
        'key': 'twr-ibs-ref-en',
        'title': 'Two-Way Radio In-Building Systems — Evertac Technical Design Reference',
        'subtitle': '16 chapters + Appendices A–N · pending technical review',
        'desc': ('Interactive reader for the Evertac engineering design reference on two-way radio '
                 'in-building systems (DMR): full 16 chapters plus Appendices A–N — architecture, '
                 'functions, design, signal source, DAS, terminals, supporting design, EMC, safety '
                 'and earthing, installation, testing, acceptance and O&M. Clause-level search, '
                 'vector-drawn architecture diagrams. Methodology referenced from Shanghai '
                 'DG/TJ 08—2406—2022; jurisdiction-specific citations are marked [REF-CHECK] and '
                 'must be replaced with local equivalents (IMDA / MCMC, IEC / SS, SCDF / BOMBA).'),
        'accent': '#9c2b1f',
        'topic': 'Industry-Knowledge',
        'cover': 'twr-ibs-ref-en.png',
    },
}


def run(args, **kw):
    """跑 lib/ 下的子步骤。cwd 设在仓库根 —— 子脚本会 create_app()，
    在 lib/ 里跑会把 app_version.json 之类的运行期文件掉进包目录。"""
    print('   $', ' '.join(str(a) for a in args))
    args = [os.path.join(LIB, args[0])] + args[1:]
    r = subprocess.run([sys.executable] + args, cwd=P.project_root(), **kw)
    if r.returncode:
        raise SystemExit(f'❌ 步骤失败: {args}')


def build_reader(target):
    """构建单文件阅读器；返回 html 路径。"""
    os.makedirs(P.BUILD, exist_ok=True)
    key = COURSES[target]['key']
    if target == 'cn':
        # 中文：转换包原样打包（索引已在包内 content.js 里补到条目级）
        src, out = P.SRC, os.path.join(P.BUILD, 'cn')
    else:
        # 英文：先由 doc.json + translations.json 合成源包，再打包
        run(['build_en_reader.py'])
        src, out = os.path.join(P.BUILD, 'en-src'), os.path.join(P.BUILD, 'en')
    run(['build_dgtj_reader.py', src, out, '--key', key, '--no-cover'])
    html = os.path.join(out, key + '.html')
    if not os.path.isfile(html):
        raise SystemExit(f'❌ 阅读器未生成: {html}')
    return html


def place_assets(target, html):
    """投放课件 + 封面到 app/course_assets/。

    ⚠️ 容器里 /app/app 是**只读**挂载，这一步只能在宿主机做（见
    publish-on-nas.sh）。容器内跑请加 --skip-assets。
    """
    c = COURSES[target]
    dst_dir = P.COURSE_ASSETS()
    if not os.access(os.path.dirname(dst_dir), os.W_OK):
        raise SystemExit(
            f'❌ {dst_dir} 不可写（容器里 /app/app 是只读挂载）。\n'
            f'   课件请在宿主机投放，容器内本步骤加 --skip-assets 跳过；\n'
            f'   NAS 上用 deploy/knowledge-content/publish-on-nas.sh 一条命令跑完整流程。')
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy2(html, os.path.join(dst_dir, c['key'] + '.html'))
    print(f"   ✅ 课件 → app/course_assets/{c['key']}.html  ({os.path.getsize(html)//1024} KB)")

    cover = os.path.join(P.COVERS, c['cover'])
    has_thumbs = False
    if os.path.isfile(cover):
        thumbs = os.path.join(dst_dir, c['key'] + '.thumbs')
        os.makedirs(thumbs, exist_ok=True)
        shutil.copy2(cover, os.path.join(thumbs, '1.png'))
        has_thumbs = True
        print(f"   ✅ 封面 → app/course_assets/{c['key']}.thumbs/1.png")
    return has_thumbs


def register_course(target, has_thumbs):
    """登记 / 更新 interactive_courses 行。"""
    from app import create_app, db
    from app.models.course import InteractiveCourse
    from app.models.user import User
    c = COURSES[target]
    app = create_app()
    with app.app_context():
        row = InteractiveCourse.query.filter_by(key=c['key']).first()
        if not row:
            admin = User.query.filter_by(role='admin').first()
            row = InteractiveCourse(key=c['key'], owner_id=admin.id if admin else None)
            db.session.add(row)
        row.title, row.subtitle, row.desc = c['title'], c['subtitle'], c['desc']
        row.accent, row.topic = c['accent'], c['topic']
        row.page_count = 0          # 滚动长文档，不是分页 deck
        row.cover_page = 1
        row.has_thumbs = has_thumbs
        db.session.commit()
        print(f"   ✅ interactive_courses id={row.id} key={c['key']} has_thumbs={has_thumbs}")


def ingest_articles(target, commit, scope):
    flag = ['--commit'] if commit else []
    if target == 'cn':
        run(['ingest_dgtj_standard.py'] + flag + ['--scope', scope])
    else:
        run(['build_en_reference.py'])          # 先出 markdown
        run(['ingest_dgtj_en.py'] + flag + ['--scope', scope])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('target', choices=['cn', 'en'])
    ap.add_argument('--commit', action='store_true', help='真正写库（缺省只构建 + 预览）')
    ap.add_argument('--scope', default='company', choices=['personal', 'department', 'company', 'system'])
    ap.add_argument('--skip-assets', action='store_true',
                    help='跳过课件/封面投放（容器内 /app/app 只读时用，由宿主机侧投放）')
    ap.add_argument('--has-thumbs', action='store_true',
                    help='配合 --skip-assets：宿主机已放好封面，登记时置 has_thumbs=true')
    args = ap.parse_args()

    if not os.environ.get('DATABASE_URL'):
        raise SystemExit('请显式设置 DATABASE_URL，避免误写另一边的库')
    print(f"目标库: {os.environ['DATABASE_URL'].rsplit('/', 1)[-1]}  |  内容: {args.target}  |  "
          f"scope={args.scope}  |  {'写库' if args.commit else '预览(不写库)'}")

    print('\n[1/4] 构建阅读器')
    html = build_reader(args.target)

    if args.commit:
        if args.skip_assets:
            print('\n[2/4] 课件投放：--skip-assets，由宿主机侧完成')
            has_thumbs = args.has_thumbs
        else:
            print('\n[2/4] 投放课件与封面')
            has_thumbs = place_assets(args.target, html)
        print('\n[3/4] 登记课程')
        sys.path.insert(0, P.project_root())
        register_course(args.target, has_thumbs)
    else:
        print('\n[2-3/4] 预览模式：跳过投放与登记')

    print('\n[4/4] 文章入库')
    ingest_articles(args.target, args.commit, args.scope)

    key = COURSES[args.target]['key']
    print(f"\n✅ 完成。阅读器：/wiki/play/{key}    文章：/wiki/at → "
          f"{COURSES[args.target]['topic']}")
    if args.target == 'en':
        print('⚠️  英文版为 DRAFT：73 处 [REF-CHECK] 待替换成本地标准（IMDA/MCMC、IEC/SS、SCDF/BOMBA）')


if __name__ == '__main__':
    main()
