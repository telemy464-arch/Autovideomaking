import asyncio
import os
import subprocess
from pathlib import Path
import edge_tts
from config import TEMP_DIR, VOICES

async def generate_speech_async(
    text: str,
    output_path: Path,
    voice: str = "bn-BD-NabanitaNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz"
) -> dict:
    """
    Generates speech using Edge-TTS for Bengali text.
    Also extracts word/sentence timings for karaoke or timed subtitles.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    
    submaker = edge_tts.SubMaker()
    word_timings = []
    
    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)
                w_text = chunk.get("text", "").strip()
                if w_text:
                    offset_sec = chunk["offset"] / 10_000_000.0
                    dur_sec = chunk["duration"] / 10_000_000.0
                    word_timings.append({
                        "word": w_text,
                        "start": offset_sec,
                        "end": offset_sec + dur_sec,
                        "duration": dur_sec
                    })
                
    # Get exact duration using ffprobe
    duration = get_audio_duration(output_path)
    
    # Generate SRT formatted subtitle text from SubMaker
    srt_content = submaker.get_srt()
    
    return {
        "audio_path": str(output_path),
        "duration": duration,
        "srt_content": srt_content,
        "word_timings": word_timings
    }

def generate_speech(
    text: str,
    output_filename: str = "speech.mp3",
    voice: str = "bn-BD-NabanitaNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz"
) -> dict:
    """Synchronous wrapper for generate_speech_async"""
    out_path = TEMP_DIR / output_filename
    return asyncio.run(generate_speech_async(text, out_path, voice, rate, pitch))

def get_audio_duration(file_path: Path) -> float:
    """Extract accurate audio duration in seconds using ffprobe or ffmpeg"""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        # Fallback using ffmpeg
        try:
            cmd = ["ffmpeg", "-i", str(file_path)]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for line in result.stderr.split("\n"):
                if "Duration" in line:
                    time_str = line.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = time_str.split(":")
                    return int(h) * 3600 + int(m) * 60 + float(s)
        except Exception:
            return 10.0
    return 10.0
