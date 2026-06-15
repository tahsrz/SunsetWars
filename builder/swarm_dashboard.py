import os
import json
import time
from pathlib import Path

def get_progress():
    project_root = Path("C:/Users/Taz")
    progress_file = project_root / "alphabetical_progress.json"
    universe_dir = project_root / "cartridges/universe"
    
    if not progress_file.exists():
        print("No progress file found.")
        return

    with open(progress_file, 'r') as f:
        state = json.load(f)

    last_page = state.get("last_page", "N/A")
    current_letter = state.get("current_letter", "A").upper()
    
    # Calculate A-Z progress
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    letter_idx = alphabet.find(current_letter)
    if letter_idx == -1: letter_idx = 0
    
    progress_pct = (letter_idx / 26.0) * 100
    
    # Count shards
    shards = list(universe_dir.glob("*.tah"))
    hats = list(universe_dir.glob("*.hat"))
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*60)
    print(f" 🌌 MEMORIA UNIVERSAL SWARM DASHBOARD ")
    print("="*60)
    print(f" Status:        ACTIVE CRAWL")
    print(f" Current Letter: {current_letter}")
    print(f" Last Indexed:   {last_page}")
    print(f" Total Shards:   {len(shards)} (.tah) | {len(hats)} (.hat)")
    
    # Progress Bar
    bar_width = 40
    filled = int(bar_width * (letter_idx / 25.0))
    bar = "█" * filled + "░" * (bar_width - filled)
    
    print(f"\n Global A-Z Progress:")
    print(f" [{bar}] {progress_pct:.1f}%")
    print(f" " + " ".join(list(alphabet)))
    
    print("\n" + "="*60)
    print(f" Next Sync Target: Supabase Bucket 'cartridges'")
    print(f" Watcher Status:   IDLE")
    print("="*60)

if __name__ == "__main__":
    try:
        while True:
            get_progress()
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nDashboard detached.")
