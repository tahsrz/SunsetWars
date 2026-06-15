import os
import sys
import time
import json
import requests
import wikipediaapi
from pathlib import Path

# Add builder to path
sys.path.append(os.path.dirname(__file__))
from memoria_builder import MemoriaBuilder, OzrielSegmenter

class WikipediaUniversalIndexer:
    """
    Wikipedia A-Z Universal Indexer v4.0 (Ozriel Protocol)
    Performs a general alphabetical crawl using the MediaWiki 'allpages' API.
    """
    def __init__(self, state_file="alphabetical_progress.json"):
        self.wiki_api_url = "https://en.wikipedia.org/w/api.php"
        self.wiki = wikipediaapi.Wikipedia(
            user_agent='Jamie-Universal-Indexer/4.0 (SunsetWars; contact:taz@sunsetpulse.com)',
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
            json.dump(self.state, f, indent=2)

    def _vitality_filter(self, text):
        """Ozriel Protocol: Discard noise, keep signal."""
        if len(text) < 1500: return False # Higher threshold for general crawl
        if "may refer to:" in text or "List of" in text: return False
        # Discard boilerplate or low-signal stubs
        if text.count('\n') < 5: return False
        return True

    def get_all_pages_generator(self, apfrom, limit=50):
        """Queries the MediaWiki API for the next batch of alphabetical pages."""
        headers = {
            'User-Agent': 'Jamie-Universal-Indexer/4.0 (SunsetWars; contact:taz@sunsetpulse.com)'
        }
        params = {
            "action": "query",
            "format": "json",
            "list": "allpages",
            "apfrom": apfrom,
            "aplimit": limit,
            "apnamespace": 0, # Main namespace only
            "apfilterredir": "nonredirects"
        }
        
        response = requests.get(self.wiki_api_url, params=params, headers=headers)
        if response.status_code != 200:
            print(f"[Error] API Access Denied ({response.status_code}): {response.text[:100]}")
            return [], None
            
        data = response.json()
        
        if "query" in data and "allpages" in data["query"]:
            return data["query"]["allpages"], data.get("continue", {}).get("apcontinue", None)
        return [], None

    def crawl_alphabetical(self, batch_size=50):
        start_cursor = self.state['last_page'] if self.state['last_page'] else self.state['current_letter']
        print(f"[A-Z Swarm] General Crawl Resuming from: {start_cursor}")
        
        pages_metadata, next_cursor = self.get_all_pages_generator(start_cursor, limit=batch_size)
        
        current_batch = []
        last_processed_title = self.state['last_page']

        for page_meta in pages_metadata:
            title = page_meta['title']
            if title <= self.state['last_page']: continue
            
            print(f"[A-Z Swarm] Indexing: {title}")
            full_page = self.wiki.page(title)
            
            try:
                if self._vitality_filter(full_page.text):
                    current_batch.append(f"ARTICLE: {title}\n{full_page.text}")
                
                last_processed_title = title
            except Exception as e:
                print(f"[A-Z Swarm] Skip {title} due to fetch error: {e}")

        if current_batch:
            self.compile_batch(current_batch)
            
        # Update state with the actual API continuation point or the last title
        self.state['last_page'] = last_processed_title
        if next_cursor:
            # Optionally update current_letter if the cursor moves to a new one
            if next_cursor[0].upper() != self.state['current_letter']:
                self.state['current_letter'] = next_cursor[0].upper()
        
        self.save_state()
        return len(current_batch)

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
            shards_forged = indexer.crawl_alphabetical(batch_size=25)
            if shards_forged == 0:
                print("[A-Z Swarm] Low signal batch. Advancing...")
                time.sleep(5)
                continue
                
            print(f"[A-Z Swarm] Batch complete ({shards_forged} articles). Sleeping for throttle control...")
            time.sleep(30) # Respectful throttle
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[Error] Swarm stall: {e}")
            time.sleep(10)
