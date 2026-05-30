#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-kuli-order-system}"
LOCAL_DB_NAME="${KULI_LOCAL_DB_NAME:-kuli_runtime}"
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8000}"
WEB_HOST="${WEB_HOST:-0.0.0.0}"
WEB_PORT="${WEB_PORT:-3000}"
API_BASE_URL="${NUXT_PUBLIC_API_BASE_URL:-http://127.0.0.1:${API_PORT}}"
SITE_URL="${NUXT_PUBLIC_SITE_URL:-http://127.0.0.1:${WEB_PORT}}"

API_SESSION="${KULI_API_SESSION:-kuli-api}"
WEB_SESSION="${KULI_WEB_SESSION:-kuli-web}"
WORKER_SESSION="${KULI_WORKER_SESSION:-kuli-worker}"

DATABASE_URL="${KULI_DATABASE_URL:-postgresql+psycopg://kuli:kuli@localhost:5432/${LOCAL_DB_NAME}}"
REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"

log() {
  printf "\033[1;36m[酷里启动]\033[0m %s\n" "$1"
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf "缺少命令：%s\n" "$1" >&2
    exit 1
  fi
}

copy_env_if_missing() {
  local source_file="$1"
  local target_file="$2"
  if [ ! -f "$target_file" ]; then
    cp "$source_file" "$target_file"
    log "已创建 ${target_file}"
  fi
}

wait_for_http() {
  local url="$1"
  local name="$2"
  local attempts="${3:-60}"
  for _ in $(seq 1 "$attempts"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      log "${name} 已就绪：${url}"
      return 0
    fi
    sleep 1
  done
  printf "%s 启动超时：%s\n" "$name" "$url" >&2
  exit 1
}

wait_for_compose_service() {
  local service="$1"
  local attempts="${2:-60}"
  for _ in $(seq 1 "$attempts"); do
    local status
    status="$(docker compose -p "$COMPOSE_PROJECT_NAME" ps "$service" --format '{{.Health}}' 2>/dev/null || true)"
    if [ "$status" = "healthy" ] || [ "$status" = "" ]; then
      log "${service} 已就绪"
      return 0
    fi
    sleep 1
  done
  docker compose -p "$COMPOSE_PROJECT_NAME" ps
  printf "%s 健康检查超时\n" "$service" >&2
  exit 1
}

kill_tmux_session() {
  local session="$1"
  tmux kill-session -t "$session" >/dev/null 2>&1 || true
}

start_tmux_session() {
  local session="$1"
  local workdir="$2"
  local command="$3"
  kill_tmux_session "$session"
  tmux new-session -d -s "$session" -c "$workdir" "$command"
  log "已启动 tmux session：${session}"
}

require_command npm
require_command uv
require_command docker
require_command tmux
require_command curl

copy_env_if_missing ".env.example" ".env"
copy_env_if_missing "apps/api/.env.example" "apps/api/.env"
copy_env_if_missing "apps/web/.env.example" "apps/web/.env"

log "安装 Node 依赖"
npm install

log "同步 Python 依赖"
uv sync --project apps/api

log "启动 Postgres/pgvector 与 Redis"
docker compose -p "$COMPOSE_PROJECT_NAME" up -d postgres redis
wait_for_compose_service postgres
wait_for_compose_service redis

log "确保本地数据库存在：${LOCAL_DB_NAME}"
docker exec "${COMPOSE_PROJECT_NAME}-postgres-1" createdb -U kuli "$LOCAL_DB_NAME" >/dev/null 2>&1 || true

log "运行 Alembic migration"
DATABASE_URL="$DATABASE_URL" REDIS_URL="$REDIS_URL" npm run db:migrate

log "索引文档中心知识库"
DATABASE_URL="$DATABASE_URL" REDIS_URL="$REDIS_URL" PYTHONPATH=apps/api uv run --project apps/api python scripts/index_knowledge.py

log "检查知识库健康"
DATABASE_URL="$DATABASE_URL" REDIS_URL="$REDIS_URL" PYTHONPATH=apps/api uv run --project apps/api python scripts/knowledge_doctor.py

log "构建 Nuxt 前端"
NUXT_PUBLIC_API_BASE_URL="$API_BASE_URL" NUXT_PUBLIC_SITE_URL="$SITE_URL" npm run build

start_tmux_session "$API_SESSION" "$ROOT_DIR" \
  "DATABASE_URL='$DATABASE_URL' REDIS_URL='$REDIS_URL' PYTHONPATH=apps/api uv run --project apps/api uvicorn app.main:app --host '$API_HOST' --port '$API_PORT'"

start_tmux_session "$WORKER_SESSION" "$ROOT_DIR" \
  "DATABASE_URL='$DATABASE_URL' REDIS_URL='$REDIS_URL' PYTHONPATH=apps/api uv run --project apps/api celery -A app.tasks.celery_app.celery_app worker --loglevel=INFO"

start_tmux_session "$WEB_SESSION" "$ROOT_DIR/apps/web" \
  "HOST='$WEB_HOST' PORT='$WEB_PORT' NITRO_HOST='$WEB_HOST' NITRO_PORT='$WEB_PORT' NUXT_PUBLIC_API_BASE_URL='$API_BASE_URL' NUXT_PUBLIC_SITE_URL='$SITE_URL' node .output/server/index.mjs"

wait_for_http "http://127.0.0.1:${API_PORT}/api/health" "FastAPI"
wait_for_http "http://127.0.0.1:${WEB_PORT}" "Nuxt Web"

log "启动完成"
printf "\n访问地址：\n"
printf "  Web:  http://127.0.0.1:%s\n" "$WEB_PORT"
printf "  API:  http://127.0.0.1:%s/api/health\n" "$API_PORT"
printf "  Deps: http://127.0.0.1:%s/api/health/deps\n" "$API_PORT"
printf "\n查看日志：\n"
printf "  tmux attach -t %s\n" "$API_SESSION"
printf "  tmux attach -t %s\n" "$WEB_SESSION"
printf "  tmux attach -t %s\n" "$WORKER_SESSION"
printf "\n停止服务：npm run stop:local\n"
