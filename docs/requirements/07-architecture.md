# 07 · Architecture

> Index: [README](README.md) · Depends on: [03](03-domain-model.md), [06](06-contradiction-policy.md) · Related: [08](08-data-contract-api.md), [13](13-setup.md)

```mermaid
graph TD
    subgraph FE["Frontend — React + @xyflow/react + Zustand (zh-CN UI)"]
        UI["Canvas · Timeline · Sources · Review · Inspector"]
        Store["Zustand Store: snapshot (per revision) + view state"]
        UI --- Store
    end

    subgraph BE["Backend — FastAPI"]
        API["REST + SSE"]
        Intake["intake: drafts · normalize · chunk · checkpoint queue"]
        Graph["graph: Graphiti adapter (only Graphiti importer)<br/>invalidated_by hook · write-back"]
        Policy["policy: P1–P6 · supports · decisions"]
        Snap["snapshot: effective graph per revision (cached)"]
        QA["qa: context assembly · streaming · citation check"]
        Tpl["templates: Pydantic registry"]
    end

    LLM["OpenAI-compatible LLM endpoint<br/>(default DeepSeek; thinking level per case / question)"]
    EMB["OpenAI-compatible embedding endpoint<br/>(multilingual, pinned dimension)"]
    Neo4j[("Neo4j ≥ 5.26<br/>Graphiti graph + IG_* nodes")]
    Files[("Local files: sanitized images, normalized source text")]

    Store -->|"GET snapshot · POST actions"| API
    API -->|"SSE: hello · source.progress · graph.changed"| Store
    API --> Intake
    API --> QA
    Intake --> Files
    Intake -->|"vision"| LLM
    Intake --> Graph
    Graph --> Policy
    Policy --> Graph
    Policy --> Snap
    Snap --> QA
    Graph <--> Neo4j
    Policy <--> Neo4j
    Snap <--> Neo4j
    Graph --> LLM
    Graph --> EMB
    Policy --> LLM
    Policy --> EMB
    QA --> LLM
    Tpl -.-> Graph
    Tpl -.-> Policy
```

## Module boundaries

| Module | Responsibility | Must not |
| :--- | :--- | :--- |
| `graph` | The only module importing `graphiti_core`. Builds clients, calls `add_episode`, runs the `invalidated_by` hook and write-back, and reads raw graph data | Hold policy logic |
| `intake` | Drafts, normalization, chunking, checkpoints, the per-case FIFO worker | Call Graphiti directly |
| `policy` | P1–P6, supports and excerpt location, decisions, undo | Import Graphiti types |
| `snapshot` | Builds and caches the effective graph per revision; publishes `graph.changed` | Write data |
| `qa` | Context assembly from the cached snapshot, streaming, citation checks | Query Graphiti search |
| `templates` | Pydantic template schema and registry | Contain executable logic |
| `overlay` | Repositories for the `IG_*` nodes: Cypher reads and writes, transactions, case scoping, stable keys | Contain business logic |
| `contracts` | Shared Pydantic models: API shapes (08), SSE payloads, errors, and the capture DTOs between `graph` and `policy` | Contain logic; import `graphiti_core` |
| `api` | FastAPI routes; the source of the OpenAPI schema | Contain business logic |

**Shared contract.** The frontend types are generated from the backend's OpenAPI schema. SSE payloads use one shared schema module.

## Key decisions

| Decision | Rationale |
| :--- | :--- |
| Single store: Neo4j ≥ 5.26, **no APOC** | Graphiti does not support Postgres. The pinned Graphiti code path makes no APOC calls. |
| Graphiti's default vector search (cosine similarity over stored embeddings), with no vector-index setup | This is what 0.31.2 does. The embedding model and dimension are pinned per database, and changing either requires re-embedding. |
| `graphiti-core==0.31.2` pinned behind the `graph` adapter | The `invalidated_by` hook and write-back depend on internals. Contract tests guard upgrades. |
| One ingestion worker, one chunk at a time | Graphiti expects sequential `add_episode` calls per graph. Serial processing makes P1 capture and write-back race-free. |
| A revision is published after each chunk's policy, and after each analyst mutation | Clients never see raw Graphiti changes before the policy has run. |
| `graph.changed {version}` plus a snapshot refetch, instead of graph deltas | A local snapshot is ≤ 1 MB. This avoids a delta reducer, tombstones and replay logic. Typed deltas are a measured optimization for later. |
| Snapshot cached per revision; Q&A reads the same cache | No duplicate graph reads; Q&A context is consistent with what the analyst sees. |
| Timeline and paths run in the frontend | The case fits in memory, and both use the same time semantics. |
| Vision runs before Graphiti | Graphiti's ingestion API is text-only. |

## Integration notes (verified in M0; see the [spike report](../spikes/m0-report.md))

* **Graphiti LLM.** Configure it as follows:

  ```python
  OpenAIGenericClient(
      config=LLMConfig(api_key=…, base_url=…, model=…),
      structured_output_mode="json_object",
  )
  ```

  * **`json_object` is required.** DeepSeek's Chat Completions API supports only `text` and `json_object`; there is no `json_schema`.
  * **Graphiti uses one model.** This client does not route requests to `small_model`.
  * IntelGraph's own calls go through the OpenAI SDK; P2 classification may use `LLM_SMALL_MODEL`.
  * **Typed-attribute normalization is mandatory.** In `json_object` mode, Graphiti pastes the raw JSON Schema into the prompt. DeepSeek then often wraps attribute values in `properties` (or `attributes`, or the type name). Graphiti keeps undeclared keys, so the nested map reaches Neo4j and the whole episode rolls back.
    * The adapter's `generate_response` override unwraps one such level for attribute-extraction calls.
    * It keeps only declared fields that pass strict validation.
    * It logs every unwrap and every dropped key.
  * **Done means committed.** A successful extraction is a committed episode, not just a parseable JSON response.
