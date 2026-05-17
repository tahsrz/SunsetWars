import os
import sys
import wikipediaapi
from pathlib import Path

# Add builder to path
sys.path.append(os.path.dirname(__file__))
from memoria_builder import MemoriaBuilder, OzrielSegmenter

class WikipediaSwarm:
    """
    Wikipedia Swarm Ingestor v3.1 (Ozriel Protocol)
    Recursively ingests Wikipedia categories into Memoria Vaults.
    """
    def __init__(self, target_fp=0.0001):
        self.wiki = wikipediaapi.Wikipedia(
            user_agent='Jamie-Intelligence-Swarm/3.1 (SunsetWars; contact:taz@sunsetpulse.com)',
            language='en',
            extract_format=wikipediaapi.ExtractFormat.WIKI
        )
        self.target_fp = target_fp
        self.visited_pages = set()

    def _vitality_filter(self, text):
        """Ozriel Protocol Vitality Check: Discard low-signal content."""
        if len(text) < 500: return False
        # Discard boilerplate/lists that are just dates or references
        if text.count('\n') > len(text) / 100: return False 
        return True

    def ingest_category(self, category_name, max_pages=50):
        print(f"[Wiki-Swarm] Initiating Swarm for Category: {category_name}")
        cat = self.wiki.page(f"Category:{category_name}")
        
        ingested_count = 0
        all_content = []
        
        # Ingest pages in this category
        for member in cat.categorymembers.values():
            if ingested_count >= max_pages: break
            if member.ns == wikipediaapi.Namespace.MAIN and member.title not in self.visited_pages:
                print(f"[Wiki-Swarm] Absorbing: {member.title}")
                page = self.wiki.page(member.title)
                if self._vitality_filter(page.text):
                    all_content.append(f"ARTICLE: {member.title}\n{page.text}")
                    self.visited_pages.add(member.title)
                    ingested_count += 1
        
        if not all_content:
            print(f"[Warning] No vital articles found in {category_name}")
            return None

        # Compile into Vault
        full_text = "\n\n--- NEXT ARTICLE ---\n\n".join(all_content)
        shards = OzrielSegmenter.segment(full_text, max_shard_size=1200)
        
        builder = MemoriaBuilder(target_fp=self.target_fp, expected_elements=len(shards) * 40)
        for shard in shards:
            builder.add_text_shard(shard)
            
        vault_name = category_name.lower().replace(" ", "_")
        output_path = f"cartridges/universe/wiki_{vault_name}"
        builder.save(output_path)
        print(f"[Wiki-Swarm] Compiled {vault_name} vault with {len(shards)} shards.")
        return output_path

if __name__ == "__main__":
    swarm = WikipediaSwarm()
    # Initial High-Signal Seeds
    seeds = ["Real estate", "Artificial intelligence", "Dallas", "Blockchain", "SICP"]
    
    for seed in seeds:
        swarm.ingest_category(seed, max_pages=10)
