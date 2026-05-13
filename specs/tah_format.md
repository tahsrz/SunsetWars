# TAH File Format Specification (v3.0 - Polymorphic)

## Overview
The `.tah` file v3.0 extends the probabilistic retrieval model to non-textual data types using a **Data-Directed Shard Index**. This allows a single cartridge to hold mixed-media "Specialized Knowledge."

## 1. Binary Header (64 Bytes)
The header remains 64 bytes.

| Offset | Size (Bytes) | Field Name | Description |
| :--- | :--- | :--- | :--- |
| 0 | 4 | Magic Number | `0x54414821` ("TAH!") |
| 4 | 2 | Version | `0x0300` (3.0) |
| 6 | 1 | k | Number of hash functions. |
| 7 | 1 | Default Type | Default shard type (0=Text). |
| 8 | 8 | m | Global Bloom filter size in bits. |
| 16 | 4 | Shard Count | Total shards. |
| 20 | 4 | Avg Complexity | Avg word count (Text) or precision (Coords). |
| 24 | 40 | Reserved | Padding. |

## 2. Global Bloom Filter Area
Starts at offset 64. Maps all keys (text tokens, geohash prefixes, visual hashes).

## 3. Shard Index (v3.0 Polymorphic)
Contains `Shard Count` entries. Each entry is **80 bytes**.

| Offset | Size (Bytes) | Field Name | Description |
| :--- | :--- | :--- | :--- |
| 0 | 1 | Type Tag | `0=Text`, `1=Coordinate`, `2=Image`, `3=Vector`. |
| 1 | 7 | Reserved | Padding for alignment. |
| 8 | 8 | Offset | Absolute byte offset to data. |
| 16 | 4 | Length | Length of the shard data. |
| 20 | 4 | Meta/Score | WordCount (Text), Z-Order (Coords), etc. |
| 24 | 56 | Specialized Index | 448-bit bit-array (Bloom for Text, Spatial for Coords). |

## 4. Specialized Indexing Logic
- **Text (Tag 0)**: 448-bit Bloom Filter, $k=4$.
- **Coordinate (Tag 1)**: Centroid Geohash (bits 0-31) + Bounding Radius (bits 32-63) + Precision Mask.
- **Image (Tag 2)**: 64-bit pHash + 384-bit feature bloom.

## 5. Abstraction Barriers (SICP Principles)
The retrieval layer MUST NOT assume the structure of a shard. It must dispatch based on the `Type Tag` to a specific **Generic Operator** (e.g., `calculate_relevance`).
- `get_relevance(shard, query)` -> Dispatch to `bm25_score` or `haversine_distance` or `hamming_distance`.
