import struct
import hashlib
import json
from typing import List, Dict, Any, Optional

# Memoria v3.5 Swarm Tags
TAG_TEXT = 0
TAG_SWARM_SYMBOL = 4 # New tag for shards with Symbol Tables

class SwarmMemoriaBuilder:
    """
    Memoria Swarm Builder v3.5 (Late-Binding Prototype)
    Implements Shards with Local Symbol Tables for Asynchronous DHT-based Linking.
    """
    
    def __init__(self):
        self.data_store = bytearray()
        self.shard_entries = []
        self.current_offset = 0
        self.symbol_registry = {} # Simulated Global DHT: SymbolHash -> GlobalOffset

    def _generate_cid(self, data: bytes) -> str:
        """Simulates an IPFS-style multihash (CID)."""
        return hashlib.sha256(data).hexdigest()

    def add_swarm_shard(self, text: str, symbols: List[str] = None):
        """
        Adds a shard with a Local Symbol Table for Late Binding.
        
        Binary Layout:
        [UTF-8 Text] 
        [0x00] (Null Terminator)
        [SymbolCount (H)] 
        [Symbol1_Hash (32B)][Symbol2_Hash (32B)...]
        """
        text_data = text.encode('utf-8')
        symbols = symbols or []
        
        symbol_hashes = [hashlib.sha256(s.encode('utf-8')).digest() for s in symbols]
        
        # Pack Symbol Table: Count (Unsigned Short) + N * 32-byte hashes
        symbol_table = struct.pack(f'<H', len(symbol_hashes))
        for s_hash in symbol_hashes:
            symbol_table += s_hash
            
        shard_data = text_data + b'\x00' + symbol_table
        length = len(shard_data)
        
        # In a real swarm, the offset would be derived from the CID or DHT range
        # Here we use contiguous allocation but record the CID
        cid = self._generate_cid(text_data)
        offset = self.current_offset
        
        self.data_store.extend(shard_data)
        self.current_offset += length
        
        # Record entry for the .hat (header)
        # v3.5 Layout: Tag, Offset(Q), Length(I), Meta(I), Spec(56B)
        self.shard_entries.append({
            'tag': TAG_SWARM_SYMBOL,
            'offset': offset,
            'length': length,
            'cid': cid,
            'symbols': symbols
        })
        
        return offset

    def register_symbol(self, symbol_name: str, offset: int):
        """Simulates DHT registration."""
        s_hash = hashlib.sha256(symbol_name.encode('utf-8')).hexdigest()
        self.symbol_registry[s_hash] = offset

    def save_prototype(self, base_name: str):
        """Saves the prototype .tah and a sidecar DHT state."""
        tah_path = f"{base_name}.tah"
        with open(tah_path, 'wb') as f:
            f.write(self.data_store)
            
        # Save simulated DHT for the resolver to use
        dht_path = f"{base_name}_dht.json"
        with open(dht_path, 'w') as f:
            json.dump(self.symbol_registry, f, indent=2)
            
        print(f"Prototype Saved: {tah_path} and {dht_path}")

class SwarmResolver:
    """Simulates the MemoriaCommunicator's Late-Binding Resolver."""
    
    def __init__(self, tah_path: str, dht_path: str):
        self.tah_path = tah_path
        with open(dht_path, 'r') as f:
            self.dht = json.load(f)

    def resolve_shard(self, offset: int, length: int = -1):
        """Reads a shard and resolves its local symbol table."""
        with open(self.tah_path, 'rb') as f:
            f.seek(offset)
            if length > 0:
                data = f.read(length)
            else:
                data = f.read() # Read remainder if length not known
            
        # Split text and symbol table at the FIRST null terminator
        null_pos = data.find(b'\x00')
        if null_pos == -1:
            return data.decode('utf-8'), []
            
        text = data[:null_pos].decode('utf-8')
        symbol_data = data[null_pos+1:]
        
        if len(symbol_data) < 2:
            return text, []

        count = struct.unpack('<H', symbol_data[:2])[0]
        hashes = [symbol_data[2+i*32:2+(i+1)*32].hex() for i in range(count)]
        
        resolved_links = []
        for h in hashes:
            global_offset = self.dht.get(h, "UNRESOLVED")
            resolved_links.append({'hash': h, 'offset': global_offset})
            
        return text, resolved_links

if __name__ == "__main__":
    builder = SwarmMemoriaBuilder()
    
    # 1. Add a 'Dependency' shard
    dep_text = "RFC 7540: Hypertext Transfer Protocol Version 2 (HTTP/2)"
    dep_offset = builder.add_swarm_shard(dep_text)
    builder.register_symbol("RFC_7540", dep_offset)
    
    # Calculate exact length of shard 1 to find shard 2
    # [Text] + [Null] + [Count(2)] + [0 Symbols]
    shard1_len = len(dep_text.encode('utf-8')) + 1 + 2
    
    # 2. Add a 'Primary' shard that references the dependency
    primary_text = "Sunset Pulse uses high-performance networking via HTTP/2."
    builder.add_swarm_shard(
        primary_text,
        symbols=["RFC_7540"]
    )
    
    builder.save_prototype("cartridges/swarm_test")
    
    # 3. Test Resolution
    resolver = SwarmResolver("cartridges/swarm_test.tah", "cartridges/swarm_test_dht.json")
    
    # Resolve the second shard
    text, links = resolver.resolve_shard(shard1_len)
    
    print("\n--- Resolved Shard ---")
    print(f"Content: {text}")
    for link in links:
        print(f"Linked Symbol Hash: {link['hash']} -> Global Offset: {link['offset']}")
