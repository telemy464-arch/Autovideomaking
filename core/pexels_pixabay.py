import os
import requests
import hashlib
from pathlib import Path
from config import TEMP_DIR, TEMPLATES_DIR, get_pexels_api_key, get_pixabay_api_key

CACHE_DIR = TEMP_DIR / "video_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def fetch_pexels_video(query: str, orientation: str = "portrait", api_key: str = None) -> str:
    """Fetches a video download URL from Pexels API"""
    key = api_key or get_pexels_api_key()
    if not key:
        return None

    pex_orientation = "portrait" if orientation == "portrait" else "landscape"
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=8&orientation={pex_orientation}"
    headers = {"Authorization": key}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            videos = data.get("videos", [])
            for v in videos:
                # Find best 1080p or 720p file
                files = v.get("video_files", [])
                # Sort descending by width
                files_sorted = sorted(files, key=lambda x: x.get("width", 0), reverse=True)
                for vf in files_sorted:
                    if vf.get("link") and vf.get("file_type") == "video/mp4":
                        return vf.get("link")
    except Exception as e:
        print(f"[Pexels Error] {e}")
    return None

def fetch_pixabay_video(query: str, orientation: str = "portrait", api_key: str = None, video_type: str = None) -> str:
    """Fetches a video download URL from Pixabay API with optional animation video_type filter"""
    key = api_key or get_pixabay_api_key()
    if not key:
        return None

    pix_orientation = "vertical" if orientation == "portrait" else "horizontal"
    vtype_param = f"&video_type={video_type}" if video_type else ""
    url = f"https://pixabay.com/api/videos/?key={key}&q={query}&orientation={pix_orientation}{vtype_param}&per_page=8"

    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            hits = data.get("hits", [])
            for h in hits:
                v_sizes = h.get("videos", {})
                # prefer large (HD/4K) then medium
                for size in ["large", "medium", "small"]:
                    if size in v_sizes and v_sizes[size].get("url"):
                        return v_sizes[size]["url"]
    except Exception as e:
        print(f"[Pixabay Error] {e}")
    return None

def download_video_file(url: str, filename_prefix: str = "clip") -> Path:
    """Downloads video from URL with caching based on URL hash"""
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:10]
    out_path = CACHE_DIR / f"{filename_prefix}_{url_hash}.mp4"
    
    if out_path.exists() and out_path.stat().st_size > 10000:
        return out_path
        
    try:
        r = requests.get(url, stream=True, timeout=20)
        if r.status_code == 200:
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 512):
                    if chunk:
                        f.write(chunk)
            return out_path
    except Exception as e:
        print(f"[Download Error] {e}")
    return None

def generate_motion_clip_for_prompt(prompt: str, orientation: str = "portrait", duration: float = 6.0) -> Path:
    """
    Generates an animated HD motion video clip based on the prompt's theme
    when stock footage cannot be matched.
    """
    import subprocess
    prompt_lower = prompt.lower()
    url_hash = hashlib.md5(f"gen_{prompt}_{orientation}".encode("utf-8")).hexdigest()[:10]
    out_path = CACHE_DIR / f"ai_gen_{url_hash}.mp4"
    if out_path.exists() and out_path.stat().st_size > 10000:
        return out_path
        
    width, height = (1080, 1920) if orientation == "portrait" else (1920, 1080)
    
    # Theme color palettes based on prompt semantics
    if any(w in prompt_lower for w in ["tech", "ai", "robot", "future", "cyber", "code", "digital", "data"]):
        c0, c1 = "0x050814", "0x0284c7"  # Deep navy to cyber cyan
    elif any(w in prompt_lower for w in ["space", "galaxy", "star", "universe", "cosmic", "black hole", "moon"]):
        c0, c1 = "0x0b0217", "0x6366f1"  # Deep space to electric indigo
    elif any(w in prompt_lower for w in ["nature", "forest", "green", "river", "tree", "garden", "earth"]):
        c0, c1 = "0x022c22", "0x10b981"  # Forest green to emerald
    elif any(w in prompt_lower for w in ["money", "gold", "finance", "rich", "wealth", "cash", "bank"]):
        c0, c1 = "0x1c1917", "0xd97706"  # Dark carbon to rich gold/amber
    elif any(w in prompt_lower for w in ["love", "heart", "health", "life", "peace", "calm", "meditation"]):
        c0, c1 = "0x1e1b4b", "0xec4899"  # Soothing purple to rose
    else:
        c0, c1 = "0x0f172a", "0x334155"  # Sleek cinematic slate
        
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"gradients=s={width}x{height}:c0={c0}:c1={c1}:x0=150:y0=150:x1={width-150}:y1={height-150}:duration={duration}:speed=0.03",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        str(out_path)
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return out_path
    except Exception as e:
        print(f"[Motion Gen Error] {e}")
        
    fallback_file = "fallback_portrait.mp4" if orientation == "portrait" else "fallback_landscape.mp4"
    return TEMPLATES_DIR / fallback_file

