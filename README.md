# TAH (Tactical Atlas & Heuristics) - v1.1

**"Surgical Context Injection for Token-Disciplined Power Users"**

TAH is a high-performance AI Gateway. It enables LLMs to gain instant domain expertise via local **Knowledge Cartridges (.tah)**, bypassing the latency of vector databases and the brute force token tax of massive context windows. By utilizing probabilistic data structures and surgical byte-offset seeking, TAH finds the "Knowledge Bullseye" in sub-milliseconds.


---By moving away from traditional "Exact Matching" (SQL) and "Semantic Guessing" (Vector DBs), we at the Sunset Collective are creating a third category: Deterministic Edge Retrieval.
It's NoSQL for the Agentic Age

## 🎯 The Core Philosophy: Token Discipline
Standard RAG often "regurgitates" entire documents into an LLM's context window. TAH uses a **Surgical Retrieval** model:
  **Edge Detection**: A global Bloom filter determines if a query exists in a cartridge before a single byte of text is read.
  **Surgical Extraction**: Utilizing C#-inspired Just-In-Time (JIT) principles, the system jumps to specific byte-offsets to extract only the relevant "shards" of data.
  **Expert Handshake**: Precise shards are injected into the LLM's prompt, making it an instant expert for that specific turn.

---

## 🛠️ Technical Architecture: The .tah Spec (v2.0)
The `.tah` file is a custom binary format structured for maximum **"Seek"** performance:
-   **Header (64 bytes)**: Pulse ID (`0x54414821`), Versioning, and metadata ($m$, $k$, AvgWordCount).
-   **Global Bloom Filter**: A probabilistic bit-array mapping all keywords in the library.
-   **Shard Index (88 bytes/entry)**: A lookup table containing `Offset | Length | WordCount | Local_Bloom`.
-   **Local Bloom Filters**: Per-shard 512-bit filters for pinpoint surgical accuracy.
-   **Data Shards**: Raw, UTF-8 encoded tactical knowledge.

---

## 🏗️ The Builder Suite (Python)
Located in `/builder`. Uses `CityHash64` with strict 64-bit parity for cross-platform consistency.

### 1. `pdf_builder.py`
Ingests massive PDFs (e.g., SICP, Medical Encyclopedias), chunks them into semantic shards, and indexes them with **N-Gram** support (Unigrams, Bigrams, Trigrams).

### 2. `web_builder.py` (v1.2 - Ozriel Protocol)
A recursive intelligence collector that follows the **Ozriel Protocol**:
-   **Semantic Vitality Checks**: Evaluates the "life" of a container, prioritizing technical density over navigational boilerplate.
-   **Recursive Discovery**: Follows high-vitality links to map an entire domain's expertise.
-   **Ontological Anchoring**: Anchors to core knowledge nodes while ignoring ads and footers.

### 3. `youtube_ingestor.py`
Turns any technical lecture into a cartridge via local **OpenAI Whisper** transcription.

---

## 🖥️ The Retrieval Layer

### 1. The Terminal (C#/.NET)
Located in `/terminal`. A high-performance, asynchronous client optimized for the CLR.
-   **BM25 Ranking**: Uses Best Matching 25 to score shards based on term rarity and document length.
-   **Stopword Filtering**: Automatically ignores "noise" words to prevent broad context dumping.

### 2. The Agent Hook (`tah_query.py`)
The bridge to the **Gemini CLI**. Allows the AI agent to programmatically search cartridges and inject ground truth.

---

## 🧪 The Inventor's Workbench
Located in `/workbench`. A "Set and Forget" intelligence pipeline.
1.  **`targets.txt`**: A drop-file for URLs (Web or YouTube).
2.  **`forge.py`**: A background engine that monitors targets and automatically builds the `workbench_expertise.tah` cartridge.

---

## 📦 Getting Started

### 1. The Workbench (Automated Forge)
Keep the Forge running to automatically digest links from `workbench/targets.txt`:
```powershell
python workbench/forge.py
```

### 2. Manual Cartridge Building (PDF)
Turn your local documents into Expertise Cartridges:
```powershell
python builder/pdf_builder.py "C:\Users\Taz\documents\deed_recording_master_tarrant.pdf" "tarrant_deeds"
```

### 3. The Retrieval Layer (High-Performance CLI)
Launch the C# Terminal to browse and query your cartridges:
```powershell
.\terminal\tah.exe
```

### 4. Agentic Interaction (The Hook)
Query a cartridge directly through the Gemini CLI for surgical context injection:
```powershell
python builder/tah_query.py cartridges/sicp_expert.tah "metacircular evaluator"
```

---
*SunsetPulse Collective 2026.*
