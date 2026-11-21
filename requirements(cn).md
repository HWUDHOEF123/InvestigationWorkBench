# IntelGraph: 双时态 GraphRAG 情报调查工作台

> **IntelGraph** 是一款基于 **双时态知识图谱（Graphiti）** 与 **GraphRAG** 技术的交互式 AI 情报调查工作台。它打破了传统线性对话框范式，通过“空间图谱画布 + 时间轴动态回放 + 信源置信度分级 + 自动化矛盾检测”，帮助分析师在海量、碎片化且强时效的多源情报流中，快速还原事件脉络、定位逻辑冲突并完成可溯源的多跳推演。

## 一、 核心价值与问题定义

在财务审计、商业尽调、地缘政治风险评估与开源情报（OSINT）分析中，分析师需要处理海量存在真伪冲突与时间差的非结构化文档（如 SEC 8-K/Form 4 申报文件、监管传票、深度调查报道与匿名爆料）。传统的 LLM 和 RAG 管线存在三个致命的工程缺陷：

1. **静态图谱谬误（Static Graph Fallacy）**：传统知识图谱（KG）假定世界是静态的。当文档 A 指出 *“X 担任 Y 公司 CEO”*（$t_1$），而文档 B 指出 *“X 已辞去 Y 公司 CEO 职务”*（$t_2$）时，静态图谱会导致边被直接覆盖更新，或产生互相矛盾的平行事实，彻底丢失历史演变轨迹。

2. **向量 RAG 的多跳检索盲区**：基于 Top-$k$ 密集的向量检索无法跨越多个实体追踪隐蔽的因果链或利益输送链（例如：`政府顾问` $\rightarrow$ `政策基金会` $\rightarrow$ `云厂商` $\rightarrow$ `开源算力联盟`）。

3. **AI 推理的黑盒感**：通用 RAG 的输出缺乏确定性的数据源锚定，分析师必须花费大量精力人工验证易幻觉的结论。

### IntelGraph 的解法与创新

* **双时态数据模型**：依托 **Graphiti**，IntelGraph 显式追踪两个时间维度：**事件发生时间（Event Time: `valid_at` / `invalid_at`）** 和 **数据入库时间（Ingestion Time: `created_at`）**。过期的事实绝不会被物理删除，而是自动转换为失效的历史状态（在画布上渲染为半透明灰色虚线）。

* **信源分级置信度体系**：情报来源被严格划分为不同权重的级别（Tier 1: 官方监管公告；Tier 2: 权威媒体报道；Tier 3: 未经证实/匿名爆料）。当不同信源产生语义冲突时，系统依据权重优先级进行自动置信判别或警报呈现，而非盲目依赖 LLM 投票。

* **确定性路径发现**：图算法（$O(V+E)$ 最短路径）可在 $<50\text{ms}$ 内完成结构化关联检索，无 LLM 延迟且零幻觉，将生成式 AI 严格限制在定性归因与简报生成阶段。

## 二、 架构原则与分层设计

IntelGraph 采用 **“Headless State + Pluggable Renderer（数据与视图解耦）”** 架构设计。后端图引擎与前端视觉呈现解耦，仅通过 REST 和 SSE（Server-Sent Events）暴露纯语义 JSON 模型。

```
graph TD
    subgraph "前端应用层 (React + React Flow / XYFlow)"
        UI_Shell["画布容器与交互控制器"]
        Theme_State["Zustand 状态库 (双时态快照)"]
        
        Render_Intel["情报分析风 (默认主工作台)"]
        Render_Pluggable["主题 Token 适配层 (白板风 / 侦探风)"]

        Theme_State -->|主题 Token & 帧数据| UI_Shell
        UI_Shell --> Render_Intel
        UI_Shell -.-> Render_Pluggable
    end

    subgraph "实时流式与 API 网关"
        API_SSE["FastAPI SSE 服务器 (增量图谱推送)"]
        API_REST["REST 网关 (最短路径 / 深度推理 / 简报导出)"]
    end

    subgraph "核心图引擎与 GraphRAG 中间件"
        Ingest_Pipe["文档切片与入库管线 (Docling / PyMuPDF)"]
        Graphiti_Engine["Graphiti 核心引擎 (双时态消除歧义与实体消歧)"]
        Reasoning_Agent["子图推理 Agent (Subgraph-in-the-Loop)"]

        Ingest_Pipe --> Graphiti_Engine
    end

    subgraph "持久化层"
        Neo4j[("Neo4j 数据库 (节点、边、双时态约束)")]
        Vector_DB[("向量索引 / Postgres pgvector (实体与线索 Embedding)")]
    end

    UI_Shell <-->|SSE 流式入库| API_SSE
    UI_Shell <-->|HTTP POST / GET| API_REST
    API_SSE <-- Graphiti_Engine
    API_REST <-- Reasoning_Agent
    Graphiti_Engine <--> Neo4j
    Graphiti_Engine <--> Vector_DB
```

