# 08 · Data Contract & API

> Index: [README](README.md) · Depends on: [03](03-domain-model.md), [05](05-time-and-fact-states.md), [06](06-contradiction-policy.md)

**Source of truth.** The backend's Pydantic models and OpenAPI schema. The frontend types are generated from them; the TypeScript below is illustrative.

**Field conventions:**

* Timestamps are UTC epoch milliseconds.
* Generated text (`text`, `summary`, `description_zh`) is zh-CN.
* Names, aliases, titles and verbatim text keep their original language.

## Snapshot

```ts
type ThinkingLevel = 'off' | 'low' | 'medium' | 'high';

type Snapshot = {
  case: { id: string; name: string; template: string; template_version: string; timezone: string;
          time_mode: 'absolute' | 'story'; story_anchor_ts?: number;
          settings: { thinking: { extraction: ThinkingLevel; classification: ThinkingLevel;
                                  qa_default: ThinkingLevel };        // all default 'off'
                      known_aliases: string[][] } };  // canonical name first; seeded at creation
  version: number;                                   // revision
  entities: Entity[]; facts: Fact[]; conflicts: Conflict[]; sources: Source[];
  layout: { version: number; positions: Record<string, { x: number; y: number }> };
};

type EntityType = 'Person' | 'Organization' | 'Location' | 'Object' | 'Event' | 'Concept';

type Entity = {
  id: string;                                        // canonical id
  name: string; type: EntityType; subtype?: string; unclassified: boolean;
  aliases: string[]; merged_ids: string[]; summary: string;
  first_seen_ts: number;
};

type Fact = {
  id: string; from_entity: string; to_entity: string;   // canonical ids
  relation: string; text: string; attributes: Record<string, string>;
  modality: 'stated' | 'planned' | 'denied' | 'suspected'; asserted_by?: string;
  valid_at_ts: number | null; valid_at_inferred: boolean; display_valid_at_ts: number;
  invalid_at_ts: number | null;
  best_tier: 1 | 2 | 3 | null;                        // null = only speculative support
  supports: { source_id: string; episode_id: string; tier: 1 | 2 | 3;
              speculative: boolean; synthetic: boolean;
              stated_end_ts: number | null }[];                // P1 stated end, if any
  status: 'reported' | 'corroborated' | 'disputed' | 'refuted';
  speculative: boolean; synthetic: boolean; closure_unconfirmed: boolean; end_claimed: boolean;
  conflict_ids: string[];
};

type Conflict = {
  id: string; fact_ids: [string, string];
  kind: 'disagreement' | 'contested_change'; origin: 'policy' | 'manual';
  label: 'CHANGE' | 'DISAGREE' | null;
  state: 'open' | 'resolved';
  suggestion: { fact_id: string | null; strength: 'normal' | 'strong' | null };
  resolution?: { outcome: 'a' | 'b' | 'both_partial' | 'not_conflict' | 'change_accepted' | 'change_rejected';
                 note: string; at_ts: number; decision_id: string };
  decision_ids: string[];
};

type Source = {
  id: string; kind: 'document' | 'image' | 'note'; title: string; source_type: string;
  tier: 1 | 2 | 3; speaker?: string; speculative: boolean; synthetic: boolean;
  reference_time_ts: number; url?: string;
  status: 'queued' | 'parsing' | 'extracting' | 'applying_policy' | 'committed' | 'partial' | 'failed';
  current_chunk: number; chunk_count: number; error?: string; image_ids?: string[];
};
```

## Evidence and drafts

```ts
type Evidence = {                                   // POST /cases/{id}/evidence {fact_ids}
  fact_id: string;
  supports: { source_id: string; title: string; tier: 1 | 2 | 3; reference_time_ts: number;
              speaker?: string; speculative: boolean; synthetic: boolean;
              excerpt: string; located: 'auto' | 'none';            // 'none' = whole chunk
              chunk: { index: number; start: number; end: number };  // offsets in normalized text
              image_id?: string; transcription_origin?: 'machine' | 'reviewed' }[];
}[];

type ImageDraft = {
  id: string; status: 'uploading' | 'transcribing' | 'awaiting_review' | 'failed'; expires_at_ts: number;
  images: { image_id: string; original_text: string; description_zh: string;
            detected_dates: string[]; error?: string }[];
  reviewed_text?: string;
};
```

