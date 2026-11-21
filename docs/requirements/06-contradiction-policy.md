# 06 · Contradiction Policy (v1)

> Index: [README](README.md) · Depends on: [04](04-sources-and-tiers.md), [05](05-time-and-fact-states.md) · UI: [F4](features/F4-contradiction-review.md)

## Why

Graphiti closes the fact with the earlier `valid_at` whenever it confirms a contradiction, regardless of source. Two problems follow:

* A Tier 3 leak dated after a Tier 1 fact closes the Tier 1 fact.
* A denial dated after a leak closes the leak.

The policy restores source reliability and routes genuine disagreements to the analyst.

## When rules run

* **P1–P4** run automatically, in order, after every chunk's `add_episode` and before the revision is published.
* **P4** also re-runs after a tier change or a merge.
* **P5–P6** are analyst actions.
* Every rule outcome writes a decision record.

## P1 · Capture closures with their cause

The Graphiti adapter wraps `graphiti_core.graphiti.resolve_extracted_edges` for the duration of one `add_episode` call. It does this to pass the function's own `invalidated_by` argument, which exists in 0.31.2 but which `add_episode` does not pass.

This yields exact pairs: *closed fact → the new fact(s) that closed it*. Self-closure is handled separately.

**Self-closure (backfill).** Here Graphiti closes the incoming fact because an existing candidate starts later.

* If exactly one stored candidate has `valid_at` equal to the incoming fact's new `invalid_at`, that candidate is the cause.
* Otherwise the closure is **unattributed**.

The adapter also records each closed fact's pre-chunk `invalid_at` / `expired_at`, which write-back and undo need.

The hook is pinned to the Graphiti version, and a contract test runs on every upgrade ([11](11-verification.md)).

## P2 · Classify each attributed pair

Each attributed pair is classified by one small-model call per batch. The call uses temperature 0, a versioned prompt, and the case's classification thinking level, which defaults to `off`.

| Label | Meaning |
| :--- | :--- |
| `CHANGE` | The world changed, so the closed fact really ended. |
| `DISAGREE` | The sources contradict each other about the same period. |
| `COMPATIBLE` | No real contradiction: Graphiti was wrong. One example is a plan to leave versus currently holding the role. |

If classification fails after one retry, the pair is treated like an unattributed closure. Ingestion is never blocked.

## P3 · Apply

"Winner" means the fact that caused the closure. "Loser" means the closed fact. Tiers are best tiers ([04](04-sources-and-tiers.md)).

| Case | Result |
| :--- | :--- |
| `CHANGE`, and the winner's tier is equal to or better than the loser's | Keep Graphiti's closure. |
| `CHANGE`, and the winner is less reliable | **Write back** the loser's pre-chunk values. Open a conflict with kind `contested_change`. |
| `DISAGREE` | Write back the loser's pre-chunk values. Open a conflict with kind `disagreement`. Both facts become `disputed`. |
| `COMPATIBLE` | Write back the loser's pre-chunk values. No conflict is opened. |
| Unattributed or unclassified | Keep Graphiti's closure and set `closure_unconfirmed`. The analyst can *撤销失效* (write back) or *确认失效* from the review list ([F4](features/F4-contradiction-review.md)). |

**Write-back** sets `invalid_at` / `expired_at` on the Graphiti edge through the adapter, between chunks, while ingestion is serialized. It always records the before and after values.

## P4 · Suggest a winner

* Compare the best tiers of the two sides.
  * If exactly one side is better, it is the **suggested** winner (normal strength).
  * If the tiers are equal, there is no suggestion.
* The suggestion is **strong** when that side has a non-speculative T1 support from a source whose `reference_time` is on or after the latest `reference_time` among the other side's supports.
* **v1 never auto-resolves.**

## P5 · Manual conflict

The analyst selects two facts and marks them as a conflict. This opens a `disagreement` conflict with both facts `disputed`. Graphiti data is not changed.

## P6 · Adjudication

A note is mandatory. Each action writes a decision record.

| Conflict kind | Outcome | Conflict state | Effect |
| :--- | :--- | :--- | :--- |
| `disagreement` | `a` (A 成立) / `b` (B 成立) | resolved | The loser becomes `refuted`. |
| `disagreement` | `both_partial` (都部分成立) | resolved | No fact is refuted. |
| `disagreement` | `not_conflict` (不构成冲突) | resolved | No fact is refuted. |
| `contested_change` | `change_accepted` (变化成立) | resolved | Write back the closure Graphiti proposed: the old fact ends at the new fact's `valid_at`. No fact is refuted, because the old fact was true before the change. |
| `contested_change` | `change_rejected` (变化不成立) | resolved | The new fact becomes `refuted`. |
| any | *保持待定* | stays `open` | The note is recorded. |

**Undo** (`POST /decisions/{id}/undo`):

* Appends an inverse decision.
* Restores the previous state, including any written-back values.
* Only the latest non-undone decision on an object can be undone.
* After an undo, the conflict can be adjudicated again.

**Interactions:**

* A tier change recomputes corroboration and suggestions. It never reverses an adjudication or an accepted change.
* Refutation takes precedence over open conflicts ([05](05-time-and-fact-states.md)).
