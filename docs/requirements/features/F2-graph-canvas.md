# F2 · Graph Canvas

> Index: [README](../README.md) · Depends on: [03](../03-domain-model.md), [05](../05-time-and-fact-states.md), [09](../09-ui-ux.md)

* **Rendering.** `@xyflow/react` renders the effective graph, with shapes and styles from [09](../09-ui-ux.md).
* **Anchored layout.**
  * **First load.** A force-directed layout runs once with a fixed seed and stable node ordering. Positions are persisted with `PUT /cases/{id}/layout`, debounced and versioned separately from the graph revision.
  * **New nodes.** Each one is placed near its highest-degree existing neighbour without overlap. The default is a ring of 180 px, +60 px per extra ring, at the free angle with least overlap; the result is deterministic. A node with no neighbour goes into an "incoming" grid to the right of the bounding box.
  * **Existing nodes** move **only** when the analyst drags them or runs **Re-layout**. Re-layout has a one-step undo that lasts until the next layout change.
  * **Acceptance.** Positions of existing nodes are unchanged across revisions, and new nodes do not overlap.
* **Filters (canvas).**
  * entity type;
  * tier;
  * *显示历史*: expired facts, on by default;
  * *隐藏已驳斥*;
  * *仅看冲突*;
  * *隐藏推测*;
  * *隐藏推演*.

  Paths have their own eligibility rules ([F5](F5-path-discovery.md)).
* **Hidden elements** are excluded from rendering, focus, selection, `fitView` and canvas search. Hiding them must not move any coordinates. Implementations may use CSS invisibility, culling or filtered arrays, provided they pass the no-jitter and interaction tests.
* **A fact is renderable** only when both of its endpoint nodes are visible.
* **Search.** By name or alias, matched locally in the snapshot. Selecting a result centers and highlights it; if it is hidden at T, the canvas offers to reveal it.
* **Level of detail.** Below zoom 0.55, edge labels are hidden. Below 0.35, node labels are hidden too, except for selected and hovered nodes.
* **Selection.** Click, Shift-click or box-select. The toolbar offers:
  * *最短路径* (2 nodes);
  * *提问* (1–8 nodes);
  * *合并实体* (2 nodes of the same type);
  * *标记冲突* (2 facts).

  Disabled actions show the reason in a tooltip.
* **Manual merge.** The analyst picks which node is canonical and may rename it. The request is `POST /cases/{id}/merges {alias_id, canonical_id, canonical_name?, version}`. The projection rules are in [03](../03-domain-model.md). Undo goes through the merge's decision record.
