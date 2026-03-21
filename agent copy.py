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

# ==========================================
# 1. הגדרות וחיבורים
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
INSTAGRAM_BUSINESS_ID = os.environ.get("INSTAGRAM_BUSINESS_ID")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")

GEMINI_MODEL = "gemini-2.5-flash"
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

MEDIA_BANK = {
    "extreme": [
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/bg-frontal.mp4",
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/kalride-11.mp4",
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/kalride-9.webp",
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/kalride-24.webp",
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/kalride-21.webp"
    ],
    "family": [
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-1.jpg",
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-2.jpg",
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-4.jpg",
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-5.jpg",
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-6.jpg",
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/karide-30.jpeg"
    ],
    "nature": [
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/summday_9665585533.jpg",
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/karide-29.jpeg",
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/route-110.jpeg",
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/route-170.jpg",
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/tour-14.jpg",
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/tour-15.jpg"
    ],
    "pov": [
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/pov/bg-pov.mp4",
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/pov/pov.jpeg"
    ],
    "technical": [
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/specs.webp",
        "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/ready.jpeg"
    ]
}

BRAND_CONTEXT = """
BRAND & PRODUCT CONTEXT:
- "Kal Ride" offers premium, extreme off-road driving experiences in Motza Valley (Jerusalem).
- Vehicles: "Mia Four" - 100% electric, quiet, eco-friendly.
- RULES: Strictly 2x4 drive. NEVER call them 4x4. No license needed.
- Mention local spots: Motza Valley, Jerusalem mountains, natural springs.
"""

# ==========================================
# 2. עזרי AI וחילוץ JSON
# ==========================================
def extract_json(text):
    start, end = text.find('{'), text.rfind('}')
    return text[start:end+1] if start != -1 and end != -1 else text

def call_ai(prompt, system_prompt, schema=None, use_google=False, expect_json=True):
    for attempt in range(3):
        try:
            config = {"system_instruction": system_prompt, "max_output_tokens": 8192}
            if use_google:
                config["tools"] = [{"google_search": {}}]
                if expect_json: prompt += "\n\nOutput only a valid JSON object."
            elif expect_json:
                config["response_mime_type"] = "application/json"
                if schema: config["response_schema"] = schema

            res = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=types.GenerateContentConfig(**config))
            if not expect_json: return res.text.strip()
            return json.loads(extract_json(res.text), strict=False)
        except Exception as e:
            print(f"⚠️ AI Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    raise Exception("AI Pipeline Failed")

# ==========================================
# 3. פונקציות פרסום למטא (FB & IG)
# ==========================================
def post_to_meta(caption, media_url):
    if not META_ACCESS_TOKEN:
        print("❌ Error: Missing Token in .env")
        return

    is_video = media_url.lower().endswith('.mp4')
    print(f"🚀 Publishing to Meta... (Media: {'Video' if is_video else 'Photo'})")

    try:
        # --- Facebook ---
        fb_url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/{'videos' if is_video else 'photos'}"
        fb_payload = {
            'access_token': META_ACCESS_TOKEN,
            'caption' if is_video else 'message': caption,
            'file_url' if is_video else 'url': media_url
        }
        fb_res = requests.post(fb_url, data=fb_payload).json()
        if "id" in fb_res: print(f"✅ Facebook: Posted (ID: {fb_res['id']})")
        else: print(f"❌ Facebook Error: {fb_res}")

        # --- Instagram ---
        print("📸 Instagram: Creating container...")
        ig_cont_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_BUSINESS_ID}/media"
        ig_payload = {
            'access_token': META_ACCESS_TOKEN,
            'caption': caption,
            'media_type': 'REELS' if is_video else 'IMAGE'
        }
        if is_video: ig_payload['video_url'] = media_url
        else: ig_payload['image_url'] = media_url

        cont_res = requests.post(ig_cont_url, data=ig_payload).json()
        if "id" in cont_res:
            creation_id = cont_res["id"]
            # לופ המתנה לעיבוד (קריטי לסרטונים ותמונות כבדות)
            for i in range(15):
                time.sleep(20)
                status = requests.get(f"https://graph.facebook.com/v19.0/{creation_id}?fields=status_code&access_token={META_ACCESS_TOKEN}").json().get("status_code")
                print(f"   IG Status Check ({i+1}): {status}")
                if status == "FINISHED":
                    pub_res = requests.post(f"https://graph.facebook.com/v19.0/{INSTAGRAM_BUSINESS_ID}/media_publish", 
                                            data={'creation_id': creation_id, 'access_token': META_ACCESS_TOKEN}).json()
                    if "id" in pub_res: print(f"✅ Instagram: Posted (ID: {pub_res['id']})")
                    return
            print("⚠️ Instagram: Timeout during processing.")
        else: print(f"❌ Instagram Container Error: {cont_res}")
    except Exception as e: print(f"❌ Meta Fatal Error: {e}")

