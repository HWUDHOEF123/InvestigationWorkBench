# IntelGraph: Bi-Temporal GraphRAG Investigation Workbench

> **IntelGraph** is an interactive AI intelligence investigation workbench built on **Bi-Temporal Knowledge Graphs (Graphiti)** and **GraphRAG** technologies. It breaks away from traditional linear conversational interfaces by pairing a spatial graph canvas with dynamic timeline replay, source-reliability tiering, and automated contradiction detection—enabling analysts to reconstruct event chronologies, pinpoint logical conflicts, and execute grounded multi-hop reasoning across multi-source, time-sensitive intelligence streams.

---

## Executive Summary & Core Value Proposition

In forensic accounting, commercial due diligence, geopolitical risk assessment, and open-source intelligence (OSINT), analysts process heterogeneous, fragment-heavy, and potentially contradictory documents (e.g., SEC 8-K/Form 4 filings, regulatory subpoenas, investigative journalism, and anonymous leaks). Traditional LLM and RAG pipelines suffer from three fundamental architectural flaws:

1. **Static Graph Fallacy**: Standard Knowledge Graphs (KGs) assume a static state of the world. When Document A states *"Person X is CEO of Company Y"* ($t_1$) and Document B states *"Person X resigned from Company Y"* ($t_2$), static KGs produce mutating edge overwrites or conflicting parallel facts, erasing the historical trajectory.
2. **Multi-Hop Blind Spots in Vector RAG**: Top-$k$ dense vector retrieval fails to trace multi-step causal or financial chains across disparate entities (e.g., `Government Advisor` $\rightarrow$ `Policy Foundation` $\rightarrow$ `Cloud Vendor` $\rightarrow$ `Open-Source Consortium`).
3. **Black-Box AI Inference**: Generic RAG outputs lack deterministic source anchoring, forcing analysts to manually verify every hallucination-prone claim.

### The IntelGraph Paradigm

* **Bi-Temporal Model**: By leveraging **Graphiti**, IntelGraph explicitly tracks two temporal dimensions: **Event Time** (`valid_at` / `invalid_at`) and **Ingestion Time** (`created_at`). Overwritten facts are never physically deleted; they transition to invalidated historical states (rendered as low-opacity dashed edges).
* **Source Reliability Tiering**: Intelligence sources are strictly bucketed into weighted tiers (Tier 1: Official Regulatory Filings; Tier 2: Reputable Outlets; Tier 3: Unverified/Anonymous Leaks). Contradictions are resolved or flagged deterministically based on tier dominance rather than naïve LLM voting.
* **Deterministic Path Discovery**: Graph algorithms ($O(V+E)$ shortest path) resolve structural connections in $<50\text{ms}$ with zero LLM latency or hallucination, reserving generative AI strictly for qualitative synthesis.

---

## Architectural Principles & Layout Engine

IntelGraph implements a **Headless State + Pluggable Renderer** architecture. The backend graph engine remains decoupled from visual presentation, exposing pure semantic JSON models over REST and Server-Sent Events (SSE).

```mermaid
graph TD
    subgraph "Frontend Application Layer (React + React Flow / XYFlow)"
        UI_Shell["Canvas Shell & Interactive Controllers"]
        Theme_State["Zustand State Store (Bi-Temporal Snapshots)"]
        
        Render_Intel["Intel Dark Mode (Primary Workbench)"]
        Render_Pluggable["Pluggable Theme Tokens (Whiteboard / Retro)"]

        Theme_State -->|Theme Tokens & Frame Data| UI_Shell
        UI_Shell --> Render_Intel
        UI_Shell -.-> Render_Pluggable
    end

    subgraph "Real-Time Streaming & API Gateway"
        API_SSE["FastAPI SSE Server (Incremental Graph Pipeline)"]
        API_REST["REST Gateway (Shortest Path / Reasoning / Export)"]
    end

    subgraph "Core Graph Engine & GraphRAG Middleware"
        Ingest_Pipe["Document Chunking & Ingestion (Docling / PyMuPDF)"]
        Graphiti_Engine["Graphiti Core Engine (Temporal Disambiguation & Entity Resolution)"]
        Reasoning_Agent["Subgraph-in-the-Loop Reasoning Engine"]

        Ingest_Pipe --> Graphiti_Engine
    end

    subgraph "Persistence Layer"
        Neo4j[("Neo4j Database (Nodes, Edges, Bi-Temporal Constraints)")]
        Vector_DB[("Vector Index / Postgres pgvector (Entity & Episode Embeddings)")]
    end

    UI_Shell <-->|SSE Ingestion Pipeline| API_SSE
    UI_Shell <-->|HTTP POST / GET| API_REST
    API_SSE <-- Graphiti_Engine
    API_REST <-- Reasoning_Agent
    Graphiti_Engine <--> Neo4j
    Graphiti_Engine <--> Vector_DB
```

