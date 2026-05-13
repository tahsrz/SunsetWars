import os
import re
from memoria_builder import MemoriaBuilder, OzrielSegmenter
from cityhash import city_hash64, normalize

class MemoriaWikiIngestor:
    """
    Memoria Wiki Ingestor v3.1 (Memoria Protocol)
    Encodes knowledge as 'Addressable Truths' within the Memoria Vault.
    """
    def __init__(self, target_fp=0.0001):
        self.target_fp = target_fp
        self.entries = {} # name -> text

    def add_entry(self, name: str, content: str):
        """Adds a named wiki entry."""
        self.entries[name.strip()] = content.strip()

    def build_vault(self, vault_name: str):
        print(f"[Memoria-Protocol] Compiling {len(self.entries)} addressable truths into Vault...")
        
        # Pre-calculate entry hashes for recursive pointing
        entry_map = {name: (city_hash64(normalize(name)) & 0xFFFFFFFF) for name in self.entries.keys()}
        
        expected_elements = sum(len(c.split()) for c in self.entries.values()) + len(self.entries) * 10
        builder = MemoriaBuilder(target_fp=self.target_fp, expected_elements=expected_elements)
        
        # 1. Generate Vault Index (Shard 0)
        toc = "MEMORIA VAULT INDEX\n" + "\n".join([f"- {name}" for name in self.entries.keys()])
        builder.add_text_shard(toc, meta=0x70C) 
        
        # 2. Add Entries as specialized shards
        for name, content in self.entries.items():
            formatted_content = f"[MEMORIA: {name}]\n\n{content}"
            shards = OzrielSegmenter.segment(formatted_content)
            
            # Find recursive links in content
            links = []
            for entry_name, entry_hash in entry_map.items():
                if entry_name.lower() in content.lower() and entry_name != name:
                    links.append(entry_hash)

            for i, shard in enumerate(shards):
                entry_hash = entry_map[name]
                # Shards of the same entry also link back to the entry head
                builder.add_text_shard(shard, meta=entry_hash, links=links)
        
        output_path = f"cartridges/{vault_name}.tah"
        builder.save(output_path)
        return output_path

if __name__ == "__main__":
    ingestor = MemoriaWikiIngestor()
    ingestor.add_entry("Abidan Court", "The Abidan are a group of god-like beings who maintain the order of the multiverse.")
    ingestor.add_entry("Makiel", "The Hound. The First Judge of the Abidan Court. Overseer of Fate and the Great Seven.")
    ingestor.add_entry("Suriel", "The Phoenix. The Sixth Judge. Responsible for healing and restoration across the iterations.")
    ingestor.add_entry("Eithan Arelius", "A mysterious figure with deep connections to the Abidan and the origin of the Ozriel Protocol.")
    ingestor.add_entry("The Way", "The source of order and existence that connects all stable iterations in the multiverse.")
    
    ingestor.build_vault("abidan_vault")
