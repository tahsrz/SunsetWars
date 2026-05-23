"""
TAH Cartridge Query -- v3.1

Reads .tah cartridges in v3.1 format (version 0x0003) and falls back to the
Python-v2 legacy format (0x0200 / version > 0xFF in LE uint16) per spec section 6.

v3.1 shard-index layout (80 bytes per entry):
    offset 0:   type byte
    offset 1-7: reserved
    offset 8:   dataOffset uint64 LE
    offset 16:  dataLength uint32 LE  (includes null terminator)
    offset 20:  meta uint32 LE  (word_count)
    offset 24:  surgicalHash uint64 LE
    offset 32-79: reserved

v2 shard-index layout (80 bytes per entry):
    offset 0:   dataOffset uint64 LE
    offset 8:   dataLength uint32 LE
    offset 12:  wordCount uint32 LE
    offset 16:  localBloom bytes (64 bytes)

The v2 fallback read path is kept because existing cartridges may still be in
v2 format.  Once all cartridges are regenerated under v3.1, the fallback remains
as a safety net and does not need to be removed.

--- Per-process cartridge metadata cache ---
The module holds a module-level OrderedDict LRU cache of parsed cartridge
metadata, keyed by (resolved_path_str, mtime_ns).  On cache hit, TAHQuery.__init__
copies the pre-parsed fields (is_v2, k, m, shard_count, avg_shard_len, bloom_offset,
index_offset, global_bloom) onto self and skips _load_metadata() entirely, saving
200-800ms of header + bloom + full shard-index-scan work per instantiation.
The file handle is still opened per-instance (cheap) because file handles are not
safe to share across instances.  Cache is NOT thread-safe; it is designed for
single-threaded process usage.  Default LRU size is 4 cartridges; override with
the environment variable TAH_CACHE_SIZE=<positive int>.
"""
import struct
import math
import sys
import os
from collections import OrderedDict
from pathlib import Path

# Add current dir to path for imports
sys.path.append(os.path.dirname(__file__))
from cityhash import get_tah_indices, city_hash64, normalize

# v3.1 spec constants
TAH_MAGIC = 0x54414821
VERSION_V3_1 = 0x0003
HEADER_SIZE = 64
SHARD_ENTRY_SIZE = 80

# ---------------------------------------------------------------------------
# Module-level LRU metadata cache
# ---------------------------------------------------------------------------
# Read cache size from env at module-load time.
# TAH_CACHE_SIZE=<positive int> overrides the default of 4.
_DEFAULT_CACHE_SIZE = 4
_env_cache_size = os.environ.get("TAH_CACHE_SIZE", "")
try:
    _parsed = int(_env_cache_size)
    _CACHE_MAX = _parsed if _parsed > 0 else _DEFAULT_CACHE_SIZE
except ValueError:
    _CACHE_MAX = _DEFAULT_CACHE_SIZE

# Cache: OrderedDict[(path_str, mtime_ns)] -> dict of parsed metadata fields.
# NOTE: NOT thread-safe.  Intended for single-threaded usage.
_metadata_cache: OrderedDict = OrderedDict()

# Counters for testability -- readable by test code, zero I/O in production.
_cache_hits: int = 0
_cache_misses: int = 0


def _cache_get(key: tuple) -> "dict | None":
    """Return cached metadata dict for key, or None on miss.

    Moves the key to the end (most-recently-used position) on hit.
    """
    global _cache_hits, _cache_misses
    if key in _metadata_cache:
        _metadata_cache.move_to_end(key)
        _cache_hits += 1
        return _metadata_cache[key]
    _cache_misses += 1
    return None


def _cache_put(key: tuple, value: dict) -> None:
    """Insert metadata dict under key, evicting LRU entry when at capacity."""
    if key in _metadata_cache:
        _metadata_cache.move_to_end(key)
    _metadata_cache[key] = value
    while len(_metadata_cache) > _CACHE_MAX:
        _metadata_cache.popitem(last=False)  # evict oldest


def set_cache_size(n: int) -> None:
    """Adjust the cache capacity at runtime (for test harness use).

    Trims entries immediately if the cache exceeds the new size.
    This is the testability hook for TAH_CACHE_SIZE env-var tests
    that cannot reload the module between cases.
    """
    global _CACHE_MAX
    if n <= 0:
        raise ValueError("Cache size must be a positive integer.")
    _CACHE_MAX = n
    while len(_metadata_cache) > _CACHE_MAX:
        _metadata_cache.popitem(last=False)


def reset_cache() -> None:
    """Clear the metadata cache and reset hit/miss counters (for testing)."""
    global _cache_hits, _cache_misses
    _metadata_cache.clear()
    _cache_hits = 0
    _cache_misses = 0


def _is_v2_version(version_raw: int) -> bool:
    """Return True if the version field looks like Python-v2 legacy.

    Per spec section 6.1: version == 0x0002 or version > 0x00FF (the Python v2
    0x0200 reads as 512 in LE uint16) -> treat as v2 legacy.
    """
    return version_raw == 0x0002 or version_raw > 0x00FF


