# 03 · Domain Model

> Index: [README](README.md) · Depends on: [01-overview](01-overview.md) · Related: [04](04-sources-and-tiers.md), [05](05-time-and-fact-states.md), [06](06-contradiction-policy.md)

## Core objects

| Object | Meaning | Owner |
| :--- | :--- | :--- |
| **Case** | One investigation: a template and version, a time zone, a versioned case brief, an optional story anchor, and settings. The settings hold thinking levels for extraction, classification and the Q&A default; each defaults to `off`. Maps to a Graphiti `group_id`. | IntelGraph |
| **Source** | One unit of evidence (document, confirmed image set or note) with tier, `reference_time`, optional speaker and flags. See [04](04-sources-and-tiers.md). | IntelGraph |
| **Chunk** | A deterministic slice of a Source's normalized text, with character offsets and a two-phase checkpoint: *staged* (the P1 capture is persisted before Graphiti writes) and *complete* (the policy finished, so the revision can be published). See [F1](features/F1-source-intake.md). | IntelGraph |
| **Episode** | The Graphiti `EpisodicNode` for one chunk. It is named `{source_id}:{chunk_index}`, and its `valid_at` is the Source's `reference_time`. | Graphiti |
| **Entity** | A Graphiti `EntityNode`, typed per the ontology below. | Graphiti (+ merge projection) |
| **Fact** | A Graphiti `EntityEdge`: relation name, Chinese `fact` text, `valid_at` / `invalid_at`, `episodes`, `attributes`. | Graphiti |
| **Support** | `IG_FactSupport`: one `(fact, source, episode)` link. It is created whenever an episode creates a fact or re-confirms it as a duplicate. It carries the source's tier, speculative/synthetic flags, an automatically located excerpt, and a `stated_end` when the source states an end for the claim ([06](06-contradiction-policy.md) P1). | IntelGraph |
| **Conflict** | A recorded contradiction between facts, with its kind, suggestion, state and adjudication history. See [06](06-contradiction-policy.md). | IntelGraph |
| **Decision record** | An append-only audit entry for each policy decision and analyst action (closure kept / written back, stated end applied / claimed / confirmed / dismissed, adjudication, merge, tier change, skipped review, undo). It stores before/after values and is the basis for undo. | IntelGraph |
| **Revision** | A monotonically increasing version of the case's effective graph, published after each chunk's policy completes and after each analyst mutation. | IntelGraph |

## Ownership and write-back

* Graphiti owns entities, edges and episodes. IntelGraph state lives in `IG_*` nodes in the same Neo4j database, keyed by Graphiti UUIDs:
  * `IG_Case`, `IG_Source`, `IG_Chunk`
  * `IG_ImageDraft`
  * `IG_FactSupport`
  * `IG_Conflict`
  * `IG_Merge`
  * `IG_Layout`
  * `IG_Decision`
* **Only one write to Graphiti data is allowed.** When P3 or P6 overrides a closure, or applies a stated end, the Graphiti adapter writes `invalid_at` / `expired_at` back onto that edge. It stores the original values in a decision record and restores them on undo.
* Write-back keeps Graphiti's own later contradiction checks consistent with what the analyst sees. Graphiti reads these fields from the database and does not see the overlay.
* All other Graphiti properties are read-only to IntelGraph.
* The **Snapshot Builder** combines Graphiti data with merges, supports, conflicts and flags into the *effective graph* for one revision. It caches that graph for the snapshot and Q&A.

## Ontology

**Core entity types.** These are fixed across all scenarios, so shapes, colors and code stay stable. They extend the police-standard POLE model (Person, Object, Location, Event):

| Type | Covers | Finance | Criminal | 剧本杀 / fiction |
| :--- | :--- | :--- | :--- | :--- |
| `Person` | individuals, characters | executives, officials | suspects, victims, witnesses | characters |
| `Organization` | companies, agencies, groups | companies, regulators | gangs, employers | families, factions |
| `Location` | places, rooms, addresses | HQs, jurisdictions | crime scene, addresses | rooms of the manor |
| `Object` | physical or documentary items, accounts, assets, products | chips, filings, accounts | weapon, phone, vehicle | clue items, letters |
| `Event` | actions, meetings, transactions, incidents | investigations, filings, transitions | the crime, calls, transfers | the murder, a quarrel |
| `Concept` | abstract topics | policies, technologies (CUDA) | motives, debts | secrets, wills, rules |