---

## Functional Requirements Specification (PRD)

### Focused Production Feature Matrix

To maximize practical intelligence value, non-essential aesthetic features have been eliminated in favor of robust, low-latency analysis tools.

| Module | Feature Name | Priority | Technical Specification & Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **Ingestion Pipeline** | Stream Parsing & Anchored Growth | **P0** | Text/PDF ingestion streamed via SSE. New entities spawn on canvas using **Anchored Radial Layout** (existing node coordinates are pinned; new nodes expand radially without layout jumping). |
| **Graph Canvas** | Ego-Network & LOD Rendering | **P0** | Infinite canvas built on `@xyflow/react`. Default view renders **Top-15 centrality nodes** (Ego-Network) to eliminate hairball clutter. Double-click expands 1-hop connections. Implements Level-of-Detail (LOD) edge label hiding at `zoom < 0.55`. |
| **Bi-Temporal Engine** | 60fps Snapshot Timeline | **P0** | Bottom timeline console with event-density histogram. Dragging slider filters the graph state at time $T_{\text{as-of}}$ in frontend memory ($<2\text{ms}$). Inactive nodes fade (`opacity: 0`); invalidated edges render as gray dashed lines (`#475569`). |
| **Source Tiering & Conflicts** | Contradiction Alert System | **P0** | Evaluates source weights (Tier 1 > Tier 2 > Tier 3). Higher-tier facts automatically invalidate lower-tier claims (`status: invalidated`). Equal-tier conflicting claims spawn a **Neon Red Pulsing Edge** (`status: conflict`). |
| **Deterministic Pathing** | Shortest Path Discovery | **P0** | Select any 2 nodes to trigger Neo4j Cypher `shortestPath` query ($<50\text{ms}$). Path nodes and edges illuminate while unselected canvas elements dim to 15% opacity. Zero LLM call required. |
| **Targeted Reasoning** | Subgraph-in-the-Loop QA | **P0** | Marquee-select 2–5 nodes and trigger `Deep Reasoning`. Backend extracts the sub-graph triples and associated source episodes, streaming qualitative conclusions to the right inspector pane (TTFT $<1\text{s}$) and pinning an **Emerald AI Hypothesis Node** to the canvas. |
| **Entity Resolution** | Disambiguation Queue | **P0** | Background embedding matcher detects duplicate entity candidates (e.g., `Jensen Huang` vs `黄仁勋`). Prompts the analyst in a side panel queue for one-click Neo4j node merging and edge redirect. |
| **Intelligence Delivery** | Grounded Dossier Export | **P1** | Generates a structured Markdown intelligence dossier from selected subgraphs or timeline slices, complete with executive summaries, timeline breakdown, conflict tables, and verbatim source citations. |

---

## Core System Flows & Performance Architecture

### Flow 1: Low-Latency Ingestion with Anchored Radial Layout

To prevent canvas jitter and layout disruption when new entities are ingested, coordinates of pre-existing nodes are strictly locked.

