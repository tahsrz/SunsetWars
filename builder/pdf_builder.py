import os
import re
from pypdf import PdfReader
from tah_builder import TAHBuilder

class PDFIngestor:
    def __init__(self, target_fp=0.0001, shard_size=1000):
        self.target_fp = target_fp
        self.shard_size = shard_size

    def extract_text(self, pdf_path):
        """Extracts text from PDF and returns a list of page contents."""
        reader = PdfReader(pdf_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return pages

    def chunk_text(self, text_list):
        """Chunks long text into shards of roughly shard_size characters."""
        full_text = "\n".join(text_list)
        # Simple chunking by character count, trying to break at sentences
        shards = []
        start = 0
        while start < len(full_text):
            end = start + self.shard_size
            if end < len(full_text):
                # Look for a period to end the shard cleanly
                last_period = full_text.rfind('.', start, end + 100)
                if last_period != -1 and last_period > start:
                    end = last_period + 1
            
            shards.append(full_text[start:end].strip())
            start = end
        return shards

    def build_cartridge(self, pdf_path, cartridge_name):
        print(f"Ingesting: {pdf_path}")
        pages = self.extract_text(pdf_path)
        shards = self.chunk_text(pages)
        
        # Estimate keyword count (Roughly 10 unique keywords per shard)
        expected_elements = len(shards) * 15
        
        builder = TAHBuilder(target_fp=self.target_fp, expected_elements=expected_elements)
        
        for shard in shards:
            # Auto-indexing will handle the keyword extraction
            builder.add_shard(shard)
            
        output_path = f"cartridges/{cartridge_name}.tah"
        builder.save(output_path)
        return output_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pdf_builder.py <path_to_pdf> [cartridge_name]")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    cartridge_name = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(os.path.basename(pdf_path))[0]
    
    ingestor = PDFIngestor()
    ingestor.build_cartridge(pdf_path, cartridge_name)
