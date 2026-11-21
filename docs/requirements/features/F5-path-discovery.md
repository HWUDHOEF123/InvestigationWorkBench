# F5 · Path Discovery

> Index: [README](../README.md) · Depends on: [05](../05-time-and-fact-states.md), [08](../08-data-contract-api.md)

* **Trigger.** Select exactly 2 nodes → *最短路径* (or `P`).
* **Graph.** A per-revision, undirected adjacency list built in the frontend. Neighbours are sorted by `(entity_id, fact_id)`, so results are deterministic.
* **Fact eligibility at T:**
  * `valid_at ≤ T` (future facts are excluded);
  * `expired` facts are allowed by default and labelled *历史*; a toggle turns this off;
  * `refuted` facts are excluded;
  * speculative facts are excluded by default; a toggle includes them;
  * both endpoints' types pass the canvas entity-type filter.

  The other canvas filters do not affect paths.
* **Search.** BFS, at most 6 hops. It returns the first shortest path in the deterministic order.
  * When several facts connect the same pair of nodes, the best tier is used, then the earliest `valid_at`.
  * The hop detail says "另有 n 条".
* **Display.**
  * The path is highlighted, and everything else dims to 15%.
  * Path nodes hidden by canvas filters are temporarily revealed for as long as the path is shown.
  * The inspector lists each hop with:
    * the fact's original direction;
    * its text and interval;
    * best tier;
    * the "推演" marker where it applies;
    * the excerpt, loaded in one batched call (`POST /cases/{id}/evidence`).
* **No path.**
  * Distinguish "6 跳内无路径" from "当前条件下不连通".
  * Re-run once with history and speculation enabled. If that finds a path, show "开启「…」后可找到路径".
* **Budget.** ≤ 50 ms.
