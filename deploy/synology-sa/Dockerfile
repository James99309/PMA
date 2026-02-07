# PMA 应用 Docker 镜像
# 针对新加坡 DS925+ 群晖 NAS (PMA-SA / OVS)
# 使用标准 PyPI 源（非中国镜像）

FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Singapore

# 设置工作目录
WORKDIR /app

# 安装系统依赖（WeasyPrint PDF 生成需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    libcairo2 \
    libgirepository1.0-dev \
    gir1.2-pango-1.0 \
    fonts-noto-cjk \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（标准 PyPI 源）
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# 复制应用代码
COPY . .

# 编译翻译文件
RUN pybabel compile -d app/translations || true

# 创建存储目录
RUN mkdir -p /app/storage /app/logs

# 创建非 root 用户并设置权限
RUN useradd -m -u 1000 pma && chown -R pma:pma /app && chmod -R u+rX /app
USER pma

# 暴露端口
EXPOSE 5000

# 健康检查（启动期间给足时间加载字体和初始化数据库）
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:5000/ || exit 1

# 默认启动命令（生产环境使用 gunicorn）
# --preload: 主进程加载应用后 fork worker，节省内存
# --timeout 300: 首次启动加载 19MB CJK 字体较慢，需要充足超时
# --max-requests 500: worker 处理 500 个请求后自动重启，防止内存泄漏
# --max-requests-jitter 50: 添加随机偏移，避免所有 worker 同时重启
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "300", "--preload", "--max-requests", "500", "--max-requests-jitter", "50", "wsgi:app"]
