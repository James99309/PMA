# PMA 培训模块开发文档

> 本文档定义培训模块的完整设计规范，包括数据库模型、API接口、UI界面和交互逻辑。开发时必须严格遵循本文档。

---

## 一、模块概述

### 1.1 功能描述

在"账户管理"下新增**培训中心**，提供：
- 课程分类管理（Tab选卡形式）
- 课程与章节管理（视频/PDF学习内容）
- 在线测试系统（单选/多选/判断/简答题）
- 学习进度追踪
- 积分累计系统

### 1.2 用户角色

| 角色 | 权限 |
|-----|------|
| 管理员 (admin) | 完整管理权限：创建/编辑/删除课程、评分简答题 |
| 培训负责人 | 创建/编辑课程、评分简答题 |
| 普通员工 | 浏览课程、学习、参加测试 |

### 1.3 课程结构

```
课程分类 (Category)
└── 课程 (Course)
    ├── 章节1 (Lesson) - 视频
    ├── 章节2 (Lesson) - PDF
    ├── 章节3 (Lesson) - 外部视频链接
    └── 测试 (Exam)
        ├── 单选题 (Question)
        ├── 多选题 (Question)
        ├── 判断题 (Question)
        └── 简答题 (Question)
```

---

## 二、文件目录结构

### 2.1 新建文件

```
app/
├── models/
│   └── training.py                      # 培训模块所有数据模型
│
├── views/
│   └── training.py                      # 培训模块视图和API
│
├── templates/
│   └── training/                        # 培训模块模板目录（独立）
│       ├── tw_admin_list.html           # 管理端 - 课程列表
│       ├── tw_admin_category.html       # 管理端 - 分类管理弹窗内容
│       ├── tw_admin_course_edit.html    # 管理端 - 课程编辑
│       ├── tw_admin_lesson_edit.html    # 管理端 - 章节编辑弹窗
│       ├── tw_admin_exam_edit.html      # 管理端 - 测试编辑
│       ├── tw_admin_question_edit.html  # 管理端 - 题目编辑弹窗
│       ├── tw_admin_grading.html        # 管理端 - 简答题评分
│       ├── tw_learn_index.html          # 学员端 - 学习中心首页
│       ├── tw_learn_course.html         # 学员端 - 课程详情
│       ├── tw_learn_lesson.html         # 学员端 - 章节学习页
│       ├── tw_learn_exam.html           # 学员端 - 考试页面
│       ├── tw_learn_result.html         # 学员端 - 考试结果
│       └── tw_my_progress.html          # 学员端 - 我的学习进度
│
├── static/
│   └── js/
│       └── training/                    # 培训模块JS目录（独立）
│           ├── video-player.js          # 视频播放器组件
│           ├── exam-controller.js       # 考试控制器
│           ├── question-editor.js       # 题目编辑器
│           └── course-editor.js         # 课程编辑器
```

### 2.2 需修改的现有文件

| 文件路径 | 修改内容 |
|---------|---------|
| `app/models/__init__.py` | 添加 `from .training import *` |
| `app/__init__.py` | 注册 `training_bp` 蓝图 |
| `app/templates/components/tw_sidebar.html` | 添加"培训中心"菜单项 |

---

## 三、数据库模型设计

### 3.1 完整模型定义

文件：`app/models/training.py`

