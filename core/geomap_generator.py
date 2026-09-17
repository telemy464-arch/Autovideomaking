import os
import re
import math
import json
import hashlib
import urllib.request
import urllib.parse
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

import config

CACHE_DIR = config.TEMP_DIR / "geomap_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

GEO_ENTITIES = [
    "Afghanistan", "Albania", "Algeria", "Argentina", "Armenia", "Australia", "Austria",
    "Azerbaijan", "Bahrain", "Bangladesh", "Belarus", "Belgium", "Bhutan", "Bolivia",
    "Bosnia", "Brazil", "Bulgaria", "Canada", "Chile", "China", "Colombia", "Congo",
    "Cuba", "Cyprus", "Czech Republic", "Denmark", "Egypt", "Estonia", "Ethiopia",
    "Finland", "France", "Georgia", "Germany", "Ghana", "Greece", "Greenland",
    "Hong Kong", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland",
    "Israel", "Italy", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kuwait", "Lebanon",
    "Libya", "Malaysia", "Maldives", "Mexico", "Mongolia", "Morocco", "Myanmar",
    "Nepal", "Netherlands", "New Zealand", "Nigeria", "North Korea", "Norway", "Oman",
    "Pakistan", "Palestine", "Panama", "Peru", "Philippines", "Poland", "Portugal",
    "Qatar", "Romania", "Russia", "Saudi Arabia", "Singapore", "Somalia", "South Africa",
    "South Korea", "Spain", "Sri Lanka", "Sudan", "Sweden", "Switzerland", "Syria",
    "Taiwan", "Thailand", "Turkey", "Ukraine", "United Arab Emirates", "UAE",
    "United Kingdom", "UK", "United States", "USA", "Uzbekistan", "Vatican", "Venezuela",
    "Vietnam", "Yemen", "Zimbabwe",
    "Africa", "Asia", "Europe", "North America", "South America", "Antarctica", "Arctic",
    "Middle East", "Balkans", "Scandinavia", "Pacific Ocean", "Atlantic Ocean", "Indian Ocean",
    "Himalayas", "Amazon", "Sahara", "Red Sea", "Black Sea", "Mediterranean", "Gaza"
]

def extract_geo_target(query: str) -> str:
    clean = query.strip()
    for entity in GEO_ENTITIES:
        if re.search(rf"\b{re.escape(entity)}\b", clean, re.IGNORECASE):
            return entity
            
    tokens_to_remove = [
        "satellite", "earth", "map", "3d", "globe", "geopolitical", "animation",
        "border", "zoom", "view", "aerial", "footage", "cinematic", "drone", "4k"
    ]
    words = clean.split()
    filtered = [w for w in words if w.lower() not in tokens_to_remove]
    if filtered:
        candidate = " ".join(filtered[:3])
        return candidate.title()
        
    return "Earth"

def geocode_location(location_name: str) -> dict:
    cache_key = hashlib.md5(location_name.strip().lower().encode("utf-8")).hexdigest()
    cache_file = CACHE_DIR / f"geocode_{cache_key}.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(location_name)}&format=json&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "MizanGeoVideoStudio/2.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data:
                res = {
                    "name": location_name,
                    "lat": float(data[0]["lat"]),
                    "lon": float(data[0]["lon"]),
                    "bbox": [float(x) for x in data[0]["boundingbox"]]
                }
                cache_file.write_text(json.dumps(res), encoding="utf-8")
                return res
    except Exception as e:
        print(f"[Geocode Error for {location_name}] {e}")

    return {
        "name": location_name,
        "lat": 20.0,
        "lon": 0.0,
        "bbox": [-50.0, 70.0, -140.0, 140.0]
    }

