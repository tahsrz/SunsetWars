# TAH (Terminal AI Hub) - Project Mandates

## Core Objective
Build a lightweight, edge-based AI Gateway using probabilistic data structures (Bloom Filters) for instant, private context injection.

## TAH Code Bible (Mandatory Rules)
1. **Normalization**: Always `.lower().strip()` strings in both Python and C# before hashing.
2. **The Math**: The bit array size `m` must be identical in both implementations; modulo operations depend on this consistency.
3. **Binary Layout**:
   - **Header (First 64 bytes)**: Metadata like version, m, and k (padded for alignment).
   - **Bloom Filter Area**: The actual bit-array.
   - **Context Shards**: Niche text data for LLM injection.

## Technical Architecture
### .tah File Format (Version 1.0)
- **Binary Header (64 bytes)**: 
  - Magic Number: `0x54414821` ("TAH!") (4 bytes)
  - Version: (2 bytes)
  - k (Number of hash functions): (1 byte)
  - Padding: (1 byte)
  - m (Bloom filter size in bits): (8 bytes)
  - Shard Count: (4 bytes)
  - Reserved: (44 bytes padding to reach 64 bytes)
- **Bloom Filter**: Bit-array of size `m` (byte-aligned).
- **Shard Index**: Offsets and lengths for data shards.
- **Data Shards**: UTF-8 encoded text chunks.

### Hashing
- **Algorithm**: CityHash64.
- **Method**: Double Hashing ($g_i(x) = h1(x) + i \cdot h2(x)$) to generate $k$ indices.
- **Endianness**: Little-Endian for cross-platform compatibility.

## Developer Stack
- **Builder**: Python (Data processing, Bloom Filter construction).
- **Terminal**: C#/.NET (UI, bitwise operations, API orchestration).

## Directory Structure
- `/builder`: Python source code.
- `/terminal`: C# source code.
- `/specs`: Technical specifications and file format documentation.
- `/cartridges`: Storage for generated .tah files.
