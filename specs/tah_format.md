# TAH File Format Specification (v3.1)

## Overview

The `.tah` file format is a binary retrieval cartridge combining a global Bloom filter
with a shard index and raw UTF-8 text payloads.  v3.1 replaces the per-shard local Bloom
filter (present in v3.0 Polymorphic) with a `surgicalHash` field that enables O(1) exact
primary-keyword lookup, while retaining BM25 scoring as a fallback for all shards that
pass the global Bloom filter.

## 1. Binary Header (64 Bytes)

| Offset | Size (Bytes) | Field Name   | Description                              |
| :----- | :----------- | :----------- | :--------------------------------------- |
| 0      | 4            | Magic Number | `0x54414821` ("TAH!")                    |
| 4      | 2            | Version      | `0x0003` (v3.1, LE uint16)               |
| 6      | 1            | k            | Number of hash functions                 |
| 7      | 1            | Reserved     | 0x00                                     |
| 8      | 8            | m            | Global Bloom filter size in bits (uint64 LE) |
| 16     | 4            | Shard Count  | Total shards (uint32 LE)                 |
| 20     | 44           | Reserved     | Zeroed; avg_shard_len field from earlier versions dropped |

## 2. Global Bloom Filter Area

Starts at byte offset 64.  Size = `ceil(m / 8)` bytes.  Encodes all indexing terms
(unigrams, bigrams, trigrams) across all shards using double-hashing with `k` hash
functions.

## 3. Shard Index (v3.1)

Immediately follows the Global Bloom Filter.  Contains `Shard Count` entries; each entry
is exactly **80 bytes**.

| Offset | Size (Bytes) | Field Name    | Description                                           |
| :----- | :----------- | :------------ | :---------------------------------------------------- |
| 0      | 1            | Type Tag      | `1` = UTF-8 text shard                                |
| 1      | 7            | Reserved      | Zeroed                                                |
| 8      | 8            | dataOffset    | Absolute byte offset to shard payload (uint64 LE)     |
| 16     | 4            | dataLength    | Byte length of shard payload including null terminator (uint32 LE) |
| 20     | 4            | meta          | Word count of shard text (uint32 LE)                  |
| 24     | 8            | surgicalHash  | CityHash64(normalize(primary keyword)); `0x0` if none (uint64 LE) |
| 32     | 48           | Reserved      | Zeroed                                                |

### surgicalHash computation

`surgicalHash = CityHash64(normalize(primary_keyword)) & 0xFFFFFFFFFFFFFFFF`

where `normalize(s)` lowercases and strips leading/trailing whitespace.  The sentinel
value `0x0000000000000000` (8 zero bytes) means "no primary keyword assigned to this
shard."  Do NOT substitute `CityHash64("")` for the absent-keyword case; the empty-string
hash is a valid non-zero value.

## 4. Shard Data Region

Immediately follows the Shard Index.  Each shard payload is null-terminated UTF-8:

- The `dataLength` field includes the null terminator byte (`0x00`).
- Readers must strip the trailing `0x00` before decoding to a Python `str`.

## 5. Retrieval Logic

1. **Global Bloom pre-screen** -- if the query term does not appear in the global Bloom
   filter, skip the shard index entirely.
2. **Surgical hash lookup** -- for each shard entry where `surgicalHash != 0` and
   `surgicalHash == CityHash64(normalize(term))`, assign a strong boost (5x).
3. **BM25 fallback** -- all shards that pass step 1 are scored via BM25; surgical-matched
   shards receive the 5x boost on top.
4. Return the top-N shards by accumulated score.

## 6. Legacy v2 Compatibility

Readers that encounter `version == 0x0002` or `version > 0x00FF` (the Python v2 wire
format `0x0200` reads as 512 in LE uint16) should treat the file as v2 legacy.

v2 shard-index layout (80 bytes per entry):

| Offset | Size (Bytes) | Field Name  | Description          |
| :----- | :----------- | :---------- | :------------------- |
| 0      | 8            | dataOffset  | uint64 LE            |
| 8      | 4            | dataLength  | uint32 LE (no null terminator) |
| 12     | 4            | wordCount   | uint32 LE            |
| 16     | 64           | localBloom  | 512-bit per-shard Bloom filter (k=4) |

v2 shard payloads are raw UTF-8 without a null terminator.

---

## Version History

| Version | Wire value | Notes                                         |
| :------ | :--------- | :-------------------------------------------- |
| v2      | `0x0002` / `0x0200` | Python legacy; per-shard local Bloom filter   |
| v3.0    | `0x0300`   | Polymorphic type tags; per-shard Bloom retained |
| v3.1    | `0x0003`   | surgicalHash replaces per-shard Bloom; null-terminated shards; avg_shard_len removed from header |
