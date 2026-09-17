import streamlit as st
import os
import time
from pathlib import Path
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv(override=True)

import config
from agents.topic_agent import generate_topics
from agents.script_agent import generate_and_check_script, auto_segment_script_into_scenes
from agents.media_agent import collect_media_for_scenes
from agents.composer_agent import compose_full_video
from core.tts_engine import VOICES

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
        background: #09090b;
        color: #f4f4f5;
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
    
    /* Primary buttons */
    .stButton>button {
        border-radius: 12px;
        font-weight: 600;
        letter-spacing: -0.01em;
        transition: all 0.2s ease-in-out;
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
    st.markdown("### ⚙️ Engine Settings")
    
    with st.expander("🔑 API Credentials", expanded=False):
        st.caption("Provide API keys for unlimited high-quality generation:")
        gemini_key = st.text_input("Google Gemini API Key", value=config.get_gemini_api_key(), type="password")
        pexels_key = st.text_input("Pexels API Key", value=config.get_pexels_api_key(), type="password")
        pixabay_key = st.text_input("Pixabay API Key", value=config.get_pixabay_api_key(), type="password")
        google_maps_key = st.text_input(
            "Google Maps / Earth API Key (Optional)",
            value=config.get_google_maps_api_key(),
            type="password",
            help="Optional for Google Maps Satellite tiles. Free high-res Esri & OSM global satellite imagery is active automatically!"
        )
        fal_key = st.text_input(
            "Fal.ai API Key (AI Video & FLUX Generator)",
            value=config.get_fal_key(),
            type="password",
            help="When stock video cannot match a scene, Fal.ai automatically generates custom 4K AI video clips!"
        )
        
        if st.button("💾 Save API Credentials", use_container_width=True):
            env_path = config.BASE_DIR / ".env"
            set_key(env_path, "GEMINI_API_KEY", gemini_key.strip())
            set_key(env_path, "PEXELS_API_KEY", pexels_key.strip())
            set_key(env_path, "PIXABAY_API_KEY", pixabay_key.strip())
            set_key(env_path, "GOOGLE_MAPS_API_KEY", google_maps_key.strip())
            set_key(env_path, "FAL_KEY", fal_key.strip())
            os.environ["GEMINI_API_KEY"] = gemini_key.strip()
            os.environ["PEXELS_API_KEY"] = pexels_key.strip()
            os.environ["PIXABAY_API_KEY"] = pixabay_key.strip()
            os.environ["GOOGLE_MAPS_API_KEY"] = google_maps_key.strip()
            os.environ["FAL_KEY"] = fal_key.strip()
            st.success("API Credentials saved successfully!")
            st.rerun()
            
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.caption("Gemini: " + ("🟢" if gemini_key else "⚪"))
        with c2: st.caption("Pexels: " + ("🟢" if pexels_key else "⚪"))
        with c3: st.caption("Pixabay: " + ("🟢" if pixabay_key else "⚪"))
        with c4: st.caption("Maps: " + ("🟢" if google_maps_key else "🟡 Free"))
        with c5: st.caption("Fal.ai: " + ("🟢" if fal_key else "⚪"))

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
    st.markdown("### 🎙️ Voice & Audio Synthesis")
    voice_filter = st.radio("Voice Language Filter:", ["All Voices", "🇧🇩 Bengali", "🇺🇸/🇬🇧 English"], horizontal=True)
    
    if voice_filter == "🇧🇩 Bengali":
        filtered_voices = {k: v for k, v in config.VOICES.items() if v.startswith("bn-")}
    elif voice_filter == "🇺🇸/🇬🇧 English":
        filtered_voices = {k: v for k, v in config.VOICES.items() if v.startswith("en-")}
    else:
        filtered_voices = config.VOICES

    selected_voice_label = st.selectbox("Select Voice:", options=list(filtered_voices.keys()), index=0)
    selected_voice_code = filtered_voices[selected_voice_label]

    speed_val = st.slider("Speech Speed Rate", min_value=-20, max_value=50, value=0, step=5, format="%d%%")
    tts_rate = f"{speed_val:+d}%"

    pitch_val = st.slider("Speech Tone / Pitch", min_value=-10, max_value=10, value=0, step=1, format="%dHz")
    tts_pitch = f"{pitch_val:+d}Hz"

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

    bgm_vol = st.slider("Music Volume (Auto-Ducking)", min_value=0.05, max_value=0.30, value=0.12, step=0.01)

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
                        is_english=selected_voice_code.startswith("en-"),
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
            default_val = default_prompts[i] if i < len(default_prompts) else ""
            p_val = st.text_input(
                f"🎬 Scene {i+1} Prompt:",
                value=default_val,
                placeholder=f"e.g. {default_prompts[0]}",
                key=f"vp_{i}"
            )
            user_visual_prompts.append(p_val.strip())

    st.markdown("---")
    start_custom_gen = st.button("🚀 Render Full Video (Custom Script & Style)", type="primary", use_container_width=True)

    if start_custom_gen:
        is_eng = selected_voice_code.startswith("en-")
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
                tts_pitch=tts_pitch
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
            is_eng = selected_voice_code.startswith("en-")
            
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
                tts_pitch=tts_pitch
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
                is_eng = selected_voice_code.startswith("en-")
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
                    tts_pitch=tts_pitch
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
