import requests
import json
import os
import time
from typing import List, Dict, Any
from memoria_builder import MemoriaBuilder, OzrielSegmenter

class Dallas311Ingestor:
    """
    Surgical Ingestor for Dallas 311 Service Requests (d7e7-envw).
    Compiles high-signal community vitality requests into a Memoria cartridge.
    """
    API_URL = "https://www.dallasopendata.com/resource/d7e7-envw.json"
    
    # High-signal categories for real estate and neighborhood quality
    TARGET_TYPES = [
        "Code Concern",
        "High Weeds",
        "Junk Motor Vehicle",
        "Illegal Dump",
        "Street Repair",
        "Pot Hole",
        "Sidewalk Repair",
        "Litter",
        "Animal Lack of Care",
        "Parking Violation"
    ]

    def __init__(self, limit=2500):
        self.limit = limit
        self.builder = MemoriaBuilder(target_fp=0.0001, expected_elements=limit * 2)

    def fetch_data(self) -> List[Dict[str, Any]]:
        print(f"[Dallas-311] Fetching {self.limit} high-signal requests from {self.API_URL}...")
        
        # Build SoQL query to filter by type and order by date
        # Note: 'service_request_type' is the field name for type
        type_filter = " OR ".join([f"service_request_type LIKE '%{t}%'" for t in self.TARGET_TYPES])
        params = {
            "$limit": self.limit,
            "$where": type_filter,
            "$order": "created_date DESC"
        }
        
        try:
            response = requests.get(self.API_URL, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[Error] Failed to fetch Dallas 311 data: {e}")
            return []

    def format_shard(self, req: Dict[str, Any]) -> str:
        """Formats a 311 request into a high-signal text shard."""
        sr_type = req.get("service_request_type", "UNKNOWN")
        status = req.get("status", "UNKNOWN")
        outcome = req.get("outcome", "PENDING")
        address = req.get("address", "UNKNOWN")
        city = req.get("city", "Dallas")
        zip_code = req.get("zip_code", "")
        created_date = req.get("created_date", "UNKNOWN")
        sr_number = req.get("service_request_number", "UNKNOWN")
        
        # Coordinates extraction
        lat = req.get("latitude", 0)
        lng = req.get("longitude", 0)
        
        shard_lines = [
            f"Community Vitality: {sr_type}",
            f"Status: {status} | Outcome: {outcome}",
            f"Location: {address}, {city} TX {zip_code}".strip(),
            f"Reported: {created_date}",
            f"Coordinates: {lat}, {lng}",
            f"Service Request: {sr_number}"
        ]
        
        return "\n".join(shard_lines)

    def build_cartridge(self, output_base="cartridges/dallas_community_intel"):
        data = self.fetch_data()
        if not data:
            print("[Error] No 311 data to process.")
            return

        print(f"[Dallas-311] Processing {len(data)} records...")
        for req in data:
            shard_text = self.format_shard(req)
            sr_number = req.get("service_request_number")
            source_url = f"{self.API_URL}?service_request_number={sr_number}" if sr_number else self.API_URL
            
            self.builder.add_text_shard(
                shard_text,
                url=source_url,
                location="USA_TX_DALLAS",
                relevance=0.85
            )

        self.builder.save(output_base)
        print(f"[Dallas-311] Cartridge saved: {output_base}")

if __name__ == "__main__":
    # Ensure cartridges directory exists relative to project root
    base_dir = os.path.dirname(os.path.dirname(__file__))
    cartridge_dir = os.path.join(base_dir, "cartridges")
    if not os.path.exists(cartridge_dir):
        os.makedirs(cartridge_dir)
        
    output_path = os.path.join(cartridge_dir, "dallas_community_intel")
    ingestor = Dallas311Ingestor(limit=3000)
    ingestor.build_cartridge(output_path)
