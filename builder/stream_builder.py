import sys
import os
from pathlib import Path

# Add builder to path
sys.path.append(str(Path(__file__).parent / "builder"))
from tah_builder import TAHBuilder

class TAHStreamBuilder:
    """
    TAH v3.1 - Stream-Based Ingestor
    Implements SICP Stream principles to handle massive datasets with constant memory overhead.
    """
    def __init__(self, target_path, expected_elements=10000):
        self.target_path = target_path
        self.builder = TAHBuilder(target_fp=0.0001, expected_elements=expected_elements)

    def ingest_from_generator(self, generator):
        """
        Processes a stream of data shards. 
        In SICP, a stream is a delayed list; here we use a Python generator.
        """
        print(f"[Stream] Starting ingestion pipeline for {self.target_path}...")
        count = 0
        for item in generator:
            # item: (data, type_tag, kwargs)
            data, tag, kwargs = item
            self.builder.add_shard(data, type_tag=tag, **kwargs)
            count += 1
            if count % 100 == 0:
                print(f"[Stream] Processed {count} shards...")
        
        self.builder.save(self.target_path)
        print(f"[Stream] Pipeline complete. {count} shards indexed.")

def mock_real_estate_stream():
    """Simulates a massive stream of real estate data points."""
    # 1. Text Shards (Descriptions)
    yield ("Modern penthouse with panoramic views of the skyline.", 0, {})
    yield ("Historic craftsman home with original hardwood floors.", 0, {})
    
    # 2. Coordinate Shards (Listings)
    yield ((32.7767, -96.7970), 1, {"label": "Downtown Dallas Penthouse"})
    yield ((30.2672, -97.7431), 1, {"label": "Austin Tech Loft"})
    
    # 3. Image Shards (Property Photos)
    yield ("assets/luxury_kitchen.jpg", 2, {"tags": ["kitchen", "marble", "modern"]})
    yield ("assets/backyard_pool.jpg", 2, {"tags": ["pool", "outdoor", "luxury"]})

if __name__ == "__main__":
    stream_builder = TAHStreamBuilder("cartridges/sunset_pulse_expertise.tah")
    stream_builder.ingest_from_generator(mock_real_estate_stream())
