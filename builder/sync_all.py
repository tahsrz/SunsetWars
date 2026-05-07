import os
import sys
import json
import time
import subprocess

# Add builder to path
sys.path.append(os.path.dirname(__file__))
from github_sync import GitHubSync

def sync_all():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(root, "config", "github_sources.json")
    
    if not os.path.exists(config_path):
        print(f"[Error] Config not found: {config_path}")
        return

    with open(config_path, 'r') as f:
        config = json.load(f)

    syncer = GitHubSync(workspace_root=root)
    repos = config.get("repos", [])
    
    print(f"[Sync-All] Processing {len(repos)} repositories...")
    for repo in repos:
        url = repo.get("url")
        name = repo.get("name")
        if url and name:
            if syncer.sync_repo(url, name):
                syncer.build_cartridge(name)
        else:
            print(f"[Sync-All] Warning: Skipping invalid repo entry: {repo}")

if __name__ == "__main__":
    if "--loop" in sys.argv:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(root, "config", "github_sources.json")
        interval = 60
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                interval = config.get("sync_interval_minutes", 60)
        
        print(f"[Sync-All] Starting auto-sync loop (Interval: {interval} minutes)...")
        while True:
            sync_all()
            print(f"[Sync-All] Sleeping for {interval} minutes...")
            time.sleep(interval * 60)
    else:
        sync_all()