```python
# -*- coding: utf-8 -*-
"""培训模块数据模型"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app import db
from app.utils import get_local_time


class TrainingCategory(db.Model):
    """课程分类表"""
    __tablename__ = 'training_categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, comment='分类名称')
    name_en = Column(String(100), comment='英文名称')
    description = Column(Text, comment='分类描述')
    icon = Column(String(50), default='school', comment='Material Symbols图标名')
    color = Column(String(20), default='blue', comment='主题色: blue/green/purple/orange')
    sort_order = Column(Integer, default=0, comment='排序顺序')

    # 系统字段
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = Column(Boolean, default=False)

    # 关系
    owner = relationship('User', foreign_keys=[owner_id])
    courses = relationship('TrainingCourse', backref='category', lazy='dynamic')

    @property
    def course_count(self):
        """获取分类下的课程数量"""
        return self.courses.filter_by(is_deleted=False).count()


class TrainingCourse(db.Model):
    """课程表"""
    __tablename__ = 'training_courses'

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('training_categories.id'), nullable=False)

    title = Column(String(200), nullable=False, comment='课程标题')
    title_en = Column(String(200), comment='英文标题')
    description = Column(Text, comment='课程描述')
    cover_image = Column(String(500), comment='封面图片URL')

    # 学习配置
    estimated_duration = Column(Integer, default=0, comment='预计学习时长(分钟)')
    points = Column(Integer, default=0, comment='完成可获积分')
    is_required = Column(Boolean, default=False, comment='是否必修')
    is_sequential = Column(Boolean, default=True, comment='是否需要按顺序学习')

    # 发布状态: draft/published/archived
    status = Column(String(20), default='draft')
    published_at = Column(DateTime, comment='发布时间')

    # 系统字段
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = Column(Boolean, default=False)

    # 关系
    owner = relationship('User', foreign_keys=[owner_id])
    lessons = relationship('TrainingLesson', backref='course', lazy='dynamic',
                          order_by='TrainingLesson.sort_order')
    exams = relationship('TrainingExam', backref='course', lazy='dynamic')

    @property
    def lesson_count(self):
        return self.lessons.filter_by(is_deleted=False).count()

    @property
    def total_duration(self):
        """计算总时长(分钟)"""
        total = 0
        for lesson in self.lessons.filter_by(is_deleted=False):
            if lesson.video_duration:
                total += lesson.video_duration // 60
        return total or self.estimated_duration


class TrainingLesson(db.Model):
    """章节表"""
    __tablename__ = 'training_lessons'

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('training_courses.id'), nullable=False)

    title = Column(String(200), nullable=False, comment='章节标题')
    title_en = Column(String(200), comment='英文标题')
    description = Column(Text, comment='章节描述')
    sort_order = Column(Integer, default=0, comment='排序顺序')

    # 内容类型: video_upload/video_link/pdf
    content_type = Column(String(20), nullable=False)

    # 视频相关
    video_url = Column(String(500), comment='视频URL(上传或外链)')
    video_platform = Column(String(20), comment='视频平台: youtube/bilibili/uploaded/other')
    video_duration = Column(Integer, comment='视频时长(秒)')
    video_storage_path = Column(String(500), comment='上传视频存储路径')

    # PDF相关
    pdf_url = Column(String(500), comment='PDF文件URL')
    pdf_storage_path = Column(String(500), comment='PDF存储路径')
    pdf_pages = Column(Integer, comment='PDF页数')

    # 系统字段
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = Column(Boolean, default=False)

    # 关系
    owner = relationship('User', foreign_keys=[owner_id])


class TrainingExam(db.Model):
    """测试表"""
    __tablename__ = 'training_exams'

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('training_courses.id'), nullable=False)

    title = Column(String(200), nullable=False, comment='测试标题')
    description = Column(Text, comment='测试说明')

    # 考试配置
    passing_score = Column(Integer, default=60, comment='及格分数')
    time_limit = Column(Integer, default=0, comment='限时(分钟), 0=不限时')
    max_attempts = Column(Integer, default=3, comment='最大尝试次数, 0=不限')
    shuffle_questions = Column(Boolean, default=True, comment='是否打乱题目顺序')
    show_answer_after = Column(Boolean, default=True, comment='交卷后显示正确答案')

    # 发布状态
    status = Column(String(20), default='draft')  # draft/published

    # 系统字段
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = Column(Boolean, default=False)

    # 关系
    owner = relationship('User', foreign_keys=[owner_id])
    questions = relationship('TrainingQuestion', backref='exam', lazy='dynamic',
                            order_by='TrainingQuestion.sort_order')

    @property
    def total_score(self):
        """计算试卷总分"""
        return sum(q.points for q in self.questions.filter_by(is_deleted=False))

    @property
    def question_count(self):
        return self.questions.filter_by(is_deleted=False).count()


class TrainingQuestion(db.Model):
    """题目表"""
    __tablename__ = 'training_questions'

    id = Column(Integer, primary_key=True)
    exam_id = Column(Integer, ForeignKey('training_exams.id'), nullable=False)

    # 题目类型: single_choice/multiple_choice/true_false/short_answer
    question_type = Column(String(20), nullable=False)

    content = Column(Text, nullable=False, comment='题目内容')

    # 选项(选择题): [{"key": "A", "text": "选项内容"}, ...]
    options = Column(JSON, comment='选项列表')

    # 正确答案
    # 单选: ["A"]
    # 多选: ["A", "C"]
    # 判断: true/false
    # 简答: null (人工评分)
    correct_answer = Column(JSON, comment='正确答案')

    points = Column(Integer, default=1, comment='分值')
    explanation = Column(Text, comment='答案解析')
    sort_order = Column(Integer, default=0, comment='排序顺序')

    # 系统字段
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = Column(Boolean, default=False)


# ============ 用户学习记录表 ============

class UserCourseProgress(db.Model):
    """用户课程学习进度"""
    __tablename__ = 'user_course_progress'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('training_courses.id'), nullable=False)

    # 进度状态: not_started/in_progress/completed
    status = Column(String(20), default='not_started')
    progress_percent = Column(Integer, default=0, comment='完成百分比 0-100')
    completed_lessons = Column(Integer, default=0, comment='已完成章节数')

    started_at = Column(DateTime, comment='开始学习时间')
    completed_at = Column(DateTime, comment='完成时间')
    last_lesson_id = Column(Integer, comment='最后学习的章节ID')

    # 已获积分
    points_earned = Column(Integer, default=0)

    # 关系
    user = relationship('User', foreign_keys=[user_id])
    course = relationship('TrainingCourse', foreign_keys=[course_id])

    __table_args__ = (
        db.UniqueConstraint('user_id', 'course_id', name='uq_user_course_progress'),
    )


class UserLessonProgress(db.Model):
    """用户章节学习进度"""
    __tablename__ = 'user_lesson_progress'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    lesson_id = Column(Integer, ForeignKey('training_lessons.id'), nullable=False)

    # 进度状态
    is_completed = Column(Boolean, default=False)
    video_position = Column(Integer, default=0, comment='视频观看位置(秒)')
    video_watched_percent = Column(Integer, default=0, comment='视频观看百分比')
    pdf_current_page = Column(Integer, default=1, comment='PDF当前页码')
    pdf_read_pages = Column(JSON, default=list, comment='已阅读的页码列表')

    last_accessed_at = Column(DateTime, comment='最后访问时间')
    completed_at = Column(DateTime, comment='完成时间')
    total_time_spent = Column(Integer, default=0, comment='总学习时长(秒)')

    # 关系
    user = relationship('User', foreign_keys=[user_id])
    lesson = relationship('TrainingLesson', foreign_keys=[lesson_id])

    __table_args__ = (
        db.UniqueConstraint('user_id', 'lesson_id', name='uq_user_lesson_progress'),
    )


class UserExamAttempt(db.Model):
    """用户考试记录"""
    __tablename__ = 'user_exam_attempts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    exam_id = Column(Integer, ForeignKey('training_exams.id'), nullable=False)
    attempt_number = Column(Integer, default=1, comment='第几次尝试')

    # 考试状态: in_progress/submitted/graded/pending_review
    status = Column(String(20), default='in_progress')

    # 成绩
    score = Column(Integer, comment='得分')
    max_score = Column(Integer, comment='满分')
    is_passed = Column(Boolean, default=False, comment='是否及格')

    # 答题数据: {"question_id": "user_answer", ...}
    answers = Column(JSON, comment='用户答案')

    # 评分详情: {"question_id": {"status": "graded", "points": 3, "is_correct": true}, ...}
    grading_details = Column(JSON, comment='评分详情')

    # 时间记录
    started_at = Column(DateTime, default=get_local_time)
    submitted_at = Column(DateTime)
    graded_at = Column(DateTime)
    graded_by = Column(Integer, ForeignKey('users.id'), comment='评分人(简答题)')

    # 关系
    user = relationship('User', foreign_keys=[user_id])
    exam = relationship('TrainingExam', foreign_keys=[exam_id])
    grader = relationship('User', foreign_keys=[graded_by])

    __table_args__ = (
        db.Index('ix_user_exam_attempt', 'user_id', 'exam_id'),
    )


class UserTrainingPoints(db.Model):
    """用户培训积分记录"""
    __tablename__ = 'user_training_points'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # 积分来源类型: course_complete/exam_pass/manual_award
    source_type = Column(String(30), nullable=False)
    source_id = Column(Integer, comment='来源ID(课程ID或考试ID)')
    source_name = Column(String(200), comment='来源名称(用于显示)')

    points = Column(Integer, nullable=False, comment='获得积分')
    description = Column(String(500), comment='描述')

    created_at = Column(DateTime, default=get_local_time)
    created_by = Column(Integer, ForeignKey('users.id'), comment='操作人(手动奖励时)')

    # 关系
    user = relationship('User', foreign_keys=[user_id])

    __table_args__ = (
        db.Index('ix_user_training_points', 'user_id', 'created_at'),
    )


# ============ 辅助函数 ============

def get_user_total_points(user_id):
    """获取用户总积分"""
    from sqlalchemy import func
    result = db.session.query(func.sum(UserTrainingPoints.points))\
        .filter(UserTrainingPoints.user_id == user_id).scalar()
    return result or 0


def get_user_course_status(user_id, course_id):
    """获取用户课程学习状态"""
    progress = UserCourseProgress.query.filter_by(
        user_id=user_id,
        course_id=course_id
    ).first()

    if not progress:
        return 'not_started', 0
    return progress.status, progress.progress_percent
```

