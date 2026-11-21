# F6 · Grounded Q&A on a Selection

> Index: [README](../README.md) · Depends on: [05](../05-time-and-fact-states.md), [08](../08-data-contract-api.md)

## Request

`POST /cases/{id}/qa` with body:

```json
{
  "entity_ids": [],
  "as_of_ts": 0,
  "snapshot_version": 0,
  "question": "",
  "options": { "include_history": true, "include_speculative": false }
}
```

* `entity_ids`: 1–8 entities.
* `question`: optional. The default question is "梳理这些实体之间的关系、最有依据的结论、矛盾与信息缺口".
* If `snapshot_version` is no longer cached, the server returns `409 stale_version`. The client then refetches the snapshot and resubmits.

## Context assembly

Context is assembled deterministically from the cached snapshot of that version.

* **Scope.** The selected entities, the facts among them, and their 1-hop facts, all eligible at `as_of_ts`.
  * Historical facts are labelled 历史.
  * Refuted facts are labelled 已驳斥.
  * Speculative facts are included only if `include_speculative` is true, and are then labelled 推测.
  * Synthetic facts are labelled 推演.
* **Ranking.** Facts among the selection, then disputed facts, then better tier, then later `valid_at`, then `fact_id`.
* **Limits.**
  * At most 60 facts and about 12k tokens of context.
  * Each excerpt is ≤ 300 characters, fetched in one batched query.
* **IDs.** Citation IDs are scoped to the request: `[F1]…[Fn]` for facts and `[S1]…` for sources. They map to real IDs in the `context` event.
* **System prompt.**
  * The case brief is included.
  * Source text is wrapped as quoted data: instructions inside sources are ignored.
  * The model runs in non-thinking mode.

## Answer grammar

Chinese Markdown with fixed sections: `## 关键判断`, `## 证据`, `## 矛盾`, `## 信息缺口`.

Under 关键判断, write one judgment per list item, ending with citations and confidence, for example: `…[F3][F7]（置信度：中）`.

Confidence levels:

| Level | Meaning |
| :--- | :--- |
| 高 | Several independent corroborated supports, and no open conflict. |
| 中 | Supported, but by a single source or with a dispute. |
| 低 | Thin or indirect evidence. |

## Stream

SSE over `text/event-stream`, UTF-8. Each event has an `event:` line and a JSON `data:` line. The client reads it with fetch streaming plus an `AbortController`.

| Event | Contents |
| :--- | :--- |
| `context` | `{id_map, fact_ids}`. The canvas highlights these facts immediately. |
| `token` | `{text}` |
| `citations` | Per judgment: unknown IDs, missing citations, citations to refuted facts, and synthetic support. The UI marks each case as 缺乏依据 / 引用已驳斥事实 / 含推演. |
| `done` or `error` | Terminal. Exactly one is sent. |

* When the client disconnects or cancels, the upstream LLM request is aborted.
* There is no automatic resubmit.
* Heartbeat comments are sent every 15 s.

**Semantic support is not machine-verified.** A correct ID can still be cited for a claim it does not support, and the UI says so.

## Output handling

* Answers live in the inspector, with a copy button.
* Copied text keeps the 推演 / 已驳斥 markers.
* Answers are session-only and are never written to the graph.
* *存为笔记* opens the F1 note form prefilled with `reference_time = as_of_ts` and `speculative = true`, which cannot be unchecked.

## Budget

* `context` event ≤ 300 ms after the request.
* Log context-to-first-token latency and total latency, together with the provider, model and thinking setting. Target: p50 first token ≤ 2 s on the M3 prompt set.
