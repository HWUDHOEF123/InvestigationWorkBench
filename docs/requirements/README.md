# IntelGraph Requirements — Index

> **Version 1.5.0-PRD** · Draft for implementation · Chinese reading copy: [`../requirements(cn).md`](<../requirements(cn).md>) (keep in sync; these English files are canonical for identifiers)

IntelGraph is a Chinese-language investigation workbench. It turns fragmented, time-sensitive, contradictory material into a source-grounded case graph on **Graphiti** (`graphiti-core==0.31.2`) and **Neo4j**.

The v1 core loop is: **ingest sources → view the graph at any event time → review contradictions → trace paths → ask grounded questions.**

## How to use these docs (for agents)

1. Read this index first. The **Key invariants** and **Glossary** cover most tasks.
2. Open only the files relevant to the task (see *Read when…* in the table below). Each file states what it depends on.
3. IDs are stable; cite them in code, tests and commits:
   - Features: `F1`–`F6`
   - Policy rules: `P1`–`P6`. `P1`–`P4` run automatically after each chunk; `P5`–`P6` are analyst actions.
   - Scenario assertions: `A1`–`A7`, `B1`–`B3`
   - Milestones: `M0`–`M3`

   All F1–F6 are in v1, so there is no separate priority label.

## Files

| File | Covers | Read when… |
| :--- | :--- | :--- |
| [01-overview.md](01-overview.md) | Problem, approach, scenarios, language policy | Onboarding; writing user-facing text |
| [02-scope.md](02-scope.md) | v1 features, backlog & exploration, non-goals | Deciding whether something is in v1 |
| [03-domain-model.md](03-domain-model.md) | Core objects, Graphiti/overlay ownership, ontology, templates, merges | Data modelling, Graphiti types, templates |
| [04-sources-and-tiers.md](04-sources-and-tiers.md) | Source kinds, image drafts, case brief, tiers, speaker | Intake, tier logic |
| [05-time-and-fact-states.md](05-time-and-fact-states.md) | Event-time semantics on Graphiti, story time, fact status and flags | Timeline, visibility, status derivation |
| [06-contradiction-policy.md](06-contradiction-policy.md) | P1–P6: causal capture, classification, write-back, suggestions, adjudication | Policy layer, review UI |
| [07-architecture.md](07-architecture.md) | Modules, key decisions, Graphiti/DeepSeek integration, run modes | Backend structure, adapter, infra |
| [features/F1-source-intake.md](features/F1-source-intake.md) | Cases, sources, image drafts, chunking, progress, resume, ingestion flow | Intake API/UI, ingestion worker |
| [features/F2-graph-canvas.md](features/F2-graph-canvas.md) | Canvas, anchored layout, filters, search, selection, merge | Canvas frontend |
| [features/F3-timeline.md](features/F3-timeline.md) | Event-time slider, ticks, visibility, performance | Timeline frontend |
| [features/F4-contradiction-review.md](features/F4-contradiction-review.md) | Review list, conflict detail, adjudication, unconfirmed closures | Review UI |
| [features/F5-path-discovery.md](features/F5-path-discovery.md) | Frontend shortest path, eligibility, tie-breaks | Pathing |
| [features/F6-grounded-qa.md](features/F6-grounded-qa.md) | Q&A request, thinking level, context, stream protocol, citation checks | Q&A backend and inspector |
| [08-data-contract-api.md](08-data-contract-api.md) | Snapshot & evidence types, endpoints, SSE, errors | Any frontend↔backend work |
| [09-ui-ux.md](09-ui-ux.md) | Layout, complete style table, interaction rules | Styling, components |
| [10-non-functional.md](10-non-functional.md) | Budgets, reliability, durability, privacy | Performance and quality |
| [11-verification.md](11-verification.md) | Scenarios A and B, test layers | Fixtures, tests, acceptance |
| [12-delivery-and-risks.md](12-delivery-and-risks.md) | Milestones M0–M3, risks | Planning |
| [13-setup.md](13-setup.md) | Requirements, repo layout, `.env`, Homebrew Neo4j, `check_env.py`, run commands | Environment setup |
| [14-references.md](14-references.md) | External references | Background research |

## Key invariants