### 3.2 表关系图

```
┌──────────────────┐
│ TrainingCategory │
│──────────────────│
│ id (PK)          │
│ name             │
│ icon             │
│ sort_order       │
└────────┬─────────┘
         │ 1:N
         ▼
┌──────────────────┐       ┌──────────────────┐
│  TrainingCourse  │──────▶│ UserCourseProgress│
│──────────────────│  1:N  │──────────────────│
│ id (PK)          │       │ user_id (FK)     │
│ category_id (FK) │       │ course_id (FK)   │
│ title            │       │ status           │
│ points           │       │ progress_percent │
│ status           │       └──────────────────┘
└────────┬─────────┘
         │ 1:N
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌─────────────┐       ┌──────────────────┐
│ Lesson  │ │ TrainingExam│──────▶│ UserExamAttempt  │
│─────────│ │─────────────│  1:N  │──────────────────│
│ id (PK) │ │ id (PK)     │       │ user_id (FK)     │
│course_id│ │ course_id   │       │ exam_id (FK)     │
│ type    │ │passing_score│       │ score            │
│video_url│ └──────┬──────┘       │ is_passed        │
│ pdf_url │        │ 1:N          └──────────────────┘
└────┬────┘        ▼
     │      ┌──────────────────┐
     │      │ TrainingQuestion │
     │      │──────────────────│
     │      │ id (PK)          │
     │      │ exam_id (FK)     │
     │      │ question_type    │
     │      │ options (JSON)   │
     │      │ correct_answer   │
     │      └──────────────────┘
     │
     ▼
┌──────────────────┐
│UserLessonProgress│
│──────────────────│
│ user_id (FK)     │
│ lesson_id (FK)   │
│ is_completed     │
│ video_position   │
└──────────────────┘
```

---

## 四、API接口设计

### 4.1 管理端API

#### 分类管理

| 方法 | 路由 | 说明 |
|-----|------|------|
| GET | `/training/admin/categories` | 获取所有分类 |
| POST | `/training/admin/api/category` | 创建分类 |
| PUT | `/training/admin/api/category/<id>` | 更新分类 |
| DELETE | `/training/admin/api/category/<id>` | 删除分类 |
| PUT | `/training/admin/api/categories/sort` | 更新分类排序 |

#### 课程管理

| 方法 | 路由 | 说明 |
|-----|------|------|
| GET | `/training/admin/courses` | 课程列表页面 |
| GET | `/training/admin/course/<id>/edit` | 课程编辑页面 |
| POST | `/training/admin/api/course` | 创建课程 |
| PUT | `/training/admin/api/course/<id>` | 更新课程 |
| DELETE | `/training/admin/api/course/<id>` | 删除课程 |
| POST | `/training/admin/api/course/<id>/publish` | 发布课程 |
| POST | `/training/admin/api/course/<id>/archive` | 归档课程 |
| POST | `/training/admin/api/course/<id>/upload-cover` | 上传封面 |

#### 章节管理

| 方法 | 路由 | 说明 |
|-----|------|------|
| POST | `/training/admin/api/lesson` | 创建章节 |
| PUT | `/training/admin/api/lesson/<id>` | 更新章节 |
| DELETE | `/training/admin/api/lesson/<id>` | 删除章节 |
| PUT | `/training/admin/api/lessons/sort` | 更新章节排序 |
| POST | `/training/admin/api/lesson/<id>/upload-video` | 上传视频 |
| POST | `/training/admin/api/lesson/<id>/upload-pdf` | 上传PDF |

#### 测试管理

| 方法 | 路由 | 说明 |
|-----|------|------|
| GET | `/training/admin/exam/<id>/edit` | 测试编辑页面 |
| POST | `/training/admin/api/exam` | 创建测试 |
| PUT | `/training/admin/api/exam/<id>` | 更新测试 |
| DELETE | `/training/admin/api/exam/<id>` | 删除测试 |

#### 题目管理

| 方法 | 路由 | 说明 |
|-----|------|------|
| POST | `/training/admin/api/question` | 添加题目 |
| PUT | `/training/admin/api/question/<id>` | 更新题目 |
| DELETE | `/training/admin/api/question/<id>` | 删除题目 |
| PUT | `/training/admin/api/questions/sort` | 更新题目排序 |

#### 简答题评分

| 方法 | 路由 | 说明 |
|-----|------|------|
| GET | `/training/admin/grading` | 待评分列表 |
| GET | `/training/admin/grading/<attempt_id>` | 评分页面 |
| POST | `/training/admin/api/grading/<attempt_id>` | 提交评分 |

### 4.2 学员端API

#### 学习中心

| 方法 | 路由 | 说明 |
|-----|------|------|
| GET | `/training/learn` | 学习中心首页 |
| GET | `/training/learn/course/<id>` | 课程详情 |
| GET | `/training/learn/lesson/<id>` | 章节学习页面 |

#### 学习进度

| 方法 | 路由 | 说明 |
|-----|------|------|
| POST | `/training/api/lesson/<id>/progress` | 更新章节进度 |
| POST | `/training/api/lesson/<id>/complete` | 完成章节 |
| GET | `/training/api/course/<id>/progress` | 获取课程进度 |

#### 考试

| 方法 | 路由 | 说明 |
|-----|------|------|
| GET | `/training/learn/exam/<id>` | 考试页面 |
| POST | `/training/api/exam/<id>/start` | 开始考试 |
| POST | `/training/api/exam/<id>/save` | 保存答案 |
| POST | `/training/api/exam/<id>/submit` | 提交考试 |
| GET | `/training/learn/result/<attempt_id>` | 查看结果 |

