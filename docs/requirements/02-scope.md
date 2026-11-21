# 02 · Scope

> Index: [README](README.md) · Depends on: [01-overview](01-overview.md)

## v1 features (core loop)

| ID | Feature | Acceptance (summary) | Spec |
| :--- | :--- | :--- | :--- |
| F1 | Source intake: documents, images, analyst notes, case brief | Each kind reaches `committed` with durable progress. Images are reviewed before ingestion by default, and skipping the review is audited. A failed source can be resumed without re-running committed chunks. | [F1](features/F1-source-intake.md) |
| F2 | Graph canvas: anchored layout, filters, search, manual entity merge | New sources never move existing nodes. Merges are reversible. | [F2](features/F2-graph-canvas.md) |
| F3 | Event-time timeline | Scrubbing shows the graph at T with no server calls. Ticks adapt from minutes to years. | [F3](features/F3-timeline.md) |
| F4 | Contradiction review | P1–P4 correct Graphiti closures. The analyst adjudicates with a note, and can undo. | [F4](features/F4-contradiction-review.md) |
| F5 | Path discovery | A deterministic shortest path at T. Every hop opens its evidence. | [F5](features/F5-path-discovery.md) |
| F6 | Grounded Q&A on a selection | A streamed Chinese answer. Each judgment cites facts. Invalid, refuted and synthetic citations are flagged. | [F6](features/F6-grounded-qa.md) |

## Backlog (planned after v1)

| Item | Note |
| :--- | :--- |
| **Knowledge time** ("what did we know at date K / round 2 / chapter 5") | Graphiti's `created_at` / `expired_at` record processing time and keep no change history. This needs an IntelGraph event log stamped with each source's `received_at` or stage, plus received-order ingestion. v1 records none of this. |
| Reported-speech tier cap (a quoted character in a T1 narration counts as T3) | Needs per-support speaker attribution. In v1, enter each testimony as its own Source with a speaker. |
| Verified literal spans (character offsets checked against the source) | In v1, excerpts are located automatically and labelled as such. |
| Automatic conflict resolution by Tier 1 evidence | v1 only suggests. |
| IntelGraph contradiction scan (catching what Graphiti misses) | In v1, the analyst marks these manually (P5). Exception: ends stated by a source for an open fact are applied in v1 by P3 *stated ends* ([06](06-contradiction-policy.md)). |
| Automatic duplicate-entity queue | v1 relies on Graphiti resolution, the known-alias list and manual merge. |
| Stateful fixture API (mutations without LLM) | v1 fixture mode is read-only. |
| AI hypothesis nodes; dossier export; manual fact editing | |
| Ego-network view, k-shortest paths, server-side paths | |
| Scanned PDF (page-to-image); Docling | Reuses the image pipeline. |
| Speaker credibility statistics | |
| Validated `criminal_case` and `mystery_fiction` templates | Shipped as draft configs in v1. |
| Repeated-run statistical evaluation | |

## Exploration

* Two-axis grading: source reliability × information credibility (in the style of the NATO Admiralty code).
* Non-linear narratives (flashbacks) on story time.
* Graphiti communities for case-wide summaries.

## Non-goals

* Multi-user collaboration and authentication. v1 binds to `127.0.0.1`.
* Additional visual themes.
* Automated web collection.
* Cases above ~2,000 facts.
