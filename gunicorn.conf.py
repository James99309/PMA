# Gunicorn 生产环境配置
# 解决 --preload + fork 导致的数据库连接池共享问题

bind = "0.0.0.0:5000"
workers = 2
threads = 4
worker_class = "gthread"
timeout = 300
preload_app = True
max_requests = 500
max_requests_jitter = 50


def post_fork(server, worker):
    """
    worker fork 后立即清理从父进程继承的数据库连接。

    --preload 模式下，SQLAlchemy Engine 在 fork 前创建，
    子进程会继承父进程的 socket fd，导致多个 worker 共享同一条 TCP 连接。
    dispose() 关闭继承的连接，让每个 worker 按需重建自己的独立连接。
    """
    try:
        from wsgi import app
        with app.app_context():
            from app import db
            db.engine.dispose()
        server.log.info("Worker %s: disposed inherited DB connection pool", worker.pid)
    except Exception as e:
        server.log.warning("Worker %s: dispose failed: %s", worker.pid, e)
