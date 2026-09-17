import json
import os
from google import genai
from config import get_gemini_api_key

FALLBACK_TOPICS = [
    {
        "id": 1,
        "title": "মহাকাশের ৫টি সবচেয়ে ভয়ংকর রহস্য যা বিজ্ঞানীরাও জানেন না",
        "hook": "আপনি কি জানেন মহাকাশে এমন এক জায়গা আছে যেখানে সময় উল্টো চলে?",
        "category": "বিজ্ঞান ও রহস্য",
        "target_audience": "সাধারণ কৌতূহলী দর্শক",
        "estimated_duration": "Shorts (50 sec)"
    },
    {
        "id": 2,
        "title": "AI যেভাবে আগামী ৫ বছরে আমাদের দুনিয়া বদলে দেবে",
        "hook": "আপনার বর্তমান চাকরি কি আগামী ৩ বছর পর থাকবে? এই ভিডিওটি দেখুন!",
        "category": "প্রযুক্তি ও ভবিষ্যৎ",
        "target_audience": "তরুণ ও প্রযুক্তিপ্রেমী",
        "estimated_duration": "Shorts (55 sec)"
    },
    {
        "id": 3,
        "title": "সকালে ঘুম থেকে উঠেই এই ৩টি ভুল কখনো করবেন না",
        "hook": "আপনার সারাদিনের ক্লান্তি আর হতাশার মূল কারণ হয়তো আপনার সকালের এই একটি ভুল!",
        "category": "স্বাস্থ্য ও লাইফস্টাইল",
        "target_audience": "সব বয়সী মানুষ",
        "estimated_duration": "Shorts (45 sec)"
    },
    {
        "id": 4,
        "title": "ইতিহাসের সবচেয়ে ধনী মানুষ কে ছিলেন? যার সম্পদ গণনা করা যেত না",
        "hook": "এলন মাস্ক বা জেফ বেজোস নন, ইতিহাসের সবচেয়ে ধনী মানুষটি কে ছিলেন জানেন?",
        "category": "ইতিহাস ও অনুপ্রেরণা",
        "target_audience": "ইতিহাস ও জ্ঞানপিপাসু",
        "estimated_duration": "Shorts (60 sec)"
    },
    {
        "id": 5,
        "title": "টাকা সঞ্চয় করার সবচেয়ে সহজ জাপানি গোপন নিয়ম: কাকিবো",
        "hook": "মাস শেষে পকেটে টাকা থাকে না? জাপানিদের এই ১টি কৌশল আপনার জীবন বদলে দেবে!",
        "category": "অর্থনীতি ও ক্যারিয়ার",
        "target_audience": "শিক্ষার্থী ও চাকরিজীবী",
        "estimated_duration": "Shorts (50 sec)"
    }
]

