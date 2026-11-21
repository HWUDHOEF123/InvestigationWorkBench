# 10 · Non-Functional Requirements

> Index: [README](README.md) · Depends on: —

**Reference conditions:** 300 entities / 1,000 facts; Apple M1 with 16 GB RAM; current stable Chrome. Provider timings are measured against the configured DeepSeek endpoint in non-thinking mode.

| Area | Requirement |
| :--- | :--- |
| Snapshot load | ≤ 1.5 s from request to interactive canvas (gzip, no embeddings or binary data in the JSON) |
| Timeline scrub | Visibility evaluation ≤ 2 ms; frame time p95 ≤ 18 ms while dragging, render and paint included |
| Path | ≤ 50 ms in the frontend |
| Q&A | `context` ≤ 300 ms. Log context-to-first-token and total latency. Target p50 first token ≤ 2 s (gated in M3) |
| Ingestion | Stage changes visible within 1 s. Per-chunk time is logged but not gated. A6 sets the scenario target |
| Reliability | SSE resume or `resync`; idempotent source creation; chunk checkpoints and resume; the policy is idempotent per chunk |
| Durability | **Durable:** cases, briefs, sources, drafts (24 h), Graphiti graph, `IG_*` state, layout, decisions. **Session-only:** Q&A answers, selection. **Browser `localStorage`:** filters, slider position, panel state |
| Low variance | Temperature is set explicitly (0 for extraction, transcription and classification), with non-thinking mode. Model, prompt and template versions are recorded per chunk. Results are low-variance, not guaranteed identical |
| Auditability | Every policy decision and analyst action is a decision record holding actor, time, inputs and before/after values |
| Privacy | Bind the API and Neo4j to `127.0.0.1`. Secrets live in `.env`. Graphiti telemetry is disabled. The UI names every recipient endpoint. Original image bytes never leave the browser. Any OpenAI-compatible self-hosted endpoint is supported |
| Accessibility | Shape duplicates color; reduced motion is respected; text meets WCAG AA; actions are reachable from the keyboard |