## 三、 系统功能需求规范 (PRD)

### 落地功能矩阵（去伪存真版）

聚焦高价值的情报分析硬能力，砍掉繁琐花哨的非必要交互：

| 模块 | 功能名称 | 优先级 | 技术规范与验收标准 |
| ----- | ----- | ----- | ----- |
| **线索入库管线** | 流式解析与增量生长 | **P0** | 文本/PDF 导入后通过 SSE 流式推送。新节点在画布上采用**锚定式局部布局（Anchored Radial Layout）**：已有节点坐标强制锁定，新节点按径向避让生成，绝不引起整体布局乱跳。 |
| **情报主画布** | Ego-Network 与 LOD 渲染 | **P0** | 基于 `@xyflow/react` 实现无限画布。默认仅渲染**中心度 Top-15 实体（焦点网络）**以消除“毛球效应”；双击节点按需展开 1 跳关联。缩放比例 `zoom < 0.55` 时自动隐藏连线文字（LOD）。 |
| **双时态引擎** | 60fps 零延迟时间轴 | **P0** | 底部常驻时间轴与情报密度柱状图。拖动滑块时纯前端内存筛选历史时间点 $T_{\text{as-of}}$ 的图谱快照（$<2\text{ms}$）。未发生实体隐藏，失效边渲染为灰色虚线（`#475569`）。 |
| **信源分级与矛盾检测** | 事实冲突警报系统 | **P0** | 评估信源权重（Tier 1 > Tier 2 > Tier 3）。高权重事实自动打标覆盖低权重断言（`status: invalidated`）；同权重互斥事实自动生成**红色脉冲警报边**（`status: conflict`）。 |
| **确定性寻路** | 最短路径发现 | **P0** | 框选画布任意 2 个节点触发 Neo4j `shortestPath` 查询（$<50\text{ms}$）。高亮命中路径上的节点与边，其余无关节点自动压暗至 15% 透明度，零 LLM 开销。 |
| **框选子图推理** | Subgraph-in-the-Loop QA | **P0** | 框选 2–5 个节点发起深度推理。后端提取子图三元组与关联原文线索，右侧抽屉流式吐出推理结论（TTFT $<1\text{s}$），并在画布中心生成一张**翡翠绿 AI 假设节点**。 |
| **实体消歧** | 候选消歧审核队列 | **P0** | 后端 Embedding 向量匹配器自动识别疑似同义实体（如 `Jensen Huang` 与 `黄仁勋`），在侧边栏弹出队列卡片，用户点击一次即可完成 Neo4j 节点合并与边重定向。 |
| **情报输出** | 可溯源研判简报导出 | **P1** | 框选子图或选择特定时间切片，一键生成结构化 Markdown 简报，包含研判摘要、时间线复盘表、矛盾清单及包含原文引用角标的附录。 |

## 四、 核心数据流与低延迟架构

### 流程 1：锚定式局部布局与流式入库

为避免新实体入库时画布整体坐标重排导致用户视觉记忆错乱，系统在增量更新时严格冻结已有节点的坐标。

