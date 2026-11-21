# 12 · Delivery Plan & Risks

> Index: [README](README.md) · Depends on: [02](02-scope.md), [11](11-verification.md)

## Milestones

| Milestone | Content | Exit criterion (named artifacts) |
| :--- | :--- | :--- |
| M0 Spike & data — **done 2026-11-21** ([report](../spikes/m0-report.md)) | 1. DeepSeek through `OpenAIGenericClient`:
   * `json_object` mode, and thinking-level injection via the adapter;
   * JSON validity of extraction at each thinking level;
   * one Chinese chunk and one English chunk with the language override and the naming policy applied. 2. Vision on one image. 3. Multilingual embedder and stub cross-encoder. 4. The `invalidated_by` hook and write-back visibility. 5. Two-case isolation. 6. Resume after Graphiti has committed. 7. Chinese full-text recall (default vs `cjk`). 8. Telemetry off. 9. Freeze S0–S3, write S4–S7 and Scenario B | A spike report with one section per item, plus frozen fixture sources |
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
