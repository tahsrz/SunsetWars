"""
TAH Cartridge Builder -- v3.1

Implements the v3.1 binary format (version field 0x0003) with the following
layout changes from v3.0:

  - Version field emits 0x0003 (LE uint16) instead of 0x0300.
  - Shard-index entry (80 bytes each) migrated to canonical v3.1 layout:
      offset 0:   type byte (1 = UTF-8 text)
      offset 1-7: reserved (zeroed)
      offset 8:   dataOffset uint64 LE
      offset 16:  dataLength uint32 LE  (includes null terminator)
      offset 20:  meta uint32 LE  (word_count)
      offset 24:  surgicalHash uint64 LE  (CityHash64 of primary keyword, or 0)
      offset 32-79: reserved (zeroed)
  - Each shard data payload is null-terminated UTF-8 (dataLength includes 0x00).
  - surgicalHash is CityHash64(normalize(keywords[0])) or 0x0 sentinel if no
    keywords are available.
  - Per-shard local bloom filter (present in earlier layouts) is removed;
    header bytes 20-63 (avg_shard_len field) are zeroed per spec SS2.
  - Global bloom filter and double-hashing logic are unchanged from v3.0.
"""
import math
import struct
import re
from cityhash import city_hash64, get_tah_indices, normalize


# v3.1 format constants (spec SS2 / SS4)
TAH_MAGIC = 0x54414821
TAH_VERSION_V3_1 = 0x0003
HEADER_SIZE = 64
SHARD_ENTRY_SIZE = 80


