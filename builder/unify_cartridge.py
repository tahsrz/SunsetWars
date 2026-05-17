import struct
import os

def unify(base_name):
    hat_path = f"{base_name}.hat"
    tah_path = f"{base_name}.tah"
    output_path = f"{base_name}.unified.tah"

    if not os.path.exists(hat_path) or not os.path.exists(tah_path):
        print(f"[Error] Missing {hat_path} or {tah_path}")
        return

    with open(hat_path, 'rb') as f:
        hat_data = bytearray(f.read())

    # Header is 64 bytes
    header = hat_data[:64]
    magic, version, k, zero, m, shard_count, avg_comp = struct.unpack('<I H B B Q I I', header[:24])
    
    bloom_size = (m + 7) // 8
    index_start = 64 + bloom_size
    index_size = shard_count * 80
    
    hat_size = index_start + index_size
    
    print(f"[Unifier] Unified Size Prefix: {hat_size} bytes")
    
    # Update offsets in the index
    for i in range(shard_count):
        entry_offset = index_start + (i * 80)
        # Tag(1), Pad(7), Offset(8), Length(4), Meta(4), Spec(56)
        # Offset is at entry_offset + 8
        current_offset = struct.unpack('<Q', hat_data[entry_offset+8:entry_offset+16])[0]
        new_offset = current_offset + hat_size
        hat_data[entry_offset+8:entry_offset+16] = struct.pack('<Q', new_offset)

    with open(output_path, 'wb') as f:
        f.write(hat_data)
        with open(tah_path, 'rb') as tf:
            f.write(tf.read())

    print(f"[Unifier] SUCCESS: Created {output_path}")

if __name__ == "__main__":
    import sys
    base = sys.argv[1] if len(sys.argv) > 1 else "cartridges/user_memories"
    unify(base)
