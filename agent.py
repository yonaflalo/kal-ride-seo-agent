import os
import json
import random
import time
import re
import requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai
from google.genai import types

# טעינת משתני סביבה
load_dotenv()
load_dotenv(override=True) # הוספנו override כדי להכריח אותו לקרוא
print("👉 DEBUG: SUPABASE_URL is:", os.environ.get("SUPABASE_URL"))
# ==========================================
# 1. הגדרות וחיבורים
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
INSTAGRAM_BUSINESS_ID = os.environ.get("INSTAGRAM_BUSINESS_ID")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")

# שימוש במודל יציב וזמין ציבורית
GEMINI_MODEL = "gemini-2.5-flash"
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

MEDIA_BANK = {
    "extreme": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/bg-frontal.mp4", "desc": "Frontal extreme video"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/kalride-11.mp4", "desc": "Technical riding"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/kalride-9.webp", "desc": "Mia Four high mountains"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/kalride-24.jpeg", "desc": "Extreme dirt path"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/kalride-21.webp", "desc": "Riding through clouds"}
    ],
    "family_and_couples": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-1.jpg", "desc": "Couple smiling"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-2.jpg", "desc": "Group of friends"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-4.jpg", "desc": "Arazim valley nature"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-5.jpg", "desc": "Sunset romantic"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-6.jpg", "desc": "Relaxed nature break"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/karide-30.jpeg", "desc": "Clean vehicles ready"}
    ],
    "nature_and_views": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/summday_9665585533.jpg", "desc": "Sunny day forest"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/karide-29.jpeg", "desc": "Panoramic view"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/route-110.jpeg", "desc": "Scenic route"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/tour-14.jpg", "desc": "Jerusalem sunset"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/tour-15.jpg", "desc": "Hidden springs"}
    ],
    "pov": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/pov/bg-pov.mp4", "desc": "POV driving experience video"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/pov/pov.jpeg", "desc": "POV driver perspective"}
    ],
    "technical": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/bg-stability.mp4", "desc": "Vehicle stability demonstration"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/kalride-13.webp", "desc": "Technical terrain"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/kalride-21.webp", "desc": "Technical ride details"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/kalride-22.jpeg", "desc": "Technical maneuver"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/kalride-25.jpeg", "desc": "Technical off-road"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/kalride-27.jpeg", "desc": "Vehicle capabilities"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/kalride-28.jpeg", "desc": "Advanced terrain"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/ready.jpeg", "desc": "Vehicle ready for ride"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/specs.webp", "desc": "Mia Four specifications"}
    ]
}

BRAND_CONTEXT = """
BRAND CONTEXT:
- "Kal Ride" offers premium, extreme off-road driving experiences in Motza Valley (Jerusalem).
- Vehicles: "Mia Four" - 100% electric, quiet, eco-friendly 4-wheelers.
- Core USP: Extreme off-roading with zero hassle.
RULES:
1. TECH SPEC: Strictly 2x4.
2. MESSAGING: Do NOT compare to owning a private Jeep.
3. LOCALIZATION: Mention Motza Valley, Jerusalem mountains.
"""

# ==========================================
# 2. עזרי AI ו-JSON
# ==========================================
def extract_json(text):
    start, end = text.find('{'), text.rfind('}')
    if start != -1 and end != -1:
        return text[start:end+1]
    return text

def call_ai(prompt, system_prompt, schema=None, use_google=False, expect_json=True, max_tokens=8192):
    for attempt in range(3):
        try:
            config_args = {
                "system_instruction": system_prompt,
                "max_output_tokens": max_tokens
            }
            
            if use_google:
                config_args["tools"] = [{"google_search": {}}]
                # כשיש Google Search אי אפשר להשתמש ב-Response MIME Type של JSON, אז נוודא את זה בטקסט
                if expect_json: 
                    prompt += "\n\nCRITICAL: Respond ONLY with a valid JSON object."
            else:
                if expect_json:
                    config_args["response_mime_type"] = "application/json"
                    if schema: config_args["response_schema"] = schema

            res = client.models.generate_content(
                model=GEMINI_MODEL, 
                contents=prompt, 
                config=types.GenerateContentConfig(**config_args)
            )
            
            if not expect_json:
                return res.text.strip()
            
            cleaned = re.sub(r'[\x00-\x1F]+', ' ', extract_json(res.text))
            return json.loads(cleaned, strict=False)
            
        except Exception as e:
            print(f"⚠️ AI Attempt {attempt+1} failed: {e}")
            if attempt == 2: raise e
            time.sleep(3)