* **Thinking levels.** DeepSeek enables thinking by default (effort `high`), so every call must state a level explicitly.
  * The backend's **provider profile** (`LLM_PROVIDER_PROFILE`) maps each level to request parameters. The DeepSeek profile is:

    | Level | Request parameter |
    | :--- | :--- |
    | `off` | `extra_body={"thinking": {"type": "disabled"}}` |
    | `low` / `medium` / `high` | `extra_body={"reasoning_effort": <level>}` |

    All of these were accepted during environment setup.
  * A profile can declare that it has no thinking support. The UI then hides the selectors.
  * Graphiti's `OpenAIGenericClient` sends neither parameter. The adapter subclasses it and injects `extra_body` from the running job's extraction level.
  * In thinking mode the provider ignores `temperature`, so results vary more.
  * Extraction under any level other than `off` must keep producing valid `json_object` output. This is verified per level in M0.
  * Vision transcription always runs with `off`.
* **Language.** Graphiti appends a "use the same language as the source" instruction: the module-level `get_extraction_language_instruction`, called from `openai_generic_client.py`. The adapter replaces that suffix at request time through a per-instance SDK hook, so that fact text and summaries are zh-CN while entity names keep their native form.
  * The hook raises if the suffix no longer matches, so a Graphiti upgrade fails loudly.
* **Naming and time instructions.** Every `add_episode` passes the template's extraction instructions as `custom_extraction_instructions` ([03](03-domain-model.md)):
  * the naming policy, plus the case's known-alias list;
  * the case's UTC offset.

  Without the known aliases, 黄仁勋 and Jensen Huang became two nodes in M0. With them, there were no duplicates and the aliases persisted.
* **Time normalization.** Date-only values are normalized to case-local midnight before Graphiti resolves the fact ([05](05-time-and-fact-states.md)). A contract fixture checks one English day-only date and one Chinese local clock time.
* **Capture hook placement.**
  * The adapter patches `graphiti_core.graphiti.resolve_extracted_edges` around one serialized `add_episode`.
  * Inside that call it observes `_apply_temporal_invalidation` (for self-closure) and the per-edge dedupe (for stated ends).
  * It persists the staged checkpoint before Graphiti writes.
  * Write-back is one scoped Cypher statement that sets only `invalid_at` and `expired_at` on `RELATES_TO {uuid, group_id}` and returns the before/after values.
* **Embedder.** Use `OpenAIEmbedder` against a multilingual endpoint. The default is Alibaba Bailian `qwen3.7-text-embedding`, at 1024 dimensions, served on the OpenAI-compatible path `/compatible-mode/v1` (not DashScope's native `/api/v1`).
  * Graphiti does not send a `dimensions` argument; it truncates vectors to `EMBEDDING_DIM`. The model's **native** output dimension must therefore equal `EMBEDDING_DIM`.
  * Pin both the model and the dimension.
* **Cross-encoder.** Inject an order-preserving stub that implements `CrossEncoderClient`. This means no OpenAI key is needed. IntelGraph does not use Graphiti's search scoring. `Graphiti.search()` never calls the stub, so the smoke test uses `search_()` with a cross-encoder recipe.
* **Excerpt location.** After each chunk, `policy` embeds the chunk's sentences once. For each new support, the sentence nearest to the fact text becomes the excerpt (`located: "auto"`). If no sentence passes the threshold, the whole chunk is used (`located: "none"`). No LLM call is involved.
* **Full-text search.** Keep Graphiti's default analyzer. In M0, `cjk` gave identical recall@10 and MRR on 30 Chinese queries and only narrowed the candidates. The named indexes are never altered: they are created `IF NOT EXISTS`, and the Neo4j instance is shared.
* **Telemetry.** Graphiti telemetry is on by default. Set `GRAPHITI_TELEMETRY_ENABLED=false` before Graphiti is imported. Run the acceptance check in a normal process: Graphiti forces telemetry off under pytest, which would mask a missing setting.
* **Case isolation.** Every adapter call passes `group_id` explicitly, and the adapter rejects any call without one. Every API resource is scoped to and checked against its case.
  * Graphiti treats an omitted scope differently by operation. `add_episode` writes to the default group `''`. `search` reads **all** groups, including for `[]` and `[""]`.
  * Full-text filtering is a tokenized phrase match on `group_id`, followed by an exact Cypher filter. A group ID whose tokens extend another's (`…-x` vs `…-x-2`) cannot leak, but it can crowd the other's candidate limit.
  * Case IDs therefore use a fixed-length token such as `uuid4().hex`. Any adapter-owned query applies its result limit after the exact group filter.
* **Vision.** Call it directly through the OpenAI SDK, with one request per draft: `image_url` base64 parts, `json_object`, temperature 0, thinking `off`. M0 transcribed 3/3 images verbatim with `LLM_MODEL`.
  * The provider rejects the **whole** request when any image is invalid, with a 400 that names `content[i]`. Each sanitized image is therefore validated before sending. On such a 400 the named image is marked failed and the others are re-sent without it ([04](04-sources-and-tiers.md)).

## Run modes

| Mode | Behaviour | Purpose |
| :--- | :--- | :--- |
| `live` | Full pipeline | Real use |
| `fixture` | **Read-only.** Serves frozen snapshots and evidence from `fixtures/`, plus a scripted `source.progress` / `graph.changed` sequence and recorded Q&A streams. Mutation endpoints return `501`, and the UI disables them. No Neo4j or LLM is needed. | Frontend development, read-path E2E tests, reliable demos |
