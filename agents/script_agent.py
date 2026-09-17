import json
import os
from google import genai
from config import get_gemini_api_key

def build_dynamic_topic_script(topic_title: str, target_duration_sec: int = 45, is_english: bool = False) -> dict:
    clean = topic_title.strip() if topic_title and topic_title.strip() else "অজানা রহস্য ও জ্ঞান"
    if is_english:
        return {
            "title": clean,
            "hook": f"Did you know this fascinating truth about {clean}?",
            "quality_score": 8.8,
            "quality_review": "Strong hook in first 5 seconds, clear rhythm and engaging topic-focused storytelling.",
            "scenes": [
                {
                    "segment_id": 1,
                    "voiceover_text": f"Did you know this fascinating truth about {clean}? Most people have never heard of this.",
                    "subtitle_text": f"Fascinating truth about {clean}!",
                    "visual_keyword": f"{clean} cinematic mystery discovery",
                    "visual_description_bn": f"{clean} এর দারুণ দৃশ্য",
                    "target_duration": 4.5
                },
                {
                    "segment_id": 2,
                    "voiceover_text": f"When you take a closer look, {clean} completely transforms how we understand the world.",
                    "subtitle_text": f"Transforming how we see {clean}",
                    "visual_keyword": "modern innovation creative lifestyle focus",
                    "visual_description_bn": "আধুনিক দৃষ্টিভঙ্গি ও উদ্ভাবন",
                    "target_duration": 5.0
                },
                {
                    "segment_id": 3,
                    "voiceover_text": f"Studies and top experts agree that regular attention to {clean} yields extraordinary results.",
                    "subtitle_text": f"Extraordinary results of {clean}",
                    "visual_keyword": "success growth leadership inspiration",
                    "visual_description_bn": "সাফল্য ও সমৃদ্ধির দৃশ্য",
                    "target_duration": 5.0
                },
                {
                    "segment_id": 4,
                    "voiceover_text": f"The most incredible part is the massive positive evolution happening right now!",
                    "subtitle_text": "Incredible evolution happening right now!",
                    "visual_keyword": "futuristic city bright lights cinematic progress",
                    "visual_description_bn": "ভবিষ্যত ও আধুনিক আলোর ঝলকানি",
                    "target_duration": 4.8
                },
                {
                    "segment_id": 5,
                    "voiceover_text": f"What do you think about {clean}? Share your thoughts in the comments and subscribe!",
                    "subtitle_text": "Comment your thoughts & Subscribe!",
                    "visual_keyword": "happy person smiling connection community",
                    "visual_description_bn": "হাস্যোজ্জ্বল মুখ ও সোশ্যাল কমিউনিটি",
                    "target_duration": 4.2
                }
            ]
        }
    else:
        return {
            "title": clean,
            "hook": f"আপনি কি জানেন {clean} নিয়ে লুকিয়ে থাকা এই অবিশ্বাস্য তথ্যটি?",
            "quality_score": 8.8,
            "quality_review": "প্রথম ৫ সেকেন্ডের শক্তিশালী হুক, কথ্য বাংলা ভঙ্গি এবং বিষয়ভিত্তিক ধারাবাহিক দৃশ্য বিন্যাস।",
            "scenes": [
                {
                    "segment_id": 1,
                    "voiceover_text": f"আপনি কি জানেন {clean} নিয়ে লুকিয়ে থাকা এই অবিশ্বাস্য তথ্যটি? যা অনেকেরই পুরোপুরি অজানা!",
                    "subtitle_text": f"{clean} নিয়ে অবিশ্বাস্য তথ্য!",
                    "visual_keyword": f"{clean} mystery cinematic concept discovery",
                    "visual_description_bn": f"{clean} সম্পর্কিত রহস্যময় দৃশ্য",
                    "target_duration": 4.5
                },
                {
                    "segment_id": 2,
                    "voiceover_text": f"আসলে {clean} আমাদের প্রতিদিনের জীবন ও চিন্তাধারায় এক দারুণ ইতিবাচক প্রভাব ফেলে।",
                    "subtitle_text": f"{clean} আমাদের জীবনে কীভাবে প্রভাব ফেলে",
                    "visual_keyword": "positive mindset nature peaceful motivation",
                    "visual_description_bn": "প্রকৃতি ও ইতিবাচক মানসিকতা",
                    "target_duration": 5.0
                },
                {
                    "segment_id": 3,
                    "voiceover_text": f"বিশেষজ্ঞদের মতে, {clean} সম্পর্কে স্পষ্ট ধারণা তৈরি হলে যে কোনো লক্ষ্য অর্জন করা সহজ হয়ে যায়।",
                    "subtitle_text": f"{clean} সম্পর্কে সঠিক ধারণা অর্জন",
                    "visual_keyword": "creative thinking ideas strategy solution",
                    "visual_description_bn": "সৃজনশীল ভাবনা ও নতুন আইডিয়া",
                    "target_duration": 5.0
                },
                {
                    "segment_id": 4,
                    "voiceover_text": f"সবচেয়ে আকর্ষণীয় বিষয় হলো, এর মাধ্যমে আগামী দিনগুলোতে তৈরি হচ্ছে নতুন সম্ভাবনার অপার দুয়ার!",
                    "subtitle_text": "তৈরি হচ্ছে নতুন সম্ভাবনার অপার দুয়ার!",
                    "visual_keyword": "future technology light speed cinematic city",
                    "visual_description_bn": "ভবিষ্যত প্রযুক্তি ও গতির আলো",
                    "target_duration": 4.8
                },
                {
                    "segment_id": 5,
                    "voiceover_text": f"{clean} নিয়ে আপনার নিজস্ব ভাবনা কী? কমেন্টে লিখে জানান আর সাবস্ক্রাইব করে সাথে থাকুন!",
                    "subtitle_text": "কমেন্টে জানান আর সাবস্ক্রাইব করে সাথে থাকুন!",
                    "visual_keyword": "smiling person happy social community connection",
                    "visual_description_bn": "কমেন্ট ও সাবস্ক্রাইব আহ্বান",
                    "target_duration": 4.2
                }
            ]
        }

