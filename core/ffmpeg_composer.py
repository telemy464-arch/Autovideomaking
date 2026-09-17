import subprocess
import os
from pathlib import Path
from config import OUTPUT_DIR, TEMP_DIR, FONTS_DIR, BGM_DIR, DEFAULT_FONT_PATH

def escape_ffmpeg_filter_path(path: Path) -> str:
    """Properly escapes file paths for FFmpeg filter graph (subtitles/ass)"""
    s = str(path.resolve()).replace("\\", "/")
    s = s.replace(":", "\\:")
    return s

def prepare_clip(
    input_clip: Path,
    output_clip: Path,
    target_duration: float,
    width: int,
    height: int
) -> bool:
    """
    Normalizes a single video clip to exact width, height, framerate (30fps) and duration.
    Uses scale+crop with center alignment.
    """
    output_clip = Path(output_clip)
    output_clip.parent.mkdir(parents=True, exist_ok=True)
    
    vf = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps=30,setsar=1"
    
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", str(input_clip),
        "-t", str(target_duration),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-an",
        str(output_clip)
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.returncode == 0
    except Exception as e:
        print(f"[Clip Preparation Error] {e}")
        return False

def assemble_final_video(
    clips: list,
    durations: list,
    voice_audio: Path,
    output_path: Path,
    subtitles_path: Path = None,
    subtitle_overlays: list = None,
    subtitles_concat_path: Path = None,
    bgm_path: Path = None,
    bgm_volume: float = 0.12,
    width: int = 1080,
    height: int = 1920
) -> Path:
    """
    Compiles normalized clips, mixes voice audio + background music, overlays 100% unbroken Bengali subtitles,
    and produces final clean MP4 without watermarks.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Normalize each clip
    prepared_clips = []
    concat_list_file = TEMP_DIR / "concat_list.txt"
    
    with open(concat_list_file, "w", encoding="utf-8") as f_concat:
        for idx, duration in enumerate(durations):
            clip_path = clips[idx % len(clips)]
            prep_out = TEMP_DIR / f"prep_clip_{idx:04d}.mp4"
            if prepare_clip(clip_path, prep_out, duration, width, height):
                prepared_clips.append(prep_out)
                f_concat.write(f"file '{str(prep_out.resolve())}'\n")
                
    if not prepared_clips:
        raise RuntimeError("No valid video clips could be prepared.")
        
    stitched_video = TEMP_DIR / "stitched_video.mp4"
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-c", "copy",
        str(stitched_video)
    ]
    subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    
    # 2. Build inputs and filters
    input_args = ["-i", str(stitched_video), "-i", str(voice_audio)]
    
    # Check BGM
    has_bgm = bgm_path and Path(bgm_path).exists()
    if has_bgm:
        input_args.extend(["-stream_loop", "-1", "-i", str(bgm_path)])
        audio_filter = f"[1:a]volume=1.0[v_speech];[2:a]volume={bgm_volume}[v_bgm];[v_speech][v_bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    else:
        audio_filter = "[1:a]volume=1.0[aout]"
        
    filter_complex = []
    
    # Subtitle processing (Karaoke concat track preferred, fallback to overlays or ass)
    if subtitles_concat_path and Path(subtitles_concat_path).exists():
        y_pos = "H-420" if height > width else "H-220"
        sub_input_idx = input_args.count("-i")
        input_args.extend(["-f", "concat", "-safe", "0", "-i", str(subtitles_concat_path)])
        filter_complex.append(f"[0:v][{sub_input_idx}:v]overlay=0:{y_pos}[v_sub]")
        map_video = "[v_sub]"
    elif subtitle_overlays and len(subtitle_overlays) > 0:
        y_pos = "H-420" if height > width else "H-220"
        current_v = "0:v"
        overlay_filters = []
        base_input_idx = 3 if has_bgm else 2
        
        for i, ov in enumerate(subtitle_overlays):
            png_p = Path(ov["png_path"])
            if png_p.exists():
                input_args.extend(["-i", str(png_p)])
                next_v = f"v_sub_{i}"
                s_time = max(0.0, float(ov["start"]))
                e_time = float(ov["end"])
                overlay_filters.append(f"[{current_v}][{base_input_idx}:v]overlay=0:{y_pos}:enable='between(t,{s_time:.2f},{e_time:.2f})'[{next_v}]")
                current_v = next_v
                base_input_idx += 1
                
        if overlay_filters:
            filter_complex.extend(overlay_filters)
            map_video = f"[{current_v}]"
        else:
            map_video = "0:v"
    elif subtitles_path and Path(subtitles_path).exists():
        escaped_sub = escape_ffmpeg_filter_path(subtitles_path)
        filter_complex.append(f"[0:v]subtitles='{escaped_sub}'[vout]")
        map_video = "[vout]"
    else:
        map_video = "0:v"
        
    filter_complex.append(audio_filter)
    
    cmd_final = ["ffmpeg", "-y"]
    cmd_final.extend(input_args)
    cmd_final.extend([
        "-filter_complex", ";".join(filter_complex),
        "-map", map_video,
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_path)
    ])
    
    res = subprocess.run(cmd_final, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"[FFmpeg Error] {res.stderr}")
        # Fallback without subtitles if font/subtitle parser encountered syntax issue
        cmd_fallback = [
            "ffmpeg", "-y",
            "-i", str(stitched_video),
            "-i", str(voice_audio),
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_path)
        ]
        subprocess.run(cmd_fallback, check=True)
        
    return output_path
