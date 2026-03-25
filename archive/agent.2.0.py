import os
import json
import ast
import time
import random
import string
import re
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# ספריות עבור גוגל מפות
from google.oauth2 import service_account
import googleapiclient.discovery

# ==========================================
# 1. אתחול והגדרות (Initialisation)
# ==========================================
load_dotenv(override=True)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
INSTAGRAM_BUSINESS_ID = os.environ.get("INSTAGRAM_BUSINESS_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_KEY_FILE = 'kal-ride-publisher-key.json'

# משתנים גלובליים לבקרה
FAIL_COUNTER = 0
MAX_FAILS = 5

# ==========================================
# 2. קונטקסט ובנק מדיה
# ==========================================
BRAND_CONTEXT = """
BRAND CONTEXT:
- "Kal Ride" offers premium, quiet electric off-road experiences in Motza Valley, Jerusalem.
- Vehicles: "Mia Four" (Electric, stable, high-end).
- CAPACITY: Boutique fleet of 5 vehicles.
- STRATEGY: High-end luxury, boutique feel, focus on nature and off-road stability.
"""

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
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/karide-30.jpeg", "desc": "Clean vehicles ready"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/family240326.mp4", "desc": "Beautiful nature ride"}
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
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/pov/pov240326.mp4", "desc": "Kal Ride action POV"},
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
# 3. פונקציות תשתית (Infrastructure)
# ==========================================

def safe_json_parse(text):
    try:
        clean_text = text.replace("```json", "").replace("```", "").strip()
        start, end = clean_text.find('{'), clean_text.rfind('}')
        if start != -1 and end != -1:
            clean_text = clean_text[start:end+1]
        return json.loads(clean_text)
    except:
        try:
            return ast.literal_eval(clean_text)
        except:
            return None

def call_ai(prompt, system_prompt, expect_json=True, max_retries=3):
    global FAIL_COUNTER
    if FAIL_COUNTER >= MAX_FAILS:
        raise Exception("🚨 CIRCUIT BREAKER TRIGGERED")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096}
    }
    if expect_json:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            res_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
            FAIL_COUNTER = 0
            if not expect_json: return res_text
            parsed = safe_json_parse(res_text)
            if parsed: return parsed
            raise Exception("Invalid JSON")
        except:
            FAIL_COUNTER += 1
            time.sleep(2)
    raise Exception("🚨 AI FAILED")

def is_shabbat_now():
    now = datetime.now()
    if (now.weekday() == 4 and now.hour >= 16) or (now.weekday() == 5 and now.hour < 19):
        return True
    return False

def can_post():
    try:
        last = supabase.table("agent_learning").select("created_at").order("created_at", desc=True).limit(1).execute()
        if last.data:
            last_time = datetime.fromisoformat(last.data[0]["created_at"])
            if (datetime.now() - last_time).total_seconds() < 14400:
                return False
    except: pass
    return True

# ==========================================
# 4. ניהול אסטרטגיה ודאטה
# ==========================================

def get_cmo_targets():
    manual_file = "manual_strategy.json"
    if os.path.exists(manual_file):
        with open(manual_file, "r", encoding="utf-8") as f:
            manual_data = json.load(f)
            if manual_data.get("is_active"):
                now = datetime.now()
                end_time = datetime.fromisoformat(manual_data.get("end_time", "2099-01-01T00:00:00"))
                if now > end_time:
                    manual_data["is_active"] = False
                    with open(manual_file, "w", encoding="utf-8") as fw:
                        json.dump(manual_data, fw, indent=4)
                else:
                    return manual_data.get("override_target", 15), manual_data.get("focus", "Créatif")
    return 15, "Croissance automatique"

def fetch_meta_insights():
    if not META_ACCESS_TOKEN or not FACEBOOK_PAGE_ID: return "No Meta Token."
    url = f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}/posts?fields=message,likes.summary(total_count),comments.summary(total_count)&limit=3&access_token={META_ACCESS_TOKEN}"
    try:
        res = requests.get(url).json().get('data', [])
        insights = []
        for p in res:
            eng = p.get('likes',{}).get('summary',{}).get('total_count',0) + p.get('comments',{}).get('summary',{}).get('total_count',0)
            insights.append(f"Post: {p.get('message','')[:30]} | Engagement: {eng}")
        return "\n".join(insights)
    except: return "No insights."

