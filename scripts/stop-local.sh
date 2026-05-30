#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-kuli-order-system}"
API_SESSION="${KULI_API_SESSION:-kuli-api}"
WEB_SESSION="${KULI_WEB_SESSION:-kuli-web}"
WORKER_SESSION="${KULI_WORKER_SESSION:-kuli-worker}"
KEEP_STACK=false

for arg in "$@"; do
  case "$arg" in
    --keep-stack)
      KEEP_STACK=true
      ;;
    *)
      printf "未知参数：%s\n" "$arg" >&2
      exit 1
      ;;
  esac
done

log() {
  printf "\033[1;36m[酷里停止]\033[0m %s\n" "$1"
}

for session in "$API_SESSION" "$WEB_SESSION" "$WORKER_SESSION"; do
  if tmux has-session -t "$session" >/dev/null 2>&1; then
    tmux kill-session -t "$session"
    log "已停止 tmux session：${session}"
  fi
done

if [ "$KEEP_STACK" = false ]; then
  npm run stack:down
else
  log "保留 Postgres/Redis 容器"
fi

log "完成"