```mermaid
sequenceDiagram
    autonumber
    actor Analyst as Intelligence Analyst
    participant FE as Graph Canvas (React Flow)
    participant API as FastAPI Gateway
    participant G as Graphiti Engine
    participant LLM as Extraction LLM
    participant DB as Neo4j Database

    Analyst->>FE: Submit Document / Text Snippet (with Reference Time & Tier)
    FE->>API: POST /api/v1/ingest (Optimistic UI state created)
    API->>G: add_episode(text, group_id, reference_time, source_tier)
    G->>LLM: Extract Entities & Triples (Structured JSON Schema)
    LLM-->>G: Return Entity Triples & Temporal Anchors
    G->>DB: Query Existing Entities (Vector & Fuzzy Resolution)
    G->>DB: Perform Temporal Conflict & Invalidation Checks
    alt Higher-Tier Overwrite Detected
        G->>DB: Set existing edge invalid_at = reference_time
        G->>DB: Insert new edge valid_from = reference_time
    else Direct Contradiction Detected
        G->>DB: Insert/Update edge status = 'conflict'
    end
    API-->>FE: Stream SSE Events (node_added, edge_invalidated, conflict_raised)
    FE->>FE: Lock existing node coordinates (x, y)
    FE->>FE: Calculate radial offset for new nodes (400ms transition)
```

### Flow 2: 60fps Zero-Latency Timeline Replay Architecture

* **Performance Bottleneck Elimination**: Timeline scrubbing **never** queries the backend server.
* **Frontend Memory Pipeline**:
  1. Upon workspace load, the complete graph payload (typically $<500$ nodes/edges, $<500\text{KB}$ JSON) is loaded into Zustand state with pre-parsed Unix timestamps (`valid_at_ts`, `invalid_at_ts`).
  2. As the analyst drags the slider to time $T_{\text{as-of}}$, a pure JS evaluation filters visibility in $O(E)$ time ($<2\text{ms}$):
     $$\text{Visible}(e) = (e.\text{valid\_at\_ts} \le T_{\text{as-of}}) \land (e.\text{invalid\_at\_ts} > T_{\text{as-of}} \lor e.\text{invalid\_at\_ts} = \text{null})$$
  3. Nodes hidden at time $T_{\text{as-of}}$ retain pre-computed XY coordinates and toggle CSS properties (`opacity: 0; pointer-events: none`). This prevents layout recalculation jitter and maintains 60fps rendering performance.

### Flow 3: Subgraph-in-the-Loop Reasoning (Dual-Stream Pipeline)

To avoid UI lockup during LLM inference, reasoning uses a dual-stream architecture: text commentary streams instantly to the inspector pane, followed by structured node pinning.

```mermaid
sequenceDiagram
    autonumber
    actor Analyst as Analyst
    participant FE as Canvas & Inspector Pane
    participant API as FastAPI Middleware
    participant DB as Neo4j Graph DB
    participant LLM as LLM Streaming Engine

    Analyst->>FE: Marquee-select Nodes [N1, N2, N3] & click "Deep Reasoning"
    FE->>API: POST /api/v1/reasoning { node_ids: [N1, N2, N3] }
    API->>DB: Extract 1-Hop Subgraph JSON & Source Text Episodes
    DB-->>API: Subgraph Structure & Raw Citations
    API->>LLM: Stream Prompt (Selected Graph Context + Raw Text)
    LLM-->>API: Stream Text Response (Markdown + [Citation IDs])
    API-->>FE: SSE Stream StreamChunk (TTFT < 1s)
    FE->>FE: Render Streamed Text in Inspector Pane (Typing Effect)
    LLM-->>API: Append Terminal JSON Payload { title, confidence, hypothesis_node }
    API-->>FE: Finalize Event
    FE->>FE: Pin Emerald Hypothesis Node at centroid of [N1, N2, N3]
```

---

## UI/UX Visual & Design Specifications (Intel Dark Mode)

### Canvas Layout & Geometry

