import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
BGM_DIR = ASSETS_DIR / "bgm"
TEMPLATES_DIR = ASSETS_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

# Create required directories if they don't exist
for folder in [OUTPUT_DIR, TEMP_DIR, FONTS_DIR, BGM_DIR, TEMPLATES_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# App Metadata
APP_NAME = "Mizan AI Video Studio"
APP_TAGLINE = "Autonomous AI Video Creator • Ultra-Fast • Grok Edition"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Mizan"

def _get_key_from_env_or_secrets(key_name: str) -> str:
    val = os.getenv(key_name, "").strip()
    if not val:
        try:
            import streamlit as st
            val = str(st.secrets.get(key_name, "")).strip()
        except Exception:
            pass
    return val

# API Keys
def get_gemini_api_key():
    return _get_key_from_env_or_secrets("GEMINI_API_KEY")

def get_pexels_api_key():
    return _get_key_from_env_or_secrets("PEXELS_API_KEY")

def get_pixabay_api_key():
    return _get_key_from_env_or_secrets("PIXABAY_API_KEY")

def get_google_maps_api_key():
    return _get_key_from_env_or_secrets("GOOGLE_MAPS_API_KEY")

def get_fal_key():
    return _get_key_from_env_or_secrets("FAL_KEY")

# Visual Styles & Animation Modes
VISUAL_STYLES = {
    "🗺️ Geo Map Style Video": {
        "id": "geomap",
        "description": "Google Earth 3D zoom, geopolitical world maps, satellite aerials, and animated country borders.",
        "search_modifier": "satellite earth map 3d globe geopolitical animation",
        "video_type": "all"
    },
    "🎬 Realistic 4K Cinematic": {
        "id": "realistic",
        "description": "Live action realistic 4K stock footage with cinematic lighting and documentary feel.",
        "search_modifier": "cinematic 4k realistic",
        "video_type": "film"
    },
    "🎨 3D & 2D Cartoon Animation": {
        "id": "cartoon",
        "description": "Vibrant 3D/2D animated cartoon characters, Pixar/Disney style colorful motion.",
        "search_modifier": "cartoon 3d animation character",
        "video_type": "animation"
    },
    "✏️ Stickman & Doodle Animation": {
        "id": "stickman",
        "description": "Minimalist stick figure, whiteboard sketch, hand-drawn doodle animation storytelling.",
        "search_modifier": "stickman animation stick figure whiteboard doodle",
        "video_type": "animation"
    },
    "🤖 Cyberpunk & Futuristic Sci-Fi": {
        "id": "cyberpunk",
        "description": "Neon holographic glowing visual style, futuristic AI robot cyber aesthetic.",
        "search_modifier": "cyberpunk futuristic neon technology sci-fi 4k",
        "video_type": "all"
    }
}

# Edge-TTS Bengali & English Voices
VOICES = {
    "🇧🇩 Bengali - Nabanita (Female)": "bn-BD-NabanitaNeural",
    "🇧🇩 Bengali - Pradeep (Male)": "bn-BD-PradeepNeural",
    "🇮🇳 Bengali - Tanisha (Female)": "bn-IN-TanishaaNeural",
    "🇮🇳 Bengali - Bashkar (Male)": "bn-IN-BashkarNeural",
    "🇺🇸 English US - Jenny (Female)": "en-US-JennyNeural",
    "🇺🇸 English US - Guy (Male)": "en-US-GuyNeural",
    "🇺🇸 English US - Christopher (Deep Male)": "en-US-ChristopherNeural",
    "🇬🇧 English UK - Sonia (Female)": "en-GB-SoniaNeural",
    "🇬🇧 English UK - Ryan (Male)": "en-GB-RyanNeural",
}

# Video Dimensions & Ratios
ASPECT_RATIOS = {
    "Shorts / Reels (9:16)": {"width": 1080, "height": 1920, "orientation": "portrait"},
    "YouTube Video (16:9)": {"width": 1920, "height": 1080, "orientation": "landscape"},
}

# Default font candidates in order of preference
DEFAULT_FONT_PATH = None
for candidate in [
    FONTS_DIR / "NotoSansBengali.ttf",
    FONTS_DIR / "NirmalaB.ttf",
    FONTS_DIR / "Nirmala.ttf",
    Path(r"C:\Windows\Fonts\Nirmala.ttf"),
]:
    if candidate.exists():
        DEFAULT_FONT_PATH = str(candidate).replace("\\", "/")
        break

# Categorized Background Music Library (25 Tracks)
BGM_CATEGORIES = {
    "🎓 Educational (শিক্ষামূলক ও বিজ্ঞান)": [
        ("Curious Mind (চিন্তাশীল ও শান্ত)", "educational_curious_mind.mp3"),
        ("Documentary Clarity (পরিষ্কার ডকুমেন্টারি)", "educational_documentary_clarity.mp3"),
        ("Science Discovery (বিজ্ঞান ও উদ্ভাবন)", "educational_science_discovery.mp3"),
        ("Focus Study (মনোযোগ ও পড়াশোনা)", "educational_focus_study.mp3"),
    ],
    "👻 Horror (ভৌতিক ও রহস্যময়)": [
        ("Dark Suspense (গভীর ভয় ও সাসপেন্স)", "horror_dark_suspense.mp3"),
        ("Creepy Ambience (ভুতুড়ে পরিবেশ)", "horror_creepy_ambience.mp3"),
        ("Spooky Nightmare (আতঙ্ক ও দুঃস্বপ্ন)", "horror_spooky_nightmare.mp3"),
        ("Thriller Chase (রোমাঞ্চকর তাড়া)", "horror_thriller_chase.mp3"),
    ],
    "🔥 Motivational (অনুপ্রেরণামূলক ও সাফল্য)": [
        ("Uplifting Drive (সাফল্যের উদ্দীপনা)", "motivational_uplifting_drive.mp3"),
        ("Epic Triumph (বিজয়ের মহাকাব্য)", "motivational_epic_triumph.mp3"),
        ("Champion Energy (চ্যাম্পিয়ন এনার্জি)", "motivational_champion_energy.mp3"),
        ("Limitless Potential (সীমাহীন আত্মবিশ্বাস)", "motivational_limitless_potential.mp3"),
        ("Inspiring Cinematic (অনুপ্রেরণাদায়ী সিনেমাটিক)", "inspiring_cinematic.mp3"),
    ],
    "🧭 Exploring (ভ্রমণ ও অ্যাডভেঞ্চার)": [
        ("Wild Journey (বুনো ভ্রমণ ও রোমাঞ্চ)", "exploring_wild_journey.mp3"),
        ("Adventure Expedition (অভিযান ও নতুন দিগন্ত)", "exploring_adventure_expedition.mp3"),
        ("Nature Wonder (প্রকৃতির বিস্ময়)", "exploring_nature_wonder.mp3"),
        ("Lost Horizons (হারিয়ে যাওয়া সীমানা)", "exploring_lost_horizons.mp3"),
    ],
    "🌍 Geofact (ভূগোল, ইতিহাস ও রাজনীতি)": [
        ("World History (বিশ্ব ইতিহাস ও ঐতিহ্য)", "geofact_world_history.mp3"),
        ("Ancient Civilization (প্রাচীন সভ্যতা ও রহস্য)", "geofact_ancient_civilization.mp3"),
        ("Global Strategy (আন্তর্জাতিক কূটনীতি ও স্ট্র্যাটেজি)", "geofact_global_strategy.mp3"),
        ("Historic Chronicles (ঐতিহাসিক কাহিনী)", "geofact_historic_chronicles.mp3"),
    ],
    "🧘 Chill / Lofi / Cinematic (শান্ত ও আধুনিক)": [
        ("Lofi Chill (লুফি শান্ত সুর)", "lofi_chill.mp3"),
        ("Ambient Calm (রিলাক্সিং পিস)", "ambient_calm.mp3"),
        ("Emotional Piano (আবেগঘন পিয়ানো)", "cinematic_emotional_piano.mp3"),
        ("Cyber Tech Future (ভবিষ্যত প্রযুক্তি ও সাইবার)", "cyber_tech_future.mp3"),
    ]
}
