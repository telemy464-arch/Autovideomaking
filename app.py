import streamlit as st
import os
import time
import threading
from pathlib import Path
from dotenv import load_dotenv, set_key
import requests as _req

# Load environment variables
load_dotenv(override=True)

# ── Live Global User / Usage Tracker ──────────────────────────────────────────
def _get_live_count() -> int:
    """Increment and fetch global user launch / visit count."""
    import re
    # Tracker 1: visitor-badge
    try:
        r = _req.get("https://visitor-badge.laobi.icu/badge?page_id=mizanai.video.studio", timeout=3.5)
        if r.status_code == 200:
            nums = re.findall(r'>(\d+)<', r.text)
            if nums:
                return int(nums[0])
    except Exception:
        pass

    # Tracker 2: komarev fallback
    try:
        r = _req.get("https://komarev.com/ghpvc/?username=mizanai-video-studio", timeout=3.5)
        if r.status_code == 200:
            nums = re.findall(r'>(\d+)<', r.text)
            if nums:
                return int(nums[0])
    except Exception:
        pass
    return 1

# Fire-and-fetch: only once per browser session
if "visitor_count" not in st.session_state or st.session_state["visitor_count"] <= 0:
    st.session_state["visitor_count"] = _get_live_count()

import config
from agents.topic_agent import generate_topics
from agents.script_agent import generate_and_check_script, auto_segment_script_into_scenes
from agents.media_agent import collect_media_for_scenes
from agents.composer_agent import compose_full_video
from core.tts_engine import VOICES, generate_speech

