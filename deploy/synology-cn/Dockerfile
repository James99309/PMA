# PMA 应用 Docker 镜像
# 针对中国 DS925+ 群晖 NAS 优化
# 使用国内镜像源加速构建

FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

# 设置工作目录
WORKDIR /app

# 替换 apt 为阿里云镜像源（加速中国网络下载）
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's|security.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖（WeasyPrint PDF 生成需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    pandoc \
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
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*
# 注：ffmpeg / libreoffice 不在镜像,走 Mac mini 服务（PMA_*_SERVICE_URL）

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（使用清华镜像源）
RUN pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    -r requirements.txt gunicorn

# Playwright Chromium(互动课件缩略图渲染)
# 装到全局路径 /ms-playwright,供非 root 运行用户 pma 在运行时读取;ENV 需保留到运行时
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
# PLAYWRIGHT_DOWNLOAD_HOST 仅 build 时内联(国内 CDN,避免 chromium 下载被墙);不持久化到运行时
RUN PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright \
    python -m playwright install --with-deps chromium \
    && chmod -R a+rX /ms-playwright

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
# 配置集中在 gunicorn.conf.py，包含 post_fork 钩子修复连接池共享问题
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
