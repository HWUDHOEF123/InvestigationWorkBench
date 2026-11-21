# 06 · Contradiction Policy (v1)

> Index: [README](README.md) · Depends on: [04](04-sources-and-tiers.md), [05](05-time-and-fact-states.md) · UI: [F4](features/F4-contradiction-review.md)

## Why

Graphiti closes the fact with the earlier `valid_at` whenever it confirms a contradiction, regardless of source. Two problems follow:

* A Tier 3 leak dated after a Tier 1 fact closes the Tier 1 fact.
* A denial dated after a leak closes the leak.

The policy restores source reliability and routes genuine disagreements to the analyst.

## When rules run

* **P1–P4** run automatically, in order, after every chunk's `add_episode` and before the revision is published.
* **P3 re-check and P4** also run whenever either side's best tier changes: a tier edit, a new support added during ingestion, or a change to a speculative flag. **P4** also re-runs after a merge.
* **P3 stated ends** run after the closure rows of P3, in the same chunk.
* **P5–P6** are analyst actions.
* Every rule outcome writes a decision record.

## P1 · Capture closures with their cause

The Graphiti adapter wraps `graphiti_core.graphiti.resolve_extracted_edges` for the duration of one `add_episode` call. It does this to pass the function's own `invalidated_by` argument, which exists in 0.31.2 but which `add_episode` does not pass.

This yields exact pairs: *closed fact → the new fact(s) that closed it*. Self-closure is handled separately.

**Self-closure (backfill).** Here Graphiti closes the incoming fact because an existing candidate starts later. The adapter observes Graphiti's temporal step (`_apply_temporal_invalidation`) inside the same resolver call, because only there are the LLM-selected candidates visible.

* If exactly one distinct stored candidate in that list has `valid_at` equal to the incoming fact's new `invalid_at`, that candidate is the cause.
* Otherwise the closure is **unattributed**.
* An end that the incoming fact already carried before the temporal step came from the source text. It is a stated end (below), not a self-closure.

**Stated ends.** Within the same resolver call, the adapter also records every incoming fact whose source states an end: extraction gave it an `invalid_at` before Graphiti's temporal step, and its `modality` is `stated`. Graphiti does not apply such ends to existing facts. A duplicate keeps the stored edge and drops the incoming end, and a parallel fact with the same start closes nothing ([05](05-time-and-fact-states.md)). For each stated end the adapter records:

* the end;
* the claim: canonical endpoints, relation and claim-key attributes;
* the dedupe outcome: merged into an existing fact, or stored as its own fact.

The end is kept on the resulting support as `stated_end` ([03](03-domain-model.md)). P3 applies it.

**Durability.** The adapter records each closed fact's pre-chunk `invalid_at` / `expired_at`, which write-back and undo need. For a self-closed fact it records the values from before the temporal step. The adapter persists these values, the causal map and the stated ends as the chunk's **staged** checkpoint *before* Graphiti writes, so that a crash after Graphiti's commit loses nothing ([F1](features/F1-source-intake.md)).

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

### P3 · Stated ends

This step applies the stated ends captured by P1 to facts that are still open. Speculative supports and stated ends with any `modality` other than `stated` are ignored.

**Target.** The target is the single open fact (null `invalid_at`) that meets all of these conditions:

* it has the same canonical endpoints (after merges) and the same relation as the stated end;
* its claim-key attributes are equal to the stated end's;
* its start is before the stated end.

The template defines the claim key for each relation, for example `role` for `AFFILIATED_WITH` and `kind` for `SOCIAL_TIE`. A relation without a key matches on endpoints and relation alone.

| Case | Result |
| :--- | :--- |
| Exactly one target, and the stated end's support tier is equal to or better than the target's best tier | **Write back** the stated end onto the target: `invalid_at` = the stated end, `expired_at` = now. The result is kept automatically, so it is subject to the P3 re-check. |
| Exactly one target, and the support is less reliable | No write. Set `end_claimed` on the target. The analyst can *确认结束* (write the end) or *驳回* from the review list ([F4](features/F4-contradiction-review.md)). |
| More than one candidate, e.g. one bundled statement covering several roles | No write. Set `end_claimed` on every candidate. The analyst resolves them as above. |
| No candidate | Nothing to apply. A stated end stored as its own fact simply stays as that fact. |

### P3 re-check

This applies to every closure that P3 **kept automatically** under the first `CHANGE` row, and to every stated end that P3 applied automatically. It is re-checked whenever either side's best tier changes.

* **Condition broken.** If "winner's tier is equal to or better than the loser's" no longer holds, apply the `CHANGE` / less-reliable row: write back the loser's pre-closure values and open a `contested_change` conflict.
  * For a stated end, the condition is that the support's tier is equal to or better than the target's best tier. If it breaks, write back the target's pre-closure values and set `end_claimed`.
  * Example: the winner's source is downgraded.
  * Example: the loser gains a better support, such as a new T1 source that Graphiti merged as a duplicate.
  * The re-check writes a decision record. Undoing the tier edit that triggered it also undoes the re-check.
* **One direction only.** A tier change can only *open* review. It never closes a fact or resolves a conflict automatically. If a `contested_change` conflict's winner later becomes equal or better, only the P4 suggestion is updated. An `end_claimed` support that becomes equal or better stays in review.
* **Not re-checked:** closures the analyst accepted through P6 (`change_accepted`), stated ends the analyst confirmed or dismissed, and any adjudicated conflict.

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

* A tier change recomputes corroboration and suggestions, and triggers the P3 re-check. It never reverses an analyst decision: neither a P6 adjudication nor an analyst-accepted change (`change_accepted`).
* Refutation takes precedence over open conflicts ([05](05-time-and-fact-states.md)).