#### 我的学习

| 方法 | 路由 | 说明 |
|-----|------|------|
| GET | `/training/my-progress` | 我的学习进度 |
| GET | `/training/api/my-points` | 获取积分统计 |
| GET | `/training/api/my-courses` | 获取我的课程列表 |

---

## 五、UI界面设计

> 所有页面使用 **Tailwind CSS (tw_)** 风格

### 5.1 学员端 - 学习中心首页

**文件**: `tw_learn_index.html`

**布局设计**:
```
┌─────────────────────────────────────────────────────────────┐
│  学习中心                               [我的学习进度] 按钮  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┬─────────┬─────────┬─────────┐                 │
│  │ 全部(25)│产品知识(8)│销售技巧(10)│公司制度(7)│   ← Tab选卡 │
│  └─────────┴─────────┴─────────┴─────────┘                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ [封面图片] │  │ [封面图片] │  │ [封面图片] │            │
│  │            │  │            │  │            │            │
│  │ 课程名称   │  │ 课程名称   │  │ 课程名称   │            │
│  │ 8个章节    │  │ 5个章节    │  │ 3个章节    │            │
│  │ ━━━━━━━━  │  │ ━━━━━░░░░ │  │ ░░░░░░░░░ │  ← 进度条   │
│  │ 已完成100% │  │ 进度 60%  │  │ 未开始    │            │
│  │ ⭐ 必修    │  │            │  │            │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│                                                             │
│  (响应式：大屏3列，中屏2列，小屏1列)                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Tab交互**:
- 使用 `tw_tabbed_card` 组件
- 点击Tab → 筛选该分类课程（前端过滤，无需刷新）
- Tab显示各分类课程数量

**课程卡片状态**:
| 状态 | 进度条颜色 | 标签 |
|-----|----------|------|
| 未开始 | 灰色 | 无 |
| 进行中 | 蓝色 | 显示百分比 |
| 已完成 | 绿色 | "已完成" |
| 必修 | - | 红色星标 |

---

### 5.2 学员端 - 课程详情页

**文件**: `tw_learn_course.html`

**布局设计**:
```
┌─────────────────────────────────────────────────────────────┐
│  ← 返回学习中心                                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐│
│  │                   [课程封面大图]                        ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   📖 产品A完整操作指南                      ⭐ 必修课程     │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                             │
│   课程简介：本课程详细介绍产品A的所有功能和操作方法...      │
│                                                             │
│   📊 预计时长：2小时  |  🎯 可获积分：50分  |  📝 含测试   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│   章节列表                                    进度: 3/8     │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ ✅ 1. 课程介绍              📹 视频  5分钟   [已完成]   ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ ✅ 2. 基础功能操作          📹 视频  15分钟  [已完成]   ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ ▶️ 3. 高级功能详解          📹 视频  20分钟  [继续学习] ││
│  │      ━━━━━━━━━━░░░░ 进度 70%                            ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ 🔒 4. 常见问题解答          📄 PDF   10页    [未解锁]   ││
│  ├─────────────────────────────────────────────────────────┤│
│  │ 🔒 5. 实战案例分析          📹 视频  25分钟  [未解锁]   ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│   课程测试                                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 📝 产品A知识测试                                        ││
│  │ 及格分数：60分  |  限时：30分钟  |  可尝试：3次         ││
│  │ 状态：🔒 完成所有章节后解锁                             ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**章节状态图标**:
| 状态 | 图标 | 可点击 |
|-----|------|-------|
| 已完成 | ✅ | 是（可复习）|
| 进行中 | ▶️ | 是 |
| 未解锁 | 🔒 | 否 |
| 未开始 | ○ | 是（第一个）|

**交互逻辑**:
1. 按顺序学习模式：需完成前一章节才能解锁下一章
2. 自由学习模式：所有章节可自由访问
3. 测试解锁条件：完成所有章节

---

### 5.3 学员端 - 章节学习页（视频）

**文件**: `tw_learn_lesson.html`

**布局设计**:
```
┌─────────────────────────────────────────────────────────────┐
│  ← 返回课程    产品A完整操作指南 / 第3章 高级功能详解       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                                                         ││
│  │                                                         ││
│  │              [视频播放器区域]                           ││
│  │                                                         ││
│  │                 ▶️  12:35 / 20:00                       ││
│  │              ━━━━━━━━━━━░░░░░░░                         ││
│  │                                                         ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│   进度：70%  |  观看时长：14分钟                            │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│   章节导航                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  ← 上一章        │  │  下一章 →        │                │
│  │  2.基础功能操作  │  │  4.常见问题(🔒)  │                │
│  └──────────────────┘  └──────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   [标记为已完成] 按钮                                       │
│   (观看超过90%后自动完成，或手动标记)                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**视频播放器组件**:
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    视频画面区域                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  ▶️ ━━━━━━━━━━━━━━━━━░░░░░░░░░  12:35/20:00  🔊 ⛶ ⚙️      │
│     播放  进度条              时间  音量 全屏 设置          │
└─────────────────────────────────────────────────────────────┘
```

**支持的视频源**:
| 来源 | 实现方式 | 进度保存 |
|-----|---------|---------|
| 上传视频 | HTML5 `<video>` | 支持 |
| YouTube | iframe嵌入 | 不支持 |
| Bilibili | iframe嵌入 | 不支持 |
| 其他链接 | iframe/video | 视情况 |

**进度保存逻辑**:
1. 每30秒自动保存播放位置到服务器
2. 再次打开自动跳转到上次位置
3. 观看超过90%时长自动标记完成

---

### 5.4 学员端 - 章节学习页（PDF）

**布局设计**:
```
┌─────────────────────────────────────────────────────────────┐
│  ← 返回课程    公司制度 / 第2章 员工手册                    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────┐ ┌──────┐                    [下载PDF] [全屏查看]  │
│  │ ← 页 │ │ 页 → │  第 3 页 / 共 15 页     🔍 缩放: 100%   │
│  └──────┘ └──────┘                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                                                         ││
│  │                  [PDF 预览区域]                         ││
│  │                  使用 PDF.js 渲染                       ││
│  │                                                         ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
├─────────────────────────────────────────────────────────────┤
│   阅读进度：已查看 3/15 页 (20%)                            │
│                                                             │
│   [标记为已完成]                                            │
│   (查看超过80%页面后自动完成)                               │
└─────────────────────────────────────────────────────────────┘
```

