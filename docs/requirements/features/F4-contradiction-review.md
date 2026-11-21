# F4 · Contradiction Review

> Index: [README](../README.md) · Depends on: [06](../06-contradiction-policy.md)

* **Review list (left panel)** has two groups. Their counts appear in the panel header.
  * **冲突:** open conflicts first, then resolved ones.
  * **待确认失效:** facts with `closure_unconfirmed` (from P1/P3), and facts with `end_claimed` (from P3 stated ends).
* **Conflict detail (inspector):**
  * Both facts side by side. Each shows:
    * best tier;
    * the source's speaker and the informational `asserted_by`;
    * the `[valid_at, invalid_at)` interval;
    * each supporting source's title and `reference_time`;
    * the excerpt, with an image thumbnail for image sources;
    * the "推演" marker where it applies.
  * The conflict's kind (`disagreement` / `contested_change`), origin (`policy` / `manual`) and classifier label.
  * The suggested winner and its strength, or "无建议" if there is none.
  * The decision history.
* **Actions.**
  * The P6 outcomes valid for the conflict's kind, each with a mandatory note.
  * *保持待定*.
  * Undo of the latest decision on the conflict.
* **Unconfirmed closure detail.** Shows the fact, Graphiti's proposed end, and the candidate cause if one exists. Actions: *确认失效* or *撤销失效* (write-back). Both are undoable.
* **Claimed end detail.** Shows the open fact and each claiming support: source, tier, stated end and excerpt, plus why P3 did not apply it (less reliable, or several candidate facts). Actions per support: *确认结束* (writes the stated end) or *驳回*. Both need a note and are undoable.
* **Selecting a conflict** highlights both facts on the canvas. It does not move the slider. The inspector offers "跳到 A 的时间" and "跳到 B 的时间", and previews any fact that is hidden at the current T.
