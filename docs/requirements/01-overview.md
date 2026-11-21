# 01 · Overview

> Index: [README](README.md) · Depends on: —

## Product

**IntelGraph** is an investigation workbench for Chinese-speaking analysts. It turns fragmented, time-sensitive and contradictory material into a navigable, source-grounded case graph, built on **Graphiti** (temporal knowledge graph) and **Neo4j**. Case templates make it work across domains.

**Core loop (v1):** ingest sources → see the graph at any event time → review contradictions → trace connections → ask grounded questions.

## Problem

Whether the file is a due-diligence report, a homicide dossier or a mystery plot, analysts run into the same three problems:

1. **Facts change and sources disagree.** A static graph either overwrites history or stores contradictions as parallel truths. It also cannot tell *"the world changed"* (a CEO stepped down) from *"sources disagree"* (a leak versus a denial).
2. **Connections span documents.** Vector top-*k* retrieval cannot reliably follow a chain such as `Advisor → Foundation → Vendor → Consortium` when each hop comes from a different source.
3. **AI answers lack provenance.** Every claim has to be re-verified by hand.

## Approach

* **Event-time facts.** Each fact records when it was true: Graphiti's `valid_at` / `invalid_at`. Superseded facts become history and are never deleted, so the timeline can show the graph as of any moment.
* **Reliability-aware contradiction review.**
  * When Graphiti closes a fact, it decides by date order and ignores the source.
  * IntelGraph records which fact caused each closure and classifies the change.
  * It then applies tier rules and writes the corrected interval back. Genuine disagreements go to the analyst with a suggested winner.
  * Every policy decision and analyst action is recorded and can be undone.
* **Deterministic structure, grounded generation.**
  * Timeline filtering and path discovery are pure graph computations.
  * Every fact links to its supporting sources, and AI judgments must cite facts.

## Target scenarios

| Scenario | Typical sources | Time scale | What matters most |
| :--- | :--- | :--- | :--- |
| Corporate / financial intelligence | filings, regulators' notices, news, leaks | days–years | Authority of the source, state changes |
| Criminal case analysis | forensic reports, CCTV, records, testimony | minutes–days | Whereabouts, alibis, testimony vs. physical evidence |
| Murder-mystery game (剧本杀) | rule book / host facts, clue cards, character statements | minutes–hours (story time) | Who is lying |
| Mystery fiction | chapters (narration + dialogue) | story time | Unreliable statements, hidden links |

## Language policy

| Layer | Language |
| :--- | :--- |
| UI strings; generated fact text, entity summaries, transcription descriptions and AI answers | **Simplified Chinese** (zh-CN) |
| Verbatim source text, original-language transcription, source titles as given | Unchanged |
| Code, APIs, field names, enum values, relation types (`AFFILIATED_WITH`) | **English** |
| Entity canonical names | Native or most authoritative form (`Jensen Huang`, `Nvidia`, `华为`, `国家市场监督管理总局`), with aliases in other languages (`黄仁勋`, `英伟达`, `SAMR`). The UI shows `Jensen Huang（黄仁勋）` when the canonical name is not Chinese |
| Times | Stored in UTC; displayed in the case time zone (default Asia/Shanghai) |
