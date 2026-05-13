import math
import struct
import re
import os
import tempfile
import concurrent.futures
from typing import List, Dict, Any, Optional
from cityhash import get_memoria_indices, normalize

# Memoria v3.1 Polymorphic Tags
TAG_TEXT = 0
TAG_COORD = 1
TAG_IMAGE = 2
TAG_VECTOR = 3

class MemoriaBuilder:
    """
    Memoria Knowledge Compiler v3.1 (Polymorphic)
    Implements streaming builds, Ozriel segmentation, and parallel hashing.
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
        
        # Calculate optimal m and k for Global Filter
        self.m = math.ceil(-(self.n * math.log(self.target_fp)) / (math.log(2)**2))
        self.k = math.ceil((self.m / self.n) * math.log(2))
        self.m = math.ceil(self.m / 8) * 8
        
        self.bloom_filter = bytearray(self.m // 8)
        self.shard_entries = [] # List of (type, offset, length, meta, specialized_index)
        
        # Streaming storage
        self.temp_data = tempfile.NamedTemporaryFile(delete=False)
        self.current_data_offset = 0
        self.total_word_count = 0

    def _add_to_global_filter(self, text: str):
        indices = get_memoria_indices(text, self.m, self.k)
        for idx in indices:
            byte_idx = idx // 8
            bit_idx = idx % 8
            self.bloom_filter[byte_idx] |= (1 << bit_idx)

    def _generate_text_index(self, text: str) -> bytearray:
        """Generates a 448-bit (56-byte) local bloom filter for text."""
        bloom = bytearray(56)
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        words = clean_text.split()
        
        # Extract Unigrams, Bigrams
        unigrams = [w for w in words if w not in self.NEGATIVE_UNIGRAMS and len(w) > 2]
        bigrams = [" ".join(words[i:i+2]) for i in range(len(words)-1)]
        
        for term in unigrams + bigrams:
            self._add_to_global_filter(term)
            # Local Bloom: m=448, k=4
            indices = get_memoria_indices(term, 448, 4)
            for idx in indices:
                bloom[idx // 8] |= (1 << (idx % 8))
        return bloom

    def add_text_shard(self, text: str, meta: int = None, links: List[int] = None):
        """Adds a text shard with optional recursive binary pointers."""
        text_data = text.encode('utf-8')
        
        # Binary Structure: [UTF-8 Text] [0x00] [LinkCount (B)] [Link1 (I)...]
        links = links or []
        link_data = struct.pack(f'<B {len(links)}I', len(links), *links)
        shard_data = text_data + b'\x00' + link_data
        
        length = len(shard_data)
        
        # Generate Index (Bloom filter only covers the text part)
        specialized = self._generate_text_index(text)
        
        # Word count as metadata if not provided
        word_count = meta if meta is not None else len(text.split())
        self.total_word_count += word_count
        
        # Store data in temp file
        offset = self.current_data_offset
        self.temp_data.write(shard_data)
        self.current_data_offset += length
        
        self.shard_entries.append((TAG_TEXT, offset, length, word_count, specialized))

    def add_coord_shard(self, lat: float, lon: float, label: str):
        """Adds a spatial shard (v3.1 Polymorphic)."""
        data = f"{lat},{lon}|{label}".encode('utf-8')
        length = len(data)
        
        # Simplified Spatial Index: Geohash-like bits in the 56-byte area
        specialized = bytearray(56)
        struct.pack_into('<ff', specialized, 0, lat, lon)
        
        # Index label in global filter
        self._add_to_global_filter(label)
        label_bloom_indices = get_memoria_indices(label, 384, 4) # 56-8 = 48 bytes = 384 bits
        for idx in label_bloom_indices:
            byte_idx = 8 + (idx // 8)
            specialized[byte_idx] |= (1 << (idx % 8))

        offset = self.current_data_offset
        self.temp_data.write(data)
        self.current_data_offset += length
        
        self.shard_entries.append((TAG_COORD, offset, length, 0, specialized))

    def save(self, base_name: str):
        """Finalizes the Memoria vault, saving .hat (header) and .tah (data)."""
        self.temp_data.close()
        
        hat_path = f"{base_name}.hat"
        tah_path = f"{base_name}.tah"
        
        magic_hat = 0x48415421 # 'HAT!'
        version = 0x0350
        shard_count = len(self.shard_entries)
        avg_complexity = self.total_word_count // shard_count if shard_count > 0 else 0
        
        # 1. Write the .HAT (Header Atlas)
        # Header (64 bytes): Magic, Version, k, m, ShardCount, AvgComp
        header = struct.pack('<I H B B Q I I', 
                             magic_hat, version, self.k, 0, self.m, shard_count, avg_complexity)
        header = header.ljust(64, b'\x00')
        
        with open(hat_path, 'wb') as f:
            f.write(header)
            f.write(self.bloom_filter)
            # Write Index Entries (Offsets now refer to the .tah file)
            for tag, offset, length, meta, spec in self.shard_entries:
                # v3.5 Layout: Tag(1), Pad(7), Offset(8), Length(4), Meta(4), Spec(56) = 80 bytes
                entry = struct.pack('<B 7x Q I I', tag, offset, length, meta)
                f.write(entry)
                f.write(spec)

        # 2. Write the .TAH (Tactical Data)
        with open(tah_path, 'wb') as f:
            with open(self.temp_data.name, 'rb') as tmp:
                while True:
                    chunk = tmp.read(1024 * 1024)
                    if not chunk: break
                    f.write(chunk)
                    
        os.unlink(self.temp_data.name)
        print(f"Vault Compiled: {base_name}.hat | {base_name}.tah")
        print(f"Stats: m={self.m}, k={self.k}, Shards={shard_count}")

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
    builder.add_text_shard("The Memoria Protocol ensures surgical intelligence.")
    builder.add_coord_shard(32.7767, -96.7970, "Dallas HQ")
    builder.save("cartridges/test_v3_1.tah")
