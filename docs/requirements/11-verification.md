# 11 · Verification

> Index: [README](README.md) · Depends on: [04](04-sources-and-tiers.md), [05](05-time-and-fact-states.md), [06](06-contradiction-policy.md) · Fixtures: `fixtures/nvidia/`, `fixtures/rainy_manor/`

## Scenario A — Nvidia: leadership, regulation and the AI-chip contest (`corporate_intel`)

This scenario uses real companies, real people and current events.

### Background sources (S0–S3)

These are real public sources. They are **frozen in M0**: each one is recorded with its URL, publication date, the SHA-256 of the saved text, and the exact assertions it must yield. Dates and wording follow the originals, and the set mixes Chinese and English sources. Candidate threads:

* Nvidia's latest 10-K (Jensen Huang, founder and CEO since 1993);
* China SAMR's antitrust investigation of Nvidia;
* US export-control actions on H20-class chips, and Nvidia's related filings;
* the CAC's summons of Nvidia over H20 security concerns;
* the UXL Foundation's CUDA-alternative effort.

**S3 must explicitly name one cloud vendor as a UXL member.** That vendor, called *V* below, is fixed in M0 and used verbatim in S6.

### Hypothetical developments (S4–S7)

These are synthetic sources. They are dated relative to a day D, which is set after the latest background item.

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
| A1 | after S0–S3 | Key entities exist with zh-CN summaries and the correct canonical names and aliases. `Jensen Huang –AFFILIATED_WITH{role: CEO}→ Nvidia` is active and corroborated. *V* `–AFFILIATED_WITH{role: member}→` UXL Foundation exists, supported by S3. |
| A2 | after S4 | The draft is transcribed, reviewed and confirmed. 黄仁勋 / 英伟达 resolve to Jensen Huang / Nvidia, either directly or after one manual merge. The leak yields *F_plan* (`modality: planned`) and *F_reason*, both T3. **The CEO fact is active for every T < D+14.** If Graphiti closed it, P2 labels the pair `COMPATIBLE` or `CHANGE`, and P3 writes it back (opening a `contested_change` conflict if the label is `CHANGE`). |
| A3 | after S5 | A `disagreement` conflict C1 between *F_plan* and *F_denial* is open. It comes from P1–P3, or from P5 if Graphiti missed it. Both facts are `disputed`. The suggestion is *F_denial*, at normal strength. Nothing is auto-resolved. |
| A4 | after S6 | At T = D+7, the shortest path *Mercer → foundation → V → UXL Foundation* (3 hops) is found. Hop 1 has the interval `[D−3y, D−1y)` and is labelled *历史*. Hop 3 is supported by S3, so the path spans documents. |
| A5 | after S7 | The CEO fact ends at D+14. It is active at T = D+13 and expired (gray dashed) at T = D+14. This works even if A2 required a write-back. The new role facts are active from D+14. After the analyst adjudicates C1 with outcome `a` (*F_plan* holds), citing S7 in the note, *F_denial* is `refuted` and *F_reason* stays `reported`. |
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
| B3 | The note's facts render as speculative. With speculation excluded (the default), the path 张三 → 拆信刀 is longer or absent. With it included, the path uses the note's fact. They never count toward corroboration. |

## Test layers

| Layer | What | Needs |
| :--- | :--- | :--- |
| Policy unit tests | P1–P6 on hand-authored graph states: write-back followed by a later genuine transition (the A5 risk); two same-date incoming facts; backfill self-closure; `COMPATIBLE`; every P6 outcome and undo; precedence across multiple conflicts; **P3 re-check**: downgrading the winner, or a new T1 support for the loser, reopens a kept closure as `contested_change`, while an upgrade never closes anything automatically; a fact with null `valid_at` is placed by its inferred start on the timeline and in paths | Nothing external |
| Adapter contract tests | Against pinned `graphiti-core` and Neo4j, with a scripted fake LLM: the `invalidated_by` hook fires; write-back is visible to Graphiti's next resolution; two `group_id`s stay isolated; resume after Graphiti has committed but before the policy runs | Neo4j |
| Frontend E2E (fixture mode) | Read paths: rendering and styles, timeline at the A/B timestamps, paths A4/B3, conflict display, recorded Q&A stream with citation flags | Nothing external |
| Live checklist | A1–A7 and B1–B3 end to end, before each release | Provider + Neo4j |