```
sequenceDiagram
    autonumber
    actor Analyst as 情报分析师
    participant FE as 前端画布 (React Flow)
    participant API as FastAPI 网关
    participant G as Graphiti 引擎
    participant LLM as 抽取大模型
    participant DB as Neo4j 数据库

    Analyst->>FE: 提交文档/短文本 (指定发生时间与信源 Tier)
    FE->>API: POST /api/v1/ingest (建立乐观 UI 状态)
    API->>G: add_episode(text, group_id, reference_time, source_tier)
    G->>LLM: 抽取实体与三元组 (结构化 JSON Schema)
    LLM-->>G: 返回实体三元组与时间锚点
    G->>DB: 查询已有实体 (向量与模糊匹配)
    G->>DB: 执行时间冲突与失效校验
    alt 发现更高权重的覆盖事实
        G->>DB: 更新旧边 invalid_at = reference_time
        G->>DB: 插入新边 valid_from = reference_time
    else 发现同权重的语义冲突
        G->>DB: 插入/更新边 status = 'conflict'
    end
    API-->>FE: SSE 流推送事件 (node_added, edge_invalidated, conflict_raised)
    FE->>FE: 锁定已有节点坐标 (x, y)
    FE->>FE: 计算新节点的径向偏移坐标 (400ms 平滑过渡)
```

### 流程 2：前端内存 60fps 零延迟时间轴回放

* **性能瓶颈消除**：拖动时间轴滑块**严禁**向后端发起网络请求。

* **前端内存计算管线**：

  1. 加载案件时，全量图谱 JSON（通常 $<500$ 节点/边，体积 $<500\text{KB}$）一次性载入 Zustand 状态库，并预解析 Unix 时间戳（`valid_at_ts`, `invalid_at_ts`）。

  2. 拖动滑块至时间点 $T_{\text{as-of}}$ 时，前端执行 $O(E)$ 级别的内存过滤（耗时 $<2\text{ms}$）：
     

     $$
     \text{Visible}(e) = (e.\text{valid\_at\_ts} \le T_{\text{as-of}}) \land (e.\text{invalid\_at\_ts} > T_{\text{as-of}} \lor e.\text{invalid\_at\_ts} = \text{null})
     $$

  3. 在 $T_{\text{as-of}}$ 未生效的节点，保留其预先算好的 `(x, y)` 坐标，仅切换 CSS 属性（`opacity: 0; pointer-events: none`），从而实现 60fps 的丝滑回放且零布局抖动。

### 流程 3：框选子图推理双轨流式输出

为避免 LLM 生成时间过长造成页面假死，推理过程采用“文本打字机 + 节点落盘”双轨流式机制：

```
sequenceDiagram
    autonumber
    actor Analyst as 分析师
    participant FE as 画布 & 右侧抽屉
    participant API as FastAPI 中间件
    participant DB as Neo4j 图数据库
    participant LLM as LLM 流式引擎

    Analyst->>FE: 框选节点 [N1, N2, N3] 并点击 "深度推理"
    FE->>API: POST /api/v1/reasoning { node_ids: [N1, N2, N3] }
    API->>DB: 提取 1-Hop 子图 JSON 与关联原文 Episode
    DB-->>API: 返回子图结构与原文引用
    API->>LLM: 发送 Prompt (子图上下文 + 原文线索)
    LLM-->>API: 流式返回文本 (Markdown + [引用编号])
    API-->>FE: SSE 流推送 StreamChunk (首字延迟 TTFT < 1s)
    FE->>FE: 在右侧抽屉渲染文本 (打字机效果)
    LLM-->>API: 追加尾部 JSON 元数据 { title, confidence, hypothesis_node }
    API-->>FE: 完成事件推送
    FE->>FE: 在 [N1, N2, N3] 几何中心生成翡翠绿 AI 假设卡片
```

## 五、 UI/UX 视觉与设计规范 (Intel Dark Mode)

### 画布布局与几何区域