# ==========================================
# 4. הפעלה (The Unified Pipeline)
# ==========================================
def run_integrated_agent():
    print(f"--- 🏭 KAL RIDE CONTENT FACTORY ({GEMINI_MODEL}) ---")
    try:
        # שלב 1: אסטרטגיה
        strat = call_ai("Find a Jerusalem nature/offroad trend for today.", 
                        f"ROLE: SEO Expert. {BRAND_CONTEXT} HEBREW. JSON: {{'topic':'...','angle':'...','category':'{list(MEDIA_BANK.keys())}','slug':'...'}}", use_google=True)
        print(f"💡 Topic: {strat['topic']}")

        # שלב 2: כתיבת עומק בעברית
        outline = call_ai(f"Structure 4 sections for: {strat['topic']}", "ROLE: Architect. JSON: {'sections': ['...', '...', '...', '...']}")
        raw_body = ""
        for s in outline["sections"]:
            raw_body += f"<h2>{s}</h2>\n<p>{call_ai(f'Write 150 words on: {s}', f'ROLE: Elite Writer. {BRAND_CONTEXT} HEBREW. No HTML.', expect_json=False)}</p>\n\n"

        # שלב 3: עריכה סופית
        edit = call_ai(f"Finalize: {strat['topic']}", f"ROLE: Editor. {BRAND_CONTEXT} Highlight 1-2 words in title with **. JSON: {{'title_he': '...', 'intro_he': '...', 'outro_he': '...', 'meta_desc': '...'}}")
        full_content_he = f"<p>{edit['intro_he']}</p>\n\n{raw_body}\n\n<h2>מוכנים להרפתקה?</h2>\n<p>{edit['outro_he']}</p>"

        # שלב 4: תרגום (EN & FR)
        print("🌍 Translating...")
        trans = call_ai(f"Translate this to English and French: {edit['title_he']}\n\n{full_content_he}", 
                        "ROLE: Translator. JSON: {'t_en': '...', 'c_en': '...', 't_fr': '...', 'c_fr': '...'}")

        # שלב 5: בחירת מדיה וסושיאל
        media = random.choice(MEDIA_BANK.get(strat['category'], MEDIA_BANK['nature']))
        social = call_ai(f"Create a social post for: {edit['title_he']}", f"ROLE: Social Expert. {BRAND_CONTEXT} HEBREW. JSON: {{'post': '...'}}")

        # שלב 6: שמירה ל-Supabase
        record = {
            "slug": strat["slug"],
            "media_url": media,
            "title_he": edit["title_he"], "content_he": full_content_he,
            "title_en": trans["t_en"], "content_en": trans["c_en"],
            "title_fr": trans["t_fr"], "content_fr": trans["c_fr"],
            "meta_description": edit["meta_desc"],
            "social_post": social["post"],
            "status": "published", "language_code": "he",
            "title": edit["title_he"], "content": full_content_he # Legacy support
        }
        supabase.table("articles").insert(record).execute()
        print(f"🔥 Article Live: https://kalride.co.il/articles/{strat['slug']}")

        # שלב 7: פרסום למטא
        final_caption = f"{social['post']}\n\nלסיפור המלא באתר:\nhttps://kalride.co.il/articles/{strat['slug']}"
        post_to_meta(final_caption, media)

    except Exception as e:
        print(f"❌ Pipeline Crash: {e}")

if __name__ == "__main__":
    run_integrated_agent()