def get_media_clip(
    query: str,
    orientation: str = "portrait",
    pexels_key: str = None,
    pixabay_key: str = None,
    visual_style: str = "realistic",
    google_maps_key: str = None,
    fal_key: str = None
) -> Path:
    """
    End-to-end media collector supporting visual styles (Geo Map, Cartoon, Stickman, Realistic, Cyberpunk):
    - For geomap: Searches 3D Earth, satellite & map animations, with real satellite zoom clip generation!
    - For cartoon/stickman: Prioritizes Pixabay animation engine + stylized cartoon searches
    - For realistic/cyberpunk: Prioritizes Pexels 4K footage + Pixabay HD
    - AI Fallback: If no stock footage matches, automatically generates custom AI video via Fal.ai!
    - Final Fallback: Procedural motion video clip or template.
    """
    clean_query = query.replace("-", " ").replace("_", " ").strip()
    is_animation_style = visual_style in ["cartoon", "stickman"]
    is_geomap_style = visual_style == "geomap"
    
    if is_geomap_style:
        # 1. Try Pexels for 3D earth / map animations
        geo_query = f"{clean_query} satellite earth 3d map animation"
        url = fetch_pexels_video(geo_query, orientation, pexels_key)
        if url:
            path = download_video_file(url, "pexels_geomap")
            if path:
                return path

        # 2. Try Pixabay with map query
        url = fetch_pixabay_video(f"{clean_query} map animation earth", orientation, pixabay_key)
        if url:
            path = download_video_file(url, "pixabay_geomap")
            if path:
                return path

        # 3. Direct Real Satellite Map Zoom Generator (Google Earth / Esri World Satellite)
        try:
            from core.geomap_generator import generate_geomap_clip
            g_key = google_maps_key or config.get_google_maps_api_key()
            geomap_clip = generate_geomap_clip(clean_query, orientation, duration=8.0, google_maps_api_key=g_key)
            if geomap_clip and Path(geomap_clip).exists():
                return Path(geomap_clip)
        except Exception as e:
            print(f"[GeoMap Generator Fallback Error] {e}")

    elif is_animation_style:
        # 1. Try Pixabay with animation filter first
        pix_vtype = "animation"
        url = fetch_pixabay_video(clean_query, orientation, pixabay_key, video_type=pix_vtype)
        if url:
            path = download_video_file(url, f"pixabay_{visual_style}")
            if path:
                return path
                
        # 2. Try Pexels with animation search query
        anim_query = f"{clean_query} animation cartoon" if visual_style == "cartoon" else f"{clean_query} stickman animation doodle"
        url = fetch_pexels_video(anim_query, orientation, pexels_key)
        if url:
            path = download_video_file(url, f"pexels_{visual_style}")
            if path:
                return path
    else:
        # 1. Try Pexels first (4K realistic)
        url = fetch_pexels_video(clean_query, orientation, pexels_key)
        if url:
            path = download_video_file(url, "pexels")
            if path:
                return path
                
        # 2. Try Pixabay next (Large/HD prioritized)
        url = fetch_pixabay_video(clean_query, orientation, pixabay_key)
        if url:
            path = download_video_file(url, "pixabay")
            if path:
                return path
            
    # 3. Fal.ai Generative AI Fallback: Generate 4K AI scene video if stock footage not found!
    try:
        from core.fal_engine import generate_fal_flux_clip
        f_key = fal_key or config.get_fal_key()
        if f_key:
            fal_clip = generate_fal_flux_clip(
                prompt=clean_query,
                orientation=orientation,
                duration=8.0,
                visual_style=visual_style,
                fal_key=f_key
            )
            if fal_clip and Path(fal_clip).exists():
                return Path(fal_clip)
    except Exception as e:
        print(f"[Fal.ai Generative Fallback Error] {e}")

    # 4. If AI footage cannot be generated, generate motion video clip according to prompt!
    generated_path = generate_motion_clip_for_prompt(clean_query, orientation, duration=8.0)
    if generated_path and Path(generated_path).exists():
        return Path(generated_path)
        
    fallback_file = "fallback_portrait.mp4" if orientation == "portrait" else "fallback_landscape.mp4"
    return TEMPLATES_DIR / fallback_file

