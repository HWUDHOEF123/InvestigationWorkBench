# 13 · Environment & Setup

> Index: [README](README.md) · Depends on: [07](07-architecture.md)

`main` provides the specification. Start implementation branches from `develop`, which includes dependency locks, `backend/.env.example`, and the environment self-check. Keep real provider keys and Neo4j credentials in the ignored local `.env`.

## Requirements

* **Python ≥ 3.11.** `backend/requirements.in` lists the top-level dependencies, and `backend/requirements.txt` is the uv-compiled lock.
  * `graphiti-core==0.31.2` is pinned exactly.
  * Its transitive stack is constrained to the versions Graphiti v0.31.2 was tested with: `openai<3`, `httpx[socks] 0.28.x`, `neo4j<7`.
  * Graphiti imports `httpx` but does not declare it, and openai 3.x no longer provides it.
  * The `[socks]` extra is needed because httpx honours `ALL_PROXY=socks5://…` from the environment.
* **Node.js ≥ 20 LTS; pnpm ≥ 9.**
* **Neo4j ≥ 5.26 Community**, installed natively with Homebrew. No Docker and no plugins.
  * Homebrew ships the calendar-versioned line, currently 2026.10.x, which is newer than 5.26.
  * Neo4j listens on `127.0.0.1` by default.
* **An OpenAI-compatible LLM endpoint.** The default is DeepSeek, with model IDs `deepseek-flash` and `deepseek-v4-pro`.
* **An OpenAI-compatible cloud embedding service** serving a multilingual model. The default is Alibaba Bailian `qwen3.7-text-embedding` (native 1024 dimensions).
  * Use the OpenAI-compatible path: `https://dashscope.aliyuncs.com/compatible-mode/v1`, or your workspace host followed by `/compatible-mode/v1`.
  * Embedded text, i.e. entity names and fact text, is sent to this provider. The UI's recipient indicator shows it.
* **Proxies.** HTTP and SOCKS proxies set in the environment (`HTTP(S)_PROXY`, `ALL_PROXY`) are honoured, and `NO_PROXY` should include `127.0.0.1` and `localhost` so that Neo4j and the API stay direct.

## Target repository layout

```text
backend/app/        api/ contracts/ intake/ graph/ overlay/ policy/ snapshot/ qa/ templates/
backend/app/config.py  settings resolution (shared by app and scripts)
backend/scripts/    bootstrap_worktree.sh · check_env.py · seed_case.py · drop_source.py · export_snapshot.py   (scenario scripts call the running API)
backend/requirements.in · requirements.txt · .env.example
frontend/src/       canvas/ timeline/ panels/ inspector/ store/ api/ (generated types) i18n/zh-CN/
fixtures/           nvidia/ rainy_manor/
docs/               requirements/ (EN, canonical) · requirements(cn).md
```

## `backend/.env`

Copy it from `backend/.env.example`. The file is git-ignored.

```ini
APP_MODE=live                          # live | fixture
API_HOST=127.0.0.1
API_PORT=8000                          # linked worktrees: set in .env.local by bootstrap_worktree.sh
FRONTEND_PORT=5173
# CASE_NAMESPACE=                      # group_id prefix; defaults to the worktree directory name
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=change_me               # the initial password set before first start
GRAPHITI_TELEMETRY_ENABLED=false       # must be set before graphiti_core is imported
SEMAPHORE_LIMIT=4                      # Graphiti's internal concurrency for LLM, embedding and search calls

# LLM (OpenAI-compatible)
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=
LLM_MODEL=deepseek-flash               # Graphiti, vision and Q&A; this model was used in M0
LLM_SMALL_MODEL=deepseek-flash         # VeriTrace P2 classification only
LLM_STRUCTURED_OUTPUT=json_object      # DeepSeek supports json_object only
LLM_PROVIDER_PROFILE=deepseek          # maps thinking levels off/low/medium/high to request params

# Embeddings (OpenAI-compatible cloud service, multilingual; changing them requires re-embedding)
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_API_KEY=
EMBEDDING_MODEL=qwen3.7-text-embedding
EMBEDDING_DIM=1024                     # must equal the model's native output dimension
```

## One-time setup

**Neo4j (macOS / Homebrew).** Set the initial password before the first start:

```bash
brew install neo4j                                         # also installs openjdk@21 and cypher-shell
neo4j-admin dbms set-initial-password '<password>'
brew services start neo4j                                  # background service; stop with: brew services stop neo4j
```

**Backend** (in `backend/`):

```bash
uv venv venv --python 3.11
VIRTUAL_ENV=venv uv pip sync requirements.txt
cp .env.example .env                                       # fill in NEO4J_PASSWORD and the two API keys
venv/bin/python scripts/check_env.py                       # checks Python, graphiti-core, Neo4j, LLM (thinking off), embeddings
```

* `check_env.py` exits with `0` only when every check passes.
* The embedding check also prints the cross-lingual similarity of `黄仁勋` vs `Jensen Huang`.
* To update dependencies: edit `requirements.in`, run `uv pip compile requirements.in -o requirements.txt --python-version 3.11`, then sync again.

## Parallel worktrees

Several git worktrees can run side by side and share one Neo4j instance and one set of secrets.

**Configuration.** `app/config.py` is used by the app and every script. It resolves settings in this order, highest priority first:

1. process environment variables;
2. `<worktree>/backend/.env.local`, holding per-worktree overrides (git-ignored);
3. `<worktree>/backend/.env`;
4. `<main worktree>/backend/.env`, holding the shared secrets. It is located through the linked worktree's `.git` file.

**Setup.** In a new worktree, run `backend/scripts/bootstrap_worktree.sh` once. It is idempotent and takes about 10 s with the uv cache. It does three things:

* creates the worktree's own `backend/venv` and syncs the lock;
* in a linked worktree, writes `.env.local` with free ports and `SEMAPHORE_LIMIT=2`. Ports start at 8001/5174; 8000/5173 belong to the main worktree.
* runs `check_env.py`.

**Isolation in the shared Neo4j.** Neo4j Community has a single user database, so isolation works at the data level:

* Every Graphiti `group_id` is `<namespace>__<case_id>`, built by `Settings.group_id()`.
  * The namespace defaults to the worktree directory name and can be overridden with `CASE_NAMESPACE`.
* Tests use unique case IDs and delete only their own `group_id`s.
* **Never** call Graphiti's `clear_data()` without `group_ids`, and never run an unscoped `MATCH (n) DETACH DELETE n`.
* Index and constraint creation is idempotent, so it is safe to run concurrently.

**Concurrency.** N worktrees running at once make N × `SEMAPHORE_LIMIT` concurrent LLM calls. Watch the provider's rate limits.

**Index readiness.** On startup, the backend builds Graphiti's indices and constraints, then waits on `CALL db.awaitIndexes()`, and only then accepts traffic.

## Running

These commands describe the planned app once its entry points are available. The current `develop` baseline supports environment setup and self-check. Frontend work can start with a hand-written snapshot following [08](08-data-contract-api.md).

**Terminal 1 — backend** (in `backend/`):

```bash
venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

For fixture mode, start the backend with `APP_MODE=fixture`. Fixture mode needs neither Neo4j nor an LLM.

**Terminal 2 — scenario scripts** (in `backend/`; the backend must be running):

```bash
venv/bin/python scripts/seed_case.py --case nvidia --through S6
venv/bin/python scripts/drop_source.py --case nvidia --source S7      # live drop
```

**Terminal 3 — frontend** (in `frontend/`):

```bash
pnpm install && pnpm dev                                    # http://127.0.0.1:5173, proxies /api to :8000
```