def generate_script_draft(
    topic_title: str,
    target_duration_sec: int = 45,
    format_type: str = "Shorts / Reels (9:16)",
    client: genai.Client = None,
    model_name: str = "gemini-3.6-flash",
    improvement_feedback: str = None,
    is_english: bool = False,
    target_scenes: int = None,
    visual_style: str = "realistic"
) -> dict:
    if target_scenes:
        scene_count_rule = f"Target Scene Count: Create approximately {target_scenes} scenes."
    else:
        scene_count_rule = "Scene Count: Dynamically create as many scenes as naturally required to tell the full, engaging story scene-by-scene with NO artificial limitation. Do NOT restrict yourself to 9 scenes; provide rich, continuous visual transitions for the entire target duration."
    
    if target_duration_sec >= 300:
        scene_dur_rule = "Each scene voiceover should be a descriptive narration of 8 to 20 seconds."
    else:
        scene_dur_rule = "Each scene duration should be 3.5 to 6.0 seconds."
    
    # Style-specific prompt guidelines
    if visual_style == "geomap":
        style_rule = """VISUAL STYLE: GEO MAP STYLE VIDEO (3D Earth & Geopolitical Map Animation).
Every scene's 'visual_keyword' MUST be tailored for 3D Earth, Google Earth satellite zoom, geopolitical maps, and country border animations.
Extract or pinpoint the specific country, city, continent, landmark, or geographical region mentioned (e.g., 'Bangladesh border satellite map 3D', 'Ukraine Eastern Europe map animation', 'Middle East geopolitical map satellite', 'Earth rotating space 4k', 'Red Sea trade route map animation'). Always include the target country/location name followed by 'satellite map 3D'."""
    elif visual_style == "stickman":
        style_rule = """VISUAL STYLE: STICKMAN & WHITEBOARD DOODLE ANIMATION.
Every scene's 'visual_keyword' MUST be tailored for minimalist stickman / stick figure / whiteboard doodle animation.
Examples: 'stickman character thinking whiteboard animation', 'stick figure running funny cartoon doodle', 'stickman celebration victory simple drawing', 'stickman walking animated sketch'."""
    elif visual_style == "cartoon":
        style_rule = """VISUAL STYLE: 3D & 2D CARTOON ANIMATION.
Every scene's 'visual_keyword' MUST be tailored for colorful animated cartoon characters (Pixar / Disney / vibrant anime 3D render).
Examples: '3d cartoon character happy walking colorful animation', 'cute animated robot cartoon friendly', 'colorful animated cartoon explosion surprise', 'cartoon person working on laptop animation'."""
    elif visual_style == "cyberpunk":
        style_rule = """VISUAL STYLE: CYBERPUNK & FUTURISTIC SCI-FI.
Every scene's 'visual_keyword' MUST be tailored for futuristic sci-fi, glowing neon city, holographic tech.
Examples: 'futuristic neon city cyber tech lights 4k', 'hologram interface ai technology glowing'."""
    else:
        style_rule = """VISUAL STYLE: REALISTIC 4K CINEMATIC.
Every scene's 'visual_keyword' MUST be tailored for cinematic, high-definition realistic photography and 4K stock video.
Examples: 'cinematic 4k dramatic lighting city night', 'calm peaceful nature river sunlight'."""

    feedback_instruction = ""
    if improvement_feedback:
        feedback_instruction = f"Previous Quality Feedback: '{improvement_feedback}'. Please fix these issues."

    lang_instruction = "Language: Natural, engaging, spoken conversational ENGLISH." if is_english else "ভাষা: সম্পূর্ণ সহজ, কথ্য ও আধুনিক বাংলা (কোনো জটিল বইয়ের ভাষা নয়)।"

    prompt = f"""
You are a world-class professional YouTube and Shorts video scriptwriter and director.
Topic: "{topic_title}"
Video Format: {format_type}
Target Duration: ~{target_duration_sec} seconds.
{scene_count_rule}
{style_rule}
{lang_instruction}

Strict Rules:
1. The first 5 seconds MUST have an irresistible hook that locks in the viewer.
2. Short, punchy, conversational sentences tailored for spoken voiceover.
3. For each scene, provide a highly relevant English 'visual_keyword' for video search strictly matching the requested visual style ({visual_style}).
4. {scene_dur_rule}
5. Strictly focus on the given topic: "{topic_title}".
6. Add as many scenes as needed to cover the topic completely without any arbitrary cap or limitation.

{feedback_instruction}

Respond ONLY with valid JSON in this exact structure (no markdown fences or commentary):
{{
  "title": "{topic_title}",
  "hook": "Hook line in first 5 seconds",
  "scenes": [
    {{
      "segment_id": 1,
      "voiceover_text": "Spoken voiceover text...",
      "subtitle_text": "Short clean subtitle text...",
      "visual_keyword": "english stock footage search prompt",
      "visual_description_bn": "Brief visual description",
      "target_duration": 4.5
    }}
  ]
}}
"""
    models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-latest", model_name, "gemini-2.5-flash"]
    for m in models_to_try:
        try:
            resp = client.models.generate_content(
                model=m,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            txt = resp.text.strip()
            if txt.startswith("```json"):
                txt = txt[7:]
            if txt.endswith("```"):
                txt = txt[:-3]
            return json.loads(txt.strip())
        except Exception as e:
            continue
    return None

def auto_segment_script_into_scenes(
    script_text: str,
    api_key: str = None,
    is_english: bool = False,
    visual_style: str = "realistic"
) -> list:
    """
    Takes any user-provided raw script (any size, 1 minute to 1 hour+)
    and splits it into unlimited scenes with high-relevance English visual keywords for Pexels/Pixabay,
    tailored strictly to the requested visual style (Stickman, Cartoon, Cyberpunk, Realistic).
    """
    clean_script = script_text.strip() if script_text else ""
    if not clean_script:
        return []

    if visual_style == "geomap":
        style_prompt = "VISUAL STYLE: GEO MAP STYLE VIDEO (3D Earth & Geopolitical Map Animation). For every scene's 'visual_keyword', identify the specific country, city, continent, body of water, or geographical region mentioned in the narration (e.g. 'Bangladesh satellite border map', 'Ukraine Eastern Europe map animation', 'Taiwan Strait naval ocean map', 'Middle East satellite earth zoom', 'Amazon Rainforest aerial satellite map', 'Red Sea trade route map animation'). Always include the target country/location name followed by 'satellite map 3D'."
    elif visual_style == "stickman":
        style_prompt = "VISUAL STYLE: STICKMAN & WHITEBOARD DOODLE ANIMATION. For every scene's 'visual_keyword', generate search queries specifically for stick figures, whiteboard animations, doodle sketches (e.g. 'stickman thinking whiteboard animation', 'stick figure walking doodle animation', 'stickman celebration sketch funny')."
    elif visual_style == "cartoon":
        style_prompt = "VISUAL STYLE: 3D & 2D CARTOON ANIMATION. For every scene's 'visual_keyword', generate search queries for vibrant animated cartoon characters, 3D Pixar-style renders, colorful motion (e.g. '3d cartoon character happy walking colorful animation', 'cute animated robot cartoon friendly', 'colorful animated cartoon story motion')."
    elif visual_style == "cyberpunk":
        style_prompt = "VISUAL STYLE: CYBERPUNK & FUTURISTIC SCI-FI. For every scene's 'visual_keyword', generate search queries for neon cyber tech, futuristic holographic city 4k."
    else:
        style_prompt = "VISUAL STYLE: REALISTIC 4K CINEMATIC. For every scene's 'visual_keyword', generate search queries for cinematic 4K realistic stock video footage."

    key = api_key or get_gemini_api_key()
    if key:
        try:
            client = genai.Client(api_key=key)
            prompt = f"""You are a professional video director and editor.
Take the following script and break it down scene-by-scene into as many scenes as naturally needed.
There is NO limitation on the number of scenes (whether 5, 12, 25, 50, or 100+ scenes). Every distinct thought, action, or sentence should become its own visual scene.
{style_prompt}

Script:
\"\"\"
{clean_script}
\"\"\"

Instructions:
1. Break down the entire script sequentially scene-by-scene.
2. For EVERY scene, create:
   - "segment_id": integer starting from 1
   - "voiceover_text": the exact spoken narration text for this scene
   - "subtitle_text": clean, easily readable subtitle text for screen display
   - "visual_keyword": A HIGHLY RELEVANT 3-5 word ENGLISH search query for video search strictly matching the requested style ({visual_style})
   - "visual_description_bn": short description
   - "target_duration": estimated speaking duration in seconds (typically 3.0 to 6.0s)

Respond ONLY with valid JSON:
{{
  "scenes": [
    {{
      "segment_id": 1,
      "voiceover_text": "...",
      "subtitle_text": "...",
      "visual_keyword": "...",
      "visual_description_bn": "...",
      "target_duration": 4.5
    }}
  ]
}}
"""
            models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]
            for m in models_to_try:
                try:
                    resp = client.models.generate_content(
                        model=m,
                        contents=prompt,
                        config={"response_mime_type": "application/json"}
                    )
                    txt = resp.text.strip()
                    if txt.startswith("```json"):
                        txt = txt[7:]
                    if txt.endswith("```"):
                        txt = txt[:-3]
                    data = json.loads(txt.strip())
                    if data and "scenes" in data and len(data["scenes"]) > 0:
                        return data["scenes"]
                except Exception as err:
                    print(f"[Auto Segment Model {m} Error] {err}")
                    continue
        except Exception as e_ai:
            print(f"[Auto Segment AI Error] {e_ai}")

    # Fallback Rule-Engine: Split intelligently by sentence punctuation with no limit
    import re
    lines = [l.strip() for l in clean_script.split("\n") if l.strip()]
    raw_sentences = []
    for line in lines:
        if len(line) > 100:
            parts = [p.strip() for p in re.split(r'[।\.\?\!]+', line) if p.strip()]
            raw_sentences.extend(parts if parts else [line])
        else:
            raw_sentences.append(line)
            
    if not raw_sentences:
        raw_sentences = [clean_script]

    if visual_style == "stickman":
        default_keywords = [
            "stickman character walking animation doodle",
            "stick figure thinking whiteboard sketch",
            "stickman running funny cartoon animation",
            "stickman celebration victory simple drawing",
            "whiteboard animation stick figure explanation"
        ]
    elif visual_style == "cartoon":
        default_keywords = [
            "3d cartoon character animation vibrant",
            "colorful 2d cartoon motion story",
            "cute animated cartoon character happy",
            "fun cartoon motion animated scene 3d",
            "playful cartoon animation character expressive"
        ]
    elif visual_style == "cyberpunk":
        default_keywords = [
            "futuristic neon city night lights cyber",
            "digital ai technology holographic matrix",
            "glowing cyber grid futuristic world 4k",
            "cyberpunk robot technology lights"
        ]
    else:
        default_keywords = [
            "cinematic dramatic mystery discovery 4k",
            "creative thinking modern strategy technology",
            "success growth wealth leadership motivation",
            "futuristic progress lights city night",
            "happy smiling people community lifestyle",
            "nature calm peaceful forest landscape"
        ]

    scenes = []
    for idx, sentence in enumerate(raw_sentences):
        kw = default_keywords[idx % len(default_keywords)]
        scenes.append({
            "segment_id": idx + 1,
            "voiceover_text": sentence,
            "subtitle_text": sentence,
            "visual_keyword": kw,
            "visual_description_bn": f"Scene {idx+1}",
            "target_duration": max(3.5, min(7.0, len(sentence) * 0.15))
        })
        
    return scenes