```text
+-------------------------------------------------------------------------------------------------------------------+
|  IntelGraph // Investigation Board: [Case: Nvidia Leadership Transition]          [Theme: Intel Dark v] [Zoom: 100%]  |
+----------------------+-------------------------------------------------------------------+------------------------+
| Files & Data Tiers   |  Main Spatial Graph Canvas (Infinite React Flow Viewport)         | Inspector Pane         |
| -------------------- |                                                                   | (Right Drawer)         |
| [+] Ingest Intelligence|  (Cyan) [Jensen Huang] -----(Active Edge)-----> (Purple) [Nvidia]  | ---------------------- |
|                      |         |                                           ^             | [Properties] [AI QA]   |
| [Tier 1] SEC_8K.pdf  |         | (Invalidated: Gray Dashed)                |             |                        |
| [Tier 2] Media_WSJ.txt|        v                                           | (Conflict)  | Entity: Jensen Huang   |
| [Tier 3] Leak_X.txt  |  (Gold) [Resignation Rumor] <====================== (Gold) [8-K]  | Type: Person           |
|                      |                                                                   | Source Tier: Tier 1    |
| Filter Controls      |  ┌─────────────────────────────────────────────────────────────┐ | Valid: 2023-01 ~ Present|
| [x] Person           |  | Marquee Toolbar: [Deep Reasoning] [Shortest Path] [Clear]   | |                        |
| [x] Organization     |  └─────────────────────────────────────────────────────────────┘ | Verbatim Excerpt:      |
| [x] Conflicts Only   |                                                                   | "Per SEC Form 8-K..."  |
+----------------------+-------------------------------------------------------------------+------------------------+
| Timeline Scrubbing   [|<] [ Play ] [>|]  --------------------●----------------------------- 2025-10-28 (As-of) |
| Console              Histogram:   ▄█   █  █  ▅ █                                                          |
+-------------------------------------------------------------------------------------------------------------------+
```

### Visual Semantics & Color Palette

| Category | Visual Representation | Hex Code | Design Intent |
| :--- | :--- | :--- | :--- |
| **Canvas Background** | Dark Cyan-Grid Pattern | `#0B0F19` | High-contrast dark theme optimized for low eye fatigue. |
| **Person Entity** | Glowing Circular Badge + Icon | `#06B6D4` (Cyan) | Individuals, executives, regulators, or whistleblowers. |
| **Organization Entity** | Glowing Circular Badge + Icon | `#A855F7` (Purple) | Corporations, offshore entities, government agencies. |
| **Event / Filing Entity** | Diamond / Rounded Card | `#F59E0B` (Gold) | SEC filings, trade dates, press releases, leaks. |
| **AI Hypothesis Node** | Glowing Emerald Card + Star Badge | `#10B981` (Emerald) | Synthetic nodes generated via Subgraph-in-the-Loop reasoning. |
| **Active Edge** | Solid Line + Directional Arrow | `#64748B` (Slate) | Confirmed fact valid at selected $T_{\text{as-of}}$. |
| **Invalidated Edge** | Thin Dashed Line (Opacity 0.35) | `#475569` (Gray) | Superseded historical facts ($t < T_{\text{as-of}}$). |
| **Conflict Edge** | Heavy Dashed + Pulsing Animation | `#EF4444` (Neon Red) | Unresolved or active semantic contradictions. |

---

## Production Verification Benchmark: Nvidia Leadership Transition

To validate systemic performance under complex conditions, IntelGraph utilizes a standard, multi-threaded intelligence benchmark: *The Nvidia Leadership Transition & Geopolitical Tech Dynamics*.

### Benchmark Dataset Dynamics

This scenario integrates three concurrent macro narratives:
1. **Regulatory & Antitrust Pressures**: DOJ Antitrust Division investigations into CUDA software lock-in alongside Biden-Harris Administration AI policy mandates.
2. **Geopolitical Trade Restrictions**: BIS export controls targeting China-specific AI silicon (H20/B20) and third-country transshipment enforcement.
3. **Architecture Warfare**: Open-source model proliferation (DeepSeek, Llama) and hardware abstraction initiatives (UXL Foundation / Triton).

### 4-Phase Time-Series Verification Dataset

