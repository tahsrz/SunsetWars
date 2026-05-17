import os
import re
from pypdf import PdfReader
from memoria_builder import MemoriaBuilder, OzrielSegmenter

class PDFIngestor:
    """Memoria PDF Ingestor v3.1 (Ozriel Protocol)"""
    def __init__(self, target_fp=0.0001, shard_size=1200):
        self.target_fp = target_fp
        self.shard_size = shard_size

    def extract_text(self, pdf_path):
        reader = PdfReader(pdf_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return pages

    def build_vault(self, pdf_path, vault_name):
        print(f"[Memoria-Ingest v3.1] {pdf_path}")
        pages = self.extract_text(pdf_path)
        full_text = "\n".join(pages)
        
        # Use Ozriel semantic segmentation
        shards = OzrielSegmenter.segment(full_text, max_shard_size=self.shard_size)
        
        print(f"[Protocol-Complete] Extracted {len(shards)} shards.")
        
        # Estimate keyword count
        expected_elements = len(shards) * 20
        builder = MemoriaBuilder(target_fp=self.target_fp, expected_elements=expected_elements)
        
        for shard in shards:
            builder.add_text_shard(shard)
            
        output_base = f"cartridges/{vault_name}"
        builder.save(output_base)
        return output_base

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python builder/memoria_pdf_builder.py <path_to_pdf> [vault_name]")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    vault_name = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(os.path.basename(pdf_path))[0]
    
    ingestor = PDFIngestor()
    ingestor.build_vault(pdf_path, vault_name)
