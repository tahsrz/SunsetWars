import requests
import json
import os
import time
from typing import List, Dict, Any
from memoria_builder import MemoriaBuilder, OzrielSegmenter

class DallasPoliceIngestor:
    """
    Surgical Ingestor for Dallas Police RMS Incidents (qv6i-rri7).
    Compiles recent high-signal safety incidents into a Memoria cartridge.
    """
    API_URL = "https://www.dallasopendata.com/resource/qv6i-rri7.json"
    
    def __init__(self, limit=2500):
        self.limit = limit
        self.builder = MemoriaBuilder(target_fp=0.0001, expected_elements=limit * 2)

    def fetch_data(self) -> List[Dict[str, Any]]:
        print(f"[Dallas-Ingest] Fetching {self.limit} most recent incidents from {self.API_URL}...")
        # Order by reporteddate descending to get latest activity
        params = {
            "$limit": self.limit,
            "$order": "reporteddate DESC"
        }
        try:
            response = requests.get(self.API_URL, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[Error] Failed to fetch Dallas data: {e}")
            return []

    def format_shard(self, incident: Dict[str, Any]) -> str:
        """Formats an incident record into a high-signal text shard."""
        incident_num = incident.get("incidentnum", "UNKNOWN")
        offense = incident.get("offincident", "UNKNOWN")
        address = incident.get("incident_address", "UNKNOWN")
        city = incident.get("city", "Dallas")
        zip_code = incident.get("zip_code", "")
        date = incident.get("date1", "UNKNOWN")
        time_str = incident.get("time1", "UNKNOWN")
        division = incident.get("division", "UNKNOWN")
        council = incident.get("council_district", "UNKNOWN")
        
        # Coordinates extraction
        coords = incident.get("geocoded_column", {})
        lat = coords.get("latitude", 0)
        lng = coords.get("longitude", 0)
        
        shard_lines = [
            f"Safety Incident: {offense}",
            f"Location: {address}, {city} TX {zip_code}".strip(),
            f"Time: {date} at {time_str}",
            f"Police Division: {division}",
            f"Council District: {council}",
            f"Coordinates: {lat}, {lng}",
            f"Source ID: {incident_num}"
        ]
        
        return "\n".join(shard_lines)

    def build_cartridge(self, output_base="cartridges/dallas_safety_intel"):
        data = self.fetch_data()
        if not data:
            print("[Error] No data to process.")
            return

        print(f"[Dallas-Ingest] Processing {len(data)} records...")
        for incident in data:
            shard_text = self.format_shard(incident)
            # Use the specific incident URL for traceability
            incident_num = incident.get("incidentnum")
            source_url = f"{self.API_URL}?incidentnum={incident_num}" if incident_num else self.API_URL
            
            self.builder.add_text_shard(
                shard_text,
                url=source_url,
                location="USA_TX_DALLAS",
                relevance=0.9
            )

        self.builder.save(output_base)
        print(f"[Dallas-Ingest] Cartridge saved: {output_base}")

if __name__ == "__main__":
    # Ensure cartridges directory exists relative to project root
    base_dir = os.path.dirname(os.path.dirname(__file__))
    cartridge_dir = os.path.join(base_dir, "cartridges")
    if not os.path.exists(cartridge_dir):
        os.makedirs(cartridge_dir)
        
    output_path = os.path.join(cartridge_dir, "dallas_safety_intel")
    ingestor = DallasPoliceIngestor(limit=3000)
    ingestor.build_cartridge(output_path)