class TAHQuery:
    def __init__(self, cartridge_path):
        self.path = Path(cartridge_path).resolve()
        if not self.path.exists():
            raise FileNotFoundError(f"Cartridge not found: {cartridge_path}")

        # Build cache key: (resolved_path_str, mtime_ns).
        # os.stat() raises naturally if the file vanishes between the exists()
        # check above and here -- we let that propagate per the soft-fail spec.
        stat = os.stat(self.path)
        cache_key = (str(self.path), stat.st_mtime_ns)

        cached = _cache_get(cache_key)
        if cached is not None:
            # Fast path: copy pre-parsed metadata, skip _load_metadata()
            self.is_v2 = cached["is_v2"]
            self.k = cached["k"]
            self.m = cached["m"]
            self.shard_count = cached["shard_count"]
            self.avg_shard_len = cached["avg_shard_len"]
            self.bloom_offset = cached["bloom_offset"]
            self.index_offset = cached["index_offset"]
            self.global_bloom = cached["global_bloom"]
        else:
            # Cold path: parse header + bloom + shard index, then store.
            self.file = open(self.path, 'rb')
            self._load_metadata()
            _cache_put(cache_key, {
                "is_v2": self.is_v2,
                "k": self.k,
                "m": self.m,
                "shard_count": self.shard_count,
                "avg_shard_len": self.avg_shard_len,
                "bloom_offset": self.bloom_offset,
                "index_offset": self.index_offset,
                "global_bloom": self.global_bloom,
            })
            return  # file already open from cold path

        # Warm path: open a fresh file handle (not cached -- handles are per-instance)
        self.file = open(self.path, 'rb')

    def _load_metadata(self):
        # 1. Read Header (64 bytes)
        header = self.file.read(64)
        magic, version, self.k, _, self.m, self.shard_count = struct.unpack_from(
            '<I H B B Q I', header, 0
        )

        if magic != TAH_MAGIC:
            raise ValueError(f"Invalid TAH cartridge (bad magic 0x{magic:08x}).")

        # Determine format version
        self.is_v2 = _is_v2_version(version)
        if self.is_v2:
            # v2: avg_shard_len is at header offset 20 as uint32
            self.avg_shard_len = struct.unpack_from('<I', header, 20)[0]
        else:
            # v3.1: header offset 20 is reserved/zeroed; compute avg later
            self.avg_shard_len = 0  # will be set after reading shard index

        # 2. Locate regions
        bloom_size = math.ceil(self.m / 8)
        self.bloom_offset = HEADER_SIZE
        self.index_offset = HEADER_SIZE + bloom_size

        # Load Global Bloom for quick check
        self.file.seek(self.bloom_offset)
        self.global_bloom = self.file.read(bloom_size)

        # For v3.1, compute avg_shard_len from shard index (meta field)
        if not self.is_v2 and self.shard_count > 0:
            total_words = 0
            self.file.seek(self.index_offset)
            for _ in range(self.shard_count):
                entry = self.file.read(SHARD_ENTRY_SIZE)
                # meta (word_count) is at offset 20 in entry
                wc = struct.unpack_from('<I', entry, 20)[0]
                total_words += wc
            self.avg_shard_len = total_words // self.shard_count if self.shard_count else 1
        # Protect against divide-by-zero in BM25
        if self.avg_shard_len == 0:
            self.avg_shard_len = 1

    def contains_keyword(self, keyword):
        indices = get_tah_indices(keyword, self.m, self.k)
        for idx in indices:
            byte_idx = idx // 8
            bit_idx = idx % 8
            if not (self.global_bloom[byte_idx] & (1 << bit_idx)):
                return False
        return True

    def _read_shard_entry_v2(self, entry_bytes):
        """Parse a v2 80-byte shard-index entry.

        Returns (data_offset, data_length, word_count, local_bloom_bytes).
        """
        data_offset, data_length, word_count = struct.unpack_from('<Q I I', entry_bytes, 0)
        local_bloom = entry_bytes[16:80]
        return data_offset, data_length, word_count, local_bloom

    def _read_shard_entry_v31(self, entry_bytes):
        """Parse a v3.1 80-byte shard-index entry.

        Returns (data_offset, data_length, word_count, surgical_hash).
        type byte is at offset 0; dataOffset@8; dataLength@16; meta(wc)@20; surgicalHash@24.
        """
        data_offset = struct.unpack_from('<Q', entry_bytes, 8)[0]
        data_length = struct.unpack_from('<I', entry_bytes, 16)[0]
        word_count = struct.unpack_from('<I', entry_bytes, 20)[0]
        surgical_hash = struct.unpack_from('<Q', entry_bytes, 24)[0]
        return data_offset, data_length, word_count, surgical_hash

    def _read_shard_text_v2(self, data_offset: int, data_length: int) -> str:
        """Read shard text in v2 format (no null terminator)."""
        self.file.seek(data_offset)
        return self.file.read(data_length).decode('utf-8', errors='replace')

    def _read_shard_text_v31(self, data_offset: int, data_length: int) -> str:
        """Read shard text in v3.1 format (null-terminated; strip the 0x00)."""
        self.file.seek(data_offset)
        raw = self.file.read(data_length)
        # Strip null terminator
        if raw and raw[-1] == 0:
            raw = raw[:-1]
        return raw.decode('utf-8', errors='replace')

    def get_matches(self, query_text, top_n=2):
        terms = [t.lower().strip() for t in query_text.split() if len(t) > 2]
        # Include N-Grams
        ngrams = terms[:]
        for i in range(len(terms)-1):
            ngrams.append(f"{terms[i]} {terms[i+1]}")

        scores = {}  # shard_idx -> score

        if self.is_v2:
            # v2: use local bloom filter for pre-screening
            for term in ngrams:
                if not self.contains_keyword(term):
                    continue

                self.file.seek(self.index_offset)
                local_indices = get_tah_indices(term, 512, 4)

                for i in range(self.shard_count):
                    entry_data = self.file.read(SHARD_ENTRY_SIZE)
                    offset, length, word_count, local_bloom = self._read_shard_entry_v2(entry_data)

                    # Check Local Bloom
                    match = True
                    for idx in local_indices:
                        if not (local_bloom[idx // 8] & (1 << (idx % 8))):
                            match = False
                            break

                    if match:
                        idf = math.log((self.shard_count - 0 + 0.5) / (0 + 0.5) + 1.0)
                        tf = 1.0
                        score = idf * (tf * 2.5) / (tf + 1.5 * (0.25 + 0.75 * (word_count / self.avg_shard_len)))
                        if " " in term:
                            score *= 3.0
                        scores[i] = scores.get(i, 0) + score

        else:
            # v3.1: surgical-hash primary lookup + global bloom pre-screen
            for term in ngrams:
                if not self.contains_keyword(term):
                    continue

                term_hash = city_hash64(normalize(term)) & 0xFFFFFFFFFFFFFFFF

                self.file.seek(self.index_offset)
                for i in range(self.shard_count):
                    entry_data = self.file.read(SHARD_ENTRY_SIZE)
                    offset, length, word_count, surgical_hash = self._read_shard_entry_v31(entry_data)

                    # Primary: surgical-hash exact match on primary keyword
                    # Secondary: BM25 fallback for all shards that pass global bloom.
                    # Spec section 4.1 step 2-3 retrieval logic.
                    matched = False
                    boost = 1.0
                    if surgical_hash != 0 and surgical_hash == term_hash:
                        matched = True
                        boost = 5.0  # strong boost for surgical match
                    else:
                        matched = True  # BM25 fallback

                    if matched:
                        idf = math.log((self.shard_count - 0 + 0.5) / (0 + 0.5) + 1.0)
                        tf = 1.0
                        score = idf * (tf * 2.5) / (tf + 1.5 * (0.25 + 0.75 * (word_count / self.avg_shard_len)))
                        if " " in term:
                            score *= 3.0
                        score *= boost
                        scores[i] = scores.get(i, 0) + score

        # Sort and return text
        sorted_indices = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_n]
        results = []
        for idx in sorted_indices:
            self.file.seek(self.index_offset + (idx * SHARD_ENTRY_SIZE))
            entry_data = self.file.read(SHARD_ENTRY_SIZE)
            if self.is_v2:
                offset, length, _, _ = self._read_shard_entry_v2(entry_data)
                results.append(self._read_shard_text_v2(offset, length))
            else:
                offset, length, _, _ = self._read_shard_entry_v31(entry_data)
                results.append(self._read_shard_text_v31(offset, length))

        return results

    def close(self):
        self.file.close()


if __name__ == "__main__":
    import time as _time

    args = sys.argv[1:]

    # --bench <cartridge> mode: cold vs warm timing
    if len(args) >= 2 and args[0] == "--bench":
        cartridge_path = args[1]

        # --- Cold run ---
        reset_cache()
        t0 = _time.perf_counter()
        q_cold = TAHQuery(cartridge_path)
        t1 = _time.perf_counter()
        cold_ms = (t1 - t0) * 1000.0
        q_cold.close()

        # --- Warm run ---
        t0 = _time.perf_counter()
        q_warm = TAHQuery(cartridge_path)
        t1 = _time.perf_counter()
        warm_ms = (t1 - t0) * 1000.0
        q_warm.close()

        ratio = warm_ms / cold_ms if cold_ms > 0 else 0.0
        print(f"cold={cold_ms:.1f}ms warm={warm_ms:.1f}ms ratio={ratio:.3f}")
        sys.exit(0)

    # Normal query mode
    if len(args) < 2:
        print("Usage: python builder/tah_query.py <cartridge> <query>")
        print("       python builder/tah_query.py --bench <cartridge>")
        sys.exit(1)

    try:
        q = TAHQuery(args[0])
        matches = q.get_matches(" ".join(args[1:]))
        for m in matches:
            print(f"--- SHARD ---\n{m}\n")
        q.close()
    except Exception as e:
        print(f"Error: {e}")
