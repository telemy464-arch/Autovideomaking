import os
import time
from datetime import datetime
from pathlib import Path
from core.tts_engine import generate_speech, get_audio_duration
from core.subtitle_engine import (
    generate_ass_subtitles,
    generate_subtitle_png_overlays,
    generate_karaoke_subtitle_track,
    estimate_word_timings_for_custom_audio
)
from core.audio_aligner import align_audio_with_script
from core.ffmpeg_composer import assemble_final_video
from config import OUTPUT_DIR, TEMP_DIR, BGM_DIR, ASPECT_RATIOS

def compose_full_video(
    script_data: dict,
    video_clips: list,
    voice_name: str = "bn-BD-NabanitaNeural",
    aspect_ratio_key: str = "Shorts / Reels (9:16)",
    bgm_filename: str = "inspiring_cinematic.mp3",
    bgm_volume: float = 0.12,
    custom_audio_path: Path = None,
    tts_rate: str = "+0%",
    tts_pitch: str = "+0Hz",
    progress_callback = None
) -> dict:
    """
    এজেন্ট ৪: ভিডিও কম্পোজার
    সব ক্লিপ, অডিও, সাবটাইটেল, মিউজিক একত্রে মিলিয়ে ফাইনাল ভিডিও তৈরি করে।
    কাস্টম অডিও আপলোড অথবা AI ভয়েসওভার সাপোর্ট করে।
    """
    scenes = script_data.get("scenes", [])
    if not scenes:
        raise ValueError("স্ক্রিপ্টে কোনো সিন নেই।")
        
    aspect_cfg = ASPECT_RATIOS.get(aspect_ratio_key, ASPECT_RATIOS["Shorts / Reels (9:16)"])
    width = aspect_cfg["width"]
    height = aspect_cfg["height"]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    total_scenes = len(scenes)
    
    scene_durations = []
    dialogues = []
    all_word_timings = []
    current_time = 0.0

    # 1. Check if user provided custom voiceover audio upload
    if custom_audio_path and Path(custom_audio_path).exists():
        if progress_callback:
            progress_callback(20, "কাস্টম আপলোডকৃত ভয়েসওভার ও সাবটাইটেল নিখুঁত সিঙ্ক করা হচ্ছে...")
            
        master_voice_audio = Path(custom_audio_path)
        
        # High-accuracy AI + acoustic alignment for uploaded voice
        aligned_result = align_audio_with_script(
            audio_path=master_voice_audio,
            scenes=scenes,
            progress_callback=progress_callback
        )
        
        scene_durations = [max(1.5, st["duration"]) for st in aligned_result["scene_timings"]]
        dialogues = aligned_result["scene_timings"]
        all_word_timings = aligned_result["word_timings"]
        current_time = aligned_result["total_duration"]
            
    else:
        # Generate Voiceover for each scene using Edge-TTS with selected tone/pitch/rate
        scene_audios = []
        for idx, scene in enumerate(scenes):
            if progress_callback:
                progress_callback(10 + int((idx / total_scenes) * 30), f"ভয়েসওভার তৈরি হচ্ছে (সিন {idx+1}/{total_scenes})...")
                
            vo_text = scene.get("voiceover_text", "").strip()
            sub_text = scene.get("subtitle_text", vo_text).strip()
            
            audio_filename = f"scene_audio_{idx:03d}_{timestamp}.mp3"
            audio_result = generate_speech(
                text=vo_text,
                output_filename=audio_filename,
                voice=voice_name,
                rate=tts_rate,
                pitch=tts_pitch
            )
            audio_path = Path(audio_result["audio_path"])
            duration = max(2.5, audio_result["duration"])
            
            # Record exact word-level boundaries for dynamic karaoke
            w_timings = audio_result.get("word_timings", [])
            for wt in w_timings:
                all_word_timings.append({
                    "word": wt["word"],
                    "start": current_time + wt["start"],
                    "end": current_time + wt["end"],
                    "duration": wt["duration"]
                })
            
            scene_audios.append(audio_path)
            scene_durations.append(duration)
            
            dialogues.append({
                "start": current_time,
                "end": current_time + duration,
                "text": sub_text
            })
            current_time += duration

        # Combine scene audios into one master voiceover track
        if progress_callback:
            progress_callback(45, "অডিও ট্র্যাক একত্রিত করা হচ্ছে...")
            
        concat_audio_list = TEMP_DIR / f"audio_concat_{timestamp}.txt"
        master_voice_audio = TEMP_DIR / f"master_voice_{timestamp}.mp3"
        
        with open(concat_audio_list, "w", encoding="utf-8") as f_a:
            for a_path in scene_audios:
                f_a.write(f"file '{str(a_path.resolve())}'\n")
                
        import subprocess
        cmd_concat_audio = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_audio_list),
            "-c", "copy",
            str(master_voice_audio)
        ]
        subprocess.run(cmd_concat_audio, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    
    # 3. Generate Word-by-Word Karaoke Subtitles (White text, vibrant pink mark on active spoken word)
    if progress_callback:
        progress_callback(55, "কারাওকে সাবটাইটেল (পিঙ্ক হাইলাইট ও সাদা ফন্ট) তৈরি করা হচ্ছে...")
        
    subtitles_concat_path = None
    if all_word_timings:
        subtitles_concat_path = generate_karaoke_subtitle_track(
            word_timings=all_word_timings,
            total_duration=current_time,
            width=width,
            height=height
        )
        
    # Fallback overlays if needed
    subtitle_overlays = None
    if not subtitles_concat_path:
        sub_font_size = 46 if height > width else 42
        subtitle_overlays = generate_subtitle_png_overlays(
            dialogues=dialogues,
            width=width,
            font_size=sub_font_size
        )
    
    # 4. Resolve Background Music
    bgm_path = None
    if bgm_filename and str(bgm_filename).strip() not in ["কোনো মিউজিক নয়", "No Background Music", "None", ""]:
        p = Path(bgm_filename)
        if p.exists() and p.is_file():
            bgm_path = p
        elif (BGM_DIR / bgm_filename).exists():
            bgm_path = BGM_DIR / bgm_filename
    print(f"[Composer Agent] Resolving BGM: bgm_filename={bgm_filename} -> resolved bgm_path={bgm_path}")
            
    # 5. Assemble Video using FFmpeg Composer
    if progress_callback:
        progress_callback(70, "ভিডিও ক্লিপ ও এফেক্ট রেন্ডারিং হচ্ছে (FFmpeg)...")
        
    output_filename = f"AI_Video_Mizan_{timestamp}.mp4"
    final_output_path = OUTPUT_DIR / output_filename
    
    assemble_final_video(
        clips=video_clips,
        durations=scene_durations,
        voice_audio=master_voice_audio,
        output_path=final_output_path,
        subtitles_path=None,
        subtitle_overlays=subtitle_overlays,
        subtitles_concat_path=subtitles_concat_path,
        bgm_path=bgm_path,
        bgm_volume=bgm_volume,
        width=width,
        height=height
    )
    
    if progress_callback:
        progress_callback(100, "ভিডিও তৈরি সম্পন্ন!")
        
    return {
        "output_path": str(final_output_path),
        "filename": output_filename,
        "duration": current_time,
        "scenes_count": len(scenes)
    }
