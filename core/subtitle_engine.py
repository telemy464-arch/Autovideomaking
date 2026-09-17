import re
from pathlib import Path
from config import DEFAULT_FONT_PATH, FONTS_DIR

def convert_seconds_to_ass_time(seconds: float) -> str:
    """Converts seconds float to ASS timestamp format H:MM:SS.cs"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

def convert_seconds_to_srt_time(seconds: float) -> str:
    """Converts seconds float to SRT timestamp format HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def parse_srt_to_dialogues(srt_content: str) -> list:
    """Parses an SRT string into list of dicts with start, end, text"""
    dialogues = []
    blocks = srt_content.strip().split("\n\n")
    time_pattern = re.compile(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})")
    
    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if len(lines) >= 2:
            time_match = time_pattern.search(lines[1]) if len(lines) > 1 else None
            if not time_match and len(lines) > 2:
                time_match = time_pattern.search(lines[2])
                text = " ".join(lines[3:])
            else:
                text = " ".join(lines[2:])
                
            if time_match:
                sh, sm, ss, sms, eh, em, es, ems = map(int, time_match.groups())
                start_sec = sh * 3600 + sm * 60 + ss + sms / 1000.0
                end_sec = eh * 3600 + em * 60 + es + ems / 1000.0
                if text.strip():
                    dialogues.append({
                        "start": start_sec,
                        "end": end_sec,
                        "text": text.strip()
                    })
    return dialogues

def generate_ass_subtitles(
    dialogues: list,
    output_path: Path,
    width: int = 1080,
    height: int = 1920,
    font_name: str = "Noto Sans Bengali",
    font_size: int = 42,
    primary_color: str = "&H0000FFFF",  # Yellow (BGR)
    outline_color: str = "&H00000000",  # Black
    outline_width: float = 3.5,
    margin_v: int = 120
) -> Path:
    """
    Generates a styled ASS subtitle file for crisp Bengali rendering in FFmpeg.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Adjust font size and vertical margin for landscape vs portrait
    if width > height:  # 16:9
        font_size = 46
        margin_v = 70
    else:  # 9:16
        font_size = 48
        margin_v = 280

    ass_header = f"""[Script Info]
Title: AI Video making By Mizan Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_color},&H000000FF,{outline_color},&H80000000,-1,0,0,0,100,100,0,0,1,{outline_width},1.5,2,30,30,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for d in dialogues:
        start_str = convert_seconds_to_ass_time(d["start"])
        end_str = convert_seconds_to_ass_time(d["end"])
        clean_text = d["text"].replace("\\n", " ").strip()
        events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{clean_text}")

    ass_content = ass_header + "\n".join(events) + "\n"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
        
    return output_path

