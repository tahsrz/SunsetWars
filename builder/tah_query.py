import struct
import math
import sys
import os
from pathlib import Path

# Add current dir to path for imports
sys.path.append(os.path.dirname(__file__))
from cityhash import get_tah_indices

class TAHQuery:
    """
    TAH Query v3.0 - Data-Directed Retrieval
    Dispatches scoring logic based on shard type tags.
    """
    def __init__(self, cartridge_path):
        self.path = Path(cartridge_path)
        if not self.path.exists():
            raise FileNotFoundError(f"Cartridge not found: {cartridge_path}")
        
        self.file = open(self.path, 'rb')
        self._load_metadata()

    def _load_metadata(self):
        header = self.file.read(64)
        magic, self.version, self.k, self.default_type, self.m, self.shard_count, self.avg_complexity = struct.unpack('<I H B B Q I I', header[:24])
        
        if magic != 0x54414821:
            raise ValueError("Invalid TAH cartridge.")

        bloom_size = math.ceil(self.m / 8)
        self.bloom_offset = 64
        self.index_offset = 64 + bloom_size
        
        self.file.seek(self.bloom_offset)
        self.global_bloom = self.file.read(bloom_size)

    def contains_keyword(self, keyword):
        indices = get_tah_indices(keyword, self.m, self.k)
        for idx in indices:
            if not (self.global_bloom[idx // 8] & (1 << (idx % 8))):
                return False
        return True

    def get_matches(self, query_text, top_n=3):
        scores = {}
        terms = [t.lower().strip() for t in query_text.split() if len(t) > 2]
        ngrams = terms[:]
        for i in range(len(terms)-1): ngrams.append(f"{terms[i]} {terms[i+1]}")
        
        self.file.seek(self.index_offset)
        for i in range(self.shard_count):
            entry_data = self.file.read(80)
            tag, offset, length, meta = struct.unpack('<B 7x Q I I', entry_data[:24])
            specialized_index = entry_data[24:80]
            
            score = 0
            if tag == 0: # TEXT
                score = self._score_text(ngrams, specialized_index, meta)
            elif tag == 1: # COORD
                score = self._score_coord(query_text, ngrams, specialized_index, meta)
            elif tag == 2: # IMAGE
                score = self._score_image(ngrams, specialized_index, meta)
            
            if score > 0:
                scores[i] = score

        sorted_indices = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_n]
        results = []
        for idx in sorted_indices:
            self.file.seek(self.index_offset + (idx * 80))
            _, offset, length, _ = struct.unpack('<B 7x Q I I', self.file.read(24))
            self.file.seek(offset)
            results.append(self.file.read(length).decode('utf-8', errors='ignore'))
            
        return results

    def _score_text(self, ngrams, local_bloom, word_count):
        score = 0
        for term in ngrams:
            if not self.contains_keyword(term): continue
            indices = get_tah_indices(term, 448, 4)
            match = True
            for idx in indices:
                if not (local_bloom[idx // 8] & (1 << (idx % 8))):
                    match = False
                    break
            if match:
                idf = math.log((self.shard_count + 0.5) / (1.5) + 1.0)
                tf = 1.0
                s = idf * (tf * 2.5) / (tf + 1.5 * (0.25 + 0.75 * (word_count / self.avg_complexity)))
                if " " in term: s *= 3.0
                score += s
        return score

    def _score_coord(self, query_text, ngrams, local_index, z_order):
        # 1. Physical Proximity
        match = re.match(r'^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)$', query_text.strip())
        if match:
            q_lat, q_lon = map(float, match.groups())
            q_x = int(((q_lon + 180) / 360) * 65535)
            q_y = int(((q_lat + 90) / 180) * 65535)
            q_z = 0
            for i in range(16):
                q_z |= (q_x & (1 << i)) << i
                q_z |= (q_y & (1 << i)) << (i + 1)
            dist = abs(q_z - z_order)
            if dist == 0: return 100.0
            return 10.0 / (math.log(dist + 1) + 1)
        
        # 2. Semantic Label Match
        score = 0
        for term in ngrams:
            if not self.contains_keyword(term): continue
            # Label bloom starts at byte 8
            indices = get_tah_indices(term, 384, 4)
            match = True
            for idx in indices:
                byte_idx = (idx // 8) + 8
                if byte_idx >= 56 or not (local_index[byte_idx] & (1 << (idx % 8))):
                    match = False
                    break
            if match: score += 50.0
        return score

    def _score_image(self, ngrams, local_index, meta):
        score = 0
        for term in ngrams:
            if not self.contains_keyword(term): continue
            # Tags bloom starts at byte 8
            indices = get_tah_indices(term, 384, 4)
            match = True
            for idx in indices:
                byte_idx = (idx // 8) + 8
                if byte_idx >= 56 or not (local_index[byte_idx] & (1 << (idx % 8))):
                    match = False
                    break
            if match: score += 50.0
        return score

    def close(self):
        self.file.close()

import re
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python builder/tah_query.py <cartridge> <query>")
        sys.exit(1)
        
    try:
        q = TAHQuery(sys.argv[1])
        matches = q.get_matches(" ".join(sys.argv[2:]))
        for m in matches:
            print(f"--- MATCH ---\n{m}\n")
        q.close()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
