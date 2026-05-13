import os
import sys
import io
from contextlib import redirect_stdout

# Add builder to path for Pulse
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'builder'))
from pulse_query import pulse_search

def generate_script(topic):
    print(f"--- TAH Voiceover Generator: '{topic}' ---")
    
    # Capture pulse_search output
    f = io.StringIO()
    with redirect_stdout(f):
        try:
            pulse_search(topic)
        except Exception as e:
            print(f"Error during pulse search: {e}")
    
    raw_context = f.getvalue()
    
    if "No matches found" in raw_context or not raw_context.strip():
        print(f"Error: No technical ground truth found for '{topic}' in the library.")
        return

    # In a real micro-agent, this would call an LLM API. 
    # Here, we provide the 'Surgical Script Template' for the user to fill or for the agent to complete.
    
    print("\n[SCENE 1: THE HOOK - 0:00-0:15]")
    print(f"Visual: Macro shot of code or Sunset Pulse logo.")
    print(f"Audio: 'Ever wondered how we achieve sub-millisecond precision in {topic}? Most systems guess. We seek.'")

    print("\n[SCENE 2: THE TECH - 0:15-0:45]")
    print(f"Visual: 3D Visualization of the TAH Cartridge structure.")
    print(f"Audio: 'Using the TAH v3.1 spec, we bypass the token tax. Here is what the library says about it:'")
    
    # Extract a snippet from the pulse results for the script
    lines = [l for l in raw_context.split('\n') if l.strip() and not l.startswith('---') and not l.startswith('[SOURCE')]
    snippet = " ".join(lines[:3]) # Take the first few lines of actual data
    print(f"Audio (Technical): '...{snippet}...'")

    print("\n[SCENE 3: THE EDGE - 0:45-1:00]")
    print(f"Visual: Fast-paced montage of Sunset Pulse UI.")
    print(f"Audio: 'This isn't just search. It is deterministic intelligence. Surgical. Fast. Sunset Pulse.'")

    print("\n--- SCRIPT GENERATED ---")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python voiceover_gen.py \"Your Topic\"")
    else:
        generate_script(sys.argv[1])
