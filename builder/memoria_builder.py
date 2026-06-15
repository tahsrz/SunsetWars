import math
import struct
import re
import os
import time
import json
import tempfile
import concurrent.futures
from typing import List, Dict, Any, Optional
from cityhash import get_memoria_indices, normalize, city_hash64
from webgraph import BVGraphEncoder

# Memoria v3.6 Polymorphic Tags
TAG_TEXT = 0
TAG_COORD = 1
TAG_IMAGE = 2
TAG_VECTOR = 3

# Region Mapping (Simplified for v3.6)
REGION_CODES = {
    "USA_TX": 1,
    "USA_CA": 2,
    "USA_NY": 3,
    "USA_FL": 4,
    "UK": 100,
    "DE": 101,
    "FR": 102,
    "JP": 103,
    "UNKNOWN": 0
}

class MemoriaBuilder:
    """
    Memoria Knowledge Compiler v3.6 (Intelligence-Aware)
    Implements v3.6 layout with Source Registry, Analytics, and Region Tracking.
    """
    
    NEGATIVE_UNIGRAMS = {
        'the', 'and', 'for', 'with', 'under', 'over', 'from', 'this', 'that',
        'these', 'those', 'is', 'are', 'was', 'were', 'been', 'being', 'have',
        'has', 'had', 'what', 'how', 'where', 'when', 'which', 'who', 'whom',
        'common', 'rules', 'general', 'about', 'above', 'below', 'into', 'onto'
    }

    def __init__(self, target_fp=0.0001, expected_elements=5000):
        self.target_fp = target_fp
        self.n = expected_elements
        
        # WebGraph Integration
        self.graph_encoder = BVGraphEncoder()
        self.compressed_links = [] # List of bytes
        
        # Calculate optimal m and k for Global Filter
        self.m = math.ceil(-(self.n * math.log(self.target_fp)) / (math.log(2)**2))
        self.k = math.ceil((self.m / self.n) * math.log(2))
        self.m = math.ceil(self.m / 8) * 8
        
        self.bloom_filter = bytearray(self.m // 8)
        self.shard_entries = [] # List of (type, offset, length, source_id, region_id, hash, complexity, relevance, timestamp, bloom)
        
        # Source Registry
        self.source_registry = [] # List of {"url": str, "location": str, "timestamp": int}
        self.source_map = {} # url -> source_id
        
        # Streaming storage
        self.temp_data = tempfile.NamedTemporaryFile(delete=False)
        self.current_data_offset = 0
        self.total_word_count = 0

    def get_or_create_source(self, url: str, location: str = "UNKNOWN") -> int:
        if url in self.source_map:
            return self.source_map[url]
        
        source_id = len(self.source_registry)
        self.source_registry.append({
            "url": url,
            "location": location,
            "created_at": int(time.time())
        })
        self.source_map[url] = source_id
        return source_id

    def calculate_complexity(self, text: str) -> float:
        """Lexical Diversity as a proxy for Information Density."""
        tokens = re.findall(r'\w+', text.lower())
        if not tokens: return 0.0
        return float(len(set(tokens)) / len(tokens))

    def _add_to_global_filter(self, text: str):
        indices = get_memoria_indices(text, self.m, self.k)
        for idx in indices:
            byte_idx = idx // 8
            bit_idx = idx % 8
            self.bloom_filter[byte_idx] |= (1 << bit_idx)

    def _generate_local_bloom(self, text: str) -> bytearray:
        """Generates a 288-bit (36-byte) local bloom filter for text."""
        bloom = bytearray(36)
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        words = clean_text.split()
        
        # Extract Unigrams, Bigrams
        unigrams = [w for w in words if w not in self.NEGATIVE_UNIGRAMS and len(w) > 2]
        bigrams = [" ".join(words[i:i+2]) for i in range(len(words)-1)]
        
        for term in unigrams + bigrams:
            self._add_to_global_filter(term)
            # Local Bloom: m=288, k=4
            indices = get_memoria_indices(term, 288, 4)
            for idx in indices:
                bloom[idx // 8] |= (1 << (idx % 8))
        return bloom

    def add_text_shard(self, text: str, url: str = "local://manual", location: str = "USA_TX", relevance: float = 0.8, links: List[int] = None):
        """Adds an intelligence-aware text shard with optional WebGraph out-links."""
        text_data = text.encode('utf-8')
        shard_data = text_data + b'\x00' # Simple null-terminated for now
        length = len(shard_data)
        
        # Metadata & Analytics
        source_id = self.get_or_create_source(url, location)
        region_id = REGION_CODES.get(location, 0)
        complexity = self.calculate_complexity(text)
        timestamp = int(time.time())
        kw_hash = city_hash64(normalize(text))
        
        # WebGraph Links
        link_offset = 0
        link_count = 0
        if links:
            shard_id = len(self.shard_entries)
            compressed = self.graph_encoder.encode_node(shard_id, links)
            link_offset = sum(len(b) for b in self.compressed_links)
            self.compressed_links.append(compressed)
            link_count = len(links)

        # Indices
        bloom = self._generate_local_bloom(text)
        
        # Word count tracking
        self.total_word_count += len(text.split())
        
        # Store data
        offset = self.current_data_offset
        self.temp_data.write(shard_data)
        self.current_data_offset += length
        
        self.shard_entries.append((
            TAG_TEXT, offset, length, source_id, region_id, 
            kw_hash, complexity, relevance, timestamp, bloom,
            link_offset, link_count
        ))

    def save(self, base_name: str):
        """Finalizes v3.6 Memoria vault with Source Registry and WebGraph Links."""
        self.temp_data.close()
        
        hat_path = f"{base_name}.hat"
        tah_path = f"{base_name}.tah"
        
        magic_tah = 0x54414821 # 'TAH!'
        version = 0x0360
        shard_count = len(self.shard_entries)
        avg_complexity = self.total_word_count // shard_count if shard_count > 0 else 0
        
        # Serialize Source Registry
        registry_json = json.dumps(self.source_registry).encode('utf-8')
        registry_len = len(registry_json)
        
        # WebGraph Links Section
        links_data = b"".join(self.compressed_links)
        links_len = len(links_data)
        
        # Calculate offsets
        bloom_byte_size = len(self.bloom_filter)
        index_offset = 64 + bloom_byte_size
        registry_offset = index_offset + (shard_count * 80)
        links_offset = registry_offset + registry_len
        
        # Header (64 bytes): Magic(4), Ver(2), k(1), Pad(1), m(8), Shards(4), AvgComp(4), RegistryOff(8), RegistryLen(4), LinksOff(8), LinksLen(4), Pad(12)
        header = struct.pack('<I H B x Q I I Q I Q I', 
                             magic_tah, version, self.k, self.m, shard_count, 
                             avg_complexity, registry_offset, registry_len,
                             links_offset, links_len)
        header = header.ljust(64, b'\x00')
        
        with open(hat_path, 'wb') as f:
            f.write(header)
            f.write(self.bloom_filter)
            
            # Layout: Tag(1), LinkCount(2), LinkOff(4), Pad(1), Offset(8), Length(4), SourceID(2), RegionID(2), Hash(8), Comp(4), Rel(4), Time(4), Bloom(36)
            for tag, offset, length, sid, rid, h, comp, rel, ts, bloom, loff, lcnt in self.shard_entries:
                # First 8 bytes: Tag(1) + LinkCount(2) + LinkOff(4) + Pad(1)
                entry_head = struct.pack('<B H I x', tag, lcnt, loff)
                # Next 12 bytes: Offset(8) + Length(4)
                entry_data = struct.pack('<Q I', offset, length)
                # Next 4 bytes: SourceID(2) + RegionID(2)
                ids = struct.pack('<HH', sid, rid)
                # Remaining: Hash(8) + Comp(f32) + Rel(f32) + Time(u32) + Bloom(36) = 56 bytes
                analytics = struct.pack('<Q f f I 36s', h, comp, rel, ts, bloom)
                f.write(entry_head + entry_data + ids + analytics)
            
            # Append Source Registry
            f.write(registry_json)
            # Append WebGraph Links
            f.write(links_data)

        # 2. Write the .TAH (Tactical Data)
        with open(tah_path, 'wb') as f:
            with open(self.temp_data.name, 'rb') as tmp:
                while True:
                    chunk = tmp.read(1024 * 1024)
                    if not chunk: break
                    f.write(chunk)
                    
        os.unlink(self.temp_data.name)
        print(f"Vault v3.6 Compiled: {base_name}.hat | {base_name}.tah")
        print(f"Analytics: Sources={len(self.source_registry)}, Avg Complexity={avg_complexity}%")

class OzrielSegmenter:
    """Smart segmentation for Ozriel Protocol compliance."""
    @staticmethod
    def segment(text: str, max_shard_size=1200) -> List[str]:
        # Split by double newlines or headers first
        raw_chunks = re.split(r'\n\n|(?=^# )', text, flags=re.MULTILINE)
        refined_shards = []
        
        current_shard = ""
        for chunk in raw_chunks:
            if len(current_shard) + len(chunk) < max_shard_size:
                current_shard += "\n\n" + chunk if current_shard else chunk
            else:
                if current_shard: refined_shards.append(current_shard.strip())
                current_shard = chunk
        
        if current_shard: refined_shards.append(current_shard.strip())
        return [s for s in refined_shards if len(s) > 50] # Vitality threshold

if __name__ == "__main__":
    builder = MemoriaBuilder(expected_elements=1000)
    builder.add_text_shard(
        "The Memoria Protocol ensures surgical intelligence via probabilistic binary structures.",
        url="https://sunsetpulse.ai/docs/protocol",
        location="USA_TX"
    )
    builder.add_text_shard(
        "SICP introduces the Metacircular Evaluator, a core component of lisp-based intelligence.",
        url="https://mitpress.mit.edu/sicp",
        location="USA_CA"
    )
    builder.save("cartridges/test_v3_6")
