import sys
import os
import time

# Add the builder directory to path to import MemoriaBuilder
sys.path.append(os.path.dirname(__file__))
from memoria_builder import MemoriaBuilder

def forge_from_file(source_file, output_base):
    if not os.path.exists(source_file):
        print(f"[Error] Source file not found: {source_file}")
        return False

    with open(source_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    if not lines:
        print("[Warning] No memories found in source file.")
        return False

    # Initialize builder based on memory density
    builder = MemoriaBuilder(target_fp=0.0001, expected_elements=max(200, len(lines) * 5))
    
    print(f"[Memoria-Forge] Syncing {len(lines)} memories from {os.path.basename(source_file)}...")
    for memory in lines:
        builder.add_text_shard(memory)
        
    builder.save(output_base)
    print(f"[Memoria-Forge] Sync complete: {output_base}")
    return True

if __name__ == "__main__":
    # Standard paths relative to project root
    base_dir = os.path.dirname(os.path.dirname(__file__))
    source_path = os.path.join(base_dir, "user_memories.txt")
    cartridge_dir = os.path.join(base_dir, "cartridges")
    output_base = os.path.join(cartridge_dir, "user_memories")

    if not os.path.exists(cartridge_dir):
        os.makedirs(cartridge_dir)

    # Initial Sync
    forge_from_file(source_path, output_base)

    # Watch Mode (Simple polling for automation)
    if "--watch" in sys.argv:
        print(f"[Watcher] Monitoring {source_path} for changes...")
        last_mtime = os.path.getmtime(source_path)
        try:
            while True:
                time.sleep(2)
                current_mtime = os.path.getmtime(source_path)
                if current_mtime > last_mtime:
                    print("[Watcher] Change detected.")
                    if forge_from_file(source_path, output_base):
                        last_mtime = current_mtime
        except KeyboardInterrupt:
            print("[Watcher] Stopped.")
