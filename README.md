# TAH (Terminal AI Hub) - v1.1


⚡ The "Just-In-Time" (JIT) Contextualizer 


Inspired by the C# JIT Compiler, just as the CommonLanguageRuntime transforms MSIL into native code at the very last microsecond for peak performance, our JIT Contextualizer waits until the query hits the wire to "emit" the perfect knowledge shard.

TAH is a high-performance, edge-based AI Gateway. It enables LLMs to gain instant domain expertise via local **Knowledge Cartridges (.tah)**, bypassing the latency of vector databases and the brute force token usage of massive CLIs.


Moving from the "everything everywhere" approach of Java to the streamlined power of C# allowed for a more robust, event-driven architecture. By leveraging C#’s high-performance memory management and asynchronous streams, we’ve built a system that feels alive—dynamic, type-safe, and incredibly fast. It’s not just retrieval; it’s contextual execution.


## 🎯 The Philosophy: Token Discipline
Standard RAG often "regurgitates" entire documents into an LLM's context window, wasting thousands of tokens and degrading response quality. TAH uses a **Surgical Retrieval** model:
 **Edge Detection**: A local C# terminal monitors your queries via a probabilistic Bloom filter (sub-millisecond latency).
 **Surgical Extraction**: Only the most relevant snippets (shards) are pulled using a hybrid **BM25 + N-Grams** ranking system.
 **Expert Handshake**: These precise shards are injected into the LLM's prompt, making it an instant expert for that specific turn.

WIP Inventor's Workbench: Drop folder with a text file called targets.txt background pyScript fetches new urls, transcribes/scrapes using Ozriel Protocol (see SunsetPulse)


## 🛠️ Technical Architecture

### 1. The .tah Cartridge (Binary Format v2.0)
- **Global Bloom Filter**: Maps keywords across the entire document library.
- **Local Bloom Filters**: Per-shard filters (512-bit) for surgical pinpointing.
- **BM25 Metadata**: Stores word counts and average lengths for probabilistic ranking.
- **N-Gram Indexing**: Supports Unigrams, Bigrams, and Trigrams for phrase matching.

### 2. The Builder Suite (Python)
Located in `/builder`. 
- `pdf_builder.py`: Ingests PDFs, chunks text, and generates cartridges.
- `web_builder.py`: **[v1.1]** Extracts semantic content from URLs, ignoring navigational noise and ads.
- `medical_builder.py`: Example script for building large-scale encyclopedias.

### 3. The Terminal (C#/.NET)
Located in `/terminal`. 
- **Ranked Retrieval**: Uses BM25 to score shards so you only get the "Knowledge Bullseye."
- **Stopword Filtering**: Automatically ignores noise words to focus on technical jargon.

### 4. The Hub (Downloader)
Located in `/downloader`. 
- `tah_hub.py`: A lightweight utility to fetch pre-built cartridges from remote repositories with binary integrity validation.

## 📦 Getting Started

### Creating a Cartridge from a PDF
```powershell
python builder/pdf_builder.py "path/to/your/document.pdf"
```

### Creating a Cartridge from a URL [v1.1]
```powershell
python builder/web_builder.py "https://docs.microsoft.com/en-us/dotnet/csharp/" "csharp_docs"
```

### Downloading a Cartridge
```powershell
python downloader/tah_hub.py "https://example.com/expert_knowledge.tah"
```

### Running the Terminal
```powershell
.\terminal\tah.exe
```

## 🏗️ Developer Stack
- **Hashing**: CityHash64 (Strict 64-bit parity).
- **Ranking**: BM25 (Best Matching 25) + Bigram/Trigram Boosting.
- **Platform**: Python (Ingestion) / C# (Client).

---
*SunsetPulse Collective 2026.*
