import struct
import math
import sys
import os
import json
from pathlib import Path

# Add current dir to path for imports
sys.path.append(os.path.dirname(__file__))
from cityhash import get_memoria_indices, city_hash64, normalize
from webgraph import BitReader

# Memoria v3.6 Tags
TAG_TEXT = 0
TAG_COORD = 1

class MemoriaQuery:
    """
    Memoria Query Engine v3.6 (Intelligence-Aware)
    Supports v3.6 binary layout with Source Registry, Analytics, and WebGraph Links.
    """
    def __init__(self, base_path):
        self.base = str(base_path).replace('.hat', '').replace('.tah', '')
        self.hat_path = Path(f"{self.base}.hat")
        self.tah_path = Path(f"{self.base}.tah")
        
        if not self.hat_path.exists():
            raise FileNotFoundError(f"Header Atlas not found: {self.hat_path}")
        
        self.hat_file = open(self.hat_path, 'rb')
        self.tah_file = None
        self.source_registry = []
        self.links_data = b""
        self._load_metadata()

    def _load_metadata(self):
        # 1. Read Header (v3.6: 48 bytes used in 64B block)
        header = self.hat_file.read(64)
        # Format: <I H B x Q I I Q I Q I (Magic, Ver, k, Pad, m, Shards, AvgComp, RegOff, RegLen, LinksOff, LinksLen)
        magic, version, self.k, self.m, self.shard_count, self.avg_complexity, reg_off, reg_len, links_off, links_len = struct.unpack('<I H B x Q I I Q I Q I', header[:48])
        
        if magic not in (0x54414821, 0x48415421):
            raise ValueError(f"Invalid Memoria Header: {hex(magic)}")

        # 2. Map Global Bloom
        bloom_size = self.m // 8
        self.bloom_offset = 64
        self.index_offset = 64 + bloom_size
        
        self.hat_file.seek(self.bloom_offset)
        self.global_bloom = self.hat_file.read(bloom_size)

        # 3. Load Source Registry
        if reg_len > 0:
            self.hat_file.seek(reg_off)
            reg_json = self.hat_file.read(reg_len).decode('utf-8')
            self.source_registry = json.loads(reg_json)

        # 4. Load Links Data
        if links_len > 0:
            self.hat_file.seek(links_off)
            self.links_data = self.hat_file.read(links_len)

    def decode_links(self, shard_index, link_count, link_offset):
        if link_count == 0 or not self.links_data:
            return []
        
        # Simple decode implementation matching WebGraph.cs/webgraph.ts
        reader = BitReader(self.links_data[link_offset:])
        
        # 1. Outdegree
        actual_outdegree = reader.read_gamma() - 1
        # 2. Reference (Distance 0)
        ref_dist = reader.read_gamma() - 1
        # 3. Intervals
        num_intervals = reader.read_gamma() - 1
        
        links = []
        last_pos = shard_index
        for _ in range(num_intervals):
            zigzag = reader.read_gamma() - 1
            gap = (zigzag // 2) if (zigzag % 2 == 0) else -(zigzag // 2 + 1)
            start = last_pos + gap
            length = reader.read_gamma() + 2
            for i in range(length):
                links.append(start + i)
            last_pos = start + length
            
        while len(links) < actual_outdegree:
            zigzag = reader.read_gamma() - 1
            gap = (zigzag // 2) if (zigzag % 2 == 0) else -(zigzag // 2 + 1)
            val = last_pos + gap
            links.append(val)
            last_pos = val + 1
            
        return sorted(links)

    def _open_tah(self):
        if not self.tah_file:
            if not self.tah_path.exists():
                raise FileNotFoundError(f"Tactical Data not found: {self.tah_path}")
            self.tah_file = open(self.tah_path, 'rb')

    def contains_keyword(self, keyword):
        indices = get_memoria_indices(keyword, self.m, self.k)
        for idx in indices:
            if not (self.global_bloom[idx // 8] & (1 << (idx % 8))):
                return False
        return True

    def get_matches(self, query_text, top_n=3):
        query_hash = city_hash64(normalize(query_text))
        terms = [t.lower().strip() for t in query_text.split() if len(t) > 2]
        ngrams = terms[:]
        for i in range(len(terms)-1): ngrams.append(f"{terms[i]} {terms[i+1]}")
        
        scores = {}
        
        # O(1) Pre-check via Global Bloom
        if not any(self.contains_keyword(term) for term in ngrams):
            return []

        # Local Bloom indices for sub-search (m=288, k=4)
        term_indices = {term: get_memoria_indices(term, 288, 4) for term in ngrams if self.contains_keyword(term)}

        self.hat_file.seek(self.index_offset)
        for i in range(self.shard_count):
            entry_data = self.hat_file.read(80)
            # v3.6: Tag(1), LinkCount(2), LinkOff(4), Pad(1), Offset(8), Length(4), SID(2), RID(2), Hash(8), Comp(4), Rel(4), Time(4), Bloom(36)
            tag, lcnt, loff = struct.unpack('<B H I x', entry_data[:8])
            offset, length = struct.unpack('<Q I', entry_data[8:20])
            sid, rid = struct.unpack('<HH', entry_data[20:24])
            h, comp, rel, ts, bloom = struct.unpack('<Q f f I 36s', entry_data[24:80])
            
            if h == query_hash:
                scores[i] = scores.get(i, 0) + 100.0 # Surgical Match

            if tag == TAG_TEXT:
                for term, local_indices in term_indices.items():
                    match = True
                    for idx in local_indices:
                        if not (bloom[idx // 8] & (1 << (idx % 8))):
                            match = False
                            break
                    if match:
                        # Intelligence-Weighted Score (Handle NaN for legacy v3.0 cartridges)
                        s_rel = rel if not math.isnan(rel) else 1.0
                        s_comp = comp if not math.isnan(comp) else 1.0
                        score = (s_rel * 2.0) + (s_comp * 1.5)
                        if " " in term: score *= 2.0
                        scores[i] = scores.get(i, 0) + score
        
        sorted_indices = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_n]
        results = []
        if sorted_indices:
            self._open_tah()
            for idx in sorted_indices:
                # Re-fetch entry for data
                self.hat_file.seek(self.index_offset + (idx * 80))
                entry_data = self.hat_file.read(80)
                tag, lcnt, loff = struct.unpack('<B H I x', entry_data[:8])
                offset, length = struct.unpack('<Q I', entry_data[8:20])
                sid, rid = struct.unpack('<HH', entry_data[20:24])
                
                self.tah_file.seek(offset)
                raw_data = self.tah_file.read(length).decode('utf-8', errors='ignore').split('\0')[0]
                
                source = self.source_registry[sid] if sid < len(self.source_registry) else {"url": "unknown"}
                links = self.decode_links(idx, lcnt, loff)
                
                results.append({
                    "index": idx,
                    "data": raw_data,
                    "source": source["url"],
                    "location": source.get("location", "USA"),
                    "score": scores[idx],
                    "links": links
                })
        return results

    def close(self):
        self.hat_file.close()
        if self.tah_file: self.tah_file.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python builder/memoria_query.py <cartridge> <query>")
        sys.exit(1)
        
    try:
        q = MemoriaQuery(sys.argv[1])
        matches = q.get_matches(" ".join(sys.argv[2:]))
        for m in matches:
            print(f"--- MATCH (Score: {m['score']:.2f}) ---")
            print(f"Source: {m['source']} | Origin: {m['location']}")
            print(f"Index: {m['index']} | Links: {m['links']}")
            print(f"{m['data']}\n")
        q.close()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