# ==========================================
# 3. פונקציות הפרסום למטא (פייסבוק ואינסטגרם)
# ==========================================
def post_to_meta(caption, media_url):
    if not META_ACCESS_TOKEN:
        print("❌ Error: META_ACCESS_TOKEN is missing in .env")
        return

    is_video = media_url.lower().endswith('.mp4')
    print(f"🚀 Starting Meta Posting (Media Type: {'Video' if is_video else 'Image'})...")

    try:
        # --- פתרון הקסם: המרה אוטומטית מטוקן משתמש לטוקן עמוד ---
        print("🔍 Fetching Facebook Page Token automatically...")
        page_token = META_ACCESS_TOKEN
        accounts_res = requests.get(f"https://graph.facebook.com/v19.0/me/accounts?access_token={META_ACCESS_TOKEN}").json()
        if "data" in accounts_res:
            for page in accounts_res["data"]:
                if page["id"] == str(FACEBOOK_PAGE_ID):
                    page_token = page["access_token"]
                    break

        # 1. פייסבוק
        fb_endpoint = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/{'videos' if is_video else 'photos'}"
        fb_payload = {
            'access_token': page_token, # משתמשים בטוקן העמוד שחילצנו הרגע!
            'description' if is_video else 'message': caption,
            'file_url' if is_video else 'url': media_url
        }
        fb_res = requests.post(fb_endpoint, data=fb_payload).json()
        if "id" in fb_res:
            print(f"✅ Facebook: Success (ID: {fb_res['id']})")
        else:
            print(f"❌ Facebook: Error - {fb_res.get('error', {}).get('message', fb_res)}")

        # 2. אינסטגרם - יצירת Media Container (משתמשים בטוקן הרגיל)
        print("📸 Instagram: Creating media container...")
        ig_container_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_BUSINESS_ID}/media"
        ig_payload = {
            'access_token': META_ACCESS_TOKEN,
            'caption': caption,
            'media_type': 'REELS' if is_video else 'IMAGE'
        }
        if is_video: ig_payload['video_url'] = media_url
        else: ig_payload['image_url'] = media_url

        container_res = requests.post(ig_container_url, data=ig_payload).json()
        
        if "id" not in container_res:
            print(f"❌ Instagram: Container Error - {container_res.get('error', {}).get('message', container_res)}")
            return

        creation_id = container_res["id"]
        print(f"⏳ Instagram: Processing media ({creation_id})...")

        # 3. אינסטגרם - בדיקת סטטוס ופרסום סופי
        for attempt in range(12):
            time.sleep(20)
            status_res = requests.get(f"https://graph.facebook.com/v19.0/{creation_id}?fields=status_code&access_token={META_ACCESS_TOKEN}").json()
            status = status_res.get("status_code")
            print(f"   Check ({attempt+1}/12): {status}")
            
            if status == "FINISHED":
                publish_res = requests.post(f"https://graph.facebook.com/v19.0/{INSTAGRAM_BUSINESS_ID}/media_publish", data={
                    'creation_id': creation_id,
                    'access_token': META_ACCESS_TOKEN
                }).json()
                
                if "id" in publish_res:
                    print(f"✅ Instagram: Success (ID: {publish_res['id']})")
                    return
                else:
                    print(f"❌ Instagram: Publish Error - {publish_res}")
                    return
            elif status == "ERROR":
                print(f"❌ Instagram: Processing Failed - {status_res}")
                return
        
        print("⚠️ Instagram: Processing timed out.")

    except Exception as e:
        print(f"❌ Fatal Meta API Error: {e}")
# ==========================================
# 4. פס הייצור (Multi-Agent Pipeline)
# ==========================================
def agent_1_strategist():
    print("🧠 Agent 1: Finding unwritten trends...")
    past = supabase.table("articles").select("title_he").order("created_at", desc=True).limit(10).execute()
    past_titles = [p['title_he'] for p in past.data] if past.data else []
    sys = f"ROLE: Lead SEO Strategist. DATE: {datetime.now().strftime('%Y-%m-%d')}.\n{BRAND_CONTEXT}\nOUTPUT MUST BE HEBREW."
    prompt = f"Research Jerusalem nature trends. AVOID these past topics: {past_titles}.\nJSON FORMAT: {{'topic':'...','angle':'...','category':'extreme|family_and_couples|nature_and_views','slug':'english-slug',}}"
    return call_ai(prompt, sys, use_google=True)

def agent_2_architect(strategy):
    print("📐 Agent 2: Blueprinting 4 heavy sections...")
    sys = "ROLE: Content Architect. ALL TEXT IN HEBREW."
    schema = {
        "type": "OBJECT", 
        "properties": {
            "title_raw": {"type": "STRING"}, 
            "sections": {"type": "ARRAY", "items": {"type": "STRING"}}
           
        }
    }
    prompt = f"Topic: {strategy['topic']}. Angle: {strategy['angle']}. Create a raw title and exactly 4 section titles. BODY ONLY."
    return call_ai(prompt, sys, schema=schema)

