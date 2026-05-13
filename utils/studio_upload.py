import requests
import json
import os
import sys

def upload_to_studio(wav_path, topic="Market Intel"):
    url = "http://localhost:3000/api/studio"
    
    if not os.path.exists(wav_path):
        print(f"Error: File {wav_path} not found.")
        return

    # Basic recipe
    recipe = {
        "targetScene": "/videos/jamie_base.mp4",
        "extractedEntity": {
            "uid": "JAMIE-01",
            "name": "Jamie",
            "visual": { "assetPath": "/videos/jamie_base.mp4", "meshColor": "#3b82f6" },
            "isExtracted": True
        },
        "transform": { "x": 0, "y": 0, "scale": 1, "maskRadius": 80, "maskFeather": 20, "brightness": 110, "contrast": 120 },
        "compositing": { "blendMode": "normal", "vibePreset": "tactical", "motionPath": "none", "opacity": 100 },
        "audioConfig": { "backgroundTrack": "/audio/intro.mp3", "backgroundVolume": 30, "subjectVolume": 100, "isMuted": False },
        "script": f"Tactical Briefing: {topic}",
        "voice": "Jamie"
    }

    print(f"[*] Sending {wav_path} to Sunset Pulse Studio...")
    
    with open(wav_path, 'rb') as f:
        files = {'file': (os.path.basename(wav_path), f, 'audio/wav')}
        data = {'recipe': json.dumps(recipe)}
        
        try:
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                print(f"[+] Success! Production rendered.")
                print(f"[+] Download URL: http://localhost:3000{result.get('downloadUrl')}")
            else:
                print(f"[-] Render Failed: {result.get('message')}")
                print(f"[-] Details: {result.get('details')}")
                
        except Exception as e:
            print(f"[-] Request Failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python studio_upload.py <WAV_PATH> [TOPIC]")
    else:
        topic = sys.argv[2] if len(sys.argv) > 2 else "Market Intel"
        upload_to_studio(sys.argv[1], topic)
