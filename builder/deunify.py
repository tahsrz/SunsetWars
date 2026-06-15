import struct
import os
from pathlib import Path

def deunify(tah_path):
    tah_path = Path(tah_path)
    base = tah_path.parent / tah_path.stem
    
    with open(tah_path, 'rb') as f:
        header = f.read(64)
        magic, ver, k, m, shards, avg, reg_off, reg_len, links_off, links_len = struct.unpack('<I H B x Q I I Q I Q I', header[:48])
        
        bloom_size = (m + 7) // 8
        index_start = 64 + bloom_size
        index_size = shards * 80
        
        hat_size = index_start + index_size
        
        f.seek(0)
        hat_data = f.read(hat_size)
        tah_data = f.read()
        
    with open(f"{base}.hat", 'wb') as f:
        f.write(hat_data)
    
    # We overwrite the .tah with just the data part to make it standard
    # But wait,oria_query.py expects .tah to be the data part.
    with open(f"{base}.tah", 'wb') as f:
        f.write(tah_data)
        
    print(f"De-unified {tah_path} -> .hat and .tah (Data Offset: {hat_size})")

if __name__ == "__main__":
    import sys
    deunify(sys.argv[1])
