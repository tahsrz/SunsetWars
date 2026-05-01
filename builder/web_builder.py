import requests
from bs4 import BeautifulSoup
from tah_builder import TAHBuilder
import re
import os

class WebIngestor:
    """
    TAH Web Ingestor (v1.2) - Ozriel Protocol Integrated
    Implements recursive semantic discovery and vitality-based extraction.
    """
    def __init__(self, target_fp=0.0001, shard_size=1200, max_depth=2):
        self.target_fp = target_fp
        self.shard_size = shard_size
        self.max_depth = max_depth
        self.visited_urls = set()
        self.headers = {
            'User-Agent': 'TAH-Ozriel/1.2 (Terminal AI Hub; Protocol-V)'
        }

    def _vitality_check(self, element):
        """
        Ozriel Vitality Check: Evaluates the 'life' of a semantic container.
        Prioritizes density of technical terms vs. boilerplate.
        """
        text = element.get_text(strip=True)
        if len(text) < 100: return 0
        
        # Count high-value markers (Capitalized terms, technical punctuation)
        vitality_score = len(re.findall(r'[A-Z][a-z]{3,}', text)) 
        vitality_score += text.count('(') + text.count('{')
        
        # Penalize navigational density (Ozriel Rule: Expertise is dense, Navigation is sparse)
        link_density = len(element.find_all('a')) / (len(text.split()) + 1)
        return vitality_score * (1 - link_density)

    def fetch_semantic_nodes(self, url, depth=0):
        """
        Recursive Semantic Discovery under Ozriel Gating.
        Follows high-vitality links within the same domain.
        """
        if depth > self.max_depth or url in self.visited_urls:
            return []
        
        self.visited_urls.add(url)
        print(f"[Ozriel-Pulse] Depth {depth}: Scanning {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Clean non-vital noise
            for noise in soup(['nav', 'footer', 'header', 'script', 'style', 'aside']):
                noise.decompose()

            # 1. Ontological Anchoring: Identify the core "vital" nodes
            # We look for containers that pass the vitality threshold
            potential_nodes = soup.find_all(['div', 'section', 'article', 'main'])
            
            # Find the single most vital node on the page
            best_node = max(potential_nodes, key=self._vitality_check, default=None)
            
            extracted_text = []
            if best_node and self._vitality_check(best_node) > 5:
                node_text = best_node.get_text(separator=' ', strip=True)
                extracted_text.append(node_text)
                
                # 2. Recursive Discovery: Follow links within high-vitality nodes
                if depth < self.max_depth:
                    links = best_node.find_all('a', href=True)
                    # Gate breadth to preserve protocol integrity
                    discovered_count = 0
                    for link in links:
                        if discovered_count >= 5: break
                        
                        next_url = link['href']
                        if next_url.startswith('/'): 
                            next_url = requests.compat.urljoin(url, next_url)
                        
                        # Only follow links within the same sub-domain
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
        """Orchestrates the Ozriel-compliant conversion."""
        print(f"[Initiating Protocol] Target: {url}")
        semantic_nodes = self.fetch_semantic_nodes(url)
        
        if not semantic_nodes:
            print("[Warning] No vital semantic nodes discovered. Protocol aborted.")
            return None

        # Flatten and chunk under Ozriel integrity rules
        full_content = "\n\n--- Node Boundary ---\n\n".join(semantic_nodes)
        shards = self._chunk_text(full_content)
        
        print(f"[Protocol-Complete] Extracted {len(shards)} shards from {len(self.visited_urls)} nodes.")
        
        # Increased keyword multiplier for recursive density
        expected_elements = len(shards) * 30 
        
        builder = TAHBuilder(target_fp=self.target_fp, expected_elements=expected_elements)
        
        for shard in shards:
            builder.add_shard(shard)
            
        output_path = f"cartridges/{cartridge_name}.tah"
        builder.save(output_path)
        return output_path

    def _chunk_text(self, text):
        """Segments text into shards optimized for LLM context windows."""
        text = re.sub(r'\s+', ' ', text).strip()
        shards = []
        start = 0
        while start < len(text):
            end = start + self.shard_size
            if end < len(text):
                boundary = text.rfind('.', start, end + 200)
                if boundary != -1 and boundary > start:
                    end = boundary + 1
            shards.append(text[start:end].strip())
            start = end
        return shards

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("TAH Web Ingestor v1.2 [Ozriel Protocol]")
        print("Usage: python builder/web_builder.py <url> [cartridge_name]")
        sys.exit(1)
        
    url = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else "ozriel_resource"
    
    ingestor = WebIngestor(max_depth=2)
    ingestor.build_cartridge(url, name)
