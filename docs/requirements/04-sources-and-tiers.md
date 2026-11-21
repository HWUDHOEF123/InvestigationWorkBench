# 04 · Sources & Reliability Tiers

> Index: [README](README.md) · Depends on: [03-domain-model](03-domain-model.md) · Implemented by: [F1](features/F1-source-intake.md)

## Source kinds

| Kind | Input | Processing |
| :--- | :--- | :--- |
| `document` | Pasted text, `.txt`, `.md`, or `.pdf` with a text layer | Normalize, chunk ([F1](features/F1-source-intake.md)), ingest |
| `image` | 1–10 images (photos, screenshots, scanned pages, clue cards) via an **image draft** (below) | The reviewed text is ingested like a document |
| `note` | A summary or record written by the analyst | Ingested like a document. The checkbox **"这是推测，不是证据"** sets `speculative` |

Every Source has:

* `reference_time`: the document's own date, or its date on the story calendar in story mode. It is passed to Graphiti and anchors relative time expressions.
* `source_type`: from the template's list. It sets the default tier.
* An optional `speaker`.
* Flags `speculative` and `synthetic`. `synthetic` is set for test-scenario material; see [11](11-verification.md).

## Image drafts

1. **Select.** The browser reads the EXIF capture time. It is only a suggestion for `reference_time`, because it often has no time-zone offset and may differ from the document date.
2. **Sanitize.** The browser makes one sanitized copy per image: EXIF (including GPS) stripped, long edge ≤ 2048 px, WebP/JPEG q≈0.8, ≤ 1.5 MB, and ≤ 10 MB per draft in total. **Original bytes never leave the browser.** The sanitized copy is what is stored as evidence and what is sent to the vision model.
3. **Upload.** The upload creates an `IG_ImageDraft`. The server validates the MIME type. Unconfirmed drafts expire after 24 h.
4. **Transcribe.** One vision request covers the whole draft. Each image gets:
   * `original_text`: verbatim, in the original language;
   * `description_zh`: a visual description in Chinese;
   * `detected_dates`: calendar dates found in the image, optionally with a time. Bare clock times such as "21:00" are not dates.

   Only the images that failed are retried. The provider rejects the whole request when any image is invalid, so each image is validated before sending. If the request still fails on one image, that image is marked failed and the rest are re-sent without it ([07](07-architecture.md)).
5. **Review.** The analyst edits `reviewed_text`. Edits are stored separately from the model output, and nothing is re-recognized after an edit.
6. **Confirm.** Confirming creates the Source; its `reviewed_text` is what gets ingested. Skipping the review is allowed but writes a decision record.

In the evidence view, the image sits next to its transcription, which is labelled *机器转写* (or *人工修订* if edited).

## Case brief (案件指引)

The case brief is free-text guidance, for example "重点关注资金流向" or "'老王' 指王建国". It is **not** a source.

* It is versioned. Each ingestion job pins the brief version in effect when it starts.
* It is appended to the extraction instructions and the Q&A system prompt, explicitly marked as guidance and not evidence.
* It is never ingested into the graph and never cited.

## Three tiers, with template-specific meaning

**T1 is best.** Each tier has a default per source type, defined in the template. The analyst can change a source's tier at any time; each change writes a decision record and can be undone.

| Tier | `corporate_intel` | `criminal_case` | `murder_mystery_game` | `mystery_fiction` |
| :--- | :--- | :--- | :--- | :--- |
| **T1** | Official records with strong evidentiary weight (filings, regulator notices, court documents) | Forensic and objective records (autopsy, DNA, CCTV, telecom records) | Rule book / facts confirmed by the host (DM) | Facts stated by an omniscient narrator |
| **T2** | Attributed reporting; official non-binding statements | Documents; neutral witnesses | Clue cards (physical evidence) | Physical and documentary clues in the text |
| **T3** | Anonymous posts, leaks, rumors | Statements by involved parties; hearsay | Character statements (may lie) | Character dialogue and testimony |

**Tier rules:**

* **Support tier.** Each support carries its source's tier.
* **Best tier.** A fact's **best tier** is the best tier among its non-speculative supports. A fact whose supports are all speculative has no best tier and is shown as speculative.
* **Speaker attribution in v1.** Attribution is per source. For 剧本杀 and fiction, enter each character's statement as its own Source with a `speaker`. Per-fact reported-speech caps are in the backlog.
* **Distinct sources.** Corroboration counts distinct Source IDs. Content that is byte-identical after normalization is rejected as a duplicate. Reprints with different text count separately, and judging that is the analyst's responsibility in v1.

## Known limits

These are why tiers are suggestions, not verdicts:

* An unreliable narrator or a forged clue can still mislead. The analyst can re-tier the source.
* Self-interested statements are not modelled separately. Two-axis grading is under Exploration in [02](02-scope.md).
