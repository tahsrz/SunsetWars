import os
import subprocess
import time
import sys

# Add builder to path for TAHQuery
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'builder'))
from pulse_query import main as pulse_main

def get_clipboard():
    """Get clipboard text using PowerShell (Zero Dependency)."""
    try:
        return subprocess.check_output(['powershell', '-command', 'Get-Clipboard'], universal_newlines=True).strip()
    except:
        return ""

def main():
    print("--- TAH Pulse Clip v1.0 ---")
    print("Monitoring clipboard... (Press Ctrl+C to stop)")
    
    last_clip = ""
    while True:
        try:
            current_clip = get_clipboard()
            if current_clip and current_clip != last_clip:
                if len(current_clip) < 100: # Only pulse for short snippets/keywords
                    print(f"\n[Clipboard Change Detected: '{current_clip}']")
                    print("Pulsing tactical library...")
                    # Mock sys.argv for pulse_query.main
                    original_argv = sys.argv
                    sys.argv = ['pulse_query.py', current_clip]
                    try:
                        pulse_main()
                    except SystemExit:
                        pass
                    sys.argv = original_argv
                last_clip = current_clip
            time.sleep(2)
        except KeyboardInterrupt:
            print("\nStopping...")
            break

if __name__ == "__main__":
    main()
