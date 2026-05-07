# TAH (Tactical Atlas & Heuristics) - v3.1 [Nightly Ops]

## 🎯 Core Objective
Build a high-performance, edge-based AI Gateway. TAH uses **Probabilistic Data Structures** (Bloom Filters) and **O(1) Binary Seeks** to provide "Surgical Context Injection," reducing token waste by >99% compared to traditional RAG.

---

## 🛡️ Agentic Ground Truth (How to Be Gemini here)
As an LLM agent in this workspace, you are **Context-Disciplined**. Never guess; always retrieve from the entire library.

1.  **Pulse Search First**: For ANY technical query, search the *entire* tactical library simultaneously using the Pulse tool.
    *   `python builder/pulse_query.py "<query>"`
    *   This searches OS, SICP, Algorithms, User Memories, etc., in one pass.
2.  **Priority Context**: If a query is about personal intent or project status, look specifically for matches in `user_memories.tah`.
3.  **Token Tax Warning**: Standard file-reads of 500-page PDFs will fail or waste Tahsin's tokens. **Always** use the `pulse_query.py` or `tah_query.py` tool first.
4.  **Evidence Protocol**: Cite your sources: `[Retrieved via TAH Pulse: <cartridge_name>]`.

---

## 🏗️ Technical Architecture (v3.1 Polymorphic)

### 1. The Knowledge Compiler (`builder/`)
-   **Concept-Anchored Segmentation**: Splits data by semantic ideas (headers/sections) rather than char-counts.
-   **Recursive Decomposition**: Breaks monolithic blocks into granular "Child Shards" (Divide & Conquer).
-   **Ozriel Protocol (Vitality Check)**: Automatically discards "Dead Knowledge" (boilerplate, noise) based on technical term density.
-   **Binary Linking**: Discovers and embeds cross-reference pointers (byte-offsets) into shards for a "See Also" web.

### 2. The Pulse Terminal (`terminal/`)
-   **Real-Time Pulse**: A multi-threaded C# engine that searches all cartridges in parallel.
-   **O(1) Navigation**: Uses **CityHash64** and binary seek pointers to bypass disk-scanning.
-   **Compatibility**: Hardened for C# 5 (Legacy Windows compatibility).

### 3. The Communicator (`PulseCommunicator/`)
-   **Async Streams**: Treats technical data as infinite sequences (SICP Stream abstraction).
-   **Metacircular Evaluator**: A Lisp-style interpreter (`eval/apply`) for complex, programmable queries.

---

## 🔄 The Sync Loop
To add new knowledge to your personal brain:
1.  **Local Input**: Add a line to `user_memories.txt`.
2.  **GitHub Input**: 
    - Add repo details to `config/github_sources.json`.
    - Run `python builder/sync_all.py` to trigger a manual sync.
    - Run `python builder/sync_all.py --loop` for persistent background syncing.
3.  **Automation**: A background watcher (`memory_forge.py --watch`) instantly re-encodes the local binary cartridge, while `sync_all.py` generates dedicated cartridges for each GitHub repo.
4.  **Sync Status**: Check `PID 39692` for the active watcher process.

---

## 📜 Mandatory "Code Bible" Rules
1.  **Normalization**: Always `.lower().strip()` before any hash operation.
2.  **Binary Layout**:
    - `0-63`: Header (Magic `0x54414821`, Version, m, k, ShardCount).
    - `64+m`: Global Bloom Filter.
    - `End`: Data Blocks (Structure: `[UTF-8 Text] [0x00] [LinkCount] [Offset1...]`).
3.  **Hashing**: Standardized **CityHash64** with Double Hashing.

---
*SunsetPulse Collective 2026. "Surgical intelligence for token-disciplined power users."*