**PDF预览**:
- 使用现有 `file-preview.js` + PDF.js
- 记录已阅读的页码
- 查看超过80%的页面自动完成

---

### 5.5 学员端 - 考试页面

**文件**: `tw_learn_exam.html`

**开始前**:
```
┌─────────────────────────────────────────────────────────────┐
│  📝 产品A知识测试                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   考试说明                                                  │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                             │
│   📊 题目数量：20题                                         │
│   ⏱️ 考试时间：30分钟                                       │
│   ✅ 及格分数：60分                                         │
│   🔄 剩余次数：2次（已用1次）                               │
│                                                             │
│   题型分布：                                                │
│   • 单选题：10题 (每题3分)                                  │
│   • 多选题：5题 (每题4分)                                   │
│   • 判断题：3题 (每题2分)                                   │
│   • 简答题：2题 (每题13分)                                  │
│                                                             │
│   注意事项：                                                │
│   1. 开始后请在规定时间内完成                               │
│   2. 中途离开进度会保存                                     │
│   3. 简答题需等待管理员评分                                 │
│                                                             │
│              ┌─────────────────────┐                        │
│              │    开始考试 →       │                        │
│              └─────────────────────┘                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**考试进行中**:
```
┌─────────────────────────────────────────────────────────────┐
│  📝 产品A知识测试              ⏱️ 剩余时间：25:32          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   题目 3/20                                    [提交试卷]   │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                             │
│   【单选题】(3分)                                           │
│                                                             │
│   产品A的主要功能是什么？                                   │
│                                                             │
│   ○ A. 数据分析                                            │
│   ● B. 客户管理        ← 已选择                            │
│   ○ C. 财务报表                                            │
│   ○ D. 库存管理                                            │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│   题目导航                                                  │
│   ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐              │
│   │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ 8 │ 9 │10 │              │
│   │ ✓ │ ✓ │ ● │   │   │   │   │   │   │   │              │
│   └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘              │
│                                                             │
│   ✓ = 已答  ● = 当前  空 = 未答                            │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│       [← 上一题]              [下一题 →]                    │
└─────────────────────────────────────────────────────────────┘
```

**题型UI设计**:

**单选题**:
```
【单选题】(3分)
产品A支持哪种数据库？

○ A. MySQL
● B. PostgreSQL    ← 点击选中（实心圆）
○ C. MongoDB
○ D. SQLite
```

**多选题**:
```
【多选题】(4分) — 多选题至少选2项

以下哪些是产品A的核心功能？（多选）

☑ A. 客户管理      ← checkbox 可多选
☑ B. 项目跟踪
☐ C. 视频会议
☑ D. 报价生成
```

**判断题**:
```
【判断题】(2分)

产品A支持移动端访问。

● 正确
○ 错误
```

**简答题**:
```
【简答题】(13分)

请简述产品A在客户管理方面的三个主要优势。

┌─────────────────────────────────────────────────────────┐
│  (textarea 文本输入框)                                   │
│                                                         │
│  产品A在客户管理方面有以下优势：                        │
│  1. 完整的客户信息管理...                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
字数：156/500
```

**交互逻辑**:
1. 倒计时：右上角显示，最后5分钟变红闪烁
2. 自动保存：每次选择/输入自动保存到服务器
3. 题目导航：点击题号快速跳转
4. 提交确认：检查未答题目，显示确认弹窗

---

### 5.6 学员端 - 考试结果页

**文件**: `tw_learn_result.html`

```
┌─────────────────────────────────────────────────────────────┐
│  📝 产品A知识测试 - 考试结果                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    ┌──────────────┐                        │
│                    │              │                        │
│                    │   ✅ 通过    │  (或 ❌ 未通过)        │
│                    │              │                        │
│                    │    85分      │                        │
│                    │  (满分100)   │                        │
│                    │              │                        │
│                    └──────────────┘                        │
│                                                             │
│   🎉 恭喜！你已通过测试，获得 50 积分                      │
│   (或：未通过，还剩 2 次机会)                              │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│   答题详情                                                  │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                             │
│   单选题：8/10 正确 (24/30分)                              │
│   多选题：4/5 正确 (16/20分)                               │
│   判断题：3/3 正确 (6/6分)                                 │
│   简答题：等待评分... (0/26分) ← 如有简答题               │
│                                                             │
│   ⚠️ 简答题评分后，最终成绩可能会变化                      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│   [查看答题详情]    [返回课程]    [再次测试(剩余1次)]      │
└─────────────────────────────────────────────────────────────┘
```

**答题详情展开**:
```
┌─────────────────────────────────────────────────────────────┐
│ 第1题【单选题】✅ 正确 +3分                                │
├─────────────────────────────────────────────────────────────┤
│ 产品A的主要功能是什么？                                    │
│                                                             │
│ 你的答案：B. 客户管理 ✅                                   │
│ 正确答案：B. 客户管理                                      │
├─────────────────────────────────────────────────────────────┤
│ 第2题【单选题】❌ 错误 +0分                                │
├─────────────────────────────────────────────────────────────┤
│ 产品A支持哪种数据库？                                      │
│                                                             │
│ 你的答案：A. MySQL ❌                                      │
│ 正确答案：B. PostgreSQL                                    │
│                                                             │
│ 💡 解析：产品A基于PostgreSQL数据库开发...                  │
└─────────────────────────────────────────────────────────────┘
```

---

### 5.7 学员端 - 我的学习进度

**文件**: `tw_my_progress.html`

```
┌─────────────────────────────────────────────────────────────┐
│  📊 我的学习进度                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│   │  累计积分   │  │  已完成课程  │  │  学习时长   │        │
│   │    850     │  │    12/25    │  │   28小时    │        │
│   └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│   积分记录                                    [查看全部 →]  │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                             │
│   • 2024-01-15  完成"产品A操作指南"        +50分           │
│   • 2024-01-14  通过"产品A知识测试"        +30分           │
│   • 2024-01-10  完成"销售技巧入门"         +40分           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│   学习记录                                                  │
│   ┌─────────┬─────────────┬─────────────┐                  │
│   │ 进行中(3)│ 已完成(12) │ 未开始(10) │   ← Tab切换      │
│   └─────────┴─────────────┴─────────────┘                  │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │ 📖 高级销售技巧          进度：60%     [继续学习]    │  │
│   │    最后学习：2024-01-16                              │  │
│   ├─────────────────────────────────────────────────────┤  │
│   │ 📖 客户沟通艺术          进度：30%     [继续学习]    │  │
│   │    最后学习：2024-01-15                              │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 5.8 管理端 - 课程列表

