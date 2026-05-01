import math
import struct
import re
from cityhash import get_tah_indices, normalize

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
        self.shards = [] # List of dicts: {data, local_bloom, word_count}
        self.keywords = set()

    def _get_ngrams(self, words, n):
        return [" ".join(words[i:i+n]) for i in range(len(words)-n+1)]

    def add_shard(self, text: str, keywords: list[str] = None):
        shard_data = text.encode('utf-8')
        local_bloom = bytearray(64) # 512 bits
        
        # Tokenize for N-Grams and Word Count
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        words = clean_text.split()
        word_count = len(words)
        
        # Generate N-Grams (Unigrams, Bigrams, Trigrams)
        unigrams = [w for w in words if w not in self.NEGATIVE_UNIGRAMS and len(w) > 2]
        bigrams = self._get_ngrams(words, 2)
        trigrams = self._get_ngrams(words, 3)
        
        # Negative N-Gram Logic: We only index Bigrams/Trigrams if they 
        # contain at least one non-stopword to ensure semantic value.
        def is_vital(phrase):
            return any(w not in self.NEGATIVE_UNIGRAMS for w in phrase.split())

        all_shards_ngrams = unigrams + [b for b in bigrams if is_vital(b)] + [t for t in trigrams if is_vital(t)]
        
        # If specific keywords provided, prioritize them
        indexing_terms = keywords if keywords else all_shards_ngrams
            
        for kw in indexing_terms:
            self._add_to_global_filter(kw)
            self._add_to_local_filter(local_bloom, kw)
            
        self.shards.append({
            'data': shard_data,
            'local_bloom': local_bloom,
            'word_count': word_count
        })

    def _add_to_global_filter(self, text: str):
        indices = get_tah_indices(text, self.m, self.k)
        for idx in indices:
            byte_idx = idx // 8
            bit_idx = idx % 8
            self.bloom_filter[byte_idx] |= (1 << bit_idx)
        self.keywords.add(text.lower().strip())

    def _add_to_local_filter(self, bloom, text: str):
        indices = get_tah_indices(text, 512, 4)
        for idx in indices:
            byte_idx = idx // 8
            bit_idx = idx % 8
            bloom[byte_idx] |= (1 << bit_idx)

    def save(self, file_path: str):
        magic = 0x54414821
        version = 0x0200
        shard_count = len(self.shards)
        
        avg_shard_len = sum(s['word_count'] for s in self.shards) // shard_count if shard_count > 0 else 0
        
        header = struct.pack('<I H B B Q I I', 
                             magic, version, self.k, 0, self.m, shard_count, avg_shard_len)
        header = header.ljust(64, b'\x00')
        
        index_start = 64 + len(self.bloom_filter)
        shard_index_data = bytearray()
        current_offset = index_start + (shard_count * 80)
        
        for s in self.shards:
            shard_len = len(s['data'])
            shard_index_data.extend(struct.pack('<Q I I', current_offset, shard_len, s['word_count']))
            shard_index_data.extend(s['local_bloom'])
            current_offset += shard_len
            
        with open(file_path, 'wb') as f:
            f.write(header)
            f.write(self.bloom_filter)
            f.write(shard_index_data)
            for s in self.shards:
                f.write(s['data'])
        
        print(f"Cartridge saved to {file_path} (v2.0)")
        print(f"Stats: m={self.m}, k={self.k}, Shards={shard_count}, AvgLen={avg_shard_len}")

if __name__ == "__main__":
    builder = TAHBuilder(target_fp=0.001, expected_elements=1000)
    builder.add_shard("The Texas Real Estate Commission protects consumers.", ["TREC", "Texas"])
    builder.save("cartridges/test_v2.tah")
