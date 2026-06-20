# PMA 应用 Docker 镜像
# 针对群晖 NAS 优化

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（WeasyPrint 需要）
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
    libredwg-tools \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*
# 注：ffmpeg / libreoffice 不在镜像,走 Mac mini 服务（PMA_*_SERVICE_URL）

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# 复制应用代码
COPY . .

# 编译翻译文件
RUN pybabel compile -d app/translations || true

# 创建非 root 用户运行应用
RUN useradd -m -u 1000 pma && chown -R pma:pma /app
USER pma

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "120", "wsgi:app"]
