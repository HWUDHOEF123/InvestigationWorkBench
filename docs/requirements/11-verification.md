# 11 · Verification

> Index: [README](README.md) · Depends on: [04](04-sources-and-tiers.md), [05](05-time-and-fact-states.md), [06](06-contradiction-policy.md) · Fixtures: `fixtures/nvidia/`, `fixtures/rainy_manor/`

## Acceptance baseline

M0 used Graphiti 0.31.2, Neo4j 2026.10.2, DeepSeek `deepseek-flash`, and Bailian `qwen3.7-text-embedding`. A scripted model verified causal capture, write-back, and the next Graphiti read. Live extraction can still miss or pick the wrong contradiction candidate. Verify A1–A3 and the backend part of A5 through the API for M1, using the v1.5.2 fixture dates below.

## Scenario A — Nvidia: leadership, regulation and the AI-chip contest (`corporate_intel`)

The frozen scenario uses real companies and people. S0–S3 are public background, and S4–S7 are explicitly marked synthetic.

### Background sources (S0–S3)

The frozen M0 fixture records the URL, publication date, saved-text SHA-256, and expected assertions for each source.

* S0: NVIDIA FY2026 Form 10-K, executive officers excerpt.
* S1: China SAMR's antitrust investigation notice.
* S2: NVIDIA Form 8-K, H20 export-control license requirement.
* S3: oneAPI blog announcing the UXL Foundation. It names Google, the vendor *V* used in S6.

### Hypothetical developments (S4–S7)

These are synthetic sources. The v1.5.2 fixture fixes D at `2026-12-01` in Asia/Shanghai.

* Every one carries `synthetic: true`.
* Every fact they support is marked "推演" in the UI, in paths and in Q&A.
* The one allegation about a non-public individual uses a role and an alias: "DOJ 特别顾问 'Mercer'".

| ID | Day | Tier | Kind / type | Content |
| :--- | :--- | :--- | :--- | :--- |
| S0–S3 | real dates | T1/T2 | document (zh/en) | The real background described above |
| S4 | D | T3 | **image**: screenshot of an anonymous Chinese post | "黄仁勋计划辞去英伟达 CEO，原因是与董事会在中国战略上存在分歧" |
| S5 | D+2 | T2 | document: Nvidia statement | "黄仁勋没有辞任 CEO 的计划，相关传闻毫无根据" (denies the same plan) |
| S6 | D+7 | T2 | document: investigative report (zh) | "Mercer" sat on the policy board of a tech-policy foundation from D−3y to D−1y. The foundation is funded by *V* |
| S7 | D+14 | T1 | document: Form 8-K (**live drop**) | Effective D+14, Jensen Huang moves from CEO to Executive Chairman & Chief Architect. A new CEO is appointed. Nvidia commits to opening low-level CUDA runtime APIs |

### Assertions

| # | Phase | Assertion |
| :--- | :--- | :--- |
| A1 | after S0–S3 | Key entities exist with zh-CN summaries and the correct canonical names. Every alias form that has appeared in S0–S3 is recorded (e.g. `Jen-Hsun Huang`); forms that first appear later are checked after those sources. `Jensen Huang –AFFILIATED_WITH{role: CEO}→ Nvidia` is active and corroborated. *V* `–AFFILIATED_WITH{role: member}→` UXL Foundation exists, supported by S3. |
| A2 | after S4 | The draft is transcribed, reviewed and confirmed. 黄仁勋 / 英伟达 resolve to Jensen Huang / Nvidia, either directly or after one manual merge. The leak yields *F_plan* (`modality: planned`) and *F_reason*, both T3. **The CEO fact is active for every T in [its start, D+14).** If Graphiti closed it, P2 labels the pair `COMPATIBLE` or `CHANGE`, and P3 writes it back (opening a `contested_change` conflict if the label is `CHANGE`). |
| A3 | after S5 | A `disagreement` conflict C1 between *F_plan* and *F_denial* is open. It comes from P1–P3, or from P5 if Graphiti missed it. Both facts are `disputed`. The suggestion is *F_denial*, at normal strength. Nothing is auto-resolved. |
| A4 | after S6 | At T = D+7, the shortest path *Mercer → foundation → V → UXL Foundation* (3 hops) is found. Hop 1 has the interval `[D−3y, D−1y)` and is labelled *历史*. Hop 3 is supported by S3, so the path spans documents. |
| A5 | after S7 | The CEO fact ends exactly at D+14 00:00 case-local (Asia/Shanghai, `2026-12-14T16:00Z`). It is active at T = D+14 − 1 min and expired (gray dashed) at T = D+14 00:00. This works even if A2 required a write-back. The new role facts are active from that same instant. After the analyst adjudicates C1 with outcome `a` (*F_plan* holds), citing S7 in the note, *F_denial* is `refuted` and *F_reason* stays `reported`. |
| A6 | during S7 | Every stage shows progress. Existing node positions are unchanged. The time from confirmation to `committed` is logged; the target is ≤ 3 min under the reference conditions. |
| A7 | after S7, at the published version | Q&A on {Jensen Huang, Nvidia, 美国司法部反垄断局} returns zh-CN judgments. Every judgment cites a fact, there are zero invalid IDs, and every judgment citing S4–S7 facts carries 含推演. |

