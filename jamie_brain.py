import sys
import os
from pathlib import Path

# Add builder to path for pulse_query
sys.path.append('SunsetWars/builder')
from pulse_query import pulse_search

def jamie_answer(question):
    print(f"\n[Jamie Thinking] Querying Global Cartridges...")
    
    # 1. Search all cartridges in /cartridges and /cartridges/universe
    # pulse_query is already optimized for this
    results = pulse_search(question)
    
    if not results:
        return "I couldn't find a surgical match in my cartridges. Please add more knowledge seeds to my hub."
    
    # In a real scenario, this would be fed to an LLM context.
    # For now, we return the highest signal match.
    return results[0]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python SunsetWars/jamie_brain.py '<question>'")
    else:
        print(jamie_answer(" ".join(sys.argv[1:])))
