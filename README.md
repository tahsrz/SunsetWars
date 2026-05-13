# TAH (Tactical Atlas & Heuristics) - v3.1 [Nightly Ops]

**"Surgical Context Injection for Token-Disciplined Power Users"**


TAH is a high-performance AI Gateway. It enables LLMs to gain instant domain expertise via local **Knowledge Cartridges (.tah)**, bypassing the latency of vector databases and the brute force token tax of massive context windows. By utilizing probabilistic data structures and surgical byte-offset seeking, TAH finds the "Knowledge Bullseye" in sub-milliseconds.


**There are multiple .tah files in the cartridges directory. You may copy them into any LLM and it will translate the BINARY file into contextual knowledge.**

---By moving away from traditional "Exact Matching" (SQL) and "Semantic Guessing" (Vector DBs), we at the Sunset Collective are creating a third category: Deterministic Edge Retrieval.
It's NoSQL for the Agentic Age

## 🎯 The Core Philosophy: Token Discipline
Standard RAG often "regurgitates" entire documents into an LLM's context window. TAH uses a **Surgical Retrieval** model:
  **Edge Detection**: A global Bloom filter determines if a query exists in a cartridge before a single byte of text is read.
  **Surgical Extraction**: Utilizing C#-inspired Just-In-Time (JIT) principles, the system jumps to specific byte-offsets to extract only the relevant "shards" of data.
  **Expert Handshake**: Precise shards are injected into the LLM's prompt, making it an instant expert for that specific turn.

---

## 🛠️ Technical Architecture: The .tah Spec (v3.1 Polymorphic)
The `.tah` file is a custom binary format structured for maximum **"Seek"** performance:
-   **Header (64 bytes)**: Pulse ID (`0x54414821`), Versioning, and metadata ($m$, $k$, ShardCount).
-   **Global Bloom Filter**: A probabilistic bit-array mapping all keywords in the library.
-   **Concept-Anchored Segmentation**: Splits data by semantic ideas (headers/sections) rather than char-counts.
-   **Recursive Decomposition**: Breaks monolithic blocks into granular "Child Shards" (Divide & Conquer).
-   **Data Blocks**: Raw, UTF-8 encoded tactical knowledge with embedded binary cross-reference pointers.

---

## 🏗️ The Builder Suite (Python)
Located in `/builder`. Uses `CityHash64` with strict 64-bit parity for cross-platform consistency.

### 1. `sync_all.py` & `github_sync.py`
The primary sync engine. Ingests local files and remote GitHub repositories (defined in `config/github_sources.json`) to create dedicated cartridges.

### 2. `pdf_builder.py`
Ingests massive PDFs (e.g., SICP, Medical Encyclopedias), chunks them into semantic shards, and indexes them with **N-Gram** support.

### 3. `web_builder.py` (v3.1 - Ozriel Protocol)
A recursive intelligence collector that evaluates the "life" of a container, prioritizing technical density over navigational boilerplate (Semantic Vitality Check).

### 4. `memory_forge.py`
A background watcher that monitors `user_memories.txt` and automatically re-encodes the `user_memories.tah` cartridge in real-time.

### 5. `youtube_ingestor.py`
Turns any technical lecture into a cartridge via local **OpenAI Whisper** transcription.

---

## 🖥️ The Retrieval Layer

### 1. The Pulse Terminal (C#/.NET)
Located in `/terminal`. A multi-threaded engine that searches all cartridges in parallel using **CityHash64** and binary seek pointers for O(1) navigation.

### 2. The PulseCommunicator
Located in `/PulseCommunicator`. Treats technical data as infinite sequences (SICP Stream abstraction) and includes a **Metacircular Evaluator** for complex, programmable queries.

### 3. The Agent Hooks (`pulse_query.py` & `tah_query.py`)
The bridge to the **Gemini CLI**. `pulse_query.py` searches the entire tactical library simultaneously, while `tah_query.py` targets specific cartridges.

---

## 🧪 The Inventor's Workbench
Located in `/workbench`. A "Set and Forget" intelligence pipeline.
1.  **`targets.txt`**: A drop-file for URLs (Web or YouTube).
2.  **`forge.py`**: A background engine that monitors targets and automatically builds the `workbench_expertise.tah` cartridge.

---

## 📚 The Tactical Library: Domain Index
The following expertise cartridges are currently active and optimized for surgical retrieval.

### 1. 🏗️ The CS Bedrock (Theory & Fundamentals)
*   **`sicp.tah` / `sicp_expert.tah`:** Functional programming, language design, and the Metacircular Evaluator.
*   **`algorithms.tah`:** Pattern matching (KMP, Rabin-Karp), NP-Completeness, and complexity analysis.
*   **`architecture.tah`:** Multiprocessor performance, cache coherence, and distributed systems.
*   **`compilers.tah` / `operatingSystem.tah`:** Kernel-space mechanics and language translation.

### 2. 🧩 Specialized Intelligence
*   **`deepLearning.tah` / `categoryTheory.tah`:** Neural architectures and mathematical foundations.
*   **`unixArt.tah`:** The Unix philosophy of modularity, clarity, and composition.
*   **`theLittleSchemer.tah`:** Recursive logic and fundamental computation.

### 3. 🌇 The Sunset Stack (Domain Expertise)
*   **`texas_real_estate.tah` / `tarrant_deeds.tah`:** Ground-truth for real estate law, deed recording, and Texas property regulations.
*   **`sunset_pulse_expertise.tah`:** Platform-specific architectural decisions for Sunset Pulse.
*   **`sunset_wars.tah`:** Strategic objectives and evolution of the TAH project.

### 4. 🧠 Agentic Memory & Ops
*   **`user_memories.tah`:** Personal context, project secrets, and developer preferences (synced via `memory_forge.py`).
*   **`polymorphic_test.tah`:** Validation of the v3.1 Polymorphic spec and concept-anchored segmentation.

---

## 🛠️ The Micro-Agent Toolkit (`/micro_agents`)
A collection of "Little Things" built on the TAH engine for specialized tasks.

-   **`lisp_shell.py`:** Interactive S-Expression REPL for programmable queries.
-   **`pulse_clip.py`:** Clipboard monitor that pulses the library for copied technical terms.
-   **`voiceover_gen.py`:** Generates high-impact video scripts from technical ground truth.
-   **`tah_micro_factory.py`:** Meta-tool to generate new specialized micro-agents.

---

## 📦 Getting Started

### 1. The Sync Loop (Persistent Intelligence)
Run the sync engine in the background to keep your entire library updated:
```powershell
python builder/sync_all.py --loop
```

### 2. The Memory Watcher
Keep your personal "User Memories" cartridge synced with your notes:
```powershell
python builder/memory_forge.py --watch
```

### 3. High-Performance Retrieval (Pulse)
Search the *entire* tactical library simultaneously for any technical query:
```powershell
python builder/pulse_query.py "metacircular evaluator"
```

### 4. Agentic Hook (Specific Cartridge)
Target a specific expertise cartridge for surgical injection:
```powershell
python builder/tah_query.py cartridges/sicp_expert.tah "streams"
```

---
*SunsetPulse Collective 2026. "Surgical intelligence for token-disciplined power users."*