def get_dynamic_topics(niche_or_prompt: str) -> list:
    clean = niche_or_prompt.strip()
    if not clean:
        return FALLBACK_TOPICS
    return [
        {
            "id": 1,
            "title": f"{clean}: শীর্ষ ৫টি অজানা রহস্য ও তথ্য",
            "hook": f"আপনি কি জানেন {clean} নিয়ে লুকিয়ে আছে এমন কিছু অবিশ্বাস্য সত্য?",
            "category": "তথ্য ও জ্ঞান",
            "target_audience": "কৌতূহলী দর্শক",
            "estimated_duration": "Shorts (50 sec)"
        },
        {
            "id": 2,
            "title": f"{clean} যেভাবে আপনার জীবন বদলে দিতে পারে",
            "hook": f"{clean} সম্পর্কে এই গুরুত্বপূর্ণ বিষয়টি আগে কখনো ভেবে দেখেছেন?",
            "category": "লাইফস্টাইল ও সচেতনতা",
            "target_audience": "সব বয়সী মানুষ",
            "estimated_duration": "Shorts (55 sec)"
        },
        {
            "id": 3,
            "title": f"{clean} নিয়ে শীর্ষ ৩টি প্রচলিত ভুল ধারণা",
            "hook": f"{clean} নিয়ে এই ভুলটি আমরা অনেকেই প্রতিদিন করে থাকি!",
            "category": "ফ্যাক্ট চেক",
            "target_audience": "সচেতন দর্শক",
            "estimated_duration": "Shorts (45 sec)"
        },
        {
            "id": 4,
            "title": f"ভবিষ্যতে {clean} এর রূপ কেমন হতে চলেছে?",
            "hook": f"আগামী কয়েক বছরে {clean} কতটা বিস্ময়কর হতে চলেছে জানেন?",
            "category": "ভবিষ্যৎ ও উদ্ভাবন",
            "target_audience": "প্রযুক্তি ও ভবিষ্যৎপ্রেমী",
            "estimated_duration": "Shorts (60 sec)"
        },
        {
            "id": 5,
            "title": f"{clean} সম্পর্কে সফল মানুষের আসল গোপন রহস্য",
            "hook": f"{clean} নিয়ে এই ছোট্ট কৌশলটি আপনার দৃষ্টিভঙ্গি সম্পূর্ণ বদলে দেবে!",
            "category": "অনুপ্রেরণা",
            "target_audience": "সকল দর্শক",
            "estimated_duration": "Shorts (50 sec)"
        }
    ]

def generate_topics(
    niche_or_prompt: str,
    format_type: str = "Shorts / Reels (9:16)",
    api_key: str = None,
    model_name: str = "gemini-2.5-flash"
) -> list:
    """
    এজেন্ট ১: টপিক জেনারেটর
    ব্যবহারকারী একটি বিষয় বা নিচ দিলে স্বয়ংক্রিয়ভাবে ৫টি সেরা বাংলা টপিক তৈরি করে।
    """
    key = api_key or get_gemini_api_key()
    
    if not key:
        return get_dynamic_topics(niche_or_prompt)

    prompt = f"""
তুমি একজন দক্ষ বাংলা ও ইংরেজি ইউটিউব কন্টেন্ট স্ট্র্যাটেজিস্ট ও ভাইরাল ভিডিও ক্রিয়েটর।
ব্যবহারকারীর দেওয়া নিচ/বিষয়: "{niche_or_prompt}"
ভিডিও ফরম্যাট: {format_type}

কাজ:
এই বিষয়ের উপর ভিত্তি করে ৫টি অত্যন্ত আকর্ষণীয়, ক্লিকযোগ্য এবং ভাইরাল হওয়ার মতো ভিডিও টপিক তৈরি করো।
ইউটিউব অ্যালগরিদম ও মানুষের কৌতূহল মাথায় রেখে শিরোনামগুলো তৈরি করবে।

নিম্নলিখিত JSON ফরম্যাটে ফলাফল দাও (কোনো অতিরিক্ত টেক্সট বা মার্কডাউন ছাড়া কেবল ভ্যালিড JSON):
[
  {{
    "id": 1,
    "title": "আকর্ষণীয় শিরোনাম",
    "hook": "প্রথম ৫ সেকেন্ডের কৌতূহলোদ্দীপক হুক লাইন",
    "category": "ক্যাটাগরি",
    "target_audience": "টার্গেট অডিয়েন্স",
    "estimated_duration": "Shorts (45-60s) অথবা Long (3-5 min)"
  }}
]
"""
    try:
        client = genai.Client(api_key=key)
        models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-latest", model_name, "gemini-2.5-flash"]
        
        response_text = None
        for m in models_to_try:
            try:
                response = client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config={"response_mime_type": "application/json"}
                )
                response_text = response.text
                if response_text:
                    break
            except Exception as e:
                continue
                
        if response_text:
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            data = json.loads(cleaned.strip())
            if isinstance(data, list) and len(data) > 0:
                return data
    except Exception as e:
        print(f"[Agent 1 Error] {e}")

    return get_dynamic_topics(niche_or_prompt)

