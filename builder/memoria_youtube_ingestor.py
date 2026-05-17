import os
import subprocess
import whisper
import re
from memoria_builder import MemoriaBuilder, OzrielSegmenter

class YouTubeIngestor:
    """
    Memoria YouTube Ingestor (v3.1)
    Transforms video audio into privacy-centric specialized knowledge vaults.
    """
    def __init__(self, model_size="base", target_fp=0.0001, shard_size=1200):
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

    def build_vault(self, url, vault_name):
        """Pipeline: Download -> Transcribe -> Memoria Build."""
        temp_audio = f"temp_{vault_name}"
        audio_path = self.download_audio(url, temp_audio)
        
        if not audio_path:
            return None
        
        try:
            transcript = self.transcribe_audio(audio_path)
            
            # Use Ozriel semantic segmentation
            shards = OzrielSegmenter.segment(transcript, max_shard_size=self.shard_size)
            
            print(f"[Memoria] Generating vault from {len(shards)} transcript shards...")
            
            expected_elements = len(shards) * 20
            builder = MemoriaBuilder(target_fp=self.target_fp, expected_elements=expected_elements)
            
            for shard in shards:
                builder.add_text_shard(shard)
            
            output_base = f"cartridges/{vault_name}"
            builder.save(output_base)
            
            return output_base
        finally:
            # Cleanup temporary audio files
            if os.path.exists(audio_path):
                os.remove(audio_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Memoria YouTube Ingestor v3.1")
        print("Usage: python builder/memoria_youtube_ingestor.py <url> [vault_name]")
        sys.exit(1)
        
    url = sys.argv[1]
    vault_name = sys.argv[2] if len(sys.argv) > 2 else "youtube_expert"
    
    ingestor = YouTubeIngestor(model_size="base")
    ingestor.build_vault(url, vault_name)
