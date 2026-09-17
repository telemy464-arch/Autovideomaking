import os
import json
import re
from pathlib import Path
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from google import genai
from config import get_gemini_api_key

def align_audio_with_script(
    audio_path: Path,
    scenes: list,
    api_key: str = None,
    progress_callback = None
) -> dict:
    """
    Aligns uploaded voiceover audio with script scenes and words.
    Uses a hybrid approach:
    1. Gemini 3.6 Flash Audio Understanding (listens to voice and extracts exact sentence timestamps)
    2. Acoustic Voice Activity Detection (VAD via Pydub) as robust offline/fallback alignment.
    
    Returns:
    {
        "scene_timings": [{"start": float, "end": float, "duration": float, "text": str}],
        "word_timings": [{"word": str, "start": float, "end": float, "duration": float}],
        "total_duration": float
    }
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
    audio_seg = AudioSegment.from_file(str(audio_path))
    total_duration = len(audio_seg) / 1000.0
    total_scenes = len(scenes)
    
    if total_scenes == 0:
        return {
            "scene_timings": [],
            "word_timings": [],
            "total_duration": total_duration
        }

    key = api_key or get_gemini_api_key()
    aligned_data = None
    
    # Attempt 1: Gemini Multimodal Audio Alignment
    if key:
        try:
            if progress_callback:
                progress_callback(25, "🎙️ AI অডিও শুনে প্রতিটি বাক্যের নিখুঁত টাইমস্ট্যাম্প বিশ্লেষণ করছে...")
            aligned_data = _align_with_gemini(audio_path, scenes, total_duration, key)
        except Exception as e:
            print(f"[Gemini Audio Alignment Error] {e}")
            aligned_data = None

    # Attempt 2: Acoustic Speech Silence / VAD Alignment (Fallback or primary if no API key)
    if not aligned_data or len(aligned_data.get("scene_timings", [])) == 0:
        if progress_callback:
            progress_callback(30, "🎙️ অ্যাকোস্টিক ভয়েস পজ ও সাইলেন্স বিশ্লেষণ করে সিঙ্ক করা হচ্ছে...")
        aligned_data = _align_with_acoustic_vad(audio_seg, scenes, total_duration)

    return aligned_data

def _align_with_gemini(audio_path: Path, scenes: list, total_duration: float, api_key: str) -> dict:
    client = genai.Client(api_key=api_key)
    uploaded_file = client.files.upload(file=str(audio_path))
    
    scenes_text_list = []
    for idx, sc in enumerate(scenes):
        txt = sc.get("subtitle_text", sc.get("voiceover_text", "")).strip()
        scenes_text_list.append(f"Scene {idx+1}: {txt}")
        
    script_context = "\n".join(scenes_text_list)
    
    prompt = f"""You are an expert audio-to-text subtitle alignment engine.
Listen carefully to the provided audio (total duration: {total_duration:.2f} seconds).
Match the following {len(scenes)} script scenes to the audio and find the exact timestamps when each scene is spoken:

{script_context}

Rules:
1. Return the exact start and end times in seconds for each of the {len(scenes)} scenes in order.
2. Timestamps must be within 0.0 and {total_duration:.2f} seconds.
3. Start time of scene 1 should match the first spoken word.
4. Ensure scenes do not overlap improperly and respect natural speech pauses.

