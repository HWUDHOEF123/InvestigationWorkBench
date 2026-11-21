# 09 · UI/UX (zh-CN)

> Index: [README](README.md) · Depends on: [05](05-time-and-fact-states.md) · Used by: [F2](features/F2-graph-canvas.md)–[F6](features/F6-grounded-qa.md)

## Workbench styles

Users can switch among three page styles while working on the same case. Each style uses the same case data and evidence links. [Design previews](../../README.md#界面预览)

| Style | Visual focus |
| :--- | :--- |
| 时态图谱 | The Intel Dark palette, with a relationship graph, time scrubber, conflict markers and cited answers |
| 文档与证据画布 | A light canvas centred on source documents, entity cards and evidence excerpts |
| 案件板 | A dark board with pinned people, clippings and notes connected as investigation leads |

## Layout

| Region | Content |
| :--- | :--- |
| Top bar | Case name · template · entity search · recipient indicator ("内容发送至：LLM <host> · 向量 <host>") · ⚙ 案件设置 |
| Left panel | Source list (tier badge, kind icon, progress, "推演" / "推测" badges) and drafts, with **+ 添加信源** · review list (冲突 / 待确认失效) · filters |
| Canvas | Infinite React Flow viewport with a floating selection toolbar |
| Right panel (inspector) | Tabs: **详情** (entity / fact / conflict / closure) · **证据** (excerpts, images, location label) · **问答** ([F6](features/F6-grounded-qa.md)) |
| Bottom console | Timeline: step and play, slider, histogram, as-of time |

* The left and right panels are collapsible.
* All UI strings live in `i18n/zh-CN`; the keys are English.

## Thinking-level controls

The level is labelled **关闭 / 低 / 中 / 高**. Both controls below are hidden when `GET /providers/llm` returns no levels.

* **问答 tab.** A segmented control sits next to the question box. Its default is the case's `qa_default`. A hint shows the typical extra latency.
  * While the model is thinking, the tab shows "思考中…".
  * The 思考过程 panel is collapsed by default ([F6](features/F6-grounded-qa.md)).
* **⚙ 案件设置.** This holds the thinking levels for 信息抽取 and 矛盾分类, each defaulting to 关闭.
  * Changes apply to chunks ingested afterwards.
  * The dialog warns: "开启思考会增加每个切块的耗时与费用，且结果波动更大".

## Nodes

Shape always duplicates color.

| Type | Shape | Color |
| :--- | :--- | :--- |
| Person | Circle | `#06B6D4` cyan |
| Organization | Rounded square | `#A855F7` purple |
| Location | Map pin | `#3B82F6` blue |
| Object | Tag card | `#F472B6` pink |
| Event | Diamond | `#F59E0B` gold |
| Concept | Hexagon | `#CBD5E1` light slate ("未分类" badge when unclassified) |

In the Intel Dark graph style, the canvas background is `#0B0F19`, with a dot grid in `#1E293B`.

## Facts: line style

Exactly one line style applies to each fact. It is the first row that matches.

| Precedence | Condition | Line | Color |
| :--- | :--- | :--- | :--- |
| 1 | `future` at T | Hidden | — |
| 2 | `refuted` | Dotted 1 px, opacity 0.35, ✕, struck-through label | `#475569` |
| 3 | `disputed` | Dashed 2.5 px, 1.6 s pulse (static + ⚠ under reduced motion) | `#EF4444` |
| 4 | `expired` at T | Dashed 1 px, opacity 0.35 | `#475569` |
| 5 | `speculative` | Dotted 1.5 px, "推测" label | `#10B981` emerald |
| 6 | `corroborated` | Solid 2.5 px + arrow, ✓ | `#94A3B8` |
| 7 | `reported` | Solid 1.5 px + arrow | `#64748B` |

**Badges** are added on top of the line style, independently:

* the tier badge (`T1`–`T3`);
* **推演** when `synthetic`;
* **⚠失效待确认** when `closure_unconfirmed`;
* **⚠结束待确认** when `end_claimed`;
* **≈** on dates when `valid_at_inferred`.

A refuted or disputed fact that is also expired keeps its refuted or disputed style, and its label adds "（历史）".

**Path highlight:** a glow in `#E2E8F0` on the path; every other element dims to 15%.

## Interaction

* Shortcuts:
  * `Esc` clears the selection and highlights;
  * `P` runs shortest path;
  * `Q` opens Q&A.
* Clicking any fact, path hop or citation opens its evidence.
* Hidden elements are not focusable or selectable ([F2](features/F2-graph-canvas.md)).
* Text contrast meets WCAG AA.
* Every action is reachable from the keyboard, except dragging on the canvas.
