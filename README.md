# TAH (Tactical Atlas & Heuristics) - v3.6 [Master Grid]



TAH is a high-performance AI Gateway. It enables LLMs to gain instant domain expertise via local **Knowledge Cartridges (.tah)**, bypassing the latency of vector databases and the brute force token tax of massive context windows. By utilizing probabilistic data structures, binary analytic metadata, and surgical byte-offset seeking, TAH finds the "Knowledge Bullseye" in sub-milliseconds.


**The v3.6 Master Vault (`pulse_master_v3_6.hat`) links 24 core intelligence units across a global visual grid.**

---By moving away from traditional "Exact Matching" (SQL) and "Semantic Guessing" (Vector DBs), we at the Sunset Collective have established a protocol that encodes Information Density and Geographic Origin directly into the binary layer.


## 🏗️ New in v3.6: The Intelligence Protocol
- **Analytic Handshake**: Every data shard now carries pre-computed **Complexity (f32)** and **Relevance (f32)** scores.
- **Provenance Linking**: Integrated **Source Registry** (JSON) mapping shards to real-world URLs and Ingestion Timestamps.
- **Global Grid Mapping**: Shards are pinned to **RegionIDs** (e.g., Texas, California, Japan, Germany) for O(1) 3D visualization.
- **Surgical Sentiment**: Initial support for sentiment-weighted retrieval (Positive/Negative/Neutral).

## Semantic Expert Atlas
`builder/segmented_expert_atlas.py` compiles the cartridge library into a 400-shard expert population at `cartridges/expert_atlas/segmented_expert_atlas.*`.

- **Concept anchored segmentation**: each source shard is split around extracted concept anchors; those anchors drive the segment vitality score.
- **Precomputed density complexity**: each expert stores semantic density as its complexity score, so routing and ranking can reject low-fit regions without reading payload text.
- **Recursive binary concept links**: each expert links to nearby binary jumps plus strongest same-concept peers, giving fast traversal between related shards after the first hit.
- **Middle-out disqualification**: query starts with a binary route through segment key ranges, then rejects whole segments by domain union, segment Bloom, complexity range, and vitality metadata before `.tah` payload reads.

Run the Ollama-to-Codex bridge when a query should become an agent handoff:

```powershell
python builder/ollama_codex_bridge.py "cache memory architecture retrieval routing"
```

The bridge asks Ollama to normalize the query into retrieval tokens when the local daemon is available, searches the expert atlas plus every selected cartridge, writes `workbench/codex_handoffs/latest.md`, and invokes `codex exec` with the retrieved TAH context. Use `--no-codex` to generate the handoff without launching Codex.


## 🏗️ Technical Architecture: The v3.6 Binary Spec (80 Bytes)
The Memoria Protocol utilizes a dual-file "Atlas Handshake" to achieve O(1) surgical retrieval:

### 1. The .hat (Header Atlas) — The Map
The `.hat` file is the intelligence layer. It is loaded into memory (or bit-mapped) for instant lookups.
- **Global Bloom Filter**: A probabilistic bit-vector that determines if a keyword exists in the entire vault in a single CPU cycle.
- **The Shard Index**: A deterministic table of 80-byte entries. Each entry contains:
    - **Tag (u8)**: Shard type (Text, Coordinate, Image).
    - **Offset (u64)**: Precise byte-location in the corresponding `.tah` file.
    - **Analytics Block**: Pre-computed Complexity and Relevance scores.
    - **Local Bloom (288-bit)**: A "mini-map" for each shard, allowing for sub-millisecond keyword matching without decoding text.
- **Source Registry**: A JSON-encoded block at the end of the file that maps shards to their original URLs and provenance data.

### 2. The .tah (Tactical Data) — The Territory
The `.tah` file is the raw payload. It remains on disk and is never fully loaded.
- **Lazy Loading**: The system only reads the specific byte-range identified by the `.hat` file.
- **Zero-Waste**: If the Bloom filter says a fact isn't there, the `.tah` file is never touched, saving disk I/O and memory overhead.

---

## 🎯 The Core Philosophy: Intelligence Density
Standard RAG often "regurgitates" entire documents. TAH v3.6 uses an **Analytic Retrieval** model:
  **Heat Detection**: The UI can render a "Knowledge Heatmap" of an entire cartridge without reading a single byte of text.
  **Surgical Provenance**: Every retrieved shard is hard-linked to its source documentation or origin URL.
  **Temporal Awareness**: Shards are timestamped, allowing for the visualization of "Knowledge Growth" over time.