**文件**: `tw_admin_list.html`

```
┌─────────────────────────────────────────────────────────────┐
│  📚 培训课程管理                        [+ 新建课程] 按钮   │
├─────────────────────────────────────────────────────────────┤
│   ┌──────────┬──────────┬──────────┬──────────┐            │
│   │ 全部(25) │产品知识(8)│销售技巧(10)│公司制度(7)│ [⚙️管理] │
│   └──────────┴──────────┴──────────┴──────────┘            │
│                                                             │
│   筛选：[状态 ▼] [搜索框...]               [重置]          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────┬────────────────┬────────┬───────┬───────┬─────┐  │
│   │     │ 课程名称       │ 状态   │ 章节  │ 完成人数│操作 │  │
│   ├─────┼────────────────┼────────┼───────┼───────┼─────┤  │
│   │ ☐  │ 产品A操作指南  │ 已发布 │ 8章   │ 45人  │ ⋮  │  │
│   ├─────┼────────────────┼────────┼───────┼───────┼─────┤  │
│   │ ☐  │ 产品B使用手册  │ 草稿   │ 5章   │ --    │ ⋮  │  │
│   ├─────┼────────────────┼────────┼───────┼───────┼─────┤  │
│   │ ☐  │ 销售话术技巧   │ 已发布 │ 12章  │ 32人  │ ⋮  │  │
│   └─────┴────────────────┴────────┴───────┴───────┴─────┘  │
│                                                             │
│   操作菜单 (⋮)：                                           │
│   • 编辑课程                                                │
│   • 发布/取消发布                                           │
│   • 查看学习统计                                            │
│   • 删除课程                                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**分类管理弹窗** (点击⚙️管理):
```
┌─────────────────────────────────────────┐
│  课程分类管理                     [×]   │
├─────────────────────────────────────────┤
│                                         │
│   ≡ 产品知识  📦  [编辑] [删除]        │
│   ≡ 销售技巧  💼  [编辑] [删除]        │
│   ≡ 公司制度  📋  [编辑] [删除]        │
│                                         │
│   (可拖拽 ≡ 调整排序)                   │
│                                         │
│   [+ 添加分类]                          │
│                                         │
└─────────────────────────────────────────┘
```

---

### 5.9 管理端 - 课程编辑

**文件**: `tw_admin_course_edit.html`

```
┌─────────────────────────────────────────────────────────────┐
│  ← 返回列表    编辑课程：产品A操作指南     [保存] [发布]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   基本信息                                                  │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                             │
│   课程名称 *   [产品A操作指南                    ]         │
│   所属分类 *   [产品知识 ▼                       ]         │
│   课程封面     [上传图片] 或 拖拽上传                       │
│   课程简介     [多行文本框...                    ]         │
│   预计时长     [120] 分钟                                   │
│   完成积分     [50] 分                                      │
│   ☑ 设为必修课程                                            │
│   ☑ 按顺序学习（需完成前一章节才能解锁下一章）              │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│   章节管理                                    [+ 添加章节]  │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │ ≡  1. 课程介绍                📹 视频    [编辑][删除]│  │
│   ├─────────────────────────────────────────────────────┤  │
│   │ ≡  2. 基础功能操作            📹 视频    [编辑][删除]│  │
│   ├─────────────────────────────────────────────────────┤  │
│   │ ≡  3. 高级功能详解            📹 视频    [编辑][删除]│  │
│   ├─────────────────────────────────────────────────────┤  │
│   │ ≡  4. 常见问题解答            📄 PDF     [编辑][删除]│  │
│   └─────────────────────────────────────────────────────┘  │
│   (可拖拽 ≡ 调整顺序)                                      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│   课程测试                                    [+ 添加测试]  │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                             │
│   📝 产品A知识测试  |  20题  |  及格60分  [编辑测试][删除] │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**添加/编辑章节弹窗**:
```
┌─────────────────────────────────────────────┐
│  添加章节                             [×]   │
├─────────────────────────────────────────────┤
│                                             │
│   章节标题 *  [                         ]   │
│                                             │
│   内容类型 *  ○ 视频  ○ PDF文档             │
│                                             │
│   ── 视频设置 (选择视频时显示) ──────────   │
│                                             │
│   视频来源    ○ 上传视频  ○ 外部链接        │
│                                             │
│   [选择上传]                                │
│   ┌────────────────────────────────────┐   │
│   │  点击或拖拽上传视频                 │   │
│   │  支持 MP4, WebM (最大500MB)        │   │
│   └────────────────────────────────────┘   │
│                                             │
│   [选择外部链接]                            │
│   视频链接    [https://youtube.com/...  ]   │
│   自动识别：YouTube ✓                       │
│                                             │
│   ── PDF设置 (选择PDF时显示) ─────────────  │
│                                             │
│   ┌────────────────────────────────────┐   │
│   │  点击或拖拽上传PDF                  │   │
│   │  (最大50MB)                        │   │
│   └────────────────────────────────────┘   │
│                                             │
│            [取消]  [保存章节]               │
│                                             │
└─────────────────────────────────────────────┘
```

---

### 5.10 管理端 - 测试编辑

**文件**: `tw_admin_exam_edit.html`