## Scenario B — "雨夜山庄" mini murder mystery (`murder_mystery_game`, story time)

All sources are on story day 1, in UTC+8.

| Source | Tier | Content |
| :--- | :--- | :--- |
| Host rule sheet | T1 | The time of death is [21:00, 21:30) |
| Clue card 1 | T2 | **Kitchen CCTV: nobody in the kitchen during [21:00, 21:30)** |
| Clue card 2 | T2 | Muddy footprints in the study |
| Statement 李四 | T3, speaker 李四 | "我 21:10 到 21:20 一直在厨房" |
| Statements 张三, 王五, 赵六 | T3, each with its speaker | Whereabouts with explicit intervals |
| Analyst note | speculative | "张三可能拿走了书房的拆信刀" (creates a shortcut 张三 → 拆信刀) |

| # | Assertion |
| :--- | :--- |
| B1 | The timeline uses minute ticks labelled "第1天 HH:mm". Each statement yields `LOCATED_AT` facts with half-open intervals. |
| B2 | 李四's statement conflicts with clue card 1, either from the policy or via P5. The suggestion is clue card 1 (T2 over T3), and the speaker 李四 is shown. |
| B3 | The note-only object is identified by the note's fact and its UUID, not by display name. Extraction may name it with a qualifier, e.g. `书房的拆信刀`. The note's facts render as speculative. With speculation excluded (the default), the path 张三 → 拆信刀 is longer or absent. With it included, the path uses the note's fact. They never count toward corroboration. |

## Test layers

| Layer | What | Needs |
| :--- | :--- | :--- |
| Policy unit tests | P1–P6 on hand-authored graph states: write-back followed by a later genuine transition (the A5 risk); two same-date incoming facts; backfill self-closure; `COMPATIBLE`; every P6 outcome and undo; precedence across multiple conflicts; **P3 re-check**: downgrading the winner, or a new T1 support for the loser, reopens a kept closure as `contested_change`, while an upgrade never closes anything automatically; a fact with null `valid_at` is placed by its inferred start on the timeline and in paths; **P3 stated ends**: a T1 stated end closes its unique target (both when merged as a duplicate and when stored as a parallel same-start fact), a T3 stated end only sets `end_claimed`, a bundled claim matching several facts sets `end_claimed` on each, a `planned`/`denied` modality is ignored, and *确认结束* / *驳回* / undo work | Nothing external |
| Adapter contract tests | Against pinned `graphiti-core` and Neo4j, with a scripted fake LLM: the `invalidated_by` hook fires; write-back is visible to Graphiti's next resolution; two `group_id`s stay isolated; resume after Graphiti has committed but before the policy runs (UUID match → replay; orphaned staged checkpoint → retry; mismatch → `capture_mismatch`); a stated end is captured when dedupe merges the incoming fact; a date-only effective date is normalized to case-local midnight | Neo4j |
| Frontend E2E (fixture mode) | Read paths: rendering and styles, timeline at the A/B timestamps, paths A4/B3, conflict display, recorded Q&A stream with citation flags | Nothing external |
| Live checklist | A1–A7 and B1–B3 end to end, before each release | Provider + Neo4j |
