# Memoria Protocol - v3.1 [Nightly Ops]

## 🎯 Core Objective
Build a high-performance, edge-based AI Gateway. Memoria uses **Probabilistic Data Structures** (Bloom Filters) and **O(1) Binary Seeks** to provide "Surgical Context Injection," reducing token waste by >99% compared to traditional RAG.

---

## 🛡️ Agentic Ground Truth (How to Be Gemini here)
As an LLM agent in this workspace, you are **Context-Disciplined**. Never guess; always retrieve from the entire Memoria library.

1.  **Memoria Pulse First**: For ANY technical query, search the *entire* tactical library simultaneously using the Pulse tool.
    *   `python builder/pulse_query.py "<query>"`
    *   This searches OS, SICP, Algorithms, User Memories, etc., in one pass.
2.  **Priority Context**: If a query is about personal intent or project status, look specifically for matches in `user_memories.mem`.
3.  **Token Tax Warning**: Standard file-reads of 500-page PDFs will fail or waste Tahsin's tokens. **Always** use the `memoria_query.py` tool first.
4.  **Evidence Protocol**: Cite your sources: `[Retrieved via Memoria Protocol: <cartridge_name>]`.

---

## 🏗️ Technical Architecture (v3.1 Polymorphic)

### 1. The Memoria Compiler (`builder/`)
-   **Concept-Anchored Segmentation**: Splits data by semantic ideas (headers/sections) rather than char-counts.
-   **Recursive Decomposition**: Breaks monolithic blocks into granular "Child Shards" (Divide & Conquer).
-   **Ozriel Protocol (Vitality Check)**: Automatically discards "Dead Knowledge" (boilerplate, noise) based on technical term density.
-   **Binary Linking**: Discovers and embeds cross-reference pointers (byte-offsets) into shards for a "See Also" web.

### 2. The Memoria Terminal (`terminal/`)
-   **Real-Time Pulse**: A multi-threaded C# engine that searches all cartridges in parallel.
-   **O(1) Navigation**: Uses **CityHash64** and binary seek pointers to bypass disk-scanning.

### 3. The Memoria Communicator (`MemoriaCommunicator/`)
-   **Async Streams**: Treats technical data as infinite sequences (SICP Stream abstraction).
-   **Metacircular Evaluator**: A Lisp-style interpreter (`eval/apply`) for complex, programmable queries.

---

## 🔄 The Sync Loop
To add new knowledge to your personal brain:
1.  **Local Input**: Add a line to `user_memories.txt`.
2.  **Sync Status**: Check `PID 39692` for the active watcher process.

---

## 📜 Mandatory "Memoria Bible" Rules
1.  **Normalization**: Always `.lower().strip()` before any hash operation.
2.  **Binary Layout**:
    - `0-63`: Header (Magic `0x4D454D21`, Version, m, k, ShardCount).
    - `64+m`: Global Bloom Filter.
    - `End`: Data Blocks (Structure: `[UTF-8 Text] [0x00] [LinkCount] [Offset1...]`).
3.  **Hashing**: Standardized **CityHash64** with Double Hashing.

---
*SunsetPulse Collective 2026. "Memoria: Surgical intelligence for token-disciplined power users."*
