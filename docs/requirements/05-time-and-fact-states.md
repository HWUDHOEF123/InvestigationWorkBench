# 05 · Time Model & Fact States

> Index: [README](README.md) · Depends on: [03-domain-model](03-domain-model.md) · Used by: [F3](features/F3-timeline.md), [F5](features/F5-path-discovery.md), [06](06-contradiction-policy.md), [09](09-ui-ux.md)

## v1 uses event time only

v1 follows Graphiti's native model: one axis, **event time**, plus each document's own date. Knowledge time is out of scope ([02](02-scope.md)).

| Concept | Graphiti field | v1 handling |
| :--- | :--- | :--- |
| Document time | `EpisodicNode.valid_at`, from `add_episode(reference_time=…)` | The Source's `reference_time` |
| Event-time start | `EntityEdge.valid_at`, extracted by the LLM relative to `reference_time` | If it is null, the display falls back to the earliest `reference_time` among the fact's supports, flagged `valid_at_inferred` (UI "≈"). Graphiti's own date guards skip null starts, so such a fact is never closed automatically; the analyst can use P5 |
| Event-time end | `EntityEdge.invalid_at`. It is set either by the source text (an explicit end) or by a Graphiti closure | Closures are processed by P1–P4. When the policy overrides one, the corrected value is written back ([06](06-contradiction-policy.md)) |
| System timestamps | `created_at`; `expired_at` (processing clock) | Not shown; `expired_at` is written back together with `invalid_at` |

## How Graphiti detects contradictions

Graphiti's detection is bounded and best-effort. Do not treat it as complete:

* **Bounded search.** For each new fact, Graphiti searches the case (`group_id`) for a bounded, ranked set of candidates. An LLM then judges which candidates contradict the new fact.
* **No source awareness.** Among confirmed contradictions, the fact with the **strictly earlier** `valid_at` is closed at the other's `valid_at`, regardless of source.
* **When no closure happens:**
  * the two facts have equal or null starts;
  * the facts do not overlap;
  * the candidate already has an end on or before the new fact's start.
* **Backfill.** An older document ingested later can close *its own* new fact against an existing one that starts later.
* **Order sensitivity.** Results can vary with ingestion order and recent-episode context. Identical graphs are not guaranteed.

What follows from this:

* Missed contradictions are handled by P5 (analyst-marked).
* Write-back ensures Graphiti always reasons over the corrected intervals. For example, if an overridden closure were left in place, a later genuine transition would be skipped.

## Interval and calendar rules

* **Intervals are half-open:** `[valid_at, invalid_at)`; a null `invalid_at` means the fact is still valid.
* **Precision.** Timestamps are stored to the minute. Day-precision dates mean 00:00 in the case time zone.
* **Story time.** The case defines an anchor date, and story day *n* starts at anchor + (n−1) days, 00:00 case-local. Story cases use a fixed-offset time zone (default UTC+8, no DST). Each Source's `reference_time` is entered on this calendar, and the UI renders it as "第n天 HH:mm".
* **Timeline granularity** sets the initial zoom and slider step. It comes from the template; tick labels adapt to the visible span ([F3](features/F3-timeline.md)).

## Temporal state at T

Derived on demand and never stored.

| State | Condition |
| :--- | :--- |
| `future` | `valid_at > T` |
| `expired` | `invalid_at ≠ null ∧ invalid_at ≤ T` |
| `active` | otherwise |

**Node visibility.** A node is shown when `first_seen ≤ T`.

* `first_seen` is the earliest `valid_at` among its facts.
* If none of its facts has a `valid_at`, use the earliest `reference_time` among the sources supporting those facts.

## Epistemic status and flags

`status` is single-valued and derived in this order. The first matching row wins.

| Status | Rule |
| :--- | :--- |
| `refuted` | The fact lost an adjudication that has not been undone. This holds even if it belongs to other conflicts. |
| `disputed` | The fact belongs to at least one open conflict. |
| `corroborated` | The fact has one non-speculative T1 support, **or** ≥ 2 distinct non-speculative sources of tier ≤ T2. The UI label "已印证" means exactly this rule. |
| `reported` | Otherwise. |

Independent flags are derived from the supports:

| Flag | Rule |
| :--- | :--- |
| `speculative` | All of the fact's supports are speculative. |
| `synthetic` | At least one support comes from a synthetic source. The fact is marked "推演" wherever it appears. |
| `closure_unconfirmed` | Graphiti closed the fact, but P1 could not attribute the closure or P2 could not classify it ([06](06-contradiction-policy.md)). |

How state and flags render is defined in [09-ui-ux](09-ui-ux.md).