```
+-------------------------------------------------------------------------------------------------------------------+
|  IntelGraph // 情报调查工作台: [案件: 英伟达高层变动]                            [主题: 情报分析风 v] [缩放: 100%]  |
+----------------------+-------------------------------------------------------------------+------------------------+
| 线索与信源分级       |  中央空间图谱画布 (无限 React Flow 视口)                          | 情报与推理抽屉         |
| -------------------- |                                                                   | (右侧折叠面板)         |
| [+] 注入突发线索     |  (青色) [黄仁勋] --------(生效实线)--------> (紫色) [英伟达]     | ---------------------- |
|                      |         |                                           ^             | [属性详情] [AI问答]    |
| [Tier 1] SEC_8K.pdf  |         | (历史失效边: 灰色虚线)                    |             |                        |
| [Tier 2] Media_WSJ.txt|        v                                           | (冲突警报)  | 实体: 黄仁勋           |
| [Tier 3] Leak_X.txt  |  (金色) [离职传闻] <====================== (金色) [8-K 公告]      | 类型: 人物 (Person)    |
|                      |                                                                   | 信源等级: Tier 1       |
| 实体筛选             |  ┌─────────────────────────────────────────────────────────────┐ | 生效期: 2023-01 ~ 至今 |
| [x] 人物 (Person)    |  | 框选快捷条: [AI 深度推理] [发现隐蔽路径] [清除选择]          | |                        |
| [x] 组织 (Org)       |  └─────────────────────────────────────────────────────────────┘ | 原始摘录:              |
| [x] 仅看矛盾冲突     |                                                                   | "据 SEC Form 8-K..."  |
+----------------------+-------------------------------------------------------------------+------------------------+
| 时间轴控制台         [|<] [ 播放 ] [>|]  --------------------●----------------------------- 2025-10-28 (当前)  |
|                      情报密度:    ▄█   █  █  ▅ █                                                          |
+-------------------------------------------------------------------------------------------------------------------+
```

### 视觉语义与色彩规范

| 元素类别 | 视觉形态 | 色彩规范 (Hex) | 设计意图与含义 |
| ----- | ----- | ----- | ----- |
| **画布背景** | 暗黑深蓝网格 | `#0B0F19` | 高对比度暗色主题，降低长久盯着屏幕的视觉疲劳。 |
| **人物实体（Person）** | 发光圆形徽章 + 人物图标 | `#06B6D4` (青色) | 关键个人、高管、监管人员、爆料人。 |
| **组织实体（Organization）** | 发光圆形徽章 + 建筑图标 | `#A855F7` (紫色) | 公司、离岸实体、政府监管机构。 |
| **事件/公告（Event）** | 菱形 / 圆角卡片 | `#F59E0B` (金色) | SEC 申报文件、交易日期、官方发布会、爆料。 |
| **AI 假设节点（Hypothesis）** | 发光边框卡片 + 星标 | `#10B981` (翡翠绿) | 框选子图推理后在画布落盘的结构化结论节点。 |
| **生效关系边（Active）** | 实线 + 方向箭头 | `#64748B` (蓝灰) | 在当前时间点 $T_{\text{as-of}}$ 生效的确定事实。 |
| **失效历史边（Invalidated）** | 细虚线 (透明度 0.35) | `#475569` (暗灰) | 已被新证据覆盖的历史事实（$t < T_{\text{as-of}}$）。 |
| **矛盾冲突边（Conflict）** | 粗虚线 + 呼吸脉冲动效 | `#EF4444` (警示红) | 尚未解决或存在直接语义冲突的线索。 |

## 六、 功能验证测试集：《英伟达高层变动与算力格局》

为确保系统工程落地的严谨性，开发阶段采用该标准测试集（Seed Dataset）验证所有 P0/P1 功能。

### 测试集背景框架

本数据集模拟了三个真实交织的宏观脉络：

1. **监管与反垄断压力**：美国司法部（DOJ）反垄断司对 CUDA 闭源捆绑的调查，以及白宫 AI 政策指令。

2. **地缘政治出口管制**：商务部工业与安全局（BIS）对特供芯片（H20/B20）的审查与转口贸易追查。

3. **算力生态竞争**：开源模型（DeepSeek、Llama）崛起与跨平台算力联盟（UXL 基金会）对 CUDA 护城河的解构。

### 四阶段测试数据