```
┌─────────────────────────────────────────────────────────────┐
│  ← 返回课程    编辑测试：产品A知识测试          [保存测试]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   测试设置                                                  │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                             │
│   测试名称 *  [产品A知识测试                    ]          │
│   及格分数 *  [60] 分                                       │
│   考试时间    [30] 分钟 (0=不限时)                          │
│   最大尝试    [3] 次 (0=不限次)                             │
│   ☑ 随机打乱题目顺序                                        │
│   ☑ 交卷后显示正确答案                                      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│   题目管理                                    [+ 添加题目]  │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                             │
│   总分：100分  |  单选:30分  多选:20分  判断:6分  简答:44分 │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │ ≡ 1. [单选] 产品A的主要功能是什么？      3分 [⋮]   │  │
│   ├─────────────────────────────────────────────────────┤  │
│   │ ≡ 2. [单选] 产品A支持哪种数据库？        3分 [⋮]   │  │
│   ├─────────────────────────────────────────────────────┤  │
│   │ ≡ 3. [多选] 以下哪些是核心功能？         4分 [⋮]   │  │
│   ├─────────────────────────────────────────────────────┤  │
│   │ ≡ 4. [判断] 产品A支持移动端访问          2分 [⋮]   │  │
│   ├─────────────────────────────────────────────────────┤  │
│   │ ≡ 5. [简答] 请简述产品A的三个优势       13分 [⋮]   │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
│   操作 [⋮]：编辑 | 复制 | 删除                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**添加题目弹窗**:
```
┌─────────────────────────────────────────────┐
│  添加题目                             [×]   │
├─────────────────────────────────────────────┤
│                                             │
│   题目类型 *  [单选题 ▼]                    │
│              • 单选题                       │
│              • 多选题                       │
│              • 判断题                       │
│              • 简答题                       │
│                                             │
│   题目内容 *                                │
│   ┌────────────────────────────────────┐   │
│   │ 产品A的主要功能是什么？            │   │
│   └────────────────────────────────────┘   │
│                                             │
│   选项设置（单选/多选题显示）               │
│   ┌────────────────────────────────────┐   │
│   │ ○ A. [数据分析              ]  [×] │   │
│   │ ● B. [客户管理              ]  [×] │  ← 点击○设为正确答案
│   │ ○ C. [财务报表              ]  [×] │   │
│   │ ○ D. [库存管理              ]  [×] │   │
│   └────────────────────────────────────┘   │
│   [+ 添加选项]                              │
│                                             │
│   正确答案（判断题显示）                    │
│   ○ 正确  ○ 错误                            │
│                                             │
│   分值 *      [3] 分                        │
│                                             │
│   答案解析（可选）                          │
│   ┌────────────────────────────────────┐   │
│   │ 产品A的核心功能是客户管理...       │   │
│   └────────────────────────────────────┘   │
│                                             │
│            [取消]  [保存题目]               │
│                                             │
└─────────────────────────────────────────────┘
```

---

### 5.11 管理端 - 简答题评分

**文件**: `tw_admin_grading.html`

**待评分列表**:
```
┌─────────────────────────────────────────────────────────────┐
│  📝 简答题评分                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   待评分：5条                                               │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │ 张三 - 产品A知识测试                                 │  │
│   │ 提交时间：2024-01-15 14:30                          │  │
│   │ 自动评分：72/74分  |  简答题：2题待评               │  │
│   │                                     [去评分 →]      │  │
│   ├─────────────────────────────────────────────────────┤  │
│   │ 李四 - 销售技巧测试                                  │  │
│   │ 提交时间：2024-01-15 15:20                          │  │
│   │ 自动评分：45/60分  |  简答题：1题待评               │  │
│   │                                     [去评分 →]      │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**评分页面**:
```
┌─────────────────────────────────────────────────────────────┐
│  ← 返回列表    评分：张三 - 产品A知识测试                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   考生信息                                                  │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│   考生：张三  |  提交时间：2024-01-15 14:30                │
│   自动评分：72/74分  |  及格分数：60分                     │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│   待评分题目                                                │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                             │
│   题目1【简答题】(满分13分)                                │
│   ───────────────────────────────────────────────────      │
│   请简述产品A在客户管理方面的三个主要优势。                │
│                                                             │
│   考生答案：                                                │
│   ┌─────────────────────────────────────────────────────┐  │
│   │ 产品A在客户管理方面有以下优势：                      │  │
│   │ 1. 完整的客户信息管理，包括基本信息、联系人、       │  │
│   │    跟进记录等...                                     │  │
│   │ 2. 智能的客户分类功能...                             │  │
│   │ 3. 强大的数据分析能力...                             │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
│   参考答案：                                                │
│   ┌─────────────────────────────────────────────────────┐  │
│   │ 1. 统一客户信息管理  2. 智能分类  3. 数据分析       │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
│   评分：[    ] / 13分     评语：[                      ]   │
│                                                             │
│   ───────────────────────────────────────────────────      │
│                                                             │
│   题目2【简答题】(满分13分)                                │
│   ...                                                       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   最终得分：72 + [   ] = [   ] 分                          │
│                                                             │
│              [取消]              [提交评分]                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 六、交互流程

### 6.1 学习流程

```
┌──────────────┐
│  学习中心    │
│  (选择分类)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  课程详情    │
│  (选择章节)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│  章节学习    │────▶│  完成章节    │
│  (视频/PDF)  │     │  (自动/手动) │
└──────────────┘     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ 所有章节完成? │
                     └──────┬───────┘
                            │ 是
                            ▼
                     ┌──────────────┐
                     │  参加测试    │
                     │  (答题)      │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  提交试卷    │
                     │  (自动评分)  │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  查看结果    │────▶│  获得积分    │
                     │              │     │  (通过时)    │
                     └──────────────┘     └──────────────┘
```

### 6.2 管理流程

```
┌──────────────┐
│  课程列表    │
│  (Tab分类)   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  新建/编辑   │
│  课程基本信息│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  添加章节    │
│  (视频/PDF)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  添加测试    │
│  (题目)      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  发布课程    │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│  查看统计    │◀───│  评分简答题  │
│              │     │  (如有)      │
└──────────────┘     └──────────────┘
```

---

## 七、权限配置

### 7.1 权限模块注册

需要在数据库中添加 `training` 权限模块：

```sql
INSERT INTO permission_modules (
    module_id, name, name_en, icon, description,
    group_name, group_name_en, sort_order,
    supports_discount, supports_owner_change, supports_affiliation, supports_content_filter
) VALUES (
    'training',
    '培训管理',
    'Training Management',
    'school',
    '培训课程的创建、编辑、管理和学习',
    '账户管理',
    'Account',
    50,
    FALSE,
    FALSE,
    FALSE,
    FALSE
);
```

### 7.2 权限定义

| 权限 | 说明 | admin | 培训负责人 | 普通员工 |
|-----|------|-------|-----------|---------|
| `training.view` | 查看/学习课程 | ✅ | ✅ | ✅ |
| `training.create` | 创建课程 | ✅ | ✅ | ❌ |
| `training.edit` | 编辑课程 | ✅ | ✅ | ❌ |
| `training.delete` | 删除课程 | ✅ | ❌ | ❌ |
| `training.grade` | 评分简答题 | ✅ | ✅ | ❌ |

### 7.3 路由权限装饰器

```python
# 学员端 - 所有登录用户可访问
@training_bp.route('/learn')
@login_required
@permission_required('training', 'view')
def learn_index():
    pass

