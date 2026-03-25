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
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest

# ==========================================
# 1. אתחול, הגדרות ובסיס נתונים
# ==========================================
load_dotenv(override=True)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

GA4_JSON = os.environ.get("GOOGLE_ANALYTICS_JSON")
GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
INSTAGRAM_BUSINESS_ID = os.environ.get("INSTAGRAM_BUSINESS_ID")

GEMINI_MODEL = "gemini-2.0-flash"
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# הגדרת הקונטקסט - פותר את שגיאת BRAND_CONTEXT
BRAND_CONTEXT = """
BRAND CONTEXT:
- "Kal Ride" offers premium, quiet electric off-road experiences in Motza Valley, Jerusalem.
- Vehicles: "Mia Four" (Electric, stable, high-end).
- CAPACITY: Boutique fleet of 5 vehicles. For larger groups, custom solutions.
- SCHEDULE: Sun-Thu full day, Friday until afternoon. Closed on Shabbat/Holidays.
- STRATEGY: High-end luxury, boutique feel.


"""

# הגדרת בנק המדיה - פותר את שגיאת MEDIA_BANK
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

# ==========================================
# 2. עזרי תשתית (Utility Functions)
# ==========================================

def is_shabbat_now():
    """בודק אם עכשיו זמן שבת - פותר את שגיאת is_shabbat_now"""
    now = datetime.now()
    weekday = now.weekday()  # 4 = Friday, 5 = Saturday
    hour = now.hour
    if (weekday == 4 and hour >= 15) or (weekday == 5 and hour < 19):
        return True
    return False

def extract_json(text):
    start, end = text.find('{'), text.rfind('}')
    return text[start:end+1] if (start != -1 and end != -1) else text

def call_ai(prompt, system_prompt, schema=None, use_google=False, expect_json=True):
    config_args = {"system_instruction": system_prompt, "max_output_tokens": 8192}
    if expect_json: config_args["response_mime_type"] = "application/json"
    if schema: config_args["response_schema"] = schema
    if use_google: config_args["tools"] = [{"google_search": {}}]
    
    res = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=types.GenerateContentConfig(**config_args))
    if not expect_json: return res.text.strip()
    cleaned = re.sub(r'[\x00-\x1F]+', ' ', extract_json(res.text))
    return json.loads(cleaned, strict=False)

def post_to_meta(caption, media_url):
    """פרסום למטא - פותר את שגיאת post_to_meta"""
    if not META_ACCESS_TOKEN: return
    print(f"🚀 Posting to Meta: {media_url}")
    # כאן תבוא הלוגיקה המלאה של ה-Requests למטא כפי שהייתה לך קודם
    pass

# ==========================================
# 3. סוכני הייצור (The Agents)
# ==========================================

def agent_0_challenger():
    print("🧠 Agent 0: Analyzing performance & inventing trend...")
    # שליפת לקח רלוונטי לרטרוספקטיבה
    last_action = supabase.table("agent_learning").select("*").order("created_at", desc=True).limit(1).execute()
    stats = {"conversions": 0, "clicks": 0} # כאן אפשר להפעיל את פונקציית ה-GA4
    
    sys = f"ROLE: Aggressive CMO. {BRAND_CONTEXT}. KPI: Customer Conversion."
    prompt = f"Data: {stats}. Invent a unique trend for Kal Ride that breaks the box. Output JSON."
    return call_ai(prompt, sys)

def agent_1_strategist(trend):
    print(f"🎯 Agent 1: Planning for trend: {trend['trend_concept']}")
    sys = f"Lead SEO Strategist. {BRAND_CONTEXT}"
    prompt = f"Trend: {trend['trend_concept']}. Create topic, angle, category, and slug in Hebrew."
    return call_ai(prompt, sys)

def agent_3_writer(title, section, prev_text):
    print(f"✍️ Agent 3: Writing section: {section}")
    sys = f"Elite SEO Writer. {BRAND_CONTEXT}. Hebrew only."
    prompt = f"Article: {title}. Section: {section}. Write 250 words."
    return call_ai(prompt, sys, expect_json=False)

def agent_7_proofreader(text, lang):
    """סוכן הגהה - התחנה האחרונה לתיקון טעויות כתיב"""
    print(f"🔍 Agent 7: Proofreading {lang}...")
    sys = f"ROLE: Expert Proofreader in {lang}. FIX ALL SPELLING/GRAMMAR. Keep luxury tone. Return ONLY corrected text."
    return call_ai(f"Fix this: {text}", sys, expect_json=False)

# ==========================================
# 4. הריצה המרכזית (Main Loop)
# ==========================================

def run_full_cycle():
    print("--- 🏭 KAL RIDE AUTOMATED MARKETING STARTED ---")
    
    # 1. אסטרטגיה וניתוח
    trend = agent_0_challenger()
    strat = agent_1_strategist(trend)
    
    # 2. כתיבה והגהה לעברית
    raw_body = "תוכן גולמי..." # כאן הלולאה של ה-sections
    final_body_he = agent_7_proofreader(raw_body, "Hebrew")
    
    # 3. בחירת מדיה
    cat = trend.get('category', 'nature_and_views')
    media = random.choice(MEDIA_BANK.get(cat, MEDIA_BANK['nature_and_views']))
    
    # 4. פרסום (אם לא שבת)
    if not is_shabbat_now():
        final_caption = agent_7_proofreader("פוסט שיווקי אגרסיבי...", "Hebrew")
        post_to_meta(final_caption, media['url'])
    
    # 5. שמירה ללמידה
    supabase.table("agent_learning").insert({
        "trend_concept": trend['trend_concept'],
        "insight": trend['logic'],
        "created_at": datetime.now().isoformat()
    }).execute()

if __name__ == "__main__":
    run_full_cycle()