Respond ONLY with valid JSON matching this schema:
{{
  "scenes": [
    {{
      "scene_index": 1,
      "start": 0.0,
      "end": 3.4,
      "text": "spoken text..."
    }}
  ]
}}
"""
    models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]
    parsed_json = None
    for m in models_to_try:
        try:
            resp = client.models.generate_content(
                model=m,
                contents=[uploaded_file, prompt],
                config={"response_mime_type": "application/json"}
            )
            txt = resp.text.strip()
            if txt.startswith("```json"):
                txt = txt[7:]
            if txt.endswith("```"):
                txt = txt[:-3]
            parsed_json = json.loads(txt.strip())
            if parsed_json and "scenes" in parsed_json and len(parsed_json["scenes"]) > 0:
                break
        except Exception as err:
            print(f"[Gemini Audio Alignment Model {m} error] {err}")
            continue

    if not parsed_json or "scenes" not in parsed_json:
        return None

    raw_ai_scenes = parsed_json["scenes"]
    scene_timings = []
    word_timings = []

    for idx, sc in enumerate(scenes):
        raw_text = sc.get("subtitle_text", sc.get("voiceover_text", "")).strip()
        if idx < len(raw_ai_scenes):
            ai_sc = raw_ai_scenes[idx]
            s_time = max(0.0, float(ai_sc.get("start", 0.0)))
            e_time = min(total_duration, float(ai_sc.get("end", s_time + 3.0)))
            if e_time <= s_time:
                e_time = min(total_duration, s_time + 2.5)
        else:
            prev_end = scene_timings[-1]["end"] if scene_timings else 0.0
            s_time = prev_end
            e_time = min(total_duration, s_time + 3.0)

        dur = max(1.0, e_time - s_time)
        scene_timings.append({
            "start": s_time,
            "end": e_time,
            "duration": dur,
            "text": raw_text
        })
        
        # Word level timings inside scene
        words = [w for w in raw_text.split() if w]
        if words:
            w_total_chars = sum(len(w) for w in words)
            cur_w_time = s_time
            for w in words:
                w_dur = (len(w) / w_total_chars) * dur if w_total_chars > 0 else dur / len(words)
                w_dur = max(0.12, w_dur)
                word_timings.append({
                    "word": w,
                    "start": cur_w_time,
                    "end": min(e_time, cur_w_time + w_dur),
                    "duration": w_dur
                })
                cur_w_time += w_dur

    return {
        "scene_timings": scene_timings,
        "word_timings": word_timings,
        "total_duration": total_duration
    }

def _align_with_acoustic_vad(audio_seg: AudioSegment, scenes: list, total_duration: float) -> dict:
    """
    Acoustic Voice Activity Detection (VAD) using Pydub silence detection.
    Detects natural pauses/silence between spoken sentences, so subtitles pause
    exactly when the speaker pauses, and align to spoken segments.
    """
    # Detect nonsilent chunks (speech bursts)
    db_thresh = audio_seg.dBFS - 15 if audio_seg.dBFS != float("-inf") else -35
    nonsilent = detect_nonsilent(audio_seg, min_silence_len=280, silence_thresh=db_thresh)
    
    total_scenes = len(scenes)
    scene_timings = []
    word_timings = []

    if not nonsilent:
        chunk_dur = total_duration / total_scenes
        nonsilent = [(int(i * chunk_dur * 1000), int((i + 1) * chunk_dur * 1000)) for i in range(total_scenes)]

    scene_char_counts = [len(sc.get("subtitle_text", sc.get("voiceover_text", "")).strip()) for sc in scenes]
    total_chars = sum(scene_char_counts) if sum(scene_char_counts) > 0 else total_scenes
    
    speech_points = []
    for s_ms, e_ms in nonsilent:
        speech_points.append((s_ms / 1000.0, e_ms / 1000.0))

    if len(speech_points) == total_scenes:
        for idx, sc in enumerate(scenes):
            s_time, e_time = speech_points[idx]
            txt = sc.get("subtitle_text", sc.get("voiceover_text", "")).strip()
            dur = max(1.0, e_time - s_time)
            scene_timings.append({
                "start": s_time,
                "end": e_time,
                "duration": dur,
                "text": txt
            })
    else:
        first_speech_start = speech_points[0][0]
        last_speech_end = speech_points[-1][1]
        active_span = max(1.0, last_speech_end - first_speech_start)
        
        cur_pos = first_speech_start
        for idx, sc in enumerate(scenes):
            txt = sc.get("subtitle_text", sc.get("voiceover_text", "")).strip()
            c_len = len(txt) if len(txt) > 0 else 1
            scene_span = (c_len / total_chars) * active_span
            
            s_time = cur_pos
            e_time = min(total_duration, s_time + scene_span)
            dur = max(1.0, e_time - s_time)
            
            scene_timings.append({
                "start": s_time,
                "end": e_time,
                "duration": dur,
                "text": txt
            })
            cur_pos = e_time

    for st in scene_timings:
        s_time = st["start"]
        e_time = st["end"]
        dur = st["duration"]
        txt = st["text"]
        words = [w for w in txt.split() if w]
        if not words:
            continue
            
        w_chars = sum(len(w) for w in words)
        cur_w_time = s_time
        for w in words:
            w_weight = len(w) / w_chars if w_chars > 0 else 1.0 / len(words)
            w_dur = max(0.12, w_weight * dur)
            word_timings.append({
                "word": w,
                "start": cur_w_time,
                "end": min(e_time, cur_w_time + w_dur),
                "duration": w_dur
            })
            cur_w_time += w_dur

    return {
        "scene_timings": scene_timings,
        "word_timings": word_timings,
        "total_duration": total_duration
    }
