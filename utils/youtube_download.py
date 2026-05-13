import subprocess
import sys
import os

def download_video(url):
    print(f"[*] Starting YouTube Download: {url}")
    
    # Target directory in Sunset Pulse
    target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../SunsetPulse/public/videos"))
    os.makedirs(target_dir, exist_ok=True)
    
    output_template = os.path.join(target_dir, "%(title)s.%(ext)s")
    
    cmd = [
        "python", "-m", "yt_dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
        "-o", output_template,
        "--no-playlist",
        "--merge-output-format", "mp4",
        url
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n[+] Download Complete! File saved to SunsetPulse/public/videos")
        print(f"[+] You can now use this file in the Production Studio.")
    except Exception as e:
        print(f"[-] Download Failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python youtube_download.py <YOUTUBE_URL>")
    else:
        download_video(sys.argv[1])