def fetch_satellite_imagery(
    location_name: str,
    orientation: str = "portrait",
    google_maps_api_key: str = None
) -> tuple[Path, dict]:
    geo_info = geocode_location(location_name)
    lat = geo_info["lat"]
    lon = geo_info["lon"]
    bbox = geo_info["bbox"]
    
    img_key = hashlib.md5(f"{location_name}_{lat}_{lon}_{orientation}".encode("utf-8")).hexdigest()
    sat_img_path = CACHE_DIR / f"sat_{img_key}.png"
    
    if sat_img_path.exists() and sat_img_path.stat().st_size > 10000:
        return sat_img_path, geo_info

    # 1. Try Google Maps Static API if key exists
    if google_maps_api_key:
        try:
            g_url = (
                f"https://maps.googleapis.com/maps/api/staticmap?"
                f"center={lat},{lon}&zoom=6&size=640x640&scale=2&maptype=satellite"
                f"&key={google_maps_api_key}"
            )
            req = urllib.request.Request(g_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    sat_img_path.write_bytes(resp.read())
                    return sat_img_path, geo_info
        except Exception as e:
            print(f"[Google Maps Static API Error] {e}")

    # 2. Try Esri World Imagery (ArcGIS Global Satellite)
    try:
        minlat, maxlat, minlon, maxlon = bbox
        lat_span = max(1.0, maxlat - minlat)
        lon_span = max(1.0, maxlon - minlon)
        pad_lat = lat_span * 0.45
        pad_lon = lon_span * 0.45
        
        req_minlat = max(-85.0, minlat - pad_lat)
        req_maxlat = min(85.0, maxlat + pad_lat)
        req_minlon = max(-180.0, minlon - pad_lon)
        req_maxlon = min(180.0, maxlon + pad_lon)
        
        width = 1920
        height = 1080 if orientation == "landscape" else 1920
        
        esri_url = (
            f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?"
            f"bbox={req_minlon:.4f},{req_minlat:.4f},{req_maxlon:.4f},{req_maxlat:.4f}"
            f"&bboxSR=4326&imageSR=4326&size={width},{height}&f=image"
        )
        req = urllib.request.Request(esri_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            if len(content) > 10000:
                sat_img_path.write_bytes(content)
                return sat_img_path, geo_info
    except Exception as e:
        print(f"[Esri Satellite Imagery Error] {e}")

    width, height = (1080, 1920) if orientation == "portrait" else (1920, 1080)
    img = Image.new("RGB", (width, height), color=(10, 15, 25))
    draw = ImageDraw.Draw(img)
    for x in range(0, width, 120):
        draw.line([(x, 0), (x, height)], fill=(25, 40, 60), width=1)
    for y in range(0, height, 120):
        draw.line([(0, y), (width, y)], fill=(25, 40, 60), width=1)
    cx, cy = width // 2, height // 2
    for r in [150, 300, 450, 600]:
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=(0, 200, 255), width=2)
    img.save(sat_img_path, "PNG")
    return sat_img_path, geo_info

def generate_geomap_clip(
    query_or_location: str,
    orientation: str = "portrait",
    duration: float = 6.0,
    google_maps_api_key: str = None
) -> Path:
    target_name = extract_geo_target(query_or_location)
    sat_img, geo_info = fetch_satellite_imagery(target_name, orientation, google_maps_api_key)
    
    out_w, out_h = (1080, 1920) if orientation == "portrait" else (1920, 1080)
    clip_id = hashlib.md5(f"{target_name}_{orientation}_{duration}".encode("utf-8")).hexdigest()[:10]
    out_path = config.TEMP_DIR / f"geomap_{clip_id}.mp4"
    
    if out_path.exists() and out_path.stat().st_size > 10000:
        return out_path

    lat = geo_info.get("lat", 24.0)
    lon = geo_info.get("lon", 90.0)
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    display_title = f"TARGET: {target_name.upper()}"
    coords_text = f"LAT: {abs(lat):.2f}° {lat_dir}  |  LON: {abs(lon):.2f}° {lon_dir}  |  SATELLITE 3D"

    escaped_title = display_title.replace(":", "\:").replace("'", "")
    escaped_coords = coords_text.replace(":", "\:").replace("'", "")

    total_frames = int(duration * 25)
    zoom_step = 0.0016

    vf_filters = [
        f"scale={out_w}:{out_h}:force_original_aspect_ratio=increase,crop={out_w}:{out_h}",
        f"zoompan=z='min(zoom+{zoom_step},1.38)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={out_w}x{out_h}:fps=25",
        f"drawtext=text='{escaped_title}':fontcolor=white:fontsize=38:x=(w-text_w)/2:y=130:box=1:boxcolor=black@0.65:boxborderw=10",
        f"drawtext=text='{escaped_coords}':fontcolor=0x00FFCC:fontsize=22:x=(w-text_w)/2:y=195:box=1:boxcolor=black@0.65:boxborderw=6",
        "format=yuv420p"
    ]
    vf_string = ",".join(vf_filters)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(sat_img),
        "-vf", vf_string,
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        str(out_path)
    ]

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return out_path
    except Exception as e:
        print(f"[GeoMap Clip Generation Error] {e}")
        fallback_file = "fallback_portrait.mp4" if orientation == "portrait" else "fallback_landscape.mp4"
        return config.TEMPLATES_DIR / fallback_file
