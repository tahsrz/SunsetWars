import os
import sys
import json
import time
from pathlib import Path

# Add builder to path for imports
sys.path.append(str(Path(__file__).parent.parent / "builder"))

from web_builder import WebIngestor
from youtube_ingestor import YouTubeIngestor
from tah_builder import TAHBuilder

class Forge:
    """
    The Forge: Automated Intelligence Ingestion Engine.
    Monitors targets.txt and builds a consolidated Workbench Cartridge.
    """
    def __init__(self, workbench_dir="workbench"):
        self.workbench_dir = Path(workbench_dir)
        self.targets_file = self.workbench_dir / "targets.txt"
        self.cache_file = self.workbench_dir / "knowledge_cache.json"
        self.cartridge_path = Path("cartridges/workbench_expertise.tah")
        
        self.web_ingestor = WebIngestor(max_depth=1)
        self.yt_ingestor = YouTubeIngestor(model_size="base")
        
        # Load processed history
        self.cache = self._load_cache()

    def _load_cache(self):
        if self.cache_file.exists():
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"processed_urls": {}, "shards": []}

    def _save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=4)

    def process_targets(self):
        """Reads targets.txt and ingests any new URLs."""
        if not self.targets_file.exists():
            print("[Forge] No targets.txt found.")
            return

        with open(self.targets_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        new_content = False
        for url in urls:
            if url in self.cache["processed_urls"]:
                continue

            print(f"\n[Forge] Ingesting New Target: {url}")
            shards = []
            
            if "youtube.com" in url or "youtu.be" in url:
                # YouTube Ingestion
                # YouTubeIngestor currently builds its own cartridge, 
                # we'll adapt it to return text/shards for the forge.
                # For now, we use a temp cartridge and extract its text.
                temp_name = f"forge_temp_{int(time.time())}"
                self.yt_ingestor.build_cartridge(url, temp_name)
                # Re-loading shards from the builder is cleaner in a real app,
                # but for this script we'll assume the ingestor logic works.
                # (Future improvement: Refactor Ingestors to return Shard lists)
                print("[Forge] YouTube ingestion completed.")
                # Since ingestors currently output files, we'll mark it as processed
                # and in v2 we'll consolidate the actual text shards.
            else:
                # Web Ingestion
                nodes = self.web_ingestor.fetch_semantic_nodes(url)
                if nodes:
                    for node in nodes:
                        # Simple chunking for cache
                        text_shards = self.web_ingestor._chunk_text(node)
                        self.cache["shards"].extend(text_shards)
                    new_content = True

            self.cache["processed_urls"][url] = time.time()
            new_content = True

        if new_content:
            self._rebuild_cartridge()
            self._save_cache()

    def _rebuild_cartridge(self):
        """Rebuilds the workbench cartridge from all cached shards."""
        shard_count = len(self.cache["shards"])
        if shard_count == 0:
            print("[Forge] No knowledge shards to index.")
            return

        print(f"[Forge] Rebuilding Workbench Cartridge with {shard_count} shards...")
        
        # Sizing for total elements (Shards * keyword multiplier)
        expected_elements = shard_count * 25
        builder = TAHBuilder(target_fp=0.0001, expected_elements=expected_elements)
        
        for shard in self.cache["shards"]:
            builder.add_shard(shard)
            
        builder.save(str(self.cartridge_path))
        print(f"[Forge] Workbench expertise updated: {self.cartridge_path}")

if __name__ == "__main__":
    forge = Forge()
    print("=== TAH Inventor's Workbench: The Forge ===")
    while True:
        forge.process_targets()
        print("\n[Forge] Sleeping for 60 seconds... (Ctrl+C to stop)")
        time.sleep(60)
