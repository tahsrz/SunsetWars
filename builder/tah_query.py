import struct
import math
import sys
import os
from pathlib import Path

# Add current dir to path for imports
sys.path.append(os.path.dirname(__file__))
from cityhash import get_tah_indices

class TAHQuery:
    def __init__(self, cartridge_path):
        self.path = Path(cartridge_path)
        if not self.path.exists():
            raise FileNotFoundError(f"Cartridge not found: {cartridge_path}")
        
        self.file = open(self.path, 'rb')
        self._load_metadata()

    def _load_metadata(self):
        # 1. Read Header (64 bytes)
        header = self.file.read(64)
        magic, version, self.k, _, self.m, self.shard_count, self.avg_shard_len = struct.unpack('<I H B B Q I I', header[:28])
        
        if magic != 0x54414821:
            raise ValueError("Invalid TAH cartridge.")

        # 2. Skip Global Bloom (already read header)
        bloom_size = math.ceil(self.m / 8)
        self.bloom_offset = 64
        self.index_offset = 64 + bloom_size
        
        # Load Global Bloom for quick check
        self.file.seek(self.bloom_offset)
        self.global_bloom = self.file.read(bloom_size)

    def contains_keyword(self, keyword):
        indices = get_tah_indices(keyword, self.m, self.k)
        for idx in indices:
            byte_idx = idx // 8
            bit_idx = idx % 8
            if not (self.global_bloom[byte_idx] & (1 << bit_idx)):
                return False
        return True

    def get_matches(self, query_text, top_n=2):
        terms = [t.lower().strip() for t in query_text.split() if len(t) > 2]
        # Include N-Grams
        ngrams = terms[:]
        for i in range(len(terms)-1): ngrams.append(f"{terms[i]} {terms[i+1]}")
        
        scores = {} # shard_idx -> score
        
        # Local Filter Params (v2 spec): m=512, k=4
        for term in ngrams:
            if not self.contains_keyword(term):
                continue
            
            # Scan Shard Index (80 bytes per entry)
            self.file.seek(self.index_offset)
            local_indices = get_tah_indices(term, 512, 4)
            
            for i in range(self.shard_count):
                entry_data = self.file.read(80)
                offset, length, word_count = struct.unpack('<Q I I', entry_data[:16])
                local_bloom = entry_data[16:80]
                
                # Check Local Bloom
                match = True
                for idx in local_indices:
                    if not (local_bloom[idx // 8] & (1 << (idx % 8))):
                        match = False
                        break
                
                if match:
                    # BM25 Scoring (Simplified for tool)
                    idf = math.log((self.shard_count - 0 + 0.5) / (0 + 0.5) + 1.0)
                    tf = 1.0
                    score = idf * (tf * 2.5) / (tf + 1.5 * (0.25 + 0.75 * (word_count / self.avg_shard_len)))
                    
                    # Boost phrases
                    if " " in term: score *= 3.0
                    
                    scores[i] = scores.get(i, 0) + score

        # Sort and return text
        sorted_indices = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_n]
        results = []
        for idx in sorted_indices:
            # Re-read shard info
            self.file.seek(self.index_offset + (idx * 80))
            offset, length, _ = struct.unpack('<Q I I', self.file.read(16))
            self.file.seek(offset)
            results.append(self.file.read(length).decode('utf-8'))
            
        return results

    def close(self):
        self.file.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python builder/tah_query.py <cartridge> <query>")
        sys.exit(1)
        
    try:
        q = TAHQuery(sys.argv[1])
        matches = q.get_matches(" ".join(sys.argv[2:]))
        for m in matches:
            print(f"--- SHARD ---\n{m}\n")
        q.close()
    except Exception as e:
        print(f"Error: {e}")
