"""announcements 加横幅跳转地址,去掉从未生效的定时发布

仪表盘顶部通栏改为轮播多条通知,内容来自公告系统:公告一经发布就会出现在
横幅上,撤回即下架 —— 不另设"要不要上横幅"的开关(加过一个勾选框,实测两次
都栽在没人记得去勾上)。所以只需要一列:

  banner_link  点击跳转地址;为空 = 纯告知,渲染成不可点的文字

同时删掉 scheduled_time:这一列全仓库只写不读,没有任何定时任务会去扫它,
填了时间照样立即发布,是个纯误导的表单项。删前核对过两台生产(CN/SG)都是
0 行填过值,不存在数据丢失。

幂等:两条 DDL 都带 IF (NOT) EXISTS,重复跑不报错。

Revision ID: announcement_banner_20260913
Revises: course_cover_url_20260730
Create Date: 2026-09-13
"""
from alembic import op


revision = 'announcement_banner_20260913'
down_revision = 'course_cover_url_20260730'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE announcements ADD COLUMN IF NOT EXISTS banner_link VARCHAR(500)")
    op.execute("ALTER TABLE announcements DROP COLUMN IF EXISTS scheduled_time")


def downgrade():
    op.execute("ALTER TABLE announcements ADD COLUMN IF NOT EXISTS scheduled_time TIMESTAMP")
    op.execute("ALTER TABLE announcements DROP COLUMN IF EXISTS banner_link")
