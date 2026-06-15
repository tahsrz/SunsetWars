import os
import sys
import json
import time
import subprocess
import win32api

# Add builder to path
sys.path.append(os.path.dirname(__file__))
from github_sync import GitHubSync

def get_idle_time_seconds():
    """Returns the time in seconds since the last user input (mouse/keyboard)."""
    return (win32api.GetTickCount() - win32api.GetLastInputInfo()) / 1000.0

def sync_all(force=False):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(root, "config", "github_sources.json")
    
    if not os.path.exists(config_path):
        print(f"[Error] Config not found: {config_path}")
        return False

    with open(config_path, 'r') as f:
        config = json.load(f)

    syncer = GitHubSync(workspace_root=root)
    repos = config.get("repos", [])
    
    any_updated = False
    print(f"[Sync-All] Processing {len(repos)} repositories...")
    for repo in repos:
        url = repo.get("url")
        name = repo.get("name")
        if url and name:
            # Only re-forge if there were actual changes pulled or if forced
            if syncer.sync_repo(url, name) or force:
                syncer.build_cartridge(name)
                any_updated = True
        else:
            print(f"[Sync-All] Warning: Skipping invalid repo entry: {repo}")
    return any_updated

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(root, "config", "github_sources.json")
    
    # Default configuration
    interval = 60
    idle_threshold = 15 # Minutes
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            interval = config.get("sync_interval_minutes", 60)
            idle_threshold = config.get("idle_threshold_minutes", 15)

    if "--loop" in sys.argv:
        print(f"[Cold-Path] Initializing Inactivity-Based Sync...")
        print(f"[Cold-Path] Loop Interval: {interval}m | Idle Threshold: {idle_threshold}m")
        
        while True:
            idle_sec = get_idle_time_seconds()
            idle_min = idle_sec / 60.0
            
            if idle_min >= idle_threshold:
                print(f"🌙 [Cold-Path] System IDLE ({idle_min:.1f}m). Triggering synchronization...")
                if sync_all():
                    print(f"✅ [Cold-Path] Synchronization complete.")
                else:
                    print(f"💤 [Cold-Path] No changes detected in repositories.")
                
                print(f"[Cold-Path] Sleeping for {interval} minutes...")
                time.sleep(interval * 60)
            else:
                remaining = idle_threshold - idle_min
                # print(f"🔭 [Cold-Path] User active. Waiting for silence ({remaining:.1f}m remaining)...")
                time.sleep(60) # Check every minute
    else:
        # One-shot execution
        sync_all(force="--force" in sys.argv)
