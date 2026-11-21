#!/usr/bin/env bash
# Prepare the backend in the current git worktree (main or linked). Idempotent.
#   - creates backend/venv and syncs the locked dependencies (uv cache makes this fast)
#   - linked worktrees: writes backend/.env.local with free ports and lower LLM concurrency;
#     secrets are read from the main worktree's backend/.env (see app/config.py)
#   - runs the environment self-check
# Usage: backend/scripts/bootstrap_worktree.sh
set -euo pipefail
cd "$(dirname "$0")/.."

uv venv venv --python 3.11 --allow-existing -q
VIRTUAL_ENV=venv uv pip sync requirements.txt -q

if [ -f ../.git ] && [ ! -f .env.local ]; then
  used=" 0 "  # offset 0 (8000/5173) is reserved for the main worktree
  while read -r line; do
    wt=${line#worktree }
    f="$wt/backend/.env.local"
    [ -f "$f" ] && used+=" $(sed -n 's/^API_PORT=\([0-9]*\).*/\1/p' "$f" | awk '{print $1-8000}') "
  done < <(git worktree list --porcelain | grep '^worktree ')
  for off in $(seq 1 99); do
    api=$((8000 + off)); fe=$((5173 + off))
    [[ $used == *" $off "* ]] && continue
    lsof -nP -iTCP:"$api" -sTCP:LISTEN >/dev/null 2>&1 && continue
    lsof -nP -iTCP:"$fe" -sTCP:LISTEN >/dev/null 2>&1 && continue
    break
  done
  cat > .env.local <<EOF
# Per-worktree overrides (git-ignored). Secrets come from the main worktree's backend/.env.
API_PORT=$api
FRONTEND_PORT=$fe
SEMAPHORE_LIMIT=2
EOF
  echo "wrote backend/.env.local (API_PORT=$api FRONTEND_PORT=$fe)"
fi

venv/bin/python scripts/check_env.py