1. **Ownership.** Graphiti owns entities, edges and episodes. IntelGraph state lives in `IG_*` nodes keyed by Graphiti UUIDs. **Single exception:** the Graphiti adapter may write back `invalid_at` / `expired_at` on an edge when the policy overrides Graphiti. It records the original values in a decision record and restores them on undo. Nothing else writes to Graphiti data. → 03, 06
2. **Event time only in v1.** Facts use Graphiti `valid_at` / `invalid_at` (half-open `[valid_at, invalid_at)`), and `reference_time` is the document date. Knowledge time is out of v1. → 05
3. **Graphiti closes facts by date order only.** P1–P4 correct this using source tiers. **v1 never auto-resolves conflicts**; it only suggests a winner. → 06
4. **Serialized ingestion.** One chunk is processed at a time. A new case revision is published only after the policy has finished for that chunk. Clients refetch the snapshot on `graph.changed`. → 07, F1
5. **Timeline and paths run in the frontend** on the in-memory snapshot. No server calls are made while scrubbing. → F3, F5
6. **Every fact links to its supporting sources** (`IG_FactSupport`). Excerpts are located automatically and labelled as such, with the whole chunk as fallback. Q&A citations are validated. → 03, F6
7. **Language.** UI and generated content are in Simplified Chinese. Code, fields, enums and relation types are in English. Entity names keep their native form, with aliases (`Jensen Huang（黄仁勋）`). The adapter overrides Graphiti's "same language as source" instruction. → 01, 07
8. **Providers.** All model calls use OpenAI-compatible endpoints (default DeepSeek, `json_object` mode).
   * **Thinking level** (`off` / `low` / `medium` / `high`) is selectable: per case for extraction and classification, and per question for Q&A. The default is `off`. A provider profile maps each level to request parameters.
   * Graphiti uses a single model.
   * The embedder is multilingual, and its native dimension must equal `EMBEDDING_DIM`.
   * Graphiti telemetry is off.

   → 07
9. **Parallel worktrees share one Neo4j.**
   * Settings resolve via `app/config.py`, so secrets come from the main worktree.
   * Every Graphiti `group_id` is `<namespace>__<case_id>`.
   * Tests delete only their own `group_id`s; never call `clear_data()` unscoped.

   → 13

## Glossary

| Term | Meaning |
| :--- | :--- |
| Case | One investigation. A Graphiti `group_id`, with a template, time zone, case brief and optional story anchor |
| Template | Versioned config specialising ontology, tier labels and time mode (`corporate_intel`, `murder_mystery_game`, …) |
| Source | One unit of evidence: a document, a confirmed image set or an analyst note |
| Image draft | Uploaded, transcribed images awaiting analyst review. It becomes a Source on confirm |
| Chunk / Episode | A slice of a Source; ingested as one Graphiti `EpisodicNode` named `{source_id}:{chunk_index}` |
| Entity | Node of type `Person`, `Organization`, `Location`, `Object`, `Event` or `Concept` |
| Fact | Directed relation between entities (Graphiti `EntityEdge`), with Chinese text and an event-time interval |
| Support | One `(fact, source, episode)` link (`IG_FactSupport`) carrying source tier and flags; the basis for evidence and corroboration |
| Best tier | The best tier (T1 is best) among a fact's non-speculative supports |
| Reference time | The document's own date (on the story calendar in story mode), passed to Graphiti as `reference_time` |
| Event time | When a fact was true: `[valid_at, invalid_at)` |
| Story time | Event time on a synthetic calendar ("第1天 21:00") |
| Closure | Graphiti setting `invalid_at` on a fact |
| Write-back | The adapter changing `invalid_at`/`expired_at` on a Graphiti edge to apply a policy decision |
| Conflict | A recorded contradiction (`disagreement` or `contested_change`) with a suggestion and resolution |
| Decision record | Append-only audit entry for every policy decision and analyst action; the basis for undo |
| Revision | A monotonically increasing version of a case's effective graph |
| Effective graph | Graphiti data plus overlay (merges, conflicts, supports, flags), as served in the snapshot |
| Case brief | Analyst guidance added to extraction and Q&A prompts; never ingested |
| Thinking level | `off` \| `low` \| `medium` \| `high`. How much model reasoning a call may use; mapped to provider parameters by the provider profile |
| Speculative | A support from a note flagged "这是推测". A fact is speculative only if all its supports are |
| Synthetic | A support from a test-scenario source with `synthetic: true`; marked "推演" wherever the fact appears |

## Revision history

| Version | Changes |
| :--- | :--- |
| 1.0.0 | Initial PRD (single file). |
| 1.1.0 | Fixed inconsistencies; added domain model, adjudication policy, overlay, data contract, assertions and milestones. |
| 1.2.0 | v1 cut to F1–F6; Chinese-first; image/note sources; generic ontology and templates; DeepSeek; Scenarios A/B. |
| 1.3.0 | Knowledge time removed from v1; decision records; English PRD split into this folder. |
| 1.4.0 | Applied the independent review (Codex, verified against `graphiti-core` 0.31.2): causal capture via Graphiti's `invalidated_by`; invalidation write-back; `IG_FactSupport` evidence; chunk checkpoints and resume; `graph.changed` + snapshot refetch; image drafts; full P6 transitions; complete style/eligibility rules; Q&A request and stream contract; fixed Scenarios A and B; telemetry off, loopback ports, no APOC; reported-speech tier cap moved to backlog; CN parity and links fixed. |
| 1.5.0 | **Selectable thinking level** (`off`/`low`/`medium`/`high`, default `off`): set per case for extraction and classification, and per question for Q&A (with an optional, unverified reasoning stream). Mapped by a provider profile and injected by the adapter. Provider facts verified during environment setup: DeepSeek supports `json_object` only; thinking is on by default and is disabled via `thinking: {type: disabled}`; Bailian's OpenAI-compatible path is `/compatible-mode/v1`; the embedder's native dimension must equal `EMBEDDING_DIM`; `httpx[socks]` is needed under SOCKS proxies. Setup moved to Homebrew Neo4j and a cloud embedder. |
