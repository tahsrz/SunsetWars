TAH (Terminal AI Hub) 
Surgical Context Injection for Token-Disciplined LLMs 
TAH is a high-performance, edge-based AI Gateway. It enables LLMs to gain instant domain expertise via local Knowledge Cartridges (.tah), bypassing the latency of vector databases and the "token tax" of massive context windows. 
🎯 The Philosophy: Token Discipline 
Standard RAG often "regurgitates" entire documents into an LLM's context window, wasting thousands of tokens and degrading response quality. TAH uses a Surgical Retrieval model: 
Edge Detection: A local C# terminal monitors your queries via a probabilistic Bloom filter (sub-millisecond latency). 
Surgical Extraction: Only the most relevant snippets (shards) are pulled using a hybrid BM25 + N-Gram ranking system. 
Expert Handshake: These precise shards are injected into the LLM's prompt, making it an instant expert for that specific turn. 
🛠️ Technical Architecture 
The .tah Cartridge (Binary Format v1.0) 
A custom binary format optimized for speed: 
Global Bloom Filter: Maps keywords across the entire document library. 
Local Bloom Filters: Per-shard filters (512-bit) for surgical pinpointing. 
BM25 Metadata: Stores word counts and average lengths for probabilistic ranking. 
N-Gram Indexing: Supports Unigrams, Bigrams, and Trigrams for phrase matching. 
The Builder (Python)Located in /builder. Uses CityHash64 for cross-platform hashing parity. 
pdf_builder.py: Ingests PDFs, chunks text, and generates cartridges. 
medical_builder.py: Example script for building large-scale encyclopedias. 
The Terminal (C#/.NET)Located in /terminal. A high-performance client that performs the "membership checks" and retrieval. 
Ranked Retrieval: Uses BM25 to score shards so you only get the "Knowledge Bullseye. 
"Stopword Filtering: Automatically ignores noise words to focus on technical keywords. 
📦 Getting Started 
Prerequisites 
Python 3.x (with pypdf) 
.NET Framework 4.0+ (supports legacy csc.exe systems) 
Creating a Cartridge 
Place your PDF in a directory and run:PowerShellpython builder/pdf_builder.py "path/to/your/document.pdf" 
This generates a .tah file in the /cartridges folder.Running the TerminalCompile (if not using provided binary) and run:PowerShell.\terminal\tah.exe
Select your cartridge and start typing. TAH will surgically extract context only when your keywords match the indexed knowledge. 
🏗️ Developer Stack 
Hashing: CityHash64 (Strict 64-bit parity). 
Ranking: BM25 (Best Matching 25) + Bigram/Trigram Boosting. 
Logic: Double Hashing ($g_i(x) = h_1(x) + i \cdot h_2(x)$). 
Platform: Python (Ingestion) / C# (Client).
 

SunsetPulse Collective 2026.