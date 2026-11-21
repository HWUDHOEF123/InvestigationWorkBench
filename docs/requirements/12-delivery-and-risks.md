# 12 · Delivery Plan & Risks

> Index: [README](README.md) · Depends on: [02](02-scope.md), [11](11-verification.md)

## Milestones

| Milestone | Content | Exit criterion (named artifacts) |
| :--- | :--- | :--- |
| M0 Spike & data — **done 2026-11-21** | Provider compatibility, Chinese extraction and search, vision, case isolation, capture and write-back, crash recovery and telemetry | Integration and recovery requirements adopted, and scenario sources frozen. [07](07-architecture.md) · [F1](features/F1-source-intake.md) · [11](11-verification.md) |
| M1 Backend core | Intake (drafts, chunking, checkpoints, resume); `graph` adapter; P1–P6; supports and excerpts; decisions and undo; snapshot and revisions; SSE | Policy unit tests and adapter contract tests pass; A1–A3 and the backend part of A5 pass through the API |
| M2 Frontend core (can start in parallel on a hand-written fixture) | Canvas, layout, timeline, filters, review, path, merge, inspector | Fixture E2E passes; A4, A6 and B1–B3 pass in the UI; the frontend budgets in [10](10-non-functional.md) are met (all except Q&A) |
| M3 Q&A & acceptance | Grounded Q&A, fixture export, live checklist | A5 (adjudication), A7 and all of Scenario B pass; the Q&A latency targets are met |

## Risks

| Risk | Mitigation |
| :--- | :--- |
| A Graphiti upgrade breaks the `invalidated_by` hook or the write-back assumptions | Pin 0.31.2; isolate both in the `graph` adapter; run the contract tests before any upgrade |
| DeepSeek compatibility (structured output, vision, model ID, thinking parameters) | Verified in M0: `json_object` at every thinking level, vision with `LLM_MODEL`. Typed-attribute normalization is required (schema echo). The endpoint, model and provider profile are configuration only |
| Chinese extraction quality and naming drift | Template instructions, the language override and the known-alias list; dates and aliases visible in the UI and correctable through merge |
| Weak Chinese full-text or cross-lingual matching | Multilingual embedder; known-alias list in the extraction instructions (bare acronyms such as SAMR embed weakly); manual merge. M0 showed no gain from `cjk` |
| Graphiti misses or misclassifies contradictions | P5 manual conflicts; `closure_unconfirmed` review; suggestions only; everything undoable. Live detection varies between runs (M0), so contract tests use a scripted LLM |
| Graphiti drops a stated end (dedupe) or closes nothing (same start) | P1 stated-end capture and P3 stated ends, tier-gated, with `end_claimed` review |
| Date-only times read as UTC (an 8 h offset in Asia/Shanghai, seen in M0) | Case offset in the extraction instructions; adapter normalization; A5 pinned to the case-local instant |
| Ingestion latency and cost | Staged progress; one model for Graphiti; a small model only for P2; one retry budget per chunk |
| A partial failure between Graphiti's commit and the policy | Two-phase checkpoints (staged capture persisted before Graphiti writes), stable episode names, UUID-matched replay, idempotent policy (verified in M0) |
| Synthetic claims about real people | `synthetic` flag propagated to facts, paths and Q&A; alias for the non-public individual |
