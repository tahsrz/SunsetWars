import os
import sys
import time
import json
import wikipediaapi
from pathlib import Path

# Add builder to path
sys.path.append(os.path.dirname(__file__))
from memoria_builder import MemoriaBuilder, OzrielSegmenter

class WikipediaUniversalIndexer:
    """
    Wikipedia A-Z Universal Indexer v3.5 (Ozriel Protocol)
    Performs alphabetical traversal of the entire Wikipedia library.
    """
    def __init__(self, state_file="alphabetical_progress.json"):
        self.wiki = wikipediaapi.Wikipedia(
            user_agent='Jamie-Universal-Indexer/3.5 (SunsetWars; contact:taz@sunsetpulse.com)',
            language='en',
            extract_format=wikipediaapi.ExtractFormat.WIKI
        )
        self.state_file = Path(state_file)
        self.load_state()

    def load_state(self):
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {"last_page": "", "current_letter": "A"}

    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f)

    def _vitality_filter(self, text):
        """Ozriel Protocol: Discard noise, keep signal."""
        if len(text) < 1000: return False # Higher threshold for universal ingestion
        # Exclude disambiguation pages and lists
        if "may refer to:" in text or "List of" in text: return False
        return True

    def crawl_alphabetical(self, batch_size=50):
        print(f"[A-Z Swarm] Resuming from: {self.state['last_page'] or self.state['current_letter']}")
        
        # Use MediaWiki API to get pages from a specific point
        # wikipediaapi doesn't have a direct 'allpages' iterator, so we use categories or seed lists
        # For a true A-Z, we'll use a seed category "Main topic articles" or similar
        # But to be truly A-Z, we'll iterate through the alphabet using seed strings
        
        current_batch = []
        count = 0
        
        # This is a simplified A-Z simulation using category members for high-signal A-Z
        # True A-Z requires the MediaWiki 'allpages' API which we'll simulate here
        search_query = self.state['last_page'] if self.state['last_page'] else self.state['current_letter']
        
        # For the sake of a functional demo that doesn't hang, we'll process 20 pages per turn
        # In a real background process, this would run infinitely.
        pages = self.wiki.categorymembers(self.wiki.page("Category:Main topic articles"))
        
        for title, page in pages.items():
            if count >= batch_size: break
            if title <= self.state['last_page']: continue
            
            print(f"[A-Z Swarm] Indexing: {title}")
            full_page = self.wiki.page(title)
            if self._vitality_filter(full_page.text):
                current_batch.append(f"ARTICLE: {title}\n{full_page.text}")
                count += 1
            
            self.state['last_page'] = title
            self.save_state()

        if current_batch:
            self.compile_batch(current_batch)

    def compile_batch(self, content_list):
        full_text = "\n\n--- NEXT ARTICLE ---\n\n".join(content_list)
        shards = OzrielSegmenter.segment(full_text, max_shard_size=1500)
        
        builder = MemoriaBuilder(expected_elements=len(shards) * 50)
        for shard in shards:
            builder.add_text_shard(shard)
            
        timestamp = int(time.time())
        vault_name = f"universe/alphabetical_{self.state['current_letter']}_{timestamp}"
        builder.save(f"cartridges/{vault_name}")
        print(f"[A-Z Swarm] Vault {vault_name} compiled with {len(shards)} shards.")

if __name__ == "__main__":
    indexer = WikipediaUniversalIndexer()
    while True:
        try:
            indexer.crawl_alphabetical(batch_size=25)
            print("[A-Z Swarm] Batch complete. Sleeping for throttle control...")
            time.sleep(60) # High throttle to respect Wiki API and token usage
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[Error] Swarm stall: {e}")
            time.sleep(10)
