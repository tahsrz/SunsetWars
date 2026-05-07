import os
import sys
from concurrent.futures import ThreadPoolExecutor

# Add builder to path for TAHQuery
sys.path.append(os.path.dirname(__file__))
from tah_query import TAHQuery

def pulse_search(query_terms):
    cartridge_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cartridges")
    if not os.path.exists(cartridge_dir):
        print("Error: Cartridges directory not found.")
        return

    cartridges = [f for f in os.listdir(cartridge_dir) if f.endswith('.tah')]
    
    results = []
    
    def search_cartridge(filename):
        path = os.path.join(cartridge_dir, filename)
        try:
            q = TAHQuery(path)
            # We use a lower threshold for agentic retrieval to ensure we don't miss nuanced info
            matches = q.get_matches(query_terms)
            q.close()
            return [(filename, m) for m in matches]
        except:
            return []

    # Parallel search across all cartridges
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(search_cartridge, c) for c in cartridges]
        for future in futures:
            results.extend(future.result())

    if not results:
        print("No matches found in tactical library.")
        return

    # Print top results formatted for Agent ingestion
    print(f"--- PULSE SEARCH RESULTS for '{query_terms}' ---")
    for source, text in results[:5]: # Top 5 across all sources
        print(f"\n[SOURCE: {source}]")
        print(text)
        print("-" * 20)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pulse_query.py \"<query>\"")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    pulse_search(query)
