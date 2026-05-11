import os
import subprocess
import whisper
import re
from tah_builder import TAHBuilder

class YouTubeIngestor:
    """
    TAH YouTube Ingestor (v1.0)
    Transforms video audio into privacy-centric specialized knowledge cartridges.
    """
    def __init__(self, model_size="base", target_fp=0.0001, shard_size=1000):
        self.model_size = model_size
        self.target_fp = target_fp
        self.shard_size = shard_size
        self._model = None

    @property
    def model(self):
        if self._model is None:
            print(f"[Whisper] Loading local model: {self.model_size}...")
            self._model = whisper.load_model(self.model_size)
        return self._model

    def download_audio(self, url, output_name):
        """Downloads audio from YouTube using yt-dlp."""
        audio_file = f"{output_name}.mp3"
        print(f"[yt-dlp] Extracting audio from: {url}")
        
        # Use subprocess to call yt-dlp (handling path if not in env)
        cmd = [
            "python", "-m", "yt_dlp", 
            "-x", "--audio-format", "mp3", 
            "-o", f"{output_name}.%(ext)s", 
            url
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return audio_file
        except Exception as e:
            print(f"[Error] Audio extraction failed: {e}")
            return None

    def transcribe_audio(self, audio_path):
        """Transcribes audio file using local OpenAI Whisper."""
        print(f"[Whisper] Transcribing {audio_path}...")
        result = self.model.transcribe(audio_path)
        return result['text']

    def build_cartridge(self, url, cartridge_name):
        """Pipeline: Download -> Transcribe -> TAH Build."""
        temp_audio = f"temp_{cartridge_name}"
        audio_path = self.download_audio(url, temp_audio)
        
        if not audio_path:
            return None
        
        try:
            transcript = self.transcribe_audio(audio_path)
            
            # Clean transcript and chunk
            transcript = re.sub(r'\s+', ' ', transcript).strip()
            shards = self._chunk_text(transcript)
            
            print(f"[TAH] Generating cartridge from {len(shards)} transcript shards...")
            
            expected_elements = len(shards) * 20
            builder = TAHBuilder(target_fp=self.target_fp, expected_elements=expected_elements)
            
            for shard in shards:
                builder.add_shard(shard)
            
            output_path = f"cartridges/{cartridge_name}.tah"
            builder.save(output_path)
            
            return output_path
        finally:
            # Cleanup temporary audio files
            if os.path.exists(audio_path):
                os.remove(audio_path)

    def _chunk_text(self, text):
        """Segments transcript into tactical shards."""
        shards = []
        start = 0
        while start < len(text):
            end = start + self.shard_size
            if end < len(text):
                boundary = text.rfind('.', start, end + 200)
                if boundary != -1 and boundary > start:
                    end = boundary + 1
            shards.append(text[start:end].strip())
            start = end
        return shards

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("TAH YouTube Ingestor v1.0")
        print("Usage: python builder/youtube_ingestor.py <url> [cartridge_name]")
        sys.exit(1)
        
    url = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else "youtube_expert"
    
    ingestor = YouTubeIngestor(model_size="base")
    ingestor.build_cartridge(url, name)
