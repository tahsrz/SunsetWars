import sys
import os
from pathlib import Path

# Add builder to path
sys.path.append(os.path.dirname(__file__))
from memoria_builder import MemoriaBuilder

class MemoriaStreamBuilder:
    """
    Memoria v3.1 - Stream-Based Ingestor
    Implements SICP Stream principles to handle massive datasets with constant memory overhead.
    """
    def __init__(self, target_base, expected_elements=10000):
        self.target_base = target_base
        self.builder = MemoriaBuilder(target_fp=0.0001, expected_elements=expected_elements)

    def ingest_from_generator(self, generator):
        """
        Processes a stream of data shards. 
        In SICP, a stream is a delayed list; here we use a Python generator.
        """
        print(f"[Memoria-Stream] Starting ingestion pipeline for {self.target_base}...")
        count = 0
        for item in generator:
            # item: (data, type_tag, kwargs)
            data, tag, kwargs = item
            if tag == 0: # TEXT
                self.builder.add_text_shard(data, **kwargs)
            elif tag == 1: # COORD
                lat, lon = data
                label = kwargs.get('label', '')
                self.builder.add_coord_shard(lat, lon, label)
            # Add more tags as needed
            count += 1
            if count % 100 == 0:
                print(f"[Memoria-Stream] Processed {count} shards...")
        
        self.builder.save(self.target_base)
        print(f"[Memoria-Stream] Pipeline complete. {count} shards indexed.")

def mock_real_estate_stream():
    """Simulates a massive stream of real estate data points."""
    # 1. Text Shards (Descriptions)
    yield ("Modern penthouse with panoramic views of the skyline.", 0, {})
    yield ("Historic craftsman home with original hardwood floors.", 0, {})
    
    # 2. Coordinate Shards (Listings)
    yield ((32.7767, -96.7970), 1, {"label": "Downtown Dallas Penthouse"})
    yield ((30.2672, -97.7431), 1, {"label": "Austin Tech Loft"})

if __name__ == "__main__":
    stream_builder = MemoriaStreamBuilder("cartridges/sunset_pulse_expertise")
    stream_builder.ingest_from_generator(mock_real_estate_stream())
