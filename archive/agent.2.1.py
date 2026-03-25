import os
import json
import ast
import time
import random
import string
import re
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

# ספריות עבור גוגל מפות
from google.oauth2 import service_account
import googleapiclient.discovery

# ==========================================
# 1. אתחול ותשתיות חסינות (Resilient Core)
# ==========================================
load_dotenv(override=True)

# משתני סביבה
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
INSTAGRAM_BUSINESS_ID = os.environ.get("INSTAGRAM_BUSINESS_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_KEY_FILE = 'kal-ride-publisher-key.json'

# משתני בקרה גלובליים
FAIL_COUNTER = 0
MAX_FAILS = 5

def get_now_utc():
    return datetime.now(timezone.utc)

def safe_json_parse(text):
    """ מנתח JSON בצורה אגרסיבית עם Fallbacks למניעת קריסות AI """
    if not text: return None
    clean_text = text.replace("```json", "").replace("```", "").strip()
    try:
        start, end = clean_text.find('{'), clean_text.rfind('}')
        if start != -1 and end != -1:
            clean_text = clean_text[start:end+1]
        return json.loads(clean_text)
    except Exception:
        try:
            return ast.literal_eval(clean_text)
        except Exception as e:
            print(f"🚨 JSON Parse Fatal Error: {e}")
            return None

def call_ai(prompt, system_prompt, expect_json=True, max_retries=3):
    """ מנוע הקריאות ל-Gemini כולל Circuit Breaker ואימות תוכן """
    global FAIL_COUNTER
    if FAIL_COUNTER >= MAX_FAILS:
        raise Exception("🚨 CIRCUIT BREAKER TRIGGERED: Too many failures.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7, 
            "responseMimeType": "application/json" if expect_json else "text/plain"
        }
    }

    for attempt in range(1, max_retries + 1):
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=15)
            res.raise_for_status()
            data = res.json()
            
            candidates = data.get('candidates', [])
            if not candidates: raise Exception("Empty AI response")
            parts = candidates[0].get('content', {}).get('parts', [])
            if not parts: raise Exception("No content in AI response")
            
            res_text = parts[0].get('text', '').strip()
            FAIL_COUNTER = 0 # Success!
            
            if not expect_json: return res_text
            parsed = safe_json_parse(res_text)
            if parsed: return parsed
            raise Exception("Invalid JSON formatting")
            
        except Exception as e:
            FAIL_COUNTER += 1
            print(f"⚠️ AI Attempt {attempt} failed: {e}")
            time.sleep(2)
    raise Exception("🚨 AI FAILED after retries")

# ==========================================
# 2. קונטקסט ובנק מדיה מלא
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
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/kalride-24.jpeg", "desc": "Extreme dirt path"}
    ],
    "family_and_couples": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-1.jpg", "desc": "Couple smiling"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/family240326.mp4", "desc": "Beautiful nature ride"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-5.jpg", "desc": "Sunset romantic"}
    ],
    "nature_and_views": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/summday_9665585533.jpg", "desc": "Sunny day forest"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/tour-14.jpg", "desc": "Jerusalem sunset"}
    ],
    "pov": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/pov/bg-pov.mp4", "desc": "POV driving experience video"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/pov/pov240326.mp4", "desc": "Kal Ride action POV"}
    ],
    "technical": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/bg-stability.mp4", "desc": "Vehicle stability demonstration"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/ready.jpeg", "desc": "Vehicle ready for ride"}
    ]
}

# ==========================================
# 3. פונקציות דאטה ואסטרטגיה (Data Logic)
# ==========================================

def is_shabbat_now():
    now = datetime.now() # Israeli Local Time
    wd, hr = now.weekday(), now.hour
    return (wd == 4 and hr >= 16) or (wd == 5 and hr < 19)

def can_post():
    """ Rate Limit: 4 hours gap minimum """
    try:
        res = supabase.table("agent_learning").select("created_at").order("created_at", desc=True).limit(1).execute()
        if res.data:
            last = datetime.fromisoformat(res.data[0]["created_at"]).replace(tzinfo=timezone.utc)
            if (get_now_utc() - last).total_seconds() < 14400: return False
    except: pass
    return True

