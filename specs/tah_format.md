# TAH File Format Specification (v2.0)

## Overview
The `.tah` file is a binary format designed for efficient, local knowledge retrieval using Bloom filters. v2.0 introduces BM25 scoring support and N-Gram indexing.

## 1. Binary Header (64 Bytes)
The header is always 64 bytes, using Little-Endian byte order.

| Offset | Size (Bytes) | Field Name | Description |
| :--- | :--- | :--- | :--- |
| 0 | 4 | Magic Number | `0x54414821` ("TAH!") |
| 4 | 2 | Version | `0x0200` (2.0) |
| 6 | 1 | k | Number of hash functions. |
| 7 | 1 | Padding | Reserved (Set to 0). |
| 8 | 8 | m | Bloom filter size in bits (unsigned 64-bit). |
| 16 | 4 | Shard Count | Number of data shards in the file. |
| 20 | 4 | Avg Shard Len | Average word count per shard (for BM25). |
| 24 | 40 | Reserved | Padding for 64-byte alignment. |

## 2. Bloom Filter Area
Starts at offset 64.
- Size: `ceil(m / 8)` bytes.

## 3. Shard Index
Starts immediately after the Bloom Filter Area.
Contains `Shard Count` entries. Each entry is **80 bytes**.

| Offset | Size (Bytes) | Field Name | Description |
| :--- | :--- | :--- | :--- |
| 0 | 8 | Offset | Absolute byte offset to the start of the shard. |
| 8 | 4 | Length | Length of the shard in bytes. |
| 12 | 4 | Word Count | Number of words in this shard (for BM25). |
| 16 | 64 | Local Bloom Filter | Shard-specific bit-array for surgical keyword matching. |

## 4. Data Shards
Raw UTF-8 encoded text data.

## 5. Hashing Logic (N-Grams)
1. **Unigrams**: Individual words (e.g., "rejection").
2. **Bigrams**: Pairs of words (e.g., "rejection reasons").
3. **Trigrams**: Triplets of words (e.g., "common rejection reasons").
All N-Grams are normalized (lower, strip) before hashing.
Double hashing is used for both global and local filters.

**Local Filter Config**: 64 bytes (512 bits), $k=4$.

## 6. Normalization
Before hashing, all input strings must be:
- Converted to lowercase (`.lower()`).
- Stripped of leading/trailing whitespace (`.strip()`).
- Encoded as UTF-8.
