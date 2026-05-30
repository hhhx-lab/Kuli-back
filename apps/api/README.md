# Kuli API

FastAPI 后端应用，负责账号、权限、订单、附件、通知、文档知识库、小酷 Agent、健康检查和后台任务。

## 技术栈

- Python + FastAPI
- SQLAlchemy + Alembic
- SQLite local fallback / Postgres + pgvector
- Redis + Celery
- local / S3 / R2 / OSS 对象存储
- OpenAI-compatible LLM + RAG fallback

## 启动

```bash
uv sync --project apps/api
cp apps/api/.env.example apps/api/.env
PYTHONPATH=apps/api uv run --project apps/api uvicorn app.main:app --reload --reload-dir apps/api/app --reload-dir apps/api/alembic --host 0.0.0.0 --port 8000
```

## 常用命令

```bash
PYTHONPATH=apps/api uv run --project apps/api pytest apps/api/tests
PYTHONPATH=apps/api uv run --project apps/api ruff check apps/api/app apps/api/tests scripts
PYTHONPATH=apps/api uv run --project apps/api alembic -c apps/api/alembic.ini upgrade head
PYTHONPATH=apps/api uv run --project apps/api celery -A app.tasks.celery_app.celery_app worker --loglevel=INFO
```

## 关键目录

- `app/main.py`：API 路由、鉴权依赖和 DTO 输出。
- `app/models/entities.py`：SQLAlchemy models 和 seed 数据。
- `app/schemas/api.py`：OpenAPI 合同源。
- `app/notifications/`：通知事件、邮件 provider、站内通知和模板。
- `app/services/`：服务目录、订单自动化、知识检索、小酷、对象存储、健康检查和账号 token。
- `app/tasks/`：Celery worker 任务。
- `knowledge/docs/`：文档中心和小酷 RAG 的 Markdown 源。

## 发布注意

- production 必须使用 Postgres、Redis、对象存储、邮件 provider 和强 `APP_SECRET_KEY`。
- 邮箱验证和密码重置 token 只保存 hash；邮件通过 `notification_events` 统一发送。
- 修改 API 后运行 `npm run contracts:generate`，再运行 `npm run contracts:check`。
