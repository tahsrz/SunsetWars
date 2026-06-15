import os
import time
import subprocess
from pathlib import Path

def watch_and_sync():
    project_root = Path("C:/Users/Taz")
    universe_dir = project_root / "cartridges/universe"
    sync_script = project_root / "SunsetPulse/scripts/vercel-sync.mjs"
    
    print(f"🔭 [Sync-Watcher] Monitoring {universe_dir} for new shards...")
    
    # Get initial state
    last_count = len(list(universe_dir.glob("*.tah")))
    
    while True:
        try:
            current_shards = list(universe_dir.glob("*.tah"))
            current_count = len(current_shards)
            
            if current_count > last_count:
                new_count = current_count - last_count
                print(f"🚀 [Sync-Watcher] Detected {new_count} new shards. Triggering Cloud Sync...")
                
                # Run the sync script
                result = subprocess.run(["node", str(sync_script)], capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ [Sync-Watcher] Cloud Sync Success.")
                else:
                    print(f"❌ [Sync-Watcher] Sync Failed: {result.stderr}")
                
                last_count = current_count
                
            time.sleep(60) # Check every minute
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error in watcher: {e}")
            time.sleep(10)

if __name__ == "__main__":
    watch_and_sync()