# 管理端 - 需要 create/edit 权限
@training_bp.route('/admin/courses')
@login_required
@permission_required('training', 'create')
def admin_courses():
    pass

# 删除 - 仅管理员
@training_bp.route('/admin/api/course/<int:id>', methods=['DELETE'])
@login_required
@permission_required('training', 'delete')
def delete_course(id):
    pass
```

---

## 八、复用现有组件

| 需求 | 复用组件 | 文件路径 |
|-----|---------|---------|
| 页面布局 | `tw_layout` | `components/tw_layout.html` |
| Tab选卡 | `tw_tabbed_card` | `components/tw_tabbed_card.html` |
| 文件上传 | `FileUploadComponent` | `static/js/file-upload-component.js` |
| PDF预览 | `file-preview` | `static/js/file-preview.js` |
| 云端存储 | `supabase_client` | `utils/supabase_client.py` |
| 数据表格 | `tw_data_table` | `components/tw_data_table.html` |
| 按钮 | `tw_buttons` | `components/tw_buttons.html` |
| 表单字段 | `tw_form_fields` | `components/tw_form_fields.html` |
| 确认弹窗 | `tw_confirm_modal` | `components/tw_confirm_modal.html` |
| 卡片 | `tw_card_shell` | `components/tw_card_shell.html` |

---

## 九、实现计划

### 阶段1：基础架构（第1-2天）

1. 创建数据模型文件 `app/models/training.py`
2. 在 `app/models/__init__.py` 中导入
3. 创建视图文件 `app/views/training.py`
4. 在 `app/__init__.py` 中注册蓝图
5. 生成数据库迁移文件
6. 添加权限模块配置

### 阶段2：管理端功能（第3-5天）

1. 分类管理（CRUD + Tab展示）
2. 课程列表页面
3. 课程编辑页面（基本信息）
4. 章节管理（CRUD + 拖拽排序）
5. 视频上传功能
6. 外部视频链接解析
7. PDF上传功能
8. 测试管理页面
9. 题目编辑器

### 阶段3：学员端功能（第6-8天）

1. 学习中心首页
2. 课程详情页
3. 章节学习页（视频）
4. 视频播放器组件
5. 章节学习页（PDF）
6. 学习进度保存
7. 考试页面
8. 自动评分逻辑
9. 考试结果页

### 阶段4：积分与评分（第9-10天）

1. 积分获取逻辑
2. 我的学习进度页
3. 简答题评分页面
4. 用户资料页积分展示

### 阶段5：测试与优化（第11-12天）

1. 功能测试
2. 国际化翻译（中英文）
3. UI细节优化
4. 性能优化

---

## 十、验证方案

### 10.1 数据库验证

```bash
# 生成迁移
flask db migrate -m "Add training module"

# 执行迁移
flask db upgrade

# 验证表创建
python -c "from app.models.training import *; print('Models loaded successfully')"
```

### 10.2 功能测试清单

**管理端**:
- [ ] 创建分类 → 分类列表显示
- [ ] 创建课程 → 课程列表显示
- [ ] 添加视频章节（上传）→ 播放正常
- [ ] 添加视频章节（YouTube链接）→ 嵌入显示
- [ ] 添加PDF章节 → 预览正常
- [ ] 创建测试 → 添加各类型题目
- [ ] 发布课程 → 学员端可见

**学员端**:
- [ ] 浏览课程列表 → Tab切换正常
- [ ] 进入课程详情 → 章节列表显示
- [ ] 学习视频章节 → 进度保存
- [ ] 学习PDF章节 → 页码记录
- [ ] 完成所有章节 → 测试解锁
- [ ] 参加测试 → 答题正常
- [ ] 提交测试 → 自动评分
- [ ] 查看结果 → 显示正确

**积分系统**:
- [ ] 完成课程 → 获得积分
- [ ] 通过测试 → 获得积分
- [ ] 我的进度页 → 积分统计正确

---

## 附录：关键代码参考

### A. 视频链接解析

```python
import re

def parse_video_url(url):
    """解析外部视频链接"""

    # YouTube
    youtube_patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)',
        r'youtube\.com/embed/([\w-]+)',
    ]
    for pattern in youtube_patterns:
        match = re.search(pattern, url)
        if match:
            return {'platform': 'youtube', 'video_id': match.group(1)}

    # Bilibili
    bilibili_patterns = [
        r'bilibili\.com/video/(BV[\w]+)',
        r'b23\.tv/(BV[\w]+)',
    ]
    for pattern in bilibili_patterns:
        match = re.search(pattern, url)
        if match:
            return {'platform': 'bilibili', 'video_id': match.group(1)}

    return {'platform': 'other', 'video_id': None}
```

### B. 考试自动评分

```python
def auto_grade_exam(attempt):
    """自动评分选择题和判断题"""
    exam = attempt.exam
    questions = exam.questions.filter_by(is_deleted=False).all()
    answers = attempt.answers or {}

    total_score = 0
    max_score = 0
    grading_details = {}
    has_short_answer = False

    for question in questions:
        max_score += question.points
        q_id = str(question.id)
        user_answer = answers.get(q_id)

        if question.question_type == 'short_answer':
            has_short_answer = True
            grading_details[q_id] = {
                'status': 'pending',
                'points': 0
            }
        else:
            is_correct = check_answer(question, user_answer)
            earned = question.points if is_correct else 0
            total_score += earned
            grading_details[q_id] = {
                'status': 'graded',
                'is_correct': is_correct,
                'points': earned
            }

    attempt.score = total_score
    attempt.max_score = max_score
    attempt.grading_details = grading_details
    attempt.status = 'pending_review' if has_short_answer else 'graded'

    if not has_short_answer:
        attempt.is_passed = total_score >= exam.passing_score
        attempt.graded_at = get_local_time()

    return attempt


def check_answer(question, user_answer):
    """检查答案是否正确"""
    correct = question.correct_answer

    if question.question_type == 'true_false':
        return user_answer == correct

    if question.question_type == 'single_choice':
        return user_answer == (correct[0] if correct else None)

    if question.question_type == 'multiple_choice':
        if not user_answer or not correct:
            return False
        return set(user_answer) == set(correct)

    return False
```

---

**文档版本**: 1.0
**创建日期**: 2024-01-XX
**最后更新**: 2024-01-XX
