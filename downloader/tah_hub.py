import os
import struct
import urllib.request
from pathlib import Path

class TAHHub:
    def __init__(self, target_dir="cartridges"):
        self.target_dir = Path(target_dir)
        self.target_dir.mkdir(exist_ok=True)

    def fetch(self, url, filename=None):
        """Downloads a .tah file from a URL and validates its integrity."""
        if not filename:
            filename = url.split("/")[-1]
            if not filename.endswith(".tah"):
                filename += ".tah"
        
        target_path = self.target_dir / filename
        print(f"Fetching TAH Cartridge: {url} ...")
        
        try:
            with urllib.request.urlopen(url) as response:
                # Read the first 4 bytes to validate unique id
                header_chunk = response.read(4)
                if len(header_chunk) < 4:
                    print("Error: Remote file is too small.")
                    return False
                
                magic = struct.unpack('<I', header_chunk)[0]
                if magic != 0x54414821:
                    print(f"Error: Invalid TAH magic number (Found: {hex(magic)}). Not a valid cartridge.")
                    return False
                
                # If valid, download the rest
                with open(target_path, 'wb') as f:
                    f.write(header_chunk) # Write the id back
                    f.write(response.read())
                    
            print(f"Successfully downloaded: {target_path}")
            return True
            
        except Exception as e:
            print(f"Failed to fetch cartridge: {e}")
            return False

if __name__ == "__main__":
    import sys
    hub = TAHHub()
    
    if len(sys.argv) < 2:
        print("Usage: python downloader/tah_hub.py <cartridge_url> [filename]")
        print("\nExample:")
        print("python downloader/tah_hub.py https://example.com/medical_v2.tah")
    else:
        url = sys.argv[1]
        filename = sys.argv[2] if len(sys.argv) > 2 else None
        hub.fetch(url, filename)