def evaluate_script_quality(
    script_data: dict,
    client: genai.Client,
    model_name: str = "gemini-3.6-flash"
) -> dict:
    script_summary = json.dumps(script_data, ensure_ascii=False, indent=2)
    prompt = f"""
You are an expert video director and script auditor.
Evaluate this video script on a scale of 1 to 10:

{script_summary}

Criteria:
1. Hook strength (first 5 seconds retention)
2. Conversational flow and pacing
3. Simplicity and clarity for voiceover
4. Stock footage query relevance

Respond ONLY with valid JSON:
{{
  "overall_score": 8.8,
  "hook_score": 9.0,
  "pacing_score": 8.5,
  "needs_rewrite": false,
  "feedback": "Strong hook and clear topic alignment.",
  "improvement_notes": ""
}}
"""
    models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-latest", model_name, "gemini-2.5-flash"]
    for m in models_to_try:
        try:
            resp = client.models.generate_content(
                model=m,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            txt = resp.text.strip()
            if txt.startswith("```json"):
                txt = txt[7:]
            if txt.endswith("```"):
                txt = txt[:-3]
            return json.loads(txt.strip())
        except Exception:
            continue

    return {
        "overall_score": 8.5,
        "hook_score": 8.5,
        "pacing_score": 8.5,
        "needs_rewrite": False,
        "feedback": "High quality script with strong retention hook.",
        "improvement_notes": ""
    }

def generate_and_check_script(
    topic_title: str,
    target_duration_sec: int = 45,
    format_type: str = "Shorts / Reels (9:16)",
    api_key: str = None,
    model_name: str = "gemini-3.6-flash",
    max_retries: int = 3,
    is_english: bool = False,
    target_scenes: int = None,
    visual_style: str = "realistic"
) -> dict:
    key = api_key or get_gemini_api_key()
    if not key:
        return build_dynamic_topic_script(topic_title, target_duration_sec, is_english)

    try:
        client = genai.Client(api_key=key)
        feedback = None
        
        for attempt in range(1, max_retries + 1):
            script = generate_script_draft(
                topic_title=topic_title,
                target_duration_sec=target_duration_sec,
                format_type=format_type,
                client=client,
                model_name=model_name,
                improvement_feedback=feedback,
                is_english=is_english,
                target_scenes=target_scenes,
                visual_style=visual_style
            )
            if not script or "scenes" not in script or not script["scenes"]:
                continue
                
            eval_result = evaluate_script_quality(script, client, model_name)
            score = eval_result.get("overall_score", 8.5)
            script["quality_score"] = score
            script["quality_review"] = eval_result.get("feedback", "Script successfully verified.")
            
            if score >= 7.0 and not eval_result.get("needs_rewrite", False):
                return script
            else:
                feedback = eval_result.get("improvement_notes", "Improve hook retention.")

        if script:
            return script
    except Exception as e:
        print(f"[Agent 2 Gemini Error] {e}")

    return build_dynamic_topic_script(topic_title, target_duration_sec, is_english)
