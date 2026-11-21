# 12 · Delivery Plan & Risks

> Index: [README](README.md) · Depends on: [02](02-scope.md), [11](11-verification.md)

## Milestones

| Milestone | Content | Exit criterion (named artifacts) |
| :--- | :--- | :--- |
| M0 Spike & data | 1. DeepSeek through `OpenAIGenericClient` (structured-output mode, thinking off, temperature); one Chinese chunk and one English chunk with the language override applied. 2. Vision on one image. 3. Multilingual embedder and stub cross-encoder. 4. The `invalidated_by` hook and write-back visibility. 5. Two-case isolation. 6. Resume after Graphiti has committed. 7. Chinese full-text recall (default vs `cjk`). 8. Telemetry off. 9. Freeze S0–S3, write S4–S7 and Scenario B | A spike report with one section per item, plus frozen fixture sources |
| M1 Backend core | Intake (drafts, chunking, checkpoints, resume); `graph` adapter; P1–P6; supports and excerpts; decisions and undo; snapshot and revisions; SSE | Policy unit tests and adapter contract tests pass; A1–A3 and the backend part of A5 pass through the API |
| M2 Frontend core (can start in parallel on a hand-written fixture) | Canvas, layout, timeline, filters, review, path, merge, inspector | Fixture E2E passes; A4, A6 and B1–B3 pass in the UI; the frontend budgets in [10](10-non-functional.md) are met (all except Q&A) |
| M3 Q&A & acceptance | Grounded Q&A, fixture export, live checklist | A5 (adjudication), A7 and all of Scenario B pass; the Q&A latency targets are met |

## Risks

| Risk | Mitigation |
| :--- | :--- |
| A Graphiti upgrade breaks the `invalidated_by` hook or the write-back assumptions | Pin 0.31.2; isolate both in the `graph` adapter; run the contract tests before any upgrade |
| DeepSeek compatibility (structured output, vision, model ID, thinking parameter) | Run the M0 spike first; the endpoint and model are configuration only |
| Chinese extraction quality and naming drift | Template instructions, the language override and the known-alias list; dates and aliases visible in the UI and correctable through merge |
| Weak Chinese full-text or cross-lingual matching | Multilingual embedder; `cjk` analyzer if M0 shows a gain; manual merge |
| Graphiti misses or misclassifies contradictions | P5 manual conflicts; `closure_unconfirmed` review; suggestions only; everything undoable |
| Ingestion latency and cost | Staged progress; one model for Graphiti; a small model only for P2; one retry budget per chunk |
| A partial failure between Graphiti's commit and the policy | Chunk checkpoints, stable episode names, idempotent policy, resume |
| Synthetic claims about real people | `synthetic` flag propagated to facts, paths and Q&A; alias for the non-public individual |