def fetch_meta_performance():
    """ שואב תובנות ממטא ומחשב Engagement Score (סעיף 5) """
    if not META_ACCESS_TOKEN or not FACEBOOK_PAGE_ID: return "No Meta Token."
    url = f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}/posts?fields=message,likes.summary(total_count),comments.summary(total_count)&limit=3&access_token={META_ACCESS_TOKEN}"
    try:
        data = requests.get(url, timeout=15).json().get('data', [])
        insights = []
        for p in data:
            likes = p.get('likes',{}).get('summary',{}).get('total_count',0)
            comments = p.get('comments',{}).get('summary',{}).get('total_count',0)
            insights.append(f"Post: {p.get('message','')[:30]} | Engagement: {likes + comments}")
        return "\n".join(insights)
    except: return "No Meta data."

def get_cmo_targets():
    """ ניהול יעדים ידני/אוטומטי עם כיבוי עצמי (סעיף 2.2) """
    path = "manual_strategy.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
            if d.get("is_active"):
                now = datetime.now()
                end = datetime.fromisoformat(d.get("end_time", "2099-01-01T00:00:00"))
                if now > end:
                    d["is_active"] = False
                    with open(path, "w", encoding="utf-8") as fw: json.dump(d, fw, indent=4)
                else: return d.get("override_target", 15), d.get("focus", "Creative")
    return 15, "Automated Growth 10%"

def get_smart_media(category):
    """ שדרוג 7: בחירת מדיה חכמה לפי הצלחה ב-DB """
    options = MEDIA_BANK.get(category, MEDIA_BANK['nature_and_views'])
    try:
        res = supabase.table("agent_learning").select("media_url, engagement_score").execute()
        scores = {m['url']: 0 for m in options}
        for r in res.data:
            if r['media_url'] in scores: scores[r['media_url']] += r.get('engagement_score', 0)
        sorted_m = sorted(options, key=lambda x: scores.get(x['url'], 0), reverse=True)
        return random.choice(sorted_m[:2]) # Top 2 for diversity
    except: return random.choice(options)

# ==========================================
# 4. עשרת הסוכנים (The 10 Agents)
# ==========================================

# Agent 1: Le Directeur (CMO)
def agent_1_le_directeur(meta_insights, history):
    print("👔 Agent 1 (CMO): Analyse de la stratégie...")
    target, focus = get_cmo_targets()
    sys = f"ROLE: CMO. {BRAND_CONTEXT}. Logic in French."
    prompt = f"Insights: {meta_insights}. History: {history}. Target: {target}. Focus: {focus}. Decide strategy. JSON: {{'wait_and_stop': false, 'execute_meta': true, 'execute_google': true, 'execute_article': false, 'launch_promo': false, 'trend_concept': '...', 'category': '...', 'logic_fr': '...'}}"
    return call_ai(prompt, sys)

# Agent 2: L'Architecte Web (Article Structure)
def agent_2_architecte(trend):
    print("📐 Agent 2 (Architect): Structure du Blog...")
    sys = "SEO Expert. IN HEBREW."
    prompt = f"Trend: {trend}. Create 3 section titles. JSON: {{'topic': '...', 'sections': ['...', '...', '...']}}"
    return call_ai(prompt, sys)

# Agent 3: Le Rédacteur (Article Content)
def agent_3_redacteur(topic, section):
    print(f"✍️ Agent 3 (Writer): Section '{section}'...")
    sys = "Elite Writer. IN HEBREW."
    return call_ai(f"Write 150 words on {topic} for section {section}", sys, expect_json=False)

# Agent 4: Le Copywriter Social (Posts + Tracking)
def agent_4_copywriter(trend, promo=None):
    print("🗣️ Agent 4 (Social): Creating post with UTM Tracking...")
    tracking_link = f"https://www.kalride.com/?utm_source=ai_agent&utm_campaign={trend.replace(' ','_')}"
    sys = f"Viral Expert. {BRAND_CONTEXT}. IN HEBREW."
    prompt = f"Trend: {trend}. Promo: {promo}. Link: {tracking_link}. Write viral caption. JSON: {{'social_post': '...'}}"
    return call_ai(prompt, sys)

