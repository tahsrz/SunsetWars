import requests
from bs4 import BeautifulSoup
from tah_builder import TAHBuilder, OzrielSegmenter
import re
import os

class WebIngestor:
    """
    TAH Web Ingestor v3.0 (Ozriel Protocol)
    Implements recursive semantic discovery and v3 polymorphic storage.
    """
    def __init__(self, target_fp=0.0001, shard_size=1200, max_depth=2):
        self.target_fp = target_fp
        self.shard_size = shard_size
        self.max_depth = max_depth
        self.visited_urls = set()
        self.headers = {
            'User-Agent': 'TAH-Ozriel/3.0 (Terminal AI Hub; Protocol-V3)'
        }

    def _vitality_check(self, element):
        text = element.get_text(strip=True)
        if len(text) < 100: return 0
        vitality_score = len(re.findall(r'[A-Z][a-z]{3,}', text)) 
        vitality_score += text.count('(') + text.count('{')
        link_density = len(element.find_all('a')) / (len(text.split()) + 1)
        return vitality_score * (1 - link_density)

    def fetch_semantic_nodes(self, url, depth=0):
        if depth > self.max_depth or url in self.visited_urls:
            return []
        
        self.visited_urls.add(url)
        print(f"[Ozriel-Pulse] Depth {depth}: Scanning {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for noise in soup(['nav', 'footer', 'header', 'script', 'style', 'aside']):
                noise.decompose()

            potential_nodes = soup.find_all(['div', 'section', 'article', 'main'])
            best_node = max(potential_nodes, key=self._vitality_check, default=None)
            
            extracted_text = []
            if best_node and self._vitality_check(best_node) > 5:
                node_text = best_node.get_text(separator=' ', strip=True)
                extracted_text.append(node_text)
                
                if depth < self.max_depth:
                    links = best_node.find_all('a', href=True)
                    discovered_count = 0
                    for link in links:
                        if discovered_count >= 5: break
                        next_url = link['href']
                        if next_url.startswith('/'): 
                            next_url = requests.compat.urljoin(url, next_url)
                        if next_url.startswith('http') and url.split('/')[2] in next_url:
                            res = self.fetch_semantic_nodes(next_url, depth + 1)
                            if res:
                                extracted_text.extend(res)
                                discovered_count += 1
            
            return extracted_text
        except Exception as e:
            print(f"[Protocol-Error] Node failure at {url}: {e}")
            return []

    def build_cartridge(self, url, cartridge_name):
        print(f"[Initiating Protocol v3.0] Target: {url}")
        semantic_nodes = self.fetch_semantic_nodes(url)
        
        if not semantic_nodes:
            print("[Warning] No vital semantic nodes discovered.")
            return None

        full_content = "\n\n".join(semantic_nodes)
        shards = OzrielSegmenter.segment(full_content, max_shard_size=self.shard_size)
        
        print(f"[Protocol-Complete] Extracted {len(shards)} shards.")
        
        builder = TAHBuilder(target_fp=self.target_fp, expected_elements=len(shards) * 30)
        for shard in shards:
            builder.add_text_shard(shard)
            
        output_path = f"cartridges/{cartridge_name}.tah"
        builder.save(output_path)
        return output_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python builder/web_builder.py <url> [cartridge_name]")
        sys.exit(1)
        
    url = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else "ozriel_resource"
    ingestor = WebIngestor(max_depth=1)
    ingestor.build_cartridge(url, name)
