import math
import struct
import re
from cityhash import get_tah_indices, normalize

class TAHBuilder:
    """
    TAH Builder v3.0 - Data-Directed Polymorphic Architecture
    Implements SICP principles of Abstraction Barriers and Generic Procedures.
    """
    
    # Type Tags
    TYPE_TEXT = 0
    TYPE_COORD = 1
    TYPE_IMAGE = 2
    TYPE_VECTOR = 3

    # Stopwords for Text
    NEGATIVE_UNIGRAMS = {
        'the', 'and', 'for', 'with', 'under', 'over', 'from', 'this', 'that',
        'these', 'those', 'is', 'are', 'was', 'were', 'been', 'being', 'have',
        'has', 'had', 'what', 'how', 'where', 'when', 'which', 'who', 'whom'
    }

    def __init__(self, target_fp=0.001, expected_elements=1000):
        self.target_fp = target_fp
        self.n = expected_elements
        
        # Calculate optimal m and k for Global Filter
        self.m = math.ceil(-(self.n * math.log(self.target_fp)) / (math.log(2)**2))
        self.k = math.ceil((self.m / self.n) * math.log(2))
        self.m = math.ceil(self.m / 8) * 8
        
        self.bloom_filter = bytearray(self.m // 8)
        self.shards = [] # List of dicts: {data, type, meta, index}
        self.keywords = set()

    def _get_ngrams(self, words, n):
        return [" ".join(words[i:i+n]) for i in range(len(words)-n+1)]

    def calculate_vitality(self, text: str):
        """
        The Ozriel Protocol: Evaluates semantic density.
        Returns a score from 0.0 to 1.0.
        """
        words = text.lower().split()
        if not words: return 0.0
        
        # Count 'Vital' words (not stopwords, length > 3, alphanumeric)
        vital_words = [w for w in words if w not in self.NEGATIVE_UNIGRAMS and len(w) > 3 and any(c.isalpha() for c in w)]
        
        # Ratio of vital content to total content
        density = len(vital_words) / len(words)
        
        # Penalty for 'Structural Noise' (too many numbers, single chars, or symbols)
        noise_count = sum(1 for w in words if re.match(r'^[\d\W_]+$', w))
        noise_penalty = (noise_count / len(words)) * 0.5
        
        score = max(0.0, min(1.0, density - noise_penalty))
        return score

    def add_shard(self, data, type_tag=0, min_vitality=0.2, **kwargs):
        """Generic entry point with Vitality Filtering."""
        if type_tag == self.TYPE_TEXT:
            vitality = self.calculate_vitality(data)
            if vitality < min_vitality:
                # Silently skip 'low-life' shards (boilerplate, page numbers, etc.)
                return False
            self._add_text_shard(data, **kwargs)
            return True
        elif type_tag == self.TYPE_COORD:
            self._add_coord_shard(data, **kwargs)
            return True
        elif type_tag == self.TYPE_IMAGE:
            self._add_image_shard(data, **kwargs)
            return True
        else:
            raise ValueError(f"Unsupported shard type: {type_tag}")

    def _add_text_shard(self, text: str, keywords: list[str] = None, links: list[int] = None):
        shard_data = text.encode('utf-8')
        local_index = bytearray(56) # 448 bits
        
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        words = clean_text.split()
        word_count = len(words)
        
        unigrams = [w for w in words if w not in self.NEGATIVE_UNIGRAMS and len(w) > 2]
        bigrams = self._get_ngrams(words, 2)
        trigrams = self._get_ngrams(words, 3)
        
        def is_vital(phrase):
            return any(w not in self.NEGATIVE_UNIGRAMS for w in phrase.split())

        all_shards_ngrams = unigrams + [b for b in bigrams if is_vital(b)] + [t for t in trigrams if is_vital(t)]
        indexing_terms = keywords if keywords else all_shards_ngrams
            
        for kw in indexing_terms:
            self._add_to_global_filter(kw)
            self._add_to_local_bloom(local_index, kw, 448, 4)
            
        self.shards.append({
            'data': shard_data,
            'type': self.TYPE_TEXT,
            'meta': word_count,
            'index': local_index,
            'links': links if links else []
        })

    def _add_coord_shard(self, coords: tuple[float, float], label: str = "", links: list[int] = None):
        lat, lon = coords
        x = int(((lon + 180) / 360) * 65535)
        y = int(((lat + 90) / 180) * 65535)
        
        z_order = 0
        for i in range(16):
            z_order |= (x & (1 << i)) << i
            z_order |= (y & (1 << i)) << (i + 1)
            
        local_index = bytearray(56)
        struct.pack_into('<I', local_index, 0, z_order)
        
        shard_data = f"{label}|{lat},{lon}".encode('utf-8')
        
        if label:
            # Tokenize label for better retrieval
            clean_label = re.sub(r'[^\w\s]', '', label.lower())
            words = clean_label.split()
            unigrams = [w for w in words if w not in self.NEGATIVE_UNIGRAMS and len(w) > 2]
            bigrams = self._get_ngrams(words, 2)
            
            indexing_terms = [label] + unigrams + bigrams
            
            for term in indexing_terms:
                self._add_to_global_filter(term)
                self._add_to_local_bloom(local_index, term, 384, 4, offset=8)
            
        self.shards.append({
            'data': shard_data,
            'type': self.TYPE_COORD,
            'meta': z_order,
            'index': local_index,
            'links': links if links else []
        })

    def _add_image_shard(self, image_path: str, tags: list[str] = None, links: list[int] = None):
        import hashlib
        phash = int(hashlib.md5(image_path.encode()).hexdigest()[:16], 16)
        
        local_index = bytearray(56)
        struct.pack_into('<Q', local_index, 0, phash)
        
        if tags:
            for tag in tags:
                self._add_to_global_filter(tag)
                # Add tags to local bloom starting at byte 8
                self._add_to_local_bloom(local_index, tag, 384, 4, offset=8)
                
        shard_data = f"IMAGE:{image_path}".encode('utf-8')
        self.shards.append({
            'data': shard_data,
            'type': self.TYPE_IMAGE,
            'meta': 0,
            'index': local_index,
            'links': links if links else []
        })

    def _add_to_global_filter(self, text: str):
        indices = get_tah_indices(text, self.m, self.k)
        for idx in indices:
            self.bloom_filter[idx // 8] |= (1 << (idx % 8))
        self.keywords.add(text.lower().strip())

    def _add_to_local_bloom(self, bloom, text: str, m_bits, k_funcs, offset=0):
        indices = get_tah_indices(text, m_bits, k_funcs)
        for idx in indices:
            byte_idx = (idx // 8) + offset
            bit_idx = idx % 8
            if byte_idx < len(bloom):
                bloom[byte_idx] |= (1 << bit_idx)

    def save(self, file_path: str):
        magic = 0x54414821
        version = 0x0300
        shard_count = len(self.shards)
        
        avg_complexity = sum(s['meta'] for s in self.shards) // shard_count if shard_count > 0 else 0
        
        header = struct.pack('<I H B B Q I I', 
                             magic, version, self.k, self.TYPE_TEXT, self.m, shard_count, avg_complexity)
        header = header.ljust(64, b'\x00')
        
        index_start = 64 + len(self.bloom_filter)
        shard_index_data = bytearray()
        
        # Pre-calculate data offsets
        current_offset = index_start + (shard_count * 80)
        offsets = []
        
        final_shard_data = []
        for s in self.shards:
            offsets.append(current_offset)
            
            # Prepare data: [Raw Data] [0x00] [Link Count] [Link 1 Offset] ...
            data = bytearray(s['data'])
            data.append(0) # Null separator
            data.extend(struct.pack('<I', len(s['links'])))
            
            # Temporary storage for link indices to be converted to offsets
            final_shard_data.append({'base_data': data, 'links': s['links']})
            current_offset += len(data) + (len(s['links']) * 8)

        # Build the final data blocks and the index
        for i, s in enumerate(self.shards):
            # Convert link indices to absolute offsets
            link_offsets = [offsets[idx] for idx in final_shard_data[i]['links'] if idx < len(offsets)]
            
            full_data = final_shard_data[i]['base_data']
            for lo in link_offsets:
                full_data.extend(struct.pack('<Q', lo))
            
            entry = struct.pack('<B 7x Q I I', s['type'], offsets[i], len(full_data), s['meta'])
            shard_index_data.extend(entry)
            shard_index_data.extend(s['index'])
            final_shard_data[i]['full'] = full_data
            
        with open(file_path, 'wb') as f:
            f.write(header)
            f.write(self.bloom_filter)
            f.write(shard_index_data)
            for fd in final_shard_data:
                f.write(fd['full'])
        
        print(f"Cartridge saved to {file_path} (v3.0 Polymorphic with Binary Linking)")
        print(f"Stats: m={self.m}, k={self.k}, Shards={shard_count}, Links={sum(len(s['links']) for s in self.shards)}")

if __name__ == "__main__":
    builder = TAHBuilder(target_fp=0.001, expected_elements=100)
    builder.add_shard("Structure and Interpretation of Computer Programs", type_tag=TAHBuilder.TYPE_TEXT)
    builder.add_shard((32.7767, -96.7970), type_tag=TAHBuilder.TYPE_COORD, label="Dallas")
    builder.add_shard("assets/sunset.jpg", type_tag=TAHBuilder.TYPE_IMAGE, tags=["sunset", "orange"])
    builder.save("cartridges/polymorphic_test.tah")
