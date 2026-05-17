import os
import sys
import time
import subprocess
from pathlib import Path

# Path Configuration
BASE_DIR = Path("C:/Users/Taz/SunsetWars")
BUILDER_DIR = BASE_DIR / "builder"
SEEDS_DIR = BASE_DIR / "knowledge_hub/seeds"
CARTRIDGE_DIR = BASE_DIR / "cartridges/universe"

sys.path.append(str(BUILDER_DIR))

def process_seeds():
    """Scans for new seeds and triggers the appropriate Memoria builder."""
    seeds = list(SEEDS_DIR.glob("*"))
    if not seeds:
        return

    print(f"[Orchestrator] Found {len(seeds)} new seeds. Initiating Ozriel Protocol...")
    
    for seed in seeds:
        if seed.suffix == ".txt" and seed.name.startswith("url_"):
            # Process as Web Seed
            with open(seed, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            for url in urls:
                vault_name = f"universe/web_{int(time.time())}"
                print(f"[Orchestrator] Ingesting URL: {url}")
                subprocess.run([sys.executable, str(BUILDER_DIR / "memoria_web_builder.py"), url, vault_name])
        
        elif seed.suffix == ".pdf":
            # Process as PDF Seed
            vault_name = f"universe/pdf_{seed.stem}"
            print(f"[Orchestrator] Ingesting PDF: {seed.name}")
            subprocess.run([sys.executable, str(BUILDER_DIR / "memoria_pdf_builder.py"), str(seed), vault_name])
            
        # Move seed to processed
        processed_path = BASE_DIR / "knowledge_hub/processed" / seed.name
        seed.rename(processed_path)

if __name__ == "__main__":
    print("[Orchestrator] Zero-Noise Ingestion Hub Active.")
    while True:
        try:
            process_seeds()
            time.sleep(10)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[Error] Orchestrator glitch: {e}")
            time.sleep(5)