def get_past_successful_trends():
    try:
        history = supabase.table("agent_learning").select("trend_concept").order("created_at", desc=True).limit(5).execute()
        return "\n".join([f"- {h['trend_concept']}" for h in history.data]) if history.data else "No history."
    except: return "No history."

# ==========================================
# 5. הסוכנים (Agents)
# ==========================================

def agent_1_le_directeur(meta_insights, history_memory):
    sales_target, strategic_focus = get_cmo_targets()
    sys = f"ROLE: Directeur Marketing (CMO). {BRAND_CONTEXT}. KPI: ROI & Ventes."
    prompt = f"Insights: {meta_insights}. History: {history_memory}. Target: {sales_target}. Focus: {strategic_focus}. Decide strategy. JSON output: {{'wait_and_stop': false, 'execute_meta': true, 'execute_google': true, 'launch_promo': false, 'trend_concept': '...', 'category': 'nature_and_views', 'logic_fr': '...'}}"
    return call_ai(prompt, sys)

def agent_4_social_copywriter(trend, promo_code=None):
    sys = f"Viral Copywriter. {BRAND_CONTEXT}. IN HEBREW."
    promo_text = f"Include coupon: {promo_code}" if promo_code else ""
    prompt = f"Trend: {trend}. {promo_text}. Write caption with https://www.kalride.com. JSON: {{'social_post': '...'}}"
    return call_ai(prompt, sys)

def agent_5_admin_web(discount_percent=15):
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    code = f"KAL-{random_str}"
    try:
        supabase.table("active_promotions").insert({"coupon_code": code, "discount_percent": discount_percent, "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()}).execute()
        return code
    except: return code

def agent_7_correcteur(text, lang="Hebrew"):
    sys = f"Proofreader in {lang}. Return only the corrected text."
    return call_ai(f"Fix this: {text}", sys, expect_json=False)

def agent_8_meta_distributor(caption, media_url):
    print(f"✅ Meta Distributing: {media_url}")
    return True # כאן תשלים את הלוגיקה של מטא כשתסיים טסטים

def agent_9_google_distributor(caption, promo_code=None):
    print(f"✅ Google Distributing: {promo_code if promo_code else 'Update'}")
    return True

# ==========================================
# 6. מנוע ההרצה (Pipeline)
# ==========================================

def run_full_cycle():
    print("--- 🏭 KAL RIDE AI 2.0 : EXÉCUTION ---")
    if is_shabbat_now() or not can_post():
        print("⏸️ System Paused (Shabbat or Rate Limit)")
        return

    meta_in = fetch_meta_insights()
    hist = get_past_successful_trends()
    decision = agent_1_le_directeur(meta_in, hist)
    
    if not decision or decision.get("wait_and_stop"):
        print("🛑 Wait decision.")
        return

    promo = agent_5_admin_web() if decision.get("launch_promo") else None
    raw_social = agent_4_social_copywriter(decision.get('trend_concept'), promo)
    
    if raw_social:
        final_text = agent_7_correcteur(raw_social.get('social_post', ''), "Hebrew")
        media = random.choice(MEDIA_BANK.get(decision.get('category', 'nature_and_views')))
        
        success = False
        if decision.get("execute_meta"):
            if agent_8_meta_distributor(final_text, media['url']): success = True
        if decision.get("execute_google"):
            if agent_9_google_distributor(final_text, promo): success = True

        if success:
            supabase.table("agent_learning").insert({
                "trend_concept": decision.get('trend_concept', ''),
                "insight": decision.get('logic_fr', ''),
                "action_taken": "Published"
            }).execute()
            print("💾 Saved to Supabase.")

if __name__ == "__main__":
    run_full_cycle()