def agent_3_writer(title, current_section, previous_ending):
    print(f"✍️ Agent 3: Deep drafting - {current_section}...")
    sys = f"ROLE: Elite SEO Copywriter.\n{BRAND_CONTEXT}\nRULES:\n1. Write in HEBREW.\n2. Write approx 150 words.\n3. NO INTRO/CONCLUSION. NO HTML."
    prompt = f"Article: {title}.\nPrevious text ends: '{previous_ending[-100:] if previous_ending else 'Start'}'.\nWrite: {current_section}."
    return call_ai(prompt, sys, expect_json=False)

def agent_4_finisher(title_raw, strategy):
    print("🎀 Agent 4: Writing Intro, Outro & Meta...")
    sys = f"ROLE: Editor in Chief.\n{BRAND_CONTEXT}\nTASK: 1. Wrap 1-2 words in **asterisks**. 2. Write Intro and Outro."
    schema = {
        "type": "OBJECT", "properties": {
            "highlighted_title_he": {"type": "STRING"},
            "intro_he": {"type": "STRING"}, 
            "outro_he": {"type": "STRING"}, 
            "meta_description": {"type": "STRING"}
        }
    }
    return call_ai(f"Title: {title_raw}. Topic: {strategy['topic']}.", sys, schema=schema)

def translate_to(lang_code, title_he, content_he, tone):
    print(f"🌍 Agent 5: Translating to {lang_code.upper()}...")
    sys = f"ROLE: High-end Translator. Translate to {lang_code} ({tone}). First line is Title, blank line, then content."
    text = call_ai(f"Title: {title_he}\n\n{content_he}", sys, expect_json=False)
    parts = text.split('\n', 1)
    return {
        "title": parts[0].strip().replace("Title:", "").strip(), 
        "content": parts[1].strip() if len(parts) > 1 else ""
    }

def agent_6_social_and_media(title, strategy):
    print("📱 Agent 6: Picking media & Crafting social post...")
    past_media_res = supabase.table("articles").select("media_url").execute()
    used_media = [m['media_url'] for m in past_media_res.data] if past_media_res.data else []
    
    cat_key = strategy.get("category", "nature_and_views")
    available_media = [m for m in MEDIA_BANK.get(cat_key, MEDIA_BANK["nature_and_views"]) if m["url"] not in used_media]
    if not available_media: available_media = MEDIA_BANK.get(cat_key, MEDIA_BANK["nature_and_views"])
    
    selected = random.choice(available_media)
    
    sys = f"ROLE: Viral Social Media Strategist.\n{BRAND_CONTEXT}\nTASK: Punchy HEBREW post with emojis."
    schema = {"type": "OBJECT", "properties": {"social_post": {"type": "STRING"}}}
    social = call_ai(f"Post for '{title}'.", sys, schema=schema)
    
    return {"media_url": selected["url"], "social_post": social["social_post"]}

# ==========================================
# 5. ריצה מרכזית
# ==========================================
if __name__ == "__main__":
    print("--- 🏭 KAL RIDE CONTENT FACTORY STARTED ---")
    try:
        strat = agent_1_strategist()
        outline = agent_2_architect(strat)
        
        raw_body = ""
        for s in outline["sections"]:
            section_text = agent_3_writer(outline["title_raw"], s, raw_body)
            raw_body += f"<h2>{s}</h2>\n<p>{section_text}</p>\n\n"
            
        finisher = agent_4_finisher(outline["title_raw"], strat)
        full_he = f"<p>{finisher['intro_he']}</p>\n\n{raw_body}\n\n<h2>מוכנים להרפתקה?</h2>\n<p>{finisher['outro_he']}</p>"
        
        en_data = translate_to("English", finisher["highlighted_title_he"], full_he, "Luxury Tourist")
        fr_data = translate_to("French", finisher["highlighted_title_he"], full_he, "Elegant")
        
        social_data = agent_6_social_and_media(finisher["highlighted_title_he"], strat)
        
        record = {
            "slug": strat["slug"],
            "category": strat.get("category", "nature_and_views"),
            "trending_context": strat["topic"],
            "media_url": social_data["media_url"],
            "title_he": finisher["highlighted_title_he"],
            "content_he": full_he, 
            "title_en": en_data["title"],
            "content_en": en_data["content"],
            "title_fr": fr_data["title"],
            "content_fr": fr_data["content"],
            "meta_description_he": finisher.get("meta_description", ""),
            "social_caption_insta": social_data["social_post"],
            "status": "published",
            "language_code": "he",
            "title": finisher["highlighted_title_he"],
            "content": full_he
        }
        
        supabase.table("articles").insert(record).execute()
        print(f"\n🔥 WEB UPDATE: '{record['slug']}' IS LIVE.")
        
        post_link = f"\n\nהכתבה המלאה באתר:\nhttps://kalride.co.il/articles/{record['slug']}"
        post_to_meta(f"{social_data['social_post']}{post_link}", social_data["media_url"])
        
    except Exception as e:
        print(f"\n❌ Pipeline Crash: {e}")