If Graphiti returns an entity with no core label, it is shown as `Concept` with an "未分类" badge. When a node carries several labels, the first core type in the order of the table above wins.

**Core relation types.** These are English names, available in every template, and are passed to Graphiti as `edge_types` plus `edge_type_map`:

| Relation | Typed attributes | Meaning |
| :--- | :--- | :--- |
| `AFFILIATED_WITH` | `role` | Role or membership (CEO, employee, member) |
| `SOCIAL_TIE` | `kind` | Family, romantic, friendship, enmity, business partner |
| `LOCATED_AT` | — | A person or object at a location; the event-time interval gives whereabouts and alibis |
| `PARTICIPATED_IN` | `role` | Initiator, victim, witness, party |
| `OCCURRED_AT` | — | An event at a location |
| `OWNS` | — | Ownership or possession |
| `TRANSFERRED` | `item`, `amount` | A flow of money or goods |
| `COMMUNICATED_WITH` | `channel` | Contact between parties |
| `CAUSED` | — | A causal link between events |
| `INVESTIGATES` | — | Investigation of a party |
| `RELATED_TO` | — | Fallback; also used for any Graphiti relation without a custom type |

* **Shared attributes on every relation** come from a common Pydantic base:
  * `modality`: `stated` | `planned` | `denied` | `suspected`. Missing values are normalised to `stated` at the adapter boundary.
  * `asserted_by`: the speaker of reported speech.
* Graphiti keeps one attribute map per edge, shared across duplicate supports. For that reason, `asserted_by` is informational in v1 (shown in the inspector) and does not affect tiers.
* The snapshot exposes typed attributes as `Fact.attributes`.

## Case templates

* A template is a Pydantic-validated config held in a registry. Each case pins its template **and version**.
* Templates reuse the shared entity and edge models. They contain no custom code.

A template defines:

* subtype labels (e.g. `Person.subtype = 角色`);
* extra relation types and the `edge_type_map`;
* the **claim key** per relation: the typed attributes that identify the same claim, e.g. `role` for `AFFILIATED_WITH` and `kind` for `SOCIAL_TIE`. Used by P3 stated ends ([06](06-contradiction-policy.md));
* extraction instructions, passed on every episode as Graphiti's `custom_extraction_instructions`:
  * zh-CN fact text and summaries;
  * naming policy (one entity per real-world referent; native or most authoritative canonical name; other-language names as aliases), followed by the case's known-alias list;
  * atomic facts (one claim per fact);
  * plans and denials expressed through `modality`;
  * the case's UTC offset, so that extracted times are case-local ([05](05-time-and-fact-states.md));
* tier labels and the default tier per source type ([04](04-sources-and-tiers.md));
* time mode (`absolute` | `story`) and default granularity ([05](05-time-and-fact-states.md)).

| Template | Extra relations | Time | v1 status |
| :--- | :--- | :--- | :--- |
| `corporate_intel` | `FUNDS`, `REGULATES`, `ANNOUNCES` | absolute, day | To be validated in v1 (Scenario A) |
| `murder_mystery_game` | `SUSPECTS`, `HAS_MOTIVE`, `USED` | story, minute | To be validated in v1 (Scenario B) |
| `criminal_case` | `HAS_MOTIVE`, `USED` | absolute, minute | Draft config |
| `mystery_fiction` | `SUSPECTS`, `HAS_MOTIVE` | story, minute | Draft config |

## Merges (canonical projection)

* **The mapping.** A merge is `IG_Merge { alias_id → canonical_id }` between two entities of the same type in the same case.
  * Mappings resolve to a root: merging into an alias targets that alias's canonical.
  * A merge that would create a cycle is rejected.
* **What the Snapshot Builder does:**
  * Remaps fact endpoints to the canonical ID.
  * Unions aliases and supports.
  * Uses the earliest `first_seen` of the merged entities.
  * Keeps every original fact as a separate (parallel) fact.
  * Shows a fact that becomes a self-loop only in the inspector.
* **Raw data is kept.** Raw UUIDs and the alias's layout position are retained, so undo is exact.
* **Undo.** A merge can be undone only if no later merge depends on it; otherwise those dependent merges must be undone first.
* **Later ingestion.** Graphiti keeps resolving against its raw nodes.
  * New edges attached to either raw node are remapped automatically.
  * A brand-new raw node for a known alias needs another merge.
  * To reduce such repeats, the case's known-alias list is added to the extraction instructions.