```
阶段 1: 暗流合围期 (T1: 10月01日 - 10月10日)
├── 线索 1 [Tier 1 / BIS 问询函]: 启动对第三国 AI 算力转口贸易的审查。
├── 线索 2 [Tier 1 / DOJ 调查传票]: 向英伟达发出 CUDA 软件捆绑销售调查问询。
└── 线索 3 [Tier 2 / 科技媒体]: UXL 算力联盟发布跨平台 CUDA 替代编译器 2.0。

阶段 2: 爆料与矛盾冲突期 (T2: 10月14日 - 10月16日)
├── 线索 4 [Tier 3 / 匿名爆料]: 爆料称 CEO 黄仁勋因对华战略分歧与董事会决裂，拟辞去 CEO。
└── 线索 5 [Tier 2 / 官方公关]: 英伟达辟谣声明：“高层变动传闻纯属恶意捏造。”
    └── [系统动作]: 生成红色矛盾警报边 (Tier 3 爆料 vs Tier 2 辟谣)。

阶段 3: 隐蔽政商关系发现 (T3: 10月21日)
└── 线索 6 [Tier 2 / 深度报道]: 披露 DOJ 主导调查的特别顾问，此前曾任某开源基金会理事，
    而该基金会主要金主为 UXL 联盟核心成员。
    └── [系统动作]: 触发 3 跳最短路径发现: (DOJ 顾问) -> (基金会) -> (云厂商) -> (UXL 联盟)。

阶段 4: 正式公告与失效更新 (T4: 10月28日 - 现场实时注入测试)
└── 线索 7 [Tier 1 / SEC 8-K 公告]: 正式文件：
    1. 黄仁勋卸任 CEO，转任执行董事长兼首席架构师；
    2. 任命前大型科技合规高管出任新任 CEO；
    3. 同步开源部分底层 CUDA 运行时 API 以平息反垄断调查。
    └── [系统 SSE 增量更新动作]:
        • (黄仁勋)-[担任CEO]->(英伟达) 边打上 invalid_at: 10-28 -> 平滑变为灰色虚线。
        • 插入新生效边: (黄仁勋)-[担任执行董事长]->(英伟达)。
        • 此前的离职传闻与公关辟谣均自动标记为已证伪/已过时。
```

## 七、 环境要求与快速启动

### 1. 开发环境要求

* **Python 依赖**: `Python >= 3.11`

* **前端环境**: `Node.js >= v20.0.0` (LTS)

* **包管理器**: `pnpm >= 8.x`

* **图数据库**: Neo4j Community 或 Enterprise `5.x+` (需安装 APOC 插件)

* **向量数据库**: PostgreSQL `16`（配 `pgvector` 扩展）或 Neo4j 原生向量索引

### 2. 后端环境变量配置 (`.env`)

```env
# Graphiti 与 Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password_change_me
GRAPHITI_GROUP_ID=nvidia_investigation_01

# LLM 供应商 (支持 OpenAI Structured Output)
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o

# Vector & Embeddings
EMBEDDING_MODEL=text-embedding-3-small
POSTGRES_DB_URL=postgresql://user:pass@localhost:5432/intelgraph
```

### 3. 一键启动 Docker Compose (本地数据库)

项目根目录提供了用于快速拉起数据库环境的 `docker-compose.yml`：

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

### 4. 数据灌入与服务启动

灌入测试集并启动后端：

```bash
# 创建并激活 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 将测试数据 T1~T3 灌入 Neo4j
python scripts/seed_db.py --case nvidia_transition --phase T1-T3

# 启动 FastAPI 服务
uvicorn app.main:app --reload --port 8000
```

启动前端：

```bash
cd frontend
pnpm install
pnpm dev # 在 http://localhost:5173 打开工作台 UI
```

## 八、 参考链接与研究文献

1. **Graphiti 核心图引擎**: [github.com/getzep/graphiti](https://github.com/getzep/graphiti)

   *关于双时态知识图谱建模、线索抽取与增量实体消歧的实现参考。*

2. **React Flow / XYFlow 官方文档**: [reactflow.dev](https://reactflow.dev/)

   *高性能空间画布状态控制、自定义节点/边组件渲染参考。*

3. **Neo4j APOC 最短路径过程**: [neo4j.com/docs/apoc/current](https://neo4j.com/docs/apoc/current/)

   *确定性图路径算法参考。*

4. **Microsoft GraphRAG 架构指南**: [github.com/microsoft/graphrag](https://github.com/microsoft/graphrag)

   *全局子图总结与社区抽取参考。*

---

**IntelGraph 开发团队** | *版本: 1.0.0-PRD* | *开源协议: MIT*