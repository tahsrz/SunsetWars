import os
import subprocess
import sys
import shutil
import json
import re

# Add builder to path
sys.path.append(os.path.dirname(__file__))
from memoria_builder import MemoriaBuilder, OzrielSegmenter

class GitHubSync:
    """
    Memoria GitHub Sync Workflow (v3.0)
    Automates fetching knowledge from GitHub and converting to Memoria Vaults.
    """
    def __init__(self, workspace_root=None):
        if workspace_root:
            self.root = workspace_root
        else:
            self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        self.sync_dir = os.path.join(self.root, "workbench", "sync")
        self.vault_dir = os.path.join(self.root, "cartridges")
        
        for d in [self.sync_dir, self.vault_dir]:
            if not os.path.exists(d):
                os.makedirs(d)

    def sync_repo(self, repo_url, name):
        """Clones or pulls the repository."""
        target_path = os.path.join(self.sync_dir, name)
        print(f"[Memoria-Sync] Syncing {name} from {repo_url}...")
        
        if os.path.exists(target_path):
            try:
                subprocess.run(["git", "pull"], cwd=target_path, check=True, capture_output=True)
                print(f"[Memoria-Sync] Updated {name}.")
            except subprocess.CalledProcessError as e:
                print(f"[Memoria-Sync] Pull failed for {name}: {e.stderr.decode()}")
                return False
        else:
            try:
                subprocess.run(["git", "clone", "--depth", "1", repo_url, target_path], check=True, capture_output=True)
                print(f"[Memoria-Sync] Cloned {name}.")
            except subprocess.CalledProcessError as e:
                print(f"[Memoria-Sync] Clone failed for {name}: {e.stderr.decode()}")
                return False
        return True

    def extract_shards(self, directory):
        """Recursively extracts vital shards from supported files using Ozriel Protocol."""
        all_shards = []
        # Support common documentation and code files
        extensions = {
            '.md', '.mdx', '.txt', '.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
            '.c', '.cpp', '.h', '.hpp', '.cs', '.html', '.css', '.scss', '.json',
            '.yml', '.yaml', '.toml', '.sql', '.sh', '.ps1', '.rs', '.go', '.java'
        }
        skip_names = {
            'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'bun.lockb',
            'node_modules', 'dist', 'build', '.next', '.git'
        }
        
        for root, _, files in os.walk(directory):
            if '.git' in root: continue
            
            for file in files:
                if file in skip_names:
                    continue
                ext = os.path.splitext(file)[1].lower()
                if ext in extensions:
                    file_path = os.path.join(root, file)
                    if os.path.getsize(file_path) > 512_000:
                        continue
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if not content.strip(): continue
                            
                            # Clean markdown frontmatter
                            content = re.sub(r'^---.*?---', '', content, flags=re.DOTALL)
                            rel_path = os.path.relpath(file_path, directory).replace(os.sep, "/")
                            file_text = f"--- FILE: {rel_path} ---\n\n{content}"
                            all_shards.extend((shard, rel_path) for shard in OzrielSegmenter.segment(file_text))
                    except Exception as e:
                        print(f"[Memoria-Sync] Warning: Failed to read {file}: {e}")
        
        return all_shards

    def build_cartridge(self, name, repo_url=None):
        """Processes the synced repo and generates a Memoria vault (.hat + .tah)."""
        source_dir = os.path.join(self.sync_dir, name)
        if not os.path.exists(source_dir):
            print(f"[Memoria-Sync] Error: Source directory {source_dir} not found.")
            return False
            
        shards = self.extract_shards(source_dir)
        if not shards:
            print(f"[Memoria-Sync] Warning: No vital shards found in {name}.")
            return False
            
        print(f"[Memoria-Sync] Compiling Vault for {name} with {len(shards)} shards...")
        
        builder = MemoriaBuilder(target_fp=0.0001, expected_elements=max(1000, len(shards) * 15))
        
        added_count = 0
        for shard in shards:
            if isinstance(shard, tuple):
                text, rel_path = shard
                source_url = f"{repo_url.replace('.git', '')}/blob/main/{rel_path}" if repo_url else f"local://{name}/{rel_path}"
                builder.add_text_shard(text, url=source_url)
            else:
                builder.add_text_shard(shard)
            added_count += 1
                
        output_base = os.path.join(self.vault_dir, name)
        builder.save(output_base)
        print(f"[Memoria-Sync] SUCCESS: Vault compiled for {name} ({added_count} shards)")
        return True

def main():
    if len(sys.argv) < 3:
        print("Memoria GitHub Sync Workflow (v3.0)")
        print("Usage: python builder/github_sync.py <repo_url> <vault_name>")
        sys.exit(1)
        
    repo_url = sys.argv[1]
    name = sys.argv[2]
    
    sync = GitHubSync()
    if sync.sync_repo(repo_url, name):
        sync.build_cartridge(name, repo_url)

if __name__ == "__main__":
    main()