# Page Configuration
st.set_page_config(
    page_title="Mizan AI Video Studio • Grok Edition",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Grok AI-Inspired Custom Styling
st.markdown("""
<style>
    /* Grok AI Dark Minimalist Theme */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", Roboto, sans-serif;
    }
    
    .stApp {
        background: #09090b !important;
        color: #f4f4f5 !important;
    }
    
    /* Enforce Dark Theme on Sidebar */
    [data-testid="stSidebar"], 
    [data-testid="stSidebar"] > div:first-child,
    section[data-testid="stSidebar"] {
        background-color: #0c0e14 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
    }

    /* Widget Labels & Text Elements (High Contrast) */
    label, 
    label p,
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p,
    .stWidgetLabel,
    .stWidgetLabel p,
    .stMarkdown p,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span {
        color: #f1f5f9 !important;
        font-weight: 600 !important;
        -webkit-text-fill-color: #f1f5f9 !important;
    }
    
    /* Captions & Subtitles */
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p,
    [data-testid="stCaptionContainer"] span,
    .stCaption,
    small {
        color: #94a3b8 !important;
        -webkit-text-fill-color: #94a3b8 !important;
        font-weight: 500 !important;
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6,
    [data-testid="stHeadingWithActionElements"] {
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
    }

    /* Text Area Styling (Fixes invisible text on white background) */
    textarea,
    div[data-baseweb="textarea"],
    div[data-baseweb="textarea"] textarea {
        background-color: #111625 !important;
        color: #ffffff !important;
        border: 1px solid #2d3748 !important;
        border-radius: 12px !important;
        font-size: 0.96rem !important;
        line-height: 1.6 !important;
        -webkit-text-fill-color: #ffffff !important;
        caret-color: #38bdf8 !important;
    }

    textarea::placeholder,
    input::placeholder {
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
    }
    
    textarea:focus,
    div[data-baseweb="textarea"]:focus-within {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25) !important;
        background-color: #151b2e !important;
    }

    /* Text Inputs (Password, Text, Number) */
    input[type="text"],
    input[type="password"],
    input[type="number"],
    div[data-baseweb="input"],
    div[data-baseweb="input"] input {
        background-color: #111625 !important;
        color: #ffffff !important;
        border: 1px solid #2d3748 !important;
        border-radius: 10px !important;
        -webkit-text-fill-color: #ffffff !important;
        caret-color: #38bdf8 !important;
    }
    
    input:focus,
    div[data-baseweb="input"]:focus-within {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25) !important;
    }

    /* Selectbox & Dropdown Menus */
    div[data-baseweb="select"] > div {
        background-color: #111625 !important;
        border: 1px solid #2d3748 !important;
        border-radius: 10px !important;
        color: #ffffff !important;
    }
    
    div[data-baseweb="select"] * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    ul[role="listbox"], li[role="option"] {
        background-color: #111625 !important;
        color: #ffffff !important;
    }
    
    li[role="option"]:hover, li[aria-selected="true"] {
        background-color: #1e293b !important;
        color: #38bdf8 !important;
    }

    /* File Uploader Container & Button */
    [data-testid="stFileUploader"] {
        background-color: #111625 !important;
        border: 1px dashed rgba(56, 189, 248, 0.4) !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }
    
    [data-testid="stFileUploader"] section {
        background-color: transparent !important;
    }
    
    [data-testid="stFileUploader"] * {
        color: #e2e8f0 !important;
        -webkit-text-fill-color: #e2e8f0 !important;
    }
    
    [data-testid="stFileUploader"] button {
        background: #1e293b !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        font-weight: 600 !important;
        -webkit-text-fill-color: #38bdf8 !important;
    }

    /* Primary & Standard Buttons */
    .stButton>button, 
    .stDownloadButton>button {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%) !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 8px 18px !important;
        transition: all 0.2s ease-in-out !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    .stButton>button *, 
    .stDownloadButton>button * {
        color: inherit !important;
        -webkit-text-fill-color: inherit !important;
    }
    
    .stButton>button:hover,
    .stDownloadButton>button:hover {
        background: #2563eb !important;
        color: #ffffff !important;
        border-color: #38bdf8 !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4) !important;
        transform: translateY(-1px) !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    .stButton>button[kind="primary"],
    .stDownloadButton>button[kind="primary"] {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    .stButton>button[kind="secondary"],
    .stDownloadButton>button[kind="secondary"] {
        background: #1e293b !important;
        color: #f1f5f9 !important;
        border: 1px solid #334155 !important;
        -webkit-text-fill-color: #f1f5f9 !important;
    }

    /* Radio buttons & Sliders */
    [data-testid="stRadio"] label,
    [data-testid="stSlider"] label {
        color: #f1f5f9 !important;
        font-weight: 600 !important;
        -webkit-text-fill-color: #f1f5f9 !important;
    }

    /* Expanders */
    [data-testid="stExpander"] details {
        background: #11141f !important;
        border: 1px solid #27272a !important;
        border-radius: 12px !important;
    }
    
    [data-testid="stExpander"] summary {
        color: #f1f5f9 !important;
        font-weight: 600 !important;
        -webkit-text-fill-color: #f1f5f9 !important;
    }
    
    [data-testid="stExpander"] summary:hover {
        color: #38bdf8 !important;
    }
    
    /* Grok Header Card */
    .grok-header {
        background: radial-gradient(ellipse 80% 50% at 50% -20%, rgba(56, 189, 248, 0.15), rgba(15, 23, 42, 0) 70%),
                    linear-gradient(180deg, #111116 0%, #0c0c0f 100%);
        padding: 26px 30px;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.7);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    
    .grok-header::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, #38bdf8, #a855f7, transparent);
    }
    
    .grok-badge-super {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #38bdf8;
        background: rgba(56, 189, 248, 0.1);
        padding: 4px 10px;
        border-radius: 20px;
        border: 1px solid rgba(56, 189, 248, 0.25);
        margin-bottom: 8px;
    }
    
    .grok-title {
        font-size: 2.4rem;
        font-weight: 900;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #ffffff 30%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.15;
    }
    
    .grok-tagline {
        font-size: 1.05rem;
        color: #71717a;
        margin-top: 6px;
    }
    
    .grok-pill-bar {
        display: flex;
        gap: 10px;
        margin-top: 16px;
        flex-wrap: wrap;
    }
    
    .grok-pill {
        background: rgba(255, 255, 255, 0.04);
        padding: 5px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        color: #a1a1aa;
        border: 1px solid rgba(255, 255, 255, 0.08);
        transition: all 0.2s ease;
    }
    
    .grok-pill:hover {
        background: rgba(255, 255, 255, 0.08);
        color: #f4f4f5;
        border-color: rgba(255, 255, 255, 0.15);
    }
    
    /* Grok Card Container */
    .grok-card {
        background: #111115;
        border: 1px solid #27272a;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #111115;
        padding: 6px;
        border-radius: 14px;
        border: 1px solid #27272a;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.92rem;
        padding: 10px 18px;
        color: #a1a1aa;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(56, 189, 248, 0.12) !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
    }
    
    /* Contact Card & Buttons */
    .contact-card {
        background: linear-gradient(180deg, #141419 0%, #0d0d11 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px;
        margin-top: 10px;
        margin-bottom: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    
    .contact-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        width: 100%;
        padding: 11px 16px;
        margin-bottom: 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.88rem;
        text-decoration: none !important;
        transition: all 0.25s ease-in-out;
        box-sizing: border-box;
    }
    
    .contact-btn-wa {
        background: rgba(37, 211, 102, 0.12);
        color: #25D366 !important;
        border: 1px solid rgba(37, 211, 102, 0.3);
    }
    .contact-btn-wa:hover {
        background: #25D366;
        color: #0c0c0f !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 211, 102, 0.35);
    }
    
    .contact-btn-fb {
        background: rgba(24, 119, 242, 0.12);
        color: #3b82f6 !important;
        border: 1px solid rgba(24, 119, 242, 0.3);
    }
    .contact-btn-fb:hover {
        background: #1877F2;
        color: #ffffff !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(24, 119, 242, 0.35);
    }
    
    .contact-btn-tg {
        background: rgba(0, 136, 204, 0.12);
        color: #38bdf8 !important;
        border: 1px solid rgba(0, 136, 204, 0.3);
    }
    .contact-btn-tg:hover {
        background: #0088cc;
        color: #ffffff !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 136, 204, 0.35);
    }
    
    /* Footer Bar */
    .grok-footer {
        background: linear-gradient(180deg, #111116 0%, #0c0c0f 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-top: 36px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .grok-footer-links {
        display: flex;
        justify-content: center;
        gap: 12px;
        flex-wrap: wrap;
        margin-top: 14px;
    }
    
    .grok-footer-link {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 18px;
        border-radius: 10px;
        font-size: 0.85rem;
        font-weight: 600;
        text-decoration: none !important;
        transition: all 0.2s ease;
    }

    /* Live User Counter Card */
    .user-counter-card {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.12) 0%, rgba(168, 85, 247, 0.08) 100%);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 8px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
    }
    .user-counter-card .uc-top {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        color: #38bdf8 !important;
        -webkit-text-fill-color: #38bdf8 !important;
        margin-bottom: 4px;
    }
    .user-counter-card .uc-number {
        font-size: 2.3rem;
        font-weight: 900;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #ffffff 30%, #38bdf8 80%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
        margin: 2px 0;
    }
    .user-counter-card .uc-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #f1f5f9 !important;
        -webkit-text-fill-color: #f1f5f9 !important;
    }
    .user-counter-card .uc-sub {
        font-size: 0.7rem;
        color: #94a3b8 !important;
        -webkit-text-fill-color: #94a3b8 !important;
        margin-top: 3px;
    }
    .uc-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #22c55e;
        border-radius: 50%;
        box-shadow: 0 0 8px rgba(34, 197, 94, 0.8);
        animation: pulse-dot 1.8s infinite;
    }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.35; transform: scale(0.7); }
    }
</style>
""", unsafe_allow_html=True)

# Brand Header Banner
st.markdown(f"""
<div class="grok-header">
    <div class="grok-badge-super">⚡ GROK MULTI-AGENT ENGINE v{config.APP_VERSION}</div>
    <div class="grok-title">{config.APP_NAME}</div>
    <div class="grok-tagline">{config.APP_TAGLINE}</div>
    <div class="grok-pill-bar">
        <span class="grok-pill">🧠 4-Agent Pipeline</span>
        <span class="grok-pill">🎨 Stickman & Cartoon Animation</span>
        <span class="grok-pill">🎙️ Precision Subtitle Audio Sync</span>
        <span class="grok-pill">🎞️ Unlimited Scenes Support</span>
        <span class="grok-pill">⚡ 4K Media Search</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    # ── Live Visitor Counter ─────────────────────────────────────
    _vc = st.session_state.get("visitor_count", 0)
    _vc_display = f"{_vc:,}" if _vc > 0 else "১"
    st.markdown(f"""
    <div class="user-counter-card">
        <div class="uc-top">
            <span class="uc-dot"></span> LIVE SYSTEM ACTIVE
        </div>
        <div class="uc-number">{_vc_display}</div>
        <div class="uc-label">মোট সক্রিয় ব্যবহারকারী / ইউজার</div>
        <div class="uc-sub">রিয়েলটাইম ক্লাউড ট্র্যাকিং দ্বারা সংযুক্ত</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 লাইভ কাউন্টার আপডেট করুন", use_container_width=True, key="btn_refresh_counter"):
        st.session_state["visitor_count"] = _get_live_count()
        st.rerun()

    st.markdown("### ⚙️ Engine Settings")

    # Built-in Engine Credentials (hidden from user)
    gemini_key = config.get_gemini_api_key()
    pexels_key = config.get_pexels_api_key()
    pixabay_key = config.get_pixabay_api_key()
    eleven_key = config.get_elevenlabs_api_key()
    google_maps_key = config.get_google_maps_api_key()
    fal_key = config.get_fal_key()

    st.markdown("""
    <div style="background: rgba(34, 197, 94, 0.08); border: 1px solid rgba(34, 197, 94, 0.25); border-radius: 12px; padding: 12px 14px; margin-bottom: 14px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="display: inline-block; width: 8px; height: 8px; background: #22c55e; border-radius: 50%; box-shadow: 0 0 8px #22c55e;"></span>
            <span style="font-size: 0.8rem; font-weight: 700; color: #22c55e; letter-spacing: 0.05em;">PREMIUM AI ENGINE ACTIVE</span>
        </div>
        <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 4px;">
            Gemini AI • Edge-TTS Free Voice • 4K Pexels/Pixabay • Ultra HD মিডিয়া রেডি
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🎨 Visual Style & Animation Mode")
    selected_style_label = st.selectbox(
        "Select Visual Style:",
        options=list(config.VISUAL_STYLES.keys()),
        index=0
    )
    selected_style_cfg = config.VISUAL_STYLES[selected_style_label]
    selected_style_id = selected_style_cfg["id"]
    st.caption(f"💡 {selected_style_cfg['description']}")

    st.markdown("---")
    st.markdown("### 🎙️ Voice & Audio Synthesis (Edge-TTS)")
    clone_sample_path = None
    clone_language = "bn"
    clone_pitch_hz = 0
    clone_speed_pct = 0
    fish_api_key = None
    fish_reference_id = None
    fish_speed = 1.0

    selected_tts_engine = "edge-tts"
    selected_eleven_model = "eleven_multilingual_v2"
    eleven_stability = 0.5
    eleven_similarity = 0.75

    voice_filter = st.radio("Voice Language Filter:", ["All Voices", "🇧🇩 Bengali", "🇺🇸/🇬🇧 English"], horizontal=True)
    if voice_filter == "🇧🇩 Bengali":
        filtered_voices = {k: v for k, v in config.VOICES.items() if v.startswith("bn-")}
    elif voice_filter == "🇺🇸/🇬🇧 English":
        filtered_voices = {k: v for k, v in config.VOICES.items() if v.startswith("en-")}
    else:
        filtered_voices = config.VOICES

    selected_voice_label = st.selectbox("Select Voice:", options=list(filtered_voices.keys()), index=0)
    selected_voice_code = filtered_voices[selected_voice_label]
    is_voice_english = selected_voice_code.startswith("en-")

    col_sp1, col_sp2 = st.columns(2)
    with col_sp1:
        speed_val = st.slider("Speech Speed Rate", min_value=-20, max_value=50, value=0, step=5, format="%d%%")
        tts_rate = f"{speed_val:+d}%"
    with col_sp2:
        pitch_val = st.slider("Speech Tone / Pitch", min_value=-10, max_value=10, value=0, step=1, format="%dHz")
        tts_pitch = f"{pitch_val:+d}Hz"

    c_prev1, c_prev2 = st.columns([2, 3])
    with c_prev1:
        if st.button("🔊 Test Spoken Voice", use_container_width=True):
            with st.spinner("ভয়েস অডিও তৈরি হচ্ছে..."):
                test_phrase = "Welcome to today's video." if is_voice_english else "আজকের ভিডিওতে আপনাদের সবাইকে স্বাগতম।"
                try:
                    prev_res = generate_speech(
                        text=test_phrase,
                        output_filename="edge_sample_preview.mp3",
                        voice=selected_voice_code,
                        rate=tts_rate,
                        pitch=tts_pitch,
                        engine="edge-tts"
                    )
                    st.audio(prev_res["audio_path"])
                except Exception as err:
                    st.error(f"Voice preview error: {err}")
    with c_prev2:
        st.caption("⚡ Edge-TTS: ১০০% ফ্রি, আনলিমিটেড এবং দ্রুত গতির প্রাকৃতিক বাংলা ও ইংরেজি ভয়েস।")

    st.markdown("---")
    st.markdown("### 📐 Video Dimensions")
    format_choice = st.radio("Aspect Ratio:", options=list(config.ASPECT_RATIOS.keys()), index=0)

    st.markdown("---")
    st.markdown("### 🎵 Background Music (BGM)")
    bgm_category = st.selectbox(
        "BGM Category:",
        ["All Tracks (25 BGM Tracks)"] + list(config.BGM_CATEGORIES.keys())
    )

    bgm_track_map = {"No Background Music": None}
    if bgm_category == "All Tracks (25 BGM Tracks)":
        for cat, tracks in config.BGM_CATEGORIES.items():
            cat_icon = cat.split()[0]
            for label, fname in tracks:
                bgm_track_map[f"{cat_icon} {label}"] = fname
    else:
        for label, fname in config.BGM_CATEGORIES[bgm_category]:
            bgm_track_map[label] = fname

    selected_bgm_label = st.selectbox("Select BGM Track:", options=list(bgm_track_map.keys()), index=min(1, len(bgm_track_map)-1))
    selected_bgm = bgm_track_map[selected_bgm_label]

    # Live Audio Preview inside expander for instant page startup
    with st.expander("🎧 Preview Selected Music", expanded=False):
        if selected_bgm and (config.BGM_DIR / selected_bgm).exists():
            st.audio(str(config.BGM_DIR / selected_bgm))

    # Custom BGM Upload
    uploaded_custom_bgm = st.file_uploader("📁 Or Upload Custom Music (.mp3, .wav):", type=["mp3", "wav"])
    if uploaded_custom_bgm is not None:
        user_bgm_path = config.TEMP_DIR / f"custom_bgm_{uploaded_custom_bgm.name}"
        with open(user_bgm_path, "wb") as f_b:
            f_b.write(uploaded_custom_bgm.getbuffer())
        selected_bgm = str(user_bgm_path)
        st.success("✅ Custom background music loaded!")

    bgm_vol_percent = st.slider(
        "Music Volume Level",
        min_value=5,
        max_value=80,
        value=28,
        step=5,
        format="%d%%",
        help="Background music loudness relative to voice. 20%-35% is ideal for clear background ambiance!"
    )
    bgm_vol = round(bgm_vol_percent / 100.0, 2)

    st.markdown("---")
    st.markdown("### 📬 Contact & Support")
    st.markdown("""
    <div class="contact-card">
        <a href="https://wa.me/8801737929107" target="_blank" rel="noopener noreferrer" class="contact-btn contact-btn-wa">
            💬 WhatsApp
        </a>
        <a href="https://www.facebook.com/Agpt2" target="_blank" rel="noopener noreferrer" class="contact-btn contact-btn-fb">
            🔵 Facebook
        </a>
        <a href="https://t.me/aibymizan" target="_blank" rel="noopener noreferrer" class="contact-btn contact-btn-tg">
            ✈️ Telegram Group For More Updates
        </a>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📝 Direct Contact Form", expanded=False):
        st.caption("আপনার বার্তা লিখে সরাসরি যোগাযোগ করুন:")
        cf_user_name = st.text_input("আপনার নাম (Name):", key="cf_sidebar_name", placeholder="আপনার নাম...")
        cf_user_msg = st.text_area("আপনার বার্তা (Message):", key="cf_sidebar_msg", placeholder="কী জানতে বা জানাতে চান লিখুন...", height=80)
        if st.button("🚀 WhatsApp এ পাঠান", use_container_width=True, key="cf_sidebar_btn"):
            if cf_user_msg.strip():
                import urllib.parse
                sender_label = cf_user_name.strip() if cf_user_name.strip() else "একজন ব্যবহারকারী"
                direct_msg = f"হ্যালো মিজান ভাই, আমি {sender_label}।\n\nবার্তা:\n{cf_user_msg.strip()}"
                enc_msg = urllib.parse.quote(direct_msg)
                st.success("✅ নিচে ক্লিক করে সরাসরি চ্যাট ওপেন করুন:")
                st.link_button("📲 চ্যাট শুরু করতে ক্লিক করুন", f"https://wa.me/8801737929107?text={enc_msg}", use_container_width=True)
            else:
                st.warning("দয়া করে বার্তাটি লিখুন।")

    st.markdown("---")
    st.caption("© 2026 Mizan AI Video Studio • Grok Edition")

# Navigation Tabs
tab_studio, tab_auto, tab_batch, tab_gallery = st.tabs([
    "🎨 Custom Studio",
    "⚡ 1-Click Auto Video",
    "📦 Batch Generator",
    "📂 Video Library"
])

# -------------------------------------------------------------
# TAB 1: Custom Studio (Script, Voice Upload, Visual Prompts)
# -------------------------------------------------------------
with tab_studio:
    st.markdown("### 🎨 Custom Script & Animation Studio")
    st.write("Write or paste any script (short or 1hr+), upload custom recorded voice, and auto-generate scene-by-scene animation or stock footage prompts with no scene limits.")
    
    col_sc1, col_sc2 = st.columns([3, 2])
    
    with col_sc1:
        st.markdown("#### 1. Script Input or File Upload")
        uploaded_script_file = st.file_uploader(
            "📂 Upload Large Script (.txt):",
            type=["txt"],
            key="custom_script_file_upload"
        )
        
        default_script_content = """মাস শেষে পকেট খালি? জাপানিদের এই এক সিক্রেট নিয়মে প্রতি মাসে বাঁচবে হাজার টাকা!
কাকিবো নিয়মে খরচের আগে সঞ্চয়ের অংশ সরিয়ে রাখুন।
অপ্রয়োজনীয় খরচ চিহ্নিত করে বাজেটে কঠোর হোন।
এই ছোট অভ্যাসই আপনাকে আর্থিক স্বাধীনতা এনে দেবে!
ভিডিওটি ভালো লাগলে লাইক দিন এবং সাবস্ক্রাইব করুন।"""

        if uploaded_script_file is not None:
            try:
                loaded_txt = uploaded_script_file.read().decode("utf-8")
                if loaded_txt.strip():
                    default_script_content = loaded_txt
                    st.success(f"✅ Large script loaded! (Total characters: {len(loaded_txt):,})")
            except Exception as e_file:
                st.error(f"Error reading script file: {e_file}")

        custom_script_text = st.text_area(
            "Enter, paste or edit your script (Bengali or English, any length):",
            value=default_script_content,
            height=200,
            key="custom_script_area"
        )
        
        c_auto_sc, c_clear_sc = st.columns([3, 1])
        with c_auto_sc:
            if st.button(f"🪄 Auto-Generate Scenes for {selected_style_label} (No Limit)", use_container_width=True, type="secondary"):
                with st.spinner(f"Analyzing script & generating unlimited scenes for {selected_style_label}..."):
                    seg_scenes = auto_segment_script_into_scenes(
                        script_text=custom_script_text,
                        api_key=gemini_key,
                        is_english=is_voice_english,
                        visual_style=selected_style_id
                    )
                    if seg_scenes:
                        st.session_state["prompt_box_count"] = len(seg_scenes)
                        for s_i, sc in enumerate(seg_scenes):
                            st.session_state[f"vp_{s_i}"] = sc.get("visual_keyword", "")
                        st.session_state["parsed_scenes"] = seg_scenes
                        st.success(f"✅ Successfully created {len(seg_scenes)} scenes tailored for {selected_style_label}!")
                        st.rerun()
        with c_clear_sc:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state["prompt_box_count"] = 4
                if "parsed_scenes" in st.session_state:
                    del st.session_state["parsed_scenes"]
                st.rerun()
        
        # Audio Source Mode
        st.markdown("#### 2. Voiceover Source")
        audio_mode = st.radio(
            "Voiceover Synthesis Mode:",
            ["🤖 AI Voiceover Synthesis (Edge-TTS)", "🎙️ Upload Custom Recorded Voice Audio"],
            horizontal=True
        )
        
        uploaded_voice_file = None
        if audio_mode == "🎙️ Upload Custom Recorded Voice Audio":
            uploaded_voice_file = st.file_uploader("Upload Voice File (.mp3, .wav, .m4a):", type=["mp3", "wav", "m4a"])
            if uploaded_voice_file:
                st.audio(uploaded_voice_file)
                st.success("✅ Custom voice uploaded! Precision AI alignment will match subtitles to spoken words.")

    with col_sc2:
        st.markdown(f"#### 3. Scene Prompts ({selected_style_label})")
        st.caption("💡 The AI auto-generates keywords matching your selected style. You can edit prompt boxes or let AI handle everything automatically.")
        
        if "prompt_box_count" not in st.session_state:
            st.session_state["prompt_box_count"] = 4
            
        c_btn1, c_btn2, c_btn3, c_btn4 = st.columns([1, 1, 1, 1])
        with c_btn1:
            if st.button("➕ 1 Scene", use_container_width=True):
                st.session_state["prompt_box_count"] += 1
                st.rerun()
        with c_btn2:
            if st.button("➕ 5 Scenes", use_container_width=True):
                st.session_state["prompt_box_count"] += 5
                st.rerun()
        with c_btn3:
            if st.button("➖ Remove", use_container_width=True):
                if st.session_state["prompt_box_count"] > 1:
                    st.session_state["prompt_box_count"] -= 1
                    st.rerun()
        with c_btn4:
            st.write(f"Total: **{st.session_state['prompt_box_count']}**")
            
        # Default prompts tailored to style
        if selected_style_id == "geomap":
            default_prompts = [
                "world globe rotating satellite view earth from space 3D",
                "Bangladesh satellite map zoom in border flight 3D",
                "Asia geopolitical animated map routes territory",
                "satellite view night lights city country zoom 4k",
                "global earth coordinates tracking hud glowing map"
            ]
        elif selected_style_id == "stickman":
            default_prompts = [
                "stickman looking at empty wallet doodle animation",
                "stick figure saving money whiteboard drawing",
                "stickman shopping cart cartoon sketch animation",
                "stick figure happy successful celebration drawing",
                "stickman subscribe button thumbs up animation"
            ]
        elif selected_style_id == "cartoon":
            default_prompts = [
                "3d cartoon character stressed empty wallet animation",
                "colorful cartoon character calculating budget 3d",
                "animated cartoon character cutting credit card fun",
                "happy rich cartoon character celebrating success 3d",
                "cute animated cartoon character subscribe thumbs up"
            ]
        elif selected_style_id == "cyberpunk":
            default_prompts = [
                "cyberpunk person empty digital wallet holographic neon 4k",
                "futuristic computer budget calculation neon grid",
                "cyber tech financial freedom holographic data",
                "neon futuristic successful person cyber city night",
                "cyberpunk holographic subscribe button glowing interface"
            ]
        else:
            default_prompts = [
                "man looking at empty wallet money stressed 4k",
                "japanese notebook piggy bank coins calculating budget 4k",
                "shopping cart cutting credit card saving money 4k",
                "happy successful wealthy person smiling freedom 4k",
                "subscribe button thumbs up social media connection 4k"
            ]
        
        user_visual_prompts = []
        for i in range(st.session_state["prompt_box_count"]):
            k = f"vp_{i}"
            if k not in st.session_state:
                st.session_state[k] = default_prompts[i] if i < len(default_prompts) else ""
            p_val = st.text_input(
                f"🎬 Scene {i+1} Prompt:",
                placeholder=f"e.g. {default_prompts[0]}",
                key=k
            )
            user_visual_prompts.append(p_val.strip())

    st.markdown("---")
    start_custom_gen = st.button("🚀 Render Full Video (Custom Script & Style)", type="primary", use_container_width=True)

    if start_custom_gen:
        is_eng = is_voice_english
        if "parsed_scenes" in st.session_state and st.session_state["parsed_scenes"]:
            constructed_scenes = list(st.session_state["parsed_scenes"])
        else:
            with st.spinner(f"Auto-segmenting script into scenes for {selected_style_label}..."):
                constructed_scenes = auto_segment_script_into_scenes(
                    script_text=custom_script_text,
                    api_key=gemini_key,
                    is_english=is_eng,
                    visual_style=selected_style_id
                )
                
        if not constructed_scenes:
            constructed_scenes = [{
                "segment_id": 1,
                "voiceover_text": custom_script_text.strip() or "Mizan AI Video Studio",
                "subtitle_text": custom_script_text.strip() or "Mizan AI Video Studio",
                "visual_keyword": default_prompts[0],
                "visual_description_bn": "Scene 1",
                "target_duration": 4.5
            }]
            
        # Prioritize custom prompts entered in boxes
        for idx in range(len(constructed_scenes)):
            if idx < len(user_visual_prompts) and user_visual_prompts[idx].strip():
                constructed_scenes[idx]["visual_keyword"] = user_visual_prompts[idx].strip()
                
        custom_script_data = {
            "title": "Custom Script Video",
            "hook": constructed_scenes[0]["voiceover_text"][:50],
            "quality_score": 9.3,
            "quality_review": f"Structured with {len(constructed_scenes)} scenes tailored for {selected_style_label}.",
            "scenes": constructed_scenes
        }
        
        c_status = st.status(f"⚡ Rendering {len(constructed_scenes)}-scene {selected_style_label} video...", expanded=True)
        c_progress = st.progress(10)
        
        try:
            custom_audio_path = None
            if audio_mode == "🎙️ Upload Custom Recorded Voice Audio" and uploaded_voice_file is not None:
                c_status.write("🎙️ Processing uploaded voiceover audio...")
                custom_audio_path = config.TEMP_DIR / f"user_audio_{uploaded_voice_file.name}"
                with open(custom_audio_path, "wb") as f_u:
                    f_u.write(uploaded_voice_file.getbuffer())
                c_status.write("✅ Custom voice ready! Performing precision AI subtitle alignment...")
                
            c_status.write(f"🎞️ Collecting media clips matching style '{selected_style_label}'...")
            c_progress.progress(40)
            orientation_str = "portrait" if "9:16" in format_choice else "landscape"
            
            clips = collect_media_for_scenes(
                scenes=constructed_scenes,
                orientation=orientation_str,
                pexels_key=pexels_key,
                pixabay_key=pixabay_key,
                visual_style=selected_style_id,
                google_maps_key=google_maps_key,
                fal_key=fal_key
            )
            c_status.write(f"✅ {len(clips)} visual clips prepared for {selected_style_label}!")
            c_progress.progress(70)
            
            c_status.write("⚙️ Assembling video, animated karaoke subtitles, audio mixing...")
            comp_res = compose_full_video(
                script_data=custom_script_data,
                video_clips=clips,
                voice_name=selected_voice_code,
                aspect_ratio_key=format_choice,
                bgm_filename=selected_bgm if selected_bgm != "No Background Music" else None,
                bgm_volume=bgm_vol,
                custom_audio_path=custom_audio_path,
                tts_rate=tts_rate,
                tts_pitch=tts_pitch,
                tts_engine=selected_tts_engine,
                eleven_model=selected_eleven_model,
                eleven_api_key=eleven_key,
                eleven_stability=eleven_stability,
                eleven_similarity=eleven_similarity,
                clone_sample_path=clone_sample_path,
                clone_language=clone_language,
                clone_pitch_hz=clone_pitch_hz,
                clone_speed_pct=clone_speed_pct,
                fish_api_key=fish_api_key,
                fish_reference_id=fish_reference_id,
                fish_speed=fish_speed
            )
            c_progress.progress(100)
            c_status.update(label="🎉 Your video is ready!", state="complete", expanded=False)
            
            st.success(f"🎬 Video generated successfully: {comp_res['filename']} (Duration: {comp_res['duration']:.1f}s)")
            col_v1, col_v2 = st.columns([3, 2])
            with col_v1:
                st.video(comp_res["output_path"])
                with open(comp_res["output_path"], "rb") as f_out:
                    st.download_button(
                        label="⬇️ Download Full Video (MP4)",
                        data=f_out,
                        file_name=comp_res["filename"],
                        mime="video/mp4",
                        type="primary",
                        use_container_width=True
                    )
            with col_v2:
                st.markdown("#### 📋 Scene-by-Scene Breakdown")
                st.write(f"**Total Scenes:** {len(constructed_scenes)}")
                st.write(f"**Visual Style:** {selected_style_label}")
                st.write(f"**Audio Mode:** {'Uploaded Custom Audio' if custom_audio_path else f'AI Voice ({selected_voice_label})'}")
                with st.expander("View All Scene Details", expanded=True):
                    for sc in constructed_scenes:
                        st.markdown(f"**Scene {sc['segment_id']}:** {sc['voiceover_text']}")
                        st.caption(f"Prompt: {sc['visual_keyword']}")
                        st.markdown("---")

        except Exception as e_gen:
            c_status.update(label="❌ Generation failed", state="error")
            st.error(f"Error: {e_gen}")

# -------------------------------------------------------------
# TAB 2: 1-Click Auto Video
# -------------------------------------------------------------
with tab_auto:
    st.markdown("### ⚡ 1-Click Autonomous Video Generator")
    st.write("Enter any topic or idea. Autonomous AI multi-agents write the script, collect stylized visuals, synthesize voiceover, and render the complete video in one click.")
    
    col_input, col_dur = st.columns([3, 1])
    with col_input:
        user_prompt = st.text_input(
            "Enter your topic or concept:",
            placeholder="e.g. 5 terrifying secrets of deep space, how AI changes the world, Japanese rule to save money...",
            key="auto_topic_input"
        )
    with col_dur:
        duration_choice = st.selectbox(
            "Video Target Duration:",
            options=[30, 60, 180, 300, 600, 1800, 3600],
            index=1,
            format_func=lambda x: f"{x} Seconds" if x < 60 else (f"{x//60} Minutes" if x < 3600 else f"{x/3600:.1f} Hours")
        )
        
    st.caption("Or click any trending topic prompt:")
    c_p1, c_p2, c_p3, c_p4 = st.columns(4)
    if c_p1.button("🪐 Space & Universe"): user_prompt = "5 terrifying mysteries of outer space"
    if c_p2.button("🤖 AI & Singularity"): user_prompt = "How artificial intelligence will transform human life"
    if c_p3.button("💰 Wealth Psychology"): user_prompt = "The simplest psychological habit that makes people rich"
    if c_p4.button("🧘 Mindfulness & Focus"): user_prompt = "3 morning mistakes that destroy your daily energy"

    start_auto = st.button("⚡ Generate Autonomous Video", type="primary", use_container_width=True, key="btn_start_auto")

    if start_auto:
        topic_text = user_prompt.strip() if user_prompt and user_prompt.strip() else "Knowledge and Science"
        status_box = st.status("⚡ Grok Multi-Agent Pipeline executing...", expanded=True)
        progress_bar = st.progress(5)
        
        try:
            is_eng = is_voice_english
            
            # Agent 1: Topic Generator
            status_box.write("🔹 **Agent 1 (Topic Architect):** Synthesizing high-retention title & hook...")
            topics = generate_topics(niche_or_prompt=topic_text, format_type=format_choice, api_key=gemini_key)
            selected_topic = user_prompt.strip() if user_prompt and user_prompt.strip() else (topics[0]["title"] if topics else topic_text)
            status_box.write(f"✅ Topic Locked: **{selected_topic}**")
            progress_bar.progress(25)
            
            # Agent 2: Script Writer
            status_box.write(f"🔹 **Agent 2 (Scriptwriter & Auditor):** Generating unlimited scenes tailored for {selected_style_label}...")
            script = generate_and_check_script(
                topic_title=selected_topic,
                target_duration_sec=duration_choice,
                format_type=format_choice,
                api_key=gemini_key,
                is_english=is_eng,
                visual_style=selected_style_id
            )
            score = script.get("quality_score", 9.0)
            hook_text = script.get("hook", "")
            scenes = script.get("scenes", [])
            status_box.write(f"✅ Script Verified! Quality Score: **{score}/10** | Scenes: **{len(scenes)}**")
            progress_bar.progress(50)
            
            # Agent 3: Media Collector
            status_box.write(f"🔹 **Agent 3 (Visual Collector):** Sourcing clips matching '{selected_style_label}'...")
            orientation_str = "portrait" if "9:16" in format_choice else "landscape"
            clips = collect_media_for_scenes(
                scenes=scenes,
                orientation=orientation_str,
                pexels_key=pexels_key,
                pixabay_key=pixabay_key,
                visual_style=selected_style_id,
                google_maps_key=google_maps_key,
                fal_key=fal_key
            )
            status_box.write(f"✅ Sourced {len(clips)} visual clips!")
            progress_bar.progress(75)
            
            # Agent 4: Video Composer
            status_box.write("🔹 **Agent 4 (Composer & Renderer):** Synthesizing voiceover, karaoke subtitles, and rendering...")
            comp_result = compose_full_video(
                script_data=script,
                video_clips=clips,
                voice_name=selected_voice_code,
                aspect_ratio_key=format_choice,
                bgm_filename=selected_bgm if selected_bgm != "No Background Music" else None,
                bgm_volume=bgm_vol,
                tts_rate=tts_rate,
                tts_pitch=tts_pitch,
                tts_engine=selected_tts_engine,
                eleven_model=selected_eleven_model,
                eleven_api_key=eleven_key,
                eleven_stability=eleven_stability,
                eleven_similarity=eleven_similarity,
                clone_sample_path=clone_sample_path,
                clone_language=clone_language,
                clone_pitch_hz=clone_pitch_hz,
                clone_speed_pct=clone_speed_pct,
                fish_api_key=fish_api_key,
                fish_reference_id=fish_reference_id,
                fish_speed=fish_speed
            )
            progress_bar.progress(100)
            status_box.update(label="🎉 Autonomous Video Complete!", state="complete", expanded=False)
            
            out_file = Path(comp_result["output_path"])
            st.success(f"🎬 Video Ready: {comp_result['filename']} (Duration: {comp_result['duration']:.1f}s)")
            
            v_col1, v_col2 = st.columns([2, 1])
            with v_col1:
                st.video(str(out_file))
                with open(out_file, "rb") as f_v:
                    st.download_button(
                        label="⬇️ Download Full Video (MP4)",
                        data=f_v,
                        file_name=comp_result["filename"],
                        mime="video/mp4",
                        type="primary",
                        use_container_width=True
                    )
            with v_col2:
                st.markdown("#### 🏆 Audit & Specifications")
                st.markdown(f"<span class='grok-pill'>Quality Score: {score}/10</span>", unsafe_allow_html=True)
                st.write(f"**Title:** {script.get('title')}")
                st.write(f"**Hook:** *{hook_text}*")
                st.write(f"**Total Scenes:** {len(scenes)}")
                st.write(f"**Visual Style:** {selected_style_label}")

            with st.expander("📝 View Full Script & Scene Prompts"):
                for sc in scenes:
                    st.markdown(f"**Scene {sc.get('segment_id', '')}:** {sc.get('voiceover_text', '')}")
                    st.caption(f"Visual Keyword: {sc.get('visual_keyword', '')}")
                    st.markdown("---")

        except Exception as err:
            status_box.update(label="❌ Generation error", state="error")
            st.error(f"Error: {err}")

# -------------------------------------------------------------
# TAB 3: Batch Generator
# -------------------------------------------------------------
with tab_batch:
    st.markdown("### 📦 Batch Video Generator — 5 Autonomous Videos")
    st.write("Generate 5 unique viral videos concurrently from a single category or theme.")
    
    batch_niche = st.text_input("Batch Niche or Theme:", value="Motivation and Self-Improvement", key="batch_niche_input")
    batch_dur = st.selectbox("Duration per Video:", options=[15, 30, 45, 60], index=1, key="batch_dur_select")
    
    if st.button("🚀 Start 5-Video Batch Generation", type="primary", key="btn_start_batch"):
        st.info("Generating batch topics...")
        batch_topics = generate_topics(batch_niche, format_choice, gemini_key)
        
        batch_progress = st.progress(0)
        total_videos = len(batch_topics)
        
        for idx, top in enumerate(batch_topics):
            st.markdown(f"---")
            st.markdown(f"#### 🎬 Video {idx+1}/{total_videos}: {top['title']}")
            
            with st.status(f"Processing Video {idx+1}...", expanded=False) as b_stat:
                is_eng = is_voice_english
                script = generate_and_check_script(
                    top['title'],
                    batch_dur,
                    format_choice,
                    gemini_key,
                    is_english=is_eng,
                    visual_style=selected_style_id
                )
                b_stat.write(f"Hook: {script.get('hook', '')}")
                
                orientation_str = "portrait" if "9:16" in format_choice else "landscape"
                clips = collect_media_for_scenes(
                    script.get("scenes", []),
                    orientation_str,
                    pexels_key,
                    pixabay_key,
                    visual_style=selected_style_id,
                    google_maps_key=google_maps_key,
                    fal_key=fal_key
                )
                
                res = compose_full_video(
                    script_data=script,
                    video_clips=clips,
                    voice_name=selected_voice_code,
                    aspect_ratio_key=format_choice,
                    bgm_filename=selected_bgm if selected_bgm != "No Background Music" else None,
                    bgm_volume=bgm_vol,
                    tts_rate=tts_rate,
                    tts_pitch=tts_pitch,
                    tts_engine=selected_tts_engine,
                    eleven_model=selected_eleven_model,
                    eleven_api_key=eleven_key,
                    eleven_stability=eleven_stability,
                    eleven_similarity=eleven_similarity,
                    clone_sample_path=clone_sample_path,
                    clone_language=clone_language,
                    clone_pitch_hz=clone_pitch_hz,
                    clone_speed_pct=clone_speed_pct,
                    fish_api_key=fish_api_key,
                    fish_reference_id=fish_reference_id,
                    fish_speed=fish_speed
                )
                b_stat.update(label=f"Video {idx+1} complete!", state="complete")
                
            st.video(res["output_path"])
            with open(res["output_path"], "rb") as f_b:
                st.download_button(f"⬇️ Download Video {idx+1}", data=f_b, file_name=res["filename"], mime="video/mp4", key=f"dl_b_{idx}")
                
            batch_progress.progress(int(((idx + 1) / total_videos) * 100))

# -------------------------------------------------------------
# TAB 4: Video Library & Player
# -------------------------------------------------------------
with tab_gallery:
    st.markdown("### 📂 Video Library & Player")
    st.write("Browse, preview, and download all rendered videos in your studio:")
    
    video_files = sorted(list(config.OUTPUT_DIR.glob("*.mp4")), key=os.path.getmtime, reverse=True)
    
    if not video_files:
        st.info("No videos generated yet. Head over to Custom Studio or 1-Click Auto Video to make one.")
    else:
        st.caption(f"Total Rendered Videos: {len(video_files)}")
        
        # On-demand selector prevents high WebSocket memory payload on startup
        v_names = [v.name for v in video_files]
        selected_vid_name = st.selectbox("Select Video to Play / Download:", options=v_names, index=0)
        
        target_vpath = config.OUTPUT_DIR / selected_vid_name
        if target_vpath.exists():
            size_mb = target_vpath.stat().st_size / (1024 * 1024)
            mod_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(target_vpath.stat().st_mtime))
            
            c_vid, c_info = st.columns([3, 2])
            with c_vid:
                st.video(str(target_vpath))
            with c_info:
                st.markdown(f"#### 🎬 {target_vpath.name}")
                st.write(f"**File Size:** {size_mb:.2f} MB")
                st.write(f"**Rendered Time:** {mod_time}")
                with open(target_vpath, "rb") as f_g:
                    st.download_button(
                        label=f"⬇️ Download Video ({size_mb:.1f} MB)",
                        data=f_g,
                        file_name=target_vpath.name,
                        mime="video/mp4",
                        type="primary",
                        use_container_width=True,
                        key=f"dl_gallery_{selected_vid_name}"
                    )
                    
        with st.expander("📋 All Rendered Files Directory", expanded=False):
            for vpath in video_files:
                s_mb = vpath.stat().st_size / (1024 * 1024)
                m_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(vpath.stat().st_mtime))
                st.write(f"• **{vpath.name}** ({s_mb:.1f} MB) — *{m_time}*")

# -------------------------------------------------------------
# Global Footer Card with Contact & Support
# -------------------------------------------------------------
st.markdown("""
<div class="grok-footer">
    <div style="font-size: 1.15rem; font-weight: 800; color: #ffffff; margin-bottom: 6px;">
        🎬 Mizan AI Video Studio • Grok Edition
    </div>
    <div style="font-size: 0.88rem; color: #a1a1aa; margin-bottom: 14px;">
        স্বয়ংক্রিয় বাংলা ভিডিও তৈরির সহজতম ইঞ্জিন | নির্মাতা: <strong>Mizan</strong>
    </div>
    <div class="grok-footer-links">
        <a href="https://wa.me/8801737929107" target="_blank" rel="noopener noreferrer" class="grok-footer-link contact-btn-wa">
            💬 WhatsApp
        </a>
        <a href="https://www.facebook.com/Agpt2" target="_blank" rel="noopener noreferrer" class="grok-footer-link contact-btn-fb">
            🔵 Facebook
        </a>
        <a href="https://t.me/aibymizan" target="_blank" rel="noopener noreferrer" class="grok-footer-link contact-btn-tg">
            ✈️ Telegram Group For More Updates
        </a>
    </div>
    <div style="font-size: 0.78rem; color: #52525b; margin-top: 16px;">
        © 2026 Mizan AI Video Studio. All rights reserved.
    </div>
</div>
""", unsafe_allow_html=True)
