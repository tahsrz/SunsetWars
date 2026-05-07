import os
import subprocess
import sys
import shutil
import json
import re

# Add builder to path
sys.path.append(os.path.dirname(__file__))
from tah_builder import TAHBuilder

class GitHubSync:
    """
    GitHub Sync Workflow (v1.0)
    Automates fetching knowledge from GitHub and converting to TAH cartridges.
    """
    def __init__(self, workspace_root=None):
        if workspace_root:
            self.root = workspace_root
        else:
            self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        self.sync_dir = os.path.join(self.root, "workbench", "sync")
        self.cartridge_dir = os.path.join(self.root, "cartridges")
        
        for d in [self.sync_dir, self.cartridge_dir]:
            if not os.path.exists(d):
                os.makedirs(d)

    def sync_repo(self, repo_url, name):
        """Clones or pulls the repository."""
        target_path = os.path.join(self.sync_dir, name)
        print(f"[GitHub-Sync] Syncing {name} from {repo_url}...")
        
        if os.path.exists(target_path):
            try:
                subprocess.run(["git", "pull"], cwd=target_path, check=True, capture_output=True)
                print(f"[GitHub-Sync] Updated {name}.")
            except subprocess.CalledProcessError as e:
                print(f"[GitHub-Sync] Pull failed for {name}: {e.stderr.decode()}")
                return False
        else:
            try:
                subprocess.run(["git", "clone", "--depth", "1", repo_url, target_path], check=True, capture_output=True)
                print(f"[GitHub-Sync] Cloned {name}.")
            except subprocess.CalledProcessError as e:
                print(f"[GitHub-Sync] Clone failed for {name}: {e.stderr.decode()}")
                return False
        return True

    def extract_shards(self, directory):
        """Recursively extracts vital shards from supported files."""
        shards = []
        # Support common documentation and code files
        extensions = {'.md', '.txt', '.py', '.js', '.ts', '.c', '.cpp', '.h', '.cs'}
        
        for root, _, files in os.walk(directory):
            if '.git' in root: continue
            
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in extensions:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if not content.strip(): continue
                            
                            # Clean markdown frontmatter or simple headers
                            content = re.sub(r'^---.*?---', '', content, flags=re.DOTALL)
                            
                            # Split into semantic blocks (paragraphs or functions)
                            # For simplicity, we split by double newlines
                            blocks = [b.strip() for b in content.split('\n\n') if len(b.strip()) > 50]
                            shards.extend(blocks)
                    except Exception as e:
                        print(f"[GitHub-Sync] Warning: Failed to read {file}: {e}")
        return shards

    def build_cartridge(self, name):
        """Processes the synced repo and generates a TAH cartridge."""
        source_dir = os.path.join(self.sync_dir, name)
        if not os.path.exists(source_dir):
            print(f"[GitHub-Sync] Error: Source directory {source_dir} not found.")
            return False
            
        shards = self.extract_shards(source_dir)
        if not shards:
            print(f"[GitHub-Sync] Warning: No vital shards found in {name}.")
            return False
            
        print(f"[GitHub-Sync] Building cartridge for {name} with {len(shards)} shards...")
        
        builder = TAHBuilder(target_fp=0.0001, expected_elements=max(500, len(shards) * 10))
        
        added_count = 0
        for shard in shards:
            if builder.add_shard(shard, type_tag=TAHBuilder.TYPE_TEXT):
                added_count += 1
                
        output_path = os.path.join(self.cartridge_dir, f"{name}.tah")
        builder.save(output_path)
        print(f"[GitHub-Sync] SUCCESS: {output_path} ({added_count} vital shards ingested)")
        return True

def main():
    if len(sys.argv) < 3:
        print("GitHub Sync Workflow (v1.0)")
        print("Usage: python builder/github_sync.py <repo_url> <cartridge_name>")
        sys.exit(1)
        
    repo_url = sys.argv[1]
    name = sys.argv[2]
    
    sync = GitHubSync()
    if sync.sync_repo(repo_url, name):
        sync.build_cartridge(name)

if __name__ == "__main__":
    main()