class TAHBuilder:
    # Stopwords that should never be indexed as isolated Unigrams Commandments
    NEGATIVE_UNIGRAMS = {
        'the', 'and', 'for', 'with', 'under', 'over', 'from', 'this', 'that',
        'these', 'those', 'is', 'are', 'was', 'were', 'been', 'being', 'have',
        'has', 'had', 'what', 'how', 'where', 'when', 'which', 'who', 'whom',
        'common', 'rules', 'general', 'about', 'above', 'below', 'into', 'onto'
    }

    def __init__(self, target_fp=0.001, expected_elements=1000):
        self.target_fp = target_fp
        self.n = expected_elements

        # Calculate optimal m and k for Global Filter
        self.m = math.ceil(-(self.n * math.log(self.target_fp)) / (math.log(2)**2))
        self.k = math.ceil((self.m / self.n) * math.log(2))
        self.m = math.ceil(self.m / 8) * 8

        self.bloom_filter = bytearray(self.m // 8)
        # Each shard dict tracks: data, primary_keyword, word_count
        # (local_bloom removed in v3.1)
        self.shards = []
        self.keywords = set()

    def _get_ngrams(self, words, n):
        return [" ".join(words[i:i+n]) for i in range(len(words)-n+1)]

    def add_shard(self, text: str, keywords: list = None):
        shard_data = text.encode('utf-8')

        # Tokenize for N-Grams and Word Count
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        words = clean_text.split()
        word_count = len(words)

        # Generate N-Grams (Unigrams, Bigrams, Trigrams)
        unigrams = [w for w in words if w not in self.NEGATIVE_UNIGRAMS and len(w) > 2]
        bigrams = self._get_ngrams(words, 2)
        trigrams = self._get_ngrams(words, 3)

        # Negative N-Gram Logic: only index Bigrams/Trigrams if they contain
        # at least one non-stopword to ensure semantic value.
        def is_vital(phrase):
            return any(w not in self.NEGATIVE_UNIGRAMS for w in phrase.split())

        all_shards_ngrams = unigrams + [b for b in bigrams if is_vital(b)] + [t for t in trigrams if is_vital(t)]

        # If specific keywords provided, prioritize them
        indexing_terms = keywords if keywords else all_shards_ngrams

        for kw in indexing_terms:
            self._add_to_global_filter(kw)

        # Determine primary keyword for surgicalHash (v3.1 SS4.1):
        # first element of the caller-supplied list, or first surviving unigram.
        if keywords:
            primary_keyword = keywords[0] if keywords else None
        else:
            primary_keyword = unigrams[0] if unigrams else None

        self.shards.append({
            'data': shard_data,
            'word_count': word_count,
            'primary_keyword': primary_keyword,
        })

    def _add_to_global_filter(self, text: str):
        indices = get_tah_indices(text, self.m, self.k)
        for idx in indices:
            byte_idx = idx // 8
            bit_idx = idx % 8
            self.bloom_filter[byte_idx] |= (1 << bit_idx)
        self.keywords.add(text.lower().strip())

    def _surgical_hash(self, primary_keyword):
        """Return CityHash64(normalize(keyword)) or 0x0 sentinel if no keyword.

        Spec SS4.1: 0x0 (8 zero bytes) is the 'no primary keyword' sentinel.
        CityHash64(b'') == K0 which is a valid hash value; the absent-keyword
        case must use 0x0 explicitly rather than hashing an empty string.
        """
        if not primary_keyword:
            return 0
        return city_hash64(normalize(primary_keyword)) & 0xFFFFFFFFFFFFFFFF

    def _pack_header(self, shard_count: int) -> bytes:
        """Pack the 64-byte v3.1 header per spec SS2.

        Offset 0:  magic uint32 LE (0x54414821)
        Offset 4:  version uint16 LE (0x0003)
        Offset 6:  k uint8
        Offset 7:  reserved 0x00
        Offset 8:  m uint64 LE
        Offset 16: shardCount uint32 LE
        Offset 20-63: reserved (zeroed)
        """
        header = bytearray(HEADER_SIZE)
        struct.pack_into('<I', header, 0, TAH_MAGIC)
        struct.pack_into('<H', header, 4, TAH_VERSION_V3_1)
        struct.pack_into('<B', header, 6, self.k & 0xFF)
        struct.pack_into('<B', header, 7, 0)
        struct.pack_into('<Q', header, 8, self.m & 0xFFFFFFFFFFFFFFFF)
        struct.pack_into('<I', header, 16, shard_count & 0xFFFFFFFF)
        # Bytes 20-63 remain zero (reserved; avg_shard_len from earlier versions dropped)
        return bytes(header)

    def _pack_shard_index_entry(self, data_offset: int, data_length: int,
                                word_count: int, surgical_hash: int) -> bytes:
        """Pack one 80-byte shard-index entry per v3.1 spec SS4.

        type=1 (text) at offset 0, reserved 1-7,
        dataOffset@8 (u64 LE), dataLength@16 (u32 LE),
        meta@20 (u32 LE = word_count), surgicalHash@24 (u64 LE),
        reserved 32-79 zero-padded.
        """
        entry = bytearray(SHARD_ENTRY_SIZE)
        struct.pack_into('<B', entry, 0, 1)  # type=1 (UTF-8 text)
        # offsets 1-7: remain zero (reserved)
        struct.pack_into('<Q', entry, 8, data_offset & 0xFFFFFFFFFFFFFFFF)
        struct.pack_into('<I', entry, 16, data_length & 0xFFFFFFFF)
        struct.pack_into('<I', entry, 20, word_count & 0xFFFFFFFF)
        struct.pack_into('<Q', entry, 24, surgical_hash & 0xFFFFFFFFFFFFFFFF)
        # offsets 32-79: remain zero (reserved)
        return bytes(entry)

    def save(self, file_path: str):
        shard_count = len(self.shards)

        # Pre-compute null-terminated shard payloads (v3.1 SS5: text shards
        # are UTF-8 + 0x00; dataLength includes the null terminator).
        shard_payloads = []
        for s in self.shards:
            payload = s['data'] + b'\x00'
            shard_payloads.append(payload)

        bloom_byte_size = len(self.bloom_filter)
        shard_index_byte_size = shard_count * SHARD_ENTRY_SIZE
        data_region_start = HEADER_SIZE + bloom_byte_size + shard_index_byte_size

        # Build shard index entries
        shard_index_data = bytearray()
        cursor = data_region_start
        for s, payload in zip(self.shards, shard_payloads):
            sh = self._surgical_hash(s['primary_keyword'])
            entry = self._pack_shard_index_entry(
                data_offset=cursor,
                data_length=len(payload),
                word_count=s['word_count'],
                surgical_hash=sh,
            )
            shard_index_data.extend(entry)
            cursor += len(payload)

        header = self._pack_header(shard_count)

        with open(file_path, 'wb') as f:
            f.write(header)
            f.write(self.bloom_filter)
            f.write(shard_index_data)
            for payload in shard_payloads:
                f.write(payload)

        print(f"Cartridge saved to {file_path} (v3.1)")
        if shard_count > 0:
            avg_len = sum(s['word_count'] for s in self.shards) // shard_count
        else:
            avg_len = 0
        print(f"Stats: m={self.m}, k={self.k}, Shards={shard_count}, AvgLen={avg_len}")


if __name__ == "__main__":
    builder = TAHBuilder(target_fp=0.001, expected_elements=1000)
    builder.add_shard("The Texas Real Estate Commission protects consumers.", ["TREC", "Texas"])
    builder.save("cartridges/test_v31.tah")
