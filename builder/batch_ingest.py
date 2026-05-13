import os
import subprocess
import sys

def batch_ingest():
    # Setup paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    builder_script = os.path.join(base_dir, "pdf_builder.py")
    
    # List of PDFs to process
    pdfs = [f for f in os.listdir(project_root) if f.endswith('.pdf')]
    
    print(f"[Batch] Found {len(pdfs)} PDFs to process.")
    
    for pdf in pdfs:
        pdf_path = os.path.join(project_root, pdf)
        # Use filename without extension as cartridge name
        cartridge_name = os.path.splitext(pdf)[0]
        
        print(f"\n[Batch] Starting ingestion: {pdf} -> {cartridge_name}.tah")
        
        try:
            # Run the builder script
            result = subprocess.run(
                [sys.executable, builder_script, pdf_path, cartridge_name],
                cwd=project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Extract stats from output if possible
                stats = [line for line in result.stdout.split('\n') if "Stats:" in line]
                print(f"[Batch] SUCCESS: {pdf}")
                if stats: print(f"        {stats[0]}")
            else:
                print(f"[Batch] ERROR processing {pdf}:")
                print(result.stderr)
                
        except Exception as e:
            print(f"[Batch] Failed to launch builder for {pdf}: {e}")

if __name__ == "__main__":
    batch_ingest()