### 📊 The Token Tax: A Quantitative Reality Check
To understand the power of surgical retrieval, consider the processing of the **"Computer Architecture: A Quantitative Approach" (5th Ed)** cartridge:

| Metric | Raw PDF Read (Monolithic) | Memoria Pulse Query (Surgical) | Efficiency Gain |
| :--- | :--- | :--- | :--- |
| **Token Usage** | ~744,326 tokens | ~2,500 tokens | **297x Reduction** |
| **Context Overhead** | 100% (Full Book) | <0.4% (Surgical) | **99.6% Saved** |
| **Monetary Cost** | ~$5.21 | < $0.02 | **260x Cheaper** |

**The Bottom Line:** By encoding metadata and probabilistic filters into the binary layer, TAH allows you to "query the book" 300 times for the cost of reading it once.

---

## 🛠️ Technical Architecture: The v3.6 Binary Spec (80 Bytes)
The `.tah` entry has been optimized for O(1) analytic rendering:
-   **Offset 0-19**: Tag (u8), Offset (u64), Length (u32).
-   **Offset 20-23**: SourceID (u16), RegionID (u16) [Map Pointers].
-   **Offset 24-31**: Surgical Hash (u64) [Instant Lookup].
-   **Offset 32-39**: Complexity (f32), Relevance (f32) [Analytic Block].
-   **Offset 40-43**: Ingestion Timestamp (u32) [Timeline Pointer].
-   **Offset 44-79**: Local Bloom Filter (288-bit) [Sub-Keyword Index].

---

## 🌌 The Master Grid: 24 Core Intelligence Units
The `pulse_master_v3_6` vault consolidates your entire engineering stack:

| Sector | Intelligence Units | Global Links |
| :--- | :--- | :--- |
| **Security** | Zero Trust (NIST), IAM Hardening, ECC Crypto, JWT/JOSE | TX, CA, UK |
| **Data** | PostgreSQL WAL, PostGIS, Supabase Realtime, Redis Pub/Sub | NY, FL, TX |
| **Visuals** | Three.js Scene Graph, Mapbox Vector Tiles, Tailwind CSS, Cannon.js | JP, CA, NY, DE |
| **AI/Logic** | OpenRouter Orchestration, Groq LPU Speed, BM25 Ranking | JP, CA, FR |
| **Ops** | Docker Multi-Stage, GitHub Actions, Node.js Async, Zod Validation | FR, TX, JP, DE |

---

## 🏗️ The Builder Suite (Python)
Located in `/builder`. 

### 1. `memoria_builder.py` (v3.6)
The primary compiler. Automatically calculates **Lexical Diversity** and manages the **Source Registry**.

### 2. `migrate_assets_v3_6.py`
The "Knowledge Rescue" tool. Batch-compiles legacy text sources into the unified v3.6 Master Grid.

### 3. `memory_forge.py`
Monitors `user_memories.txt` to keep your personal context cartridge in sync with the v3.6 spec.

---

## 🖥️ The Retrieval Layer

### 1. The v3.6 TypeScript Retriever
Located in `SunsetPulse/apps/pulse/lib/core/tah_retriever_v3_6.ts`. Designed for instant dashboarding and Mapbox/Three.js integration.

### 2. The Python Query Engine (`memoria_query.py`)
Used by the Telegram bot. Implements Intelligence-Weighted BM25 ranking for surgical answers.

---

## 📦 Getting Started / Swapping Accounts

### 1. Configure the Pulse Engine
Open `.env` in the bot or UI directory.

**To Swap Telegram/Gemini Accounts:**
1.  **Bot Token**: Replace `TELEGRAM_BOT_TOKEN` with your new bot's token from @BotFather.
2.  **Authorized ID**: Update `AUTHORIZED_USER_ID` to match the new user's Telegram ID.
3.  **UI Token**: If using the Web UI, update `GEMINI_UI_TOKEN` to pair with the new session.

### 2. Run the Intelligence Grid
```powershell
# Compile the Master Grid
python builder/migrate_assets_v3_6.py

# Start the Query Engine
python builder/memoria_query.py cartridges/pulse_master_v3_6 "How does Groq LPU work?"
```

---
*SunsetPulse Collective 2026. "Global intelligence for token-disciplined power users."*
