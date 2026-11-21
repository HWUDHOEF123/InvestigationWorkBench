# F3 · Event-Time Timeline

> Index: [README](../README.md) · Depends on: [05](../05-time-and-fact-states.md), [10](../10-non-functional.md)

* **Bottom console.**
  * A slider over the case's event-time span.
  * Step back / forward, and Play.
  * An editable "as of" time.
  * The template's default granularity sets the initial zoom and the slider step.
  * The tick labels adapt to the visible span: minutes, then hours, days, months and years. Story mode uses "第n天 HH:mm".
* **Histogram.** Shows the density of fact starts, with markers for T1 sources (◆) and open conflicts (⚠).
* **Semantics.** Temporal states and node visibility at T follow [05](../05-time-and-fact-states.md), with half-open intervals. Status and flags always reflect the current revision.
* **No server calls while scrubbing.**
  * Hidden elements follow the rules in [F2](F2-graph-canvas.md): not interactive, and their coordinates are kept.
  * Position or slider changes never trigger a layout.
* **Implementation guidance.**
  * Parse timestamps once per revision.
  * Throttle with `requestAnimationFrame`.
  * Compute every element's visual state in one O(V+E) scan per frame. Each element reads its own state through its own selector.
  * Use an indexed boundary list only if the scan misses the budget.
* **Budget.** Visibility evaluation ≤ 2 ms. Frame time p95 ≤ 18 ms while dragging, including render and paint. Reference conditions are in [10](../10-non-functional.md).