```text
Phase 1: Macro Pressure Building (T1: Oct 01 - Oct 10)
├── Source 1 [Tier 1 / BIS Subpoena]: Inquiry into third-party AI chip transshipments.
├── Source 2 [Tier 1 / DOJ Document]: CID issued investigating CUDA software bundling practices.
└── Source 3 [Tier 2 / Tech Media]: UXL Foundation launches cross-platform CUDA abstraction layer.

Phase 2: Leak & Contradiction Stage (T2: Oct 14 - Oct 16)
├── Source 4 [Tier 3 / Anonymous Post]: Leaks claim CEO Jensen Huang to resign over board conflict on China strategy.
└── Source 5 [Tier 2 / PR Statement]: Nvidia PR issues formal denial: "Management rumors are completely baseless."
    └── [System Action]: Generates Neon Red Conflict Edge (Tier 3 Leak vs Tier 2 PR Statement).

Phase 3: Hidden Network Discovery (T3: Oct 21)
└── Source 6 [Tier 2 / Investigative Journalism]: Reveals Lead DOJ Special Advisor previously served on Policy Board 
    of Foundation funded by UXL Consortium members.
    └── [System Action]: Enables 3-hop Shortest Path: (DOJ Advisor) -> (Foundation) -> (Cloud Vendor) -> (UXL).

Phase 4: Regulatory Settlement & Invalidation Stream (T4: Oct 28 - Live Test Drop)
└── Source 7 [Tier 1 / SEC Form 8-K]: Official Filing:
    1. Jensen Huang transitions from CEO to Executive Chairman & Chief Architect.
    2. Former Regulatory Legal Executive appointed new CEO.
    3. Nvidia open-sources low-level CUDA runtime APIs to settle DOJ inquiry.
    └── [System Action via SSE Stream]:
        • (Jensen Huang)-[is CEO]->(Nvidia) edge gets invalid_at: Oct 28 -> Fades to Gray Dashed Edge.
        • New active edge added: (Jensen Huang)-[is Executive Chairman]->(Nvidia).
        • Prior denials and rumors marked as Refuted / Superseded.
```

---

## Environment & Setup Instructions

### 1. System Requirements

* **Python Engine**: `Python >= 3.11`
* **Node Environment**: `Node.js >= v20.0.0` (LTS)
* **Package Manager**: `pnpm >= 8.x`
* **Graph Database**: Neo4j Community or Enterprise `5.x+` (with APOC plugin enabled)
* **Vector Store**: PostgreSQL `16` with `pgvector` extension OR Neo4j Native Vector Index

### 2. Backend Environment Variables (`.env`)

```ini
# Graphiti & Neo4j Settings
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password_change_me
GRAPHITI_GROUP_ID=nvidia_investigation_01

# LLM Providers (OpenAI Structured Output Mode Supported)
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o

# Vector & Embeddings
EMBEDDING_MODEL=text-embedding-3-small
POSTGRES_DB_URL=postgresql://user:pass@localhost:5432/intelgraph
```

### 3. Infrastructure Bootstrap (Docker Compose)

The project includes a streamlined `docker-compose.yml` for local development:

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5.18.0-community
    container_name: intelgraph-neo4j
    ports:
      - "7474:7474" # HTTP Browser
      - "7687:7687" # Bolt Protocol
    environment:
      - NEO4J_AUTH=neo4j/password_change_me
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*
    volumes:
      - neo4j_data:/data

  postgres:
    image: pgvector/pgvector:pg16
    container_name: intelgraph-postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=intelgraph
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - pg_data:/var/lib/postgresql/data

volumes:
  neo4j_data:
  pg_data:
```

### 4. Verification Dataset Script Execution

To initialize the backend database with the benchmark verification dataset:

```bash
# Initialize Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Seed Phases T1 through T3 into Neo4j
python scripts/seed_db.py --case nvidia_transition --phase T1-T3

# Start FastAPI SSE server
uvicorn app.main:app --reload --port 8000
```

To run the frontend:

```bash
cd frontend
pnpm install
pnpm dev # Serves canvas UI at http://localhost:5173
```

---

## References & Underlying Research

1. **Graphiti Core Engine**: [github.com/getzep/graphiti](https://github.com/getzep/graphiti)  
   *Reference for temporal knowledge graph modeling, episode ingestion, and incremental entity resolution.*
2. **React Flow / XYFlow Documentation**: [reactflow.dev](https://reactflow.dev/)  
   *Reference for high-performance canvas state, custom node/edge rendering, and viewport controls.*
3. **Neo4j APOC & Shortest Path Procedures**: [neo4j.com/docs/apoc/current](https://neo4j.com/docs/apoc/current/)  
   *Reference for deterministic pathfinding algorithms.*
4. **Microsoft GraphRAG Architecture**: [github.com/microsoft/graphrag](https://github.com/microsoft/graphrag)  
   *Reference for global query synthesis and community summarization techniques.*

---

**IntelGraph Development Team** | *Version: 1.0.0-PRD* | *License: MIT*