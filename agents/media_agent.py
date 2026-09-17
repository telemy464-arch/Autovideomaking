import os
from pathlib import Path
from core.pexels_pixabay import get_media_clip
from config import get_pexels_api_key, get_pixabay_api_key

def collect_media_for_scenes(
    scenes: list,
    orientation: str = "portrait",
    pexels_key: str = None,
    pixabay_key: str = None,
    visual_style: str = "realistic",
    google_maps_key: str = None,
    fal_key: str = None,
    progress_callback = None
) -> list:
    """
    Agent 3: Media Collector
    Collects stock footage or generates AI/Geo-Map animation clips scene-by-scene via Fal.ai.
    """
    collected_clips = []
    total = len(scenes)
    
    p_key = pexels_key or get_pexels_api_key()
    pix_key = pixabay_key or get_pixabay_api_key()
    g_key = google_maps_key
    f_key = fal_key or config.get_fal_key()
    
    query_clip_cache = {}
    max_unique_downloads = total
    
    for i, scene in enumerate(scenes):
        query = scene.get("visual_keyword", "nature landscape calm").strip()
        desc_bn = scene.get("visual_description_bn", "")
        
        if query in query_clip_cache:
            collected_clips.append(query_clip_cache[query])
            continue
            
        if len(query_clip_cache) >= max_unique_downloads:
            # Reuse from the collected high-quality pool
            cached_list = list(query_clip_cache.values())
            reuse_clip = cached_list[i % len(cached_list)]
            collected_clips.append(reuse_clip)
            continue
            
        if progress_callback:
            progress_callback(len(query_clip_cache) + 1, max_unique_downloads, f"Collecting media ({len(query_clip_cache)+1}/{max_unique_downloads}): {query}")
            
        clip_path = get_media_clip(
            query=query,
            orientation=orientation,
            pexels_key=p_key,
            pixabay_key=pix_key,
            visual_style=visual_style,
            google_maps_key=g_key,
            fal_key=f_key
        )
        
        if clip_path and Path(clip_path).exists():
            clip_p = Path(clip_path)
            query_clip_cache[query] = clip_p
            collected_clips.append(clip_p)
        else:
            from config import TEMPLATES_DIR
            template_name = "fallback_portrait.mp4" if orientation == "portrait" else "fallback_landscape.mp4"
            fallback_p = TEMPLATES_DIR / template_name
            collected_clips.append(fallback_p)
            
    return collected_clips
