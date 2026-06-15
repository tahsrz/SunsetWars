import sys
import os
import csv
import json

# Add SunsetWars/builder to path for MemoriaBuilder
sys.path.append(os.path.join(os.getcwd(), 'SunsetWars', 'builder'))

from memoria_builder import MemoriaBuilder

def build_tah_from_db(db_path, output_name, limit=10000):
    print(f"Starting TAH build from {db_path} (limit={limit})...")
    builder = MemoriaBuilder(expected_elements=limit)
    
    usage_path = os.path.join(db_path, 'NameUsage.tsv')
    vernacular_path = os.path.join(db_path, 'VernacularName.tsv')
    
    # 1. Map taxonID to common names
    vernaculars = {}
    print("Indexing vernacular names...")
    with open(vernacular_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            tid = row.get('col:taxonID')
            name = row.get('col:name')
            if tid and name:
                if tid not in vernaculars: vernaculars[tid] = []
                vernaculars[tid].append(name)
    
    # 2. Process NameUsage
    id_to_index = {}
    entries = [] # To store temp data for linking
    
    print("Processing taxa...")
    with open(usage_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        count = 0
        for row in reader:
            if row.get('col:status') != 'accepted': continue
            
            tid = row.get('col:ID')
            name = row.get('col:scientificName')
            rank = row.get('col:rank')
            
            # Construct text shard
            hierarchy = [
                row.get('col:kingdom'), row.get('col:phylum'), row.get('col:class'),
                row.get('col:order'), row.get('col:family'), row.get('col:genus')
            ]
            hierarchy = [h for h in hierarchy if h]
            h_str = " > ".join(hierarchy)
            
            v_names = vernaculars.get(tid, [])
            v_str = ", ".join(v_names) if v_names else "None"
            
            text = f"Taxon: {name}\nRank: {rank}\nPath: {h_str}\nVernacular: {v_str}"
            if row.get('col:link'):
                text += f"\nLink: {row.get('col:link')}"
            
            # Placeholder for links (will fill in second pass)
            id_to_index[tid] = count
            entries.append({
                'id': tid,
                'parent': row.get('col:parentID'),
                'text': text,
                'url': row.get('col:link') or "local://catalogue"
            })
            
            count += 1
            if count >= limit: break

    # 3. Second pass: Build Links and Add Shards
    print("Finalizing shards with WebGraph links...")
    for i, entry in enumerate(entries):
        links = []
        parent_id = entry['parent']
        if parent_id in id_to_index:
            links.append(id_to_index[parent_id])
            
        # Add shard to builder
        builder.add_text_shard(
            text=entry['text'],
            url=entry['url'],
            location="GLOBAL",
            relevance=1.0,
            links=links
        )

    builder.save(f"cartridges/{output_name}")
    print(f"Success! Cartridge {output_name} compiled.")

if __name__ == "__main__":
    db_dir = r'C:\Users\Taz\Videos\extracted_db'
    build_tah_from_db(db_dir, "catalogue_of_life_v3_6", limit=5000)