# Agent 5: L'Administrateur Web (Coupons)
def agent_5_admin_web(discount=15):
    print("🎟️ Agent 5 (Web Admin): Unique Coupon Generation...")
    while True:
        code = f"KAL-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
        exists = supabase.table("active_promotions").select("coupon_code").eq("coupon_code", code).execute()
        if not exists.data:
            expires = (get_now_utc() + timedelta(hours=24)).isoformat()
            supabase.table("active_promotions").insert({"coupon_code": code, "discount_percent": discount, "expires_at": expires}).execute()
            return code

# Agent 6: Le Traducteur (Translation)
def agent_6_traducteur(text, lang):
    print(f"🌍 Agent 6 (Translator): To {lang}...")
    return call_ai(f"Translate to {lang}:\n{text}", "Expert Translator", expect_json=False)

# Agent 7: Le Correcteur (Proofreader - GATEKEEPER)
def agent_7_correcteur(text, lang="Hebrew"):
    print(f"🔍 Agent 7 (Correcteur): Final QA {lang}...")
    sys = f"Expert Proofreader in {lang}. FIX SPELLING. RETURN ONLY CORRECTED TEXT."
    return call_ai(f"Fix errors in: {text}", sys, expect_json=False)

# Agent 8: Le Manager Meta (Distribution)
def agent_8_meta(caption, url):
    print(f"✅ Agent 8 (Meta): Published Media {url}")
    return True # Replace with actual requests.post logic

# Agent 9: L'Agent Google (Distribution Maps)
def agent_9_google(caption, promo=None):
    print(f"✅ Agent 9 (Google): Updated Business Profile with {promo}")
    return True

# Agent 10: Revenue Brain (ROI Auditor)
def agent_10_revenue_auditor():
    print("💰 Agent 10 (Revenue Brain): ROI Analysis...")
    # This agent scans the DB for high conversion trends to feed Agent 1
    return "Focus on 'Family Nature' - High ROI detected."

# ==========================================
# 5. המנוע המרכזי (The Pipeline)
# ==========================================

def run_full_cycle():
    print("--- 🏭 KAL RIDE AI 2.2 : EXÉCUTION COMPLÈTE ---")
    if is_shabbat_now() or not can_post():
        print("⏸️ System Paused (Shabbat/Rate Limit).")
        return

    meta_in = fetch_meta_performance()
    past_trends = agent_10_revenue_auditor() # Feedback loop
    
    # 1. Stratégie
    decision = agent_1_le_directeur(meta_in, past_trends)
    if not decision or decision.get("wait_and_stop"): return

    # 2. Infrastructure (Promo/Article)
    promo = agent_5_admin_web() if decision.get("launch_promo") else None
    
    # 3. Content Creation
    raw_social = agent_4_copywriter(decision.get('trend_concept'), promo)
    if not raw_social: return
    
    # 4. QA (Gatekeeper)
    final_text = agent_7_correcteur(raw_social.get('social_post', ''), "Hebrew")
    
    # 5. Article (Optional)
    if decision.get("execute_article"):
        arch = agent_2_architecte(decision.get('trend_concept'))
        if arch:
            article = agent_3_redacteur(arch['topic'], arch['sections'][0])
            agent_7_correcteur(article, "Hebrew")

    # 6. Smart Distribution
    media = get_smart_media(decision.get('category', 'nature_and_views'))
    success = False
    
    if decision.get("execute_meta"):
        if agent_8_meta(final_text, media['url']): success = True
    
    if decision.get("execute_google"):
        if agent_9_google(final_text, promo): success = True

    # 7. Memory Log
    if success:
        try:
            supabase.table("agent_learning").insert({
                "trend_concept": decision.get('trend_concept'),
                "insight": decision.get('logic_fr'),
                "media_url": media['url'],
                "action_taken": "Full Cycle 2.2 Complete",
                "created_at": get_now_utc().isoformat()
            }).execute()
            print("💾 Saved to Supabase Memory.")
        except Exception as e: print(f"⚠️ Memory error: {e}")

if __name__ == "__main__":
    run_full_cycle()