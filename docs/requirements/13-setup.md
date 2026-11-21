# 13 · Environment & Setup

> Index: [README](README.md) · Depends on: [07](07-architecture.md)

## Requirements

* Python ≥ 3.11; `graphiti-core==0.31.2`, pinned in `backend/requirements.txt`.
* Node.js ≥ 20 LTS; pnpm ≥ 9.
* Neo4j ≥ 5.26 Community. No plugins are required.
* An OpenAI-compatible LLM endpoint (default: DeepSeek).
* An OpenAI-compatible embedding endpoint that serves a multilingual model.

## Repository layout

```text
backend/app/      api/ intake/ graph/ policy/ snapshot/ qa/ templates/
backend/scripts/  seed_case.py · drop_source.py · export_snapshot.py   (call the running API)
frontend/src/     canvas/ timeline/ panels/ inspector/ store/ api/ (generated types) i18n/zh-CN/
fixtures/         nvidia/ rainy_manor/
docs/             requirements/ (EN, canonical) · requirements(cn).md
docker-compose.yml
```

## `backend/.env`

```ini
APP_MODE=live                          # live | fixture
API_HOST=127.0.0.1
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password_change_me
GRAPHITI_TELEMETRY_ENABLED=false       # must be set before graphiti_core is imported
SEMAPHORE_LIMIT=4                      # Graphiti's internal concurrency for LLM, embedding and search calls

# LLM (OpenAI-compatible)
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=...
LLM_MODEL=deepseek-flash               # Graphiti, vision and Q&A; confirm the exact ID in M0
LLM_SMALL_MODEL=deepseek-flash         # IntelGraph P2 classification only
LLM_STRUCTURED_OUTPUT=json_object      # json_schema | json_object
LLM_THINKING=disabled                  # non-thinking mode; confirm the parameter in M0

# Embeddings (OpenAI-compatible, multilingual; changing them requires re-embedding)
EMBEDDING_BASE_URL=http://127.0.0.1:11434/v1
EMBEDDING_API_KEY=none
EMBEDDING_MODEL=bge-m3
EMBEDDING_DIM=1024
```

## `docker-compose.yml` (repository root)

```yaml
services:
  neo4j:
    image: neo4j:5.26-community
    container_name: intelgraph-neo4j
    ports: ["127.0.0.1:7474:7474", "127.0.0.1:7687:7687"]
    environment:
      - NEO4J_AUTH=neo4j/password_change_me
    volumes: [neo4j_data:/data]
    healthcheck:
      test: ["CMD-SHELL", "cypher-shell -u neo4j -p password_change_me 'RETURN 1' || exit 1"]
      interval: 10s
      retries: 10
volumes:
  neo4j_data:
```

* The health check only proves that Bolt is accepting connections.
* On startup, the backend first builds Graphiti's indices and constraints, then waits for the indexes to come online (`CALL db.awaitIndexes()`), and only then accepts traffic.

## Running

**Terminal 1 — infrastructure** (repository root):

```bash
docker compose up -d neo4j
```

**Terminal 2 — backend** (`backend/`):

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

For fixture mode, start the backend with `APP_MODE=fixture` instead. Neo4j and the LLM are then not needed.

**Terminal 3 — scenario scripts** (`backend/`, needs the backend running):

```bash
source venv/bin/activate
python scripts/seed_case.py --case nvidia --through S6
python scripts/drop_source.py --case nvidia --source S7   # live drop
```

**Terminal 4 — frontend** (`frontend/`):

```bash
pnpm install && pnpm dev                                    # http://127.0.0.1:5173, proxies /api to :8000
```