## Endpoints (prefix `/api/v1`)

All case-scoped resources are checked against the case in the path. A mutation returns `{ version }`, the new revision.

| Method & path | Purpose |
| :--- | :--- |
| `GET /templates` | Templates and their versions |
| `GET /providers/llm` | `{model, thinking_levels: ThinkingLevel[]}`. An empty list means the provider has no thinking support, and the UI hides the selectors |
| `POST /cases` · `GET /cases/{id}` | Create or read a case. The create body accepts an optional `known_aliases` (canonical name first in each group). Extraction uses these plus the groups derived from active merges ([03](03-domain-model.md)) |
| `PUT /cases/{id}/settings` | `{thinking: {extraction, classification, qa_default}}`. Applies to jobs started afterwards and writes a decision record |
| `GET /cases/{id}/brief` · `PUT /cases/{id}/brief` | Case brief (versioned) |
| `GET /cases/{id}/snapshot` | Latest effective graph. Supports `ETag` / `If-None-Match` |
| `GET /cases/{id}/events` | SSE stream for the case (see below) |
| `POST /cases/{id}/image-drafts` | Upload sanitized images (multipart). Returns `{draft_id}` and starts transcription |
| `GET /image-drafts/{id}` · `PUT /image-drafts/{id}` | Read a draft, or save `reviewed_text` |
| `POST /image-drafts/{id}/confirm` | Source metadata, `skip_review?` → `202 {source_id}` |
| `POST /cases/{id}/sources` | Document or note (with `Idempotency-Key`) → `202 {source_id}`. Returns `409 duplicate_source` with `{existing_source_id}` if the content already exists |
| `GET /sources/{id}` · `PATCH /sources/{id}` | Read a source, or change its `tier` |
| `POST /sources/{id}/resume` | Resume a `partial` or `failed` source |
| `GET /cases/{id}/images/{image_id}` | A sanitized evidence image |
| `POST /cases/{id}/evidence` | `{fact_ids}` → `Evidence[]` (batched) |
| `POST /cases/{id}/conflicts` | P5 manual conflict `{fact_ids}` |
| `POST /conflicts/{id}/adjudicate` | P6 `{outcome \| "hold", note}` |
| `POST /facts/{id}/closure` | Resolve an unconfirmed closure `{action: "confirm" \| "revert", note?}`, or a claimed end `{action: "apply_end" \| "dismiss_end", support_id, note}` |
| `POST /cases/{id}/merges` | `{alias_id, canonical_id, canonical_name?, version}` |
| `POST /decisions/{id}/undo` | Undo any undoable decision: adjudication, closure action, tier change, merge, re-layout, settings change |
| `GET /cases/{id}/decisions` | Audit log, filterable by object and type |
| `POST /cases/{id}/qa` | Grounded Q&A (one-shot SSE response; see [F6](features/F6-grounded-qa.md)) |
| `PUT /cases/{id}/layout` | `{positions, layout_version}` |

**Errors** use the shape `{ code, message, details? }`. The codes are:

* `not_found`
* `duplicate_source`
* `stale_version`
* `invalid_state` (e.g. adjudicating a resolved conflict)
* `not_undoable`
* `fixture_read_only` (HTTP `501`)

## Case event stream

* On connect, the server sends `hello { version }`.
* Then it sends:
  * `source.progress { source_id, status, current_chunk, chunk_count, error? }`
  * `graph.changed { version }`
  * `draft.progress { draft_id, status }`
* Every event has an `id`. The server keeps a replay buffer of the last 500 events and honours `Last-Event-ID`. If the requested ID is no longer in the buffer, the server sends `resync`, and the client refetches the snapshot and every source and draft that is still in progress.
* **Client rules.**
  * Coalesce `graph.changed` events.
  * Fetch only the latest version.
  * Drop any response that is older than the version already held.
