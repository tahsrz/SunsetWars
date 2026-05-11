import os
import re
from pypdf import PdfReader
from tah_builder import TAHBuilder

class ConceptChunker:
    """
    SICP-inspired Semantic Segmenter.
    Groups text into atomic 'Concept Blocks' based on structural markers.
    """
    def __init__(self, max_shard_chars=3000):
        self.max_shard_chars = max_shard_chars
        # Regex for common academic/technical headers
        self.header_patterns = [
            r'^\d+\.\d+\s+[A-Z].*',      # 4.1 Metacircular Evaluator
            r'^[A-Z][A-Z\s]{5,40}$',      # ALL CAPS HEADER
            r'^Chapter\s+\d+.*',         # Chapter 1
            r'^Section\s+.*'             # Section ...
        ]

    def is_header(self, line):
        line = line.strip()
        if not line: return False
        return any(re.match(pattern, line) for pattern in self.header_patterns)

    def decompose(self, text):
        """Recursively decomposes a large block into smaller sub-concepts."""
        if len(text) <= self.max_shard_chars:
            return [text]
        
        # Look for sub-structure (e.g., 4.1.1 or bullet points)
        sub_patterns = [r'\n\d+\.\d+\.\d+\s+', r'\n\s*[\*\-]\s+', r'\n\n']
        
        for pattern in sub_patterns:
            parts = re.split(pattern, text)
            if len(parts) > 1:
                decomposed = []
                for p in parts:
                    decomposed.extend(self.decompose(p.strip()))
                return [d for d in decomposed if len(d) > 50]
        
        # Fallback: Hard cut if no structure found (rare in technical docs)
        return [text[:self.max_shard_chars], text[self.max_shard_chars:]]

    def segment(self, pages):
        """Segments text into concept-anchored blocks with recursive decomposition."""
        full_text = "\n".join(pages)
        lines = full_text.split('\n')
        
        raw_shards = []
        current_shard = []
        current_length = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped: continue
            
            if self.is_header(stripped) and current_length > 300:
                raw_shards.append("\n".join(current_shard))
                current_shard = [stripped]
                current_length = len(stripped)
            else:
                current_shard.append(stripped)
                current_length += len(stripped)
        
        if current_shard:
            raw_shards.append("\n".join(current_shard))
            
        # Final pass: Recursively decompose oversized shards
        final_shards = []
        for rs in raw_shards:
            final_shards.extend(self.decompose(rs))
            
        return [s for s in final_shards if len(s) > 50]

class PDFIngestor:
    def __init__(self, target_fp=0.0001):
        self.target_fp = target_fp
        self.chunker = ConceptChunker()

    def extract_text(self, pdf_path):
        reader = PdfReader(pdf_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return pages

    def build_cartridge(self, pdf_path, cartridge_name):
        print(f"[ConceptBuilder] Ingesting: {pdf_path}")
        pages = self.extract_text(pdf_path)
        shards = self.chunker.segment(pages)
        
        print(f"[ConceptBuilder] Generated {len(shards)} atomic concept blocks.")
        
        # 1. Map Titles to Indices for Linking
        concept_map = {}
        for i, shard in enumerate(shards):
            # Treat the first non-empty line as the Concept Title
            title = shard.strip().split('\n')[0].lower().strip()
            # Remove common structural noise from title for better matching
            title = re.sub(r'^\d+[\.\d]*\s+', '', title)
            if len(title) > 3:
                concept_map[title] = i
        
        # 2. Initialize Builder
        expected_elements = len(shards) * 25
        builder = TAHBuilder(target_fp=self.target_fp, expected_elements=expected_elements)
        
        # 3. Add Shards with Cross-Reference Discovery
        print(f"[ConceptBuilder] Discovering cross-references...")
        for i, shard in enumerate(shards):
            links = []
            shard_lower = shard.lower()
            for title, target_idx in concept_map.items():
                if target_idx != i and title in shard_lower:
                    links.append(target_idx)
            
            # Limit to top 5 links for efficiency
            builder.add_shard(shard, links=links[:5])
            
        output_path = f"cartridges/{cartridge_name}.tah"
        builder.save(output_path)
        print(f"[ConceptBuilder] Cartridge saved: {output_path}")
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