def generate_subtitle_png_overlays(
    dialogues: list,
    width: int = 1080,
    font_size: int = 46
) -> list:
    """
    Renders 100% UNBROKEN Bengali and English subtitles as transparent PNG overlays
    using Windows native GDI+ engine.
    """
    import json
    import subprocess
    from config import TEMP_DIR, BASE_DIR
    
    sub_items = []
    overlays = []
    
    ps_script = BASE_DIR / "core" / "render_subtitles.ps1"
    json_path = TEMP_DIR / "sub_batch_render.json"
    
    for idx, d in enumerate(dialogues):
        png_out = TEMP_DIR / f"sub_overlay_{idx:03d}.png"
        clean_text = d["text"].replace("\n", " ").strip()
        sub_items.append({
            "id": idx,
            "text": clean_text,
            "outPath": str(png_out.resolve()).replace("\\", "/")
        })
        overlays.append({
            "start": d["start"],
            "end": d["end"],
            "png_path": png_out
        })
        
    payload = {
        "width": width,
        "fontSize": font_size,
        "subtitles": sub_items
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        
    cmd = [
        "powershell",
        "-ExecutionPolicy", "Bypass",
        "-File", str(ps_script),
        "-jsonPath", str(json_path)
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print(f"[Subtitle PNG Gen Warning] {e}")
        
    return overlays

def estimate_word_timings_for_custom_audio(scenes: list, total_duration: float) -> list:
    """
    Estimates word-level timestamps when custom voice audio is uploaded,
    proportional to syllable / character weight, so karaoke pink highlight is fully functional.
    """
    all_words = []
    scene_words = []
    for sc in scenes:
        text = sc.get("subtitle_text", sc.get("voiceover_text", "")).strip()
        w_list = [w for w in text.split() if w]
        if w_list:
            scene_words.append(w_list)
            
    total_words_count = sum(len(wl) for wl in scene_words)
    if total_words_count == 0:
        return []
        
    current_time = 0.2
    usable_duration = max(1.0, total_duration - 0.4)
    total_chars = sum(sum(len(w) for w in wl) for wl in scene_words)
    
    for wl in scene_words:
        for w in wl:
            weight = len(w) / total_chars if total_chars > 0 else 1.0 / total_words_count
            dur = max(0.22, weight * usable_duration)
            all_words.append({
                "word": w,
                "start": current_time,
                "end": current_time + dur,
                "duration": dur
            })
            current_time += dur
            
    return all_words

def generate_karaoke_subtitle_track(
    word_timings: list,
    total_duration: float,
    width: int = 1080,
    height: int = 1920,
    max_words_per_chunk: int = 4
) -> Path:
    """
    Renders word-by-word karaoke subtitles:
    - Font color: Crisp White with black border
    - Spoken word: Vibrant hot pink badge/mark on the active word
    - Exactly synced with voiceover WordBoundary timestamps
    - Produces a single concat track for FFmpeg for maximum performance and 0 lag.
    """
    import json
    import subprocess
    from config import TEMP_DIR, BASE_DIR
    
    if not word_timings:
        return None
        
    font_size = 46 if width <= height else 42
    ps_script = BASE_DIR / "core" / "render_karaoke_subtitles.ps1"
    json_path = TEMP_DIR / "sub_karaoke_render.json"
    concat_txt_path = TEMP_DIR / "subtitles_concat.txt"
    
    # 1. Group into readable chunks of 3-4 words (or break on pauses > 1.2s)
    chunks = []
    curr_chunk = []
    
    for w in word_timings:
        if curr_chunk:
            time_gap = w["start"] - curr_chunk[-1]["end"]
            if len(curr_chunk) >= max_words_per_chunk or time_gap > 1.2:
                chunks.append(curr_chunk)
                curr_chunk = []
        curr_chunk.append(w)
    if curr_chunk:
        chunks.append(curr_chunk)
        
    # 2. Build the frame sequence
    sub_items = []
    timeline_frames = []
    current_time = 0.0
    img_idx = 0
    
    # Empty transparent image for gaps
    blank_png = TEMP_DIR / "karaoke_blank.png"
    
    for c_idx, chunk in enumerate(chunks):
        c_start = chunk[0]["start"]
        c_words = [w["word"] for w in chunk]
        
        # Gap before chunk
        if c_start > current_time + 0.05:
            gap_dur = c_start - current_time
            timeline_frames.append({
                "png_path": blank_png,
                "duration": gap_dur
            })
            current_time = c_start
            
        next_chunk_start = chunks[c_idx + 1][0]["start"] if c_idx + 1 < len(chunks) else total_duration
        
        # Each word in chunk
        for w_idx in range(len(chunk)):
            w_item = chunk[w_idx]
            w_start = w_item["start"]
            
            if w_start > current_time + 0.05:
                current_time = w_start
                
            if w_idx < len(chunk) - 1:
                w_end = chunk[w_idx + 1]["start"]
            else:
                # Last word of chunk: hold for duration or until next chunk
                w_end = min(w_item["end"] + 0.4, next_chunk_start)
                
            dur = max(0.08, w_end - current_time)
            
            frame_png = TEMP_DIR / f"karaoke_frame_{img_idx:06d}.png"
            sub_items.append({
                "id": img_idx,
                "words": c_words,
                "activeWordIndex": w_idx,
                "isTransparent": False,
                "outPath": str(frame_png.resolve()).replace("\\", "/")
            })
            timeline_frames.append({
                "png_path": frame_png,
                "duration": dur
            })
            
            current_time += dur
            img_idx += 1
            
    # Gap after last chunk
    if current_time < total_duration:
        tail_dur = total_duration - current_time
        timeline_frames.append({
            "png_path": blank_png,
            "duration": tail_dur
        })
        
    # Blank frame item
    sub_items.append({
        "id": 99999,
        "words": [],
        "activeWordIndex": -1,
        "isTransparent": True,
        "outPath": str(blank_png.resolve()).replace("\\", "/")
    })
    
    # 3. Render all frames with PowerShell GDI+
    payload = {
        "width": width,
        "fontSize": font_size,
        "subtitles": sub_items
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        
    cmd = [
        "powershell",
        "-ExecutionPolicy", "Bypass",
        "-File", str(ps_script),
        "-jsonPath", str(json_path)
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print(f"[Karaoke Subtitle Gen Warning] {e}")
        return None
        
    # 4. Generate subtitles_concat.txt
    with open(concat_txt_path, "w", encoding="utf-8") as f_c:
        f_c.write("ffconcat version 1.0\n")
        for tf in timeline_frames:
            p_str = str(tf["png_path"].resolve()).replace("\\", "/")
            f_c.write(f"file '{p_str}'\n")
            f_c.write(f"duration {tf['duration']:.3f}\n")
        if timeline_frames:
            last_p = str(timeline_frames[-1]["png_path"].resolve()).replace("\\", "/")
            f_c.write(f"file '{last_p}'\n")
            
    return concat_txt_path
