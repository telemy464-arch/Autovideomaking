import asyncio
import os
import json
import base64
import urllib.request
import subprocess
from pathlib import Path
import edge_tts
from config import (
    TEMP_DIR,
    VOICES,
    ELEVEN_DEFAULT_VOICES,
    ELEVEN_MODELS,
    get_elevenlabs_api_key
)

def align_characters_to_words(chars: list, starts: list, ends: list) -> list:
    """
    Groups character-level timestamps from ElevenLabs API into word-level boundaries
    for animated karaoke subtitles.
    """
    words = []
    curr_word = []
    w_start = None
    w_end = None
    for c, s, e in zip(chars, starts, ends):
        if c.isspace():
            if curr_word:
                words.append({
                    "word": "".join(curr_word),
                    "start": round(w_start, 3),
                    "end": round(w_end, 3),
                    "duration": round(w_end - w_start, 3)
                })
                curr_word = []
                w_start = None
                w_end = None
        else:
            if w_start is None:
                w_start = s
            w_end = e
            curr_word.append(c)
    if curr_word:
        words.append({
            "word": "".join(curr_word),
            "start": round(w_start, 3),
            "end": round(w_end, 3),
            "duration": round(w_end - w_start, 3)
        })
    return words

def fetch_elevenlabs_voices(api_key: str = None) -> dict:
    """
    Fetches user's available ElevenLabs voices (custom cloned voices + library voices) via API.
    Falls back to ELEVEN_DEFAULT_VOICES if offline or error.
    """
    key = api_key or get_elevenlabs_api_key()
    if not key:
        return ELEVEN_DEFAULT_VOICES
    try:
        req = urllib.request.Request(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": key, "User-Agent": "MizanAIStudio/2.0"}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            voices = {}
            for v in data.get("voices", []):
                name = v.get("name", "Voice")
                labels = v.get("labels", {})
                gender = labels.get("gender", "")
                accent = labels.get("accent", "")
                use_case = labels.get("use_case", "")
                details = []
                if accent: details.append(accent.title())
                if gender: details.append(gender.title())
                if use_case: details.append(use_case.replace("_", " ").title())
                detail_str = f" ({', '.join(details)})" if details else ""
                label = f"{name}{detail_str}"
                voices[label] = v.get("voice_id")
            if voices:
                return voices
    except Exception:
        pass
    return ELEVEN_DEFAULT_VOICES

def generate_elevenlabs_speech(
    text: str,
    output_path: Path,
    voice_id: str = "JBFqnCBsd6RMkjVDRZzb",
    model_id: str = "eleven_multilingual_v2",
    api_key: str = None,
    stability: float = 0.5,
    similarity_boost: float = 0.75
) -> dict:
    """
    Generates ultra-realistic voiceover using ElevenLabs REST API.
    Supports Bengali, English, and 29+ languages with millisecond word-timestamp karaoke alignment.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    key = api_key or get_elevenlabs_api_key()
    if not key:
        raise ValueError("ElevenLabs API Key not found. Please provide an API key.")
        
    headers = {
        "xi-api-key": key,
        "Content-Type": "application/json",
        "User-Agent": "MizanAIStudio/2.0"
    }

    # 1. First attempt with-timestamps endpoint for millisecond karaoke subtitles
    ts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": float(stability),
            "similarity_boost": float(similarity_boost)
        }
    }
    
    word_timings = []
    audio_written = False
    
    try:
        req = urllib.request.Request(
            ts_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=35) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            if "audio_base64" in res_data:
                audio_bytes = base64.b64decode(res_data["audio_base64"])
                with open(output_path, "wb") as f_out:
                    f_out.write(audio_bytes)
                audio_written = True
                
                align = res_data.get("alignment", {})
                chars = align.get("characters", [])
                starts = align.get("character_start_times_seconds", [])
                ends = align.get("character_end_times_seconds", [])
                if chars and starts and ends:
                    word_timings = align_characters_to_words(chars, starts, ends)
    except Exception as ts_err:
        pass

    # 2. Fallback to standard MP3 stream endpoint if with-timestamps was unavailable
    if not audio_written:
        std_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        std_headers = {
            "xi-api-key": key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
            "User-Agent": "MizanAIStudio/2.0"
        }
        req_std = urllib.request.Request(
            std_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=std_headers
        )
        with urllib.request.urlopen(req_std, timeout=35) as resp_std:
            with open(output_path, "wb") as f_out:
                f_out.write(resp_std.read())

    duration = get_audio_duration(output_path)

    # 3. If word timings were not provided by API, estimate proportionally
    if not word_timings and text.strip():
        words = text.strip().split()
        if words and duration > 0:
            step = duration / len(words)
            for idx, w in enumerate(words):
                w_s = idx * step
                w_e = (idx + 1) * step
                word_timings.append({
                    "word": w,
                    "start": round(w_s, 3),
                    "end": round(w_e, 3),
                    "duration": round(step, 3)
                })

    return {
        "audio_path": str(output_path),
        "duration": duration,
        "srt_content": "",
        "word_timings": word_timings
    }

async def generate_speech_async(
    text: str,
    output_path: Path,
    voice: str = "bn-BD-NabanitaNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz"
) -> dict:
    """
    Generates speech using Edge-TTS for Bengali and English text.
    Also extracts word/sentence timings for karaoke subtitles.
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
                
    duration = get_audio_duration(output_path)
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
    pitch: str = "+0Hz",
    engine: str = "edge-tts",
    eleven_model: str = "eleven_multilingual_v2",
    eleven_api_key: str = None,
    eleven_stability: float = 0.5,
    eleven_similarity: float = 0.75
) -> dict:
    """
    Synchronous wrapper for speech generation.
    Supports Edge-TTS (free, fast, unlimited) and ElevenLabs (ultra-realistic studio voices).
    Gracefully falls back to Edge-TTS if ElevenLabs quota is exhausted or encounters an error.
    """
    out_path = TEMP_DIR / output_filename
    
    # 1. Handle ElevenLabs Engine
    if engine.lower() in ["elevenlabs", "eleven_labs", "eleven"]:
        try:
            return generate_elevenlabs_speech(
                text=text,
                output_path=out_path,
                voice_id=voice,
                model_id=eleven_model,
                api_key=eleven_api_key,
                stability=eleven_stability,
                similarity_boost=eleven_similarity
            )
        except Exception as e:
            # Automatic fallback to Edge-TTS
            fallback_voice = "bn-BD-NabanitaNeural" if any('\u0980' <= c <= '\u09ff' for c in text) else "en-US-JennyNeural"
            print(f"[ElevenLabs Notice] {e}. Auto-falling back to Edge-TTS ({fallback_voice})...")
            return asyncio.run(generate_speech_async(text, out_path, fallback_voice, rate, pitch))
            
    # 2. Default: Edge-TTS
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
    except Exception:
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
