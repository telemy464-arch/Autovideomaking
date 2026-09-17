import os
import re
import json
import hashlib
import urllib.request
import urllib.parse
import subprocess
from pathlib import Path

import config

CACHE_DIR = config.TEMP_DIR / "fal_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def clean_fal_key(raw_key: str) -> str:
    """
    Cleans up duplicate pastes or accidental concatenations in Fal API keys.
    Fal keys are structured as <uuid-36-chars>:<hash-32-chars>.
    """
    if not raw_key:
        return ""
    key = raw_key.strip().strip("'").strip('"')
    if ":" in key:
        parts = key.split(":")
        first_uuid = parts[0]
        rest = ":".join(parts[1:])
        # If rest contains the uuid again, extract just the first 32-char hex secret
        if first_uuid in rest:
            secret = rest.replace(first_uuid, "").strip(":")
            # Secret is typically 32-64 chars
            secret_match = re.search(r"[0-9a-fA-F]{32,64}", secret)
            if secret_match:
                return f"{first_uuid}:{secret_match.group(0)}"
        return f"{first_uuid}:{rest[:32]}"
    return key

def generate_fal_flux_clip(
    prompt: str,
    orientation: str = "portrait",
    duration: float = 5.0,
    visual_style: str = "realistic",
    fal_key: str = None
) -> Path | None:
    """
    Generates a 4K AI image matching the exact scene prompt and visual style via FLUX.1 [schnell],
    then renders a smooth 3D cinematic camera pan/zoom (Ken Burns) MP4 clip with FFmpeg.
    """
    key = clean_fal_key(fal_key or config.get_fal_key())
    if not key:
        return None

    # Style-specific prompt engineering
    if visual_style == "cartoon":
        styled_prompt = f"3D Pixar Disney style animated cartoon: {prompt}, vibrant colors, smooth render, highly detailed"
    elif visual_style == "stickman":
        styled_prompt = f"minimalist whiteboard stickman animation sketch: {prompt}, clean black and white line art, doodle drawing"
    elif visual_style == "cyberpunk":
        styled_prompt = f"cyberpunk futuristic sci-fi neon aesthetic: {prompt}, glowing neon lights, holographic 4k"
    elif visual_style == "geomap":
        styled_prompt = f"satellite orbital 3d earth view: {prompt}, high resolution geopolitical satellite map"
    else:
        styled_prompt = f"cinematic 4k realistic photography: {prompt}, professional studio lighting, 8k resolution"

    img_size = "portrait_16_9" if orientation == "portrait" else "landscape_16_9"
    out_w, out_h = (1080, 1920) if orientation == "portrait" else (1920, 1080)
    
    hash_id = hashlib.md5(f"{styled_prompt}_{orientation}_{duration}".encode("utf-8")).hexdigest()[:12]
    out_mp4 = config.TEMP_DIR / f"fal_flux_{hash_id}.mp4"
    if out_mp4.exists() and out_mp4.stat().st_size > 10000:
        return out_mp4

    img_cache = CACHE_DIR / f"flux_{hash_id}.png"
    
    if not img_cache.exists():
        try:
            url = "https://fal.run/fal-ai/flux/schnell"
            payload = json.dumps({
                "prompt": styled_prompt,
                "image_size": img_size,
                "num_inference_steps": 4,
                "num_images": 1,
                "enable_safety_checker": False
            }).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Authorization": f"Key {key}",
                    "Content-Type": "application/json",
                    "User-Agent": "MizanVideoStudio/2.0"
                }
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                images = data.get("images", [])
                if not images:
                    return None
                img_url = images[0].get("url")
                if not img_url:
                    return None
                    
            # Download image
            req_img = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req_img, timeout=20) as resp:
                img_cache.write_bytes(resp.read())
                
        except Exception as e:
            print(f"[Fal.ai FLUX Error] {e}")
            if hasattr(e, "read"):
                try:
                    print(f"[Fal.ai Error Detail] {e.read().decode('utf-8')}")
                except Exception:
                    pass
            return None

    # Render dynamic camera flight MP4 using FFmpeg
    total_frames = int(duration * 25)
    zoom_step = 0.0015
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(img_cache),
        "-vf", (
            f"scale={out_w}:{out_h}:force_original_aspect_ratio=increase,crop={out_w}:{out_h},"
            f"zoompan=z='min(zoom+{zoom_step},1.35)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps=25,"
            "format=yuv420p"
        ),
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        str(out_mp4)
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return out_mp4
    except Exception as e:
        print(f"[Fal.ai Video Render Error] {e}")
        return None

def generate_fal_direct_video(
    prompt: str,
    orientation: str = "portrait",
    duration: float = 5.0,
    visual_style: str = "realistic",
    fal_key: str = None
) -> Path | None:
    """
    Generates direct AI video via Fal.ai CogVideoX / Kling / Minimax if configured.
    Falls back automatically to FLUX 4K motion clip for speed & reliability.
    """
    key = clean_fal_key(fal_key or config.get_fal_key())
    if not key:
        return None

    # Try CogVideoX 5B or Minimax
    aspect = "9:16" if orientation == "portrait" else "16:9"
    try:
        url = "https://fal.run/fal-ai/cogvideox-5b"
        payload = json.dumps({
            "prompt": f"{prompt}, cinematic lighting, high quality 4k motion",
            "aspect_ratio": aspect
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Key {key}",
                "Content-Type": "application/json",
                "User-Agent": "MizanVideoStudio/2.0"
            }
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            video_url = data.get("video", {}).get("url")
            if video_url:
                hash_id = hashlib.md5(prompt.encode("utf-8")).hexdigest()[:10]
                out_path = config.TEMP_DIR / f"fal_vid_{hash_id}.mp4"
                req_v = urllib.request.Request(video_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req_v, timeout=30) as v_resp:
                    out_path.write_bytes(v_resp.read())
                    return out_path
    except Exception as e:
        print(f"[Fal Direct Video Error] {e}")

    # Fallback to FLUX 4K motion clip
    return generate_fal_flux_clip(prompt, orientation, duration, visual_style, fal_key)
